"""
Xsolla Game Recap - Main Application Entrypoint
Coordinates background game detection, right edge fade in toast banner,
the minimalist in-game GameBar HUD with dim backdrop, in-game screenshot capture,
in-game MP4 video recording, photo album gallery, and Windows System Tray navbar icon.
"""

import sys
import ctypes

# Automatically hide any console window immediately on Windows (zero cmd visibility)
if sys.platform == "win32":
    try:
        _hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        if _hwnd:
            ctypes.windll.user32.ShowWindow(_hwnd, 0)  # 0 = SW_HIDE
    except Exception:
        pass

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import argparse
import webbrowser
import tkinter as tk

from config import load_config, WEBSITE_LOGIN_URL
import auth_state
from detector import GameDetector
from recap_manager import RecapManager
from banner import WatchingBanner
from gamebar import GameBarOverlay
from hotkey import GlobalHotkeyListener
from tray import SystemTrayIcon
from polaroid_service import PolaroidService
from video_recorder import VideoRecorderService
from album_viewer import AlbumViewerWindow


class XsollaGameRecapApp:
    def __init__(self, open_immediately: bool = True):
        self.config = load_config()

        # Master invisible root for Tkinter message loop
        self.root = tk.Tk()
        self.root.withdraw()
        self.root.title("Xsolla Game Recap")

        # Subsystems
        self.recap_mgr = RecapManager()
        self.polaroid_svc = PolaroidService()
        self.video_rec = VideoRecorderService(on_state_change=self._on_record_state_change)
        self.banner = WatchingBanner(self.root)
        self.album_viewer = AlbumViewerWindow(
            self.root,
            self.polaroid_svc,
            on_capture_request=self._on_capture_requested,
            on_record_request=self._on_record_toggled,
            on_pause_request=self._on_pause_toggled,
            video_recorder=self.video_rec
        )

        self.detector = GameDetector(
            on_game_launched=self._on_game_launched,
            on_game_closed=self._on_game_closed
        )

        self.gamebar = GameBarOverlay(
            self.root,
            self.detector,
            self.recap_mgr,
            polaroid_svc=self.polaroid_svc,
            on_quit_app=self.shutdown,
            on_capture=self._on_capture_requested,
            on_open_album=self._open_visual_memories,
            on_toggle_record=self._on_record_toggled,
            on_toggle_pause=self._on_pause_toggled,
            video_recorder=self.video_rec
        )

        self.hotkey_listener = GlobalHotkeyListener(
            on_hotkey=self._on_hotkey,
            on_capture=self._on_capture_requested,
            on_record=self._on_record_toggled,
            on_pause=self._on_pause_toggled
        )

        # Windows System Tray Integration
        self.tray = SystemTrayIcon(
            on_open_gamebar=self.gamebar.open,
            on_test_banner=self._trigger_test_banner,
            on_quit=self.shutdown,
            on_capture=self._on_capture_requested,
            on_open_album=self._open_visual_memories,
            on_toggle_record=self._on_record_toggled,
            on_login=self._on_login,
            on_logout=self._on_logout,
            is_logged_in=auth_state.is_logged_in
        )

        # Start listeners, watchers and tray
        self.hotkey_listener.start()
        self.detector.start_monitoring(interval_sec=self.config.get("scan_interval_sec", 1.0))
        self.tray.start()

        print("==========================================================")
        print("  XSOLLA GAME RECAP ACTIVE")
        print("  Background game detection: ON")
        print("  System Tray Icon: Active in Windows taskbar")
        print("  Overlay Shortcut: [Ctrl + Shift + X]")
        print("  Screenshot Capture: [F11]")
        print("  Video Recording: [F9]")
        print("  Recording Pause: [F10]")
        print("==========================================================")

        if open_immediately:
            self.root.after(200, self.gamebar.open)

    def _on_game_launched(self, game: dict, pid: int, window_title: str):
        print(f"[App] Game Launched: {game.get('name')} (PID {pid})")
        self.recap_mgr.start_session(game, pid, window_title)
        shortcut = self.config.get("hotkey", "Ctrl+Shift+X")
        self.banner.show(game.get("name", "Active Game"), shortcut=shortcut)

    def _on_game_closed(self, game: dict):
        print(f"[App] Game Exited: {game.get('name')}")
        if self.video_rec.is_recording:
            self._on_record_toggled()
        self.recap_mgr.end_session()

    def _on_hotkey(self):
        """Called when Ctrl+Shift+X or Alt+X is pressed anywhere in Windows."""
        self.gamebar.toggle()

    def _open_visual_memories(self):
        """Opens the GameBar navbar with the Visual Memories tab expanded."""
        if self.video_rec and getattr(self.video_rec, "is_recording", False):
            print("[App] Prevented opening album/files: video recording is active.")
            if self.gamebar:
                self.gamebar.open(show_album=False)
                self.gamebar.show_toast("File access locked while recording", color="#ff5c5c")
            return
        self.gamebar.open(show_album=True)

    def _refresh_media_ui(self):
        """Refreshes visual memories tab, recording states, and any open galleries."""
        if self.gamebar.window and self.gamebar.window.winfo_exists():
            self.gamebar.update_recording_state()
            if self.gamebar.is_album_open and self.gamebar.visual_memories_tab:
                self.gamebar.visual_memories_tab.refresh()
        if self.album_viewer.window and self.album_viewer.window.winfo_exists():
            self.album_viewer._refresh_content()

    def _on_capture_requested(self):
        """Called when F11 or Ctrl+Shift+S is pressed, or SNAP button clicked."""
        active = self.detector.active_game
        game_name = active.get("name") if active else "Highlight Capture"
        duration = self.detector.get_session_duration_str() if active else "00:00:00"

        result = self.polaroid_svc.capture_memory(game_name=game_name, session_duration=duration)
        if result:
            self.recap_mgr.add_event(f"Screenshot Saved: {result['filename']}")
            self.banner.show_capture(game_name, hint="Saved in High Quality • [F11]")
            self._refresh_media_ui()

    def _on_record_toggled(self):
        """Called when F9 or Ctrl+Shift+R is pressed, or REC button clicked."""
        active = self.detector.active_game
        game_name = active.get("name") if active else "Gameplay Clip"

        if self.video_rec.is_recording:
            # Stop recording
            result = self.video_rec.stop_recording()
            if result:
                self.recap_mgr.add_event(f"Video Clip Saved: {result['filename']} ({result['duration_str']})")
                self.banner.show_record_stopped(result["filename"], result["duration_str"])
                self._refresh_media_ui()
        else:
            # Start recording
            started = self.video_rec.start_recording(game_name=game_name)
            if started:
                self.banner.show_record_started(game_name, shortcut="F9")
                self._refresh_media_ui()

    def _on_pause_toggled(self):
        """Called when F10 is pressed or PAUSE button clicked."""
        if not self.video_rec.is_recording:
            return
        active = self.detector.active_game
        game_name = active.get("name") if active else "Gameplay Clip"
        is_paused = self.video_rec.toggle_pause()
        if is_paused:
            self.banner.show_record_paused(game_name)
        else:
            self.banner.show_record_resumed(game_name)

        self._refresh_media_ui()

    def _on_record_state_change(self, is_recording: bool, duration_str: str):
        """Callback from video recorder on start/stop/pause."""
        self._refresh_media_ui()

    def _trigger_test_banner(self):
        active = self.detector.active_game
        game_name = active.get("name") if active else "Hello Neighbor"
        self.banner.show(game_name, shortcut=self.config.get("hotkey", "Ctrl+Shift+X"))

    def _on_login(self):
        """Opens the website's login page and marks this local install as
        logged in. This is a local UI flag only — no real session/token is
        exchanged with the website yet."""
        webbrowser.open(WEBSITE_LOGIN_URL)
        auth_state.log_in()
        print("[Auth] Opened login page; marked local install as logged in.")

    def _on_logout(self):
        auth_state.log_out()
        print("[Auth] Signed out locally.")

    def run(self):
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.shutdown()

    def shutdown(self):
        print("\n[App] Shutting down Xsolla Game Recap...")
        if hasattr(self, 'gamebar') and self.gamebar:
            self.gamebar.close_recordings_folder()
        if hasattr(self, 'video_rec') and self.video_rec.is_recording:
            self.video_rec.stop_recording()
        self.detector.stop_monitoring()
        self.hotkey_listener.stop()
        self.tray.stop()
        try:
            self.root.destroy()
        except Exception:
            pass
        sys.exit(0)


def main():
    parser = argparse.ArgumentParser(description="Xsolla Game Recap In Game Overlay and GameBar")
    parser.add_argument("--hide", action="store_true", help="Start minimized directly to the system tray")
    args = parser.parse_args()

    app = XsollaGameRecapApp(open_immediately=not args.hide)
    app.run()


if __name__ == "__main__":
    main()
