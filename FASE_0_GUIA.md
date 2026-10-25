# Fase 0: Cimientos — Guía de Ejecución

Esta guía te lleva paso a paso desde cero hasta tener un `aegis.exe` funcional compilado desde el código fuente de Chromium.

---

## Diagnóstico Actual del Entorno

Ejecuta esto primero para ver qué falta:

```powershell
cd "c:\Users\PC\Documents\antigravity\proud-tesla\instance_creator\profiles\capsuit\home\.gemini\antigravity\scratch\aegis-browser"
python scripts\verify_env.py
```

**Estado actual confirmado:**

| Prerequisito | Estado | Notas |
|:---|:---:|:---|
| Python 3.14 | ✅ | Instalado y funcional |
| Git 2.55 | ✅ | Instalado y funcional |
| Ninja | ✅ | Disponible en PATH |
| Disco D: (382 GB libres) | ✅ | Espacio más que suficiente |
| Rust / Cargo | ❌ | Falta instalar |
| depot_tools | ❌ | Falta instalar |
| Visual Studio Build Tools (MSVC) | ❌ | Falta instalar |
| Windows SDK | ❌ | Falta instalar |
| Código fuente de Chromium | ❌ | Se descarga en el paso 2 |

---

## Paso 1: Instalar los Prerequisitos (Bootstrap)

> [!IMPORTANT]
> Abre PowerShell **como Administrador** (clic derecho → "Ejecutar como administrador")

```powershell
# Navegar al proyecto
cd "c:\Users\PC\Documents\antigravity\proud-tesla\instance_creator\profiles\capsuit\home\.gemini\antigravity\scratch\aegis-browser"

# Ejecutar bootstrap completo
.\scripts\phase0_bootstrap.ps1 -ChromiumSrcDir "D:\aegis-chromium-src" -DepotToolsDir "D:\depot_tools"
```

**Qué hace este script:**
1. Instala **Rust** (stable-msvc) via rustup
2. Instala **Visual Studio Build Tools 2022** con el workload de C++ y Windows 11 SDK
3. Clona **depot_tools** en `D:\depot_tools` y lo agrega al PATH del sistema
4. Hace bootstrap de gclient
5. Crea el directorio `D:\aegis-chromium-src`
6. Inicia el **fetch de Chromium** (~35 GB, 1-3 horas según velocidad de internet)

> [!NOTE]
> Si quieres solo instalar las herramientas sin descargar Chromium aún, usa `-SkipFetch`:
> ```powershell
> .\scripts\phase0_bootstrap.ps1 -SkipFetch
> ```

---

## Paso 2: Verificar el Entorno Post-Bootstrap

```powershell
# Abrir una NUEVA sesión de PowerShell (para que tome el PATH actualizado)
python scripts\verify_env.py
```

Todos los ítems deben aparecer como `[OK]` antes de continuar.

---

## Paso 3: Compilar Chromium Vanilla

> [!WARNING]
> La primera compilación toma entre **2 y 6 horas** dependiendo del hardware.
> Las compilaciones incrementales (después de cambiar un solo archivo) tardan minutos.

```powershell
.\scripts\phase0_compile.ps1 -ChromiumSrcDir "D:\aegis-chromium-src" -DepotToolsDir "D:\depot_tools"
```

**Qué hace:**
1. `gclient sync` — sincroniza sub-dependencias de Chromium
2. `gn gen out\Aegis` — genera el sistema de build con nuestro `args.gn`
3. `autoninja -C out\Aegis chrome` — compila el navegador usando todos los núcleos
4. Verifica que `chrome.exe` existe y tiene tamaño válido
5. Lo copia como `aegis.exe` para prueba

---

## Paso 4: Verificar el Entregable

Después de compilar, deberías tener:

```
D:\aegis-chromium-src\src\out\Aegis\
├── aegis.exe          ← El navegador compilado
├── chrome.dll         ← DLL principal
├── v8_context_snapshot.bin
├── icudtl.dat
└── locales\
    └── es.pak, en-US.pak, ...
```

**Verificación manual:**
1. Abrir `D:\aegis-chromium-src\src\out\Aegis\aegis.exe` → debe abrir el navegador
2. Navegar a `example.com` → debe renderizar la página
3. Abrir `chrome://version` → verificar que muestra la versión de Chromium compilada

---

## Paso 5: Gestión de Parches (Para Uso Futuro)

El gestor de parches te permite aplicar/revertir las modificaciones de Aegis:

```powershell
# Listar estado de todos los parches
python scripts\apply_patches.py --src D:\aegis-chromium-src\src --list

# Aplicar todos los parches en orden
python scripts\apply_patches.py --src D:\aegis-chromium-src\src

# Revertir todos los parches
python scripts\apply_patches.py --src D:\aegis-chromium-src\src --reverse

# Aplicar solo un parche específico (ej: el de telemetría)
python scripts\apply_patches.py --src D:\aegis-chromium-src\src --patch 001
```

> [!NOTE]
> En la Fase 0 no se aplican parches todavía. Los parches se aplican a partir de la **Fase 1**.

---

## Estimación de Tiempo y Recursos

| Paso | Tiempo estimado | Espacio necesario |
|:---|:---:|:---:|
| Bootstrap (herramientas) | 10-30 min | ~5 GB |
| Fetch de Chromium | 1-3 horas | ~35 GB |
| Compilación vanilla | 2-6 horas | ~45 GB adicionales |
| **Total** | **3-9 horas** | **~85 GB en D:** |

**Especificaciones de tu máquina:**
- Disco D: **382 GB libres** ✅ (suficiente de sobra)
- Se usará `D:\aegis-chromium-src` como directorio de trabajo

---

## Entregable de Fase 0

✅ Un ejecutable `aegis.exe` (Chromium vanilla renombrado) que:
- Abre y navega páginas web
- Usa las flags de optimización de `args.gn` (LTO, sin debug symbols)
- NO tiene aún las modificaciones de privacidad ni Aegis Shields (eso es Fase 1 y 2)

Una vez verificado, estás listo para **Fase 1: De-Googled**.
