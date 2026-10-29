// ==UserScript==
// @name         Aegis Streaming Anti-Popup, Anti-Bot Scam & AdShield Deflector
// @description  Elimina popups, popunders, alertas falsas de "Not a Robot", trampas de clic y redirecciones publicitarias en sitios de streaming.
// @match        *://*/*
// @run-at       document-start
// ==/UserScript==
(function() {
    'use strict';
    if (window._aegisPopupBlockerLoaded) return;
    window._aegisPopupBlockerLoaded = true;

    // Lista de dominios publicitarios y redes agresivas de popunders / scams
    const AD_DOMAINS = [
        'popads', 'adcash', 'adsterra', 'propellerads', 'monetag', 'exoclick',
        'trafficfactory', 'onclickalgo', 'onclick', 'adnxs', 'syndication',
        'bet365', '1xbet', 'doubleclick', 'googlesyndication', 'yieldlab',
        'criteo', 'outbrain', 'taboola', 'mgid', 'revcontent', 'zeroredirect',
        'clickadu', 'hilltopads', 'richpush', 'evadav', 'rollerads', 'admaven',
        'streamtape', 'waaw', 'doodstream', 'filemoon', 'vidhide', 'voe',
        'cerdma', 'livejasmin', 'cyrl', 'redirectin', 'onclickalgo', 'push'
    ];

    // 1. Desactivar API de notificaciones para evitar popups "Permitir notificaciones para verificar que no eres un robot"
    if (window.Notification) {
        try {
            window.Notification.requestPermission = () => Promise.resolve('denied');
            Object.defineProperty(window.Notification, 'permission', {
                get: () => 'denied',
                configurable: true
            });
        } catch(e) {}
    }

    // 2. Interceptar y suprimir alertas/confirmaciones falsas ("TO ACCESS THE CONTENT, CONFIRM YOU ARE NOT A ROBOT!")
    const origAlert = window.alert;
    window.alert = function(msg) {
        const str = String(msg || '').toLowerCase();
        if (str.includes('robot') || str.includes('confirm') || str.includes('access the content') || str.includes('notific') || str.includes('human')) {
            console.log('[Aegis Shield] Alerta falsa de verificacion de robot bloqueada:', msg);
            return;
        }
        return origAlert.apply(this, arguments);
    };

    const origConfirm = window.confirm;
    window.confirm = function(msg) {
        const str = String(msg || '').toLowerCase();
        if (str.includes('robot') || str.includes('confirm') || str.includes('access the content') || str.includes('notific') || str.includes('human')) {
            console.log('[Aegis Shield] Dialogo falso de confirmacion bloqueado:', msg);
            return false;
        }
        return origConfirm.apply(this, arguments);
    };

    // 3. Proteger window.open contra popunders automáticos
    const originalOpen = window.open;
    window.open = function(url, target, features) {
        if (!url || typeof url !== 'string') {
            console.log('[Aegis Shield] Bloqueada llamada vacia a window.open()');
            return null;
        }

        const urlLower = url.toLowerCase();
        if (AD_DOMAINS.some(d => urlLower.includes(d))) {
            console.log('[Aegis Shield] Popup publicitario bloqueado:', url);
            return null;
        }

        // Si no fue accionado por un evento de usuario real
        const e = window.event;
        if (e && !e.isTrusted) {
            console.log('[Aegis Shield] Popup no confiable bloqueado:', url);
            return null;
        }

        return originalOpen.apply(this, arguments);
    };

    // 4. Desactivar trampas de clic invisibles y superposiciones falsas de robot
    function cleanTrapsAndScams() {
        const badTexts = ['not a robot', 'confirm you are not a robot', 'to access the content', 'allow notifications'];
        document.querySelectorAll('div, dialog, section, a, span').forEach(el => {
            try {
                // Verificar si contiene texto del scam de robot
                const text = (el.innerText || '').toLowerCase();
                if (badTexts.some(bt => text.includes(bt)) && el.innerText.length < 500) {
                    el.remove();
                    console.log('[Aegis Shield] Overlay falso de robot eliminado:', text.slice(0, 50));
                    return;
                }

                // Trampas invisibles de pantalla completa
                const cs = window.getComputedStyle(el);
                if ((cs.position === 'fixed' || cs.position === 'absolute') && parseInt(cs.zIndex) > 1000) {
                    const rect = el.getBoundingClientRect();
                    if (rect.width >= window.innerWidth * 0.8 && rect.height >= window.innerHeight * 0.8) {
                        if (el.tagName === 'A' && el.href) {
                            const h = el.href.toLowerCase();
                            if (AD_DOMAINS.some(d => h.includes(d)) || !el.innerText.trim()) {
                                el.remove();
                                console.log('[Aegis Shield] Click-trap eliminada:', el.href);
                            }
                        }
                    }
                }
            } catch(e) {}
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', cleanTrapsAndScams);
    } else {
        cleanTrapsAndScams();
    }
    setInterval(cleanTrapsAndScams, 1500);
})();
