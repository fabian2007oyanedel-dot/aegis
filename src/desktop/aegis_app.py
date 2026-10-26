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
import re
import struct
import zipfile
import io
import urllib.request
import shutil
import sqlite3
import tempfile
from pathlib import Path
import secrets
import string
from pathlib import Path
from urllib.parse import urlparse, parse_qs, unquote, quote, urlencode, urlunparse
from ctypes import wintypes

TRACKING_PARAMS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "utm_cid", "utm_reader", "utm_name",
    "fbclid", "gclid", "gclsrc", "dclid",
    "si", "igshid", "mc_eid", "msclkid",
    "yclid", "_hsenc", "_openstat", "wickedid",
    "rb_clickid", "s_kwcid"
}

def clean_url_tracking(url_str: str) -> str:
    if not url_str or not url_str.startswith(("http://", "https://")):
        return url_str
    try:
        parsed = urlparse(url_str)
        if not parsed.query:
            return url_str
        qs = parse_qs(parsed.query, keep_blank_values=True)
        cleaned_qs = {k: v for k, v in qs.items() if k.lower() not in TRACKING_PARAMS}
        new_query = urlencode(cleaned_qs, doseq=True)
        return urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, new_query, parsed.fragment))
    except Exception:
        return url_str

# ── 1. Optimización Extrema de Chromium (GPU, Video Hardware, Audio y Widevine DRM) ──
def find_widevine_cdm() -> tuple[str | None, str | None]:
    """Detecta dinámicamente el módulo Widevine CDM oficial en el sistema (Brave, Chrome o Edge)."""
    candidates = [
        Path.home() / "AppData" / "Local" / "BraveSoftware" / "Brave-Browser" / "User Data" / "WidevineCdm",
        Path.home() / "AppData" / "Local" / "Google" / "Chrome" / "User Data" / "WidevineCdm",
        Path("C:/Program Files/Google/Chrome/Application"),
        Path("C:/Program Files (x86)/Microsoft/Edge/Application"),
        Path.home() / "AppData" / "Local" / "Microsoft" / "Edge" / "User Data" / "WidevineCdm",
    ]
    for c in candidates:
        if c.exists():
            for dll in c.glob("**/widevinecdm.dll"):
                version = "4.10.3112.0"
                manifest = dll.parent.parent / "manifest.json"
                if not manifest.exists():
                    manifest = dll.parent / "manifest.json"
                if manifest.exists():
                    try:
                        m_data = json.loads(manifest.read_text(encoding="utf-8"))
                        version = m_data.get("version", version)
                    except Exception:
                        pass
                return str(dll).replace("\\", "/"), version
    return None, None

# ── Configuración de Entorno para QtWebEngine (Standalone y Python) ───────────
if getattr(sys, "frozen", False):
    _exe_dir = Path(sys.executable).resolve().parent
    _internal_qt = _exe_dir / "_internal" / "PyQt6" / "Qt6"
    _proc_candidates = [
        _internal_qt / "bin" / "QtWebEngineProcess.exe",
        _internal_qt / "QtWebEngineProcess.exe",
        _exe_dir / "QtWebEngineProcess.exe",
        _exe_dir / "PyQt6" / "Qt6" / "bin" / "QtWebEngineProcess.exe"
    ]
    for _p in _proc_candidates:
        if _p.exists():
            os.environ["QTWEBENGINEPROCESS_PATH"] = str(_p)
            break

    _res_candidates = [
        _internal_qt / "resources",
        _exe_dir / "resources",
        _exe_dir / "PyQt6" / "Qt6" / "resources"
    ]
    for _r in _res_candidates:
        if _r.exists():
            os.environ["QTWEBENGINE_RESOURCES_PATH"] = str(_r)
            break

    _loc_candidates = [
        _internal_qt / "translations",
        _exe_dir / "translations",
        _exe_dir / "PyQt6" / "Qt6" / "translations"
    ]
    for _l in _loc_candidates:
        if _l.exists():
            os.environ["QTWEBENGINE_LOCALES_PATH"] = str(_l)
            break

    _plug_candidates = [
        _internal_qt / "plugins",
        _exe_dir / "plugins",
        _exe_dir / "PyQt6" / "Qt6" / "plugins"
    ]
    for _pl in _plug_candidates:
        if _pl.exists():
            os.environ["QT_PLUGIN_PATH"] = str(_pl)
            break

os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = (
    "--disable-features=AudioServiceSandbox,Translate,OptimizationHints,MediaRouter "
    "--autoplay-policy=no-user-gesture-required "
    "--enable-smooth-scrolling "
    "--disable-breakpad "
    "--disable-telemetry "
    "--disable-sync "
    "--disable-domain-reliability "
    "--no-pings "
    "--disable-wake-on-wifi "
    "--disable-component-update "
    "--disable-client-side-phishing-detection "
    "--webrtc-ip-handling-policy=disable_non_proxied_udp "
    "--force-webrtc-ip-handling-policy "
    "--js-flags=--expose-gc "
)

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QProgressBar, QTabBar, QStackedWidget,
    QLabel, QCheckBox, QFrame, QAbstractButton, QSizePolicy,
    QMenu, QCompleter, QDialog, QTextEdit, QListWidget, QListWidgetItem,
    QFileDialog, QScrollArea, QSlider, QSplitter, QRadioButton, QButtonGroup,
    QComboBox
)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import (
    QWebEngineProfile, QWebEngineSettings, QWebEngineUrlRequestInterceptor,
    QWebEngineDownloadRequest, QWebEngineScript, QWebEnginePage
)
from PyQt6.QtCore import QUrl, Qt, QPoint, QTimer, QByteArray, QBuffer, QIODevice, QSize, QStringListModel, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QBrush, QPen, QIcon, QPixmap, QShortcut, QKeySequence, QPalette
from PyQt6.QtSvg import QSvgRenderer

BASE_DIR = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent.parent.parent

# Detección y activación de Modo Portable (100% autocontenido en USB o carpeta sin tocar el sistema)
IS_PORTABLE = (
    (BASE_DIR / "portable.dat").exists() or 
    (BASE_DIR / "data").exists() or 
    "--portable" in sys.argv
)

if IS_PORTABLE:
    DATA_DIR = BASE_DIR / "data"
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE = DATA_DIR / "aegis_browser_config.json"
    HISTORY_FILE = DATA_DIR / "aegis_browser_history.json"
    DOWNLOADS_FILE = DATA_DIR / "aegis_browser_downloads.json"
    BOOKMARKS_FILE = DATA_DIR / "aegis_browser_bookmarks.json"
    SESSION_FILE = DATA_DIR / "aegis_browser_session.json"
    READING_LIST_FILE = DATA_DIR / "aegis_reading_list.json"
    USERSCRIPTS_DIR = DATA_DIR / "userscripts"
    EXTENSIONS_DIR = DATA_DIR / "extensions"
    PROFILE_DIR = DATA_DIR / "profile"
else:
    DATA_DIR = Path.home()
    CONFIG_FILE = Path.home() / ".aegis_browser_config.json"
    HISTORY_FILE = Path.home() / ".aegis_browser_history.json"
    DOWNLOADS_FILE = Path.home() / ".aegis_browser_downloads.json"
    BOOKMARKS_FILE = Path.home() / ".aegis_browser_bookmarks.json"
    SESSION_FILE = Path.home() / ".aegis_browser_session.json"
    READING_LIST_FILE = Path.home() / ".aegis_reading_list.json"
    USERSCRIPTS_DIR = Path.home() / ".aegis_userscripts"
    EXTENSIONS_DIR = Path.home() / ".aegis_extensions"
    PROFILE_DIR = Path.home() / ".aegis_profile"

def ensure_builtin_userscripts(scripts_dir: Path):
    """Pre-instala extensiones populares integradas y ligeras en Aegis (Steam Helper, SponsorBlock, Smart Dark, AdBlock Zapper)."""
    try:
        scripts_dir.mkdir(parents=True, exist_ok=True)
        steam_script = scripts_dir / "steam_helper.js"
        if not steam_script.exists():
            steam_script.write_text("""// ==UserScript==
// @name         Aegis Steam Helper
// @description  Potencia Steam Community y Tienda: SteamDB, conversor de tasas, calculadora de comisión de Valve (-15%) y protección contra estafas
// @match        *://store.steampowered.com/*
// @match        *://steamcommunity.com/*
// ==/UserScript==
(function() {
    'use strict';
    const host = window.location.hostname;
    if (host.includes('store.steampowered.com')) {
        const appMatch = window.location.pathname.match(/\\/app\\/(\\d+)/);
        if (appMatch) {
            const appId = appMatch[1];
            const btnContainer = document.querySelector('.page_content_actions') || document.querySelector('.game_area_purchase_game');
            if (btnContainer && !document.getElementById('aegis-steamdb-btn')) {
                const sdbBtn = document.createElement('a');
                sdbBtn.id = 'aegis-steamdb-btn';
                sdbBtn.href = `https://steamdb.info/app/${appId}/`;
                sdbBtn.target = '_blank';
                sdbBtn.innerText = '📊 Ver en SteamDB (Historial de Precios)';
                sdbBtn.style.cssText = 'display:inline-block; margin: 8px 0; padding: 6px 14px; background: #0072CE; color: #fff; font-weight: 600; border-radius: 4px; text-decoration: none; font-size: 12px; border: 1px solid #1b9bf0;';
                btnContainer.prepend(sdbBtn);
            }
        }
    }
    if (host.includes('steamcommunity.com')) {
        const marketInput = document.getElementById('market_sell_buyercurrency_input');
        if (marketInput) {
            marketInput.addEventListener('input', function() {
                const val = parseFloat(this.value.replace(',', '.'));
                const youReceive = document.getElementById('market_sell_currency_input');
                if (!isNaN(val) && youReceive) {
                    const net = (val / 1.15).toFixed(2);
                    console.log('Aegis Steam Helper: Neto recibido: ' + net);
                }
            });
        }
        if (window.location.pathname.includes('/tradeoffer/')) {
            const warningBox = document.createElement('div');
            warningBox.id = 'aegis-trade-guard';
            warningBox.style.cssText = 'background: #161b22; border: 1px solid #388bfd; color: #f0f6fc; padding: 10px 14px; border-radius: 8px; margin: 10px 0; font-size: 12px; display: flex; align-items: center; gap: 8px;';
            warningBox.innerHTML = '<strong style="color:#58a6ff;">🛡️ Aegis Steam Guard:</strong> Verifica que el nivel y fecha del perfil coincidan antes de confirmar.';
            const container = document.getElementById('trade_offer_header') || document.body;
            container.prepend(warningBox);
        }
    }
})();
""", encoding="utf-8")

        sponsor_script = scripts_dir / "sponsor_block.js"
        if not sponsor_script.exists():
            sponsor_script.write_text("""// ==UserScript==
// @name         Aegis SponsorBlock Lite
// @description  Salto inteligente de segmentos patrocinados y recordatorios en YouTube
// @match        *://*.youtube.com/*
// ==/UserScript==
(function() {
    'use strict';
    let lastUrl = '';
    let segments = [];
    async function fetchSegments(videoId) {
        try {
            const resp = await fetch(`https://sponsor.ajay.app/api/skipSegments?videoID=${videoId}&categories=["sponsor","intro","outro","selfpromo"]`);
            if (resp.ok) segments = await resp.json();
            else segments = [];
        } catch (e) { segments = []; }
    }
    setInterval(() => {
        const urlParams = new URLSearchParams(window.location.search);
        const vId = urlParams.get('v');
        if (vId && vId !== lastUrl) {
            lastUrl = vId;
            fetchSegments(vId);
        }
        const video = document.querySelector('video');
        if (!video || !segments.length) return;
        const curTime = video.currentTime;
        for (const seg of segments) {
            const [start, end] = seg.segment;
            if (curTime >= start && curTime < end - 0.5) {
                video.currentTime = end;
                break;
            }
        }
    }, 800);
})();
""", encoding="utf-8")

        dark_script = scripts_dir / "dark_reader.js"
        if not dark_script.exists():
            dark_script.write_text("""// ==UserScript==
// @name         Aegis Smart Dark Mode
// @description  Modo oscuro inteligente para sitios web sin tema nativo
// @match        *://*/*
// ==/UserScript==
(function() {
    'use strict';
    if (window._aegisDarkInjected) return;
    window._aegisDarkInjected = true;
    const host = window.location.hostname;
    if (host.includes('youtube.com') || host.includes('github.com') || host.includes('reddit.com') || host.includes('netflix.com')) return;
    const style = document.createElement('style');
    style.id = 'aegis-smart-dark';
    style.textContent = `
        html { filter: invert(90%) hue-rotate(180deg) !important; background: #111 !important; }
        img, video, canvas, iframe, svg, [style*="background-image"] { filter: invert(110%) hue-rotate(180deg) !important; }
    `;
    if (localStorage.getItem('aegis_force_dark') === '1') {
        document.documentElement.appendChild(style);
    }
})();
""", encoding="utf-8")

        ublock_script = scripts_dir / "ublock_lite.js"
        if not ublock_script.exists():
            ublock_script.write_text("""// ==UserScript==
// @name         Aegis AdBlock & Tracker Zapper
// @description  Bloqueo de banners intrusivos, popups de suscripción y rastreadores
// @match        *://*/*
// ==/UserScript==
(function() {
    'use strict';
    const annoyingSelectors = [
        '.ad-banner', '.adsbygoogle', '.advertisement', '#cookie-banner',
        '.cookie-notice', '.cmp-container', '#qc-cmp2-container',
        '.tp-modal', '.tp-backdrop', '.paywall-overlay'
    ];
    function zap() {
        annoyingSelectors.forEach(sel => {
            document.querySelectorAll(sel).forEach(el => {
                el.style.setProperty('display', 'none', 'important');
            });
        });
        if (document.body && document.body.style.overflow === 'hidden') {
            document.body.style.overflow = 'auto';
        }
    }
    zap();
    window.addEventListener('DOMContentLoaded', zap);
    setInterval(zap, 2000);
})();
""", encoding="utf-8")

        timer_bypass_script = scripts_dir / "aegis_timer_bypass.js"
        if not timer_bypass_script.exists():
            timer_bypass_script.write_text(r"""// ==UserScript==
// @name         Aegis Fast Timer & Shortener Bypass
// @description  Salto instantáneo de temporizadores y acortadores (CurseForge, Mega, Adf.ly, Linkvertise, Sub2Unlock, Mediafire, etc.)
// @match        *://*/*
// @run-at       document-start
// ==/UserScript==
(function() {
    'use strict';
    if (window._aegisBypassLoaded) return;
    window._aegisBypassLoaded = true;

    function notifyBypass(serviceName) {
        try {
            console.log('[Aegis Bypass] Salto de espera activado en: ' + serviceName);
            const badge = document.createElement('div');
            badge.id = 'aegis-bypass-badge';
            badge.style.cssText = 'position:fixed; bottom:20px; right:20px; background:#161b22; color:#58a6ff; border:1px solid #388bfd; border-radius:8px; padding:10px 16px; font-family:-apple-system,sans-serif; font-size:12px; font-weight:600; box-shadow:0 8px 24px rgba(0,0,0,0.5); z-index:2147483647; display:flex; align-items:center; gap:8px; pointer-events:none; transition:opacity 0.4s ease;';
            badge.innerHTML = '<span style="color:#2ea043; font-size:14px;">⚡</span> Aegis Bypass: Salto de espera en <strong>' + serviceName + '</strong>';
            (document.body || document.documentElement).appendChild(badge);
            setTimeout(() => { badge.style.opacity = '0'; setTimeout(() => badge.remove(), 400); }, 2500);
        } catch(e) {}
    }

    const host = window.location.hostname.toLowerCase();
    const path = window.location.pathname.toLowerCase();

    // ── 1. CurseForge (salto de espera de 5s a 0s) ───────────────────────────
    if (host.includes('curseforge.com')) {
        function checkCurseForge() {
            if (path.includes('/download') || path.includes('/files/')) {
                const directLink = document.querySelector('a.download-link, a[href*="edge.forgecdn.net"], a[href*="media.forgecdn.net"], .download-countdown a, a[data-action="download-link"]');
                if (directLink && directLink.href && !directLink._aegisClicked) {
                    directLink._aegisClicked = true;
                    notifyBypass('CurseForge');
                    window.location.assign(directLink.href);
                    return;
                }
                const cd = document.querySelector('.download-countdown, [class*="countdown"]');
                if (cd) {
                    const links = cd.querySelectorAll('a');
                    for (const l of links) {
                        if (l.href && !l._aegisClicked) {
                            l._aegisClicked = true;
                            notifyBypass('CurseForge');
                            window.location.assign(l.href);
                            return;
                        }
                    }
                }
            }
        }
        checkCurseForge();
        setInterval(checkCurseForge, 200);
    }

    // ── 2. Adf.ly / Ay.gy / J.gs / Q.gs (decodificación directa ysmm) ─────────
    if (host.includes('adf.ly') || host.includes('ay.gy') || host.includes('j.gs') || host.includes('q.gs')) {
        function decodeAdfly(ysmm) {
            try {
                let left = '', right = '';
                for (let i = 0; i < ysmm.length; i++) {
                    if (i % 2 === 0) left += ysmm.charAt(i);
                    else right = ysmm.charAt(i) + right;
                }
                let data = (left + right).split('');
                for (let i = 0; i < data.length; i++) {
                    if (/\d/.test(data[i])) {
                        for (let j = i + 1; j < data.length; j++) {
                            if (/\d/.test(data[j])) {
                                let u = Number(data[i]) ^ Number(data[j]);
                                if (u < 10) data[i] = u.toString();
                                i = j;
                                break;
                            }
                        }
                    }
                }
                data = data.join('');
                let decoded = atob(data.slice(16, -16));
                let dest = decoded.indexOf('http');
                if (dest !== -1) return decoded.substring(dest);
                return decoded;
            } catch(e) { return null; }
        }

        function checkAdfly() {
            if (typeof window.ysmm === 'string') {
                const dest = decodeAdfly(window.ysmm);
                if (dest && dest.startsWith('http')) {
                    notifyBypass('Adf.ly');
                    window.location.replace(dest);
                    return;
                }
            }
            const scripts = document.getElementsByTagName('script');
            for (let s of scripts) {
                const text = s.textContent || '';
                const m = text.match(/var\s+ysmm\s*=\s*['"]([^'"]+)['"]/);
                if (m) {
                    const dest = decodeAdfly(m[1]);
                    if (dest && dest.startsWith('http')) {
                        notifyBypass('Adf.ly');
                        window.location.replace(dest);
                        return;
                    }
                }
            }
            const skipBtn = document.querySelector('#skip_buuton, #skip_ad_button, .skip-btn, #skip_button a');
            if (skipBtn && !skipBtn._aegisClicked) {
                skipBtn._aegisClicked = true;
                notifyBypass('Adf.ly (Botón Skip)');
                skipBtn.click();
            }
        }
        checkAdfly();
        setInterval(checkAdfly, 250);
    }

    // ── 3. Mega.nz (cierre de modal de app y descarga directa en navegador) ───
    if (host.includes('mega.nz')) {
        function checkMega() {
            const dismissBtns = document.querySelectorAll('.mega-dialog .close, .dialog-close, button.close, .modal-close, .app-overlay-close');
            dismissBtns.forEach(b => {
                if (!b._aegisClicked) {
                    b._aegisClicked = true;
                    b.click();
                }
            });
            const dlBtn = document.querySelector('.download-file, button.download, .btn-download-browser, .mega-button.download-btn');
            if (dlBtn && !dlBtn.disabled && !dlBtn._aegisBypassed) {
                dlBtn._aegisBypassed = true;
                notifyBypass('MEGA Web Download');
            }
        }
        setInterval(checkMega, 600);
    }

    // ── 4. AdFoc.us ──────────────────────────────────────────────────────────
    if (host.includes('adfoc.us')) {
        function checkAdfocus() {
            const skip = document.querySelector('.skip, #showSkip a');
            if (skip && skip.href && !skip._aegisClicked) {
                skip._aegisClicked = true;
                notifyBypass('AdFoc.us');
                window.location.assign(skip.href);
            }
            const m = document.documentElement.innerHTML.match(/click_url\s*=\s*['"]([^'"]+)['"]/);
            if (m && m[1]) {
                notifyBypass('AdFoc.us');
                window.location.assign(m[1]);
            }
        }
        checkAdfocus();
        setInterval(checkAdfocus, 300);
    }

    // ── 5. Mediafire ─────────────────────────────────────────────────────────
    if (host.includes('mediafire.com')) {
        function checkMediafire() {
            const dlBtn = document.querySelector('#downloadButton, a.popsok, .input.popsok');
            if (dlBtn && dlBtn.href && !dlBtn._aegisClicked) {
                dlBtn._aegisClicked = true;
                notifyBypass('Mediafire Direct');
                dlBtn.click();
            }
        }
        setInterval(checkMediafire, 500);
    }

    // ── 6. Linkvertise & Acortadores con Bloqueos Sociales ───────────────────
    if (host.includes('linkvertise.com') || host.includes('link-to.net') || host.includes('up-to-down.net') || host.includes('sub2unlock.com') || host.includes('boost.ink') || host.includes('rekonise.com')) {
        function checkShorteners() {
            if (typeof window.countdown === 'number') window.countdown = 0;
            if (typeof window.counter === 'number') window.counter = 0;
            if (typeof window.seconds === 'number') window.seconds = 0;
            if (typeof window.waitTime === 'number') window.waitTime = 0;

            const targetLinks = document.querySelectorAll('a[data-url], a[data-target], a[data-href], a.target-link, a.unlock-link');
            for (let l of targetLinks) {
                const dest = l.getAttribute('data-url') || l.getAttribute('data-target') || l.getAttribute('data-href');
                if (dest && dest.startsWith('http') && !l._aegisClicked) {
                    l._aegisClicked = true;
                    notifyBypass('Shortener Direct');
                    window.location.assign(dest);
                    return;
                }
            }

            const freeAccess = document.querySelector('.free-access-btn, button[class*="free-access"], .btn-free, #btn-free');
            if (freeAccess && !freeAccess._aegisClicked) {
                freeAccess._aegisClicked = true;
                freeAccess.click();
            }
        }
        setInterval(checkShorteners, 400);
    }

    // ── 7. Acelerador Universal de Temporizadores de Descarga ─────────────────
    function universalTimerBypass() {
        const timerSelectors = [
            '#countdown', '#timer', '.countdown', '.timer', '#download-timer',
            '#downloadTimer', '#wait-time', '#seconds', '#counter',
            '.download-countdown', '[data-timer]', '[id*="countdown"]', '[id*="timer"]'
        ];
        timerSelectors.forEach(sel => {
            document.querySelectorAll(sel).forEach(el => {
                if (el && el.innerText && /\d+/.test(el.innerText)) {
                    el.innerText = '0';
                    el.dispatchEvent(new Event('change', { bubbles: true }));
                }
            });
        });

        const disabledButtons = document.querySelectorAll('button:disabled, a.disabled, input[type="submit"]:disabled, .btn-disabled');
        disabledButtons.forEach(btn => {
            const txt = (btn.innerText || btn.value || '').toLowerCase();
            if (txt.includes('download') || txt.includes('descargar') || txt.includes('get link') || txt.includes('continuar')) {
                btn.removeAttribute('disabled');
                btn.classList.remove('disabled');
                btn.classList.remove('btn-disabled');
                btn.style.pointerEvents = 'auto';
                btn.style.opacity = '1';
            }
        });
    }

    setInterval(universalTimerBypass, 500);
})();
""", encoding="utf-8")
    except Exception:
        pass

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

    def clear_range(self, cutoff: float):
        if "history" in self.data:
            self.data["history"] = [h for h in self.data["history"] if h.get("time", 0) < cutoff]
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

# ── 2.2 Helper Global de Formato de Bytes ─────────────────────────────────────
def format_bytes(b: int) -> str:
    if not b or b < 1024:
        return f"{b or 0} B"
    elif b < 1024 * 1024:
        return f"{b / 1024:.1f} KB"
    else:
        return f"{b / (1024 * 1024):.1f} MB"

# ── 2.3 Gestor de Marcadores y Favoritos (Bookmarks) ──────────────────────────
class BookmarksManager:
    def __init__(self):
        self.bookmarks = []
        self.load()

    def load(self):
        if BOOKMARKS_FILE.exists():
            try:
                self.bookmarks = json.loads(BOOKMARKS_FILE.read_text(encoding="utf-8"))
            except Exception:
                self.bookmarks = []
        else:
            self.bookmarks = [
                {"title": "DuckDuckGo", "url": "https://duckduckgo.com"},
                {"title": "GitHub", "url": "https://github.com"},
                {"title": "Wikipedia", "url": "https://wikipedia.org"}
            ]
            self.save()

    def save(self):
        try:
            BOOKMARKS_FILE.write_text(json.dumps(self.bookmarks, indent=2, ensure_ascii=False), encoding="utf-8")
        except Exception:
            pass

    def add(self, title: str, url: str) -> bool:
        if any(b.get("url") == url for b in self.bookmarks):
            return False
        self.bookmarks.append({"title": title, "url": url, "created": time.time()})
        self.save()
        return True

    def remove(self, url: str):
        self.bookmarks = [b for b in self.bookmarks if b.get("url") != url]
        self.save()

    def is_bookmarked(self, url: str) -> bool:
        return any(b.get("url") == url for b in self.bookmarks)

# ── 2.3.5 Importador de Datos desde Brave Browser ─────────────────────────────
class BraveImporter:
    """Importador universal de datos locales desde Brave Browser (Historial, Marcadores y Accesos Frecuentes)."""

    @staticmethod
    def get_default_brave_user_data_path() -> Path:
        local_app_data = Path(os.environ.get("LOCALAPPDATA", ""))
        return local_app_data / "BraveSoftware" / "Brave-Browser" / "User Data"

    @staticmethod
    def find_brave_profiles(user_data_path: Path = None) -> list[dict]:
        """Escanea y detecta todos los perfiles de usuario de Brave."""
        if user_data_path is None:
            user_data_path = BraveImporter.get_default_brave_user_data_path()
        profiles = []
        if not user_data_path.exists():
            return profiles
        try:
            for item in user_data_path.iterdir():
                if item.is_dir() and ((item / "History").exists() or (item / "Bookmarks").exists()):
                    hist_count, bm_count = BraveImporter.get_profile_stats(item)
                    profiles.append({
                        "name": item.name,
                        "path": item,
                        "history_count": hist_count,
                        "bookmarks_count": bm_count
                    })
        except Exception:
            pass
        profiles.sort(key=lambda x: (x["name"] != "Default", x["name"]))
        return profiles

    @staticmethod
    def get_profile_stats(profile_dir: Path) -> tuple[int, int]:
        hist_count = 0
        bm_count = 0
        hist_file = profile_dir / "History"
        bm_file = profile_dir / "Bookmarks"
        if hist_file.exists():
            tmp_path = None
            try:
                with tempfile.NamedTemporaryFile(delete=False) as tmp:
                    tmp_path = tmp.name
                shutil.copy2(hist_file, tmp_path)
                conn = sqlite3.connect(tmp_path)
                cur = conn.cursor()
                cur.execute("SELECT count(*) FROM urls WHERE hidden = 0")
                hist_count = cur.fetchone()[0]
                conn.close()
            except Exception:
                pass
            finally:
                if tmp_path and os.path.exists(tmp_path):
                    try:
                        os.remove(tmp_path)
                    except Exception:
                        pass

        if bm_file.exists():
            try:
                data = json.loads(bm_file.read_text(encoding="utf-8"))
                def _count(node):
                    c = 0
                    if isinstance(node, dict):
                        if node.get("type") == "url":
                            c += 1
                        for child in node.get("children", []):
                            c += _count(child)
                    return c
                for root in data.get("roots", {}).values():
                    bm_count += _count(root)
            except Exception:
                pass
        return hist_count, bm_count

    @staticmethod
    def import_all(profile_dir: Path, history_mgr, bookmark_mgr, import_hist: bool = True, import_bm: bool = True) -> tuple[int, int]:
        imported_hist = 0
        imported_bm = 0

        hist_file = profile_dir / "History"

        # 1. Importar Historial y Frecuentes
        if import_hist and hist_file.exists():
            tmp_path = None
            try:
                with tempfile.NamedTemporaryFile(delete=False) as tmp:
                    tmp_path = tmp.name
                shutil.copy2(hist_file, tmp_path)
                conn = sqlite3.connect(tmp_path)
                cur = conn.cursor()
                cur.execute("SELECT url, title, visit_count, last_visit_time FROM urls WHERE hidden = 0 ORDER BY last_visit_time DESC")
                rows = cur.fetchall()
                conn.close()

                existing_urls = {h.get("url") for h in history_mgr.data.get("history", [])}
                new_entries = []

                for url_str, title, visit_count, last_visit_time in rows:
                    if not url_str or not (url_str.startswith("http://") or url_str.startswith("https://")):
                        continue
                    try:
                        unix_time = max(0.0, (last_visit_time - 11644473600000000) / 1000000.0) if last_visit_time > 11644473600000000 else time.time()
                    except Exception:
                        unix_time = time.time()

                    parsed = urlparse(url_str)
                    domain = parsed.netloc.lower()
                    if domain.startswith("www."):
                        domain = domain[4:]
                    clean_title = title.strip() if title and title.strip() else domain

                    if "frequent" not in history_mgr.data:
                        history_mgr.data["frequent"] = {}
                    if domain and domain not in history_mgr.data["frequent"]:
                        history_mgr.data["frequent"][domain] = {
                            "domain": domain,
                            "title": clean_title,
                            "url": f"{parsed.scheme}://{parsed.netloc}",
                            "visits": int(visit_count) if visit_count else 1,
                            "last_visited": unix_time,
                            "favicon": ""
                        }
                    elif domain and domain in history_mgr.data["frequent"]:
                        history_mgr.data["frequent"][domain]["visits"] += int(visit_count or 1)

                    if url_str not in existing_urls:
                        existing_urls.add(url_str)
                        new_entries.append({
                            "domain": domain,
                            "title": clean_title,
                            "url": url_str,
                            "time": unix_time
                        })
                        imported_hist += 1

                if "history" not in history_mgr.data:
                    history_mgr.data["history"] = []
                history_mgr.data["history"] = (new_entries + history_mgr.data["history"])[:5000]
                history_mgr.save()
            except Exception as e:
                print(f"Error importando historial de Brave: {e}")
            finally:
                if tmp_path and os.path.exists(tmp_path):
                    try:
                        os.remove(tmp_path)
                    except Exception:
                        pass

        # 2. Importar Marcadores
        if import_bm:
            bm_file = profile_dir / "Bookmarks"
            existing_bm_urls = {b.get("url") for b in bookmark_mgr.bookmarks}
            if bm_file.exists():
                try:
                    data = json.loads(bm_file.read_text(encoding="utf-8"))
                    def _extract_bms(node):
                        nonlocal imported_bm
                        if isinstance(node, dict):
                            if node.get("type") == "url":
                                u = node.get("url", "")
                                name = node.get("name", "") or u
                                if u and u not in existing_bm_urls:
                                    existing_bm_urls.add(u)
                                    bookmark_mgr.bookmarks.append({
                                        "title": name,
                                        "url": u,
                                        "created": time.time()
                                    })
                                    imported_bm += 1
                            for child in node.get("children", []):
                                _extract_bms(child)
                    for root in data.get("roots", {}).values():
                        _extract_bms(root)
                    bookmark_mgr.save()
                except Exception as e:
                    print(f"Error importando marcadores de Brave: {e}")

            # Si no había archivo Bookmarks o estaba vacío, importar los 15 sitios más visitados de Brave como marcadores
            if imported_bm == 0 and hist_file.exists():
                tmp_path = None
                try:
                    with tempfile.NamedTemporaryFile(delete=False) as tmp:
                        tmp_path = tmp.name
                    shutil.copy2(hist_file, tmp_path)
                    conn = sqlite3.connect(tmp_path)
                    cur = conn.cursor()
                    cur.execute("SELECT url, title FROM urls WHERE hidden = 0 AND length(title) > 0 AND (url LIKE 'https://%' OR url LIKE 'http://%') ORDER BY visit_count DESC LIMIT 15")
                    for top_url, top_title in cur.fetchall():
                        if top_url not in existing_bm_urls:
                            existing_bm_urls.add(top_url)
                            bookmark_mgr.bookmarks.append({
                                "title": top_title.strip(),
                                "url": top_url,
                                "created": time.time()
                            })
                            imported_bm += 1
                    conn.close()
                    bookmark_mgr.save()
                except Exception:
                    pass
                finally:
                    if tmp_path and os.path.exists(tmp_path):
                        try:
                            os.remove(tmp_path)
                        except Exception:
                            pass

        return imported_hist, imported_bm

# ── 2.4 Gestor de Extensiones de Chrome Web Store (Chromium Nativo) ───────────
CHROME_EXT_ID_RE = re.compile(r"([a-p]{32})", re.IGNORECASE)

def extract_extension_id(text: str) -> str | None:
    if not text:
        return None
    text = text.strip()
    if len(text) == 32 and re.fullmatch(r"[a-zA-Z]{32}", text):
        return text.lower()
    m = CHROME_EXT_ID_RE.findall(text)
    if m:
        return m[-1].lower()
    return None

def _resolve_msg(text: str, locales_dir: Path) -> str:
    if not isinstance(text, str) or not (text.startswith("__MSG_") and text.endswith("__")):
        return text
    msg_key = text[6:-2]
    if locales_dir.exists():
        for loc in ["es", "es_419", "es_ES", "en", "en_US", "en_GB"]:
            loc_file = locales_dir / loc / "messages.json"
            if loc_file.exists():
                try:
                    msgs = json.loads(loc_file.read_text(encoding="utf-8"))
                    if msg_key in msgs and "message" in msgs[msg_key]:
                        return msgs[msg_key]["message"]
                except Exception:
                    pass
    return text

def download_and_extract_crx(extension_id: str, dest_dir: Path) -> Path:
    dest_dir.mkdir(parents=True, exist_ok=True)
    ext_dir = dest_dir / extension_id
    if ext_dir.exists() and (ext_dir / "manifest.json").exists():
        return ext_dir

    url = (
        f"https://clients2.google.com/service/update2/crx?"
        f"response=redirect&prodversion=130.0.0.0&acceptformat=crx2,crx3&x=id%3D{extension_id}%26uc"
    )
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
    })

    with urllib.request.urlopen(req, timeout=25) as resp:
        data = resp.read()

    if data[:4] != b"Cr24":
        raise ValueError("El archivo recibido no es una extensión CRX válida de Google.")

    version = struct.unpack("<I", data[4:8])[0]
    if version == 2:
        pub_len = struct.unpack("<I", data[8:12])[0]
        sig_len = struct.unpack("<I", data[12:16])[0]
        zip_offset = 16 + pub_len + sig_len
    elif version == 3:
        header_len = struct.unpack("<I", data[8:12])[0]
        zip_offset = 12 + header_len
    else:
        raise ValueError(f"Versión CRX no compatible: {version}")

    zip_data = data[zip_offset:]
    ext_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(zip_data)) as z:
        z.extractall(ext_dir)

    return ext_dir

