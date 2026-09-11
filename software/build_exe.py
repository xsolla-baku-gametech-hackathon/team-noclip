"""
Xsolla Game Recap - PyInstaller Executable Builder
Packages the entire Python application into a standalone Windows .exe with
the official Sol robot mascot icon embedded and Windows shell icon cache refreshed.
"""

import os
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

def build():
    print("[Build] Packaging Xsolla Game Recap into standalone .exe...")
    os.chdir(str(BASE_DIR))

    # 1. Terminate any running instances so target executable is not locked
    try:
        subprocess.run(["taskkill", "/F", "/IM", "XsollaGameRecap.exe"], capture_output=True)
    except Exception:
        pass

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
        import time
        built_exe = BASE_DIR / "dist" / "XsollaGameRecap.exe"
        dest_exe = BASE_DIR / "XsollaGameRecap.exe"
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

        # Invalidate Windows Explorer Shell Icon Cache so the new icon shows up immediately
        try:
            import ctypes
            # SHCNE_ASSOCCHANGED = 0x08000000, SHCNF_IDLIST = 0x0000
            ctypes.windll.shell32.SHChangeNotify(0x08000000, 0x0000, None, None)
            print("[Build] Windows Shell icon cache refreshed successfully (SHCNE_ASSOCCHANGED).")
        except Exception as err:
            print(f"[Build] Note: Could not notify shell of icon change: {err}")
    else:
        print(f"[Build] PyInstaller exited with code {res.returncode}")

if __name__ == "__main__":
    build()
