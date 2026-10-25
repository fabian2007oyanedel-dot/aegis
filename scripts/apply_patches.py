#!/usr/bin/env python3
# ==============================================================================
# Aegis Browser - Patch Manager
# ==============================================================================
# Aplica secuencialmente todos los parches del directorio patches/ al árbol
# de código fuente de Chromium. Soporta rollback en caso de fallo.
#
# Uso:
#   python scripts/apply_patches.py --src D:\aegis-chromium-src\src
#   python scripts/apply_patches.py --src D:\aegis-chromium-src\src --reverse
#   python scripts/apply_patches.py --src D:\aegis-chromium-src\src --patch 003
# ==============================================================================

import argparse
import subprocess
import sys
import os
from pathlib import Path


# Orden explícito de aplicación de parches (importante: el orden importa)
PATCH_ORDER = [
    "001-strip-telemetry.patch",
    "002-disable-sync.patch",
    "003-vertical-tabs.patch",
    "004-shields-throttle.patch",
]

PATCHES_DIR = Path(__file__).parent.parent / "patches"
APPLIED_LOG = Path(__file__).parent.parent / ".applied_patches.log"


def log(msg: str, level: str = "INFO"):
    colors = {"INFO": "\033[96m", "OK": "\033[92m", "WARN": "\033[93m", "ERR": "\033[91m"}
    reset = "\033[0m"
    prefix = colors.get(level, "") + f"[{level}]" + reset
    print(f"{prefix} {msg}")


def run_git(args: list[str], cwd: Path) -> tuple[int, str, str]:
    """Ejecuta un comando git y retorna (exit_code, stdout, stderr)."""
    result = subprocess.run(
        ["git"] + args,
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return result.returncode, result.stdout, result.stderr


def check_patch(patch_path: Path, src_dir: Path, reverse: bool = False) -> bool:
    """Verifica si un parche puede aplicarse sin errores (dry-run)."""
    args = ["apply", "--check", str(patch_path)]
    if reverse:
        args.append("--reverse")
    code, _, stderr = run_git(args, src_dir)
    if code != 0:
        log(f"  Pre-check falló: {stderr.strip()}", "WARN")
    return code == 0


def apply_patch(patch_path: Path, src_dir: Path, reverse: bool = False) -> bool:
    """Aplica un parche al árbol de Chromium."""
    args = ["apply", "--whitespace=fix", str(patch_path)]
    if reverse:
        args.append("--reverse")
    code, stdout, stderr = run_git(args, src_dir)
    if code != 0:
        log(f"Error aplicando {patch_path.name}:\n{stderr}", "ERR")
        return False
    return True


def get_applied_patches() -> list[str]:
    """Lee el log de parches aplicados."""
    if not APPLIED_LOG.exists():
        return []
    return APPLIED_LOG.read_text(encoding="utf-8").strip().splitlines()


def save_applied_patches(patches: list[str]):
    """Guarda el estado de parches aplicados."""
    APPLIED_LOG.write_text("\n".join(patches), encoding="utf-8")


def apply_all(src_dir: Path, only_patch: str | None = None):
    """Aplica todos los parches en orden."""
    applied = get_applied_patches()
    patches_to_apply = PATCH_ORDER

    if only_patch:
        patches_to_apply = [p for p in PATCH_ORDER if only_patch in p]
        if not patches_to_apply:
            log(f"No se encontró parche con '{only_patch}' en PATCH_ORDER", "ERR")
            sys.exit(1)

    success_count = 0
    fail_count = 0

    for patch_name in patches_to_apply:
        patch_path = PATCHES_DIR / patch_name

        if not patch_path.exists():
            log(f"Parche no encontrado (saltando): {patch_name}", "WARN")
            continue

        if patch_name in applied:
            log(f"Ya aplicado (saltando): {patch_name}", "INFO")
            continue

        log(f"Aplicando: {patch_name}...", "INFO")

        # Dry-run primero
        if not check_patch(patch_path, src_dir):
            log(f"Pre-check falló para {patch_name}. Abortando para evitar corrupción.", "ERR")
            log("Ejecuta con --reverse para deshacer los parches aplicados hasta ahora.", "WARN")
            fail_count += 1
            break

        # Aplicar
        if apply_patch(patch_path, src_dir):
            applied.append(patch_name)
            save_applied_patches(applied)
            log(f"Aplicado correctamente: {patch_name}", "OK")
            success_count += 1
        else:
            log(f"Falló al aplicar: {patch_name}", "ERR")
            fail_count += 1
            break

    print(f"\n  Resumen: {success_count} aplicados, {fail_count} fallidos.")
    if fail_count > 0:
        sys.exit(1)


def reverse_all(src_dir: Path):
    """Deshace todos los parches aplicados en orden inverso."""
    applied = get_applied_patches()
    if not applied:
        log("No hay parches aplicados para revertir.", "WARN")
        return

    reversed_patches = list(reversed(applied))
    success_count = 0

    for patch_name in reversed_patches:
        patch_path = PATCHES_DIR / patch_name
        if not patch_path.exists():
            log(f"Parche no encontrado para revertir: {patch_name}", "WARN")
            continue

        log(f"Revirtiendo: {patch_name}...", "INFO")
        if apply_patch(patch_path, src_dir, reverse=True):
            applied.remove(patch_name)
            save_applied_patches(applied)
            log(f"Revertido: {patch_name}", "OK")
            success_count += 1
        else:
            log(f"Error al revertir {patch_name}. El árbol puede estar en estado inconsistente.", "ERR")
            break

    print(f"\n  Revertidos: {success_count} parches.")


def list_patches():
    """Lista el estado de todos los parches."""
    applied = get_applied_patches()
    print("\n  Estado de parches:")
    print("  " + "─" * 50)
    for patch_name in PATCH_ORDER:
        status = "✅ Aplicado" if patch_name in applied else "⬜ Pendiente"
        exists  = "📄" if (PATCHES_DIR / patch_name).exists() else "❌ (archivo faltante)"
        print(f"  {status}  {exists}  {patch_name}")
    print("  " + "─" * 50)


def main():
    parser = argparse.ArgumentParser(
        description="Aegis Browser - Gestor de parches para Chromium",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--src",     required=True,  help="Ruta al directorio src/ de Chromium")
    parser.add_argument("--reverse", action="store_true", help="Deshacer todos los parches aplicados")
    parser.add_argument("--list",    action="store_true", help="Listar estado de parches")
    parser.add_argument("--patch",   default=None,   help="Aplicar solo el parche que contenga este string")
    args = parser.parse_args()

    src_dir = Path(args.src).resolve()
    if not src_dir.exists():
        log(f"Directorio src no encontrado: {src_dir}", "ERR")
        sys.exit(1)

    if args.list:
        list_patches()
    elif args.reverse:
        log("Modo REVERSE: deshaciendo parches aplicados...", "WARN")
        reverse_all(src_dir)
    else:
        log(f"Aplicando parches al árbol de Chromium en: {src_dir}", "INFO")
        apply_all(src_dir, only_patch=args.patch)


if __name__ == "__main__":
    main()
