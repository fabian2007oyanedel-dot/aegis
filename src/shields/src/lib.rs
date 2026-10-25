use std::ffi::{CStr, CString};
use std::os::raw::c_char;
use std::sync::RwLock;
use adblock::Engine;
use adblock::lists::{FilterSet, ParseOptions};
use adblock::request::Request;

/// Estructura interna que envuelve el motor adblock-rust de Brave
pub struct AegisShieldsEngine {
    engine: RwLock<Engine>,
}

#[no_mangle]
pub extern "C" fn aegis_shields_create() -> *mut AegisShieldsEngine {
    let filter_set = FilterSet::new(true);
    let engine = Engine::new_with_filter_set(filter_set);
    Box::into_raw(Box::new(AegisShieldsEngine {
        engine: RwLock::new(engine),
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
        blocker_result.should_block()
    } else {
        false
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
            let engine = aegis_shields_create();
            assert!(!engine.is_null());

            let rules = CString::new("||doubleclick.net^\n||google-analytics.com^").unwrap();
            let loaded = aegis_shields_load_rules(engine, rules.as_ptr());
            assert!(loaded);

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

            let legitimate_url = CString::new("https://wikipedia.org/logo.png").unwrap();
            let not_blocked = aegis_shields_should_block(
                engine,
                legitimate_url.as_ptr(),
                source_url.as_ptr(),
                req_type.as_ptr(),
            );
            assert!(!not_blocked, "Wikipedia no debería ser bloqueada");

            aegis_shields_destroy(engine);
        }
    }
}
