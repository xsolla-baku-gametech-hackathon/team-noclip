"""
Xsolla Game Recap - Configuration Engine
Ultra lightweight settings and paths without static lists or clutter.
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

DATA_DIR = BASE_DIR / "data"
ASSETS_DIR = BUNDLE_DIR / "assets"
CONFIG_FILE = DATA_DIR / "config.json"

DEFAULT_CONFIG = {
    "app_name": "Xsolla Game Recap",
    "version": "1.2.0",
    "hotkey": "Ctrl+Shift+X",
    "hotkey_alt": "Alt+X",
    "toast_duration_ms": 3200,
    "enable_toast_sound": True,
    "scan_interval_sec": 1.0,
    "smart_heuristic_detection": True,
    "saas_api_url": "http://localhost:3000/api/recap",
    "saas_api_token": "xsolla_baku_token",
    "custom_apps": []
}


def ensure_data_dir():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "screenshots").mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "sessions").mkdir(parents=True, exist_ok=True)


def load_config() -> dict:
    ensure_data_dir()
    if not CONFIG_FILE.exists():
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
