"""Teste de acesso às fontes de dados a partir do executor do GitHub Actions.

Para cada fonte: status HTTP, tipo de conteúdo, tamanho, trecho inicial e
uma cópia bruta da resposta em reports/probe/raw/ para inspeção.
Não interpreta valores; só responde "a fonte é acessível daqui?".
"""
from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

OUT = Path("reports/probe")
RAW = OUT / "raw"
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"

GO = (-18.7215, -50.4246)
TO = (-10.29775, -49.79627)

FRED = ["SP500", "DFF", "DFEDTARL", "DFEDTARU", "DGS10", "DCOILBRENTEU"]

PROBES: list[tuple[str, str, str]] = [
    # (nome, url, extensão do arquivo bruto)
    ("bcb_sgs1_ptax", "https://api.bcb.gov.br/dados/serie/bcdata.sgs.1/dados?formato=json&dataInicial=01/09/2026&dataFinal=31/12/2026", "json"),
    ("bcb_sgs432_selic_meta", "https://api.bcb.gov.br/dados/serie/bcdata.sgs.432/dados?formato=json&dataInicial=01/09/2026&dataFinal=31/12/2026", "json"),
    ("bcb_olinda_ptax", "https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata/CotacaoDolarPeriodo(dataInicial=@dataInicial,dataFinalCotacao=@dataFinalCotacao)?@dataInicial='09-01-2026'&@dataFinalCotacao='12-31-2026'&$format=json", "json"),
    *[(f"fred_{s.lower()}", f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={s}", "csv") for s in FRED],
    ("btc_coinbase", "https://api.exchange.coinbase.com/products/BTC-USD/candles?granularity=86400", "json"),
    ("btc_kraken", "https://api.kraken.com/0/public/OHLC?pair=XBTUSD&interval=1440", "json"),
    ("btc_coingecko", "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart?vs_currency=usd&days=30&interval=daily", "json"),
    ("ibov_yahoo", "https://query1.finance.yahoo.com/v8/finance/chart/%5EBVSP?range=2y&interval=1d", "json"),
    ("ibov_b3_pagina", "https://www.b3.com.br/pt_br/market-data-e-indices/indices/indices-amplos/indice-ibovespa-ibovespa-estatisticas-historicas.htm", "html"),
    ("cepea_boi_pagina", "https://www.cepea.org.br/br/indicador/boi-gordo.aspx", "html"),
    ("cepea_boi_series", "https://www.cepea.org.br/br/indicador/series/boi-gordo.aspx?id=2", "bin"),
    ("na_boi", "https://www.noticiasagricolas.com.br/cotacoes/boi-gordo/boi-gordo-indicador-esalq-bmf", "html"),
    ("na_boi_data_2025-12-30", "https://www.noticiasagricolas.com.br/cotacoes/boi-gordo/boi-gordo-indicador-esalq-bmf/2025-12-30", "html"),
    ("na_soja_paranagua", "https://www.noticiasagricolas.com.br/cotacoes/soja/soja-indicador-cepea-esalq-porto-paranagua", "html"),
    ("na_milho", "https://www.noticiasagricolas.com.br/cotacoes/milho/indicador-cepea-esalq-milho", "html"),
    ("na_bezerro", "https://www.noticiasagricolas.com.br/cotacoes/boi-gordo/indicador-bezerro-esalq-bmf", "html"),
    ("na_boi_index", "https://www.noticiasagricolas.com.br/cotacoes/boi-gordo", "html"),
    ("scot_boi", "https://www.scotconsultoria.com.br/cotacoes/boi-gordo/", "html"),
    ("scot_reposicao", "https://www.scotconsultoria.com.br/cotacoes/reposicao/", "html"),
    ("scot_home", "https://www.scotconsultoria.com.br/", "html"),
    ("openmeteo_go_previsao", f"https://api.open-meteo.com/v1/forecast?latitude={GO[0]}&longitude={GO[1]}&daily=precipitation_sum,temperature_2m_max,temperature_2m_min,precipitation_probability_max&past_days=31&forecast_days=10&timezone=America%2FSao_Paulo", "json"),
    ("openmeteo_to_previsao", f"https://api.open-meteo.com/v1/forecast?latitude={TO[0]}&longitude={TO[1]}&daily=precipitation_sum,temperature_2m_max,temperature_2m_min,precipitation_probability_max&past_days=31&forecast_days=10&timezone=America%2FSao_Paulo", "json"),
    ("openmeteo_go_historico", f"https://archive-api.open-meteo.com/v1/archive?latitude={GO[0]}&longitude={GO[1]}&start_date=2025-09-01&end_date=2025-12-31&daily=precipitation_sum&timezone=America%2FSao_Paulo", "json"),
    ("inmet_estacoes", "https://apitempo.inmet.gov.br/estacoes/T", "json"),
    ("climatempo_home", "https://www.climatempo.com.br/", "html"),
]

# Rodada 2 (09/10/2026): alternativas às falhas da rodada 1 (FRED timeout,
# Scot 429, Yahoo 429, CEPEA 403, URL errada do bezerro).
PROBES_R2: list[tuple[str, str, str]] = [
    ("na_bezerro_ms", "https://www.noticiasagricolas.com.br/cotacoes/boi-gordo/indicador-bezerro-esalq-bmf-bovespa-ms", "html"),
    ("na_bezerro_ms_data_2025-12-30", "https://www.noticiasagricolas.com.br/cotacoes/boi-gordo/indicador-bezerro-esalq-bmf-bovespa-ms/2025-12-30", "html"),
    ("na_soja_data_2025-12-30", "https://www.noticiasagricolas.com.br/cotacoes/soja/soja-indicador-cepea-esalq-porto-paranagua/2025-12-30", "html"),
    ("na_milho_data_2025-12-30", "https://www.noticiasagricolas.com.br/cotacoes/milho/indicador-cepea-esalq-milho/2025-12-30", "html"),
    ("na_scot", "https://www.noticiasagricolas.com.br/cotacoes/boi-gordo/boi-gordo-scot-consultoria", "html"),
    ("na_scot_data_2026-09-08", "https://www.noticiasagricolas.com.br/cotacoes/boi-gordo/boi-gordo-scot-consultoria/2026-09-08", "html"),
    ("na_scot_data_2025-10-08", "https://www.noticiasagricolas.com.br/cotacoes/boi-gordo/boi-gordo-scot-consultoria/2025-10-08", "html"),
    ("na_imea_boi", "https://www.noticiasagricolas.com.br/cotacoes/boi-gordo/boi-a-vista-imea", "html"),
    ("na_reposicao_nelore_macho", "https://www.noticiasagricolas.com.br/cotacoes/boi-gordo/reposicao-nelore-macho", "html"),
    ("fred_dgs10_timeout_longo", "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DGS10", "csv"),
    ("treasury_yields_2026", "https://home.treasury.gov/resource-center/data-chart-center/interest-rates/daily-treasury-rates.csv/2026/all?type=daily_treasury_yield_curve&field_tdr_date_value=2026&page&_format=csv", "csv"),
    ("nyfed_effr", "https://markets.newyorkfed.org/api/rates/unsecured/effr/last/30.json", "json"),
    ("eia_brent_xls", "https://www.eia.gov/dnav/pet/hist_xls/RBRTEd.xls", "xls"),
    ("stooq_spx", "https://stooq.com/q/d/l/?s=%5Espx&i=d", "csv"),
    ("stooq_ibov", "https://stooq.com/q/d/l/?s=%5Ebvp&i=d", "csv"),
    ("b3_ibov_pagina_dia", "https://sistemaswebb3-listados.b3.com.br/indexStatisticsPage/day/IBOV?language=pt-br", "html"),
    ("scot_boi_lento", "https://www.scotconsultoria.com.br/cotacoes/boi-gordo/", "html"),
    ("inmet_a011_dados", "https://apitempo.inmet.gov.br/estacao/2026-09-01/2026-10-08/A011", "json"),
    ("inmet_a055_dados", "https://apitempo.inmet.gov.br/estacao/2026-09-01/2026-10-08/A055", "json"),
]


def probe(name: str, url: str, ext: str) -> dict:
    started = time.time()
    rec = {"nome": name, "url": url}
    try:
        r = requests.get(url, headers={"User-Agent": UA}, timeout=90)
        body = r.content
        rec.update(
            status=r.status_code,
            content_type=r.headers.get("content-type", ""),
            bytes=len(body),
            segundos=round(time.time() - started, 2),
            trecho=body[:300].decode("utf-8", "replace"),
        )
        (RAW / f"{name}.{ext}").write_bytes(body[:3_000_000])
    except Exception as exc:  # noqa: BLE001 - queremos registrar qualquer falha
        rec.update(status=None, erro=f"{type(exc).__name__}: {exc}"[:500],
                   segundos=round(time.time() - started, 2))
    return rec


def main() -> None:
    import os

    RAW.mkdir(parents=True, exist_ok=True)
    probes = PROBES_R2 if os.environ.get("PROBE_SET") == "2" else PROBES
    results = []
    for p in probes:
        results.append(probe(*p))
        time.sleep(2)  # espaçar requisições evita 429 em sites pequenos
    stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    (OUT / "summary.json").write_text(
        json.dumps({"executado_em_utc": stamp, "resultados": results}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    lines = [f"# Teste de fontes — {stamp} UTC", "", "| Fonte | Status | Tipo | Bytes |", "| --- | --- | --- | --- |"]
    for r in results:
        lines.append(f"| {r['nome']} | {r.get('status') or r.get('erro', '')[:60]} | {r.get('content_type', '')[:40]} | {r.get('bytes', '')} |")
    (OUT / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
