#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
                    AEGIS BROWSER - NATIVE RUNTIME (v1.3.3)
      Chromium WebEngine + Rust FFI Shields + Sitios Frecuentes Reales
================================================================================
Características:
  - Menú de Escudos limpio idéntico a Brave Browser (sin botones placebo de RAM).
  - Sitios Frecuentes Reales en Nueva Pestaña (se generan automáticamente según
    las páginas que el usuario visita con frecuencia).
  - Posibilidad de añadir atajos personalizados (+) y eliminar sitios con (×).
  - Detección correcta del dominio en el menú de escudos (nunca más "start").
  - Optimizaciones de memoria y CPU 100% automáticas y silenciosas en segundo plano
    (sin engaños de placebo ni contadores falsos).
  - Sistema de 2 temas estrictos (Oscuro y Claro) de máximo 4 colores cada uno.
================================================================================
"""

import os
import sys
import json
import time
import gc
import ctypes
import base64
import subprocess
from pathlib import Path
from urllib.parse import urlparse, parse_qs, unquote
from ctypes import wintypes

# ── 1. Hardening Extremo de Chromium (CPU, RAM y Rendimiento de Renderizado) ──
os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = (
    "--enable-gpu-rasterization "
    "--enable-zero-copy "
    "--ignore-gpu-blocklist "
    "--renderer-process-limit=3 "
    "--disable-breakpad "
    "--disable-telemetry "
    "--disable-sync "
    "--disable-domain-reliability "
    "--no-pings "
    "--dns-prefetch-disable "
    "--disable-speech-api "
    "--disable-wake-on-wifi "
    "--disable-background-networking "
    "--disable-component-update "
    "--disable-client-side-phishing-detection "
    "--enable-features=WebContentsDiscarding,IntensiveWakeUpThrottling,ParallelDownloading,CanvasOopRasterization,PurgeAndSuspend,BlinkMemorySaver "
    "--disable-features=Translate,OptimizationHints,MediaRouter "
    "--num-raster-threads=2 "
    "--v8-cache-options=code "
    "--js-flags=--expose-gc "
)

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QProgressBar, QTabBar, QStackedWidget,
    QLabel, QCheckBox, QFrame, QAbstractButton, QSizePolicy
)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import (
    QWebEngineProfile, QWebEngineSettings, QWebEngineUrlRequestInterceptor,
    QWebEngineDownloadRequest, QWebEngineScript
)
from PyQt6.QtCore import QUrl, Qt, QPoint, QTimer, QByteArray, QBuffer, QIODevice, QSize
from PyQt6.QtGui import QPainter, QColor, QBrush, QPen, QIcon, QPixmap, QShortcut, QKeySequence
from PyQt6.QtSvg import QSvgRenderer

BASE_DIR = Path(__file__).resolve().parent.parent.parent
CONFIG_FILE = Path.home() / ".aegis_browser_config.json"
HISTORY_FILE = Path.home() / ".aegis_browser_history.json"
DOWNLOADS_FILE = Path.home() / ".aegis_browser_downloads.json"
USERSCRIPTS_DIR = Path.home() / ".aegis_userscripts"

# ── 2. Gestor de Sitios Frecuentes e Historial Real ───────────────────────────
class HistoryManager:
    def __init__(self):
        self.data = {"frequent": {}, "custom": []}
        self.load()

    def load(self):
        if HISTORY_FILE.exists():
            try:
                self.data = json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
            except Exception:
                self.data = {"frequent": {}, "custom": []}

    def save(self):
        try:
            HISTORY_FILE.write_text(json.dumps(self.data, indent=2, ensure_ascii=False), encoding="utf-8")
        except Exception:
            pass

    def record_visit(self, url_str: str, title: str):
        if not url_str or not (url_str.startswith("http://") or url_str.startswith("https://")):
            return
        try:
            parsed = urlparse(url_str)
            domain = parsed.netloc.lower()
            if domain.startswith("www."):
                domain = domain[4:]
            if not domain:
                return

            # Si es una búsqueda, agrupar en el dominio principal
            if "duckduckgo.com" in domain and "?q=" in url_str:
                domain = "duckduckgo.com"
                url_str = "https://duckduckgo.com"
            elif "google." in domain and "/search" in url_str:
                domain = "google.com"
                url_str = "https://google.com"

            clean_title = title if title and title not in ("Página", "Nueva Pestaña", "start") else domain

            if domain not in self.data.get("frequent", {}):
                if "frequent" not in self.data:
                    self.data["frequent"] = {}
                self.data["frequent"][domain] = {
                    "domain": domain,
                    "title": clean_title,
                    "url": f"{parsed.scheme}://{parsed.netloc}",
                    "visits": 1,
                    "last_visited": time.time(),
                    "favicon": ""
                }
            else:
                self.data["frequent"][domain]["visits"] += 1
                self.data["frequent"][domain]["last_visited"] = time.time()
                if clean_title != domain and len(clean_title) < 25:
                    self.data["frequent"][domain]["title"] = clean_title

            # Historial cronológico completo
            if "history" not in self.data:
                self.data["history"] = []
            self.data["history"].insert(0, {
                "domain": domain,
                "title": clean_title,
                "url": url_str,
                "time": time.time()
            })
            if len(self.data["history"]) > 500:
                self.data["history"] = self.data["history"][:500]

            self.save()
        except Exception:
            pass

    def get_history(self, limit: int = 150) -> list:
        return self.data.get("history", [])[:limit]

    def clear_history(self):
        self.data["history"] = []
        self.data["frequent"] = {}
        self.save()

    def remove_history_item(self, url: str):
        if "history" in self.data:
            self.data["history"] = [h for h in self.data["history"] if h.get("url") != url]
            self.save()

    def update_favicon(self, domain: str, icon_data: str):
        if not domain or not icon_data:
            return
        try:
            changed = False
            if "frequent" in self.data and domain in self.data["frequent"]:
                if self.data["frequent"][domain].get("favicon") != icon_data:
                    self.data["frequent"][domain]["favicon"] = icon_data
                    changed = True
            if "custom" in self.data:
                for s in self.data["custom"]:
                    if s.get("domain") == domain and s.get("favicon") != icon_data:
                        s["favicon"] = icon_data
                        changed = True
            if changed:
                self.save()
        except Exception:
            pass

    def add_custom(self, title: str, url: str):
        if not url:
            return
        if not url.startswith("http://") and not url.startswith("https://"):
            url = "https://" + url
        try:
            domain = urlparse(url).netloc.lower().replace("www.", "") or title.lower()
            if "custom" not in self.data:
                self.data["custom"] = []
            self.data["custom"].append({
                "domain": domain,
                "title": title or domain,
                "url": url,
                "visits": 9999,
                "last_visited": time.time(),
                "favicon": ""
            })
            self.save()
        except Exception:
            pass

    def remove_site(self, domain_or_url: str):
        if "frequent" in self.data and domain_or_url in self.data["frequent"]:
            del self.data["frequent"][domain_or_url]
        if "custom" in self.data:
            self.data["custom"] = [
                s for s in self.data["custom"]
                if s.get("domain") != domain_or_url and s.get("url") != domain_or_url
            ]
        self.save()

    def get_frequent_sites(self, limit: int = 8) -> list:
        custom = self.data.get("custom", [])
        frequent = sorted(
            self.data.get("frequent", {}).values(),
            key=lambda x: (x.get("visits", 0), x.get("last_visited", 0)),
            reverse=True
        )
        seen = set()
        result = []
        for s in custom + frequent:
            dom = s.get("domain")
            if dom and dom not in seen:
                seen.add(dom)
                result.append(s)
            if len(result) >= limit:
                break

        # Si aún no tiene historial (recién instalado), proveer accesos iniciales editables
        if not result:
            defaults = [
                {"domain": "youtube.com", "title": "YouTube", "url": "https://youtube.com"},
                {"domain": "github.com", "title": "GitHub", "url": "https://github.com"},
                {"domain": "reddit.com", "title": "Reddit", "url": "https://reddit.com"},
                {"domain": "twitch.tv", "title": "Twitch", "url": "https://twitch.tv"},
            ]
            return defaults

        return result

# ── 2.1 Gestor de Descargas Nativas ───────────────────────────────────────────
class DownloadsManager:
    def __init__(self):
        self.downloads = []
        self.load()

    def load(self):
        if DOWNLOADS_FILE.exists():
            try:
                self.downloads = json.loads(DOWNLOADS_FILE.read_text(encoding="utf-8"))
            except Exception:
                self.downloads = []

    def save(self):
        try:
            DOWNLOADS_FILE.write_text(json.dumps(self.downloads, indent=2, ensure_ascii=False), encoding="utf-8")
        except Exception:
            pass

    def add(self, item: dict):
        self.downloads.insert(0, item)
        if len(self.downloads) > 100:
            self.downloads = self.downloads[:100]
        self.save()

    def update(self, item_id: str, updates: dict):
        for d in self.downloads:
            if d.get("id") == item_id:
                d.update(updates)
                break
        self.save()

    def clear(self):
        self.downloads = []
        self.save()

# ── 3. Optimizador Silencioso en Segundo Plano (Sin placebo ni botones falsos) ─
TH32CS_SNAPPROCESS = 0x00000002

class PROCESSENTRY32(ctypes.Structure):
    _fields_ = [
        ('dwSize', wintypes.DWORD),
        ('cntUsage', wintypes.DWORD),
        ('th32ProcessID', wintypes.DWORD),
        ('th32DefaultHeapID', ctypes.POINTER(ctypes.c_ulong)),
        ('th32ModuleID', wintypes.DWORD),
        ('cntThreads', wintypes.DWORD),
        ('th32ParentProcessID', wintypes.DWORD),
        ('pcPriClassBase', ctypes.c_long),
        ('dwFlags', wintypes.DWORD),
        ('szExeFile', ctypes.c_char * 260)
    ]

class PROCESS_MEMORY_COUNTERS_EX(ctypes.Structure):
    _fields_ = [
        ('cb', wintypes.DWORD),
        ('PageFaultCount', wintypes.DWORD),
        ('PeakWorkingSetSize', ctypes.c_size_t),
        ('WorkingSetSize', ctypes.c_size_t),
        ('QuotaPeakPagedPoolUsage', ctypes.c_size_t),
        ('QuotaPagedPoolUsage', ctypes.c_size_t),
        ('QuotaPeakNonPagedPoolUsage', ctypes.c_size_t),
        ('QuotaNonPagedPoolUsage', ctypes.c_size_t),
        ('PagefileUsage', ctypes.c_size_t),
        ('PeakPagefileUsage', ctypes.c_size_t),
        ('PrivateUsage', ctypes.c_size_t),
    ]

kernel32 = ctypes.windll.kernel32 if sys.platform == "win32" else None
psapi = ctypes.windll.psapi if sys.platform == "win32" else None

if kernel32 and psapi:
    kernel32.GetCurrentProcess.restype = wintypes.HANDLE
    kernel32.OpenProcess.restype = wintypes.HANDLE
    kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    psapi.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(PROCESS_MEMORY_COUNTERS_EX), wintypes.DWORD]
    psapi.GetProcessMemoryInfo.restype = wintypes.BOOL
    psapi.EmptyWorkingSet.argtypes = [wintypes.HANDLE]
    psapi.EmptyWorkingSet.restype = wintypes.BOOL

def silent_background_memory_purge():
    """Compactación periódica del sistema operativo ejecutada automáticamente."""
    if not kernel32 or not psapi:
        return
    gc.collect()
    try:
        my_pid = os.getpid()
        child_pids = []
        h_snap = kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
        if h_snap != wintypes.HANDLE(-1).value and h_snap != 0:
            pe = PROCESSENTRY32()
            pe.dwSize = ctypes.sizeof(pe)
            if kernel32.Process32First(h_snap, ctypes.byref(pe)):
                while True:
                    if pe.th32ParentProcessID == my_pid:
                        child_pids.append(pe.th32ProcessID)
                    if not kernel32.Process32Next(h_snap, ctypes.byref(pe)):
                        break
            kernel32.CloseHandle(h_snap)

        all_pids = [my_pid] + child_pids
        for pid in all_pids:
            if pid == my_pid:
                h = kernel32.GetCurrentProcess()
                close_needed = False
            else:
                h = kernel32.OpenProcess(0x1F0FFF, False, pid)
                close_needed = True
            if h:
                psapi.EmptyWorkingSet(h)
                if close_needed:
                    kernel32.CloseHandle(h)
    except Exception:
        pass

# ── 4. Helper para conversión Hex a RGB y Creación de Iconos Vectoriales ──────
def hex_to_rgb(h: str) -> str:
    h = h.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"{r}, {g}, {b}"

def svg_to_icon(svg_str: str, size: int = 16) -> QIcon:
    try:
        renderer = QSvgRenderer(QByteArray(svg_str.encode("utf-8")))
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.end()
        return QIcon(pixmap)
    except Exception:
        return QIcon()

def create_shield_icon(color_hex: str = "#388bfd", size: int = 16) -> QIcon:
    """Genera un icono de escudo vectorial nítido sin emojis medievales de Windows."""
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="{size}" height="{size}" fill="none" stroke="{color_hex}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
      <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
      <path d="m9 12 2 2 4-4"/>
    </svg>"""
    return svg_to_icon(svg, size)

