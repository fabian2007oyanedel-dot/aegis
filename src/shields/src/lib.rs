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
    let mut filter_set = FilterSet::new(true);
    let engine = Engine::from_filter_set(filter_set, true);
    Box::into_raw(Box::new(AegisShieldsEngine {
        engine: RwLock::new(engine),
    }))
}

#[no_mangle]
pub unsafe extern "C" fn aegis_shields_destroy(engine: *mut AegisShieldsEngine) {
    if !engine.is_null() {
        drop(Box::from_raw(engine));
    }
}

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
    filter_set.add_filter_list(c_str, ParseOptions::default());

    let new_engine = Engine::from_filter_set(filter_set, true);
    if let Ok(mut lock) = (*engine).engine.write() {
        *lock = new_engine;
        true
    } else {
        false
    }
}

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

    let req = match Request::from_url(url_str) {
        Ok(mut r) => {
            r.source_url = source_str.to_string();
            r.request_type = req_type_str.to_string();
            r
        }
        Err(_) => return false,
    };

    if let Ok(lock) = (*engine).engine.read() {
        let blocker_result = lock.check(&req);
        blocker_result.matched
    } else {
        false
    }
}

#[no_mangle]
pub unsafe extern "C" fn aegis_shields_free_string(s: *mut c_char) {
    if !s.is_null() {
        drop(CString::from_raw(s));
    }
}
