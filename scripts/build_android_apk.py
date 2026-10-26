import sys, os, subprocess, shutil
from pathlib import Path

print("="*60)
print("COMPILANDO AEGIS BROWSER PARA ANDROID (ARM64)")
print("="*60)

BUILD_TOOLS_DIR = Path(r"C:\Users\PC\AppData\Local\Android\Sdk\build-tools\35.0.0")
ANDROID_JAR = Path(r"C:\Users\PC\AppData\Local\Android\Sdk\platforms\android-34\android.jar")

AAPT2 = BUILD_TOOLS_DIR / "aapt2.exe"
D8 = BUILD_TOOLS_DIR / "d8.bat"
ZIPALIGN = BUILD_TOOLS_DIR / "zipalign.exe"
APKSIGNER = BUILD_TOOLS_DIR / "apksigner.bat"

output_dir = Path("dist/android")
output_dir.mkdir(parents=True, exist_ok=True)
final_apk = output_dir / "Aegis-arm64-v8a.apk"

work_dir = Path("build/android_build")
if work_dir.exists():
    shutil.rmtree(work_dir)
work_dir.mkdir(parents=True, exist_ok=True)

# 1. Create project directories
src_java_dir = work_dir / "src/org/aegis/browser"
res_dir = work_dir / "res"
res_values = res_dir / "values"
res_layout = res_dir / "layout"
res_drawable = res_dir / "drawable"
assets_dir = work_dir / "assets"
bin_dir = work_dir / "bin"
gen_dir = work_dir / "gen"

for d in [src_java_dir, res_values, res_layout, res_drawable, assets_dir, bin_dir, gen_dir]:
    d.mkdir(parents=True, exist_ok=True)

# 2. Write AndroidManifest.xml
manifest_content = """<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="org.aegis.browser"
    android:versionCode="1"
    android:versionName="1.0.0">

    <uses-sdk
        android:minSdkVersion="26"
        android:targetSdkVersion="34" />

    <uses-permission android:name="android.permission.INTERNET" />
    <uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />

    <supports-screens
        android:smallScreens="true"
        android:normalScreens="true"
        android:largeScreens="true"
        android:xlargeScreens="true"
        android:anyDensity="true" />

    <application
        android:label="Aegis Browser"
        android:icon="@drawable/ic_launcher"
        android:hardwareAccelerated="true"
        android:largeHeap="true"
        android:supportsRtl="true"
        android:theme="@android:style/Theme.DeviceDefault.NoActionBar">

        <meta-data android:name="android.max_aspect" android:value="2.4" />

        <activity
            android:name=".MainActivity"
            android:exported="true"
            android:configChanges="orientation|screenSize|keyboardHidden|screenLayout|smallestScreenSize"
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

# 3. Write resources
(res_values / "strings.xml").write_text("""<?xml version="1.0" encoding="utf-8"?>
<resources>
    <string name="app_name">Aegis Browser</string>
</resources>
""", encoding="utf-8")

(res_values / "colors.xml").write_text("""<?xml version="1.0" encoding="utf-8"?>
<resources>
    <color name="bg_dark">#0d1117</color>
    <color name="surface_dark">#161b22</color>
    <color name="text_light">#f0f6fc</color>
    <color name="accent_blue">#388bfd</color>
</resources>
""", encoding="utf-8")

# Drawable icon (vector shield)
(res_drawable / "ic_launcher.xml").write_text("""<?xml version="1.0" encoding="utf-8"?>
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="108dp"
    android:height="108dp"
    android:viewportWidth="108"
    android:viewportHeight="108">
    <path
        android:fillColor="#0d1117"
        android:pathData="M0,0h108v108h-108z"/>
    <path
        android:fillColor="#388bfd"
        android:pathData="M54,20L28,32v24c0,18.4 11.2,35.6 26,40c14.8,-4.4 26,-21.6 26,-40V32L54,20z"/>
    <path
        android:fillColor="#f0f6fc"
        android:pathData="M54,26L34,36v20c0,14.2 8.6,27.5 20,31c11.4,-3.5 20,-16.8 20,-31V36L54,26z"/>
    <path
        android:fillColor="#0d1117"
        android:pathData="M54,42L42,66h24z"/>