def create_settings_icon(color_hex: str = "#388bfd", size: int = 16) -> QIcon:
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="{size}" height="{size}" fill="none" stroke="{color_hex}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="12" cy="12" r="3"/>
      <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/>
    </svg>"""
    return svg_to_icon(svg, size)

def create_download_icon(color_hex: str = "#388bfd", size: int = 16) -> QIcon:
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="{size}" height="{size}" fill="none" stroke="{color_hex}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
      <polyline points="7 10 12 15 17 10"/>
      <line x1="12" y1="15" x2="12" y2="3"/>
    </svg>"""
    return svg_to_icon(svg, size)

def create_history_icon(color_hex: str = "#388bfd", size: int = 16) -> QIcon:
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="{size}" height="{size}" fill="none" stroke="{color_hex}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="12" cy="12" r="10"/>
      <polyline points="12 6 12 12 14 14"/>
    </svg>"""
    return svg_to_icon(svg, size)

def create_extension_icon(color_hex: str = "#388bfd", size: int = 16) -> QIcon:
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="{size}" height="{size}" fill="none" stroke="{color_hex}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
      <path d="M12 2v4m0 12v4M4.93 4.93l2.83 2.83m8.48 8.48l2.83 2.83M2 12h4m12 0h4M4.93 19.07l2.83-2.83m8.48-8.48l2.83-2.83"/>
    </svg>"""
    return svg_to_icon(svg, size)

# ── 5. Soporte de Barra de Título Nativa Windows DWM ───────────────────────────
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

# ── 6. Motor Aegis Shields (Rust FFI) ──────────────────────────────────────────
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

# ── 7. Interceptor de Peticiones de Red ───────────────────────────────────────
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

# ── 8. Sistema de 2 Temas Estrictos (Máximo 4 Colores por Tema) ───────────────
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

# ── 9. Switch Interactivo Moderno (Estilo Brave) ──────────────────────────────
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

