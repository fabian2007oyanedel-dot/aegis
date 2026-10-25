#!/usr/bin/env python3
# ==============================================================================
# Aegis Browser - Minimalist, High-Performance Native Desktop Browser
# ==============================================================================
# Clean, modern architecture: Top Tab Strip, Floating Capsule Omnibox,
# Chromium Engine (PyQt6-WebEngine), and Brave Shields (adblock-rust) FFI.
# ==============================================================================

import os
import sys
import ctypes
from pathlib import Path

from PyQt6.QtCore import QUrl, Qt, QSize
from PyQt6.QtGui import QIcon, QAction, QKeySequence, QFont
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QTabBar, QStackedWidget, QLabel,
    QProgressBar, QSizePolicy
)
from PyQt6.QtWebEngineCore import (
    QWebEngineProfile, QWebEnginePage, QWebEngineUrlRequestInterceptor,
    QWebEngineSettings
)
from PyQt6.QtWebEngineWidgets import QWebEngineView

# ==============================================================================
# LOCALIZACIÓN RESILIENTE DE RECURSOS
# ==============================================================================
def find_project_root() -> Path:
    candidates = [
        Path(sys.executable).resolve().parent,
        Path(sys.executable).resolve().parent.parent,
        Path(sys.executable).resolve().parent.parent.parent,
        Path(__file__).resolve().parent,
        Path(__file__).resolve().parent.parent.parent,
        Path.cwd(),
    ]
    for c in candidates:
        if (c / "src" / "ui" / "ntp" / "index.html").exists():
            return c
        if (c / "ntp" / "index.html").exists():
            return c
    return Path(__file__).resolve().parent.parent.parent

ROOT_DIR = find_project_root()

def get_ntp_html_content() -> str:
    possible_paths = [
        ROOT_DIR / "src" / "ui" / "ntp" / "index.html",
        ROOT_DIR / "ntp" / "index.html",
        Path.cwd() / "src" / "ui" / "ntp" / "index.html",
        Path.cwd() / "dist" / "Aegis" / "ntp" / "index.html",
    ]
    for p in possible_paths:
        if p.exists():
            try:
                html = p.read_text(encoding="utf-8")
                # Incrustar CSS si existe al lado
                css_p = p.parent / "style.css"
                if css_p.exists():
                    css_content = css_p.read_text(encoding="utf-8")
                    html = html.replace('<link rel="stylesheet" href="style.css">', f"<style>{css_content}</style>")
                return html
            except Exception:
                pass
    return MINIMAL_EMBEDDED_NTP

def find_rust_dll() -> Path | None:
    possible = [
        ROOT_DIR / "src" / "shields" / "target" / "release" / "aegis_shields.dll",
        ROOT_DIR / "aegis_shields.dll",
        Path(sys.executable).resolve().parent / "aegis_shields.dll",
        Path.cwd() / "dist" / "Aegis" / "aegis_shields.dll",
        Path.cwd() / "src" / "shields" / "target" / "release" / "aegis_shields.dll",
    ]
    for p in possible:
        if p.exists():
            return p
    return None

