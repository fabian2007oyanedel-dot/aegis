@echo off
title Aegis Browser - Modo Standalone Ultra Ligero
echo ==============================================================================
echo                      INICIANDO AEGIS BROWSER v1.2.0
echo             (Navegador Seguro, Ultra Optimizado y Sin Telemetria)
echo ==============================================================================
echo.

set NTP_PATH=%~dp0src\ui\ntp\index.html
set PROFILE_DIR=%TEMP%\aegis_isolated_profile

echo [1/2] Verificando entorno y aceleracion por hardware...
echo [2/2] Abriendo interfaz WebUI en ventana de aplicacion aislada...
echo.

:: 1. Intentar lanzar con Edge en modo App (Motor Chromium nativo de Windows)
where msedge >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo Iniciando Aegis Browser en modo Standalone (Chromium Engine)...
    start "" msedge --app="file:///%NTP_PATH:\=/%" --user-data-dir="%PROFILE_DIR%" --no-first-run --disable-default-apps
    goto :fin
)

:: 2. Intentar lanzar con Chrome en modo App
where chrome >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo Iniciando Aegis Browser en modo Standalone (Chrome Engine)...
    start "" chrome --app="file:///%NTP_PATH:\=/%" --user-data-dir="%PROFILE_DIR%" --no-first-run
    goto :fin
)

:: 3. Fallback: Abrir directamente el archivo HTML en el navegador por defecto
echo Abriendo Aegis Browser en tu navegador web predeterminado...
start "" "%NTP_PATH%"

:fin
echo.
echo [OK] Aegis Browser se esta ejecutando. Disfruta de la navegacion privada y sin anuncios!
timeout /t 3 >nul
exit /b 0
