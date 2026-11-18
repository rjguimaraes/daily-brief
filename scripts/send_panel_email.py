"""Envia o painel atualizado por e-mail (PDF em tema escuro) depois de uma coleta do agro
feita pelo notebook do leitor. Pedido do leitor em 18/11/2026 (opção A: só o painel).

Uso: python scripts/send_panel_email.py [--dry-run]
Lê output/panel.md, output/panel.json e output/collect_report.json.
Só envia se a coleta "Agro via notebook" trouxe ao menos um ponto novo ou revisado.
Segredos (GitHub Actions): GMAIL_USER, GMAIL_APP_PASSWORD; destino opcional PANEL_EMAIL_TO.
"""
from __future__ import annotations

import json
import os
import smtplib
import sys
from datetime import datetime
from email.message import EmailMessage
from pathlib import Path
from zoneinfo import ZoneInfo

import markdown

sys.path.insert(0, str(Path(__file__).parent))
import dark_pdf  # noqa: E402

OUT = Path("output")
TZ = ZoneInfo("America/Sao_Paulo")
AGRO = ["boi_gordo_sp", "boi_comum_go_sul", "boi_comum_to_sul", "bezerro_ms", "bezerro_to",
        "rel_bezerro_boi_to", "rel_troca_cepea", "soja_paranagua", "milho_cepea"]


def main() -> None:
    dry = "--dry-run" in sys.argv
    report = json.loads((OUT / "collect_report.json").read_text(encoding="utf-8"))
    agro = report.get("Agro via notebook")
    if not agro:
        print("sem coleta do notebook nesta execução; nada a enviar")
        return
    if not agro.get("ok"):
        print(f"coleta do notebook falhou: {agro.get('erro')}; nada a enviar")
        return
    novos = sum(s["novos"] + len(s["revisados"]) for s in agro["series"].values())
    if novos == 0:
        print("coleta do notebook sem pontos novos; nada a enviar")
        return

    now = datetime.now(TZ)
    title = f"Painel atualizado — {now:%d/%m/%Y}"
    rows = {r["id"]: r for r in json.loads((OUT / "panel.json").read_text(encoding="utf-8")) if "id" in r}
    linhas = []
    for ind in AGRO:
        r = rows.get(ind)
        if r and r.get("atual"):
            d = datetime.fromisoformat(r["atual"]["data"]).strftime("%d/%m")
            linhas.append(f"- {r.get('nome', ind)}: {d}")

    md = (OUT / "panel.md").read_text(encoding="utf-8")
    body_html = markdown.markdown(md, extensions=["tables"])
    frag = (f"<h1>{title}</h1><p class=\"byline\">{now:%d/%m/%Y %H:%M} · coleta do agro pelo notebook "
            f"({novos} pontos novos)</p>{body_html}")
    src = OUT / "panel_email.html"
    pdf = OUT / f"painel-{now:%Y-%m-%d}.pdf"
    src.write_text(frag, encoding="utf-8")
    dark_pdf.main(str(src), str(pdf), title)
    print(f"PDF gerado: {pdf} ({pdf.stat().st_size} bytes)")

    msg = EmailMessage()
    user = os.environ.get("GMAIL_USER", "")
    msg["From"] = user
    msg["To"] = os.environ.get("PANEL_EMAIL_TO") or user
    msg["Subject"] = title
    msg.set_content(
        "Os preços do agro foram atualizados pela coleta do notebook.\n\n"
        "Data mais recente de cada indicador do agro:\n" + "\n".join(linhas) +
        "\n\nO painel completo vai em PDF. A Daily de amanhã já sai com estes números.\n")
    msg.add_attachment(pdf.read_bytes(), maintype="application", subtype="pdf", filename=pdf.name)
    if dry:
        print(msg["Subject"], "→", msg["To"]); print(msg.get_body().get_content())
        return
    if not user or not os.environ.get("GMAIL_APP_PASSWORD"):
        raise SystemExit("faltam os segredos GMAIL_USER / GMAIL_APP_PASSWORD")
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=60) as s:
        s.login(user, os.environ["GMAIL_APP_PASSWORD"])
        s.send_message(msg)
    print(f"e-mail enviado para {msg['To']}")


if __name__ == "__main__":
    main()
