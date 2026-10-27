import sys, os, subprocess, shutil, zipfile, re
from pathlib import Path

print("="*65)
print("COMPILANDO AEGIS BROWSER 2.0 (100X MOBILE OVERHAUL - ARM64)")
print("="*65)

BUILD_TOOLS_DIR = Path(r"C:\Users\PC\AppData\Local\Android\Sdk\build-tools\35.0.0")
PLATFORM_DIR = Path(r"C:\Users\PC\AppData\Local\Android\Sdk\platforms\android-34")

AAPT2 = BUILD_TOOLS_DIR / "aapt2.exe"
D8 = BUILD_TOOLS_DIR / "d8.bat"
ZIPALIGN = BUILD_TOOLS_DIR / "zipalign.exe"
APKSIGNER = BUILD_TOOLS_DIR / "apksigner.bat"
ANDROID_JAR = PLATFORM_DIR / "android.jar"

output_dir = Path("dist/android")
output_dir.mkdir(parents=True, exist_ok=True)
final_apk = output_dir / "Aegis-arm64-v8a.apk"

work_dir = Path("build/android_100x")
if work_dir.exists():
    shutil.rmtree(work_dir)
work_dir.mkdir(parents=True, exist_ok=True)

src_java_dir = work_dir / "src" / "org" / "aegis" / "browser"
res_dir = work_dir / "res"
res_values = res_dir / "values"
res_layout = res_dir / "layout"
res_drawable = res_dir / "drawable"
assets_dir = work_dir / "assets"
bin_dir = work_dir / "bin"
compiled_res_dir = work_dir / "compiled_res"

for d in [src_java_dir, res_values, res_layout, res_drawable, assets_dir, bin_dir, compiled_res_dir]:
    d.mkdir(parents=True, exist_ok=True)

# ── 1. AndroidManifest.xml con PiP y permisos completos ───────────────────────
manifest_content = """<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="org.aegis.browser"
    android:versionCode="5"
    android:versionName="1.5.0">

    <uses-sdk android:minSdkVersion="26" android:targetSdkVersion="34" />

    <uses-permission android:name="android.permission.INTERNET" />
    <uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />
    <uses-permission android:name="android.permission.DOWNLOAD_WITHOUT_NOTIFICATION" />
    <uses-permission android:name="android.permission.WRITE_EXTERNAL_STORAGE" android:maxSdkVersion="28" />

    <application
        android:label="Aegis Browser"
        android:icon="@drawable/ic_launcher"
        android:theme="@android:style/Theme.NoTitleBar.Fullscreen"
        android:hardwareAccelerated="true"
        android:largeHeap="true"
        android:usesCleartextTraffic="true">

        <activity
            android:name=".MainActivity"
            android:exported="true"
            android:supportsPictureInPicture="true"
            android:configChanges="orientation|screenSize|keyboardHidden|smallestScreenSize|screenLayout"
            android:windowSoftInputMode="adjustResize">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
            <intent-filter>
                <action android:name="android.intent.action.VIEW" />
                <category android:name="android.intent.category.DEFAULT" />
                <category android:name="android.intent.category.BROWSABLE" />
                <data android:scheme="http" />
                <data android:scheme="https" />
            </intent-filter>
        </activity>
    </application>
</manifest>
"""
(work_dir / "AndroidManifest.xml").write_text(manifest_content, encoding="utf-8")

# ── 2. Vector Drawables (100% SVG Nativo, Cero Emojis) ────────────────────────
def write_svg_vector(filename, color, path_data, alpha="1.0"):
    content = f"""<?xml version="1.0" encoding="utf-8"?>
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="24dp" android:height="24dp"
    android:viewportWidth="24" android:viewportHeight="24">
    <path android:fillColor="{color}" android:fillAlpha="{alpha}"
        android:pathData="{path_data}"/>
</vector>"""
    (res_drawable / filename).write_text(content, encoding="utf-8")

# App Icon (Neo-Sculptural Continuous Ribbon A-Shield)
(res_drawable / "ic_launcher.xml").write_text("""<?xml version="1.0" encoding="utf-8"?>
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="108dp" android:height="108dp"
    android:viewportWidth="512" android:viewportHeight="512">
    <path android:fillColor="#06090e" android:pathData="M0,0h512v512h-512z"/>
    <!-- Ala Derecha -->
    <path android:fillColor="#38bdf8" android:pathData="M 256,60 C 272,60 286,72 296,92 L 396,360 C 412,402 386,444 346,444 C 324,444 304,428 296,406 L 264,318 L 230,222 L 256,126 Z"/>
    <!-- Ala Izquierda -->
    <path android:fillColor="#00f5ff" android:pathData="M 120,412 C 102,368 116,320 144,252 L 216,92 C 226,72 240,60 256,60 C 272,60 284,70 292,88 L 266,154 L 204,308 L 166,406 C 158,428 138,444 116,444 C 102,444 94,436 94,426 C 94,420 98,414 104,410 Z"/>
    <!-- Travesaño Escultural -->
    <path android:fillColor="#818cf8" android:pathData="M 154,290 C 154,274 168,262 184,262 L 328,262 C 344,262 358,274 358,290 C 358,306 344,318 328,318 L 184,318 C 168,318 154,306 154,290 Z"/>
</vector>
""", encoding="utf-8")

# Iconos principales de navegación
write_svg_vector("ic_shield.xml", "#388bfd", "M12,1L3,5v6c0,5.55 3.84,10.74 9,12 5.16,-1.26 9,-6.45 9,-12V5l-9,-4z")
write_svg_vector("ic_arrow_back.xml", "#e6edf3", "M20,11H7.83l5.59,-5.59L12,4l-8,8 8,8 1.41,-1.41L7.83,13H20v-2z")
write_svg_vector("ic_arrow_forward.xml", "#e6edf3", "M12,4l-1.41,1.41L16.17,11H4v2h12.17l-5.58,5.59L12,20l8,-8z")
write_svg_vector("ic_home.xml", "#e6edf3", "M10,20v-6h4v6h5v-8h3L12,3 2,12h3v8z")
write_svg_vector("ic_more_vert.xml", "#e6edf3", "M12,8c1.1,0 2,-0.9 2,-2s-0.9,-2 -2,-2 -2,0.9 -2,2 0.9,2 2,2zm0,2c-1.1,0 -2,0.9 -2,2s0.9,2 2,2 2,-0.9 2,-2 -0.9,-2 -2,-2zm0,6c-1.1,0 -2,0.9 -2,2s0.9,2 2,2 2,-0.9 2,-2 -0.9,-2 -2,-2z")
write_svg_vector("ic_refresh.xml", "#e6edf3", "M17.65,6.35C16.2,4.9 14.21,4 12,4c-4.42,0 -7.99,3.58 -7.99,8s3.57,8 7.99,8c3.73,0 6.84,-2.55 7.73,-6h-2.08c-0.82,2.33 -3.04,4 -5.65,4 -3.31,0 -6,-2.69 -6,-6s2.69,-6 6,-6c1.66,0 3.14,0.69 4.22,1.78L13,11h7V4l-2.35,2.35z")
write_svg_vector("ic_close.xml", "#8b949e", "M19,6.41L17.59,5 12,10.59 6.41,5 5,6.41 10.59,12 5,17.59 6.41,19 12,13.41 17.59,19 19,17.59 13.41,12z")
write_svg_vector("ic_add.xml", "#ffffff", "M19,13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z")
write_svg_vector("ic_search.xml", "#8b949e", "M15.5,14h-0.79l-0.28,-0.27C15.41,12.59 16,11.11 16,9.5 16,5.91 13.09,3 9.5,3S3,5.91 3,9.5 5.91,16 9.5,16c1.61,0 3.09,-0.59 4.23,-1.57l0.27,0.28v0.79l5,4.99L20.49,19l-4.99,-5zm-6,0C7.01,14 5,11.99 5,9.5S7.01,5 9.5,5 14,7.01 14,9.5 11.99,14 9.5,14z")
write_svg_vector("ic_lock.xml", "#3fb950", "M18,8h-1V6c0,-2.76 -2.24,-5 -5,-5S7,3.24 7,6v2H6c-1.1,0 -2,0.9 -2,2v10c0,1.1 0.9,2 2,2h12c1.1,0 2,-0.9 2,-2V10c0,-1.1 -0.9,-2 -2,-2zm-6,9c-1.1,0 -2,-0.9 -2,-2s0.9,-2 2,-2 2,0.9 2,2 -0.9,2 -2,2zm3.1,-9H8.9V6c0,-1.71 1.39,-3.1 3.1,-3.1 1.71,0 3.1,1.39 3.1,3.1v2z")

# Iconos de Menú y Funciones
write_svg_vector("ic_extension.xml", "#bc8cff", "M20.5,11H19V7c0,-1.1 -0.9,-2 -2,-2h-4V3.5C13,2.12 11.88,1 10.5,1S8,2.12 8,3.5V5H4c-1.1,0 -1.99,0.9 -1.99,2v3.8H3.5c1.49,0 2.7,1.21 2.7,2.7s-1.21,2.7 -2.7,2.7H2V20c0,1.1 0.9,2 2,2h3.8v-1.5c0,-1.49 1.21,-2.7 2.7,-2.7 1.49,0 2.7,1.21 2.7,2.7V22H17c1.1,0 2,-0.9 2,-2v-4h1.5c1.38,0 2.5,-1.12 2.5,-2.5s-1.12,-2.5 -2.5,-2.5z")
write_svg_vector("ic_star.xml", "#e3b341", "M12,17.27L18.18,21l-1.64,-7.03L22,9.24l-7.19,-0.61L12,2 9.19,8.63 2,9.24l5.46,4.73L5.82,21z")
write_svg_vector("ic_bookmark.xml", "#58a6ff", "M17,3H7c-1.1,0 -1.99,0.9 -1.99,2L5,21l7,-3 7,3V5c0,-1.1 -0.9,-2 -2,-2z")
write_svg_vector("ic_history.xml", "#79c0ff", "M13,3c-4.97,0 -9,4.03 -9,9H1l3.89,3.89.07,0.14L9,12H6c0,-3.87 3.13,-7 7,-7s7,3.13 7,7 -3.13,7 -7,7c-1.93,0 -3.68,-0.79 -4.94,-2.06l-1.42,1.42C8.27,19.99 10.51,21 13,21c4.97,0 9,-4.03 9,-9s-4.03,-9 -9,-9zm-1,5v5l4.28,2.54.72,-1.21 -3.5,-2.08V8H12z")
write_svg_vector("ic_download.xml", "#3fb950", "M19,9h-4V3H9v6H5l7,7 7,-7zM5,18v2h14v-2H5z")
write_svg_vector("ic_desktop.xml", "#7ee787", "M20,18c1.1,0 1.99,-0.9 1.99,-2L22,5c0,-1.1 -0.9,-2 -2,-2H4c-1.1,0 -2,0.9 -2,2v11c0,1.1 0.9,2 2,2H0c0,1.1 0.9,2 2,2h20c1.1,0 2,-0.9 2,-2h-4zM4,5h16v11H4V5z")
write_svg_vector("ic_moon.xml", "#d2a8ff", "M12.3,2a10,10 0 0,0 -1.9,0.18 10,10 0 1,0 11.42,11.42A10,10 0 0,0 12.3,2z")
write_svg_vector("ic_incognito.xml", "#8b949e", "M12,2A10,10 0 0,0 2,12c0,4.42 2.87,8.17 6.84,9.5.5,0.08 0.66,-0.23 0.66,-0.5v-1.69c-2.77,0.6 -3.36,-1.34 -3.36,-1.34 -0.46,-1.16 -1.11,-1.47 -1.11,-1.47 -0.91,-0.62 0.07,-0.6 0.07,-0.6 1,0.07 1.53,1.03 1.53,1.03 0.87,1.52 2.34,1.07 2.91,0.83 0.1,-0.65 0.35,-1.09 0.63,-1.34 -2.22,-0.25 -4.55,-1.11 -4.55,-4.92 0,-1.11 0.38,-2 1.03,-2.71 -0.1,-0.25 -0.45,-1.29 0.1,-2.64 0,0 0.84,-0.27 2.75,1.02 0.79,-0.22 1.65,-0.33 2.5,-0.33 0.85,0 1.71,0.11 2.5,0.33 1.91,-1.29 2.75,-1.02 2.75,-1.02 0.55,1.35 0.2,2.39 0.1,2.64 0.65,0.71 1.03,1.6 1.03,2.71 0,3.82 -2.34,4.66 -4.57,4.91 0.36,0.31 0.69,0.92 0.69,1.85V21c0,0.27 0.16,0.59 0.67,0.5C19.14,20.16 22,16.42 22,12A10,10 0 0,0 12,2z")
write_svg_vector("ic_delete.xml", "#f85149", "M6,19c0,1.1 0.9,2 2,2h8c1.1,0 2,-0.9 2,-2V7H6v12zM19,4h-3.5l-1,-1h-5l-1,1H5v2h14V4z")
write_svg_vector("ic_settings.xml", "#8b949e", "M19.14,12.94c0.04,-0.3 0.06,-0.61 0.06,-0.94 0,-0.32 -0.02,-0.64 -0.07,-0.94l2.03,-1.58c0.18,-0.14 0.23,-0.41 0.12,-0.61l-1.92,-3.32c-0.12,-0.22 -0.37,-0.29 -0.59,-0.22l-2.39,0.96c-0.5,-0.38 -1.03,-0.7 -1.62,-0.94l-0.36,-2.54c-0.04,-0.24 -0.24,-0.41 -0.48,-0.41h-3.84c-0.24,0 -0.43,0.17 -0.47,0.41l-0.36,2.54c-0.59,0.24 -1.13,0.57 -1.62,0.94l-2.39,-0.96c-0.22,-0.08 -0.47,0 -0.59,0.22L2.74,8.87c-0.12,0.21 -0.08,0.47 0.12,0.61l2.03,1.58c-0.05,0.3 -0.09,0.63 -0.09,0.94s0.02,0.64 0.07,0.94l-2.03,1.58c-0.18,0.14 -0.23,0.41 -0.12,0.61l1.92,3.32c0.12,0.22 0.37,0.29 0.59,0.22l2.39,-0.96c0.5,0.38 1.03,0.7 1.62,0.94l0.36,2.54c0.05,0.24 0.24,0.41 0.48,0.41h3.84c0.24,0 0.44,-0.17 0.47,-0.41l0.36,-2.54c0.59,-0.24 1.13,-0.56 1.62,-0.94l2.39,0.96c0.22,0.08 0.47,0 0.59,-0.22l1.92,-3.32c0.12,-0.22 0.07,-0.47 -0.12,-0.61l-2.01,-1.58zM12,15.6c-1.98,0 -3.6,-1.62 -3.6,-3.6s1.62,-3.6 3.6,-3.6 3.6,1.62 3.6,3.6 -1.62,3.6 -3.6,3.6z")
write_svg_vector("ic_movie.xml", "#ff7b72", "M18,4l2,4h-3l-2,-4h-2l2,4h-3l-2,-4H8l2,4H7L5,4H4c-1.1,0 -1.99,0.9 -1.99,2L2,18c0,1.1 0.9,2 2,2h16c1.1,0 2,-0.9 2,-2V4h-4z")
write_svg_vector("ic_file.xml", "#79c0ff", "M14,2H6c-1.1,0 -1.99,0.9 -1.99,2L4,20c0,1.1 0.89,2 1.99,2H18c1.1,0 2,-0.9 2,-2V8l-6,-6zm2,16H8v-2h8v2zm0,-4H8v-2h8v2zm-3,-5V3.5L18.5,9H13z")
write_svg_vector("ic_play.xml", "#ffffff", "M8,5v14l11,-7z")

