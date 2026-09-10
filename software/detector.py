"""
Xsolla Game Recap - Game Detection Engine
Monitors Windows processes and visible window titles to instantly detect
when supported games launch or terminate. Supports both official Steam/Epic
installs and cracked/standalone/portable releases!
"""

import sys
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

import time
import threading
import psutil
from typing import Optional, Dict, Callable, List
import win32gui
import win32process

from config import load_config


class GameDetector:
    def __init__(self,
                 on_game_launched: Optional[Callable[[Dict, int, str], None]] = None,
                 on_game_closed: Optional[Callable[[Dict], None]] = None):
        self.on_game_launched = on_game_launched
        self.on_game_closed = on_game_closed
        self.active_game: Optional[Dict] = None
        self.active_pid: Optional[int] = None
        self.active_window_title: Optional[str] = None
        self.session_start_time: Optional[float] = None

        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._simulated_mode = False

    def get_supported_games(self) -> List[Dict]:
        cfg = load_config()
        return cfg.get("supported_games", []) + cfg.get("custom_games", [])

    def start_monitoring(self, interval_sec: float = 1.5):
        """Start the background monitoring thread."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._monitor_loop, args=(interval_sec,), daemon=True)
        self._thread.start()
        print("[Detector] Game detection engine started.")

    def stop_monitoring(self):
        """Stop background monitoring."""
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
        print("[Detector] Game detection engine stopped.")

    def _monitor_loop(self, interval_sec: float):
        while self._running:
            try:
                self.check_games()
            except Exception as err:
                print(f"[Detector] Polling error: {err}")
            time.sleep(interval_sec)

    def check_games(self):
        """Scan active processes and window titles against supported games."""
        if self._simulated_mode:
            return

        supported = self.get_supported_games()
        detected_game = None
        detected_pid = None
        detected_title = ""

        # Strategy 1: Check visible top-level windows (super reliable for cracked & renamed exes!)
        visible_windows = []
        def enum_win_proc(hwnd, _):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd).strip()
                if title:
                    visible_windows.append((hwnd, title))
            return True

        try:
            win32gui.EnumWindows(enum_win_proc, None)
        except Exception:
            pass

        # Check window titles first
        for hwnd, title in visible_windows:
            title_lower = title.lower()
            for game in supported:
                for kw in game.get("window_keywords", []):
                    if kw.lower() in title_lower:
                        try:
                            _, pid = win32process.GetWindowThreadProcessId(hwnd)
                            detected_game = game
                            detected_pid = pid
                            detected_title = title
                            break
                        except Exception:
                            pass
                if detected_game:
                    break
            if detected_game:
                break

        # Strategy 2: If no window matched, check running process names
        if not detected_game:
            try:
                for proc in psutil.process_iter(['pid', 'name']):
                    try:
                        pname = (proc.info.get('name') or '').lower()
                        for game in supported:
                            for exe in game.get("executables", []):
                                if exe.lower() == pname:
                                    detected_game = game
                                    detected_pid = proc.info.get('pid')
                                    detected_title = game.get('name')
                                    break
                            if detected_game:
                                break
                    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                        continue
                    if detected_game:
                        break
            except Exception as err:
                print(f"[Detector] Process scan exception: {err}")

        # State transition: Game Launched
        if detected_game and not self.active_game:
            self.active_game = detected_game
            self.active_pid = detected_pid
            self.active_window_title = detected_title or detected_game.get("name")
            self.session_start_time = time.time()
            print(f"[Detector] 🎮 Game Launched: {self.active_game['name']} (PID {self.active_pid})")
            if self.on_game_launched:
                self.on_game_launched(self.active_game, self.active_pid, self.active_window_title)

        # State transition: Game Closed
        elif not detected_game and self.active_game:
            closed_game = self.active_game
            print(f"[Detector] 🛑 Game Exited: {closed_game['name']}")
            self.active_game = None
            self.active_pid = None
            self.active_window_title = None
            self.session_start_time = None
            if self.on_game_closed:
                self.on_game_closed(closed_game)

    def simulate_launch(self, game_name_or_id: str = "stardew_valley"):
        """For testing & hackathon demos: manually trigger game detection!"""
        supported = self.get_supported_games()
        target = None
        for g in supported:
            if g["id"].lower() == game_name_or_id.lower() or g["name"].lower() == game_name_or_id.lower():
                target = g
                break
        if not target:
            target = supported[0] if supported else {
                "id": "stardew_valley",
                "name": "Stardew Valley",
                "genre": "Farming RPG",
                "icon": "🌾",
                "theme_color": "#ffb300"
            }

        self._simulated_mode = True
        self.active_game = target
        self.active_pid = 9999
        self.active_window_title = f"{target['name']} (Demo Session)"
        self.session_start_time = time.time()
        print(f"[Detector] [SIMULATED] Launched: {target['name']}")
        if self.on_game_launched:
            self.on_game_launched(self.active_game, self.active_pid, self.active_window_title)

    def simulate_close(self):
        """Manually trigger game close for testing."""
        if self.active_game:
            closed_game = self.active_game
            self.active_game = None
            self.active_pid = None
            self.session_start_time = None
            self._simulated_mode = False
            print(f"[Detector] [SIMULATED] Closed: {closed_game['name']}")
            if self.on_game_closed:
                self.on_game_closed(closed_game)

    def get_session_duration_str(self) -> str:
        """Returns format HH:MM:SS of current play session."""
        if not self.session_start_time:
            return "00:00:00"
        elapsed = int(time.time() - self.session_start_time)
        hrs = elapsed // 3600
        mins = (elapsed % 3600) // 60
        secs = elapsed % 60
        return f"{hrs:02d}:{mins:02d}:{secs:02d}"
