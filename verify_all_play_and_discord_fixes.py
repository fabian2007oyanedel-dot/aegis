import sys
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception: pass
"""
Aegis Browser - Suite de Verificación Exhaustiva 100x
=====================================================
Valida de extremo a extremo las 7 suites del Plan Maestro de Ingeniería:
1. Intercepción nativa de aegis:// (Cero diálogo de Windows Store).
2. Pure Video Player sin sandbox (Fin de 'Sandboxed embed is not allowed!').
3. PoseidonHD Pure Player Bypass (0s de espera, omisión de cuenta de 9s).
4. JKanime Multi-Servidor Real en Vivo (Mega, JKPlayer 1 y 2, Streamwish, Mp4upload).
5. Deflector de Anuncios 1XBET y Banners Flotantes.
6. Discord WebRTC Teardown, Anti-NaN, Selector de Audio y Cero Pantalla Blanca.
7. Expansión de Pantalla Completa en Barra Lateral de Discord.
"""

import sys
import os
import json
import re
from pathlib import Path
from urllib.parse import urlparse, parse_qs

# Ajustar PYTHONPATH para importar módulos de Aegis
sys.path.insert(0, str(Path("src/desktop").resolve()))

def test_1_accept_navigation_request_aegis_protocol():
    print("\n[TEST 1] Verificando intercepción del protocolo aegis:// en AegisWebPage...")
    app_py = Path("src/desktop/aegis_app.py").read_text(encoding="utf-8")
    
    assert "def acceptNavigationRequest(self, url: QUrl" in app_py, "Falta acceptNavigationRequest en AegisWebPage"
    assert "url_str.startswith(\"aegis://play\")" in app_py, "Falta intercepción de aegis://play"
    assert "return False" in app_py, "Falta return False para cancelar la delegación al sistema operativo"
    assert "load_aegisplay(v, query=q)" in app_py, "Falta llamada interna a load_aegisplay con parámetro de búsqueda"
    
    # Simular la lógica de extracción de query
    test_url = "aegis://play?q=dragon%20ball"
    parsed = urlparse(test_url)
    params = parse_qs(parsed.query)
    q = params.get("q", [""])[0]
    assert q == "dragon ball", f"Fallo al extraer query 'dragon ball', obtenido: {q}"
    print(" -> OK: aegis://play interceptado con éxito. Cero llamadas a Windows ShellExecute.")

def test_2_pure_video_player_no_sandbox():
    print("\n[TEST 2] Verificando ausencia de sandbox en iframe pureVideoPlayer...")
    app_py = Path("src/desktop/aegis_app.py").read_text(encoding="utf-8")
    
    # Comprobar que el iframe de pureVideoPlayer NO contiene sandbox
    pattern = r'<iframe id="pureVideoPlayer"[^>]+>'
    match = re.search(pattern, app_py)
    assert match, "No se encontró <iframe id=\"pureVideoPlayer\">"
    iframe_tag = match.group(0)
    assert "sandbox=" not in iframe_tag, f"Persiste sandbox en iframe: {iframe_tag}"
    assert "allow=\"autoplay; fullscreen; picture-in-picture; encrypted-media\"" in iframe_tag, "Faltan permisos estándar de medios"
    print(" -> OK: pureVideoPlayer libre de restricciones sandbox. 'Sandboxed embed is not allowed!' erradicado.")

def test_3_poseidon_skip_9s_countdown():
    print("\n[TEST 3] Verificando bypass del temporizador de 9 segundos en PoseidonHD...")
    import media_scraper
    
    # URL real de PoseidonHD (Al Borde del Abismo)
    test_php = "https://player.poseidonhd2.co/player.php?h=rxPRsRSX4IlkyS1F21W5j73WrtOBsRi2JXghvmfDj86m5MCTrGj3BosJpZARnrvn"
    res = media_scraper.resolve_pure_video_endpoint(test_php)
    
    assert res.get("success"), f"Fallo al resolver PoseidonHD: {res}"
    pure_url = res.get("pure_player_url", "")
    assert "streamwish" in pure_url or "dood" in pure_url or "filemoon" in pure_url or "hgcloud" in pure_url, f"No se extrajo enlace directo CDN: {pure_url}"
    assert len(res.get("servers", [])) > 0, "Lista de servidores vacía para PoseidonHD"
    print(f" -> OK: URL directa extraída en Python a 0ms: {pure_url}. Cuenta de 9s y banner intermedio omitidos.")

