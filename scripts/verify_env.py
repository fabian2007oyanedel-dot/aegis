#!/usr/bin/env python3
# ==============================================================================
# Aegis Browser - Verificador de Entorno (Fase 0)
# ==============================================================================
# Verifica que todos los prerequisitos están instalados y configurados
# correctamente antes de intentar la compilación de Chromium.
#
# Uso: python scripts/verify_env.py
# ==============================================================================

import subprocess
import sys
import shutil
import os
from pathlib import Path
from dataclasses import dataclass


@dataclass
class CheckResult:
    name: str
    passed: bool
    detail: str
    required: bool = True


def run(cmd: list[str], timeout: int = 10) -> tuple[int, str]:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout,
                           encoding="utf-8", errors="replace")
        return r.returncode, (r.stdout + r.stderr).strip()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return -1, ""


def check_command(name: str, cmd: list[str], version_pattern: str = "") -> CheckResult:
    code, output = run(cmd)
    if code == 0 or (code != -1 and output):
        detail = output.split("\n")[0] if output else "OK"
        return CheckResult(name, True, detail)
    return CheckResult(name, False, f"'{cmd[0]}' no encontrado en PATH")


def check_disk_space(path: str, min_gb: float) -> CheckResult:
    try:
        import shutil
        total, used, free = shutil.disk_usage(path)
        free_gb = free / (1024**3)
        passed = free_gb >= min_gb
        detail = f"{free_gb:.1f} GB libres en {path} (mínimo requerido: {min_gb} GB)"
        return CheckResult(f"Espacio en disco ({path})", passed, detail)
    except Exception as e:
        return CheckResult(f"Espacio en disco ({path})", False, str(e))


def check_python_version() -> CheckResult:
    major, minor = sys.version_info[:2]
    passed = (major == 3 and minor >= 11)
    detail = f"Python {major}.{minor} {'✓' if passed else '✗ (se requiere 3.11+)'}"
    return CheckResult("Python 3.11+", passed, detail)


def check_git_version() -> CheckResult:
    code, output = run(["git", "--version"])
    if code != 0:
        return CheckResult("Git", False, "git no encontrado")
    # Chromium necesita git 2.28+
    try:
        version_str = output.split("version")[1].strip().split(".windows")[0].split(" ")[0]
        parts = [int(x) for x in version_str.split(".")[:2]]
        passed = parts[0] > 2 or (parts[0] == 2 and parts[1] >= 28)
        return CheckResult("Git 2.28+", passed, output.split("\n")[0])
    except Exception:
        return CheckResult("Git 2.28+", True, output.split("\n")[0])  # Asumir OK si no podemos parsear


def check_rust() -> CheckResult:
    code, output = run(["rustup", "--version"])
    if code != 0:
        return CheckResult("Rust/rustup", False, "rustup no encontrado (ejecutar phase0_bootstrap.ps1)")
    
    code2, cargo_out = run(["cargo", "--version"])
    if code2 != 0:
        return CheckResult("Rust/rustup", False, "rustup encontrado pero cargo no está disponible")
    
    # Verificar target MSVC
    code3, targets = run(["rustup", "target", "list", "--installed"])
    has_msvc = "x86_64-pc-windows-msvc" in targets
    detail = f"{output.split(chr(10))[0]} | {cargo_out} | MSVC target: {'✓' if has_msvc else '✗'}"
    return CheckResult("Rust (stable-msvc)", code == 0 and has_msvc, detail)


def check_depot_tools() -> CheckResult:
    depot_path = os.environ.get("PATH", "")
    
    # Buscar gclient en PATH
    gclient = shutil.which("gclient") or shutil.which("gclient.bat")
    if gclient:
        code, output = run([gclient, "version"])
        return CheckResult("depot_tools (gclient)", True, f"gclient en: {gclient}")
    
    # Buscar en ubicaciones comunes
    common_paths = ["D:\\depot_tools", "C:\\depot_tools",
                    str(Path.home() / "depot_tools")]
    for p in common_paths:
        if Path(p).exists() and Path(p, "gclient.bat").exists():
            return CheckResult("depot_tools", True,
                               f"Encontrado en {p} (agregar al PATH)")
    
    return CheckResult("depot_tools", False,
                       "No encontrado. Ejecutar phase0_bootstrap.ps1")


