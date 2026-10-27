#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Lanzador directo GUI sin consola CMD para Aegis Browser.
Al ser .pyw, Windows lo ejecuta con pythonw.exe sin abrir ninguna terminal negra.
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
