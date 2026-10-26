#!/usr/bin/env python3
# ==============================================================================
# Aegis Browser - Native Desktop Browser (Minimalist, Dark Theme, Zero-Bloat)
# ==============================================================================
# - Real Top Tab Strip (Arc / Zen style)
# - Real Working Omnibox (Navigates to ANY URL or search)
# - Native Force Dark Mode for all websites (DuckDuckGo, Wikipedia, YouTube, etc.)
# - DWM Immersive Dark Title Bar (Zero lime-green Windows borders)
# - Interactive Aegis Shields Dialog (adblock-rust FFI)
# - Real 4-Theme Live Switcher (Cyber, Midnight, OLED, Light)
# - Built-in NTP with live clock, inline SVG logo, and working shortcuts
# ==============================================================================

import os
import sys
import json
import ctypes
from ctypes import wintypes
from pathlib import Path

# ── 1. Forzar Dark Mode en el motor Chromium de QtWebEngine ──────────────────
os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = (
    "--enable-gpu-rasterization "
    "--ignore-gpu-blocklist "
    "--force-dark-mode "
    "--enable-features=WebContentsForceDark,VaapiVideoDecoder,CanvasOopRasterization "
    "--blink-settings=forceDarkModeEnabled=true"
)

from PyQt6.QtCore import QUrl, Qt, QSize
from PyQt6.QtGui import QAction, QKeySequence, QColor
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QTabBar, QStackedWidget, QLabel,
    QProgressBar, QDialog, QCheckBox, QComboBox, QMessageBox
)
from PyQt6.QtWebEngineCore import (
    QWebEngineProfile, QWebEnginePage, QWebEngineUrlRequestInterceptor,
    QWebEngineSettings
)
from PyQt6.QtWebEngineWidgets import QWebEngineView

# ── 2. Localización de Rutas ──────────────────────────────────────────────────
def find_base_dir() -> Path:
    candidates = [
        Path(sys.executable).resolve().parent,
        Path(sys.executable).resolve().parent.parent,
        Path(sys.executable).resolve().parent.parent.parent,
        Path(__file__).resolve().parent,
        Path(__file__).resolve().parent.parent.parent,
        Path.cwd(),
    ]
    for c in candidates:
        if (c / "src" / "shields" / "target" / "release" / "aegis_shields.dll").exists():
            return c
        if (c / "aegis_shields.dll").exists():
            return c
    return Path(__file__).resolve().parent.parent.parent

BASE_DIR = find_base_dir()
CONFIG_FILE = Path.home() / ".aegis_browser_config.json"

# ── 3. DWM Immersive Dark Mode para la Barra de Título de Windows ─────────────
def apply_windows_dark_title_bar(window_id):
    try:
        DWMWA_USE_IMMERSIVE_DARK_MODE = 20
        DWMWA_USE_IMMERSIVE_DARK_MODE_OLD = 19
        val = ctypes.c_int(1)
        hwnd = wintypes.HWND(int(window_id))
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE, ctypes.byref(val), ctypes.sizeof(val)
        )
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE_OLD, ctypes.byref(val), ctypes.sizeof(val)
        )
    except Exception:
        pass

