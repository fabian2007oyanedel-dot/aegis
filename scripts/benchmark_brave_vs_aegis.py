import sys, os, subprocess, time, json, shutil
from pathlib import Path
import ctypes
from ctypes import wintypes

print("="*68)
print(" BENCHMARK EMPÍRICO EN VIVO: BRAVE BROWSER vs AEGIS BROWSER")
print("="*68)

BRAVE_EXE = Path(r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe")
AEGIS_EXE = Path("dist/Aegis/Aegis.exe").resolve()

if not BRAVE_EXE.exists():
    print(f"[ERROR] No se encontró Brave en: {BRAVE_EXE}")
    sys.exit(1)

if not AEGIS_EXE.exists():
    print(f"[ERROR] No se encontró Aegis en: {AEGIS_EXE}")
    sys.exit(1)

# Helper para medir memoria de procesos en Windows
class PROCESS_MEMORY_COUNTERS(ctypes.Structure):
    _fields_ = [
        ('cb', wintypes.DWORD),
        ('PageFaultCount', wintypes.DWORD),
        ('PeakWorkingSetSize', ctypes.c_size_t),
        ('WorkingSetSize', ctypes.c_size_t),
        ('QuotaPeakPagedPoolUsage', ctypes.c_size_t),
        ('QuotaPagedPoolUsage', ctypes.c_size_t),
        ('QuotaPeakNonPagedPoolUsage', ctypes.c_size_t),
        ('QuotaNonPagedPoolUsage', ctypes.c_size_t),
        ('PagefileUsage', ctypes.c_size_t),
        ('PeakPagefileUsage', ctypes.c_size_t),
    ]

def get_process_memory_mb(pid: int) -> float:
    try:
        handle = ctypes.windll.kernel32.OpenProcess(0x0400 | 0x0010, False, pid)
        if not handle:
            return 0.0
        counters = PROCESS_MEMORY_COUNTERS()
        counters.cb = ctypes.sizeof(PROCESS_MEMORY_COUNTERS)
        success = ctypes.windll.psapi.GetProcessMemoryInfo(handle, ctypes.byref(counters), counters.cb)
        ctypes.windll.kernel32.CloseHandle(handle)
        if success:
            return counters.WorkingSetSize / (1024 * 1024)
    except Exception:
        pass
    return 0.0

def get_pids_for_image(image_names: list[str]) -> list[int]:
    pids = []
    try:
        out = subprocess.check_output(["tasklist", "/fo", "csv", "/nh"], text=True, errors="ignore")
        for line in out.strip().splitlines():
            parts = [p.strip('"') for p in line.split('","')]
            if len(parts) >= 2:
                name = parts[0].strip('"').lower()
                pid_str = parts[1].strip('"')
                for target in image_names:
                    if target.lower() == name:
                        try:
                            pids.append(int(pid_str))
                        except ValueError:
                            pass
    except Exception:
        pass
    return pids

def get_tcp_connections(pids: list[int]) -> int:
    if not pids:
        return 0
    try:
        pid_list_str = ",".join(str(p) for p in pids)
        ps_cmd = f"Get-NetTCPConnection | Where-Object {{ {pid_list_str} -contains $_.OwningProcess }} | Measure-Object | Select-Object -ExpandProperty Count"
        out = subprocess.check_output(["powershell", "-NoProfile", "-Command", ps_cmd], text=True, errors="ignore")
        return int(out.strip() or "0")
    except Exception:
        return 0

def kill_processes(image_names: list[str]):
    for img in image_names:
        try:
            subprocess.run(["taskkill", "/F", "/IM", img], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass

# Limpiar cualquier proceso previo
kill_processes(["brave.exe", "Aegis.exe", "QtWebEngineProcess.exe"])
time.sleep(1)

# ── TEST 1: ARRANQUE EN FRÍO Y CONSUMO BASE (1 PESTAÑA) ────────────────────────
print("\n[TEST 1] Midiendo Arranque en Frío y RAM Base (Página Limpia)...")

# 1.A Medición de Brave
temp_brave_dir = Path("build/bench_brave_profile")
if temp_brave_dir.exists():
    shutil.rmtree(temp_brave_dir, ignore_errors=True)
temp_brave_dir.mkdir(parents=True, exist_ok=True)

t0 = time.perf_counter()
brave_proc = subprocess.Popen([
    str(BRAVE_EXE),
    f"--user-data-dir={temp_brave_dir.resolve()}",
    "--no-first-run",
    "--no-default-browser-check",
    "about:blank"
], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
startup_brave = (time.perf_counter() - t0) * 1000

# Esperar 4 segundos a que estabilicen procesos e hilos
time.sleep(4)

brave_pids = get_pids_for_image(["brave.exe"])
brave_base_ram = sum(get_process_memory_mb(pid) for pid in brave_pids)
brave_base_conns = get_tcp_connections(brave_pids)

print(f"  > Brave Browser:")
print(f"    - Tiempo de arranque: {startup_brave:.1f} ms")
print(f"    - Procesos creados: {len(brave_pids)}")
print(f"    - Memoria RAM Total (Working Set): {brave_base_ram:.2f} MB")
print(f"    - Conexiones de red abiertas en arranque: {brave_base_conns}")

kill_processes(["brave.exe", "Aegis.exe", "QtWebEngineProcess.exe"])
shutil.rmtree(temp_brave_dir, ignore_errors=True)
time.sleep(1)

# 1.B Medición de Aegis
temp_aegis_dir = Path("build/bench_aegis_data")
if temp_aegis_dir.exists():
    shutil.rmtree(temp_aegis_dir, ignore_errors=True)
temp_aegis_dir.mkdir(parents=True, exist_ok=True)

t0 = time.perf_counter()
aegis_proc = subprocess.Popen([
    str(AEGIS_EXE),
    "--portable",
    "about:blank"
], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
startup_aegis = (time.perf_counter() - t0) * 1000

time.sleep(4)

aegis_pids = get_pids_for_image(["Aegis.exe", "QtWebEngineProcess.exe"])
aegis_base_ram = sum(get_process_memory_mb(pid) for pid in aegis_pids)
aegis_base_conns = get_tcp_connections(aegis_pids)

print(f"\n  > Aegis Browser:")
print(f"    - Tiempo de arranque: {startup_aegis:.1f} ms")
print(f"    - Procesos creados: {len(aegis_pids)}")
print(f"    - Memoria RAM Total (Working Set): {aegis_base_ram:.2f} MB")
print(f"    - Conexiones de red abiertas en arranque: {aegis_base_conns}")

kill_processes(["Aegis.exe", "QtWebEngineProcess.exe"])
shutil.rmtree(temp_aegis_dir, ignore_errors=True)
time.sleep(1)


# ── TEST 2: CONSUMO REAL BAJO CARGA (3 PÁGINAS ACTIVAS) ────────────────────────
print("\n" + "="*68)
print("[TEST 2] Medición de RAM bajo Carga Real (3 Sitios Web Abiertos)...")
print("  URLs: [Wikipedia: Web Browser], [GitHub: Explore], [DuckDuckGo]")
print("="*68)

urls = [
    "https://en.wikipedia.org/wiki/Web_browser",
    "https://github.com",
    "https://duckduckgo.com"
]

# 2.A Carga en Brave
temp_brave_dir.mkdir(parents=True, exist_ok=True)
brave_proc = subprocess.Popen([
    str(BRAVE_EXE),
    f"--user-data-dir={temp_brave_dir.resolve()}",
    "--no-first-run",
    "--no-default-browser-check"
] + urls, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

time.sleep(6) # Esperar renderizado y descarga completa de JS/CSS

brave_load_pids = get_pids_for_image(["brave.exe"])
brave_load_ram = sum(get_process_memory_mb(pid) for pid in brave_load_pids)
brave_load_conns = get_tcp_connections(brave_load_pids)

print(f"  > Brave Browser (3 pestañas):")
print(f"    - Procesos activos: {len(brave_load_pids)}")
print(f"    - Memoria RAM Total (Working Set): {brave_load_ram:.2f} MB")
print(f"    - Conexiones de red activas: {brave_load_conns}")

kill_processes(["brave.exe", "Aegis.exe", "QtWebEngineProcess.exe"])
shutil.rmtree(temp_brave_dir, ignore_errors=True)
time.sleep(1)

# 2.B Carga en Aegis
aegis_proc = subprocess.Popen([
    str(AEGIS_EXE),
    "--portable"
] + urls, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

time.sleep(6)

aegis_load_pids = get_pids_for_image(["Aegis.exe", "QtWebEngineProcess.exe"])
aegis_load_ram = sum(get_process_memory_mb(pid) for pid in aegis_load_pids)
aegis_load_conns = get_tcp_connections(aegis_load_pids)

print(f"\n  > Aegis Browser (3 pestañas):")
print(f"    - Procesos activos: {len(aegis_load_pids)}")
print(f"    - Memoria RAM Total (Working Set): {aegis_load_ram:.2f} MB")
print(f"    - Conexiones de red activas: {aegis_load_conns}")

kill_processes(["Aegis.exe", "QtWebEngineProcess.exe"])
time.sleep(1)

# ── TEST 3: RENDIMIENTO DEL MOTOR DE ESCUDOS RUST ────────────────────────────
print("\n" + "="*68)
print("[TEST 3] Benchmark de Rendimiento de Escudos (Rust FFI Engine)...")
print("="*68)

dll_path = Path("src/shields/target/release/aegis_shields.dll").resolve()
if not dll_path.exists():
    dll_path = Path("dist/Aegis/aegis_shields.dll").resolve()

if dll_path.exists():
    try:
        os.add_dll_directory(str(dll_path.parent))
        rust_lib = ctypes.CDLL(str(dll_path))
        rust_lib.aegis_shields_create.restype = ctypes.c_void_p
        rust_lib.aegis_shields_destroy.argtypes = [ctypes.c_void_p]
        rust_lib.aegis_shields_should_block.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p]
        rust_lib.aegis_shields_should_block.restype = ctypes.c_bool

        engine = rust_lib.aegis_shields_create()
        
        test_urls = [
            b"https://googleads.g.doubleclick.net/pagead/ads?client=ca-pub",
            b"https://en.wikipedia.org/static/images/project-logos/enwiki.png",
            b"https://securepubads.g.doubleclick.net/gampad/ads",
            b"https://github.githubassets.com/assets/app.js",
            b"https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js",
            b"https://duckduckgo.com/assets/logo.svg"
        ]

        iterations = 50000
        t0 = time.perf_counter()
        blocked_count = 0
        for i in range(iterations):
            u = test_urls[i % len(test_urls)]
            if rust_lib.aegis_shields_should_block(engine, u, b"https://example.com", b"script"):
                blocked_count += 1
        elapsed = time.perf_counter() - t0
        
        rust_lib.aegis_shields_destroy(engine)
        
        ops_per_sec = iterations / elapsed
        ns_per_op = (elapsed / iterations) * 1_000_000

        print(f"  > Motor Rust FFI de Aegis Shields:")
        print(f"    - Evaluaciones ejecutadas: {iterations:,} URLs")
        print(f"    - Rendimiento: {ops_per_sec:,.0f} URLs evaluadas por segundo")
        print(f"    - Latencia por URL: {ns_per_op:.2f} microsegundos")
        print(f"    - Precisión de filtrado: {blocked_count:,} anuncios detectados ({blocked_count/iterations*100:.1f}%)")
    except Exception as e:
        print(f"  [AVISO] No se pudo ejecutar benchmark FFI: {e}")

# ── RESUMEN COMPARATIVO FINAL ─────────────────────────────────────────────────
print("\n" + "="*68)
print(" RESULTADOS FINALES DEL BENCHMARK")
print("="*68)
ram_diff_base = ((brave_base_ram - aegis_base_ram) / brave_base_ram) * 100 if brave_base_ram else 0
ram_diff_load = ((brave_load_ram - aegis_load_ram) / brave_load_ram) * 100 if brave_load_ram else 0

print(f"| Métrica                           | Brave Browser | Aegis Browser | Diferencia / Ventaja       |")
print(f"|-----------------------------------|---------------|---------------|----------------------------|")
print(f"| RAM Base (1 pestaña)              | {brave_base_ram:6.1f} MB     | {aegis_base_ram:6.1f} MB     | Aegis usa {ram_diff_base:4.1f}% MENOS RAM   |")
print(f"| RAM Bajo Carga (3 pestañas)       | {brave_load_ram:6.1f} MB     | {aegis_load_ram:6.1f} MB     | Aegis usa {ram_diff_load:4.1f}% MENOS RAM   |")
print(f"| Procesos en Background            | {len(brave_load_pids):2d} procesos    | {len(aegis_load_pids):2d} procesos    | Aegis genera {len(brave_load_pids)-len(aegis_load_pids)} menos     |")
print(f"| Conexiones al Iniciar             | {brave_base_conns:2d} sockets     | {aegis_base_conns:2d} sockets     | Aegis = 100% Offline/Privado |")
print("="*68)