def check_msvc() -> CheckResult:
    # Buscar vswhere
    vswhere_paths = [
        r"C:\Program Files (x86)\Microsoft Visual Studio\Installer\vswhere.exe",
        r"C:\Program Files\Microsoft Visual Studio\Installer\vswhere.exe",
    ]
    for vswhere in vswhere_paths:
        if Path(vswhere).exists():
            code, output = run([vswhere, "-latest", "-products", "*",
                                 "-requires", "Microsoft.VisualStudio.Component.VC.Tools.x86.x64",
                                 "-property", "installationVersion"])
            if code == 0 and output:
                return CheckResult("MSVC (Visual Studio)", True,
                                   f"VS {output.strip()} con C++ tools")
    
    # Buscar cl.exe directamente
    cl = shutil.which("cl")
    if cl:
        return CheckResult("MSVC (cl.exe)", True, f"cl.exe en {cl}")
    
    return CheckResult("MSVC / Build Tools", False,
                       "Visual Studio Build Tools no encontrado. Ejecutar phase0_bootstrap.ps1")


def check_chromium_src(path: str) -> CheckResult:
    src = Path(path) / "src"
    if not src.exists():
        return CheckResult("Código fuente de Chromium", False,
                           f"No encontrado en {path}. Ejecutar phase0_bootstrap.ps1", required=False)
    
    # Verificar que tiene el estructura correcta
    key_dirs = ["chrome", "content", "net", "third_party"]
    missing = [d for d in key_dirs if not (src / d).exists()]
    if missing:
        return CheckResult("Código fuente de Chromium", False,
                           f"Estructura incompleta. Faltan: {missing}", required=False)
    
    return CheckResult("Código fuente de Chromium", True,
                       f"Encontrado y completo en {src}")


def check_windows_sdk() -> CheckResult:
    """Verifica que hay un Windows SDK instalado (necesario para Chromium en Windows)."""
    sdk_base = Path(r"C:\Program Files (x86)\Windows Kits\10\Include")
    if not sdk_base.exists():
        sdk_base = Path(r"C:\Program Files\Windows Kits\10\Include")
    
    if sdk_base.exists():
        versions = sorted([d.name for d in sdk_base.iterdir() if d.is_dir()], reverse=True)
        if versions:
            return CheckResult("Windows 10/11 SDK", True,
                               f"Versión más reciente: {versions[0]}")
    
    return CheckResult("Windows 10/11 SDK", False,
                       "Windows SDK no encontrado. Instalar desde VS Installer.")


def main():
    # Forzar UTF-8 en stdout para compatibilidad con Windows cp1252
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

    print()
    print("  Aegis Browser - Verificador de Entorno (Fase 0)")
    print("  " + "=" * 56)
    print()

    checks = [
        check_python_version(),
        check_git_version(),
        check_rust(),
        check_depot_tools(),
        check_msvc(),
        check_windows_sdk(),
        check_disk_space("D:\\", 80.0),
        check_chromium_src("D:\\aegis-chromium-src"),
    ]

    all_required_passed = True
    warnings = []

    for result in checks:
        icon   = "[OK]  " if result.passed else ("[WARN] " if not result.required else "[FAIL] ")
        
        print(f"  {icon} {result.name}")
        print(f"         {result.detail}")
        print()

        if not result.passed and result.required:
            all_required_passed = False
        if not result.passed and not result.required:
            warnings.append(result.name)

    print("  " + "-" * 58)
    
    if all_required_passed:
        print()
        print("  [LISTO] ENTORNO LISTO PARA COMPILAR CHROMIUM")
        print("          Ejecuta: scripts\\phase0_compile.ps1")
        if warnings:
            print(f"\n  [WARN] Advertencias (no bloqueantes): {', '.join(warnings)}")
    else:
        print()
        print("  [FALTA] PREREQUISITOS FALTANTES")
        print("          Ejecuta: scripts\\phase0_bootstrap.ps1 (como Administrador)")
    
    print()
    sys.exit(0 if all_required_passed else 1)


if __name__ == "__main__":
    main()
