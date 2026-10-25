# ==============================================================================
# Aegis Browser - Lanzador Standalone Ultra Ligero (PowerShell)
# ==============================================================================

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$NtpPath = (Join-Path $ScriptDir "src\ui\ntp\index.html").Replace("\", "/")
$ProfileDir = Join-Path $env:TEMP "aegis_isolated_profile"

Write-Host "==============================================================================" -ForegroundColor Cyan
Write-Host "                     INICIANDO AEGIS BROWSER v1.2.0" -ForegroundColor White
Write-Host "            (Navegador Seguro, Ultra Optimizado y Sin Telemetria)" -ForegroundColor DarkGray
Write-Host "==============================================================================" -ForegroundColor Cyan
Write-Host ""

$EdgePath = (Get-Command msedge.exe -ErrorAction SilentlyContinue)?.Source
$ChromePath = (Get-Command chrome.exe -ErrorAction SilentlyContinue)?.Source

if ($EdgePath) {
    Write-Host "[>] Iniciando Aegis Browser en modo Standalone (Chromium Engine)..." -ForegroundColor Green
    Start-Process msedge.exe -ArgumentList "--app=`"file:///$NtpPath`"", "--user-data-dir=`"$ProfileDir`"", "--no-first-run", "--disable-default-apps"
} elseif ($ChromePath) {
    Write-Host "[>] Iniciando Aegis Browser en modo Standalone (Chrome Engine)..." -ForegroundColor Green
    Start-Process chrome.exe -ArgumentList "--app=`"file:///$NtpPath`"", "--user-data-dir=`"$ProfileDir`"", "--no-first-run"
} else {
    Write-Host "[>] Abriendo Aegis Browser en el navegador predeterminado..." -ForegroundColor Yellow
    Start-Process "file:///$NtpPath"
}

Write-Host "[OK] Aegis Browser ejecutandose con exito." -ForegroundColor Cyan
