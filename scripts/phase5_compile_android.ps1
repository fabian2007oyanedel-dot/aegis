# ==============================================================================
# Aegis Browser - Fase 5: Compilación de APK Nativo Android ARM64
# ==============================================================================
# Genera Aegis-arm64-v8a.apk con motor de escudos Rust, optimizaciones V8 y
# soporte para pantallas 120Hz (Xiaomi 12 Pro) y tablets (Lenovo Xiaoxin Pad 11).
# ==============================================================================

param(
    [string]$ChromiumSrcDir = "D:\aegis-chromium-src",
    [string]$DepotToolsDir  = "D:\depot_tools",
    [int]$Jobs = 0
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Step { param($msg) Write-Host "`n[STEP] $msg" -ForegroundColor Cyan }
function Write-OK   { param($msg) Write-Host "  [OK]  $msg" -ForegroundColor Green }
function Write-Warn { param($msg) Write-Host "  [!!]  $msg" -ForegroundColor Yellow }
function Write-Fail { param($msg) Write-Host "  [ERR] $msg" -ForegroundColor Red; exit 1 }

$srcDir   = "$ChromiumSrcDir\src"
$buildDir = "$srcDir\out\Aegis_Android_arm64"
$env:PATH = "$DepotToolsDir;$env:PATH"

if ($Jobs -eq 0) {
    $Jobs = (Get-CimInstance Win32_Processor).NumberOfLogicalProcessors
}

Write-Step "Verificando dependencias de build Android..."
if (-not (Test-Path $srcDir)) {
    Write-Fail "No se encontró el directorio de código fuente en $srcDir."
}

# 1. Configurar gn gen para Android ARM64
Write-Step "1/3 - Generando sistema de build GN para Android ARM64..."
$gnArgsPath = Join-Path $PSScriptRoot "..\config\args-android.gn"
if (-not (Test-Path $gnArgsPath)) { Write-Fail "No se encontró config/args-android.gn" }
$gnArgs = Get-Content $gnArgsPath -Raw

if (-not (Test-Path $buildDir)) { New-Item -ItemType Directory -Path $buildDir -Force | Out-Null }
Set-Content -Path "$buildDir\args.gn" -Value $gnArgs -Encoding utf8

Push-Location $srcDir
try {
    & "$DepotToolsDir\gn.bat" gen "out\Aegis_Android_arm64" --args="$gnArgs"
    if ($LASTEXITCODE -ne 0) { Write-Fail "Falló gn gen para Android." }
    Write-OK "Sistema de build GN generado en $buildDir"

    # 2. Compilar target chrome_public_apk
    Write-Step "2/3 - Compilando chrome_public_apk con autoninja (-j $Jobs)..."
    & "$DepotToolsDir\autoninja.bat" -C "out\Aegis_Android_arm64" chrome_public_apk -j $Jobs
    if ($LASTEXITCODE -ne 0) { Write-Fail "Falló la compilación del APK." }
    Write-OK "Compilación finalizada con éxito."
} finally {
    Pop-Location
}

# 3. Empaquetar y renombrar APK
Write-Step "3/3 - Localizando y verificando APK generado..."
$apkSource = "$buildDir\apks\ChromePublic.apk"
$outputDir = Join-Path $PSScriptRoot "..\dist\android"
if (-not (Test-Path $outputDir)) { New-Item -ItemType Directory -Path $outputDir -Force | Out-Null }
$finalApk = "$outputDir\Aegis-arm64-v8a.apk"

if (Test-Path $apkSource) {
    Copy-Item $apkSource $finalApk -Force
    $sizeMb = [Math]::Round((Get-Item $finalApk).Length / 1MB, 2)
    Write-OK "APK generado exitosamente: $finalApk ($sizeMb MB)"
    Write-Host "`nPara instalar en tu Xiaomi 12 Pro o Lenovo Xiaoxin Pad ejecuta:" -ForegroundColor Green
    Write-Host "  .\scripts\install_android.ps1 -ApkPath `"$finalApk`"" -ForegroundColor Cyan
} else {
    Write-Fail "No se encontró el APK en $apkSource."
}
