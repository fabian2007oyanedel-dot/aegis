import os
import sys
import json
import re
from pathlib import Path

os.environ["QT_QPA_PLATFORM"] = "offscreen"
sys.path.insert(0, str(Path("src/desktop").resolve()))

def test_1_discord_drawer_scroller():
    print("\n--- Test 1: Discord Drawer Scroller & Event Bridge ---")
    js_file = Path("data/userscripts/aegis_discord_optimizer.js")
    assert js_file.exists(), "data/userscripts/aegis_discord_optimizer.js no existe"
    text = js_file.read_text(encoding="utf-8")
    
    assert 'flex-direction: column !important;' in text, "Falta flex-direction: column en sidebar_"
    assert 'height: 100vh !important;' in text, "Falta height: 100vh en sidebar_"
    assert 'max-height: 100vh !important;' in text, "Falta max-height: 100vh en sidebar_"
    assert 'overflow-y: auto !important;' in text, "Falta overflow-y: auto en scroller_"
    assert 'section[class*="panels_"]' in text, "Falta sección panels en userscript"
    assert 'flex-shrink: 0 !important;' in text, "Falta flex-shrink: 0 en panels"
    assert "document.addEventListener('wheel'" in text, "Falta wheel event bridge"
    print("  [PASS] Reglas CSS de Discord Drawer y Event Bridge verificados al 100%.")

def test_2_aegisplay_crest_logo():
    print("\n--- Test 2: Aegis Cyber-Prism Crest Vector Logo ---")
    from PyQt6.QtWidgets import QApplication
    from aegis_app import create_aegisplay_icon
    
    app = QApplication.instance() or QApplication(sys.argv)
    
    icon_dark = create_aegisplay_icon("#ff3366", 20)
    assert not icon_dark.isNull(), "Icono oscuro de AegisPlay es nulo"
    
    icon_light = create_aegisplay_icon("#d32f2f", 20)
    assert not icon_light.isNull(), "Icono claro de AegisPlay es nulo"
    
    icon_tab = create_aegisplay_icon("#388bfd", 14)
    assert not icon_tab.isNull(), "Icono de pestaña es nulo"
    
    print("  [PASS] Nuevo emblema Aegis Cyber-Prism Crest genera QIcons vectoriales válidos (Dark, Light, Tab).")

def test_3_real_media_scraper():
    print("\n--- Test 3: Motor de Scraping en Vivo (Cero Demos) ---")
    import media_scraper
    cat = media_scraper.get_live_catalog(force_refresh=False)
    assert isinstance(cat, dict), "El catálogo no es un diccionario"
    items = cat.get("items", [])
    assert len(items) >= 20, f"Se esperaban >= 20 items reales, obtenidos: {len(items)}"
    
    # Comprobar que no hay videos de prueba de Google Cloud
    sample_videos = ["bigbuckbunny", "elephantsdream", "tearsofsteel", "forbiggerblazes"]
    for it in items:
        v_url = (it.get("player_url") or it.get("video_url") or "").lower()
        for sv in sample_videos:
            assert sv not in v_url, f"Elemento contiene video demo prohibido: {it['title']} -> {v_url}"
        assert it.get("title"), "Elemento sin título"
        assert it.get("poster"), "Elemento sin póster"
        assert it.get("type") in ("anime", "movie", "pelicula", "series"), f"Tipo no reconocido: {it.get('type')}"

    anime_count = sum(1 for i in items if i.get("type") == "anime")
    movie_count = sum(1 for i in items if i.get("type") in ("movie", "pelicula"))
    print(f"  [PASS] Catálogo en vivo verificado: {len(items)} títulos ({anime_count} anime, {movie_count} películas). Cero demos.")

def test_4_aegisplay_frontend_html():
    print("\n--- Test 4: aegis://play Frontend & Hybrid Player ---")
    import aegis_app
    html_dark = aegis_app.get_aegisplay_html("theme-dark")
    assert "AegisPlay" in html_dark, "Falta marca AegisPlay"
    assert "secureEmbedPlayer" in html_dark, "Falta secureEmbedPlayer iframe en modal"
    assert "videoPlayer" in html_dark, "Falta videoPlayer nativo en modal"
    assert "btnSyncLive" in html_dark, "Falta botón de sincronización en vivo"
    assert "DEFAULT_CATALOG" in html_dark, "Falta inyección de DEFAULT_CATALOG"
    assert "forceLiveSync" in html_dark, "Falta función forceLiveSync en JS"
    print("  [PASS] Plantilla aegis://play y reproductor híbrido blindado verificados.")

def test_5_offscreen_window_and_navigation():
    print("\n--- Test 5: Offscreen Aegis Browser Navigation ---")
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtCore import QTimer, QUrl
    import aegis_app
    
    app = QApplication.instance() or QApplication(sys.argv)
    win = aegis_app.AegisBrowserWindow()
    
    # Verificar que el botón de AegisPlay en el dock tiene icono
    dock_btn = win.vertical_dock.btn_aegisplay
    assert not dock_btn.icon().isNull(), "El botón de AegisPlay en el dock no tiene icono"
    
    # Navegar a aegis://play
    view = win.current_view()
    win.open_internal_page("aegis://play")
    assert view._aegis_virtual_url == "aegis://play", "Virtual URL no coincide con aegis://play"
    
    print("  [PASS] AegisBrowserWindow inicializado con dock y navegación interna a aegis://play exitosa.")
    win.close()

if __name__ == "__main__":
    print("=========================================================")
    print("      AEGIS BROWSER - SUITE DE VALIDACIÓN FINAL          ")
    print("=========================================================")
    try:
        test_1_discord_drawer_scroller()
        test_2_aegisplay_crest_logo()
        test_3_real_media_scraper()
        test_4_aegisplay_frontend_html()
        test_5_offscreen_window_and_navigation()
        print("\n=========================================================")
        print("   >>> TODAS LAS PRUEBAS (5/5) PASARON EXITOSAMENTE <<<  ")
        print("=========================================================")
    except Exception as e:
        print(f"\n[FAIL] ERROR EN PRUEBA: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
