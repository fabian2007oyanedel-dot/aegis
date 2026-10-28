#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Lanzador de Discord Ultra-Light impulsado por Aegis.
Ejecuta Discord en Modo App independiente sin compilar nada (consumo ~40-65MB RAM, 0% CPU en reposo).
"""
import sys
import runpy
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "src" / "desktop"))

if "--discord" not in sys.argv and not any(a.startswith("--app=") for a in sys.argv):
    sys.argv.append("--discord")

target_script = BASE_DIR / "src" / "desktop" / "aegis_app.py"

if __name__ == "__main__":
    runpy.run_path(str(target_script), run_name="__main__")
