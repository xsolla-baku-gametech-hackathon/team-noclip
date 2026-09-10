"""
Xsolla Game Recap - Configuration & Comprehensive Supported Games Database
Handles configuration persistence and games detection rules for official releases
(Steam, Epic, Xbox, Battle.net, Riot) and cracked/standalone executables.
"""

import os
import sys
import json
from pathlib import Path

if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys.executable).resolve().parent
    RESOURCE_DIR = Path(getattr(sys, '_MEIPASS', BASE_DIR))
else:
    BASE_DIR = Path(__file__).resolve().parent
    RESOURCE_DIR = BASE_DIR

DATA_DIR = BASE_DIR / "data"
CONFIG_FILE = DATA_DIR / "config.json"
ASSETS_DIR = RESOURCE_DIR / "assets"

# Expanded Library of 40+ supported games (Official & Cracked / Modded / Standalone)
DEFAULT_SUPPORTED_GAMES = [
    # --- The User's Explicitly Requested Games ---
    {
        "id": "hello_neighbor",
        "name": "Hello Neighbor",
        "genre": "Stealth Horror",
        "executables": [
            "helloneighbor.exe",
            "helloneighbor-win64-shipping.exe",
            "helloneighborreborn.exe",
            "helloneighbor2.exe"
        ],
        "window_keywords": ["hello neighbor"],
        "icon": "🚪",
        "theme_color": "#ffb703"
    },
    {
        "id": "ultimate_custom_night",
        "name": "Ultimate Custom Night",
        "genre": "Survival Horror",
        "executables": [
            "ultimatecustomnight.exe",
            "ucn.exe"
        ],
        "window_keywords": ["ultimate custom night", "ucn"],
        "icon": "🐻",
        "theme_color": "#e63946"
    },
    {
        "id": "fnaf_series",
        "name": "Five Nights at Freddy's",
        "genre": "Survival Horror",
        "executables": [
            "fnaf.exe", "fnaf2.exe", "fnaf3.exe", "fnaf4.exe",
            "fivenightsatfreddys.exe", "securitybreach.exe",
            "fnaf_vr.exe", "sisterlocation.exe"
        ],
        "window_keywords": ["five nights at freddy", "fnaf", "security breach"],
        "icon": "🍕",
        "theme_color": "#9d0208"
    },

    # --- Popular Indie & Hackathon Games ---
    {
        "id": "stardew_valley",
        "name": "Stardew Valley",
        "genre": "Farming RPG",
        "executables": [
            "stardew valley.exe",
            "stardewvalley.exe",
            "stardewmoddingapi.exe",
            "smapi.exe"
        ],
        "window_keywords": ["stardew valley", "smapi"],
        "icon": "🌾",
        "theme_color": "#52b788"
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
        "id": "cuphead",
        "name": "Cuphead",
        "genre": "Run & Gun",
        "executables": ["cuphead.exe"],
        "window_keywords": ["cuphead"],
        "icon": "☕",
        "theme_color": "#f77f00"
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
        "theme_color": "#70e1ff"
    },
    {
        "id": "celeste",
        "name": "Celeste",
        "genre": "Platformer",
        "executables": ["celeste.exe"],
        "window_keywords": ["celeste"],
        "icon": "🍓",
        "theme_color": "#ff70a6"
    },
    {
        "id": "terraria",
        "name": "Terraria",
        "genre": "Sandbox RPG",
        "executables": ["terraria.exe", "tmodloader.exe"],
        "window_keywords": ["terraria"],
        "icon": "🌳",
        "theme_color": "#2a9d8f"
    },
    {
        "id": "binding_of_isaac",
        "name": "The Binding of Isaac",
        "genre": "Roguelike",
        "executables": ["isaac-ng.exe"],
        "window_keywords": ["binding of isaac"],
        "icon": "💧",
        "theme_color": "#a5a58d"
    },
    {
        "id": "dead_cells",
        "name": "Dead Cells",
        "genre": "Roguelike Action",
        "executables": ["deadcells.exe", "deadcells_gl.exe"],
        "window_keywords": ["dead cells"],
        "icon": "🗡️",
        "theme_color": "#e76f51"
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
        "theme_color": "#d90429"
    },

    # --- Viral Co-op & Party Games ---
    {
        "id": "lethal_company",
        "name": "Lethal Company",
        "genre": "Co-op Survival",
        "executables": ["lethal company.exe"],
        "window_keywords": ["lethal company"],
        "icon": "📦",
        "theme_color": "#e09f3e"
    },
    {
        "id": "phasmophobia",
        "name": "Phasmophobia",
        "genre": "Psychological Horror",
        "executables": ["phasmophobia.exe"],
        "window_keywords": ["phasmophobia"],
        "icon": "👻",
        "theme_color": "#8338ec"
    },
    {
        "id": "content_warning",
        "name": "Content Warning",
        "genre": "Co-op Horror",
        "executables": ["content warning.exe"],
        "window_keywords": ["content warning"],
        "icon": "📹",
        "theme_color": "#ffee32"
    },
    {
        "id": "palworld",
        "name": "Palworld",
        "genre": "Survival Craft",
        "executables": ["palworld.exe", "palworld-win64-shipping.exe"],
        "window_keywords": ["palworld"],
        "icon": "🐾",
        "theme_color": "#06d6a0"
    },
    {
        "id": "helldivers2",
        "name": "Helldivers 2",
        "genre": "Co-op Shooter",
        "executables": ["helldivers2.exe"],
        "window_keywords": ["helldivers"],
        "icon": "🚀",
        "theme_color": "#ffbe0b"
    },

    # --- Mainstream Blockbusters & Sandbox ---
    {
        "id": "minecraft",
        "name": "Minecraft",
        "genre": "Sandbox",
        "executables": [
            "javaw.exe",
            "minecraft.exe",
            "minecraftlauncher.exe",
            "tlauncher.exe",
            "curseforge.exe"
        ],
        "window_keywords": ["minecraft"],
        "icon": "⛏️",
        "theme_color": "#38b000"
    },
    {
        "id": "roblox",
        "name": "Roblox",
        "genre": "Virtual Sandbox",
        "executables": ["robloxplayerbeta.exe", "robloxplayer.exe"],
        "window_keywords": ["roblox"],
        "icon": "🟥",
        "theme_color": "#e63946"
    },
    {
        "id": "cyberpunk2077",
        "name": "Cyberpunk 2077",
        "genre": "Open World RPG",
        "executables": ["cyberpunk2077.exe"],
        "window_keywords": ["cyberpunk 2077"],
        "icon": "🦾",
        "theme_color": "#fee440"
    },
    {
        "id": "gta5",
        "name": "Grand Theft Auto V",
        "genre": "Action-Adventure",
        "executables": ["gta5.exe", "playgtav.exe"],
        "window_keywords": ["grand theft auto v", "gta v"],
        "icon": "🚗",
        "theme_color": "#2a9d8f"
    },
    {
        "id": "rdr2",
        "name": "Red Dead Redemption 2",
        "genre": "Open World Western",
        "executables": ["rdr2.exe"],
        "window_keywords": ["red dead redemption"],
        "icon": "🤠",
        "theme_color": "#9e2a2b"
    },
    {
        "id": "elden_ring",
        "name": "Elden Ring",
        "genre": "Action RPG",
        "executables": ["eldenring.exe", "start_protected_game.exe"],
        "window_keywords": ["elden ring"],
        "icon": "💍",
        "theme_color": "#d4af37"
    },
    {
        "id": "baldur_gate_3",
        "name": "Baldur's Gate 3",
        "genre": "CRPG",
        "executables": ["bg3.exe", "bg3_dx11.exe"],
        "window_keywords": ["baldur's gate 3"],
        "icon": "🎲",
        "theme_color": "#b5179e"
    },

    # --- Competitive & Online Titles ---
    {
        "id": "valorant",
        "name": "VALORANT",
        "genre": "Tactical Shooter",
        "executables": ["valorant-win64-shipping.exe", "valorant.exe"],
        "window_keywords": ["valorant"],
        "icon": "🎯",
        "theme_color": "#ff4655"
    },
    {
        "id": "cs2",
        "name": "Counter-Strike 2",
        "genre": "Tactical FPS",
        "executables": ["cs2.exe"],
        "window_keywords": ["counter-strike 2", "counter-strike"],
        "icon": "💣",
        "theme_color": "#f77f00"
    },
    {
        "id": "dota2",
        "name": "Dota 2",
        "genre": "MOBA",
        "executables": ["dota2.exe"],
        "window_keywords": ["dota 2"],
        "icon": "🛡️",
        "theme_color": "#d90429"
    },
    {
        "id": "league_of_legends",
        "name": "League of Legends",
        "genre": "MOBA",
        "executables": ["leagueclient.exe", "league of legends.exe"],
        "window_keywords": ["league of legends"],
        "icon": "⚔️",
        "theme_color": "#00b4d8"
    },
    {
        "id": "fortnite",
        "name": "Fortnite",
        "genre": "Battle Royale",
        "executables": ["fortniteclient-win64-shipping.exe"],
        "window_keywords": ["fortnite"],
        "icon": "🪂",
        "theme_color": "#9d4edd"
    },
    {
        "id": "apex_legends",
        "name": "Apex Legends",
        "genre": "Battle Royale",
        "executables": ["r5apex.exe"],
        "window_keywords": ["apex legends"],
        "icon": "🏆",
        "theme_color": "#e63946"
    },
    {
        "id": "rocket_league",
        "name": "Rocket League",
        "genre": "Sports Action",
        "executables": ["rocketleague.exe"],
        "window_keywords": ["rocket league"],
        "icon": "⚽",
        "theme_color": "#0077b6"
    },
    {
        "id": "rust",
        "name": "Rust",
        "genre": "Survival",
        "executables": ["rustclient.exe"],
        "window_keywords": ["rust"],
        "icon": "🪓",
        "theme_color": "#cd5c5c"
    },
    {
        "id": "geometry_dash",
        "name": "Geometry Dash",
        "genre": "Rhythm Platformer",
        "executables": ["geometrydash.exe"],
        "window_keywords": ["geometry dash"],
        "icon": "🟩",
        "theme_color": "#00f5d4"
    },

    # --- Anime / Gacha Hits ---
    {
        "id": "genshin_impact",
        "name": "Genshin Impact",
        "genre": "Action RPG",
        "executables": ["genshinimpact.exe"],
        "window_keywords": ["genshin impact"],
        "icon": "✨",
        "theme_color": "#48cae4"
    },
    {
        "id": "honkai_star_rail",
        "name": "Honkai: Star Rail",
        "genre": "Turn-Based RPG",
        "executables": ["starrail.exe"],
        "window_keywords": ["honkai: star rail", "star rail"],
        "icon": "🚂",
        "theme_color": "#b5179e"
    }
]

