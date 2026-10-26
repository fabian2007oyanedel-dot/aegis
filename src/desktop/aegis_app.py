#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
                    AEGIS BROWSER - NATIVE RUNTIME (v1.3.1)
           Chromium WebEngine + Rust FFI Shields + Brave-Style UI
================================================================================
Características:
  - Interfaz minimalista inspirada en Brave Browser (Popup anclado, sin menús invasivos).
  - Escudo interactivo tipo Brave: Hostname, Switch principal, tarjeta de estadísticas
    y sección desplegable colapsable "Opciones avanzadas".
  - Sistema de 2 Temas Estrictos (Máximo 4 colores por tema): Oscuro y Claro.
  - Botón de cambio de tema rápido en barra de herramientas (sin combobox que estorbe).
  - Tira de pestañas nativa limpia y cápsula Omnibox con búsqueda DuckDuckGo / URL.
  - Sincronización con DWM de Windows (título oscuro / claro sin bordes de acento).
  - Motor de bloqueo Rust FFI de alto rendimiento con defusers para YouTube, DuckDuckGo,
    sitios de streaming y acortadores.
================================================================================
"""

import os
import sys
import json
import time
import ctypes
from pathlib import Path

# Configuración de rendimiento y aceleración para Chromium Engine
os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = (
    "--enable-gpu-rasterization "
    "--enable-zero-copy "
    "--ignore-gpu-blocklist "
    "--disable-breakpad "
    "--disable-telemetry "
    "--disable-sync "
    "--disable-domain-reliability "
    "--no-pings "
    "--dns-prefetch-disable"
)

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QProgressBar, QTabBar, QStackedWidget,
    QLabel, QCheckBox, QMessageBox, QFrame, QAbstractButton
)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import (
    QWebEngineProfile, QWebEngineSettings, QWebEngineUrlRequestInterceptor
)
from PyQt6.QtCore import QUrl, Qt, QPoint
from PyQt6.QtGui import QIcon, QPainter, QColor, QBrush, QPen

BASE_DIR = Path(__file__).resolve().parent.parent.parent
CONFIG_FILE = Path.home() / ".aegis_browser_config.json"

# ── 1. Helper para conversión Hex a RGB ────────────────────────────────────────
def hex_to_rgb(h: str) -> str:
    h = h.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"{r}, {g}, {b}"

# ── 2. Soporte de Barra de Título Nativa Windows DWM ───────────────────────────
def apply_windows_dark_title_bar(hwnd, dark: bool = True):
    if sys.platform != "win32":
        return
    try:
        DWMWA_USE_IMMERSIVE_DARK_MODE = 20
        set_attribute = ctypes.windll.dwmapi.DwmSetWindowAttribute
        val = ctypes.c_int(1 if dark else 0)
        hr = set_attribute(int(hwnd), DWMWA_USE_IMMERSIVE_DARK_MODE, ctypes.byref(val), ctypes.sizeof(val))
        if hr != 0:
            DWMWA_USE_IMMERSIVE_DARK_MODE_OLD = 19
            set_attribute(int(hwnd), DWMWA_USE_IMMERSIVE_DARK_MODE_OLD, ctypes.byref(val), ctypes.sizeof(val))
    except Exception:
        pass

# ── 3. Motor Aegis Shields (Rust FFI) ──────────────────────────────────────────
class AegisShieldsRustCore:
    def __init__(self):
        self.dll = None
        self.engine = None
        self.total_blocked = 0

        dll_paths = [
            BASE_DIR / "dist" / "Aegis" / "aegis_shields.dll",
            BASE_DIR / "src" / "shields" / "target" / "release" / "aegis_shields.dll",
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
            # Ocultación universal de publicidad en buscadores
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

# ── 4. Interceptor de Peticiones de Red ───────────────────────────────────────
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

# ── 5. Sistema de 2 Temas Estrictos (Máximo 4 Colores por Tema) ───────────────
# Regla: Cada tema contiene exactamente 4 colores fundamentales:
# 1. bg: Fondo general
# 2. surface: Superficie de controles, Omnibox, pestañas y popup
# 3. text: Texto y símbolos
# 4. accent: Color de realce interactivo / interruptor activo
THEMES = {
    "Oscuro": {
        "bg": "#0d1117",        # Color 1
        "surface": "#161b22",   # Color 2
        "text": "#f0f6fc",      # Color 3
        "accent": "#388bfd",    # Color 4
        "ntp_class": "theme-dark"
    },
    "Claro": {
        "bg": "#f6f8fa",        # Color 1
        "surface": "#ffffff",   # Color 2
        "text": "#1f2328",      # Color 3
        "accent": "#0969da",    # Color 4
        "ntp_class": "theme-light"
    }
}

# ── 6. Switch Interactivo Moderno (Estilo Brave) ──────────────────────────────
class ToggleSwitch(QAbstractButton):
    def __init__(self, checked=True, parent=None, accent_color="#388bfd", bg_color="#0d1117"):
        super().__init__(parent)
        self.setCheckable(True)
        self.setChecked(checked)
        self.setFixedSize(42, 22)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.accent_color = accent_color
        self.bg_color = bg_color

    def update_colors(self, accent_color: str, bg_color: str):
        self.accent_color = accent_color
        self.bg_color = bg_color
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect()

        if self.isChecked():
            pill_color = QColor(self.accent_color)
            thumb_color = QColor("#ffffff")
        else:
            pill_color = QColor(self.bg_color)
            thumb_color = QColor("#8b949e")

        painter.setBrush(QBrush(pill_color))
        painter.setPen(QPen(QColor(self.accent_color if self.isChecked() else "#30363d"), 1))
        painter.drawRoundedRect(rect, 11, 11)

        thumb_diam = 16
        thumb_x = (rect.width() - thumb_diam - 3) if self.isChecked() else 3
        painter.setBrush(QBrush(thumb_color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(thumb_x, 3, thumb_diam, thumb_diam)
        painter.end()

# ── 7. Menú Desplegable de Aegis Shields (Estilo Brave) ────────────────────────
class AegisShieldsPopup(QFrame):
    def __init__(self, parent=None, interceptor=None):
        super().__init__(parent, Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.setObjectName("AegisShieldsPopup")
        self.setFixedWidth(340)
        self.interceptor = interceptor
        self.parent_win = parent

        self.init_ui()

    def hideEvent(self, event):
        if self.parent_win:
            self.parent_win._last_popup_close_time = time.time()
        super().hideEvent(event)

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # ── Cabecera: Dominio actual + Subtítulo + Switch Principal ───────────
        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)

        site_info_layout = QVBoxLayout()
        site_info_layout.setSpacing(2)

        self.lbl_site = QLabel("aegis://start")
        self.lbl_site.setObjectName("PopupSiteName")
        site_info_layout.addWidget(self.lbl_site)

        self.lbl_status = QLabel("Escudos activados para este sitio")
        self.lbl_status.setObjectName("PopupStatusText")
        site_info_layout.addWidget(self.lbl_status)

        header_layout.addLayout(site_info_layout)
        header_layout.addStretch()

        self.main_switch = ToggleSwitch(checked=True)
        self.main_switch.toggled.connect(self.on_main_switch_toggled)
        header_layout.addWidget(self.main_switch)

        layout.addLayout(header_layout)

        # ── Tarjeta Estadística (Contador en cápsula estilo Brave) ────────────
        self.stat_card = QFrame()
        self.stat_card.setObjectName("PopupStatCard")
        stat_layout = QHBoxLayout(self.stat_card)
        stat_layout.setContentsMargins(14, 12, 14, 12)
        stat_layout.setSpacing(12)

        self.lbl_count = QLabel("0")
        self.lbl_count.setObjectName("PopupCount")
        stat_layout.addWidget(self.lbl_count)

        self.lbl_stat_text = QLabel("rastreadores, anuncios y más elementos bloqueados")
        self.lbl_stat_text.setObjectName("PopupStatLabel")
        self.lbl_stat_text.setWordWrap(True)
        stat_layout.addWidget(self.lbl_stat_text)

        layout.addWidget(self.stat_card)

        # ── Botón Desplegable "Opciones avanzadas" ────────────────────────────
        self.btn_advanced = QPushButton("⚙ Opciones avanzadas ▾")
        self.btn_advanced.setObjectName("PopupAdvancedBtn")
        self.btn_advanced.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_advanced.clicked.connect(self.toggle_advanced)
        layout.addWidget(self.btn_advanced)

        # Contenedor Colapsable (Opciones Avanzadas)
        self.advanced_container = QWidget()
        adv_layout = QVBoxLayout(self.advanced_container)
        adv_layout.setContentsMargins(4, 2, 4, 6)
        adv_layout.setSpacing(8)

        self.cb_network = QCheckBox("Bloqueo de red a nivel socket (Rust FFI)")
        self.cb_network.setChecked(True)
        self.cb_network.toggled.connect(self.toggle_network)
        adv_layout.addWidget(self.cb_network)

        self.cb_cosmetic = QCheckBox("Ocultación cosmética CSS en búsquedas y páginas")
        self.cb_cosmetic.setChecked(True)
        adv_layout.addWidget(self.cb_cosmetic)

        self.cb_video = QCheckBox("Salto automático de anuncios de video (YouTube)")
        self.cb_video.setChecked(True)
        adv_layout.addWidget(self.cb_video)

        self.cb_countdown = QCheckBox("Bypass de temporizadores y acortadores")
        self.cb_countdown.setChecked(True)
        adv_layout.addWidget(self.cb_countdown)

        self.btn_clear_cache = QPushButton("🗑️ Limpiar caché de sesión")
        self.btn_clear_cache.setObjectName("PopupClearBtn")
        self.btn_clear_cache.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_clear_cache.clicked.connect(self.clear_cache)
        adv_layout.addWidget(self.btn_clear_cache)

        self.advanced_container.hide()  # Colapsado por defecto para no estorbar
        layout.addWidget(self.advanced_container)

        # ── Pie de nota ───────────────────────────────────────────────────────
        self.lbl_footer = QLabel("Aegis Shields • adblock-rust FFI • Cero telemetría")
        self.lbl_footer.setObjectName("PopupFooter")
        self.lbl_footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.lbl_footer)

    def toggle_advanced(self):
        is_vis = self.advanced_container.isVisible()
        self.advanced_container.setVisible(not is_vis)
        self.btn_advanced.setText("⚙ Opciones avanzadas ▴" if not is_vis else "⚙ Opciones avanzadas ▾")
        self.adjustSize()

    def on_main_switch_toggled(self, checked: bool):
        if checked:
            self.lbl_status.setText("Escudos activados para este sitio")
            if self.interceptor:
                self.interceptor.enabled = True
        else:
            self.lbl_status.setText("Escudos desactivados para este sitio")
            if self.interceptor:
                self.interceptor.enabled = False

    def toggle_network(self, checked: bool):
        if self.interceptor:
            self.interceptor.enabled = checked

    def clear_cache(self):
        QWebEngineProfile.defaultProfile().clearHttpCache()
        self.lbl_status.setText("✓ Caché de sesión limpiada")

    def update_site(self, host: str, count: int):
        self.lbl_site.setText(host or "Nueva Pestaña")
        self.lbl_count.setText(str(count))

    def apply_theme(self, t: dict):
        rgb_text = hex_to_rgb(t["text"])
        rgb_accent = hex_to_rgb(t["accent"])
        self.main_switch.update_colors(accent_color=t["accent"], bg_color=t["bg"])

        qss = f"""
            QFrame#AegisShieldsPopup {{
                background-color: {t['surface']};
                border: 1px solid rgba({rgb_text}, 0.15);
                border-radius: 12px;
            }}
            QLabel#PopupSiteName {{
                color: {t['text']};
                font-size: 15px;
                font-weight: 700;
            }}
            QLabel#PopupStatusText {{
                color: rgba({rgb_text}, 0.7);
                font-size: 11.5px;
            }}
            QFrame#PopupStatCard {{
                background-color: {t['bg']};
                border: 1px solid rgba({rgb_text}, 0.08);
                border-radius: 10px;
            }}
            QLabel#PopupCount {{
                color: {t['accent']};
                font-size: 24px;
                font-weight: 800;
            }}
            QLabel#PopupStatLabel {{
                color: {t['text']};
                font-size: 12px;
            }}
            QPushButton#PopupAdvancedBtn {{
                background: transparent;
                border: none;
                color: rgba({rgb_text}, 0.75);
                font-size: 11.5px;
                font-weight: 600;
                text-align: left;
                padding: 4px 0;
            }}
            QPushButton#PopupAdvancedBtn:hover {{
                color: {t['accent']};
            }}
            QCheckBox {{
                color: {t['text']};
                font-size: 12px;
                spacing: 8px;
            }}
            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
                border-radius: 4px;
                border: 1px solid rgba({rgb_text}, 0.25);
                background: {t['bg']};
            }}
            QCheckBox::indicator:checked {{
                background: {t['accent']};
                border-color: {t['accent']};
            }}
            QPushButton#PopupClearBtn {{
                background-color: {t['bg']};
                border: 1px solid rgba({rgb_text}, 0.12);
                border-radius: 8px;
                color: {t['text']};
                padding: 6px 12px;
                font-size: 11.5px;
                margin-top: 4px;
            }}
            QPushButton#PopupClearBtn:hover {{
                background-color: rgba({rgb_accent}, 0.12);
                border-color: {t['accent']};
            }}
            QLabel#PopupFooter {{
                color: rgba({rgb_text}, 0.45);
                font-size: 10px;
                margin-top: 4px;
            }}
        """
        self.setStyleSheet(qss)
        self.update()

# ── 8. Ventana Principal de Aegis Browser ─────────────────────────────────────
class AegisBrowserWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Aegis")
        self.resize(1340, 860)

        self._last_popup_close_time = 0.0
        self.current_theme_name = self.load_saved_theme()

        # Configurar Perfil Chromium
        self.profile = QWebEngineProfile.defaultProfile()
        self.profile.setHttpUserAgent(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Aegis/1.3.1"
        )
        self.profile.settings().setAttribute(QWebEngineSettings.WebAttribute.JavascriptCanOpenWindows, False)
        self.profile.settings().setAttribute(QWebEngineSettings.WebAttribute.FullScreenSupportEnabled, True)
        self.profile.settings().setAttribute(QWebEngineSettings.WebAttribute.PlaybackRequiresUserGesture, False)

        # Interceptor de peticiones de red
        self.interceptor = AegisRequestInterceptor(self.on_shield_block)
        self.profile.setUrlRequestInterceptor(self.interceptor)

        self.views = []
        self.init_ui()

        # Crear menú desplegable estilo Brave
        self.shields_popup = AegisShieldsPopup(self, self.interceptor)

        # Aplicar tema inicial (Oscuro o Claro)
        self.apply_theme(self.current_theme_name)
        self.setup_shortcuts()

        # Abrir pestaña inicial
        self.add_new_tab()

    def load_saved_theme(self) -> str:
        if CONFIG_FILE.exists():
            try:
                data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
                theme = data.get("theme", "Oscuro")
                if theme in ("Oscuro", "Claro"):
                    return theme
                if "light" in theme.lower() or "claro" in theme.lower():
                    return "Claro"
            except Exception:
                pass
        return "Oscuro"

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

        # ── 1. Tira de Pestañas Limpia (Sin menús invasivos) ───────────────────
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
        main_layout.addWidget(self.tab_header)

        # ── 2. Barra de Navegación, Omnibox y Botones de Acción ───────────────
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

        # Botón Escudo Aegis Shields (Abre desplegable estilo Brave)
        self.shield_pill = QPushButton("🛡️ 0")
        self.shield_pill.setObjectName("ShieldPill")
        self.shield_pill.setToolTip("Aegis Shields: Click para desplegar panel")
        self.shield_pill.clicked.connect(self.toggle_shields_popup)
        toolbar_layout.addWidget(self.shield_pill)

        # Botón de Cambio Rápido de Tema (Oscuro / Claro)
        self.btn_theme_toggle = QPushButton("☀️")
        self.btn_theme_toggle.setObjectName("ThemeToggleBtn")
        self.btn_theme_toggle.setToolTip("Cambiar tema (Oscuro / Claro)")
        self.btn_theme_toggle.clicked.connect(self.toggle_theme)
        toolbar_layout.addWidget(self.btn_theme_toggle)

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

    def toggle_theme(self):
        new_theme = "Claro" if self.current_theme_name == "Oscuro" else "Oscuro"
        self.apply_theme(new_theme)

    def apply_theme(self, theme_name: str):
        if theme_name not in THEMES:
            theme_name = "Oscuro"
        self.current_theme_name = theme_name
        self.save_theme(theme_name)
        t = THEMES[theme_name]
        is_dark = (theme_name == "Oscuro")

        # Actualizar botón de alternancia
        if is_dark:
            self.btn_theme_toggle.setText("☀️")
            self.btn_theme_toggle.setToolTip("Cambiar a Modo Claro")
        else:
            self.btn_theme_toggle.setText("🌙")
            self.btn_theme_toggle.setToolTip("Cambiar a Modo Oscuro")

        # Sincronizar borde y barra de título de Windows
        apply_windows_dark_title_bar(self.winId(), dark=is_dark)

        # Sincronizar motor Chromium WebEngine ForceDarkMode
        self.profile.settings().setAttribute(QWebEngineSettings.WebAttribute.ForceDarkMode, is_dark)

        rgb_text = hex_to_rgb(t["text"])
        rgb_accent = hex_to_rgb(t["accent"])

        # Hoja de estilos basada estrictamente en los 4 colores del tema
        qss = f"""
            QMainWindow {{
                background-color: {t['bg']};
            }}
            QWidget#TabHeader {{
                background-color: {t['bg']};
                border-bottom: 1px solid rgba({rgb_text}, 0.08);
            }}
            QTabBar {{
                background: transparent;
                border: none;
            }}
            QTabBar::tab {{
                background-color: {t['bg']};
                color: rgba({rgb_text}, 0.65);
                border: 1px solid rgba({rgb_text}, 0.08);
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
                background-color: {t['surface']};
                color: {t['text']};
            }}
            QTabBar::tab:selected {{
                background-color: {t['surface']};
                color: {t['text']};
                border: 1px solid rgba({rgb_text}, 0.12);
                border-bottom: none;
                border-top: 2px solid {t['accent']};
                font-weight: 600;
            }}
            QPushButton#NewTabBtn {{
                background: transparent;
                border: none;
                color: rgba({rgb_text}, 0.65);
                font-size: 16px;
                border-radius: 12px;
                width: 24px;
                height: 24px;
            }}
            QPushButton#NewTabBtn:hover {{
                background-color: {t['surface']};
                color: {t['text']};
            }}
            QWidget#Toolbar {{
                background-color: {t['bg']};
                border-bottom: 1px solid rgba({rgb_text}, 0.08);
            }}
            QPushButton.nav-btn {{
                background: transparent;
                border: none;
                color: rgba({rgb_text}, 0.7);
                font-size: 15px;
                border-radius: 14px;
                width: 30px;
                height: 30px;
            }}
            QPushButton.nav-btn:hover {{
                background-color: {t['surface']};
                color: {t['text']};
            }}
            QPushButton#ThemeToggleBtn {{
                background: transparent;
                border: none;
                color: {t['text']};
                font-size: 15px;
                border-radius: 14px;
                width: 30px;
                height: 30px;
            }}
            QPushButton#ThemeToggleBtn:hover {{
                background-color: {t['surface']};
            }}
            QLineEdit#Omnibox {{
                background-color: {t['surface']};
                border: 1px solid rgba({rgb_text}, 0.12);
                border-radius: 16px;
                color: {t['text']};
                padding: 5px 16px;
                font-size: 12.5px;
                font-family: -apple-system, 'Segoe UI', sans-serif;
                selection-background-color: {t['accent']};
            }}
            QLineEdit#Omnibox:focus {{
                border: 1px solid {t['accent']};
            }}
            QPushButton#ShieldPill {{
                background-color: {t['surface']};
                border: 1px solid rgba({rgb_accent}, 0.35);
                border-radius: 13px;
                color: {t['accent']};
                padding: 4px 12px;
                font-size: 12px;
                font-weight: 600;
            }}
            QPushButton#ShieldPill:hover {{
                background-color: {t['surface']};
                border-color: {t['accent']};
            }}
            QProgressBar#MicroProgress {{
                background-color: transparent;
                border: none;
            }}
            QProgressBar#MicroProgress::chunk {{
                background-color: {t['accent']};
            }}
        """
        self.setStyleSheet(qss)

        # Actualizar tema del desplegable estilo Brave
        if hasattr(self, "shields_popup"):
            self.shields_popup.apply_theme(t)

        # Actualizar páginas de Nueva Pestaña abiertas
        for view in self.views:
            if view.url().toString() in ("aegis://start", "about:blank"):
                self.load_ntp(view)

    def toggle_shields_popup(self):
        now = time.time()
        if hasattr(self, "_last_popup_close_time") and (now - self._last_popup_close_time < 0.25):
            return

        if self.shields_popup.isVisible():
            self.shields_popup.hide()
            return

        view = self.current_view()
        url = view.url() if view else QUrl()
        host = url.host() if url.host() else ("Nueva Pestaña" if url.toString() in ("aegis://start", "") else "Página actual")
        self.shields_popup.update_site(host, SHIELDS_CORE.total_blocked)

        # Posicionamiento exacto anclado bajo la píldora del escudo
        btn_pos = self.shield_pill.mapToGlobal(QPoint(0, self.shield_pill.height()))
        popup_x = btn_pos.x() + self.shield_pill.width() - self.shields_popup.width()
        popup_y = btn_pos.y() + 6
        self.shields_popup.move(popup_x, popup_y)
        self.shields_popup.show()
        self.shields_popup.raise_()

    def setup_shortcuts(self):
        pass

    def add_new_tab(self, url_str: str = "") -> QWebEngineView:
        view = QWebEngineView()
        view.setPage(view.page())

        tab_idx = self.tab_bar.addTab("Nueva Pestaña")
        stack_idx = self.stack.addWidget(view)
        self.views.append(view)

        view.urlChanged.connect(lambda qurl, v=view: self.on_url_changed(qurl, v))
        view.loadProgress.connect(self.on_load_progress)
        view.loadFinished.connect(lambda ok, v=view: self.on_load_finished(ok, v))

        if url_str:
            view.load(QUrl(url_str))
        else:
            self.load_ntp(view)

        self.tab_bar.setCurrentIndex(tab_idx)
        self.stack.setCurrentIndex(stack_idx)
        return view

    def load_ntp(self, view: QWebEngineView):
        t = THEMES.get(self.current_theme_name, THEMES["Oscuro"])
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
        if self.shields_popup.isVisible():
            self.shields_popup.hide()
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
            # Inyección anticipada de CSS cosmético anti-anuncios
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
            # Inyección de CSS cosmético
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

            # Inyección de defusers JavaScript
            js = SHIELDS_CORE.get_injected_scripts(current_url)
            if js:
                view.page().runJavaScript(js)

    def on_shield_block(self):
        self.shield_pill.setText(f"🛡️ {SHIELDS_CORE.total_blocked}")
        if hasattr(self, "shields_popup") and self.shields_popup.isVisible():
            self.shields_popup.lbl_count.setText(str(SHIELDS_CORE.total_blocked))

# ── 9. Plantilla HTML de Nueva Pestaña (Estrictamente 4 Colores) ──────────────
def get_clean_ntp_html(theme_class: str = "theme-dark") -> str:
    return f"""<!DOCTYPE html>
