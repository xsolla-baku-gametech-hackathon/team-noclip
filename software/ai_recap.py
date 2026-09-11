"""
Xsolla Game Recap - Gameplay Story & Recap Generator
Generates a structured "Previously On...", status summary, and next objectives for any game.
"""

import requests
from typing import Dict, Any

from config import RECAP_API_URL


def format_recap(analysis: Dict[str, Any]) -> Dict[str, Any]:
    """
    Universal recap generator that executes instantaneously for any game.
    Eliminates resumption friction and tells the player what they've been doing.
    """
    game_name = analysis.get("game_name", "Your Game")
    player_name = analysis.get("player_name", "Player")
    stats = analysis.get("stats", {})
    events = analysis.get("events", [])
    priorities = analysis.get("priorities", [])

    ev_count = stats.get("events_count", len(events))
    screenshots = stats.get("screenshots_count", 0)
    duration = stats.get("duration", "Active Run")

    prev = (
        f"You last played {game_name} with your latest in-game progress securely saved. "
        f"Your active session has {ev_count} key milestones logged, and your game is positioned right at your latest checkpoint ready for action."
    )

    up_to = [
        f"Progressing through {game_name} ({ev_count} recorded session milestones).",
        f"Archived {screenshots} visual memories in your personal capture vault.",
        f"Active gameplay status: {duration} logged in this playthrough."
    ]

    objs = [
        f"Resume Primary Objective: Continue your main storyline and quest markers in {game_name}.",
        "Inventory & Resource Check: Verify weapons, supplies, and equipment before advancing.",
        "Record Epic Moments: Press F11 for instant screenshots or F9 to capture video clips."
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
        "source": "recap_engine"
    }


def generate_recap(save_analysis: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generates a recap for any game using the serverless endpoint with local fallback.
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
                timeout=6
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
                        "source": "recap_engine"
                    }
                elif "recap" in data and data["recap"]:
                    raw = data["recap"]
                    fallback = format_recap(save_analysis)
                    fallback["raw_text"] = raw
                    return fallback
        except Exception:
            pass

    return format_recap(save_analysis)
