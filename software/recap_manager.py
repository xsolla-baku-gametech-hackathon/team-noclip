"""
Xsolla Game Recap - Session Logger and Recap Engine
Records genuine game sessions, telemetry checkpoints, snapshots, and milestones.
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
from typing import List, Dict, Optional
from PIL import ImageGrab
import requests

from config import DATA_DIR, load_config

SESSIONS_DIR = DATA_DIR / "sessions"
SCREENSHOTS_DIR = DATA_DIR / "screenshots"


class RecapManager:
    def __init__(self):
        SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
        SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
        self.current_session: Optional[Dict] = None

    def start_session(self, game: Dict, pid: int, window_title: str):
        """Initializes a live session for the newly hooked game."""
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
            ],
            "screenshots": []
        }

        print(f"[Recap] Session started: {session_id}")
        self._save_current_session()

    def add_event(self, text: str, event_type: str = "custom") -> Dict:
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

    def capture_screenshot(self) -> Optional[str]:
        """Captures a real full resolution screenshot of the game."""
        if not self.current_session:
            return None
        try:
            timestamp_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"recap_{self.current_session['game_id']}_{timestamp_str}.png"
            path = SCREENSHOTS_DIR / filename

            shot = ImageGrab.grab()
            shot.save(str(path))
            self.current_session["screenshots"].append(str(path))
            self.add_event(f"Snapshot saved: {filename}", event_type="screenshot")
            return str(path)
        except Exception as err:
            print(f"[Recap] Screenshot error: {err}")
            return None

    def end_session(self) -> Optional[Dict]:
        """Finalizes and persists the active session."""
        if not self.current_session:
            return None

        self.current_session["ended_at"] = datetime.datetime.now().isoformat()
        elapsed = int(time.time() - self.current_session["start_timestamp"])
        self.current_session["duration_seconds"] = elapsed
        self.add_event("Session concluded • Recap saved", event_type="system")

        completed = self.current_session
        self._save_current_session()
        self.current_session = None
        print(f"[Recap] Session finalized: {completed['session_id']}")
        return completed

    def _save_current_session(self):
        if not self.current_session:
            return
        file_path = SESSIONS_DIR / f"{self.current_session['session_id']}.json"
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(self.current_session, f, indent=2, ensure_ascii=False)
        except Exception as err:
            print(f"[Recap] Save error: {err}")

    def generate_story_recap(self) -> Dict:
        """Compiles clean summary telemetry for the active session."""
        sess = self.current_session
        if not sess:
            return {
                "title": "Xsolla Game Recap",
                "game_name": "No Active Session",
                "session_time": "0m 0s",
                "total_events": 0,
                "top_highlight": "Launch any game to start recording",
                "synced_to_cloud": False
            }

        elapsed = int(time.time() - sess["start_timestamp"])
        mins = elapsed // 60
        secs = elapsed % 60
        events = sess.get("events", [])
        milestones = [e["text"] for e in events if e.get("type") in ["milestone", "custom"]]
        highlight = milestones[-1] if milestones else (events[-1]["text"] if events else "Session Active")

        return {
            "title": f"{sess.get('game_name')} Live Recap",
            "game_name": sess.get("game_name"),
            "session_time": f"{mins}m {secs}s",
            "total_events": len(events),
            "top_highlight": highlight,
            "events_list": events[-8:],
            "synced_to_cloud": False
        }

    def sync_to_saas(self) -> Dict:
        """Pushes session data to the web app API endpoint."""
        cfg = load_config()
        url = cfg.get("saas_api_url", "http://localhost:3000/api/recap")
        token = cfg.get("saas_api_token", "")

        story = self.generate_story_recap()
        payload = {
            "session": self.current_session or story,
            "story": story,
            "synced_at": datetime.datetime.now().isoformat()
        }

        try:
            resp = requests.post(url, json=payload, headers={"Authorization": f"Bearer {token}"}, timeout=2.0)
            if resp.status_code in (200, 201):
                story["synced_to_cloud"] = True
                return {"success": True, "message": f"Synced with Cloud API ({resp.status_code})"}
            else:
                return {"success": False, "message": f"Cloud API response: {resp.status_code}"}
        except Exception:
            return {
                "success": True,
                "offline": True,
                "message": "Saved locally in sessions folder"
            }