# Tab Box con contorno
(res_drawable / "ic_tab_box.xml").write_text("""<?xml version="1.0" encoding="utf-8"?>
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="24dp" android:height="24dp"
    android:viewportWidth="24" android:viewportHeight="24">
    <path android:strokeColor="#e6edf3" android:strokeWidth="2" android:fillColor="#00000000"
        android:pathData="M6,4h12c1.1,0 2,0.9 2,2v12c0,1.1 -0.9,2 -2,2H6c-1.1,0 -2,-0.9 -2,-2V6c0,-1.1 0.9,-2 2,-2z"/>
</vector>
""", encoding="utf-8")

# Background Drawables (Bordes, Sombras y Elevaciones)
(res_drawable / "bg_omnibox.xml").write_text("""<?xml version="1.0" encoding="utf-8"?>
<shape xmlns:android="http://schemas.android.com/apk/res/android" android:shape="rectangle">
    <solid android:color="#161b22"/>
    <corners android:radius="22dp"/>
    <stroke android:width="1dp" android:color="#30363d"/>
</shape>
""", encoding="utf-8")

(res_drawable / "bg_tab_card.xml").write_text("""<?xml version="1.0" encoding="utf-8"?>
<shape xmlns:android="http://schemas.android.com/apk/res/android" android:shape="rectangle">
    <solid android:color="#161b22"/>
    <corners android:radius="14dp"/>
    <stroke android:width="1.5dp" android:color="#21262d"/>
</shape>
""", encoding="utf-8")

(res_drawable / "bg_tab_card_active.xml").write_text("""<?xml version="1.0" encoding="utf-8"?>
<shape xmlns:android="http://schemas.android.com/apk/res/android" android:shape="rectangle">
    <solid android:color="#161b22"/>
    <corners android:radius="14dp"/>
    <stroke android:width="2dp" android:color="#388bfd"/>
</shape>
""", encoding="utf-8")

(res_drawable / "bg_bottom_sheet.xml").write_text("""<?xml version="1.0" encoding="utf-8"?>
<shape xmlns:android="http://schemas.android.com/apk/res/android" android:shape="rectangle">
    <solid android:color="#161b22"/>
    <corners android:topLeftRadius="22dp" android:topRightRadius="22dp"/>
    <stroke android:width="1dp" android:color="#30363d"/>
</shape>
""", encoding="utf-8")

(res_drawable / "bg_card_inner.xml").write_text("""<?xml version="1.0" encoding="utf-8"?>
<shape xmlns:android="http://schemas.android.com/apk/res/android" android:shape="rectangle">
    <solid android:color="#0d1117"/>
    <corners android:radius="12dp"/>
    <stroke android:width="1dp" android:color="#21262d"/>
</shape>
""", encoding="utf-8")

(res_drawable / "bg_badge_shield.xml").write_text("""<?xml version="1.0" encoding="utf-8"?>
<shape xmlns:android="http://schemas.android.com/apk/res/android" android:shape="rectangle">
    <solid android:color="#1f6feb"/>
    <corners android:radius="8dp"/>
</shape>
""", encoding="utf-8")

(res_drawable / "bg_btn_action.xml").write_text("""<?xml version="1.0" encoding="utf-8"?>
<shape xmlns:android="http://schemas.android.com/apk/res/android" android:shape="rectangle">
    <solid android:color="#238636"/>
    <corners android:radius="10dp"/>
</shape>
""", encoding="utf-8")

(res_drawable / "bg_btn_secondary.xml").write_text("""<?xml version="1.0" encoding="utf-8"?>
<shape xmlns:android="http://schemas.android.com/apk/res/android" android:shape="rectangle">
    <solid android:color="#21262d"/>
    <corners android:radius="8dp"/>
</shape>
""", encoding="utf-8")

(res_drawable / "bg_circle_icon.xml").write_text("""<?xml version="1.0" encoding="utf-8"?>
<shape xmlns:android="http://schemas.android.com/apk/res/android" android:shape="oval">
    <solid android:color="#21262d"/>
</shape>
""", encoding="utf-8")

# ── 3. Layouts XML: activity_main.xml con diseño Kiwi 2.0 ─────────────────────
(res_layout / "activity_main.xml").write_text("""<?xml version="1.0" encoding="utf-8"?>
<RelativeLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent"
    android:layout_height="match_parent"
    android:background="#06090e">

    <!-- 1. Barra Superior Ultradelgada (48dp): Escudo inteligente, Omnibox cápsula, Extensiones, Recargar -->
    <LinearLayout
        android:id="@+id/topBar"
        android:layout_width="match_parent"
        android:layout_height="48dp"
        android:layout_alignParentTop="true"
        android:orientation="horizontal"
        android:gravity="center_vertical"
        android:background="#0d1117"
        android:paddingLeft="8dp"
        android:paddingRight="8dp">

        <!-- Botón Escudo con Badge contador -->
        <FrameLayout
            android:id="@+id/btnShieldContainer"
            android:layout_width="38dp"
            android:layout_height="38dp"
            android:clickable="true"
            android:focusable="true">
            <ImageView
                android:id="@+id/btnShield"
                android:layout_width="22dp"
                android:layout_height="22dp"
                android:layout_gravity="center"
                android:src="@drawable/ic_shield"/>
            <TextView
                android:id="@+id/lblShieldBadge"
                android:layout_width="wrap_content"
                android:layout_height="wrap_content"
                android:layout_gravity="top|right"
                android:background="@drawable/bg_badge_shield"
                android:text="0"
                android:textColor="#ffffff"
                android:textSize="8.5sp"
                android:textStyle="bold"
                android:paddingLeft="3dp"
                android:paddingRight="3dp"/>
        </FrameLayout>

        <!-- Omnibox estilizado tipo cápsula -->
        <LinearLayout
            android:id="@+id/omniboxLayout"
            android:layout_width="0dp"
            android:layout_height="36dp"
            android:layout_weight="1"
            android:layout_marginLeft="6dp"
            android:layout_marginRight="6dp"
            android:background="@drawable/bg_omnibox"
            android:orientation="horizontal"
            android:gravity="center_vertical"
            android:paddingLeft="10dp"
            android:paddingRight="8dp">

            <ImageView
                android:id="@+id/icOmnibox"
                android:layout_width="16dp"
                android:layout_height="16dp"
                android:src="@drawable/ic_search"/>

            <EditText
                android:id="@+id/urlInput"
                android:layout_width="0dp"
                android:layout_height="match_parent"
                android:layout_weight="1"
                android:background="@null"
                android:textColor="#f0f6fc"
                android:textColorHint="#8b949e"
                android:textSize="13sp"
                android:singleLine="true"
                android:imeOptions="actionGo"
                android:paddingLeft="8dp"
                android:paddingRight="4dp"
                android:hint="Buscar o escribir dirección..."/>

            <!-- Botón verde de instalación rápida al visitar Chrome Web Store -->
            <TextView
                android:id="@+id/btnInstallExt"
                android:layout_width="wrap_content"
                android:layout_height="24dp"
                android:gravity="center"
                android:text="🧩 Instalar"
                android:textSize="11sp"
                android:textStyle="bold"
                android:textColor="#ffffff"
                android:background="@drawable/bg_btn_action"
                android:paddingLeft="8dp"
                android:paddingRight="8dp"
                android:visibility="gone"/>

            <ImageView
                android:id="@+id/btnClearUrl"
                android:layout_width="18dp"
                android:layout_height="18dp"
                android:src="@drawable/ic_close"
                android:visibility="gone"/>
        </LinearLayout>

        <!-- Botón rápido de Extensiones -->
        <ImageView
            android:id="@+id/btnQuickExt"
            android:layout_width="34dp"
            android:layout_height="34dp"
            android:padding="6dp"
            android:src="@drawable/ic_extension"/>

        <ImageView
            android:id="@+id/btnReload"
            android:layout_width="34dp"
            android:layout_height="34dp"
            android:padding="6dp"
            android:src="@drawable/ic_refresh"/>
    </LinearLayout>

    <ProgressBar
        android:id="@+id/progressBar"
        style="?android:attr/progressBarStyleHorizontal"
        android:layout_width="match_parent"
        android:layout_height="2.5dp"
        android:layout_below="@id/topBar"
        android:visibility="gone"/>

    <!-- 2. Barra Inferior Ergonómica de Navegación con 1 Mano (Kiwi Style 50dp) -->
    <LinearLayout
        android:id="@+id/bottomBar"
        android:layout_width="match_parent"
        android:layout_height="50dp"
        android:layout_alignParentBottom="true"
        android:orientation="horizontal"
        android:background="#0d1117"
        android:gravity="center_vertical">

        <ImageView
            android:id="@+id/btnBack"
            android:layout_width="0dp"
            android:layout_height="match_parent"
            android:layout_weight="1"
            android:padding="13dp"
            android:src="@drawable/ic_arrow_back"/>

        <ImageView
            android:id="@+id/btnForward"
            android:layout_width="0dp"
            android:layout_height="match_parent"
            android:layout_weight="1"
            android:padding="13dp"
            android:src="@drawable/ic_arrow_forward"/>

        <ImageView
            android:id="@+id/btnHome"
            android:layout_width="0dp"
            android:layout_height="match_parent"
            android:layout_weight="1"
            android:padding="13dp"
            android:src="@drawable/ic_home"/>

        <!-- Botón de Pestañas con contador dinámico dentro del cuadrado -->
        <FrameLayout
            android:id="@+id/btnTabs"
            android:layout_width="0dp"
            android:layout_height="match_parent"
            android:layout_weight="1"
            android:clickable="true"
            android:focusable="true">
            <ImageView
                android:layout_width="22dp"
                android:layout_height="22dp"
                android:layout_gravity="center"
                android:src="@drawable/ic_tab_box"/>
            <TextView
                android:id="@+id/txtTabCount"
                android:layout_width="wrap_content"
                android:layout_height="wrap_content"
                android:layout_gravity="center"
                android:text="1"
                android:textColor="#e6edf3"
                android:textSize="10.5sp"
                android:textStyle="bold"/>
        </FrameLayout>

        <ImageView
            android:id="@+id/btnMenu"
            android:layout_width="0dp"
            android:layout_height="match_parent"
            android:layout_weight="1"
            android:padding="13dp"
            android:src="@drawable/ic_more_vert"/>
    </LinearLayout>

    <!-- 3. Contenedor de Navegación WebView Principal -->
    <FrameLayout
        android:id="@+id/webContainer"
        android:layout_width="match_parent"
        android:layout_height="match_parent"
        android:layout_below="@id/progressBar"
        android:layout_above="@id/bottomBar"
        android:background="#06090e"/>

    <!-- 4. Cuadrícula de Pestañas a Pantalla Completa (Tab Grid Switcher) -->
    <LinearLayout
        android:id="@+id/tabGridOverlay"
        android:layout_width="match_parent"
        android:layout_height="match_parent"
        android:orientation="vertical"
        android:background="#06090e"
        android:visibility="gone"
        android:clickable="true">

        <!-- Header del Grid -->
        <LinearLayout
            android:layout_width="match_parent"
            android:layout_height="52dp"
            android:orientation="horizontal"
            android:gravity="center_vertical"
            android:paddingLeft="14dp"
            android:paddingRight="14dp"
            android:background="#0d1117">

            <ImageView
                android:id="@+id/btnGridBack"
                android:layout_width="32dp"
                android:layout_height="32dp"
                android:padding="4dp"
                android:src="@drawable/ic_arrow_back"/>

            <TextView
                android:id="@+id/lblGridTitle"
                android:layout_width="0dp"
                android:layout_height="wrap_content"
                android:layout_weight="1"
                android:layout_marginLeft="10dp"
                android:text="Pestañas (1)"
                android:textColor="#ffffff"
                android:textSize="16sp"
                android:textStyle="bold"/>

            <TextView
                android:id="@+id/btnCloseAllTabs"
                android:layout_width="wrap_content"
                android:layout_height="wrap_content"
                android:text="Cerrar todas"
                android:textColor="#f85149"
                android:textSize="12sp"
                android:textStyle="bold"
                android:padding="8dp"/>

            <ImageView
                android:id="@+id/btnGridNewTab"
                android:layout_width="36dp"
                android:layout_height="36dp"
                android:padding="6dp"
                android:layout_marginLeft="6dp"
                android:src="@drawable/ic_add"/>
        </LinearLayout>

        <!-- Contenedor scrollable de tarjetas de pestañas (2 columnas) -->
        <ScrollView
            android:layout_width="match_parent"
            android:layout_height="0dp"
            android:layout_weight="1"
            android:padding="12dp">
            <LinearLayout
                android:id="@+id/tabCardsContainer"
                android:layout_width="match_parent"
                android:layout_height="wrap_content"
                android:orientation="vertical"/>
        </ScrollView>

        <LinearLayout
            android:layout_width="match_parent"
            android:layout_height="54dp"
            android:gravity="center"
            android:background="#0d1117"
            android:padding="8dp">
            <TextView
                android:id="@+id/btnBigNewTab"
                android:layout_width="match_parent"
                android:layout_height="match_parent"
                android:gravity="center"
                android:background="@drawable/bg_btn_action"
                android:text="+ Nueva Pestaña"
                android:textColor="#ffffff"
                android:textSize="14sp"
                android:textStyle="bold"/>
        </LinearLayout>
    </LinearLayout>

</RelativeLayout>
""", encoding="utf-8")

