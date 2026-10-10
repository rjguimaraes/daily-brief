"""Clima das propriedades: previsão, chuva recente estimada e climatologia.

Fonte: Open-Meteo (dados abertos, por coordenada).
- Previsão (próximos 10 dias): modelos numéricos (best match; ECMWF/GFS e outros).
- Últimos dias: valores de análise/previsão de curto prazo do mesmo serviço.
  São ESTIMATIVAS DE MODELO, não chuva medida em estação.
- Climatologia: reanálise ERA5 (archive API), média 1995–2024 do mês.

Saídas: output/weather.json, output/weather.md e acumulação diária em
data/weather/<local>.csv (registro próprio, cresce a cada dia).
"""
from __future__ import annotations

import csv
import json
import time
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import requests

TZ = ZoneInfo("America/Sao_Paulo")
OUT = Path("output")
WDIR = Path("data/weather")
CLIMA = WDIR / "climatologia.json"

LOCAIS = {
    "go_quirinopolis": {"nome": "Fazenda Laçada — Quirinópolis (GO)", "lat": -18.7215, "lon": -50.4246},
    "to_lagoa_azul": {"nome": "Fazenda Laçada Lagoa Azul — Pium/Lagoa da Confusão (TO)", "lat": -10.29775, "lon": -49.79627},
}
DAILY = "precipitation_sum,precipitation_probability_max,temperature_2m_max,temperature_2m_min,et0_fao_evapotranspiration"


def get(url: str, params: dict) -> dict:
    last = None
    for i in range(3):
        try:
            r = requests.get(url, params=params, timeout=90)
            r.raise_for_status()
            return r.json()
        except requests.RequestException as exc:
            last = exc
            time.sleep(5 * (i + 1))
    raise RuntimeError(f"Open-Meteo falhou: {last}")


def climatologia() -> dict:
    """Média mensal de chuva 1995–2024 (ERA5). Calculada uma vez e guardada."""
    if CLIMA.exists():
        return json.loads(CLIMA.read_text(encoding="utf-8"))
    out = {}
    for key, loc in LOCAIS.items():
        d = get("https://archive-api.open-meteo.com/v1/archive",
                {"latitude": loc["lat"], "longitude": loc["lon"], "start_date": "1995-01-01",
                 "end_date": "2024-12-31", "daily": "precipitation_sum", "timezone": "America/Sao_Paulo"})
        tot: dict[int, float] = {m: 0.0 for m in range(1, 13)}
        daily_by_doy: dict[str, list[float]] = {}
        for t, p in zip(d["daily"]["time"], d["daily"]["precipitation_sum"]):
            if p is None:
                continue
            m = int(t[5:7])
            tot[m] += p
            daily_by_doy.setdefault(t[5:], []).append(p)
        out[key] = {
            "fonte": "Open-Meteo archive (reanálise ERA5), 1995–2024",
            "media_mensal_mm": {str(m): round(tot[m] / 30, 1) for m in range(1, 13)},
            # média por dia do ano: permite comparar acumulado parcial do mês com o normal até a mesma data
            "media_diaria_mm": {k: round(sum(v) / len(v), 2) for k, v in sorted(daily_by_doy.items())},
        }
        time.sleep(2)
    WDIR.mkdir(parents=True, exist_ok=True)
    CLIMA.write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
    return out


def registrar(key: str, rows: list[dict], today: date) -> None:
    """Guarda os dias já passados (estimativa do modelo) no registro próprio."""
    p = WDIR / f"{key}.csv"
    hist: dict[str, dict] = {}
    if p.exists():
        with p.open(encoding="utf-8") as fh:
            hist = {r["data"]: r for r in csv.DictReader(fh)}
    for r in rows:
        if r["data"] < today.isoformat():
            hist[r["data"]] = {"data": r["data"], "chuva_mm": r["chuva_mm"], "tmax": r["tmax"], "tmin": r["tmin"],
                               "tipo": "estimativa de modelo (Open-Meteo)"}
    WDIR.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["data", "chuva_mm", "tmax", "tmin", "tipo"])
        w.writeheader()
        for k in sorted(hist):
            w.writerow(hist[k])


