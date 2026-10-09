"""Coletores, um por fonte. Cada um devolve {indicador_id: [(data, valor), ...]}.

Nenhum coletor interpreta ou estima: só lê o que a fonte publica. Falhas sobem
como exceção e são isoladas pelo orquestrador (as demais fontes seguem).
"""
from __future__ import annotations

import base64
import csv
import io
import json
import re
import time
from datetime import date, datetime, timedelta, timezone
from typing import Callable

import requests

UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
TIMEOUT = 60

Points = list[tuple[date, float]]


def _session() -> requests.Session:
    s = requests.Session()
    s.headers["User-Agent"] = UA
    return s


def _get(s: requests.Session, url: str, **kw) -> requests.Response:
    last = None
    for attempt in range(3):
        try:
            r = s.get(url, timeout=TIMEOUT, **kw)
            if r.status_code in (429, 500, 502, 503, 504):
                last = RuntimeError(f"HTTP {r.status_code} em {url.split('?')[0]}")
                time.sleep(5 * (attempt + 1))
                continue
            r.raise_for_status()
            return r
        except requests.RequestException as exc:
            last = exc
            time.sleep(5 * (attempt + 1))
    raise RuntimeError(f"falha após 3 tentativas: {last}")


def br_number(text: str) -> float:
    """'3.066,58' -> 3066.58"""
    return float(text.strip().replace(".", "").replace(",", "."))


# --------------------------------------------------------------------- BCB
def bcb_ptax(start: date, end: date) -> dict[str, Points]:
    s = _session()
    url = ("https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata/"
           "CotacaoDolarPeriodo(dataInicial=@dataInicial,dataFinalCotacao=@dataFinalCotacao)")
    params = {"@dataInicial": f"'{start:%m-%d-%Y}'", "@dataFinalCotacao": f"'{end:%m-%d-%Y}'",
              "$format": "json", "$select": "cotacaoVenda,dataHoraCotacao"}
    rows = _get(s, url, params=params).json()["value"]
    pts = [(date.fromisoformat(r["dataHoraCotacao"][:10]), float(r["cotacaoVenda"])) for r in rows]
    return {"ptax_venda": pts}


def bcb_sgs(series_code: int, start: date, end: date) -> Points:
    s = _session()
    url = f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{series_code}/dados"
    params = {"formato": "json", "dataInicial": f"{start:%d/%m/%Y}", "dataFinal": f"{end:%d/%m/%Y}"}
    rows = _get(s, url, params=params).json()
    return [(datetime.strptime(r["data"], "%d/%m/%Y").date(), float(r["valor"])) for r in rows]


def bcb_selic(start: date, end: date) -> dict[str, Points]:
    return {"selic_meta": bcb_sgs(432, start, end)}


# --------------------------------------------------------------------- B3
def b3_ibovespa(start: date, end: date) -> dict[str, Points]:
    s = _session()
    pts: Points = []
    for year in range(start.year, end.year + 1):
        payload = json.dumps({"index": "IBOVESPA", "language": "pt-br", "year": str(year)},
                             separators=(",", ":"))
        b64 = base64.b64encode(payload.encode()).decode()
        url = f"https://sistemaswebb3-listados.b3.com.br/indexStatisticsProxy/IndexCall/GetPortfolioDay/{b64}"
        data = _get(s, url).json()
        for row in data["results"]:
            day = int(row["day"])
            for m in range(1, 13):
                v = row.get(f"rateValue{m}")
                if v:
                    pts.append((date(year, m, day), br_number(v)))
        time.sleep(1)
    return {"ibovespa": pts}


# --------------------------------------------------------------------- EUA
def fred_sp500(start: date, end: date, api_key: str) -> dict[str, Points]:
    if not api_key:
        raise RuntimeError("FRED_API_KEY ausente")
    s = _session()
    r = _get(s, "https://api.stlouisfed.org/fred/series/observations",
             params={"series_id": "SP500", "api_key": api_key, "file_type": "json",
                     "observation_start": start.isoformat(), "observation_end": end.isoformat()})
    pts = [(date.fromisoformat(o["date"]), float(o["value"]))
           for o in r.json()["observations"] if o["value"] not in (".", "")]
    return {"sp500": pts}


