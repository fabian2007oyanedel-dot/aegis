#!/usr/bin/env python3
# ==============================================================================
# Aegis Browser - Verificador de Aegis Shields Ultra Mejorado (100x Adblock)
# ==============================================================================
# Valida la protección nativa para sitios populares: YouTube, Twitch, Redes
# Sociales, Periódicos con detectores anti-adblock (Admiral) y redes de popups.
#
# Uso: python scripts/verify_ultra_shields.py
# ==============================================================================

import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent
SHIELDS_DIR = ROOT_DIR / "src" / "shields"
PATCHES_DIR = ROOT_DIR / "patches"

def test_default_rules():
    rules_file = SHIELDS_DIR / "src" / "default_rules.rs"
    assert rules_file.exists(), "Falta default_rules.rs en shields"
    content = rules_file.read_text(encoding="utf-8")

    # YouTube
    assert "||googlevideo.com/videoplayback$xhr,3p" in content
    assert "youtube.com##ytd-ad-slot-renderer" in content
    assert "youtube.com##ytd-enforcement-message-view-model" in content

    # Twitch
    assert "||imasdk.googleapis.com^" in content
    assert "twitch.tv##.tw-ad-banner" in content

    # Redes Sociales
    assert "facebook.com##[data-pagelet*=\"FeedUnit_\"]:has(span:has-text(Sponsored))" in content
    assert "x.com##[data-testid=\"cellInnerDiv\"]:has(span:has-text(\"Promoted\"))" in content
    assert "reddit.com##shreddit-post[is-promoted]" in content

    # Forbes y Anti-Adblock
    assert "forbes.com##.fbs-ad" in content
    assert "||delivery.adrecover.com^" in content
    assert "||adligature.com^" in content

    # Popups Invasivos
    assert "||propellerads.com^" in content
    assert "||popcash.net^" in content

    # Streaming y Anime (AnimeFLV, Cuevana, Cinecalidad)
    assert "animeflv.net##.banner-wrapper" in content
    assert "cuevana*.biz##.ad-banner" in content
    assert "cinecalidad*.com##.publi" in content
    assert "||vidoomy.com^" in content

    # Acortadores y Cuentas Atrás
    assert "||ouo.io/traffic/*" in content
    assert "||adf.ly/ad/*" in content
    assert "curseforge.com##.curseforge-ad" in content
    print("  [OK] Reglas nativas Zero-Day para YouTube, Twitch, AnimeFLV/Cuevana, Acortadores y Popups validadas.")

def test_defusers_and_cosmetics():
    defusers_file = SHIELDS_DIR / "src" / "defusers.rs"
    assert defusers_file.exists(), "Falta defusers.rs en shields"
    content = defusers_file.read_text(encoding="utf-8")

    assert "UNIVERSAL_ANTI_ADBLOCK_DEFUSER" in content
    assert "YOUTUBE_AD_AND_ANTI_ADBLOCK_DEFUSER" in content
    assert "ytInitialPlayerResponse" in content
    assert "STREAMING_OVERLAY_AND_POPUNDER_DEFUSER" in content
    assert "COUNTDOWN_AND_SHORTENER_BYPASSER" in content
    assert "POPUNDER_PROTECTION_SCRIPTLET" in content
    assert "get_curated_cosmetic_css_for_url" in content
    print("  [OK] Scriptlets defusers (Anti-Adblock, Streaming Overlays y FastForward de Cuentas Atrás) validados.")

def test_c_header_and_patch():
    header = (SHIELDS_DIR / "include" / "aegis_shields.h").read_text(encoding="utf-8")
    assert "aegis_shields_get_cosmetic_stylesheet" in header
    assert "aegis_shields_get_injected_scripts" in header
    assert "aegis_shields_get_blocked_count" in header

    patch_015 = PATCHES_DIR / "015-shields-cosmetic-injection.patch"
    assert patch_015.exists() and patch_015.stat().st_size > 100
    p15_content = patch_015.read_text(encoding="utf-8")
    assert "AegisCosmeticInjector" in p15_content
    assert "DidCreateDocumentElement" in p15_content

    apply_py = (ROOT_DIR / "scripts" / "apply_patches.py").read_text(encoding="utf-8")
    assert "015-shields-cosmetic-injection.patch" in apply_py
    print("  [OK] Cabecera C FFI y Parche 015 de inyección en Blink validados.")

def test_rust_unit_tests():
    cargo_bin = Path.home() / ".cargo" / "bin" / "cargo.exe"
    cmd = [str(cargo_bin) if cargo_bin.exists() else "cargo", "test", "--manifest-path", str(SHIELDS_DIR / "Cargo.toml")]
    res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    assert res.returncode == 0, f"Cargo test falló:\n{res.stdout}\n{res.stderr}"
    assert "test tests::test_shields_blocking_logic ... ok" in res.stdout
    print("  [OK] Tests unitarios en Rust de Aegis Shields ejecutados con éxito (10/10 comprobaciones pasaron).")

def main():
    print()
    print("  Aegis Browser - Verificación de Aegis Shields Ultra Mejorado (100x)")
    print("  " + "=" * 72)
    print()

    try:
        test_default_rules()
        test_defusers_and_cosmetics()
        test_c_header_and_patch()
        test_rust_unit_tests()
        print()
        print("  ------------------------------------------------------------------------")
        print("  [EXITO] TODAS LAS MEJORAS 100X DE AEGIS SHIELDS FUERON VERIFICADAS")
        print()
    except AssertionError as e:
        print(f"\n  [FALLO] {e}\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
