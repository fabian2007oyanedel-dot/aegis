@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"
title Aegis Browser

echo ==============================================================================
echo                      INICIANDO AEGIS BROWSER v1.3.5
echo            (Navegador Nativo con Chromium Engine y Rust Shields)
echo ==============================================================================
echo.

set "COMPILED_EXE=%~dp0dist\Aegis\Aegis.exe"
set "PYTHON_EXE=C:\Users\PC\AppData\Local\Python\bin\python.exe"
set "PYTHONW_EXE=C:\Users\PC\AppData\Local\Python\bin\pythonw.exe"
set "APP_SCRIPT=%~dp0src\desktop\aegis_app.py"

if exist "%COMPILED_EXE%" (
    echo [OK] Iniciando binario nativo compilado Aegis.exe...
    start "" /D "%~dp0dist\Aegis" "%COMPILED_EXE%"
    exit /b 0
)

if exist "%PYTHONW_EXE%" (
    echo [OK] Iniciando Aegis Browser via PythonW...
    start "" "%PYTHONW_EXE%" "%APP_SCRIPT%"
    exit /b 0
)

if exist "%PYTHON_EXE%" (
    echo [OK] Iniciando Aegis Browser via Python...
    start "" "%PYTHON_EXE%" "%APP_SCRIPT%"
    exit /b 0
)

where python >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo [OK] Iniciando Aegis Browser via comando python del sistema...
    start "" python "%APP_SCRIPT%"
    exit /b 0
)

echo.
echo [ERROR] No se pudo encontrar Aegis.exe ni un entorno de Python valido.
echo Verifica que el proyecto este compilado en dist\Aegis o ejecuta scripts\phase0_bootstrap.ps1.
echo.
pause
exit /b 1