def nyfed_effr(start: date, end: date) -> dict[str, Points]:
    s = _session()
    url = "https://markets.newyorkfed.org/api/rates/unsecured/effr/search.json"
    rows = _get(s, url, params={"startDate": start.isoformat(), "endDate": end.isoformat()}).json()["refRates"]
    eff, sup, inf = [], [], []
    for r in rows:
        d = date.fromisoformat(r["effectiveDate"])
        eff.append((d, float(r["percentRate"])))
        if r.get("targetRateTo") is not None:
            sup.append((d, float(r["targetRateTo"])))
            inf.append((d, float(r["targetRateFrom"])))
    return {"fed_funds_efetiva": eff, "fed_funds_alvo_sup": sup, "fed_funds_alvo_inf": inf}


def treasury_10y(start: date, end: date) -> dict[str, Points]:
    s = _session()
    pts: Points = []
    for year in range(start.year, end.year + 1):
        url = (f"https://home.treasury.gov/resource-center/data-chart-center/interest-rates/"
               f"daily-treasury-rates.csv/{year}/all")
        r = _get(s, url, params={"type": "daily_treasury_yield_curve",
                                 "field_tdr_date_value": str(year), "page": "", "_format": "csv"})
        for row in csv.DictReader(io.StringIO(r.text)):
            v = row.get("10 Yr", "").strip()
            if v:
                pts.append((datetime.strptime(row["Date"], "%m/%d/%Y").date(), float(v)))
        time.sleep(1)
    return {"treasury_10a": pts}


def eia_brent(start: date, end: date) -> dict[str, Points]:
    import xlrd  # instalado no executor

    s = _session()
    r = _get(s, "https://www.eia.gov/dnav/pet/hist_xls/RBRTEd.xls")
    book = xlrd.open_workbook(file_contents=r.content)
    sheet = book.sheet_by_name("Data 1")
    pts: Points = []
    for i in range(sheet.nrows):
        a, b = sheet.cell_value(i, 0), sheet.cell_value(i, 1)
        if isinstance(a, float) and isinstance(b, float):
            d = xlrd.xldate_as_datetime(a, book.datemode).date()
            if start <= d <= end:
                pts.append((d, b))
    if not pts:
        raise RuntimeError("planilha EIA sem dados no período (layout mudou?)")
    return {"brent_spot": pts}


# --------------------------------------------------------------------- Bitcoin
def coinbase_btc(start: date, end: date) -> dict[str, Points]:
    """Candle diário UTC; o valor é o fechamento (00:00 UTC do dia seguinte).
    O candle do dia corrente (incompleto) é descartado."""
    s = _session()
    today_utc = datetime.now(timezone.utc).date()
    pts: dict[date, float] = {}
    cur = start
    while cur <= end:
        stop = min(cur + timedelta(days=290), end)
        r = _get(s, "https://api.exchange.coinbase.com/products/BTC-USD/candles",
                 params={"granularity": 86400, "start": f"{cur}T00:00:00Z", "end": f"{stop}T23:59:59Z"})
        for t, _low, _high, _open, close, _vol in r.json():
            d = datetime.fromtimestamp(t, tz=timezone.utc).date()
            if d < today_utc:
                pts[d] = float(close)
        cur = stop + timedelta(days=1)
        time.sleep(1)
    return {"bitcoin": sorted(pts.items())}


# --------------------------------------------------------------------- Notícias Agrícolas
NA = "https://www.noticiasagricolas.com.br/cotacoes"
NA_CEPEA = {
    "boi_gordo_sp": f"{NA}/boi-gordo/boi-gordo-indicador-esalq-bmf",
    "bezerro_ms": f"{NA}/boi-gordo/indicador-bezerro-esalq-bmf-bovespa-ms",
    "soja_paranagua": f"{NA}/soja/soja-indicador-cepea-esalq-porto-paranagua",
    "milho_cepea": f"{NA}/milho/indicador-cepea-esalq-milho",
}
NA_SCOT = f"{NA}/boi-gordo/boi-gordo-scot-consultoria"
SCOT_ROWS = {"GO Reg. Sul": "boi_comum_go_sul", "TO Sul": "boi_comum_to_sul"}

