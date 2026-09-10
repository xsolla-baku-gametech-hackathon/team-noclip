"""
Xsolla Game Recap - Automated Test Suite
Verifies game detection logic, custom cracked game registration, session logging,
and Story Recap compilation without needing manual GUI interaction.
"""

import sys
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

import unittest
import time
from pathlib import Path

from config import load_config, add_custom_game, DEFAULT_SUPPORTED_GAMES
from detector import GameDetector
from recap_manager import RecapManager


class TestXsollaGameRecap(unittest.TestCase):
    def test_config_defaults(self):
        cfg = load_config()
        self.assertIn("app_name", cfg)
        self.assertIn("hotkey", cfg)
        self.assertGreaterEqual(len(cfg.get("supported_games", [])), 5)

        # Check Stardew Valley & Undertale are present
        game_ids = [g["id"] for g in cfg["supported_games"]]
        self.assertIn("stardew_valley", game_ids)
        self.assertIn("undertale", game_ids)

    def test_add_custom_cracked_game(self):
        game = add_custom_game("My Custom RPG", "custom_game.exe", window_keyword="custom game")
        self.assertEqual(game["name"], "My Custom RPG")
        self.assertIn("custom_game.exe", game["executables"])

        cfg = load_config()
        custom_ids = [g["id"] for g in cfg.get("custom_games", [])]
        self.assertIn(game["id"], custom_ids)

    def test_detector_simulation(self):
        launched_events = []
        closed_events = []

        detector = GameDetector(
            on_game_launched=lambda g, pid, win: launched_events.append(g["name"]),
            on_game_closed=lambda g: closed_events.append(g["name"])
        )

        detector.simulate_launch("undertale")
        self.assertIsNotNone(detector.active_game)
        self.assertEqual(detector.active_game["id"], "undertale")
        self.assertEqual(len(launched_events), 1)
        self.assertEqual(launched_events[0], "Undertale")

        # Test session duration formatting
        time.sleep(0.1)
        dur = detector.get_session_duration_str()
        self.assertTrue(dur.startswith("00:00:"))

        # Test simulate close
        detector.simulate_close()
        self.assertIsNone(detector.active_game)
        self.assertEqual(len(closed_events), 1)

    def test_recap_manager_and_story(self):
        mgr = RecapManager()
        game_info = {
            "id": "stardew_valley",
            "name": "Stardew Valley",
            "genre": "Farming RPG",
            "icon": "🌾",
            "theme_color": "#ffb300"
        }

        mgr.start_session(game_info, 12345, "Stardew Valley")
        self.assertIsNotNone(mgr.current_session)

        # Log milestone
        evt = mgr.add_event("Completed First Crop Harvest", event_type="milestone")
        self.assertEqual(evt["text"], "Completed First Crop Harvest")

        # Story generation
        story = mgr.generate_story_recap()
        self.assertEqual(story["game_name"], "Stardew Valley")
        self.assertGreaterEqual(story["total_events"], 2)
        self.assertIn("XP", story["xsolla_points"])

        # End session
        completed = mgr.end_session()
        self.assertIsNotNone(completed)
        self.assertIsNone(mgr.current_session)


if __name__ == "__main__":
    unittest.main()