# ── 10. Menú Desplegable de Aegis Shields (Estilo Brave 100% Auténtico) ───────
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

        # ── 1. Cabecera: Dominio real + Subtítulo + Switch Principal ───────────
        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)

        site_info_layout = QVBoxLayout()
        site_info_layout.setSpacing(2)

        self.lbl_site = QLabel("Nueva Pestaña")
        self.lbl_site.setObjectName("PopupSiteName")
        site_info_layout.addWidget(self.lbl_site)

        self.lbl_status = QLabel("Protección Aegis activada")
        self.lbl_status.setObjectName("PopupStatusText")
        site_info_layout.addWidget(self.lbl_status)

        header_layout.addLayout(site_info_layout)
        header_layout.addStretch()

        self.main_switch = ToggleSwitch(checked=True)
        self.main_switch.toggled.connect(self.on_main_switch_toggled)
        header_layout.addWidget(self.main_switch)

        layout.addLayout(header_layout)

        # ── 2. Tarjeta Estadística (Estilo Brave) ─────────────────────────────
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

        # ── 3. Botón Desplegable "Opciones avanzadas" ──────────────────────────
        self.btn_advanced = QPushButton("⚙ Opciones avanzadas ▾")
        self.btn_advanced.setObjectName("PopupAdvancedBtn")
        self.btn_advanced.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_advanced.clicked.connect(self.toggle_advanced)
        layout.addWidget(self.btn_advanced)

        # Contenedor Colapsable (Opciones de Privacidad Granulares)
        self.advanced_container = QWidget()
        adv_layout = QVBoxLayout(self.advanced_container)
        adv_layout.setContentsMargins(4, 2, 4, 6)
        adv_layout.setSpacing(8)

        self.cb_network = QCheckBox("Bloqueo de red socket Rust (cero descarga)")
        self.cb_network.setChecked(True)
        self.cb_network.toggled.connect(self.toggle_network)
        adv_layout.addWidget(self.cb_network)

        self.cb_cosmetic = QCheckBox("Filtrado cosmético CSS inmediato")
        self.cb_cosmetic.setChecked(True)
        adv_layout.addWidget(self.cb_cosmetic)

        self.cb_video = QCheckBox("Salto automático de comerciales de video")
        self.cb_video.setChecked(True)
        adv_layout.addWidget(self.cb_video)

        self.cb_countdown = QCheckBox("Bypass de temporizadores y acortadores")
        self.cb_countdown.setChecked(True)
        adv_layout.addWidget(self.cb_countdown)

        self.advanced_container.hide()
        layout.addWidget(self.advanced_container)

        # ── 4. Pie de nota minimalista ────────────────────────────────────────
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

    def update_site(self, raw_host: str, count: int):
        # Detección inteligente para que nunca muestre "start" ni nombres raros
        if not raw_host or raw_host in ("start", "Nueva Pestaña", "about:blank", ""):
            self.lbl_site.setText("Nueva Pestaña")
            self.lbl_status.setText("Protección Aegis activada")
        else:
            clean_host = raw_host.lower().replace("www.", "")
            self.lbl_site.setText(clean_host)
            self.lbl_status.setText("Escudos activados para este sitio")
        self.lbl_count.setText(str(count))

    def apply_theme(self, t: dict):
        rgb_text = hex_to_rgb(t["text"])
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
            QLabel#PopupFooter {{
                color: rgba({rgb_text}, 0.45);
                font-size: 10px;
                margin-top: 4px;
            }}
        """
        self.setStyleSheet(qss)
        self.update()

# ── 10.1 Menú Principal de la Aplicación (Estilo Brave ⋮ Frameless Dropdown) ───
class AegisAppMenu(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent, Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.setObjectName("AegisAppMenu")
        self.setFixedWidth(240)
        self.parent_win = parent
        self.init_ui()

    def hideEvent(self, event):
        if self.parent_win:
            self.parent_win._last_app_menu_close_time = time.time()
        super().hideEvent(event)

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(2)

        def add_item(text: str, shortcut: str, callback):
            btn = QPushButton()
            btn.setProperty("class", "menu-item-btn")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            h_box = QHBoxLayout(btn)
            h_box.setContentsMargins(10, 6, 10, 6)
            h_box.setSpacing(8)

            lbl_txt = QLabel(text)
            lbl_txt.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
            lbl_txt.setStyleSheet("background: transparent; border: none; font-size: 12.5px; font-weight: 500;")
            h_box.addWidget(lbl_txt)
            h_box.addStretch()

            if shortcut:
                lbl_sc = QLabel(shortcut)
                lbl_sc.setProperty("class", "menu-shortcut-lbl")
                lbl_sc.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
                h_box.addWidget(lbl_sc)

            btn.clicked.connect(lambda: (self.hide(), callback()))
            layout.addWidget(btn)
            return btn

        def add_separator():
            sep = QFrame()
            sep.setObjectName("MenuSeparator")
            sep.setFixedHeight(1)
            layout.addWidget(sep)

        add_item("➕ Nueva pestaña", "Ctrl+T", lambda: self.parent_win.add_new_tab())
        add_item("🗂️ Nueva ventana", "Ctrl+N", lambda: self.parent_win.open_new_window())
        add_separator()
        add_item("📥 Descargas", "Ctrl+J", lambda: self.parent_win.open_internal_page("aegis://downloads"))
        add_item("🕒 Historial", "Ctrl+H", lambda: self.parent_win.open_internal_page("aegis://history"))
        add_item("🧩 Extensiones", "Ctrl+Shift+E", lambda: self.parent_win.open_internal_page("aegis://extensions"))
        add_separator()
        add_item("⚙️ Configuración", "Alt+S", lambda: self.parent_win.open_internal_page("aegis://settings"))
        add_separator()

        # Fila de Zoom
        zoom_widget = QWidget()
        zoom_layout = QHBoxLayout(zoom_widget)
        zoom_layout.setContentsMargins(10, 4, 10, 4)
        zoom_layout.setSpacing(8)

        lbl_zoom = QLabel("Zoom")
        lbl_zoom.setStyleSheet("font-size: 12px; font-weight: 500;")
        zoom_layout.addWidget(lbl_zoom)
        zoom_layout.addStretch()

        btn_zoom_out = QPushButton("−")
        btn_zoom_out.setProperty("class", "zoom-btn")
        btn_zoom_out.clicked.connect(lambda: self.parent_win.zoom_out())
        zoom_layout.addWidget(btn_zoom_out)

        self.lbl_zoom_val = QLabel("100%")
        self.lbl_zoom_val.setObjectName("ZoomVal")
        self.lbl_zoom_val.setAlignment(Qt.AlignmentFlag.AlignCenter)
        zoom_layout.addWidget(self.lbl_zoom_val)

        btn_zoom_in = QPushButton("+")
        btn_zoom_in.setProperty("class", "zoom-btn")
        btn_zoom_in.clicked.connect(lambda: self.parent_win.zoom_in())
        zoom_layout.addWidget(btn_zoom_in)

        layout.addWidget(zoom_widget)
        add_separator()

        add_item("ℹ️ Acerca de Aegis v1.3.4", "", lambda: self.parent_win.open_internal_page("aegis://settings"))

    def apply_theme(self, t: dict):
        rgb_text = hex_to_rgb(t["text"])
        qss = f"""
            QFrame#AegisAppMenu {{
                background-color: {t['surface']};
                border: 1px solid rgba({rgb_text}, 0.15);
                border-radius: 12px;
            }}
            QPushButton.menu-item-btn {{
                background: transparent;
                border: none;
                border-radius: 6px;
                color: {t['text']};
                padding: 0;
                min-height: 28px;
            }}
            QPushButton.menu-item-btn:hover {{
                background-color: {t['bg']};
                color: {t['accent']};
            }}
            QLabel.menu-shortcut-lbl {{
                color: rgba({rgb_text}, 0.45);
                font-size: 11px;
                font-family: -apple-system, 'Segoe UI', monospace;
                background: transparent;
                border: none;
            }}
            QFrame#MenuSeparator {{
                background-color: rgba({rgb_text}, 0.08);
                border: none;
                margin: 3px 6px;
            }}
            QPushButton.zoom-btn {{
                background-color: {t['bg']};
                border: 1px solid rgba({rgb_text}, 0.15);
                border-radius: 4px;
                color: {t['text']};
                font-size: 13px;
                font-weight: 700;
                width: 24px;
                height: 22px;
            }}
            QPushButton.zoom-btn:hover {{
                border-color: {t['accent']};
                color: {t['accent']};
            }}
            QLabel#ZoomVal {{
                color: {t['text']};
                font-size: 11.5px;
                min-width: 38px;
            }}
        """
        self.setStyleSheet(qss)
        self.update()

# ── 11. Ventana Principal de Aegis Browser ────────────────────────────────────
class AegisBrowserWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Aegis")
        self.resize(1340, 860)

        self._last_popup_close_time = 0.0
        self._last_app_menu_close_time = 0.0
        self.config = self.load_config()
        self.current_theme_name = self.config.get("theme", "Oscuro")

        # Gestores reales (Historial y Descargas Nativas)
        self.history_mgr = HistoryManager()
        self.downloads_mgr = DownloadsManager()

        # Configurar Perfil Chromium
        self.profile = QWebEngineProfile.defaultProfile()
        self.profile.setHttpUserAgent(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Aegis/1.3.4"
        )
        self.profile.settings().setAttribute(QWebEngineSettings.WebAttribute.JavascriptCanOpenWindows, False)
        self.profile.settings().setAttribute(QWebEngineSettings.WebAttribute.FullScreenSupportEnabled, True)
        self.profile.settings().setAttribute(QWebEngineSettings.WebAttribute.PlaybackRequiresUserGesture, True)

        # Interceptor de peticiones de red
        self.interceptor = AegisRequestInterceptor(self.on_shield_block)
        self.profile.setUrlRequestInterceptor(self.interceptor)

        # Gestor de Descargas Nativas conectado a Chromium
        self.profile.downloadRequested.connect(self.on_download_requested)

        # Cargar scripts de usuario (UserScripts)
        self.load_userscripts()

        self.views = []
        self.init_ui()

        # Menús flotantes (Escudos y Menú Principal ⋮ estilo Brave)
        self.shields_popup = AegisShieldsPopup(self, self.interceptor)
        self.app_menu = AegisAppMenu(self)

        # Atajos de teclado nativos
        self.setup_shortcuts()

        # Aplicar tema inicial
        self.apply_theme(self.current_theme_name)

        # Compactación silenciosa de memoria automática cada 90s
        self.auto_purge_timer = QTimer(self)
        self.auto_purge_timer.setInterval(90 * 1000)
        self.auto_purge_timer.timeout.connect(silent_background_memory_purge)
        self.auto_purge_timer.start()

        # Abrir pestaña inicial
        self.add_new_tab()

    def load_config(self) -> dict:
        default_config = {
            "theme": "Oscuro",
            "tab_position": "horizontal",
            "search_engine": "DuckDuckGo",
            "shields_enabled": True,
            "force_dark_mode": True
        }
        if CONFIG_FILE.exists():
            try:
                saved = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
                default_config.update(saved)
            except Exception:
                pass
        return default_config

    def save_config(self):
        try:
            CONFIG_FILE.write_text(json.dumps(self.config, indent=2, ensure_ascii=False), encoding="utf-8")
        except Exception:
            pass

    def setup_shortcuts(self):
        QShortcut(QKeySequence("Ctrl+T"), self, lambda: self.add_new_tab())
        QShortcut(QKeySequence("Ctrl+W"), self, lambda: self.close_tab(self.tab_bar.currentIndex()))
        QShortcut(QKeySequence("Ctrl+N"), self, self.open_new_window)
        QShortcut(QKeySequence("Ctrl+J"), self, lambda: self.open_internal_page("aegis://downloads"))
        QShortcut(QKeySequence("Ctrl+H"), self, lambda: self.open_internal_page("aegis://history"))
        QShortcut(QKeySequence("Ctrl+Shift+E"), self, lambda: self.open_internal_page("aegis://extensions"))
        QShortcut(QKeySequence("Alt+S"), self, lambda: self.open_internal_page("aegis://settings"))
        QShortcut(QKeySequence("Ctrl+L"), self, lambda: (self.url_bar.setFocus(), self.url_bar.selectAll()))
        QShortcut(QKeySequence("Ctrl+R"), self, self.reload_page)
        QShortcut(QKeySequence("F5"), self, self.reload_page)
        QShortcut(QKeySequence("Ctrl+Plus"), self, self.zoom_in)
        QShortcut(QKeySequence("Ctrl+Equal"), self, self.zoom_in)
        QShortcut(QKeySequence("Ctrl+Minus"), self, self.zoom_out)
        QShortcut(QKeySequence("Ctrl+0"), self, self.zoom_reset)

    def load_userscripts(self):
        try:
            USERSCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
            for s_file in USERSCRIPTS_DIR.glob("*.js"):
                content = s_file.read_text(encoding="utf-8")
                s = QWebEngineScript()
                s.setName(s_file.stem)
                s.setSourceCode(content)
                s.setInjectionPoint(QWebEngineScript.InjectionPoint.DocumentReady)
                s.setWorldId(QWebEngineScript.ScriptWorldId.MainWorld)
                s.setRunsOnSubFrames(False)
                self.profile.scripts().insert(s)
        except Exception:
            pass

    def on_download_requested(self, download: QWebEngineDownloadRequest):
        save_dir = Path.home() / "Downloads"
        save_dir.mkdir(parents=True, exist_ok=True)
        filename = download.suggestedFileName() or "descarga"
        download.setDownloadDirectory(str(save_dir))
        download.setDownloadFileName(filename)
        full_path = str(save_dir / filename)
        download.accept()

        download_id = str(int(time.time() * 1000))
        item = {
            "id": download_id,
            "filename": filename,
            "path": full_path,
            "url": download.url().toString(),
            "total_bytes": download.totalBytes(),
            "received_bytes": 0,
            "state": "downloading",
            "time": time.time()
        }
        self.downloads_mgr.add(item)
        download.receivedBytesChanged.connect(lambda: self.on_download_progress(download, download_id))
        download.isFinishedChanged.connect(lambda: self.on_download_finished(download, download_id))

    def on_download_progress(self, download: QWebEngineDownloadRequest, download_id: str):
        self.downloads_mgr.update(download_id, {
            "received_bytes": download.receivedBytes(),
            "total_bytes": download.totalBytes()
        })

    def on_download_finished(self, download: QWebEngineDownloadRequest, download_id: str):
        state_str = "completed" if download.state() == QWebEngineDownloadRequest.DownloadState.DownloadCompleted else "cancelled"
        self.downloads_mgr.update(download_id, {
            "state": state_str,
            "received_bytes": download.receivedBytes(),
            "total_bytes": download.totalBytes()
        })

    def toggle_app_menu(self):
        now = time.time()
        if hasattr(self, "_last_app_menu_close_time") and (now - self._last_app_menu_close_time < 0.25):
            return

        if self.app_menu.isVisible():
            self.app_menu.hide()
            return

        if self.shields_popup.isVisible():
            self.shields_popup.hide()

        v = self.current_view()
        zf = v.zoomFactor() if v else 1.0
        self.app_menu.lbl_zoom_val.setText(f"{int(zf*100)}%")

        btn_pos = self.btn_more.mapToGlobal(QPoint(0, self.btn_more.height()))
        popup_x = btn_pos.x() + self.btn_more.width() - self.app_menu.width()
        popup_y = btn_pos.y() + 6
        self.app_menu.move(popup_x, popup_y)
        self.app_menu.show()
        self.app_menu.raise_()

    def open_new_window(self):
        win = AegisBrowserWindow()
        win.show()
        if not hasattr(QApplication.instance(), "_aegis_windows"):
            QApplication.instance()._aegis_windows = []
        QApplication.instance()._aegis_windows.append(win)

    def zoom_in(self):
        v = self.current_view()
        if v:
            zf = round(v.zoomFactor() + 0.1, 1)
            if zf <= 3.0:
                v.setZoomFactor(zf)
                if hasattr(self, "app_menu"):
                    self.app_menu.lbl_zoom_val.setText(f"{int(zf*100)}%")

    def zoom_out(self):
        v = self.current_view()
        if v:
            zf = round(v.zoomFactor() - 0.1, 1)
            if zf >= 0.3:
                v.setZoomFactor(zf)
                if hasattr(self, "app_menu"):
                    self.app_menu.lbl_zoom_val.setText(f"{int(zf*100)}%")

    def zoom_reset(self):
        v = self.current_view()
        if v:
            v.setZoomFactor(1.0)
            if hasattr(self, "app_menu"):
                self.app_menu.lbl_zoom_val.setText("100%")

    def init_ui(self):
        container = QWidget()
        self.setCentralWidget(container)
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ── 1. Tira de Pestañas Limpia ────────────────────────────────────────
        self.tab_header = QWidget()
        self.tab_header.setObjectName("TabHeader")
        tab_header_layout = QHBoxLayout(self.tab_header)
        tab_header_layout.setContentsMargins(8, 6, 8, 0)
        tab_header_layout.setSpacing(6)

        self.tab_bar = QTabBar()
        self.tab_bar.setTabsClosable(True)
        self.tab_bar.setMovable(True)
        self.tab_bar.setIconSize(QSize(16, 16))
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

        # Botón Escudo Aegis Shields (Icono vectorial y borde neutral normal)
        self.shield_btn = QPushButton(" 0")
        self.shield_btn.setObjectName("ShieldBtn")
        self.shield_btn.setToolTip("Aegis Shields: Click para desplegar panel")
        self.shield_btn.clicked.connect(self.toggle_shields_popup)
        toolbar_layout.addWidget(self.shield_btn)

        # Botón de Cambio Rápido de Tema (Oscuro / Claro)
        self.btn_theme_toggle = QPushButton("☀️")
        self.btn_theme_toggle.setObjectName("ThemeToggleBtn")
        self.btn_theme_toggle.setToolTip("Cambiar tema (Oscuro / Claro)")
        self.btn_theme_toggle.clicked.connect(self.toggle_theme)
        toolbar_layout.addWidget(self.btn_theme_toggle)

        # Botón Menú Principal (⋮ Tres Puntos al estilo Brave)
        self.btn_more = QPushButton("⋮")
        self.btn_more.setObjectName("MoreBtn")
        self.btn_more.setToolTip("Personalizar y controlar Aegis")
        self.btn_more.clicked.connect(self.toggle_app_menu)
        toolbar_layout.addWidget(self.btn_more)

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

    def save_theme(self, theme_name: str):
        self.config["theme"] = theme_name
        self.save_config()

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

        if is_dark:
            self.btn_theme_toggle.setText("☀️")
            self.btn_theme_toggle.setToolTip("Cambiar a Modo Claro")
        else:
            self.btn_theme_toggle.setText("🌙")
            self.btn_theme_toggle.setToolTip("Cambiar a Modo Oscuro")

        apply_windows_dark_title_bar(self.winId(), dark=is_dark)
        self.profile.settings().setAttribute(QWebEngineSettings.WebAttribute.ForceDarkMode, is_dark)

        rgb_text = hex_to_rgb(t["text"])
        rgb_accent = hex_to_rgb(t["accent"])

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
            QPushButton#MoreBtn {{
                background: transparent;
                border: none;
                color: {t['text']};
                font-size: 17px;
                font-weight: 700;
                border-radius: 14px;
                width: 30px;
                height: 30px;
            }}
            QPushButton#MoreBtn:hover {{
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
            QPushButton#ShieldBtn {{
                background-color: transparent;
                border: 1px solid rgba({rgb_text}, 0.14);
                border-radius: 6px;
                color: {t['text']};
                padding: 4px 10px;
                font-size: 12px;
                font-weight: 500;
            }}
            QPushButton#ShieldBtn:hover {{
                background-color: {t['surface']};
                border-color: rgba({rgb_text}, 0.28);
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

        if hasattr(self, "shield_btn"):
            self.shield_btn.setIcon(create_shield_icon(t["accent"], 16))

        if hasattr(self, "shields_popup"):
            self.shields_popup.apply_theme(t)

        if hasattr(self, "app_menu"):
            self.app_menu.apply_theme(t)

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
        host = url.host() if url else ""
        self.shields_popup.update_site(host, SHIELDS_CORE.total_blocked)

        btn_pos = self.shield_btn.mapToGlobal(QPoint(0, self.shield_btn.height()))
        popup_x = btn_pos.x() + self.shield_btn.width() - self.shields_popup.width()
        popup_y = btn_pos.y() + 6
        self.shields_popup.move(popup_x, popup_y)
        self.shields_popup.show()
        self.shields_popup.raise_()

    def add_new_tab(self, url_str: str = "") -> QWebEngineView:
        view = QWebEngineView()
        view._aegis_target_url = url_str
        view.setPage(view.page())

        tab_idx = self.tab_bar.addTab("Nueva Pestaña")
        stack_idx = self.stack.addWidget(view)
        self.views.append(view)

        view.urlChanged.connect(lambda qurl, v=view: self.on_url_changed(qurl, v))
        view.loadProgress.connect(self.on_load_progress)
        view.loadFinished.connect(lambda ok, v=view: self.on_load_finished(ok, v))
        view.iconChanged.connect(lambda icon, v=view: self.on_icon_changed(icon, v))

        if url_str:
            view.load(QUrl(url_str))
        else:
            self.load_ntp(view)

        self.tab_bar.setCurrentIndex(tab_idx)
        self.stack.setCurrentIndex(stack_idx)
        return view

    def load_ntp(self, view: QWebEngineView):
        idx = self.views.index(view) if view in self.views else -1
        t = THEMES.get(self.current_theme_name, THEMES["Oscuro"])
        if idx != -1:
            self.tab_bar.setTabIcon(idx, create_shield_icon(t["accent"], 14))
            self.tab_bar.setTabText(idx, "Nueva Pestaña")
        frequent_sites = self.history_mgr.get_frequent_sites(limit=8)
        html = get_clean_ntp_html(t["ntp_class"], frequent_sites)
        view.setHtml(html, QUrl("aegis://start"))

    def open_internal_page(self, url_str: str, new_tab: bool = False):
        view = self.add_new_tab() if new_tab or not self.current_view() else self.current_view()
        if not view:
            return

        if url_str == "aegis://start":
            self.load_ntp(view)
        elif url_str == "aegis://settings":
            self.load_settings(view)
        elif url_str == "aegis://downloads":
            self.load_downloads(view)
        elif url_str == "aegis://history":
            self.load_history(view)
        elif url_str == "aegis://extensions":
            self.load_extensions(view)

    def load_settings(self, view: QWebEngineView):
        idx = self.views.index(view) if view in self.views else -1
        t = THEMES.get(self.current_theme_name, THEMES["Oscuro"])
        if idx != -1:
            self.tab_bar.setTabIcon(idx, create_settings_icon(t["accent"], 14))
            self.tab_bar.setTabText(idx, "Configuración")
        html = get_settings_html(t["ntp_class"], self.config)
        view.setHtml(html, QUrl("aegis://settings"))

    def load_downloads(self, view: QWebEngineView):
        idx = self.views.index(view) if view in self.views else -1
        t = THEMES.get(self.current_theme_name, THEMES["Oscuro"])
        if idx != -1:
            self.tab_bar.setTabIcon(idx, create_download_icon(t["accent"], 14))
            self.tab_bar.setTabText(idx, "Descargas")
        html = get_downloads_html(t["ntp_class"], self.downloads_mgr.downloads)
        view.setHtml(html, QUrl("aegis://downloads"))

    def load_history(self, view: QWebEngineView):
        idx = self.views.index(view) if view in self.views else -1
        t = THEMES.get(self.current_theme_name, THEMES["Oscuro"])
        if idx != -1:
            self.tab_bar.setTabIcon(idx, create_history_icon(t["accent"], 14))
            self.tab_bar.setTabText(idx, "Historial")
        html = get_history_html(t["ntp_class"], self.history_mgr.get_history())
        view.setHtml(html, QUrl("aegis://history"))

    def load_extensions(self, view: QWebEngineView):
        idx = self.views.index(view) if view in self.views else -1
        t = THEMES.get(self.current_theme_name, THEMES["Oscuro"])
        if idx != -1:
            self.tab_bar.setTabIcon(idx, create_extension_icon(t["accent"], 14))
            self.tab_bar.setTabText(idx, "Extensiones")
        scripts = [f.name for f in USERSCRIPTS_DIR.glob("*.js")] if USERSCRIPTS_DIR.exists() else []
        html = get_extensions_html(t["ntp_class"], scripts)
        view.setHtml(html, QUrl("aegis://extensions"))

    def update_tab_layout(self):
        is_vert = self.config.get("tab_position") == "vertical"
        if is_vert:
            self.tab_bar.setShape(QTabBar.Shape.RoundedWest)
            self.tab_header.setFixedWidth(160)
            self.tab_header.setMaximumHeight(16777215)
        else:
            self.tab_bar.setShape(QTabBar.Shape.RoundedNorth)
            self.tab_header.setFixedHeight(38)
            self.tab_header.setMaximumWidth(16777215)
        self.apply_theme(self.current_theme_name)

    def on_icon_changed(self, icon: QIcon, view: QWebEngineView):
        if icon.isNull():
            return
        idx = self.views.index(view) if view in self.views else -1
        if idx != -1:
            self.tab_bar.setTabIcon(idx, icon)

        url = view.url()
        if not url.isValid():
            return
        domain = url.host().lower().replace("www.", "")
        if not domain or domain in ("start", "about:blank"):
            return

        try:
            pixmap = icon.pixmap(64, 64)
            if not pixmap.isNull():
                buf = QByteArray()
                buffer = QBuffer(buf)
                buffer.open(QIODevice.OpenModeFlag.WriteOnly)
                pixmap.save(buffer, "PNG")
                b64 = base64.b64encode(buf.data()).decode("ascii")
                data_uri = f"data:image/png;base64,{b64}"
                self.history_mgr.update_favicon(domain, data_uri)
        except Exception:
            pass

    def close_tab(self, index: int):
        if self.tab_bar.count() > 1:
            view = self.views.pop(index)
            self.tab_bar.removeTab(index)
            self.stack.removeWidget(view)
            view.deleteLater()
            QTimer.singleShot(150, silent_background_memory_purge)
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

        # Atajos directos desde el Omnibox
        shortcuts = {
            "settings": "aegis://settings",
            "config": "aegis://settings",
            "configuracion": "aegis://settings",
            "configuración": "aegis://settings",
            "downloads": "aegis://downloads",
            "descargas": "aegis://downloads",
            "history": "aegis://history",
            "historial": "aegis://history",
            "extensions": "aegis://extensions",
            "extensiones": "aegis://extensions",
            "start": "aegis://start",
            "inicio": "aegis://start"
        }
        if text.lower() in shortcuts:
            self.open_internal_page(shortcuts[text.lower()])
            return

        if text.startswith("aegis://"):
            self.open_internal_page(text)
            return

        if text.startswith("http://") or text.startswith("https://") or text.startswith("file://"):
            target_url = QUrl(text)
        elif "." in text and " " not in text:
            target_url = QUrl("https://" + text)
        else:
            engine = self.config.get("search_engine", "DuckDuckGo")
            if engine == "Google":
                target_url = QUrl(f"https://google.com/search?q={text}")
            elif engine == "Bing":
                target_url = QUrl(f"https://www.bing.com/search?q={text}")
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
        url_str = qurl.toString()

        # Páginas internas directas
        if url_str == "aegis://settings":
            self.load_settings(view)
            return
        elif url_str == "aegis://downloads":
            self.load_downloads(view)
            return
        elif url_str == "aegis://history":
            self.load_history(view)
            return
        elif url_str == "aegis://extensions":
            self.load_extensions(view)
            return
        elif url_str == "aegis://start":
            self.load_ntp(view)
            return

        # Interceptar acciones desde páginas internas
        if url_str.startswith("aegis://action?"):
            try:
                parsed = urlparse(url_str)
                q = parse_qs(parsed.query)
                if "remove" in q:
                    domain = q["remove"][0]
                    self.history_mgr.remove_site(domain)
                    self.load_ntp(view)
                    return
                elif "add" in q:
                    data = json.loads(unquote(q["add"][0]))
                    self.history_mgr.add_custom(data.get("title", ""), data.get("url", ""))
                    self.load_ntp(view)
                    return
                elif "set_config" in q:
                    data = json.loads(unquote(q["set_config"][0]))
                    k, val = data.get("key"), data.get("value")
                    self.config[k] = val
                    self.save_config()
                    if k == "theme":
                        self.apply_theme(val)
                    elif k == "tab_position":
                        self.update_tab_layout()
                    elif k == "shields_enabled":
                        self.interceptor.enabled = bool(val)
                    self.load_settings(view)
                    return
                elif "open_file" in q:
                    file_path = unquote(q["open_file"][0])
                    if os.path.exists(file_path):
                        os.startfile(file_path)
                    return
                elif "open_folder" in q:
                    file_path = unquote(q["open_folder"][0])
                    folder = os.path.dirname(file_path) if os.path.isfile(file_path) else file_path
                    if os.path.exists(folder):
                        subprocess.Popen(f'explorer.exe "{folder}"')
                    return
                elif "clear_downloads" in q:
                    self.downloads_mgr.clear()
                    self.load_downloads(view)
                    return
                elif "clear_history" in q:
                    self.history_mgr.clear_history()
                    self.load_history(view)
                    return
                elif "remove_history" in q:
                    u = unquote(q["remove_history"][0])
                    self.history_mgr.remove_history_item(u)
                    self.load_history(view)
                    return
                elif "open_scripts_folder" in q:
                    USERSCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
                    subprocess.Popen(f'explorer.exe "{str(USERSCRIPTS_DIR)}"')
                    return
            except Exception:
                pass
            return

        if view == self.current_view():
            if url_str in ("aegis://start", "about:blank"):
                self.url_bar.setText("")
                self.url_bar.setPlaceholderText("Buscar en la web o ingresar dirección...")
            else:
                self.url_bar.setText(url_str)

    def on_load_progress(self, progress: int):
        if progress < 100:
            self.progress_bar.show()
            self.progress_bar.setValue(progress)
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

        if ok and current_url not in ("aegis://start", "about:blank") and not current_url.startswith("aegis://"):
            # Registrar visita en historial real para Sitios Frecuentes
            self.history_mgr.record_visit(current_url, view.title())

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

            # Inyección de defusers de video y temporizadores
            js = SHIELDS_CORE.get_injected_scripts(current_url)
            if js:
                view.page().runJavaScript(js)

    def on_shield_block(self):
        self.shield_btn.setText(f" {SHIELDS_CORE.total_blocked}")
        if hasattr(self, "shields_popup") and self.shields_popup.isVisible():
            self.shields_popup.lbl_count.setText(str(SHIELDS_CORE.total_blocked))

# ── 12. Plantilla HTML de Nueva Pestaña (Sitios Frecuentes Reales) ────────────
def get_clean_ntp_html(theme_class: str = "theme-dark", frequent_sites: list = None) -> str:
    if frequent_sites is None:
        frequent_sites = []

    cards_html = ""
    for site in frequent_sites:
        dom = site.get("domain", "")
        title = site.get("title", dom)
        url = site.get("url", "#")
        initial = (dom[0] if dom else "A").upper()
        # Favicon: 1) Favicon local en caché (base64) 2) CDN oficial de favicons de Google
        fav_src = site.get("favicon") or f"https://www.google.com/s2/favicons?domain={dom}&sz=64"

        cards_html += f"""
        <div class="shortcut-wrapper">
          <a href="{url}" class="shortcut-card">
            <div class="shortcut-icon-box">
              <img src="{fav_src}" class="shortcut-img" alt="{title}" onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';" />
              <span class="shortcut-avatar" style="display:none;">{initial}</span>
            </div>
            <span class="shortcut-title">{title}</span>
          </a>
          <button class="btn-remove-shortcut" onclick="removeShortcut('{dom}')" title="Eliminar de frecuentes">×</button>
        </div>
        """

    # Botón Añadir Atajo (+)
    cards_html += """
    <div class="shortcut-wrapper">
      <button class="shortcut-card shortcut-add" onclick="openAddModal()" title="Añadir sitio frecuente">
        <div class="shortcut-icon-box">
          <span class="shortcut-avatar">+</span>
        </div>
        <span class="shortcut-title">Añadir</span>
      </button>
    </div>
    """

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
      max-width: 680px;
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

    .shortcuts-section-title {{
      font-size: 0.85rem;
      font-weight: 600;
      color: var(--text);
      opacity: 0.6;
      margin-bottom: 1rem;
      letter-spacing: 0.5px;
      text-transform: uppercase;
    }}

    .shortcuts-grid {{
      display: flex;
      gap: 1.25rem;
      justify-content: center;
      flex-wrap: wrap;
      margin-bottom: 2rem;
    }}

    .shortcut-wrapper {{
      position: relative;
    }}

    .shortcut-card {{
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 9px;
      text-decoration: none;
      color: var(--text);
      font-size: 0.8rem;
      font-weight: 500;
      padding: 12px 14px;
      border-radius: 14px;
      background: var(--surface);
      border: 1px solid rgba(128, 128, 128, 0.14);
      transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
      min-width: 86px;
      max-width: 92px;
      cursor: pointer;
    }}
    .shortcut-card:hover {{
      border-color: var(--accent);
      transform: translateY(-2px);
    }}

    .shortcut-icon-box {{
      width: 46px;
      height: 46px;
      border-radius: 50%;
      background: var(--bg);
      border: 1px solid rgba(128, 128, 128, 0.16);
      display: flex;
      align-items: center;
      justify-content: center;
      overflow: hidden;
      transition: all 0.2s ease;
    }}
    .shortcut-card:hover .shortcut-icon-box {{
      border-color: var(--accent);
    }}

    .shortcut-img {{
      width: 26px;
      height: 26px;
      object-fit: contain;
      border-radius: 4px;
    }}

    .shortcut-avatar {{
      width: 100%;
      height: 100%;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 1.25rem;
      font-weight: 700;
      color: var(--accent);
      text-transform: uppercase;
    }}

    .shortcut-add {{
      background: transparent;
      border: 1px dashed rgba(128, 128, 128, 0.25);
    }}
    .shortcut-add:hover {{
      background: var(--surface);
      border-style: solid;
      border-color: var(--accent);
    }}
    .shortcut-add .shortcut-avatar {{
      font-size: 1.4rem;
      color: rgba(128, 128, 128, 0.6);
    }}
    .shortcut-add:hover .shortcut-avatar {{
      color: var(--accent);
    }}

    .shortcut-title {{
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      max-width: 72px;
      line-height: 1.2;
    }}

    .btn-remove-shortcut {{
      position: absolute;
      top: -4px;
      right: -4px;
      width: 20px;
      height: 20px;
      border-radius: 50%;
      background: var(--bg);
      border: 1px solid rgba(128, 128, 128, 0.3);
      color: var(--text);
      font-size: 13px;
      line-height: 1;
      display: none;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      z-index: 10;
    }}
    .shortcut-wrapper:hover .btn-remove-shortcut {{
      display: flex;
    }}
    .btn-remove-shortcut:hover {{
      background: var(--accent);
      color: #ffffff;
      border-color: var(--accent);
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

    /* Modal Añadir Sitio */
    .modal-backdrop {{
      position: fixed;
      top: 0; left: 0; right: 0; bottom: 0;
      background: rgba(0, 0, 0, 0.6);
      display: flex;
      align-items: center;
      justify-content: center;
      z-index: 100;
    }}
    .modal-card {{
      background: var(--surface);
      border: 1px solid var(--accent);
      border-radius: 14px;
      padding: 24px;
      width: 320px;
      box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
    }}
    .modal-title {{
      font-size: 15px;
      font-weight: 700;
      margin-bottom: 16px;
      color: var(--text);
    }}
    .modal-input {{
      width: 100%;
      background: var(--bg);
      border: 1px solid rgba(128, 128, 128, 0.25);
      border-radius: 8px;
      padding: 8px 12px;
      color: var(--text);
      font-size: 13px;
      margin-bottom: 12px;
      outline: none;
    }}
    .modal-input:focus {{
      border-color: var(--accent);
    }}
    .modal-actions {{
      display: flex;
      justify-content: flex-end;
      gap: 8px;
      margin-top: 6px;
    }}
    .modal-btn {{
      padding: 6px 14px;
      border-radius: 6px;
      font-size: 12px;
      font-weight: 600;
      cursor: pointer;
      border: none;
    }}
    .modal-btn-cancel {{
      background: transparent;
      color: var(--text);
    }}
    .modal-btn-save {{
      background: var(--accent);
      color: #ffffff;
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

    <div class="shortcuts-section-title">Sitios Frecuentes</div>
    <div class="shortcuts-grid">
      {cards_html}
    </div>
  </main>

  <div class="footer-badge">
    <div class="shield-dot"></div>
    <span>Aegis Shields Activo · adblock-rust FFI · Cero Telemetría</span>
  </div>

  <!-- Modal Interactivo Añadir Sitio Frecuente -->
  <div id="addModal" class="modal-backdrop" style="display: none;">
    <div class="modal-card">
      <div class="modal-title">Añadir sitio frecuente</div>
      <input type="text" id="siteName" class="modal-input" placeholder="Nombre (ej. GitHub)" />
      <input type="text" id="siteUrl" class="modal-input" placeholder="URL (ej. https://github.com)" />
      <div class="modal-actions">
        <button class="modal-btn modal-btn-cancel" onclick="closeAddModal()">Cancelar</button>
        <button class="modal-btn modal-btn-save" onclick="saveShortcut()">Guardar</button>
      </div>
    </div>
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

    function removeShortcut(domain) {{
      window.location.href = 'aegis://action?remove=' + encodeURIComponent(domain);
    }}

    function openAddModal() {{
      document.getElementById('addModal').style.display = 'flex';
      document.getElementById('siteName').focus();
    }}

    function closeAddModal() {{
      document.getElementById('addModal').style.display = 'none';
      document.getElementById('siteName').value = '';
      document.getElementById('siteUrl').value = '';
    }}

    function saveShortcut() {{
      const name = document.getElementById('siteName').value.trim();
      const url = document.getElementById('siteUrl').value.trim();
      if (!url) return;
      const payload = JSON.stringify({{title: name || url, url: url}});
      window.location.href = 'aegis://action?add=' + encodeURIComponent(payload);
    }}
  </script>
</body>
</html>
"""