_TABLE = re.compile(r'<table class="cot-fisicas">(.*?)</table>', re.S)
_TD = re.compile(r"<td[^>]*>(.*?)</td>", re.S)
_TH = re.compile(r"<th[^>]*>(.*?)</th>", re.S)
_TAG = re.compile(r"<[^>]+>")


def _clean(x: str) -> str:
    return re.sub(r"\s+", " ", _TAG.sub("", x)).strip()


def parse_na_closes(html: str) -> Points:
    """Tabelas 'cot-fisicas' com cabeçalho Data | Valor: devolve (data, valor)."""
    out: Points = []
    for t in _TABLE.findall(html):
        heads = [_clean(h) for h in _TH.findall(t)]
        if not heads or heads[0] != "Data":
            continue
        cells = [_clean(c) for c in _TD.findall(t)]
        for i in range(0, len(cells) - 1, len(heads)):
            if re.fullmatch(r"\d{2}/\d{2}/\d{4}", cells[i]):
                out.append((datetime.strptime(cells[i], "%d/%m/%Y").date(), br_number(cells[i + 1])))
    return out


def parse_na_scot(html: str) -> tuple[date, dict[str, float]]:
    """Tabela da Scot (Município | à vista | 30 dias | vaca). Devolve data de
    fechamento e preço bruto à vista para as praças de interesse."""
    idx = html.find("Município")
    if idx < 0:
        raise RuntimeError("tabela da Scot não encontrada")
    fech = re.findall(r"Fechamento:\s*(\d{2}/\d{2}/\d{4})", html[:idx])
    if not fech:
        raise RuntimeError("data de fechamento da Scot não encontrada")
    ref = datetime.strptime(fech[-1], "%d/%m/%Y").date()
    start = html.rfind("<table", 0, idx)
    table = html[start: html.find("</table>", idx)]
    header = _clean(table[: table.find("</tr>")])
    if "à vista" not in header:
        raise RuntimeError(f"cabeçalho inesperado na tabela da Scot: {header[:120]}")
    vals: dict[str, float] = {}
    for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", table, re.S):
        cells = [_clean(c) for c in _TD.findall(tr)]
        if len(cells) >= 2 and cells[0] in SCOT_ROWS:
            vals[SCOT_ROWS[cells[0]]] = br_number(cells[1])
    missing = set(SCOT_ROWS.values()) - set(vals)
    if missing:
        raise RuntimeError(f"praças ausentes na tabela da Scot: {sorted(missing)}")
    return ref, vals


def na_cepea_recent() -> dict[str, Points]:
    s = _session()
    out: dict[str, Points] = {}
    for ind, url in NA_CEPEA.items():
        out[ind] = parse_na_closes(_get(s, url).text)
        time.sleep(1.5)
    return out


def na_cepea_backfill(start: date, end: date, only: list[str] | None = None,
                      log: Callable[[str], None] = print) -> dict[str, Points]:
    """Uma consulta por dia útil por indicador (página por data)."""
    s = _session()
    out: dict[str, Points] = {k: [] for k in NA_CEPEA if not only or k in only}
    days = [start + timedelta(n) for n in range((end - start).days + 1)]
    days = [d for d in days if d.weekday() < 5]
    for ind in out:
        for n, d in enumerate(days):
            try:
                pts = parse_na_closes(_get(s, f"{NA_CEPEA[ind]}/{d.isoformat()}").text)
                out[ind].extend(p for p in pts if p[0] == d)
            except Exception as exc:  # noqa: BLE001
                log(f"[backfill] {ind} {d}: {exc}")
            if n % 50 == 0:
                log(f"[backfill] {ind}: {n}/{len(days)}")
            time.sleep(1.0)
    return out


def na_scot_today() -> dict[str, Points]:
    s = _session()
    ref, vals = parse_na_scot(_get(s, NA_SCOT).text)
    return {k: [(ref, v)] for k, v in vals.items()}