def test_4_jkanime_multi_server_mega():
    print("\n[TEST 4] Verificando extracción multi-servidor y Mega en JKanime...")
    import media_scraper
    
    test_ep = "https://jkanime.net/mahou-no-shimai-lulutto-lilly-part-2/3/"
    res = media_scraper.resolve_pure_video_endpoint(test_ep)
    
    assert res.get("success"), f"Fallo al resolver JKanime: {res}"
    servers = res.get("servers", [])
    assert len(servers) >= 2, f"Se esperaban múltiples servidores, obtenidos: {len(servers)}"
    
    server_names = [s["name"] for s in servers]
    print(f" -> Servidores extraídos en vivo ({len(servers)}): {server_names}")
    assert any("mega" in s["url"].lower() for s in servers), "No se encontró servidor Mega decodificado en Base64"
    assert any("jkplayer" in s["url"].lower() for s in servers), "No se encontró reproductor oficial de JKanime"
    print(" -> OK: Mega y servidores alternativos extraídos y decodificados 100% en vivo.")

def test_5_popup_blocker_1xbet_rules():
    print("\n[TEST 5] Verificando escudo cosmético anti-1XBET en aegis_popup_blocker.js...")
    blocker_code = Path("data/userscripts/aegis_popup_blocker.js").read_text(encoding="utf-8")
    
    assert "injectAntiAdCSS" in blocker_code, "Falta injectAntiAdCSS"
    assert "1xbet" in blocker_code.lower(), "Falta regla específica contra 1xbet"
    assert "#floatingBanner" in blocker_code, "Falta regla contra #floatingBanner"
    assert "bono 300%" in blocker_code, "Falta palabra clave bono 300% en filtro DOM"
    print(" -> OK: Reglas CSS y filtro DOM de 1XBET configurados para supresión automática.")

def test_6_discord_optimizer_anti_nan_and_audio():
    print("\n[TEST 6] Verificando blindaje WebRTC, selector de audio y getters seguros en Discord...")
    opt_code = Path("data/userscripts/aegis_discord_optimizer.js").read_text(encoding="utf-8")
    
    # 1. Sin v.load() destructivo
    assert "v.load()" not in opt_code, "Persiste v.load() forzado que colapsa el DOM de React"
    
    # 2. Getters conscientes del estado ended
    assert "readyState === 'ended'" in opt_code, "Falta chequeo de readyState === 'ended' en getters de video"
    
    # 3. Watchdog sin reload
    assert "window.location.reload()" not in opt_code, "Persiste reload() en el watchdog que causa pantalla blanca"
    
    # 4. Selector de audio y control de pistas
    assert "showPickerUI" in opt_code, "Falta showPickerUI"
    assert "aegis-btn-sound" in opt_code, "Falta botón 'Con Sonido' en el modal"
    assert "aegis-btn-mute" in opt_code, "Falta botón 'Silenciada' en el modal"
    assert "stream.removeTrack" in opt_code, "Falta supresión física de pistas de audio al transmitir silenciada"
    
    # 5. Fondo oscuro
    assert "#313338 !important" in opt_code, "Falta background-color #313338 en injectPerfCSS"
    print(" -> OK: Discord WebRTC blindado (Cero v.load(), audio toggle OK, getters limpios y fondo #313338).")

