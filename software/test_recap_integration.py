"""
Unit & Integration Tests for Xsolla Game Recap:
- Multi-game Save Analyzer (Stardew Valley & Undertale)
- AI Recap Service & Heuristic Fallback
- Local Auth State & Loopback Auth Server Callback Flow
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

    def test_stardew_valley_save_analysis(self):
        res = save_analyzer.analyze_game_save("Stardew Valley")
        self.assertEqual(res["game_name"], "Stardew Valley")
        self.assertEqual(res["player_name"], "Aykhan")
        self.assertIn("Misty Farm", res["farm_name"])
        self.assertGreaterEqual(res["stats"]["gold"], 10000)
        self.assertIn("Summer", res["stats"]["season"])
        self.assertGreaterEqual(len(res["priorities"]), 1)
        self.assertGreaterEqual(len(res["quests"]), 1)

    def test_undertale_save_analysis(self):
        res = save_analyzer.analyze_game_save("Undertale")
        self.assertEqual(res["game_name"], "Undertale")
        self.assertEqual(res["stats"]["lv"], 1)
        self.assertIn("Route", res["stats"]["route"])
        self.assertGreaterEqual(len(res["priorities"]), 2)

    def test_ai_recap_generation(self):
        save_data = save_analyzer.analyze_game_save("Stardew Valley")
        recap = ai_recap.generate_recap(save_data)
        self.assertIn("previously_on", recap)
        self.assertIn("Misty Farm", recap["previously_on"])
        self.assertGreaterEqual(len(recap["what_you_were_up_to"]), 2)
        self.assertGreaterEqual(len(recap["next_objectives"]), 2)
        self.assertIn("PREVIOUSLY ON", recap["raw_text"])

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
