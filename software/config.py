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

# Loads software/.env once, here, so every module that imports config gets
# these without each needing its own load_dotenv() call. .env is gitignored —
# never committed. See .env.example for the fields this app reads.
try:
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / ".env")
except ImportError:
    pass

# The desktop app calls this cloud recap service endpoint (a serverless function
# that generates recaps server-side). Set this after deploying the website.
RECAP_API_URL = os.getenv("RECAP_API_URL", "https://team-noclip.vercel.app/api/recap")

# Where the login button opens in the browser.
WEBSITE_LOGIN_URL = os.getenv("WEBSITE_LOGIN_URL", "https://team-noclip.vercel.app/login")

# Base origin of the deployed website (e.g. https://your-app.vercel.app),
# used for syncing sessions and media to your account after login (see
# sync_client.py). Requires a database configured on the website side
# (see website/api/_lib/db.js).
WEBSITE_API_URL = os.getenv("WEBSITE_API_URL", "https://team-noclip.vercel.app")

# Local player storage in Documents/XSOLLA_gamerecap/
DOCUMENTS_DIR = Path.home() / "Documents"
RECAP_DIR = DOCUMENTS_DIR / "XSOLLA_gamerecap"
SESSIONS_DIR = RECAP_DIR / "sessions"
RECORDINGS_DIR = RECAP_DIR / "recordings"  # Dedicated recordings & captures folder
SCREENSHOTS_DIR = RECORDINGS_DIR           # Unified under recordings directory
CONFIG_FILE = RECAP_DIR / "config.json"

# Cloud Settings endpoint (can sync between desktop app & website dashboard)
SETTINGS_API_URL = os.getenv("SETTINGS_API_URL", "https://team-noclip.vercel.app/api/settings")

DEFAULT_CONFIG = {
    "app_name": "Xsolla Game Recap",
    "version": "1.3.0",
    "hotkey": "Ctrl+Shift+X",
    "hotkey_alt": "Alt+X",
    "hotkey_record": "F9",
    "hotkey_capture": "F11",
    "toast_duration_ms": 3000,
    "enable_toast_sound": True,
    "scan_interval_sec": 1.0,
    "smart_heuristic_detection": True,
    "recording_fps": 30,
    "video_format": "mp4",
    "include_gamebar_in_recording": True,
    "custom_apps": []
}


def ensure_data_dir():
    RECAP_DIR.mkdir(parents=True, exist_ok=True)
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    RECORDINGS_DIR.mkdir(parents=True, exist_ok=True)
    # Also maintain legacy captures dir if exists
    (RECAP_DIR / "captures").mkdir(parents=True, exist_ok=True)


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


def get_recording_settings() -> dict:
    """Returns the current video recording and capture configuration."""
    cfg = load_config()
    return {
        "recording_fps": int(cfg.get("recording_fps", 30)),
        "video_format": str(cfg.get("video_format", "mp4")).lower(),
        "include_gamebar_in_recording": bool(cfg.get("include_gamebar_in_recording", True))
    }


def update_recording_settings(settings: dict) -> dict:
    """Updates and saves recording settings."""
    cfg = load_config()
    if "recording_fps" in settings:
        try:
            cfg["recording_fps"] = max(10, min(120, int(settings["recording_fps"])))
        except (ValueError, TypeError):
            pass
    if "video_format" in settings:
        fmt = str(settings["video_format"]).lower().strip()
        if fmt in ("mp4", "avi", "mkv"):
            cfg["video_format"] = fmt
    if "include_gamebar_in_recording" in settings:
        cfg["include_gamebar_in_recording"] = bool(settings["include_gamebar_in_recording"])
    save_config(cfg)
    return get_recording_settings()


def sync_settings_with_cloud(user_token: str = "") -> dict:
    """
    Syncs recording settings with the website dashboard API endpoint.
    Sends local settings and receives updated cloud settings.
    """
    import requests
    local_settings = get_recording_settings()
    try:
        headers = {"Content-Type": "application/json"}
        if user_token:
            headers["Authorization"] = f"Bearer {user_token}"

        resp = requests.post(
            SETTINGS_API_URL,
            json={"settings": local_settings},
            headers=headers,
            timeout=5
        )
        if resp.status_code == 200:
            data = resp.json()
            cloud_settings = data.get("settings", {})
            if cloud_settings:
                return update_recording_settings(cloud_settings)
    except Exception as err:
        print(f"[SettingsSync] Cloud sync skipped/offline: {err}")
    return local_settings


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


def set_window_capture_affinity(window, exclude_from_capture: bool = True) -> bool:
    """
    Controls whether a window is excluded from screen recordings and screenshots.
    - If exclude_from_capture is True: sets WDA_EXCLUDEFROMCAPTURE (0x00000011).
    - If exclude_from_capture is False: sets WDA_NONE (0x00000000), allowing the window
      to be captured in recordings and screenshots.
    """
    try:
        import ctypes
        window.update_idletasks()
        hwnd = window.winfo_id()
        parent = ctypes.windll.user32.GetParent(hwnd)
        target_hwnd = parent if parent else hwnd

        affinity = 0x00000011 if exclude_from_capture else 0x00000000
        res = ctypes.windll.user32.SetWindowDisplayAffinity(target_hwnd, affinity)
        if not res and hwnd != target_hwnd:
            res = ctypes.windll.user32.SetWindowDisplayAffinity(hwnd, affinity)
        return bool(res)
    except Exception as err:
        print(f"[WindowAffinity] Error setting capture affinity: {err}")
        return False


def make_window_invisible_to_capture(window) -> bool:
    """Excludes window from screen capture/recording."""
    return set_window_capture_affinity(window, exclude_from_capture=True)


def make_window_visible_to_capture(window) -> bool:
    """Includes window in screen capture/recording."""
    return set_window_capture_affinity(window, exclude_from_capture=False)

