# Coleta do agro pelo notebook (Windows)

Desde 13/11/2026 o Notícias Agrícolas (e o site do CEPEA) recusam acesso vindo do GitHub Actions (403).
O notebook baixa as páginas pela internet de casa e o painel é recalculado na nuvem com os mesmos parsers.

Fluxo: logon (ou 19h30, se ligado) → `coletar_agro.ps1` baixa CEPEA (boi SP, bezerro MS, soja, milho),
Datagro (bezerro TO), Scot (GO/TO) e, desde 25/11/2026, o Brent futuro (Yahoo Finance, BZ=F, 2 anos de
fechamentos diários; no Actions o Yahoo responde 429) → envia `data/agro_inbox/agro_<data>.zip` → dispara `panel.yml`
com `agro_inbox` → o workflow lê o pacote, recalcula, apaga o pacote, faz commit e, se houver ponto novo,
gera output/painel_agro.pdf e output/agro_update.json.
Uma tarefa agendada do Claude (por volta das 20h20) manda esse PDF pelo Gmail conectado, se for do dia.

Recupera dias perdidos (até 45 dias) para CEPEA e Datagro; a Scot só tem o fechamento mais recente.

## Instalação (uma vez)
1. Token do GitHub (fine-grained): github.com → Settings → Developer settings → Fine-grained tokens →
   Generate new token. Repository access: só `rjguimaraes/daily-brief`. Permissions: Contents = Read and write,
   Actions = Read and write. Validade: 1 ano.
2. No notebook, baixe os dois .ps1 para a mesma pasta (Downloads serve), abra o PowerShell como administrador nela e rode:
   `powershell -ExecutionPolicy Bypass -File .\instalar.ps1` (cola o token quando pedir).

Log: `%LOCALAPPDATA%\DailyBrief\log.txt`. Forçar uma coleta: rodar `coletar_agro.ps1 -Forcar`.

## Atualizar o script no notebook (quando o coletar_agro.ps1 mudar no repositório)
A tarefa agendada roda a cópia em `%LOCALAPPDATA%\DailyBrief`, não a do repositório. Baixe o
`coletar_agro.ps1` novo do GitHub para Downloads e, no PowerShell (não precisa ser administrador):
```
Copy-Item "$env:USERPROFILE\Downloads\coletar_agro.ps1" "$env:LOCALAPPDATA\DailyBrief\coletar_agro.ps1" -Force
Unblock-File "$env:LOCALAPPDATA\DailyBrief\coletar_agro.ps1"
powershell -NoProfile -ExecutionPolicy Bypass -File "$env:LOCALAPPDATA\DailyBrief\coletar_agro.ps1" -Forcar
```
O log deve mostrar "brent futuro baixado". O token e a tarefa agendada continuam os mesmos.