# ── 12.1 Helper de Formato de Bytes ───────────────────────────────────────────
def format_bytes(b: int) -> str:
    if not b or b < 1024:
        return f"{b or 0} B"
    elif b < 1024 * 1024:
        return f"{b / 1024:.1f} KB"
    else:
        return f"{b / (1024 * 1024):.1f} MB"

# ── 12.2 Plantilla HTML de Configuración (aegis://settings) ───────────────────
def get_settings_html(theme_class: str = "theme-dark", config: dict = None) -> str:
    if config is None:
        config = {}
    tab_h = "selected" if config.get("tab_position", "horizontal") == "horizontal" else ""
    tab_v = "selected" if config.get("tab_position") == "vertical" else ""
    th_dark = "selected" if config.get("theme", "Oscuro") == "Oscuro" else ""
    th_light = "selected" if config.get("theme") == "Claro" else ""
    eng_ddg = "selected" if config.get("search_engine", "DuckDuckGo") == "DuckDuckGo" else ""
    eng_google = "selected" if config.get("search_engine") == "Google" else ""
    eng_bing = "selected" if config.get("search_engine") == "Bing" else ""
    sh_on = "selected" if config.get("shields_enabled", True) else ""
    sh_off = "" if config.get("shields_enabled", True) else "selected"

    return f"""<!DOCTYPE html>
<html lang="es" class="{theme_class}">
<head>
  <meta charset="UTF-8">
  <title>Configuración - Aegis</title>
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
      padding: 3rem 1.5rem;
      display: flex;
      justify-content: center;
    }}
    .container {{
      width: 100%;
      max-width: 680px;
    }}
    .header {{
      display: flex;
      align-items: center;
      gap: 12px;
      margin-bottom: 2rem;
      padding-bottom: 1rem;
      border-bottom: 1px solid rgba(128, 128, 128, 0.15);
    }}
    .title {{
      font-size: 1.5rem;
      font-weight: 700;
    }}
    .card {{
      background: var(--surface);
      border: 1px solid rgba(128, 128, 128, 0.14);
      border-radius: 12px;
      padding: 20px;
      margin-bottom: 1.5rem;
    }}
    .card-title {{
      font-size: 1rem;
      font-weight: 600;
      margin-bottom: 14px;
      color: var(--text);
    }}
    .setting-row {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 12px 0;
      border-bottom: 1px solid rgba(128, 128, 128, 0.08);
    }}
    .setting-row:last-child {{
      border-bottom: none;
      padding-bottom: 0;
    }}
    .setting-info {{
      display: flex;
      flex-direction: column;
      gap: 4px;
    }}
    .setting-name {{
      font-size: 0.9rem;
      font-weight: 500;
    }}
    .setting-desc {{
      font-size: 0.8rem;
      opacity: 0.65;
    }}
    select, button.action-btn {{
      background: var(--bg);
      color: var(--text);
      border: 1px solid rgba(128, 128, 128, 0.25);
      border-radius: 6px;
      padding: 6px 12px;
      font-size: 0.85rem;
      font-weight: 500;
      cursor: pointer;
      outline: none;
    }}
    select:focus, button.action-btn:hover {{
      border-color: var(--accent);
    }}
    button.btn-danger {{
      background: transparent;
      color: #ff6b6b;
      border-color: rgba(255, 107, 107, 0.4);
    }}
    button.btn-danger:hover {{
      background: #ff6b6b;
      color: #ffffff;
    }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="var(--accent)" stroke-width="2.2">
        <circle cx="12" cy="12" r="3"/>
        <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/>
      </svg>
      <h1 class="title">Configuración</h1>
    </div>

    <!-- 1. Apariencia -->
    <div class="card">
      <h2 class="card-title">Diseño y Pestañas</h2>
      <div class="setting-row">
        <div class="setting-info">
          <span class="setting-name">Orientación de pestañas</span>
          <span class="setting-desc">Elige entre la barra horizontal tradicional o el panel vertical lateral</span>
        </div>
        <select onchange="updateSetting('tab_position', this.value)">
          <option value="horizontal" {tab_h}>Horizontal clásica (arriba)</option>
          <option value="vertical" {tab_v}>Vertical lateral (estilo Arc / Zen)</option>
        </select>
      </div>
      <div class="setting-row">
        <div class="setting-info">
          <span class="setting-name">Tema de interfaz</span>
          <span class="setting-desc">Paleta estricta de 4 colores de alto contraste</span>
        </div>
        <select onchange="updateSetting('theme', this.value)">
          <option value="Oscuro" {th_dark}>Oscuro</option>
          <option value="Claro" {th_light}>Claro</option>
        </select>
      </div>
    </div>

    <!-- 2. Búsqueda -->
    <div class="card">
      <h2 class="card-title">Motor de Búsqueda</h2>
      <div class="setting-row">
        <div class="setting-info">
          <span class="setting-name">Buscador predeterminado</span>
          <span class="setting-desc">Utilizado al escribir directamente en el Omnibox</span>
        </div>
        <select onchange="updateSetting('search_engine', this.value)">
          <option value="DuckDuckGo" {eng_ddg}>DuckDuckGo (Privado, sin rastreo)</option>
          <option value="Google" {eng_google}>Google</option>
          <option value="Bing" {eng_bing}>Bing</option>
        </select>
      </div>
    </div>

    <!-- 3. Privacidad y Escudos -->
    <div class="card">
      <h2 class="card-title">Escudos y Rendimiento</h2>
      <div class="setting-row">
        <div class="setting-info">
          <span class="setting-name">Aegis Shields</span>
          <span class="setting-desc">Bloqueo de socket a nivel de red Rust FFI</span>
        </div>
        <select onchange="updateSetting('shields_enabled', this.value === 'true')">
          <option value="true" {sh_on}>Activado (Recomendado)</option>
          <option value="false" {sh_off}>Desactivado</option>
        </select>
      </div>
      <div class="setting-row">
        <div class="setting-info">
          <span class="setting-name">Compactación silenciosa de RAM</span>
          <span class="setting-desc">NT kernel WorkingSet compaction cada 90s (cero placebo)</span>
        </div>
        <span style="font-size: 0.85rem; color: var(--accent); font-weight: 600;">100% Automático</span>
      </div>
    </div>

    <!-- 4. Datos -->
    <div class="card">
      <h2 class="card-title">Datos de Navegación</h2>
      <div class="setting-row">
        <div class="setting-info">
          <span class="setting-name">Historial y sitios frecuentes</span>
          <span class="setting-desc">Borrar todas las visitas guardadas en este equipo</span>
        </div>
        <button class="action-btn btn-danger" onclick="clearHistory()">Borrar Historial</button>
      </div>
    </div>
  </div>

  <script>
    function updateSetting(key, val) {{
      const payload = JSON.stringify({{key: key, value: val}});
      window.location.href = 'aegis://action?set_config=' + encodeURIComponent(payload);
    }}
    function clearHistory() {{
      if (confirm('¿Deseas borrar todo el historial de navegación?')) {{
        window.location.href = 'aegis://action?clear_history=1';
      }}
    }}
  </script>
</body>
</html>
"""

