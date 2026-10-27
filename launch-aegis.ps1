# ==============================================================================
# Aegis Browser - Lanzador GUI Nativo (PowerShell)
# ==============================================================================

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$AppScript = Join-Path $ScriptDir "aegis.pyw"

if (Get-Command pyw.exe -ErrorAction SilentlyContinue) {
    Start-Process pyw.exe -ArgumentList "-3 `"$AppScript`"" -WorkingDirectory $ScriptDir
    exit 0
}

if (Get-Command pythonw.exe -ErrorAction SilentlyContinue) {
    Start-Process pythonw.exe -ArgumentList "`"$AppScript`"" -WorkingDirectory $ScriptDir
    exit 0
}

$PythonWLocal = "C:\Users\PC\AppData\Local\Python\pythoncore-3.14-64\pythonw.exe"
if (Test-Path $PythonWLocal) {
    Start-Process $PythonWLocal -ArgumentList "`"$AppScript`"" -WorkingDirectory $ScriptDir
    exit 0
}

Start-Process py.exe -ArgumentList "-3 `"$AppScript`"" -WorkingDirectory $ScriptDir
exit 0
