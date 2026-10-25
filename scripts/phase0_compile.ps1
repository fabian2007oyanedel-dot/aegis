# ==============================================================================
# Aegis Browser - Fase 0: Compilación Vanilla de Chromium
# ==============================================================================
# Ejecutar DESPUÉS de phase0_bootstrap.ps1
# Compila Chromium sin modificaciones para verificar que el entorno funciona.
# Genera chrome.exe en out\Aegis\ como entregable verificable de Fase 0.
# ==============================================================================

param(
    [string]$ChromiumSrcDir = "D:\aegis-chromium-src",
    [string]$DepotToolsDir  = "D:\depot_tools",
    [int]$Jobs = 0       # 0 = auto (usa todos los núcleos disponibles)
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Step { param($msg) Write-Host "`n[STEP] $msg" -ForegroundColor Cyan }
function Write-OK   { param($msg) Write-Host "  [OK]  $msg" -ForegroundColor Green }
function Write-Warn { param($msg) Write-Host "  [!!]  $msg" -ForegroundColor Yellow }
function Write-Fail { param($msg) Write-Host "  [ERR] $msg" -ForegroundColor Red; exit 1 }

# ── Variables ──────────────────────────────────────────────────────────────
$srcDir   = "$ChromiumSrcDir\src"
$buildDir = "$srcDir\out\Aegis"
$env:PATH = "$DepotToolsDir;$env:PATH"
$env:DEPOT_TOOLS_WIN_TOOLCHAIN = "0"

if ($Jobs -eq 0) {
    $Jobs = (Get-CimInstance Win32_Processor).NumberOfLogicalProcessors
    Write-Host "  Detectados $Jobs núcleos lógicos. Usando todos para la compilación." -ForegroundColor DarkGray
}

# ── Verificación previa ───────────────────────────────────────────────────
Write-Step "Verificando pre-requisitos de compilación..."

if (-not (Test-Path $srcDir)) {
    Write-Fail "No se encontró el directorio src en $ChromiumSrcDir. Ejecuta primero phase0_bootstrap.ps1"
}
Write-OK "Código fuente de Chromium: $srcDir"

$gclient = Get-Command "$DepotToolsDir\gclient.bat" -ErrorAction SilentlyContinue
if (-not $gclient) { Write-Fail "depot_tools no encontrado en $DepotToolsDir" }
Write-OK "depot_tools: $DepotToolsDir"

# ── Paso 1: gclient sync final ────────────────────────────────────────────
Write-Step "1/4 - Sincronizando dependencias (gclient sync)..."
Write-Warn "Este paso instala sub-dependencias (libc++, clang de Google, etc.) ~5-10 min."
Push-Location $ChromiumSrcDir
try {
    & "$DepotToolsDir\gclient.bat" sync --no-history 2>&1 | Tee-Object -FilePath "gclient_sync.log"
    if ($LASTEXITCODE -ne 0) { Write-Fail "gclient sync falló. Ver gclient_sync.log" }
    Write-OK "gclient sync completado."
} finally {
    Pop-Location
}

# ── Paso 2: Generar archivos de build con gn ─────────────────────────────
Write-Step "2/4 - Generando sistema de build (gn gen)..."
Push-Location $srcDir
try {
    & "$DepotToolsDir\gn.bat" gen "out\Aegis" --args="$(Get-Content "$buildDir\args.gn" -Raw)" 2>&1 | Tee-Object -FilePath "gn_gen.log"
    if ($LASTEXITCODE -ne 0) { Write-Fail "gn gen falló. Ver gn_gen.log" }
    Write-OK "Sistema de build generado en out\Aegis"
} finally {
    Pop-Location
}

# ── Paso 3: Compilar con autoninja ───────────────────────────────────────
Write-Step "3/4 - Compilando Chromium (autoninja - puede tomar 2-6 horas)..."
Write-Warn "La primera compilación completa es lenta. Las compilaciones incrementales son rápidas."
Write-Warn "Log en: $srcDir\compile.log"

$startTime = Get-Date
Push-Location $srcDir
try {
    # Compilar solo el target 'chrome' (el navegador) sin tests ni herramientas extras
    & "$DepotToolsDir\autoninja.bat" -C "out\Aegis" chrome -j $Jobs 2>&1 | Tee-Object -FilePath "compile.log"
    if ($LASTEXITCODE -ne 0) { Write-Fail "Compilación fallida. Ver compile.log" }
    $elapsed = (Get-Date) - $startTime
    Write-OK "Compilación exitosa en $($elapsed.Hours)h $($elapsed.Minutes)m."
} finally {
    Pop-Location
}

# ── Paso 4: Verificar el ejecutable ──────────────────────────────────────
Write-Step "4/4 - Verificando el ejecutable generado..."
$chromeExe = "$buildDir\chrome.exe"
if (Test-Path $chromeExe) {
    $size = [Math]::Round((Get-Item $chromeExe).Length / 1MB, 1)
    Write-OK "chrome.exe generado: $chromeExe ($size MB)"
    
    # Renombrar a aegis.exe para el branding (se hará correctamente en Fase 1)
    $aegisExe = "$buildDir\aegis.exe"
    Copy-Item $chromeExe $aegisExe -Force
    Write-OK "Copiado como aegis.exe para prueba inicial."
} else {
    Write-Fail "No se encontró chrome.exe en $buildDir. La compilación puede no haber terminado."
}

# ── Resumen ───────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║      FASE 0 COMPLETADA - ENTREGABLE VERIFICABLE             ║" -ForegroundColor Green
Write-Host "╠══════════════════════════════════════════════════════════════╣" -ForegroundColor Green
Write-Host "║  Ejecutable: $buildDir\aegis.exe" -ForegroundColor Green
Write-Host "║                                                              ║" -ForegroundColor Green
Write-Host "║  VERIFICACIÓN MANUAL:                                        ║" -ForegroundColor Yellow
Write-Host "║  1. Abrir aegis.exe → debe abrir el navegador               ║" -ForegroundColor Yellow
Write-Host "║  2. Ir a una URL (ej. example.com) → debe navegar           ║" -ForegroundColor Yellow
Write-Host "║  3. Abrir Wireshark → verificar que NO haya pings           ║" -ForegroundColor Yellow
Write-Host "║     salientes espontáneos (eso se hace en Fase 1)           ║" -ForegroundColor Yellow
Write-Host "║                                                              ║" -ForegroundColor Green
Write-Host "║  SIGUIENTE: Ejecutar scripts\phase1_degoogle.ps1            ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════════════╝" -ForegroundColor Green
