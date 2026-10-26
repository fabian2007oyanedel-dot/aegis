import os
import sys
import shutil
import subprocess
import zipfile
from pathlib import Path

print("=" * 65)
print("COMPILANDO AEGIS BROWSER: INSTALADOR Y VERSIÓN PORTABLE (PC)")
print("=" * 65)

ROOT_DIR = Path(__file__).resolve().parent.parent
DIST_DIR = ROOT_DIR / "dist"
AEGIS_DIR = DIST_DIR / "Aegis"
PORTABLE_DIR = DIST_DIR / "Aegis-Portable"
PORTABLE_ZIP = DIST_DIR / "Aegis-v1.3.5-Portable.zip"
INSTALLER_DIR = DIST_DIR / "installer"
ISCC_PATH = Path(r"C:\Users\PC\AppData\Local\Programs\Inno Setup 6\ISCC.exe")

# ── 1. Recompilar ejecutable con PyInstaller ──────────────────────────────────
print("\n[1/3] Compilando ejecutable nativo de Aegis con PyInstaller...")
cmd_pyinstaller = [
    sys.executable, "-m", "PyInstaller",
    "--noconfirm",
    "--clean",
    "Aegis.spec"
]
res = subprocess.run(cmd_pyinstaller, cwd=str(ROOT_DIR))
if res.returncode != 0:
    print("[ERROR] Falló la compilación de PyInstaller.")
    sys.exit(1)

exe_path = AEGIS_DIR / "Aegis.exe"
if not exe_path.exists():
    print(f"[ERROR] No se encontró el ejecutable generado en: {exe_path}")
    sys.exit(1)
print(f"  [OK] Ejecutable generado exitosamente: {exe_path}")

# ── 2. Generar Paquete Portable (Aegis-v1.3.5-Portable.zip) ───────────────────
print("\n[2/3] Empaquetando versión Portable (100% autocontenida)...")
if PORTABLE_DIR.exists():
    shutil.rmtree(PORTABLE_DIR)

shutil.copytree(AEGIS_DIR, PORTABLE_DIR)

# Crear archivo testigo de portabilidad y carpeta data
(PORTABLE_DIR / "portable.dat").write_text("Aegis Portable Mode Active\n", encoding="utf-8")
(PORTABLE_DIR / "data").mkdir(parents=True, exist_ok=True)
(PORTABLE_DIR / "LEEME_PORTABLE.txt").write_text("""================================================================================
           🛡️ AEGIS BROWSER v1.3.5 — EDICIÓN PORTABLE OFICIAL (PC)
================================================================================

Esta versión es 100% autocontenida y lista para ejecutarse desde cualquier
directorio o memoria USB sin necesidad de instalación.

CARACTERÍSTICAS DE LA VERSIÓN PORTABLE:
• Cero huella en el sistema: Todo se almacena localmente en la carpeta 'data/'.
• Historial, marcadores, configuración y cookies quedan aislados dentro de este paquete.
• Incluye Aegis Shields (bloqueador de anuncios y rastreadores integrado).
• Salto de temporizadores universal (CurseForge, Mega, Adf.ly, etc.).
• Importador directo desde Brave Browser (Menú ⋮ -> Importar datos de Brave).

USO:
Simplemente ejecuta 'Aegis.exe'. Puedes mover esta carpeta donde prefieras.
================================================================================
""", encoding="utf-8")

if PORTABLE_ZIP.exists():
    PORTABLE_ZIP.unlink()

print(f"  [>] Comprimiendo {PORTABLE_DIR.name} en {PORTABLE_ZIP.name}...")
with zipfile.ZipFile(PORTABLE_ZIP, "w", zipfile.ZIP_DEFLATED) as zip_out:
    for file_path in PORTABLE_DIR.rglob("*"):
        if file_path.is_file():
            arcname = file_path.relative_to(DIST_DIR)
            zip_out.write(file_path, arcname)

size_mb = round(PORTABLE_ZIP.stat().st_size / (1024 * 1024), 2)
print(f"  [OK] Versión Portable creada: {PORTABLE_ZIP}")
print(f"       Tamaño comprimido: {size_mb} MB")

# ── 3. Compilar Instalador Oficial con Inno Setup ─────────────────────────────
print("\n[3/3] Compilando instalador oficial de Windows (Inno Setup)...")
INSTALLER_DIR.mkdir(parents=True, exist_ok=True)
iss_file = ROOT_DIR / "installer" / "aegis_setup.iss"

if not ISCC_PATH.exists():
    print(f"[WARN] Inno Setup no encontrado en {ISCC_PATH}.")
    print("      Saltando compilación del instalador .exe.")
else:
    cmd_inno = [str(ISCC_PATH), str(iss_file)]
    res_inno = subprocess.run(cmd_inno, cwd=str(ROOT_DIR / "installer"))
    if res_inno.returncode == 0:
        setup_exe = INSTALLER_DIR / "Aegis-Setup-v1.3.5.exe"
        if setup_exe.exists():
            setup_size_mb = round(setup_exe.stat().st_size / (1024 * 1024), 2)
            print(f"  [OK] Instalador compilado con éxito: {setup_exe}")
            print(f"       Tamaño del instalador: {setup_size_mb} MB")
        else:
            print("[WARN] Inno Setup finalizó pero el archivo setup no se encontró.")
    else:
        print("[ERROR] Error compilando el instalador con Inno Setup.")

print("\n" + "=" * 65)
print("¡PROCESO COMPLETADO EXITOSAMENTE!")
print("=" * 65)
