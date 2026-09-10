"""
Xsolla Game Recap - PyInstaller Executable Builder
Packages the entire Python application into a standalone Windows .exe.
"""

import os
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

def build():
    print("[Build] Packaging Xsolla Game Recap into standalone .exe...")
    os.chdir(str(BASE_DIR))

    cmd = [
        sys.executable,
        "-m", "PyInstaller",
        "--noconsole",
        "--name=XsollaGameRecap",
        "--clean",
        "--onefile",
        "main.py"
    ]

    print(f"[Build] Executing: {' '.join(cmd)}")
    res = subprocess.run(cmd)
    if res.returncode == 0:
        print("\n[Build] SUCCESS! Standalone executable generated at:")
        print(f"       {BASE_DIR / 'dist' / 'XsollaGameRecap.exe'}\n")
    else:
        print(f"[Build] PyInstaller exited with code {res.returncode}")

if __name__ == "__main__":
    build()
