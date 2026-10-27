@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"
title Aegis Browser

echo ==============================================================================
echo                      INICIANDO AEGIS BROWSER v1.3.5
echo            (Navegador Nativo con Chromium Engine y Rust Shields)
echo ==============================================================================
echo.

where py >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo [OK] Iniciando Aegis Browser en vivo desde codigo fuente (py -3)...
    start "" py -3 "%~dp0aegis.py"
    exit /b 0
)

where pythonw >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo [OK] Iniciando Aegis Browser en vivo via pythonw...
    start "" pythonw "%~dp0aegis.py"
    exit /b 0
)

where python >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo [OK] Iniciando Aegis Browser en vivo via python...
    start "" python "%~dp0aegis.py"
    exit /b 0
)

set "COMPILED_EXE=%~dp0dist\Aegis\Aegis.exe"
if exist "%COMPILED_EXE%" (
    echo [OK] Iniciando binario compilado Aegis.exe...
    start "" /D "%~dp0dist\Aegis" "%COMPILED_EXE%"
    exit /b 0
)

echo.
echo [ERROR] No se pudo encontrar un interprete de Python valido.
echo.
pause
exit /b 1