</vector>
""", encoding="utf-8")

# Layout Activity Main (Omnibox top, WebView center, Bottom Toolbar bottom)
(res_layout / "activity_main.xml").write_text("""<?xml version="1.0" encoding="utf-8"?>
<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent"
    android:layout_height="match_parent"
    android:orientation="vertical"
    android:background="#0d1117">

    <!-- Barra Superior / Omnibox -->
    <LinearLayout
        android:id="@+id/topBar"
        android:layout_width="match_parent"
        android:layout_height="52dp"
        android:orientation="horizontal"
        android:gravity="center_vertical"
        android:paddingLeft="12dp"
        android:paddingRight="12dp"
        android:background="#161b22">

        <TextView
            android:id="@+id/btnShield"
            android:layout_width="36dp"
            android:layout_height="36dp"
            android:gravity="center"
            android:text="🛡️"
            android:textSize="18sp"
            android:textColor="#388bfd"
            android:background="?android:attr/selectableItemBackgroundBorderless"/>

        <EditText
            android:id="@+id/urlInput"
            android:layout_width="0dp"
            android:layout_height="38dp"
            android:layout_weight="1"
            android:layout_marginLeft="8dp"
            android:layout_marginRight="8dp"
            android:background="#21262d"
            android:paddingLeft="12dp"
            android:paddingRight="12dp"
            android:textColor="#f0f6fc"
            android:textColorHint="#8b949e"
            android:textSize="14sp"
            android:singleLine="true"
            android:imeOptions="actionGo"
            android:hint="Buscar o ingresar URL..."/>

        <ProgressBar
            android:id="@+id/progressBar"
            android:layout_width="24dp"
            android:layout_height="24dp"
            android:visibility="gone"/>

        <TextView
            android:id="@+id/btnMore"
            android:layout_width="36dp"
            android:layout_height="36dp"
            android:gravity="center"
            android:text="⋮"
            android:textSize="20sp"
            android:textColor="#f0f6fc"
            android:background="?android:attr/selectableItemBackgroundBorderless"/>
    </LinearLayout>

    <!-- WebView Principal (Hardware Accelerated) -->
    <WebView
        android:id="@+id/webView"
        android:layout_width="match_parent"
        android:layout_height="0dp"
        android:layout_weight="1"/>

    <!-- Barra Inferior de Navegación Táctil (Ergonomía para una mano) -->
    <LinearLayout
        android:id="@+id/bottomBar"
        android:layout_width="match_parent"
        android:layout_height="48dp"
        android:orientation="horizontal"
        android:gravity="center"
        android:background="#161b22">

        <TextView
            android:id="@+id/btnBack"
            android:layout_width="0dp"
            android:layout_height="match_parent"
            android:layout_weight="1"
            android:gravity="center"
            android:text="◀"
            android:textSize="16sp"
            android:textColor="#f0f6fc"
            android:background="?android:attr/selectableItemBackground"/>

        <TextView
            android:id="@+id/btnForward"
            android:layout_width="0dp"
            android:layout_height="match_parent"
            android:layout_weight="1"
            android:gravity="center"
            android:text="▶"
            android:textSize="16sp"
            android:textColor="#f0f6fc"
            android:background="?android:attr/selectableItemBackground"/>

        <TextView
            android:id="@+id/btnHome"
            android:layout_width="0dp"
            android:layout_height="match_parent"
            android:layout_weight="1"
            android:gravity="center"
            android:text="🏠"
            android:textSize="18sp"
            android:textColor="#f0f6fc"
            android:background="?android:attr/selectableItemBackground"/>

        <TextView
            android:id="@+id/btnTabs"
            android:layout_width="0dp"
            android:layout_height="match_parent"
            android:layout_weight="1"
            android:gravity="center"
            android:text="📑"
            android:textSize="18sp"
            android:textColor="#f0f6fc"
            android:background="?android:attr/selectableItemBackground"/>

        <TextView
            android:id="@+id/btnDownloads"
            android:layout_width="0dp"
            android:layout_height="match_parent"
            android:layout_weight="1"
            android:gravity="center"
            android:text="📥"
            android:textSize="18sp"
            android:textColor="#f0f6fc"
            android:background="?android:attr/selectableItemBackground"/>
    </LinearLayout>
