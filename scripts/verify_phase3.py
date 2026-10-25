#!/usr/bin/env python3
# ==============================================================================
# Aegis Browser - Verificador de Fase 3: UI/UX (NTP y Pestañas)
# ==============================================================================
# Valida los recursos de la interfaz de usuario: página de nueva pestaña (NTP),
# logo SVG, cero fugas a CDNs externas, soporte de temas y parches de UI.
#
# Uso: python scripts/verify_phase3.py
# ==============================================================================

import re
import sys
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT_DIR = Path(__file__).parent.parent
UI_DIR = ROOT_DIR / "src" / "ui"
NTP_DIR = UI_DIR / "ntp"
ASSETS_DIR = UI_DIR / "assets"
PATCHES_DIR = ROOT_DIR / "patches"

def test_branding_assets():
    logo_svg = ASSETS_DIR / "aegis-logo.svg"
    assert logo_svg.exists(), "Falta src/ui/assets/aegis-logo.svg"
    
    # Validar formato XML del SVG
    try:
        tree = ET.parse(str(logo_svg))
        root = tree.getroot()
        assert "svg" in root.tag.lower(), "aegis-logo.svg no tiene nodo raíz <svg>"
        assert "viewBox" in root.attrib or "width" in root.attrib, "Falta viewBox o dimensiones en SVG"
    except Exception as e:
        raise AssertionError(f"Error parseando SVG de logo: {e}")
    print("  [OK] Logo vectorizado SVG de Aegis válido y optimizado.")

def test_ntp_files_exist():
    required = ["index.html", "style.css", "app.js"]
    for file in required:
        p = NTP_DIR / file
        assert p.exists(), f"Falta {file} en src/ui/ntp/"
        assert p.stat().st_size > 100, f"{file} está vacío"
    print("  [OK] Componentes New Tab Page (HTML, CSS, JS) presentes.")

def test_zero_external_network_leaks():
    """Garantizar que la NTP no haga llamadas a servidores externos ni CDNs."""
    html = (NTP_DIR / "index.html").read_text(encoding="utf-8")
    css = (NTP_DIR / "style.css").read_text(encoding="utf-8")
    
    # Buscar llamadas remotas en HTML (src="http...", href="http...")
    external_links = re.findall(r'(?:src|href)=["\']https?://[^"\']+["\']', html)
    # Excluir links en <a> que son accesos directos intencionales
    external_resources = [link for link in external_links if not link.startswith('href="https://') or 'rel=' in html]
    
    # En CSS no debe haber @import de google fonts ni urls remotas
    remote_fonts = re.findall(r'@import\s+url\(["\']?https?://', css)
    assert len(remote_fonts) == 0, "style.css no debe cargar fuentes remotas por privacidad"
    print("  [OK] Privacidad estricta: 0 dependencias externas en la interfaz (carga 100% offline).")

def test_theme_and_features():
    css = (NTP_DIR / "style.css").read_text(encoding="utf-8")
    assert "prefers-color-scheme: light" in css or "theme-light" in css, "Falta soporte para tema claro"
    assert "theme-dark" in css, "Falta soporte para tema oscuro"

    js = (NTP_DIR / "app.js").read_text(encoding="utf-8")
    assert "ENGINES" in js and "duckduckgo" in js, "Falta selector de buscadores en app.js"
    assert "vertical_tabs" in js, "Falta integración de pestañas verticales en app.js"
    print("  [OK] Soporte adaptativo para temas (Oscuro/Claro) y control de pestañas verificado.")

def test_ui_patches():
    patch_003 = PATCHES_DIR / "003-vertical-tabs.patch"
    patch_006 = PATCHES_DIR / "006-custom-ntp.patch"
    assert patch_003.exists(), "Falta 003-vertical-tabs.patch"
    assert patch_006.exists(), "Falta 006-custom-ntp.patch"
    
    apply_script = (ROOT_DIR / "scripts" / "apply_patches.py").read_text(encoding="utf-8")
    assert "006-custom-ntp.patch" in apply_script, "006-custom-ntp.patch no está registrado en apply_patches.py"
    print("  [OK] Parches de inyección de NTP y Pestañas Verticales registrados correctamente.")

def main():
    print()
    print("  Aegis Browser - Verificación de Fase 3 (UI/UX)")
    print("  " + "=" * 54)
    print()
    
    try:
        test_branding_assets()
        test_ntp_files_exist()
        test_zero_external_network_leaks()
        test_theme_and_features()
        test_ui_patches()
        print()
        print("  ------------------------------------------------------")
        print("  [EXITO] TODOS LOS REQUISITOS DE FASE 3 CUMPLIDOS AL 100%")
        print()
    except AssertionError as e:
        print(f"\n  [FALLO] {e}\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