# ==============================================================================
# ENLACE CON EL MOTOR RUST (adblock-rust FFI)
# ==============================================================================
class AegisShieldsRustCore:
    def __init__(self):
        self.dll = None
        self.engine = None
        self.total_blocked = 0

        dll_path = find_rust_dll()
        if dll_path and dll_path.exists():
            try:
                self.dll = ctypes.CDLL(str(dll_path))
                self.dll.aegis_shields_create.restype = ctypes.c_void_p
                self.dll.aegis_shields_destroy.argtypes = [ctypes.c_void_p]
                self.dll.aegis_shields_should_block.argtypes = [
                    ctypes.c_void_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p
                ]
                self.dll.aegis_shields_should_block.restype = ctypes.c_bool
                self.dll.aegis_shields_get_cosmetic_stylesheet.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
                self.dll.aegis_shields_get_cosmetic_stylesheet.restype = ctypes.c_void_p
                self.dll.aegis_shields_get_injected_scripts.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
                self.dll.aegis_shields_get_injected_scripts.restype = ctypes.c_void_p
                self.dll.aegis_shields_free_string.argtypes = [ctypes.c_void_p]

                self.engine = self.dll.aegis_shields_create()
                print("  [OK] Aegis Shields Core (Rust) cargado con éxito.")
            except Exception as e:
                print(f"  [AVISO] No se pudo vincular la DLL Rust: {e}")

    def should_block(self, url: str, source_url: str = "", req_type: str = "other") -> bool:
        if not self.dll or not self.engine:
            return False
        try:
            blocked = self.dll.aegis_shields_should_block(
                self.engine,
                url.encode("utf-8"),
                source_url.encode("utf-8") if source_url else None,
                req_type.encode("utf-8")
            )
            if blocked:
                self.total_blocked += 1
            return blocked
        except Exception:
            return False

    def get_cosmetic_css(self, url: str) -> str:
        if not self.dll or not self.engine:
            return ""
        try:
            ptr = self.dll.aegis_shields_get_cosmetic_stylesheet(self.engine, url.encode("utf-8"))
            if ptr:
                css = ctypes.c_char_p(ptr).value.decode("utf-8", errors="replace")
                self.dll.aegis_shields_free_string(ptr)
                return css
        except Exception:
            pass
        return ""

    def get_injected_scripts(self, url: str) -> str:
        if not self.dll or not self.engine:
            return ""
        try:
            ptr = self.dll.aegis_shields_get_injected_scripts(self.engine, url.encode("utf-8"))
            if ptr:
                js = ctypes.c_char_p(ptr).value.decode("utf-8", errors="replace")
                self.dll.aegis_shields_free_string(ptr)
                return js
        except Exception:
            pass
        return ""

SHIELDS_CORE = AegisShieldsRustCore()

# ==============================================================================
# INTERCEPTOR DE RED DE CHROMIUM
# ==============================================================================
class AegisRequestInterceptor(QWebEngineUrlRequestInterceptor):
    def __init__(self, callback=None):
        super().__init__()
        self.callback = callback

    def interceptRequest(self, info):
        url = info.requestUrl().toString()
        source = info.firstPartyUrl().toString()
        if SHIELDS_CORE.should_block(url, source, "other"):
            info.block(True)
            if self.callback:
                self.callback()