# ── 12.3 Plantilla HTML de Descargas (aegis://downloads) ──────────────────────
def get_downloads_html(theme_class: str = "theme-dark", downloads: list = None) -> str:
    if downloads is None:
        downloads = []

    items_html = ""
    if not downloads:
        items_html = """
        <div style="text-align: center; padding: 4rem 1rem; opacity: 0.6;">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" style="margin-bottom: 1rem;">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
            <polyline points="7 10 12 15 17 10"/>
            <line x1="12" y1="15" x2="12" y2="3"/>
          </svg>
          <p style="font-size: 1rem;">No hay descargas recientes</p>
        </div>
        """
    else:
        for d in downloads:
            fname = d.get("filename", "archivo")
            fpath = d.get("path", "")
            size_str = format_bytes(d.get("total_bytes", 0))
            state = d.get("state", "completed")
            state_label = "Descargando..." if state == "downloading" else "Completado"
            state_color = "var(--accent)" if state == "downloading" else "#2ea043"

            items_html += f"""
            <div class="download-item">
              <div class="dl-icon">📦</div>
              <div class="dl-info">
                <span class="dl-name">{fname}</span>
                <span class="dl-sub">{size_str} • <span style="color: {state_color}; font-weight: 600;">{state_label}</span></span>
              </div>
              <div class="dl-actions">
                <button class="action-btn" onclick="openFile('{fpath}')">Abrir</button>
                <button class="action-btn" onclick="openFolder('{fpath}')">Mostrar en carpeta</button>
              </div>
            </div>
            """

    clear_btn = '<button class="action-btn" onclick="clearDownloads()">Limpiar historial</button>' if downloads else ''

    return f"""<!DOCTYPE html>
<html lang="es" class="{theme_class}">
<head>
  <meta charset="UTF-8">
  <title>Descargas - Aegis</title>
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
      padding: 3rem 1.5rem;
      display: flex;
      justify-content: center;
    }}
    .container {{
      width: 100%;
      max-width: 680px;
    }}
    .header {{
      display: flex;
      align-items: center;
      gap: 12px;
      margin-bottom: 2rem;
      padding-bottom: 1rem;
      border-bottom: 1px solid rgba(128, 128, 128, 0.15);
    }}
    .title {{
      font-size: 1.5rem;
      font-weight: 700;
    }}
    .download-item {{
      background: var(--surface);
      border: 1px solid rgba(128, 128, 128, 0.14);
      border-radius: 10px;
      padding: 14px 16px;
      margin-bottom: 10px;
      display: flex;
      align-items: center;
      gap: 14px;
    }}
    .dl-icon {{
      font-size: 1.5rem;
    }}
    .dl-info {{
      display: flex;
      flex-direction: column;
      gap: 4px;
      flex: 1;
      overflow: hidden;
    }}
    .dl-name {{
      font-size: 0.9rem;
      font-weight: 600;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }}
    .dl-sub {{
      font-size: 0.8rem;
      opacity: 0.7;
    }}
    .dl-actions {{
      display: flex;
      gap: 8px;
    }}
    button.action-btn {{
      background: var(--bg);
      color: var(--text);
      border: 1px solid rgba(128, 128, 128, 0.25);
      border-radius: 6px;
      padding: 6px 12px;
      font-size: 0.8rem;
      font-weight: 500;
      cursor: pointer;
      outline: none;
    }}
    button.action-btn:hover {{
      border-color: var(--accent);
      color: var(--accent);
    }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="var(--accent)" stroke-width="2.2">
        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
        <polyline points="7 10 12 15 17 10"/>
        <line x1="12" y1="15" x2="12" y2="3"/>
      </svg>
      <h1 class="title">Descargas</h1>
      <div style="flex: 1;"></div>
      {clear_btn}
    </div>

    {items_html}
  </div>

  <script>
    function openFile(p) {{
      window.location.href = 'aegis://action?open_file=' + encodeURIComponent(p);
    }}
    function openFolder(p) {{
      window.location.href = 'aegis://action?open_folder=' + encodeURIComponent(p);
    }}
    function clearDownloads() {{
      window.location.href = 'aegis://action?clear_downloads=1';
    }}
  </script>
</body>
</html>
"""

