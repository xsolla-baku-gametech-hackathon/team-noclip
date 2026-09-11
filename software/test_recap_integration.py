"""
Unit & Integration Tests for Xsolla Game Recap:
- Universal Game Save & Session Analyzer (works for any game)
- Game Recap Engine & Universal Structured Recaps
- Local Auth State & Loopback Auth Server Callback Flow
- Dedicated Login Launcher Window
"""

import unittest
import urllib.request
import urllib.parse
import time
import threading

import auth_state
import auth_server
import save_analyzer
import ai_recap


class TestRecapIntegration(unittest.TestCase):
    def setUp(self):
        auth_state.log_out()

    def tearDown(self):
        auth_state.log_out()

    def test_universal_game_save_analysis(self):
        # Verify analyzer works dynamically for any game
        res = save_analyzer.analyze_game_save("Elden Ring")
        self.assertEqual(res["game_name"], "Elden Ring")
        self.assertIn("stats", res)
        self.assertIn("events_count", res["stats"])
        self.assertIn("screenshots_count", res["stats"])
        self.assertGreaterEqual(len(res["priorities"]), 2)
        self.assertIn("Elden Ring", res["summary"])

    def test_multi_game_support(self):
        games = ["Cyberpunk 2077", "Hades", "Minecraft", "Hollow Knight"]
        for g in games:
            analysis = save_analyzer.analyze_game_save(g)
            self.assertEqual(analysis["game_name"], g)
            self.assertEqual(analysis["source"], "game_session")

    from unittest.mock import patch

    @patch("requests.post")
    def test_recap_generation(self, mock_post):
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "recap": "PREVIOUSLY ON CYBERPUNK 2077: Night City awaits.",
            "structured": {
                "previously_on": "Cyberpunk 2077: V completed a major heist.",
                "what_you_were_up_to": ["Infiltrated Konpeki Plaza", "Met with Johnny Silverhand"],
                "next_objectives": ["Head to Afterlife", "Upgrade cyberware"]
            }
        }
        save_data = save_analyzer.analyze_game_save("Cyberpunk 2077")
        recap = ai_recap.generate_recap(save_data)
        self.assertIn("previously_on", recap)
        self.assertIn("Cyberpunk 2077", recap["previously_on"])
        self.assertGreaterEqual(len(recap["what_you_were_up_to"]), 2)
        self.assertGreaterEqual(len(recap["next_objectives"]), 2)
        self.assertIn("PREVIOUSLY ON CYBERPUNK 2077", recap["raw_text"])
        self.assertEqual(recap["source"], "recap_engine")

    def test_auth_state_lifecycle(self):
        self.assertFalse(auth_state.is_logged_in())
        auth_state.log_in(user_label="Alexander", email="alex@xsolla.com", token="tok_123")
        self.assertTrue(auth_state.is_logged_in())
        self.assertEqual(auth_state.get_user_label(), "Alexander")

        curr = auth_state.get_current_user()
        self.assertEqual(curr["user_email"], "alex@xsolla.com")
        self.assertEqual(curr["auth_token"], "tok_123")

        auth_state.log_out()
        self.assertFalse(auth_state.is_logged_in())
        self.assertEqual(auth_state.get_user_label(), "Player")

    def test_loopback_auth_server_callback(self):
        callback_fired = threading.Event()
        received_data = {}

        def on_success(token, user, email):
            received_data["token"] = token
            received_data["user"] = user
            received_data["email"] = email
            callback_fired.set()

        server = auth_server.AuthCallbackServer(on_success=on_success)
        port = server.start()

        # Send GET request to callback endpoint simulating browser redirect
        url = f"http://127.0.0.1:{port}/callback?token=test_jwt_99&user=JudgeAlex&email=judge@xsolla.com"
        req = urllib.request.urlopen(url, timeout=5)
        self.assertEqual(req.status, 200)
        body = req.read().decode("utf-8")
        self.assertIn("Authentication Verified", body)
        self.assertIn("JudgeAlex", body)

        # Wait for callback event
        success = callback_fired.wait(timeout=3)
        self.assertTrue(success)
        self.assertEqual(received_data["token"], "test_jwt_99")
        self.assertEqual(received_data["user"], "JudgeAlex")
        self.assertEqual(received_data["email"], "judge@xsolla.com")

        server.stop()

    def test_login_window_creation(self):
        import tkinter as tk
        from login_window import LoginWindow
        root = tk.Tk()
        root.withdraw()
        lw = LoginWindow(root, on_login_success=lambda t, u, e: None)
        lw.show()
        self.assertTrue(lw.window.winfo_exists())
        self.assertEqual(lw.window.cget("bg"), "#080b10")
        lw.destroy()
        root.destroy()


if __name__ == "__main__":
    unittest.main()