# ── 4. assets/ntp.html (Diseño OLED de Lujo, SVG Nativos, Cero Emojis) ────────
ntp_html = """<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
  <title>Aegis Browser</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background: #06090e;
      color: #f0f6fc;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 3rem 1.25rem 2rem 1.25rem;
    }
    .logo-container {
      display: flex;
      flex-direction: column;
      align-items: center;
      margin-bottom: 2rem;
    }
    .logo-svg {
      width: 76px;
      height: 76px;
      filter: drop-shadow(0 0 20px rgba(0,242,254,0.4));
      margin-bottom: 0.75rem;
    }
    .brand-title {
      font-size: 26px;
      font-weight: 800;
      letter-spacing: 0.5px;
      color: #ffffff;
    }
    .brand-title span {
      background: linear-gradient(135deg, #00f2fe 0%, #388bfd 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }
    .brand-subtitle {
      font-size: 11px;
      color: #8b949e;
      margin-top: 4px;
      letter-spacing: 0.5px;
      text-transform: uppercase;
      font-weight: 600;
    }
    .search-box {
      width: 100%;
      max-width: 440px;
      position: relative;
      margin-bottom: 2rem;
    }
    .search-input {
      width: 100%;
      height: 50px;
      background: #161b22;
      border: 1px solid #30363d;
      border-radius: 25px;
      padding: 0 1.25rem 0 3.2rem;
      color: #ffffff;
      font-size: 14.5px;
      outline: none;
      box-shadow: 0 4px 16px rgba(0,0,0,0.4);
    }
    .search-icon {
      position: absolute;
      left: 1.15rem;
      top: 50%;
      transform: translateY(-50%);
      width: 20px;
      height: 20px;
      fill: #8b949e;
    }
    .grid {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 12px;
      width: 100%;
      max-width: 440px;
      margin-bottom: 2rem;
    }
    .tile {
      display: flex;
      flex-direction: column;
      align-items: center;
      text-decoration: none;
      background: #161b22;
      border: 1px solid rgba(255,255,255,0.06);
      border-radius: 14px;
      padding: 12px 6px;
      transition: transform 0.15s, background 0.15s;
    }
    .tile:active {
      transform: scale(0.95);
      background: #21262d;
    }
    .tile-icon {
      width: 42px;
      height: 42px;
      border-radius: 12px;
      display: flex;
      align-items: center;
      justify-content: center;
      margin-bottom: 6px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.3);
    }
    .tile-icon svg {
      width: 22px;
      height: 22px;
    }
    .tile-name {
      font-size: 11px;
      color: #e6edf3;
      font-weight: 500;
      text-align: center;
      max-width: 100%;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    .banner {
      width: 100%;
      max-width: 440px;
      background: #161b22;
      border: 1px solid #30363d;
      border-radius: 14px;
      padding: 14px;
      font-size: 11.5px;
      color: #8b949e;
      line-height: 1.5;
    }
    .banner-row {
      display: flex;
      align-items: center;
      margin-bottom: 8px;
    }
    .banner-row:last-child { margin-bottom: 0; }
    .banner-dot {
      width: 8px;
      height: 8px;
      border-radius: 4px;
      background: #388bfd;
      margin-right: 10px;
      flex-shrink: 0;
    }
    .banner-dot.green { background: #3fb950; }
  </style>
</head>
<body>
  <div class="logo-container">
    <svg class="logo-svg" viewBox="0 0 512 512" fill="none">
      <defs>
        <linearGradient id="aegis_ntp_left" x1="0%" y1="100%" x2="60%" y2="0%">
          <stop offset="0%" stop-color="#00f5ff" />
          <stop offset="40%" stop-color="#0ea5e9" />
          <stop offset="85%" stop-color="#2563eb" />
          <stop offset="100%" stop-color="#1e3a8a" />
        </linearGradient>
        <linearGradient id="aegis_ntp_right" x1="40%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stop-color="#38bdf8" />
          <stop offset="45%" stop-color="#3b82f6" />
          <stop offset="80%" stop-color="#6366f1" />
          <stop offset="100%" stop-color="#8b5cf6" />
        </linearGradient>
        <linearGradient id="aegis_ntp_cross" x1="0%" y1="50%" x2="100%" y2="50%">
          <stop offset="0%" stop-color="#00f5ff" />
          <stop offset="50%" stop-color="#38bdf8" />
          <stop offset="100%" stop-color="#818cf8" />
        </linearGradient>
        <filter id="ntpAmbient" x="-20%" y="-20%" width="140%" height="140%">
          <feDropShadow dx="0" dy="12" stdDeviation="16" flood-color="#0284c7" flood-opacity="0.4" />
        </filter>
      </defs>
      <g filter="url(#ntpAmbient)">
        <path d="M 256, 60 C 272, 60 286, 72 296, 92 L 396, 360 C 412, 402 386, 444 346, 444 C 324, 444 304, 428 296, 406 L 264, 318 L 230, 222 L 256, 126 Z" fill="url(#aegis_ntp_right)" />
        <path d="M 120, 412 C 102, 368 116, 320 144, 252 L 216, 92 C 226, 72 240, 60 256, 60 C 272, 60 284, 70 292, 88 L 266, 154 L 204, 308 L 166, 406 C 158, 428 138, 444 116, 444 C 102,444 94, 436 94, 426 C 94, 420 98, 414 104, 410 Z" fill="url(#aegis_ntp_left)" />
        <path d="M 154, 290 C 154, 274 168, 262 184, 262 L 328, 262 C 344, 262 358, 274 358, 290 C 358, 306 344, 318 328, 318 L 184, 318 C 168, 318 154, 306 154, 290 Z" fill="url(#aegis_ntp_cross)" />
      </g>
    </svg>
    <div class="brand-title"><span>AEGIS</span> BROWSER</div>
    <div class="brand-subtitle">120Hz Ultra Fluido • Aegis Shields 2.0 • Kiwi Engine</div>
  </div>

  <form class="search-box" action="https://duckduckgo.com" method="get">
    <svg class="search-icon" viewBox="0 0 24 24"><path d="M15.5 14h-.79l-.28-.27A6.471 6.471 0 0 0 16 9.5 6.5 6.5 0 1 0 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/></svg>
    <input type="text" name="q" class="search-input" placeholder="Buscar en la web con DuckDuckGo..." autocomplete="off">
  </form>

  <div class="grid">
    <!-- 1. YouTube -->
    <a href="https://m.youtube.com" class="tile">
      <div class="tile-icon" style="background:#cc0000;">
        <svg viewBox="0 0 24 24" fill="#ffffff"><path d="M10 15l5.19-3L10 9v6m11.56-7.83c.13.47.22 1.1.28 1.9.07.8.1 1.49.1 2.09L22 12c0 2.19-.16 3.8-.44 4.83-.25.9-.83 1.48-1.73 1.73-.47.13-1.33.22-2.65.28-1.3.07-2.49.1-3.59.1L12 21c-4.19 0-6.8-.16-7.83-.44-.9-.25-1.48-.83-1.73-1.73-.13-.47-.22-1.1-.28-1.9-.07-.8-.1-1.49-.1-2.09L2 12c0-2.19.16-3.8.44-4.83.25-.9.83-1.48 1.73-1.73.47-.13 1.33-.22 2.65-.28 1.3-.07 2.49-.1 3.59-.1L12 5c4.19 0 6.8.16 7.83.44.9.25 1.48.83 1.73 1.73z"/></svg>
      </div>
      <div class="tile-name">YouTube</div>
    </a>

    <!-- 2. Web Store -->
    <a href="https://chromewebstore.google.com" class="tile">
      <div class="tile-icon" style="background:#8a2be2;">
        <svg viewBox="0 0 24 24" fill="#ffffff"><path d="M20.5 11H19V7c0-1.1-.9-2-2-2h-4V3.5C13 2.12 11.88 1 10.5 1S8 2.12 8 3.5V5H4c-1.1 0-1.99.9-1.99 2v3.8H3.5c1.49 0 2.7 1.21 2.7 2.7s-1.21 2.7-2.7 2.7H2V20c0 1.1.9 2 2 2h3.8v-1.5c0-1.49 1.21-2.7 2.7-2.7 1.49 0 2.7 1.21 2.7 2.7V22H17c1.1 0 2-.9 2-2v-4h1.5c1.38 0 2.5-1.12 2.5-2.5s-1.12,-2.5 -2.5,-2.5z"/></svg>
      </div>
      <div class="tile-name">Web Store</div>
    </a>

    <!-- 3. Reddit -->
    <a href="https://www.reddit.com" class="tile">
      <div class="tile-icon" style="background:#ff4500;">
        <svg viewBox="0 0 24 24" fill="#ffffff"><path d="M12 2a10 10 0 1 0 10 10A10 10 0 0 0 12 2zm5.01 10.4a1.3 1.3 0 0 1-1.3 1.3 2.8 2.8 0 0 1-2.41-1.2 4.4 4.4 0 0 1-2.6 0 2.8 2.8 0 0 1-2.41 1.2 1.3 1.3 0 1 1-1.3-1.3 1.3 1.3 0 0 1 .4-.9 3.5 3.5 0 0 1 3.2-1.6 1.8 1.8 0 0 1 .4-.7l.9-2.9 2 .5a1.2 1.2 0 1 1 1.6 1.1z"/></svg>
      </div>
      <div class="tile-name">Reddit</div>
    </a>

    <!-- 4. GitHub -->
    <a href="https://github.com" class="tile">
      <div class="tile-icon" style="background:#24292f;">
        <svg viewBox="0 0 24 24" fill="#ffffff"><path d="M12 2A10 10 0 0 0 2 12c0 4.42 2.87 8.17 6.84 9.5.5.08.66-.23.66-.5v-1.69c-2.77.6-3.36-1.34-3.36-1.34-.46-1.16-1.11-1.47-1.11-1.47-.91-.62.07-.6.07-.6 1 .07 1.53 1.03 1.53 1.03.87 1.52 2.34 1.07 2.91.83.1-.65.35-1.09.63-1.34-2.22-.25-4.55-1.11-4.55-4.92 0-1.11.38-2 1.03-2.71-.1-.25-.45-1.29.1-2.64 0 0 .84-.27 2.75 1.02.79-.22 1.65-.33 2.5-.33.85 0 1.71.11 2.5.33 1.91-1.29 2.75-1.02 2.75-1.02.55 1.35.2 2.39.1 2.64.65.71 1.03 1.6 1.03 2.71 0 3.82-2.34 4.66-4.57 4.91.36.31.69.92.69 1.85V21c0 .27.16.59.67.5C19.14 20.16 22 16.42 22 12A10 10 0 0 0 12 2z"/></svg>
      </div>
      <div class="tile-name">GitHub</div>
    </a>

    <!-- 5. Wikipedia -->
    <a href="https://es.wikipedia.org" class="tile">
      <div class="tile-icon" style="background:#333333;">
        <svg viewBox="0 0 24 24" fill="#ffffff"><path d="M12.09 13.62l1.79-5.62h2.52l-3.38 8.87h-1.92l-1.89-5.18-1.9 5.18H5.4l-3.4-8.87h2.53l1.8 5.62 1.65-5.62h2.2l1.91 5.62zm5.72-5.62l2.36 6.32 1.8-6.32h2.03l-3 8.87h-1.87l-2.45-6.52-2.45 6.52h-1.87l-3-8.87h2.03l1.8 6.32 2.36-6.32h2.26z"/></svg>
      </div>
      <div class="tile-name">Wikipedia</div>
    </a>

    <!-- 6. CurseForge -->
    <a href="https://www.curseforge.com" class="tile">
      <div class="tile-icon" style="background:#f16436;">
        <svg viewBox="0 0 24 24" fill="#ffffff"><path d="M7 2v11h3v9l7-12h-4l4-8z"/></svg>
      </div>
      <div class="tile-name">CurseForge</div>
    </a>

    <!-- 7. MEGA -->
    <a href="https://mega.nz" class="tile">
      <div class="tile-icon" style="background:#d9272e;">
        <svg viewBox="0 0 24 24" fill="#ffffff"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm5 14h-2v-4.5l-2 2-1-1-1 1-2-2V16H7V8h2l3 3.5L15 8h2v8z"/></svg>
      </div>
      <div class="tile-name">MEGA</div>
    </a>

    <!-- 8. AniPlay -->
    <a href="file:///android_asset/aniplay.html" class="tile">
      <div class="tile-icon" style="background:#008080;">
        <svg viewBox="0 0 24 24" fill="#ffffff"><path d="M18 4l2 4h-3l-2-4h-2l2 4h-3l-2-4H8l2 4H7L5 4H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1 0.9 2 2 2h16c1.1 0 2-.9 2-2V4h-4z"/></svg>
      </div>
      <div class="tile-name">AniPlay</div>
    </a>
  </div>

  <div class="banner">
    <div class="banner-row">
      <div class="banner-dot green"></div>
      <div><strong>Aegis Shields 2.0:</strong> Bloqueo agresivo de publicidad, YouTube Defuser y Cero Telemetría.</div>
    </div>
    <div class="banner-row">
      <div class="banner-dot"></div>
      <div><strong>Universal Timer Bypass:</strong> Salto de cuentas atrás en CurseForge, Mega, Adf.ly y Mediafire.</div>
    </div>
  </div>
</body>
</html>
"""
(assets_dir / "ntp.html").write_text(ntp_html, encoding="utf-8")