# ==============================================================================
# VENTANA PRINCIPAL (DISEÑO MINIMALISTA Y ELEGANTE)
# ==============================================================================
class AegisBrowserWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Aegis")
        self.resize(1300, 840)

        # Configurar Perfil Chromium
        self.profile = QWebEngineProfile.defaultProfile()
        self.profile.setHttpUserAgent(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Aegis/1.3"
        )
        self.profile.settings().setAttribute(QWebEngineSettings.WebAttribute.JavascriptCanOpenWindows, False)
        self.profile.settings().setAttribute(QWebEngineSettings.WebAttribute.FullScreenSupportEnabled, True)
        self.profile.settings().setAttribute(QWebEngineSettings.WebAttribute.PlaybackRequiresUserGesture, False)

        # Interceptor de red
        self.interceptor = AegisRequestInterceptor(self.on_shield_block)
        self.profile.setUrlRequestInterceptor(self.interceptor)

        self.views = []
        self.init_modern_ui()

    def init_modern_ui(self):
        # ── Estilos CSS de Clase Mundial (Paleta Obsidian & Soft Titanium) ─────
        self.setStyleSheet("""
            QMainWindow {
                background-color: #0b0e14;
            }
            QWidget#TabHeader {
                background-color: #0b0e14;
                border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            }
            QTabBar {
                background: transparent;
                border: none;
            }
            QTabBar::tab {
                background-color: #0e1219;
                color: #7d8590;
                border: 1px solid rgba(255, 255, 255, 0.04);
                border-bottom: none;
                padding: 6px 14px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                margin-right: 3px;
                font-size: 12px;
                font-family: 'Segoe UI', -apple-system, sans-serif;
                min-width: 90px;
                max-width: 220px;
            }
            QTabBar::tab:hover {
                background-color: #141923;
                color: #c9d1d9;
            }
            QTabBar::tab:selected {
                background-color: #161c28;
                color: #f0f6fc;
                border: 1px solid rgba(56, 189, 248, 0.25);
                border-bottom: none;
                border-top: 2px solid #38bdf8;
            }
            QPushButton#NewTabBtn {
                background: transparent;
                border: none;
                color: #7d8590;
                font-size: 16px;
                font-weight: 300;
                border-radius: 12px;
                width: 24px;
                height: 24px;
            }
            QPushButton#NewTabBtn:hover {
                background-color: rgba(255, 255, 255, 0.08);
                color: #f0f6fc;
            }
            QWidget#Toolbar {
                background-color: #101520;
                border-bottom: 1px solid rgba(255, 255, 255, 0.04);
            }
            QPushButton.nav-icon-btn {
                background: transparent;
                border: none;
                color: #8b949e;
                font-size: 15px;
                border-radius: 14px;
                width: 30px;
                height: 30px;
            }
            QPushButton.nav-icon-btn:hover {
                background-color: rgba(255, 255, 255, 0.08);
                color: #f0f6fc;
            }
            QPushButton.nav-icon-btn:pressed {
                background-color: rgba(255, 255, 255, 0.12);
            }
            QLineEdit#Omnibox {
                background-color: #07090e;
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 16px;
                color: #f0f6fc;
                padding: 5px 16px;
                font-size: 12.5px;
                font-family: 'Segoe UI', sans-serif;
                selection-background-color: #1d4ed8;
            }
            QLineEdit#Omnibox:focus {
                border: 1px solid rgba(56, 189, 248, 0.6);
                background-color: #090d14;
            }
            QPushButton#ShieldPill {
                background-color: rgba(16, 185, 129, 0.08);
                border: 1px solid rgba(16, 185, 129, 0.25);
                border-radius: 13px;
                color: #10b981;
                font-size: 11.5px;
                font-weight: 600;
                padding: 4px 11px;
            }
            QPushButton#ShieldPill:hover {
                background-color: rgba(16, 185, 129, 0.16);
                border-color: #10b981;
            }
            QProgressBar#MicroProgress {
                border: none;
                background: transparent;
                height: 2px;
            }
            QProgressBar#MicroProgress::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #38bdf8, stop:1 #818cf8);
            }
        """)

        # Contenedor Maestro
        container = QWidget()
        self.setCentralWidget(container)
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ── 1. Fila Superior: Tiras de Pestañas (Tab Strip) ─────────────────────
        tab_header = QWidget()
        tab_header.setObjectName("TabHeader")
        tab_header_layout = QHBoxLayout(tab_header)
        tab_header_layout.setContentsMargins(10, 6, 10, 0)
        tab_header_layout.setSpacing(4)

        self.tab_bar = QTabBar()
        self.tab_bar.setTabsClosable(True)
        self.tab_bar.setMovable(True)
        self.tab_bar.currentChanged.connect(self.on_tab_changed)
        self.tab_bar.tabCloseRequested.connect(self.close_tab)
        tab_header_layout.addWidget(self.tab_bar)

        self.btn_new_tab = QPushButton("+")
        self.btn_new_tab.setObjectName("NewTabBtn")
        self.btn_new_tab.setToolTip("Nueva Pestaña (Ctrl+T)")
        self.btn_new_tab.clicked.connect(lambda: self.add_new_tab())
        tab_header_layout.addWidget(self.btn_new_tab)

        tab_header_layout.addStretch()
        main_layout.addWidget(tab_header)

        # ── 2. Fila Media: Barra de Navegación y Omnibox Flotante ─────────────
        toolbar = QWidget()
        toolbar.setObjectName("Toolbar")
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(10, 6, 10, 6)
        toolbar_layout.setSpacing(6)

        # Botones de navegación
        self.btn_back = QPushButton("←")
        self.btn_back.setProperty("class", "nav-icon-btn")
        self.btn_back.setToolTip("Atrás")
        self.btn_back.clicked.connect(self.navigate_back)
        toolbar_layout.addWidget(self.btn_back)

        self.btn_forward = QPushButton("→")
        self.btn_forward.setProperty("class", "nav-icon-btn")
        self.btn_forward.setToolTip("Adelante")
        self.btn_forward.clicked.connect(self.navigate_forward)
        toolbar_layout.addWidget(self.btn_forward)

        self.btn_reload = QPushButton("↻")
        self.btn_reload.setProperty("class", "nav-icon-btn")
        self.btn_reload.setToolTip("Recargar")
        self.btn_reload.clicked.connect(self.reload_page)
        toolbar_layout.addWidget(self.btn_reload)

        self.btn_home = QPushButton("⌂")
        self.btn_home.setProperty("class", "nav-icon-btn")
        self.btn_home.setToolTip("Inicio (Nueva Pestaña)")
        self.btn_home.clicked.connect(self.navigate_home)
        toolbar_layout.addWidget(self.btn_home)

        # Omnibox Cápsula
        self.url_bar = QLineEdit()
        self.url_bar.setObjectName("Omnibox")
        self.url_bar.setPlaceholderText("Buscar en la web o ingresar dirección...")
        self.url_bar.returnPressed.connect(self.navigate_to_url)
        toolbar_layout.addWidget(self.url_bar)

        # Píldora de Aegis Shields
        self.shield_pill = QPushButton("🛡️ 0")
        self.shield_pill.setObjectName("ShieldPill")
        self.shield_pill.setToolTip("Aegis Shields Activo (adblock-rust FFI)")
        toolbar_layout.addWidget(self.shield_pill)

        main_layout.addWidget(toolbar)

        # ── 3. Micro Barra de Progreso (2px) ──────────────────────────────────
        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("MicroProgress")
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(2)
        self.progress_bar.hide()
        main_layout.addWidget(self.progress_bar)

        # ── 4. Pila de Vistas Web (QStackedWidget) ────────────────────────────
        self.stack = QStackedWidget()
        main_layout.addWidget(self.stack)

        self.setup_shortcuts()

        # Abrir pestaña inicial
        self.add_new_tab()

    def setup_shortcuts(self):
        QAction(self, shortcut=QKeySequence("Ctrl+T"), triggered=lambda: self.add_new_tab())
        QAction(self, shortcut=QKeySequence("Ctrl+W"), triggered=lambda: self.close_tab(self.tab_bar.currentIndex()))
        QAction(self, shortcut=QKeySequence("Ctrl+R"), triggered=self.reload_page)
        QAction(self, shortcut=QKeySequence("F5"), triggered=self.reload_page)
        QAction(self, shortcut=QKeySequence("Ctrl+L"), triggered=lambda: (self.url_bar.setFocus(), self.url_bar.selectAll()))

    def add_new_tab(self, url_str: str | None = None, label: str = "Nueva Pestaña"):
        view = QWebEngineView()
        page = QWebEnginePage(self.profile, view)
        view.setPage(page)

        view.urlChanged.connect(lambda qurl: self.on_url_changed(qurl, view))
        view.loadProgress.connect(self.on_load_progress)
        view.loadFinished.connect(lambda ok: self.on_load_finished(ok, view))

        self.views.append(view)
        stack_idx = self.stack.addWidget(view)
        tab_idx = self.tab_bar.addTab(label)

        if url_str:
            view.load(QUrl(url_str))
        else:
            # Cargar HTML seguro de la New Tab Page
            html = get_ntp_html_content()
            view.setHtml(html, QUrl("aegis://start"))

        self.tab_bar.setCurrentIndex(tab_idx)
        self.stack.setCurrentIndex(stack_idx)
        return view

    def close_tab(self, index: int):
        if self.tab_bar.count() > 1:
            view = self.views.pop(index)
            self.tab_bar.removeTab(index)
            self.stack.removeWidget(view)
            view.deleteLater()
        else:
            current = self.current_view()
            if current:
                html = get_ntp_html_content()
                current.setHtml(html, QUrl("aegis://start"))
                self.tab_bar.setTabText(0, "Nueva Pestaña")

    def current_view(self) -> QWebEngineView | None:
        idx = self.tab_bar.currentIndex()
        if 0 <= idx < len(self.views):
            return self.views[idx]
        return None

    def on_tab_changed(self, index: int):
        if 0 <= index < len(self.views):
            self.stack.setCurrentIndex(index)
            view = self.views[index]
            self.on_url_changed(view.url(), view)

    def navigate_to_url(self):
        text = self.url_bar.text().strip()
        if not text:
            return

        if text.startswith("http://") or text.startswith("https://") or text.startswith("file://") or text.startswith("aegis://"):
            target_url = QUrl(text)
        elif "." in text and " " not in text:
            target_url = QUrl("https://" + text)
        else:
            target_url = QUrl(f"https://duckduckgo.com/?q={text}")

        view = self.current_view()
        if view:
            view.load(target_url)

    def navigate_back(self):
        v = self.current_view()
        if v: v.back()

    def navigate_forward(self):
        v = self.current_view()
        if v: v.forward()

    def reload_page(self):
        v = self.current_view()
        if v: v.reload()

    def navigate_home(self):
        v = self.current_view()
        if v:
            html = get_ntp_html_content()
            v.setHtml(html, QUrl("aegis://start"))

    def on_url_changed(self, qurl: QUrl, view: QWebEngineView):
        if view == self.current_view():
            url_str = qurl.toString()
            if url_str == "aegis://start" or url_str == "about:blank":
                self.url_bar.setText("")
                self.url_bar.setPlaceholderText("Buscar en la web o ingresar dirección...")
            else:
                self.url_bar.setText(url_str)

    def on_load_progress(self, progress: int):
        if progress < 100:
            self.progress_bar.show()
            self.progress_bar.setValue(progress)
        else:
            self.progress_bar.hide()

    def on_load_finished(self, ok: bool, view: QWebEngineView):
        self.progress_bar.hide()
        current_url = view.url().toString()
        title = view.title() or "Página"

        if current_url == "aegis://start":
            title = "Nueva Pestaña"

        idx = self.views.index(view) if view in self.views else -1
        if idx != -1:
            display_title = title if len(title) <= 16 else title[:14] + "…"
            self.tab_bar.setTabText(idx, display_title)

        if ok and current_url != "aegis://start":
            # Inyección cosmética de Rust
            css = SHIELDS_CORE.get_cosmetic_css(current_url)
            if css:
                inject_css = f"""
                (() => {{
                    try {{
                        let s = document.getElementById('_aegis_css');
                        if (!s) {{
                            s = document.createElement('style');
                            s.id = '_aegis_css';
                            document.head.appendChild(s);
                        }}
                        s.textContent = `{css}`;
                    }} catch(e) {{}}
                }})();
                """
                view.page().runJavaScript(inject_css)

            # Inyección de defusers de anti-adblock
            js = SHIELDS_CORE.get_injected_scripts(current_url)
            if js:
                view.page().runJavaScript(js)

    def on_shield_block(self):
        self.shield_pill.setText(f"🛡️ {SHIELDS_CORE.total_blocked}")

