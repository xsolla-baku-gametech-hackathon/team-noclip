"""
Xsolla Game Recap - Configuration & Supported Games Database
Handles configuration persistence and games detection rules for both
official releases (Steam, Epic, Xbox) and cracked/standalone executables.
"""

import os
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
CONFIG_FILE = DATA_DIR / "config.json"

# Default supported games with their typical executable names & window titles.
# Both official Steam/Epic versions and cracked/portable/modded names are supported!
DEFAULT_SUPPORTED_GAMES = [
    {
        "id": "stardew_valley",
        "name": "Stardew Valley",
        "genre": "Farming / RPG",
        "executables": [
            "stardew valley.exe",
            "stardewvalley.exe",
            "stardewmoddingapi.exe",
            "smapi.exe"
        ],
        "window_keywords": ["stardew valley", "smapi"],
        "icon": "🌾",
        "theme_color": "#ffb300"
    },
    {
        "id": "undertale",
        "name": "Undertale",
        "genre": "Indie RPG",
        "executables": [
            "undertale.exe",
            "deltarune.exe"
        ],
        "window_keywords": ["undertale", "deltarune"],
        "icon": "❤️",
        "theme_color": "#ff2a5f"
    },
    {
        "id": "hades",
        "name": "Hades",
        "genre": "Roguelike Action",
        "executables": [
            "hades.exe",
            "hades2.exe"
        ],
        "window_keywords": ["hades"],
        "icon": "🔥",
        "theme_color": "#e63946"
    },
    {
        "id": "hollow_knight",
        "name": "Hollow Knight",
        "genre": "Metroidvania",
        "executables": [
            "hollow_knight.exe",
            "hollowknight.exe"
        ],
        "window_keywords": ["hollow knight"],
        "icon": "⚔️",
        "theme_color": "#a8dadc"
    },
    {
        "id": "minecraft",
        "name": "Minecraft",
        "genre": "Sandbox / Survival",
        "executables": [
            "javaw.exe",
            "minecraft.exe",
            "minecraftlauncher.exe",
            "tlauncher.exe",
            "curseforge.exe"
        ],
        "window_keywords": ["minecraft"],
        "icon": "⛏️",
        "theme_color": "#52b788"
    },
    {
        "id": "cyberpunk2077",
        "name": "Cyberpunk 2077",
        "genre": "Open World RPG",
        "executables": [
            "cyberpunk2077.exe"
        ],
        "window_keywords": ["cyberpunk 2077"],
        "icon": "🦾",
        "theme_color": "#fee440"
    },
    {
        "id": "gta5",
        "name": "Grand Theft Auto V",
        "genre": "Action-Adventure",
        "executables": [
            "gta5.exe",
            "playgtav.exe"
        ],
        "window_keywords": ["grand theft auto v", "gta v"],
        "icon": "🚗",
        "theme_color": "#2a9d8f"
    },
    {
        "id": "elden_ring",
        "name": "Elden Ring",
        "genre": "Action RPG",
        "executables": [
            "eldenring.exe",
            "start_protected_game.exe"
        ],
        "window_keywords": ["elden ring"],
        "icon": "💍",
        "theme_color": "#d4af37"
    }
]

DEFAULT_CONFIG = {
    "app_name": "Xsolla Game Recap Overlay",
    "version": "1.0.0-hackathon",
    "hotkey": "Ctrl+Shift+X",
    "hotkey_alt": "Alt+X",
    "toast_duration_ms": 4000,
    "enable_toast_sound": True,
    "scan_interval_sec": 1.5,
    "saas_api_url": "http://localhost:3000/api/recap",
    "saas_api_token": "xsolla-baku-demo-token",
    "auto_capture_screenshots": True,
    "supported_games": DEFAULT_SUPPORTED_GAMES,
    "custom_games": []
}


def ensure_data_dir():
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def load_config() -> dict:
    """Load configuration from JSON or generate default config."""
    ensure_data_dir()
    if not CONFIG_FILE.exists():
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()

    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Merge with defaults in case of missing keys
            for key, val in DEFAULT_CONFIG.items():
                if key not in data:
                    data[key] = val
            return data
    except Exception as err:
        print(f"[Config] Error loading config: {err}. Using defaults.")
        return DEFAULT_CONFIG.copy()


def save_config(config_dict: dict):
    """Save current configuration to JSON."""
    ensure_data_dir()
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config_dict, f, indent=2, ensure_ascii=False)
    except Exception as err:
        print(f"[Config] Error saving config: {err}")


def add_custom_game(name: str, executable: str, window_keyword: str = "", genre: str = "Custom Game"):
    """Easily register any custom or cracked game executable."""
    cfg = load_config()
    clean_exe = executable.strip().lower()
    if not clean_exe.endswith(".exe") and clean_exe:
        clean_exe += ".exe"

    game_entry = {
        "id": f"custom_{len(cfg.get('custom_games', [])) + 1}",
        "name": name.strip(),
        "genre": genre.strip(),
        "executables": [clean_exe] if clean_exe else [],
        "window_keywords": [window_keyword.strip().lower()] if window_keyword else [name.strip().lower()],
        "icon": "🎮",
        "theme_color": "#9d4edd",
        "is_custom": True
    }

    cfg["custom_games"].append(game_entry)
    save_config(cfg)
    return game_entry
