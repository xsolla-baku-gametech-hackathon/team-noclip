"""
Xsolla Game Recap - Configuration Engine
Stores user recaps and settings locally in Documents/XSOLLA_gamerecap/.
"""

import os
import sys
import json
from pathlib import Path

# Paths
if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys.executable).parent
    BUNDLE_DIR = Path(getattr(sys, "_MEIPASS", BASE_DIR))
else:
    BASE_DIR = Path(__file__).resolve().parent
    BUNDLE_DIR = BASE_DIR

ASSETS_DIR = BUNDLE_DIR / "assets"

# Local player storage in Documents/XSOLLA_gamerecap/
DOCUMENTS_DIR = Path.home() / "Documents"
RECAP_DIR = DOCUMENTS_DIR / "XSOLLA_gamerecap"
SESSIONS_DIR = RECAP_DIR / "sessions"
SCREENSHOTS_DIR = RECAP_DIR / "captures"
CONFIG_FILE = RECAP_DIR / "config.json"

DEFAULT_CONFIG = {
    "app_name": "Xsolla Game Recap",
    "version": "1.3.0",
    "hotkey": "Ctrl+Shift+X",
    "hotkey_alt": "Alt+X",
    "toast_duration_ms": 3000,
    "enable_toast_sound": True,
    "scan_interval_sec": 1.0,
    "smart_heuristic_detection": True,
    "custom_apps": []
}


def ensure_data_dir():
    RECAP_DIR.mkdir(parents=True, exist_ok=True)
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)


def load_config() -> dict:
    ensure_data_dir()
    if not CONFIG_FILE.exists():
        # Check if legacy local data config exists and migrate
        legacy_config = BASE_DIR / "data" / "config.json"
        if legacy_config.exists():
            try:
                with open(legacy_config, "r", encoding="utf-8") as f:
                    legacy_data = json.load(f)
                    save_config(legacy_data)
                    return legacy_data
            except Exception:
                pass
        save_config(DEFAULT_CONFIG)
        return dict(DEFAULT_CONFIG)

    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            for key, val in DEFAULT_CONFIG.items():
                if key not in data:
                    data[key] = val
            return data
    except Exception:
        return dict(DEFAULT_CONFIG)


def save_config(config_dict: dict):
    ensure_data_dir()
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config_dict, f, indent=2, ensure_ascii=False)
    except Exception as err:
        print(f"[Config] Save error: {err}")


def register_custom_app(name: str, executable: str):
    cfg = load_config()
    clean_exe = executable.strip().lower()
    if not clean_exe.endswith(".exe") and clean_exe:
        clean_exe += ".exe"

    entry = {
        "id": name.lower().replace(" ", "_"),
        "name": name.strip(),
        "executable": clean_exe
    }
    custom_list = [c for c in cfg.get("custom_apps", []) if c.get("executable") != clean_exe]
    custom_list.append(entry)
    cfg["custom_apps"] = custom_list
    save_config(cfg)