# ── 12.4 Plantilla HTML de Historial (aegis://history) ────────────────────────
def get_history_html(theme_class: str = "theme-dark", history_items: list = None) -> str:
    if history_items is None:
        history_items = []

    items_html = ""
    if not history_items:
        items_html = """
        <div style="text-align: center; padding: 4rem 1rem; opacity: 0.6;">
          <p style="font-size: 1rem;">No hay páginas en el historial</p>
        </div>
        """
    else:
        for h in history_items:
            title = h.get("title") or h.get("domain", "Página")
            url = h.get("url", "#")
            dom = h.get("domain", "")
            t_str = time.strftime("%H:%M", time.localtime(h.get("time", time.time())))

            items_html += f"""
            <div class="history-item" data-search="{title.lower()} {dom.lower()}">
              <span class="hist-time">{t_str}</span>
              <div class="hist-info">
                <a href="{url}" class="hist-title">{title}</a>
                <span class="hist-domain">{dom}</span>
              </div>
              <button class="btn-remove" onclick="removeHistory('{url}')" title="Eliminar de historial">×</button>
            </div>
            """

    clear_btn = '<button class="action-btn btn-danger" onclick="clearAllHistory()">Borrar todo el historial</button>' if history_items else ''

    return f"""<!DOCTYPE html>
<html lang="es" class="{theme_class}">
<head>
  <meta charset="UTF-8">
  <title>Historial - Aegis</title>
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
      padding: 3rem 1.5rem;
      display: flex;
      justify-content: center;
    }}
    .container {{
      width: 100%;
      max-width: 680px;
    }}
    .header {{
      display: flex;
      align-items: center;
      gap: 12px;
      margin-bottom: 1.5rem;
      padding-bottom: 1rem;
      border-bottom: 1px solid rgba(128, 128, 128, 0.15);
    }}
    .title {{
      font-size: 1.5rem;
      font-weight: 700;
    }}
    .search-box {{
      width: 100%;
      background: var(--surface);
      border: 1px solid rgba(128, 128, 128, 0.2);
      border-radius: 8px;
      padding: 10px 14px;
      color: var(--text);
      font-size: 0.9rem;
      outline: none;
      margin-bottom: 1.5rem;
    }}
    .search-box:focus {{
      border-color: var(--accent);
    }}
    .history-item {{
      background: var(--surface);
      border: 1px solid rgba(128, 128, 128, 0.12);
      border-radius: 8px;
      padding: 12px 14px;
      margin-bottom: 8px;
      display: flex;
      align-items: center;
      gap: 12px;
    }}
    .hist-time {{
      font-size: 0.8rem;
      opacity: 0.55;
      font-variant-numeric: tabular-nums;
      min-width: 42px;
    }}
    .hist-info {{
      display: flex;
      flex-direction: column;
      gap: 2px;
      flex: 1;
      overflow: hidden;
    }}
    .hist-title {{
      color: var(--text);
      text-decoration: none;
      font-size: 0.9rem;
      font-weight: 500;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }}
    .hist-title:hover {{
      color: var(--accent);
    }}
    .hist-domain {{
      font-size: 0.75rem;
      opacity: 0.6;
    }}
    .btn-remove {{
      background: transparent;
      border: none;
      color: var(--text);
      font-size: 16px;
      cursor: pointer;
      opacity: 0.5;
      padding: 4px;
    }}
    .btn-remove:hover {{
      opacity: 1;
      color: #ff6b6b;
    }}
    button.action-btn {{
      background: var(--bg);
      color: var(--text);
      border: 1px solid rgba(128, 128, 128, 0.25);
      border-radius: 6px;
      padding: 6px 12px;
      font-size: 0.8rem;
      font-weight: 500;
      cursor: pointer;
    }}
    button.btn-danger:hover {{
      background: #ff6b6b;
      color: #ffffff;
      border-color: #ff6b6b;
    }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="var(--accent)" stroke-width="2.2">
        <circle cx="12" cy="12" r="10"/>
        <polyline points="12 6 12 12 14 14"/>
      </svg>
      <h1 class="title">Historial</h1>
      <div style="flex: 1;"></div>
      {clear_btn}
    </div>

    <input type="text" id="searchBox" class="search-box" placeholder="Buscar en el historial..." oninput="filterHistory()" />

    <div id="histList">
      {items_html}
    </div>
  </div>

  <script>
    function filterHistory() {{
      const q = document.getElementById('searchBox').value.toLowerCase();
      const items = document.querySelectorAll('.history-item');
      items.forEach(el => {{
        const txt = el.getAttribute('data-search') || '';
        el.style.display = txt.includes(q) ? 'flex' : 'none';
      }});
    }}
    function removeHistory(u) {{
      window.location.href = 'aegis://action?remove_history=' + encodeURIComponent(u);
    }}
    function clearAllHistory() {{
      if (confirm('¿Deseas vaciar todo el historial?')) {{
        window.location.href = 'aegis://action?clear_history=1';
      }}
    }}
  </script>
</body>
</html>
"""