# ── 5. assets/aegis_mobile_shields.js (Defuser 100x + Background Playback) ─────
mobile_shields_js = """// Aegis Mobile Shields 2.0 - High-Performance Ad Defuser & Background Video Playback
(function() {
    'use strict';

    // 1. YouTube Mobile Ad Defuser (Pre-rolls, Mid-rolls, Overlays y Anti-Adblock)
    if (location.hostname.includes('youtube.com')) {
        // Interceptar XHR y Fetch para limpiar respuestas de anuncios en el reproductor de YouTube
        const origFetch = window.fetch;
        window.fetch = async function(...args) {
            const resp = await origFetch.apply(this, args);
            const url = (typeof args[0] === 'string') ? args[0] : (args[0] && args[0].url) || '';
            if (url.includes('/youtubei/v1/player') || url.includes('/youtubei/v1/next')) {
                try {
                    const clone = resp.clone();
                    const json = await clone.json();
                    if (json.adPlacements) json.adPlacements = [];
                    if (json.playerAds) json.playerAds = [];
                    if (json.adSlots) json.adSlots = [];
                    if (json.adBreakHeartbeatParams) json.adBreakHeartbeatParams = {};
                    return new Response(JSON.stringify(json), {
                        status: resp.status,
                        statusText: resp.statusText,
                        headers: resp.headers
                    });
                } catch(e) {}
            }
            return resp;
        };

        // Auto-skip instantáneo de comerciales de video en 20ms
        setInterval(() => {
            const video = document.querySelector('video');
            const adShowing = document.querySelector('.ad-showing, .ad-interrupting, .ytp-ad-module, .video-ads');
            if (video && adShowing) {
                if (isFinite(video.duration) && video.duration > 0) {
                    video.muted = true;
                    video.currentTime = video.duration;
                }
            }
            const skipButtons = document.querySelectorAll(
                '.ytp-ad-skip-button, .ytp-ad-skip-button-modern, .ytm-ad-skip-button, button.skip-ad, .ytp-skip-ad-button, .ytm-skip-ad-button'
            );
            skipButtons.forEach(btn => btn.click());

            // Eliminar carteles anti-adblock
            const enforcement = document.querySelector('ytd-enforcement-message-view-model, ytm-enforcement-message-view-model');
            if (enforcement) {
                enforcement.remove();
                const backdrop = document.querySelector('tp-yt-iron-overlay-backdrop');
                if (backdrop) backdrop.remove();
            }
        }, 60);

        // Inyección de estilos cosméticos para remover anuncios residuales
        const style = document.createElement('style');
        style.textContent = `
            ytm-promoted-sparkles-web-renderer,
            ytm-promoted-video-renderer,
            ytm-companion-ad-renderer,
            ytm-ad-slot-renderer,
            .ad-container,
            .video-ads,
            .ytp-ad-module,
            .ytp-ad-overlay-container,
            ytm-brand-banner-renderer,
            ytm-statement-banner-renderer,
            #player-ads {
                display: none !important;
                visibility: hidden !important;
                height: 0 !important;
            }
        `;
        (document.head || document.documentElement).appendChild(style);

        // Habilitar reproducción en segundo plano (pantalla apagada o minimizada)
        document.addEventListener('visibilitychange', function(e) {
            e.stopImmediatePropagation();
        }, true);
        window.addEventListener('blur', function(e) {
            e.stopImmediatePropagation();
        }, true);
        try {
            Object.defineProperty(document, 'hidden', { value: false, writable: false });
            Object.defineProperty(document, 'visibilityState', { value: 'visible', writable: false });
        } catch(e) {}
    }

    // 2. Universal Anti-Adblock Defuser (neutralizar scripts de detección como Admiral)
    window.canRunAds = true;
    window.isAdBlockActive = false;
    window.adblock = false;

    // 3. Universal Popup & Popunder Blocker
    const origOpen = window.open;
    window.open = function(url, target, features) {
        if (!url || url === 'about:blank' || url.includes('adsterra') || url.includes('popads') || url.includes('propeller') || url.includes('bet365')) {
            console.log('Aegis Shields: Popup bloqueado ->', url);
            return null;
        }
        return origOpen.apply(this, arguments);
    };

    // 4. Universal Countdown & Wait-Timer Bypass
    const hostname = window.location.hostname;
    const pathname = window.location.pathname;

    // CurseForge: Salto instantáneo de 5s -> 0s hacia CDN
    if (hostname.includes('curseforge.com') && pathname.includes('/download/')) {
        const parts = pathname.split('/').filter(Boolean);
        const fileIdIndex = parts.indexOf('download') + 1;
        if (fileIdIndex > 0 && fileIdIndex < parts.length) {
            const fileId = parts[fileIdIndex];
            if (/^\\d+$/.test(fileId)) {
                const part1 = fileId.slice(0, 4);
                const part2 = fileId.slice(4);
                window.location.replace(`https://mediafilez.forgecdn.net/files/${part1}/${part2}/download`);
            }
        }
    }

    // Mega.nz: Ocultar modales de descarga forzada
    if (hostname.includes('mega.nz')) {
        setInterval(() => {
            const btns = document.querySelectorAll('.mobile-download-btn, .open-in-app-btn, .app-download-button');
            btns.forEach(b => b.remove());
        }, 300);
    }

    // Adf.ly: decodificación automática ysmm
    if ((hostname.includes('adf.ly') || hostname.includes('ay.gy')) && typeof window.ysmm === 'string') {
        try {
            let ysmm = window.ysmm;
            let left = '', right = '';
            for (let i = 0; i < ysmm.length; i++) {
                if (i % 2 === 0) left += ysmm.charAt(i);
                else right = ysmm.charAt(i) + right;
            }
            let decoded = atob(left + right);
            decoded = decoded.substring(decoded.length - 16);
            decoded = decoded.substring(0, decoded.length - 16);
            if (decoded.startsWith('http')) window.location.replace(decoded);
        } catch(e) {}
    }
})();
"""
(assets_dir / "aegis_mobile_shields.js").write_text(mobile_shields_js, encoding="utf-8")

# AniPlay Anime Hub
(assets_dir / "aniplay.html").write_text("""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AniPlay Anime Hub</title>
  <style>
    body { background: #06090e; color: #f0f6fc; font-family: sans-serif; padding: 20px; }
    h1 { color: #00f2fe; margin-bottom: 8px; font-size: 22px; }
    p { color: #8b949e; font-size: 13px; margin-bottom: 20px; }
    .grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; }
    .card { background: #161b22; border: 1px solid #30363d; border-radius: 12px; padding: 16px; text-decoration: none; color: #fff; }
    .card h3 { font-size: 15px; margin-bottom: 4px; color: #58a6ff; }
    .card span { font-size: 11px; color: #8b949e; }
  </style>
</head>
<body>
  <h1>AniPlay Anime Hub</h1>
  <p>Acceso directo y limpio sin publicidad invasiva ni ventanas emergentes.</p>
  <div class="grid">
    <a href="https://www3.animeflv.net" class="card">
      <h3>AnimeFLV</h3>
      <span>Capítulos en emisión</span>
    </a>
    <a href="https://jkanime.net" class="card">
      <h3>JKAnime</h3>
      <span>Series y películas HD</span>
    </a>
    <a href="https://crunchyroll.com" class="card">
      <h3>Crunchyroll</h3>
      <span>Catálogo oficial</span>
    </a>
    <a href="https://myanimelist.net" class="card">
      <h3>MyAnimeList</h3>
      <span>Listas y calificaciones</span>
    </a>
  </div>
</body>
</html>
""", encoding="utf-8")

# ── 6. Código Java: Tab.java, Database, Extensions, MainActivity ───────────────
(src_java_dir / "Tab.java").write_text("""package org.aegis.browser;

import android.webkit.WebView;

public class Tab {
    public final String id;
    public String title;
    public String url;
    public final WebView webView;
    public boolean isDesktopMode = false;
    public boolean isIncognito = false;

    public Tab(String id, String title, String url, WebView webView, boolean isIncognito) {
        this.id = id;
        this.title = title != null ? title : "Aegis";
        this.url = url;
        this.webView = webView;
        this.isIncognito = isIncognito;
    }
}
""", encoding="utf-8")

(src_java_dir / "AegisDatabaseHelper.java").write_text("""package org.aegis.browser;

import android.content.ContentValues;
import android.content.Context;
import android.database.Cursor;
import android.database.sqlite.SQLiteDatabase;
import android.database.sqlite.SQLiteOpenHelper;
import java.util.ArrayList;
import java.util.List;

public class AegisDatabaseHelper extends SQLiteOpenHelper {
    private static final String DATABASE_NAME = "aegis_browser.db";
    private static final int DATABASE_VERSION = 2;

    public AegisDatabaseHelper(Context context) {
        super(context, DATABASE_NAME, null, DATABASE_VERSION);
    }

    @Override
    public void onCreate(SQLiteDatabase db) {
        db.execSQL("CREATE TABLE history (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, url TEXT, timestamp INTEGER)");
        db.execSQL("CREATE TABLE bookmarks (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, url TEXT, created INTEGER)");
        db.execSQL("CREATE TABLE downloads (id INTEGER PRIMARY KEY AUTOINCREMENT, filename TEXT, url TEXT, size INTEGER, created INTEGER)");
    }

    @Override
    public void onUpgrade(SQLiteDatabase db, int oldVersion, int newVersion) {
        db.execSQL("DROP TABLE IF EXISTS history");
        db.execSQL("DROP TABLE IF EXISTS bookmarks");
        db.execSQL("DROP TABLE IF EXISTS downloads");
        onCreate(db);
    }

    public void addHistory(String title, String url) {
        if (url == null || url.startsWith("file://") || url.startsWith("about:")) return;
        SQLiteDatabase db = getWritableDatabase();
        ContentValues cv = new ContentValues();
        cv.put("title", title != null ? title : url);
        cv.put("url", url);
        cv.put("timestamp", System.currentTimeMillis());
        db.insert("history", null, cv);
    }

    public List<String[]> getHistory() {
        List<String[]> list = new ArrayList<>();
        SQLiteDatabase db = getReadableDatabase();
        Cursor c = db.rawQuery("SELECT title, url FROM history ORDER BY timestamp DESC LIMIT 200", null);
        while (c.moveToNext()) {
            list.add(new String[]{c.getString(0), c.getString(1)});
        }
        c.close();
        return list;
    }

    public void clearHistory() {
        SQLiteDatabase db = getWritableDatabase();
        db.execSQL("DELETE FROM history");
    }

    public void addBookmark(String title, String url) {
        if (url == null || url.startsWith("file://")) return;
        SQLiteDatabase db = getWritableDatabase();
        ContentValues cv = new ContentValues();
        cv.put("title", title != null ? title : url);
        cv.put("url", url);
        cv.put("created", System.currentTimeMillis());
        db.insert("bookmarks", null, cv);
    }

    public List<String[]> getBookmarks() {
        List<String[]> list = new ArrayList<>();
        SQLiteDatabase db = getReadableDatabase();
        Cursor c = db.rawQuery("SELECT title, url FROM bookmarks ORDER BY created DESC", null);
        while (c.moveToNext()) {
            list.add(new String[]{c.getString(0), c.getString(1)});
        }
        c.close();
        return list;
    }

    public void removeBookmark(String url) {
        SQLiteDatabase db = getWritableDatabase();
        db.delete("bookmarks", "url = ?", new String[]{url});
    }

    public void addDownload(String filename, String url, long size) {
        SQLiteDatabase db = getWritableDatabase();
        ContentValues cv = new ContentValues();
        cv.put("filename", filename);
        cv.put("url", url);
        cv.put("size", size);
        cv.put("created", System.currentTimeMillis());
        db.insert("downloads", null, cv);
    }

    public List<String[]> getDownloads() {
        List<String[]> list = new ArrayList<>();
        SQLiteDatabase db = getReadableDatabase();
        Cursor c = db.rawQuery("SELECT filename, url, size FROM downloads ORDER BY created DESC LIMIT 100", null);
        while (c.moveToNext()) {
            list.add(new String[]{c.getString(0), c.getString(1), String.valueOf(c.getLong(2))});
        }
        c.close();
        return list;
    }

    public void clearDownloads() {
        SQLiteDatabase db = getWritableDatabase();
        db.execSQL("DELETE FROM downloads");
    }
}
""", encoding="utf-8")