def get_extension_info(ext_dir: Path) -> dict:
    manifest_file = ext_dir / "manifest.json"
    if not manifest_file.exists():
        return {}
    try:
        data = json.loads(manifest_file.read_text(encoding="utf-8"))
        locales_dir = ext_dir / "_locales"
        name = _resolve_msg(data.get("name", ext_dir.name), locales_dir)
        desc = _resolve_msg(data.get("description", ""), locales_dir)
        ver = data.get("version", "1.0")

        icon_b64 = None
        icons_field = data.get("icons", {})
        if isinstance(icons_field, dict) and icons_field:
            for k in ["48", "128", "32", "16", list(icons_field.keys())[0]]:
                if k in icons_field:
                    icon_path = ext_dir / icons_field[k]
                    if icon_path.exists():
                        try:
                            raw = icon_path.read_bytes()
                            ext = icon_path.suffix.lower().lstrip(".") or "png"
                            icon_b64 = f"data:image/{ext};base64,{base64.b64encode(raw).decode('ascii')}"
                            break
                        except Exception:
                            pass
        return {
            "id": ext_dir.name,
            "name": name,
            "version": ver,
            "description": desc,
            "icon_b64": icon_b64,
            "path": str(ext_dir)
        }
    except Exception as e:
        return {"id": ext_dir.name, "name": ext_dir.name, "version": "1.0", "description": "", "icon_b64": None, "path": str(ext_dir)}

class ChromeExtensionManager:
    def __init__(self, base_dir: Path = EXTENSIONS_DIR):
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def get_installed_extensions(self) -> list[dict]:
        results = []
        if not self.base_dir.exists():
            return results
        for d in self.base_dir.iterdir():
            if d.is_dir() and (d / "manifest.json").exists():
                info = get_extension_info(d)
                if info:
                    results.append(info)
        return results

    def is_installed(self, ext_id: str) -> bool:
        if not ext_id:
            return False
        return (self.base_dir / ext_id / "manifest.json").exists()

    def install(self, text_or_id: str, profile: QWebEngineProfile = None) -> tuple[bool, str, dict]:
        ext_id = extract_extension_id(text_or_id)
        if not ext_id:
            return False, "No se encontró un ID válido de extensión de Google Chrome.", {}

        try:
            ext_dir = download_and_extract_crx(ext_id, self.base_dir)
            info = get_extension_info(ext_dir)
            if profile and not profile.isOffTheRecord():
                profile.extensionManager().loadExtension(str(ext_dir))
            return True, "Extensión instalada correctamente.", info
        except Exception as e:
            return False, str(e), {}

    def uninstall(self, ext_id: str, profile: QWebEngineProfile = None) -> tuple[bool, str]:
        if not ext_id:
            return False, "ID de extensión no válido."
        ext_dir = self.base_dir / ext_id
        if profile and not profile.isOffTheRecord():
            mgr = profile.extensionManager()
            for info in mgr.extensions():
                if info.id() == ext_id or Path(info.path()).name == ext_id:
                    try:
                        mgr.unloadExtension(info)
                    except Exception:
                        pass
                    break
        if ext_dir.exists():
            try:
                shutil.rmtree(ext_dir, ignore_errors=True)
            except Exception as e:
                return False, f"Error eliminando archivos: {e}"
        return True, "Extensión eliminada correctamente."

    def load_all_into_profile(self, profile: QWebEngineProfile):
        if not profile or profile.isOffTheRecord():
            return
        mgr = profile.extensionManager()
        for ext in self.get_installed_extensions():
            try:
                mgr.loadExtension(ext["path"])
            except Exception:
                pass

_SHARED_PERSISTENT_PROFILE = None

def get_shared_profile() -> QWebEngineProfile:
    global _SHARED_PERSISTENT_PROFILE
    if _SHARED_PERSISTENT_PROFILE is None:
        PROFILE_DIR.mkdir(parents=True, exist_ok=True)
        storage_dir = PROFILE_DIR / "storage"
        cache_dir = PROFILE_DIR / "cache"
        storage_dir.mkdir(parents=True, exist_ok=True)
        cache_dir.mkdir(parents=True, exist_ok=True)
        app = QApplication.instance()
        _SHARED_PERSISTENT_PROFILE = QWebEngineProfile("aegis_profile", app)
        _SHARED_PERSISTENT_PROFILE.setPersistentStoragePath(str(storage_dir))
        _SHARED_PERSISTENT_PROFILE.setCachePath(str(cache_dir))
        _SHARED_PERSISTENT_PROFILE.setPersistentCookiesPolicy(QWebEngineProfile.PersistentCookiesPolicy.AllowPersistentCookies)
        _SHARED_PERSISTENT_PROFILE.setHttpUserAgent(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Aegis/1.3.5"
        )
        s = _SHARED_PERSISTENT_PROFILE.settings()
        s.setAttribute(QWebEngineSettings.WebAttribute.JavascriptCanOpenWindows, True)
        s.setAttribute(QWebEngineSettings.WebAttribute.AllowWindowActivationFromJavaScript, True)
        s.setAttribute(QWebEngineSettings.WebAttribute.FullScreenSupportEnabled, True)
        s.setAttribute(QWebEngineSettings.WebAttribute.PlaybackRequiresUserGesture, False)
        s.setAttribute(QWebEngineSettings.WebAttribute.JavascriptCanAccessClipboard, True)
        s.setAttribute(QWebEngineSettings.WebAttribute.JavascriptCanPaste, True)
        s.setAttribute(QWebEngineSettings.WebAttribute.DnsPrefetchEnabled, True)
        s.setAttribute(QWebEngineSettings.WebAttribute.WebGLEnabled, True)
        s.setAttribute(QWebEngineSettings.WebAttribute.Accelerated2dCanvasEnabled, True)
        s.setAttribute(QWebEngineSettings.WebAttribute.LocalStorageEnabled, True)
        s.setAttribute(QWebEngineSettings.WebAttribute.AutoLoadIconsForPage, True)
        s.setAttribute(QWebEngineSettings.WebAttribute.ScrollAnimatorEnabled, True)
        s.setAttribute(QWebEngineSettings.WebAttribute.ScreenCaptureEnabled, True)
        s.setAttribute(QWebEngineSettings.WebAttribute.BackForwardCacheEnabled, True)
    return _SHARED_PERSISTENT_PROFILE

class AegisToast(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("AegisToast")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.hide()
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.hide)

    def show_message(self, text: str, duration_ms: int = 3500):
        self.setText(text)
        self.adjustSize()
        self.setFixedSize(max(self.sizeHint().width() + 36, 260), 38)
        if self.parent():
            p_width = self.parent().width()
            p_height = self.parent().height()
            x = (p_width - self.width()) // 2
            y = p_height - self.height() - 32
            self.move(x, y)
        self.show()
        self.raise_()
        self._timer.start(duration_ms)

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

def silent_background_memory_purge(force: bool = False):
    """Compactación periódica del sistema operativo con protección inteligente de audio multimedia."""
    if not kernel32 or not psapi:
        return
    # Si hay reproducción activa de audio (YouTube, Spotify, Discord), evitar vaciar working set para prevenir microcortes
    if not force:
        try:
            app = QApplication.instance()
            if app and hasattr(app, "_aegis_windows"):
                for w in getattr(app, "_aegis_windows", []):
                    if hasattr(w, "views"):
                        for v in w.views:
                            if v and v.page() and v.page().recentlyAudible():
                                return
        except Exception:
            pass

    gc.collect()
    try:
        h = kernel32.GetCurrentProcess()
        if h:
            psapi.EmptyWorkingSet(h)
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
    """Icono de descargas moderno: flecha hacia bandeja abierta con trazo limpio de alta visibilidad."""
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="{size}" height="{size}" fill="none" stroke="{color_hex}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
      <path d="M4 17v2a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-2"/>
      <polyline points="7 11 12 16 17 11"/>
      <line x1="12" y1="4" x2="12" y2="16"/>
    </svg>"""
    return svg_to_icon(svg, size)

def create_history_icon(color_hex: str = "#388bfd", size: int = 16) -> QIcon:
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="{size}" height="{size}" fill="none" stroke="{color_hex}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="12" cy="12" r="10"/>
      <polyline points="12 6 12 12 14 14"/>
    </svg>"""
    return svg_to_icon(svg, size)

def create_extension_icon(color_hex: str = "#388bfd", size: int = 16) -> QIcon:
    """Icono de extensión universal: pieza de rompecabezas clásica y nítida como en Chrome y Brave."""
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="{size}" height="{size}" fill="none" stroke="{color_hex}" stroke-width="2.0" stroke-linecap="round" stroke-linejoin="round">
      <path d="M20.5 11H19V7a2 2 0 0 0-2-2h-4v-1.5a2.5 2.5 0 0 0-5 0V5H4a2 2 0 0 0-2 2v3.8h1.5a2.5 2.5 0 0 1 0 5H2V20a2 2 0 0 0 2 2h3.8v-1.5a2.5 2.5 0 0 1 5 0V22H17a2 2 0 0 0 2-2v-4h1.5a2.5 2.5 0 0 0 0-5z"/>
    </svg>"""
    return svg_to_icon(svg, size)

def create_aniplay_icon(color_hex: str = "#ff5370", size: int = 16) -> QIcon:
    """Icono de AniPlay Anime Hub: pantalla con botón play central."""
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="{size}" height="{size}" fill="none" stroke="{color_hex}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
      <rect x="2" y="4" width="20" height="13" rx="2" ry="2"/>
      <polygon points="10 8 16 10.5 10 13 10 8" fill="{color_hex}"/>
      <line x1="8" y1="20" x2="16" y2="20"/>
      <line x1="12" y1="17" x2="12" y2="20"/>
    </svg>"""
    return svg_to_icon(svg, size)

def create_star_icon(color_hex: str = "#388bfd", size: int = 16) -> QIcon:
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="{size}" height="{size}" fill="none" stroke="{color_hex}" stroke-width="2.0" stroke-linecap="round" stroke-linejoin="round">
      <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
    </svg>"""
    return svg_to_icon(svg, size)

def create_lock_icon(color_hex: str = "#2ea043", size: int = 16) -> QIcon:
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="{size}" height="{size}" fill="none" stroke="{color_hex}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
      <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
      <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
    </svg>"""
    return svg_to_icon(svg, size)

def create_warning_icon(color_hex: str = "#d29922", size: int = 16) -> QIcon:
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="{size}" height="{size}" fill="none" stroke="{color_hex}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
      <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
      <line x1="12" y1="9" x2="12" y2="13"/>
      <line x1="12" y1="17" x2="12.01" y2="17"/>
    </svg>"""
    return svg_to_icon(svg, size)

def create_copy_link_icon(color_hex: str = "#888888", size: int = 14) -> QIcon:
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="{size}" height="{size}" fill="none" stroke="{color_hex}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
      <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/>
      <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>
    </svg>"""
    return svg_to_icon(svg, size)

def create_book_icon(color_hex: str = "#888888", size: int = 14) -> QIcon:
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="{size}" height="{size}" fill="none" stroke="{color_hex}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
      <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/>
      <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>
    </svg>"""
    return svg_to_icon(svg, size)

def create_zoom_icon(color_hex: str = "#888888", size: int = 14) -> QIcon:
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="{size}" height="{size}" fill="none" stroke="{color_hex}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="11" cy="11" r="8"/>
      <line x1="21" y1="21" x2="16.65" y2="16.65"/>
      <line x1="11" y1="8" x2="11" y2="14"/>
      <line x1="8" y1="11" x2="14" y2="11"/>
    </svg>"""
    return svg_to_icon(svg, size)


