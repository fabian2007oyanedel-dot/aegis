use std::ffi::{CStr, CString};
use std::os::raw::c_char;
use std::sync::atomic::{AtomicU64, Ordering};
use std::sync::RwLock;

use adblock::Engine;
use adblock::lists::{FilterSet, ParseOptions};
use adblock::request::Request;

mod default_rules;
mod defusers;

use default_rules::DEFAULT_SHIELDS_RULES;
use defusers::{get_curated_cosmetic_css_for_url, get_injected_script_for_url};

/// Estructura interna de Aegis Shields
pub struct AegisShieldsEngine {
    engine: RwLock<Engine>,
    blocked_count: AtomicU64,
}

/// Crea una nueva instancia de Aegis Shields precargada con las reglas nativas (Zero-Day)
/// para YouTube, Twitch, redes sociales, periódicos y redes de popups.
#[no_mangle]
pub extern "C" fn aegis_shields_create() -> *mut AegisShieldsEngine {
    let mut filter_set = FilterSet::new(true);
    filter_set.add_filter_list(DEFAULT_SHIELDS_RULES.to_string(), ParseOptions::default());

    let engine = Engine::new_with_filter_set(filter_set);
    Box::into_raw(Box::new(AegisShieldsEngine {
        engine: RwLock::new(engine),
        blocked_count: AtomicU64::new(0),
    }))
}

/// # Safety
///
/// `engine` debe ser un puntero válido obtenido previamente mediante `aegis_shields_create()`,
/// o ser un puntero nulo (en cuyo caso no realiza ninguna operación).
#[no_mangle]
pub unsafe extern "C" fn aegis_shields_destroy(engine: *mut AegisShieldsEngine) {
    if !engine.is_null() {
        drop(Box::from_raw(engine));
    }
}

/// # Safety
///
/// `engine` debe apuntar a una instancia válida de `AegisShieldsEngine`.
/// `rules_text` debe ser una cadena C válida terminada en byte nulo (`\0`).
#[no_mangle]
pub unsafe extern "C" fn aegis_shields_load_rules(
    engine: *mut AegisShieldsEngine,
    rules_text: *const c_char,
) -> bool {
    if engine.is_null() || rules_text.is_null() {
        return false;
    }

    let c_str = match CStr::from_ptr(rules_text).to_str() {
        Ok(s) => s,
        Err(_) => return false,
    };

    let mut filter_set = FilterSet::new(true);
    // Preservar siempre las reglas maestras de Aegis Shields
    filter_set.add_filter_list(DEFAULT_SHIELDS_RULES.to_string(), ParseOptions::default());
    // Añadir listas adicionales (EasyList, uBlock, reglas de usuario)
    filter_set.add_filter_list(c_str.to_string(), ParseOptions::default());

    let new_engine = Engine::new_with_filter_set(filter_set);
    if let Ok(mut lock) = (*engine).engine.write() {
        *lock = new_engine;
        true
    } else {
        false
    }
}

/// # Safety
///
/// `engine` debe ser un puntero válido y no nulo.
/// `url` debe ser una cadena C válida terminada en byte nulo.
/// `source_url` y `request_type` pueden ser nulos o cadenas C válidas.
#[no_mangle]
pub unsafe extern "C" fn aegis_shields_should_block(
    engine: *mut AegisShieldsEngine,
    url: *const c_char,
    source_url: *const c_char,
    request_type: *const c_char,
) -> bool {
    if engine.is_null() || url.is_null() {
        return false;
    }

    let url_str = match CStr::from_ptr(url).to_str() {
        Ok(s) => s,
        Err(_) => return false,
    };

    let source_str = if source_url.is_null() {
        ""
    } else {
        CStr::from_ptr(source_url).to_str().unwrap_or("")
    };

    let req_type_str = if request_type.is_null() {
        "other"
    } else {
        CStr::from_ptr(request_type).to_str().unwrap_or("other")
    };

    let req = match Request::new(url_str, source_str, req_type_str, "GET") {
        Ok(r) => r,
        Err(_) => return false,
    };

    if let Ok(lock) = (*engine).engine.read() {
        let blocker_result = lock.check_network_request(&req);
        let should_block = blocker_result.should_block();

        if should_block {
            (*engine).blocked_count.fetch_add(1, Ordering::Relaxed);
        }

        should_block
    } else {
        false
    }
}