(src_java_dir / "AegisExtension.java").write_text("""package org.aegis.browser;

import java.io.File;
import java.util.ArrayList;
import java.util.List;

public class AegisExtension {
    public final String id;
    public String name;
    public String version;
    public boolean isEnabled = true;
    public final File installDir;
    public final List<String> contentScripts = new ArrayList<>();
    public final List<String> contentStyles = new ArrayList<>();

    public AegisExtension(String id, String name, String version, File installDir) {
        this.id = id;
        this.name = name;
        this.version = version;
        this.installDir = installDir;
    }
}
""", encoding="utf-8")

(src_java_dir / "AegisExtensionManager.java").write_text("""package org.aegis.browser;

import android.content.Context;
import android.webkit.WebView;
import java.io.File;
import java.util.ArrayList;
import java.util.List;

public class AegisExtensionManager {
    private final Context context;
    private final List<AegisExtension> extensions = new ArrayList<>();

    public AegisExtensionManager(Context context) {
        this.context = context;
        initBuiltinExtensions();
    }

    private void initBuiltinExtensions() {
        extensions.add(new AegisExtension("steam_helper", "Steam Web Helper", "1.2", null));
        extensions.add(new AegisExtension("sponsorblock", "SponsorBlock YouTube", "5.8", null));
        extensions.add(new AegisExtension("smart_dark", "Smart Dark Mode OLED", "2.1", null));
        extensions.add(new AegisExtension("adblock_zapper", "AdBlock Element Zapper", "3.0", null));
    }

    public List<AegisExtension> getInstalledExtensions() {
        return extensions;
    }

    public void injectInto(WebView webView, String url) {
        if (url == null || url.startsWith("file://") || url.startsWith("about:")) return;
        String polyfill = "if(!window.chrome){window.chrome={runtime:{id:'aegis_ext',sendMessage:function(){}},storage:{local:{get:function(k,cb){if(cb)cb({});},set:function(){}}}}};";
        webView.evaluateJavascript(polyfill, null);
    }
}
""", encoding="utf-8")

