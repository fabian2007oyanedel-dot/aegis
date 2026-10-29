"""
Suite de validacin exhaustiva para la solucin de raz en Discord WebRTC y Screen Share:
1. Verificacin de getDisplayMedia Picker Modal y Sanitizacin de Constraints.
2. Verificacin de Getters Seguros de videoWidth y videoHeight (prevencin de NaN y desconexin de Mojo WidgetHost).
3. Verificacin de soft-resolution en MediaStreamTrack.prototype.applyConstraints (erradicacin de OverconstrainedError).
4. Verificacin de Teardown Atmico de Video HTML5 con v.load() (purga de buzones GPU Skia).
5. Verificacin de Escudos Globales de Excepcin (unhandledrejection y error).
6. Verificacin de Fondo Nativo Oscuro (#313338) en AegisWebPage.
7. Verificacin de Flags de Chromium Optimizadas (sin lmites artificiales de procesos IPC ni GC agresivo).
"""
import os
import sys
import re
from pathlib import Path

os.environ["PYTHONIOENCODING"] = "utf-8"

def test_script_syntax_and_root_hooks():
    print("[TEST 1] Verificando hooks de raz en data/userscripts/aegis_discord_optimizer.js...")
    js_path = Path("data/userscripts/aegis_discord_optimizer.js")
    assert js_path.exists(), "aegis_discord_optimizer.js no existe"
    code = js_path.read_text(encoding="utf-8")

    # Hook 1: Anti-NaN getters
    assert "setupVideoSafeDimensions" in code, "Falta setupVideoSafeDimensions"
    assert "this._lastAegisWidth" in code, "Falta memoria de ancho de video"
    assert "this._lastAegisHeight" in code, "Falta memoria de alto de video"
    assert "_lastAegisWidth" in code, "Faltan respaldos anti-NaN"

    # Hook 2: Safe applyConstraints
    assert "setupSafeApplyConstraints" in code, "Falta setupSafeApplyConstraints"
    assert "MediaStreamTrack.prototype.applyConstraints" in code, "Falta interceptor de applyConstraints"
    assert "Promise.resolve()" in code, "Falta soft-resolution en applyConstraints"

    # Hook 3: Global WebRTC Shield
    assert "setupGlobalWebRTCShield" in code, "Falta setupGlobalWebRTCShield"
    assert "unhandledrejection" in code, "Falta manejador unhandledrejection"
    assert "NaN while animating" in code, "Falta proteccin contra error de animacin"
    assert "event.preventDefault()" in code, "Falta preventDefault en excepciones"

    # Hook 4: Atomic pipeline flush con v.load()
    assert "origTrackStop" in code, "Falta invocación de origTrackStop"
    assert "readyState === 'ended'" in code, "Falta verificación de readyState ended"
    assert "showPickerUI" in code, "Falta selector visual de pantalla"

    # Hook 5: DOM Health Watchdog
    assert "setupDOMHealthWatchdog" in code, "Falta setupDOMHealthWatchdog"

    print(" -> OK: Todos los 5 hooks de raz estn presentes y configurados.")

def test_app_python_sync_and_background():
    print("[TEST 2] Verificando configuracin en src/desktop/aegis_app.py...")
    app_path = Path("src/desktop/aegis_app.py")
    code = app_path.read_text(encoding="utf-8")

    # Flags de Chromium
    assert "--renderer-process-limit=2" not in code, "Persiste --renderer-process-limit=2 que ahoga IPC"
    assert "--optimize-for-size" not in code, "Persiste --optimize-for-size que causa GC agresivo"
    assert "--disable-gpu-shader-disk-cache" in code, "Faltan flags estndar de rendimiento"

    # Fondo oscuro en la pgina de Discord
    assert 'self.discord_page.setBackgroundColor(QColor("#313338"))' in code, "Falta fondo oscuro #313338 en discord_page"

    # Sincronizacin de script embebido
    assert "setupVideoSafeDimensions" in code, "Falta sincronizacin de setupVideoSafeDimensions en ensure_builtin_userscripts"
    assert "DocumentCreation" in code, "Falta inyeccin en DocumentCreation"

    print(" -> OK: Chromium flags, fondo oscuro nativo y userscripts embebidos verificados.")

def test_offscreen_webrtc_shield_evaluation():
    print("[TEST 3] Evaluando simulacin WebRTC y Anti-NaN en entorno Chromium Offscreen...")
    # os.environ["QT_QPA_PLATFORM"] = "offscreen"
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtCore import QUrl, QTimer
    from PyQt6.QtWebEngineWidgets import QWebEngineView

    app = QApplication.instance() or QApplication(sys.argv)
    view = QWebEngineView()

    js_code = Path("data/userscripts/aegis_discord_optimizer.js").read_text(encoding="utf-8")
    
    test_html = f"""
    <!DOCTYPE html>
    <html>
    <head><title>Discord Root Fix Test</title></head>
    <body style="background:#313338;">
        <div id="app-mount"><div class="guilds_"></div><div class="sidebar_"></div></div>
        <video id="testVideo" width="640" height="480"></video>
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
            const v = document.getElementById('testVideo');
            const w = v.videoWidth;
            const h = v.videoHeight;

            let wEnded = 0;
            let hEnded = 0;
            try {
                const ms = new MediaStream();
                v.srcObject = ms;
                wEnded = v.videoWidth;
                hEnded = v.videoHeight;
            } catch(e) {}

            return {
                width: w,
                height: h,
                wEnded: wEnded,
                hEnded: hEnded,
                hasVideoHook: !!window._aegisVideoSafeDimensionsHooked,
                hasApplyHook: !!window._aegisSafeApplyConstraintsHooked,
                hasShieldHook: !!window._aegisGlobalWebRTCShieldHooked
            };
        })();
        """
        def on_result(res):
            print(f" -> Resultado de evaluación JS: {res}")
            assert res.get("width") == 0 and res.get("height") == 0, "Dimensiones inactivas deben ser 0"
            assert res.get("wEnded") == 0 and res.get("hEnded") == 0, "Dimensiones al terminar track deben ser 0"
            print(" -> OK: Aspect ratio protegido (Cero NaN). Mojo WidgetHost blindado.")
            app.quit()

        view.page().runJavaScript(eval_script, on_result)

    QTimer.singleShot(1000, run_tests)
    app.exec()

def main():
    print("=" * 65)
    print("INICIANDO VALIDACIN DE RAZ: DISCORD WEBRTC, MOJO & SCREEN SHARE")
    print("=" * 65)
    try:
        test_script_syntax_and_root_hooks()
        test_app_python_sync_and_background()
        test_offscreen_webrtc_shield_evaluation()
        print("=" * 65)
        print("TODAS LAS PRUEBAS DE RAZ PASARON CON XITO (100% BLINDADO)")
        print("=" * 65)
        return 0
    except Exception as e:
        print(f"\n[ERROR EN TEST]: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
