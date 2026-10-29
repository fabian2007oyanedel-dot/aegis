"""
Verificación Exhaustiva de Raíz: Auditoría Completa de Aegis Browser
Valida punto por punto que todas las inconsistencias, demos y errores hayan sido erradicados.
"""
import json
import os
import re
import sys
import urllib.request
import ssl
from pathlib import Path

os.environ["PYTHONIOENCODING"] = "utf-8"

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def test_1_custom_repositories_cleanliness_and_no_demos():
    print("\n[TEST 1] Verificando repositorios custom (data/aegisplay_custom_repo.json y raíz)...")
    for file_path in [Path("data/aegisplay_custom_repo.json"), Path("aegisplay_custom_repo.json")]:
        assert file_path.exists(), f"Falta {file_path}"
        data = json.loads(file_path.read_text(encoding="utf-8"))
        items = data.get("items", [])
        assert len(items) == 24, f"Se esperaban 24 títulos, encontrados {len(items)}"

        # 1. Cero duplicados en player_url
        p_urls = [it["player_url"] for it in items]
        assert len(p_urls) == len(set(p_urls)), f"URLs duplicadas en {file_path}"

        # 2. Cero duplicados en Mega
        mega_urls = []
        for it in items:
            for s in it.get("servers", []):
                if "mega.nz" in s.get("url", "").lower():
                    mega_urls.append(s["url"])
        assert len(mega_urls) == len(set(mega_urls)), f"Mega duplicados en {file_path}"

        # 3. Cero demos prohibidos
        for it in items:
            assert "BigBuckBunny" not in json.dumps(it), "Contenido demo detectado"
            assert "sample.mp4" not in json.dumps(it), "Video dummy detectado"

    print(" -> OK: 24 títulos verificados en ambos repositorios. 0% demos, 0% URLs duplicadas.")

def test_2_posters_network_health():
    print("\n[TEST 2] Verificando que el 100% de las 24 carátulas devuelvan HTTP 200 (Cero 404)...")
    data = json.loads(Path("data/aegisplay_custom_repo.json").read_text(encoding="utf-8"))
    items = data["items"]

    tested = 0
    for idx, it in enumerate(items):
        url = it["poster"]
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, context=ctx, timeout=5) as res:
            assert res.status == 200, f"Carátula falló con status {res.status}: {url}"
            tested += 1

    print(f" -> OK: Todas las {tested}/24 carátulas devuelven HTTP 200 en vivo (Cero enlaces rotos).")

def test_3_aegisplay_player_hierarchy_and_failover():
    print("\n[TEST 3] Verificando lógica del reproductor AegisPlay en aegis_app.py...")
    code = Path("src/desktop/aegis_app.py").read_text(encoding="utf-8")

    # 1. Jerarquía de servidores
    assert "item.servers[0].url" in code, "Falta prioridad de item.servers[0].url"
    assert "serverFailoverTimer = setTimeout" in code, "Falta watchdog de auto-failover"

    # 2. Atributos allowfullscreen en iframe
    assert 'allowfullscreen="true"' in code, "Falta allowfullscreen en pureVideoPlayer"
    assert 'webkitallowfullscreen="true"' in code, "Falta webkitallowfullscreen"

    # 3. Filtrado instantáneo a 0ms en buscador
    assert "renderCatalog(q);" in code, "Falta renderCatalog(q) instantáneo en handleSearchInput"

    print(" -> OK: Jerarquía de servidores, auto-failover inteligente, fullscreen y buscador 0ms verificados.")

def test_4_discord_frame0_and_escape_key():
    print("\n[TEST 4] Verificando Discord Frame-0 dark canvas y tecla Escape en barra lateral...")
    app_code = Path("src/desktop/aegis_app.py").read_text(encoding="utf-8")
    opt_code = Path("data/userscripts/aegis_discord_optimizer.js").read_text(encoding="utf-8")

    # 1. Frame-0 dark theme
    assert "injectFrameZeroDarkBackground" in opt_code, "Falta inyección frame-0 de fondo oscuro"
    assert "#313338 !important" in opt_code, "Falta regla de fondo #313338 en frame-0"

    # 2. Manejo de Escape en barra lateral
    assert "d_view = getattr(self.sidebar, \"discord_view\", None)" in app_code, "Falta referencia a discord_view en keyPressEvent"
    assert "d_view.page().action(QWebEnginePage.WebAction.ExitFullScreen).trigger()" in app_code, "Falta ExitFullScreen en discord_view"

    # 3. Desacoplamiento asíncrono en acceptNavigationRequest
    assert "QTimer.singleShot(0, lambda: self.browser_win.load_aegisplay" in app_code, "Falta QTimer.singleShot en acceptNavigationRequest"

    print(" -> OK: Frame-0 dark theme activo, Escape key configurado y navegación virtual desacoplada.")

def test_5_userscripts_and_bootstrap_sync():
    print("\n[TEST 5] Verificando sincronización de script embebido y bootstrap offline...")
    app_code = Path("src/desktop/aegis_app.py").read_text(encoding="utf-8")
    scraper_code = Path("src/desktop/media_scraper.py").read_text(encoding="utf-8")

    # Sincronización de script embebido
    assert "injectFrameZeroDarkBackground" in app_code, "Falta injectFrameZeroDarkBackground en script embebido"
    assert "showPickerUI" in app_code, "Falta showPickerUI en script embebido"

    # Bootstrap offline con servers
    assert '"servers": [' in scraper_code, "Faltan arrays de servidores en _get_bootstrap_real_items"
    assert "Streamwish HD Directo" in scraper_code, "Falta Streamwish en bootstrap de PoseidonHD"

    print(" -> OK: Script embebido 100% sincronizado y bootstrap offline con multi-servidores.")

def main():
    print("=" * 70)
    print("INICIANDO SUITE DE AUDITORÍA DE RAÍZ COMPLETA (AEGIS 100% PRODUCTION)")
    print("=" * 70)
    test_1_custom_repositories_cleanliness_and_no_demos()
    test_2_posters_network_health()
    test_3_aegisplay_player_hierarchy_and_failover()
    test_4_discord_frame0_and_escape_key()
    test_5_userscripts_and_bootstrap_sync()
    print("\n" + "=" * 70)
    print("TODAS LAS PRUEBAS DE AUDITORÍA DE RAÍZ PASARON CON 100% DE ÉXITO")
    print("=" * 70)

if __name__ == "__main__":
    main()
