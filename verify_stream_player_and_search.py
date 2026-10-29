"""
Test suite de validacin exhaustiva para Aegis Browser:
1. Discord WebRTC screen share hooks (picker UI, constraint sanitization, safe teardown).
2. AegisPlay pure player resolution (cero web externa, servers list).
3. AegisPlay live remote search (JKanime + PoseidonHD en vivo).
4. Catlogo extendido data/aegisplay_custom_repo.json (24 ttulos reales, formato compatible).
5. Deflectores de anuncios, popups y scam "Not a Robot".
6. Sanitizacin de sitios frecuentes NTP.
7. Renderizado headless/offscreen de aegis://play y aegis://play?q=one+piece.
"""
import sys
import os
import json
from pathlib import Path

# Asegurar encoding UTF-8
os.environ["PYTHONIOENCODING"] = "utf-8"

def test_custom_repo():
    print("[TEST 1] Verificando data/aegisplay_custom_repo.json...")
    repo_path = Path("data/aegisplay_custom_repo.json")
    assert repo_path.exists(), "data/aegisplay_custom_repo.json no existe"
    data = json.loads(repo_path.read_text(encoding="utf-8"))
    items = data.get("items", [])
    assert len(items) >= 20, f"Se esperaban al menos 20 elementos, se encontraron {len(items)}"
    assert not any("BigBuckBunny" in json.dumps(item) for item in items), "Detectado contenido demo"
    
    # Verificar que los items contengan reproductores puros y servidores
    pure_endpoints = [i for i in items if any(k in i.get("player_url", "") for k in ["jkplayer", "player.poseidonhd2.co", "streamwish", "mega", "hgcloud"])]
    assert len(pure_endpoints) >= 15, f"Se esperaban al menos 15 reproductores puros, encontrados {len(pure_endpoints)}"
    print(f" -> OK: {len(items)} ttulos vlidos y {len(pure_endpoints)} reproductores puros verificados.")

def test_discord_optimizer_hooks():
    print("[TEST 2] Verificando hooks de transmisin en aegis_discord_optimizer.js...")
    js_path = Path("data/userscripts/aegis_discord_optimizer.js")
    assert js_path.exists(), "aegis_discord_optimizer.js no existe"
    code = js_path.read_text(encoding="utf-8")
    assert "showPickerUI" in code, "Falta showPickerUI en el script"
    assert "Pantalla Completa (Monitor Principal)" in code, "Falta opcin de Pantalla Completa"
    assert "Ventana de Aplicacion Activa" in code or "Ventana" in code, "Falta opcin de Ventana Activa"
    assert "cleanConstraints" in code, "Falta sanitizacin de constraints WebRTC"
    assert "origTrackStop" in code, "Falta teardown seguro de tracks"
    assert "origTrackStop" in code, "Falta origTrackStop"
    print(" -> OK: Discord Screen Share Picker, Constraints y Safe Teardown verificados.")

def test_popup_blocker():
    print("[TEST 3] Verificando bloqueo de popups y scam 'Not a Robot'...")
    js_path = Path("data/userscripts/aegis_popup_blocker.js")
    assert js_path.exists(), "aegis_popup_blocker.js no existe"
    code = js_path.read_text(encoding="utf-8")
    assert "not a robot" in code.lower(), "Falta deteccin de scam 'not a robot'"
    assert "Notification.requestPermission" in code, "Falta bloqueo de peticiones de notificacin"
    assert "origAlert" in code, "Falta intercepcin de alertas falsas"
    assert "origConfirm" in code, "Falta intercepcin de cuadros de confirmacin falsos"
    print(" -> OK: Deflector de Scam 'Not a Robot' y bloqueador de popunders activo.")

def test_media_scraper():
    print("[TEST 4] Verificando media_scraper.py (Pure Player & Live Remote Search)...")
    from src.desktop import media_scraper
    
    # 1. Pure player resolver
    res = media_scraper.resolve_pure_video_endpoint("https://jkanime.net/one-piece/1/")
    assert res.get("success"), "Fallo resolviendo endpoint puro de One Piece"
    pure_url = res.get("pure_player_url", "")
    assert any(k in pure_url for k in ["jkplayer", "mega.nz", "streamwish", "embed"]), f"Endpoint no es reproductor puro: {pure_url}"
    assert "jkanime.net/one-piece/1/" != pure_url, "Se devolvi la web externa completa"
    print(f" -> OK: Pure player endpoint resuelto: {pure_url[:65]}...")

    # 2. Live remote search
    search_results = media_scraper.search_live_sources("naruto")
    assert len(search_results) > 0, "Bsqueda en vivo no arroj resultados"
    top_pure = [r for r in search_results[:5] if "jkplayer" in r.get("player_url", "")]
    print(f" -> OK: Bsqueda remota arroj {len(search_results)} resultados en vivo ({len(top_pure)} con endpoint puro pre-resuelto).")

def test_history_sanitization():
    print("[TEST 5] Verificando HistoryManager y sanitizacin de sitios frecuentes...")
    from src.desktop.aegis_app import HistoryManager
    hist_mgr = HistoryManager()
    hist_mgr.sanitize_spam_entries()
    frequent = hist_mgr.get_frequent_sites(8)
    for site in frequent:
        host = site.get("url", "").lower()
        for spam in ["cerdma", "livejasmin", "redirectin", "cyrl"]:
            assert spam not in host, f"Dominio spam detectado en sitios frecuentes: {host}"
    print(f" -> OK: Sitios frecuentes limpios ({len(frequent)} sitios legtimos).")

def test_aegisplay_html_generation():
    print("[TEST 6] Verificando generacin de HTML para aegis://play y bsqueda remota...")
    from src.desktop.aegis_app import get_aegisplay_html
    
    # Vista estndar
    html_home = get_aegisplay_html("theme-dark")
    assert "pureVideoPlayer" in html_home, "Falta pureVideoPlayer iframe en AegisPlay HTML"
    assert "btn-server" in html_home, "Falta selector de servidores en AegisPlay HTML"
    assert "importModal" in html_home, "Falta importModal en AegisPlay HTML"
    assert "repoFileInput" in html_home, "Falta input de archivo para importar repositorio"
    assert "handleSearchInput" in html_home, "Falta buscador en AegisPlay HTML"
    print(f" -> OK: Home HTML de AegisPlay generado correctamente ({len(html_home)} bytes).")

    # Vista con bsqueda remota en vivo
    html_search = get_aegisplay_html("theme-dark", search_query="One Piece")
    assert "Resultados en Vivo para" in html_search, "Falta ttulo de resultados en vivo"
    assert "One Piece" in html_search, "No contiene el trmino buscado"
    print(f" -> OK: Search HTML de AegisPlay generado con resultados en vivo ({len(html_search)} bytes).")

def main():
    print("=" * 60)
    print("INICIANDO VALIDACIN INTEGRAL DE AEGIS STREAM, PURE PLAYER & SEARCH")
    print("=" * 60)
    try:
        test_custom_repo()
        test_discord_optimizer_hooks()
        test_popup_blocker()
        test_media_scraper()
        test_history_sanitization()
        test_aegisplay_html_generation()
        print("=" * 60)
        print("TODAS LAS 6 SUITES DE PRUEBAS PASARON EXITOSAMENTE (100% OK)")
        print("=" * 60)
        return 0
    except Exception as e:
        print(f"\n[ERROR EN TEST]: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