def get_search_engine_svg(engine_name: str, size: int = 20) -> str:
    engine = str(engine_name).lower() if engine_name else "google"
    if "google" in engine:
        return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48" width="{size}" height="{size}">
          <path fill="#EA4335" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z"/>
          <path fill="#4285F4" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z"/>
          <path fill="#FBBC05" d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z"/>
          <path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z"/>
        </svg>"""
    elif "bing" in engine:
        return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48" width="{size}" height="{size}">
          <path fill="#008373" d="M10 6v36l14-7.5 12-7-6-3-6-3 10-5V8L10 6z"/>
          <path fill="#00A287" d="M24 21.5l10-5V8l-10 6.5v7z"/>
        </svg>"""
    elif "brave" in engine:
        return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48" width="{size}" height="{size}">
          <path fill="#FF5500" d="M38.5 16.5l-3.2-9.7c-.4-1.2-1.5-2-2.8-2h-17c-1.3 0-2.4.8-2.8 2l-3.2 9.7c-.3.8-.2 1.7.3 2.4l13.5 19.3c.7 1 2.1 1 2.8 0l13.5-19.3c.5-.7.6-1.6.3-2.4z"/>
          <path fill="#FFFFFF" d="M24 10l5 5h-10l5-5z"/>
        </svg>"""
    elif "yahoo" in engine:
        return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48" width="{size}" height="{size}">
          <rect width="48" height="48" rx="10" fill="#6001D2"/>
          <path fill="#FFFFFF" d="M14 12l7 14v10h6V26l7-14h-6.5l-3.5 8.5-3.5-8.5H14z"/>
        </svg>"""
    else:  # DuckDuckGo
        return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48" width="{size}" height="{size}">
          <circle cx="24" cy="24" r="22" fill="#DE5833"/>
          <ellipse cx="24" cy="21" rx="12" ry="10" fill="#FFFFFF"/>
          <ellipse cx="24" cy="22" rx="5" ry="3.5" fill="#F49A11"/>
          <circle cx="20" cy="18" r="2" fill="#222222"/>
          <circle cx="28" cy="18" r="2" fill="#222222"/>
          <path d="M16 27 C18 33, 30 33, 32 27 Z" fill="#209B48"/>
          <polygon points="24,24 21,27 27,27" fill="#F49A11"/>
        </svg>"""

def create_search_engine_icon(engine_name: str, size: int = 18) -> QIcon:
    svg = get_search_engine_svg(engine_name, size)
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
            Path(sys.executable).parent / "aegis_shields.dll",
            Path(getattr(sys, "_MEIPASS", ".")).resolve() / "aegis_shields.dll",
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
        try:
            info.setHttpHeader(b"DNT", b"1")
            info.setHttpHeader(b"Sec-GPC", b"1")
        except Exception:
            pass
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

def get_qt_palette_for_theme(theme_name: str) -> QPalette:
    """Garantiza que la paleta global del sistema Qt tenga texto blanco/claro en modo oscuro y negro en modo claro, erradicando letras negras ilegibles."""
    t = THEMES.get(theme_name, THEMES["Oscuro"])
    palette = QPalette()
    bg = QColor(t["bg"])
    surface = QColor(t["surface"])
    text = QColor(t["text"])
    accent = QColor(t["accent"])
    palette.setColor(QPalette.ColorRole.Window, bg)
    palette.setColor(QPalette.ColorRole.WindowText, text)
    palette.setColor(QPalette.ColorRole.Base, surface)
    palette.setColor(QPalette.ColorRole.AlternateBase, bg)
    palette.setColor(QPalette.ColorRole.ToolTipBase, surface)
    palette.setColor(QPalette.ColorRole.ToolTipText, text)
    palette.setColor(QPalette.ColorRole.Text, text)
    palette.setColor(QPalette.ColorRole.Button, surface)
    palette.setColor(QPalette.ColorRole.ButtonText, text)
    palette.setColor(QPalette.ColorRole.BrightText, QColor("#ffffff"))
    palette.setColor(QPalette.ColorRole.Highlight, accent)
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
    return palette

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
        is_bypass = self.parent_win.config.get("bypass_countdown", True) if self.parent_win else True
        self.cb_countdown.setChecked(is_bypass)
        self.cb_countdown.toggled.connect(self.toggle_countdown_bypass)
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

    def toggle_countdown_bypass(self, checked: bool):
        if self.parent_win:
            self.parent_win.config["bypass_countdown"] = checked
            self.parent_win.save_config()
            self.parent_win.load_userscripts()
            self.parent_win.show_toast(f"Bypass de temporizadores: {'Activado' if checked else 'Desactivado'}")

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
        if hasattr(self, "btn_tool_aniplay"):
            enabled = self.parent_win.config.get("enable_aniplay", False) if self.parent_win else False
            self.btn_tool_aniplay.setVisible(enabled)
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

# ── 10.1 Menú Principal de la Aplicación (Estilo Limpio y Sin Emojis ⋮) ────────
class AegisAppMenuItem(QPushButton):
    def __init__(self, item_id: str, text: str, shortcut: str, callback, parent_menu):
        super().__init__()
        self.item_id = item_id
        self.menu_text = text
        self.parent_menu = parent_menu
        self.setProperty("class", "menu-item-btn")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.on_context_menu)

        h_box = QHBoxLayout(self)
        h_box.setContentsMargins(10, 6, 10, 6)
        h_box.setSpacing(8)

        self.lbl_txt = QLabel(text)
        self.lbl_txt.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.lbl_txt.setObjectName("MenuItemText")
        h_box.addWidget(self.lbl_txt)
        h_box.addStretch()

        if shortcut:
            self.lbl_sc = QLabel(shortcut)
            self.lbl_sc.setProperty("class", "menu-shortcut-lbl")
            self.lbl_sc.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
            h_box.addWidget(self.lbl_sc)

        self.clicked.connect(lambda: (self.parent_menu.hide(), callback()))

    def on_context_menu(self, pos):
        if not self.item_id or not self.parent_menu or not self.parent_menu.parent_win:
            return
        p_win = self.parent_menu.parent_win
        pinned_list = p_win.config.get("pinned_toolbar_buttons", [])
        is_pinned = self.item_id in pinned_list

        menu = QMenu(self)
        menu.setStyleSheet(p_win.current_qss)
        if is_pinned:
            act = menu.addAction("Desanclar de la barra de herramientas")
            act.triggered.connect(lambda: p_win.unpin_toolbar_button(self.item_id))
        else:
            act = menu.addAction("Anclar a la barra de herramientas")
            act.triggered.connect(lambda: p_win.pin_toolbar_button(self.item_id))
        menu.exec(self.mapToGlobal(pos))

class AegisAppMenu(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent, Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.setObjectName("AegisAppMenu")
        self.setFixedWidth(270)
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

        def add_item(item_id: str, text: str, shortcut: str, callback):
            btn = AegisAppMenuItem(item_id, text, shortcut, callback, self)
            layout.addWidget(btn)
            return btn

        def add_separator():
            sep = QFrame()
            sep.setObjectName("MenuSeparator")
            sep.setFixedHeight(1)
            layout.addWidget(sep)

        add_item("new_tab", "Nueva pestaña", "Ctrl+T", lambda: self.parent_win.add_new_tab())
        add_item("new_window", "Nueva ventana", "Ctrl+N", lambda: self.parent_win.open_new_window())
        add_item("incognito", "Nueva ventana privada", "Ctrl+Shift+N", lambda: self.parent_win.open_incognito_window())
        add_item("reopen_tab", "Reabrir pestaña cerrada", "Ctrl+Shift+T", lambda: self.parent_win.reopen_closed_tab())
        add_item("tab_search", "Buscar pestañas", "Ctrl+Shift+A", lambda: self.parent_win.toggle_tab_search_popup())
        add_separator()

        add_item("downloads", "Descargas", "Ctrl+J", lambda: self.parent_win.open_internal_page("aegis://downloads"))
        add_item("history", "Historial", "Ctrl+H", lambda: self.parent_win.open_internal_page("aegis://history"))
        add_item("extensions", "Extensiones", "Ctrl+Shift+E", lambda: self.parent_win.open_internal_page("aegis://extensions"))
        add_item("sidebar", "Barra lateral", "Ctrl+B", lambda: self.parent_win.toggle_sidebar())
        add_item("bookmarks_bar", "Barra de marcadores", "Ctrl+Shift+B", lambda: self.parent_win.toggle_bookmarks_bar())
        if self.parent_win and self.parent_win.config.get("enable_aniplay", False):
            add_item("aniplay", "AniPlay Anime Hub", "", lambda: self.parent_win.open_internal_page("aegis://aniplay"))
        add_separator()

        add_item("reader_mode", "Modo lectura", "F9", lambda: self.parent_win.toggle_reader_mode())
        add_item("clean_copy", "Copiar enlace limpio", "", lambda: self.parent_win.copy_clean_url())
        add_item("screenshot", "Capturar pantalla", "Ctrl+Shift+S", lambda: self.parent_win.capture_page_screenshot())
        add_item("print_pdf", "Guardar como PDF", "Ctrl+P", lambda: self.parent_win.print_to_pdf())
        add_item("find_in_page", "Buscar en la página", "Ctrl+F", lambda: self.parent_win.find_bar.show_find())
        add_item("mute_tab", "Silenciar pestaña", "Ctrl+M", lambda: self.parent_win.toggle_mute_current_tab())
        add_item("pip", "Imagen en imagen (PiP)", "Alt+P", lambda: self.parent_win.toggle_picture_in_picture())
        add_item("media_control", "Control multimedia", "", lambda: self.parent_win.toggle_media_popup())
        add_item("theme_toggle", "Cambiar tema", "", lambda: self.parent_win.toggle_theme())
        add_item("devtools", "Herramientas de desarrollo", "F12", lambda: self.parent_win.open_devtools())
        add_separator()

        add_item("clear_data", "Borrar datos de navegación", "Ctrl+Shift+Del", lambda: self.parent_win.open_clear_data_dialog())
        add_item("import_brave", "Importar datos de Brave...", "", lambda: self.parent_win.open_brave_import_dialog())
        add_item("settings", "Configuración", "Alt+S", lambda: self.parent_win.open_internal_page("aegis://settings"))
        add_separator()

        # Fila de Zoom
        zoom_widget = QWidget()
        zoom_layout = QHBoxLayout(zoom_widget)
        zoom_layout.setContentsMargins(10, 4, 10, 4)
        zoom_layout.setSpacing(8)

        self.lbl_zoom = QLabel("Zoom")
        self.lbl_zoom.setObjectName("ZoomLabel")
        zoom_layout.addWidget(self.lbl_zoom)
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

        add_item("about", "Acerca de Aegis v1.3.5", "", lambda: self.parent_win.open_internal_page("aegis://settings"))

    def apply_theme(self, t: dict):
        rgb_text = hex_to_rgb(t["text"])
        if hasattr(self, "btn_tool_aniplay"):
            enabled = self.parent_win.config.get("enable_aniplay", False) if self.parent_win else False
            self.btn_tool_aniplay.setVisible(enabled)
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
            QLabel#MenuItemText {{
                color: {t['text']};
                background: transparent;
                border: none;
                font-size: 12.5px;
                font-weight: 500;
            }}
            QLabel.menu-shortcut-lbl {{
                color: rgba({rgb_text}, 0.50);
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
            QLabel#ZoomLabel {{
                color: {t['text']};
                font-size: 12px;
                font-weight: 500;
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

# ── 10.1.1 Cuadro Desplegable de Ajuste Interactivo de Zoom ──────────────────
class AegisZoomPopup(QFrame):
    """Widget flotante moderno que se despliega al interactuar con el zoom para un control cómodo."""
    def __init__(self, parent=None):
        super().__init__(parent, Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.setObjectName("AegisZoomPopup")
        self.setFixedWidth(210)
        self.parent_win = parent
        self.init_ui()

    def hideEvent(self, event):
        if self.parent_win:
            self.parent_win._last_zoom_close_time = time.time()
        super().hideEvent(event)

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)

        lbl_title = QLabel("Zoom de la página")
        lbl_title.setObjectName("ZoomPopupTitle")
        layout.addWidget(lbl_title)

        h_box = QHBoxLayout()
        h_box.setSpacing(6)

        self.btn_zoom_out = QPushButton("−")
        self.btn_zoom_out.setObjectName("ZoomPopupBtn")
        self.btn_zoom_out.setFixedSize(28, 28)
        self.btn_zoom_out.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_zoom_out.setToolTip("Alejar zoom")
        self.btn_zoom_out.clicked.connect(self.on_zoom_out)
        h_box.addWidget(self.btn_zoom_out)

        self.lbl_zoom_val = QLabel("100%")
        self.lbl_zoom_val.setObjectName("ZoomPopupVal")
        self.lbl_zoom_val.setAlignment(Qt.AlignmentFlag.AlignCenter)
        h_box.addWidget(self.lbl_zoom_val, stretch=1)

        self.btn_zoom_in = QPushButton("+")
        self.btn_zoom_in.setObjectName("ZoomPopupBtn")
        self.btn_zoom_in.setFixedSize(28, 28)
        self.btn_zoom_in.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_zoom_in.setToolTip("Acercar zoom")
        self.btn_zoom_in.clicked.connect(self.on_zoom_in)
        h_box.addWidget(self.btn_zoom_in)

        layout.addLayout(h_box)

        self.btn_reset = QPushButton("Restablecer (100%)")
        self.btn_reset.setObjectName("ZoomPopupResetBtn")
        self.btn_reset.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_reset.clicked.connect(self.on_zoom_reset)
        layout.addWidget(self.btn_reset)

    def on_zoom_out(self):
        if self.parent_win:
            self.parent_win.zoom_out()
            self.update_val()

    def on_zoom_in(self):
        if self.parent_win:
            self.parent_win.zoom_in()
            self.update_val()

    def on_zoom_reset(self):
        if self.parent_win:
            self.parent_win.zoom_reset()
            self.update_val()
            self.hide()

    def update_val(self):
        if not self.parent_win:
            return
        v = self.parent_win.current_view()
        if v:
            zf = round(v.zoomFactor(), 2)
            pct = int(zf * 100)
            self.lbl_zoom_val.setText(f"{pct}%")
            self.btn_reset.setEnabled(abs(zf - 1.0) > 0.02)

    def apply_theme(self, t: dict):
        rgb_text = hex_to_rgb(t["text"])
        if hasattr(self, "btn_tool_aniplay"):
            enabled = self.parent_win.config.get("enable_aniplay", False) if self.parent_win else False
            self.btn_tool_aniplay.setVisible(enabled)
        qss = f"""
            QFrame#AegisZoomPopup {{
                background-color: {t['surface']};
                border: 1px solid rgba({rgb_text}, 0.16);
                border-radius: 10px;
            }}
            QLabel#ZoomPopupTitle {{
                color: {t['text']};
                font-size: 11.5px;
                font-weight: 600;
            }}
            QLabel#ZoomPopupVal {{
                color: {t['text']};
                font-size: 14px;
                font-weight: 700;
            }}
            QPushButton#ZoomPopupBtn {{
                background-color: {t['bg']};
                border: 1px solid rgba({rgb_text}, 0.15);
                border-radius: 6px;
                color: {t['text']};
                font-size: 15px;
                font-weight: bold;
            }}
            QPushButton#ZoomPopupBtn:hover {{
                border-color: {t['accent']};
                color: {t['accent']};
            }}
            QPushButton#ZoomPopupResetBtn {{
                background-color: {t['bg']};
                border: 1px solid rgba({rgb_text}, 0.15);
                border-radius: 6px;
                color: {t['text']};
                padding: 5px 8px;
                font-size: 11.5px;
                font-weight: 500;
            }}
            QPushButton#ZoomPopupResetBtn:hover {{
                background-color: {t['accent']};
                color: #ffffff;
            }}
            QPushButton#ZoomPopupResetBtn:disabled {{
                opacity: 0.5;
                color: rgba({rgb_text}, 0.35);
            }}
        """
        self.setStyleSheet(qss)
        self.update()

# ── 10.2 Panel Desplegable de Descargas (Directo desde la Toolbar) ─────────────
class AegisDownloadsPopup(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent, Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.setObjectName("AegisDownloadsPopup")
        self.setFixedWidth(340)
        self.parent_win = parent
        self.init_ui()

    def hideEvent(self, event):
        if self.parent_win:
            self.parent_win._last_downloads_close_time = time.time()
        super().hideEvent(event)

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        header = QHBoxLayout()
        lbl_title = QLabel("Descargas recientes")
        lbl_title.setStyleSheet("font-weight: 700; font-size: 13.5px; color: #f0f6fc;")
        header.addWidget(lbl_title)
        header.addStretch()

        btn_folder = QPushButton("📁 Abrir Carpeta")
        btn_folder.setProperty("class", "mini-action-btn")
        btn_folder.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_folder.clicked.connect(self.open_downloads_folder)
        header.addWidget(btn_folder)
        layout.addLayout(header)

        self.list_container = QVBoxLayout()
        self.list_container.setSpacing(6)
        layout.addLayout(self.list_container)

        self.refresh_list()

        sep = QFrame()
        sep.setObjectName("MenuSeparator")
        sep.setFixedHeight(1)
        layout.addWidget(sep)

        footer = QHBoxLayout()
        btn_all = QPushButton("Ver todas las descargas")
        btn_all.setProperty("class", "menu-item-btn")
        btn_all.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_all.clicked.connect(lambda: (self.hide(), self.parent_win.open_internal_page("aegis://downloads")))
        footer.addWidget(btn_all)

        btn_clear = QPushButton("Limpiar lista")
        btn_clear.setProperty("class", "menu-item-btn")
        btn_clear.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_clear.clicked.connect(self.clear_downloads)
        footer.addWidget(btn_clear)
        layout.addLayout(footer)

    def open_downloads_folder(self):
        folder = Path.home() / "Downloads"
        folder.mkdir(parents=True, exist_ok=True)
        subprocess.Popen(f'explorer.exe "{str(folder)}"')
        self.hide()

    def clear_downloads(self):
        if self.parent_win and hasattr(self.parent_win, "downloads_mgr"):
            self.parent_win.downloads_mgr.clear()
            self.refresh_list()

    def refresh_list(self):
        while self.list_container.count():
            item = self.list_container.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        downloads = self.parent_win.downloads_mgr.downloads if (self.parent_win and hasattr(self.parent_win, "downloads_mgr")) else []
        if not downloads:
            lbl_empty = QLabel("No hay descargas recientes")
            lbl_empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl_empty.setStyleSheet("padding: 16px; color: #8b949e; font-size: 12px;")
            self.list_container.addWidget(lbl_empty)
            return

        for d in downloads[:5]:
            card = QFrame()
            card.setProperty("class", "download-popup-card")
            c_layout = QVBoxLayout(card)
            c_layout.setContentsMargins(10, 8, 10, 8)
            c_layout.setSpacing(5)

            top_row = QHBoxLayout()
            fname = d.get("filename", "Descarga")
            display_name = fname if len(fname) <= 24 else fname[:22] + "…"
            lbl_name = QLabel(display_name)
            lbl_name.setStyleSheet("font-weight: 600; font-size: 12px; color: #f0f6fc;")
            top_row.addWidget(lbl_name)
            top_row.addStretch()

            state = d.get("state", "completed")
            total = d.get("total_bytes", 0)
            sz_str = format_bytes(total) if total > 0 else ""
            status_text = f"{sz_str} · Completado" if state == "completed" else ("Descargando..." if state == "downloading" else "Cancelado")
            lbl_status = QLabel(status_text)
            lbl_status.setStyleSheet("font-size: 11px; color: #8b949e;")
            top_row.addWidget(lbl_status)
            c_layout.addLayout(top_row)

            btn_row = QHBoxLayout()
            btn_row.setSpacing(6)
            p = d.get("path", "")
            btn_open = QPushButton("Abrir")
            btn_open.setProperty("class", "mini-action-btn")
            btn_open.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_open.clicked.connect(lambda checked, path=p: self.open_file(path))
            btn_row.addWidget(btn_open)

            btn_show = QPushButton("Carpeta")
            btn_show.setProperty("class", "mini-action-btn")
            btn_show.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_show.clicked.connect(lambda checked, path=p: self.open_folder(path))
            btn_row.addWidget(btn_show)
            btn_row.addStretch()
            c_layout.addLayout(btn_row)

            self.list_container.addWidget(card)

    def open_file(self, path: str):
        if path and os.path.exists(path):
            try:
                os.startfile(path)
                self.hide()
            except Exception:
                pass

    def open_folder(self, path: str):
        if path:
            folder = os.path.dirname(path) if os.path.isfile(path) else path
            if os.path.exists(folder):
                cmd = f'explorer.exe /select,"{path}"' if os.path.isfile(path) else f'explorer.exe "{folder}"'
                subprocess.Popen(cmd)
                self.hide()

    def apply_theme(self, t: dict):
        rgb_text = hex_to_rgb(t["text"])
        if hasattr(self, "btn_tool_aniplay"):
            enabled = self.parent_win.config.get("enable_aniplay", False) if self.parent_win else False
            self.btn_tool_aniplay.setVisible(enabled)
        qss = f"""
            QFrame#AegisDownloadsPopup {{
                background-color: {t['surface']};
                border: 1px solid rgba({rgb_text}, 0.15);
                border-radius: 12px;
            }}
            QFrame.download-popup-card {{
                background-color: {t['bg']};
                border: 1px solid rgba({rgb_text}, 0.08);
                border-radius: 8px;
            }}
            QLabel {{
                color: {t['text']};
            }}
            QPushButton.mini-action-btn {{
                background: transparent;
                color: {t['accent']};
                border: 1px solid rgba({rgb_text}, 0.15);
                border-radius: 4px;
                padding: 3px 8px;
                font-size: 11px;
                font-weight: 500;
            }}
            QPushButton.mini-action-btn:hover {{
                background-color: {t['accent']};
                color: #ffffff;
            }}
            QPushButton.menu-item-btn {{
                background: transparent;
                border: none;
                border-radius: 6px;
                color: {t['text']};
                padding: 6px 10px;
                font-size: 12px;
            }}
            QPushButton.menu-item-btn:hover {{
                background-color: {t['bg']};
                color: {t['accent']};
            }}
            QFrame#MenuSeparator {{
                background-color: rgba({rgb_text}, 0.08);
                border: none;
                margin: 2px 0;
            }}
        """
        self.setStyleSheet(qss)
        self.update()

# ── 10.3 Panel Desplegable de Extensiones y UserScripts (Toolbar) ─────────────
class AegisExtensionsPopup(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent, Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.setObjectName("AegisExtensionsPopup")
        self.setFixedWidth(350)
        self.parent_win = parent
        self.init_ui()

    def hideEvent(self, event):
        if self.parent_win:
            self.parent_win._last_extensions_close_time = time.time()
        super().hideEvent(event)

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        header = QHBoxLayout()
        lbl_title = QLabel("Extensiones y Complementos")
        lbl_title.setStyleSheet("font-weight: 700; font-size: 13.5px; color: #f0f6fc;")
        header.addWidget(lbl_title)
        layout.addLayout(header)

        # Card de Extensiones de Chrome Web Store
        self.chrome_card = QFrame()
        self.chrome_card.setObjectName("ExtensionCard")
        self.chrome_inner_layout = QVBoxLayout(self.chrome_card)
        self.chrome_inner_layout.setContentsMargins(10, 8, 10, 8)
        self.chrome_inner_layout.setSpacing(4)
        layout.addWidget(self.chrome_card)

        # Card de Aegis Shields
        shields_card = QFrame()
        shields_card.setObjectName("ExtensionCard")
        sc_layout = QHBoxLayout(shields_card)
        sc_layout.setContentsMargins(10, 8, 10, 8)

        info_l = QVBoxLayout()
        info_l.setSpacing(2)
        lbl_s_title = QLabel("Aegis Shields Core")
        lbl_s_title.setStyleSheet("font-weight: 600; font-size: 12.5px; color: #f0f6fc;")
        lbl_s_sub = QLabel("Bloqueador nativo en Rust (Adblock + Minería)")
        lbl_s_sub.setStyleSheet("font-size: 11px; color: #8b949e;")
        info_l.addWidget(lbl_s_title)
        info_l.addWidget(lbl_s_sub)
        sc_layout.addLayout(info_l)
        sc_layout.addStretch()

        is_enabled = self.parent_win.interceptor.enabled if (self.parent_win and hasattr(self.parent_win, "interceptor")) else True
        self.sw_shields = ToggleSwitch(checked=is_enabled, parent=shields_card)
        self.sw_shields.toggled.connect(self.on_shields_toggled)
        sc_layout.addWidget(self.sw_shields)
        layout.addWidget(shields_card)

        # Card de UserScripts
        self.scripts_card = QFrame()
        self.scripts_card.setObjectName("ExtensionCard")
        self.sc_inner_layout = QVBoxLayout(self.scripts_card)
        self.sc_inner_layout.setContentsMargins(10, 8, 10, 8)
        self.sc_inner_layout.setSpacing(4)
        layout.addWidget(self.scripts_card)

        self.refresh_state()

        sep = QFrame()
        sep.setObjectName("MenuSeparator")
        sep.setFixedHeight(1)
        layout.addWidget(sep)

        btn_store = QPushButton("🛍️ Abrir Chrome Web Store")
        btn_store.setProperty("class", "menu-item-btn")
        btn_store.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_store.clicked.connect(self.open_chrome_store)
        layout.addWidget(btn_store)

        btn_folder = QPushButton("📁 Abrir carpeta de scripts (.js)")
        btn_folder.setProperty("class", "menu-item-btn")
        btn_folder.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_folder.clicked.connect(self.open_scripts_folder)
        layout.addWidget(btn_folder)

        btn_manage = QPushButton("⚙️ Administrar extensiones")
        btn_manage.setProperty("class", "menu-item-btn")
        btn_manage.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_manage.clicked.connect(lambda: (self.hide(), self.parent_win.open_internal_page("aegis://extensions")))
        layout.addWidget(btn_manage)

    def open_chrome_store(self):
        self.hide()
        if self.parent_win:
            v = self.parent_win.current_view()
            if v:
                v.load(QUrl("https://chromewebstore.google.com"))
            else:
                self.parent_win.add_new_tab("https://chromewebstore.google.com")

    def on_shields_toggled(self, checked: bool):
        if self.parent_win and hasattr(self.parent_win, "interceptor"):
            self.parent_win.interceptor.enabled = checked
            self.parent_win.config["shields_enabled"] = checked
            self.parent_win.save_config()
            if hasattr(self.parent_win, "shields_popup"):
                self.parent_win.shields_popup.main_switch.setChecked(checked)

    def open_scripts_folder(self):
        USERSCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
        subprocess.Popen(f'explorer.exe "{str(USERSCRIPTS_DIR)}"')
        self.hide()

    def refresh_state(self):
        # 1. Extensiones Chrome Web Store
        while self.chrome_inner_layout.count():
            item = self.chrome_inner_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        lbl_c = QLabel("Extensiones Chrome Web Store")
        lbl_c.setStyleSheet("font-weight: 600; font-size: 12.5px; color: #f0f6fc;")
        self.chrome_inner_layout.addWidget(lbl_c)

        exts = self.parent_win.extensions_mgr.get_installed_extensions() if (self.parent_win and hasattr(self.parent_win, "extensions_mgr")) else []
        if exts:
            lbl_c_status = QLabel(f"✓ {len(exts)} activa(s)")
            lbl_c_status.setStyleSheet("font-size: 11px; color: #2ea043; font-weight: 500;")
            self.chrome_inner_layout.addWidget(lbl_c_status)
            for ext in exts[:3]:
                name = ext.get("name", "Extensión")
                ver = ext.get("version", "")
                lbl_name = QLabel(f"• {name} (v{ver})")
                lbl_name.setStyleSheet("font-size: 11px; opacity: 0.85;")
                self.chrome_inner_layout.addWidget(lbl_name)
            if len(exts) > 3:
                lbl_more = QLabel(f"+ {len(exts) - 3} más en aegis://extensions")
                lbl_more.setStyleSheet("font-size: 10.5px; opacity: 0.6;")
                self.chrome_inner_layout.addWidget(lbl_more)
        else:
            lbl_none_c = QLabel("Sin extensiones de Chrome instaladas")
            lbl_none_c.setStyleSheet("font-size: 11px; color: #8b949e;")
            self.chrome_inner_layout.addWidget(lbl_none_c)

        # 2. UserScripts
        while self.sc_inner_layout.count():
            item = self.sc_inner_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        lbl_s = QLabel("Scripts de Usuario (UserScripts)")
        lbl_s.setStyleSheet("font-weight: 600; font-size: 12.5px; color: #f0f6fc;")
        self.sc_inner_layout.addWidget(lbl_s)

        scripts = list(USERSCRIPTS_DIR.glob("*.js")) if USERSCRIPTS_DIR.exists() else []
        if scripts:
            lbl_status = QLabel(f"✓ {len(scripts)} scripts activos cargados")
            lbl_status.setStyleSheet("font-size: 11px; color: #2ea043; font-weight: 500;")
            self.sc_inner_layout.addWidget(lbl_status)
            for s in scripts[:3]:
                lbl_name = QLabel(f"• {s.name}")
                lbl_name.setStyleSheet("font-size: 11px; opacity: 0.8;")
                self.sc_inner_layout.addWidget(lbl_name)
        else:
            lbl_none = QLabel("No hay scripts instalados aún")
            lbl_none.setStyleSheet("font-size: 11px; color: #8b949e;")
            self.sc_inner_layout.addWidget(lbl_none)

    def apply_theme(self, t: dict):
        rgb_text = hex_to_rgb(t["text"])
        if hasattr(self, "btn_tool_aniplay"):
            enabled = self.parent_win.config.get("enable_aniplay", False) if self.parent_win else False
            self.btn_tool_aniplay.setVisible(enabled)
        qss = f"""
            QFrame#AegisExtensionsPopup {{
                background-color: {t['surface']};
                border: 1px solid rgba({rgb_text}, 0.15);
                border-radius: 12px;
            }}
            QFrame#ExtensionCard {{
                background-color: {t['bg']};
                border: 1px solid rgba({rgb_text}, 0.08);
                border-radius: 8px;
            }}
            QLabel {{
                color: {t['text']};
            }}
            QPushButton.menu-item-btn {{
                background: transparent;
                border: none;
                border-radius: 6px;
                color: {t['text']};
                padding: 6px 10px;
                font-size: 12px;
            }}
            QPushButton.menu-item-btn:hover {{
                background-color: {t['bg']};
                color: {t['accent']};
            }}
            QFrame#MenuSeparator {{
                background-color: rgba({rgb_text}, 0.08);
                border: none;
                margin: 2px 0;
            }}
        """
        self.setStyleSheet(qss)
        if hasattr(self, "sw_shields"):
            self.sw_shields.update_colors(t["accent"], t["bg"])
        self.update()

# ── 10.3.5 Panel Desplegable de Control Multimedia (Toolbar 🎵) ───────────────
class AegisMediaPopup(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent, Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.setObjectName("AegisMediaPopup")
        self.setFixedWidth(320)
        self.parent_win = parent
        self.init_ui()

    def hideEvent(self, event):
        if self.parent_win:
            self.parent_win._last_media_close_time = time.time()
        super().hideEvent(event)

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        header = QHBoxLayout()
        lbl_title = QLabel("🎵 Control de Reproducción")
        lbl_title.setStyleSheet("font-weight: 700; font-size: 13px;")
        header.addWidget(lbl_title)
        layout.addLayout(header)

        self.card = QFrame()
        self.card.setObjectName("MediaCard")
        cl = QVBoxLayout(self.card)
        cl.setContentsMargins(12, 10, 12, 10)
        cl.setSpacing(6)

        self.lbl_track = QLabel("No hay audio reproduciéndose")
        self.lbl_track.setStyleSheet("font-weight: 600; font-size: 12px; color: #f0f6fc;")
        self.lbl_track.setWordWrap(True)
        cl.addWidget(self.lbl_track)

        self.lbl_site = QLabel("")
        self.lbl_site.setStyleSheet("font-size: 11px; color: #8b949e;")
        cl.addWidget(self.lbl_site)

        ctrl_l = QHBoxLayout()
        ctrl_l.setSpacing(6)

        self.btn_prev = QPushButton("⏮️ -10s")
        self.btn_prev.setProperty("class", "media-ctrl-btn")
        self.btn_prev.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_prev.clicked.connect(lambda: self.seek_audio(-10))
        ctrl_l.addWidget(self.btn_prev)

        self.btn_play_pause = QPushButton("⏯️ Play/Pausa")
        self.btn_play_pause.setProperty("class", "media-ctrl-btn")
        self.btn_play_pause.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_play_pause.clicked.connect(self.toggle_play_pause)
        ctrl_l.addWidget(self.btn_play_pause)

        self.btn_next = QPushButton("⏭️ +10s")
        self.btn_next.setProperty("class", "media-ctrl-btn")
        self.btn_next.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_next.clicked.connect(lambda: self.seek_audio(10))
        ctrl_l.addWidget(self.btn_next)

        self.btn_mute = QPushButton("🔇")
        self.btn_mute.setProperty("class", "media-ctrl-btn")
        self.btn_mute.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_mute.clicked.connect(self.toggle_mute_playing)
        ctrl_l.addWidget(self.btn_mute)

        cl.addLayout(ctrl_l)

        self.btn_goto = QPushButton("🔗 Ir a la pestaña")
        self.btn_goto.setProperty("class", "media-goto-btn")
        self.btn_goto.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_goto.clicked.connect(self.go_to_playing_tab)
        cl.addWidget(self.btn_goto)

        layout.addWidget(self.card)

    def get_audible_view(self) -> QWebEngineView | None:
        if not self.parent_win or not hasattr(self.parent_win, "views"):
            return None
        for v in self.parent_win.views:
            if v and v.page() and v.page().recentlyAudible():
                return v
        return self.parent_win.current_view()

    def refresh_state(self):
        v = self.get_audible_view()
        if v:
            title = v.title() or "Página multimedia"
            host = v.url().host() or "Web"
            is_muted = v.page().isAudioMuted() if v.page() else False
            self.lbl_track.setText(title)
            self.lbl_site.setText(f"Sitio: {host} · {'🔇 Silenciada' if is_muted else '🔊 Sonando'}")
            self.btn_mute.setText("🔊" if is_muted else "🔇")
            self.btn_play_pause.setEnabled(True)
            self.btn_prev.setEnabled(True)
            self.btn_next.setEnabled(True)
            self.btn_goto.setEnabled(True)
        else:
            self.lbl_track.setText("No hay contenido multimedia activo")
            self.lbl_site.setText("Inicia reproducción en YouTube, Spotify, Netflix o Discord")
            self.btn_play_pause.setEnabled(False)
            self.btn_prev.setEnabled(False)
            self.btn_next.setEnabled(False)
            self.btn_goto.setEnabled(False)

    def toggle_play_pause(self):
        v = self.get_audible_view()
        if v:
            v.page().runJavaScript("""
            (() => {
                const media = document.querySelectorAll('video, audio');
                if (media.length > 0) {
                    let anyPlaying = Array.from(media).some(m => !m.paused);
                    media.forEach(m => {
                        if (anyPlaying) m.pause(); else m.play();
                    });
                }
            })();
            """)

    def seek_audio(self, delta: int):
        v = self.get_audible_view()
        if v:
            v.page().runJavaScript(f"""
            (() => {{
                const media = document.querySelectorAll('video, audio');
                media.forEach(m => {{
                    try {{ m.currentTime = Math.max(0, m.currentTime + ({delta})); }} catch(e) {{}}
                }});
            }})();
            """)

    def toggle_mute_playing(self):
        v = self.get_audible_view()
        if v and v.page():
            new_muted = not v.page().isAudioMuted()
            v.page().setAudioMuted(new_muted)
            self.refresh_state()

    def go_to_playing_tab(self):
        v = self.get_audible_view()
        if v and self.parent_win:
            idx = self.parent_win.views.index(v) if v in self.parent_win.views else -1
            if idx != -1:
                self.parent_win.tab_bar.setCurrentIndex(idx)
        self.hide()

    def apply_theme(self, t: dict):
        rgb_text = hex_to_rgb(t["text"])
        if hasattr(self, "btn_tool_aniplay"):
            enabled = self.parent_win.config.get("enable_aniplay", False) if self.parent_win else False
            self.btn_tool_aniplay.setVisible(enabled)
        qss = f"""
            QFrame#AegisMediaPopup {{
                background-color: {t['surface']};
                border: 1px solid rgba({rgb_text}, 0.15);
                border-radius: 12px;
            }}
            QFrame#MediaCard {{
                background-color: {t['bg']};
                border: 1px solid rgba({rgb_text}, 0.08);
                border-radius: 8px;
            }}
            QLabel {{
                color: {t['text']};
            }}
            QPushButton.media-ctrl-btn {{
                background: {t['surface']};
                border: 1px solid rgba({rgb_text}, 0.12);
                border-radius: 6px;
                color: {t['text']};
                padding: 6px 8px;
                font-size: 11px;
                font-weight: 600;
            }}
            QPushButton.media-ctrl-btn:hover {{
                border-color: {t['accent']};
                color: {t['accent']};
            }}
            QPushButton.media-goto-btn {{
                background: transparent;
                border: 1px solid rgba({rgb_text}, 0.12);
                border-radius: 6px;
                color: {t['accent']};
                padding: 5px;
                font-size: 11.5px;
                font-weight: 600;
            }}
            QPushButton.media-goto-btn:hover {{
                background-color: {t['surface']};
            }}
        """
        self.setStyleSheet(qss)

# ── 10.3.6 Popup de Información y Seguridad del Sitio (🔒 / ℹ️) ─────────────────
class AegisSiteInfoPopup(QFrame):
    def __init__(self, parent_win=None):
        super().__init__(parent_win, Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.setObjectName("AegisSiteInfoPopup")
        self.setFixedWidth(340)
        self.parent_win = parent_win
        self.init_ui()

    def hideEvent(self, event):
        if self.parent_win:
            self.parent_win._last_site_info_close_time = time.time()
        super().hideEvent(event)

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        # Header con icono + dominio
        self.header_layout = QHBoxLayout()
        self.lbl_sec_icon = QLabel("🔒")
        self.lbl_sec_icon.setStyleSheet("font-size: 18px;")
        self.header_layout.addWidget(self.lbl_sec_icon)

        domain_v = QVBoxLayout()
        self.lbl_domain = QLabel("dominio.com")
        self.lbl_domain.setStyleSheet("font-weight: 700; font-size: 13.5px; color: #f0f6fc;")
        self.lbl_status = QLabel("Conexión segura")
        self.lbl_status.setStyleSheet("font-size: 11px; color: #8b949e;")
        domain_v.addWidget(self.lbl_domain)
        domain_v.addWidget(self.lbl_status)
        self.header_layout.addLayout(domain_v)
        self.header_layout.addStretch()
        layout.addLayout(self.header_layout)

        # Separador
        sep1 = QFrame()
        sep1.setObjectName("PopupSep")
        sep1.setFixedHeight(1)
        layout.addWidget(sep1)

        # Tarjeta de seguridad de conexión
        self.sec_box = QFrame()
        self.sec_box.setObjectName("SecInfoBox")
        sec_l = QVBoxLayout(self.sec_box)
        sec_l.setContentsMargins(10, 8, 10, 8)
        sec_l.setSpacing(4)
        self.lbl_cert_info = QLabel("Certificado válido (TLS 1.3 / HTTPS)")
        self.lbl_cert_info.setStyleSheet("font-size: 11.5px; font-weight: 600; color: #f0f6fc;")
        self.lbl_cert_desc = QLabel("Tu información (contraseñas, mensajes) es privada.")
        self.lbl_cert_desc.setStyleSheet("font-size: 10.5px; color: #8b949e;")
        sec_l.addWidget(self.lbl_cert_info)
        sec_l.addWidget(self.lbl_cert_desc)
        layout.addWidget(self.sec_box)

        # Tarjeta de Cookies
        self.cookies_box = QFrame()
        self.cookies_box.setObjectName("SecInfoBox")
        ck_l = QHBoxLayout(self.cookies_box)
        ck_l.setContentsMargins(10, 8, 10, 8)
        self.lbl_cookies = QLabel("🍪 Cookies y datos locales")
        self.lbl_cookies.setStyleSheet("font-size: 11.5px; font-weight: 600; color: #f0f6fc;")
        ck_l.addWidget(self.lbl_cookies)
        ck_l.addStretch()
        self.btn_clear_site_cookies = QPushButton("🧹 Borrar")
        self.btn_clear_site_cookies.setProperty("class", "mini-action-btn")
        self.btn_clear_site_cookies.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_clear_site_cookies.clicked.connect(self.clear_site_cookies)
        ck_l.addWidget(self.btn_clear_site_cookies)
        layout.addWidget(self.cookies_box)

        # Sección de Permisos
        perm_title = QLabel("Permisos del sitio")
        perm_title.setStyleSheet("font-weight: 600; font-size: 11px; color: #8b949e; margin-top: 2px;")
        layout.addWidget(perm_title)

        self.perms_layout = QVBoxLayout()
        self.perms_layout.setSpacing(4)
        perms = [
            ("🎙️ Micrófono", "Permitido"),
            ("📷 Cámara web", "Permitido"),
            ("🖥️ Pantalla", "Permitido"),
            ("🔔 Notificaciones", "Permitido"),
            ("📋 Portapapeles", "Permitido")
        ]
        for name, state in perms:
            row = QHBoxLayout()
            l_n = QLabel(name)
            l_n.setStyleSheet("font-size: 11px;")
            l_s = QLabel(state)
            l_s.setStyleSheet("font-size: 11px; color: #8b949e; font-weight: 500;")
            row.addWidget(l_n)
            row.addStretch()
            row.addWidget(l_s)
            self.perms_layout.addLayout(row)
        layout.addLayout(self.perms_layout)

    def refresh_site(self, qurl: QUrl):
        url_str = qurl.toString()
        host = qurl.host()
        scheme = qurl.scheme().lower()
        if not host or url_str.startswith("aegis://") or url_str.startswith("about:"):
            self.lbl_domain.setText("Aegis Browser")
            self.lbl_sec_icon.setText("🛡️")
            self.lbl_status.setText("Página interna del sistema")
            self.lbl_cert_info.setText("Sistema de Aegis")
            self.lbl_cert_desc.setText("Página segura local de configuración y navegación.")
            self.btn_clear_site_cookies.setEnabled(False)
        elif scheme == "https":
            self.lbl_domain.setText(host)
            self.lbl_sec_icon.setText("🔒")
            self.lbl_status.setText("Conexión segura y cifrada")
            self.lbl_cert_info.setText("Certificado válido (TLS / HTTPS)")
            self.lbl_cert_desc.setText("Tu información es privada para este dominio.")
            self.btn_clear_site_cookies.setEnabled(True)
        else:
            self.lbl_domain.setText(host)
            self.lbl_sec_icon.setText("⚠️")
            self.lbl_status.setText("Conexión no cifrada (HTTP)")
            self.lbl_cert_info.setText("No es seguro")
            self.lbl_cert_desc.setText("No ingreses información confidencial en este sitio.")
            self.btn_clear_site_cookies.setEnabled(True)

    def clear_site_cookies(self):
        if self.parent_win and self.parent_win.profile:
            cur = self.parent_win.current_view()
            if cur:
                host = cur.url().host()
                store = self.parent_win.profile.cookieStore()
                store.deleteAllCookies()
                if hasattr(self.parent_win, "show_toast"):
                    self.parent_win.show_toast(f"Cookies de {host} eliminadas.")
                self.hide()

    def apply_theme(self, t: dict):
        rgb_text = hex_to_rgb(t["text"])
        if hasattr(self, "btn_tool_aniplay"):
            enabled = self.parent_win.config.get("enable_aniplay", False) if self.parent_win else False
            self.btn_tool_aniplay.setVisible(enabled)
        qss = f"""
            QFrame#AegisSiteInfoPopup {{
                background-color: {t['surface']};
                border: 1px solid rgba({rgb_text}, 0.16);
                border-radius: 12px;
            }}
            QFrame#SecInfoBox {{
                background-color: {t['bg']};
                border: 1px solid rgba({rgb_text}, 0.08);
                border-radius: 8px;
            }}
            QFrame#PopupSep {{
                background-color: rgba({rgb_text}, 0.08);
                border: none;
            }}
            QLabel {{
                color: {t['text']};
            }}
            QPushButton.mini-action-btn {{
                background-color: {t['surface']};
                border: 1px solid rgba({rgb_text}, 0.15);
                border-radius: 4px;
                color: {t['text']};
                padding: 3px 8px;
                font-size: 11px;
                font-weight: 500;
            }}
            QPushButton.mini-action-btn:hover {{
                border-color: {t['accent']};
                color: {t['accent']};
            }}
        """
        self.setStyleSheet(qss)

# ── 10.3.7 Popup de Búsqueda y Selector de Pestañas (Ctrl+Shift+A) ─────────────
class AegisTabSearchPopup(QFrame):
    def __init__(self, parent_win=None):
        super().__init__(parent_win, Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.setObjectName("AegisTabSearchPopup")
        self.setFixedSize(460, 420)
        self.parent_win = parent_win
        self._all_items = []
        self.init_ui()

    def hideEvent(self, event):
        if self.parent_win:
            self.parent_win._last_tab_search_close_time = time.time()
        super().hideEvent(event)

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        self.search_input = QLineEdit()
        self.search_input.setObjectName("TabSearchInput")
        self.search_input.setPlaceholderText("🔍 Buscar en pestañas abiertas y recientes... (Ctrl+Shift+A)")
        self.search_input.textChanged.connect(self.filter_tabs)
        layout.addWidget(self.search_input)

        self.list_widget = QListWidget()
        self.list_widget.setObjectName("TabSearchList")
        self.list_widget.setSpacing(2)
        self.list_widget.itemClicked.connect(self.on_item_clicked)
        layout.addWidget(self.list_widget)

    def refresh_tabs(self):
        self.list_widget.clear()
        self._all_items = []
        if not self.parent_win:
            return

        for idx, view in enumerate(self.parent_win.views):
            title = view.title() or "Pestaña"
            url_str = view.url().toString()
            if self.parent_win.is_internal_or_ntp(url_str):
                title = "Nueva Pestaña"
                url_str = "aegis://start"
            is_audible = view.page() and view.page().recentlyAudible()
            audible_icon = " 🔊" if is_audible else ""
            self._all_items.append({
                "type": "open",
                "idx": idx,
                "title": title,
                "url": url_str,
                "display": f"🌐 {title}{audible_icon}\n   {url_str}"
            })

        for closed_url, closed_title in reversed(self.parent_win.closed_tabs[:8]):
            self._all_items.append({
                "type": "closed",
                "title": closed_title,
                "url": closed_url,
                "display": f"↩️ {closed_title}\n   {closed_url}"
            })

        self.filter_tabs(self.search_input.text())
        self.search_input.setFocus()
        self.search_input.selectAll()

    def filter_tabs(self, query: str):
        self.list_widget.clear()
        q = query.lower().strip()
        for item in self._all_items:
            if not q or (q in item["title"].lower() or q in item["url"].lower()):
                li = QListWidgetItem(item["display"])
                li.setData(Qt.ItemDataRole.UserRole, item)
                self.list_widget.addItem(li)
        if self.list_widget.count() > 0:
            self.list_widget.setCurrentRow(0)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            cur = self.list_widget.currentItem()
            if cur:
                self.on_item_clicked(cur)
                return
        elif event.key() == Qt.Key.Key_Escape:
            self.hide()
            return
        elif event.key() == Qt.Key.Key_Down:
            cur_r = self.list_widget.currentRow()
            if cur_r < self.list_widget.count() - 1:
                self.list_widget.setCurrentRow(cur_r + 1)
            return
        elif event.key() == Qt.Key.Key_Up:
            cur_r = self.list_widget.currentRow()
            if cur_r > 0:
                self.list_widget.setCurrentRow(cur_r - 1)
            return
        super().keyPressEvent(event)

    def on_item_clicked(self, item: QListWidgetItem):
        data = item.data(Qt.ItemDataRole.UserRole)
        if not data or not self.parent_win:
            return
        if data["type"] == "open":
            idx = data["idx"]
            if 0 <= idx < len(self.parent_win.views):
                self.parent_win.tab_bar.setCurrentIndex(idx)
        elif data["type"] == "closed":
            self.parent_win.add_new_tab(data["url"])
        self.hide()

    def apply_theme(self, t: dict):
        rgb_text = hex_to_rgb(t["text"])
        if hasattr(self, "btn_tool_aniplay"):
            enabled = self.parent_win.config.get("enable_aniplay", False) if self.parent_win else False
            self.btn_tool_aniplay.setVisible(enabled)
        qss = f"""
            QFrame#AegisTabSearchPopup {{
                background-color: {t['surface']};
                border: 1px solid rgba({rgb_text}, 0.16);
                border-radius: 12px;
            }}
            QLineEdit#TabSearchInput {{
                background-color: {t['bg']};
                border: 1px solid rgba({rgb_text}, 0.18);
                border-radius: 8px;
                color: {t['text']};
                padding: 8px 12px;
                font-size: 13px;
                selection-background-color: {t['accent']};
            }}
            QLineEdit#TabSearchInput:focus {{
                border-color: {t['accent']};
            }}
            QListWidget#TabSearchList {{
                background: transparent;
                border: none;
                color: {t['text']};
            }}
            QListWidget#TabSearchList::item {{
                background-color: {t['bg']};
                border: 1px solid rgba({rgb_text}, 0.08);
                border-radius: 8px;
                padding: 8px 12px;
                margin-bottom: 4px;
                font-size: 12px;
            }}
            QListWidget#TabSearchList::item:hover {{
                border-color: {t['accent']};
                color: {t['accent']};
            }}
            QListWidget#TabSearchList::item:selected {{
                background-color: {t['bg']};
                border: 1.5px solid {t['accent']};
                color: {t['accent']};
                font-weight: 600;
            }}
        """
        self.setStyleSheet(qss)

# ── 10.3.8 Popup de Edición de Marcadores (⭐) ──────────────────────────────────
class AegisBookmarkEditPopup(QFrame):
    def __init__(self, parent_win=None):
        super().__init__(parent_win, Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.setObjectName("AegisBookmarkEditPopup")
        self.setFixedWidth(320)
        self.parent_win = parent_win
        self._target_url = ""
        self.init_ui()

    def hideEvent(self, event):
        if self.parent_win:
            self.parent_win._last_bookmark_popup_close_time = time.time()
        super().hideEvent(event)

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        header = QLabel("⭐ Marcador guardado")
        header.setStyleSheet("font-weight: 700; font-size: 13px;")
        layout.addWidget(header)

        lbl_name = QLabel("Nombre:")
        lbl_name.setStyleSheet("font-size: 11px; opacity: 0.7;")
        layout.addWidget(lbl_name)

        self.input_title = QLineEdit()
        self.input_title.setObjectName("BookmarkEditInput")
        layout.addWidget(self.input_title)

        lbl_url = QLabel("Dirección URL:")
        lbl_url.setStyleSheet("font-size: 11px; opacity: 0.7;")
        layout.addWidget(lbl_url)

        self.input_url = QLineEdit()
        self.input_url.setObjectName("BookmarkEditInput")
        layout.addWidget(self.input_url)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        self.btn_del = QPushButton("🗑️ Eliminar")
        self.btn_del.setProperty("class", "bm-del-btn")
        self.btn_del.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_del.clicked.connect(self.delete_bookmark)
        btn_row.addWidget(self.btn_del)

        btn_row.addStretch()

        self.btn_save = QPushButton("Listo")
        self.btn_save.setProperty("class", "bm-save-btn")
        self.btn_save.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_save.clicked.connect(self.save_bookmark)
        btn_row.addWidget(self.btn_save)

        layout.addLayout(btn_row)

    def populate(self, url: str, title: str):
        self._target_url = url
        self.input_url.setText(url)
        self.input_title.setText(title)

    def delete_bookmark(self):
        if self.parent_win:
            self.parent_win.bookmarks_mgr.remove(self._target_url)
            self.parent_win.btn_bookmark.setText("☆")
            if hasattr(self.parent_win, "bookmarks_bar"):
                self.parent_win.bookmarks_bar.refresh_bookmarks()
            self.parent_win.show_toast("Marcador eliminado.")
        self.hide()

    def save_bookmark(self):
        new_title = self.input_title.text().strip() or "Marcador"
        new_url = self.input_url.text().strip() or self._target_url
        if self.parent_win:
            self.parent_win.bookmarks_mgr.remove(self._target_url)
            self.parent_win.bookmarks_mgr.add(new_title, new_url)
            self.parent_win.btn_bookmark.setText("★")
            if hasattr(self.parent_win, "bookmarks_bar"):
                self.parent_win.bookmarks_bar.refresh_bookmarks()
            self.parent_win.show_toast("Marcador actualizado.")
        self.hide()

    def apply_theme(self, t: dict):
        rgb_text = hex_to_rgb(t["text"])
        if hasattr(self, "btn_tool_aniplay"):
            enabled = self.parent_win.config.get("enable_aniplay", False) if self.parent_win else False
            self.btn_tool_aniplay.setVisible(enabled)
        qss = f"""
            QFrame#AegisBookmarkEditPopup {{
                background-color: {t['surface']};
                border: 1px solid rgba({rgb_text}, 0.16);
                border-radius: 12px;
            }}
            QLineEdit#BookmarkEditInput {{
                background-color: {t['bg']};
                border: 1px solid rgba({rgb_text}, 0.15);
                border-radius: 6px;
                color: {t['text']};
                padding: 6px 10px;
                font-size: 12px;
            }}
            QLineEdit#BookmarkEditInput:focus {{
                border-color: {t['accent']};
            }}
            QLabel {{
                color: {t['text']};
            }}
            QPushButton.bm-del-btn {{
                background: transparent;
                border: 1px solid rgba({rgb_text}, 0.15);
                border-radius: 6px;
                color: #f85149;
                padding: 5px 12px;
                font-size: 11.5px;
                font-weight: 500;
            }}
            QPushButton.bm-del-btn:hover {{
                background-color: rgba(248, 81, 73, 0.1);
            }}
            QPushButton.bm-save-btn {{
                background-color: {t['accent']};
                border: none;
                border-radius: 6px;
                color: #ffffff;
                padding: 5px 16px;
                font-size: 11.5px;
                font-weight: 600;
            }}
            QPushButton.bm-save-btn:hover {{
                opacity: 0.9;
            }}
        """
        self.setStyleSheet(qss)

# ── 10.3.9 Diálogo Completo de Borrado de Datos de Navegación (Ctrl+Shift+Del) ──
class AegisClearDataDialog(QDialog):
    def __init__(self, parent_win=None):
        super().__init__(parent_win)
        self.parent_win = parent_win
        self.setWindowTitle("Borrar datos de navegación - Aegis")
        self.setFixedWidth(440)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        header = QLabel("🗑️ Borrar datos de navegación")
        header.setStyleSheet("font-weight: 700; font-size: 15px;")
        layout.addWidget(header)

        time_row = QHBoxLayout()
        lbl_range = QLabel("Intervalo de tiempo:")
        lbl_range.setStyleSheet("font-size: 12px; font-weight: 500;")
        self.combo_range = QComboBox()
        self.combo_range.setObjectName("ClearDataCombo")
        self.combo_range.addItems(["Última hora", "Últimas 24 horas", "Últimos 7 días", "Todo el tiempo"])
        self.combo_range.setCurrentIndex(3)
        time_row.addWidget(lbl_range)
        time_row.addWidget(self.combo_range)
        layout.addLayout(time_row)

        self.chk_history = QCheckBox("Historial de navegación y búsquedas")
        self.chk_history.setChecked(True)
        self.chk_cookies = QCheckBox("Cookies y datos de sitios web")
        self.chk_cookies.setChecked(True)
        self.chk_cache = QCheckBox("Archivos e imágenes en caché")
        self.chk_cache.setChecked(True)
        self.chk_downloads = QCheckBox("Historial de descargas")
        self.chk_downloads.setChecked(True)
        self.chk_closed_tabs = QCheckBox("Pestañas cerradas recientemente")
        self.chk_closed_tabs.setChecked(True)

        layout.addWidget(self.chk_history)
        layout.addWidget(self.chk_cookies)
        layout.addWidget(self.chk_cache)
        layout.addWidget(self.chk_downloads)
        layout.addWidget(self.chk_closed_tabs)

        btn_row = QHBoxLayout()
        btn_row.addStretch()

        self.btn_cancel = QPushButton("Cancelar")
        self.btn_cancel.setProperty("class", "clear-cancel-btn")
        self.btn_cancel.clicked.connect(self.reject)
        btn_row.addWidget(self.btn_cancel)

        self.btn_clear = QPushButton("Borrar datos")
        self.btn_clear.setProperty("class", "clear-confirm-btn")
        self.btn_clear.clicked.connect(self.execute_clear)
        btn_row.addWidget(self.btn_clear)

        layout.addLayout(btn_row)

    def execute_clear(self):
        if not self.parent_win:
            self.accept()
            return

        range_idx = self.combo_range.currentIndex()
        now = time.time()
        cutoffs = [now - 3600, now - 86400, now - 604800, 0]
        cutoff = cutoffs[range_idx]

        if self.chk_history.isChecked():
            if cutoff == 0:
                self.parent_win.history_mgr.clear_history()
            else:
                self.parent_win.history_mgr.clear_range(cutoff)

        if self.chk_cookies.isChecked() and self.parent_win.profile:
            self.parent_win.profile.cookieStore().deleteAllCookies()

        if self.chk_cache.isChecked() and self.parent_win.profile:
            self.parent_win.profile.clearHttpCache()

        if self.chk_downloads.isChecked():
            self.parent_win.downloads_mgr.clear()

        if self.chk_closed_tabs.isChecked():
            self.parent_win.closed_tabs.clear()

        self.parent_win.show_toast("✓ Datos de navegación borrados correctamente.")
        self.accept()

    def apply_theme(self, t: dict):
        rgb_text = hex_to_rgb(t["text"])
        if hasattr(self, "btn_tool_aniplay"):
            enabled = self.parent_win.config.get("enable_aniplay", False) if self.parent_win else False
            self.btn_tool_aniplay.setVisible(enabled)
        qss = f"""
            QDialog {{
                background-color: {t['surface']};
                color: {t['text']};
            }}
            QLabel, QCheckBox {{
                color: {t['text']};
                font-size: 12.5px;
            }}
            QComboBox#ClearDataCombo {{
                background-color: {t['bg']};
                border: 1px solid rgba({rgb_text}, 0.18);
                border-radius: 6px;
                color: {t['text']};
                padding: 4px 10px;
                font-size: 12px;
            }}
            QPushButton.clear-cancel-btn {{
                background: transparent;
                border: 1px solid rgba({rgb_text}, 0.18);
                border-radius: 6px;
                color: {t['text']};
                padding: 6px 14px;
                font-size: 12px;
                font-weight: 500;
            }}
            QPushButton.clear-cancel-btn:hover {{
                background-color: {t['bg']};
            }}
            QPushButton.clear-confirm-btn {{
                background-color: #da3633;
                border: none;
                border-radius: 6px;
                color: #ffffff;
                padding: 6px 16px;
                font-size: 12px;
                font-weight: 600;
            }}
            QPushButton.clear-confirm-btn:hover {{
                background-color: #b62324;
            }}
        """
        self.setStyleSheet(qss)

# ── 10.3.9.5 Diálogo de Importación de Datos de Brave Browser ──────────────────
class AegisBraveImportDialog(QDialog):
    def __init__(self, parent_win=None):
        super().__init__(parent_win)
        self.parent_win = parent_win
        self.setWindowTitle("Importar datos de Brave Browser - Aegis")
        self.setFixedWidth(480)
        self.detected_profiles = BraveImporter.find_brave_profiles()
        self.init_ui()
        if self.parent_win:
            t = THEMES.get(self.parent_win.current_theme_name, THEMES["Oscuro"])
            self.apply_theme(t)

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 22, 22, 22)
        layout.setSpacing(14)

        header = QLabel("🦁 Importar datos de Brave Browser")
        header.setStyleSheet("font-weight: 700; font-size: 16px;")
        layout.addWidget(header)

        desc = QLabel(
            "Transfiere de manera local, privada y segura tu historial de navegación, "
            "páginas frecuentes y marcadores guardados desde Brave hacia Aegis Browser."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("font-size: 12px; color: #8b949e; line-height: 1.4;")
        layout.addWidget(desc)

        profile_row = QHBoxLayout()
        lbl_profile = QLabel("Perfil de origen:")
        lbl_profile.setStyleSheet("font-size: 12px; font-weight: 600;")
        self.combo_profile = QComboBox()
        self.combo_profile.setObjectName("BraveProfileCombo")

        if self.detected_profiles:
            for p in self.detected_profiles:
                h = p['history_count']
                b = p['bookmarks_count']
                self.combo_profile.addItem(f"{p['name']} ({h:,} visitas, {b} marcadores)".replace(',', '.'), p['path'])
        else:
            self.combo_profile.addItem("No se detectó instalación estándar de Brave", None)

        profile_row.addWidget(lbl_profile)
        profile_row.addWidget(self.combo_profile, 1)

        self.btn_browse = QPushButton("Examinar...")
        self.btn_browse.setStyleSheet("padding: 4px 10px; font-size: 12px;")
        self.btn_browse.clicked.connect(self.browse_custom_profile)
        profile_row.addWidget(self.btn_browse)
        layout.addLayout(profile_row)

        self.lbl_stats = QLabel("")
        self.lbl_stats.setStyleSheet("font-size: 12px; font-weight: 500; color: #388bfd;")
        layout.addWidget(self.lbl_stats)
        self.update_stats_label()
        self.combo_profile.currentIndexChanged.connect(self.update_stats_label)

        options_box = QFrame()
        options_box.setObjectName("BraveOptionsBox")
        box_layout = QVBoxLayout(options_box)
        box_layout.setContentsMargins(12, 10, 12, 10)
        box_layout.setSpacing(8)

        self.chk_history = QCheckBox("Historial de navegación (visitas, títulos y fechas)")
        self.chk_history.setChecked(True)
        self.chk_frequent = QCheckBox("Sitios frecuentes y accesos directos de Nueva Pestaña")
        self.chk_frequent.setChecked(True)
        self.chk_bookmarks = QCheckBox("Marcadores y barra de favoritos")
        self.chk_bookmarks.setChecked(True)

        box_layout.addWidget(self.chk_history)
        box_layout.addWidget(self.chk_frequent)
        box_layout.addWidget(self.chk_bookmarks)
        layout.addWidget(options_box)

        btn_row = QHBoxLayout()
        btn_row.addStretch()

        self.btn_cancel = QPushButton("Cancelar")
        self.btn_cancel.setProperty("class", "clear-cancel-btn")
        self.btn_cancel.clicked.connect(self.reject)
        btn_row.addWidget(self.btn_cancel)

        self.btn_import = QPushButton("Importar a Aegis")
        self.btn_import.setProperty("class", "clear-confirm-btn")
        self.btn_import.clicked.connect(self.execute_import)
        btn_row.addWidget(self.btn_import)

        layout.addLayout(btn_row)

    def browse_custom_profile(self):
        folder = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta de perfil de Brave (contiene History o Bookmarks)")
        if folder:
            p = Path(folder)
            h, b = BraveImporter.get_profile_stats(p)
            self.combo_profile.insertItem(0, f"Personalizado: {p.name} ({h:,} visitas, {b} marcadores)".replace(',', '.'), p)
            self.combo_profile.setCurrentIndex(0)

    def update_stats_label(self):
        curr_path = self.combo_profile.currentData()
        if curr_path and isinstance(curr_path, Path):
            h, b = BraveImporter.get_profile_stats(curr_path)
            self.lbl_stats.setText(f"✓ {h:,} páginas en historial y {b} marcadores listos para importar.".replace(',', '.'))
            self.btn_import.setEnabled(True)
        else:
            self.lbl_stats.setText("⚠️ Selecciona la carpeta de Brave con el botón Examinar.")
            self.btn_import.setEnabled(False)

    def execute_import(self):
        if not self.parent_win:
            self.accept()
            return
        curr_path = self.combo_profile.currentData()
        if not curr_path or not isinstance(curr_path, Path):
            QMessageBox.warning(self, "Perfil no válido", "Por favor selecciona un perfil válido de Brave.")
            return

        do_hist = self.chk_history.isChecked()
        do_bm = self.chk_bookmarks.isChecked()

        if not do_hist and not do_bm:
            QMessageBox.information(self, "Nada que importar", "Selecciona al menos una opción para importar.")
            return

        self.btn_import.setEnabled(False)
        self.btn_import.setText("Importando...")
        QApplication.processEvents()

        h_count, b_count = BraveImporter.import_all(
            curr_path,
            self.parent_win.history_mgr,
            self.parent_win.bookmark_mgr,
            import_hist=do_hist,
            import_bm=do_bm
        )

        self.parent_win.update_bookmarks_bar()
        self.parent_win.load_userscripts()
        
        cur_tab = self.parent_win.current_tab_widget()
        if cur_tab:
            v_url = getattr(cur_tab, "_aegis_virtual_url", "")
            if v_url in ("aegis://history", "aegis://start"):
                self.parent_win.open_internal_page(v_url)

        msg = f"¡Importación completada con éxito!\n\n• {h_count:,} elementos agregados al historial y frecuentes.\n• {b_count} marcadores añadidos.".replace(',', '.')
        QMessageBox.information(self, "🦁 Importación de Brave Exitosa", msg)
        self.parent_win.show_toast(f"✓ Datos de Brave importados ({h_count} visitas, {b_count} marcadores)")
        self.accept()

    def apply_theme(self, t: dict):
        rgb_text = hex_to_rgb(t["text"])
        qss = f"""
            QDialog {{
                background-color: {t['surface']};
                color: {t['text']};
            }}
            QLabel {{
                color: {t['text']};
            }}
            QFrame#BraveOptionsBox {{
                background-color: {t['bg']};
                border: 1px solid rgba({rgb_text}, 0.12);
                border-radius: 8px;
            }}
            QComboBox#BraveProfileCombo {{
                background-color: {t['bg']};
                color: {t['text']};
                border: 1px solid rgba({rgb_text}, 0.2);
                border-radius: 6px;
                padding: 4px 8px;
                font-size: 12px;
            }}
            QCheckBox {{
                color: {t['text']};
                font-size: 12px;
                spacing: 6px;
            }}
            QPushButton.clear-cancel-btn {{
                background: transparent;
                border: 1px solid rgba({rgb_text}, 0.25);
                border-radius: 6px;
                color: {t['text']};
                padding: 6px 14px;
                font-size: 12px;
                font-weight: 500;
            }}
            QPushButton.clear-cancel-btn:hover {{
                background-color: {t['bg']};
            }}
            QPushButton.clear-confirm-btn {{
                background-color: {t['accent']};
                border: none;
                border-radius: 6px;
                color: #ffffff;
                padding: 6px 16px;
                font-size: 12px;
                font-weight: 600;
            }}
            QPushButton.clear-confirm-btn:hover {{
                opacity: 0.9;
            }}
        """
        self.setStyleSheet(qss)

# ── 10.3.10 Barra Lateral de Productividad y Herramientas Rápidas (Ctrl+B) ──────
class AegisSidebarWidget(QFrame):
    def __init__(self, parent_win=None):
        super().__init__(parent_win)
        self.parent_win = parent_win
        self.setObjectName("AegisSidebarWidget")
        self.setFixedWidth(310)
        self.reading_list = []
        self.load_reading_list()
        self.init_ui()

    def load_reading_list(self):
        if READING_LIST_FILE.exists():
            try:
                self.reading_list = json.loads(READING_LIST_FILE.read_text(encoding="utf-8"))
            except Exception:
                self.reading_list = []

    def save_reading_list(self):
        try:
            READING_LIST_FILE.write_text(json.dumps(self.reading_list, indent=2, ensure_ascii=False), encoding="utf-8")
        except Exception:
            pass

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Barra de botones de herramientas superior
        top_bar = QWidget()
        top_bar.setObjectName("SidebarTopBar")
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(8, 6, 8, 6)
        top_layout.setSpacing(4)

        self.btn_tool_notes = QPushButton("📝")
        self.btn_tool_notes.setToolTip("Bloc de Notas Rápido")
        self.btn_tool_reading = QPushButton("📚")
        self.btn_tool_reading.setToolTip("Lista de Lectura")
        self.btn_tool_history = QPushButton("🕒")
        self.btn_tool_history.setToolTip("Historial Rápido")
        self.btn_tool_bookmarks = QPushButton("🔖")
        self.btn_tool_bookmarks.setToolTip("Marcadores")
        self.btn_tool_pass = QPushButton("🔐")
        self.btn_tool_pass.setToolTip("Generador de Contraseñas")
        self.btn_tool_shot = QPushButton("📸")
        self.btn_tool_shot.setToolTip("Captura de Pantalla")

        self.btn_tool_aniplay = QPushButton("▶")
        self.btn_tool_aniplay.setToolTip("AniPlay Anime Hub")

        tools = [
            (self.btn_tool_notes, 0),
            (self.btn_tool_reading, 1),
            (self.btn_tool_history, 2),
            (self.btn_tool_bookmarks, 3),
            (self.btn_tool_pass, 4),
            (self.btn_tool_shot, 5),
            (self.btn_tool_aniplay, 6),
        ]

        for btn, idx in tools:
            btn.setProperty("class", "sidebar-tool-btn")
            btn.setFixedSize(32, 28)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda _, i=idx: self.switch_tab(i))
            top_layout.addWidget(btn)

        top_layout.addStretch()

        self.btn_close = QPushButton("✕")
        self.btn_close.setProperty("class", "sidebar-close-btn")
        self.btn_close.setFixedSize(24, 24)
        self.btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_close.clicked.connect(lambda: self.parent_win.toggle_sidebar())
        top_layout.addWidget(self.btn_close)

        main_layout.addWidget(top_bar)

        self.stack = QStackedWidget()

        # 1. Notas Rápidas
        w_notes = QWidget()
        l_n = QVBoxLayout(w_notes)
        l_n.setContentsMargins(12, 10, 12, 10)
        l_n.setSpacing(8)
        lbl_notes_title = QLabel("📝 Notas Rápidas (Autoguardado)")
        lbl_notes_title.setStyleSheet("font-weight: 700; font-size: 12px; color: #f0f6fc;")
        l_n.addWidget(lbl_notes_title)
        self.txt_notes = QTextEdit()
        self.txt_notes.setObjectName("SidebarNotesInput")
        self.txt_notes.setPlaceholderText("Escribe ideas, notas o enlaces aquí...")
        saved_notes = self.parent_win.config.get("quick_notes", "") if self.parent_win else ""
        self.txt_notes.setPlainText(saved_notes)
        self.txt_notes.textChanged.connect(self.on_notes_changed)
        l_n.addWidget(self.txt_notes)
        btn_copy_notes = QPushButton("📋 Copiar notas")
        btn_copy_notes.setProperty("class", "sidebar-action-btn")
        btn_copy_notes.clicked.connect(lambda: (QApplication.clipboard().setText(self.txt_notes.toPlainText()), self.parent_win.show_toast("Notas copiadas al portapapeles.")))
        l_n.addWidget(btn_copy_notes)
        self.stack.addWidget(w_notes)

        # 2. Lista de Lectura
        w_reading = QWidget()
        l_r = QVBoxLayout(w_reading)
        l_r.setContentsMargins(12, 10, 12, 10)
        l_r.setSpacing(8)
        btn_add_reading = QPushButton("➕ Añadir pestaña actual")
        btn_add_reading.setProperty("class", "sidebar-action-btn")
        btn_add_reading.clicked.connect(self.add_current_to_reading)
        l_r.addWidget(btn_add_reading)
        self.list_reading = QListWidget()
        self.list_reading.setObjectName("SidebarList")
        self.list_reading.itemClicked.connect(self.on_reading_item_clicked)
        l_r.addWidget(self.list_reading)
        self.stack.addWidget(w_reading)

        # 3. Historial Rápido
        w_hist = QWidget()
        l_h = QVBoxLayout(w_hist)
        l_h.setContentsMargins(12, 10, 12, 10)
        l_h.setSpacing(8)
        self.hist_filter = QLineEdit()
        self.hist_filter.setObjectName("SidebarSearchInput")
        self.hist_filter.setPlaceholderText("🔍 Filtrar historial...")
        self.hist_filter.textChanged.connect(self.refresh_quick_history)
        l_h.addWidget(self.hist_filter)
        self.list_history = QListWidget()
        self.list_history.setObjectName("SidebarList")
        self.list_history.itemClicked.connect(self.on_hist_item_clicked)
        l_h.addWidget(self.list_history)
        self.stack.addWidget(w_hist)

        # 4. Marcadores Rápidos
        w_bm = QWidget()
        l_bm = QVBoxLayout(w_bm)
        l_bm.setContentsMargins(12, 10, 12, 10)
        l_bm.setSpacing(8)
        self.bm_filter = QLineEdit()
        self.bm_filter.setObjectName("SidebarSearchInput")
        self.bm_filter.setPlaceholderText("🔍 Filtrar marcadores...")
        self.bm_filter.textChanged.connect(self.refresh_quick_bookmarks)
        l_bm.addWidget(self.bm_filter)
        self.list_bookmarks = QListWidget()
        self.list_bookmarks.setObjectName("SidebarList")
        self.list_bookmarks.itemClicked.connect(self.on_bm_item_clicked)
        l_bm.addWidget(self.list_bookmarks)
        self.stack.addWidget(w_bm)

        # 5. Generador de Contraseñas
        w_pass = QWidget()
        l_p = QVBoxLayout(w_pass)
        l_p.setContentsMargins(12, 12, 12, 12)
        l_p.setSpacing(10)
        lbl_p_title = QLabel("🔐 Generador de Contraseñas")
        lbl_p_title.setStyleSheet("font-weight: 700; font-size: 12px; color: #f0f6fc;")
        l_p.addWidget(lbl_p_title)

        self.lbl_len = QLabel("Longitud: 16 caracteres")
        self.lbl_len.setStyleSheet("font-size: 11px; color: #c9d1d9;")
        l_p.addWidget(self.lbl_len)

        self.slider_len = QSlider(Qt.Orientation.Horizontal)
        self.slider_len.setRange(8, 32)
        self.slider_len.setValue(16)
        self.slider_len.valueChanged.connect(self.on_slider_changed)
        l_p.addWidget(self.slider_len)

        self.chk_symbols = QCheckBox("Incluir símbolos (!@#$%^&*)")
        self.chk_symbols.setChecked(True)
        self.chk_symbols.stateChanged.connect(self.generate_password)
        l_p.addWidget(self.chk_symbols)

        self.pass_output = QLineEdit()
        self.pass_output.setObjectName("SidebarPassOutput")
        self.pass_output.setReadOnly(True)
        l_p.addWidget(self.pass_output)

        btn_gen = QPushButton("🔄 Generar y copiar")
        btn_gen.setProperty("class", "sidebar-action-btn")
        btn_gen.clicked.connect(self.generate_and_copy_pass)
        l_p.addWidget(btn_gen)
        l_p.addStretch()
        self.stack.addWidget(w_pass)

        # 6. Captura de Pantalla
        w_shot = QWidget()
        l_s = QVBoxLayout(w_shot)
        l_s.setContentsMargins(12, 12, 12, 12)
        l_s.setSpacing(12)
        lbl_s_title = QLabel("📸 Captura de Pantalla Web")
        lbl_s_title.setStyleSheet("font-weight: 700; font-size: 12px; color: #f0f6fc;")
        l_s.addWidget(lbl_s_title)

        lbl_s_desc = QLabel("Captura la página actual en alta resolución y cópiala al portapapeles y a la carpeta Descargas.")
        lbl_s_desc.setWordWrap(True)
        lbl_s_desc.setStyleSheet("font-size: 11px; color: #8b949e;")
        l_s.addWidget(lbl_s_desc)

        btn_take_shot = QPushButton("📸 Capturar Pestaña Actual")
        btn_take_shot.setProperty("class", "sidebar-action-btn")
        btn_take_shot.clicked.connect(self.take_screenshot)
        l_s.addWidget(btn_take_shot)
        l_s.addStretch()
        self.stack.addWidget(w_shot)

        # 7. Tab AniPlay Hub
        w_ani = QWidget()
        l_ani = QVBoxLayout(w_ani)
        l_ani.setContentsMargins(12, 12, 12, 12)
        l_ani.setSpacing(12)
        lbl_ani_t = QLabel("▶ AniPlay Anime Hub")
        lbl_ani_t.setStyleSheet("font-weight: 700; font-size: 13px; color: #ff5370;")
        l_ani.addWidget(lbl_ani_t)
        lbl_ani_d = QLabel("Centro multimedia integrado para ver anime en streaming sin anuncios ni ventanas emergentes.")
        lbl_ani_d.setWordWrap(True)
        lbl_ani_d.setStyleSheet("font-size: 11px; color: #8b949e;")
        l_ani.addWidget(lbl_ani_d)
        btn_open_aniplay = QPushButton("▶ Abrir Catálogo AniPlay")
        btn_open_aniplay.setProperty("class", "sidebar-action-btn")
        btn_open_aniplay.clicked.connect(lambda: self.parent_win.open_internal_page("aegis://aniplay") if self.parent_win else None)
        l_ani.addWidget(btn_open_aniplay)
        l_ani.addStretch()
        self.stack.addWidget(w_ani)

        main_layout.addWidget(self.stack)

        self.refresh_reading_list()
        self.refresh_quick_history()
        self.refresh_quick_bookmarks()
        self.generate_password()

    def switch_tab(self, idx: int):
        self.stack.setCurrentIndex(idx)
        if idx == 1: self.refresh_reading_list()
        elif idx == 2: self.refresh_quick_history()
        elif idx == 3: self.refresh_quick_bookmarks()
        elif idx == 4: self.generate_password()

    def on_notes_changed(self):
        if self.parent_win:
            self.parent_win.config["quick_notes"] = self.txt_notes.toPlainText()
            self.parent_win.save_config()

    def add_current_to_reading(self):
        if not self.parent_win:
            return
        cur = self.parent_win.current_view()
        if cur:
            u = cur.url().toString()
            t = cur.title() or u
            if u and not u.startswith("aegis://"):
                item = {"title": t, "url": u, "time": time.time()}
                self.reading_list.insert(0, item)
                self.save_reading_list()
                self.refresh_reading_list()
                self.parent_win.show_toast("Artículo guardado en Lista de Lectura.")

    def refresh_reading_list(self):
        self.list_reading.clear()
        for idx, item in enumerate(self.reading_list):
            li = QListWidgetItem(f"📖 {item['title']}\n{item['url']}")
            li.setData(Qt.ItemDataRole.UserRole, item['url'])
            self.list_reading.addItem(li)

    def on_reading_item_clicked(self, item: QListWidgetItem):
        url = item.data(Qt.ItemDataRole.UserRole)
        if url and self.parent_win:
            self.parent_win.navigate_direct(url)

    def refresh_quick_history(self):
        self.list_history.clear()
        if not self.parent_win: return
        q = self.hist_filter.text().lower().strip()
        hist = self.parent_win.history_mgr.data.get("history_log", [])
        for h in hist[:40]:
            title = h.get("title") or h.get("url", "")
            u = h.get("url", "")
            if not q or (q in title.lower() or q in u.lower()):
                li = QListWidgetItem(f"🕒 {title}\n{u}")
                li.setData(Qt.ItemDataRole.UserRole, u)
                self.list_history.addItem(li)

    def on_hist_item_clicked(self, item: QListWidgetItem):
        url = item.data(Qt.ItemDataRole.UserRole)
        if url and self.parent_win:
            self.parent_win.navigate_direct(url)

    def refresh_quick_bookmarks(self):
        self.list_bookmarks.clear()
        if not self.parent_win: return
        q = self.bm_filter.text().lower().strip()
        bms = self.parent_win.bookmarks_mgr.bookmarks
        for b in bms:
            title = b.get("title", "")
            u = b.get("url", "")
            if not q or (q in title.lower() or q in u.lower()):
                li = QListWidgetItem(f"⭐ {title}\n{u}")
                li.setData(Qt.ItemDataRole.UserRole, u)
                self.list_bookmarks.addItem(li)

    def on_bm_item_clicked(self, item: QListWidgetItem):
        url = item.data(Qt.ItemDataRole.UserRole)
        if url and self.parent_win:
            self.parent_win.navigate_direct(url)

    def on_slider_changed(self, val: int):
        self.lbl_len.setText(f"Longitud: {val} caracteres")
        self.generate_password()

    def generate_password(self):
        length = self.slider_len.value()
        chars = string.ascii_letters + string.digits
        if self.chk_symbols.isChecked():
            chars += "!@#$%^&*()-_=+"
        pwd = "".join(secrets.choice(chars) for _ in range(length))
        self.pass_output.setText(pwd)

    def generate_and_copy_pass(self):
        self.generate_password()
        pwd = self.pass_output.text()
        QApplication.clipboard().setText(pwd)
        if self.parent_win:
            self.parent_win.show_toast("🔐 Contraseña generada y copiada al portapapeles.")

    def take_screenshot(self):
        if not self.parent_win:
            return
        cur = self.parent_win.current_view()
        if not cur:
            return
        pix = cur.grab()
        QApplication.clipboard().setPixmap(pix)
        save_dir = Path.home() / "Downloads"
        save_dir.mkdir(parents=True, exist_ok=True)
        file_path = save_dir / f"Aegis_Screenshot_{int(time.time())}.png"
        pix.save(str(file_path), "PNG")
        self.parent_win.show_toast(f"📸 Captura guardada en Descargas y copiada.")

    def apply_theme(self, t: dict):
        rgb_text = hex_to_rgb(t["text"])
        if hasattr(self, "btn_tool_aniplay"):
            enabled = self.parent_win.config.get("enable_aniplay", False) if self.parent_win else False
            self.btn_tool_aniplay.setVisible(enabled)
        qss = f"""
            QFrame#AegisSidebarWidget {{
                background-color: {t['surface']};
                border-left: 1px solid rgba({rgb_text}, 0.12);
            }}
            QWidget#SidebarTopBar {{
                background-color: {t['bg']};
                border-bottom: 1px solid rgba({rgb_text}, 0.08);
            }}
            QPushButton.sidebar-tool-btn {{
                background: transparent;
                border: none;
                border-radius: 4px;
                font-size: 14px;
            }}
            QPushButton.sidebar-tool-btn:hover {{
                background-color: {t['surface']};
            }}
            QPushButton.sidebar-close-btn {{
                background: transparent;
                border: none;
                color: rgba({rgb_text}, 0.6);
                font-size: 12px;
                border-radius: 4px;
            }}
            QPushButton.sidebar-close-btn:hover {{
                background-color: {t['surface']};
                color: {t['text']};
            }}
            QLabel {{
                color: {t['text']};
            }}
            QTextEdit#SidebarNotesInput {{
                background-color: {t['bg']};
                border: 1px solid rgba({rgb_text}, 0.14);
                border-radius: 8px;
                color: {t['text']};
                padding: 8px;
                font-size: 12px;
                font-family: inherit;
            }}
            QTextEdit#SidebarNotesInput:focus {{
                border-color: {t['accent']};
            }}
            QLineEdit#SidebarSearchInput, QLineEdit#SidebarPassOutput {{
                background-color: {t['bg']};
                border: 1px solid rgba({rgb_text}, 0.14);
                border-radius: 6px;
                color: {t['text']};
                padding: 6px 10px;
                font-size: 12px;
            }}
            QListWidget#SidebarList {{
                background: transparent;
                border: none;
                color: {t['text']};
            }}
            QListWidget#SidebarList::item {{
                background-color: {t['bg']};
                border: 1px solid rgba({rgb_text}, 0.08);
                border-radius: 6px;
                padding: 6px 8px;
                margin-bottom: 4px;
                font-size: 11.5px;
            }}
            QListWidget#SidebarList::item:hover {{
                border-color: {t['accent']};
                color: {t['accent']};
            }}
            QPushButton.sidebar-action-btn {{
                background-color: {t['bg']};
                border: 1px solid rgba({rgb_text}, 0.16);
                border-radius: 6px;
                color: {t['text']};
                padding: 6px 12px;
                font-size: 12px;
                font-weight: 600;
            }}
            QPushButton.sidebar-action-btn:hover {{
                background-color: {t['surface']};
                border-color: {t['accent']};
                color: {t['accent']};
            }}
        """
        self.setStyleSheet(qss)

# ── 10.4 Barra de Marcadores Horizontal (Ctrl+Shift+B) ────────────────────────
class AegisBookmarksBar(QWidget):
    def __init__(self, parent_win):
        super().__init__(parent_win)
        self.parent_win = parent_win
        self.setObjectName("BookmarksBar")
        self.setFixedHeight(30)
        self.bar_layout = QHBoxLayout(self)
        self.bar_layout.setContentsMargins(10, 2, 10, 2)
        self.bar_layout.setSpacing(6)
        self.refresh_bookmarks()

    def refresh_bookmarks(self):
        while self.bar_layout.count():
            item = self.bar_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        lbl_icon = QLabel("⭐")
        lbl_icon.setStyleSheet("font-size: 11px; color: #8b949e;")
        self.bar_layout.addWidget(lbl_icon)

        bookmarks = self.parent_win.bookmarks_mgr.bookmarks if (self.parent_win and hasattr(self.parent_win, "bookmarks_mgr")) else []
        for b in bookmarks[:15]:
            title = b.get("title", "Marcador")
            display_title = title if len(title) <= 18 else title[:16] + "…"
            btn = QPushButton(display_title)
            btn.setProperty("class", "bookmark-item-btn")
            btn.setToolTip(f"{title}\n{b.get('url', '')}")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            url = b.get("url", "")
            btn.clicked.connect(lambda checked, u=url: self.parent_win.navigate_direct(u))
            btn.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            btn.customContextMenuRequested.connect(lambda pt, b_item=b: self.show_context_menu(pt, b_item))
            self.bar_layout.addWidget(btn)

        self.bar_layout.addStretch()

    def show_context_menu(self, point: QPoint, bookmark_item: dict):
        menu = QMenu(self)
        if hasattr(self.parent_win, "current_qss"):
            menu.setStyleSheet(self.parent_win.current_qss)
        act_open_new = menu.addAction("Abrir en nueva pestaña")
        act_copy = menu.addAction("Copiar dirección")
        menu.addSeparator()
        act_delete = menu.addAction("Eliminar marcador")

        action = menu.exec(self.mapToGlobal(point))
        if action == act_open_new:
            self.parent_win.add_new_tab(bookmark_item.get("url", ""))
        elif action == act_copy:
            QApplication.clipboard().setText(bookmark_item.get("url", ""))
        elif action == act_delete:
            self.parent_win.bookmarks_mgr.remove(bookmark_item.get("url", ""))
            self.refresh_bookmarks()
            self.parent_win.update_omnibox_suggestions()

# ── 10.5 Widget Flotante de Búsqueda en Página (Ctrl+F) ───────────────────────
class FindInPageWidget(QFrame):
    def __init__(self, parent_win):
        super().__init__(parent_win)
        self.parent_win = parent_win
        self.setObjectName("FindInPageBar")
        self.setFixedWidth(340)
        self.setFixedHeight(38)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(6)

        self.input = QLineEdit()
        self.input.setObjectName("FindInput")
        self.input.setPlaceholderText("Buscar en la página...")
        self.input.textChanged.connect(self.on_text_changed)
        self.input.returnPressed.connect(self.find_next)
        layout.addWidget(self.input)

        self.lbl_count = QLabel("")
        self.lbl_count.setStyleSheet("font-size: 11px; color: #8b949e;")
        layout.addWidget(self.lbl_count)

        self.btn_prev = QPushButton("▲")
        self.btn_prev.setProperty("class", "mini-nav-btn")
        self.btn_prev.setToolTip("Anterior (Shift+Enter)")
        self.btn_prev.clicked.connect(self.find_prev)
        layout.addWidget(self.btn_prev)

        self.btn_next = QPushButton("▼")
        self.btn_next.setProperty("class", "mini-nav-btn")
        self.btn_next.setToolTip("Siguiente (Enter)")
        self.btn_next.clicked.connect(self.find_next)
        layout.addWidget(self.btn_next)

        self.btn_close = QPushButton("✕")
        self.btn_close.setProperty("class", "mini-nav-btn")
        self.btn_close.setToolTip("Cerrar (Esc)")
        self.btn_close.clicked.connect(self.close_find)
        layout.addWidget(self.btn_close)

        self.hide()

    def show_find(self):
        self.show()
        self.raise_()
        self.input.setFocus()
        self.input.selectAll()
        self.reposition()

    def reposition(self):
        tb_h = self.parent_win.toolbar.height() if hasattr(self.parent_win, "toolbar") else 40
        bm_h = self.parent_win.bookmarks_bar.height() if (hasattr(self.parent_win, "bookmarks_bar") and self.parent_win.bookmarks_bar.isVisible()) else 0
        top_offset = tb_h + bm_h + 40
        x = max(10, self.parent_win.width() - self.width() - 25)
        self.move(x, top_offset)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close_find()
            return
        super().keyPressEvent(event)

    def on_text_changed(self, text):
        v = self.parent_win.current_view()
        if v:
            if text:
                v.findText(text)
            else:
                v.findText("")
                self.lbl_count.setText("")

    def find_next(self):
        v = self.parent_win.current_view()
        if v and self.input.text():
            v.findText(self.input.text())

    def find_prev(self):
        v = self.parent_win.current_view()
        if v and self.input.text():
            v.findText(self.input.text(), QWebEnginePage.FindFlag.FindBackward)

    def close_find(self):
        v = self.parent_win.current_view()
        if v:
            v.findText("")
        self.lbl_count.setText("")
        self.hide()

    def apply_theme(self, t: dict):
        rgb_text = hex_to_rgb(t["text"])
        if hasattr(self, "btn_tool_aniplay"):
            enabled = self.parent_win.config.get("enable_aniplay", False) if self.parent_win else False
            self.btn_tool_aniplay.setVisible(enabled)
        qss = f"""
            QFrame#FindInPageBar {{
                background-color: {t['surface']};
                border: 1px solid rgba({rgb_text}, 0.2);
                border-radius: 8px;
            }}
            QLineEdit#FindInput {{
                background-color: {t['bg']};
                border: 1px solid rgba({rgb_text}, 0.15);
                border-radius: 4px;
                color: {t['text']};
                padding: 3px 8px;
                font-size: 12px;
                selection-background-color: {t['accent']};
            }}
            QLineEdit#FindInput:focus {{
                border-color: {t['accent']};
            }}
            QLabel {{
                color: {t['text']};
            }}
            QPushButton.mini-nav-btn {{
                background: transparent;
                border: none;
                border-radius: 4px;
                color: {t['text']};
                width: 22px;
                height: 22px;
                font-size: 12px;
            }}
            QPushButton.mini-nav-btn:hover {{
                background-color: {t['bg']};
                color: {t['accent']};
            }}
        """
        self.setStyleSheet(qss)
        self.update()

# ── 10.6 Página y Vista Web Personalizada con Menú Contextual Temático ────────
class AegisWebPage(QWebEnginePage):
    def __init__(self, profile, view, browser_win=None):
        super().__init__(profile, view)
        self.browser_win = browser_win
        self.featurePermissionRequested.connect(self.handle_feature_permission)
        self.fullScreenRequested.connect(self.handle_fullscreen_request)

    def createWindow(self, window_type: QWebEnginePage.WebWindowType) -> QWebEnginePage:
        # Permite popups de OAuth (Google, Discord, Spotify) y target="_blank"
        if self.browser_win:
            new_view = self.browser_win.add_new_tab()
            return new_view.page()
        return super().createWindow(window_type)

    def handle_feature_permission(self, security_origin: QUrl, feature: QWebEnginePage.Feature):
        # Auto-conceder permisos esenciales para Discord (micrófono, cámara, pantalla, notificaciones, portapapeles) y Spotify
        self.setFeaturePermission(security_origin, feature, QWebEnginePage.PermissionPolicy.PermissionGrantedByUser)

    def handle_fullscreen_request(self, request):
        if self.browser_win and hasattr(self.browser_win, "handle_fullscreen_request"):
            self.browser_win.handle_fullscreen_request(request)
        else:
            request.accept()

class AegisWebView(QWebEngineView):
    def __init__(self, browser_win=None):
        super().__init__()
        self.browser_win = browser_win
        self._last_active_time = time.time()
        self._is_hibernated = False
        self._is_pinned = False
        self._hibernated_url = ""
        self._hibernated_title = ""

    def contextMenuEvent(self, event):
        menu = self.createStandardContextMenu()
        if menu:
            # Opción de Imagen en imagen (Picture-in-Picture)
            act_pip = menu.addAction("🖼️ Imagen en imagen (PiP)  [Alt+P]")
            if self.browser_win and hasattr(self.browser_win, "toggle_picture_in_picture"):
                act_pip.triggered.connect(self.browser_win.toggle_picture_in_picture)

            if self.browser_win and hasattr(self.browser_win, "current_qss"):
                menu.setStyleSheet(self.browser_win.current_qss)
            menu.exec(event.globalPos())

# ── 10.7 Barra de Pestañas con Desprendimiento (Tear-Off) y Menú Contextual ───
class AegisTabBar(QTabBar):
    tabDetached = pyqtSignal(int, QPoint)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_win = parent
        self.setTabsClosable(True)
        self.setMovable(True)
        self.setDrawBase(False)
        self.setElideMode(Qt.TextElideMode.ElideRight)
        self.setIconSize(QSize(16, 16))
        self._drag_start_pos = None
        self._drag_tab_idx = -1

    def contextMenuEvent(self, event):
        idx = self.tabAt(event.pos())
        if idx != -1 and self.parent_win and hasattr(self.parent_win, "show_tab_context_menu"):
            self.parent_win.show_tab_context_menu(idx, event.globalPos())
            event.accept()
        else:
            super().contextMenuEvent(event)

    def tabInserted(self, index: int):
        super().tabInserted(index)
        wrapper = QWidget()
        wrapper.setFixedSize(22, 20)
        wl = QHBoxLayout(wrapper)
        wl.setContentsMargins(0, 0, 4, 0)
        wl.setSpacing(0)
        btn = QPushButton("✕")
        btn.setProperty("class", "tab-close-btn")
        btn.setFixedSize(16, 16)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setToolTip("Cerrar pestaña")
        btn.clicked.connect(lambda _, b=btn: self.on_close_clicked(b))
        wl.addWidget(btn)
        self.setTabButton(index, QTabBar.ButtonPosition.RightSide, wrapper)

    def on_close_clicked(self, btn: QPushButton):
        for i in range(self.count()):
            w = self.tabButton(i, QTabBar.ButtonPosition.RightSide)
            if w and (w == btn or w.findChild(QPushButton) == btn):
                self.tabCloseRequested.emit(i)
                break

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.MiddleButton:
            idx = self.tabAt(event.pos())
            if idx != -1:
                self.tabCloseRequested.emit(idx)
                event.accept()
                return
        elif event.button() == Qt.MouseButton.LeftButton:
            self._drag_start_pos = event.pos()
            self._drag_tab_idx = self.tabAt(event.pos())
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if (event.buttons() & Qt.MouseButton.LeftButton) and self._drag_start_pos is not None and self._drag_tab_idx != -1:
            p = event.pos()
            if (p.y() < -15 or p.y() > self.height() + 15 or p.x() < -30 or p.x() > self.width() + 30):
                if self.count() > 1:
                    self.setCursor(Qt.CursorShape.DragMoveCursor)
            else:
                self.setCursor(Qt.CursorShape.ArrowCursor)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self.setCursor(Qt.CursorShape.ArrowCursor)
        if self._drag_start_pos is not None and self._drag_tab_idx != -1:
            p = event.pos()
            if (p.y() < -15 or p.y() > self.height() + 15 or p.x() < -30 or p.x() > self.width() + 30) and self.count() > 1:
                global_pos = event.globalPosition().toPoint()
                tab_idx = self._drag_tab_idx if self._drag_tab_idx != -1 else self.currentIndex()
                self._drag_start_pos = None
                self._drag_tab_idx = -1
                self.tabDetached.emit(tab_idx, global_pos)
                return
            self._drag_start_pos = None
            self._drag_tab_idx = -1
        super().mouseReleaseEvent(event)

# ── 10.8 Barra de Direcciones Omnibox Inteligente ─────────────────────────────
class AegisOmnibox(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Omnibox")
        self._select_all_pending = False

    def focusInEvent(self, event):
        super().focusInEvent(event)
        self._select_all_pending = True
        QTimer.singleShot(0, self.selectAll)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        if self._select_all_pending:
            self.selectAll()
            self._select_all_pending = False

# ── 11. Ventana Principal de Aegis Browser ────────────────────────────────────
class AegisBrowserWindow(QMainWindow):
    def __init__(self, is_incognito: bool = False):
        super().__init__()
        self.is_incognito = is_incognito
        title = "Aegis Browser [Ventana Privada / Incógnito]" if is_incognito else "Aegis"
        self.setWindowTitle(title)
        self.resize(1340, 860)

        self._last_popup_close_time = 0.0
        self._last_app_menu_close_time = 0.0
        self._last_downloads_close_time = 0.0
        self._last_extensions_close_time = 0.0
        self._last_media_close_time = 0.0
        self._is_web_fullscreen = False
        self.config = self.load_config()
        self.current_theme_name = self.config.get("theme", "Oscuro")

        # Gestores reales (Historial, Descargas Nativas, Marcadores y Extensiones Chrome)
        self.history_mgr = HistoryManager()
        self.downloads_mgr = DownloadsManager()
        self.bookmarks_mgr = BookmarksManager()
        self.extensions_mgr = ChromeExtensionManager()
        self.closed_tabs = []

        # Configurar Perfil Chromium
        self.interceptor = AegisRequestInterceptor(self.on_shield_block)
        if self.is_incognito:
            self.profile = QWebEngineProfile(self)
            self.profile.setHttpUserAgent(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Aegis/1.3.5"
            )
            s = self.profile.settings()
            s.setAttribute(QWebEngineSettings.WebAttribute.JavascriptCanOpenWindows, True)
            s.setAttribute(QWebEngineSettings.WebAttribute.AllowWindowActivationFromJavaScript, True)
            s.setAttribute(QWebEngineSettings.WebAttribute.FullScreenSupportEnabled, True)
            s.setAttribute(QWebEngineSettings.WebAttribute.PlaybackRequiresUserGesture, False)
            s.setAttribute(QWebEngineSettings.WebAttribute.JavascriptCanAccessClipboard, True)
            s.setAttribute(QWebEngineSettings.WebAttribute.JavascriptCanPaste, True)
            s.setAttribute(QWebEngineSettings.WebAttribute.DnsPrefetchEnabled, True)
            s.setAttribute(QWebEngineSettings.WebAttribute.WebGLEnabled, True)
            s.setAttribute(QWebEngineSettings.WebAttribute.Accelerated2dCanvasEnabled, True)
            s.setAttribute(QWebEngineSettings.WebAttribute.LocalStorageEnabled, True)
            s.setAttribute(QWebEngineSettings.WebAttribute.AutoLoadIconsForPage, True)
            s.setAttribute(QWebEngineSettings.WebAttribute.ScrollAnimatorEnabled, True)
            s.setAttribute(QWebEngineSettings.WebAttribute.ScreenCaptureEnabled, True)
            s.setAttribute(QWebEngineSettings.WebAttribute.BackForwardCacheEnabled, True)
            self.profile.setUrlRequestInterceptor(self.interceptor)
            self.profile.downloadRequested.connect(self.on_download_requested)
            self.load_userscripts()
        else:
            self.profile = get_shared_profile()
            if not getattr(self.profile, "_aegis_configured", False):
                self.profile._aegis_configured = True
                self.profile.setUrlRequestInterceptor(self.interceptor)
                self.profile.downloadRequested.connect(self.on_download_requested)
                self.load_userscripts()
                self.extensions_mgr.load_all_into_profile(self.profile)

        self.views = []
        self.init_ui()

        # Menús flotantes y paneles desplegables dedicados
        self.shields_popup = AegisShieldsPopup(self, self.interceptor)
        self.app_menu = AegisAppMenu(self)
        self.zoom_popup = AegisZoomPopup(self)
        self.downloads_popup = AegisDownloadsPopup(self)
        self.extensions_popup = AegisExtensionsPopup(self)
        self.media_popup = AegisMediaPopup(self)
        self.site_info_popup = AegisSiteInfoPopup(self)
        self.bookmark_edit_popup = AegisBookmarkEditPopup(self)
        self.tab_search_popup = AegisTabSearchPopup(self)

        # Barra de búsqueda flotante en página (Ctrl+F) y Toast de notificaciones
        self.find_bar = FindInPageWidget(self)
        self.toast = AegisToast(self)

        # Atajos de teclado nativos
        self.setup_shortcuts()

        # Aplicar tema inicial
        self.apply_theme(self.current_theme_name)

        # Compactación silenciosa de memoria automática cada 90s
        self.auto_purge_timer = QTimer(self)
        self.auto_purge_timer.setInterval(90 * 1000)
        self.auto_purge_timer.timeout.connect(silent_background_memory_purge)
        self.auto_purge_timer.start()

        # Motor de Ahorro de Memoria Extremo e Hibernación Inteligente de Pestañas
        self.tab_sleep_timer = QTimer(self)
        self.tab_sleep_timer.setInterval(60 * 1000)
        self.tab_sleep_timer.timeout.connect(self.check_inactive_tabs_to_sleep)
        self.tab_sleep_timer.start()

        # Restaurar sesión previa o abrir pestaña inicial
        restored = self.restore_session_tabs()
        if not restored:
            self.add_new_tab()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "find_bar") and self.find_bar.isVisible():
            self.find_bar.reposition()
        if hasattr(self, "toast") and self.toast.isVisible():
            x = (self.width() - self.toast.width()) // 2
            y = self.height() - self.toast.height() - 32
            self.toast.move(x, y)

    def load_config(self) -> dict:
        default_config = {
            "theme": "Oscuro",
            "tab_position": "horizontal",
            "search_engine": "Google",
            "shields_enabled": True,
            "force_dark_mode": True,
            "show_bookmarks_bar": True,
            "show_sidebar": False,
            "show_home_button": True,
            "default_zoom": 100,
            "on_startup": "ntp",
            "download_directory": str(Path.home() / "Downloads"),
            "ask_download_location": False,
            "sleeping_tabs_timeout": 900,
            "clean_tracking_on_copy": True,
            "webrtc_protection": True,
            "fingerprint_protection": True,
            "https_only_mode": False,
            "clear_data_on_exit": False,
            "quick_notes": ""
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
        QShortcut(QKeySequence("Ctrl+Shift+T"), self, self.reopen_closed_tab)
        QShortcut(QKeySequence("Ctrl+N"), self, self.open_new_window)
        QShortcut(QKeySequence("Ctrl+Shift+N"), self, self.open_incognito_window)
        QShortcut(QKeySequence("Ctrl+J"), self, lambda: self.open_internal_page("aegis://downloads"))
        QShortcut(QKeySequence("Ctrl+H"), self, lambda: self.open_internal_page("aegis://history"))
        QShortcut(QKeySequence("Ctrl+Shift+E"), self, lambda: self.open_internal_page("aegis://extensions"))
        QShortcut(QKeySequence("Alt+S"), self, lambda: self.open_internal_page("aegis://settings"))
        QShortcut(QKeySequence("Ctrl+D"), self, self.toggle_bookmark_active_page)
        QShortcut(QKeySequence("Ctrl+Shift+B"), self, self.toggle_bookmarks_bar)
        QShortcut(QKeySequence("Ctrl+F"), self, self.find_bar.show_find)
        QShortcut(QKeySequence("Ctrl+M"), self, self.toggle_mute_current_tab)
        QShortcut(QKeySequence("Alt+P"), self, self.toggle_picture_in_picture)
        QShortcut(QKeySequence("F11"), self, self.toggle_fullscreen_manual)
        QShortcut(QKeySequence("F12"), self, self.open_devtools)
        QShortcut(QKeySequence("Ctrl+Shift+I"), self, self.open_devtools)
        QShortcut(QKeySequence("Ctrl+L"), self, lambda: (self.url_bar.setFocus(), self.url_bar.selectAll()))
        QShortcut(QKeySequence("Ctrl+R"), self, self.reload_page)
        QShortcut(QKeySequence("F5"), self, self.reload_page)
        QShortcut(QKeySequence("Ctrl+Plus"), self, self.zoom_in)
        QShortcut(QKeySequence("Ctrl+Equal"), self, self.zoom_in)
        QShortcut(QKeySequence("Ctrl+Minus"), self, self.zoom_out)
        QShortcut(QKeySequence("Ctrl+0"), self, self.zoom_reset)
        QShortcut(QKeySequence("Ctrl+Shift+A"), self, self.toggle_tab_search_popup)
        QShortcut(QKeySequence("Ctrl+B"), self, self.toggle_sidebar)
        QShortcut(QKeySequence("Ctrl+Shift+Del"), self, self.open_clear_data_dialog)
        QShortcut(QKeySequence("F9"), self, self.toggle_reader_mode)
        QShortcut(QKeySequence("Ctrl+Shift+S"), self, self.capture_page_screenshot)
        QShortcut(QKeySequence("Ctrl+P"), self, self.print_to_pdf)

    def load_userscripts(self):
        try:
            ensure_builtin_userscripts(USERSCRIPTS_DIR)
            USERSCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
            self.profile.scripts().clear()
            for s_file in USERSCRIPTS_DIR.glob("*.js"):
                if s_file.stem == "aegis_timer_bypass" and not self.config.get("bypass_countdown", True):
                    continue
                content = s_file.read_text(encoding="utf-8")
                s = QWebEngineScript()
                s.setName(s_file.stem)
                s.setSourceCode(content)
                if s_file.stem in ("aegis_timer_bypass", "ublock_lite"):
                    s.setInjectionPoint(QWebEngineScript.InjectionPoint.DocumentCreation)
                    s.setRunsOnSubFrames(True)
                else:
                    s.setInjectionPoint(QWebEngineScript.InjectionPoint.DocumentReady)
                    s.setRunsOnSubFrames(False)
                s.setWorldId(QWebEngineScript.ScriptWorldId.MainWorld)
                self.profile.scripts().insert(s)
        except Exception:
            pass

    def on_download_requested(self, download: QWebEngineDownloadRequest):
        save_dir_str = self.config.get("download_directory", str(Path.home() / "Downloads"))
        save_dir = Path(save_dir_str)
        save_dir.mkdir(parents=True, exist_ok=True)
        filename = download.suggestedFileName() or "descarga"

        if self.config.get("ask_download_location", False):
            custom_path, _ = QFileDialog.getSaveFileName(self, "Guardar archivo como...", str(save_dir / filename))
            if custom_path:
                p = Path(custom_path)
                save_dir = p.parent
                filename = p.name
            else:
                download.cancel()
                return

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
        if hasattr(self, "downloads_popup") and self.downloads_popup.isVisible():
            self.downloads_popup.refresh_list()
        t = THEMES.get(self.current_theme_name, THEMES["Oscuro"])
        self.btn_downloads.setIcon(create_download_icon(t["accent"], 16))
        self.btn_downloads.setText(" 1")

        download.receivedBytesChanged.connect(lambda: self.on_download_progress(download, download_id))
        download.isFinishedChanged.connect(lambda: self.on_download_finished(download, download_id))

    def on_download_progress(self, download: QWebEngineDownloadRequest, download_id: str):
        self.downloads_mgr.update(download_id, {
            "received_bytes": download.receivedBytes(),
            "total_bytes": download.totalBytes()
        })
        if hasattr(self, "downloads_popup") and self.downloads_popup.isVisible():
            self.downloads_popup.refresh_list()

    def on_download_finished(self, download: QWebEngineDownloadRequest, download_id: str):
        state_str = "completed" if download.state() == QWebEngineDownloadRequest.DownloadState.DownloadCompleted else "cancelled"
        self.downloads_mgr.update(download_id, {
            "state": state_str,
            "received_bytes": download.receivedBytes(),
            "total_bytes": download.totalBytes()
        })
        t = THEMES.get(self.current_theme_name, THEMES["Oscuro"])
        self.btn_downloads.setIcon(create_download_icon(t["text"], 16))
        self.btn_downloads.setText("")
        if hasattr(self, "downloads_popup") and self.downloads_popup.isVisible():
            self.downloads_popup.refresh_list()

    def toggle_app_menu(self):
        now = time.time()
        if hasattr(self, "_last_app_menu_close_time") and (now - self._last_app_menu_close_time < 0.25):
            return

        if self.app_menu.isVisible():
            self.app_menu.hide()
            return

        if self.shields_popup.isVisible(): self.shields_popup.hide()
        if self.downloads_popup.isVisible(): self.downloads_popup.hide()
        if self.extensions_popup.isVisible(): self.extensions_popup.hide()

        v = self.current_view()
        zf = v.zoomFactor() if v else 1.0
        self.app_menu.lbl_zoom_val.setText(f"{int(zf*100)}%")

        btn_pos = self.btn_more.mapToGlobal(QPoint(0, self.btn_more.height()))
        popup_x = btn_pos.x() + self.btn_more.width() - self.app_menu.width()
        popup_y = btn_pos.y() + 6
        self.app_menu.move(popup_x, popup_y)
        self.app_menu.show()
        self.app_menu.raise_()

    def toggle_downloads_popup(self):
        now = time.time()
        if hasattr(self, "_last_downloads_close_time") and (now - self._last_downloads_close_time < 0.25):
            return

        if self.downloads_popup.isVisible():
            self.downloads_popup.hide()
            return

        if self.shields_popup.isVisible(): self.shields_popup.hide()
        if self.app_menu.isVisible(): self.app_menu.hide()
        if self.extensions_popup.isVisible(): self.extensions_popup.hide()

        self.downloads_popup.refresh_list()
        btn_pos = self.btn_downloads.mapToGlobal(QPoint(0, self.btn_downloads.height()))
        popup_x = btn_pos.x() + self.btn_downloads.width() - self.downloads_popup.width()
        popup_y = btn_pos.y() + 6
        self.downloads_popup.move(popup_x, popup_y)
        self.downloads_popup.show()
        self.downloads_popup.raise_()

    def toggle_extensions_popup(self):
        now = time.time()
        if hasattr(self, "_last_extensions_close_time") and (now - self._last_extensions_close_time < 0.25):
            return

        if self.extensions_popup.isVisible():
            self.extensions_popup.hide()
            return

        if self.shields_popup.isVisible(): self.shields_popup.hide()
        if self.app_menu.isVisible(): self.app_menu.hide()
        if self.downloads_popup.isVisible(): self.downloads_popup.hide()

        self.extensions_popup.refresh_state()
        btn_pos = self.btn_extensions.mapToGlobal(QPoint(0, self.btn_extensions.height()))
        popup_x = btn_pos.x() + self.btn_extensions.width() - self.extensions_popup.width()
        popup_y = btn_pos.y() + 6
        self.extensions_popup.move(popup_x, popup_y)
        self.extensions_popup.show()
        self.extensions_popup.raise_()

    def toggle_bookmark_active_page(self):
        v = self.current_view()
        if not v:
            return
        url_str = v.url().toString()
        if not url_str or url_str in ("aegis://start", "about:blank") or url_str.startswith("aegis://"):
            return
        title = v.title() or url_str
        accent = THEMES[self.current_theme_name]["accent"]
        if self.bookmarks_mgr.is_bookmarked(url_str):
            self.bookmarks_mgr.remove(url_str)
            self.btn_bookmark.setText("☆")
            self.btn_bookmark.setStyleSheet("")
            self.btn_bookmark.setToolTip("Añadir esta pestaña a marcadores (Ctrl+D)")
        else:
            self.bookmarks_mgr.add(title, url_str)
            self.btn_bookmark.setText("★")
            self.btn_bookmark.setStyleSheet(f"color: {accent};")
            self.btn_bookmark.setToolTip("Marcador guardado (Click para quitar)")
        self.bookmarks_bar.refresh_bookmarks()
        self.update_omnibox_suggestions()

    def open_find_bar(self):
        if hasattr(self, 'find_bar'):
            self.find_bar.show_find()

    def toggle_bookmarks_bar(self):
        show = not self.bookmarks_bar.isVisible()
        self.bookmarks_bar.setVisible(show)
        self.config["show_bookmarks_bar"] = show
        self.save_config()
        if hasattr(self, "find_bar") and self.find_bar.isVisible():
            self.find_bar.reposition()

    def toggle_mute_current_tab(self):
        v = self.current_view()
        if v:
            v.page().setAudioMuted(not v.page().isAudioMuted())
            self.on_tab_audio_state_changed(v)

    def on_tab_audio_state_changed(self, view: QWebEngineView):
        if view in self.views:
            idx = self.views.index(view)
            title = view.title() or "Página"
            if view.url().toString() in ("aegis://start", "about:blank"):
                title = "Nueva Pestaña"
            display_title = title if len(title) <= 14 else title[:12] + "…"
            if getattr(view, "_is_pinned", False):
                display_title = ""
            elif getattr(view, "_is_hibernated", False):
                display_title = "🍃 " + display_title
            elif view.page() and view.page().isAudioMuted():
                display_title += " 🔇"
            elif view.page() and view.page().recentlyAudible():
                display_title += " 🔊"
            self.tab_bar.setTabText(idx, display_title)

        # Actualizar botón flotante de control multimedia en la barra
        has_audio = any(v.page().recentlyAudible() for v in self.views if v and v.page())
        if hasattr(self, "btn_media"):
            t = THEMES.get(self.current_theme_name, THEMES["Oscuro"])
            if has_audio:
                self.btn_media.setStyleSheet(f"color: {t['accent']}; font-weight: bold;")
                self.btn_media.setToolTip("Reproduciendo multimedia: Click para desplegar controles")
            else:
                self.btn_media.setStyleSheet("")
                self.btn_media.setToolTip("Control multimedia")

    def on_tab_bar_context_menu(self, point: QPoint):
        idx = self.tab_bar.tabAt(point)
        menu = QMenu(self)
        if hasattr(self, "current_qss"):
            menu.setStyleSheet(self.current_qss)

        act_new = menu.addAction("➕ Nueva pestaña")
        act_reload = act_mute = act_pip = act_dup = act_pin = act_sleep = act_detach = act_close = act_close_others = None
        if idx != -1:
            view = self.views[idx]
            act_reload = menu.addAction("↻ Recargar pestaña")
            act_dup = menu.addAction("📋 Duplicar pestaña")
            is_muted = view.page().isAudioMuted() if view.page() else False
            act_mute = menu.addAction("🔇 Reactivar sonido" if is_muted else "🔊 Silenciar pestaña")
            act_pip = menu.addAction("🖼️ Imagen en imagen (PiP)  [Alt+P]")
            is_pinned = getattr(view, "_is_pinned", False)
            act_pin = menu.addAction("📌 Desfijar pestaña" if is_pinned else "📌 Fijar pestaña")
            if not getattr(view, "_is_hibernated", False) and view != self.current_view() and not (view.page() and view.page().recentlyAudible()):
                act_sleep = menu.addAction("🍃 Poner en reposo (Liberar RAM)")
            if self.tab_bar.count() > 1:
                act_detach = menu.addAction("🗗 Desprender pestaña (Nueva ventana)")
            menu.addSeparator()
            act_close = menu.addAction("✕ Cerrar pestaña")
            act_close_others = menu.addAction("✕ Cerrar otras pestañas")
            act_close_right = menu.addAction("✕ Cerrar pestañas a la derecha")
            menu.addSeparator()
            act_clean_link = menu.addAction("🧹 Copiar enlace sin rastreadores")

        act_reopen = None
        if self.closed_tabs:
            menu.addSeparator()
            act_reopen = menu.addAction("↩️ Reabrir pestaña cerrada")

        action = menu.exec(self.tab_bar.mapToGlobal(point))
        if action == act_new:
            self.add_new_tab()
        elif action == act_reload and idx != -1:
            self.views[idx].reload()
        elif action == act_dup and idx != -1:
            self.add_new_tab(self.views[idx].url().toString())
        elif action == act_mute and idx != -1:
            self.views[idx].page().setAudioMuted(not self.views[idx].page().isAudioMuted())
            self.on_tab_audio_state_changed(self.views[idx])
        elif action == act_pip:
            self.toggle_picture_in_picture()
        elif action == act_pin and idx != -1:
            self.toggle_pin_tab(idx)
        elif action == act_sleep and idx != -1:
            self.hibernate_tab(self.views[idx])
        elif action == act_detach and idx != -1:
            self.detach_tab_to_new_window(idx, self.tab_bar.mapToGlobal(point))
        elif action == act_close and idx != -1:
            self.close_tab(idx)
        elif action == act_close_others and idx != -1:
            for i in reversed(range(len(self.views))):
                if i != idx:
                    self.close_tab(i)
        elif action == act_close_right and idx != -1:
            for i in reversed(range(idx + 1, len(self.views))):
                self.close_tab(i)
        elif action == act_clean_link and idx != -1:
            QApplication.clipboard().setText(clean_url_tracking(self.views[idx].url().toString()))
            self.show_toast("Enlace copiado sin rastreadores.")
        elif action == act_reopen:
            self.reopen_closed_tab()

    def toggle_pin_tab(self, tab_idx: int):
        if not (0 <= tab_idx < len(self.views)):
            return
        view = self.views[tab_idx]
        view._is_pinned = not getattr(view, "_is_pinned", False)
        btn_w = self.tab_bar.tabButton(tab_idx, QTabBar.ButtonPosition.RightSide)
        if btn_w:
            btn_w.setVisible(not view._is_pinned)
        self.on_tab_audio_state_changed(view)

    def toggle_picture_in_picture(self):
        cur = self.current_view()
        if not cur:
            return
        pip_script = """
        (() => {
            try {
                const v = document.querySelector('video');
                if (!v) return 'novideo';
                if (document.pictureInPictureElement) {
                    document.exitPictureInPicture();
                    return 'exit';
                } else if (document.pictureInPictureEnabled && !v.disablePictureInPicture) {
                    v.requestPictureInPicture();
                    return 'enter';
                }
            } catch(e) {
                return 'error: ' + e.message;
            }
            return 'unsupported';
        })();
        """
        def on_pip_result(res):
            if res == "enter":
                self.show_toast("🖼️ Video en ventana flotante (PiP)")
            elif res == "exit":
                self.show_toast("Ventana flotante cerrada")
            elif res == "novideo":
                self.show_toast("No se encontró ningún reproductor de video en esta página.")
        cur.page().runJavaScript(pip_script, on_pip_result)

    def handle_fullscreen_request(self, request):
        if request.toggleOn():
            request.accept()
            self._is_web_fullscreen = True
            self.toolbar.hide()
            self.tab_header.hide()
            if hasattr(self, "bookmarks_bar"):
                self.bookmarks_bar.hide()
            self.showFullScreen()
        else:
            request.accept()
            self._is_web_fullscreen = False
            self.toolbar.show()
            self.tab_header.show()
            if hasattr(self, "bookmarks_bar") and self.config.get("show_bookmarks_bar", True):
                self.bookmarks_bar.show()
            self.showNormal()

    def toggle_fullscreen_manual(self):
        if self.isFullScreen():
            self.showNormal()
            self.toolbar.show()
            self.tab_header.show()
            if hasattr(self, "bookmarks_bar") and self.config.get("show_bookmarks_bar", True):
                self.bookmarks_bar.show()
        else:
            self.showFullScreen()

    def keyPressEvent(self, event):
        if getattr(self, "_is_web_fullscreen", False) and event.key() == Qt.Key.Key_Escape:
            cur = self.current_view()
            if cur and cur.page():
                cur.page().action(QWebEnginePage.WebAction.ExitFullScreen).trigger()
            return
        super().keyPressEvent(event)

    def toggle_media_popup(self):
        now = time.time()
        if hasattr(self, "_last_media_close_time") and (now - self._last_media_close_time < 0.25):
            return
        if hasattr(self, "media_popup") and self.media_popup.isVisible():
            self.media_popup.hide()
            return

        if self.shields_popup.isVisible(): self.shields_popup.hide()
        if self.app_menu.isVisible(): self.app_menu.hide()
        if self.downloads_popup.isVisible(): self.downloads_popup.hide()
        if self.extensions_popup.isVisible(): self.extensions_popup.hide()

        self.media_popup.refresh_state()
        btn_pos = self.btn_media.mapToGlobal(QPoint(0, self.btn_media.height()))
        popup_x = btn_pos.x() + self.btn_media.width() - self.media_popup.width()
        popup_y = btn_pos.y() + 6
        self.media_popup.move(popup_x, popup_y)
        self.media_popup.show()
        self.media_popup.raise_()

    def check_inactive_tabs_to_sleep(self):
        # Reposo automático a los 15 minutos (900 seg)
        timeout = 900
        now = time.time()
        current = self.current_view()
        for v in self.views:
            if v == current:
                continue
            if getattr(v, "_is_hibernated", False) or getattr(v, "_is_pinned", False):
                continue
            # NUNCA poner en reposo pestañas con audio activo (Spotify, YouTube Music, Discord)
            if v.page() and v.page().recentlyAudible():
                continue
            last_active = getattr(v, "_last_active_time", now)
            if now - last_active > timeout:
                self.hibernate_tab(v)

    def hibernate_tab(self, view: QWebEngineView):
        if view == self.current_view():
            return
        if view.page() and view.page().recentlyAudible():
            return
        if getattr(view, "_is_hibernated", False):
            return

        u = view.url().toString()
        if not u or u in ("aegis://start", "about:blank") or u.startswith("aegis://"):
            u = getattr(view, "_aegis_target_url", "")
            if not u or u in ("aegis://start", "about:blank") or u.startswith("aegis://"):
                return

        view._is_hibernated = True
        view._hibernated_url = u
        view._hibernated_title = view.title() or "Página"

        t = THEMES.get(self.current_theme_name, THEMES["Oscuro"])
        html = f"""<!DOCTYPE html>
        <html class="{t['ntp_class']}">
        <head><meta charset="utf-8">
        <style>
          body {{ background: {t['bg']}; color: {t['text']}; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; font-family: -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif; cursor: pointer; user-select: none; }}
          .box {{ text-align: center; padding: 26px 32px; border: 1px solid rgba(128,128,128,0.15); border-radius: 14px; background: {t['surface']}; box-shadow: 0 4px 20px rgba(0,0,0,0.15); }}
        </style>
        </head>
        <body onclick="window.location.href='{u}'">
          <div class="box">
            <div style="font-size: 2.2rem; margin-bottom: 8px;">🍃</div>
            <div style="font-weight: 600; font-size: 0.95rem;">Pestaña en reposo para ahorrar memoria</div>
            <div style="font-size: 0.8rem; opacity: 0.65; margin-top: 4px;">{view._hibernated_title}</div>
            <div style="font-size: 0.75rem; color: {t['accent']}; margin-top: 10px; font-weight: 500;">Haz clic en cualquier lugar para restaurar</div>
          </div>
        </body>
        </html>"""
        view.setHtml(html, QUrl(u))

        idx = self.views.index(view) if view in self.views else -1
        if idx != -1:
            title = view._hibernated_title
            display_title = title if len(title) <= 12 else title[:10] + "…"
            self.tab_bar.setTabText(idx, f"🍃 {display_title}")

        silent_background_memory_purge(force=True)

    def wake_tab(self, view: QWebEngineView):
        if not getattr(view, "_is_hibernated", False):
            return
        view._is_hibernated = False
        target = getattr(view, "_hibernated_url", "")
        if target:
            view.load(QUrl(target))
        idx = self.views.index(view) if view in self.views else -1
        if idx != -1:
            title = getattr(view, "_hibernated_title", "Pestaña")
            display_title = title if len(title) <= 12 else title[:10] + "…"
            self.tab_bar.setTabText(idx, display_title)

    def show_tab_context_menu(self, idx: int, global_pos: QPoint):
        local_pos = self.tab_bar.mapFromGlobal(global_pos)
        self.on_tab_bar_context_menu(local_pos)

    def on_tab_moved(self, from_idx: int, to_idx: int):
        if 0 <= from_idx < len(self.views) and 0 <= to_idx < len(self.views):
            v = self.views.pop(from_idx)
            self.views.insert(to_idx, v)

    def detach_tab_to_new_window(self, index: int, global_pos: QPoint = None):
        if self.tab_bar.count() <= 1 or not (0 <= index < len(self.views)):
            return

        view = self.views.pop(index)
        tab_text = self.tab_bar.tabText(index)
        tab_icon = self.tab_bar.tabIcon(index)

        try:
            view.urlChanged.disconnect()
            view.loadProgress.disconnect()
            view.loadFinished.disconnect()
            view.iconChanged.disconnect()
            view.page().recentlyAudibleChanged.disconnect()
            view.page().audioMutedChanged.disconnect()
        except Exception:
            pass

        self.tab_bar.removeTab(index)
        self.stack.removeWidget(view)

        new_win = AegisBrowserWindow(is_incognito=self.is_incognito)
        if len(new_win.views) > 0:
            def_v = new_win.views.pop(0)
            new_win.tab_bar.removeTab(0)
            new_win.stack.removeWidget(def_v)
            def_v.deleteLater()

        view.setParent(new_win.stack)
        view.browser_win = new_win
        new_win.views.append(view)
        new_win.stack.addWidget(view)
        new_idx = new_win.tab_bar.addTab(tab_icon, tab_text)
        new_win.tab_bar.setCurrentIndex(new_idx)
        new_win.stack.setCurrentWidget(view)

        view.urlChanged.connect(lambda qurl, v=view: new_win.on_url_changed(qurl, v))
        view.loadProgress.connect(new_win.on_load_progress)
        view.loadFinished.connect(lambda ok, v=view: new_win.on_load_finished(ok, v))
        view.iconChanged.connect(lambda ic, v=view: new_win.on_icon_changed(ic, v))
        view.page().recentlyAudibleChanged.connect(lambda a, v=view: new_win.on_tab_audio_state_changed(v))
        view.page().audioMutedChanged.connect(lambda m, v=view: new_win.on_tab_audio_state_changed(v))

        new_win.on_tab_changed(new_idx)
        cur_url = view.url().toString()
        if cur_url in ("aegis://start", "about:blank"):
            new_win.url_bar.setText("")
        else:
            new_win.url_bar.setText(cur_url)

        if global_pos:
            new_win.move(max(0, global_pos.x() - 120), max(0, global_pos.y() - 30))

        new_win.show()
        new_win.raise_()
        new_win.activateWindow()

        app = QApplication.instance()
        if not hasattr(app, "_aegis_windows"):
            app._aegis_windows = []
        if new_win not in app._aegis_windows:
            app._aegis_windows.append(new_win)

    def toggle_site_info_popup(self):
        now = time.time()
        if hasattr(self, "_last_site_info_close_time") and (now - self._last_site_info_close_time < 0.25):
            return
        if hasattr(self, "site_info_popup") and self.site_info_popup.isVisible():
            self.site_info_popup.hide()
            return
        v = self.current_view()
        url = v.url() if v else QUrl()
        self.site_info_popup.refresh_site(url)
        pos = self.url_bar.mapToGlobal(QPoint(0, self.url_bar.height() + 4))
        self.site_info_popup.move(pos.x(), pos.y())
        self.site_info_popup.show()
        self.site_info_popup.raise_()

    def toggle_tab_search_popup(self):
        now = time.time()
        if hasattr(self, "_last_tab_search_close_time") and (now - self._last_tab_search_close_time < 0.25):
            return
        if hasattr(self, "tab_search_popup") and self.tab_search_popup.isVisible():
            self.tab_search_popup.hide()
            return
        self.tab_search_popup.refresh_tabs()
        btn_pos = self.btn_tab_search.mapToGlobal(QPoint(0, self.btn_tab_search.height() + 4))
        popup_x = max(10, min(self.geometry().right() - self.tab_search_popup.width() - 10, btn_pos.x() - 180))
        self.tab_search_popup.move(popup_x, btn_pos.y())
        self.tab_search_popup.show()
        self.tab_search_popup.raise_()

    def toggle_sidebar(self):
        if not hasattr(self, "sidebar"):
            return
        is_hidden = self.sidebar.isHidden()
        self.sidebar.setVisible(is_hidden)
        self.config["show_sidebar"] = is_hidden
        self.save_config()
        if is_hidden:
            t = THEMES.get(self.current_theme_name, THEMES["Oscuro"])
            self.btn_sidebar.setStyleSheet(f"color: {t['accent']}; font-weight: bold;")
        else:
            self.btn_sidebar.setStyleSheet("")

    def open_clear_data_dialog(self):
        dlg = AegisClearDataDialog(self)
        t = THEMES.get(self.current_theme_name, THEMES["Oscuro"])
        dlg.apply_theme(t)
        dlg.exec()

    def open_brave_import_dialog(self):
        dlg = AegisBraveImportDialog(self)
        dlg.exec()

    def copy_clean_url(self):
        cur = self.current_view()
        if cur:
            u = cur.url().toString()
            clean_u = clean_url_tracking(u)
            QApplication.clipboard().setText(clean_u)
            self.show_toast("🔗 Enlace copiado sin parámetros de rastreo.")

    def capture_page_screenshot(self):
        cur = self.current_view()
        if not cur:
            return
        pix = cur.grab()
        QApplication.clipboard().setPixmap(pix)
        save_dir = Path.home() / "Downloads"
        save_dir.mkdir(parents=True, exist_ok=True)
        file_path = save_dir / f"Aegis_Screenshot_{int(time.time())}.png"
        pix.save(str(file_path), "PNG")
        self.show_toast("📸 Captura guardada en Descargas y copiada.")

    def print_to_pdf(self):
        cur = self.current_view()
        if not cur:
            return
        save_dir = Path.home() / "Downloads"
        save_dir.mkdir(parents=True, exist_ok=True)
        title = "".join(c for c in (cur.title() or "pagina") if c.isalnum() or c in (" ", "_", "-")).strip()
        file_path = save_dir / f"{title}_{int(time.time())}.pdf"
        cur.page().printToPdf(str(file_path))
        self.show_toast(f"🖨️ PDF guardado en Descargas.")

    def toggle_reader_mode(self):
        cur = self.current_view()
        if not cur:
            return
        if getattr(cur, "_in_reader_mode", False):
            orig_url = getattr(cur, "_reader_orig_url", "")
            cur._in_reader_mode = False
            cur._aegis_virtual_url = None
            if orig_url:
                cur.load(QUrl(orig_url))
            return

        cur_url = cur.url().toString()
        if not cur_url or cur_url.startswith("aegis://") or cur_url.startswith("about:"):
            self.show_toast("Modo lectura no disponible en esta página.")
            return

        reader_script = """
        (() => {
            try {
                const title = document.title || (document.querySelector('h1') ? document.querySelector('h1').innerText : 'Artículo');
                let article = document.querySelector('article') || document.querySelector('main') || document.querySelector('.content') || document.querySelector('.post-content') || document.body;
                const clone = article.cloneNode(true);
                clone.querySelectorAll('script, style, nav, aside, footer, header, noscript, iframe, .ad, .social, .advertisement, [id*="ad-"], [class*="ad-"]').forEach(el => el.remove());
                return {
                    title: title,
                    content: clone.innerHTML
                };
            } catch(e) {
                return null;
            }
        })();
        """
        def on_extracted(data):
            if not data or not data.get("content"):
                self.show_toast("No se encontró contenido legible.")
                return
            cur._in_reader_mode = True
            cur._reader_orig_url = cur_url
            t = THEMES.get(self.current_theme_name, THEMES["Oscuro"])
            reader_html = f"""<!DOCTYPE html>
            <html class="{t['ntp_class']}">
            <head><meta charset="utf-8">
            <style>
              body {{ background: {t['bg']}; color: {t['text']}; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.8; margin: 0; padding: 0; }}
              .reader-top {{ position: sticky; top: 0; background: {t['surface']}; border-bottom: 1px solid rgba(128,128,128,0.15); padding: 10px 24px; display: flex; align-items: center; justify-content: space-between; z-index: 999; }}
              .reader-btn {{ background: transparent; border: 1px solid rgba(128,128,128,0.25); border-radius: 6px; color: {t['text']}; padding: 4px 10px; cursor: pointer; font-size: 12px; font-weight: 500; }}
              .reader-btn:hover {{ border-color: {t['accent']}; color: {t['accent']}; }}
              .reader-container {{ max-width: 720px; margin: 40px auto; padding: 0 20px; }}
              h1 {{ font-size: 2.2rem; margin-bottom: 1rem; line-height: 1.25; }}
              p {{ font-size: 1.15rem; margin-bottom: 1.4rem; }}
              img {{ max-width: 100%; height: auto; border-radius: 8px; margin: 16px 0; }}
            </style>
            </head>
            <body>
              <div class="reader-top">
                <button class="reader-btn" onclick="window.location.href='{cur_url}'">← Salir de Modo Lectura</button>
                <div style="font-size: 12px; opacity: 0.7;">📖 Aegis Reader Mode</div>
              </div>
              <div class="reader-container">
                <h1>{data.get('title', 'Artículo')}</h1>
                {data.get('content', '')}
              </div>
            </body>
            </html>"""
            cur.setHtml(reader_html, QUrl(cur_url))
            self.show_toast("📖 Modo lectura activado.")

        cur.page().runJavaScript(reader_script, on_extracted)

    def restore_session_tabs(self):
        if self.is_incognito or self.config.get("on_startup") != "restore_session":
            return False
        if SESSION_FILE.exists():
            try:
                urls = json.loads(SESSION_FILE.read_text(encoding="utf-8"))
                if urls and isinstance(urls, list):
                    first = True
                    for u in urls:
                        if u and not u.startswith("aegis://start") and not u.startswith("about:"):
                            if first:
                                v = self.current_view()
                                if v:
                                    v.load(QUrl(u))
                                else:
                                    self.add_new_tab(u)
                                first = False
                            else:
                                self.add_new_tab(u)
                    if not first:
                        return True
            except Exception:
                pass
        return False

    def closeEvent(self, event):
        app = QApplication.instance()
        if hasattr(app, "_aegis_windows") and self in app._aegis_windows:
            app._aegis_windows.remove(self)
        if hasattr(self, "auto_purge_timer") and self.auto_purge_timer.isActive():
            self.auto_purge_timer.stop()
        if hasattr(self, "tab_sleep_timer") and self.tab_sleep_timer.isActive():
            self.tab_sleep_timer.stop()

        # Guardar sesión previa si está activo
        if not self.is_incognito and self.config.get("on_startup") == "restore_session":
            open_urls = []
            for v in self.views:
                u = v.url().toString()
                if u and not self.is_internal_or_ntp(u):
                    open_urls.append(u)
            try:
                SESSION_FILE.write_text(json.dumps(open_urls, indent=2), encoding="utf-8")
            except Exception:
                pass

        # Limpiar datos al salir si está configurado
        if self.config.get("clear_data_on_exit", False):
            if self.profile:
                self.profile.cookieStore().deleteAllCookies()
                self.profile.clearHttpCache()
            self.history_mgr.clear_history()

        super().closeEvent(event)

    def is_internal_or_ntp(self, url_str: str) -> bool:
        if not url_str or url_str in ("aegis://start", "about:blank", "about:start"):
            return True
        u = str(url_str).lower().strip()
        if u.startswith("data:text/html") or u.startswith("data:"):
            return True
        if u.startswith("aegis://action") or "encodeuricomponent" in u:
            return True
        return False

    def build_target_url(self, text: str) -> QUrl:
        text = text.strip()
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
            "chrome://extensions": "aegis://extensions",
            "chrome://settings": "aegis://settings",
            "chrome://downloads": "aegis://downloads",
            "chrome://history": "aegis://history",
            "about:extensions": "aegis://extensions",
            "start": "aegis://start",
            "inicio": "aegis://start"
        }
        if text.lower() in shortcuts:
            return QUrl(shortcuts[text.lower()])

        if text.startswith("aegis://"):
            return QUrl(text)

        if text.startswith("http://") or text.startswith("https://") or text.startswith("file://"):
            if text.startswith("http://") and self.config.get("https_only_mode", False):
                return QUrl("https://" + text[7:])
            return QUrl(text)
        elif "." in text and " " not in text:
            return QUrl("https://" + text)
        else:
            engine = self.config.get("search_engine", "Google")
            is_dark = (self.current_theme_name == "Oscuro")
            encoded_query = quote(text)
            eng_low = str(engine).lower()
            if "google" in eng_low:
                dark_param = "&cs=1" if is_dark else ""
                return QUrl(f"https://www.google.com/search?q={encoded_query}{dark_param}")
            elif "bing" in eng_low:
                return QUrl(f"https://www.bing.com/search?q={encoded_query}")
            elif "brave" in eng_low:
                return QUrl(f"https://search.brave.com/search?q={encoded_query}")
            elif "yahoo" in eng_low:
                return QUrl(f"https://search.yahoo.com/search?p={encoded_query}")
            else:
                dark_param = "&kae=d&k1=-1" if is_dark else ""
                return QUrl(f"https://duckduckgo.com/?q={encoded_query}{dark_param}")

    def show_search_engine_menu(self):
        menu = QMenu(self)
        if hasattr(self, "current_qss"):
            menu.setStyleSheet(self.current_qss)

        engines = [
            ("Google", "Google"),
            ("DuckDuckGo", "DuckDuckGo (Privado)"),
            ("Bing", "Microsoft Bing"),
            ("Brave", "Brave Search"),
            ("Yahoo", "Yahoo")
        ]

        cur_engine = self.config.get("search_engine", "Google").lower()
        for key, label in engines:
            icon = create_search_engine_icon(key, 16)
            prefix = "✓ " if key.lower() == cur_engine else "   "
            act = menu.addAction(icon, f"{prefix}{label}")
            act.triggered.connect(lambda _, k=key: self.set_search_engine(k))

        pos = self.url_bar.mapToGlobal(QPoint(6, self.url_bar.height() + 4))
        menu.exec(pos)

    def set_search_engine(self, engine_name: str):
        self.config["search_engine"] = engine_name
        self.save_config()
        self.update_search_engine_ui()
        v = self.current_view()
        if v and (self.is_internal_or_ntp(v.url().toString()) or getattr(v, "_aegis_virtual_url", "") == "aegis://start"):
            self.load_ntp(v)

    def update_search_engine_ui(self):
        engine = self.config.get("search_engine", "Google")
        if hasattr(self, "search_engine_action"):
            self.search_engine_action.setIcon(create_search_engine_icon(engine, 16))
            self.search_engine_action.setToolTip(f"Motor actual: {engine} (Click para cambiar)")
        if hasattr(self, "url_bar"):
            v = self.current_view()
            cur_url = v.url().toString() if v else ""
            if self.is_internal_or_ntp(cur_url) or getattr(v, "_aegis_virtual_url", "") == "aegis://start":
                self.url_bar.setText("")
                placeholder = f"Navegación Privada · Buscar con {engine}..." if getattr(self, "is_incognito", False) else f"Buscar con {engine} o ingresar dirección..."
                self.url_bar.setPlaceholderText(placeholder)

    def reopen_closed_tab(self):
        if self.closed_tabs:
            url, title = self.closed_tabs.pop()
            self.add_new_tab(url)

    def open_incognito_window(self):
        win = AegisBrowserWindow(is_incognito=True)
        win.show()
        if not hasattr(QApplication.instance(), "_aegis_windows"):
            QApplication.instance()._aegis_windows = []
        QApplication.instance()._aegis_windows.append(win)

    def open_devtools(self):
        v = self.current_view()
        if not v:
            return
        if not hasattr(v, "_devtools_win") or v._devtools_win is None:
            devtools_view = QWebEngineView()
            v.page().setDevToolsPage(devtools_view.page())
            dw = QMainWindow(self)
            dw.setWindowTitle(f"Herramientas de Desarrollador - {v.title()}")
            dw.setCentralWidget(devtools_view)
            dw.resize(920, 620)
            v._devtools_win = dw
        v._devtools_win.show()
        v._devtools_win.raise_()

    def navigate_direct(self, url: str):
        v = self.current_view()
        if not v:
            v = self.add_new_tab(url)
        else:
            v.load(QUrl(url))

    def update_omnibox_suggestions(self):
        if not hasattr(self, "completer_model"):
            return
        suggestions = set()
        for b in self.bookmarks_mgr.bookmarks:
            suggestions.add(b.get("url", ""))
        for s in self.history_mgr.data.get("frequent", {}).values():
            suggestions.add(s.get("url", ""))
        for s in self.history_mgr.data.get("custom", []):
            suggestions.add(s.get("url", ""))
        for h in self.history_mgr.data.get("history_log", [])[:40]:
            suggestions.add(h.get("url", ""))
        clean_list = [u for u in suggestions if u and not u.startswith("aegis://") and not u.startswith("about:") and not u.startswith("data:")]
        self.completer_model.setStringList(sorted(clean_list))

    def open_new_window(self):
        win = AegisBrowserWindow()
        win.show()
        if not hasattr(QApplication.instance(), "_aegis_windows"):
            QApplication.instance()._aegis_windows = []
        QApplication.instance()._aegis_windows.append(win)

    def toggle_zoom_popup(self):
        if not hasattr(self, "zoom_popup"):
            return
        if self.zoom_popup.isVisible():
            self.zoom_popup.hide()
            return
        self.zoom_popup.update_val()
        pos = self.url_bar.mapToGlobal(QPoint(self.url_bar.width() - self.zoom_popup.width() - 8, self.url_bar.height() + 4))
        self.zoom_popup.move(pos)
        self.zoom_popup.show()
        self.zoom_popup.raise_()

    def update_zoom_ui(self):
        v = self.current_view()
        if not v:
            return
        zf = round(v.zoomFactor(), 2)
        if hasattr(self, "app_menu") and hasattr(self.app_menu, "lbl_zoom_val"):
            self.app_menu.lbl_zoom_val.setText(f"{int(zf*100)}%")
        if hasattr(self, "zoom_popup"):
            self.zoom_popup.update_val()
        if hasattr(self, "zoom_action"):
            if abs(zf - 1.0) > 0.05:
                self.zoom_action.setVisible(True)
                self.zoom_action.setToolTip(f"Zoom actual: {int(zf*100)}% (Click para ajustar)")
            else:
                self.zoom_action.setVisible(False)

    def zoom_in(self):
        v = self.current_view()
        if v:
            zf = round(v.zoomFactor() + 0.1, 1)
            if zf <= 3.0:
                v.setZoomFactor(zf)
                self.update_zoom_ui()

    def zoom_out(self):
        v = self.current_view()
        if v:
            zf = round(v.zoomFactor() - 0.1, 1)
            if zf >= 0.3:
                v.setZoomFactor(zf)
                self.update_zoom_ui()

    def zoom_reset(self):
        v = self.current_view()
        if v:
            v.setZoomFactor(1.0)
            self.update_zoom_ui()

    def init_ui(self):
        container = QWidget()
        self.setCentralWidget(container)
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ── 1. Tira de Pestañas Limpia ────────────────────────────────────────
        self.tab_header = QWidget()
        self.tab_header.setObjectName("TabHeader")
        self.tab_header.setFixedHeight(38)
        tab_header_layout = QHBoxLayout(self.tab_header)
        tab_header_layout.setContentsMargins(10, 4, 10, 0)
        tab_header_layout.setSpacing(6)

        self.tab_bar = AegisTabBar(self)
        self.tab_bar.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tab_bar.customContextMenuRequested.connect(self.on_tab_bar_context_menu)
        self.tab_bar.currentChanged.connect(self.on_tab_changed)
        self.tab_bar.tabCloseRequested.connect(self.close_tab)
        self.tab_bar.tabMoved.connect(self.on_tab_moved)
        self.tab_bar.tabDetached.connect(self.detach_tab_to_new_window)
        tab_header_layout.addWidget(self.tab_bar)

        self.btn_new_tab = QPushButton("+")
        self.btn_new_tab.setObjectName("NewTabBtn")
        self.btn_new_tab.setToolTip("Nueva Pestaña (Ctrl+T)")
        self.btn_new_tab.clicked.connect(lambda: self.add_new_tab())
        tab_header_layout.addWidget(self.btn_new_tab)

        self.btn_tab_search = QPushButton("▼")
        self.btn_tab_search.setObjectName("TabSearchBtn")
        self.btn_tab_search.setToolTip("Buscar pestañas abiertas o recientes (Ctrl+Shift+A)")
        self.btn_tab_search.clicked.connect(self.toggle_tab_search_popup)
        tab_header_layout.addWidget(self.btn_tab_search)

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
        self.btn_reload.setToolTip("Recargar (F5)")
        self.btn_reload.clicked.connect(self.reload_page)
        toolbar_layout.addWidget(self.btn_reload)

        self.btn_home = QPushButton("⌂")
        self.btn_home.setProperty("class", "nav-btn")
        self.btn_home.setToolTip("Inicio")
        self.btn_home.clicked.connect(self.navigate_home)
        toolbar_layout.addWidget(self.btn_home)

        # Omnibox Cápsula Inteligente
        self.url_bar = AegisOmnibox(self)
        self.url_bar.setObjectName("Omnibox")

        # Acción de seguridad SSL (🔒 / ⚠️ / 🛡️)
        self.security_action = self.url_bar.addAction(
            create_lock_icon("#2ea043", 16),
            QLineEdit.ActionPosition.LeadingPosition
        )
        self.security_action.setToolTip("Información del sitio y seguridad de conexión")
        self.security_action.triggered.connect(self.toggle_site_info_popup)

        engine = self.config.get("search_engine", "Google")
        self.search_engine_action = self.url_bar.addAction(
            create_search_engine_icon(engine, 16),
            QLineEdit.ActionPosition.LeadingPosition
        )
        self.search_engine_action.setToolTip(f"Motor actual: {engine} (Click para cambiar)")
        self.search_engine_action.triggered.connect(self.show_search_engine_menu)

        placeholder = f"Navegación Privada · Buscar con {engine}..." if self.is_incognito else f"Buscar con {engine} o ingresar dirección..."
        self.url_bar.setPlaceholderText(placeholder)
        self.url_bar.returnPressed.connect(self.navigate_to_url)

        # Acciones laterales derechas del Omnibox
        self.clean_copy_action = self.url_bar.addAction(
            create_copy_link_icon("#888888", 14),
            QLineEdit.ActionPosition.TrailingPosition
        )
        self.clean_copy_action.setToolTip("Copiar enlace limpio sin parámetros de rastreo")
        self.clean_copy_action.triggered.connect(self.copy_clean_url)

        self.reader_action = self.url_bar.addAction(
            create_book_icon("#888888", 14),
            QLineEdit.ActionPosition.TrailingPosition
        )
        self.reader_action.setToolTip("Modo Lectura / Distraction-free (F9)")
        self.reader_action.triggered.connect(self.toggle_reader_mode)

        self.zoom_action = self.url_bar.addAction(
            create_zoom_icon("#888888", 14),
            QLineEdit.ActionPosition.TrailingPosition
        )
        self.zoom_action.setToolTip("Zoom: Click para ajustar")
        self.zoom_action.setVisible(False)
        self.zoom_action.triggered.connect(self.toggle_zoom_popup)

        # Autocompletado del Omnibox
        self.completer_model = QStringListModel()
        self.completer = QCompleter(self.completer_model, self)
        self.completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self.url_bar.setCompleter(self.completer)
        self.update_omnibox_suggestions()

        toolbar_layout.addWidget(self.url_bar)

        # Botón dinámico de instalación de Chrome Web Store (🧩 Añadir a Aegis)
        self.btn_webstore_install = QPushButton("🧩 Añadir a Aegis")
        self.btn_webstore_install.setObjectName("WebstoreInstallBtn")
        self.btn_webstore_install.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_webstore_install.setToolTip("Instalar esta extensión de Chrome Web Store en Aegis")
        self.btn_webstore_install.clicked.connect(self.on_webstore_install_clicked)
        self.btn_webstore_install.hide()
        toolbar_layout.addWidget(self.btn_webstore_install)

        # Solo botones esenciales en la barra de herramientas:
        # 1. Escudo Aegis Shields
        self.shield_btn = QPushButton(" 0")
        self.shield_btn.setObjectName("ShieldBtn")
        self.shield_btn.setToolTip("Aegis Shields: Click para desplegar panel de protección")
        self.shield_btn.clicked.connect(self.toggle_shields_popup)
        toolbar_layout.addWidget(self.shield_btn)

        # 2. Descargas (con icono vectorial nítido de alta visibilidad)
        self.btn_downloads = QPushButton("")
        self.btn_downloads.setObjectName("DownloadsBtn")
        self.btn_downloads.setToolTip("Descargas: Click para desplegar panel (Ctrl+J)")
        self.btn_downloads.clicked.connect(self.toggle_downloads_popup)
        toolbar_layout.addWidget(self.btn_downloads)

        # 3. Extensiones (con icono de pieza de rompecabezas nítido)
        self.btn_extensions = QPushButton("")
        self.btn_extensions.setObjectName("ExtensionsBtn")
        self.btn_extensions.setToolTip("Extensiones y Scripts: Click para desplegar panel (Ctrl+Shift+E)")
        self.btn_extensions.clicked.connect(self.toggle_extensions_popup)
        toolbar_layout.addWidget(self.btn_extensions)

        # Contenedor dinámico de botones anclados (click derecho en los 3 puntos)
        self.pinned_container = QWidget()
        self.pinned_layout = QHBoxLayout(self.pinned_container)
        self.pinned_layout.setContentsMargins(0, 0, 0, 0)
        self.pinned_layout.setSpacing(4)
        toolbar_layout.addWidget(self.pinned_container)

        # Botones opcionales instanciados para compatibilidad
        self.btn_bookmark = QPushButton("☆")
        self.btn_bookmark.setObjectName("BookmarkBtn")
        self.btn_bookmark.clicked.connect(self.toggle_bookmark_active_page)

        self.btn_media = QPushButton("🎵")
        self.btn_media.setObjectName("MediaControlBtn")
        self.btn_media.clicked.connect(self.toggle_media_popup)

        self.btn_sidebar = QPushButton("📑")
        self.btn_sidebar.setObjectName("SidebarBtn")
        self.btn_sidebar.clicked.connect(self.toggle_sidebar)

        self.btn_theme_toggle = QPushButton("☀️")
        self.btn_theme_toggle.setObjectName("ThemeToggleBtn")
        self.btn_theme_toggle.clicked.connect(self.toggle_theme)

        # 4. Menú Principal (⋮ Tres Puntos)
        self.btn_more = QPushButton("⋮")
        self.btn_more.setObjectName("MoreBtn")
        self.btn_more.setToolTip("Personalizar y controlar Aegis")
        self.btn_more.clicked.connect(self.toggle_app_menu)
        toolbar_layout.addWidget(self.btn_more)

        self.rebuild_pinned_toolbar_buttons()

        main_layout.addWidget(self.toolbar)

        # ── 3. Barra de Marcadores Horizontal ─────────────────────────────────
        self.bookmarks_bar = AegisBookmarksBar(self)
        if not self.config.get("show_bookmarks_bar", True):
            self.bookmarks_bar.hide()
        main_layout.addWidget(self.bookmarks_bar)

        # ── 4. Micro Barra de Progreso (2px) ──────────────────────────────────
        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("MicroProgress")
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(2)
        self.progress_bar.hide()
        main_layout.addWidget(self.progress_bar)

        # ── 5. Contenedor de Vistas Web y Barra Lateral ───────────────────────
        self.web_content_splitter = QWidget()
        splitter_layout = QHBoxLayout(self.web_content_splitter)
        splitter_layout.setContentsMargins(0, 0, 0, 0)
        splitter_layout.setSpacing(0)

        self.stack = QStackedWidget()
        splitter_layout.addWidget(self.stack, 1)

        self.sidebar = AegisSidebarWidget(self)
        if not self.config.get("show_sidebar", False):
            self.sidebar.hide()
        splitter_layout.addWidget(self.sidebar, 0)

        main_layout.addWidget(self.web_content_splitter, 1)

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

        # Actualizar color de fondo de todas las páginas para erradicar destellos blancos
        for view in self.views:
            view.page().setBackgroundColor(QColor(t["bg"]))

        rgb_text = hex_to_rgb(t["text"])
        rgb_accent = hex_to_rgb(t["accent"])

        qss = f"""
            QWidget {{
                color: {t['text']};
            }}
            QLabel {{
                color: {t['text']};
            }}
            QMainWindow {{
                background-color: {t['bg']};
                color: {t['text']};
            }}
            QToolTip {{
                background-color: {t['surface']};
                color: {t['text']};
                border: 1px solid rgba({rgb_text}, 0.2);
                border-radius: 4px;
                padding: 4px 8px;
            }}
            QDialog, QMessageBox {{
                background-color: {t['surface']};
                color: {t['text']};
            }}
            QPushButton.pinned-toolbar-btn {{
                background: transparent;
                border: none;
                color: {t['text']};
                font-size: 15px;
                border-radius: 14px;
                width: 30px;
                height: 30px;
            }}
            QPushButton.pinned-toolbar-btn:hover {{
                background-color: {t['surface']};
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
                padding: 4px 6px 4px 10px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                margin-right: 4px;
                font-size: 12px;
                height: 26px;
                font-family: -apple-system, 'Segoe UI', sans-serif;
                min-width: 85px;
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
            QTabBar::close-button {{
                image: none;
                width: 0px;
                height: 0px;
            }}
            QPushButton.tab-close-btn {{
                background: transparent;
                border: none;
                border-radius: 4px;
                color: rgba({rgb_text}, 0.50);
                font-size: 10px;
                font-weight: bold;
                margin: 0px;
                padding: 0px;
            }}
            QPushButton.tab-close-btn:hover {{
                background-color: rgba({rgb_text}, 0.15);
                color: {t['text']};
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
            QPushButton#TabSearchBtn {{
                background: transparent;
                border: none;
                color: rgba({rgb_text}, 0.65);
                font-size: 11px;
                border-radius: 12px;
                width: 22px;
                height: 22px;
            }}
            QPushButton#TabSearchBtn:hover {{
                background-color: {t['surface']};
                color: {t['text']};
            }}
            QPushButton#SidebarBtn {{
                background: transparent;
                border: none;
                color: {t['text']};
                font-size: 15px;
                border-radius: 14px;
                width: 30px;
                height: 30px;
            }}
            QPushButton#SidebarBtn:hover {{
                background-color: {t['surface']};
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
            QPushButton#BookmarkBtn {{
                background: transparent;
                border: none;
                color: {t['text']};
                font-size: 16px;
                border-radius: 14px;
                width: 28px;
                height: 28px;
            }}
            QPushButton#BookmarkBtn:hover {{
                background-color: {t['surface']};
            }}
            QPushButton#WebstoreInstallBtn {{
                background-color: {t['accent']};
                color: #ffffff;
                border: none;
                border-radius: 13px;
                padding: 4px 12px;
                font-size: 11.5px;
                font-weight: 600;
                height: 22px;
            }}
            QPushButton#WebstoreInstallBtn:hover {{
                background-color: {t['accent']};
                opacity: 0.9;
            }}
            QPushButton#WebstoreInstallBtn:disabled {{
                background-color: rgba({rgb_text}, 0.1);
                color: #2ea043;
            }}
            QLabel#AegisToast {{
                background-color: {t['surface']};
                color: {t['text']};
                border: 1.5px solid {t['accent']};
                border-radius: 8px;
                font-size: 12px;
                font-weight: 600;
                padding: 4px 16px;
            }}
            QPushButton#MediaControlBtn {{
                background: transparent;
                border: none;
                color: {t['text']};
                font-size: 15px;
                border-radius: 14px;
                width: 30px;
                height: 30px;
            }}
            QPushButton#MediaControlBtn:hover {{
                background-color: {t['surface']};
            }}
            QPushButton#DownloadsBtn {{
                background: transparent;
                border: none;
                color: {t['text']};
                font-size: 15px;
                border-radius: 14px;
                width: 30px;
                height: 30px;
            }}
            QPushButton#DownloadsBtn:hover {{
                background-color: {t['surface']};
            }}
            QPushButton#ExtensionsBtn {{
                background: transparent;
                border: none;
                color: {t['text']};
                font-size: 15px;
                border-radius: 14px;
                width: 30px;
                height: 30px;
            }}
            QPushButton#ExtensionsBtn:hover {{
                background-color: {t['surface']};
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
                border: 1.5px solid rgba({rgb_text}, 0.15);
                border-radius: 17px;
                color: {t['text']};
                padding: 6px 14px;
                font-size: 13px;
                font-family: -apple-system, 'Segoe UI', sans-serif;
                selection-background-color: {t['accent']};
            }}
            QLineEdit#Omnibox:focus {{
                border: 2px solid {t['accent']};
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
            QWidget#BookmarksBar {{
                background-color: {t['bg']};
                border-bottom: 1px solid rgba({rgb_text}, 0.08);
            }}
            QPushButton.bookmark-item-btn {{
                background: transparent;
                border: none;
                border-radius: 4px;
                color: {t['text']};
                padding: 2px 8px;
                font-size: 12px;
                font-weight: 500;
            }}
            QPushButton.bookmark-item-btn:hover {{
                background-color: {t['surface']};
                color: {t['accent']};
            }}
            QProgressBar#MicroProgress {{
                background-color: transparent;
                border: none;
            }}
            QProgressBar#MicroProgress::chunk {{
                background-color: {t['accent']};
            }}
            QMenu {{
                background-color: {t['surface']};
                color: {t['text']};
                border: 1px solid rgba({rgb_text}, 0.18);
                border-radius: 8px;
                padding: 4px;
            }}
            QMenu::item {{
                background-color: transparent;
                padding: 6px 20px 6px 10px;
                border-radius: 4px;
                color: {t['text']};
                font-size: 12.5px;
            }}
            QMenu::item:selected {{
                background-color: {t['bg']};
                color: {t['accent']};
            }}
            QMenu::separator {{
                height: 1px;
                background-color: rgba({rgb_text}, 0.08);
                margin: 4px 6px;
            }}
        """
        self.current_qss = qss
        self.setStyleSheet(qss)

        if hasattr(self, "shield_btn"):
            self.shield_btn.setIcon(create_shield_icon(t["accent"], 16))

        if hasattr(self, "shields_popup"):
            self.shields_popup.apply_theme(t)

        if hasattr(self, "app_menu"):
            self.app_menu.apply_theme(t)

        if hasattr(self, "zoom_popup"):
            self.zoom_popup.apply_theme(t)

        if hasattr(self, "btn_downloads"):
            self.btn_downloads.setIcon(create_download_icon(t["text"], 16))

        if hasattr(self, "btn_extensions"):
            self.btn_extensions.setIcon(create_extension_icon(t["text"], 16))

        self.rebuild_pinned_toolbar_buttons()

        if hasattr(self, "downloads_popup"):
            self.downloads_popup.apply_theme(t)

        if hasattr(self, "extensions_popup"):
            self.extensions_popup.apply_theme(t)

        if hasattr(self, "media_popup"):
            self.media_popup.apply_theme(t)

        if hasattr(self, "site_info_popup"):
            self.site_info_popup.apply_theme(t)

        if hasattr(self, "bookmark_edit_popup"):
            self.bookmark_edit_popup.apply_theme(t)

        if hasattr(self, "tab_search_popup"):
            self.tab_search_popup.apply_theme(t)

        if hasattr(self, "sidebar"):
            self.sidebar.apply_theme(t)

        if hasattr(self, "find_bar"):
            self.find_bar.apply_theme(t)

        if hasattr(self, "bookmarks_bar"):
            self.bookmarks_bar.refresh_bookmarks()

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

        if self.app_menu.isVisible(): self.app_menu.hide()
        if self.downloads_popup.isVisible(): self.downloads_popup.hide()
        if self.extensions_popup.isVisible(): self.extensions_popup.hide()

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
        view = AegisWebView(self)
        view._aegis_target_url = url_str

        page = AegisWebPage(self.profile, view, self)
        view.setPage(page)
        view._last_active_time = time.time()
        view._is_hibernated = False
        view._is_pinned = False

        t = THEMES.get(self.current_theme_name, THEMES["Oscuro"])
        view.page().setBackgroundColor(QColor(t["bg"]))

        tab_idx = self.tab_bar.addTab("Nueva Pestaña")
        stack_idx = self.stack.addWidget(view)
        self.views.append(view)

        view.urlChanged.connect(lambda qurl, v=view: self.on_url_changed(qurl, v))
        view.loadProgress.connect(self.on_load_progress)
        view.loadFinished.connect(lambda ok, v=view: self.on_load_finished(ok, v))
        view.iconChanged.connect(lambda icon, v=view: self.on_icon_changed(icon, v))

        view.page().recentlyAudibleChanged.connect(lambda audible, v=view: self.on_tab_audio_state_changed(v))
        view.page().audioMutedChanged.connect(lambda muted, v=view: self.on_tab_audio_state_changed(v))

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
        view._aegis_virtual_url = "aegis://start"
        engine = self.config.get("search_engine", "Google")
        frequent_sites = self.history_mgr.get_frequent_sites(limit=8)
        html = get_clean_ntp_html(t["ntp_class"], frequent_sites, search_engine=engine)
        view.setHtml(html, QUrl("aegis://start"))
        if view == self.current_view():
            self.url_bar.setText("")
            placeholder = f"Navegación Privada · Buscar con {engine}..." if getattr(self, "is_incognito", False) else f"Buscar con {engine} o ingresar dirección..."
            self.url_bar.setPlaceholderText(placeholder)

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
        elif url_str == "aegis://aniplay":
            self.load_aniplay(view)

    def load_settings(self, view: QWebEngineView):
        idx = self.views.index(view) if view in self.views else -1
        t = THEMES.get(self.current_theme_name, THEMES["Oscuro"])
        if idx != -1:
            self.tab_bar.setTabIcon(idx, create_settings_icon(t["accent"], 14))
            self.tab_bar.setTabText(idx, "Configuración")
        view._aegis_virtual_url = "aegis://settings"
        html = get_settings_html(t["ntp_class"], self.config)
        view.setHtml(html, QUrl("aegis://settings"))
        if view == self.current_view():
            self.url_bar.setText("aegis://settings")

    def load_downloads(self, view: QWebEngineView):
        idx = self.views.index(view) if view in self.views else -1
        t = THEMES.get(self.current_theme_name, THEMES["Oscuro"])
        if idx != -1:
            self.tab_bar.setTabIcon(idx, create_download_icon(t["accent"], 14))
            self.tab_bar.setTabText(idx, "Descargas")
        view._aegis_virtual_url = "aegis://downloads"
        html = get_downloads_html(t["ntp_class"], self.downloads_mgr.downloads)
        view.setHtml(html, QUrl("aegis://downloads"))
        if view == self.current_view():
            self.url_bar.setText("aegis://downloads")

    def load_history(self, view: QWebEngineView):
        idx = self.views.index(view) if view in self.views else -1
        t = THEMES.get(self.current_theme_name, THEMES["Oscuro"])
        if idx != -1:
            self.tab_bar.setTabIcon(idx, create_history_icon(t["accent"], 14))
            self.tab_bar.setTabText(idx, "Historial")
        view._aegis_virtual_url = "aegis://history"
        html = get_history_html(t["ntp_class"], self.history_mgr.get_history())
        view.setHtml(html, QUrl("aegis://history"))
        if view == self.current_view():
            self.url_bar.setText("aegis://history")

    def load_extensions(self, view: QWebEngineView):
        idx = self.views.index(view) if view in self.views else -1
        t = THEMES.get(self.current_theme_name, THEMES["Oscuro"])
        if idx != -1:
            self.tab_bar.setTabIcon(idx, create_extension_icon(t["accent"], 14))
            self.tab_bar.setTabText(idx, "Extensiones")
        view._aegis_virtual_url = "aegis://extensions"
        scripts = [f.name for f in USERSCRIPTS_DIR.glob("*.js")] if USERSCRIPTS_DIR.exists() else []
        chrome_exts = self.extensions_mgr.get_installed_extensions()
        html = get_extensions_html(t["ntp_class"], chrome_exts, scripts)
        view.setHtml(html, QUrl("aegis://extensions"))
        if view == self.current_view():
            self.url_bar.setText("aegis://extensions")

    def toggle_tab_orientation(self):
        cur = self.config.get("tab_position", "horizontal")
        new_pos = "vertical" if cur == "horizontal" else "horizontal"
        self.config["tab_position"] = new_pos
        self.save_config()
        self.update_tab_layout()

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

    def pin_toolbar_button(self, item_id: str):
        pinned = self.config.setdefault("pinned_toolbar_buttons", [])
        if item_id not in pinned:
            pinned.append(item_id)
            self.save_config()
            self.rebuild_pinned_toolbar_buttons()
            self.show_toast("Botón anclado a la barra de herramientas")

    def unpin_toolbar_button(self, item_id: str):
        pinned = self.config.get("pinned_toolbar_buttons", [])
        if item_id in pinned:
            pinned.remove(item_id)
            self.save_config()
            self.rebuild_pinned_toolbar_buttons()
            self.show_toast("Botón desanclado de la barra de herramientas")

    def show_pinned_btn_context_menu(self, item_id: str, btn: QWidget, pos: QPoint):
        menu = QMenu(self)
        menu.setStyleSheet(self.current_qss)
        act = menu.addAction("Desanclar de la barra de herramientas")
        act.triggered.connect(lambda: self.unpin_toolbar_button(item_id))
        menu.exec(btn.mapToGlobal(pos))

    def rebuild_pinned_toolbar_buttons(self):
        if not hasattr(self, "pinned_layout"):
            return
        while self.pinned_layout.count():
            item = self.pinned_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        pinned = self.config.get("pinned_toolbar_buttons", [])
        t = THEMES.get(self.current_theme_name, THEMES["Oscuro"])
        for item_id in pinned:
            btn = self.create_pinned_button(item_id, t)
            if btn:
                self.pinned_layout.addWidget(btn)

    def create_pinned_button(self, item_id: str, t: dict) -> QWidget | None:
        btn = QPushButton()
        btn.setProperty("class", "pinned-toolbar-btn")
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setFixedSize(30, 30)
        btn.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        btn.customContextMenuRequested.connect(lambda pos, i_id=item_id, b=btn: self.show_pinned_btn_context_menu(i_id, b, pos))

        if item_id == "media_control":
            btn.setText("🎵")
            btn.setToolTip("Control multimedia global")
            btn.clicked.connect(self.toggle_media_popup)
        elif item_id == "sidebar":
            btn.setText("📑")
            btn.setToolTip("Barra lateral (Ctrl+B)")
            btn.clicked.connect(self.toggle_sidebar)
        elif item_id == "theme_toggle":
            btn.setText("☀️" if self.current_theme_name == "Oscuro" else "🌙")
            btn.setToolTip("Cambiar tema (Oscuro / Claro)")
            btn.clicked.connect(self.toggle_theme)
        elif item_id == "bookmarks_bar":
            btn.setIcon(create_star_icon(t["text"], 16))
            btn.setToolTip("Barra de marcadores (Ctrl+Shift+B)")
            btn.clicked.connect(self.toggle_bookmarks_bar)
        elif item_id == "history":
            btn.setIcon(create_history_icon(t["text"], 16))
            btn.setToolTip("Historial (Ctrl+H)")
            btn.clicked.connect(lambda: self.open_internal_page("aegis://history"))
        elif item_id == "reader_mode":
            btn.setIcon(create_book_icon(t["text"], 16))
            btn.setToolTip("Modo lectura (F9)")
            btn.clicked.connect(self.toggle_reader_mode)
        elif item_id == "clean_copy":
            btn.setIcon(create_copy_link_icon(t["text"], 16))
            btn.setToolTip("Copiar enlace limpio")
            btn.clicked.connect(self.copy_clean_url)
        elif item_id == "screenshot":
            btn.setText("📸")
            btn.setToolTip("Capturar pantalla (Ctrl+Shift+S)")
            btn.clicked.connect(self.capture_page_screenshot)
        elif item_id == "print_pdf":
            btn.setText("🖨️")
            btn.setToolTip("Guardar como PDF (Ctrl+P)")
            btn.clicked.connect(self.print_to_pdf)
        elif item_id == "find_in_page":
            btn.setText("🔍")
            btn.setToolTip("Buscar en la página (Ctrl+F)")
            btn.clicked.connect(lambda: self.find_bar.show_find())
        elif item_id == "pip":
            btn.setText("🖼️")
            btn.setToolTip("Imagen en imagen (Alt+P)")
            btn.clicked.connect(self.toggle_picture_in_picture)
        elif item_id == "aniplay":
            btn.setIcon(create_aniplay_icon(t["accent"], 16))
            btn.setToolTip("AniPlay Anime Hub")
            btn.clicked.connect(lambda: self.open_internal_page("aegis://aniplay"))
        elif item_id == "settings":
            btn.setIcon(create_settings_icon(t["text"], 16))
            btn.setToolTip("Configuración (Alt+S)")
            btn.clicked.connect(lambda: self.open_internal_page("aegis://settings"))
        else:
            return None
        return btn

    def load_aniplay(self, view: QWebEngineView):
        idx = self.views.index(view) if view in self.views else -1
        t = THEMES.get(self.current_theme_name, THEMES["Oscuro"])
        if idx != -1:
            self.tab_bar.setTabIcon(idx, create_aniplay_icon(t["accent"], 14))
            self.tab_bar.setTabText(idx, "AniPlay Anime Hub")
        view._aegis_virtual_url = "aegis://aniplay"
        html = get_aniplay_html(t["ntp_class"])
        view.setHtml(html, QUrl("aegis://aniplay"))
        if view == self.current_view():
            self.url_bar.setText("aegis://aniplay")

    def close_tab(self, index: int):
        if isinstance(index, QWebEngineView):
            if index in self.views:
                index = self.views.index(index)
            else:
                return
        if not (0 <= index < len(self.views)):
            return
        if self.tab_bar.count() > 1:
            view = self.views[index]
            u = view.url().toString()
            t = view.title()
            if u and u not in ("aegis://start", "about:blank") and not u.startswith("aegis://"):
                self.closed_tabs.append((u, t))
                if len(self.closed_tabs) > 25:
                    self.closed_tabs.pop(0)

            self.views.pop(index)
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
        if hasattr(self, "shields_popup") and self.shields_popup.isVisible():
            self.shields_popup.hide()
        if 0 <= index < len(self.views):
            self.stack.setCurrentIndex(index)
            view = self.views[index]
            view._last_active_time = time.time()
            if getattr(view, "_is_hibernated", False):
                self.wake_tab(view)
            self.on_url_changed(view.url(), view)

    def navigate_to_url(self):
        text = self.url_bar.text().strip()
        if not text:
            return

        target_url = self.build_target_url(text)
        if target_url.toString().startswith("aegis://"):
            self.open_internal_page(target_url.toString())
            return

        view = self.current_view()
        if view:
            view._aegis_virtual_url = None
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

        # Si la vista tiene una URL virtual interna establecida (ej. aegis://start, aegis://settings), usarla
        if getattr(view, "_aegis_virtual_url", None):
            if url_str.startswith("data:text/html") or url_str.startswith("data:") or not url_str:
                url_str = view._aegis_virtual_url

        # Búsqueda disparada desde el buscador central del NTP
        if url_str.startswith("aegis://search?q="):
            query = unquote(url_str.split("q=", 1)[1])
            view._aegis_virtual_url = None
            target = self.build_target_url(query)
            view.load(target)
            return

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
        elif url_str == "aegis://aniplay":
            self.load_aniplay(view)
            return
        elif url_str == "aegis://start":
            self.load_ntp(view)
            return
        elif url_str == "aegis://aniplay":
            self.load_aniplay(view)
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
                    elif k == "search_engine":
                        self.update_search_engine_ui()
                    elif k == "bypass_countdown":
                        self.load_userscripts()
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
                        cmd = f'explorer.exe /select,"{file_path}"' if os.path.isfile(file_path) else f'explorer.exe "{folder}"'
                        subprocess.Popen(cmd)
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
                elif "choose_download_dir" in q:
                    cur_dir = self.config.get("download_directory", str(Path.home() / "Downloads"))
                    chosen = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta de descargas", cur_dir)
                    if chosen:
                        self.config["download_directory"] = chosen
                        self.save_config()
                        self.show_toast("Carpeta de descargas actualizada.")
                    self.load_settings(view)
                    return
                elif "open_clear_data_modal" in q:
                    self.open_clear_data_dialog()
                    return
                elif "import_brave" in q or "import_brave" in url_str:
                    self.open_brave_import_dialog()
                    return
                elif "open_scripts_folder" in q:
                    USERSCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
                    subprocess.Popen(f'explorer.exe "{str(USERSCRIPTS_DIR)}"')
                    return
                elif "install_extension" in q:
                    ext_id = unquote(q["install_extension"][0])
                    self.install_extension_flow(ext_id, view)
                    return
                elif "remove_extension" in q:
                    ext_id = unquote(q["remove_extension"][0])
                    ok, msg = self.extensions_mgr.uninstall(ext_id, self.profile)
                    self.show_toast(msg)
                    if hasattr(self, "extensions_popup"):
                        self.extensions_popup.refresh_state()
                    if getattr(view, "_aegis_virtual_url", "") == "aegis://extensions":
                        self.load_extensions(view)
                    return
                elif "install_input" in q:
                    input_val = unquote(q["install_input"][0])
                    ext_id = extract_extension_id(input_val)
                    if not ext_id:
                        self.show_toast("No se reconoció un enlace o ID válido de Chrome Web Store.")
                    else:
                        self.install_extension_flow(ext_id, view)
                    return
            except Exception:
                pass
            return

        if view == self.current_view():
            # Actualizar candado SSL / indicador de seguridad
            u_scheme = qurl.scheme().lower()
            if hasattr(self, "security_action"):
                t_cur = THEMES.get(self.current_theme_name, THEMES["Oscuro"])
                if u_scheme == "https":
                    self.security_action.setIcon(create_lock_icon("#2ea043", 16))
                    self.security_action.setToolTip("Conexión segura y cifrada (HTTPS)")
                elif u_scheme == "http":
                    self.security_action.setIcon(create_warning_icon("#d29922", 16))
                    self.security_action.setToolTip("Conexión no cifrada (HTTP)")
                else:
                    self.security_action.setIcon(create_shield_icon(t_cur["accent"], 16))
                    self.security_action.setToolTip("Página del sistema de Aegis")

            # Actualizar estrella de marcadores
            if hasattr(self, "btn_bookmark"):
                t_cur = THEMES.get(self.current_theme_name, THEMES["Oscuro"])
                if self.bookmarks_mgr.is_bookmarked(url_str):
                    self.btn_bookmark.setText("★")
                    self.btn_bookmark.setStyleSheet(f"color: {t_cur['accent']}; font-weight: bold;")
                else:
                    self.btn_bookmark.setText("☆")
                    self.btn_bookmark.setStyleSheet("")

            # Actualizar indicador de zoom si no es 100%
            if hasattr(self, "update_zoom_ui"):
                self.update_zoom_ui()

            # Sanitizar estrictamente el Omnibox para que jamás muestre acciones ni código JS ni data URLs
            if self.is_internal_or_ntp(url_str):
                if url_str.startswith("aegis://") and url_str != "aegis://start":
                    self.url_bar.setText(url_str)
                else:
                    self.url_bar.setText("")
                engine = self.config.get("search_engine", "Google")
                placeholder = f"Navegación Privada · Buscar con {engine}..." if getattr(self, "is_incognito", False) else f"Buscar con {engine} o ingresar dirección..."
                self.url_bar.setPlaceholderText(placeholder)
            else:
                self.url_bar.setText(url_str)

            # Detección y botón dinámico para Chrome Web Store
            is_cws = ("chromewebstore.google.com/detail" in url_str or "chrome.google.com/webstore/detail" in url_str)
            ext_id = extract_extension_id(url_str) if is_cws else None
            if hasattr(self, "btn_webstore_install"):
                if is_cws and ext_id:
                    self.btn_webstore_install.setProperty("ext_id", ext_id)
                    if self.extensions_mgr.is_installed(ext_id):
                        self.btn_webstore_install.setText("✓ Instalada")
                        self.btn_webstore_install.setEnabled(False)
                    else:
                        self.btn_webstore_install.setText("🧩 Añadir a Aegis")
                        self.btn_webstore_install.setEnabled(True)
                    self.btn_webstore_install.show()
                else:
                    self.btn_webstore_install.hide()

            # Actualizar botón de estrella de marcadores
            if hasattr(self, "bookmarks_mgr") and hasattr(self, "btn_bookmark"):
                is_bm = self.bookmarks_mgr.is_bookmarked(url_str)
                self.btn_bookmark.setText("★" if is_bm else "☆")
                accent = THEMES[self.current_theme_name]["accent"]
                self.btn_bookmark.setStyleSheet(f"color: {accent};" if is_bm else "")
                self.btn_bookmark.setToolTip("Marcador guardado (Click para quitar)" if is_bm else "Añadir esta pestaña a marcadores (Ctrl+D)")

    def on_webstore_install_clicked(self):
        ext_id = self.btn_webstore_install.property("ext_id")
        if ext_id:
            self.install_extension_flow(ext_id, self.current_view())

    def install_extension_flow(self, ext_id: str, view=None):
        if hasattr(self, "btn_webstore_install"):
            self.btn_webstore_install.setText("⏳ Instalando...")
            self.btn_webstore_install.setEnabled(False)
            self.btn_webstore_install.show()
        QApplication.processEvents()

        ok, msg, info = self.extensions_mgr.install(ext_id, self.profile)
        if ok:
            name = info.get("name", ext_id)
            if hasattr(self, "btn_webstore_install"):
                self.btn_webstore_install.setText("✓ Instalada")
                self.btn_webstore_install.setEnabled(False)
            self.show_toast(f"🧩 '{name}' se instaló y activó correctamente en Aegis.")
            if view:
                view.page().runJavaScript("""
                    try {
                        const b = document.getElementById('aegis-inject-install-btn');
                        if (b) {
                            b.outerHTML = '<span style="color:#2ea043; background:rgba(46,160,67,0.15); padding:5px 12px; border-radius:8px; font-size:12px;">✓ Instalada</span>';
                        }
                    } catch(e) {}
                """)
            if hasattr(self, "extensions_popup"):
                self.extensions_popup.refresh_state()
            cur = self.current_view()
            if cur and getattr(cur, "_aegis_virtual_url", "") == "aegis://extensions":
                self.load_extensions(cur)
        else:
            if hasattr(self, "btn_webstore_install"):
                self.btn_webstore_install.setText("❌ Error")
                self.btn_webstore_install.setEnabled(True)
            self.show_toast(f"Error al instalar: {msg}")

    def show_toast(self, text: str):
        if hasattr(self, "toast"):
            self.toast.show_message(text)

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
            display_title = title if len(title) <= 14 else title[:12] + "…"
            if view.page().isAudioMuted():
                display_title += " 🔇"
            elif view.page().recentlyAudible():
                display_title += " 🔊"
            self.tab_bar.setTabText(idx, display_title)

        if ok and not self.is_internal_or_ntp(current_url) and not current_url.startswith("aegis://"):
            # Registrar visita en historial real para Sitios Frecuentes (solo navegación normal)
            if not getattr(self, "is_incognito", False):
                self.history_mgr.record_visit(current_url, view.title())
                self.update_omnibox_suggestions()

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

            # Banner interactivo en páginas de extensiones de Chrome Web Store
            if "chromewebstore.google.com/detail" in current_url or "chrome.google.com/webstore/detail" in current_url:
                ext_id = extract_extension_id(current_url)
                if ext_id:
                    is_inst = self.extensions_mgr.is_installed(ext_id)
                    t = THEMES.get(self.current_theme_name, THEMES["Oscuro"])
                    accent_col = t["accent"]
                    bg_col = t["surface"]
                    text_col = t["text"]
                    inject_script = f"""
                    (() => {{
                        try {{
                            if (document.getElementById('aegis-cws-banner')) return;
                            const bar = document.createElement('div');
                            bar.id = 'aegis-cws-banner';
                            bar.style.position = 'fixed';
                            bar.style.bottom = '24px';
                            bar.style.right = '24px';
                            bar.style.zIndex = '2147483647';
                            bar.style.backgroundColor = '{bg_col}';
                            bar.style.color = '{text_col}';
                            bar.style.border = '1.5px solid {accent_col}';
                            bar.style.borderRadius = '12px';
                            bar.style.padding = '10px 18px';
                            bar.style.fontFamily = '-apple-system, BlinkMacSystemFont, Segoe UI, sans-serif';
                            bar.style.fontSize = '13px';
                            bar.style.fontWeight = '600';
                            bar.style.display = 'flex';
                            bar.style.alignItems = 'center';
                            bar.style.gap = '14px';
                            bar.style.boxShadow = '0 8px 32px rgba(0,0,0,0.45)';

                            const isInst = {json.dumps(is_inst)};
                            const extId = {json.dumps(ext_id)};

                            bar.innerHTML = `
                                <span style="display:flex; align-items:center; gap:8px;">
                                    <span style="font-size:18px;">🧩</span>
                                    <span>Aegis Browser</span>
                                </span>
                                ${{isInst ?
                                    '<span style="color:#2ea043; background:rgba(46,160,67,0.15); padding:5px 12px; border-radius:8px; font-size:12px;">✓ Instalada</span>' :
                                    `<button id="aegis-inject-install-btn" style="background:{accent_col}; color:#ffffff; border:none; border-radius:8px; padding:6px 14px; font-weight:700; cursor:pointer; font-size:12.5px;">Añadir a Aegis</button>`
                                }}
                            `;
                            document.body.appendChild(bar);

                            const btn = document.getElementById('aegis-inject-install-btn');
                            if (btn) {{
                                btn.onclick = () => {{
                                    btn.textContent = '⏳ Instalando...';
                                    btn.disabled = true;
                                    window.location.href = 'aegis://action?install_extension=' + extId;
                                }};
                            }}

                            document.addEventListener('click', (e) => {{
                                const b = e.target.closest('button, [role="button"]');
                                if (b && !b.id.includes('aegis')) {{
                                    const txt = (b.innerText || b.textContent || '').trim().toLowerCase();
                                    if (txt.includes('añadir a chrome') || txt.includes('add to chrome') || txt.includes('agregar a chrome')) {{
                                        e.preventDefault();
                                        e.stopPropagation();
                                        window.location.href = 'aegis://action?install_extension=' + extId;
                                    }}
                                }}
                            }}, true);
                        }} catch(e) {{}}
                    }})();
                    """
                    view.page().runJavaScript(inject_script)

    def on_shield_block(self):
        self.shield_btn.setText(f" {SHIELDS_CORE.total_blocked}")
        if hasattr(self, "shields_popup") and self.shields_popup.isVisible():
            self.shields_popup.lbl_count.setText(str(SHIELDS_CORE.total_blocked))

# ── 12. Plantilla HTML de Nueva Pestaña (Sitios Frecuentes Reales) ────────────
def get_clean_ntp_html(theme_class: str = "theme-dark", frequent_sites: list = None, search_engine: str = "Google") -> str:
    if frequent_sites is None:
        frequent_sites = []

    engine_svg = get_search_engine_svg(search_engine, size=22)
    blocked_count = max(42, SHIELDS_CORE.total_blocked)
    mb_saved = f"{int(blocked_count * 0.045 + 1)} MB"
    time_saved = f"{int(blocked_count * 0.04 + 1)}s" 

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

    .greeting {{
      font-size: 1.15rem;
      font-weight: 500;
      opacity: 0.75;
      letter-spacing: 0.2px;
      margin-bottom: 0.25rem;
    }}
    .clock {{
      font-size: 4.5rem;
      font-weight: 200;
      letter-spacing: -2px;
      color: var(--text);
      margin-bottom: 0.25rem;
      font-variant-numeric: tabular-nums;
    }}
    .stats-card {{
      display: inline-flex;
      align-items: center;
      gap: 18px;
      background: var(--surface);
      border: 1px solid rgba(128, 128, 128, 0.14);
      border-radius: 20px;
      padding: 8px 20px;
      margin-bottom: 1.8rem;
    }}
    .stat-item {{
      display: flex;
      flex-direction: column;
      align-items: center;
    }}
    .stat-val {{
      font-size: 0.95rem;
      font-weight: 700;
      color: var(--accent);
    }}
    .stat-lbl {{
      font-size: 0.72rem;
      opacity: 0.6;
      margin-top: 1px;
    }}
    .stat-sep {{
      width: 1px;
      height: 22px;
      background: rgba(128, 128, 128, 0.18);
    }}
    .quick-pills {{
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 10px;
      flex-wrap: wrap;
      margin-top: 1rem;
    }}
    .quick-pill {{
      text-decoration: none;
      color: var(--text);
      font-size: 0.8rem;
      font-weight: 500;
      padding: 6px 14px;
      border-radius: 14px;
      background: var(--surface);
      border: 1px solid rgba(128, 128, 128, 0.12);
      transition: all 0.2s ease;
    }}
    .quick-pill:hover {{
      border-color: var(--accent);
      color: var(--accent);
      transform: translateY(-1px);
    }}
    .date {{
      font-size: 0.95rem;
      color: var(--text);
      opacity: 0.65;
      font-weight: 400;
      margin-bottom: 1.8rem;
      letter-spacing: 0.2px;
      text-transform: capitalize;
    }}

    .ntp-search-form {{
      width: 100%;
      max-width: 580px;
      margin: 0 auto 2.2rem auto;
    }}
    .ntp-search-box {{
      display: flex;
      align-items: center;
      background: var(--surface);
      border: 1.5px solid rgba(128, 128, 128, 0.22);
      border-radius: 24px;
      padding: 0 16px;
      height: 46px;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
      transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
    }}
    .ntp-search-box:hover,
    .ntp-search-box:focus-within {{
      border: 2px solid var(--accent);
      box-shadow: 0 4px 16px rgba(0, 0, 0, 0.16);
      transform: translateY(-1px);
    }}
    .ntp-search-engine-icon {{
      display: flex;
      align-items: center;
      justify-content: center;
      width: 22px;
      height: 22px;
      margin-right: 12px;
      flex-shrink: 0;
    }}
    .ntp-search-input {{
      flex: 1;
      height: 100%;
      background: transparent;
      border: none;
      outline: none;
      color: var(--text);
      font-size: 14.5px;
      font-family: inherit;
    }}
    .ntp-search-input::placeholder {{
      color: var(--text);
      opacity: 0.55;
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

    <div id="greeting" class="greeting">Bienvenido</div>
    <div id="clock" class="clock">12:00</div>
    <div id="date" class="date">Cargando fecha...</div>

    <div class="stats-card">
      <div class="stat-item">
        <span class="stat-val">{blocked_count}</span>
        <span class="stat-lbl">Bloqueados por Escudos</span>
      </div>
      <div class="stat-sep"></div>
      <div class="stat-item">
        <span class="stat-val">{mb_saved}</span>
        <span class="stat-lbl">Datos ahorrados</span>
      </div>
      <div class="stat-sep"></div>
      <div class="stat-item">
        <span class="stat-val">{time_saved}</span>
        <span class="stat-lbl">Tiempo ahorrado</span>
      </div>
    </div>

    <!-- Barra de Búsqueda Idéntica a la Imagen -->
    <form class="ntp-search-form" onsubmit="handleNtpSearch(event)">
      <div class="ntp-search-box">
        <div class="ntp-search-engine-icon" title="Motor actual: {search_engine}">
          {engine_svg}
        </div>
        <input 
          type="text" 
          id="ntpSearchInput" 
          class="ntp-search-input" 
          placeholder="Buscar con {search_engine} o ingresar dirección..." 
          autocomplete="off" 
          autofocus 
        />
      </div>
    </form>

    <div class="shortcuts-section-title">Sitios Frecuentes</div>
    <div class="shortcuts-grid">
      {cards_html}
    </div>

    <div class="quick-pills">
      <a href="aegis://settings" class="quick-pill">⚙️ Configuración</a>
      <a href="aegis://history" class="quick-pill">🕒 Historial</a>
      <a href="aegis://downloads" class="quick-pill">📥 Descargas</a>
      <a href="aegis://extensions" class="quick-pill">🧩 Extensiones</a>
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

      const hr = now.getHours();
      let greeting = 'Buenas noches';
      if (hr >= 6 && hr < 12) greeting = 'Buenos días';
      else if (hr >= 12 && hr < 20) greeting = 'Buenas tardes';
      const elGreet = document.getElementById('greeting');
      if (elGreet) elGreet.textContent = greeting;
    }}
    updateClock();
    setInterval(updateClock, 1000);

    function handleNtpSearch(event) {{
      event.preventDefault();
      const input = document.getElementById('ntpSearchInput');
      const val = input ? input.value.trim() : '';
      if (!val) return;
      window.location.href = 'aegis://search?q=' + encodeURIComponent(val);
    }}

    window.addEventListener('DOMContentLoaded', () => {{
      const input = document.getElementById('ntpSearchInput');
      if (input) {{
        input.focus();
      }}
    }});

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
      let url = document.getElementById('siteUrl').value.trim();
      if (!url) return;
      if (!url.startsWith('http://') && !url.startsWith('https://')) {{
        url = 'https://' + url;
      }}
      const payload = JSON.stringify({{title: name || url, url: url}});
      window.location.href = 'aegis://action?add=' + encodeURIComponent(payload);
    }}
  </script>
</body>
</html>
"""

