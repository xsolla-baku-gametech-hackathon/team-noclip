"""
Xsolla Game Recap - Main Application Entrypoint
Unifies background game detection, the "Xsolla Game Recap is Watching" animated toast,
and the in-game GameBar overlay dashboard accessible via Ctrl+Shift+X or Alt+X.
"""

import sys
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

import argparse
import tkinter as tk

from config import load_config
from detector import GameDetector
from recap_manager import RecapManager
from banner import WatchingBanner
from gamebar import GameBarOverlay
from hotkey import GlobalHotkeyListener


class XsollaGameRecapApp:
    def __init__(self, demo_mode: bool = False, open_immediately: bool = False):
        self.config = load_config()
        self.demo_mode = demo_mode

        # Master invisible root for Tkinter message loop
        self.root = tk.Tk()
        self.root.withdraw()  # Hidden background service
        self.root.title("Xsolla Game Recap Service")

        # Subsystems
        self.recap_mgr = RecapManager()
        self.banner = WatchingBanner(self.root)
        self.detector = GameDetector(
            on_game_launched=self._on_game_launched,
            on_game_closed=self._on_game_closed
        )
        self.gamebar = GameBarOverlay(
            self.root,
            self.detector,
            self.recap_mgr,
            on_test_banner=self._trigger_test_banner
        )
        self.hotkey_listener = GlobalHotkeyListener(on_hotkey=self._on_hotkey)

        # Start listeners & watchers
        self.hotkey_listener.start()
        self.detector.start_monitoring(interval_sec=self.config.get("scan_interval_sec", 1.5))

        print("==========================================================")
        print("  ⚡ XSOLLA GAME RECAP OVERLAY & GAMEBAR ACTIVE")
        print("  • Background game watcher: ON (official + cracked)")
        print("  • In-Game Shortcut: [Ctrl + Shift + X] (or Alt + X)")
        print("==========================================================")

        # Handle launch arguments
        if demo_mode:
            self.root.after(800, self._run_demo_sequence)
        elif open_immediately:
            self.root.after(300, self.gamebar.open)

    def _on_game_launched(self, game: dict, pid: int, window_title: str):
        print(f"[App] Game Launched: {game.get('name')} (PID: {pid})")
        # 1. Start tracking session
        self.recap_mgr.start_session(game, pid, window_title)

        # 2. Show the awesome 'Watching' toast banner!
        shortcut = self.config.get("hotkey", "Ctrl+Shift+X")
        self.banner.show(game.get("name", "Active Game"), shortcut=shortcut)

    def _on_game_closed(self, game: dict):
        print(f"[App] Game Exited: {game.get('name')}")
        self.recap_mgr.end_session()

    def _on_hotkey(self):
        """Called when Ctrl+Shift+X or Alt+X is pressed anywhere in Windows."""
        self.gamebar.toggle()

    def _trigger_test_banner(self):
        active = self.detector.active_game
        game_name = active.get("name") if active else "Stardew Valley"
        self.banner.show(game_name, shortcut=self.config.get("hotkey", "Ctrl+Shift+X"))

    def _run_demo_sequence(self):
        """Simulates a game launch and triggers both the banner and GameBar for showcase."""
        print("[App] Running Showcase Demo Mode...")
        self.detector.simulate_launch("stardew_valley")
        # Banner will appear automatically via callback
        # Then open the GameBar overlay after 2 seconds
        self.root.after(2500, self.gamebar.open)

    def run(self):
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.shutdown()

    def shutdown(self):
        print("\n[App] Shutting down Xsolla Game Recap...")
        self.detector.stop_monitoring()
        self.hotkey_listener.stop()
        try:
            self.root.destroy()
        except Exception:
            pass


def main():
    parser = argparse.ArgumentParser(description="Xsolla Game Recap In-Game Overlay & GameBar")
    parser.add_argument("--demo", action="store_true", help="Launch interactive demo mode simulating a game start")
    parser.add_argument("--open-gamebar", action="store_true", help="Immediately open the GameBar dashboard on launch")
    args = parser.parse_args()

    app = XsollaGameRecapApp(demo_mode=args.demo, open_immediately=args.open_gamebar)
    app.run()


if __name__ == "__main__":
    main()
