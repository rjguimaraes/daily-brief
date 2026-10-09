"""Cálculo dos comparativos do Painel. Funções puras, cobertas por testes.

Regras (documentadas no plano aprovado):
- "Atual" = última observação com data <= data de referência da edição.
- Comparativos ancorados na data da observação atual:
    1 mês  = última observação <= (data atual − 1 mês)
    YTD    = última observação <= 31/12 do ano anterior
    1 ano  = última observação <= (data atual − 12 meses)
  Nunca se olha para frente. Se a observação de referência estiver mais de
  MAX_GAP_DIAS antes da data-alvo, o comparativo fica ausente (com motivo).
- Preços e relações: variação % = (atual / referência − 1) × 100.
- Taxas: variação em pontos-base = (atual − referência) × 100.
"""
from __future__ import annotations

import bisect
import calendar
from datetime import date

MAX_GAP_DIAS = 7


def minus_months(d: date, n: int) -> date:
    """Mesma data n meses antes; se o dia não existir, usa o último dia do mês."""
    y, m = d.year, d.month - n
    while m <= 0:
        m += 12
        y -= 1
    last = calendar.monthrange(y, m)[1]
    return date(y, m, min(d.day, last))


def as_of(dates_sorted: list[date], target: date) -> date | None:
    """Última data <= target numa lista ordenada."""
    i = bisect.bisect_right(dates_sorted, target)
    return dates_sorted[i - 1] if i else None


def pct_change(cur: float, ref: float) -> float:
    if ref == 0:
        raise ZeroDivisionError("referência zero")
    return (cur / ref - 1.0) * 100.0


def bp_change(cur: float, ref: float) -> float:
    return (cur - ref) * 100.0


def change(kind: str, cur: float, ref: float) -> float:
    if kind == "taxa":
        return bp_change(cur, ref)
    if kind in ("preco", "relacao"):
        return pct_change(cur, ref)
    raise ValueError(f"tipo desconhecido: {kind}")


def comparison_targets(cur_date: date) -> dict[str, date]:
    return {
        "m1": minus_months(cur_date, 1),
        "ytd": date(cur_date.year - 1, 12, 31),
        "y1": minus_months(cur_date, 12),
    }


def compute_row(series: dict[date, float], kind: str, ref_date: date, max_age_days: int) -> dict:
    """Calcula atual + 3 comparativos para uma série {data: valor}.

    Retorna dicionário com valores, datas usadas e motivos de ausência.
    """
    dates = sorted(series)
    cur_d = as_of(dates, ref_date)
    if cur_d is None:
        return {"status": "ausente", "motivo": "série sem observações até a data de referência"}
    cur_v = series[cur_d]
    age = (ref_date - cur_d).days
    row = {
        "status": "defasado" if age > max_age_days else "ok",
        "atual": {"data": cur_d.isoformat(), "valor": cur_v, "idade_dias": age},
    }
    for key, target in comparison_targets(cur_d).items():
        ref_d = as_of(dates, target)
        if ref_d is None:
            row[key] = {"alvo": target.isoformat(), "motivo": f"histórico começa em {dates[0].isoformat()}"}
            continue
        gap = (target - ref_d).days
        if gap > MAX_GAP_DIAS:
            row[key] = {"alvo": target.isoformat(),
                        "motivo": f"sem observação nos {MAX_GAP_DIAS} dias anteriores a {target.isoformat()}"}
            continue
        ref_v = series[ref_d]
        row[key] = {
            "alvo": target.isoformat(),
            "data_ref": ref_d.isoformat(),
            "valor_ref": ref_v,
            "variacao": change(kind, cur_v, ref_v),
            "unidade_variacao": "pb" if kind == "taxa" else "%",
        }
    return row


def ratio_series(num: dict[date, float], den: dict[date, float]) -> dict[date, float]:
    """Relação num/den apenas nas datas em que ambas existem (mesma data)."""
    return {d: num[d] / den[d] for d in sorted(set(num) & set(den)) if den[d]}


def daily_jumps(series: dict[date, float], limit_pct: float, since: date) -> list[dict]:
    """Variações entre observações consecutivas acima do limite, a partir de `since`."""
    out = []
    ds = sorted(series)
    for a, b in zip(ds, ds[1:]):
        if b < since or series[a] == 0:
            continue
        v = pct_change(series[b], series[a])
        if abs(v) > limit_pct:
            out.append({"de": a.isoformat(), "para": b.isoformat(), "variacao_pct": round(v, 2)})
    return out
