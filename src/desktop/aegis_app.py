#!/usr/bin/env python3
# ==============================================================================
# Aegis Browser - Aplicación de Escritorio Nativa (Chromium + Rust Shields FFI)
# ==============================================================================
# Navegador web completo con pestañas reales, omnibox para cualquier sitio web,
# historial, marcadores y el motor de bloqueo nativo en Rust (adblock-rust).
# ==============================================================================

import os
import sys
import ctypes
from pathlib import Path

from PyQt6.QtCore import QUrl, Qt, pyqtSignal, QObject
from PyQt6.QtGui import QIcon, QAction, QKeySequence
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QTabWidget, QToolBar, QLabel, QMenu,
    QProgressBar, QStatusBar
)
from PyQt6.QtWebEngineCore import (
    QWebEngineProfile, QWebEnginePage, QWebEngineUrlRequestInterceptor,
    QWebEngineScript, QWebEngineSettings
)
from PyQt6.QtWebEngineWidgets import QWebEngineView

# Rutas del proyecto (Compatible con desarrollo y con PyInstaller .exe)
if getattr(sys, "frozen", False):
    APP_DIR = Path(sys.executable).resolve().parent
    BASE_DIR = APP_DIR.parent.parent
else:
    APP_DIR = Path(__file__).resolve().parent
    BASE_DIR = APP_DIR.parent.parent

if (APP_DIR / "ntp" / "index.html").exists():
    NTP_PATH = APP_DIR / "ntp" / "index.html"
else:
    NTP_PATH = BASE_DIR / "src" / "ui" / "ntp" / "index.html"

NTP_URL = QUrl.fromLocalFile(str(NTP_PATH))
LOGO_PATH = BASE_DIR / "src" / "ui" / "assets" / "aegis-logo.svg"

if (APP_DIR / "aegis_shields.dll").exists():
    RUST_DLL_PATH = APP_DIR / "aegis_shields.dll"
else:
    RUST_DLL_PATH = BASE_DIR / "src" / "shields" / "target" / "release" / "aegis_shields.dll"

# ==============================================================================
# ENLACE FFI CON EL MOTOR RUST (aegis_shields.dll)
# ==============================================================================
class AegisShieldsRustCore:
    def __init__(self):
        self.dll = None
        self.engine = None
        self.total_blocked = 0

        if RUST_DLL_PATH.exists():
            try:
                self.dll = ctypes.CDLL(str(RUST_DLL_PATH))
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
                print("  [OK] Motor nativo Aegis Shields (Rust FFI) inicializado correctamente.")
            except Exception as e:
                print(f"  [AVISO] No se pudo enlazar DLL de Rust: {e}")

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

# Instancia global del motor Rust
SHIELDS_CORE = AegisShieldsRustCore()

# ==============================================================================
# INTERCEPTOR DE PETICIONES DE RED (URLLoaderThrottle en Chromium)
# ==============================================================================
class AegisRequestInterceptor(QWebEngineUrlRequestInterceptor):
    def __init__(self, update_callback=None):
        super().__init__()
        self.update_callback = update_callback

    def interceptRequest(self, info):
        url = info.requestUrl().toString()
        source = info.firstPartyUrl().toString()
        req_type = "other"

        # Comprobar contra el motor adblock-rust
        if SHIELDS_CORE.should_block(url, source, req_type):
            info.block(True)
            if self.update_callback:
                self.update_callback()