/// # Safety
///
/// Genera y devuelve una hoja de estilo CSS cosmética para ocultar anuncios en el DOM de la URL dada.
/// La memoria devuelta debe liberarse invocando `aegis_shields_free_string()`.
#[no_mangle]
pub unsafe extern "C" fn aegis_shields_get_cosmetic_stylesheet(
    engine: *mut AegisShieldsEngine,
    url: *const c_char,
) -> *mut c_char {
    if engine.is_null() || url.is_null() {
        return std::ptr::null_mut();
    }

    let url_str = match CStr::from_ptr(url).to_str() {
        Ok(s) => s,
        Err(_) => return std::ptr::null_mut(),
    };

    let mut css_rules = Vec::new();

    // 1. Obtener selectores cosméticos calculados por adblock-rust
    if let Ok(lock) = (*engine).engine.read() {
        let resources = lock.url_cosmetic_resources(url_str);
        if !resources.hide_selectors.is_empty() {
            let selectors: Vec<&str> = resources.hide_selectors.iter().map(|s| s.as_str()).collect();
            let joined = selectors.join(", ");
            css_rules.push(format!("{} {{ display: none !important; }}", joined));
        }
    }

    // 2. Añadir reglas cosméticas curadas para YouTube, Twitch, Reddit, X, Forbes, etc.
    let curated = get_curated_cosmetic_css_for_url(url_str);
    if !curated.is_empty() {
        css_rules.push(curated);
    }

    let final_css = css_rules.join("\n\n");
    match CString::new(final_css) {
        Ok(c_string) => c_string.into_raw(),
        Err(_) => std::ptr::null_mut(),
    }
}

/// # Safety
///
/// Devuelve el código JavaScript de defusers anti-adblock para la URL dada (ej. YouTube, Admiral).
/// La memoria devuelta debe liberarse invocando `aegis_shields_free_string()`.
#[no_mangle]
pub unsafe extern "C" fn aegis_shields_get_injected_scripts(
    _engine: *mut AegisShieldsEngine,
    url: *const c_char,
) -> *mut c_char {
    if url.is_null() {
        return std::ptr::null_mut();
    }

    let url_str = match CStr::from_ptr(url).to_str() {
        Ok(s) => s,
        Err(_) => return std::ptr::null_mut(),
    };

    let script = get_injected_script_for_url(url_str);
    match CString::new(script) {
        Ok(c_string) => c_string.into_raw(),
        Err(_) => std::ptr::null_mut(),
    }
}

/// # Safety
///
/// Devuelve el total acumulado de anuncios y rastreadores bloqueados.
#[no_mangle]
pub unsafe extern "C" fn aegis_shields_get_blocked_count(engine: *mut AegisShieldsEngine) -> u64 {
    if engine.is_null() {
        0
    } else {
        (*engine).blocked_count.load(Ordering::Relaxed)
    }
}

