import sys, os
from pathlib import Path

desktop_dir = Path("src/desktop").resolve()
sys.path.insert(0, str(desktop_dir))

import aegis_app
from aegis_app import (
    AegisBrowserWindow, AegisAppMenu, AegisAppMenuItem,
    AegisZoomPopup, AegisShieldsPopup, AegisDownloadsPopup,
    AegisExtensionsPopup, AegisMediaPopup, AegisSidebarWidget,
    FindInPageWidget, THEMES
)
from PyQt6.QtWidgets import QApplication, QFileDialog, QDialog
from PyQt6.QtCore import Qt, QPoint

# Monkeypatch modal dialogs to avoid blocking during automated test
QFileDialog.getSaveFileName = lambda *args, **kwargs: ("", "")
QFileDialog.getOpenFileName = lambda *args, **kwargs: ("", "")
QFileDialog.getExistingDirectory = lambda *args, **kwargs: ""
QDialog.exec = lambda self: 1

app = QApplication.instance() or QApplication(sys.argv)

print("="*60)
print("AUDITORÍA EXHAUSTIVA DE BOTONES Y FUNCIONES")
print("="*60)

errors = []

def run_test(name, func):
    try:
        func()
        print(f"  [OK] {name}")
    except Exception as e:
        import traceback
        err_msg = f"ERROR en {name}: {e}\n{traceback.format_exc()}"
        print(f"  [FAIL] {err_msg}")
        errors.append((name, err_msg))

win = AegisBrowserWindow()
win.show()

# Test 1: Navigation toolbar buttons
def test_nav_buttons():
    win.btn_back.click()
    win.btn_forward.click()
    win.btn_reload.click()
    win.btn_home.click()

run_test("Botones de navegación (Atrás, Adelante, Recargar, Inicio)", test_nav_buttons)

# Test 2: Omnibox actions
def test_omnibox_actions():
    win.copy_clean_url()
    win.security_action.trigger()
    # close site info if opened
    for w in app.topLevelWidgets():
        if w.objectName() == "SiteInfoDialog" or "Información del sitio" in getattr(w, "windowTitle", lambda: "")():
            w.close()
    win.zoom_action.trigger()
    if hasattr(win, "zoom_popup") and win.zoom_popup.isVisible():
        win.zoom_popup.hide()

run_test("Acciones del Omnibox (Copiar limpio, Seguridad, Zoom)", test_omnibox_actions)

# Test 3: Essential Toolbar buttons
def test_toolbar_buttons():
    win.shield_btn.click()
    assert win.shields_popup.isVisible()
    win.shields_popup.hide()

    win.btn_downloads.click()
    assert win.downloads_popup.isVisible()
    win.downloads_popup.hide()

    win.btn_extensions.click()
    assert win.extensions_popup.isVisible()
    win.extensions_popup.hide()

    win.btn_more.click()
    assert win.app_menu.isVisible()
    win.app_menu.hide()

run_test("Botones principales de la barra (Escudo, Descargas, Extensiones, Menú 3 puntos)", test_toolbar_buttons)

# Test 4: Tab bar operations
def test_tab_operations():
    init_count = win.tab_bar.count()
    win.btn_new_tab.click()
    assert win.tab_bar.count() == init_count + 1, "Pestaña no añadida"
    
    # Toggle horizontal / vertical tab orientation
    init_pos = win.config.get("tab_position", "horizontal")
    win.toggle_tab_orientation()
    assert win.config.get("tab_position") != init_pos
    win.toggle_tab_orientation()
    assert win.config.get("tab_position") == init_pos
    
    # Close added tab
    win.close_tab(win.tab_bar.count() - 1)
    assert win.tab_bar.count() == init_count

run_test("Operaciones de pestañas (Añadir, Alternar orientación Vertical/Horizontal, Cerrar)", test_tab_operations)

# Test 5: Zoom Controls & Popup buttons
def test_zoom_controls():
    win.zoom_in()
    assert win.zoom_popup.isVisible() or win.zoom_action.isVisible()
    win.toggle_zoom_popup()
    assert win.zoom_popup.isVisible()
    
    # Test buttons inside zoom popup
    win.zoom_popup.btn_zoom_in.click()
    win.zoom_popup.btn_zoom_out.click()
    win.zoom_popup.btn_reset.click()
    assert round(win.current_view().zoomFactor(), 2) == 1.0
    win.zoom_popup.hide()

run_test("Controles de Zoom y botones de AegisZoomPopup (+, -, Restablecer)", test_zoom_controls)

