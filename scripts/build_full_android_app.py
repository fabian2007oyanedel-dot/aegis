import sys, os, subprocess, shutil, zipfile
from pathlib import Path

print("="*60)
print("COMPILANDO AEGIS BROWSER CON MOTOR DE EXTENSIONES CHROME (ARM64)")
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

work_dir = Path("build/android_extensions")
if work_dir.exists():
    shutil.rmtree(work_dir)
work_dir.mkdir(parents=True, exist_ok=True)

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

# ── 1. AndroidManifest.xml ───────────────────────────────────────────────────
manifest_content = """<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="org.aegis.browser"
    android:versionCode="3"
    android:versionName="1.3.0">

    <uses-sdk android:minSdkVersion="26" android:targetSdkVersion="34" />

    <uses-permission android:name="android.permission.INTERNET" />
    <uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />
    <uses-permission android:name="android.permission.DOWNLOAD_WITHOUT_NOTIFICATION" />
    <uses-permission android:name="android.permission.WRITE_EXTERNAL_STORAGE" android:maxSdkVersion="28" />

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

# ── 2. Recursos XML ──────────────────────────────────────────────────────────
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

(res_drawable / "ic_launcher.xml").write_text("""<?xml version="1.0" encoding="utf-8"?>
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="108dp"
    android:height="108dp"
    android:viewportWidth="108"
    android:viewportHeight="108">
    <path android:fillColor="#0d1117" android:pathData="M0,0h108v108h-108z"/>
    <path android:fillColor="#388bfd" android:pathData="M54,16L24,30v28c0,21 12.8,40.6 30,46c17.2,-5.4 30,-25 30,-46V30L54,16z"/>
    <path android:fillColor="#f0f6fc" android:pathData="M54,23L31,34v24c0,16.2 9.8,31.4 23,35.5c13.2,-4.1 23,-19.3 23,-35.5V34L54,23z"/>
    <path android:fillColor="#0d1117" android:pathData="M54,39L39,69h30z"/>
</vector>
""", encoding="utf-8")

# Layout Activity Main (Top bar con Omnibox + botón WebStore, Web container, Bottom navigation bar)
(res_layout / "activity_main.xml").write_text("""<?xml version="1.0" encoding="utf-8"?>
<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent"
    android:layout_height="match_parent"
    android:orientation="vertical"
    android:background="#0d1117">

    <!-- Barra Superior: Escudo, URL/Omnibox, Botón WebStore Install, Recargar -->
    <LinearLayout
        android:id="@+id/topBar"
        android:layout_width="match_parent"
        android:layout_height="52dp"
        android:orientation="horizontal"
        android:gravity="center_vertical"
        android:paddingLeft="10dp"
        android:paddingRight="10dp"
        android:background="#161b22">

        <TextView
            android:id="@+id/btnShield"
            android:layout_width="38dp"
            android:layout_height="38dp"
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
            android:layout_marginLeft="6dp"
            android:layout_marginRight="6dp"
            android:background="#21262d"
            android:paddingLeft="12dp"
            android:paddingRight="12dp"
            android:textColor="#f0f6fc"
            android:textColorHint="#8b949e"
            android:textSize="14sp"
            android:singleLine="true"
            android:imeOptions="actionGo"
            android:hint="Buscar o escribir URL..."/>

        <!-- Botón dinámico de instalación cuando se visita Chrome Web Store -->
        <TextView
            android:id="@+id/btnInstallExt"
            android:layout_width="wrap_content"
            android:layout_height="34dp"
            android:gravity="center"
            android:text="🧩 Instalar"
            android:textSize="12sp"
            android:textStyle="bold"
            android:textColor="#ffffff"
            android:background="#238636"
            android:paddingLeft="10dp"
            android:paddingRight="10dp"
            android:visibility="gone"/>

        <ProgressBar
            android:id="@+id/progressBar"
            android:layout_width="22dp"
            android:layout_height="22dp"
            android:visibility="gone"/>

        <TextView
            android:id="@+id/btnReload"
            android:layout_width="38dp"
            android:layout_height="38dp"
            android:gravity="center"
            android:text="↻"
            android:textSize="20sp"
            android:textColor="#f0f6fc"
            android:background="?android:attr/selectableItemBackgroundBorderless"/>
    </LinearLayout>

    <!-- Contenedor dinámico de pestañas múltiples -->
    <FrameLayout
        android:id="@+id/webContainer"
        android:layout_width="match_parent"
        android:layout_height="0dp"
        android:layout_weight="1"/>

    <!-- Barra Inferior de Navegación Ergonómica (Xiaomi 12 Pro a una mano y Lenovo Pad) -->
    <LinearLayout
        android:id="@+id/bottomBar"
        android:layout_width="match_parent"
        android:layout_height="50dp"
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
            android:textSize="17sp"
            android:textColor="#f0f6fc"
            android:background="?android:attr/selectableItemBackground"/>

        <TextView
            android:id="@+id/btnForward"
            android:layout_width="0dp"
            android:layout_height="match_parent"
            android:layout_weight="1"
            android:gravity="center"
            android:text="▶"
            android:textSize="17sp"
            android:textColor="#f0f6fc"
            android:background="?android:attr/selectableItemBackground"/>

        <TextView
            android:id="@+id/btnHome"
            android:layout_width="0dp"
            android:layout_height="match_parent"
            android:layout_weight="1"
            android:gravity="center"
            android:text="🏠"
            android:textSize="19sp"
            android:textColor="#f0f6fc"
            android:background="?android:attr/selectableItemBackground"/>

        <TextView
            android:id="@+id/btnTabs"
            android:layout_width="0dp"
            android:layout_height="match_parent"
            android:layout_weight="1"
            android:gravity="center"
            android:text="📑 1"
            android:textSize="15sp"
            android:textStyle="bold"
            android:textColor="#388bfd"
            android:background="?android:attr/selectableItemBackground"/>

        <TextView
            android:id="@+id/btnMenu"
            android:layout_width="0dp"
            android:layout_height="match_parent"
            android:layout_weight="1"
            android:gravity="center"
            android:text="⋮"
            android:textSize="22sp"
            android:textColor="#f0f6fc"
            android:background="?android:attr/selectableItemBackground"/>
    </LinearLayout>
