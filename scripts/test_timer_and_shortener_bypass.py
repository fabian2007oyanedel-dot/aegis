import sys, os
from pathlib import Path

desktop_dir = Path("src/desktop").resolve()
sys.path.insert(0, str(desktop_dir))

import aegis_app
from aegis_app import (
    USERSCRIPTS_DIR, ensure_builtin_userscripts, AegisBrowserWindow,
    get_settings_html, get_extensions_html
)
from PyQt6.QtWidgets import QApplication

app = QApplication.instance() or QApplication(sys.argv)

print("="*60)
print("VERIFICACIÓN DE BYPASS DE TEMPORIZADORES Y ACORTADORES")
print("="*60)

# 1. Ensure scripts generated
ensure_builtin_userscripts(USERSCRIPTS_DIR)
script_path = USERSCRIPTS_DIR / "aegis_timer_bypass.js"
assert script_path.exists(), "aegis_timer_bypass.js no existe en USERSCRIPTS_DIR"
code = script_path.read_text(encoding="utf-8")
assert len(code) > 500, "Script aegis_timer_bypass.js vacío o incompleto"

# Check key bypass modules in script
assert "curseforge.com" in code, "Falta módulo CurseForge"
assert "adf.ly" in code, "Falta módulo Adf.ly"
assert "decodeAdfly" in code, "Falta decodificador ysmm Adf.ly"
assert "mega.nz" in code, "Falta módulo Mega.nz"
assert "adfoc.us" in code, "Falta módulo AdFoc.us"
assert "mediafire.com" in code, "Falta módulo Mediafire"
assert "linkvertise.com" in code, "Falta módulo Linkvertise"
assert "sub2unlock.com" in code, "Falta módulo Sub2Unlock"
assert "universalTimerBypass" in code, "Falta acelerador universal de temporizadores"
print("[OK] 1. Userscript aegis_timer_bypass.js verificado con todos los módulos requeridos.")

# 2. Verify window integration
win = AegisBrowserWindow()
win.show()

# Verify scripts injected in profile
scripts = [s for s in win.profile.scripts().toList() if "Bypass" in s.name() or s.name() == "aegis_timer_bypass"]
assert len(scripts) > 0, "Script aegis_timer_bypass no inyectado en QWebEngineProfile"
bypass_script = scripts[0]
assert bypass_script.runsOnSubFrames() == True, "Debe ejecutarse en subframes para saltar acortadores en iframes"
print("[OK] 2. aegis_timer_bypass cargado en el perfil de WebEngine con soporte de subframes.")

# 3. Verify toggle in Shields Popup
assert hasattr(win.shields_popup, "cb_countdown"), "cb_countdown no existe en AegisShieldsPopup"
assert win.shields_popup.cb_countdown.isChecked() == True, "cb_countdown debe estar activado por defecto"

# Test toggling
win.shields_popup.cb_countdown.setChecked(False)
assert win.config.get("bypass_countdown") == False, "Config no actualizada tras desmarcar"
win.shields_popup.cb_countdown.setChecked(True)
assert win.config.get("bypass_countdown") == True, "Config no actualizada tras marcar"
print("[OK] 3. Control de activación en AegisShieldsPopup verificado.")

# 4. Verify settings HTML and extensions HTML
settings_html = get_settings_html("theme-dark", win.config)
assert "Bypass de temporizadores y acortadores" in settings_html, "Opción no visible en aegis://settings"
assert "CurseForge, Mega, Adf.ly" in settings_html, "Descripción de servicios no presente en settings"

exts_html = get_extensions_html("theme-dark", [], [])
assert "Aegis Fast Timer & Shortener Bypass" in exts_html, "Bypass no visible en aegis://extensions"
print("[OK] 4. Páginas internas aegis://settings y aegis://extensions reflejan el módulo de bypass.")

win.close()
print("="*60)
print("TODAS LAS PRUEBAS DE BYPASS PASARON EXITOSAMENTE (100% OK)")
print("="*60)
