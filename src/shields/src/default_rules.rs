//! Aegis Browser - Reglas de filtrado nativas de alta eficiencia (Zero-Day Built-in)
//! Optimizadas para sitios web populares con publicidad invasiva, trackers y anti-adblocks.

pub const DEFAULT_SHIELDS_RULES: &str = r#"
! ==============================================================================
! Aegis Shields - Reglas Base de Alta Eficiencia (uBlock / EasyList Compatible)
! ==============================================================================

! ── 1. YouTube & Plataformas de Video ──────────────────────────────────────────
||googlevideo.com/videoplayback$xhr,3p
||youtube.com/api/stats/ads^
||youtube.com/api/stats/atr^
||youtube.com/api/stats/qoe*&adformat=
||youtube.com/pagead/*
||youtube.com/ptracking*
||youtube.com/get_midroll_info*
||youtube.com/youtubei/v1/player/ad_break*
youtube.com##ytd-ad-slot-renderer
youtube.com##.ytd-in-feed-ad-layout-renderer
youtube.com##ytd-promoted-sparkles-web-renderer
youtube.com##ytd-promoted-video-renderer
youtube.com##ytd-banner-promo-renderer
youtube.com##ytd-statement-banner-renderer
youtube.com##.ytp-ad-overlay-container
youtube.com##.ytp-ad-message-container
youtube.com##.ytp-ad-player-overlay
youtube.com##.ytp-ad-preview-container
youtube.com##ytd-display-ad-renderer
youtube.com##ytd-enforcement-message-view-model
youtube.com##tp-yt-paper-dialog:has(#feedback)
youtube.com##ytd-popup-container:has(ytd-enforcement-message-view-model)
youtube.com##ytd-action-companion-ad-renderer

! ── 2. Twitch & Streaming en Vivo ─────────────────────────────────────────────
||imasdk.googleapis.com^
||amazon-adsystem.com^
||twitch.tv/api/channel/all/lead_in*
twitch.tv##.tw-ad-banner
twitch.tv##[data-test-selector="ad-banner"]
twitch.tv##.video-player__overlay:has(.tw-ad-banner)
twitch.tv##.channel-root__right-column:has(.tw-ad-banner)

! ── 3. Redes Sociales (Facebook, Instagram, Twitter/X, Reddit) ─────────────────
||facebook.com/tr/*
||connect.facebook.net/*/fbevents.js
facebook.com##[data-pagelet*="FeedUnit_"]:has(span:has-text(Sponsored))
facebook.com##div[role="feed"] > div:has(a[href*="/ads/about"])
instagram.com##article:has(span:has-text(Sponsored))
instagram.com##div:has(> a[href*="/sponsored/"])
||static.ads-twitter.com^
||ads-api.twitter.com^
x.com##[data-testid="cellInnerDiv"]:has(span:has-text("Ad"))
x.com##[data-testid="cellInnerDiv"]:has(span:has-text("Promoted"))
twitter.com##[data-testid="cellInnerDiv"]:has(span:has-text("Promoted"))
x.com##[data-testid="trend"]:has(span:has-text("Promoted"))
||reddit.com/api/v2/gold/gild*
reddit.com##shreddit-post[is-promoted]
reddit.com##.promotedlink
reddit.com##div[data-testid="post-container"]:has(span:has-text("promoted"))
reddit.com##shreddit-comment-tree + shreddit-async-loader

! ── 4. Forbes, Medios de Noticias y Neutralización de Anti-Adblocks ───────────
forbes.com##.fbs-ad
forbes.com##.ad-container
forbes.com##div[id*="ad-"]
forbes.com##.ad-unit
forbes.com##.top-ad-container
forbes.com##.vestpocket
forbes.com##fbs-ad
||adligature.com^
||delivery.adrecover.com^
||detectadblock.com^
||pagefair.com^
||blockadblock.com^
||adblocknotify.com^
||fundingchoicesmessages.google.com^

! ── 5. Gigantes de Publicidad y Redes Nativas ─────────────────────────────────
||doubleclick.net^
||pagead2.googlesyndication.com^
||securepubads.g.doubleclick.net^
||googleads.g.doubleclick.net^
||adservice.google.com^
||googletagservices.com^
||taboola.com^
||outbrain.com^
||criteo.com^
||criteo.net^
||adnxs.com^
||pubmatic.com^
||rubiconproject.com^
||openx.net^
||bidswitch.net^
||casalemedia.com^
||smartadserver.com^
||yieldmo.com^

! ── 6. Redes Invasivas de Popups, Popunders y Clickjacking ───────────────────
||propellerads.com^
||popcash.net^
||clickadu.com^
||adsterra.com^
||exoclick.com^
||trafficjunky.net^
||hilltopads.com^
||monetag.com^
||richpush.co^
||ad-maven.com^
||popads.net^
||juicyads.com^
||adcash.com^
||yengo.com^
||zeroredirect1.com^
||adxprts.com^

! ── 7. Telemetría y Rastreadores Globales ──────────────────────────────────────
||google-analytics.com^
||analytics.google.com^
||hotjar.com^
||amplitude.com^
||segment.io^
||mixpanel.com^
||scorecardresearch.com^
||mc.yandex.ru^

! ── 8. Banners de Cookies y Consentimiento Invasivos ──────────────────────────
||onetrust.com^
||cookiebot.com^
||cookielaw.org^
||didomi.io^
||quantcast.mgr.consensu.org^

! ── 9. Sitios de Streaming y Anime (AnimeFLV, Cuevana, Cinecalidad) ───────────
animeflv.net##.banner-wrapper
animeflv.net##.publicidad
animeflv.net##div[class*="ads"]
animeflv.net##.CnsntMdl
animeflv.net##div[style*="z-index: 99999"]
cuevana*.biz##.ad-banner
cuevana*.biz##.banner-desktop
cuevana*.biz##div[class*="dfp-ad"]
cuevana*.biz##.play-fake
cinecalidad*.com##.publi
cinecalidad*.com##.publi-header
cinecalidad*.com##.fake-player
||vidoomy.com^
||ezoic.com^
||mgid.com^
||richaudience.com^
||adtng.com^
||adk2x.com^
||streamtape.com/ads*
||doodstream.com/ad*
||mixdrop.co/ads*

! ── 10. Acortadores de Enlaces y Cuentas Atrás (Adf.ly, CurseForge, ouo.io) ────
||ouo.io/traffic/*
||ouo.press/traffic/*
||adf.ly/ad/*
||ay.gy/ad/*
||linkvertise.com/api/v1/redirect*
||shrinkme.io/ads*
||cuty.io/ads*
curseforge.com##.curseforge-ad
curseforge.com##div[id*="cf-ad-"]
"#;
