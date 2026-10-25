#ifndef AEGIS_SHIELDS_H_
#define AEGIS_SHIELDS_H_

#include <stdbool.h>
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

// Puntero opaco al motor de filtrado en Rust
typedef struct AegisShieldsEngine AegisShieldsEngine;

/**
 * Inicializa una nueva instancia del motor Aegis Shields (adblock-rust).
 */
AegisShieldsEngine* aegis_shields_create(void);

/**
 * Libera la memoria del motor y sus estructuras de datos.
 */
void aegis_shields_destroy(AegisShieldsEngine* engine);

/**
 * Carga reglas de filtrado en formato uBlock / EasyList / Adblock Plus.
 * Retorna true si se cargaron y compilaron con éxito.
 */
bool aegis_shields_load_rules(AegisShieldsEngine* engine, const char* rules_text);

/**
 * Consulta en microsegundos si una petición de red debe ser bloqueada.
 * Se invoca dentro de URLLoaderThrottle antes de abrir la conexión HTTP/HTTPS.
 * 
 * @param engine Instancia del motor.
 * @param url URL de destino que se intenta cargar.
 * @param source_url URL de la página origen que originó la petición.
 * @param request_type Tipo de recurso ("script", "image", "xmlhttprequest", "subdocument", etc.).
 * @return true si la petición debe ser abortada inmediatamente; false si se permite.
 */
bool aegis_shields_should_block(
    AegisShieldsEngine* engine,
    const char* url,
    const char* source_url,
    const char* request_type
);

/**
 * Obtiene la hoja de estilos CSS cosmética (element hiding) para la URL consultada.
 * Oculta contenedores de anuncios en YouTube, Twitch, Twitter/X, Reddit, Forbes, etc.
 * La cadena devuelta debe liberarse con aegis_shields_free_string().
 */
char* aegis_shields_get_cosmetic_stylesheet(
    AegisShieldsEngine* engine,
    const char* url
);

/**
 * Obtiene los scriptlets de desactivación anti-adblock para la URL consultada.
 * Neutraliza el modal de bloqueo de YouTube y detectores como Admiral antes de que se ejecuten.
 * La cadena devuelta debe liberarse con aegis_shields_free_string().
 */
char* aegis_shields_get_injected_scripts(
    AegisShieldsEngine* engine,
    const char* url
);

/**
 * Retorna el contador total acumulado de anuncios y rastreadores bloqueados.
 */
unsigned long long aegis_shields_get_blocked_count(AegisShieldsEngine* engine);

/**
 * Libera cadenas devueltas por el motor Rust.
 */
void aegis_shields_free_string(char* s);

#ifdef __cplusplus
}
#endif

#endif  // AEGIS_SHIELDS_H_
