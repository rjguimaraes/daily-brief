# Daily Brief - instalacao da coleta do agro no notebook (rodar uma vez, no PowerShell como administrador)
# 1) guarda o token do GitHub criptografado para o seu usuario do Windows
# 2) copia coletar_agro.ps1 para %LOCALAPPDATA%\DailyBrief
# 3) cria a tarefa "Daily Brief - agro": ao fazer logon (2 min depois) e todo dia as 19h30
# 4) roda a primeira coleta
$ErrorActionPreference = 'Stop'
$State = Join-Path $env:LOCALAPPDATA 'DailyBrief'
New-Item -ItemType Directory -Force -Path $State | Out-Null

$tok = Read-Host 'Cole o token do GitHub (nao aparece na tela)' -AsSecureString
$tok | ConvertFrom-SecureString | Set-Content (Join-Path $State 'token.txt')

$src = Join-Path $PSScriptRoot 'coletar_agro.ps1'
$dst = Join-Path $State 'coletar_agro.ps1'
Copy-Item $src $dst -Force

$action  = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$dst`""
$tLogon  = New-ScheduledTaskTrigger -AtLogOn -User "$env:USERDOMAIN\$env:USERNAME"
$tLogon.Delay = 'PT2M'
$tNoite  = New-ScheduledTaskTrigger -Daily -At '19:30'
$set     = New-ScheduledTaskSettingsSet -StartWhenAvailable -RunOnlyIfNetworkAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit (New-TimeSpan -Minutes 20)
$princ   = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive -RunLevel Limited
Register-ScheduledTask -TaskName 'Daily Brief - agro' -Action $action -Trigger $tLogon, $tNoite -Settings $set -Principal $princ `
  -Description 'Baixa os precos do agro (CEPEA/Scot/Datagro) e atualiza o painel do Daily Brief' -Force | Out-Null
Write-Host 'Tarefa "Daily Brief - agro" criada.'

Write-Host 'Rodando a primeira coleta...'
& powershell.exe -NoProfile -ExecutionPolicy Bypass -File $dst -Forcar
Write-Host "Pronto. Log: $State\log.txt"