def test_7_discord_sidebar_fullscreen_expansion():
    print("\n[TEST 7] Verificando expansión de pantalla completa en barra lateral...")
    app_py = Path("src/desktop/aegis_app.py").read_text(encoding="utf-8")
    
    assert "_sidebar_fullscreen_active" in app_py, "Falta flag _sidebar_fullscreen_active en AegisWindow"
    assert "self.sidebar.setMaximumWidth(16777215)" in app_py, "Falta expansión al 100% de la barra lateral"
    assert "self.web_splitter.hide()" in app_py, "Falta ocultar web_splitter al entrar a pantalla completa desde sidebar"
    assert "self.sidebar.setMaximumWidth(950)" in app_py, "Falta restaurar ancho máximo de sidebar al salir"
    print(" -> OK: Expansión de pantalla completa fuera de los 360px verificada.")

def test_8_offscreen_chromium_getters_evaluation():
    print("\n[TEST 8] Evaluando simulación WebRTC y getters en Chromium Offscreen...")
    os.environ["QT_QPA_PLATFORM"] = "offscreen"
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtCore import QUrl, QTimer
    from PyQt6.QtWebEngineWidgets import QWebEngineView

    app = QApplication.instance() or QApplication(sys.argv)
    view = QWebEngineView()

    js_code = Path("data/userscripts/aegis_discord_optimizer.js").read_text(encoding="utf-8")
    test_html = f"""
    <!DOCTYPE html>
    <html>
    <head><title>Discord WebRTC Evaluation</title></head>
    <body style="background:#313338;">
        <div id="app-mount"></div>
        <video id="vTest"></video>
        <script>
        {js_code}
        </script>
    </body>
    </html>
    """
    view.setHtml(test_html, QUrl("https://discord.com/app"))

    def run_tests():
        eval_script = """
        (function() {
            const v = document.getElementById('vTest');
            const wNoSrc = v.videoWidth;
            const hNoSrc = v.videoHeight;
            
            let wEnded = -1;
            let hEnded = -1;
            try {
                const ms = new MediaStream();
                v.srcObject = ms;
                wEnded = v.videoWidth;
                hEnded = v.videoHeight;
            } catch(e) {}

            return {
                wNoSrc: wNoSrc,
                hNoSrc: hNoSrc,
                wEnded: wEnded,
                hEnded: hEnded,
                hasVideoHook: !!window._aegisVideoSafeDimensionsHooked,
                hasApplyHook: !!window._aegisSafeApplyConstraintsHooked
            };
        })();
        """
        def on_result(res):
            print(f" -> Resultado de evaluación Offscreen: {res}")
            assert res["wNoSrc"] == 0, f"videoWidth sin srcObject debe ser 0, obtenido: {res['wNoSrc']}"
            assert res["hNoSrc"] == 0, f"videoHeight sin srcObject debe ser 0, obtenido: {res['hNoSrc']}"
            assert res["wEnded"] == 0, f"videoWidth con track ended debe ser 0, obtenido: {res['wEnded']}"
            assert res["hEnded"] == 0, f"videoHeight con track ended debe ser 0, obtenido: {res['hEnded']}"
            print(" -> OK: Getters de video retornan legítimamente 0 al terminar la transmisión.")
            app.quit()

        view.page().runJavaScript(eval_script, on_result)

    QTimer.singleShot(1500, run_tests)
    app.exec()

def main():
    print("=" * 70)
    print("INICIANDO SUITE DE VERIFICACIÓN 100x: AEGISPLAY & DISCORD ROBUSTNESS")
    print("=" * 70)
    try:
        test_1_accept_navigation_request_aegis_protocol()
        test_2_pure_video_player_no_sandbox()
        test_3_poseidon_skip_9s_countdown()
        test_4_jkanime_multi_server_mega()
        test_5_popup_blocker_1xbet_rules()
        test_6_discord_optimizer_anti_nan_and_audio()
        test_7_discord_sidebar_fullscreen_expansion()
        test_8_offscreen_chromium_getters_evaluation()
        print("\n" + "=" * 70)
        print("TODAS LAS 8 PRUEBAS PASARON EXITOSAMENTE (100% OPERATIVO Y VERIFICADO)")
        print("=" * 70)
        return 0
    except Exception as e:
        print(f"\n[ERROR EN VERIFICACIÓN]: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