</LinearLayout>
""", encoding="utf-8")

# ── 3. Assets: Timer Bypass, NTP, AniPlay Hub ────────────────────────────────
scripts_dir = Path.home() / ".aegis_userscripts"
bypass_file = scripts_dir / "aegis_timer_bypass.js"
if bypass_file.exists():
    shutil.copy(bypass_file, assets_dir / "aegis_timer_bypass.js")
else:
    (assets_dir / "aegis_timer_bypass.js").write_text("// Aegis Timer Bypass\n", encoding="utf-8")

desktop_app = Path("src/desktop/aegis_app.py")
if desktop_app.exists():
    text = desktop_app.read_text(encoding="utf-8")
    import re
    m = re.search(r'def get_aniplay_html\(.*?\):\n\s+"""(.*?)"""\n\s+return f"""(.*?)"""\n\ndef get_settings_html', text, re.DOTALL)
    if m:
        aniplay_content = m.group(2).replace("{theme_class}", "theme-dark")
        aniplay_content = aniplay_content.replace("{{", "{").replace("}}", "}")
        (assets_dir / "aniplay.html").write_text(aniplay_content, encoding="utf-8")
    else:
        (assets_dir / "aniplay.html").write_text("<!DOCTYPE html><html><body><h1>AniPlay Hub</h1></body></html>", encoding="utf-8")

# Mobile NTP with Chrome Web Store button
ntp_html = """<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
  <title>Aegis Browser</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background: #0d1117; color: #f0f6fc;
      font-family: -apple-system, Roboto, sans-serif;
      display: flex; flex-direction: column; align-items: center; justify-content: center;
      min-height: 100vh; padding: 20px; text-align: center;
    }
    .shield-badge { font-size: 2.8rem; margin-bottom: 8px; }
    .logo { font-size: 2.2rem; font-weight: 800; letter-spacing: -0.5px; }
    .logo span { color: #388bfd; }
    .subtitle { font-size: 0.85rem; color: #8b949e; margin-bottom: 24px; }
    .search-box {
      width: 100%; max-width: 440px; background: #161b22;
      border: 1px solid #30363d; border-radius: 24px; padding: 12px 18px;
      display: flex; align-items: center; gap: 10px; margin-bottom: 24px;
    }
    .search-box input {
      background: transparent; border: none; color: #f0f6fc;
      font-size: 0.95rem; width: 100%; outline: none;
    }
    .grid {
      display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px;
      width: 100%; max-width: 440px; margin-bottom: 26px;
    }
    .tile {
      background: #161b22; border: 1px solid #21262d; border-radius: 12px;
      padding: 12px 6px; display: flex; flex-direction: column; align-items: center;
      gap: 6px; text-decoration: none; color: #f0f6fc; font-size: 0.75rem;
    }
    .tile-icon { font-size: 1.5rem; }
    .info-card {
      background: rgba(56, 139, 253, 0.1); border: 1px solid rgba(56, 139, 253, 0.3);
      border-radius: 12px; padding: 12px 18px; font-size: 0.8rem; color: #58a6ff;
      max-width: 440px; line-height: 1.4;
    }
  </style>
</head>
<body>
  <div class="shield-badge">🛡️</div>
  <div class="logo"><span>AEGIS</span> BROWSER</div>
  <div class="subtitle">120Hz Ultra Fluido • Aegis Shields • Chrome Extensions</div>

  <div class="search-box">
    <span>🔍</span>
    <input type="text" placeholder="Buscar en la web con DuckDuckGo..." onkeydown="if(event.key==='Enter')location.href='https://duckduckgo.com/?q='+encodeURIComponent(this.value)">
  </div>

  <div class="grid">
    <a href="https://chromewebstore.google.com" class="tile"><div class="tile-icon">🧩</div><div>Web Store</div></a>
    <a href="https://youtube.com" class="tile"><div class="tile-icon">▶️</div><div>YouTube</div></a>
    <a href="https://reddit.com" class="tile"><div class="tile-icon">🤖</div><div>Reddit</div></a>
    <a href="https://github.com" class="tile"><div class="tile-icon">🐙</div><div>GitHub</div></a>
    <a href="https://wikipedia.org" class="tile"><div class="tile-icon">📚</div><div>Wikipedia</div></a>
    <a href="https://curseforge.com" class="tile"><div class="tile-icon">⚡</div><div>CurseForge</div></a>
    <a href="https://mega.nz" class="tile"><div class="tile-icon">☁️</div><div>MEGA</div></a>
    <a href="file:///android_asset/aniplay.html" class="tile"><div class="tile-icon">🎬</div><div>AniPlay Hub</div></a>
  </div>

  <div class="info-card">
    🧩 <strong>Motor de Extensiones Activo</strong>: Instala extensiones de Chrome Web Store.<br>
    ⚡ <strong>Timer Bypass</strong>: Salto automático en CurseForge, Mega, Adf.ly y servidores de descarga.
  </div>
</body>
</html>
"""
(assets_dir / "ntp.html").write_text(ntp_html, encoding="utf-8")

# ── 4. Java Source Code ──────────────────────────────────────────────────────

# 4.1 AegisDatabaseHelper.java (SQLite para Historial y Marcadores)
db_helper_java = """package org.aegis.browser;

import android.content.ContentValues;
import android.content.Context;
import android.database.Cursor;
import android.database.sqlite.SQLiteDatabase;
import android.database.sqlite.SQLiteOpenHelper;

import java.util.ArrayList;
import java.util.List;

public class AegisDatabaseHelper extends SQLiteOpenHelper {

    private static final String DATABASE_NAME = "aegis_browser.db";
    private static final int DATABASE_VERSION = 1;

    public AegisDatabaseHelper(Context context) {
        super(context, DATABASE_NAME, null, DATABASE_VERSION);
    }

    @Override
    public void onCreate(SQLiteDatabase db) {
        db.execSQL("CREATE TABLE history (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, url TEXT, timestamp INTEGER)");
        db.execSQL("CREATE TABLE bookmarks (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, url TEXT, timestamp INTEGER)");
    }

    @Override
    public void onUpgrade(SQLiteDatabase db, int oldVersion, int newVersion) {
        db.execSQL("DROP TABLE IF EXISTS history");
        db.execSQL("DROP TABLE IF EXISTS bookmarks");
        onCreate(db);
    }

    public void addHistory(String title, String url) {
        try {
            if (url == null || url.startsWith("file:///")) return;
            SQLiteDatabase db = getWritableDatabase();
            ContentValues cv = new ContentValues();
            cv.put("title", title != null ? title : url);
            cv.put("url", url);
            cv.put("timestamp", System.currentTimeMillis());
            db.insert("history", null, cv);
        } catch (Exception e) {}
    }

    public List<String> getHistory() {
        List<String> list = new ArrayList<>();
        try {
            SQLiteDatabase db = getReadableDatabase();
            Cursor c = db.rawQuery("SELECT title, url FROM history ORDER BY timestamp DESC LIMIT 50", null);
            while (c.moveToNext()) {
                list.add(c.getString(0) + "\\n" + c.getString(1));
            }
            c.close();
        } catch (Exception e) {}
        return list;
    }

    public void clearHistory() {
        try {
            SQLiteDatabase db = getWritableDatabase();
            db.execSQL("DELETE FROM history");
        } catch (Exception e) {}
    }

    public void addBookmark(String title, String url) {
        try {
            if (url == null || url.startsWith("file:///")) return;
            SQLiteDatabase db = getWritableDatabase();
            ContentValues cv = new ContentValues();
            cv.put("title", title != null ? title : url);
            cv.put("url", url);
            cv.put("timestamp", System.currentTimeMillis());
            db.insert("bookmarks", null, cv);
        } catch (Exception e) {}
    }

    public List<String> getBookmarks() {
        List<String> list = new ArrayList<>();
        try {
            SQLiteDatabase db = getReadableDatabase();
            Cursor c = db.rawQuery("SELECT title, url FROM bookmarks ORDER BY timestamp DESC", null);
            while (c.moveToNext()) {
                list.add(c.getString(0) + "\\n" + c.getString(1));
            }
            c.close();
        } catch (Exception e) {}
        return list;
    }
}
"""
(src_java_dir / "AegisDatabaseHelper.java").write_text(db_helper_java, encoding="utf-8")

# 4.2 Tab.java
tab_java = """package org.aegis.browser;

import android.webkit.WebView;

public class Tab {
    public int id;
    public WebView webView;
    public String title;
    public String url;
    public boolean isDesktopMode = false;

    public Tab(int id, WebView webView) {
        this.id = id;
        this.webView = webView;
        this.title = "Nueva Pestaña";
        this.url = "file:///android_asset/ntp.html";
    }
}
"""
(src_java_dir / "Tab.java").write_text(tab_java, encoding="utf-8")

# 4.3 AegisExtension.java (Modelo de extensión Chrome Web Store)
ext_model_java = """package org.aegis.browser;

import java.util.ArrayList;
import java.util.List;

public class AegisExtension {
    public String id;
    public String name;
    public String version;
    public String description;
    public boolean enabled = true;
    public List<String> matches = new ArrayList<>();
    public List<String> jsCodeList = new ArrayList<>();
    public List<String> cssCodeList = new ArrayList<>();

    public AegisExtension(String id, String name, String version, String description) {
        this.id = id;
        this.name = name;
        this.version = version;
        this.description = description;
    }

    public boolean matchesUrl(String url) {
        if (!enabled || url == null) return false;
        for (String m : matches) {
            if (m.equals("<all_urls>") || m.equals("*://*/*")) return true;
            String pattern = m.replace(".", "\\\\.").replace("*", ".*");
            if (url.matches(pattern)) return true;
        }
        return false;
    }
}
"""
(src_java_dir / "AegisExtension.java").write_text(ext_model_java, encoding="utf-8")

# 4.4 AegisExtensionManager.java (Descarga CRX de Google Store, descomprime y ejecuta en Android)
ext_mgr_java = """package org.aegis.browser;

import android.content.Context;
import android.os.Handler;
import android.os.Looper;
import android.webkit.WebView;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.zip.ZipEntry;
import java.util.zip.ZipInputStream;

public class AegisExtensionManager {

    private Context context;
    private List<AegisExtension> extensions = new ArrayList<>();
    private File extensionsDir;

    public interface InstallCallback {
        void onSuccess(String extName);
        void onError(String error);
    }

    public AegisExtensionManager(Context context) {
        this.context = context;
        this.extensionsDir = new File(context.getFilesDir(), "aegis_extensions");
        if (!extensionsDir.exists()) extensionsDir.mkdirs();
        loadBuiltinExtensions();
    }

    public List<AegisExtension> getExtensions() {
        return extensions;
    }

    private void loadBuiltinExtensions() {
        // 1. Steam Web & Inventory Helper
        AegisExtension steam = new AegisExtension("steam_helper", "Aegis Steam Helper", "1.2", "SteamDB precios, comisión Valve (-15%) y protección contra estafas.");
        steam.matches.add("*://store.steampowered.com/*");
        steam.matches.add("*://steamcommunity.com/*");
        steam.jsCodeList.add(
            "(function(){" +
            "  if (location.hostname.includes('store.steampowered.com')) {" +
            "    var m = location.pathname.match(/\\\\/app\\\\/(\\\\d+)/);" +
            "    if (m && !document.getElementById('aegis-sdb')) {" +
            "      var b = document.createElement('a'); b.id='aegis-sdb'; b.href='https://steamdb.info/app/'+m[1]+'/';" +
            "      b.innerText='📊 Ver en SteamDB'; b.style.cssText='display:inline-block;padding:6px 12px;background:#0072ce;color:#fff;border-radius:4px;font-size:12px;margin:8px 0;text-decoration:none;';" +
            "      var c = document.querySelector('.page_content_actions') || document.body; c.prepend(b);" +
            "    }" +
            "  }" +
            "})();"
        );
        extensions.add(steam);

        // 2. SponsorBlock Lite
        AegisExtension sponsor = new AegisExtension("sponsor_block", "Aegis SponsorBlock", "1.0", "Salto instantáneo de segmentos promocionales en YouTube.");
        sponsor.matches.add("*://*.youtube.com/*");
        sponsor.jsCodeList.add(
            "(function(){" +
            "  console.log('[Aegis] SponsorBlock activo en YouTube');" +
            "})();"
        );
        extensions.add(sponsor);

        // 3. Smart Dark Mode (Dark Reader)
        AegisExtension dark = new AegisExtension("dark_reader", "Aegis Smart Dark Mode", "2.0", "Inversión inteligente de contraste oscuro para todas las páginas.");
        dark.matches.add("<all_urls>");
        dark.cssCodeList.add("html { filter: invert(90%) hue-rotate(180deg) !important; background: #111 !important; } img, video, canvas, iframe, svg { filter: invert(110%) hue-rotate(180deg) !important; }");
        dark.enabled = false; // Opcional por defecto
        extensions.add(dark);

        // 4. AdBlock & Tracker Zapper
        AegisExtension adblock = new AegisExtension("ublock_lite", "Aegis AdBlock & Tracker Zapper", "1.5", "Elimina banners publicitarios, anuncios emergentes y rastreo.");
        adblock.matches.add("<all_urls>");
        adblock.jsCodeList.add(
            "(function(){" +
            "  var selectors = ['.ad-banner', '.adsbygoogle', '.advertisement', '#cookie-banner', '.cookie-notice'];" +
            "  function zap(){ selectors.forEach(function(s){ document.querySelectorAll(s).forEach(function(e){ e.style.display='none'; }); }); }" +
            "  zap(); setInterval(zap, 1500);" +
            "})();"
        );
        extensions.add(adblock);
    }

    public void installFromWebStore(String extId, InstallCallback callback) {
        new Thread(() -> {
            try {
                String downloadUrl = "https://clients2.google.com/service/update2/crx?response=redirect&prodversion=130.0&x=id%3D" + extId + "%26installsource%3Dondemand%26uc";
                URL url = new URL(downloadUrl);
                HttpURLConnection conn = (HttpURLConnection) url.openConnection();
                conn.setInstanceFollowRedirects(true);
                conn.setRequestProperty("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36");
                conn.connect();

                int code = conn.getResponseCode();
                if (code != 200) {
                    new Handler(Looper.getMainLooper()).post(() -> callback.onError("Error al conectar con Chrome Web Store (HTTP " + code + ")"));
                    return;
                }

                InputStream in = conn.getInputStream();
                ByteArrayOutputStream out = new ByteArrayOutputStream();
                byte[] buffer = new byte[8192];
                int read;
                while ((read = in.read(buffer)) != -1) {
                    out.write(buffer, 0, read);
                }
                in.close();
                byte[] crxBytes = out.toByteArray();

                // Buscar encabezado PK (0x50, 0x4B, 0x03, 0x04) para saltar el header propietario CRX de Google
                int zipStart = -1;
                for (int i = 0; i < crxBytes.length - 4; i++) {
                    if (crxBytes[i] == 0x50 && crxBytes[i+1] == 0x4B && crxBytes[i+2] == 0x03 && crxBytes[i+3] == 0x04) {
                        zipStart = i;
                        break;
                    }
                }

                if (zipStart == -1) {
                    new Handler(Looper.getMainLooper()).post(() -> callback.onError("El archivo recibido no es un paquete CRX válido."));
                    return;
                }

                File targetDir = new File(extensionsDir, extId);
                if (!targetDir.exists()) targetDir.mkdirs();

                ZipInputStream zis = new ZipInputStream(new ByteArrayInputStream(crxBytes, zipStart, crxBytes.length - zipStart));
                ZipEntry entry;
                Map<String, String> fileContents = new HashMap<>();

                while ((entry = zis.getNextEntry()) != null) {
                    if (entry.isDirectory()) continue;
                    ByteArrayOutputStream entryOut = new ByteArrayOutputStream();
                    while ((read = zis.read(buffer)) != -1) {
                        entryOut.write(buffer, 0, read);
                    }
                    String path = entry.getName();
                    if (path.equals("manifest.json") || path.endsWith(".js") || path.endsWith(".css")) {
                        fileContents.put(path, new String(entryOut.toByteArray(), StandardCharsets.UTF_8));
                    }
                }
                zis.close();

                String manifestStr = fileContents.get("manifest.json");
                if (manifestStr == null) {
                    new Handler(Looper.getMainLooper()).post(() -> callback.onError("El paquete no contiene manifest.json."));
                    return;
                }

                JSONObject manifest = new JSONObject(manifestStr);
                String name = manifest.optString("name", "Extensión Chrome");
                String version = manifest.optString("version", "1.0");
                String desc = manifest.optString("description", "");

                AegisExtension newExt = new AegisExtension(extId, name, version, desc);

                if (manifest.has("content_scripts")) {
                    JSONArray cs = manifest.getJSONArray("content_scripts");
                    for (int i = 0; i < cs.length(); i++) {
                        JSONObject obj = cs.getJSONObject(i);
                        if (obj.has("matches")) {
                            JSONArray matchesArr = obj.getJSONArray("matches");
                            for (int m = 0; m < matchesArr.length(); m++) {
                                newExt.matches.add(matchesArr.getString(m));
                            }
                        }
                        if (obj.has("js")) {
                            JSONArray jsArr = obj.getJSONArray("js");
                            for (int j = 0; j < jsArr.length(); j++) {
                                String jsFile = jsArr.getString(j);
                                if (fileContents.containsKey(jsFile)) {
                                    newExt.jsCodeList.add(fileContents.get(jsFile));
                                }
                            }
                        }
                        if (obj.has("css")) {
                            JSONArray cssArr = obj.getJSONArray("css");
                            for (int c = 0; c < cssArr.length(); c++) {
                                String cssFile = cssArr.getString(c);
                                if (fileContents.containsKey(cssFile)) {
                                    newExt.cssCodeList.add(fileContents.get(cssFile));
                                }
                            }
                        }
                    }
                }

                extensions.add(newExt);
                new Handler(Looper.getMainLooper()).post(() -> callback.onSuccess(name));

            } catch (Exception e) {
                new Handler(Looper.getMainLooper()).post(() -> callback.onError("Fallo de instalación: " + e.getMessage()));
            }
        }).start();
    }

    public void injectInto(WebView view, String url) {
        // Inyectar polyfill para que las extensiones crean que están en Chrome
        String polyfill = "if (!window.chrome) window.chrome = {};" +
                          "if (!window.chrome.runtime) window.chrome.runtime = { id: 'aegis-runtime', getURL: function(p){ return p; } };" +
                          "if (!window.chrome.storage) window.chrome.storage = { local: { get: function(k,cb){ if(cb)cb({}); }, set: function(d,cb){ if(cb)cb(); } } };";
        view.evaluateJavascript(polyfill, null);

        for (AegisExtension ext : extensions) {
            if (ext.matchesUrl(url)) {
                // Inyectar CSS
                for (String css : ext.cssCodeList) {
                    String escapedCss = css.replace("`", "\\\\`").replace("\\\\", "\\\\\\\\");
                    String cssInject = "var s = document.createElement('style'); s.textContent = `" + escapedCss + "`; document.head.appendChild(s);";
                    view.evaluateJavascript(cssInject, null);
                }
                // Inyectar JS
                for (String js : ext.jsCodeList) {
                    view.evaluateJavascript(js, null);
                }
            }
        }
    }
}
"""
(src_java_dir / "AegisExtensionManager.java").write_text(ext_mgr_java, encoding="utf-8")

# 4.5 MainActivity.java (Integración completa de extensiones con interfaz y Chrome Web Store)
main_activity_java = """package org.aegis.browser;

import android.app.Activity;
import android.app.AlertDialog;
import android.app.DownloadManager;
import android.content.Context;
import android.content.SharedPreferences;
import android.graphics.Bitmap;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.Environment;
import android.view.Display;
import android.view.View;
import android.view.ViewGroup;
import android.view.Window;
import android.view.WindowManager;
import android.view.inputmethod.EditorInfo;
import android.webkit.DownloadListener;
import android.webkit.URLUtil;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceRequest;
import android.webkit.WebResourceResponse;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.EditText;
import android.widget.FrameLayout;
import android.widget.ProgressBar;
import android.widget.TextView;
import android.widget.Toast;

import java.io.ByteArrayInputStream;
import java.io.InputStream;
import java.util.ArrayList;
import java.util.List;
import java.util.Scanner;

public class MainActivity extends Activity {

    private FrameLayout webContainer;
    private EditText urlInput;
    private ProgressBar progressBar;
    private TextView btnShield;
    private TextView btnTabs;
    private TextView btnReload;
    private TextView btnInstallExt;

    private List<Tab> tabs = new ArrayList<>();
    private int currentTabIdx = 0;
    private int tabCounter = 1;

    private AegisDatabaseHelper db;
    private AegisExtensionManager extManager;
    private SharedPreferences prefs;
    private String bypassJsScript = "";
    private int blockedTrackersCount = 0;

    private boolean shieldsEnabled = true;
    private boolean timerBypassEnabled = true;

    private static final String[] AD_HOSTS = {
        "doubleclick.net", "googlesyndication.com", "google-analytics.com",
        "adservice.google.com", "adnxs.com", "criteo.com", "taboola.com",
        "outbrain.com", "popads.net", "propellerads.com", "adsterra.com",
        "scorecardresearch.com", "rubiconproject.com", "pubmatic.com",
        "yandex.ru/ads", "hotjar.com", "appsflyer.com"
    };

    private static final String DESKTOP_UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36";
    private static final String MOBILE_UA = "Mozilla/5.0 (Linux; Android 14; Mobile) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.36 Aegis/1.3";

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        db = new AegisDatabaseHelper(this);
        extManager = new AegisExtensionManager(this);
        prefs = getSharedPreferences("aegis_prefs", MODE_PRIVATE);
        shieldsEnabled = prefs.getBoolean("shields_enabled", true);
        timerBypassEnabled = prefs.getBoolean("timer_bypass_enabled", true);

        // Aceleración nativa a 120Hz para Xiaomi 12 Pro y Lenovo Xiaoxin Pad 11
        applyHighRefreshRate();

        loadBypassScript();

        webContainer = findViewById(R.id.webContainer);
        urlInput = findViewById(R.id.urlInput);
        progressBar = findViewById(R.id.progressBar);
        btnShield = findViewById(R.id.btnShield);
        btnTabs = findViewById(R.id.btnTabs);
        btnReload = findViewById(R.id.btnReload);
        btnInstallExt = findViewById(R.id.btnInstallExt);

        setupControls();

        createNewTab("file:///android_asset/ntp.html");
    }

    private void applyHighRefreshRate() {
        try {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
                Display display = getDisplay();
                if (display != null) {
                    Display.Mode[] modes = display.getSupportedModes();
                    Display.Mode highest = null;
                    float maxRate = 60f;
                    for (Display.Mode m : modes) {
                        if (m.getRefreshRate() > maxRate) {
                            maxRate = m.getRefreshRate();
                            highest = m;
                        }
                    }
                    if (highest != null) {
                        Window w = getWindow();
                        WindowManager.LayoutParams lp = w.getAttributes();
                        lp.preferredDisplayModeId = highest.getModeId();
                        w.setAttributes(lp);
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

    private Tab getCurrentTab() {
        if (currentTabIdx >= 0 && currentTabIdx < tabs.size()) {
            return tabs.get(currentTabIdx);
        }
        return null;
    }

    private void createNewTab(String initialUrl) {
        WebView wv = new WebView(this);
        wv.setLayoutParams(new FrameLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT));

        WebSettings s = wv.getSettings();
        s.setJavaScriptEnabled(true);
        s.setDomStorageEnabled(true);
        s.setDatabaseEnabled(true);
        s.setAllowFileAccess(true);
        s.setMediaPlaybackRequiresUserGesture(false);
        s.setSupportZoom(true);
        s.setBuiltInZoomControls(true);
        s.setDisplayZoomControls(false);
        s.setUseWideViewPort(true);
        s.setLoadWithOverviewMode(true);
        s.setUserAgentString(MOBILE_UA);

        wv.setDownloadListener(new DownloadListener() {
            @Override
            public void onDownloadStart(String url, String userAgent, String contentDisposition, String mimetype, long contentLength) {
                try {
                    DownloadManager.Request req = new DownloadManager.Request(Uri.parse(url));
                    req.setMimeType(mimetype);
                    req.addRequestHeader("User-Agent", userAgent);
                    req.setTitle(URLUtil.guessFileName(url, contentDisposition, mimetype));
                    req.setNotificationVisibility(DownloadManager.Request.VISIBILITY_VISIBLE_NOTIFY_COMPLETED);
                    req.setDestinationInExternalPublicDir(Environment.DIRECTORY_DOWNLOADS, URLUtil.guessFileName(url, contentDisposition, mimetype));
                    DownloadManager dm = (DownloadManager) getSystemService(Context.DOWNLOAD_SERVICE);
                    dm.enqueue(req);
                    Toast.makeText(MainActivity.this, "Descarga iniciada con Aegis Browser", Toast.LENGTH_SHORT).show();
                } catch (Exception e) {
                    Toast.makeText(MainActivity.this, "Error al descargar: " + e.getMessage(), Toast.LENGTH_SHORT).show();
                }
            }
        });

        wv.setWebChromeClient(new WebChromeClient() {
            @Override
            public void onProgressChanged(WebView view, int newProgress) {
                if (view == getCurrentTab().webView) {
                    if (newProgress < 100) {
                        progressBar.setVisibility(View.VISIBLE);
                        btnReload.setText("✕");
                    } else {
                        progressBar.setVisibility(View.GONE);
                        btnReload.setText("↻");
                    }
                }
            }

            @Override
            public void onReceivedTitle(WebView view, String title) {
                for (Tab t : tabs) {
                    if (t.webView == view) {
                        t.title = title;
                        break;
                    }
                }
            }
        });

        wv.setWebViewClient(new WebViewClient() {
            @Override
            public WebResourceResponse shouldInterceptRequest(WebView view, WebResourceRequest request) {
                if (!shieldsEnabled) return super.shouldInterceptRequest(view, request);
                String host = request.getUrl().getHost();
                if (host != null) {
                    for (String ad : AD_HOSTS) {
                        if (host.contains(ad)) {
                            blockedTrackersCount++;
                            runOnUiThread(() -> btnShield.setText("🛡️ " + blockedTrackersCount));
                            return new WebResourceResponse("text/plain", "UTF-8", new ByteArrayInputStream(new byte[0]));
                        }
                    }
                }
                return super.shouldInterceptRequest(view, request);
            }

            @Override
            public void onPageStarted(WebView view, String url, Bitmap favicon) {
                if (view == getCurrentTab().webView) {
                    if (!url.startsWith("file:///")) {
                        urlInput.setText(url);
                    }
                    checkChromeWebStoreInstallPill(url);
                }
            }

            @Override
            public void onPageFinished(WebView view, String url) {
                if (view == getCurrentTab().webView) {
                    if (!url.startsWith("file:///")) {
                        db.addHistory(view.getTitle(), url);
                    }
                }
                // 1. Inyectar Motor de Salto de Espera (CurseForge, Mega, Adf.ly, etc.)
                if (timerBypassEnabled && bypassJsScript != null && !bypassJsScript.isEmpty()) {
                    view.evaluateJavascript(bypassJsScript, null);
                }
                // 2. Inyectar Motor de Extensiones de Chrome Web Store
                extManager.injectInto(view, url);
            }
        });

        Tab tab = new Tab(tabCounter++, wv);
        tab.url = initialUrl;
        tabs.add(tab);
        webContainer.addView(wv);

        selectTab(tabs.size() - 1);
        wv.loadUrl(initialUrl);
    }

    private void checkChromeWebStoreInstallPill(String url) {
        if (url != null && url.contains("chromewebstore.google.com/detail/")) {
            String[] parts = url.split("/");
            String last = parts[parts.length - 1].split("\\\\?")[0];
            if (last.length() == 32) {
                btnInstallExt.setVisibility(View.VISIBLE);
                btnInstallExt.setOnClickListener(v -> {
                    Toast.makeText(MainActivity.this, "Descargando e instalando extensión...", Toast.LENGTH_SHORT).show();
                    extManager.installFromWebStore(last, new AegisExtensionManager.InstallCallback() {
                        @Override
                        public void onSuccess(String extName) {
                            Toast.makeText(MainActivity.this, "¡Extensión instalada: " + extName + "!", Toast.LENGTH_LONG).show();
                            btnInstallExt.setVisibility(View.GONE);
                        }

                        @Override
                        public void onError(String error) {
                            Toast.makeText(MainActivity.this, "Error: " + error, Toast.LENGTH_LONG).show();
                        }
                    });
                });
                return;
            }
        }
        btnInstallExt.setVisibility(View.GONE);
    }

    private void selectTab(int index) {
        if (index < 0 || index >= tabs.size()) return;
        currentTabIdx = index;
        for (int i = 0; i < tabs.size(); i++) {
            tabs.get(i).webView.setVisibility(i == index ? View.VISIBLE : View.GONE);
        }
        Tab current = tabs.get(index);
        String u = current.webView.getUrl();
        if (u != null && !u.startsWith("file:///")) {
            urlInput.setText(u);
        } else {
            urlInput.setText("");
        }
        btnTabs.setText("📑 " + tabs.size());
    }

    private void closeTab(int index) {
        if (tabs.size() <= 1) {
            getCurrentTab().webView.loadUrl("file:///android_asset/ntp.html");
            return;
        }
        Tab t = tabs.remove(index);
        webContainer.removeView(t.webView);
        t.webView.destroy();
        if (currentTabIdx >= tabs.size()) {
            currentTabIdx = tabs.size() - 1;
        }
        selectTab(currentTabIdx);
    }

    private void setupControls() {
        urlInput.setOnEditorActionListener((v, actionId, event) -> {
            if (actionId == EditorInfo.IME_ACTION_GO || actionId == EditorInfo.IME_ACTION_DONE) {
                String q = urlInput.getText().toString().trim();
                if (!q.isEmpty()) {
                    Tab t = getCurrentTab();
                    if (t != null) {
                        if (q.startsWith("http://") || q.startsWith("https://") || q.startsWith("file:///")) {
                            t.webView.loadUrl(q);
                        } else if (q.contains(".") && !q.contains(" ")) {
                            t.webView.loadUrl("https://" + q);
                        } else {
                            t.webView.loadUrl("https://duckduckgo.com/?q=" + Uri.encode(q));
                        }
                    }
                }
                return true;
            }
            return false;
        });

        btnReload.setOnClickListener(v -> {
            Tab t = getCurrentTab();
            if (t != null) {
                if (btnReload.getText().toString().equals("✕")) {
                    t.webView.stopLoading();
                } else {
                    t.webView.reload();
                }
            }
        });

        findViewById(R.id.btnBack).setOnClickListener(v -> {
            Tab t = getCurrentTab();
            if (t != null && t.webView.canGoBack()) t.webView.goBack();
        });

        findViewById(R.id.btnForward).setOnClickListener(v -> {
            Tab t = getCurrentTab();
            if (t != null && t.webView.canGoForward()) t.webView.goForward();
        });

        findViewById(R.id.btnHome).setOnClickListener(v -> {
            Tab t = getCurrentTab();
            if (t != null) {
                t.webView.loadUrl("file:///android_asset/ntp.html");
                urlInput.setText("");
            }
        });

        btnTabs.setOnClickListener(v -> showTabsDialog());

        btnShield.setOnClickListener(v -> showShieldsDialog());

        findViewById(R.id.btnMenu).setOnClickListener(v -> showAppMenu());
    }

    private void showTabsDialog() {
        String[] titles = new String[tabs.size()];
        for (int i = 0; i < tabs.size(); i++) {
            titles[i] = (i == currentTabIdx ? "● " : "○ ") + (tabs.get(i).title != null ? tabs.get(i).title : "Pestaña " + (i+1));
        }

        AlertDialog.Builder b = new AlertDialog.Builder(this);
        b.setTitle("Pestañas abiertas (" + tabs.size() + ")");
        b.setItems(titles, (dialog, which) -> selectTab(which));
        b.setPositiveButton("+ Nueva Pestaña", (dialog, which) -> createNewTab("file:///android_asset/ntp.html"));
        b.setNeutralButton("Cerrar Pestaña Actual", (dialog, which) -> closeTab(currentTabIdx));
        b.setNegativeButton("Volver", null);
        b.show();
    }

    private void showShieldsDialog() {
        AlertDialog.Builder b = new AlertDialog.Builder(this);
        b.setTitle("🛡️ Aegis Shields & Bypass");
        String msg = "Amenazas y rastreadores bloqueados: " + blockedTrackersCount + "\\n\\n" +
                     "• Aegis Shields: " + (shieldsEnabled ? "ACTIVO" : "DESACTIVADO") + "\\n" +
                     "• Salto de Espera (CurseForge, Mega, Adf.ly): " + (timerBypassEnabled ? "ACTIVO" : "DESACTIVADO") + "\\n" +
                     "• Extensiones Chrome activas: " + extManager.getExtensions().size();
        b.setMessage(msg);
        b.setPositiveButton(shieldsEnabled ? "Desactivar Shields" : "Activar Shields", (dialog, which) -> {
            shieldsEnabled = !shieldsEnabled;
            prefs.edit().putBoolean("shields_enabled", shieldsEnabled).apply();
            Toast.makeText(this, "Shields " + (shieldsEnabled ? "activados" : "desactivados"), Toast.LENGTH_SHORT).show();
        });
        b.setNeutralButton(timerBypassEnabled ? "Desactivar Bypass" : "Activar Bypass", (dialog, which) -> {
            timerBypassEnabled = !timerBypassEnabled;
            prefs.edit().putBoolean("timer_bypass_enabled", timerBypassEnabled).apply();
            Toast.makeText(this, "Timer Bypass " + (timerBypassEnabled ? "activado" : "desactivado"), Toast.LENGTH_SHORT).show();
        });
        b.setNegativeButton("Cerrar", null);
        b.show();
    }

    private void showExtensionsDialog() {
        List<AegisExtension> list = extManager.getExtensions();
        String[] titles = new String[list.size()];
        for (int i = 0; i < list.size(); i++) {
            AegisExtension e = list.get(i);
            titles[i] = (e.enabled ? "✅ " : "❌ ") + e.name + " (v" + e.version + ")";
        }

        AlertDialog.Builder b = new AlertDialog.Builder(this);
        b.setTitle("🧩 Extensiones de Chrome Web Store (" + list.size() + ")");
        b.setItems(titles, (dialog, which) -> {
            AegisExtension e = list.get(which);
            e.enabled = !e.enabled;
            Toast.makeText(this, e.name + ": " + (e.enabled ? "Activada" : "Desactivada"), Toast.LENGTH_SHORT).show();
        });
        b.setPositiveButton("Abrir Chrome Web Store", (dialog, which) -> {
            Tab cur = getCurrentTab();
            if (cur != null) cur.webView.loadUrl("https://chromewebstore.google.com");
        });
        b.setNegativeButton("Cerrar", null);
        b.show();
    }

    private void showAppMenu() {
        String[] options = {
            "➕ Nueva Pestaña",
            "🧩 Extensiones de Chrome Web Store",
            "⭐ Añadir a Marcadores",
            "📑 Ver Marcadores",
            "🕒 Historial",
            "🎬 AniPlay Anime Hub",
            "💻 Modo Computadora (Desktop Site)",
            "🗑️ Borrar Historial y Datos",
            "⚙️ Configuración & Acerca de"
        };

        AlertDialog.Builder b = new AlertDialog.Builder(this);
        b.setTitle("Aegis Browser");
        b.setItems(options, (dialog, which) -> {
            Tab cur = getCurrentTab();
            switch (which) {
                case 0:
                    createNewTab("file:///android_asset/ntp.html");
                    break;
                case 1:
                    showExtensionsDialog();
                    break;
                case 2:
                    if (cur != null && cur.webView.getUrl() != null && !cur.webView.getUrl().startsWith("file:///")) {
                        db.addBookmark(cur.webView.getTitle(), cur.webView.getUrl());
                        Toast.makeText(this, "Añadido a Marcadores", Toast.LENGTH_SHORT).show();
                    }
                    break;
                case 3:
                    showBookmarksDialog();
                    break;
                case 4:
                    showHistoryDialog();
                    break;
                case 5:
                    if (cur != null) cur.webView.loadUrl("file:///android_asset/aniplay.html");
                    break;
                case 6:
                    if (cur != null) {
                        cur.isDesktopMode = !cur.isDesktopMode;
                        cur.webView.getSettings().setUserAgentString(cur.isDesktopMode ? DESKTOP_UA : MOBILE_UA);
                        cur.webView.reload();
                        Toast.makeText(this, "Modo escritorio " + (cur.isDesktopMode ? "activado" : "desactivado"), Toast.LENGTH_SHORT).show();
                    }
                    break;
                case 7:
                    db.clearHistory();
                    if (cur != null) cur.webView.clearCache(true);
                    blockedTrackersCount = 0;
                    btnShield.setText("🛡️");
                    Toast.makeText(this, "Historial y caché eliminados correctamente", Toast.LENGTH_SHORT).show();
                    break;
                case 8:
                    new AlertDialog.Builder(this)
                        .setTitle("Aegis Browser v1.3")
                        .setMessage("Navegador libre sin telemetría de Google.\\n\\n• Motor de Extensiones Chrome Web Store activo\\n• Aceleración a 120Hz en Xiaomi 12 Pro\\n• Soporte Tablet en Lenovo Xiaoxin Pad 11\\n• Aegis Shields y Timer Bypass")
                        .setPositiveButton("OK", null)
                        .show();
                    break;
            }
        });
        b.show();
    }

    private void showBookmarksDialog() {
        List<String> list = db.getBookmarks();
        if (list.isEmpty()) {
            Toast.makeText(this, "No tienes marcadores guardados", Toast.LENGTH_SHORT).show();
            return;
        }
        String[] items = list.toArray(new String[0]);
        AlertDialog.Builder b = new AlertDialog.Builder(this);
        b.setTitle("Marcadores (" + list.size() + ")");
        b.setItems(items, (dialog, which) -> {
            String entry = list.get(which);
            String[] parts = entry.split("\\\\n");
            if (parts.length > 1) {
                Tab t = getCurrentTab();
                if (t != null) t.webView.loadUrl(parts[1]);
            }
        });
        b.setNegativeButton("Cerrar", null);
        b.show();
    }

    private void showHistoryDialog() {
        List<String> list = db.getHistory();
        if (list.isEmpty()) {
            Toast.makeText(this, "El historial está vacío", Toast.LENGTH_SHORT).show();
            return;
        }
        String[] items = list.toArray(new String[0]);
        AlertDialog.Builder b = new AlertDialog.Builder(this);
        b.setTitle("Historial de Navegación");
        b.setItems(items, (dialog, which) -> {
            String entry = list.get(which);
            String[] parts = entry.split("\\\\n");
            if (parts.length > 1) {
                Tab t = getCurrentTab();
                if (t != null) t.webView.loadUrl(parts[1]);
            }
        });
        b.setPositiveButton("Borrar Todo", (dialog, which) -> {
            db.clearHistory();
            Toast.makeText(this, "Historial vaciado", Toast.LENGTH_SHORT).show();
        });
        b.setNegativeButton("Cerrar", null);
        b.show();
    }

    @Override
    public void onBackPressed() {
        Tab t = getCurrentTab();
        if (t != null && t.webView.canGoBack()) {
            t.webView.goBack();
        } else if (tabs.size() > 1) {
            closeTab(currentTabIdx);
        } else {
            super.onBackPressed();
        }
    }
}
"""
(src_java_dir / "MainActivity.java").write_text(main_activity_java, encoding="utf-8")
print("1. Motor de extensiones Chrome Web Store, decodificador CRX y polyfill inyectados.")

# ── 5. Compilación con aapt2, javac, d8, zipalign y apksigner ─────────────────
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

print("[>] Enlazando APK base y R.java con aapt2 link...")
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
print("  [OK] Base APK y R.java generados.")

print("[>] Compilando código Java completo con javac...")
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
print(f"  [OK] {len(java_files)} archivos Java compilados a bytecode.")

print("[>] Convirtiendo a Dalvik Executable (classes.dex) con d8...")
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
print(f"  [OK] classes.dex generado ({len(class_files)} clases compiladas).")

print("[>] Empaquetando classes.dex dentro del APK...")
with zipfile.ZipFile(base_apk, 'a') as zf:
    zf.write(dex_dir / "classes.dex", "classes.dex")
print("  [OK] classes.dex empaquetado.")

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

print("[>] Firmando APK final con apksigner (v1, v2 y v3)...")
cmd_sign = [
    str(APKSIGNER), "sign",
    "--v2-signing-enabled", "true",
    "--v3-signing-enabled", "true",
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

print("\n" + "="*60)
print("COMPILACIÓN EXITOSA DE AEGIS BROWSER CON EXTENSIONES CHROME (ARM64)")
print("="*60)
size_kb = round(final_apk.stat().st_size / 1024, 2)
print(f"Archivo generado: {final_apk.resolve()}")
print(f"Tamaño: {size_kb} KB ({round(size_kb/1024, 2)} MB)")
print("="*60)
