"""Gera o PDF do painel (tema escuro) depois de uma coleta do agro feita pelo notebook do
leitor, e o marcador output/agro_update.json. Uma tarefa agendada do Claude (~20h) lê o
marcador e, se for do dia e ainda não enviado, manda o PDF pelo Gmail conectado.
Pedido do leitor em 18/11/2026 (opção A: só o painel; sem senha de app do Gmail).

Uso: python scripts/make_panel_pdf.py
Lê output/panel.md, output/panel.json e output/collect_report.json.
Só gera se a coleta "Agro via notebook" trouxe ao menos um ponto novo ou revisado.
Saídas: output/painel_agro.pdf, output/agro_update.json
"""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import markdown

sys.path.insert(0, str(Path(__file__).parent))
import dark_pdf  # noqa: E402

OUT = Path("output")
TZ = ZoneInfo("America/Sao_Paulo")
AGRO = ["boi_gordo_sp", "boi_comum_go_sul", "boi_comum_to_sul", "bezerro_ms", "bezerro_to",
        "rel_bezerro_boi_to", "rel_troca_cepea", "soja_paranagua", "milho_cepea", "brent_futuro"]


def main() -> None:
    report = json.loads((OUT / "collect_report.json").read_text(encoding="utf-8"))
    agro = report.get("Agro via notebook")
    if not agro or not agro.get("ok"):
        print(f"sem coleta válida do notebook nesta execução ({(agro or {}).get('erro', 'ausente')}); nada a gerar")
        return
    novos = sum(s["novos"] + len(s["revisados"]) for s in agro["series"].values())
    if novos == 0:
        print("coleta do notebook sem pontos novos; nada a gerar")
        return

    now = datetime.now(TZ)
    title = f"Painel atualizado — {now:%d/%m/%Y}"
    rows = {r["id"]: r for r in json.loads((OUT / "panel.json").read_text(encoding="utf-8")) if "id" in r}
    datas = {}
    for ind in AGRO:
        r = rows.get(ind)
        if r and r.get("atual"):
            datas[r.get("nome", ind)] = datetime.fromisoformat(r["atual"]["data"]).strftime("%d/%m")

    md = (OUT / "panel.md").read_text(encoding="utf-8")
    body_html = markdown.markdown(md, extensions=["tables"])
    frag = (f"<h1>{title}</h1><p class=\"byline\">{now:%d/%m/%Y %H:%M} · coleta do agro pelo notebook "
            f"({novos} pontos novos)</p>{body_html}")
    src = OUT / "panel_email.html"
    pdf = OUT / "painel_agro.pdf"
    src.write_text(frag, encoding="utf-8")
    dark_pdf.main(str(src), str(pdf), title)
    src.unlink()
    marker = {"data_brt": now.date().isoformat(), "gerado_em": now.isoformat(timespec="minutes"),
              "titulo": title, "novos": novos, "datas_agro": datas, "pdf": str(pdf), "email_enviado": False}
    (OUT / "agro_update.json").write_text(json.dumps(marker, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"PDF gerado: {pdf} ({pdf.stat().st_size} bytes); marcador atualizado")


if __name__ == "__main__":
    main()