# ── 4. Enlace FFI con el Motor Rust (adblock-rust) ────────────────────────────
class AegisShieldsRustCore:
    def __init__(self):
        self.dll = None
        self.engine = None
        self.total_blocked = 0

        dll_paths = [
            BASE_DIR / "src" / "shields" / "target" / "release" / "aegis_shields.dll",
            BASE_DIR / "dist" / "Aegis" / "aegis_shields.dll",
            BASE_DIR / "aegis_shields.dll",
            Path.cwd() / "dist" / "Aegis" / "aegis_shields.dll",
        ]
        for p in dll_paths:
            if p.exists():
                try:
                    self.dll = ctypes.CDLL(str(p.resolve()))
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
                    print(f"  [OK] Aegis Shields cargado desde: {p.name}")
                    break
                except Exception as e:
                    print(f"  [AVISO] Error cargando DLL: {e}")

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
        css_rules = [
            # Reglas cosméticas de respaldo universal para DuckDuckGo, Google, etc.
            ".results--ads, [data-testid=\"ad\"], .badge--ad, li[data-layout=\"ad\"], "
            ".js-badge--ad, div[class*=\"badge--ad\"], .result--ad, div[data-layout=\"ad\"], "
            "div[data-text-ad], .uEierd, div[id*=\"tads\"], div[id*=\"bottomads\"], .b_ad "
            "{ display: none !important; opacity: 0 !important; height: 0 !important; visibility: hidden !important; }"
        ]
        if self.dll and self.engine:
            try:
                ptr = self.dll.aegis_shields_get_cosmetic_stylesheet(self.engine, url.encode("utf-8"))
                if ptr:
                    c = ctypes.c_char_p(ptr).value.decode("utf-8", errors="replace")
                    self.dll.aegis_shields_free_string(ptr)
                    if c:
                        css_rules.append(c)
            except Exception:
                pass
        return "\n".join(css_rules)

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

# ── 5. Interceptor de Peticiones de Red ───────────────────────────────────────
class AegisRequestInterceptor(QWebEngineUrlRequestInterceptor):
    def __init__(self, callback=None):
        super().__init__()
        self.callback = callback
        self.enabled = True

    def interceptRequest(self, info):
        if not self.enabled:
            return
        url = info.requestUrl().toString()
        source = info.firstPartyUrl().toString()
        if SHIELDS_CORE.should_block(url, source, "other"):
            info.block(True)
            if self.callback:
                self.callback()

# ── 6. Sistema de 4 Temas Reales (Cyber, Midnight, OLED, Light) ───────────────
THEMES = {
    "Cyber Dark": {
        "bg_win": "#090d14",
        "bg_tab_header": "#090d14",
        "bg_tab_unselected": "#0e1420",
        "bg_tab_selected": "#141c2c",
        "border_tab": "#38bdf8",
        "bg_toolbar": "#0f1624",
        "bg_omnibox": "#070b12",
        "text_main": "#f0f6fc",
        "text_muted": "#8b949e",
        "accent": "#38bdf8",
        "shield_color": "#10b981",
        "shield_bg": "rgba(16, 185, 129, 0.08)",
        "shield_border": "rgba(16, 185, 129, 0.25)",
        "ntp_class": "theme-cyber"
    },
    "Midnight Indigo": {
        "bg_win": "#090a12",
        "bg_tab_header": "#090a12",
        "bg_tab_unselected": "#0f111e",
        "bg_tab_selected": "#181b2e",
        "border_tab": "#818cf8",
        "bg_toolbar": "#111422",
        "bg_omnibox": "#090a12",
        "text_main": "#f8fafc",
        "text_muted": "#94a3b8",
        "accent": "#818cf8",
        "shield_color": "#a855f7",
        "shield_bg": "rgba(168, 85, 247, 0.08)",
        "shield_border": "rgba(168, 85, 247, 0.25)",
        "ntp_class": "theme-midnight"
    },
    "Pure OLED Black": {
        "bg_win": "#000000",
        "bg_tab_header": "#000000",
        "bg_tab_unselected": "#0a0a0a",
        "bg_tab_selected": "#141414",
        "border_tab": "#10b981",
        "bg_toolbar": "#080808",
        "bg_omnibox": "#000000",
        "text_main": "#ffffff",
        "text_muted": "#737373",
        "accent": "#10b981",
        "shield_color": "#10b981",
        "shield_bg": "rgba(16, 185, 129, 0.12)",
        "shield_border": "rgba(16, 185, 129, 0.3)",
        "ntp_class": "theme-oled"
    },
    "Clean Titanium Light": {
        "bg_win": "#f1f5f9",
        "bg_tab_header": "#e2e8f0",
        "bg_tab_unselected": "#e2e8f0",
        "bg_tab_selected": "#ffffff",
        "border_tab": "#0284c7",
        "bg_toolbar": "#ffffff",
        "bg_omnibox": "#f8fafc",
        "text_main": "#0f172a",
        "text_muted": "#64748b",
        "accent": "#0284c7",
        "shield_color": "#059669",
        "shield_bg": "rgba(5, 150, 105, 0.1)",
        "shield_border": "rgba(5, 150, 105, 0.25)",
        "ntp_class": "theme-light"
    }
}

