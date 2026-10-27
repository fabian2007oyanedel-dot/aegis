@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

where pyw >nul 2>&1
if %ERRORLEVEL% equ 0 (
    start "" pyw -3 "%~dp0aegis.pyw"
    exit /b 0
)

where pythonw >nul 2>&1
if %ERRORLEVEL% equ 0 (
    start "" pythonw "%~dp0aegis.pyw"
    exit /b 0
)

set "PYTHONW_LOCAL=C:\Users\PC\AppData\Local\Python\pythoncore-3.14-64\pythonw.exe"
if exist "%PYTHONW_LOCAL%" (
    start "" "%PYTHONW_LOCAL%" "%~dp0aegis.pyw"
    exit /b 0
)

start "" py -3 "%~dp0aegis.pyw"
exit /b 0