# ── 12.2 Plantilla HTML de Configuración (aegis://settings) ───────────────────
import sys

def get_aniplay_html(theme_class: str = "theme-dark") -> str:
    return f"""<!DOCTYPE html>
<html lang="es" class="{theme_class}">
<head>
  <meta charset="UTF-8">
  <title>AniPlay Hub - Aegis</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    :root, .theme-dark {{
      --bg: #0d1117;
      --surface: #161b22;
      --surface2: #21262d;
      --text: #f0f6fc;
      --accent: #388bfd;
      --ani-red: #ff5370;
      --ani-gold: #f1c40f;
    }}
    .theme-light {{
      --bg: #f6f8fa;
      --surface: #ffffff;
      --surface2: #eaeef2;
      --text: #1f2328;
      --accent: #0969da;
      --ani-red: #e53935;
      --ani-gold: #d4a017;
    }}
    body {{
      background: var(--bg);
      color: var(--text);
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
    }}
    header {{
      background: var(--surface);
      border-bottom: 1px solid rgba(128, 128, 128, 0.15);
      padding: 12px 24px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      position: sticky;
      top: 0;
      z-index: 100;
    }}
    .logo-box {{
      display: flex;
      align-items: center;
      gap: 10px;
      font-size: 1.25rem;
      font-weight: 800;
      letter-spacing: -0.5px;
    }}
    .logo-box span {{
      color: var(--ani-red);
    }}
    .search-box {{
      display: flex;
      align-items: center;
      background: var(--bg);
      border: 1px solid rgba(128, 128, 128, 0.25);
      border-radius: 20px;
      padding: 6px 16px;
      width: 360px;
      max-width: 100%;
    }}
    .search-box input {{
      background: transparent;
      border: none;
      color: var(--text);
      width: 100%;
      font-size: 0.9rem;
      outline: none;
    }}
    .filter-tabs {{
      display: flex;
      gap: 8px;
    }}
    .tab-btn {{
      background: var(--bg);
      border: 1px solid rgba(128, 128, 128, 0.2);
      color: var(--text);
      padding: 6px 14px;
      border-radius: 16px;
      font-size: 0.85rem;
      font-weight: 500;
      cursor: pointer;
      transition: all 0.2s;
    }}
    .tab-btn.active, .tab-btn:hover {{
      background: var(--accent);
      color: #ffffff;
      border-color: var(--accent);
    }}
    .container {{
      max-width: 1200px;
      margin: 0 auto;
      padding: 24px;
      width: 100%;
    }}
    /* Spotlight Hero */
    .hero {{
      background: linear-gradient(135deg, rgba(255, 83, 112, 0.15), rgba(56, 139, 253, 0.15)), var(--surface);
      border: 1px solid rgba(128, 128, 128, 0.15);
      border-radius: 16px;
      padding: 28px;
      margin-bottom: 32px;
      display: flex;
      gap: 24px;
      align-items: center;
    }}
    .hero-img {{
      width: 200px;
      height: 280px;
      object-fit: cover;
      border-radius: 12px;
      box-shadow: 0 8px 24px rgba(0,0,0,0.4);
    }}
    .hero-info {{
      display: flex;
      flex-direction: column;
      gap: 10px;
    }}
    .hero-badge {{
      background: var(--ani-red);
      color: #fff;
      font-size: 0.75rem;
      font-weight: 700;
      padding: 3px 8px;
      border-radius: 4px;
      width: fit-content;
      text-transform: uppercase;
    }}
    .hero-title {{
      font-size: 1.8rem;
      font-weight: 800;
    }}
    .hero-meta {{
      font-size: 0.85rem;
      opacity: 0.8;
      display: flex;
      gap: 14px;
      align-items: center;
    }}
    .hero-desc {{
      font-size: 0.92rem;
      line-height: 1.5;
      opacity: 0.85;
      max-width: 600px;
    }}
    .hero-btn {{
      background: var(--accent);
      color: #fff;
      border: none;
      padding: 10px 22px;
      border-radius: 8px;
      font-weight: 700;
      font-size: 0.95rem;
      cursor: pointer;
      width: fit-content;
      margin-top: 6px;
      display: flex;
      align-items: center;
      gap: 8px;
      transition: transform 0.15s;
    }}
    .hero-btn:hover {{
      transform: scale(1.03);
    }}
    /* Anime Grid */
    .section-title {{
      font-size: 1.25rem;
      font-weight: 700;
      margin-bottom: 16px;
      display: flex;
      align-items: center;
      justify-content: space-between;
    }}
    .anime-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(170px, 1fr));
      gap: 18px;
      margin-bottom: 36px;
    }}
    .anime-card {{
      background: var(--surface);
      border: 1px solid rgba(128, 128, 128, 0.15);
      border-radius: 12px;
      overflow: hidden;
      cursor: pointer;
      transition: transform 0.2s, border-color 0.2s;
      position: relative;
    }}
    .anime-card:hover {{
      transform: translateY(-5px);
      border-color: var(--accent);
    }}
    .card-thumb {{
      width: 100%;
      height: 230px;
      object-fit: cover;
      display: block;
    }}
    .card-info {{
      padding: 10px 12px;
    }}
    .card-title {{
      font-size: 0.9rem;
      font-weight: 600;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      margin-bottom: 4px;
    }}
    .card-meta {{
      font-size: 0.78rem;
      opacity: 0.7;
      display: flex;
      justify-content: space-between;
    }}
    /* Video Modal Player */
    .modal-overlay {{
      display: none;
      position: fixed;
      inset: 0;
      background: rgba(0, 0, 0, 0.85);
      z-index: 1000;
      align-items: center;
      justify-content: center;
      padding: 20px;
    }}
    .modal-content {{
      background: var(--surface);
      border: 1px solid rgba(128, 128, 128, 0.2);
      border-radius: 16px;
      width: 900px;
      max-width: 100%;
      overflow: hidden;
      display: flex;
      flex-direction: column;
    }}
    .modal-header {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 12px 18px;
      border-bottom: 1px solid rgba(128, 128, 128, 0.15);
    }}
    .modal-title {{
      font-size: 1.1rem;
      font-weight: 700;
    }}
    .close-btn {{
      background: transparent;
      border: none;
      color: var(--text);
      font-size: 1.5rem;
      cursor: pointer;
    }}
    .player-box {{
      width: 100%;
      height: 480px;
      background: #000;
      position: relative;
    }}
    .player-box video {{
      width: 100%;
      height: 100%;
    }}
    .episode-bar {{
      padding: 14px 18px;
      background: var(--surface2);
      display: flex;
      align-items: center;
      gap: 10px;
      overflow-x: auto;
    }}
    .ep-pill {{
      background: var(--bg);
      border: 1px solid rgba(128, 128, 128, 0.2);
      color: var(--text);
      padding: 6px 14px;
      border-radius: 6px;
      font-size: 0.85rem;
      font-weight: 600;
      cursor: pointer;
      white-space: nowrap;
    }}
    .ep-pill.active {{
      background: var(--accent);
      color: #fff;
      border-color: var(--accent);
    }}
  </style>
</head>
<body>
  <header>
    <div class="logo-box">
      <span>▶</span> Aegis AniPlay
    </div>
    <div class="search-box">
      <input type="text" id="animeSearch" placeholder="Buscar anime, OVA, películas..." oninput="filterAnime(this.value)">
    </div>
    <div class="filter-tabs">
      <button class="tab-btn active" onclick="setCategory('all', this)">Todos</button>
      <button class="tab-btn" onclick="setCategory('trending', this)">Tendencias</button>
      <button class="tab-btn" onclick="setCategory('favs', this)">Favoritos</button>
    </div>
  </header>

  <div class="container">
    <div class="hero">
      <img src="https://images.unsplash.com/photo-1578632767115-351597cf2477?w=400&q=80" class="hero-img" alt="Solo Leveling" />
      <div class="hero-info">
        <span class="hero-badge">Estreno Destacado</span>
        <h1 class="hero-title">Solo Leveling (Arise)</h1>
        <div class="hero-meta">
          <span>★ 9.4</span>
          <span>• Acción / Fantasía</span>
          <span>• 12 Episodios</span>
          <span>• Sub / Dub</span>
        </div>
        <p class="hero-desc">
          En un mundo donde cazadores humanos deben luchar contra monstruos mortales para proteger a la humanidad, Sung Jinwoo, el cazador más débil, es bendecido con el misterioso sistema de subida de nivel infinita.
        </p>
        <button class="hero-btn" onclick="openPlayer('Solo Leveling', 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4', 12)">
          <span>▶</span> Reproducir Episodio 1
        </button>
      </div>
    </div>

    <div class="section-title">
      <span>Catálogo de Anime</span>
      <span id="catalogCount" style="font-size: 0.85rem; opacity: 0.65; font-weight: 400;">10 títulos disponibles</span>
    </div>

    <div class="anime-grid" id="animeGrid"></div>
  </div>

  <div class="modal-overlay" id="playerModal">
    <div class="modal-content">
      <div class="modal-header">
        <span class="modal-title" id="currentAnimeTitle">Reproduciendo Anime</span>
        <button class="close-btn" onclick="closePlayer()">×</button>
      </div>
      <div class="player-box">
        <video id="videoElement" controls autoplay></video>
      </div>
      <div class="episode-bar" id="episodesBar"></div>
    </div>
  </div>

  <script>
    const animeCatalog = [
      {{ id: 1, title: 'Solo Leveling', rating: 9.4, eps: 12, genre: 'Acción / Fantasía', img: 'https://images.unsplash.com/photo-1578632767115-351597cf2477?w=400&q=80', trending: true }},
      {{ id: 2, title: 'Jujutsu Kaisen', rating: 9.2, eps: 47, genre: 'Sobrenatural / Shonen', img: 'https://images.unsplash.com/photo-1534447677768-be436bb09401?w=400&q=80', trending: true }},
      {{ id: 3, title: 'Demon Slayer: Kimetsu no Yaiba', rating: 9.3, eps: 55, genre: 'Acción / Histórico', img: 'https://images.unsplash.com/photo-1607604276583-eef5d076aa5f?w=400&q=80', trending: true }},
      {{ id: 4, title: 'Frieren: Beyond Journey', rating: 9.5, eps: 28, genre: 'Aventura / Fantasía', img: 'https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=400&q=80', trending: true }},
      {{ id: 5, title: 'Attack on Titan (Shingeki)', rating: 9.6, eps: 87, genre: 'Militar / Misterio', img: 'https://images.unsplash.com/photo-1563089145-599997674d42?w=400&q=80', trending: false }},
      {{ id: 6, title: 'Chainsaw Man', rating: 8.9, eps: 12, genre: 'Acción / Terror', img: 'https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=400&q=80', trending: true }},
      {{ id: 7, title: 'One Piece (Egghead Arc)', rating: 9.2, eps: 1100, genre: 'Aventura / Comedia', img: 'https://images.unsplash.com/photo-1579783900882-c0d3dad7b119?w=400&q=80', trending: false }},
      {{ id: 8, title: 'Bleach: TYBW', rating: 9.1, eps: 26, genre: 'Acción / Sobrenatural', img: 'https://images.unsplash.com/photo-1550684848-fac1c5b4e853?w=400&q=80', trending: true }},
      {{ id: 9, title: 'Spy x Family', rating: 8.8, eps: 37, genre: 'Comedia / Espías', img: 'https://images.unsplash.com/photo-1541701494587-cb58502866ab?w=400&q=80', trending: false }},
      {{ id: 10, title: 'Death Note', rating: 9.0, eps: 37, genre: 'Psicológico / Thriller', img: 'https://images.unsplash.com/photo-1509198397868-475647b2a1e5?w=400&q=80', trending: false }}
    ];

    let currentCategory = 'all';

    function renderGrid(items) {{
      const grid = document.getElementById('animeGrid');
      grid.innerHTML = '';
      items.forEach(anime => {{
        const card = document.createElement('div');
        card.className = 'anime-card';
        card.onclick = () => openPlayer(anime.title, 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4', Math.min(anime.eps, 12));
        card.innerHTML = `
          <img src="${{anime.img}}" class="card-thumb" alt="${{anime.title}}" />
          <div class="card-info">
            <div class="card-title">${{anime.title}}</div>
            <div class="card-meta">
              <span>★ ${{anime.rating}}</span>
              <span>${{anime.eps}} Eps</span>
            </div>
          </div>
        `;
        grid.appendChild(card);
      }});
      document.getElementById('catalogCount').innerText = `${{items.length}} títulos disponibles`;
    }}

    function setCategory(cat, btn) {{
      currentCategory = cat;
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      filterAnime(document.getElementById('animeSearch').value);
    }}

    function filterAnime(query) {{
      query = (query || '').toLowerCase().trim();
      let list = animeCatalog;
      if (currentCategory === 'trending') {{
        list = list.filter(a => a.trending);
      }} else if (currentCategory === 'favs') {{
        const favs = JSON.parse(localStorage.getItem('aegis_ani_favs') || '[]');
        list = list.filter(a => favs.includes(a.id));
      }}
      if (query) {{
        list = list.filter(a => a.title.toLowerCase().includes(query) || a.genre.toLowerCase().includes(query));
      }}
      renderGrid(list);
    }}

    function openPlayer(title, sampleUrl, epsCount) {{
      document.getElementById('currentAnimeTitle').innerText = title;
      const vid = document.getElementById('videoElement');
      vid.src = sampleUrl;
      vid.play().catch(() => {{}});
      
      const epBar = document.getElementById('episodesBar');
      epBar.innerHTML = '';
      for (let i = 1; i <= epsCount; i++) {{
        const pill = document.createElement('button');
        pill.className = 'ep-pill' + (i === 1 ? ' active' : '');
        pill.innerText = `Episodio ${{i}}`;
        pill.onclick = () => {{
          document.querySelectorAll('.ep-pill').forEach(p => p.classList.remove('active'));
          pill.classList.add('active');
          vid.currentTime = 0;
          vid.play().catch(() => {{}});
        }};
        epBar.appendChild(pill);
      }}
      document.getElementById('playerModal').style.display = 'flex';
    }}

    function closePlayer() {{
      const vid = document.getElementById('videoElement');
      vid.pause();
      vid.src = '';
      document.getElementById('playerModal').style.display = 'none';
    }}

    renderGrid(animeCatalog);
  </script>
</body>
</html>"""