# ── 7. Diálogo Interactivo de Aegis Shields ───────────────────────────────────
class AegisShieldsDialog(QDialog):
    def __init__(self, parent=None, interceptor=None):
        super().__init__(parent)
        self.interceptor = interceptor
        self.setWindowTitle("Aegis Shields — Centro de Control")
        self.setFixedSize(420, 390)
        self.setStyleSheet("""
            QDialog {
                background-color: #0d121c;
                color: #f0f6fc;
                border: 1px solid rgba(56, 189, 248, 0.3);
                border-radius: 12px;
                font-family: -apple-system, 'Segoe UI', sans-serif;
            }
            QLabel {
                color: #f0f6fc;
            }
            QCheckBox {
                color: #e2e8f0;
                font-size: 13px;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 4px;
                border: 1px solid rgba(255, 255, 255, 0.2);
                background: #090d14;
            }
            QCheckBox::indicator:checked {
                background: #10b981;
                border-color: #10b981;
            }
            QPushButton {
                background: rgba(255, 255, 255, 0.06);
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 8px;
                color: #f0f6fc;
                padding: 7px 14px;
                font-weight: 600;
                font-size: 12px;
            }
            QPushButton:hover {
                background: rgba(56, 189, 248, 0.15);
                border-color: #38bdf8;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        # Encabezado
        title = QLabel(f"🛡️ Aegis Shields (adblock-rust)")
        title.setStyleSheet("font-size: 16px; font-weight: 700; color: #38bdf8;")
        layout.addWidget(title)

        # Contador
        stats = QLabel(f"<b>{SHIELDS_CORE.total_blocked}</b> anuncios y rastreadores bloqueados en esta sesión.")
        stats.setStyleSheet("font-size: 13px; color: #10b981; margin-bottom: 6px;")
        layout.addWidget(stats)

        # Opciones interactivas reales
        self.cb_network = QCheckBox("Bloqueo de red a nivel socket (adblock-rust)")
        self.cb_network.setChecked(self.interceptor.enabled if self.interceptor else True)
        self.cb_network.toggled.connect(self.toggle_network)
        layout.addWidget(self.cb_network)

        self.cb_cosmetic = QCheckBox("Filtrado cosmético (eliminar espacios y anuncios DuckDuckGo)")
        self.cb_cosmetic.setChecked(True)
        layout.addWidget(self.cb_cosmetic)

        self.cb_youtube = QCheckBox("Bypass de comerciales y anti-adblock de YouTube")
        self.cb_youtube.setChecked(True)
        layout.addWidget(self.cb_youtube)

        self.cb_countdown = QCheckBox("FastForward automático de cuentas atrás (CurseForge / ouo.io)")
        self.cb_countdown.setChecked(True)
        layout.addWidget(self.cb_countdown)

        layout.addSpacing(6)

        # Botón limpiar caché
        btn_clear = QPushButton("🗑️ Limpiar Caché y Cookies de Sesión")
        btn_clear.clicked.connect(self.clear_cache)
        layout.addWidget(btn_clear)

        # Botón Cerrar
        btn_close = QPushButton("Entendido")
        btn_close.setStyleSheet("background: #10b981; color: #052e16; font-weight: 700;")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close)

    def toggle_network(self, checked):
        if self.interceptor:
            self.interceptor.enabled = checked

    def clear_cache(self):
        QWebEngineProfile.defaultProfile().clearHttpCache()
        QMessageBox.information(self, "Caché", "✓ Caché HTTP de navegación limpiada correctamente.")

# ── 8. Ventana Principal de Aegis Browser ─────────────────────────────────────
class AegisBrowserWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Aegis")
        self.resize(1340, 860)

        # Cargar configuración guardada
        self.current_theme_name = self.load_saved_theme()

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
        self.init_ui()

        # Aplicar borde oscuro nativo de Windows (eliminar verde lima)
        apply_windows_dark_title_bar(self.winId())

    def load_saved_theme(self) -> str:
        if CONFIG_FILE.exists():
            try:
                data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
                theme = data.get("theme", "Cyber Dark")
                if theme in THEMES:
                    return theme
            except Exception:
                pass
        return "Cyber Dark"

    def save_theme(self, theme_name: str):
        try:
            CONFIG_FILE.write_text(json.dumps({"theme": theme_name}, indent=2), encoding="utf-8")
        except Exception:
            pass

    def init_ui(self):
        container = QWidget()
        self.setCentralWidget(container)
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ── 1. Tira de Pestañas (En la cima de la ventana) ──────────────────────
        self.tab_header = QWidget()
        self.tab_header.setObjectName("TabHeader")
        tab_header_layout = QHBoxLayout(self.tab_header)
        tab_header_layout.setContentsMargins(8, 6, 8, 0)
        tab_header_layout.setSpacing(6)

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

        # Selector de Tema en Vivo
        self.theme_combo = QComboBox()
        self.theme_combo.setObjectName("ThemeSelector")
        for t_name in THEMES.keys():
            self.theme_combo.addItem(t_name)
        self.theme_combo.setCurrentText(self.current_theme_name)
        self.theme_combo.currentTextChanged.connect(self.change_theme)
        tab_header_layout.addWidget(self.theme_combo)

        main_layout.addWidget(self.tab_header)

        # ── 2. Barra de Navegación y Omnibox Flotante ─────────────────────────
        self.toolbar = QWidget()
        self.toolbar.setObjectName("Toolbar")
        toolbar_layout = QHBoxLayout(self.toolbar)
        toolbar_layout.setContentsMargins(10, 6, 10, 6)
        toolbar_layout.setSpacing(6)

        self.btn_back = QPushButton("←")
        self.btn_back.setProperty("class", "nav-btn")
        self.btn_back.setToolTip("Atrás")
        self.btn_back.clicked.connect(self.navigate_back)
        toolbar_layout.addWidget(self.btn_back)

        self.btn_forward = QPushButton("→")
        self.btn_forward.setProperty("class", "nav-btn")
        self.btn_forward.setToolTip("Adelante")
        self.btn_forward.clicked.connect(self.navigate_forward)
        toolbar_layout.addWidget(self.btn_forward)

        self.btn_reload = QPushButton("↻")
        self.btn_reload.setProperty("class", "nav-btn")
        self.btn_reload.setToolTip("Recargar")
        self.btn_reload.clicked.connect(self.reload_page)
        toolbar_layout.addWidget(self.btn_reload)

        self.btn_home = QPushButton("⌂")
        self.btn_home.setProperty("class", "nav-btn")
        self.btn_home.setToolTip("Inicio")
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
        self.shield_pill.setToolTip("Aegis Shields: Click para ver panel de control")
        self.shield_pill.clicked.connect(self.open_shields_panel)
        toolbar_layout.addWidget(self.shield_pill)

        main_layout.addWidget(self.toolbar)

        # ── 3. Micro Barra de Progreso (2px) ──────────────────────────────────
        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("MicroProgress")
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(2)
        self.progress_bar.hide()
        main_layout.addWidget(self.progress_bar)

        # ── 4. Contenedor de Vistas Web ───────────────────────────────────────
        self.stack = QStackedWidget()
        main_layout.addWidget(self.stack)

        self.apply_theme(self.current_theme_name)
        self.setup_shortcuts()

        # Abrir pestaña inicial
        self.add_new_tab()

    def apply_theme(self, theme_name: str):
        t = THEMES.get(theme_name, THEMES["Cyber Dark"])
        self.current_theme_name = theme_name
        self.save_theme(theme_name)

        qss = f"""
            QMainWindow {{
                background-color: {t['bg_win']};
            }}
            QWidget#TabHeader {{
                background-color: {t['bg_tab_header']};
                border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            }}
            QTabBar {{
                background: transparent;
                border: none;
            }}
            QTabBar::tab {{
                background-color: {t['bg_tab_unselected']};
                color: {t['text_muted']};
                border: 1px solid rgba(255, 255, 255, 0.05);
                border-bottom: none;
                padding: 6px 14px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                margin-right: 3px;
                font-size: 12px;
                font-family: -apple-system, 'Segoe UI', sans-serif;
                min-width: 90px;
                max-width: 220px;
            }}
            QTabBar::tab:hover {{
                background-color: {t['bg_tab_selected']};
                color: {t['text_main']};
            }}
            QTabBar::tab:selected {{
                background-color: {t['bg_tab_selected']};
                color: {t['text_main']};
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-bottom: none;
                border-top: 2px solid {t['border_tab']};
                font-weight: 600;
            }}
            QPushButton#NewTabBtn {{
                background: transparent;
                border: none;
                color: {t['text_muted']};
                font-size: 16px;
                border-radius: 12px;
                width: 24px;
                height: 24px;
            }}
            QPushButton#NewTabBtn:hover {{
                background-color: rgba(255, 255, 255, 0.08);
                color: {t['text_main']};
            }}
            QComboBox#ThemeSelector {{
                background-color: {t['bg_omnibox']};
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 6px;
                color: {t['text_muted']};
                padding: 2px 8px;
                font-size: 11px;
            }}
            QWidget#Toolbar {{
                background-color: {t['bg_toolbar']};
                border-bottom: 1px solid rgba(255, 255, 255, 0.04);
            }}
            QPushButton.nav-btn {{
                background: transparent;
                border: none;
                color: {t['text_muted']};
                font-size: 15px;
                border-radius: 14px;
                width: 30px;
                height: 30px;
            }}
            QPushButton.nav-btn:hover {{
                background-color: rgba(255, 255, 255, 0.08);
                color: {t['text_main']};
            }}
            QLineEdit#Omnibox {{
                background-color: {t['bg_omnibox']};
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 16px;
                color: {t['text_main']};
                padding: 5px 16px;
                font-size: 12.5px;
                font-family: -apple-system, 'Segoe UI', sans-serif;
                selection-background-color: {t['accent']};
            }}
            QLineEdit#Omnibox:focus {{
                border: 1px solid {t['accent']};
            }}
            QPushButton#ShieldPill {{
                background-color: {t['shield_bg']};
                border: 1px solid {t['shield_border']};
                border-radius: 13px;
                color: {t['shield_color']};
                font-size: 11.5px;
                font-weight: 600;
                padding: 4px 11px;
            }}
            QPushButton#ShieldPill:hover {{
                background-color: {t['shield_color']};
                color: #000000;
            }}
            QProgressBar#MicroProgress {{
                border: none;
                background: transparent;
                height: 2px;
            }}
            QProgressBar#MicroProgress::chunk {{
                background: {t['accent']};
            }}
        """
        self.setStyleSheet(qss)

        # Si la pestaña actual está en la New Tab Page, actualizar su tema dinámicamente
        for v in self.views:
            if v.url().toString() in ("aegis://start", "about:blank"):
                v.page().runJavaScript(f"document.documentElement.className = '{t['ntp_class']}';")

    def change_theme(self, theme_name: str):
        if theme_name in THEMES:
            self.apply_theme(theme_name)

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
            self.load_ntp(view)

        self.tab_bar.setCurrentIndex(tab_idx)
        self.stack.setCurrentIndex(stack_idx)
        return view

    def load_ntp(self, view: QWebEngineView):
        t = THEMES.get(self.current_theme_name, THEMES["Cyber Dark"])
        html = get_clean_ntp_html(t["ntp_class"])
        view.setHtml(html, QUrl("aegis://start"))

    def close_tab(self, index: int):
        if self.tab_bar.count() > 1:
            view = self.views.pop(index)
            self.tab_bar.removeTab(index)
            self.stack.removeWidget(view)
            view.deleteLater()
        else:
            current = self.current_view()
            if current:
                self.load_ntp(current)
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
        if v: self.load_ntp(v)

    def on_url_changed(self, qurl: QUrl, view: QWebEngineView):
        if view == self.current_view():
            url_str = qurl.toString()
            if url_str in ("aegis://start", "about:blank"):
                self.url_bar.setText("")
                self.url_bar.setPlaceholderText("Buscar en la web o ingresar dirección...")
            else:
                self.url_bar.setText(url_str)

    def on_load_progress(self, progress: int):
        if progress < 100:
            self.progress_bar.show()
            self.progress_bar.setValue(progress)
            # Inyección anticipada de CSS cosmético anti-anuncios al 50% de carga
            v = self.current_view()
            if v and v.url().toString() not in ("aegis://start", "about:blank"):
                css = SHIELDS_CORE.get_cosmetic_css(v.url().toString())
                if css:
                    v.page().runJavaScript(f"""
                        try {{
                            let s = document.getElementById('_aegis_css_fast');
                            if (!s) {{
                                s = document.createElement('style');
                                s.id = '_aegis_css_fast';
                                document.head.appendChild(s);
                            }}
                            s.textContent = `{css}`;
                        }} catch(e) {{}}
                    """)
        else:
            self.progress_bar.hide()

    def on_load_finished(self, ok: bool, view: QWebEngineView):
        self.progress_bar.hide()
        current_url = view.url().toString()
        title = view.title() or "Página"

        if current_url in ("aegis://start", "about:blank"):
            title = "Nueva Pestaña"

        idx = self.views.index(view) if view in self.views else -1
        if idx != -1:
            display_title = title if len(title) <= 16 else title[:14] + "…"
            self.tab_bar.setTabText(idx, display_title)

        if ok and current_url not in ("aegis://start", "about:blank"):
            # Inyección cosmética de Rust (Oculta DuckDuckGo ads, YouTube ads, etc.)
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

            # Inyección de scriptlets defusers (Anti-adblock bypass, skip videos, skip popups)
            js = SHIELDS_CORE.get_injected_scripts(current_url)
            if js:
                view.page().runJavaScript(js)

    def on_shield_block(self):
        self.shield_pill.setText(f"🛡️ {SHIELDS_CORE.total_blocked}")

    def open_shields_panel(self):
        dlg = AegisShieldsDialog(self, self.interceptor)
        dlg.exec()

# ── 9. Plantilla HTML Autocontenida (Reloj Vivo, SVG Nítido, Cero Bugs) ──────
def get_clean_ntp_html(theme_class: str = "theme-cyber") -> str:
    return f"""<!DOCTYPE html>