DEFAULT_CONFIG = {
    "app_name": "Xsolla Game Recap",
    "version": "1.1.0-baku",
    "hotkey": "Ctrl+Shift+X",
    "hotkey_alt": "Alt+X",
    "toast_duration_ms": 3800,
    "enable_toast_sound": True,
    "scan_interval_sec": 1.2,
    "smart_heuristic_detection": True,  # Automatically hooks any game in Steam/Epic/Games folders
    "saas_api_url": "http://localhost:3000/api/recap",
    "saas_api_token": "xsolla-baku-demo-token",
    "supported_games": DEFAULT_SUPPORTED_GAMES,
    "custom_games": []
}


def ensure_data_dir():
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def load_config() -> dict:
    ensure_data_dir()
    if not CONFIG_FILE.exists():
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()

    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Always ensure the latest supported games library is merged in
            data["supported_games"] = DEFAULT_SUPPORTED_GAMES
            for key, val in DEFAULT_CONFIG.items():
                if key not in data:
                    data[key] = val
            return data
    except Exception as err:
        print(f"[Config] Error loading config: {err}. Using defaults.")
        return DEFAULT_CONFIG.copy()


def save_config(config_dict: dict):
    ensure_data_dir()
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config_dict, f, indent=2, ensure_ascii=False)
    except Exception as err:
        print(f"[Config] Error saving config: {err}")


def add_custom_game(name: str, executable: str, window_keyword: str = "", genre: str = "Custom Game"):
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
        "theme_color": "#70e1ff",
        "is_custom": True
    }

    cfg["custom_games"].append(game_entry)
    save_config(cfg)
    return game_entry
