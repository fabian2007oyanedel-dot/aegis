# Aegis Browser 🛡️

[![Build Status](https://img.shields.io/badge/Build-GitHub%20Actions-brightgreen)](https://github.com/fabian2007oyanedel-dot/aegis/actions)
[![Rust](https://img.shields.io/badge/Shields%20Core-Rust%201.99-orange)](src/shields/)
[![Platform](https://img.shields.io/badge/Platform-Windows%20x64%20%7C%20Android%20ARM64-blue)](#)
[![Privacy](https://img.shields.io/badge/Privacy-100%25%20De--Googled-success)](#)

**Aegis Browser** es un navegador web de alto rendimiento centrado en la velocidad pura, el bajo consumo de recursos y la privacidad estricta. Toma como base **Chromium limpio**, extirpando toda la telemetría corporativa y servicios de Google, e integrando de forma nativa en Rust el motor de bloqueo de **Brave Shields (`adblock-rust`)** a nivel de red (`URLLoaderThrottle`).

---

## ⚡ Características Principales

1. **Cero Bloatware y Cero Criptomonedas:** Sin billeteras, sin tokens BAT, sin programas de recompensas, sin telemetría P3A ni rastreadores de Google Analytics.
2. **Motor de Bloqueo Nativo (Rust):** Utiliza el motor oficial de `adblock-rust` de Brave. Las peticiones a publicidad se cancelan en microsegundos antes de abrir sockets de red.
3. **Anti-Fingerprinting Avanzado (*Farbling*):** Inyección de ruido en APIs de Canvas y AudioContext para impedir que los rastreadores perfilen tu máquina.
4. **Pestañas a tu Medida:** Pestañas clásicas horizontales por defecto, con interruptor en Configuración para activar **Pestañas Verticales Plegables**.
5. **Cifrado 100% Local:** Contraseñas e historial cifrados mediante la clave del sistema operativo (**Windows DPAPI / Android Keystore**). Cero dependencia de cuentas en la nube.
6. **Optimizado para Android ARM64:** Compatible con pantallas de 120Hz sin tirones (*jank-free scroll*), soporte de barra inferior táctil y ahorro agresivo de batería.
7. **Compilación en la Nube (GitHub Actions):** No necesitas 100 GB libres en tu disco ni instalar gigabytes de compiladores. GitHub Actions compila los instaladores (`.exe` y `.apk`) automáticamente en la nube.
8. **Arquitectura Ultra Eficiente (100x Improvement):** Punteros V8 comprimidos (~40% menos RAM), PartitionAlloc con purga de páginas libres hacia el SO en reposo, estrangulamiento de timers en segundo plano a 1Hz, suspensión rápida de pestañas en 5 minutos, y una WebUI con 4 temas, gestor de marcadores, bloc de notas privado y generador de contraseñas de alta entropía.

---

## 📁 Estructura del Repositorio

```text
aegis-browser/
├── .github/
│   └── workflows/
│       ├── build-windows.yml       # Pipeline CI/CD para compilar el ejecutable Windows x64
│       ├── build-android.yml       # Pipeline CI/CD para compilar el APK de Android ARM64
│       └── release-v1.0.yml        # Pipeline de publicación de la Release Oficial v1.0.0
├── config/
│   ├── args.gn                     # Parámetros GN optimizados para Windows (AVX2, sin telemetría)
│   ├── args-android.gn             # Parámetros GN optimizados para Android (ARM64, sin GMS)
│   └── default_settings.json       # Configuración inicial de privacidad estricta (Do Not Track, dFPI)
├── patches/
│   ├── 001-strip-telemetry.patch   # Desconexión de métricas UMA/UKM y servicios remotos
│   ├── 002-disable-sync.patch      # Eliminación completa del subsistema de cuentas y sync
│   ├── 003-vertical-tabs.patch     # Soporte para alternar pestañas horizontales y verticales
│   ├── 004-shields-throttle.patch  # Inyección de adblock-rust en el URLLoader de Chromium
│   ├── 005-branding-identity.patch # Renombrado de binarios y User-Agent a Aegis/1.0
│   ├── 006-custom-ntp.patch        # Inyección de la New Tab Page limpia y privada
│   ├── 007-local-storage-encryption.patch # Cifrado DPAPI local y aislamiento dFPI
│   ├── 008-data-retention-clearing.patch  # Borrado al salir y reanudación de descargas
│   ├── 009-android-touch-ui.patch  # Barra inferior táctil y navegación por gestos en Android
│   ├── 010-android-keystore.patch  # Cifrado con chip seguro local (Android KeyStore)
│   ├── 011-android-battery-saver.patch    # Sincronización a 120Hz y ahorro de batería
│   ├── 012-anti-fingerprinting.patch      # Protección Farbling en Canvas, WebGL y Audio
│   ├── 013-webrtc-leak-prevention.patch   # Prevención de fuga de IP local y VPN en WebRTC
│   └── 014-extreme-resource-optimization.patch # Purga de RAM en reposo (PartitionAlloc) y estrangulación de CPU 1Hz
├── src/
│   ├── shields/                    # Motor de bloqueo nativo en Rust (adblock-rust FFI)
│   │   ├── Cargo.toml
│   │   ├── src/lib.rs              # Puente FFI C/C++ <-> Rust con tests unitarios
│   │   └── include/aegis_shields.h # Cabecera C++ para el motor de Chromium
│   └── ui/                         # Interfaz gráfica propia
│       ├── assets/aegis-logo.svg   # Logo vectorizado oficial
│       └── ntp/                    # New Tab Page (4 Temas, Marcadores, Bloc de notas, Generador de Contraseñas)
├── scripts/
│   ├── apply_patches.py            # Gestor automatizado de parches con rollback
│   ├── audit_codebase.py           # Auditoría integral de la base de código
│   ├── verify_phase1.py            # Suite de pruebas de desgooglizado
│   ├── verify_phase3.py            # Suite de pruebas de interfaz y NTP
│   ├── verify_phase4.py            # Suite de pruebas de cifrado y retención
│   ├── verify_phase5.py            # Suite de pruebas de Android ARM64
│   ├── verify_phase6.py            # Suite de pruebas de release y anti-fingerprinting
│   └── verify_ultra_enhancements.py # Suite de validación de optimizaciones 100x y UI Hub
└── README.md
```

---

## 🚀 Cómo Descargar y Compilar

1. Ve a la pestaña **[Actions](https://github.com/fabian2007oyanedel-dot/aegis/actions)** de tu repositorio.
2. Selecciona **Build Aegis Browser (Windows x64)** o **Build Aegis Browser (Android ARM64)**.
3. Descarga el paquete compilado directamente desde la sección **Artifacts** o **Releases**.
