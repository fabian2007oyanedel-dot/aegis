# Aegis Browser 🛡️

**Aegis Browser** es un navegador web de alto rendimiento centrado en la privacidad y la velocidad pura. Toma como base **Chromium limpio**, extirpando toda la telemetría corporativa y servicios innecesarios, e integrando de forma nativa en Rust el motor de bloqueo de **Brave Shields (`adblock-rust`)** a nivel de red (`URLLoaderThrottle`).

---

## ⚡ Principios de Diseño

1. **Sin Bloatware ni Cripto:** Cero billeteras, cero tokens BAT, cero programas de recompensas, cero VPNs de pago, cero telemetría P3A o Google Analytics.
2. **Motor de Bloqueo Nativo (Rust):** Utiliza el motor oficial de `adblock-rust` de Brave. Las peticiones a rastreadores y publicidad se bloquean antes de abrir sockets de red.
3. **Pestañas a tu Medida:** Pestañas clásicas horizontales por defecto, con interruptor en Configuración (`aegis://settings`) para activar **Pestañas Verticales Plegables**.
4. **100% Local y Privado:** Sin sincronización obligatoria en la nube ni inicios de sesión. Contraseñas e historial cifrados localmente en tu sistema operativo (Windows DPAPI / Android Keystore).
5. **Compilación en la Nube (GitHub Actions):** No necesitas 100 GB libres en tu disco local ni instalar gigabytes de compiladores. GitHub Actions compila los instaladores (`.exe` y `.apk`) automáticamente en la nube.

---

## 📁 Estructura del Proyecto

```text
aegis-browser/
├── .github/
│   └── workflows/
│       ├── build-windows.yml       # Pipeline CI/CD para compilar el instalador Windows x64
│       └── build-android.yml       # Pipeline CI/CD para compilar el APK de Android
├── config/
│   ├── args.gn                     # Parámetros de compilación GN optimizados (AVX2, sin telemetría)
│   └── default_settings.json       # Configuración inicial de privacidad y UI
├── patches/
│   ├── 001-strip-telemetry.patch   # Desconexión de métricas de Google y servicios remotos
│   ├── 002-disable-sync.patch      # Eliminación completa del subsistema de cuentas y sync
│   ├── 003-vertical-tabs.patch     # Soporte para alternar pestañas horizontales y verticales
│   └── 004-shields-throttle.patch  # Inyección de adblock-rust en el URLLoader de Chromium
├── src/
│   └── shields/
│       ├── Cargo.toml              # Definición de la librería Rust de filtrado (adblock-rust)
│       ├── src/lib.rs              # Enlaces FFI (C/C++ -> Rust) para inspección de URLs
│       └── include/aegis_shields.h # Cabecera C++ para el motor de Chromium
└── README.md
```

---

## 🚀 Cómo Compilar (Vía GitHub Actions)

1. Sube este repositorio a tu cuenta de **GitHub** (puede ser un repositorio privado o público).
2. Ve a la pestaña **Actions**.
3. Ejecuta el workflow **Build Aegis Browser (Windows)** o **Build Aegis Browser (Android)**.
4. Una vez finalizado (los servidores de GitHub compilan Chromium en la nube), descarga el instalador listo para usar desde la sección **Releases / Artifacts**.
