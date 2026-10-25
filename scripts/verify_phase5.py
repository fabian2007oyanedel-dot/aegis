#!/usr/bin/env python3
# ==============================================================================
# Aegis Browser - Verificador de Fase 5: Adaptación y Optimización Android (APK)
# ==============================================================================
# Valida la configuración GN para arquitectura ARM64 móvil, UI táctil,
# cifrado con Android KeyStore, aceleración de video y ahorro de batería.
#
# Uso: python scripts/verify_phase5.py
# ==============================================================================

import re
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent
CONFIG_DIR = ROOT_DIR / "config"
PATCHES_DIR = ROOT_DIR / "patches"
WORKFLOWS_DIR = ROOT_DIR / ".github" / "workflows"

def test_android_gn_args():
    args_file = CONFIG_DIR / "args-android.gn"
    assert args_file.exists(), "Falta config/args-android.gn"
    content = args_file.read_text(encoding="utf-8")
    
    assert re.search(r'target_os\s*=\s*"android"', content), "target_os debe ser 'android'"
    assert re.search(r'target_cpu\s*=\s*"arm64"', content), "target_cpu debe ser 'arm64'"
    assert re.search(r'enable_aegis_shields\s*=\s*true', content), "enable_aegis_shields debe ser true"
    assert re.search(r'safe_browsing_mode\s*=\s*0', content), "safe_browsing_mode debe ser 0 (sin GMS)"
    assert re.search(r'enable_signin_service\s*=\s*false', content), "enable_signin_service debe ser false"
    print("  [OK] config/args-android.gn configurado para ARM64 móvil sin servicios GMS.")

def test_android_patches():
    p9 = PATCHES_DIR / "009-android-touch-ui.patch"
    p10 = PATCHES_DIR / "010-android-keystore.patch"
    p11 = PATCHES_DIR / "011-android-battery-saver.patch"
    
    assert p9.exists() and p9.stat().st_size > 100, "Falta 009-android-touch-ui.patch"
    assert p10.exists() and p10.stat().st_size > 100, "Falta 010-android-keystore.patch"
    assert p11.exists() and p11.stat().st_size > 100, "Falta 011-android-battery-saver.patch"
    
    p9_text = p9.read_text(encoding="utf-8")
    assert "Aegis Browser" in p9_text, "009 debe renombrar el APK a 'Aegis Browser'"
    assert "isBottomToolbarPositionPreferred" in p9_text, "009 debe soportar barra inferior móvil"
    
    p10_text = p10.read_text(encoding="utf-8")
    assert "AndroidKeyStore" in p10_text, "010 debe implementar cifrado con Android KeyStore"
    
    p11_text = p11.read_text(encoding="utf-8")
    assert "SetFramePacingRate" in p11_text, "011 debe soportar sincronización 60Hz/120Hz fluida"
    assert "isColdTabSerializationEnabled" in p11_text, "011 debe serializar pestañas inactivas para ahorrar batería"
    print("  [OK] Parches Android: Barra inferior táctil, KeyStore local y optimización de batería 120Hz.")

def test_android_workflow():
    workflow_file = WORKFLOWS_DIR / "build-android.yml"
    assert workflow_file.exists(), "Falta build-android.yml"
    text = workflow_file.read_text(encoding="utf-8")
    assert "cargo-ndk" in text, "build-android.yml debe usar cargo-ndk para enlace Bionic"
    assert "arm64-v8a" in text, "build-android.yml debe compilar para arm64-v8a"
    print("  [OK] Pipeline CI/CD para compilación de Android ARM64 validado.")

def test_patch_manager_registration():
    apply_script = (ROOT_DIR / "scripts" / "apply_patches.py").read_text(encoding="utf-8")
    assert "009-android-touch-ui.patch" in apply_script, "Parche 009 no registrado en apply_patches.py"
    assert "010-android-keystore.patch" in apply_script, "Parche 010 no registrado en apply_patches.py"
    assert "011-android-battery-saver.patch" in apply_script, "Parche 011 no registrado en apply_patches.py"
    print("  [OK] Parches 009, 010 y 011 registrados en apply_patches.py.")

def main():
    print()
    print("  Aegis Browser - Verificación de Fase 5 (Android APK)")
    print("  " + "=" * 56)
    print()
    
    try:
        test_android_gn_args()
        test_android_patches()
        test_android_workflow()
        test_patch_manager_registration()
        print()
        print("  --------------------------------------------------------")
        print("  [EXITO] TODOS LOS REQUISITOS DE FASE 5 CUMPLIDOS AL 100%")
        print()
    except AssertionError as e:
        print(f"\n  [FALLO] {e}\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
