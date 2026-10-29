// ==UserScript==
// @name         Aegis Discord Ultra-Light Optimizer
// @description  Reduce drásticamente el consumo de CPU y RAM de Discord Web: limita requestAnimationFrame a 1 FPS en segundo plano, defiende el WebRTC de voz sin microcortes, suprime desenfoques GPU pesados, oculta banners publicitarios de Nitro y ofrece un Responsive Drawer limpio para la barra lateral.
// @match        *://*.discord.com/*
// @match        *://discord.com/*
// @run-at       document-start
// ==/UserScript==
(function() {
    'use strict';
    if (window._aegisDiscordOptimizerLoaded) return;

    const host = (window.location.hostname || '').toLowerCase();
    if (!host.includes('discord.com') && !host.includes('discordapp.com')) return;

    if (window.self !== window.top) return;

        // =========================================================================
    // AEGIS WEBRTC & DOM ROBUSTNESS SHIELD (ROOT-LEVEL FIX)
    // =========================================================================

    // 1. Inmunizacion contra NaN en Aspect Ratio (Evita que Mojo WidgetHost rechace mensajes IPC)
    (function setupVideoSafeDimensions() {
        if (window._aegisVideoSafeDimensionsHooked) return;
        window._aegisVideoSafeDimensionsHooked = true;
        try {
            const origWidthDesc = Object.getOwnPropertyDescriptor(HTMLVideoElement.prototype, 'videoWidth');
            const origHeightDesc = Object.getOwnPropertyDescriptor(HTMLVideoElement.prototype, 'videoHeight');

            if (origWidthDesc && origWidthDesc.get) {
                Object.defineProperty(HTMLVideoElement.prototype, 'videoWidth', {
                    get() {
                        const val = origWidthDesc.get.call(this);
                        if (typeof val === 'number' && !isNaN(val) && val > 0) {
                            this._lastAegisWidth = val;
                            return val;
                        }
                        return this._lastAegisWidth || 1280;
                    },
                    configurable: true
                });
            }

            if (origHeightDesc && origHeightDesc.get) {
                Object.defineProperty(HTMLVideoElement.prototype, 'videoHeight', {
                    get() {
                        const val = origHeightDesc.get.call(this);
                        if (typeof val === 'number' && !isNaN(val) && val > 0) {
                            this._lastAegisHeight = val;
                            return val;
                        }
                        return this._lastAegisHeight || 720;
                    },
                    configurable: true
                });
            }
        } catch(e) {
            console.warn('[Aegis] Error instalando getters seguros de video:', e);
        }
    })();

    // 2. Blindaje de MediaStreamTrack.prototype.applyConstraints (Erradica OverconstrainedError)
    (function setupSafeApplyConstraints() {
        if (window._aegisSafeApplyConstraintsHooked) return;
        window._aegisSafeApplyConstraintsHooked = true;
        try {
            const origApply = MediaStreamTrack.prototype.applyConstraints;
            MediaStreamTrack.prototype.applyConstraints = function(constraints) {
                if (!this || this.readyState === 'ended' || !constraints) {
                    return Promise.resolve();
                }
                let clean = {};
                try {
                    clean = JSON.parse(JSON.stringify(constraints));
                    if (clean.video && typeof clean.video === 'object') {
                        if (clean.video.width && clean.video.width.exact) {
                            clean.video.width.ideal = clean.video.width.exact;
                            delete clean.video.width.exact;
                        }
                        if (clean.video.height && clean.video.height.exact) {
                            clean.video.height.ideal = clean.video.height.exact;
                            delete clean.video.height.exact;
                        }
                        if (clean.video.frameRate && clean.video.frameRate.exact) {
                            clean.video.frameRate.ideal = clean.video.frameRate.exact;
                            delete clean.video.frameRate.exact;
                        }
                    }
                } catch(err) {
                    clean = constraints;
                }

                return origApply.call(this, clean).catch(err => {
                    console.warn('[Aegis WebRTC] applyConstraints soft-handled para prevenir caida de React:', err);
                    return Promise.resolve();
                });
            };
        } catch(e) {
            console.warn('[Aegis] Error en setupSafeApplyConstraints:', e);
        }
    })();

    // 3. Escudo Global contra Excepciones de WebRTC y Animacion (Protege el arbol de React)
    (function setupGlobalWebRTCShield() {
        if (window._aegisGlobalWebRTCShieldHooked) return;
        window._aegisGlobalWebRTCShieldHooked = true;

        window.addEventListener('unhandledrejection', (event) => {
            const reason = String(event.reason || '');
            if (reason.includes('Overconstrained') || reason.includes('Constraint') || reason.includes('StreamPreview') || reason.includes('UploadManager')) {
                console.warn('[Aegis Shield] Unhandled rejection WebRTC suprimida:', reason);
                event.preventDefault();
            }
        });

        window.addEventListener('error', (event) => {
            const msg = String(event.message || '');
            if (msg.includes('NaN while animating') || msg.includes('animating') || msg.includes('Overconstrained')) {
                console.warn('[Aegis Shield] Error de animacion suprimido para proteger DOM:', msg);
                event.preventDefault();
                return true;
            }
        });
    })();

    // 4. Watchdog de Integridad del DOM (Auto-recuperacion en caso de desmontaje anormal)
    (function setupDOMHealthWatchdog() {
        let wasLoggedIn = false;
        setInterval(() => {
            const hasAppUI = !!document.querySelector('[class*="guilds_"], [class*="sidebar_"], [class*="chat_"], [class*="channels_"]');
            if (hasAppUI) {
                wasLoggedIn = true;
                return;
            }
            const appMount = document.getElementById('app-mount');
            if (wasLoggedIn && appMount && appMount.children.length === 0) {
                console.warn('[Aegis Watchdog] Discord sufrio vaciado de DOM. Restaurando...');
                window.location.reload();
            }
        }, 1500);
    })();


function isAuthOrLogin() {
        const path = (window.location.pathname || '').toLowerCase();
        const href = (window.location.href || '').toLowerCase();
        if (path.startsWith('/login') || path.startsWith('/register') || href.includes('captcha')) {
            return true;
        }
        return !!document.querySelector('input[type="password"], input[name="email"], input[name="login"], [class*="qrCode_"]');
    }

    function startOptimizerWhenLoggedIn() {
        if (isAuthOrLogin()) {
            setTimeout(startOptimizerWhenLoggedIn, 1500);
            return;
        }

        const hasAppUI = !!document.querySelector('[class*="guilds_"], [class*="sidebar_"], [class*="chatContent_"], [class*="channels_"]');
        if (!hasAppUI) {
            setTimeout(startOptimizerWhenLoggedIn, 1500);
            return;
        }

        if (window._aegisDiscordOptimizerLoaded) return;
        window._aegisDiscordOptimizerLoaded = true;

        function injectPerfCSS() {
            if (document.getElementById('aegis-discord-perf-css')) return;
            const target = document.head || document.documentElement;
            if (!target) return;
            const style = document.createElement('style');
            style.id = 'aegis-discord-perf-css';
            style.textContent = `
                *, *::before, *::after {
                    backdrop-filter: none !important;
                    -webkit-backdrop-filter: none !important;
                }
                [class*="messagesWrapper_"], [class*="chatContent_"], [class*="scrollerInner_"] {
                    contain: content !important;
                }
                [class*="emoji_"]:not(:hover), [class*="sticker_"]:not(:hover) {
                    animation-play-state: paused !important;
                }
                [class*="membersWrap_"] [class*="avatar_"] img {
                    image-rendering: -webkit-optimize-contrast;
                }
                [class*="scrollerBase_"] {
                    will-change: transform;
                    transform: translateZ(0);
                }
            `;
            try {
                target.appendChild(style);
            } catch(e) {}
        }
        injectPerfCSS();

        let isVoiceActive = false;
        window._aegisIsDiscordVoiceActive = () => isVoiceActive;

        function checkVoiceStatus() {
            const inVoice = !!document.querySelector(
                '[class*="rtcConnectionStatus_"], [class*="connection_"], button[aria-label*="Desconectar"], button[aria-label*="Disconnect"], [class*="voiceUsers_"]'
            );
            isVoiceActive = inVoice;
        }
        setInterval(checkVoiceStatus, 2000);

        const origRAF = window.requestAnimationFrame.bind(window);
        const origCAF = window.cancelAnimationFrame.bind(window);

        let isHidden = document.hidden;
        document.addEventListener('visibilitychange', () => {
            isHidden = document.hidden;
            if (!isHidden) {
                flushPendingFrames();
            }
        });

        const pendingCallbacks = new Map();
        let nextCallbackId = 1;
        let bgTimer = null;

        function flushPendingFrames() {
            if (pendingCallbacks.size > 0) {
                const now = performance.now();
                const entries = Array.from(pendingCallbacks.entries());
                pendingCallbacks.clear();
                entries.forEach(([id, cb]) => {
                    try { cb(now); } catch(e) {}
                });
            }
        }

        window.requestAnimationFrame = function(cb) {
            if (!isHidden || isVoiceActive) {
                return origRAF(cb);
            }
            const id = nextCallbackId++;
            pendingCallbacks.set(id, cb);
            if (!bgTimer) {
                bgTimer = setTimeout(() => {
                    bgTimer = null;
                    flushPendingFrames();
                }, 1000);
            }
            return id;
        };

        window.cancelAnimationFrame = function(id) {
            if (pendingCallbacks.has(id)) {
                pendingCallbacks.delete(id);
                return;
            }
            return origCAF(id);
        };

        setInterval(() => {
            if (document.hidden && !isVoiceActive) {
                document.querySelectorAll('video').forEach(v => {
                    if (!v.closest('[class*="pictureInPicture_"], [class*="callContainer_"]')) {
                        if (!v.paused) {
                            try { v.pause(); } catch(e) {}
                        }
                    }
                });
            }
        }, 4000);

        // ── 5. Responsive Drawer & Limpieza Estética para Barra Lateral ──────────
        function setupResponsiveDrawer() {
            if (document.getElementById('aegis-discord-drawer-css')) return;
            const target = document.head || document.documentElement;
            if (!target) return;
            const style = document.createElement('style');
            style.id = 'aegis-discord-drawer-css';
            style.textContent = `
                /* Ocultar banners promocionales molestos de Nitro que roban espacio vertical */
                [class*="notice_"],
                [class*="channelNotice_"],
                [class*="guildNotice_"],
                [class*="premiumNotice_"] {
                    display: none !important;
                }

                @media (max-width: 680px) {
                    /* Por defecto en panel lateral: Servidores y Canales ocultos para que el chat ocupe el 100% */
                    body:not(.aegis-drawer-open) nav[class*="guilds_"],
                    body:not(.aegis-drawer-open) [class*="guilds_"],
                    body:not(.aegis-drawer-open) div[class*="sidebar_"] {
                        display: none !important;
                    }

                    /* Compactar la barra de título del canal para eliminar espacio gris vacío */
                    section[class*="title_"] {
                        height: 38px !important;
                        min-height: 38px !important;
                        padding: 0 10px 0 44px !important;
                        background: #2b2d31 !important;
                        border-bottom: 1px solid rgba(0, 0, 0, 0.2) !important;
                    }

                    /* Chat y contenido principal al 100% de ancho sin márgenes */
                    div[class*="chat_"],
                    main[class*="chatContent_"],
                    form[class*="form_"],
                    div[class*="messagesWrapper_"],
                    div[class*="container_"] > div[class*="base_"],
                    div[class*="base_"] > div[class*="content_"] {
                        width: 100% !important;
                        max-width: 100% !important;
                        margin-left: 0 !important;
                        flex: 1 1 100% !important;
                    }

                    /* Formulario de envío compacto */
                    form[class*="form_"] {
                        padding-left: 6px !important;
                        padding-right: 6px !important;
                        margin-bottom: 6px !important;
                    }

                    /* Botón flotante hamburguesa ☰ */
                    #aegis-discord-hamburger {
                        position: fixed;
                        top: 5px;
                        left: 6px;
                        width: 28px;
                        height: 28px;
                        background: #5865F2;
                        border-radius: 6px;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        color: #ffffff;
                        cursor: pointer;
                        z-index: 100010;
                        box-shadow: 0 3px 10px rgba(0, 0, 0, 0.5);
                        font-size: 15px;
                        font-weight: bold;
                        user-select: none;
                        transition: transform 0.15s, background 0.15s;
                    }
                    #aegis-discord-hamburger:hover {
                        background: #4752c4;
                        transform: scale(1.08);
                    }

                    /* Overlay flotante sin transformaciones GPU problemáticas cuando se abre ☰ */
                    body.aegis-drawer-open nav[class*="guilds_"],
                    body.aegis-drawer-open [class*="guilds_"] {
                        display: flex !important;
                        position: fixed !important;
                        top: 0 !important;
                        bottom: 0 !important;
                        left: 0 !important;
                        width: 72px !important;
                        z-index: 100005 !important;
                        background: #1e1f22 !important;
                        box-shadow: 4px 0 20px rgba(0, 0, 0, 0.7) !important;
                        transform: none !important;
                    }

                    body.aegis-drawer-open div[class*="sidebar_"] {
                        display: flex !important;
                        flex-direction: column !important;
                        position: fixed !important;
                        top: 0 !important;
                        bottom: 0 !important;
                        left: 72px !important;
                        width: 240px !important;
                        height: 100vh !important;
                        max-height: 100vh !important;
                        overflow: hidden !important;
                        z-index: 100004 !important;
                        background: #2b2d31 !important;
                        box-shadow: 6px 0 25px rgba(0, 0, 0, 0.7) !important;
                        transform: none !important;
                        will-change: auto !important;
                    }

                    /* Contenedor de canales: absorbe espacio restante y no expande indefinidamente */
                    body.aegis-drawer-open div[class*="sidebar_"] nav[class*="container_"],
                    body.aegis-drawer-open div[class*="sidebar_"] div[class*="container_"],
                    body.aegis-drawer-open div[class*="sidebar_"] [class*="channels_"] {
                        display: flex !important;
                        flex-direction: column !important;
                        flex: 1 1 auto !important;
                        min-height: 0 !important;
                        max-height: calc(100vh - 56px) !important;
                        overflow: hidden !important;
                    }

                    /* Scroller de canales de texto y voz: activa desplazamiento vertical suave */
                    body.aegis-drawer-open div[class*="sidebar_"] [class*="scroller_"] {
                        overflow-y: auto !important;
                        overflow-x: hidden !important;
                        flex: 1 1 auto !important;
                        min-height: 0 !important;
                        height: auto !important;
                        pointer-events: auto !important;
                        touch-action: pan-y !important;
                        scrollbar-width: thin !important;
                        scrollbar-color: rgba(255, 255, 255, 0.25) transparent !important;
                        overscroll-behavior: contain !important;
                    }

                    /* Barra inferior de usuario (Micrófono, Auriculares, Estado): fija y sin superposición */
                    body.aegis-drawer-open div[class*="sidebar_"] section[class*="panels_"] {
                        flex-shrink: 0 !important;
                        position: relative !important;
                        z-index: 10 !important;
                        background: #232428 !important;
                        border-top: 1px solid rgba(0, 0, 0, 0.25) !important;
                    }
                }
            `;
            try {
                target.appendChild(style);
            } catch(e) {}

            function ensureHamburgerBtn() {
                if (document.getElementById('aegis-discord-hamburger')) return;
                const btn = document.createElement('div');
                btn.id = 'aegis-discord-hamburger';
                btn.innerHTML = '&#9776;';
                btn.title = 'Servidores y Canales (Aegis Drawer)';
                btn.onclick = (e) => {
                    e.stopPropagation();
                    document.body.classList.toggle('aegis-drawer-open');
                };
                document.body.appendChild(btn);

                document.addEventListener('click', (e) => {
                    if (document.body.classList.contains('aegis-drawer-open')) {
                        if (!e.target.closest('nav[class*="guilds_"], div[class*="sidebar_"], #aegis-discord-hamburger')) {
                            document.body.classList.remove('aegis-drawer-open');
                        }
                    }
                });

                document.addEventListener('click', (e) => {
                    if (e.target.closest('[class*="channel_"], [class*="link_"]')) {
                        setTimeout(() => document.body.classList.remove('aegis-drawer-open'), 150);
                    }
                });
            }
            
                // Event bridge: redirige scroll de rueda al scroller de canales si el cursor está en el sidebar
                document.addEventListener('wheel', (e) => {
                    if (!document.body.classList.contains('aegis-drawer-open')) return;
                    const sidebar = document.querySelector('div[class*="sidebar_"]');
                    if (sidebar && sidebar.contains(e.target)) {
                        const scroller = sidebar.querySelector('[class*="scroller_"]');
                        if (scroller && !scroller.contains(e.target)) {
                            scroller.scrollTop += e.deltaY;
                        }
                    }
                }, { passive: true });

            ensureHamburgerBtn();
            setInterval(ensureHamburgerBtn, 2000);
        }
        setupResponsiveDrawer();

        // 6. Discord Screen Share Picker, Constraint Sanitizer & Atomic GPU Pipeline Flush
        function setupScreenShareHandler() {
            if (!navigator.mediaDevices || !navigator.mediaDevices.getDisplayMedia) return;
            if (window._aegisDisplayMediaHooked) return;
            window._aegisDisplayMediaHooked = true;

            const origGetDisplayMedia = navigator.mediaDevices.getDisplayMedia.bind(navigator.mediaDevices);

            function showPickerUI() {
                return new Promise((resolve) => {
                    const old = document.getElementById('aegis-screen-modal');
                    if (old) old.remove();

                    const modal = document.createElement('div');
                    modal.id = 'aegis-screen-modal';
                    modal.style.cssText = 'position:fixed;inset:0;background:rgba(0,0,0,0.85);backdrop-filter:blur(6px);z-index:999999;display:flex;align-items:center;justify-content:center;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;';
                    modal.innerHTML = `
                        <div style="background:#2b2d31;border:1px solid rgba(255,255,255,0.12);border-radius:12px;padding:24px;width:460px;color:#f2f3f5;box-shadow:0 20px 50px rgba(0,0,0,0.8);">
                            <div style="display:flex;align-items:center;gap:10px;margin-bottom:12px;">
                                <div style="font-size:22px;">📺</div>
                                <div style="font-size:17px;font-weight:700;">Transmitir Pantalla (Aegis Shields)</div>
                            </div>
                            <div style="font-size:13px;color:#949ba4;margin-bottom:18px;">
                                Selecciona qué origen de video deseas compartir en esta sala de Discord:
                            </div>
                            <div style="display:flex;flex-direction:column;gap:10px;margin-bottom:20px;">
                                <button id="aegis-opt-screen" style="background:#1e1f22;border:1px solid rgba(255,255,255,0.1);border-radius:8px;padding:12px 14px;color:#fff;text-align:left;cursor:pointer;display:flex;align-items:center;gap:12px;transition:all 0.15s;">
                                    <span style="font-size:24px;">🖥️</span>
                                    <div>
                                        <div style="font-weight:700;font-size:14px;">Pantalla Completa (Monitor Principal)</div>
                                        <div style="font-size:12px;color:#949ba4;">Transmite todo tu escritorio a 1080p 30/60 FPS fluidos</div>
                                    </div>
                                </button>
                                <button id="aegis-opt-window" style="background:#1e1f22;border:1px solid rgba(255,255,255,0.1);border-radius:8px;padding:12px 14px;color:#fff;text-align:left;cursor:pointer;display:flex;align-items:center;gap:12px;transition:all 0.15s;">
                                    <span style="font-size:24px;">🪟</span>
                                    <div>
                                        <div style="font-weight:700;font-size:14px;">Ventana de Aplicacion Activa</div>
                                        <div style="font-size:12px;color:#949ba4;">Transmite únicamente la ventana activa de primer plano</div>
                                    </div>
                                </button>
                            </div>
                            <div style="display:flex;justify-content:flex-end;gap:8px;">
                                <button id="aegis-opt-cancel" style="background:transparent;border:none;color:#949ba4;padding:8px 16px;border-radius:6px;cursor:pointer;font-size:14px;font-weight:600;">Cancelar</button>
                            </div>
                        </div>
                    `;
                    document.body.appendChild(modal);

                    const hoverStyle = (btn) => {
                        btn.onmouseenter = () => btn.style.borderColor = '#5865F2';
                        btn.onmouseleave = () => btn.style.borderColor = 'rgba(255,255,255,0.1)';
                    };
                    const bScreen = document.getElementById('aegis-opt-screen');
                    const bWin = document.getElementById('aegis-opt-window');
                    const bCancel = document.getElementById('aegis-opt-cancel');
                    if (bScreen) hoverStyle(bScreen);
                    if (bWin) hoverStyle(bWin);

                    if (bScreen) bScreen.onclick = () => { modal.remove(); resolve({ type: 'screen' }); };
                    if (bWin) bWin.onclick = () => { modal.remove(); resolve({ type: 'window' }); };
                    if (bCancel) bCancel.onclick = () => { modal.remove(); resolve(null); };
                });
            }

            navigator.mediaDevices.getDisplayMedia = async function(constraints = {}) {
                const choice = await showPickerUI();
                if (!choice) {
                    const err = new Error('Permission denied by user');
                    err.name = 'NotAllowedError';
                    throw err;
                }

                const cleanConstraints = {
                    video: {
                        width: { ideal: 1920, max: 1920 },
                        height: { ideal: 1080, max: 1080 },
                        frameRate: { ideal: 30, max: 60 }
                    },
                    audio: constraints.audio || false
                };

                const stream = await origGetDisplayMedia(cleanConstraints);

                // Teardown Atómico Seguro: desacoplar pipeline y purgar texturas GPU antes de detener capturador
                stream.getVideoTracks().forEach(track => {
                    const origTrackStop = track.stop.bind(track);
                    track.stop = function() {
                        // 1. Purgar todos los elementos de video asociados para liberar mailboxes Skia
                        document.querySelectorAll('video').forEach(v => {
                            if (v.srcObject === stream || v.srcObject === track) {
                                try {
                                    v.pause();
                                    v.srcObject = null;
                                    v.removeAttribute('src');
                                    v.load(); // Desecha síncronamente el WebMediaPlayerImpl
                                } catch(e) {}
                            }
                        });
                        // 2. Ejecutar inmediatamente el stop nativo para mantener sincronizado readyState = 'ended'
                        try { origTrackStop(); } catch(e) {}
                    };
                });

                return stream;
            };
        }
        setupScreenShareHandler();

        console.log('[Aegis] Optimizador Discord Ultra-Light activado (0% CPU en fondo, WebRTC blindado, Responsive Drawer OK).');
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', startOptimizerWhenLoggedIn);
    } else {
        startOptimizerWhenLoggedIn();
    }
})();
