"""Gera o PDF da edição em tema escuro (fundo #191919, texto #efefef, como o Claude em modo escuro).

Uso: python scripts/dark_pdf.py <export.html> <saida.pdf> [titulo]
Entrada: o HTML exportado pelo Claude Docs (export, format html; vem em data.bytes_b64, decodificado).
Pedido do leitor em 17/11/2026: PDF em fundo escuro com letras brancas, no tema do Claude.
"""
import re
import sys

from playwright.sync_api import sync_playwright

CSS = """
@page { size: A4; margin: 16mm 14mm; background: #191919; }
html, body { background: #191919; }
body { color: #efefef; font-family: "Inter", "Segoe UI", "Helvetica Neue", Arial, sans-serif;
       font-size: 10.5pt; line-height: 1.55; margin: 0; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
h1 { font-family: Georgia, "Times New Roman", serif; font-weight: 500; font-size: 22pt; margin: 0 0 4pt; color: #ffffff; }
h2 { font-family: Georgia, "Times New Roman", serif; font-weight: 500; font-size: 15pt; color: #ffffff;
     border-bottom: 1px solid #3a3a3a; padding-bottom: 4pt; margin: 22pt 0 8pt; break-after: avoid; }
h3 { font-size: 12pt; color: #ffffff; margin: 14pt 0 4pt; break-after: avoid; }
p { margin: 0 0 7pt; }
a { color: #e08a6b; text-decoration: none; }
strong { color: #ffffff; }
em { color: #d6d6d6; }
blockquote { background: #232323; border-left: 3px solid #d97757; margin: 10pt 0; padding: 8pt 12pt; border-radius: 4pt; }
ul, ol { margin: 0 0 7pt; padding-left: 18pt; }
li > p { margin: 0 0 3pt; }
table { border-collapse: collapse; width: 100%; font-size: 8.3pt; margin: 6pt 0 10pt; }
th, td { border: 1px solid #3a3a3a; padding: 4pt 5pt; vertical-align: top; text-align: left; }
th { background: #2b2b2b; color: #ffffff; }
tr:nth-child(even) td { background: #1f1f1f; }
tr { break-inside: avoid; }
td p, th p { margin: 0; }
code { background: #303030; padding: 0 3pt; border-radius: 3pt; }
.byline { color: #9a9a9a; font-size: 9.5pt; margin-bottom: 12pt; }
"""


def main(src, out, title="Daily Brief"):
    html = open(src, encoding="utf-8").read()
    # byline: data em dd/mm/aaaa e autor legível
    html = re.sub(r'<time[^>]*datetime="(\d{4})-(\d{2})-(\d{2})"[^>]*>.*?</time>',
                  lambda m: f"{m.group(3)}/{m.group(2)}/{m.group(1)}", html, count=1)
    html = re.sub(r'<span data-atom="mention"[^>]*>.*?</span>', "Rafael", html)
    html = html.replace("<p>" + re.search(r"\d{2}/\d{2}/\d{4} · Rafael", html).group(0),
                        '<p class="byline">' + re.search(r"\d{2}/\d{2}/\d{4} · Rafael", html).group(0), 1) \
        if re.search(r"\d{2}/\d{2}/\d{4} · Rafael", html) else html
    page = (f'<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><title>{title}</title>'
            f"<style>{CSS}</style></head><body>{html}</body></html>")
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page()
        pg.set_content(page, wait_until="load")
        pg.pdf(path=out, format="A4", print_background=True, prefer_css_page_size=True)
        b.close()


if __name__ == "__main__":
    main(*sys.argv[1:])
