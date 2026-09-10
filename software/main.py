"""
Xsolla Game Recap - Main Application Entrypoint
Unifies background game detection, the "Xsolla Game Recap is Watching" animated toast,
the in-game GameBar overlay dashboard, and the Windows System Tray navbar icon.
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
from tray import SystemTrayIcon


class XsollaGameRecapApp:
    def __init__(self, demo_mode: bool = False, open_immediately: bool = True):
        self.config = load_config()
        self.demo_mode = demo_mode

        # Master invisible root for Tkinter message loop
        self.root = tk.Tk()
        self.root.withdraw()
        self.root.title("Xsolla Game Recap")

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
            on_test_banner=self._trigger_test_banner,
            on_quit_app=self.shutdown
        )
        self.hotkey_listener = GlobalHotkeyListener(on_hotkey=self._on_hotkey)

        # Windows Taskbar Notification Area / System Tray Integration
        self.tray = SystemTrayIcon(
            on_open_gamebar=self.gamebar.open,
            on_test_banner=self._trigger_test_banner,
            on_quit=self.shutdown,
            on_simulate_game=self._simulate_game
        )

        # Start listeners, watchers & tray
        self.hotkey_listener.start()
        self.detector.start_monitoring(interval_sec=self.config.get("scan_interval_sec", 1.2))
        self.tray.start()

        print("==========================================================")
        print("  ⚡ XSOLLA GAME RECAP OVERLAY & GAMEBAR ACTIVE")
        print("  • Background game watcher: ON (40+ games + smart heuristics)")
        print("  • System Tray Icon: Active in Windows taskbar navbar")
        print("  • In-Game Shortcut: [Ctrl + Shift + X] (or Alt + X)")
        print("==========================================================")

        # Handle launch behavior
        if demo_mode:
            self.root.after(800, self._run_demo_sequence)
        elif open_immediately:
            # Open HUD right away so the user immediately sees the interface
            self.root.after(300, self.gamebar.open)

    def _on_game_launched(self, game: dict, pid: int, window_title: str):
        print(f"[App] Game Launched: {game.get('name')} (PID: {pid})")
        self.recap_mgr.start_session(game, pid, window_title)
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
        game_name = active.get("name") if active else "Hello Neighbor"
        self.banner.show(game_name, shortcut=self.config.get("hotkey", "Ctrl+Shift+X"))

    def _simulate_game(self, game_id: str):
        self.detector.simulate_launch(game_id)

    def _run_demo_sequence(self):
        print("[App] Running Showcase Demo Mode...")
        self.detector.simulate_launch("hello_neighbor")
        self.root.after(2200, self.gamebar.open)

    def run(self):
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.shutdown()

    def shutdown(self):
        print("\n[App] Gracefully shutting down Xsolla Game Recap...")
        self.detector.stop_monitoring()
        self.hotkey_listener.stop()
        self.tray.stop()
        try:
            self.root.destroy()
        except Exception:
            pass
        sys.exit(0)


def main():
    parser = argparse.ArgumentParser(description="Xsolla Game Recap In-Game Overlay & GameBar")
    parser.add_argument("--demo", action="store_true", help="Launch interactive demo mode simulating a game start")
    parser.add_argument("--hide", action="store_true", help="Start minimized directly to the system tray")
    args = parser.parse_args()

    app = XsollaGameRecapApp(demo_mode=args.demo, open_immediately=not args.hide)
    app.run()


if __name__ == "__main__":
    main()
