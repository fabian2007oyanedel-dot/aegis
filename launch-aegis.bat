@echo off
chcp 65001 >nul
title Aegis Browser

set "HTML_TARGET=%~dp0src\ui\ntp\index.html"
set "HTML_TARGET=%HTML_TARGET:\=/%"
set "APP_URL=file:///%HTML_TARGET%"

echo ==============================================================================
echo                      INICIANDO AEGIS BROWSER v1.3.0
echo             (Navegador Seguro, Ultra Optimizado y Sin Telemetria)
echo ==============================================================================
echo.
echo URL de inicio: %APP_URL%
echo.

:: 1. Probar Microsoft Edge (Ruta estándar de Windows)
if exist "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" (
    echo [OK] Lanzando Aegis Browser en ventana standalone (Edge Chromium Engine)...
    start "" "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" --app="%APP_URL%"
    goto :fin
)

if exist "C:\Program Files\Microsoft\Edge\Application\msedge.exe" (
    echo [OK] Lanzando Aegis Browser en ventana standalone (Edge Chromium Engine)...
    start "" "C:\Program Files\Microsoft\Edge\Application\msedge.exe" --app="%APP_URL%"
    goto :fin
)

:: 2. Probar Google Chrome
if exist "C:\Program Files\Google\Chrome\Application\chrome.exe" (
    echo [OK] Lanzando Aegis Browser en ventana standalone (Chrome Engine)...
    start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --app="%APP_URL%"
    goto :fin
)

if exist "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" (
    echo [OK] Lanzando Aegis Browser en ventana standalone (Chrome Engine)...
    start "" "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" --app="%APP_URL%"
    goto :fin
)

:: 3. Fallback con el explorador de Windows
echo [OK] Abriendo Aegis Browser en el navegador predeterminado de Windows...
start explorer.exe "%APP_URL%"

:fin
echo.
echo Disfruta de la navegacion privada y sin publicidad en Aegis Browser!
timeout /t 2 >nul
exit /b 0
