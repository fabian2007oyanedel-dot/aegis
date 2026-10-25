//! Aegis Browser - Inyección de Scriptlets Desactivadores (Anti-Adblock Defusers)
//! Neutraliza los muros anti-adblock (YouTube, Admiral, etc.) y bloquea la publicidad dinámica en sitios populares.

/// Devuelve el script JS que se inyecta en el documento antes de la ejecución de scripts (`document_start`).
pub fn get_injected_script_for_url(url: &str) -> String {
    let lower_url = url.to_lowercase();

    let mut scripts = Vec::new();

    // 1. Defuser Universal de Anti-Adblock (Neutraliza Admiral, BlockAdBlock, etc.)
    scripts.push(UNIVERSAL_ANTI_ADBLOCK_DEFUSER);

    // 2. Defuser Especializado para YouTube
    if lower_url.contains("youtube.com") || lower_url.contains("youtu.be") {
        scripts.push(YOUTUBE_AD_AND_ANTI_ADBLOCK_DEFUSER);
    }

    // 3. Defuser para Twitch (Amazon IVS)
    if lower_url.contains("twitch.tv") {
        scripts.push(TWITCH_AD_DEFUSER);
    }

    // 4. Defuser de Popups & Clickjacking en sitios de streaming / descargas
    scripts.push(POPUNDER_PROTECTION_SCRIPTLET);

    scripts.join("\n\n")
}

/// Devuelve reglas CSS cosméticas prioritarias para el dominio consultado
pub fn get_curated_cosmetic_css_for_url(url: &str) -> String {
    let lower_url = url.to_lowercase();
    let mut rules = Vec::new();

    if lower_url.contains("youtube.com") || lower_url.contains("youtu.be") {
        rules.push(
            "ytd-ad-slot-renderer, .ytd-in-feed-ad-layout-renderer, \
             ytd-promoted-sparkles-web-renderer, ytd-banner-promo-renderer, \
             ytd-statement-banner-renderer, .ytp-ad-overlay-container, \
             .ytp-ad-message-container, .ytp-ad-player-overlay, \
             .ytp-ad-preview-container, ytd-display-ad-renderer, \
             ytd-enforcement-message-view-model, tp-yt-paper-dialog:has(#feedback), \
             ytd-action-companion-ad-renderer { display: none !important; opacity: 0 !important; height: 0 !important; }"
        );
    }

    if lower_url.contains("twitch.tv") {
        rules.push(
            ".tw-ad-banner, [data-test-selector=\"ad-banner\"], \
             .video-player__overlay:has(.tw-ad-banner) { display: none !important; }"
        );
    }

    if lower_url.contains("reddit.com") {
        rules.push(
            "shreddit-post[is-promoted], .promotedlink, \
             div[data-testid=\"post-container\"]:has(span:has-text(\"promoted\")), \
             shreddit-comment-tree + shreddit-async-loader { display: none !important; }"
        );
    }

    if lower_url.contains("x.com") || lower_url.contains("twitter.com") {
        rules.push(
            "[data-testid=\"cellInnerDiv\"]:has(span:has-text(\"Ad\")), \
             [data-testid=\"cellInnerDiv\"]:has(span:has-text(\"Promoted\")) { display: none !important; }"
        );
    }

    if lower_url.contains("facebook.com") || lower_url.contains("instagram.com") {
        rules.push(
            "[data-pagelet*=\"FeedUnit_\"]:has(span:has-text(\"Sponsored\")), \
             article:has(span:has-text(\"Sponsored\")) { display: none !important; }"
        );
    }

    if lower_url.contains("forbes.com") {
        rules.push(
            ".fbs-ad, .ad-container, div[id*=\"ad-\"], .ad-unit, .top-ad-container, \
             .vestpocket, fbs-ad { display: none !important; }"
        );
    }

    rules.join("\n")
}

// ── IMPLEMENTACIÓN DE SCRIPTLETS (DEFUSERS) ───────────────────────────────────

