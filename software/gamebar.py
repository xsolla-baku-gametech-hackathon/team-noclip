"""
Xsolla Game Recap - In-Game Bar Overlay
Sleek, minimalist horizontal bar modeled after the NVIDIA GeForce Game Bar.
Displays the stacked Xsolla emblem, active game title, session duration,
and real time hardware telemetry. Zero emojis, zero clutter.
"""

import tkinter as tk
from PIL import Image, ImageTk
from typing import Optional, Callable

from config import ASSETS_DIR
from detector import GameDetector
from recap_manager import RecapManager


class GameBarOverlay:
    def __init__(self,
                 master: tk.Tk,
                 detector: GameDetector,
                 recap_mgr: RecapManager,
                 on_quit_app: Optional[Callable] = None):
        self.master = master
        self.detector = detector
        self.recap_mgr = recap_mgr
        self.on_quit_app = on_quit_app

        self.window: Optional[tk.Toplevel] = None
        self.is_open = False
        self._timer_job = None
        self._logo_photo = None
        self._drag_start_x = 0
        self._drag_start_y = 0

    def toggle(self):
        """Toggles the GameBar visibility."""
        self.master.after(0, self._do_toggle)

    def _do_toggle(self):
        if self.is_open and self.window and self.window.winfo_exists():
            self.close()
        else:
            self.open()

    def open(self):
        """Displays the horizontal NVIDIA style GameBar."""
        if self.window and self.window.winfo_exists():
            self.window.deiconify()
            self.window.lift()
            self.window.focus_force()
            self.is_open = True
            return

        self.is_open = True
        self.window = tk.Toplevel(self.master)
        self.window.title("Xsolla Game Recap")
        self.window.configure(bg="#0a0e14")

        # Frameless floating bar
        self.window.overrideredirect(True)
        self.window.attributes("-topmost", True)

        # Sleek Horizontal Bar Dimensions (NVIDIA style)
        width = 720
        height = 56
        sw = self.window.winfo_screenwidth()
        x = (sw - width) // 2
        y = 20
        self.window.geometry(f"{width}x{height}+{x}+{y}")

        self.window.bind("<Escape>", lambda e: self.close())

        self._build_bar(width, height)
        self._start_refresh_timer()

        self.window.lift()
        self.window.focus_force()

    def close(self):
        """Hides the GameBar."""
        self.is_open = False
        if self._timer_job:
            try:
                self.master.after_cancel(self._timer_job)
            except Exception:
                pass
            self._timer_job = None

        if self.window and self.window.winfo_exists():
            try:
                self.window.withdraw()
            except Exception:
                pass

    def _build_bar(self, width: int, height: int):
        # Outer Border Shell
        outer = tk.Frame(self.window, bg="#0a0e14", highlightthickness=1, highlightbackground="#70e1ff")
        outer.pack(fill="both", expand=True)

        bar = tk.Frame(outer, bg="#0d1117")
        bar.pack(fill="both", expand=True)

        bar.bind("<Button-1>", self._start_drag)
        bar.bind("<B1-Motion>", self._on_drag)

        # 1. Stacked Xsolla Logo (Mascot on top, XSOLLA wordmark below)
        logo_frame = tk.Frame(bar, bg="#0d1117", padx=14)
        logo_frame.pack(side="left", fill="y")
        logo_frame.bind("<Button-1>", self._start_drag)
        logo_frame.bind("<B1-Motion>", self._on_drag)

        logo_path = ASSETS_DIR / "xsolla_stacked_logo.png"
        if logo_path.exists():
            try:
                pil_logo = Image.open(str(logo_path))
                # Fit nicely within 42px height
                lh = 42
                lw = int(pil_logo.width * (lh / pil_logo.height))
                resized = pil_logo.resize((lw, lh), Image.Resampling.LANCZOS)
                self._logo_photo = ImageTk.PhotoImage(resized)
                lbl_logo = tk.Label(logo_frame, image=self._logo_photo, bg="#0d1117")
                lbl_logo.pack(side="left")
                lbl_logo.bind("<Button-1>", self._start_drag)
                lbl_logo.bind("<B1-Motion>", self._on_drag)
            except Exception:
                pass

        self._add_separator(bar)

        # 2. Game Section
        game_frame = tk.Frame(bar, bg="#0d1117", padx=16)
        game_frame.pack(side="left", fill="y")
        game_frame.bind("<Button-1>", self._start_drag)
        game_frame.bind("<B1-Motion>", self._on_drag)

        tk.Label(game_frame, text="GAME", font=("Segoe UI", 7, "bold"), fg="#8b949e", bg="#0d1117").pack(anchor="w", pady=(8, 0))
        self.game_lbl = tk.Label(game_frame, text="NO ACTIVE GAME", font=("Segoe UI", 10, "bold"), fg="#f0f6fc", bg="#0d1117")
        self.game_lbl.pack(anchor="w")

        self._add_separator(bar)

        # 3. Session Duration Section
        timer_frame = tk.Frame(bar, bg="#0d1117", padx=16)
        timer_frame.pack(side="left", fill="y")
        timer_frame.bind("<Button-1>", self._start_drag)
        timer_frame.bind("<B1-Motion>", self._on_drag)

        tk.Label(timer_frame, text="SESSION", font=("Segoe UI", 7, "bold"), fg="#8b949e", bg="#0d1117").pack(anchor="w", pady=(8, 0))
        self.timer_lbl = tk.Label(timer_frame, text="00:00:00", font=("Consolas", 11, "bold"), fg="#70e1ff", bg="#0d1117")
        self.timer_lbl.pack(anchor="w")

        self._add_separator(bar)

        # 4. Telemetry Metrics Section
        stats_frame = tk.Frame(bar, bg="#0d1117", padx=16)
        stats_frame.pack(side="left", fill="y")
        stats_frame.bind("<Button-1>", self._start_drag)
        stats_frame.bind("<B1-Motion>", self._on_drag)

        tk.Label(stats_frame, text="TELEMETRY", font=("Segoe UI", 7, "bold"), fg="#8b949e", bg="#0d1117").pack(anchor="w", pady=(8, 0))
        self.stats_lbl = tk.Label(stats_frame, text="RAM 0 MB  |  CPU 0.0%", font=("Segoe UI", 9), fg="#c9d1d9", bg="#0d1117")
        self.stats_lbl.pack(anchor="w")

        self._add_separator(bar)

        # 5. Status Section
        status_frame = tk.Frame(bar, bg="#0d1117", padx=16)
        status_frame.pack(side="left", fill="y")
        status_frame.bind("<Button-1>", self._start_drag)
        status_frame.bind("<B1-Motion>", self._on_drag)

        tk.Label(status_frame, text="STATUS", font=("Segoe UI", 7, "bold"), fg="#8b949e", bg="#0d1117").pack(anchor="w", pady=(8, 0))
        self.status_lbl = tk.Label(status_frame, text="IDLE", font=("Segoe UI", 9, "bold"), fg="#6e7681", bg="#0d1117")
        self.status_lbl.pack(anchor="w")

    def _add_separator(self, parent):
        sep = tk.Frame(parent, bg="#21262d", width=1)
        sep.pack(side="left", fill="y", pady=10)

    def _start_drag(self, event):
        self._drag_start_x = event.x
        self._drag_start_y = event.y

    def _on_drag(self, event):
        if self.window and self.window.winfo_exists():
            x = self.window.winfo_x() + (event.x - self._drag_start_x)
            y = self.window.winfo_y() + (event.y - self._drag_start_y)
            self.window.geometry(f"+{x}+{y}")

    def _start_refresh_timer(self):
        self._update_views()
        if self.is_open:
            self._timer_job = self.master.after(500, self._start_refresh_timer)

    def _update_views(self):
        if not self.window or not self.window.winfo_exists():
            return

        active = self.detector.active_game
        if active:
            duration = self.detector.get_session_duration_str()
            stats = self.detector.get_live_process_stats()
            self.game_lbl.config(text=active.get("name", "ACTIVE GAME").upper())
            self.timer_lbl.config(text=duration)
            self.stats_lbl.config(text=f"RAM {stats.get('ram_mb', 0)} MB  |  CPU {stats.get('cpu_pct', 0.0)}%")
            self.status_lbl.config(text="RECORDING", fg="#3fb950")
        else:
            self.game_lbl.config(text="NO ACTIVE GAME")
            self.timer_lbl.config(text="00:00:00")
            self.stats_lbl.config(text="RAM 0 MB  |  CPU 0.0%")
            self.status_lbl.config(text="IDLE", fg="#6e7681")
