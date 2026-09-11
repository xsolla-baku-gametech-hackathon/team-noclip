"""
Xsolla Game Recap - In-Game Bar Overlay
Sleek, minimalist horizontal bar modeled after the NVIDIA GeForce Game Bar.
Displays the stacked Xsolla emblem, active game title, session duration,
and real time hardware telemetry.
Features a cinematic dim backdrop covering the screen when opened. Zero emojis, zero clutter.
"""

import tkinter as tk
from PIL import Image, ImageTk
from typing import Optional, Callable

from config import ASSETS_DIR, make_window_invisible_to_capture
from detector import GameDetector
from recap_manager import RecapManager
from polaroid_service import PolaroidService
from album_viewer import VisualMemoriesTab


class GameBarOverlay:
    def __init__(self,
                 master: tk.Tk,
                 detector: GameDetector,
                 recap_mgr: RecapManager,
                 polaroid_svc: Optional[PolaroidService] = None,
                 on_quit_app: Optional[Callable] = None,
                 on_capture: Optional[Callable] = None,
                 on_open_album: Optional[Callable] = None,
                 on_toggle_record: Optional[Callable] = None,
                 on_toggle_pause: Optional[Callable] = None,
                 video_recorder: Optional[object] = None):
        self.master = master
        self.detector = detector
        self.recap_mgr = recap_mgr
        self.polaroid_svc = polaroid_svc or PolaroidService()
        self.on_quit_app = on_quit_app
        self.on_capture = on_capture
        self.on_open_album = on_open_album or self.toggle_album
        self.on_toggle_record = on_toggle_record
        self.on_toggle_pause = on_toggle_pause
        self.video_rec = video_recorder
        self.btn_rec = None
        self.btn_snap = None
        self.btn_album = None
        self.rec_badge = None
        self.btn_pause = None
        self.btn_stop = None

        self.window: Optional[tk.Toplevel] = None
        self.backdrop: Optional[tk.Toplevel] = None
        self.outer = None
        self.bar = None
        self.tab_container = None
        self.visual_memories_tab: Optional[VisualMemoriesTab] = None
        self.is_open = False
        self.is_album_open = False
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

    def _show_backdrop(self):
        """Creates or shows the fullscreen semi-transparent dim backdrop."""
        try:
            import win32api
            import win32con
            x = win32api.GetSystemMetrics(win32con.SM_XVIRTUALSCREEN)
            y = win32api.GetSystemMetrics(win32con.SM_YVIRTUALSCREEN)
            w = win32api.GetSystemMetrics(win32con.SM_CXVIRTUALSCREEN)
            h = win32api.GetSystemMetrics(win32con.SM_CYVIRTUALSCREEN)
        except Exception:
            x, y = 0, 0
            w = self.master.winfo_screenwidth()
            h = self.master.winfo_screenheight()

        if not self.backdrop or not self.backdrop.winfo_exists():
            self.backdrop = tk.Toplevel(self.master)
            self.backdrop.title("Xsolla Dim Backdrop")
            self.backdrop.configure(bg="#000000")
            self.backdrop.overrideredirect(True)
            self.backdrop.attributes("-topmost", True)
            self.backdrop.attributes("-alpha", 0.55)  # Cinematic dim darkness (55% opacity)

            # Clicking anywhere on the dim background or pressing ESC closes the overlay
            self.backdrop.bind("<Button-1>", lambda e: self.close())
            self.backdrop.bind("<Escape>", lambda e: self.close())
            make_window_invisible_to_capture(self.backdrop)

        self.backdrop.geometry(f"{w}x{h}+{x}+{y}")
        self.backdrop.deiconify()
        self.backdrop.lift()
        make_window_invisible_to_capture(self.backdrop)

    def open(self, show_album: bool = False):
        """Displays the dim backdrop and the horizontal NVIDIA style GameBar."""
        self.is_open = True

        # 1. Show the dim backdrop behind the game
        self._show_backdrop()

        # 2. Show or create the GameBar window
        if self.window and self.window.winfo_exists():
            self.window.deiconify()
            if self.backdrop and self.backdrop.winfo_exists():
                self.backdrop.lift()
            self.window.lift()
            self.window.focus_force()
            self.update_recording_state()
            self._start_refresh_timer()
            if show_album and not self.is_album_open:
                self.toggle_album()
            make_window_invisible_to_capture(self.window)
            return

        self.window = tk.Toplevel(self.master)
        self.window.title("Xsolla Game Recap")
        self.window.configure(bg="#0a0e14")

        # Frameless floating bar
        self.window.overrideredirect(True)
        self.window.attributes("-topmost", True)

        # Sleek Horizontal Bar Dimensions (NVIDIA style)
        width = 980
        height = 660 if show_album else 56
        sw = self.window.winfo_screenwidth()
        x = (sw - width) // 2
        y = 20
        self.window.geometry(f"{width}x{height}+{x}+{y}")

        self.window.bind("<Escape>", lambda e: self._on_escape())

        self._build_bar(width, height)
        if show_album:
            self.toggle_album()
        self.update_recording_state()
        self._start_refresh_timer()

        # Stack order: backdrop behind, bar in front
        if self.backdrop and self.backdrop.winfo_exists():
            self.backdrop.lift()
        self.window.lift()
        self.window.focus_force()
        make_window_invisible_to_capture(self.window)

    def toggle_album(self):
        """Toggles the Visual Memories tab inside the GameBar navbar."""
        if not self.window or not self.window.winfo_exists():
            self.open(show_album=True)
            return

        self.is_album_open = not self.is_album_open
        cur_x = self.window.winfo_x()
        cur_y = self.window.winfo_y()

        if self.is_album_open:
            if self.tab_divider:
                self.tab_divider.pack(fill="x", side="top")
            if self.tab_container:
                self.tab_container.pack(fill="both", expand=True, side="top")
            if self.visual_memories_tab:
                self.visual_memories_tab.refresh()
            self.window.geometry(f"980x660+{cur_x}+{cur_y}")
            if self.btn_album and self.btn_album.winfo_exists():
                self.btn_album.config(bg="#70e1ff", fg="#0d1117", text="📸 VISUAL MEMORIES ▾")
            make_window_invisible_to_capture(self.window)
        else:
            if self.tab_divider:
                self.tab_divider.pack_forget()
            if self.tab_container:
                self.tab_container.pack_forget()
            self.window.geometry(f"980x56+{cur_x}+{cur_y}")
            if self.btn_album and self.btn_album.winfo_exists():
                self.btn_album.config(bg="#21262d", fg="#f0f6fc", text="📸 VISUAL MEMORIES")
            make_window_invisible_to_capture(self.window)

    def _on_escape(self):
        if self.visual_memories_tab and getattr(self.visual_memories_tab, "is_viewer_active", False):
            self.visual_memories_tab.close_viewer()
            return
        if self.is_album_open:
            self.toggle_album()
        else:
            self.close()

    def close(self):
        """Hides the GameBar and the dim backdrop."""
        self.is_open = False
        if self._timer_job:
            try:
                self.master.after_cancel(self._timer_job)
            except Exception:
                pass
            self._timer_job = None

        if self.window and self.window.winfo_exists():
            try:
                if self.is_album_open:
                    self.toggle_album()
                self.window.withdraw()
            except Exception:
                pass

        self.hide_backdrop()

    def hide_backdrop(self):
        """Hides the dim backdrop shadow."""
        if self.backdrop and self.backdrop.winfo_exists():
            try:
                self.backdrop.withdraw()
            except Exception:
                pass

    def get_backdrop_hwnd(self) -> Optional[int]:
        """Returns the Win32 HWND of the dim backdrop overlay window."""
        if self.backdrop and self.backdrop.winfo_exists():
            try:
                return int(self.backdrop.wm_frame(), 16)
            except Exception:
                try:
                    return self.backdrop.winfo_id()
                except Exception:
                    pass
        return None

    def get_window_hwnd(self) -> Optional[int]:
        """Returns the Win32 HWND of the GameBar overlay window."""
        if self.window and self.window.winfo_exists():
            try:
                return int(self.window.wm_frame(), 16)
            except Exception:
                try:
                    return self.window.winfo_id()
                except Exception:
                    pass
        return None

    def _on_open_folder_requested(self):
        """Elevates the recordings folder on top of everything without removing the shadow."""
        if self.visual_memories_tab:
            self.visual_memories_tab._open_recordings_folder()

    def _build_bar(self, width: int, height: int):
        # Outer Border Shell
        self.outer = tk.Frame(self.window, bg="#0a0e14", highlightthickness=1, highlightbackground="#70e1ff")
        self.outer.pack(fill="both", expand=True)

        self.bar = tk.Frame(self.outer, bg="#0d1117", height=54)
        self.bar.pack(fill="x", side="top")
        self.bar.pack_propagate(False)

        self.bar.bind("<Button-1>", self._start_drag)
        self.bar.bind("<B1-Motion>", self._on_drag)

        # 1. Standalone Clean Xsolla Logo
        logo_frame = tk.Frame(self.bar, bg="#0d1117", padx=14)
        logo_frame.pack(side="left", fill="y")
        logo_frame.bind("<Button-1>", self._start_drag)
        logo_frame.bind("<B1-Motion>", self._on_drag)

        logo_path = ASSETS_DIR / "xsolla_mascot_clean.png"
        if not logo_path.exists():
            logo_path = ASSETS_DIR / "xsolla_logo.png"

        if logo_path.exists():
            try:
                with Image.open(str(logo_path)) as pil_logo:
                    # Clean standalone logo sized to fit 36px height
                    lh = 36
                    lw = int(pil_logo.width * (lh / pil_logo.height))
                    resized = pil_logo.resize((lw, lh), Image.Resampling.LANCZOS)
                    self._logo_photo = ImageTk.PhotoImage(resized)
                    lbl_logo = tk.Label(logo_frame, image=self._logo_photo, bg="#0d1117")
                    lbl_logo.pack(side="left", pady=10)
                    lbl_logo.bind("<Button-1>", self._start_drag)
                    lbl_logo.bind("<B1-Motion>", self._on_drag)
            except Exception:
                pass

        self._add_separator(self.bar)

        # 2. Game Section
        game_frame = tk.Frame(self.bar, bg="#0d1117", padx=16)
        game_frame.pack(side="left", fill="y")
        game_frame.bind("<Button-1>", self._start_drag)
        game_frame.bind("<B1-Motion>", self._on_drag)

        tk.Label(game_frame, text="GAME", font=("Segoe UI", 7, "bold"), fg="#8b949e", bg="#0d1117").pack(anchor="w", pady=(8, 0))
        self.game_lbl = tk.Label(game_frame, text="NO ACTIVE GAME", font=("Segoe UI", 10, "bold"), fg="#f0f6fc", bg="#0d1117")
        self.game_lbl.pack(anchor="w")

        self._add_separator(self.bar)

        # 3. Session Duration Section
        timer_frame = tk.Frame(self.bar, bg="#0d1117", padx=16)
        timer_frame.pack(side="left", fill="y")
        timer_frame.bind("<Button-1>", self._start_drag)
        timer_frame.bind("<B1-Motion>", self._on_drag)

        tk.Label(timer_frame, text="SESSION", font=("Segoe UI", 7, "bold"), fg="#8b949e", bg="#0d1117").pack(anchor="w", pady=(8, 0))
        self.timer_lbl = tk.Label(timer_frame, text="00:00:00", font=("Consolas", 11, "bold"), fg="#70e1ff", bg="#0d1117")
        self.timer_lbl.pack(anchor="w")

        self._add_separator(self.bar)

        # 4. Telemetry Metrics Section
        stats_frame = tk.Frame(self.bar, bg="#0d1117", padx=16)
        stats_frame.pack(side="left", fill="y")
        stats_frame.bind("<Button-1>", self._start_drag)
        stats_frame.bind("<B1-Motion>", self._on_drag)

        tk.Label(stats_frame, text="TELEMETRY", font=("Segoe UI", 7, "bold"), fg="#8b949e", bg="#0d1117").pack(anchor="w", pady=(8, 0))
        self.stats_lbl = tk.Label(stats_frame, text="RAM 0 MB  |  CPU 0.0%", font=("Segoe UI", 9), fg="#c9d1d9", bg="#0d1117")
        self.stats_lbl.pack(anchor="w")

        self._add_separator(self.bar)

        # 5. Status Section
        status_frame = tk.Frame(self.bar, bg="#0d1117", padx=16)
        status_frame.pack(side="left", fill="y")
        status_frame.bind("<Button-1>", self._start_drag)
        status_frame.bind("<B1-Motion>", self._on_drag)

        tk.Label(status_frame, text="STATUS", font=("Segoe UI", 7, "bold"), fg="#8b949e", bg="#0d1117").pack(anchor="w", pady=(8, 0))
        self.status_lbl = tk.Label(status_frame, text="IDLE", font=("Segoe UI", 9, "bold"), fg="#6e7681", bg="#0d1117")
        self.status_lbl.pack(anchor="w")

        self._add_separator(self.bar)

        # 6. Quick Action Buttons: [📸 SNAP] & [📸 VISUAL MEMORIES]
        action_frame = tk.Frame(self.bar, bg="#0d1117", padx=12)
        action_frame.pack(side="left", fill="y")
        action_frame.bind("<Button-1>", self._start_drag)
        action_frame.bind("<B1-Motion>", self._on_drag)

        # Standard Idle Controls
        self.btn_snap = tk.Label(
            action_frame,
            text="📸 SNAP (F11)",
            font=("Segoe UI", 8, "bold"),
            fg="#f0f6fc",
            bg="#21262d",
            cursor="hand2",
            padx=10,
            pady=4
        )
        if self.on_capture:
            self.btn_snap.bind("<Button-1>", lambda e: self.on_capture())
        self.btn_snap.bind("<Enter>", lambda e: self.btn_snap.config(bg="#70e1ff", fg="#0d1117"))
        self.btn_snap.bind("<Leave>", lambda e: self.btn_snap.config(bg="#21262d", fg="#f0f6fc"))

        self.btn_rec = tk.Label(
            action_frame,
            text="🔴 REC (F9)",
            font=("Segoe UI", 8, "bold"),
            fg="#ff5c5c",
            bg="#21262d",
            cursor="hand2",
            padx=10,
            pady=4
        )
        if self.on_toggle_record:
            self.btn_rec.bind("<Button-1>", lambda e: self.on_toggle_record())
        self.btn_rec.bind("<Enter>", lambda e: self._on_rec_hover(True))
        self.btn_rec.bind("<Leave>", lambda e: self._on_rec_hover(False))

        self.btn_album = tk.Label(
            action_frame,
            text="📸 VISUAL MEMORIES",
            font=("Segoe UI", 8, "bold"),
            fg="#f0f6fc",
            bg="#21262d",
            cursor="hand2",
            padx=10,
            pady=4
        )
        self.btn_album.bind("<Button-1>", lambda e: self.toggle_album())
        self.btn_album.bind("<Enter>", lambda e: self._on_album_hover(True))
        self.btn_album.bind("<Leave>", lambda e: self._on_album_hover(False))

        # Active Video Recording Controls (Only shown during video recording)
        self.rec_badge = tk.Label(
            action_frame,
            text="🔴 REC 00:00",
            font=("Segoe UI", 8, "bold"),
            fg="#ff5c5c",
            bg="#251217",
            padx=8,
            pady=4
        )

        self.btn_pause = tk.Label(
            action_frame,
            text="⏸️ PAUSE (F10)",
            font=("Segoe UI", 8, "bold"),
            fg="#f0f6fc",
            bg="#21262d",
            cursor="hand2",
            padx=10,
            pady=4
        )
        if self.on_toggle_pause:
            self.btn_pause.bind("<Button-1>", lambda e: self.on_toggle_pause())
        self.btn_pause.bind("<Enter>", lambda e: self._on_pause_hover(True))
        self.btn_pause.bind("<Leave>", lambda e: self._on_pause_hover(False))

        self.btn_stop = tk.Label(
            action_frame,
            text="⏹️ STOP (F9)",
            font=("Segoe UI", 8, "bold"),
            fg="#ffffff",
            bg="#da3633",
            cursor="hand2",
            padx=10,
            pady=4
        )
        if self.on_toggle_record:
            self.btn_stop.bind("<Button-1>", lambda e: self.on_toggle_record())
        self.btn_stop.bind("<Enter>", lambda e: self.btn_stop.config(bg="#b62324"))
        self.btn_stop.bind("<Leave>", lambda e: self.btn_stop.config(bg="#da3633"))

        # Initial layout: standard buttons shown
        self.btn_snap.pack(side="left", pady=12, padx=3)
        self.btn_rec.pack(side="left", pady=12, padx=3)
        self.btn_album.pack(side="left", pady=12, padx=3)

        # 7. Close Button [X] on the far right
        close_frame = tk.Frame(self.bar, bg="#0d1117", padx=12)
        close_frame.pack(side="right", fill="y")
        btn_close = tk.Label(
            close_frame,
            text="✕",
            font=("Segoe UI", 11, "bold"),
            fg="#8b949e",
            bg="#0d1117",
            cursor="hand2",
            padx=8,
            pady=4
        )
        btn_close.pack(anchor="center", expand=True)
        btn_close.bind("<Button-1>", lambda e: self.close())
        btn_close.bind("<Enter>", lambda e: btn_close.config(fg="#ff5c5c", bg="#21262d"))
        btn_close.bind("<Leave>", lambda e: btn_close.config(fg="#8b949e", bg="#0d1117"))

        # 8. Visual Memories Integrated Tab Panel (Expands directly below navbar)
        self.tab_divider = tk.Frame(self.outer, bg="#1a2230", height=1)
        self.tab_container = tk.Frame(self.outer, bg="#080b10")

        self.visual_memories_tab = VisualMemoriesTab(
            self.tab_container,
            polaroid_svc=self.polaroid_svc,
            on_capture_request=self.on_capture,
            on_record_request=self.on_toggle_record,
            on_pause_request=self.on_toggle_pause,
            on_close_tab=self.toggle_album,
            on_open_folder=self._on_open_folder_requested,
            get_backdrop_hwnd=self.get_backdrop_hwnd,
            get_window_hwnd=self.get_window_hwnd,
            video_recorder=self.video_rec
        )
        self.visual_memories_tab.pack(fill="both", expand=True)

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

    def _on_rec_hover(self, is_hovered: bool):
        if not self.btn_rec or not self.btn_rec.winfo_exists():
            return
        self.btn_rec.config(bg="#ff3b30" if is_hovered else "#21262d", fg="#ffffff" if is_hovered else "#ff5c5c")

    def _on_pause_hover(self, is_hovered: bool):
        if not self.btn_pause or not self.btn_pause.winfo_exists():
            return
        is_paused = bool(self.video_rec and getattr(self.video_rec, "is_paused", False))
        if is_paused:
            self.btn_pause.config(bg="#2ea043" if is_hovered else "#238636")
        else:
            self.btn_pause.config(bg="#30363d" if is_hovered else "#21262d")

    def _on_album_hover(self, is_hovered: bool):
        if not self.btn_album or not self.btn_album.winfo_exists():
            return
        if self.is_album_open:
            self.btn_album.config(bg="#5bd2f0" if is_hovered else "#70e1ff", fg="#0d1117")
        else:
            self.btn_album.config(bg="#30363d" if is_hovered else "#21262d", fg="#ffffff" if is_hovered else "#f0f6fc")

    def update_recording_state(self):
        """Swaps UI buttons: hides SNAP & ALBUM, shows PAUSE & STOP during video recording."""
        if not self.window or not self.window.winfo_exists():
            return

        is_rec = bool(self.video_rec and self.video_rec.is_recording)
        is_paused = bool(self.video_rec and getattr(self.video_rec, "is_paused", False))
        duration = self.video_rec.get_duration_str() if self.video_rec else "00:00"

        if is_rec:
            # Hide screenshot and album buttons completely
            if self.btn_snap and self.btn_snap.winfo_ismapped():
                self.btn_snap.pack_forget()
            if self.btn_album and self.btn_album.winfo_ismapped():
                self.btn_album.pack_forget()
            if self.btn_rec and self.btn_rec.winfo_ismapped():
                self.btn_rec.pack_forget()

            # Display recording badge, pause button, and stop button
            if self.rec_badge and not self.rec_badge.winfo_ismapped():
                self.rec_badge.pack(side="left", pady=12, padx=4)
            if self.btn_pause and not self.btn_pause.winfo_ismapped():
                self.btn_pause.pack(side="left", pady=12, padx=4)
            if self.btn_stop and not self.btn_stop.winfo_ismapped():
                self.btn_stop.pack(side="left", pady=12, padx=4)

            # Update live texts
            if is_paused:
                self.rec_badge.config(text=f"⏸️ PAUSED {duration}", fg="#ffcc00", bg="#2b2308")
                self.btn_pause.config(text="▶️ RESUME (F10)", bg="#238636", fg="#ffffff")
            else:
                self.rec_badge.config(text=f"🔴 REC {duration}", fg="#ff5c5c", bg="#251217")
                self.btn_pause.config(text="⏸️ PAUSE (F10)", bg="#21262d", fg="#f0f6fc")

            self.btn_stop.config(text="⏹️ STOP (F9)", bg="#da3633", fg="#ffffff")

        else:
            # Hide recording badge, pause button, and stop button
            if self.rec_badge and self.rec_badge.winfo_ismapped():
                self.rec_badge.pack_forget()
            if self.btn_pause and self.btn_pause.winfo_ismapped():
                self.btn_pause.pack_forget()
            if self.btn_stop and self.btn_stop.winfo_ismapped():
                self.btn_stop.pack_forget()

            # Restore screenshot and album buttons
            if self.btn_snap and not self.btn_snap.winfo_ismapped():
                self.btn_snap.pack(side="left", pady=12, padx=3)
            if self.btn_rec and not self.btn_rec.winfo_ismapped():
                self.btn_rec.pack(side="left", pady=12, padx=3)
            if self.btn_album and not self.btn_album.winfo_ismapped():
                self.btn_album.pack(side="left", pady=12, padx=3)

    def _start_refresh_timer(self):
        self._update_views()
        if self.is_open:
            self._timer_job = self.master.after(500, self._start_refresh_timer)

    def _update_views(self):
        if not self.window or not self.window.winfo_exists():
            return

        self.update_recording_state()

        active = self.detector.active_game
        if active:
            duration = self.detector.get_session_duration_str()
            stats = self.detector.get_live_process_stats()
            self.game_lbl.config(text=active.get("name", "ACTIVE GAME").upper())
            self.timer_lbl.config(text=duration)
            self.stats_lbl.config(text=f"RAM {stats.get('ram_mb', 0)} MB  |  CPU {stats.get('cpu_pct', 0.0)}%")
            self.status_lbl.config(text="ACTIVE", fg="#3fb950")
        else:
            self.game_lbl.config(text="NO ACTIVE GAME")
            self.timer_lbl.config(text="00:00:00")
            self.stats_lbl.config(text="RAM 0 MB  |  CPU 0.0%")
            self.status_lbl.config(text="IDLE", fg="#6e7681")
