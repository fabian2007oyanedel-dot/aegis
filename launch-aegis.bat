@echo off
setlocal
cd /d "%~dp0"
title Aegis Browser

echo ==============================================================================
echo                      INICIANDO AEGIS BROWSER v1.3.0
echo            (Navegador Nativo con Chromium Engine y Rust Shields)
echo ==============================================================================
echo.

:: 1. Prioridad: Ejecutable nativo en dist\Aegis (con directorio de trabajo correcto)
if exist "%~dp0dist\Aegis\Aegis.exe" (
    echo [OK] Iniciando Aegis.exe desde dist\Aegis...
    start "" /D "%~dp0dist\Aegis" "%~dp0dist\Aegis\Aegis.exe"
    exit /b 0
)

:: 2. Respaldo: Lanzar vía PythonW
set "PYTHON_EXE=C:\Users\PC\AppData\Local\Python\bin\pythonw.exe"
if exist "%PYTHON_EXE%" (
    echo [OK] Iniciando Aegis Browser (PythonW)...
    start "" "%PYTHON_EXE%" "%~dp0src\desktop\aegis_app.py"
    exit /b 0
)

:: 3. Respaldo: Lanzar vía Python estándar
where python >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo [OK] Iniciando Aegis Browser...
    start "" python "%~dp0src\desktop\aegis_app.py"
    exit /b 0
)

echo [ERROR] No se pudo iniciar el navegador.
pause
exit /b 1
