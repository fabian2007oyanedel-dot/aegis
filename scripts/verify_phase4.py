#!/usr/bin/env python3
# ==============================================================================
# Aegis Browser - Verificador de Fase 4: Gestión de Datos del Usuario
# ==============================================================================
# Valida el almacenamiento seguro local (DPAPI/Keystore), aislamiento de cookies
# (dFPI), desactivación de detección de fugas remotas y políticas de retención.
#
# Uso: python scripts/verify_phase4.py
# ==============================================================================

import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent
PATCHES_DIR = ROOT_DIR / "patches"
CONFIG_DIR = ROOT_DIR / "config"

def test_phase4_patches():
    p7 = PATCHES_DIR / "007-local-storage-encryption.patch"
    p8 = PATCHES_DIR / "008-data-retention-clearing.patch"
    
    assert p7.exists() and p7.stat().st_size > 100, "Falta 007-local-storage-encryption.patch"
    assert p8.exists() and p8.stat().st_size > 100, "Falta 008-data-retention-clearing.patch"
    
    p7_text = p7.read_text(encoding="utf-8")
    assert "CryptProtectData" in p7_text, "007 debe implementar DPAPI nativo"
    assert "LeakDetectionCheckImpl" in p7_text, "007 debe anular el envío de contraseñas a Google"
    assert "CookiePartitionKey" in p7_text, "007 debe forzar dFPI (cookie partitioning)"
    print("  [OK] Parches de cifrado local DPAPI y aislamiento dFPI verificados.")

def test_settings_user_data_policies():
    settings_file = CONFIG_DIR / "default_settings.json"
    assert settings_file.exists(), "Falta default_settings.json"
    data = json.loads(settings_file.read_text(encoding="utf-8"))
    
    profile = data.get("profile", {})
    assert profile.get("password_manager_enabled") is True, "Password manager debe estar habilitado"
    assert profile.get("password_manager_leak_detection") is False, "Leak detection remoto debe ser false"
    assert profile.get("password_encryption") == "system_local_dpapi", "Cifrado debe ser local DPAPI"

    privacy = data.get("privacy", {})
    assert privacy.get("dynamic_first_party_isolation") is True, "dFPI debe estar activo"
    assert privacy.get("clear_on_exit", {}).get("enabled") is True, "Clear on exit debe estar configurado"

    download = data.get("download", {})
    assert download.get("resilient_resumption_enabled") is True, "Reanudación de descargas debe estar activa"
    print("  [OK] Políticas de datos: Cifrado local, cero telemetría de credenciales y descargas resilientes.")

def test_patch_manager_registration():
    apply_script = (ROOT_DIR / "scripts" / "apply_patches.py").read_text(encoding="utf-8")
    assert "007-local-storage-encryption.patch" in apply_script, "Parche 007 no registrado en apply_patches.py"
    assert "008-data-retention-clearing.patch" in apply_script, "Parche 008 no registrado en apply_patches.py"
    print("  [OK] Parches 007 y 008 registrados en apply_patches.py.")

def main():
    print()
    print("  Aegis Browser - Verificación de Fase 4 (Gestión de Datos)")
    print("  " + "=" * 58)
    print()
    
    try:
        test_phase4_patches()
        test_settings_user_data_policies()
        test_patch_manager_registration()
        print()
        print("  ----------------------------------------------------------")
        print("  [EXITO] TODOS LOS REQUISITOS DE FASE 4 CUMPLIDOS AL 100%")
        print()
    except AssertionError as e:
        print(f"\n  [FALLO] {e}\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
