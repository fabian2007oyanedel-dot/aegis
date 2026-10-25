#!/usr/bin/env python3
# ==============================================================================
# Aegis Browser - Auditoría Integral de la Base de Código
# ==============================================================================
# Ejecuta todas las suites de validación y análisis de errores:
# - Fase 1: Desgooglizado y Privacidad
# - Fase 2: Motor Rust Shields
# - Fase 3: Interfaz de Usuario y NTP
# - Fase 4: Cifrado Local y Gestión de Datos
#
# Uso: python scripts/audit_codebase.py
# ==============================================================================

import subprocess
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SCRIPTS_DIR = Path(__file__).parent

def run_check(title: str, cmd: list[str]) -> bool:
    print(f"\n[>] Ejecutando {title}...")
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if result.returncode == 0:
        print(f"  [OK] {title}: PASO")
        return True
    else:
        print(f"  [FALLO] {title}: FALLO")
        print(result.stdout)
        print(result.stderr)
        return False

def main():
    print("=" * 60)
    print("      AEGIS BROWSER - AUDITORÍA MAESTRA DE CÓDIGO")
    print("=" * 60)

    results = []
    
    # 1. Auditoría Fase 1
    results.append(run_check("Auditoría Fase 1 (De-Googled & Privacidad)", [sys.executable, str(SCRIPTS_DIR / "verify_phase1.py")]))

    # 2. Auditoría Fase 3
    results.append(run_check("Auditoría Fase 3 (UI/UX & NTP Limpia)", [sys.executable, str(SCRIPTS_DIR / "verify_phase3.py")]))

    # 3. Auditoría Fase 4
    results.append(run_check("Auditoría Fase 4 (Cifrado Local & Datos)", [sys.executable, str(SCRIPTS_DIR / "verify_phase4.py")]))

    # 4. Auditoría Fase 5
    results.append(run_check("Auditoría Fase 5 (Adaptación Android APK)", [sys.executable, str(SCRIPTS_DIR / "verify_phase5.py")]))

    # 5. Auditoría Fase 6
    results.append(run_check("Auditoría Fase 6 (Anti-Fingerprinting & Release v1.0)", [sys.executable, str(SCRIPTS_DIR / "verify_phase6.py")]))

    # 6. Auditoría Optimizaciones 100x & Supercharged UI
    results.append(run_check("Auditoría Ultra Rendimiento 100x & UI Completa", [sys.executable, str(SCRIPTS_DIR / "verify_ultra_enhancements.py")]))

    # 7. Auditoría Aegis Shields 100x (Sitios Populares & Anti-Adblock)
    results.append(run_check("Auditoría Aegis Shields 100x (Sitios Populares)", [sys.executable, str(SCRIPTS_DIR / "verify_ultra_shields.py")]))

    print("\n" + "=" * 60)
    if all(results):
        print("  [EXITO] AUDITORIA COMPLETA: 0 ERRORES ENCONTRADOS")
        print("=" * 60)
        sys.exit(0)
    else:
        print("  [ALERTA] AUDITORIA: ALGUNAS COMPROBACIONES FALLARON")
        print("=" * 60)
        sys.exit(1)

if __name__ == "__main__":
    main()
