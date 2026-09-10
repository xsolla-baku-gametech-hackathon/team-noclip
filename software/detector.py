"""
Xsolla Game Recap - Dynamic Game Detection Engine
Monitors foreground windows and running processes in real time.
Identifies genuine game processes dynamically without static mock lists.
"""

import sys
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import time
import re
import threading
import psutil
from typing import Optional, Dict, Callable
import win32gui
import win32process

from config import load_config

# Common desktop and OS processes that are never games
IGNORED_PROCESSES = {
    "explorer.exe", "svchost.exe", "chrome.exe", "firefox.exe", "msedge.exe",
    "code.exe", "devenv.exe", "cmd.exe", "powershell.exe", "conhost.exe",
    "taskmgr.exe", "discord.exe", "slack.exe", "spotify.exe", "steam.exe",
    "steamwebhelper.exe", "epicgameslauncher.exe", "python.exe", "pythonw.exe",
    "xsollagamerecap.exe", "xsolla_launcher.exe", "shellexperiencehost.exe",
    "startmenuexperiencehost.exe", "searchhost.exe", "textinputhost.exe",
    "systemsettings.exe", "applicationframehost.exe", "dwm.exe", "fontdrvhost.exe",
    "ctfmon.exe", "lockapp.exe", "rundll32.exe", "windowsterminal.exe"
}

# Directories characteristic of game installations
GAME_PATH_MARKERS = [
    "\\steamapps\\common\\",
    "\\epic games\\",
    "\\xboxgames\\",
    "\\gog games\\",
    "\\riot games\\",
    "\\ubisoft\\",
    "\\games\\",
    "\\game\\",
    "\\repack\\",
    "\\fitgirl\\",
    "\\dodi\\",
    "\\ea games\\",
    "\\battlenet\\"
]


