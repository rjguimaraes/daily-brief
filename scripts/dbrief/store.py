"""Armazenamento das séries em CSV, uma por indicador (data/series/<id>.csv).

CSV é a fonte da verdade: legível, versionado no Git, e cada linha diz de onde
veio o número e quando foi coletado. Uma revisão de valor (mesma data, valor
diferente) é aplicada e registrada para o relatório de qualidade.
"""
from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path

SERIES_DIR = Path("data/series")
FIELDS = ["data", "valor", "fonte", "coletado_em", "metodo"]


@dataclass
class Obs:
    data: date
    valor: float
    fonte: str
    coletado_em: str
    metodo: str


def path_for(indicator_id: str, base: Path = SERIES_DIR) -> Path:
    return base / f"{indicator_id}.csv"


def load(indicator_id: str, base: Path = SERIES_DIR) -> dict[date, Obs]:
    p = path_for(indicator_id, base)
    if not p.exists():
        return {}
    out: dict[date, Obs] = {}
    with p.open(encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            d = date.fromisoformat(row["data"])
            out[d] = Obs(d, float(row["valor"]), row["fonte"], row["coletado_em"], row["metodo"])
    return out


def save(indicator_id: str, series: dict[date, Obs], base: Path = SERIES_DIR) -> None:
    p = path_for(indicator_id, base)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(FIELDS)
        for d in sorted(series):
            o = series[d]
            w.writerow([o.data.isoformat(), repr(o.valor), o.fonte, o.coletado_em, o.metodo])


def upsert(
    indicator_id: str,
    points: list[tuple[date, float]],
    fonte: str,
    metodo: str,
    today: date,
    base: Path = SERIES_DIR,
) -> dict:
    """Insere pontos novos; registra revisões; ignora datas futuras.

    Retorna um resumo: novos, revisados (lista), futuros_descartados.
    """
    series = load(indicator_id, base)
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    novos, revisados, futuros = 0, [], 0
    for d, v in points:
        if d > today:
            futuros += 1
            continue
        v = float(v)
        old = series.get(d)
        if old is None:
            series[d] = Obs(d, v, fonte, now, metodo)
            novos += 1
        elif abs(old.valor - v) > 1e-9:
            revisados.append({"data": d.isoformat(), "antes": old.valor, "depois": v})
            series[d] = Obs(d, v, fonte, now, metodo)
    save(indicator_id, series, base)
    return {"novos": novos, "revisados": revisados, "futuros_descartados": futuros}