# ==============================================================================
# PLANTILLA HTML ELEGANTE Y MINIMALISTA INCORPORADA (FAIL-SAFE)
# ==============================================================================
MINIMAL_EMBEDDED_NTP = """
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <title>Aegis</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background: radial-gradient(circle at 50% 15%, #121824 0%, #080a0f 65%, #05060a 100%);
      color: #f0f6fc;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 2rem;
      user-select: none;
    }
    .hero {
      text-align: center;
      max-width: 680px;
      width: 100%;
    }
    .clock {
      font-size: 4.8rem;
      font-weight: 200;
      letter-spacing: -2px;
      color: #f8fafc;
      margin-bottom: 0.25rem;
      font-variant-numeric: tabular-nums;
    }
    .date {
      font-size: 0.95rem;
      color: #8b949e;
      font-weight: 400;
      margin-bottom: 2.5rem;
      letter-spacing: 0.5px;
      text-transform: capitalize;
    }
    .search-box {
      position: relative;
      width: 100%;
      margin-bottom: 2.5rem;
    }
    .search-input {
      width: 100%;
      background: rgba(255, 255, 255, 0.04);
      border: 1px solid rgba(255, 255, 255, 0.1);
      border-radius: 999px;
      padding: 14px 24px;
      font-size: 15px;
      color: #f0f6fc;
      outline: none;
      backdrop-filter: blur(12px);
      transition: all 0.25s ease;
    }
    .search-input:focus {
      background: rgba(255, 255, 255, 0.08);
      border-color: rgba(56, 189, 248, 0.5);
      box-shadow: 0 0 24px rgba(56, 189, 248, 0.15);
    }
    .shortcuts-grid {
      display: flex;
      gap: 1.25rem;
      justify-content: center;
      flex-wrap: wrap;
    }
    .shortcut-card {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 0.5rem;
      text-decoration: none;
      color: #c9d1d9;
      font-size: 0.8rem;
      padding: 12px 16px;
      border-radius: 14px;
      background: rgba(255, 255, 255, 0.03);
      border: 1px solid rgba(255, 255, 255, 0.05);
      transition: all 0.2s ease;
      min-width: 82px;
    }
    .shortcut-card:hover {
      background: rgba(255, 255, 255, 0.08);
      border-color: rgba(255, 255, 255, 0.15);
      transform: translateY(-2px);
      color: #ffffff;
    }
    .shortcut-icon {
      font-size: 1.6rem;
    }
    .footer-badge {
      position: fixed;
      bottom: 1.5rem;
      display: flex;
      align-items: center;
      gap: 0.5rem;
      font-size: 0.75rem;
      color: #6e7681;
    }
    .shield-dot {
      width: 7px;
      height: 7px;
      background: #10b981;
      border-radius: 50%;
      box-shadow: 0 0 8px #10b981;
    }
  </style>
</head>
<body>
  <main class="hero">
    <div id="clock" class="clock">12:00</div>
    <div id="date" class="date">Cargando...</div>

    <form class="search-box" action="https://duckduckgo.com" method="GET">
      <input type="text" name="q" class="search-input" placeholder="Buscar con DuckDuckGo o ingresar URL..." autofocus autocomplete="off">
    </form>

    <div class="shortcuts-grid">
      <a href="https://youtube.com" class="shortcut-card">
        <span class="shortcut-icon">▶</span>
        <span>YouTube</span>
      </a>
      <a href="https://twitch.tv" class="shortcut-card">
        <span class="shortcut-icon">🟣</span>
        <span>Twitch</span>
      </a>
      <a href="https://animeflv.net" class="shortcut-card">
        <span class="shortcut-icon">⚡</span>
        <span>AnimeFLV</span>
      </a>
      <a href="https://cuevana.biz" class="shortcut-card">
        <span class="shortcut-icon">🎬</span>
        <span>Cuevana</span>
      </a>
      <a href="https://curseforge.com" class="shortcut-card">
        <span class="shortcut-icon">🔨</span>
        <span>CurseForge</span>
      </a>
      <a href="https://reddit.com" class="shortcut-card">
        <span class="shortcut-icon">🤖</span>
        <span>Reddit</span>
      </a>
      <a href="https://github.com" class="shortcut-card">
        <span class="shortcut-icon">🐙</span>
        <span>GitHub</span>
      </a>
    </div>
  </main>

  <div class="footer-badge">
    <div class="shield-dot"></div>
    <span>Aegis Shields Activo · adblock-rust FFI · Cero Telemetría</span>
  </div>

  <script>
    function updateClock() {
      const now = new Date();
      const h = String(now.getHours()).padStart(2, '0');
      const m = String(now.getMinutes()).padStart(2, '0');
      document.getElementById('clock').textContent = `${h}:${m}`;

      const options = { weekday: 'long', month: 'long', day: 'numeric' };
      document.getElementById('date').textContent = now.toLocaleDateString('es-ES', options);
    }
    updateClock();
    setInterval(updateClock, 1000);
  </script>
</body>
</html>
"""

def main():
    os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = (
        "--enable-gpu-rasterization --enable-zero-copy --ignore-gpu-blocklist "
        "--enable-features=VaapiVideoDecoder,CanvasOopRasterization"
    )

    app = QApplication(sys.argv)
    app.setApplicationName("Aegis")
    app.setApplicationVersion("1.3.0")

    window = AegisBrowserWindow()
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
