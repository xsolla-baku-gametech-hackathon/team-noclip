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

    def test_recap_manager_and_session(self):
        mgr = RecapManager()
        game_info = {
            "id": "hello_neighbor",
            "name": "Hello Neighbor",
            "executable": "helloneighbor.exe"
        }

        mgr.start_session(game_info, 12345, "Hello Neighbor")
        self.assertIsNotNone(mgr.current_session)

        # Log event
        evt = mgr.add_event("Sneaked into Basement", event_type="gameplay")
        self.assertEqual(evt["text"], "Sneaked into Basement")

        # End session
        completed = mgr.end_session()
        self.assertIsNotNone(completed)
        self.assertIsNone(mgr.current_session)
        self.assertEqual(completed["game_name"], "Hello Neighbor")

    def test_robot_mascot_favicon(self):
        from config import ASSETS_DIR
        from PIL import Image
        mascot_path = ASSETS_DIR / "xsolla_mascot_clean.png"
        self.assertTrue(mascot_path.exists(), "xsolla_mascot_clean.png must exist")
        with Image.open(str(mascot_path)) as img:
            self.assertEqual(img.mode, "RGBA")
            self.assertGreater(img.width, 0)
            self.assertGreater(img.height, 0)

    def test_recording_file_lock(self):
        from unittest.mock import MagicMock
        from album_viewer import VisualMemoriesTab
        from gamebar import GameBarOverlay

        mock_recorder = MagicMock()
        mock_recorder.is_recording = True

        tab = VisualMemoriesTab.__new__(VisualMemoriesTab)
        tab.video_recorder = mock_recorder
        tab.subtitle_lbl = None
        tab.on_open_folder = None
        tab._show_recording_locked_toast = MagicMock()
        tab._show_photo_viewer = MagicMock()
        tab._show_video_player = MagicMock()

        # Attempt to open media during recording
        fake_path = Path("fake_clip.mp4")
        tab._open_media(fake_path)
        tab._show_recording_locked_toast.assert_called_once()
        tab._show_video_player.assert_not_called()
        tab._show_photo_viewer.assert_not_called()

        # Attempt to open folder during recording
        tab._show_recording_locked_toast.reset_mock()
        tab._open_recordings_folder()
        tab._show_recording_locked_toast.assert_called_once()

        # GameBar toggle_album during recording
        gamebar = GameBarOverlay.__new__(GameBarOverlay)
        gamebar.video_rec = mock_recorder
        gamebar.is_album_open = False
        gamebar.show_toast = MagicMock()
        gamebar.toggle_album()
        gamebar.show_toast.assert_called_once()
        self.assertFalse(gamebar.is_album_open)


if __name__ == "__main__":
    unittest.main()