/// # Safety
///
/// `s` debe ser una cadena asignada previamente por Rust vía `CString::into_raw()`, o ser nula.
#[no_mangle]
pub unsafe extern "C" fn aegis_shields_free_string(s: *mut c_char) {
    if !s.is_null() {
        drop(CString::from_raw(s));
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::ffi::CString;

    #[test]
    fn test_shields_blocking_logic() {
        unsafe {
            // aegis_shields_create() ahora viene con reglas por defecto integradas
            let engine = aegis_shields_create();
            assert!(!engine.is_null());

            // 1. Probar bloqueo de DoubleClick
            let ad_url = CString::new("https://ad.doubleclick.net/tracker.js").unwrap();
            let source_url = CString::new("https://news.com").unwrap();
            let req_type = CString::new("script").unwrap();

            let blocked = aegis_shields_should_block(
                engine,
                ad_url.as_ptr(),
                source_url.as_ptr(),
                req_type.as_ptr(),
            );
            assert!(blocked, "Doubleclick debería haber sido bloqueado");

            // 2. Probar bloqueo de Popups invasivos (PropellerAds)
            let popup_url = CString::new("https://propellerads.com/zone/pop.js").unwrap();
            let blocked_popup = aegis_shields_should_block(
                engine,
                popup_url.as_ptr(),
                source_url.as_ptr(),
                req_type.as_ptr(),
            );
            assert!(blocked_popup, "PropellerAds debería ser bloqueado");

            // 3. Probar bloqueo de YouTube Ads API
            let yt_ad = CString::new("https://www.youtube.com/api/stats/ads?ns=yt").unwrap();
            let yt_source = CString::new("https://www.youtube.com/watch?v=xyz").unwrap();
            let blocked_yt = aegis_shields_should_block(
                engine,
                yt_ad.as_ptr(),
                yt_source.as_ptr(),
                req_type.as_ptr(),
            );
            assert!(blocked_yt, "YouTube ads API debería ser bloqueado");

            // 4. Probar que sitios legítimos NO se bloquean
            let legitimate_url = CString::new("https://wikipedia.org/logo.png").unwrap();
            let not_blocked = aegis_shields_should_block(
                engine,
                legitimate_url.as_ptr(),
                source_url.as_ptr(),
                req_type.as_ptr(),
            );
            assert!(!not_blocked, "Wikipedia no debería ser bloqueada");

            // 5. Verificar contador acumulado de bloqueos
            let count = aegis_shields_get_blocked_count(engine);
            assert_eq!(count, 3, "Debería haber registrado 3 peticiones bloqueadas");

            // 6. Probar generación de hojas de estilo cosméticas
            let yt_url = CString::new("https://www.youtube.com/watch?v=dQw4w9WgXcQ").unwrap();
            let css_ptr = aegis_shields_get_cosmetic_stylesheet(engine, yt_url.as_ptr());
            assert!(!css_ptr.is_null());
            let css_str = CStr::from_ptr(css_ptr).to_str().unwrap();
            assert!(css_str.contains("ytd-ad-slot-renderer"));
            assert!(css_str.contains("display: none !important"));
            aegis_shields_free_string(css_ptr);

            // 7. Probar inyección de defusers de scriptlets para YouTube
            let scripts_ptr = aegis_shields_get_injected_scripts(engine, yt_url.as_ptr());
            assert!(!scripts_ptr.is_null());
            let script_str = CStr::from_ptr(scripts_ptr).to_str().unwrap();
            assert!(script_str.contains("Universal Anti-Adblock Defuser"));
            assert!(script_str.contains("YouTube Ad Skipper"));
            aegis_shields_free_string(scripts_ptr);

            // 8. Probar Twitch y Amazon Ad System
            let twitch_ad = CString::new("https://aax.amazon-adsystem.com/e/dtb/bid").unwrap();
            let twitch_source = CString::new("https://www.twitch.tv/ninja").unwrap();
            let blocked_twitch = aegis_shields_should_block(
                engine,
                twitch_ad.as_ptr(),
                twitch_source.as_ptr(),
                req_type.as_ptr(),
            );
            assert!(blocked_twitch, "Amazon Ad System en Twitch debe ser bloqueado");

            // 9. Probar Forbes y script anti-adblock Admiral
            let admiral_url = CString::new("https://delivery.adrecover.com/script.js").unwrap();
            let forbes_source = CString::new("https://www.forbes.com/sites/editor").unwrap();
            let blocked_admiral = aegis_shields_should_block(
                engine,
                admiral_url.as_ptr(),
                forbes_source.as_ptr(),
                req_type.as_ptr(),
            );
            assert!(blocked_admiral, "Script anti-adblock de Admiral debe ser bloqueado");

            let forbes_css_ptr = aegis_shields_get_cosmetic_stylesheet(engine, forbes_source.as_ptr());
            assert!(!forbes_css_ptr.is_null());
            let forbes_css = CStr::from_ptr(forbes_css_ptr).to_str().unwrap();
            assert!(forbes_css.contains(".fbs-ad"));
            aegis_shields_free_string(forbes_css_ptr);

            // 10. Probar Redes Sociales (Facebook Tracking Pixel & Twitter Ads)
            let fb_pixel = CString::new("https://www.facebook.com/tr/?id=12345&ev=PageView").unwrap();
            let blocked_fb = aegis_shields_should_block(
                engine,
                fb_pixel.as_ptr(),
                source_url.as_ptr(),
                req_type.as_ptr(),
            );
            assert!(blocked_fb, "Pixel de tracking de Facebook debe ser bloqueado");

            aegis_shields_destroy(engine);
        }
    }
}
