# Daily Brief - coleta do agro pelo notebook (Windows PowerShell 5.1+)
# Baixa as paginas do Noticias Agricolas (CEPEA, Scot, Datagro) pela internet de casa,
# envia um .zip para data/agro_inbox/ do repositorio e dispara o workflow panel.yml,
# que recalcula o painel e manda o PDF por e-mail se houver dado novo.
# Roda pelo Agendador de Tarefas (ao fazer logon e as 19h30). Log em %LOCALAPPDATA%\DailyBrief\log.txt
param([switch]$Forcar)

$ErrorActionPreference = 'Stop'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$ProgressPreference = 'SilentlyContinue'

$Repo     = 'rjguimaraes/daily-brief'
$State    = Join-Path $env:LOCALAPPDATA 'DailyBrief'
$TokenFile = Join-Path $State 'token.txt'
$LastFile = Join-Path $State 'ultima_coleta.txt'
$Log      = Join-Path $State 'log.txt'
$UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36'
$Base = 'https://www.noticiasagricolas.com.br/cotacoes'
# tipo -> caminho; o nome do tipo precisa bater com AGRO_KINDS em scripts/dbrief/collectors.py
$Pages = [ordered]@{
  'boi_gordo_sp'   = 'boi-gordo/boi-gordo-indicador-esalq-bmf'
  'bezerro_ms'     = 'boi-gordo/indicador-bezerro-esalq-bmf-bovespa-ms'
  'soja_paranagua' = 'soja/soja-indicador-cepea-esalq-porto-paranagua'
  'milho_cepea'    = 'milho/indicador-cepea-esalq-milho'
  'datagro'        = 'boi-gordo/reposicao-nelore-macho'
  'scot'           = 'boi-gordo/boi-gordo-scot-consultoria'
}
$SemHistorico = @('scot')   # a Scot nao tem pagina por data: so o fechamento mais recente

New-Item -ItemType Directory -Force -Path $State | Out-Null
function Log($m) { $l = "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') $m"; Add-Content -Path $Log -Value $l; Write-Host $l }

try {
  if (-not (Test-Path $TokenFile)) { throw "token nao encontrado; rode instalar.ps1" }
  $sec = Get-Content $TokenFile | ConvertTo-SecureString
  $Token = (New-Object System.Net.NetworkCredential('', $sec)).Password
  $Hdr = @{ Authorization = "Bearer $Token"; Accept = 'application/vnd.github+json'; 'X-GitHub-Api-Version' = '2022-11-28' }

  # Evita repetir em logons seguidos: no maximo uma coleta a cada 4 horas.
  $last = $null
  if (Test-Path $LastFile) { $last = [datetime]::ParseExact((Get-Content $LastFile -Raw).Trim(), 'yyyy-MM-dd HH:mm', $null) }
  if (-not $Forcar -and $last -and ((Get-Date) - $last).TotalHours -lt 4) { Log "coleta recente ($last); nada a fazer"; exit 0 }

  # Dias uteis a buscar: desde 3 dias antes da ultima coleta (ou 14 dias), no maximo 45 dias.
  $hoje = (Get-Date).Date
  $inicio = if ($last) { $last.Date.AddDays(-3) } else { $hoje.AddDays(-14) }
  if ($inicio -lt $hoje.AddDays(-45)) { $inicio = $hoje.AddDays(-45) }
  $dias = @()
  for ($d = $inicio; $d -le $hoje; $d = $d.AddDays(1)) { if ($d.DayOfWeek -ne 'Saturday' -and $d.DayOfWeek -ne 'Sunday') { $dias += $d } }

  $tmp = Join-Path $env:TEMP ("agro_" + (Get-Date -Format 'yyyyMMddHHmmss'))
  New-Item -ItemType Directory -Force -Path $tmp | Out-Null
  $ok = 0; $falhas = 0; $bloqueios = 0
  function Baixar($url, $arquivo) {
    try {
      Invoke-WebRequest -Uri $url -OutFile $arquivo -UseBasicParsing -UserAgent $UA -TimeoutSec 60
      $script:ok++
    } catch {
      $code = $null; try { $code = [int]$_.Exception.Response.StatusCode } catch {}
      if ($code -eq 403) { $script:bloqueios++ }
      if ($code -ne 404) { $script:falhas++; Log "falha $code em $url" }
      if (Test-Path $arquivo) { Remove-Item $arquivo -Force }
    }
    Start-Sleep -Milliseconds 800
  }
  foreach ($k in $Pages.Keys) {
    Baixar "$Base/$($Pages[$k])" (Join-Path $tmp "$($k)__recente.html")
    if ($SemHistorico -contains $k) { continue }
    foreach ($d in $dias) {
      $iso = $d.ToString('yyyy-MM-dd')
      Baixar "$Base/$($Pages[$k])/$iso" (Join-Path $tmp "$($k)__$iso.html")
    }
  }
  Log "paginas baixadas: $ok; falhas: $falhas (403: $bloqueios); dias: $($dias.Count)"
  if ($ok -eq 0) { throw "nenhuma pagina baixada (o site bloqueou tambem esta rede?)" }

  $stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
  $zip = Join-Path $env:TEMP "agro_$stamp.zip"
  Compress-Archive -Path (Join-Path $tmp '*') -DestinationPath $zip -Force
  $repoPath = "data/agro_inbox/agro_$stamp.zip"
  $body = @{ message = "Agro via notebook $stamp"; content = [Convert]::ToBase64String([IO.File]::ReadAllBytes($zip)) } | ConvertTo-Json
  Invoke-RestMethod -Method Put -Uri "https://api.github.com/repos/$Repo/contents/$repoPath" -Headers $Hdr -Body $body -ContentType 'application/json' | Out-Null
  Log "pacote enviado: $repoPath ($([math]::Round((Get-Item $zip).Length/1KB)) KB)"

  $disp = @{ ref = 'main'; inputs = @{ agro_inbox = $repoPath } } | ConvertTo-Json
  Invoke-RestMethod -Method Post -Uri "https://api.github.com/repos/$Repo/actions/workflows/panel.yml/dispatches" -Headers $Hdr -Body $disp -ContentType 'application/json' | Out-Null
  Log "workflow panel.yml disparado; o e-mail chega em poucos minutos se houver dado novo"

  Set-Content -Path $LastFile -Value (Get-Date -Format 'yyyy-MM-dd HH:mm')
  Remove-Item $tmp -Recurse -Force; Remove-Item $zip -Force
} catch {
  Log "ERRO: $($_.Exception.Message)"
  exit 1
}
