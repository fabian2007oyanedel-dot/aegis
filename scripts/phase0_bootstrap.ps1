# ==============================================================================
# Aegis Browser - Fase 0: Script de Bootstrap de Entorno
# ==============================================================================
# Este script prepara TODOS los prerequisitos para compilar Chromium desde 0.
# Ejecutar como Administrador en PowerShell.
# Plataforma objetivo: Windows x64
# Código fuente de Chromium se descarga en D:\aegis-chromium-src
# ==============================================================================

param(
    [string]$ChromiumSrcDir = "D:\aegis-chromium-src",
    [string]$DepotToolsDir  = "D:\depot_tools",
    [switch]$SkipFetch      = $false,   # Saltar fetch de Chromium (si ya se descargó)
    [switch]$SkipRust       = $false,   # Saltar instalación de Rust
    [switch]$DryRun         = $false    # Solo mostrar pasos sin ejecutar
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# ── Colores de consola ──────────────────────────────────────────────────────
function Write-Step  { param($msg) Write-Host "`n[STEP] $msg" -ForegroundColor Cyan }
function Write-OK    { param($msg) Write-Host "  [OK]  $msg" -ForegroundColor Green }
function Write-Warn  { param($msg) Write-Host "  [!!]  $msg" -ForegroundColor Yellow }
function Write-Fail  { param($msg) Write-Host "  [ERR] $msg" -ForegroundColor Red; exit 1 }

function Run {
    param([string]$Cmd, [string[]]$Args, [string]$WorkDir = $null)
    if ($DryRun) {
        Write-Host "  [DRY] $Cmd $Args" -ForegroundColor DarkGray
        return
    }
    $opts = @{ FilePath = $Cmd; ArgumentList = $Args; PassThru = $true }
    if ($WorkDir) { $opts.WorkingDirectory = $WorkDir }
    $proc = Start-Process @opts -Wait
    if ($proc.ExitCode -ne 0) { Write-Fail "Comando fallido: $Cmd $Args (exit $($proc.ExitCode))" }
}

# ── Verificar que se ejecuta como Admin ────────────────────────────────────
Write-Step "Verificando privilegios de administrador..."
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) { Write-Fail "Ejecuta este script como Administrador (clic derecho → Ejecutar como administrador)." }
Write-OK "Privilegios de administrador confirmados."

