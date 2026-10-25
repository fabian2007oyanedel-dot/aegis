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

SCRIPTS_DIR = Path(__file__).parent

def run_check(title: str, cmd: list[str]) -> bool:
    print(f"\n▶ Ejecutando {title}...")
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if result.returncode == 0:
        print(f"  ✅ {title}: PASÓ")
        return True
    else:
        print(f"  ❌ {title}: FALLÓ")
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

    print("\n" + "=" * 60)
    if all(results):
        print("  🎉 AUDITORÍA COMPLETA: 0 ERRORES ENCONTRADOS")
        print("=" * 60)
        sys.exit(0)
    else:
        print("  ⚠️ AUDITORÍA: ALGUNAS COMPROBACIONES FALLARON")
        print("=" * 60)
        sys.exit(1)

if __name__ == "__main__":
    main()