const UNIVERSAL_ANTI_ADBLOCK_DEFUSER: &str = r#"
(() => {
  // Aegis Shields - Universal Anti-Adblock Defuser
  try {
    window.canRunAds = true;
    window.isAdBlockActive = false;
    window.adblock = false;
    window.google_ad_status = 1;

    // Stub para Google Tag Manager / Publisher Services para que la página no rompa su ejecución
    if (!window.googletag) {
      window.googletag = { cmd: [] };
    }
    if (window.googletag && !window.googletag._aegis_patched) {
      window.googletag._aegis_patched = true;
      const originalPush = window.googletag.cmd.push;
      window.googletag.cmd.push = function(...args) {
        for (const fn of args) {
          if (typeof fn === 'function') {
            try { fn(); } catch(e) {}
          }
        }
        return originalPush ? originalPush.apply(this, args) : 1;
      };
    }

    // No-op para funciones de tracking que provocan cuelgues si son bloqueadas
    window.ga = window.ga || function() {};
    window.gtag = window.gtag || function() {};
    
    // Desbloquear scroll si algún detector anti-adblock intentó bloquear la pantalla
    const unlockScroll = () => {
      if (document.body) {
        if (document.body.style.overflow === 'hidden') document.body.style.overflow = 'auto';
        document.body.classList.remove('modal-open', 'freeze-scroll');
      }
      if (document.documentElement) {
        if (document.documentElement.style.overflow === 'hidden') document.documentElement.style.overflow = 'auto';
      }
    };
    window.addEventListener('DOMContentLoaded', unlockScroll);
    setTimeout(unlockScroll, 1500);
  } catch (e) {}
})();
"#;

const YOUTUBE_AD_AND_ANTI_ADBLOCK_DEFUSER: &str = r#"
(() => {
  // Aegis Shields - YouTube Ad Skipper & Anti-Adblock Defuser
  try {
    // 1. Limpieza de datos de anuncios en ytInitialPlayerResponse
    const cleanPlayerResponse = (obj) => {
      if (!obj || typeof obj !== 'object') return;
      if (obj.adPlacements) obj.adPlacements = [];
      if (obj.playerAds) obj.playerAds = [];
      if (obj.adSlots) obj.adSlots = [];
    };

    if (window.ytInitialPlayerResponse) {
      cleanPlayerResponse(window.ytInitialPlayerResponse);
    }

    Object.defineProperty(window, 'ytInitialPlayerResponse', {
      configurable: true,
      set: function(val) {
        cleanPlayerResponse(val);
        this._aegis_ytInitialPlayerResponse = val;
      },
      get: function() {
        return this._aegis_ytInitialPlayerResponse;
      }
    });

    // 2. Desactivar modal de detección anti-adblock de YouTube ("Los bloqueadores de anuncios infringen...")
    const neutraliseYouTubeModals = () => {
      const enforcement = document.querySelector('ytd-enforcement-message-view-model');
      if (enforcement) {
        enforcement.remove();
        const backdrop = document.querySelector('tp-yt-iron-overlay-backdrop');
        if (backdrop) backdrop.remove();
        const video = document.querySelector('video');
        if (video && video.paused) {
          video.play().catch(() => {});
        }
      }

      // Auto-saltador instantáneo para videos comerciales si alguno intenta reproducirse
      const player = document.getElementById('movie_player') || document.querySelector('.html5-video-player');
      if (player && (player.classList.contains('ad-showing') || player.classList.contains('ad-interrupting'))) {
        const video = player.querySelector('video');
        if (video && isFinite(video.duration) && video.duration > 0) {
          video.muted = true;
          video.currentTime = video.duration;
        }
        const skipBtn = document.querySelector('.ytp-ad-skip-button, .ytp-ad-skip-button-modern, .ytp-skip-ad-button');
        if (skipBtn) skipBtn.click();
      }
    };

    setInterval(neutraliseYouTubeModals, 250);
  } catch (e) {}
})();
"#;

const TWITCH_AD_DEFUSER: &str = r#"
(() => {
  // Aegis Shields - Twitch Stream Ad Interceptor
  try {
    // Desactiva banners superpuestos en transmisiones de Twitch
    const cleanTwitch = () => {
      const banners = document.querySelectorAll('.tw-ad-banner, [data-test-selector="ad-banner"]');
      banners.forEach(b => b.remove());
    };
    setInterval(cleanTwitch, 1000);
  } catch (e) {}
})();
"#;

const POPUNDER_PROTECTION_SCRIPTLET: &str = r#"
(() => {
  // Aegis Shields - Popunder & Unsolicited Window Protector
  try {
    const rawOpen = window.open;
    window.open = function(url, target, features) {
      // Bloquear popups que intenten abrirse sin una interacción directa legítima
      if (window.event && window.event.isTrusted === false) {
        return null;
      }
      return rawOpen.call(window, url, target, features);
    };
  } catch (e) {}
})();
"#;