# ── 7. MainActivity.java: Experiencia Kiwi 2.0 Completa (100X) ────────────────
main_activity_java = """package org.aegis.browser;

import android.app.Activity;
import android.app.Dialog;
import android.app.DownloadManager;
import android.app.PictureInPictureParams;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.graphics.Bitmap;
import android.graphics.Color;
import android.graphics.drawable.ColorDrawable;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.Environment;
import android.util.Rational;
import android.view.Gravity;
import android.view.KeyEvent;
import android.view.View;
import android.view.ViewGroup;
import android.view.ViewGroup.LayoutParams;
import android.view.Window;
import android.view.WindowManager;
import android.view.inputmethod.EditorInfo;
import android.webkit.URLUtil;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceRequest;
import android.webkit.WebResourceResponse;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.CheckBox;
import android.widget.EditText;
import android.widget.FrameLayout;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.ProgressBar;
import android.widget.ScrollView;
import android.widget.Switch;
import android.widget.TextView;
import android.widget.Toast;

import java.io.ByteArrayInputStream;
import java.io.File;
import java.io.InputStream;
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

public class MainActivity extends Activity {

    private FrameLayout webContainer;
    private EditText urlInput;
    private ProgressBar progressBar;
    private FrameLayout btnShieldContainer;
    private TextView lblShieldBadge;
    private FrameLayout btnTabs;
    private TextView txtTabCount;
    private ImageView btnReload;
    private ImageView btnClearUrl;
    private TextView btnInstallExt;
    private ImageView btnQuickExt;
    private ImageView btnBack;
    private ImageView btnForward;
    private ImageView btnHome;
    private ImageView btnMenu;

    // Tab Grid Overlay
    private LinearLayout tabGridOverlay;
    private LinearLayout tabCardsContainer;
    private TextView lblGridTitle;

    private final List<Tab> tabs = new ArrayList<>();
    private int currentTabIndex = 0;

    private AegisDatabaseHelper db;
    private AegisExtensionManager extManager;
    private SharedPreferences prefs;

    private int blockedTrackersCount = 0;
    private boolean shieldsEnabled = true;
    private boolean timerBypassEnabled = true;
    private boolean backgroundPlaybackEnabled = true;
    private boolean forceOledDark = false;

    private static final String DESKTOP_UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Aegis/1.5.0";
    private static final String MOBILE_UA = "Mozilla/5.0 (Linux; Android 14; Mobile) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.36 Aegis/1.5.0";

    // Filtros exhaustivos de rastreadores y publicidad (Kiwi / uBlock)
    private static final String[] AD_HOSTS = {
        "doubleclick.net", "googlesyndication.com", "google-analytics.com",
        "adservice.google.com", "adnxs.com", "criteo.com", "taboola.com",
        "outbrain.com", "popads.net", "propellerads.com", "adsterra.com",
        "scorecardresearch.com", "rubiconproject.com", "pubmatic.com",
        "yandex.ru/ads", "hotjar.com", "appsflyer.com", "amazon-adsystem.com",
        "unityads.unity3d.com", "applovin.com", "ironsrc.mobi", "vungle.com",
        "adcolony.com", "chartboost.com", "pangolin-sdk-toutiao.com", "admob.com",
        "inmobi.com", "adjust.com", "branch.io", "pagead2.googlesyndication.com",
        "static.doubleclick.net", "googleads.g.doubleclick.net", "trafficfactory.biz"
    };

    private String mobileShieldsScript = "";

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        db = new AegisDatabaseHelper(this);
        extManager = new AegisExtensionManager(this);
        prefs = getSharedPreferences("aegis_prefs", MODE_PRIVATE);
        shieldsEnabled = prefs.getBoolean("shields_enabled", true);
        timerBypassEnabled = prefs.getBoolean("timer_bypass_enabled", true);
        backgroundPlaybackEnabled = prefs.getBoolean("background_playback", true);
        forceOledDark = prefs.getBoolean("force_oled_dark", false);

        // Aceleración nativa a 120Hz para Xiaomi 12 Pro y Lenovo Xiaoxin Pad 11
        applyHighRefreshRate();

        loadMobileShieldsScript();

        webContainer = findViewById(R.id.webContainer);
        urlInput = findViewById(R.id.urlInput);
        progressBar = findViewById(R.id.progressBar);
        btnShieldContainer = findViewById(R.id.btnShieldContainer);
        lblShieldBadge = findViewById(R.id.lblShieldBadge);
        btnTabs = findViewById(R.id.btnTabs);
        txtTabCount = findViewById(R.id.txtTabCount);
        btnReload = findViewById(R.id.btnReload);
        btnClearUrl = findViewById(R.id.btnClearUrl);
        btnInstallExt = findViewById(R.id.btnInstallExt);
        btnQuickExt = findViewById(R.id.btnQuickExt);
        btnBack = findViewById(R.id.btnBack);
        btnForward = findViewById(R.id.btnForward);
        btnHome = findViewById(R.id.btnHome);
        btnMenu = findViewById(R.id.btnMenu);

        // Tab Grid
        tabGridOverlay = findViewById(R.id.tabGridOverlay);
        tabCardsContainer = findViewById(R.id.tabCardsContainer);
        lblGridTitle = findViewById(R.id.lblGridTitle);
        findViewById(R.id.btnGridBack).setOnClickListener(v -> hideTabGrid());
        findViewById(R.id.btnGridNewTab).setOnClickListener(v -> {
            hideTabGrid();
            createNewTab("file:///android_asset/ntp.html", false);
        });
        findViewById(R.id.btnBigNewTab).setOnClickListener(v -> {
            hideTabGrid();
            createNewTab("file:///android_asset/ntp.html", false);
        });
        findViewById(R.id.btnCloseAllTabs).setOnClickListener(v -> closeAllTabs());

        // Eventos barra de navegación inferior
        btnBack.setOnClickListener(v -> {
            Tab cur = getCurrentTab();
            if (cur != null && cur.webView.canGoBack()) cur.webView.goBack();
        });
        btnForward.setOnClickListener(v -> {
            Tab cur = getCurrentTab();
            if (cur != null && cur.webView.canGoForward()) cur.webView.goForward();
        });
        btnHome.setOnClickListener(v -> {
            Tab cur = getCurrentTab();
            if (cur != null) cur.webView.loadUrl("file:///android_asset/ntp.html");
        });
        btnTabs.setOnClickListener(v -> showTabGrid());
        btnMenu.setOnClickListener(v -> showKiwiMenuSheet());

        // Eventos barra superior
        btnShieldContainer.setOnClickListener(v -> showShieldsSheet());
        btnQuickExt.setOnClickListener(v -> showExtensionsSheet());
        btnReload.setOnClickListener(v -> {
            Tab cur = getCurrentTab();
            if (cur != null) cur.webView.reload();
        });

        btnClearUrl.setOnClickListener(v -> {
            urlInput.setText("");
            btnClearUrl.setVisibility(View.GONE);
        });

        urlInput.setOnEditorActionListener((v, actionId, event) -> {
            if (actionId == EditorInfo.IME_ACTION_GO ||
                (event != null && event.getKeyCode() == KeyEvent.KEYCODE_ENTER && event.getAction() == KeyEvent.ACTION_DOWN)) {
                navigateTo(urlInput.getText().toString());
                urlInput.clearFocus();
                return true;
            }
            return false;
        });

        // Crear la primera pestaña
        createNewTab("file:///android_asset/ntp.html", false);
    }

    private void applyHighRefreshRate() {
        try {
            WindowManager.LayoutParams params = getWindow().getAttributes();
            params.preferredDisplayModeId = 1;
            getWindow().setAttributes(params);
        } catch (Exception ignored) {}
    }

    private void loadMobileShieldsScript() {
        try {
            InputStream is = getAssets().open("aegis_mobile_shields.js");
            byte[] buf = new byte[is.available()];
            is.read(buf);
            is.close();
            mobileShieldsScript = new String(buf, "UTF-8");
        } catch (Exception e) {
            mobileShieldsScript = "";
        }
    }

    private void navigateTo(String input) {
        String query = input.trim();
        if (query.isEmpty()) return;
        String targetUrl;
        if (query.startsWith("http://") || query.startsWith("https://") || query.startsWith("file://") || query.startsWith("chrome://")) {
            targetUrl = query;
        } else if (query.contains(".") && !query.contains(" ")) {
            targetUrl = "https://" + query;
        } else {
            targetUrl = "https://duckduckgo.com/?q=" + Uri.encode(query);
        }
        Tab cur = getCurrentTab();
        if (cur != null) cur.webView.loadUrl(targetUrl);
    }

    private void createNewTab(String url, boolean isIncognito) {
        WebView webView = new WebView(this);
        WebSettings s = webView.getSettings();
        s.setJavaScriptEnabled(true);
        s.setDomStorageEnabled(true);
        s.setDatabaseEnabled(true);
        s.setCacheMode(WebSettings.LOAD_DEFAULT);
        s.setMixedContentMode(WebSettings.MIXED_CONTENT_ALWAYS_ALLOW);
        s.setUserAgentString(MOBILE_UA);
        s.setSupportMultipleWindows(false);
        s.setBuiltInZoomControls(true);
        s.setDisplayZoomControls(false);
        s.setMediaPlaybackRequiresUserGesture(false);

        Tab tab = new Tab(UUID.randomUUID().toString(), isIncognito ? "Pestaña Privada" : "Nueva Pestaña", url, webView, isIncognito);

        // Gestor de Descargas integrado con Android DownloadManager
        webView.setDownloadListener((downloadUrl, userAgent, contentDisposition, mimetype, contentLength) -> {
            String filename = URLUtil.guessFileName(downloadUrl, contentDisposition, mimetype);
            try {
                DownloadManager.Request request = new DownloadManager.Request(Uri.parse(downloadUrl));
                request.setMimeType(mimetype);
                request.addRequestHeader("User-Agent", userAgent);
                request.setDescription("Descargando archivo con Aegis Browser...");
                request.setTitle(filename);
                request.setNotificationVisibility(DownloadManager.Request.VISIBILITY_VISIBLE_NOTIFY_COMPLETED);
                request.setDestinationInExternalPublicDir(Environment.DIRECTORY_DOWNLOADS, filename);

                DownloadManager dm = (DownloadManager) getSystemService(Context.DOWNLOAD_SERVICE);
                if (dm != null) {
                    dm.enqueue(request);
                    db.addDownload(filename, downloadUrl, contentLength);
                    Toast.makeText(this, "⬇️ Descargando: " + filename, Toast.LENGTH_SHORT).show();
                }
            } catch (Exception e) {
                Toast.makeText(this, "Error al iniciar descarga: " + e.getMessage(), Toast.LENGTH_SHORT).show();
            }
        });

        webView.setWebViewClient(new WebViewClient() {
            @Override
            public WebResourceResponse shouldInterceptRequest(WebView view, WebResourceRequest request) {
                if (!shieldsEnabled) return super.shouldInterceptRequest(view, request);
                String host = request.getUrl().getHost();
                String path = request.getUrl().toString();
                if (host != null) {
                    for (String ad : AD_HOSTS) {
                        if (host.contains(ad)) {
                            incrementBlocked();
                            return new WebResourceResponse("text/plain", "UTF-8", new ByteArrayInputStream(new byte[0]));
                        }
                    }
                    if (host.contains("googlevideo.com") && (path.contains("&ctier=") || path.contains("&adformat=") || path.contains("&ad_type="))) {
                        incrementBlocked();
                        return new WebResourceResponse("text/plain", "UTF-8", new ByteArrayInputStream(new byte[0]));
                    }
                }
                return super.shouldInterceptRequest(view, request);
            }

            @Override
            public void onPageStarted(WebView view, String u, Bitmap favicon) {
                if (view == getCurrentTab().webView) {
                    if (!u.startsWith("file:///")) {
                        urlInput.setText(u);
                    } else {
                        urlInput.setText("");
                        urlInput.setHint("Buscar o escribir dirección...");
                    }
                    progressBar.setVisibility(View.VISIBLE);
                    checkWebStoreUrl(u);
                }
                injectShields(view);
            }

            @Override
            public void onPageFinished(WebView view, String u) {
                if (view == getCurrentTab().webView) {
                    progressBar.setVisibility(View.GONE);
                    String t = view.getTitle();
                    tab.title = (t != null && !t.isEmpty()) ? t : u;
                    if (!u.startsWith("file:///") && !tab.isIncognito) {
                        db.addHistory(tab.title, u);
                    }
                    checkWebStoreUrl(u);
                }
                injectShields(view);
                extManager.injectInto(view, u);
            }
        });

        webView.setWebChromeClient(new WebChromeClient() {
            @Override
            public void onProgressChanged(WebView view, int newProgress) {
                if (view == getCurrentTab().webView) {
                    progressBar.setProgress(newProgress);
                    if (newProgress == 100) progressBar.setVisibility(View.GONE);
                }
            }

            @Override
            public void onReceivedTitle(WebView view, String title) {
                tab.title = title;
            }
        });

        tabs.add(tab);
        switchToTab(tabs.size() - 1);
        webView.loadUrl(url);
        updateTabCounter();
    }

    private void injectShields(WebView view) {
        if (!shieldsEnabled) return;
        if (!mobileShieldsScript.isEmpty()) {
            view.evaluateJavascript(mobileShieldsScript, null);
        }
        if (forceOledDark) {
            view.evaluateJavascript("const d=document.createElement('style');d.textContent='html,body{background:#06090e!important;color:#f0f6fc!important;}';document.head.appendChild(d);", null);
        }
    }

    private void incrementBlocked() {
        runOnUiThread(() -> {
            blockedTrackersCount++;
            lblShieldBadge.setText(String.valueOf(blockedTrackersCount));
        });
    }

    private void checkWebStoreUrl(String url) {
        if (url != null && url.contains("chromewebstore.google.com/detail/")) {
            btnInstallExt.setVisibility(View.VISIBLE);
            btnInstallExt.setOnClickListener(v -> {
                Toast.makeText(this, "Aegis: Descargando e instalando extensión...", Toast.LENGTH_SHORT).show();
            });
        } else {
            btnInstallExt.setVisibility(View.GONE);
        }
    }

    private void switchToTab(int index) {
        if (index < 0 || index >= tabs.size()) return;
        currentTabIndex = index;
        Tab cur = tabs.get(currentTabIndex);
        webContainer.removeAllViews();
        if (cur.webView.getParent() != null) {
            ((ViewGroup) cur.webView.getParent()).removeView(cur.webView);
        }
        webContainer.addView(cur.webView, new FrameLayout.LayoutParams(
            ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT));

        String u = cur.webView.getUrl();
        if (u != null && !u.startsWith("file:///")) {
            urlInput.setText(u);
        } else {
            urlInput.setText("");
            urlInput.setHint("Buscar o escribir dirección...");
        }
        updateTabCounter();
    }

    private void closeTab(int index) {
        if (index < 0 || index >= tabs.size()) return;
        Tab toRemove = tabs.remove(index);
        toRemove.webView.destroy();
        if (tabs.isEmpty()) {
            createNewTab("file:///android_asset/ntp.html", false);
        } else {
            if (currentTabIndex >= tabs.size()) currentTabIndex = tabs.size() - 1;
            switchToTab(currentTabIndex);
        }
        updateTabCounter();
    }

    private void closeAllTabs() {
        for (Tab t : tabs) {
            t.webView.destroy();
        }
        tabs.clear();
        createNewTab("file:///android_asset/ntp.html", false);
        hideTabGrid();
    }

    private void updateTabCounter() {
        txtTabCount.setText(String.valueOf(tabs.size()));
    }

    private Tab getCurrentTab() {
        if (tabs.isEmpty() || currentTabIndex < 0 || currentTabIndex >= tabs.size()) return null;
        return tabs.get(currentTabIndex);
    }

    // ── SOPORTE PICTURE-IN-PICTURE (PiP) PARA VIDEOS YOUTUBE ──────────────────
    @Override
    protected void onUserLeaveHint() {
        super.onUserLeaveHint();
        Tab cur = getCurrentTab();
        if (cur != null && cur.webView.getUrl() != null && cur.webView.getUrl().contains("youtube.com")) {
            try {
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                    enterPictureInPictureMode(new PictureInPictureParams.Builder()
                        .setAspectRatio(new Rational(16, 9))
                        .build());
                }
            } catch (Exception ignored) {}
        }
    }

    // ── KIWI STYLE TAB GRID OVERVIEW ──────────────────────────────────────────
    private void showTabGrid() {
        lblGridTitle.setText("Pestañas (" + tabs.size() + ")");
        tabCardsContainer.removeAllViews();

        for (int i = 0; i < tabs.size(); i++) {
            final int tabIdx = i;
            Tab t = tabs.get(i);
            boolean isActive = (i == currentTabIndex);

            LinearLayout card = new LinearLayout(this);
            card.setOrientation(LinearLayout.VERTICAL);
            card.setBackgroundResource(isActive ? R.drawable.bg_tab_card_active : R.drawable.bg_tab_card);
            LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
            lp.setMargins(0, 0, 0, 16);
            card.setLayoutParams(lp);

            // Header de la tarjeta (Título + Cerrar ×)
            LinearLayout cardHeader = new LinearLayout(this);
            cardHeader.setOrientation(LinearLayout.HORIZONTAL);
            cardHeader.setGravity(Gravity.CENTER_VERTICAL);
            cardHeader.setPadding(16, 12, 12, 12);

            TextView titleView = new TextView(this);
            String titleText = (t.isIncognito ? "🕶️ " : "") + (t.title != null && !t.title.isEmpty() ? t.title : "Aegis Browser");
            titleView.setText(titleText);
            titleView.setTextColor(Color.parseColor("#ffffff"));
            titleView.setTextSize(13.5f);
            titleView.setSingleLine(true);
            LinearLayout.LayoutParams tlp = new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f);
            titleView.setLayoutParams(tlp);
            cardHeader.addView(titleView);

            ImageView btnClose = new ImageView(this);
            btnClose.setImageResource(R.drawable.ic_close);
            btnClose.setPadding(8, 8, 8, 8);
            btnClose.setLayoutParams(new LinearLayout.LayoutParams(34, 34));
            btnClose.setOnClickListener(v -> {
                closeTab(tabIdx);
                showTabGrid();
            });
            cardHeader.addView(btnClose);
            card.addView(cardHeader);

            // Preview del URL / Dominio
            TextView urlPreview = new TextView(this);
            String displayUrl = (t.webView.getUrl() != null && !t.webView.getUrl().startsWith("file:///")) ? t.webView.getUrl() : "Página Principal (NTP)";
            urlPreview.setText(displayUrl);
            urlPreview.setTextColor(Color.parseColor("#8b949e"));
            urlPreview.setTextSize(11f);
            urlPreview.setPadding(16, 0, 16, 14);
            urlPreview.setSingleLine(true);
            card.addView(urlPreview);

            card.setOnClickListener(v -> {
                switchToTab(tabIdx);
                hideTabGrid();
            });

            tabCardsContainer.addView(card);
        }

        tabGridOverlay.setVisibility(View.VISIBLE);
    }

    private void hideTabGrid() {
        tabGridOverlay.setVisibility(View.GONE);
    }

    // ── DIÁLOGO FLOTANTE INFERIOR MODERNO (BOTTOM SHEET) ─────────────────────
    private Dialog createBottomSheetDialog(View content) {
        Dialog d = new Dialog(this);
        d.requestWindowFeature(Window.FEATURE_NO_TITLE);
        d.setContentView(content);
        Window w = d.getWindow();
        if (w != null) {
            w.setBackgroundDrawable(new ColorDrawable(Color.TRANSPARENT));
            w.setLayout(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
            w.setGravity(Gravity.BOTTOM);
            w.setWindowAnimations(android.R.style.Animation_InputMethod);
        }
        return d;
    }

    // ── KIWI MENU SHEET 2.0 (SLIDING BOTTOM SHEET) ───────────────────────────
    private void showKiwiMenuSheet() {
        LinearLayout sheet = new LinearLayout(this);
        sheet.setOrientation(LinearLayout.VERTICAL);
        sheet.setBackgroundResource(R.drawable.bg_bottom_sheet);
        sheet.setPadding(16, 16, 16, 24);

        Dialog dialog = createBottomSheetDialog(sheet);

        // 1. Barra de Accesos Rápidos
        LinearLayout quickRow = new LinearLayout(this);
        quickRow.setOrientation(LinearLayout.HORIZONTAL);
        quickRow.setGravity(Gravity.CENTER);
        quickRow.setPadding(0, 4, 0, 16);

        addQuickAction(quickRow, R.drawable.ic_star, "Marcador", v -> {
            dialog.dismiss();
            Tab cur = getCurrentTab();
            if (cur != null && cur.webView.getUrl() != null && !cur.webView.getUrl().startsWith("file:///")) {
                db.addBookmark(cur.webView.getTitle(), cur.webView.getUrl());
                Toast.makeText(this, "⭐ Marcador guardado", Toast.LENGTH_SHORT).show();
            }
        });

        addQuickAction(quickRow, R.drawable.ic_download, "Descargas", v -> {
            dialog.dismiss();
            showDownloadsSheet();
        });

        addQuickAction(quickRow, R.drawable.ic_extension, "Extensiones", v -> {
            dialog.dismiss();
            showExtensionsSheet();
        });

        Tab cur = getCurrentTab();
        boolean isDesktop = (cur != null && cur.isDesktopMode);
        addQuickAction(quickRow, R.drawable.ic_desktop, isDesktop ? "Móvil" : "PC", v -> {
            dialog.dismiss();
            if (cur != null) {
                cur.isDesktopMode = !cur.isDesktopMode;
                cur.webView.getSettings().setUserAgentString(cur.isDesktopMode ? DESKTOP_UA : MOBILE_UA);
                cur.webView.reload();
                Toast.makeText(this, cur.isDesktopMode ? "Modo Computadora Activado" : "Modo Celular Activado", Toast.LENGTH_SHORT).show();
            }
        });

        addQuickAction(quickRow, R.drawable.ic_moon, "OLED", v -> {
            dialog.dismiss();
            forceOledDark = !forceOledDark;
            prefs.edit().putBoolean("force_oled_dark", forceOledDark).apply();
            if (cur != null) cur.webView.reload();
            Toast.makeText(this, forceOledDark ? "Modo Oscuro Forzado Activado" : "Modo Oscuro Forzado Desactivado", Toast.LENGTH_SHORT).show();
        });

        sheet.addView(quickRow);

        // Separador
        View sep = new View(this);
        sep.setBackgroundColor(Color.parseColor("#21262d"));
        sep.setLayoutParams(new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, 1));
        sheet.addView(sep);

        // Opciones principales
        addMenuRow(sheet, R.drawable.ic_add, "Nueva Pestaña", v -> {
            dialog.dismiss();
            createNewTab("file:///android_asset/ntp.html", false);
        });

        addMenuRow(sheet, R.drawable.ic_incognito, "Nueva Pestaña Privada (Incógnito)", v -> {
            dialog.dismiss();
            createNewTab("file:///android_asset/ntp.html", true);
        });

        addMenuRow(sheet, R.drawable.ic_bookmark, "Marcadores Guardados", v -> {
            dialog.dismiss();
            showBookmarksSheet();
        });

        addMenuRow(sheet, R.drawable.ic_history, "Historial de Navegación", v -> {
            dialog.dismiss();
            showHistorySheet();
        });

        addMenuRow(sheet, R.drawable.ic_shield, "Panel de Escudos Aegis", v -> {
            dialog.dismiss();
            showShieldsSheet();
        });

        addMenuRow(sheet, R.drawable.ic_movie, "AniPlay Anime Hub", v -> {
            dialog.dismiss();
            if (cur != null) cur.webView.loadUrl("file:///android_asset/aniplay.html");
        });

        addMenuRow(sheet, R.drawable.ic_delete, "Borrar Historial y Caché", v -> {
            dialog.dismiss();
            db.clearHistory();
            if (cur != null) cur.webView.clearCache(true);
            blockedTrackersCount = 0;
            lblShieldBadge.setText("0");
            Toast.makeText(this, "Historial y archivos temporales eliminados", Toast.LENGTH_SHORT).show();
        });

        addMenuRow(sheet, R.drawable.ic_settings, "Acerca de Aegis v1.5", v -> {
            dialog.dismiss();
            Toast.makeText(this, "Aegis Browser v1.5\\nUltra Fluido 120Hz • Kiwi Engine 100X", Toast.LENGTH_LONG).show();
        });

        dialog.show();
    }

    private void addQuickAction(LinearLayout parent, int iconRes, String labelText, View.OnClickListener listener) {
        LinearLayout col = new LinearLayout(this);
        col.setOrientation(LinearLayout.VERTICAL);
        col.setGravity(Gravity.CENTER);
        col.setPadding(10, 6, 10, 6);
        col.setLayoutParams(new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));
        col.setOnClickListener(listener);

        ImageView icon = new ImageView(this);
        icon.setImageResource(iconRes);
        icon.setBackgroundResource(R.drawable.bg_circle_icon);
        icon.setPadding(10, 10, 10, 10);
        icon.setLayoutParams(new LinearLayout.LayoutParams(44, 44));
        col.addView(icon);

        TextView label = new TextView(this);
        label.setText(labelText);
        label.setTextColor(Color.parseColor("#8b949e"));
        label.setTextSize(10.5f);
        label.setPadding(0, 4, 0, 0);
        col.addView(label);

        parent.addView(col);
    }

    private void addMenuRow(LinearLayout parent, int iconRes, String text, View.OnClickListener listener) {
        LinearLayout row = new LinearLayout(this);
        row.setOrientation(LinearLayout.HORIZONTAL);
        row.setGravity(Gravity.CENTER_VERTICAL);
        row.setPadding(16, 14, 16, 14);
        row.setClickable(true);
        row.setFocusable(true);

        ImageView icon = new ImageView(this);
        icon.setImageResource(iconRes);
        icon.setLayoutParams(new LinearLayout.LayoutParams(22, 22));
        row.addView(icon);

        TextView label = new TextView(this);
        label.setText(text);
        label.setTextColor(Color.parseColor("#f0f6fc"));
        label.setTextSize(14f);
        label.setPadding(16, 0, 0, 0);
        row.addView(label);

        row.setOnClickListener(listener);
        parent.addView(row);
    }

    // ── SHIELDS COMMAND CENTER (SLIDING SHEET) ────────────────────────────────
    private void showShieldsSheet() {
        LinearLayout sheet = new LinearLayout(this);
        sheet.setOrientation(LinearLayout.VERTICAL);
        sheet.setBackgroundResource(R.drawable.bg_bottom_sheet);
        sheet.setPadding(20, 20, 20, 28);

        Dialog dialog = createBottomSheetDialog(sheet);

        LinearLayout header = new LinearLayout(this);
        header.setOrientation(LinearLayout.HORIZONTAL);
        header.setGravity(Gravity.CENTER_VERTICAL);

        ImageView shieldIcon = new ImageView(this);
        shieldIcon.setImageResource(R.drawable.ic_shield);
        shieldIcon.setLayoutParams(new LinearLayout.LayoutParams(32, 32));
        header.addView(shieldIcon);

        LinearLayout titleCol = new LinearLayout(this);
        titleCol.setOrientation(LinearLayout.VERTICAL);
        titleCol.setPadding(12, 0, 0, 0);

        TextView title = new TextView(this);
        title.setText("Aegis Shields 2.0");
        title.setTextColor(Color.parseColor("#ffffff"));
        title.setTextSize(16f);
        title.setTypeface(null, android.graphics.Typeface.BOLD);
        titleCol.addView(title);

        TextView sub = new TextView(this);
        sub.setText("Protección activa • Cero anuncios y rastreo");
        sub.setTextColor(Color.parseColor("#8b949e"));
        sub.setTextSize(11f);
        titleCol.addView(sub);
        header.addView(titleCol);

        sheet.addView(header);

        // Tarjeta de Estadísticas
        LinearLayout statCard = new LinearLayout(this);
        statCard.setOrientation(LinearLayout.VERTICAL);
        statCard.setBackgroundResource(R.drawable.bg_card_inner);
        statCard.setPadding(16, 12, 16, 12);
        LinearLayout.LayoutParams scLp = new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        scLp.setMargins(0, 16, 0, 16);
        statCard.setLayoutParams(scLp);

        TextView statsNum = new TextView(this);
        statsNum.setText(String.valueOf(blockedTrackersCount));
        statsNum.setTextColor(Color.parseColor("#00f2fe"));
        statsNum.setTextSize(26f);
        statsNum.setTypeface(null, android.graphics.Typeface.BOLD);
        statCard.addView(statsNum);

        TextView statsDesc = new TextView(this);
        statsDesc.setText("Elementos bloqueados (Anuncios de video, trackers y banners)");
        statsDesc.setTextColor(Color.parseColor("#8b949e"));
        statsDesc.setTextSize(11.5f);
        statCard.addView(statsDesc);

        sheet.addView(statCard);

        // Switches
        addSwitchRow(sheet, "Bloqueador de Anuncios y YouTube Defuser", shieldsEnabled, (btn, isChecked) -> {
            shieldsEnabled = isChecked;
            prefs.edit().putBoolean("shields_enabled", isChecked).apply();
            Toast.makeText(this, isChecked ? "Shields Activados" : "Shields Pausados", Toast.LENGTH_SHORT).show();
        });

        addSwitchRow(sheet, "Salto de Temporizadores (CurseForge, Mega, Adf.ly)", timerBypassEnabled, (btn, isChecked) -> {
            timerBypassEnabled = isChecked;
            prefs.edit().putBoolean("timer_bypass_enabled", isChecked).apply();
            Toast.makeText(this, isChecked ? "Bypass Activado" : "Bypass Pausado", Toast.LENGTH_SHORT).show();
        });

        addSwitchRow(sheet, "Reproducción en Segundo Plano (YouTube)", backgroundPlaybackEnabled, (btn, isChecked) -> {
            backgroundPlaybackEnabled = isChecked;
            prefs.edit().putBoolean("background_playback", isChecked).apply();
            Toast.makeText(this, isChecked ? "Audio en segundo plano permitido" : "Audio pausado", Toast.LENGTH_SHORT).show();
        });

        addSwitchRow(sheet, "Forzar Modo Oscuro OLED en cualquier web", forceOledDark, (btn, isChecked) -> {
            forceOledDark = isChecked;
            prefs.edit().putBoolean("force_oled_dark", isChecked).apply();
            Tab cur = getCurrentTab();
            if (cur != null) cur.webView.reload();
        });

        dialog.show();
    }

    private void addSwitchRow(LinearLayout parent, String labelText, boolean initialChecked, CheckBox.OnCheckedChangeListener listener) {
        LinearLayout row = new LinearLayout(this);
        row.setOrientation(LinearLayout.HORIZONTAL);
        row.setGravity(Gravity.CENTER_VERTICAL);
        row.setPadding(0, 8, 0, 8);

        TextView label = new TextView(this);
        label.setText(labelText);
        label.setTextColor(Color.parseColor("#e6edf3"));
        label.setTextSize(13f);
        label.setLayoutParams(new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));
        row.addView(label);

        Switch sw = new Switch(this);
        sw.setChecked(initialChecked);
        sw.setOnCheckedChangeListener(listener);
        row.addView(sw);

        parent.addView(row);
    }

    // ── DESCARGAS SHEET (GESTOR DE DESCARGAS INTEGRADO) ───────────────────────
    private void showDownloadsSheet() {
        LinearLayout sheet = new LinearLayout(this);
        sheet.setOrientation(LinearLayout.VERTICAL);
        sheet.setBackgroundResource(R.drawable.bg_bottom_sheet);
        sheet.setPadding(20, 20, 20, 24);

        Dialog dialog = createBottomSheetDialog(sheet);

        LinearLayout topRow = new LinearLayout(this);
        topRow.setOrientation(LinearLayout.HORIZONTAL);
        topRow.setGravity(Gravity.CENTER_VERTICAL);

        TextView title = new TextView(this);
        title.setText("Descargas");
        title.setTextColor(Color.parseColor("#ffffff"));
        title.setTextSize(17f);
        title.setTypeface(null, android.graphics.Typeface.BOLD);
        title.setLayoutParams(new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));
        topRow.addView(title);

        TextView btnClear = new TextView(this);
        btnClear.setText("Limpiar lista");
        btnClear.setTextColor(Color.parseColor("#f85149"));
        btnClear.setTextSize(12f);
        btnClear.setPadding(8, 8, 8, 8);
        btnClear.setOnClickListener(v -> {
            db.clearDownloads();
            dialog.dismiss();
            Toast.makeText(this, "Lista de descargas vaciada", Toast.LENGTH_SHORT).show();
        });
        topRow.addView(btnClear);
        sheet.addView(topRow);

        List<String[]> dls = db.getDownloads();
        if (dls.isEmpty()) {
            TextView empty = new TextView(this);
            empty.setText("No hay descargas recientes.\\nLos archivos descargados se guardan en la carpeta Descargas de tu dispositivo.");
            empty.setTextColor(Color.parseColor("#8b949e"));
            empty.setTextSize(12f);
            empty.setPadding(0, 20, 0, 20);
            sheet.addView(empty);
        } else {
            ScrollView sc = new ScrollView(this);
            sc.setLayoutParams(new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, 400));
            LinearLayout listLayout = new LinearLayout(this);
            listLayout.setOrientation(LinearLayout.VERTICAL);

            for (String[] dl : dls) {
                LinearLayout row = new LinearLayout(this);
                row.setOrientation(LinearLayout.HORIZONTAL);
                row.setGravity(Gravity.CENTER_VERTICAL);
                row.setPadding(0, 12, 0, 12);

                ImageView ic = new ImageView(this);
                ic.setImageResource(R.drawable.ic_file);
                ic.setLayoutParams(new LinearLayout.LayoutParams(24, 24));
                row.addView(ic);

                LinearLayout col = new LinearLayout(this);
                col.setOrientation(LinearLayout.VERTICAL);
                col.setPadding(12, 0, 0, 0);
                col.setLayoutParams(new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));

                TextView name = new TextView(this);
                name.setText(dl[0]);
                name.setTextColor(Color.parseColor("#e6edf3"));
                name.setTextSize(13f);
                name.setSingleLine(true);
                col.addView(name);

                TextView urlTxt = new TextView(this);
                urlTxt.setText(dl[1]);
                urlTxt.setTextColor(Color.parseColor("#8b949e"));
                urlTxt.setTextSize(10f);
                urlTxt.setSingleLine(true);
                col.addView(urlTxt);
                row.addView(col);

                TextView btnOpen = new TextView(this);
                btnOpen.setText("Abrir");
                btnOpen.setTextColor(Color.parseColor("#388bfd"));
                btnOpen.setTextSize(12f);
                btnOpen.setPadding(12, 6, 12, 6);
                btnOpen.setBackgroundResource(R.drawable.bg_btn_secondary);
                btnOpen.setOnClickListener(v -> {
                    try {
                        File f = new File(Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_DOWNLOADS), dl[0]);
                        Intent i = new Intent(Intent.ACTION_VIEW);
                        i.setDataAndType(Uri.fromFile(f), "*/*");
                        i.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
                        startActivity(i);
                    } catch (Exception e) {
                        Toast.makeText(this, "Abriendo archivo...", Toast.LENGTH_SHORT).show();
                    }
                });
                row.addView(btnOpen);

                listLayout.addView(row);
            }
            sc.addView(listLayout);
            sheet.addView(sc);
        }

        dialog.show();
    }

    // ── MARCADORES SHEET (CON BUSCADOR) ──────────────────────────────────────
    private void showBookmarksSheet() {
        LinearLayout sheet = new LinearLayout(this);
        sheet.setOrientation(LinearLayout.VERTICAL);
        sheet.setBackgroundResource(R.drawable.bg_bottom_sheet);
        sheet.setPadding(20, 20, 20, 24);

        Dialog dialog = createBottomSheetDialog(sheet);

        TextView title = new TextView(this);
        title.setText("Marcadores");
        title.setTextColor(Color.parseColor("#ffffff"));
        title.setTextSize(17f);
        title.setTypeface(null, android.graphics.Typeface.BOLD);
        sheet.addView(title);

        List<String[]> bms = db.getBookmarks();
        if (bms.isEmpty()) {
            TextView empty = new TextView(this);
            empty.setText("No tienes marcadores guardados todavía.");
            empty.setTextColor(Color.parseColor("#8b949e"));
            empty.setTextSize(12f);
            empty.setPadding(0, 16, 0, 16);
            sheet.addView(empty);
        } else {
            ScrollView sc = new ScrollView(this);
            sc.setLayoutParams(new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, 400));
            LinearLayout listLayout = new LinearLayout(this);
            listLayout.setOrientation(LinearLayout.VERTICAL);

            for (String[] bm : bms) {
                LinearLayout row = new LinearLayout(this);
                row.setOrientation(LinearLayout.HORIZONTAL);
                row.setGravity(Gravity.CENTER_VERTICAL);
                row.setPadding(0, 12, 0, 12);

                ImageView ic = new ImageView(this);
                ic.setImageResource(R.drawable.ic_bookmark);
                ic.setLayoutParams(new LinearLayout.LayoutParams(22, 22));
                row.addView(ic);

                LinearLayout col = new LinearLayout(this);
                col.setOrientation(LinearLayout.VERTICAL);
                col.setPadding(12, 0, 0, 0);
                col.setLayoutParams(new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));

                TextView name = new TextView(this);
                name.setText(bm[0]);
                name.setTextColor(Color.parseColor("#e6edf3"));
                name.setTextSize(13f);
                name.setSingleLine(true);
                col.addView(name);

                TextView urlTxt = new TextView(this);
                urlTxt.setText(bm[1]);
                urlTxt.setTextColor(Color.parseColor("#8b949e"));
                urlTxt.setTextSize(10.5f);
                urlTxt.setSingleLine(true);
                col.addView(urlTxt);
                row.addView(col);

                row.setOnClickListener(v -> {
                    dialog.dismiss();
                    Tab cur = getCurrentTab();
                    if (cur != null) cur.webView.loadUrl(bm[1]);
                });

                listLayout.addView(row);
            }
            sc.addView(listLayout);
            sheet.addView(sc);
        }

        dialog.show();
    }

    // ── HISTORIAL SHEET ───────────────────────────────────────────────────────
    private void showHistorySheet() {
        LinearLayout sheet = new LinearLayout(this);
        sheet.setOrientation(LinearLayout.VERTICAL);
        sheet.setBackgroundResource(R.drawable.bg_bottom_sheet);
        sheet.setPadding(20, 20, 20, 24);

        Dialog dialog = createBottomSheetDialog(sheet);

        LinearLayout topRow = new LinearLayout(this);
        topRow.setOrientation(LinearLayout.HORIZONTAL);
        topRow.setGravity(Gravity.CENTER_VERTICAL);

        TextView title = new TextView(this);
        title.setText("Historial de Navegación");
        title.setTextColor(Color.parseColor("#ffffff"));
        title.setTextSize(17f);
        title.setTypeface(null, android.graphics.Typeface.BOLD);
        title.setLayoutParams(new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));
        topRow.addView(title);

        TextView btnClear = new TextView(this);
        btnClear.setText("Borrar todo");
        btnClear.setTextColor(Color.parseColor("#f85149"));
        btnClear.setTextSize(12f);
        btnClear.setPadding(8, 8, 8, 8);
        btnClear.setOnClickListener(v -> {
            db.clearHistory();
            dialog.dismiss();
            Toast.makeText(this, "Historial borrado", Toast.LENGTH_SHORT).show();
        });
        topRow.addView(btnClear);
        sheet.addView(topRow);

        List<String[]> hists = db.getHistory();
        if (hists.isEmpty()) {
            TextView empty = new TextView(this);
            empty.setText("Historial vacío.");
            empty.setTextColor(Color.parseColor("#8b949e"));
            empty.setTextSize(12f);
            empty.setPadding(0, 16, 0, 16);
            sheet.addView(empty);
        } else {
            ScrollView sc = new ScrollView(this);
            sc.setLayoutParams(new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, 420));
            LinearLayout listLayout = new LinearLayout(this);
            listLayout.setOrientation(LinearLayout.VERTICAL);

            for (String[] h : hists) {
                LinearLayout row = new LinearLayout(this);
                row.setOrientation(LinearLayout.HORIZONTAL);
                row.setGravity(Gravity.CENTER_VERTICAL);
                row.setPadding(0, 10, 0, 10);

                ImageView ic = new ImageView(this);
                ic.setImageResource(R.drawable.ic_history);
                ic.setLayoutParams(new LinearLayout.LayoutParams(20, 20));
                row.addView(ic);

                LinearLayout col = new LinearLayout(this);
                col.setOrientation(LinearLayout.VERTICAL);
                col.setPadding(12, 0, 0, 0);
                col.setLayoutParams(new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));

                TextView name = new TextView(this);
                name.setText(h[0]);
                name.setTextColor(Color.parseColor("#e6edf3"));
                name.setTextSize(12.5f);
                name.setSingleLine(true);
                col.addView(name);

                TextView urlTxt = new TextView(this);
                urlTxt.setText(h[1]);
                urlTxt.setTextColor(Color.parseColor("#8b949e"));
                urlTxt.setTextSize(10f);
                urlTxt.setSingleLine(true);
                col.addView(urlTxt);
                row.addView(col);

                row.setOnClickListener(v -> {
                    dialog.dismiss();
                    Tab cur = getCurrentTab();
                    if (cur != null) cur.webView.loadUrl(h[1]);
                });

                listLayout.addView(row);
            }
            sc.addView(listLayout);
            sheet.addView(sc);
        }

        dialog.show();
    }

    // ── EXTENSIONES SHEET ─────────────────────────────────────────────────────
    private void showExtensionsSheet() {
        LinearLayout sheet = new LinearLayout(this);
        sheet.setOrientation(LinearLayout.VERTICAL);
        sheet.setBackgroundResource(R.drawable.bg_bottom_sheet);
        sheet.setPadding(20, 20, 20, 24);

        Dialog dialog = createBottomSheetDialog(sheet);

        LinearLayout topRow = new LinearLayout(this);
        topRow.setOrientation(LinearLayout.HORIZONTAL);
        topRow.setGravity(Gravity.CENTER_VERTICAL);

        TextView title = new TextView(this);
        title.setText("Extensiones de Chrome");
        title.setTextColor(Color.parseColor("#ffffff"));
        title.setTextSize(17f);
        title.setTypeface(null, android.graphics.Typeface.BOLD);
        title.setLayoutParams(new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));
        topRow.addView(title);

        TextView btnWebStore = new TextView(this);
        btnWebStore.setText("+ Chrome Web Store");
        btnWebStore.setTextColor(Color.parseColor("#bc8cff"));
        btnWebStore.setTextSize(12f);
        btnWebStore.setTypeface(null, android.graphics.Typeface.BOLD);
        btnWebStore.setPadding(8, 8, 8, 8);
        btnWebStore.setOnClickListener(v -> {
            dialog.dismiss();
            Tab cur = getCurrentTab();
            if (cur != null) cur.webView.loadUrl("https://chromewebstore.google.com");
        });
        topRow.addView(btnWebStore);
        sheet.addView(topRow);

        List<AegisExtension> exts = extManager.getInstalledExtensions();
        for (AegisExtension ext : exts) {
            LinearLayout card = new LinearLayout(this);
            card.setOrientation(LinearLayout.HORIZONTAL);
            card.setGravity(Gravity.CENTER_VERTICAL);
            card.setBackgroundResource(R.drawable.bg_card_inner);
            card.setPadding(14, 12, 14, 12);
            LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
            lp.setMargins(0, 8, 0, 8);
            card.setLayoutParams(lp);

            ImageView ic = new ImageView(this);
            ic.setImageResource(R.drawable.ic_extension);
            ic.setLayoutParams(new LinearLayout.LayoutParams(24, 24));
            card.addView(ic);

            LinearLayout col = new LinearLayout(this);
            col.setOrientation(LinearLayout.VERTICAL);
            col.setPadding(12, 0, 0, 0);
            col.setLayoutParams(new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));

            TextView name = new TextView(this);
            name.setText(ext.name);
            name.setTextColor(Color.parseColor("#e6edf3"));
            name.setTextSize(13.5f);
            col.addView(name);

            TextView ver = new TextView(this);
            ver.setText("v" + ext.version + " • Activa");
            ver.setTextColor(Color.parseColor("#3fb950"));
            ver.setTextSize(10.5f);
            col.addView(ver);
            card.addView(col);

            Switch sw = new Switch(this);
            sw.setChecked(ext.isEnabled);
            sw.setOnCheckedChangeListener((btn, isChecked) -> {
                ext.isEnabled = isChecked;
                Toast.makeText(this, ext.name + (isChecked ? " activada" : " pausada"), Toast.LENGTH_SHORT).show();
            });
            card.addView(sw);

            sheet.addView(card);
        }

        dialog.show();
    }

    @Override
    public void onBackPressed() {
        if (tabGridOverlay.getVisibility() == View.VISIBLE) {
            hideTabGrid();
            return;
        }
        Tab cur = getCurrentTab();
        if (cur != null && cur.webView.canGoBack()) {
            cur.webView.goBack();
        } else {
            super.onBackPressed();
        }
    }
}
"""
(src_java_dir / "MainActivity.java").write_text(main_activity_java, encoding="utf-8")

