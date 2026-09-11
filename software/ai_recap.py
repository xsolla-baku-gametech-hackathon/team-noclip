"""
Xsolla Game Recap - AI Recap Generator
Calls the serverless OpenRouter endpoint or local heuristic engine to generate
a structured "Previously On...", status summary, and next objectives for the player.
"""

import os
import json
import requests
from typing import Dict, Any, Optional

from config import RECAP_API_URL


def format_heuristic_recap(analysis: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deterministic recap generator that executes instantaneously without any API calls.
    Used for local testing and as an infallible fallback.
    """
    game_name = analysis.get("game_name", "Your Game")
    player_name = analysis.get("player_name", "Player")
    stats = analysis.get("stats", {})
    priorities = analysis.get("priorities", [])
    low = game_name.lower()

    if "stardew" in low:
        season = stats.get("season", "Summer")
        day = stats.get("day", 18)
        year = stats.get("year", 2)
        gold = stats.get("gold", 12450)
        farm = analysis.get("farm_name", "Misty Farm")
        ready = stats.get("ready_to_harvest", 2)
        dry = stats.get("needs_water", 0)
        dead = stats.get("dead_crops", 1)
        bundles = stats.get("completed_bundles", 18)

        prev = (
            f"You returned to {farm} on {season} {day}, Year {year} with {gold:,}g in savings. "
            f"Your fields are in active cultivation, while Pelican Town and the Community Center await your attention."
        )
        up_to = [
            f"Managing {stats.get('crops_total', 3)} crops across {farm} ({ready} ready for harvest, {dry} dry, {dead} withered).",
            f"Restoring the Community Center with {bundles}/30 bundles completed.",
            f"Fulfilling local Pelican Town requests and tending villager friendships."
        ]
        objs = [
            f"Harvest Ripe Crops: Pick {ready} crops ready today to free up tilled soil.",
            "Clear & Fertilize: Scythe withered crops and plant seasonal seeds.",
            f"Deliver Quest: Check active tasks with Clint and Robin before day's end."
        ]
    elif "undertale" in low or "deltarune" in low:
        lv = stats.get("lv", 1)
        hp = stats.get("hp", 20)
        max_hp = stats.get("max_hp", 20)
        gold = stats.get("gold", 142)
        location = stats.get("location", "Waterfall - Quiet Area")
        route = stats.get("route", "Pacifist Route")

        prev = (
            f"You left {player_name} resting at a glowing SAVE star in {location} with {gold}G. "
            f"Your journey across the Underground remains firmly grounded on the {route}."
        )
        up_to = [
            f"Traversing {location} with {hp}/{max_hp} HP and 0 EXP.",
            f"Adhering to the {route} by sparing monsters in combat.",
            f"Maintaining ties with Papyrus and friends via your cell phone."
        ]
        objs = [
            "Maintain Pacifist Vow: Use ACT and SPARE when encountering cave denizens.",
            f"Explore {location}: Search subterranean alcoves for dimensional chests and items.",
            "Reach the Next Checkpoint: Continue forward to meet Undyne and head toward Hotland."
        ]
    else:
        events = analysis.get("events", [])
        prev = (
            f"You resumed your gameplay session in {game_name}. "
            f"Your journey is in progress with recent achievements and milestones securely preserved."
        )
        up_to = [
            f"Logged {len(events)} in-game actions and visual memories during this run.",
            "Game performance and active session state maintained.",
            "Ready to continue right where you last saved."
        ]
        objs = [
            "Check Mission Objectives: Review active quest log and map markers.",
            "Inspect Gear & Inventory: Verify supplies, ammo, and equipment.",
            "Advance Forward: Continue towards the primary waypoint."
        ]

    raw_text = (
        f"PREVIOUSLY ON {game_name.upper()}:\n"
        f"{prev}\n\n"
        f"WHAT YOU WERE UP TO:\n"
        + "\n".join([f"• {u}" for u in up_to]) + "\n\n"
        f"NEXT OBJECTIVES:\n"
        + "\n".join([f"• {o}" for o in objs])
    )

    return {
        "previously_on": prev,
        "what_you_were_up_to": up_to,
        "next_objectives": objs,
        "raw_text": raw_text,
        "game_name": game_name,
        "player_name": player_name,
        "source": "heuristic_engine"
    }


def generate_recap(save_analysis: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sends the save analysis to the serverless OpenRouter recap endpoint.
    Falls back to the local heuristic engine if the API is unconfigured or offline.
    """
    game_name = save_analysis.get("game_name", "Game")
    player_name = save_analysis.get("player_name", "Player")

    if RECAP_API_URL:
        try:
            resp = requests.post(
                RECAP_API_URL,
                json={
                    "game_name": game_name,
                    "player_name": player_name,
                    "save_data": save_analysis,
                    "events": save_analysis.get("events", [])
                },
                timeout=8
            )
            if resp.status_code == 200:
                data = resp.json()
                if "structured" in data:
                    s = data["structured"]
                    return {
                        "previously_on": s.get("previously_on", ""),
                        "what_you_were_up_to": s.get("what_you_were_up_to", []),
                        "next_objectives": s.get("next_objectives", []),
                        "raw_text": data.get("recap", ""),
                        "game_name": game_name,
                        "player_name": player_name,
                        "source": "openrouter_api"
                    }
                elif "recap" in data:
                    raw = data["recap"]
                    # Extract sections if available or fallback
                    fallback = format_heuristic_recap(save_analysis)
                    fallback["raw_text"] = raw
                    fallback["source"] = "openrouter_api"
                    return fallback
        except Exception as err:
            print(f"[AiRecap] Remote recap call failed ({err}); using heuristic fallback.")

    return format_heuristic_recap(save_analysis)
