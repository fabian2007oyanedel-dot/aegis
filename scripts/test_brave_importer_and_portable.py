import sys
import os
import shutil
import tempfile
from pathlib import Path

# Agregar directorio src/desktop al sys.path
sys.path.insert(0, str(Path("src/desktop").resolve()))

from aegis_app import BraveImporter, HistoryManager, BookmarksManager, IS_PORTABLE

def test_brave_import():
    print("=" * 60)
    print("PROBANDO IMPORTADOR DE BRAVE BROWSER")
    print("=" * 60)

    # 1. Detectar perfiles de Brave
    profiles = BraveImporter.find_brave_profiles()
    print(f"Perfiles detectados de Brave: {[p['name'] for p in profiles]}")
    assert len(profiles) > 0, "No se detectó el perfil de Brave en el equipo."

    default_prof = profiles[0]
    hist_count = default_prof["history_count"]
    bm_count = default_prof["bookmarks_count"]
    print(f"Perfil: {default_prof['name']} -> {hist_count} visitas registradas, {bm_count} marcadores.")
    assert hist_count > 0, "El historial de Brave debería tener visitas."

    # 2. Probar importación en managers aislados
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        hist_mgr = HistoryManager()
        hist_mgr.data = {"frequent": {}, "history": []}

        bm_mgr = BookmarksManager()
        bm_mgr.bookmarks = []

        imported_h, imported_b = BraveImporter.import_all(
            default_prof["path"],
            hist_mgr,
            bm_mgr,
            import_hist=True,
            import_bm=True
        )

        print(f"[OK] Importación exitosa: {imported_h} visitas importadas, {imported_b} marcadores generados.")
        assert imported_h > 0, "Se debieron importar visitas de historial."
        assert imported_b > 0, "Se debieron importar o generar marcadores de sitios top."
        assert len(hist_mgr.data["frequent"]) > 0, "Deben haberse poblado los sitios frecuentes."

        sample_hist = hist_mgr.data["history"][0]
        print(f"  Muestra de historial importado: '{sample_hist['title']}' ({sample_hist['url']})")
        print(f"  Muestra de frecuentes: {list(hist_mgr.data['frequent'].keys())[:5]}")
        print(f"  Muestra de marcadores: {[b['title'] for b in bm_mgr.bookmarks[:5]]}")

def test_portable_paths():
    print("\n" + "=" * 60)
    print("PROBANDO RESOLUCIÓN DE RUTAS DE MODO PORTABLE")
    print("=" * 60)
    import aegis_app
    print(f"BASE_DIR: {aegis_app.BASE_DIR}")
    print(f"IS_PORTABLE detectado actualmente: {aegis_app.IS_PORTABLE}")
    print(f"CONFIG_FILE: {aegis_app.CONFIG_FILE}")
    print(f"HISTORY_FILE: {aegis_app.HISTORY_FILE}")
    print(f"BOOKMARKS_FILE: {aegis_app.BOOKMARKS_FILE}")
    print(f"PROFILE_DIR: {aegis_app.PROFILE_DIR}")
    print("[OK] Verificación de rutas de modo portable completada.")

if __name__ == "__main__":
    test_brave_import()
    test_portable_paths()
    print("\n" + "=" * 60)
    print("TODAS LAS PRUEBAS DE IMPORTACIÓN DE BRAVE Y PORTABLE PASARON CON ÉXITO")
    print("=" * 60)