def resumo(key: str, loc: dict, clima: dict, today: date) -> dict:
    d = get("https://api.open-meteo.com/v1/forecast",
            {"latitude": loc["lat"], "longitude": loc["lon"], "daily": DAILY, "past_days": 31,
             "forecast_days": 10, "timezone": "America/Sao_Paulo"})
    dd = d["daily"]
    rows = [{"data": t, "chuva_mm": p, "prob_pct": pr, "tmax": tx, "tmin": tn, "et0_mm": e}
            for t, p, pr, tx, tn, e in zip(dd["time"], dd["precipitation_sum"], dd["precipitation_probability_max"],
                                           dd["temperature_2m_max"], dd["temperature_2m_min"],
                                           dd["et0_fao_evapotranspiration"])]
    registrar(key, rows, today)
    t = today.isoformat()
    passado = [r for r in rows if r["data"] < t and r["chuva_mm"] is not None]
    futuro = [r for r in rows if r["data"] >= t][:7]

    def soma(rs, k="chuva_mm"):
        return round(sum(r[k] or 0 for r in rs), 1)

    mes_ini = today.replace(day=1).isoformat()
    mes = [r for r in passado if r["data"] >= mes_ini]
    c = clima[key]
    normal_ate_hoje = round(sum(c["media_diaria_mm"].get(f"{today.month:02d}-{dia:02d}", 0)
                                for dia in range(1, today.day)), 1)
    seca = 0
    for r in reversed(passado):
        if (r["chuva_mm"] or 0) >= 1.0:
            break
        seca += 1
    return {
        "local": loc["nome"], "lat": loc["lat"], "lon": loc["lon"],
        "gerado_em": datetime.now(TZ).isoformat(timespec="minutes"),
        "recente": {
            "tipo": "estimativa de modelo (Open-Meteo), não estação",
            "ultimos_7_dias_mm": soma(passado[-7:]),
            "ultimos_30_dias_mm": soma(passado[-30:]),
            "dias_com_chuva_7d": sum((r["chuva_mm"] or 0) >= 1.0 for r in passado[-7:]),
            "dias_com_chuva_30d": sum((r["chuva_mm"] or 0) >= 1.0 for r in passado[-30:]),
            "dias_consecutivos_sem_chuva": seca,
            "mes_ate_ontem_mm": soma(mes),
            "periodo_mes": f"{mes_ini} a {(today - timedelta(days=1)).isoformat()}",
        },
        "climatologia": {
            "fonte": c["fonte"],
            "normal_mes_mm": c["media_mensal_mm"][str(today.month)],
            "normal_ate_ontem_mm": normal_ate_hoje,
        },
        "previsao_7d": {
            "tipo": "previsão de modelo numérico (Open-Meteo, best match)",
            "periodo": f"{futuro[0]['data']} a {futuro[-1]['data']}" if futuro else "",
            "acumulado_mm": soma(futuro),
            "dias_com_chuva": sum((r["chuva_mm"] or 0) >= 1.0 for r in futuro),
            "tmax_max": max((r["tmax"] for r in futuro), default=None),
            "tmin_min": min((r["tmin"] for r in futuro), default=None),
            "et0_mm": soma(futuro, "et0_mm"),
            "dias": futuro,
        },
    }


def render(res: list[dict]) -> str:
    lines = ["| Local | Recente (estimado) | Próximos 7 dias (previsão) | Distribuição |", "| --- | --- | --- | --- |"]
    for r in res:
        rc, cl, pv = r["recente"], r["climatologia"], r["previsao_7d"]
        dist = " · ".join(f"{datetime.fromisoformat(d['data']):%d/%m} {d['chuva_mm']:.0f}" for d in pv["dias"])
        lines.append(
            f"| {r['local']} | 7 d: {rc['ultimos_7_dias_mm']} mm ({rc['dias_com_chuva_7d']} dias) · 30 d: "
            f"{rc['ultimos_30_dias_mm']} mm · mês até ontem: {rc['mes_ate_ontem_mm']} mm vs. normal "
            f"{cl['normal_ate_ontem_mm']} mm até a mesma data (normal do mês {cl['normal_mes_mm']} mm) · "
            f"{rc['dias_consecutivos_sem_chuva']} dias seguidos sem chuva ≥ 1 mm "
            f"| {pv['acumulado_mm']} mm em {pv['dias_com_chuva']} dias · máx {pv['tmax_max']} °C · "
            f"mín {pv['tmin_min']} °C · ET0 {pv['et0_mm']} mm | {dist} (mm/dia) |")
    lines.append("")
    lines.append("Recente = estimativa de modelo (Open-Meteo), não chuva medida em estação. "
                 "Normal = reanálise ERA5 1995–2024. Previsão = modelo numérico.")
    return "\n".join(lines) + "\n"


def main() -> None:
    today = datetime.now(TZ).date()
    clima = climatologia()
    res = [resumo(k, v, clima, today) for k, v in LOCAIS.items()]
    OUT.mkdir(exist_ok=True)
    (OUT / "weather.json").write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
    md = render(res)
    (OUT / "weather.md").write_text(md, encoding="utf-8")
    print(md)


if __name__ == "__main__":
    main()
