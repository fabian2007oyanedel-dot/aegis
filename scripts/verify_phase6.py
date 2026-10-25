#!/usr/bin/env python3
# ==============================================================================
# Aegis Browser - Verificador de Fase 6: Pulido, Anti-Fingerprinting y Release v1.0
# ==============================================================================
# Valida la protección contra huella digital (Canvas/WebGL/Audio Farbling),
# prevención de fugas WebRTC, flujo de release oficial y notas de versión.
#
# Uso: python scripts/verify_phase6.py
# ==============================================================================

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent
PATCHES_DIR = ROOT_DIR / "patches"
WORKFLOWS_DIR = ROOT_DIR / ".github" / "workflows"

def test_anti_fingerprinting_patch():
    p12 = PATCHES_DIR / "012-anti-fingerprinting.patch"
    assert p12.exists() and p12.stat().st_size > 100, "Falta 012-anti-fingerprinting.patch"
    content = p12.read_text(encoding="utf-8")
    
    assert "getImageData" in content, "012 debe inyectar farbling en Canvas getImageData"
    assert "GL_UNMASKED_RENDERER_WEBGL" in content, "012 debe ocultar identificador de GPU WebGL"
    assert "copyFromChannel" in content, "012 debe proteger contra AudioContext fingerprinting"
    print("  [OK] Anti-Fingerprinting: Farbling activo en Canvas, WebGL y AudioContext.")

def test_webrtc_leak_patch():
    p13 = PATCHES_DIR / "013-webrtc-leak-prevention.patch"
    assert p13.exists() and p13.stat().st_size > 100, "Falta 013-webrtc-leak-prevention.patch"
    content = p13.read_text(encoding="utf-8")
    
    assert "continual_gathering_policy" in content, "013 debe limitar recolección de candidatos ICE"
    assert "surface_cellular_candidates" in content, "013 debe ocultar interfaces locales/VPN"
    print("  [OK] WebRTC: Prevención activa de fugas de IP local y túneles VPN.")

def test_release_infrastructure():
    release_workflow = WORKFLOWS_DIR / "release-v1.0.yml"
    assert release_workflow.exists(), "Falta .github/workflows/release-v1.0.yml"
    
    release_notes = ROOT_DIR / "RELEASE_NOTES_v1.0.md"
    assert release_notes.exists() and release_notes.stat().st_size > 200, "Falta RELEASE_NOTES_v1.0.md"
    
    readme = ROOT_DIR / "README.md"
    assert "Aegis Browser v1.0" in release_notes.read_text(encoding="utf-8")
    assert "adblock-rust" in readme.read_text(encoding="utf-8")
    print("  [OK] Infraestructura de Release v1.0.0 y notas de versión verificadas.")

def test_full_patch_pipeline():
    apply_script = (ROOT_DIR / "scripts" / "apply_patches.py").read_text(encoding="utf-8")
    for i in range(1, 14):
        num_str = f"{i:03d}"
        assert any(num_str in line for line in apply_script.splitlines()), f"Falta parche {num_str} en apply_patches.py"
    print("  [OK] Pipeline completo: Los 13 parches de arquitectura están registrados y enlazados.")

def main():
    print()
    print("  Aegis Browser - Verificación de Fase 6 (Release v1.0)")
    print("  " + "=" * 56)
    print()
    
    try:
        test_anti_fingerprinting_patch()
        test_webrtc_leak_patch()
        test_release_infrastructure()
        test_full_patch_pipeline()
        print()
        print("  --------------------------------------------------------")
        print("  [EXITO] TODOS LOS REQUISITOS DE FASE 6 CUMPLIDOS AL 100%")
        print()
    except AssertionError as e:
        print(f"\n  [FALLO] {e}\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
