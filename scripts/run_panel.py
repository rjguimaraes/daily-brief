"""Orquestrador do Painel: coleta → grava → calcula → valida → publica.

Uso:
  python scripts/run_panel.py                 # execução diária
  python scripts/run_panel.py --backfill      # carga histórica (uma vez)
  python scripts/run_panel.py --only-calc     # só recalcula a partir dos CSVs

Saídas: output/panel.json, output/panel.md, output/quality.json
Princípio: se uma fonte falhar, as demais seguem; nada é estimado.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import traceback
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import yaml

sys.path.insert(0, str(Path(__file__).parent))
from dbrief import calc, collectors as col, store  # noqa: E402

TZ = ZoneInfo("America/Sao_Paulo")
OUT = Path("output")
CONFIG = Path("config/indicators.yaml")

HIST_START = date(2024, 1, 1)          # APIs baratas: histórico amplo
NA_BACKFILL_START = date(2025, 9, 15)  # CEPEA por data: o necessário para 1 ano + folga


def load_config() -> list[dict]:
    return yaml.safe_load(CONFIG.read_text(encoding="utf-8"))["indicadores"]


def collect(today: date, backfill: bool, log) -> dict:
    """Roda cada coletor isolado. Retorna o relatório por fonte."""
    start = HIST_START if backfill else today - timedelta(days=20)
    fred_key = os.environ.get("FRED_API_KEY", "")
    jobs = [
        ("BCB PTAX", lambda: col.bcb_ptax(start, today), "olinda PTAX CotacaoDolarPeriodo, cotacaoVenda"),
        ("BCB Selic", lambda: col.bcb_selic(start, today), "SGS 432"),
        ("B3 Ibovespa", lambda: col.b3_ibovespa(start, today), "B3 GetPortfolioDay"),
        ("FRED S&P 500", lambda: col.fred_sp500(start, today, fred_key), "FRED API SP500"),
        ("NY Fed EFFR", lambda: col.nyfed_effr(start, today), "NY Fed EFFR search"),
        ("Tesouro EUA", lambda: col.treasury_10y(start, today), "Daily Par Yield Curve 10 Yr"),
        ("EIA Brent", lambda: col.eia_brent(start, today), "EIA RBRTEd.xls"),
        ("Coinbase BTC", lambda: col.coinbase_btc(start, today), "Coinbase candles 86400 close"),
        ("CEPEA (NA) recentes", col.na_cepea_recent, "Notícias Agrícolas, página do indicador"),
        ("Scot (NA)", col.na_scot_today, "Notícias Agrícolas, tabela Scot, bruto à vista"),
    ]
    if backfill:
        jobs.append(("CEPEA (NA) histórico",
                     lambda: col.na_cepea_backfill(NA_BACKFILL_START, today, log=log),
                     "Notícias Agrícolas, página por data"))
    fontes = {ind["id"]: ind["fonte"] for ind in load_config()}
    report = {}
    for name, fn, method in jobs:
        try:
            result = fn()
            summary = {}
            for ind_id, pts in result.items():
                summary[ind_id] = store.upsert(ind_id, pts, fontes.get(ind_id, name), method, today)
                summary[ind_id]["recebidos"] = len(pts)
            report[name] = {"ok": True, "series": summary}
            log(f"[ok] {name}: " + ", ".join(f"{k} +{v['novos']}" for k, v in summary.items()))
        except Exception as exc:  # noqa: BLE001 — isolamento por fonte
            report[name] = {"ok": False, "erro": f"{type(exc).__name__}: {exc}"[:500]}
            log(f"[FALHA] {name}: {exc}")
            traceback.print_exc()
    return report


def ptax_crosscheck(today: date) -> list[dict]:
    """Compara PTAX (Olinda) com SGS 1 nos últimos 30 dias."""
    try:
        sgs = dict(col.bcb_sgs(1, today - timedelta(days=30), today))
    except Exception as exc:  # noqa: BLE001
        return [{"erro": f"checagem SGS 1 indisponível: {exc}"}]
    ptax = {d: o.valor for d, o in store.load("ptax_venda").items()}
    return [{"data": d.isoformat(), "olinda": ptax[d], "sgs1": v}
            for d, v in sorted(sgs.items()) if d in ptax and abs(ptax[d] - v) > 1e-6]


def build(today: date, collect_report: dict | None) -> dict:
    cfg = load_config()
    series = {ind["id"]: {d: o.valor for d, o in store.load(ind["id"]).items()} for ind in cfg}

    # Séries derivadas (relação de troca CEPEA)
    for ind in cfg:
        if ind.get("derivado_de"):
            num, den = ind["derivado_de"]
            ratio = calc.ratio_series(series[num], series[den])
            store.upsert(ind["id"], [(d, round(v, 6)) for d, v in ratio.items()],
                         ind["fonte"], "derivado", today)
            series[ind["id"]] = ratio

    rows, jumps = [], {}
    for ind in cfg:
        r = calc.compute_row(series[ind["id"]], ind["tipo"], today, ind["max_idade_dias"])
        r.update({k: ind.get(k) for k in ("id", "nome", "unidade", "tipo", "fonte", "url", "decimais", "leitura", "oculto")})
        rows.append(r)
        j = calc.daily_jumps(series[ind["id"]], ind["salto_max_pct"], today - timedelta(days=30))
        if j:
            jumps[ind["id"]] = j

    visible = [r for r in rows if not r.get("oculto")]
    n_cmp = sum(1 for r in visible for k in ("m1", "ytd", "y1") if "variacao" in r.get(k, {}))
    quality = {
        "data_referencia": today.isoformat(),
        "gerado_em_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "indicadores": len(visible),
        "ok": sum(r["status"] == "ok" for r in visible),
        "defasados": [r["id"] for r in visible if r["status"] == "defasado"],
        "ausentes": [r["id"] for r in visible if r["status"] == "ausente"],
        "comparativos_preenchidos": n_cmp,
        "comparativos_possiveis": 3 * len(visible),
        "comparativos_ausentes": {r["id"]: {k: r[k]["motivo"] for k in ("m1", "ytd", "y1")
                                            if k in r and "motivo" in r[k]}
                                  for r in visible if any("motivo" in r.get(k, {}) for k in ("m1", "ytd", "y1"))},
        "fontes_com_falha": {k: v["erro"] for k, v in (collect_report or {}).items() if not v["ok"]},
        "revisoes": {i: s["revisados"] for v in (collect_report or {}).values() if v.get("ok")
                     for i, s in v["series"].items() if s["revisados"]},
        "alertas_salto_diario": jumps,
        "divergencias_ptax_olinda_vs_sgs1": ptax_crosscheck(today) if collect_report is not None else [],
    }
    return {"rows": rows, "quality": quality}


# ----------------------------------------------------------------- formatação
def fmt_num(v: float, dec: int) -> str:
    s = f"{v:,.{dec}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def fmt_date(iso: str) -> str:
    d = date.fromisoformat(iso)
    return f"{d:%d/%m/%y}"


def fmt_change(c: dict) -> str:
    v = c["variacao"]
    sign = "+" if v > 0 else ("−" if v < 0 else "")
    if c["unidade_variacao"] == "pb":
        return f"{sign}{fmt_num(abs(v), 0)} pb"
    return f"{sign}{fmt_num(abs(v), 1)}%"


def render_md(rows: list[dict], quality: dict) -> str:
    by_id = {r["id"]: r for r in rows}
    notes: list[str] = []

    def cell(r: dict, key: str) -> str:
        c = r.get(key, {})
        if "variacao" in c:
            return fmt_change(c)
        if "motivo" in c:
            notes.append(f"{r['nome']} ({ {'m1': '1 mês', 'ytd': 'YTD', 'y1': '1 ano'}[key] }): {c['motivo']}")
            return f"—[{len(notes)}]"
        return "—"

    lines = [
        f"**Painel — referência {fmt_date(quality['data_referencia'])}** · "
        f"comparativos ancorados na data de cada observação",
        "",
        "| Indicador | Atual | vs. ~1 mês | YTD | vs. ~1 ano | Leitura |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for r in rows:
        if r.get("oculto"):
            continue
        if r["status"] == "ausente":
            notes.append(f"{r['nome']}: {r['motivo']}")
            lines.append(f"| {r['nome']} | ausente[{len(notes)}] | — | — | — | |")
            continue
        a = r["atual"]
        val = fmt_num(a["valor"], r["decimais"])
        if r["id"] == "fed_funds_alvo_sup" and "fed_funds_alvo_inf" in by_id and "atual" in by_id["fed_funds_alvo_inf"]:
            val = f"{fmt_num(by_id['fed_funds_alvo_inf']['atual']['valor'], 2)}–{val}"
            name = "Fed Funds intervalo-alvo"
        else:
            name = r["nome"]
        flag = " defasado" if r["status"] == "defasado" else ""
        atual = f"{val} {r['unidade']} ({fmt_date(a['data'])}{flag})"
        lines.append(f"| {name} | {atual} | {cell(r, 'm1')} | {cell(r, 'ytd')} | {cell(r, 'y1')} | {r.get('leitura') or ''} |")
    if notes:
        lines += ["", "Notas:"] + [f"{i}. {n}" for i, n in enumerate(notes, 1)]
    lines += ["", f"Fontes: " + "; ".join(sorted({r['fonte'] for r in rows if not r.get('oculto')}))]
    return "\n".join(lines) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--backfill", action="store_true")
    ap.add_argument("--only-calc", action="store_true")
    ap.add_argument("--ref-date")
    args = ap.parse_args()
    today = date.fromisoformat(args.ref_date) if args.ref_date else datetime.now(TZ).date()

    report = None if args.only_calc else collect(today, args.backfill, print)
    result = build(today, report)
    OUT.mkdir(exist_ok=True)
    (OUT / "panel.json").write_text(json.dumps(result["rows"], ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    (OUT / "quality.json").write_text(json.dumps(result["quality"], ensure_ascii=False, indent=2), encoding="utf-8")
    if report is not None:
        (OUT / "collect_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    md = render_md(result["rows"], result["quality"])
    (OUT / "panel.md").write_text(md, encoding="utf-8")
    print(md)
    q = result["quality"]
    print(f"Qualidade: {q['ok']}/{q['indicadores']} ok · comparativos {q['comparativos_preenchidos']}/{q['comparativos_possiveis']}"
          f" · falhas: {list(q['fontes_com_falha'])}")


if __name__ == "__main__":
    main()