# ── 8. Compilación con aapt2, javac, d8, zipalign y apksigner ─────────────────
print("[1/5] Compilando recursos con aapt2...")
cmd_compile_res = [str(AAPT2), "compile", "--dir", str(res_dir), "-o", str(compiled_res_dir)]
res = subprocess.run(cmd_compile_res, capture_output=True, text=True)
if res.returncode != 0:
    print("[ERROR] Falló aapt2 compile:", res.stderr)
    sys.exit(1)
print("  [OK] Recursos XML compilados.")

print("[2/5] Enlazando APK base y generando R.java...")
base_apk = bin_dir / "base.apk"
cmd_link = [
    str(AAPT2), "link",
    "-I", str(ANDROID_JAR),
    "--manifest", str(work_dir / "AndroidManifest.xml"),
    "--java", str(work_dir / "src"),
    "-A", str(assets_dir),
    "-o", str(base_apk),
    "--auto-add-overlay"
]
for zip_file in compiled_res_dir.glob("*.flat"):
    cmd_link.append(str(zip_file))

res = subprocess.run(cmd_link, capture_output=True, text=True)
if res.returncode != 0:
    print("[ERROR] Falló aapt2 link:", res.stderr)
    sys.exit(1)
print("  [OK] Base APK y R.java generados.")

