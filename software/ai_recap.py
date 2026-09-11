"""
Xsolla Game Recap - Gameplay Story & Recap Generator
Calls the website's recap endpoint (which holds the real AI service key
server-side) to turn the current save analysis into a "Previously On...",
status summary, and next objectives. No local fallback: if the service
isn't configured or fails, that's shown honestly rather than fabricated.
"""

from typing import Dict, Any

import requests

from config import RECAP_API_URL


def _unavailable(save_analysis: Dict[str, Any], reason: str) -> Dict[str, Any]:
    """Same shape recap_panel.py expects, but honest about not having a
    real recap rather than inventing one."""
    game_name = save_analysis.get("game_name", "Your Game")
    player_name = save_analysis.get("player_name", "Player")
    message = f"Recap unavailable right now: {reason}"
    return {
        "previously_on": message,
        "what_you_were_up_to": [],
        "next_objectives": [],
        "raw_text": message,
        "game_name": game_name,
        "player_name": player_name,
        "source": "unavailable",
    }


def generate_recap(save_analysis: Dict[str, Any]) -> Dict[str, Any]:
    """Generates a recap via the website's /api/recap endpoint. Never
    fabricates content locally — a failure is surfaced as an honest
    'unavailable' message instead of a fake narrative."""
    game_name = save_analysis.get("game_name", "Game")
    player_name = save_analysis.get("player_name", "Player")

    if not RECAP_API_URL:
        return _unavailable(save_analysis, "RECAP_API_URL is not configured.")

    try:
        resp = requests.post(
            RECAP_API_URL,
            json={
                "game_name": game_name,
                "player_name": player_name,
                "save_data": save_analysis,
                "events": save_analysis.get("events", []),
            },
            timeout=15,
        )
    except requests.RequestException as err:
        return _unavailable(save_analysis, str(err))

    if resp.status_code != 200:
        try:
            reason = resp.json().get("error", f"HTTP {resp.status_code}")
        except ValueError:
            reason = f"HTTP {resp.status_code}"
        return _unavailable(save_analysis, reason)

    data = resp.json()
    structured = data.get("structured", {})
    return {
        "previously_on": structured.get("previously_on", ""),
        "what_you_were_up_to": structured.get("what_you_were_up_to", []),
        "next_objectives": structured.get("next_objectives", []),
        "raw_text": data.get("recap", ""),
        "game_name": game_name,
        "player_name": player_name,
        "source": "recap_engine",
    }
