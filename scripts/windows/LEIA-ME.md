# Coleta do agro pelo notebook (Windows)

Desde 13/11/2026 o Notícias Agrícolas (e o site do CEPEA) recusam acesso vindo do GitHub Actions (403).
O notebook baixa as páginas pela internet de casa e o painel é recalculado na nuvem com os mesmos parsers.

Fluxo: logon (ou 19h30, se ligado) → `coletar_agro.ps1` baixa CEPEA (boi SP, bezerro MS, soja, milho),
Datagro (bezerro TO) e Scot (GO/TO) → envia `data/agro_inbox/agro_<data>.zip` → dispara `panel.yml`
com `agro_inbox` → o workflow lê o pacote, recalcula, apaga o pacote, faz commit e, se houver ponto novo,
manda o painel em PDF (tema escuro) por e-mail.

Recupera dias perdidos (até 45 dias) para CEPEA e Datagro; a Scot só tem o fechamento mais recente.

## Instalação (uma vez)
1. Token do GitHub (fine-grained): github.com → Settings → Developer settings → Fine-grained tokens →
   Generate new token. Repository access: só `rjguimaraes/daily-brief`. Permissions: Contents = Read and write,
   Actions = Read and write. Validade: 1 ano.
2. Segredos do repositório (Settings → Secrets and variables → Actions → New repository secret):
   `GMAIL_USER` = seu Gmail; `GMAIL_APP_PASSWORD` = senha de app do Google
   (myaccount.google.com/apppasswords; exige verificação em duas etapas). Opcional: `PANEL_EMAIL_TO`.
3. No notebook, baixe esta pasta, abra o PowerShell como administrador nela e rode:
   `powershell -ExecutionPolicy Bypass -File .\instalar.ps1` (cola o token quando pedir).

Log: `%LOCALAPPDATA%\DailyBrief\log.txt`. Forçar uma coleta: rodar `coletar_agro.ps1 -Forcar`.
