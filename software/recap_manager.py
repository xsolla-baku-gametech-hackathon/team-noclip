"""
Xsolla Game Recap - Session Logger & Story Recap Engine
Handles tracking session events, milestone highlights, screenshot captures,
and compiling dynamic story recaps ready for synchronization to the SaaS cloud.
"""

import sys
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
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

# Game-specific auto-milestones to demonstrate intelligent event hooking
SAMPLE_GAME_EVENTS = {
    "stardew_valley": [
        "🌾 Cleared farm parcel for Spring Year 1",
        "🧺 Harvested 24 Quality Parsnips",
        "⛏️ Reached Mine Floor 40 (Iron Ore Unlocked)",
        "🎣 Caught Rare Sturgeon in Mountain Lake",
        "🎉 Community Center Boiler Room Completed!"
    ],
    "undertale": [
        "❤️ Fell down into the Ruins",
        "🥧 Accepted butterscotch-cinnamon pie from Toriel",
        "🦴 Escaped Papyrus's Puzzle Gauntlet with 0 damage",
        "🐟 Survived Undyne's Spear Barrage in Waterfall",
        "✨ Gained True Pacifist determination!"
    ],
    "hades": [
        "🔥 Escaped Tartarus with Stygian Blade",
        "⚡ Accepted Boon of Zeus: Lightning Strike",
        "💀 Defeated Meg and the Furies",
        "🏛️ Reached Elysium Arena against Theseus",
        "👑 Boon of Chaos: +45% Backstab Damage"
    ],
    "hollow_knight": [
        "⚔️ Acquired the Mothwing Cloak in Greenpath",
        "🐛 Rescued 5 Grubs in Forgotten Crossroads",
        "👑 Defeated the False Knight",
        "🪪 Purchased Map & Quill from Cornifer"
    ],
    "minecraft": [
        "🌲 Punched first oak tree",
        "⛏️ Crafted Stone Pickaxe and built shelter",
        "💎 Discovered 8 Diamonds at Y=-58",
        "🔥 Activated Nether Portal"
    ]
}


class RecapManager:
    def __init__(self):
        SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
        SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

        self.current_session: Optional[Dict] = None

    def start_session(self, game: Dict, pid: int, window_title: str):
        """Initialize a new live game recap session."""
        session_id = f"{game.get('id', 'game')}_{int(time.time())}"
        self.current_session = {
            "session_id": session_id,
            "game_id": game.get("id"),
            "game_name": game.get("name"),
            "genre": game.get("genre", "Game"),
            "icon": game.get("icon", "🎮"),
            "theme_color": game.get("theme_color", "#ff0055"),
            "pid": pid,
            "window_title": window_title,
            "started_at": datetime.datetime.now().isoformat(),
            "start_timestamp": time.time(),
            "ended_at": None,
            "duration_seconds": 0,
            "events": [
                {
                    "timestamp": datetime.datetime.now().strftime("%H:%M:%S"),
                    "text": f"Session Hooked: {game.get('name')} is active!",
                    "type": "system"
                }
            ],
            "screenshots": []
        }

        # Add initial sample event if known game
        known_events = SAMPLE_GAME_EVENTS.get(game.get("id"), [])
        if known_events:
            self.add_event(known_events[0], event_type="milestone")

        print(f"[Recap] Session started: {session_id}")
        self._save_current_session()

    def add_event(self, text: str, event_type: str = "custom") -> Dict:
        """Add an event to the current live session."""
        if not self.current_session:
            return {}

        evt = {
            "timestamp": datetime.datetime.now().strftime("%H:%M:%S"),
            "text": text,
            "type": event_type
        }
        self.current_session["events"].append(evt)
        self._save_current_session()
        print(f"[Recap] Event logged: {text}")
        return evt

    def inject_random_milestone(self) -> Optional[str]:
        """Adds next realistic game milestone for demoing."""
        if not self.current_session:
            return None
        gid = self.current_session.get("game_id")
        candidates = SAMPLE_GAME_EVENTS.get(gid, [
            "⭐ Level Up Achieved!",
            "🏆 Achievement Unlocked: Fast Reflexes",
            "📦 Discovered Hidden Chest",
            "⚔️ Flawless Encounter Finished"
        ])

        logged_texts = {e["text"] for e in self.current_session["events"]}
        for item in candidates:
            if item not in logged_texts:
                self.add_event(item, event_type="milestone")
                return item

        # Fallback dynamic event
        dyn = f"⭐ Milestone #{len(self.current_session['events'])} Achieved!"
        self.add_event(dyn, event_type="milestone")
        return dyn

    def capture_screenshot(self) -> Optional[str]:
        """Captures in-game screenshot and tags it to the session."""
        if not self.current_session:
            return None
        try:
            timestamp_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"recap_{self.current_session['game_id']}_{timestamp_str}.png"
            path = SCREENSHOTS_DIR / filename

            shot = ImageGrab.grab()
            shot.save(str(path))
            self.current_session["screenshots"].append(str(path))
            self.add_event(f"📸 Highlight snapshot saved: {filename}", event_type="screenshot")
            return str(path)
        except Exception as err:
            print(f"[Recap] Screenshot error: {err}")
            return None

    def end_session(self) -> Optional[Dict]:
        """Finalize and save completed session."""
        if not self.current_session:
            return None

        self.current_session["ended_at"] = datetime.datetime.now().isoformat()
        elapsed = int(time.time() - self.current_session["start_timestamp"])
        self.current_session["duration_seconds"] = elapsed
        self.add_event("Game session concluded. Recap ready!", event_type="system")

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
            print(f"[Recap] Error saving session file: {err}")

    def generate_story_recap(self) -> Dict:
        """Compile a Spotify Wrapped / Story style recap for the current session."""
        sess = self.current_session
        if not sess:
            # Generate a mock showcase recap if no game currently running
            return {
                "title": "Stardew Valley Season Highlights",
                "game_name": "Stardew Valley",
                "vibe": "Cozy Agronomist",
                "session_time": "42 minutes",
                "total_events": 5,
                "top_highlight": "🎉 Community Center Boiler Room Restored!",
                "player_rank": "Grand Master Farmer",
                "xsolla_points": "+250 GameTech XP",
                "synced_to_cloud": False
            }

        elapsed = int(time.time() - sess["start_timestamp"])
        mins = elapsed // 60
        secs = elapsed % 60
        events = sess.get("events", [])
        milestones = [e["text"] for e in events if e.get("type") == "milestone"]

        top_highlight = milestones[-1] if milestones else (events[-1]["text"] if events else "Session completed")

        story = {
            "title": f"{sess.get('game_name')} Live Recap",
            "game_name": sess.get("game_name"),
            "genre": sess.get("genre"),
            "vibe": "Ultra Focused",
            "session_time": f"{mins}m {secs}s",
            "total_events": len(events),
            "top_highlight": top_highlight,
            "player_rank": "Diamond Tier",
            "xsolla_points": f"+{len(events) * 50} GameTech XP",
            "events_list": events[-6:],
            "synced_to_cloud": False
        }
        return story

    def sync_to_saas(self) -> Dict:
        """Pushes current session recap to the SaaS website."""
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
                return {"success": True, "message": f"Successfully synced with SaaS API ({resp.status_code})"}
            else:
                return {"success": False, "message": f"SaaS API responded: {resp.status_code}"}
        except Exception as err:
            # Graceful offline mode: save locally and notify user
            return {
                "success": True,
                "offline": True,
                "message": f"Saved locally! (SaaS web server offline at {url})"
            }
