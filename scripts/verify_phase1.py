#!/usr/bin/env python3
# ==============================================================================
# Aegis Browser - Verificador de Fase 1: Chromium De-Googled
# ==============================================================================
# Verifica que todos los parches de desgooglizado, configuración de privacidad
# y renombrado de identidad cumplan con los estándares requeridos.
#
# Uso: python scripts/verify_phase1.py
# ==============================================================================

import json
import sys
import os
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent
PATCHES_DIR = ROOT_DIR / "patches"
CONFIG_DIR = ROOT_DIR / "config"

def test_patches_exist():
    required_patches = [
        "001-strip-telemetry.patch",
        "002-disable-sync.patch",
        "003-vertical-tabs.patch",
        "004-shields-throttle.patch",
        "005-branding-identity.patch",
    ]
    for patch in required_patches:
        p = PATCHES_DIR / patch
        assert p.exists(), f"Falta el parche: {patch}"
        assert p.stat().st_size > 100, f"El parche {patch} está vacío o incompleto"
    print("  [OK] Todos los 5 parches esenciales de privacidad y branding existen.")

def test_args_gn():
    args_file = CONFIG_DIR / "args.gn"
    assert args_file.exists(), "Falta config/args.gn"
    content = args_file.read_text(encoding="utf-8")
    
    import re
    assert re.search(r'enable_reporting\s*=\s*false', content), "enable_reporting debe ser false"
    assert re.search(r'safe_browsing_mode\s*=\s*0', content), "safe_browsing_mode debe ser 0"
    assert re.search(r'enable_signin_service\s*=\s*false', content), "enable_signin_service debe ser false"
    assert re.search(r'google_api_key\s*=\s*""', content), "google_api_key debe estar vacía"
    print("  [OK] config/args.gn desactiva telemetría, Safe Browsing y API keys.")

def test_default_settings():
    settings_file = CONFIG_DIR / "default_settings.json"
    assert settings_file.exists(), "Falta config/default_settings.json"
    data = json.loads(settings_file.read_text(encoding="utf-8"))
    
    privacy = data.get("privacy", {})
    assert privacy.get("do_not_track_enabled") is True, "Do Not Track debe ser true"
    assert privacy.get("block_third_party_cookies") is True, "Cookies de terceros deben estar bloqueadas"
    assert privacy.get("webrtc_ip_handling_policy") == "default_public_interface_only", "WebRTC no debe filtrar IP local"
    
    tabs = data.get("aegis", {}).get("tabs", {})
    assert tabs.get("vertical_enabled") is False, "Pestañas deben ser horizontales por defecto"
    print("  [OK] default_settings.json configurado con políticas de privacidad estrictas.")

def test_branding():
    patch = (PATCHES_DIR / "005-branding-identity.patch").read_text(encoding="utf-8")
    assert "aegis.exe" in patch, "El binario ejecutable debe renombrarse a aegis.exe"
    assert "Aegis/1.0" in patch, "El User-Agent debe identificar como Aegis/1.0"
    print("  [OK] Identidad y User-Agent de Aegis verificados.")

def main():
    print()
    print("  Aegis Browser - Verificación de Fase 1 (De-Googled)")
    print("  " + "=" * 54)
    print()
    
    try:
        test_patches_exist()
        test_args_gn()
        test_default_settings()
        test_branding()
        print()
        print("  ------------------------------------------------------")
        print("  [EXITO] TODOS LOS REQUISITOS DE FASE 1 CUMPLIDOS AL 100%")
        print()
    except AssertionError as e:
        print(f"\n  [FALLO] {e}\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
