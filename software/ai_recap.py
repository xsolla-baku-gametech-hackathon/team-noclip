"""
Xsolla Game Recap - Gameplay Story & Recap Generator
Powered by OpenRouter AI (gpt-4o-mini).
Generates a structured "Previously On...", status summary, and actionable next objectives for any game.
"""

import os
import json
import requests
from typing import Dict, Any, List

from config import RECAP_API_URL

OPENROUTER_ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = "openai/gpt-4o-mini"
OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY") or os.getenv("RECAP_API_KEY") or ""


def format_recap(analysis: Dict[str, Any]) -> Dict[str, Any]:
    """
    Universal local fallback generator that executes instantaneously.
    """
    game_name = analysis.get("game_name", "Your Game")
    player_name = analysis.get("player_name", "Player")
    stats = analysis.get("stats", {})
    events = analysis.get("events", [])

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

    raw_objs = [
        {"title": "Resume Primary Objective", "description": f"Continue your main storyline and quest markers in {game_name}.", "priority": "HIGH"},
        {"title": "Inventory & Resource Check", "description": "Verify weapons, supplies, and equipment before advancing.", "priority": "MEDIUM"},
        {"title": "Record Epic Moments", "description": "Press F11 for instant screenshots or F9 to capture video clips.", "priority": "OPTIONAL"}
    ]
    objs = [f"{o['title']}: {o['description']}" for o in raw_objs]

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
        "raw_objectives": raw_objs,
        "raw_text": raw_text,
        "game_name": game_name,
        "player_name": player_name,
        "source": "recap_engine"
    }


def call_openrouter_direct(game_name: str, player_name: str, save_analysis: Dict[str, Any]) -> Dict[str, Any]:
    """
    Direct OpenRouter AI call if serverless endpoint is offline or unavailable.
    """
    try:
        prompt = (
            f"Player: {player_name}\n"
            f"Game: {game_name}\n"
            f"Session Telemetry: {json.dumps(save_analysis.get('stats', {}))}\n"
            f"Recent Milestones: {json.dumps(save_analysis.get('events', []))}\n"
            "Task: Generate a high-energy, context-aware gaming recap in JSON format with:\n"
            "- previously_on: 2-3 engaging sentences summarizing storyline state where the player left off\n"
            "- what_you_were_up_to: array of 3 distinct bullet strings detailing progress & status\n"
            "- next_objectives: array of 3 objects with 'title', 'description', and 'priority' ('HIGH', 'MEDIUM', 'OPTIONAL')"
        )

        if not OPENROUTER_KEY:
            return {}

        resp = requests.post(
            OPENROUTER_ENDPOINT,
            headers={
                "Authorization": f"Bearer {OPENROUTER_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": DEFAULT_MODEL,
                "response_format": {"type": "json_object"},
                "messages": [
                    {
                        "role": "system",
                        "content": "You are the official Xsolla Game Recap AI engine. Respond ONLY with a valid JSON object."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            },
            timeout=8
        )

        if resp.status_code == 200:
            data = resp.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
            parsed = json.loads(content)
            if "previously_on" in parsed:
                raw_objs = parsed.get("next_objectives", [])
                objs = [
                    f"{o.get('title', 'Objective')}: {o.get('description', '')}" if isinstance(o, dict) else str(o)
                    for o in raw_objs
                ]
                up_to = parsed.get("what_you_were_up_to", [])
                prev = parsed.get("previously_on", "")

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
                    "raw_objectives": raw_objs,
                    "raw_text": raw_text,
                    "game_name": game_name,
                    "player_name": player_name,
                    "source": "openrouter_ai"
                }
    except Exception as err:
        print(f"[AI] Direct OpenRouter call notice: {err}")
    return {}


def generate_recap(save_analysis: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generates a recap for any game using the serverless endpoint or direct OpenRouter fallback.
    """
    game_name = save_analysis.get("game_name", "Game")
    player_name = save_analysis.get("player_name", "Player")

    # 1. Primary path: Call the Vercel serverless function
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
                timeout=7
            )
            if resp.status_code == 200:
                data = resp.json()
                if "structured" in data:
                    s = data["structured"]
                    raw_objs = s.get("raw_objectives") or []
                    objs = s.get("next_objectives") or []
                    return {
                        "previously_on": s.get("previously_on", ""),
                        "what_you_were_up_to": s.get("what_you_were_up_to", []),
                        "next_objectives": objs,
                        "raw_objectives": raw_objs,
                        "raw_text": data.get("recap", ""),
                        "game_name": game_name,
                        "player_name": player_name,
                        "source": "recap_engine"
                    }
        except Exception as err:
            print(f"[AI] Cloud endpoint notice: {err}")

    # 2. Secondary path: Direct OpenRouter call with configured API key
    direct_res = call_openrouter_direct(game_name, player_name, save_analysis)
    if direct_res:
        return direct_res

    # 3. Local fallback if offline
    return format_recap(save_analysis)
