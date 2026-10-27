# ==============================================================================
# Aegis Browser - Lanzador de Aplicación Nativa (PowerShell)
# ==============================================================================

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$AppScript = Join-Path $ScriptDir "aegis.py"

Write-Host "[>] Iniciando Aegis Browser (Codigo fuente en vivo)..." -ForegroundColor Cyan

if (Get-Command py.exe -ErrorAction SilentlyContinue) {
    Start-Process py.exe -ArgumentList "-3 `"$AppScript`"" -WorkingDirectory $ScriptDir
    Write-Host "[OK] Aegis Browser ejecutandose." -ForegroundColor Green
    exit 0
}

if (Get-Command pythonw.exe -ErrorAction SilentlyContinue) {
    Start-Process pythonw.exe -ArgumentList "`"$AppScript`"" -WorkingDirectory $ScriptDir
    Write-Host "[OK] Aegis Browser ejecutandose." -ForegroundColor Green
    exit 0
}

if (Get-Command python.exe -ErrorAction SilentlyContinue) {
    Start-Process python.exe -ArgumentList "`"$AppScript`"" -WorkingDirectory $ScriptDir
    Write-Host "[OK] Aegis Browser ejecutandose." -ForegroundColor Green
    exit 0
}

$CompiledExe = Join-Path $ScriptDir "dist\Aegis\Aegis.exe"
if (Test-Path $CompiledExe) {
    Start-Process $CompiledExe -WorkingDirectory (Split-Path -Parent $CompiledExe)
    exit 0
}