def clean_game_title(raw_name: str, window_title: str = "") -> str:
    """Derives a clean, human readable game title from process or window."""
    if window_title and len(window_title) > 2:
        low = window_title.lower()
        if not any(skip in low for skip in ["default ime", "msctfime", "nvidia", "overlay"]):
            return window_title.strip()

    name = raw_name
    if name.lower().endswith(".exe"):
        name = name[:-4]

    for suffix in ["_win64_shipping", "-win64-shipping", "_shipping", "-shipping", "_x64", "-x64", "_x86", "-x86", "win64", "win32"]:
        if name.lower().endswith(suffix):
            name = name[:-len(suffix)]

    # Split camelCase before lowercasing
    name = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", name)
    name = name.replace("_", " ").replace("-", " ")

    words = [w.capitalize() for w in name.split()]
    return " ".join(words).strip()


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
        self._cached_proc: Optional[psutil.Process] = None
        self._cached_config: Optional[Dict] = None
        self._last_config_load: float = 0.0

    def _get_config(self) -> Dict:
        now = time.time()
        if self._cached_config is None or (now - self._last_config_load) > 10.0:
            self._cached_config = load_config()
            self._last_config_load = now
        return self._cached_config

    def start_monitoring(self, interval_sec: float = 1.0):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._monitor_loop, args=(interval_sec,), daemon=True)
        self._thread.start()
        print("[Detector] Real time game monitoring active.")

    def stop_monitoring(self):
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
        print("[Detector] Game detector stopped.")

    def _monitor_loop(self, interval_sec: float):
        while self._running:
            try:
                self.check_active_game()
            except Exception as err:
                print(f"[Detector] Poll error: {err}")
            time.sleep(interval_sec)

    def check_active_game(self):
        """Scans the active foreground window and running processes."""
        detected = self._identify_foreground_game()

        # If no foreground game found, check if currently hooked game is still alive
        if not detected and self.active_pid:
            if self._is_pid_alive(self.active_pid):
                return
            else:
                self._handle_game_closed()
                return

        if detected:
            game_info, pid, title = detected
            if not self.active_game or self.active_pid != pid:
                self._handle_game_launched(game_info, pid, title)

    def _identify_foreground_game(self) -> Optional[tuple]:
        try:
            hwnd = win32gui.GetForegroundWindow()
            if not hwnd or not win32gui.IsWindowVisible(hwnd):
                return None

            title = win32gui.GetWindowText(hwnd).strip()
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            if not pid or pid == 0:
                return None

            proc = psutil.Process(pid)
            pname = proc.name().lower()
            if pname in IGNORED_PROCESSES:
                return None

            try:
                pexe = proc.exe().lower()
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                pexe = ""

            # Check if matching game path markers or shipping binary
            is_game_dir = any(marker in pexe for marker in GAME_PATH_MARKERS)
            is_shipping = "shipping" in pname
            cfg = self._get_config()
            custom_exes = [c.get("executable", "").lower() for c in cfg.get("custom_apps", [])]

            if is_game_dir or is_shipping or pname in custom_exes or self._is_likely_game(pname, title):
                clean_title = clean_game_title(pname, title)
                game_info = {
                    "id": pname.replace(".exe", ""),
                    "name": clean_title,
                    "executable": pname,
                    "path": pexe
                }
                return game_info, pid, clean_title

        except (psutil.NoSuchProcess, psutil.AccessDenied, Exception):
            pass

        return None

    def _is_likely_game(self, pname: str, title: str) -> bool:
        """Heuristics for standalone / direct game launches."""
        low_title = title.lower()
        low_pname = pname.lower()

        known_gaming_cues = [
            "neighbor", "custom night", "fnaf", "stardew", "undertale",
            "deltarune", "cuphead", "celeste", "hollow knight", "hades",
            "minecraft", "roblox", "cyberpunk", "gta", "elden ring",
            "valorant", "counter strike", "dota", "league of legends"
        ]
        if any(cue in low_title or cue in low_pname for cue in known_gaming_cues):
            return True

        return False

    def _is_pid_alive(self, pid: int) -> bool:
        try:
            proc = psutil.Process(pid)
            return proc.is_running() and proc.status() != psutil.STATUS_ZOMBIE
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return False

    def _handle_game_launched(self, game: Dict, pid: int, title: str):
        self.active_game = game
        self.active_pid = pid
        self.active_window_title = title
        self.session_start_time = time.time()
        try:
            self._cached_proc = psutil.Process(pid)
        except Exception:
            self._cached_proc = None

        print(f"[Detector] Game Hooked: {game['name']} (PID {pid})")
        if self.on_game_launched:
            self.on_game_launched(self.active_game, self.active_pid, self.active_window_title)

    def _handle_game_closed(self):
        closed = self.active_game
        print(f"[Detector] Game Exited: {closed.get('name') if closed else 'Unknown'}")
        self.active_game = None
        self.active_pid = None
        self.active_window_title = None
        self.session_start_time = None
        self._cached_proc = None

        if self.on_game_closed and closed:
            self.on_game_closed(closed)

    def get_live_process_stats(self) -> Dict:
        """Returns real live telemetry (RAM MB and CPU %)."""
        if not self.active_pid:
            return {"ram_mb": 0, "cpu_pct": 0.0}

        try:
            if not self._cached_proc or self._cached_proc.pid != self.active_pid:
                self._cached_proc = psutil.Process(self.active_pid)

            mem_bytes = self._cached_proc.memory_info().rss
            ram_mb = int(mem_bytes / (1024 * 1024))
            cpu_pct = round(self._cached_proc.cpu_percent(interval=None), 1)
            return {"ram_mb": ram_mb, "cpu_pct": cpu_pct}
        except Exception:
            return {"ram_mb": 0, "cpu_pct": 0.0}

    def get_session_duration_str(self) -> str:
        if not self.session_start_time:
            return "00:00:00"
        elapsed = int(time.time() - self.session_start_time)
        hrs = elapsed // 3600
        mins = (elapsed % 3600) // 60
        secs = elapsed % 60
        return f"{hrs:02d}:{mins:02d}:{secs:02d}"
