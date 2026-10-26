# ==============================================================================
# Aegis Browser - Instalador Automatizado de APK para Android (ARM64)
# ==============================================================================
# Soporte directo para:
# - Xiaomi 12 Pro (Snapdragon 8 Gen 1, 120Hz LTPO)
# - Lenovo Xiaoxin Pad 11 Gen 2 (MediaTek Dimensity 6300, ZUI Tablet)
# ==============================================================================

param(
    [string]$ApkPath = ""
)

$ErrorActionPreference = "Stop"

$AdbExe = "C:\Users\PC\AppData\Local\Android\Sdk\platform-tools\adb.exe"
if (-not (Test-Path $AdbExe)) {
    $AdbCmd = Get-Command adb.exe -ErrorAction SilentlyContinue
    if ($AdbCmd) { $AdbExe = $AdbCmd.Source }
}

Write-Host "`n==============================================================" -ForegroundColor Cyan
Write-Host "       AEGIS BROWSER - INSTALADOR DE APK ANDROID (ARM64)" -ForegroundColor Cyan
Write-Host "==============================================================`n" -ForegroundColor Cyan

if (-not (Test-Path $AdbExe)) {
    Write-Host "[ERR] No se encontró adb.exe en el sistema." -ForegroundColor Red
    Write-Host "Instala platform-tools o define la ruta en el script." -ForegroundColor Yellow
    exit 1
}

Write-Host "[>] Verificando dispositivos conectados via ADB..." -ForegroundColor Cyan
$rawDevices = & $AdbExe devices -l
Write-Host $rawDevices

$devices = & $AdbExe devices | Select-String -Pattern "^\s*([a-zA-Z0-9_\:\-]+)\s+device\b"
if (-not $devices) {
    Write-Host "`n[!] No se detectó ningún dispositivo con Depuración USB activa." -ForegroundColor Yellow
    Write-Host "Para conectar tu Xiaomi 12 Pro o Lenovo Xiaoxin Pad 11:" -ForegroundColor Gray
    Write-Host "  1. Conecta el cable USB a la PC." -ForegroundColor Gray
    Write-Host "  2. En el dispositivo ve a: Ajustes -> Información del teléfono -> Toca 7 veces 'Versión de MIUI/HyperOS' o 'Número de compilación'." -ForegroundColor Gray
    Write-Host "  3. Ve a: Ajustes adicionales / Sistema -> Opciones de desarrollador -> Activa 'Depuración USB'." -ForegroundColor Gray
    Write-Host "  4. Acepta el mensaje en la pantalla del teléfono/tablet: '¿Permitir depuración USB de esta computadora?'" -ForegroundColor Gray
    Write-Host "`nTambién puedes copiar el archivo APK directamente a la memoria de tu dispositivo." -ForegroundColor Green
    exit 0
}

foreach ($devLine in $devices) {
    $devId = $devLine.Matches.Groups[1].Value
    Write-Host "`n[+] Dispositivo detectado: $devId" -ForegroundColor Green
    
    $model = (& $AdbExe -s $devId shell getprop ro.product.model).Trim()
    $brand = (& $AdbExe -s $devId shell getprop ro.product.brand).Trim()
    $abi = (& $AdbExe -s $devId shell getprop ro.product.cpu.abi).Trim()
    $sdk = (& $AdbExe -s $devId shell getprop ro.build.version.sdk).Trim()
    $androidVer = (& $AdbExe -s $devId shell getprop ro.build.version.release).Trim()
    
    Write-Host "    Marca / Modelo: $brand $model" -ForegroundColor White
    Write-Host "    Arquitectura:   $abi" -ForegroundColor White
    Write-Host "    Versión Android: $androidVer (API $sdk)" -ForegroundColor White
    
    if ($abi -ne "arm64-v8a") {
        Write-Host "    [ADVERTENCIA] La arquitectura no es arm64-v8a ($abi). Puede haber incompatibilidad." -ForegroundColor Yellow
    } else {
        Write-Host "    [OK] Arquitectura compatible al 100% (ARM64 nativo de alto rendimiento)." -ForegroundColor Green
    }
    
    if ($brand -match "Xiaomi" -or $model -match "12 Pro") {
        Write-Host "    [DETECTADO] Xiaomi 12 Pro (Snapdragon 8 Gen 1)" -ForegroundColor Cyan
        Write-Host "    -> Soporta tasa de refresco ultra fluida a 120Hz y protección contra rastreo." -ForegroundColor DarkGray
    } elseif ($brand -match "Lenovo" -or $model -match "TB" -or $model -match "Xiaoxin") {
        Write-Host "    [DETECTADO] Lenovo Xiaoxin Pad 11 (MediaTek Dimensity 6300)" -ForegroundColor Cyan
        Write-Host "    -> Formato Tablet con soporte para multitarea ZUI / One-Vision." -ForegroundColor DarkGray
    }

    if ($ApkPath -and (Test-Path $ApkPath)) {
        Write-Host "`n[>] Instalando APK en $devId: $ApkPath..." -ForegroundColor Cyan
        & $AdbExe -s $devId install -r -d "$ApkPath"
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  [EXITO] Aegis Browser instalado correctamente en $model!" -ForegroundColor Green
        } else {
            Write-Host "  [FALLO] No se pudo instalar el APK. Revisa permisos en el dispositivo." -ForegroundColor Red
        }
    }
}

Write-Host "`n==============================================================" -ForegroundColor Cyan
Write-Host "                     PROCESO FINALIZADO" -ForegroundColor Cyan
Write-Host "==============================================================`n" -ForegroundColor Cyan