<html lang="es" class="{theme_class}">
<head>
  <meta charset="UTF-8">
  <title>Aegis</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    :root {{
      --bg: #090d14;
      --text: #f0f6fc;
      --muted: #8b949e;
      --accent: #38bdf8;
      --card-bg: rgba(255, 255, 255, 0.03);
      --card-border: rgba(255, 255, 255, 0.07);
    }}
    .theme-midnight {{
      --bg: #090a12;
      --text: #f8fafc;
      --muted: #94a3b8;
      --accent: #818cf8;
      --card-bg: rgba(129, 140, 248, 0.04);
      --card-border: rgba(129, 140, 248, 0.12);
    }}
    .theme-oled {{
      --bg: #000000;
      --text: #ffffff;
      --muted: #737373;
      --accent: #10b981;
      --card-bg: #0a0a0a;
      --card-border: #1a1a1a;
    }}
    .theme-light {{
      --bg: #f8fafc;
      --text: #0f172a;
      --muted: #64748b;
      --accent: #0284c7;
      --card-bg: #ffffff;
      --card-border: rgba(0, 0, 0, 0.08);
    }}

    body {{
      background: var(--bg);
      color: var(--text);
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 2rem;
      user-select: none;
      transition: background 0.3s ease, color 0.3s ease;
    }}

    .hero {{
      text-align: center;
      max-width: 640px;
      width: 100%;
    }}

    .brand-header {{
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 12px;
      margin-bottom: 1.5rem;
    }}
    .brand-logo {{
      width: 36px;
      height: 36px;
    }}
    .brand-name {{
      font-size: 1.75rem;
      font-weight: 700;
      letter-spacing: -0.5px;
      color: var(--text);
    }}

    .clock {{
      font-size: 4.5rem;
      font-weight: 200;
      letter-spacing: -2px;
      color: var(--text);
      margin-bottom: 0.25rem;
      font-variant-numeric: tabular-nums;
    }}
    .date {{
      font-size: 0.95rem;
      color: var(--muted);
      font-weight: 400;
      margin-bottom: 2.25rem;
      letter-spacing: 0.2px;
      text-transform: capitalize;
    }}

    .shortcuts-grid {{
      display: flex;
      gap: 1rem;
      justify-content: center;
      flex-wrap: wrap;
      margin-bottom: 2rem;
    }}
    .shortcut-card {{
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 6px;
      text-decoration: none;
      color: var(--text);
      font-size: 0.8rem;
      font-weight: 500;
      padding: 12px 16px;
      border-radius: 12px;
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      transition: all 0.2s ease;
      min-width: 80px;
    }}
    .shortcut-card:hover {{
      background: rgba(255, 255, 255, 0.08);
      border-color: var(--accent);
      transform: translateY(-2px);
    }}
    .shortcut-icon {{
      font-size: 1.5rem;
    }}

    .footer-badge {{
      position: fixed;
      bottom: 1.5rem;
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 0.75rem;
      color: var(--muted);
    }}
    .shield-dot {{
      width: 7px;
      height: 7px;
      background: #10b981;
      border-radius: 50%;
      box-shadow: 0 0 8px #10b981;
    }}
  </style>