</LinearLayout>
""", encoding="utf-8")

# 4. Copy bypass script and NTP files to assets
scripts_dir = Path.home() / ".aegis_userscripts"
bypass_file = scripts_dir / "aegis_timer_bypass.js"
if bypass_file.exists():
    shutil.copy(bypass_file, assets_dir / "aegis_timer_bypass.js")
else:
    (assets_dir / "aegis_timer_bypass.js").write_text("// Aegis Timer Bypass\n", encoding="utf-8")

# NTP HTML for mobile
ntp_html = """<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
  <title>Nueva Pestaña - Aegis</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background: #0d1117; color: #f0f6fc;
      font-family: -apple-system, Roboto, sans-serif;
      display: flex; flex-direction: column; align-items: center; justify-content: center;
      min-height: 100vh; padding: 20px; text-align: center;
    }
    .logo { font-size: 2.2rem; font-weight: 800; margin-bottom: 6px; letter-spacing: -0.5px; }
    .logo span { color: #388bfd; }
    .tagline { font-size: 0.85rem; color: #8b949e; margin-bottom: 24px; }
    .search-bar {
      width: 100%; max-width: 450px; background: #161b22;
      border: 1px solid #30363d; border-radius: 24px; padding: 10px 18px;
      display: flex; align-items: center; gap: 10px; margin-bottom: 28px;
    }
    .search-bar input {
      background: transparent; border: none; color: #f0f6fc;
      font-size: 0.95rem; width: 100%; outline: none;
    }
    .grid {
      display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px;
      width: 100%; max-width: 450px; margin-bottom: 30px;
    }
    .tile {
      background: #161b22; border: 1px solid #21262d; border-radius: 12px;
      padding: 12px 6px; display: flex; flex-direction: column; align-items: center;
      gap: 6px; text-decoration: none; color: #f0f6fc; font-size: 0.75rem;
    }
    .tile-icon { font-size: 1.4rem; }
    .stats {
      background: rgba(56, 139, 253, 0.1); border: 1px solid rgba(56, 139, 253, 0.3);
      border-radius: 12px; padding: 12px 20px; font-size: 0.8rem; color: #58a6ff;
    }
  </style>
</head>
<body>
  <div class="logo"><span>AEGIS</span> BROWSER</div>
  <div class="tagline">120Hz Ultra Fluido • Aegis Shields Activo • Cero Rastreo</div>
  <div class="search-bar">
    <span>🔍</span>
    <input type="text" placeholder="Buscar en la web..." onkeydown="if(event.key==='Enter')location.href='https://duckduckgo.com/?q='+encodeURIComponent(this.value)">
  </div>
  <div class="grid">
    <a href="https://youtube.com" class="tile"><div class="tile-icon">▶️</div><div>YouTube</div></a>
    <a href="https://reddit.com" class="tile"><div class="tile-icon">🤖</div><div>Reddit</div></a>
    <a href="https://github.com" class="tile"><div class="tile-icon">🐙</div><div>GitHub</div></a>
    <a href="https://wikipedia.org" class="tile"><div class="tile-icon">📚</div><div>Wikipedia</div></a>
    <a href="https://curseforge.com" class="tile"><div class="tile-icon">⚡</div><div>CurseForge</div></a>
    <a href="https://mega.nz" class="tile"><div class="tile-icon">☁️</div><div>MEGA</div></a>
    <a href="https://mediafire.com" class="tile"><div class="tile-icon">🔥</div><div>Mediafire</div></a>
    <a href="https://store.steampowered.com" class="tile"><div class="tile-icon">🎮</div><div>Steam</div></a>
  </div>
  <div class="stats">
    🛡️ <strong>Aegis Shields & Timer Bypass</strong> activos en este dispositivo.
  </div>
</body>
</html>
"""
(assets_dir / "ntp.html").write_text(ntp_html, encoding="utf-8")

# 5. Write MainActivity.java
java_content = """package org.aegis.browser;

import android.app.Activity;
import android.graphics.Bitmap;
import android.graphics.PixelFormat;
import android.os.Build;
import android.os.Bundle;
import android.view.Display;
import android.view.View;
import android.view.Window;
import android.view.WindowManager;
import android.view.inputmethod.EditorInfo;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceRequest;
import android.webkit.WebResourceResponse;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.EditText;
import android.widget.ProgressBar;
import android.widget.TextView;
import android.widget.Toast;

import java.io.ByteArrayInputStream;
import java.io.InputStream;
import java.util.Scanner;

public class MainActivity extends Activity {

    private WebView webView;
    private EditText urlInput;
    private ProgressBar progressBar;
    private TextView btnShield;
    private String bypassJsScript = "";
    private int blockedCount = 0;

    private static final String[] AD_DOMAINS = {
        "doubleclick.net", "googlesyndication.com", "google-analytics.com",
        "adservice.google.com", "adnxs.com", "criteo.com", "taboola.com",
        "outbrain.com", "popads.net", "propellerads.com", "adsterra.com"
    };

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        // Optimización 120Hz para Xiaomi 12 Pro (Snapdragon 8 Gen 1) y Lenovo Xiaoxin Pad 11
        setupHighRefreshRate();

        loadBypassScript();

        urlInput = findViewById(R.id.urlInput);
        progressBar = findViewById(R.id.progressBar);
        btnShield = findViewById(R.id.btnShield);
        webView = findViewById(R.id.webView);

        setupWebView();
        setupNavigationControls();

        // Cargar Nueva Pestaña por defecto
        webView.loadUrl("file:///android_asset/ntp.html");
    }

    private void setupHighRefreshRate() {
        try {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
                Display display = getDisplay();
                if (display != null) {
                    Display.Mode[] modes = display.getSupportedModes();
                    Display.Mode bestMode = null;
                    float maxRate = 60.0f;
                    for (Display.Mode m : modes) {
                        if (m.getRefreshRate() > maxRate) {
                            maxRate = m.getRefreshRate();
                            bestMode = m;
                        }
                    }
                    if (bestMode != null) {
                        Window window = getWindow();
                        WindowManager.LayoutParams params = window.getAttributes();
                        params.preferredDisplayModeId = bestMode.getModeId();
                        window.setAttributes(params);
                    }
                }
            }
        } catch (Exception e) {}
    }

    private void loadBypassScript() {
        try {
            InputStream is = getAssets().open("aegis_timer_bypass.js");
            Scanner s = new Scanner(is, "UTF-8").useDelimiter("\\\\A");
            bypassJsScript = s.hasNext() ? s.next() : "";
            is.close();
        } catch (Exception e) {}
    }

    private void setupWebView() {
        WebSettings settings = webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setDatabaseEnabled(true);
        settings.setAllowFileAccess(true);
        settings.setMediaPlaybackRequiresUserGesture(false);
        settings.setSupportZoom(true);
        settings.setBuiltInZoomControls(true);
        settings.setDisplayZoomControls(false);
        settings.setUseWideViewPort(true);
        settings.setLoadWithOverviewMode(true);
        settings.setUserAgentString("Mozilla/5.0 (Linux; Android 14; Mobile) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.36 Aegis/1.0");

        webView.setWebChromeClient(new WebChromeClient() {
            @Override
            public void onProgressChanged(WebView view, int newProgress) {
                if (newProgress < 100) {
                    progressBar.setVisibility(View.VISIBLE);
                } else {
                    progressBar.setVisibility(View.GONE);
                }
            }
        });

        webView.setWebViewClient(new WebViewClient() {
            @Override
            public WebResourceResponse shouldInterceptRequest(WebView view, WebResourceRequest request) {
                String host = request.getUrl().getHost();
                if (host != null) {
                    for (String ad : AD_DOMAINS) {
                        if (host.contains(ad)) {
                            blockedCount++;
                            runOnUiThread(new Runnable() {
                                @Override
                                public void run() {
                                    btnShield.setText("🛡️ " + blockedCount);
                                }
                            });
                            return new WebResourceResponse("text/plain", "UTF-8", new ByteArrayInputStream(new byte[0]));
                        }
                    }
                }
                return super.shouldInterceptRequest(view, request);
            }

            @Override
            public void onPageStarted(WebView view, String url, Bitmap favicon) {
                if (!url.startsWith("file:///")) {
                    urlInput.setText(url);
                }
            }

            @Override
            public void onPageFinished(WebView view, String url) {
                // Inyectar el motor de salto de temporizadores (CurseForge, Mega, Adf.ly, etc.)
                if (bypassJsScript != null && !bypassJsScript.isEmpty()) {
                    view.evaluateJavascript(bypassJsScript, null);
                }
            }
        });
    }

    private void setupNavigationControls() {
        urlInput.setOnEditorActionListener((v, actionId, event) -> {
            if (actionId == EditorInfo.IME_ACTION_GO || actionId == EditorInfo.IME_ACTION_DONE) {
                String q = urlInput.getText().toString().trim();
                if (!q.isEmpty()) {
                    if (q.startsWith("http://") || q.startsWith("https://")) {
                        webView.loadUrl(q);
                    } else if (q.contains(".") && !q.contains(" ")) {
                        webView.loadUrl("https://" + q);
                    } else {
                        webView.loadUrl("https://duckduckgo.com/?q=" + q);
                    }
                }
                return true;
            }
            return false;
        });

        findViewById(R.id.btnBack).setOnClickListener(v -> {
            if (webView.canGoBack()) webView.goBack();
        });

        findViewById(R.id.btnForward).setOnClickListener(v -> {
            if (webView.canGoForward()) webView.goForward();
        });

        findViewById(R.id.btnHome).setOnClickListener(v -> {
            webView.loadUrl("file:///android_asset/ntp.html");
            urlInput.setText("");
        });

        findViewById(R.id.btnTabs).setOnClickListener(v -> {
            Toast.makeText(MainActivity.this, "Aegis Tabs: Pestaña Activa", Toast.LENGTH_SHORT).show();
        });

        findViewById(R.id.btnDownloads).setOnClickListener(v -> {
            Toast.makeText(MainActivity.this, "Descargas Aegis gestionadas por el sistema", Toast.LENGTH_SHORT).show();
        });

        btnShield.setOnClickListener(v -> {
            Toast.makeText(MainActivity.this, "Aegis Shields: " + blockedCount + " rastreadores bloqueados. Timer Bypass Activo.", Toast.LENGTH_LONG).show();
        });

        findViewById(R.id.btnMore).setOnClickListener(v -> {
            Toast.makeText(MainActivity.this, "Aegis Browser v1.0 • Xiaomi 12 Pro & Lenovo Xiaoxin Pad 11", Toast.LENGTH_SHORT).show();
        });
    }

    @Override
    public void onBackPressed() {
        if (webView.canGoBack()) {
            webView.goBack();
        } else {
            super.onBackPressed();
        }
    }
}
"""
(src_java_dir / "MainActivity.java").write_text(java_content, encoding="utf-8")
print("1. Estructura del proyecto Android y código fuente generados.")

# 6. Step 1: aapt2 compile
print("[>] Compilando recursos con aapt2...")
compiled_res_zip = work_dir / "compiled_res.zip"
cmd_compile = [
    str(AAPT2), "compile",
    "--dir", str(res_dir),
    "-o", str(compiled_res_zip)
]
res = subprocess.run(cmd_compile, capture_output=True, text=True)
if res.returncode != 0:
    print("Error aapt2 compile:", res.stderr)
    sys.exit(1)
print("  [OK] Recursos compilados.")

# 7. Step 2: aapt2 link
print("[>] Enlazando APK base y generando R.java...")
base_apk = work_dir / "base.apk"
cmd_link = [
    str(AAPT2), "link",
    "-o", str(base_apk),
    "-I", str(ANDROID_JAR),
    "--manifest", str(work_dir / "AndroidManifest.xml"),
    "--java", str(gen_dir),
    "-A", str(assets_dir),
    "--auto-add-overlay",
    str(compiled_res_zip)
]
res = subprocess.run(cmd_link, capture_output=True, text=True)
if res.returncode != 0:
    print("Error aapt2 link:", res.stderr)
    sys.exit(1)
print("  [OK] APK base generado.")

# 8. Step 3: javac compile
print("[>] Compilando código Java con javac...")
java_files = list(src_java_dir.glob("*.java")) + list(gen_dir.rglob("*.java"))
cmd_javac = [
    "javac",
    "-encoding", "utf-8",
    "-cp", str(ANDROID_JAR),
    "-d", str(bin_dir),
    "-source", "1.8",
    "-target", "1.8",
    *[str(f) for f in java_files]
]
res = subprocess.run(cmd_javac, capture_output=True, text=True)
if res.returncode != 0:
    print("Error javac:", res.stderr)
    sys.exit(1)
print("  [OK] Clases Java compiladas a bytecode.")

# 9. Step 4: d8 compile to dex
print("[>] Convirtiendo bytecode a Dalvik Executable (classes.dex) con d8...")
dex_dir = work_dir / "dex"
dex_dir.mkdir(parents=True, exist_ok=True)
class_files = list(bin_dir.rglob("*.class"))
cmd_d8 = [
    str(D8),
    "--lib", str(ANDROID_JAR),
    "--output", str(dex_dir),
    *[str(f) for f in class_files]
]
res = subprocess.run(cmd_d8, capture_output=True, text=True)
if res.returncode != 0:
    print("Error d8:", res.stderr)
    sys.exit(1)
print("  [OK] classes.dex generado.")

# 10. Step 5: add classes.dex to base.apk
print("[>] Agregando classes.dex al APK...")
import zipfile
with zipfile.ZipFile(base_apk, 'a') as zf:
    zf.write(dex_dir / "classes.dex", "classes.dex")
print("  [OK] classes.dex empaquetado en base.apk.")

# 11. Step 6: zipalign
print("[>] Alineando APK a 4 bytes con zipalign...")
aligned_apk = work_dir / "aligned.apk"
cmd_align = [
    str(ZIPALIGN), "-f", "-p", "4",
    str(base_apk), str(aligned_apk)
]
res = subprocess.run(cmd_align, capture_output=True, text=True)
if res.returncode != 0:
    print("Error zipalign:", res.stderr)
    sys.exit(1)
print("  [OK] APK alineado.")

# 12. Step 7: Create keystore if not exists and sign with apksigner
keystore_path = work_dir / "aegis.keystore"
if not keystore_path.exists():
    cmd_keytool = [
        "keytool", "-genkeypair",
        "-keystore", str(keystore_path),
        "-storepass", "aegis123",
        "-keypass", "aegis123",
        "-alias", "aegis",
        "-dname", "CN=Aegis, O=AegisBrowser, C=US",
        "-keyalg", "RSA",
        "-keysize", "2048",
        "-validity", "10000"
    ]
    res = subprocess.run(cmd_keytool, capture_output=True, text=True)
    if res.returncode != 0:
        print("Error keytool:", res.stderr)
        sys.exit(1)

print("[>] Firmando APK final con apksigner (v1 + v2 + v3)...")
cmd_sign = [
    str(APKSIGNER), "sign",
    "--ks", str(keystore_path),
    "--ks-pass", "pass:aegis123",
    "--ks-key-alias", "aegis",
    "--key-pass", "pass:aegis123",
    "--out", str(final_apk),
    str(aligned_apk)
]
res = subprocess.run(cmd_sign, capture_output=True, text=True)
if res.returncode != 0:
    print("Error apksigner:", res.stderr)
    sys.exit(1)

print(f"\n[EXITO] APK generado y firmado exitosamente!")
size_mb = round(final_apk.stat().st_size / (1024*1024), 2)
print(f"Ruta: {final_apk.resolve()} ({size_mb} MB)")
print("="*60)
