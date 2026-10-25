# ==============================================================================
# Aegis Browser - Lanzador de Aplicación Nativa (PowerShell)
# ==============================================================================

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$AppScript = Join-Path $ScriptDir "src\desktop\aegis_app.py"
$PythonExe = "C:\Users\PC\AppData\Local\Python\bin\pythonw.exe"

if (-not (Test-Path $PythonExe)) {
    $PythonExe = (Get-Command pythonw.exe -ErrorAction SilentlyContinue)?.Source
    if (-not $PythonExe) {
        $PythonExe = "C:\Users\PC\AppData\Local\Python\bin\python.exe"
    }
}

Write-Host "[>] Iniciando Aegis Browser Nativo (Chromium + Rust Shields)..." -ForegroundColor Cyan
Start-Process $PythonExe -ArgumentList "`"$AppScript`"" -WorkingDirectory $ScriptDir
Write-Host "[OK] Aegis Browser ejecutandose." -ForegroundColor Green