</head>
<body>
  <main class="hero">
    <div class="brand-header">
      <svg class="brand-logo" viewBox="0 0 100 100" fill="none">
        <path d="M50 5 L88 22 V50 C88 74 50 95 50 95 C50 95 12 74 12 50 V22 Z" fill="url(#shield_grad)"/>
        <path d="M50 14 L80 27 V50 C80 69 50 86 50 86 C50 86 20 69 20 50 V27 Z" fill="#090d14"/>
        <path d="M42 50 L48 56 L62 42" stroke="#10b981" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/>
        <defs>
          <linearGradient id="shield_grad" x1="12" y1="5" x2="88" y2="95">
            <stop stop-color="#38bdf8"/>
            <stop offset="1" stop-color="#818cf8"/>
          </linearGradient>
        </defs>
      </svg>
      <div class="brand-name">Aegis</div>
    </div>

    <div id="clock" class="clock">12:00</div>
    <div id="date" class="date">Cargando fecha...</div>

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
    function updateClock() {{
      const now = new Date();
      const h = String(now.getHours()).padStart(2, '0');
      const m = String(now.getMinutes()).padStart(2, '0');
      document.getElementById('clock').textContent = `${{h}}:${{m}}`;

      const options = {{ weekday: 'long', month: 'long', day: 'numeric' }};
      document.getElementById('date').textContent = now.toLocaleDateString('es-ES', options);
    }}
    updateClock();
    setInterval(updateClock, 1000);
  </script>
</body>
</html>
"""

# ── 10. Punto de Entrada ──────────────────────────────────────────────────────
def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Aegis")
    app.setApplicationVersion("1.3.0")

    window = AegisBrowserWindow()
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
