#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Lanzador directo de desarrollo para Aegis Browser.
Ejecuta el runtime en vivo desde src/desktop/aegis_app.py sin necesidad de compilar.
"""
import sys
import runpy
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "src" / "desktop"))

target_script = BASE_DIR / "src" / "desktop" / "aegis_app.py"

if __name__ == "__main__":
    runpy.run_path(str(target_script), run_name="__main__")