# ── 0.1: Instalar Rust + Cargo ─────────────────────────────────────────────
Write-Step "0.1 - Instalando Rust y Cargo (rustup)..."
if (-not $SkipRust) {
    $rustupExe = (Get-Command rustup -ErrorAction SilentlyContinue)
    if ($rustupExe) {
        Write-OK "Rust ya instalado: $(rustup --version)"
        rustup update stable
    } else {
        Write-Warn "Rust no encontrado. Descargando rustup-init.exe..."
        $rustupInstaller = "$env:TEMP\rustup-init.exe"
        Invoke-WebRequest -Uri "https://win.rustup.rs/x86_64" -OutFile $rustupInstaller
        # Instalación silenciosa con target MSVC (compatible con Chromium)
        Run -Cmd $rustupInstaller -Args @("-y", "--default-toolchain", "stable-x86_64-pc-windows-msvc")
        # Recargar PATH para esta sesión
        $env:PATH = [System.Environment]::GetEnvironmentVariable("PATH","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("PATH","User")
        Write-OK "Rust instalado. Versión: $(rustup --version)"
    }
    # Agregar target Android para Fase 5 (instalar ya para no olvidarlo)
    rustup target add x86_64-pc-windows-msvc
    rustup target add aarch64-linux-android
    Write-OK "Targets Rust configurados: windows-msvc + android arm64"
} else {
    Write-Warn "Instalación de Rust omitida (--SkipRust)."
}

# ── 0.2: Instalar Visual Studio Build Tools (MSVC) ─────────────────────────
Write-Step "0.2 - Verificando Visual Studio Build Tools (MSVC)..."
$vsWhere = "${env:ProgramFiles(x86)}\Microsoft Visual Studio\Installer\vswhere.exe"
if (Test-Path $vsWhere) {
    $vsInstall = & $vsWhere -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath 2>$null
    if ($vsInstall) {
        Write-OK "Visual Studio encontrado en: $vsInstall"
    } else {
        Write-Warn "Visual Studio instalado pero sin componentes de C++. Instalando workload..."
        # Instalar componentes mínimos necesarios para Chromium
        & $vsWhere -latest -property installationPath | ForEach-Object {
            Run -Cmd "$_\Common7\IDE\VSIXInstaller.exe" -Args @()
        }
    }
} else {
    Write-Warn "Visual Studio no encontrado. Instalando Build Tools via winget..."
    if (-not $DryRun) {
        winget install --id Microsoft.VisualStudio.2022.BuildTools --silent --accept-package-agreements --accept-source-agreements --override "--wait --quiet --add Microsoft.VisualStudio.Workload.VCTools --add Microsoft.VisualStudio.Component.Windows11SDK.22621 --add Microsoft.VisualStudio.Component.VC.ATLMFC --includeRecommended"
        Write-OK "Visual Studio Build Tools instalado."
    }
}

# ── 0.3: Instalar depot_tools ──────────────────────────────────────────────
Write-Step "0.3 - Instalando depot_tools de Google..."
if (-not (Test-Path $DepotToolsDir)) {
    Write-Warn "depot_tools no encontrado. Clonando en $DepotToolsDir..."
    Run -Cmd "git" -Args @("clone", "https://chromium.googlesource.com/chromium/tools/depot_tools.git", $DepotToolsDir)
    Write-OK "depot_tools clonado."
} else {
    Write-OK "depot_tools ya existe en $DepotToolsDir. Actualizando..."
    Run -Cmd "git" -Args @("-C", $DepotToolsDir, "pull", "--ff-only")
}

# Agregar depot_tools al PATH de esta sesión
$env:PATH = "$DepotToolsDir;$env:PATH"
$env:DEPOT_TOOLS_WIN_TOOLCHAIN = "0"  # Usar el MSVC del sistema, no el de Google
$env:PYTHONDONTWRITEBYTECODE = "1"

# Agregar depot_tools al PATH de sistema de forma permanente
$sysPath = [System.Environment]::GetEnvironmentVariable("PATH", "Machine")
if ($sysPath -notlike "*$DepotToolsDir*") {
    [System.Environment]::SetEnvironmentVariable("PATH", "$DepotToolsDir;$sysPath", "Machine")
    Write-OK "depot_tools agregado al PATH del sistema."
}
# Variable requerida por depot_tools para usar MSVC local
[System.Environment]::SetEnvironmentVariable("DEPOT_TOOLS_WIN_TOOLCHAIN", "0", "Machine")
Write-OK "Variables de entorno configuradas."

# Bootstrap inicial de depot_tools (descarga herramientas Python internas)
Write-Step "Ejecutando bootstrap de gclient (primera ejecución tardará unos minutos)..."
Run -Cmd "$DepotToolsDir\gclient.bat" -Args @("version")
Write-OK "depot_tools bootstrap completado."

# ── 0.4: Crear directorio de código fuente de Chromium ────────────────────
Write-Step "0.4 - Preparando directorio de código fuente de Chromium..."
if (-not (Test-Path $ChromiumSrcDir)) {
    New-Item -ItemType Directory -Path $ChromiumSrcDir -Force | Out-Null
    Write-OK "Directorio creado: $ChromiumSrcDir"
} else {
    Write-OK "Directorio ya existe: $ChromiumSrcDir"
}

# ── 0.5: Fetch de Chromium ─────────────────────────────────────────────────
Write-Step "0.5 - Descargando código fuente de Chromium (~35 GB, puede tomar 1-3 horas)..."
Write-Warn "Esto descarga el árbol completo de Chromium. Asegúrate de tener al menos 80 GB libres en $ChromiumSrcDir."
Write-Warn "Una vez iniciado, NO interrumpas el proceso. Si falla, ejecuta este script de nuevo (retomará donde quedó)."

if (-not $SkipFetch) {
    if (Test-Path "$ChromiumSrcDir\src") {
        Write-OK "El directorio 'src' ya existe. Ejecutando gclient sync para actualizar..."
        Run -Cmd "$DepotToolsDir\gclient.bat" -Args @("sync", "--with_branch_heads", "--with_tags") -WorkDir $ChromiumSrcDir
    } else {
        # fetch chromium en el directorio destino
        Run -Cmd "$DepotToolsDir\fetch.bat" -Args @("--no-history", "chromium") -WorkDir $ChromiumSrcDir
        Write-OK "Fetch de Chromium completado."
    }
} else {
    Write-Warn "Fetch de Chromium omitido (--SkipFetch)."
}

# ── 0.6: Configurar directorio de build ───────────────────────────────────
Write-Step "0.6 - Configurando directorio de build de Chromium..."
$buildDir = "$ChromiumSrcDir\src\out\Aegis"

if (-not (Test-Path $buildDir)) {
    New-Item -ItemType Directory -Path $buildDir -Force | Out-Null
}

# Copiar nuestro args.gn optimizado al directorio de build
$argsGnSrc = "$PSScriptRoot\..\config\args.gn"
$argsGnDst = "$buildDir\args.gn"

if (Test-Path $argsGnSrc) {
    # Temporalmente usar args.gn sin aegis_shields para la compilación vanilla de Fase 0
    $argsContent = Get-Content $argsGnSrc -Raw
    $argsContent = $argsContent -replace "enable_aegis_shields = true", "# enable_aegis_shields = false  # Se activa en Fase 2"
    $argsContent | Set-Content $argsGnDst -Encoding UTF8
    Write-OK "args.gn copiado a $argsGnDst (modo Fase 0: sin Aegis Shields aún)"
}

Write-OK "Configuración de build lista."

# ── Resumen final ──────────────────────────────────────────────────────────
Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║          FASE 0: BOOTSTRAP COMPLETADO                   ║" -ForegroundColor Green
Write-Host "╠══════════════════════════════════════════════════════════╣" -ForegroundColor Green
Write-Host "║  Rust/Cargo     → Instalado (stable-msvc)               ║" -ForegroundColor Green
Write-Host "║  MSVC           → Build Tools instalado                 ║" -ForegroundColor Green
Write-Host "║  depot_tools    → $DepotToolsDir              ║" -ForegroundColor Green
Write-Host "║  Chromium src   → $ChromiumSrcDir            ║" -ForegroundColor Green
Write-Host "║  Build dir      → out\Aegis                             ║" -ForegroundColor Green
Write-Host "╠══════════════════════════════════════════════════════════╣" -ForegroundColor Green
Write-Host "║  SIGUIENTE PASO:                                         ║" -ForegroundColor Yellow
Write-Host "║  Ejecuta: scripts\phase0_compile.ps1                    ║" -ForegroundColor Yellow
Write-Host "╚══════════════════════════════════════════════════════════╝" -ForegroundColor Green
