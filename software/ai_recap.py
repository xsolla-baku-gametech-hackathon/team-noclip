"""
Xsolla Game Recap - AI Recap Generator

Calls the website's serverless endpoint (which holds the OpenRouter key
server-side) to turn a session's local event log into a "Previously On..."
recap. Text-only — no video/frame analysis here, since the session JSON
events (see recap_manager.py) already describe what happened.

IMPORTANT: this desktop app never holds the OpenRouter key itself. Only the
website's Vercel deployment does (set as a Vercel Environment Variable, never
committed) — see website/api/recap.js. That way the key can't be extracted
from the shipped .exe.

Setup:
  1. Deploy the website to Vercel and set OPENROUTER_API_KEY (and optionally
     OPENROUTER_MODEL) as Environment Variables in the Vercel project
     dashboard.
  2. Copy .env.example to .env in this folder and set RECAP_API_URL to your
     deployed site, e.g. https://your-app.vercel.app/api/recap
  3. pip install -r requirements.txt
"""

import json
import sys
from pathlib import Path

import requests

from config import RECAP_API_URL, SESSIONS_DIR


class RecapApiNotConfigured(Exception):
    """Raised when RECAP_API_URL is missing — no silent fake output."""


def generate_recap(session: dict) -> str:
    """Sends the session's event log to the website's recap endpoint and
    returns the generated text.

    Raises RecapApiNotConfigured if no endpoint is set, and requests.HTTPError
    or RuntimeError if the call itself fails — callers should surface the
    real error, never a fabricated result.
    """
    if not RECAP_API_URL:
        raise RecapApiNotConfigured(
            "RECAP_API_URL is not set. Copy software/.env.example to software/.env "
            "and point it at your deployed website's /api/recap endpoint."
        )

    response = requests.post(
        RECAP_API_URL,
        json={"game_name": session.get("game_name"), "events": session.get("events", [])},
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()
    if "error" in data:
        raise RuntimeError(data["error"])
    return data["recap"].strip()


def generate_recap_for_session_id(session_id: str, save: bool = True) -> str:
    """Loads a saved session JSON by id, generates its recap, and optionally saves it back."""
    session_path = Path(SESSIONS_DIR) / f"{session_id}.json"
    if not session_path.exists():
        raise FileNotFoundError(f"No session found at {session_path}")

    with open(session_path, "r", encoding="utf-8") as f:
        session = json.load(f)

    recap_text = generate_recap(session)

    if save:
        session["ai_recap"] = recap_text
        with open(session_path, "w", encoding="utf-8") as f:
            json.dump(session, f, indent=2, ensure_ascii=False)

    return recap_text


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python ai_recap.py <session_id>")
        print(f"Available sessions in {SESSIONS_DIR}:")
        for p in sorted(Path(SESSIONS_DIR).glob("*.json")):
            print(f"  - {p.stem}")
        sys.exit(1)

    try:
        recap = generate_recap_for_session_id(sys.argv[1])
        print("\n--- Previously On... ---")
        print(recap)
        print("------------------------\n")
    except RecapApiNotConfigured as err:
        print(f"[ai_recap] {err}")
        sys.exit(1)
    except requests.HTTPError as err:
        print(f"[ai_recap] Request to recap API failed: {err}")
        sys.exit(1)
