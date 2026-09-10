"""
Xsolla Game Recap - Enhanced Game Detection Engine
Monitors Windows processes and visible window titles across a 40+ game library.
Includes smart heuristics to automatically detect official and cracked games.
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

# Ignored system / tool processes that should never be detected as games
IGNORED_PROCESSES = {
    "explorer.exe", "svchost.exe", "chrome.exe", "firefox.exe", "msedge.exe",
    "code.exe", "devenv.exe", "cmd.exe", "powershell.exe", "conhost.exe",
    "taskmgr.exe", "discord.exe", "slack.exe", "spotify.exe", "steam.exe",
    "epicgameslauncher.exe", "python.exe", "pythonw.exe", "xsollagamerecap.exe",
    "xsolla_launcher.exe"
}

# Common game directory indicators for cracked / non-listed games
GAME_PATH_KEYWORDS = [
    "\\steamapps\\common\\", "\\epic games\\", "\\games\\", "\\game\\",
    "\\xboxgames\\", "\\riot games\\", "\\ubisoft game launcher\\",
    "\\gog games\\", "\\fitgirl\\", "\\dodi\\", "\\repack\\"
]


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

    def start_monitoring(self, interval_sec: float = 1.2):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._monitor_loop, args=(interval_sec,), daemon=True)
        self._thread.start()
        print("[Detector] Comprehensive Game Detection Engine active (40+ games + Smart Heuristics).")

    def stop_monitoring(self):
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
        if self._simulated_mode:
            return

        supported = self.get_supported_games()
        detected_game = None
        detected_pid = None
        detected_title = ""

        # Step 1: Scan visible top-level windows (catches games regardless of exe name!)
        visible_windows = []
        def enum_win_proc(hwnd, _):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd).strip()
                if title and len(title) > 2:
                    visible_windows.append((hwnd, title))
            return True

        try:
            win32gui.EnumWindows(enum_win_proc, None)
        except Exception:
            pass

        # Check window titles against our database
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

        # Step 2: Check active running processes by executable name
        if not detected_game:
            try:
                for proc in psutil.process_iter(['pid', 'name', 'exe']):
                    try:
                        pname = (proc.info.get('name') or '').lower()
                        if pname in IGNORED_PROCESSES:
                            continue

                        # Check database executables
                        for game in supported:
                            for exe in game.get("executables", []):
                                if exe.lower() == pname:
                                    detected_game = game
                                    detected_pid = proc.info.get('pid')
                                    detected_title = game.get('name')
                                    break
                            if detected_game:
                                break

                        # Step 3: Smart heuristic for unlisted cracked/standalone games
                        if not detected_game and proc.info.get('exe'):
                            exe_path = proc.info['exe'].lower()
                            # Check if located in a gaming folder or has shipping suffix
                            is_game_dir = any(kw in exe_path for kw in GAME_PATH_KEYWORDS)
                            is_shipping = "-shipping.exe" in pname
                            if (is_game_dir or is_shipping) and pname.endswith(".exe"):
                                clean_name = pname.replace(".exe", "").replace("-win64-shipping", "").replace("-shipping", "").title()
                                detected_game = {
                                    "id": f"auto_{pname}",
                                    "name": clean_name,
                                    "genre": "Detected Game",
                                    "icon": "🎮",
                                    "theme_color": "#70e1ff"
                                }
                                detected_pid = proc.info.get('pid')
                                detected_title = clean_name
                                break

                    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                        continue
                    if detected_game:
                        break
            except Exception as err:
                print(f"[Detector] Process scan exception: {err}")

        # Transition: Game Launched
        if detected_game and not self.active_game:
            self.active_game = detected_game
            self.active_pid = detected_pid
            self.active_window_title = detected_title or detected_game.get("name")
            self.session_start_time = time.time()
            print(f"[Detector] 🎮 Game Detected: {self.active_game['name']} (PID {self.active_pid})")
            if self.on_game_launched:
                self.on_game_launched(self.active_game, self.active_pid, self.active_window_title)

        # Transition: Game Closed
        elif not detected_game and self.active_game:
            closed_game = self.active_game
            print(f"[Detector] 🛑 Game Exited: {closed_game['name']}")
            self.active_game = None
            self.active_pid = None
            self.active_window_title = None
            self.session_start_time = None
            if self.on_game_closed:
                self.on_game_closed(closed_game)

    def simulate_launch(self, game_name_or_id: str = "hello_neighbor"):
        """For testing & hackathon demos: manually trigger game detection!"""
        supported = self.get_supported_games()
        target = None
        for g in supported:
            if g["id"].lower() == game_name_or_id.lower() or g["name"].lower() == game_name_or_id.lower():
                target = g
                break
        if not target:
            target = supported[0]

        self._simulated_mode = True
        self.active_game = target
        self.active_pid = 7777
        self.active_window_title = f"{target['name']} (Active Session)"
        self.session_start_time = time.time()
        print(f"[Detector] [SIMULATED] Launched: {target['name']}")
        if self.on_game_launched:
            self.on_game_launched(self.active_game, self.active_pid, self.active_window_title)

    def simulate_close(self):
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
        if not self.session_start_time:
            return "00:00:00"
        elapsed = int(time.time() - self.session_start_time)
        hrs = elapsed // 3600
        mins = (elapsed % 3600) // 60
        secs = elapsed % 60
        return f"{hrs:02d}:{mins:02d}:{secs:02d}"
