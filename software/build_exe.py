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

    icon_path = str(BASE_DIR / "assets" / "xsolla_icon.ico")
    assets_arg = f"{BASE_DIR / 'assets'};assets"

    cmd = [
        sys.executable,
        "-m", "PyInstaller",
        "--noconsole",
        "--name=XsollaGameRecap",
        f"--icon={icon_path}",
        f"--add-data={assets_arg}",
        "--clean",
        "--onefile",
        "main.py"
    ]

    print(f"[Build] Executing: {' '.join(cmd)}")
    res = subprocess.run(cmd)
    if res.returncode == 0:
        import shutil
        built_exe = BASE_DIR / "dist" / "XsollaGameRecap.exe"
        dest_exe = BASE_DIR / "XsollaGameRecap.exe"
        import time
        for attempt in range(10):
            try:
                shutil.copy2(str(built_exe), str(dest_exe))
                print("\n[Build] SUCCESS! Standalone executable generated at:")
                print(f"       {dest_exe}")
                print(f"       {built_exe}\n")
                break
            except PermissionError:
                time.sleep(0.5)
        else:
            print(f"[Build] Warning: Could not overwrite {dest_exe} (file locked). Output is in {built_exe}")
    else:
        print(f"[Build] PyInstaller exited with code {res.returncode}")

if __name__ == "__main__":
    build()