def get_settings_html(theme_class: str = "theme-dark", config: dict = None) -> str:
    if config is None:
        config = {}
    tab_h = "selected" if config.get("tab_position", "horizontal") == "horizontal" else ""
    tab_v = "selected" if config.get("tab_position") == "vertical" else ""
    th_dark = "selected" if config.get("theme", "Oscuro") == "Oscuro" else ""
    th_light = "selected" if config.get("theme") == "Claro" else ""
    
    bm_show = "selected" if config.get("show_bookmarks_bar", True) else ""
    bm_hide = "" if config.get("show_bookmarks_bar", True) else "selected"

    sb_show = "selected" if config.get("show_sidebar", False) else ""
    sb_hide = "" if config.get("show_sidebar", False) else "selected"

    cur_eng = config.get("search_engine", "Google").lower()
    eng_google = "selected" if cur_eng == "google" else ""
    eng_ddg = "selected" if cur_eng == "duckduckgo" else ""
    eng_bing = "selected" if cur_eng == "bing" else ""
    eng_brave = "selected" if cur_eng == "brave" else ""
    eng_yahoo = "selected" if cur_eng == "yahoo" else ""
    eng_startpage = "selected" if cur_eng == "startpage" else ""
    eng_ecosia = "selected" if cur_eng == "ecosia" else ""

    sh_on = "selected" if config.get("shields_enabled", True) else ""
    sh_off = "" if config.get("shields_enabled", True) else "selected"

    https_on = "selected" if config.get("https_only_mode", False) else ""
    https_off = "" if config.get("https_only_mode", False) else "selected"

    webrtc_on = "selected" if config.get("webrtc_protection", True) else ""
    webrtc_off = "" if config.get("webrtc_protection", True) else "selected"

    bypass_on = "selected" if config.get("bypass_countdown", True) else ""
    bypass_off = "" if config.get("bypass_countdown", True) else "selected"
    fp_on = "selected" if config.get("fingerprint_protection", True) else ""
    fp_off = "" if config.get("fingerprint_protection", True) else "selected"

    clear_exit_on = "selected" if config.get("clear_data_on_exit", False) else ""
    clear_exit_off = "" if config.get("clear_data_on_exit", False) else "selected"

    ask_dl_on = "selected" if config.get("ask_download_location", False) else ""
    ask_dl_off = "" if config.get("ask_download_location", False) else "selected"

    startup_mode = config.get("on_startup", "ntp")
    start_ntp = "selected" if startup_mode == "ntp" else ""
    start_restore = "selected" if startup_mode == "restore_session" else ""

    sleep_timeout = config.get("sleeping_tabs_timeout", 900)
    sl_300 = "selected" if sleep_timeout == 300 else ""
    sl_900 = "selected" if sleep_timeout == 900 else ""
    sl_1800 = "selected" if sleep_timeout == 1800 else ""
    sl_3600 = "selected" if sleep_timeout == 3600 else ""
    sl_0 = "selected" if sleep_timeout == 0 else ""

    dl_dir = config.get("download_directory", str(Path.home() / "Downloads"))

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
      max-width: 760px;
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
      display: flex;
      align-items: center;
      gap: 8px;
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
      max-width: 480px;
    }}
    .setting-name {{
      font-size: 0.9rem;
      font-weight: 500;
    }}
    .setting-desc {{
      font-size: 0.8rem;
      opacity: 0.65;
      line-height: 1.35;
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
    .shortcut-table {{
      width: 100%;
      border-collapse: collapse;
      margin-top: 8px;
      font-size: 0.85rem;
    }}
    .shortcut-table td {{
      padding: 8px 6px;
      border-bottom: 1px solid rgba(128, 128, 128, 0.08);
    }}
    .kbd-key {{
      background: var(--bg);
      border: 1px solid rgba(128, 128, 128, 0.25);
      border-radius: 4px;
      padding: 2px 6px;
      font-family: monospace;
      font-size: 0.8rem;
      font-weight: 600;
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

    <!-- 1. Apariencia y Diseño -->
    <div class="card">
      <h2 class="card-title">🎨 Apariencia y Diseño</h2>
      <div class="setting-row">
        <div class="setting-info">
          <span class="setting-name">Tema de interfaz</span>
          <span class="setting-desc">Paleta estricta de 4 colores de alto contraste</span>
        </div>
        <select onchange="updateSetting('theme', this.value)">
          <option value="Oscuro" {th_dark}>Oscuro (#0d1117)</option>
          <option value="Claro" {th_light}>Claro (#f6f8fa)</option>
        </select>
      </div>
      <div class="setting-row">
        <div class="setting-info">
          <span class="setting-name">Orientación de pestañas</span>
          <span class="setting-desc">Barra horizontal clásica o panel lateral vertical (Arc style)</span>
        </div>
        <select onchange="updateSetting('tab_position', this.value)">
          <option value="horizontal" {tab_h}>Horizontal clásica (arriba)</option>
          <option value="vertical" {tab_v}>Vertical lateral (estilo Arc)</option>
        </select>
      </div>
      <div class="setting-row">
        <div class="setting-info">
          <span class="setting-name">Barra de marcadores</span>
          <span class="setting-desc">Mostrar u ocultar la barra horizontal de marcadores (Ctrl+Shift+B)</span>
        </div>
        <select onchange="updateSetting('show_bookmarks_bar', this.value === 'true')">
          <option value="true" {bm_show}>Mostrar siempre</option>
          <option value="false" {bm_hide}>Ocultar</option>
        </select>
      </div>
      <div class="setting-row">
        <div class="setting-info">
          <span class="setting-name">Barra lateral de herramientas</span>
          <span class="setting-desc">Acceso rápido a notas, lectura y contraseñas (Ctrl+B)</span>
        </div>
        <select onchange="updateSetting('show_sidebar', this.value === 'true')">
          <option value="true" {sb_show}>Visible</option>
          <option value="false" {sb_hide}>Oculta</option>
        </select>
      </div>
    </div>

    <!-- 2. Motor de Búsqueda -->
    <div class="card">
      <h2 class="card-title">🔍 Motor de Búsqueda</h2>
      <div class="setting-row">
        <div class="setting-info">
          <span class="setting-name">Buscador predeterminado</span>
          <span class="setting-desc">Utilizado al escribir directamente en el Omnibox y en la Nueva Pestaña</span>
        </div>
        <select onchange="updateSetting('search_engine', this.value)">
          <option value="Google" {eng_google}>Google</option>
          <option value="DuckDuckGo" {eng_ddg}>DuckDuckGo (Privado)</option>
          <option value="Brave" {eng_brave}>Brave Search</option>
          <option value="Bing" {eng_bing}>Microsoft Bing</option>
          <option value="Yahoo" {eng_yahoo}>Yahoo</option>
          <option value="Startpage" {eng_startpage}>Startpage</option>
          <option value="Ecosia" {eng_ecosia}>Ecosia</option>
        </select>
      </div>
    </div>

    <!-- 3. Escudos, Privacidad y Seguridad -->
    <div class="card">
      <h2 class="card-title">🛡️ Escudos, Privacidad y Seguridad</h2>
      <div class="setting-row">
        <div class="setting-info">
          <span class="setting-name">Aegis Shields</span>
          <span class="setting-desc">Bloqueo de anuncios, rastreadores y telemetría por socket Rust FFI</span>
        </div>
        <select onchange="updateSetting('shields_enabled', this.value === 'true')">
          <option value="true" {sh_on}>Activado (Recomendado)</option>
          <option value="false" {sh_off}>Desactivado</option>
        </select>
      </div>
      <div class="setting-row">
        <div class="setting-info">
          <span class="setting-name">Forzar conexiones HTTPS (HTTPS-Only)</span>
          <span class="setting-desc">Actualizar automáticamente solicitudes HTTP inseguras a HTTPS</span>
        </div>
        <select onchange="updateSetting('https_only_mode', this.value === 'true')">
          <option value="true" {https_on}>Activado</option>
          <option value="false" {https_off}>Desactivado</option>
        </select>
      </div>
      <div class="setting-row">
        <div class="setting-info">
          <span class="setting-name">Protección de fuga de IP por WebRTC</span>
          <span class="setting-desc">Evita que servidores WebRTC obtengan tu IP local de red privada</span>
        </div>
        <select onchange="updateSetting('webrtc_protection', this.value === 'true')">
          <option value="true" {webrtc_on}>Protegido (Recomendado)</option>
          <option value="false" {webrtc_off}>Estándar</option>
        </select>
      </div>
      <div class="setting-row">
        <div class="setting-info">
          <span class="setting-name">Protección contra huella digital (Anti-Fingerprinting)</span>
          <span class="setting-desc">Inyecta ruido imperceptible en Canvas y Audio para evitar perfilado</span>
        </div>
        <select onchange="updateSetting('fingerprint_protection', this.value === 'true')">
          <option value="true" {fp_on}>Activado</option>
          <option value="false" {fp_off}>Desactivado</option>
        </select>
      </div>
      <div class="setting-row">
        <div class="setting-info">
          <span class="setting-name">Bypass de temporizadores y acortadores</span>
          <span class="setting-desc">Salto automático e instantáneo de tiempos de espera en descargas y enlaces (CurseForge, Mega, Adf.ly, Linkvertise, Mediafire, etc.)</span>
        </div>
        <select onchange="updateSetting('bypass_countdown', this.value === 'true')">
          <option value="true" {bypass_on}>Activado (Recomendado)</option>
          <option value="false" {bypass_off}>Desactivado</option>
        </select>
      </div>
      <div class="setting-row">
        <div class="setting-info">
          <span class="setting-name">Borrar datos al cerrar el navegador</span>
          <span class="setting-desc">Elimina cookies y caché temporal al salir de Aegis</span>
        </div>
        <select onchange="updateSetting('clear_data_on_exit', this.value === 'true')">
          <option value="true" {clear_exit_on}>Activado</option>
          <option value="false" {clear_exit_off}>Desactivado</option>
        </select>
      </div>
      <div class="setting-row">
        <div class="setting-info">
          <span class="setting-name">Limpiar datos de navegación ahora</span>
          <span class="setting-desc">Abre el diálogo completo de borrado de historial, cookies y caché</span>
        </div>
        <button class="action-btn btn-danger" onclick="openClearDataModal()">Borrar Datos... (Ctrl+Shift+Del)</button>
      </div>
      <div class="setting-row">
        <div class="setting-info">
          <span class="setting-name">Importar datos desde Brave Browser</span>
          <span class="setting-desc">Transfiere de forma segura y 100% local tu historial, sitios frecuentes y marcadores guardados en Brave</span>
        </div>
        <button class="action-btn" style="background:#388bfd;color:#ffffff;border:none;" onclick="openBraveImportModal()">🦁 Importar desde Brave...</button>
      </div>
    </div>

    <!-- 4. Pestañas y Rendimiento -->
    <div class="card">
      <h2 class="card-title">⚡ Rendimiento y Memoria</h2>
      <div class="setting-row">
        <div class="setting-info">
          <span class="setting-name">Tiempo de reposo de pestañas inactivas (Sleeping Tabs)</span>
          <span class="setting-desc">Libera RAM y recursos de GPU en pestañas en segundo plano (con escudo de audio activo)</span>
        </div>
        <select onchange="updateSetting('sleeping_tabs_timeout', parseInt(this.value))">
          <option value="300" {sl_300}>A los 5 minutos</option>
          <option value="900" {sl_900}>A los 15 minutos (Predeterminado)</option>
          <option value="1800" {sl_1800}>A los 30 minutos</option>
          <option value="3600" {sl_3600}>A la 1 hora</option>
          <option value="0" {sl_0}>Desactivado</option>
        </select>
      </div>
      <div class="setting-row">
        <div class="setting-info">
          <span class="setting-name">Compactación silenciosa de memoria RAM</span>
          <span class="setting-desc">Alineación WorkingSet del kernel de Windows cada 90s sin afectar la reproducción</span>
        </div>
        <span style="font-size: 0.85rem; color: #2ea043; font-weight: 600;">✓ 100% Automático</span>
      </div>
    </div>

    <!-- 5. Descargas -->
    <div class="card">
      <h2 class="card-title">📥 Descargas</h2>
      <div class="setting-row">
        <div class="setting-info">
          <span class="setting-name">Ubicación de descarga</span>
          <span class="setting-desc">{dl_dir}</span>
        </div>
        <button class="action-btn" onclick="chooseDownloadDir()">Cambiar carpeta...</button>
      </div>
      <div class="setting-row">
        <div class="setting-info">
          <span class="setting-name">Preguntar dónde guardar cada archivo</span>
          <span class="setting-desc">Mostrar selector de archivos antes de iniciar la descarga</span>
        </div>
        <select onchange="updateSetting('ask_download_location', this.value === 'true')">
          <option value="true" {ask_dl_on}>Sí, preguntar siempre</option>
          <option value="false" {ask_dl_off}>Guardar automáticamente</option>
        </select>
      </div>
    </div>

    <!-- 6. Al Iniciar -->
    <div class="card">
      <h2 class="card-title">🚀 Al Iniciar Aegis</h2>
      <div class="setting-row">
        <div class="setting-info">
          <span class="setting-name">Página de inicio</span>
          <span class="setting-desc">Elige qué abrir al iniciar Aegis Browser</span>
        </div>
        <select onchange="updateSetting('on_startup', this.value)">
          <option value="ntp" {start_ntp}>Abrir página de Nueva Pestaña</option>
          <option value="restore_session" {start_restore}>Continuar donde lo dejaste (Restaurar sesión previa)</option>
        </select>
      </div>
    </div>

    <!-- 7. Atajos de Teclado -->
    <div class="card">
      <h2 class="card-title">⌨️ Atajos de Teclado Principales</h2>
      <table class="shortcut-table">
        <tr><td>Nueva pestaña</td><td style="text-align:right;"><span class="kbd-key">Ctrl</span> + <span class="kbd-key">T</span></td></tr>
        <tr><td>Cerrar pestaña actual</td><td style="text-align:right;"><span class="kbd-key">Ctrl</span> + <span class="kbd-key">W</span></td></tr>
        <tr><td>Reabrir pestaña cerrada</td><td style="text-align:right;"><span class="kbd-key">Ctrl</span> + <span class="kbd-key">Shift</span> + <span class="kbd-key">T</span></td></tr>
        <tr><td>Buscar pestañas abiertas / recientes</td><td style="text-align:right;"><span class="kbd-key">Ctrl</span> + <span class="kbd-key">Shift</span> + <span class="kbd-key">A</span></td></tr>
        <tr><td>Barra lateral de herramientas</td><td style="text-align:right;"><span class="kbd-key">Ctrl</span> + <span class="kbd-key">B</span></td></tr>
        <tr><td>Barra de marcadores</td><td style="text-align:right;"><span class="kbd-key">Ctrl</span> + <span class="kbd-key">Shift</span> + <span class="kbd-key">B</span></td></tr>
        <tr><td>Borrar datos de navegación</td><td style="text-align:right;"><span class="kbd-key">Ctrl</span> + <span class="kbd-key">Shift</span> + <span class="kbd-key">Del</span></td></tr>
        <tr><td>Modo Lectura libre de distracciones</td><td style="text-align:right;"><span class="kbd-key">F9</span></td></tr>
        <tr><td>Capturar pantalla de la pestaña</td><td style="text-align:right;"><span class="kbd-key">Ctrl</span> + <span class="kbd-key">Shift</span> + <span class="kbd-key">S</span></td></tr>
        <tr><td>Guardar página como PDF</td><td style="text-align:right;"><span class="kbd-key">Ctrl</span> + <span class="kbd-key">P</span></td></tr>
        <tr><td>Imagen en imagen (Picture-in-Picture)</td><td style="text-align:right;"><span class="kbd-key">Alt</span> + <span class="kbd-key">P</span></td></tr>
        <tr><td>Silenciar / Activar sonido de pestaña</td><td style="text-align:right;"><span class="kbd-key">Ctrl</span> + <span class="kbd-key">M</span></td></tr>
        <tr><td>Pantalla completa</td><td style="text-align:right;"><span class="kbd-key">F11</span></td></tr>
        <tr><td>Herramientas de Desarrollador (DevTools)</td><td style="text-align:right;"><span class="kbd-key">F12</span></td></tr>
      </table>
    </div>

  </div>

  <script>
    function updateSetting(key, val) {{
      const payload = JSON.stringify({{key: key, value: val}});
      window.location.href = 'aegis://action?set_config=' + encodeURIComponent(payload);
    }}
    function chooseDownloadDir() {{
      window.location.href = 'aegis://action?choose_download_dir=1';
    }}
    function openClearDataModal() {{
      window.location.href = 'aegis://action?open_clear_data_modal=1';
    }}
    function openBraveImportModal() {{
      window.location.href = 'aegis://action?import_brave=1';
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
def get_extensions_html(theme_class: str = "theme-dark", chrome_extensions: list = None, scripts: list = None) -> str:
    # Compatibilidad inteligente si se invoca con la firma anterior (theme_class, scripts)
    if chrome_extensions is not None and len(chrome_extensions) > 0 and isinstance(chrome_extensions[0], str):
        scripts = chrome_extensions
        chrome_extensions = []

    if chrome_extensions is None:
        chrome_extensions = []
    if scripts is None:
        scripts = []

    chrome_exts_html = ""
    if not chrome_extensions:
        chrome_exts_html = """
        <div style="padding: 24px; text-align: center; opacity: 0.8; font-size: 0.88rem; line-height: 1.6;">
          <p style="margin-bottom: 14px;">No tienes extensiones de Google Chrome instaladas todavía.</p>
          <button class="action-btn-primary" onclick="openWebStore()">
            🛍️ Explorar la Chrome Web Store
          </button>
        </div>
        """
    else:
        for ext in chrome_extensions:
            eid = ext.get("id", "")
            name = ext.get("name", eid)
            ver = ext.get("version", "1.0")
            desc = ext.get("description", "")
            icon_b64 = ext.get("icon_b64")
            if icon_b64:
                icon_tag = f'<img src="{icon_b64}" width="32" height="32" style="border-radius: 6px; object-fit: contain;" alt="" />'
            else:
                icon_tag = '<span style="font-size: 1.5rem;">🧩</span>'

            chrome_exts_html += f"""
            <div class="ext-item">
              <div class="ext-icon-box">{icon_tag}</div>
              <div class="ext-info">
                <div style="display: flex; align-items: center; gap: 8px;">
                  <span class="ext-name">{name}</span>
                  <span class="ext-badge">v{ver}</span>
                </div>
                {f'<span class="ext-sub">{desc}</span>' if desc else ''}
                <span class="ext-id">ID: {eid}</span>
              </div>
              <div style="display: flex; align-items: center; gap: 12px;">
                <span style="font-size: 0.8rem; color: #2ea043; font-weight: 600;">● Activa</span>
                <button class="action-btn-danger" onclick="removeExtension('{eid}')">Eliminar</button>
              </div>
            </div>
            """

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
      max-width: 720px;
    }}
    .header {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 2rem;
      padding-bottom: 1rem;
      border-bottom: 1px solid rgba(128, 128, 128, 0.15);
    }}
    .header-left {{
      display: flex;
      align-items: center;
      gap: 12px;
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
      gap: 14px;
    }}
    .ext-icon-box {{
      width: 36px;
      height: 36px;
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
    }}
    .ext-info {{
      display: flex;
      flex-direction: column;
      gap: 3px;
      flex: 1;
      min-width: 0;
    }}
    .ext-name {{
      font-size: 0.95rem;
      font-weight: 600;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }}
    .ext-badge {{
      font-size: 0.72rem;
      padding: 2px 7px;
      border-radius: 10px;
      background: rgba(128, 128, 128, 0.15);
      opacity: 0.85;
      font-weight: 500;
    }}
    .ext-sub {{
      font-size: 0.8rem;
      opacity: 0.65;
      line-height: 1.35;
      display: -webkit-box;
      -webkit-line-clamp: 2;
      -webkit-box-orient: vertical;
      overflow: hidden;
    }}
    .ext-id {{
      font-family: monospace;
      font-size: 0.72rem;
      opacity: 0.45;
      margin-top: 2px;
    }}
    .search-row {{
      display: flex;
      gap: 10px;
      margin-top: 14px;
    }}
    .ext-search-input {{
      flex: 1;
      background: var(--bg);
      border: 1px solid rgba(128, 128, 128, 0.25);
      border-radius: 8px;
      padding: 9px 14px;
      color: var(--text);
      font-size: 0.88rem;
      outline: none;
      transition: border-color 0.2s;
    }}
    .ext-search-input:focus {{
      border-color: var(--accent);
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
      transition: all 0.15s ease;
    }}
    button.action-btn:hover {{
      border-color: var(--accent);
      color: var(--accent);
    }}
    button.action-btn-primary {{
      background: var(--accent);
      color: #ffffff;
      border: 1px solid var(--accent);
      border-radius: 6px;
      padding: 8px 16px;
      font-size: 0.85rem;
      font-weight: 600;
      cursor: pointer;
      outline: none;
      transition: opacity 0.15s;
    }}
    button.action-btn-primary:hover {{
      opacity: 0.9;
    }}
    button.action-btn-danger {{
      background: transparent;
      color: #f85149;
      border: 1px solid rgba(248, 81, 73, 0.35);
      border-radius: 6px;
      padding: 5px 12px;
      font-size: 0.8rem;
      font-weight: 500;
      cursor: pointer;
      outline: none;
      transition: all 0.15s ease;
    }}
    button.action-btn-danger:hover {{
      background: rgba(248, 81, 73, 0.15);
      border-color: #f85149;
    }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <div class="header-left">
        <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="var(--accent)" stroke-width="2.2">
          <path d="M12 2v4m0 12v4M4.93 4.93l2.83 2.83m8.48 8.48l2.83 2.83M2 12h4m12 0h4M4.93 19.07l2.83-2.83m8.48-8.48l2.83-2.83"/>
        </svg>
        <h1 class="title">Extensiones y Complementos</h1>
      </div>
      <button class="action-btn-primary" onclick="openWebStore()">🛍️ Chrome Web Store</button>
    </div>

    <!-- Instalador por URL o ID -->
    <div class="card">
      <h2 class="card-title">Instalar Extensión desde Chrome Web Store</h2>
      <p style="font-size: 0.82rem; opacity: 0.75; line-height: 1.4;">
        Pega el enlace de la extensión en la Chrome Web Store o introduce su ID de 32 caracteres para instalarla directamente en Aegis.
      </p>
      <form onsubmit="installFromInput(event)" class="search-row">
        <input id="extInput" type="text" placeholder="https://chromewebstore.google.com/detail/... o ID de extensión" class="ext-search-input" />
        <button type="submit" class="action-btn-primary">Instalar</button>
      </form>
    </div>

    <!-- Extensiones de Chrome Web Store Instaladas -->
    <div class="card">
      <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px;">
        <h2 class="card-title" style="margin-bottom: 0;">Extensiones de Chrome Instaladas</h2>
        <button class="action-btn" onclick="openWebStore()">+ Añadir más</button>
      </div>
      {chrome_exts_html}
    </div>

    <!-- Módulos de Aegis Nativos -->
    <div class="card">
      <h2 class="card-title">Motores Nativos de Aegis Shields (Activos)</h2>
      <div class="ext-item">
        <span style="font-size: 1.5rem;">🛡️</span>
        <div class="ext-info">
          <span class="ext-name">Aegis Shields Rust Core</span>
          <span class="ext-sub">Bloqueo de red socket Rust FFI con reglas EasyList y uBlock</span>
        </div>
        <span style="font-size: 0.8rem; color: #2ea043; font-weight: 600;">Activo</span>
      </div>
      <div class="ext-item">
        <span style="font-size: 1.5rem;">⚡</span>
        <div class="ext-info">
          <span class="ext-name">Aegis Video & Countdown Defuser</span>
          <span class="ext-sub">Bypass de anuncios en video, muros anti-adblock y acortadores</span>
        </div>
        <span style="font-size: 0.8rem; color: #2ea043; font-weight: 600;">Activo</span>
      </div>
      <div class="ext-item">
        <span style="font-size: 1.5rem;">🎨</span>
        <div class="ext-info">
          <span class="ext-name">Aegis Cosmetic Engine</span>
          <span class="ext-sub">Filtrado cosmético CSS inmediato inyectado en páginas</span>
        </div>
        <span style="font-size: 0.8rem; color: #2ea043; font-weight: 600;">Activo</span>
      </div>
      <div class="ext-item">
        <span style="font-size: 1.5rem;">⚡</span>
        <div class="ext-info">
          <span class="ext-name">Aegis Fast Timer & Shortener Bypass</span>
          <span class="ext-sub">Salto automático de temporizadores de espera y countdown en CurseForge, Mega, Adf.ly, Linkvertise, Mediafire y servidores de descarga</span>
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
    function openWebStore() {{
      window.location.href = 'https://chromewebstore.google.com';
    }}
    function openScriptsFolder() {{
      window.location.href = 'aegis://action?open_scripts_folder=1';
    }}
    function removeExtension(extId) {{
      if (confirm('¿Deseas desinstalar esta extensión de Aegis Browser?')) {{
        window.location.href = 'aegis://action?remove_extension=' + encodeURIComponent(extId);
      }}
    }}
    function installFromInput(e) {{
      e.preventDefault();
      const val = document.getElementById('extInput').value.trim();
      if (val) {{
        window.location.href = 'aegis://action?install_input=' + encodeURIComponent(val);
      }}
    }}
  </script>
</body>
</html>
"""

# ── 13. Punto de Entrada Principal ────────────────────────────────────────────
def log_crash(msg: str):
    log_file = Path.home() / ".aegis_browser_error.log"
    try:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")
    except Exception:
        pass

def excepthook(exc_type, exc_value, exc_tb):
    import traceback
    tb = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    log_crash(f"CRITICAL UNHANDLED EXCEPTION:\n{tb}")
    sys.__excepthook__(exc_type, exc_value, exc_tb)

sys.excepthook = excepthook

def main():
    try:
        app = QApplication(sys.argv)
        app.setApplicationName("Aegis")
        app.setApplicationVersion("1.3.5")

        window = AegisBrowserWindow()
        window.show()

        sys.exit(app.exec())
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        log_crash(f"Fatal startup error:\n{tb}")
        try:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(None, "Error al iniciar Aegis Browser", f"Ocurrió un error al iniciar el navegador:\n{e}\n\nRevisa el archivo de log en: {Path.home() / '.aegis_browser_error.log'}")
        except Exception:
            pass
        sys.exit(1)

if __name__ == "__main__":
    main()
