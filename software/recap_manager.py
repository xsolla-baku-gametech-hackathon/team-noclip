"""
Xsolla Game Recap - Local Session Engine
Stores all player recap data locally in Documents/XSOLLA_gamerecap/.
No cloud dependencies, no mock events, no emojis.
"""

import sys
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import time
import json
import datetime
from pathlib import Path
from typing import Dict, Optional

from config import SESSIONS_DIR, SCREENSHOTS_DIR, ensure_data_dir


class RecapManager:
    def __init__(self):
        ensure_data_dir()
        self.current_session: Optional[Dict] = None

    def start_session(self, game: Dict, pid: int, window_title: str):
        """Initializes a live session for the newly hooked game."""
        ensure_data_dir()
        game_id = game.get("id", "game")
        session_id = f"{game_id}_{int(time.time())}"
        now_time = datetime.datetime.now()

        self.current_session = {
            "session_id": session_id,
            "game_id": game_id,
            "game_name": game.get("name", "Active Game"),
            "pid": pid,
            "window_title": window_title,
            "started_at": now_time.isoformat(),
            "start_timestamp": time.time(),
            "ended_at": None,
            "duration_seconds": 0,
            "events": [
                {
                    "timestamp": now_time.strftime("%H:%M:%S"),
                    "text": f"Game Hooked: {game.get('name')} (PID {pid})",
                    "type": "system"
                }
            ]
        }

        print(f"[Recap] Session started: {session_id}")
        self._save_current_session()

    def add_event(self, text: str, event_type: str = "system") -> Dict:
        """Appends a timestamped event to the active session."""
        if not self.current_session:
            return {}

        evt = {
            "timestamp": datetime.datetime.now().strftime("%H:%M:%S"),
            "text": text,
            "type": event_type
        }
        self.current_session["events"].append(evt)
        self._save_current_session()
        print(f"[Recap] Event: {text}")
        return evt

    def end_session(self) -> Optional[Dict]:
        """Finalizes and persists the active session locally in Documents/XSOLLA_gamerecap/."""
        if not self.current_session:
            return None

        self.current_session["ended_at"] = datetime.datetime.now().isoformat()
        elapsed = int(time.time() - self.current_session["start_timestamp"])
        self.current_session["duration_seconds"] = elapsed
        self.add_event("Session concluded", event_type="system")

        completed = self.current_session
        self._save_current_session()
        self.current_session = None
        print(f"[Recap] Session finalized: {completed['session_id']}")
        return completed

    def _save_current_session(self):
        if not self.current_session:
            return
        ensure_data_dir()
        file_path = SESSIONS_DIR / f"{self.current_session['session_id']}.json"
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(self.current_session, f, indent=2, ensure_ascii=False)
        except Exception as err:
            print(f"[Recap] Save error: {err}")