# ==============================================================================
# VENTANA PRINCIPAL DEL NAVEGADOR
# ==============================================================================
class AegisBrowserWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Aegis Browser — Privado, Rápido y Sin Anuncios")
        self.resize(1280, 800)
        self.shields_enabled = True

        # Configurar Perfil de Chromium
        self.profile = QWebEngineProfile.defaultProfile()
        self.profile.setHttpUserAgent(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Aegis/1.3"
        )
        self.profile.settings().setAttribute(QWebEngineSettings.WebAttribute.JavascriptCanOpenWindows, False)
        self.profile.settings().setAttribute(QWebEngineSettings.WebAttribute.FullScreenSupportEnabled, True)
        self.profile.settings().setAttribute(QWebEngineSettings.WebAttribute.PlaybackRequiresUserGesture, False)

        # Enlazar interceptor de red
        self.interceptor = AegisRequestInterceptor(self.on_ad_blocked)
        self.profile.setUrlRequestInterceptor(self.interceptor)

        # Inicializar UI
        self.init_ui()

    def init_ui(self):
        # Estilos oscuros modernos
        self.setStyleSheet("""
            QMainWindow {
                background-color: #0b0f17;
            }
            QToolBar {
                background-color: #121824;
                border-bottom: 1px solid rgba(0, 242, 254, 0.2);
                padding: 4px;
                spacing: 6px;
            }
            QPushButton {
                background-color: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 6px;
                color: #e6edf3;
                padding: 5px 10px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: rgba(0, 242, 254, 0.15);
                border-color: #00f2fe;
            }
            QLineEdit {
                background-color: #06090f;
                border: 1px solid rgba(0, 242, 254, 0.3);
                border-radius: 8px;
                color: #f0f6fc;
                padding: 6px 14px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 1px solid #00f2fe;
                background-color: #0c131f;
            }
            QTabWidget::pane {
                border: none;
                background-color: #06090f;
            }
            QTabBar::tab {
                background-color: #0e1522;
                color: #8b949e;
                border: 1px solid rgba(255, 255, 255, 0.06);
                border-bottom: none;
                padding: 8px 16px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                margin-right: 2px;
                font-size: 12px;
            }
            QTabBar::tab:selected {
                background-color: #162032;
                color: #00f2fe;
                font-weight: bold;
                border-top: 2px solid #00f2fe;
            }
            QTabBar::tab:hover {
                background-color: #121c2d;
            }
            QStatusBar {
                background-color: #0a0e16;
                color: #8b949e;
                font-size: 11px;
                border-top: 1px solid rgba(255, 255, 255, 0.05);
            }
        """)

        # Barra de navegación
        toolbar = QToolBar("Navegación")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        # Botón Atrás
        self.btn_back = QPushButton("◀")
        self.btn_back.setToolTip("Atrás")
        self.btn_back.clicked.connect(self.navigate_back)
        toolbar.addWidget(self.btn_back)

        # Botón Adelante
        self.btn_forward = QPushButton("▶")
        self.btn_forward.setToolTip("Adelante")
        self.btn_forward.clicked.connect(self.navigate_forward)
        toolbar.addWidget(self.btn_forward)

        # Botón Recargar
        self.btn_reload = QPushButton("🔄")
        self.btn_reload.setToolTip("Recargar")
        self.btn_reload.clicked.connect(self.reload_page)
        toolbar.addWidget(self.btn_reload)

        # Botón Home (NTP)
        self.btn_home = QPushButton("🏠")
        self.btn_home.setToolTip("Página Principal (Nueva Pestaña)")
        self.btn_home.clicked.connect(self.navigate_home)
        toolbar.addWidget(self.btn_home)

        # Barra de direcciones (Omnibox)
        self.url_bar = QLineEdit()
        self.url_bar.setPlaceholderText("Escribe una URL (ej. youtube.com, animeflv.net, cuevana.biz) o busca...")
        self.url_bar.returnPressed.connect(self.navigate_to_url)
        toolbar.addWidget(self.url_bar)

        # Botón Escudos Aegis Shields (con contador en vivo)
        self.btn_shields = QPushButton(f"🛡️ {SHIELDS_CORE.total_blocked} Bloqueados")
        self.btn_shields.setToolTip("Aegis Shields Activo (Click para ver detalles)")
        self.btn_shields.setStyleSheet("color: #00f2fe; font-weight: bold;")
        self.btn_shields.clicked.connect(self.show_shields_info)
        toolbar.addWidget(self.btn_shields)

        # Botón Nueva Pestaña
        self.btn_new_tab = QPushButton("➕")
        self.btn_new_tab.setToolTip("Abrir Nueva Pestaña (Ctrl+T)")
        self.btn_new_tab.clicked.connect(lambda: self.add_new_tab())
        toolbar.addWidget(self.btn_new_tab)

        # Contenedor de pestañas
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
        self.setCentralWidget(self.tab_widget)

        # Barra de estado inferior
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("🛡️ Aegis Shields ACTIVO: Protección contra anuncios, popups y rastreadores activada.")

        # Atajos de teclado
        self.setup_shortcuts()

        # Abrir pestaña inicial
        self.add_new_tab()

    def setup_shortcuts(self):
        # Ctrl+T: Nueva pestaña
        t_action = QAction(self)
        t_action.setShortcut(QKeySequence("Ctrl+T"))
        t_action.triggered.connect(lambda: self.add_new_tab())
        self.addAction(t_action)

        # Ctrl+W: Cerrar pestaña
        w_action = QAction(self)
        w_action.setShortcut(QKeySequence("Ctrl+W"))
        w_action.triggered.connect(lambda: self.close_tab(self.tab_widget.currentIndex()))
        self.addAction(w_action)

        # Ctrl+R / F5: Recargar
        r_action = QAction(self)
        r_action.setShortcut(QKeySequence("Ctrl+R"))
        r_action.triggered.connect(self.reload_page)
        self.addAction(r_action)

        # Ctrl+L: Enfocar barra de direcciones
        l_action = QAction(self)
        l_action.setShortcut(QKeySequence("Ctrl+L"))
        l_action.triggered.connect(lambda: (self.url_bar.setFocus(), self.url_bar.selectAll()))
        self.addAction(l_action)

    def add_new_tab(self, url: QUrl | None = None, label: str = "Nueva Pestaña"):
        if url is None:
            url = NTP_URL

        view = QWebEngineView()
        page = QWebEnginePage(self.profile, view)
        view.setPage(page)

        # Conectar eventos de la vista
        view.urlChanged.connect(lambda qurl: self.on_url_changed(qurl, view))
        view.loadProgress.connect(self.on_load_progress)
        view.loadFinished.connect(lambda ok: self.on_load_finished(ok, view))

        # Cargar URL
        view.load(url)

        index = self.tab_widget.addTab(view, label)
        self.tab_widget.setCurrentIndex(index)
        return view

    def close_tab(self, index: int):
        if self.tab_widget.count() > 1:
            widget = self.tab_widget.widget(index)
            self.tab_widget.removeTab(index)
            widget.deleteLater()
        else:
            # Si es la última pestaña, reiniciarla en la página de inicio
            current_view = self.current_view()
            if current_view:
                current_view.load(NTP_URL)

    def current_view(self) -> QWebEngineView | None:
        widget = self.tab_widget.currentWidget()
        if isinstance(widget, QWebEngineView):
            return widget
        return None

    def navigate_to_url(self):
        text = self.url_bar.text().strip()
        if not text:
            return

        if text.startswith("http://") or text.startswith("https://") or text.startswith("file:///"):
            url = QUrl(text)
        elif "." in text and " " not in text:
            url = QUrl("https://" + text)
        else:
            # Búsqueda privada con DuckDuckGo
            url = QUrl(f"https://duckduckgo.com/?q={text}")

        current_view = self.current_view()
        if current_view:
            current_view.load(url)

    def navigate_back(self):
        view = self.current_view()
        if view:
            view.back()

    def navigate_forward(self):
        view = self.current_view()
        if view:
            view.forward()

    def reload_page(self):
        view = self.current_view()
        if view:
            view.reload()

    def navigate_home(self):
        view = self.current_view()
        if view:
            view.load(NTP_URL)

    def on_url_changed(self, qurl: QUrl, view: QWebEngineView):
        if view == self.current_view():
            url_str = qurl.toString()
            if url_str == NTP_URL.toString():
                self.url_bar.setText("")
                self.url_bar.setPlaceholderText("Escribe una URL o busca en la web...")
            else:
                self.url_bar.setText(url_str)

    def on_load_progress(self, progress: int):
        self.status_bar.showMessage(f"Cargando página: {progress}%...")

    def on_load_finished(self, ok: bool, view: QWebEngineView):
        current_url = view.url().toString()
        title = view.title() or "Página"
        idx = self.tab_widget.indexOf(view)
        if idx != -1:
            self.tab_widget.setTabText(idx, title[:18] + ("..." if len(title) > 18 else ""))

        if ok and current_url != NTP_URL.toString():
            self.status_bar.showMessage(f"✓ {title} cargado con éxito. Aegis Shields activo.", 4000)

            # Inyectar filtrado cosmético de Rust (ocultar anuncios en YouTube, Twitch, AnimeFLV, Cuevana, etc.)
            cosmetic_css = SHIELDS_CORE.get_cosmetic_css(current_url)
            if cosmetic_css:
                js_inject_css = f"""
                (() => {{
                    try {{
                        let style = document.getElementById('_aegis_cosmetic_style');
                        if (!style) {{
                            style = document.createElement('style');
                            style.id = '_aegis_cosmetic_style';
                            document.head.appendChild(style);
                        }}
                        style.textContent = `{cosmetic_css}`;
                    }} catch (e) {{}}
                }})();
                """
                view.page().runJavaScript(js_inject_css)

            # Inyectar defusers de anti-adblock y bypass de cuentas atrás
            defusers_js = SHIELDS_CORE.get_injected_scripts(current_url)
            if defusers_js:
                view.page().runJavaScript(defusers_js)
        else:
            self.status_bar.showMessage("Listo.", 2000)

    def on_tab_changed(self, index: int):
        view = self.current_view()
        if view:
            self.on_url_changed(view.url(), view)

    def on_ad_blocked(self):
        self.btn_shields.setText(f"🛡️ {SHIELDS_CORE.total_blocked} Bloqueados")

    def show_shields_info(self):
        view = self.current_view()
        current_site = view.url().host() if view else "esta página"
        self.status_bar.showMessage(
            f"🛡️ Aegis Shields: {SHIELDS_CORE.total_blocked} anuncios y rastreadores neutralizados en {current_site}.",
            6000
        )

# ==============================================================================
# PUNTO DE ENTRADA
# ==============================================================================
def main():
    # Habilitar soporte de renderizado acelerado por GPU
    os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = (
        "--enable-gpu-rasterization --enable-zero-copy --ignore-gpu-blocklist "
        "--enable-features=VaapiVideoDecoder,CanvasOopRasterization"
    )

    app = QApplication(sys.argv)
    app.setApplicationName("Aegis Browser")
    app.setApplicationVersion("1.3.0")

    window = AegisBrowserWindow()
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
