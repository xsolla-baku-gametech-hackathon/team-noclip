"""
Unit tests for Xsolla Game Recap Settings & FPS Recording Configuration:
- Verifies default recording settings (FPS, format, gamebar capture visibility)
- Verifies setting updates and bounds validation
- Verifies capture affinity toggle
"""

import unittest
import tkinter as tk
import config
from settings_panel import SettingsTab


class TestSettings(unittest.TestCase):
    def setUp(self):
        # Reset to known defaults
        config.update_recording_settings({
            "recording_fps": 30,
            "video_format": "mp4",
            "include_gamebar_in_recording": True
        })

    def tearDown(self):
        config.update_recording_settings({
            "recording_fps": 30,
            "video_format": "mp4",
            "include_gamebar_in_recording": True
        })

    def test_default_recording_settings(self):
        settings = config.get_recording_settings()
        self.assertIn("recording_fps", settings)
        self.assertEqual(settings["recording_fps"], 30)
        self.assertEqual(settings["video_format"], "mp4")
        self.assertTrue(settings["include_gamebar_in_recording"])

    def test_update_recording_settings(self):
        updated = config.update_recording_settings({
            "recording_fps": 60,
            "video_format": "mp4",
            "include_gamebar_in_recording": False
        })
        self.assertEqual(updated["recording_fps"], 60)
        self.assertEqual(updated["video_format"], "mp4")
        self.assertFalse(updated["include_gamebar_in_recording"])

        # Check bounds (e.g. max 120, min 10)
        bounded = config.update_recording_settings({"recording_fps": 240})
        self.assertEqual(bounded["recording_fps"], 120)

        bounded_low = config.update_recording_settings({"recording_fps": 5})
        self.assertEqual(bounded_low["recording_fps"], 10)

    def test_capture_affinity_toggle(self):
        root = tk.Tk()
        root.withdraw()
        win = tk.Toplevel(root)
        win.geometry("100x100")

        # Test setting affinity to visible (False = WDA_NONE)
        res_vis = config.make_window_visible_to_capture(win)
        self.assertTrue(res_vis)

        # Test setting affinity to invisible (True = WDA_EXCLUDEFROMCAPTURE)
        res_invis = config.make_window_invisible_to_capture(win)
        self.assertTrue(res_invis)

        win.destroy()
        root.destroy()

    def test_settings_tab_creation(self):
        root = tk.Tk()
        root.withdraw()
        tab = SettingsTab(root)
        self.assertEqual(tab.current_settings["recording_fps"], 30)
        tab._select_fps(60)
        self.assertEqual(tab.current_settings["recording_fps"], 60)
        tab.destroy()
        root.destroy()


if __name__ == "__main__":
    unittest.main()