<html lang="es" class="{theme_class}">
<head>
  <meta charset="UTF-8">
  <title>Aegis</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    
    :root, .theme-dark {{
      --bg: #0d1117;
      --surface: #161b22;
      --text: #f0f6fc;
      --accent: #388bfd;
    }}
    
    .theme-light {{
      --bg: #f6f8fa;
      --surface: #ffffff;
      --text: #1f2328;
      --accent: #0969da;
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
      transition: background 0.25s ease, color 0.25s ease;
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
      width: 38px;
      height: 38px;
    }}
    .brand-name {{
      font-size: 1.8rem;
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
      color: var(--text);
      opacity: 0.65;
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
      gap: 8px;
      text-decoration: none;
      color: var(--text);
      font-size: 0.82rem;
      font-weight: 500;
      padding: 12px 16px;
      border-radius: 12px;
      background: var(--surface);
      border: 1px solid rgba(128, 128, 128, 0.15);
      transition: all 0.2s ease;
      min-width: 82px;
    }}
    .shortcut-card:hover {{
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
      color: var(--text);
      opacity: 0.55;
    }}
    .shield-dot {{
      width: 7px;
      height: 7px;
      background: var(--accent);
      border-radius: 50%;
      box-shadow: 0 0 8px var(--accent);
    }}
  </style>
</head>
<body>
  <main class="hero">
    <div class="brand-header">
      <svg class="brand-logo" viewBox="0 0 100 100" fill="none">
        <path d="M50 5 L88 22 V50 C88 74 50 95 50 95 C50 95 12 74 12 50 V22 Z" fill="var(--accent)"/>
        <path d="M50 14 L80 27 V50 C80 69 50 86 50 86 C50 86 20 69 20 50 V27 Z" fill="var(--bg)"/>
        <path d="M42 50 L48 56 L62 42" stroke="var(--accent)" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/>
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

# ── 10. Punto de Entrada Principal ────────────────────────────────────────────
def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Aegis")
    app.setApplicationVersion("1.3.1")

    window = AegisBrowserWindow()
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
