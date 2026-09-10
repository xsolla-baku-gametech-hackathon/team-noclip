"""
Xsolla Game Recap - Automated Test Suite
Verifies configuration integrity, dynamic title cleaning, session logging,
and recap persistence without needing manual GUI interaction.
"""

import sys
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import unittest
import time
from pathlib import Path

from config import load_config, register_custom_app
from detector import GameDetector, clean_game_title
from recap_manager import RecapManager


class TestXsollaGameRecap(unittest.TestCase):
    def test_config_defaults(self):
        cfg = load_config()
        self.assertIn("app_name", cfg)
        self.assertIn("hotkey", cfg)
        self.assertEqual(cfg["app_name"], "Xsolla Game Recap")

    def test_dynamic_title_cleaning(self):
        # Test Hello Neighbor Unreal shipping executable
        self.assertEqual(clean_game_title("HelloNeighbor-Win64-Shipping.exe"), "Hello Neighbor")
        # Test Ultimate Custom Night camelCase
        self.assertEqual(clean_game_title("UltimateCustomNight.exe"), "Ultimate Custom Night")
        # Test Undertale
        self.assertEqual(clean_game_title("UNDERTALE.exe"), "Undertale")
        # Test Stardew Valley
        self.assertEqual(clean_game_title("Stardew Valley.exe"), "Stardew Valley")
        # Test window title priority
        self.assertEqual(clean_game_title("game.exe", "Hello Neighbor 2 Alpha"), "Hello Neighbor 2 Alpha")

    def test_custom_app_registration(self):
        register_custom_app("Hello Neighbor Standalone", "HelloNeighbor.exe")
        cfg = load_config()
        matching = [c for c in cfg.get("custom_apps", []) if c.get("executable") == "helloneighbor.exe"]
        self.assertGreaterEqual(len(matching), 1)
        self.assertEqual(matching[0]["name"], "Hello Neighbor Standalone")

    def test_recap_manager_and_story(self):
        mgr = RecapManager()
        game_info = {
            "id": "hello_neighbor",
            "name": "Hello Neighbor",
            "executable": "helloneighbor.exe"
        }

        mgr.start_session(game_info, 12345, "Hello Neighbor")
        self.assertIsNotNone(mgr.current_session)

        # Log milestone
        evt = mgr.add_event("Sneaked into Basement", event_type="milestone")
        self.assertEqual(evt["text"], "Sneaked into Basement")

        # Telemetry story generation
        story = mgr.generate_story_recap()
        self.assertEqual(story["game_name"], "Hello Neighbor")
        self.assertGreaterEqual(story["total_events"], 2)

        # End session
        completed = mgr.end_session()
        self.assertIsNotNone(completed)
        self.assertIsNone(mgr.current_session)


if __name__ == "__main__":
    unittest.main()