# Test 6: App Menu (Every item)
def test_app_menu_items():
    menu = win.app_menu
    items = menu.findChildren(AegisAppMenuItem)
    assert len(items) > 0, "No menu items found"
    for it in items:
        if hasattr(it, "callback") and callable(it.callback):
            if it.item_id == "exit":
                continue
            try:
                it.callback()
            except Exception as e:
                raise RuntimeError(f"Fallo al invocar item del menú '{it.item_id}': {e}")
            if win.app_menu.isVisible(): win.app_menu.hide()
            if win.shields_popup.isVisible(): win.shields_popup.hide()
            if win.downloads_popup.isVisible(): win.downloads_popup.hide()
            if win.extensions_popup.isVisible(): win.extensions_popup.hide()
            if hasattr(win, "media_popup") and win.media_popup.isVisible(): win.media_popup.hide()
            if hasattr(win, "find_bar") and win.find_bar.isVisible(): win.find_bar.hide_find()
            for w in app.topLevelWidgets():
                if w != win and w.isWindow() and w.isVisible():
                    w.close()

run_test("Invocación de todos los elementos del Menú de 3 puntos (AegisAppMenu)", test_app_menu_items)

# Test 7: Sidebar tools
def test_sidebar():
    was_hidden = win.sidebar.isHidden()
    win.toggle_sidebar()
    assert win.sidebar.isHidden() != was_hidden
    
    # Show sidebar explicitly for testing internal tools
    win.sidebar.setVisible(True)
    sidebar = win.sidebar
    sidebar.btn_tool_notes.click()
    assert sidebar.stack.currentIndex() == 0
    sidebar.btn_tool_reading.click()
    assert sidebar.stack.currentIndex() == 1
    sidebar.btn_tool_history.click()
    assert sidebar.stack.currentIndex() == 2
    sidebar.btn_tool_bookmarks.click()
    assert sidebar.stack.currentIndex() == 3
    sidebar.btn_tool_pass.click()
    assert sidebar.stack.currentIndex() == 4
    sidebar.btn_tool_shot.click()
    assert sidebar.stack.currentIndex() == 5
    if hasattr(sidebar, "btn_tool_aniplay"):
        sidebar.btn_tool_aniplay.click()
        assert sidebar.stack.currentIndex() == 6
    
    # Test notes save
    sidebar.txt_notes.setPlainText("Test Aegis Notes")
    assert "Test Aegis Notes" in sidebar.txt_notes.toPlainText()
    
    # Close sidebar
    sidebar.btn_close.click()
    assert win.sidebar.isHidden()

run_test("Herramientas de Barra Lateral (Notas, Lectura, Historial, Marcadores, Contraseñas, Captura, AniPlay)", test_sidebar)

# Test 8: Find in Page bar
def test_find_bar():
    win.find_bar.show_find()
    assert win.find_bar.isVisible()
    win.find_bar.input.setText("test")
    win.find_bar.btn_next.click()
    win.find_bar.btn_prev.click()
    win.find_bar.btn_close.click()
    assert not win.find_bar.isVisible()

run_test("Barra de búsqueda en página (FindInPageWidget)", test_find_bar)

# Test 9: Media Control Popup
def test_media_popup():
    win.toggle_media_popup()
    assert win.media_popup.isVisible()
    win.media_popup.btn_prev.click()
    win.media_popup.btn_play_pause.click()
    win.media_popup.btn_next.click()
    win.media_popup.btn_mute.click()
    win.media_popup.hide()

run_test("Control multimedia global (AegisMediaPopup)", test_media_popup)

# Test 10: Internal pages loading
def test_internal_pages():
    pages = ["aegis://start", "aegis://history", "aegis://downloads", "aegis://extensions", "aegis://settings", "aegis://aniplay"]
    v = win.current_view()
    for p in pages:
        win.open_internal_page(p)
        assert v._aegis_virtual_url == p, f"Virtual URL no coincide para {p}"

run_test("Carga y renderizado de páginas internas (aegis://*)", test_internal_pages)

# Test 11: Pinned buttons dynamic creation and context menu
def test_pinning_system():
    items = ["media_control", "sidebar", "theme_toggle", "bookmarks_bar", "history", "reader_mode", "screenshot", "find_in_page", "pip", "aniplay", "settings"]
    for it in items:
        win.pin_toolbar_button(it)
        assert it in win.config.get("pinned_toolbar_buttons", [])
    
    assert win.pinned_layout.count() == len(items), f"Contenedor anclado tiene {win.pinned_layout.count()}, esperaba {len(items)}"
    
    # Test unpinning all
    for it in items:
        win.unpin_toolbar_button(it)
    assert win.pinned_layout.count() == 0

run_test("Sistema dinámico de anclaje de botones a la barra superior", test_pinning_system)

# Test 12: Clear data dialog
def test_clear_data_dialog():
    win.open_clear_data_dialog()
    for w in app.topLevelWidgets():
        if w.objectName() == "ClearDataDialog" or "Eliminar datos" in getattr(w, "windowTitle", lambda: "")():
            w.close()

run_test("Diálogo de limpieza de datos de navegación", test_clear_data_dialog)

win.close()

print("="*60)
if not errors:
    print("RESULTADO: TODOS LOS BOTONES, ACCIONES Y FUNCIONES OPERAN AL 100% SIN ERRORES")
else:
    print(f"RESULTADO: Se encontraron {len(errors)} errores:")
    for name, msg in errors:
        print(f"  * {name}")
print("="*60)