# ── 12.5 Plantilla HTML de Extensiones (aegis://extensions) ───────────────────
def get_extensions_html(theme_class: str = "theme-dark", scripts: list = None) -> str:
    if scripts is None:
        scripts = []

    scripts_html = ""
    if not scripts:
        scripts_html = """
        <div style="padding: 12px; opacity: 0.65; font-size: 0.85rem;">
          No hay scripts de usuario (.user.js) instalados en la carpeta.
        </div>
        """
    else:
        for s in scripts:
            scripts_html += f"""
            <div class="ext-item">
              <span class="ext-icon">📄</span>
              <div class="ext-info">
                <span class="ext-name">{s}</span>
                <span class="ext-sub">Script de usuario activo</span>
              </div>
              <span style="font-size: 0.8rem; color: #2ea043; font-weight: 600;">Inyectado</span>
            </div>
            """

    return f"""<!DOCTYPE html>
<html lang="es" class="{theme_class}">
<head>
  <meta charset="UTF-8">
  <title>Extensiones - Aegis</title>
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
      padding: 3rem 1.5rem;
      display: flex;
      justify-content: center;
    }}
    .container {{
      width: 100%;
      max-width: 680px;
    }}
    .header {{
      display: flex;
      align-items: center;
      gap: 12px;
      margin-bottom: 2rem;
      padding-bottom: 1rem;
      border-bottom: 1px solid rgba(128, 128, 128, 0.15);
    }}
    .title {{
      font-size: 1.5rem;
      font-weight: 700;
    }}
    .card {{
      background: var(--surface);
      border: 1px solid rgba(128, 128, 128, 0.14);
      border-radius: 12px;
      padding: 20px;
      margin-bottom: 1.5rem;
    }}
    .card-title {{
      font-size: 1rem;
      font-weight: 600;
      margin-bottom: 14px;
      color: var(--text);
    }}
    .ext-item {{
      background: var(--bg);
      border: 1px solid rgba(128, 128, 128, 0.12);
      border-radius: 8px;
      padding: 12px 14px;
      margin-bottom: 8px;
      display: flex;
      align-items: center;
      gap: 12px;
    }}
    .ext-icon {{
      font-size: 1.4rem;
    }}
    .ext-info {{
      display: flex;
      flex-direction: column;
      gap: 3px;
      flex: 1;
    }}
    .ext-name {{
      font-size: 0.9rem;
      font-weight: 600;
    }}
    .ext-sub {{
      font-size: 0.8rem;
      opacity: 0.65;
    }}
    button.action-btn {{
      background: var(--bg);
      color: var(--text);
      border: 1px solid rgba(128, 128, 128, 0.25);
      border-radius: 6px;
      padding: 6px 12px;
      font-size: 0.85rem;
      font-weight: 500;
      cursor: pointer;
      outline: none;
    }}
    button.action-btn:hover {{
      border-color: var(--accent);
      color: var(--accent);
    }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="var(--accent)" stroke-width="2.2">
        <path d="M12 2v4m0 12v4M4.93 4.93l2.83 2.83m8.48 8.48l2.83 2.83M2 12h4m12 0h4M4.93 19.07l2.83-2.83m8.48-8.48l2.83-2.83"/>
      </svg>
      <h1 class="title">Extensiones y Módulos</h1>
    </div>

    <!-- Módulos de Aegis Nativos -->
    <div class="card">
      <h2 class="card-title">Motores Nativos de Aegis Shields (Activos)</h2>
      <div class="ext-item">
        <span class="ext-icon">🛡️</span>
        <div class="ext-info">
          <span class="ext-name">Aegis Shields Rust Core</span>
          <span class="ext-sub">Bloqueo de red socket Rust FFI con reglas EasyList y uBlock</span>
        </div>
        <span style="font-size: 0.8rem; color: #2ea043; font-weight: 600;">Activo</span>
      </div>
      <div class="ext-item">
        <span class="ext-icon">⚡</span>
        <div class="ext-info">
          <span class="ext-name">Aegis Video & Countdown Defuser</span>
          <span class="ext-sub">Bypass de anuncios en video, muros anti-adblock y acortadores</span>
        </div>
        <span style="font-size: 0.8rem; color: #2ea043; font-weight: 600;">Activo</span>
      </div>
      <div class="ext-item">
        <span class="ext-icon">🎨</span>
        <div class="ext-info">
          <span class="ext-name">Aegis Cosmetic Engine</span>
          <span class="ext-sub">Filtrado cosmético CSS inmediato inyectado en páginas</span>
        </div>
        <span style="font-size: 0.8rem; color: #2ea043; font-weight: 600;">Activo</span>
      </div>
    </div>

    <!-- Scripts de usuario -->
    <div class="card">
      <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px;">
        <h2 class="card-title" style="margin-bottom: 0;">Scripts de Usuario (UserScripts)</h2>
        <button class="action-btn" onclick="openScriptsFolder()">📂 Abrir carpeta de scripts</button>
      </div>
      <p style="font-size: 0.8rem; opacity: 0.7; margin-bottom: 14px;">
        Coloca tus scripts <code>.js</code> o <code>.user.js</code> en la carpeta de scripts para inyectarlos automáticamente en todas las páginas web.
      </p>
      {scripts_html}
    </div>
  </div>

  <script>
    function openScriptsFolder() {{
      window.location.href = 'aegis://action?open_scripts_folder=1';
    }}
  </script>
</body>
</html>
"""

# ── 13. Punto de Entrada Principal ────────────────────────────────────────────
def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Aegis")
    app.setApplicationVersion("1.3.4")

    window = AegisBrowserWindow()
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