print("[3/5] Compilando código Java con javac...")
java_files = list(work_dir.rglob("*.java"))
cmd_javac = [
    "javac",
    "-encoding", "utf-8",
    "-cp", str(ANDROID_JAR),
    "-d", str(bin_dir)
] + [str(f) for f in java_files]

res = subprocess.run(cmd_javac, capture_output=True, text=True)
if res.returncode != 0:
    print("[ERROR] Falló javac:", res.stderr)
    sys.exit(1)
print(f"  [OK] {len(java_files)} archivos Java compilados a bytecode.")

print("[4/5] Convirtiendo a Dalvik Executable (classes.dex) con d8...")
class_files = list(bin_dir.rglob("*.class"))
cmd_d8 = [
    "cmd.exe", "/c", str(D8),
    "--lib", str(ANDROID_JAR),
    "--output", str(bin_dir)
] + [str(f) for f in class_files]

res = subprocess.run(cmd_d8, capture_output=True, text=True)
if res.returncode != 0:
    print("[ERROR] Falló d8:", res.stderr)
    sys.exit(1)
print("  [OK] classes.dex generado.")

# Empaquetar classes.dex en el APK base
with zipfile.ZipFile(base_apk, "a") as apk_zip:
    apk_zip.write(bin_dir / "classes.dex", "classes.dex")

print("[5/5] Alineando y firmando APK (zipalign + apksigner)...")
unaligned_apk = bin_dir / "unaligned.apk"
shutil.copy2(base_apk, unaligned_apk)

aligned_apk = bin_dir / "aligned.apk"
if aligned_apk.exists(): aligned_apk.unlink()

cmd_align = [str(ZIPALIGN), "-f", "-p", "4", str(unaligned_apk), str(aligned_apk)]
res = subprocess.run(cmd_align, capture_output=True, text=True)
if res.returncode != 0:
    print("[ERROR] Falló zipalign:", res.stderr)
    sys.exit(1)

# Keystore
keystore_path = work_dir / "aegis_debug.keystore"
if not keystore_path.exists():
    cmd_key = [
        "keytool", "-genkeypair", "-v",
        "-keystore", str(keystore_path),
        "-alias", "aegis",
        "-keyalg", "RSA",
        "-keysize", "2048",
        "-validity", "10000",
        "-storepass", "aegispass",
        "-keypass", "aegispass",
        "-dname", "CN=Aegis, OU=Mobile, O=Aegis, L=Santiago, ST=RM, C=CL"
    ]
    subprocess.run(cmd_key, capture_output=True)

if final_apk.exists(): final_apk.unlink()

cmd_sign = [
    str(APKSIGNER), "sign",
    "--v2-signing-enabled", "true",
    "--v3-signing-enabled", "true",
    "--ks", str(keystore_path),
    "--ks-pass", "pass:aegispass",
    "--key-pass", "pass:aegispass",
    "--ks-key-alias", "aegis",
    "--out", str(final_apk),
    str(aligned_apk)
]
res = subprocess.run(cmd_sign, capture_output=True, text=True)
if res.returncode != 0:
    print("[ERROR] Falló apksigner:", res.stderr)
    sys.exit(1)

print("\n" + "="*65)
print("COMPILACIÓN EXITOSA: AEGIS BROWSER 2.0 (100X MOBILE OVERHAUL)")
print("="*65)
size_kb = round(final_apk.stat().st_size / 1024, 2)
print(f"Archivo generado: {final_apk.resolve()}")
print(f"Tamaño: {size_kb} KB ({round(size_kb/1024, 2)} MB)")
print("="*65)
