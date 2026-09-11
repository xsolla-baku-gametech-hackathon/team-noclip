"""
Xsolla Game Recap - Main Application Entrypoint
Coordinates background game detection, right edge fade in toast banner,
mandatory launcher login window, minimalist in-game GameBar HUD with dim backdrop,
in-game screenshot capture, MP4 video recording, photo album gallery,
Game Recap by Xsolla, and Windows System Tray navbar icon.
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
import threading
import tkinter as tk

from config import load_config
import auth_state
import sync_client
from detector import GameDetector
from recap_manager import RecapManager
from banner import WatchingBanner
from gamebar import GameBarOverlay
from hotkey import GlobalHotkeyListener
from tray import SystemTrayIcon
from polaroid_service import PolaroidService
from video_recorder import VideoRecorderService
from album_viewer import AlbumViewerWindow
from login_window import LoginWindow


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
            on_login_request=self._on_login,
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
            on_open_gamebar=self._on_tray_open_gamebar,
            on_test_banner=self._trigger_test_banner,
            on_quit=self.shutdown,
            on_capture=self._on_capture_requested,
            on_open_album=self._open_visual_memories,
            on_toggle_record=self._on_record_toggled,
            on_recap=self._open_game_recap,
            on_login=self._on_login,
            on_logout=self._on_logout,
            is_logged_in=auth_state.is_logged_in
        )

        # Dedicated Rectangular Launcher Login Window
        self.login_window = LoginWindow(
            self.root,
            on_login_success=self._apply_auth_success,
            on_cancel=self.shutdown
        )

        self._hotkeys_active = False
        self._monitoring_active = False

        # Mandatory Login Check:
        # If player is not logged in, display the rectangular login launcher first.
        # The in-game Xsolla bar and background detection only unlock AFTER login!
        if not auth_state.is_logged_in():
            print("[App] Mandatory login required. Presenting Xsolla login launcher...")
            self.tray.start()
            self.root.after(150, self.login_window.show)
        else:
            self._activate_app_post_login(open_gamebar=open_immediately)

    def _activate_app_post_login(self, open_gamebar: bool = True):
        """Activates hotkeys, detector, and overlay after successful login."""
        if not self._hotkeys_active:
            self.hotkey_listener.start()
            self._hotkeys_active = True

        if not self._monitoring_active:
            self.detector.start_monitoring(interval_sec=self.config.get("scan_interval_sec", 1.0))
            self._monitoring_active = True

        if not getattr(self.tray, "_thread", None) or not self.tray._thread.is_alive():
            self.tray.start()

        self.gamebar.update_auth_ui()

        print("==========================================================")
        print("  XSOLLA GAME RECAP ACTIVE")
        print("  User Authenticated: " + auth_state.get_user_label())
        print("  Background game detection: ON")
        print("  System Tray Icon: Active in Windows taskbar")
        print("  Overlay Shortcut: [Ctrl + Shift + X]")
        print("  Screenshot Capture: [F11]")
        print("  Video Recording: [F9]")
        print("  Recording Pause: [F10]")
        print("==========================================================")

        if open_gamebar:
            self.root.after(200, self.gamebar.open)

    def _on_game_launched(self, game: dict, pid: int, window_title: str):
        if not auth_state.is_logged_in():
            return
        print(f"[App] Game Launched: {game.get('name')} (PID {pid})")
        self.recap_mgr.start_session(game, pid, window_title)
        shortcut = self.config.get("hotkey", "Ctrl+Shift+X")
        self.banner.show(game.get("name", "Active Game"), shortcut=shortcut)

    def _on_game_closed(self, game: dict):
        if not auth_state.is_logged_in():
            return
        print(f"[App] Game Exited: {game.get('name')}")
        if self.video_rec.is_recording:
            self._on_record_toggled()
        completed_session = self.recap_mgr.end_session()
        if completed_session and auth_state.is_logged_in():
            threading.Thread(
                target=sync_client.sync_session, args=(completed_session,), daemon=True
            ).start()

    def _on_hotkey(self):
        """Called when Ctrl+Shift+X is pressed anywhere in Windows."""
        if not auth_state.is_logged_in():
            self.login_window.show()
            return
        self.gamebar.toggle()

    def _on_tray_open_gamebar(self):
        if not auth_state.is_logged_in():
            self.login_window.show()
            return
        self.gamebar.open()

    def _open_visual_memories(self):
        """Opens the GameBar navbar with the Visual Memories tab expanded."""
        if not auth_state.is_logged_in():
            self.login_window.show()
            return

        if self.video_rec and getattr(self.video_rec, "is_recording", False):
            print("[App] Prevented opening album/files: video recording is active.")
            if self.gamebar:
                self.gamebar.open(show_album=False)
                self.gamebar.show_toast("File access locked while recording", color="#ff5c5c")
            return
        self.gamebar.open(show_album=True)

    def _open_game_recap(self):
        """Opens the GameBar navbar with the Game Recap tab expanded."""
        if not auth_state.is_logged_in():
            self.login_window.show()
            return

        if self.video_rec and getattr(self.video_rec, "is_recording", False):
            if self.gamebar:
                self.gamebar.show_toast("Recap locked while recording", color="#ff5c5c")
            return
        self.gamebar.open(show_recap=True)

    def _refresh_media_ui(self):
        """Refreshes visual memories tab, recording states, and any open galleries."""
        if self.gamebar.window and self.gamebar.window.winfo_exists():
            self.gamebar.update_recording_state()
            if self.gamebar.is_album_open and self.gamebar.visual_memories_tab:
                self.gamebar.visual_memories_tab.refresh()
        if self.album_viewer.window and self.album_viewer.window.winfo_exists():
            self.album_viewer._refresh_content()

    def _on_capture_requested(self):
        """Called when F11 or SNAP button clicked."""
        if not auth_state.is_logged_in():
            return
        active = self.detector.active_game
        game_name = active.get("name") if active else "Highlight Capture"
        duration = self.detector.get_session_duration_str() if active else "00:00:00"

        result = self.polaroid_svc.capture_memory(game_name=game_name, session_duration=duration)
        if result:
            self.recap_mgr.add_event(f"Screenshot Saved: {result['filename']}")
            self.banner.show_capture(game_name, hint="Saved in High Quality • [F11]")
            self._refresh_media_ui()
            if auth_state.is_logged_in():
                session_id = self.recap_mgr.current_session.get("session_id") if self.recap_mgr.current_session else None
                threading.Thread(
                    target=sync_client.sync_media,
                    args=(result["path"], "screenshot", game_name, session_id),
                    daemon=True,
                ).start()

    def _on_record_toggled(self):
        """Called when F9 or REC button clicked."""
        if not auth_state.is_logged_in():
            return
        active = self.detector.active_game
        game_name = active.get("name") if active else "Gameplay Clip"

        if self.video_rec.is_recording:
            result = self.video_rec.stop_recording()
            if result:
                self.recap_mgr.add_event(f"Video Clip Saved: {result['filename']} ({result['duration_str']})")
                self.banner.show_record_stopped(result["filename"], result["duration_str"])
                self._refresh_media_ui()
                if auth_state.is_logged_in():
                    session_id = self.recap_mgr.current_session.get("session_id") if self.recap_mgr.current_session else None
                    threading.Thread(
                        target=sync_client.sync_media,
                        args=(result["path"], "video", game_name, session_id, result["duration_sec"]),
                        daemon=True,
                    ).start()
        else:
            started = self.video_rec.start_recording(game_name=game_name)
            if started:
                self.banner.show_record_started(game_name, shortcut="F9")
                self._refresh_media_ui()

    def _on_pause_toggled(self):
        """Called when F10 is pressed or PAUSE button clicked."""
        if not auth_state.is_logged_in() or not self.video_rec.is_recording:
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
        """Shows the mandatory login launcher, which opens the website via
        auth_server's loopback flow and waits for the callback."""
        self.login_window.show()

    def _apply_auth_success(self, token: str, user: str, email: str):
        """Invoked by auth_server's loopback callback after a REAL sign-in
        on the website (Google or email/password) — `token` is a device
        token minted server-side for this user, not fabricated locally."""
        auth_state.log_in(user_label=user, email=email, token=token)
        self.banner.show(f"Welcome, {user}!", shortcut="Xsolla Account Linked")
        self._activate_app_post_login(open_gamebar=True)

    def _on_logout(self):
        auth_state.log_out()
        self.gamebar.close()
        self.gamebar.update_auth_ui()
        self.login_window.show()
        print("[Auth] Signed out of Xsolla account. Returned to login launcher.")

    def run(self):
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.shutdown()

    def shutdown(self):
        print("\n[App] Shutting down Xsolla Game Recap...")
        if hasattr(self, 'login_window') and self.login_window:
            self.login_window.destroy()
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
