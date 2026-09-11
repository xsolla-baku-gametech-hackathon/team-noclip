"""
Xsolla Game Recap - Settings & Recording Configuration Panel
Allows configuring video recording FPS, container format, and GameBar capture visibility.
Provides bidirectional synchronization with the website dashboard.
"""

import webbrowser
import threading
import tkinter as tk
from typing import Optional, Callable, Dict, Any

from config import (
    get_recording_settings,
    update_recording_settings,
    sync_settings_with_cloud,
    WEBSITE_LOGIN_URL
)
import auth_state


class SettingsTab(tk.Frame):
    def __init__(self,
                 parent: tk.Widget,
                 on_close_tab: Optional[Callable[[], None]] = None,
                 on_settings_changed: Optional[Callable[[Dict[str, Any]], None]] = None,
                 on_toast: Optional[Callable[[str, str], None]] = None):
        super().__init__(parent, bg="#080b10")
        self.on_close_tab = on_close_tab
        self.on_settings_changed = on_settings_changed
        self.on_toast = on_toast or (lambda msg, color="#70e1ff": None)

        self.current_settings = get_recording_settings()
        self.fps_buttons: Dict[int, Any] = {}
        self.chk_gamebar_var = tk.BooleanVar(value=self.current_settings.get("include_gamebar_in_recording", True))
        self.sync_status_lbl: Optional[tk.Label] = None

        self._build_ui()

    def refresh(self):
        """Reloads settings from disk and refreshes the UI."""
        self.current_settings = get_recording_settings()
        cur_fps = self.current_settings.get("recording_fps", 30)
        self._update_fps_button_styles(cur_fps)
        self.chk_gamebar_var.set(self.current_settings.get("include_gamebar_in_recording", True))
        self._update_sync_status("Ready to sync with website dashboard", color="#8b949e")

    def _build_ui(self):
        for w in self.winfo_children():
            w.destroy()

        # 1. Header Bar
        header = tk.Frame(self, bg="#0d1117", height=52, padx=20)
        header.pack(fill="x", side="top")
        header.pack_propagate(False)

        left_h = tk.Frame(header, bg="#0d1117")
        left_h.pack(side="left", fill="y")

        tk.Label(
            left_h,
            text="⚙️ CAPTURE & RECORDING SETTINGS",
            font=("Segoe UI", 11, "bold"),
            fg="#70e1ff",
            bg="#0d1117"
        ).pack(side="left", pady=14)

        tk.Label(
            left_h,
            text="•  Synced with Website Dashboard",
            font=("Segoe UI", 8),
            fg="#56d364",
            bg="#0d1117"
        ).pack(side="left", padx=(10, 0), pady=16)

        if self.on_close_tab:
            btn_close = tk.Label(
                header,
                text="✕ CLOSE",
                font=("Segoe UI", 9, "bold"),
                fg="#8b949e",
                bg="#21262d",
                cursor="hand2",
                padx=12,
                pady=6
            )
            btn_close.pack(side="right", pady=10)
            btn_close.bind("<Button-1>", lambda e: self.on_close_tab())
            btn_close.bind("<Enter>", lambda e: btn_close.config(bg="#da3633", fg="#ffffff"))
            btn_close.bind("<Leave>", lambda e: btn_close.config(bg="#21262d", fg="#8b949e"))

        # 2. Main Scrollable/Padded Body
        body = tk.Frame(self, bg="#080b10", padx=24, pady=18)
        body.pack(fill="both", expand=True)

        grid_frame = tk.Frame(body, bg="#080b10")
        grid_frame.pack(fill="both", expand=True)

        # Left Column (FPS & GameBar Visibility)
        col_left = tk.Frame(grid_frame, bg="#080b10")
        col_left.pack(side="left", fill="both", expand=True, padx=(0, 12))

        # Right Column (Format & Cloud Sync)
        col_right = tk.Frame(grid_frame, bg="#080b10")
        col_right.pack(side="left", fill="both", expand=True, padx=(12, 0))

        # --- CARD 1: FPS Settings Format ---
        card_fps = tk.Frame(col_left, bg="#0d1117", highlightthickness=1, highlightbackground="#21262d", padx=16, pady=14)
        card_fps.pack(fill="x", pady=(0, 16))

        tk.Label(
            card_fps,
            text="🎞️ RECORDING FRAMERATE (FPS)",
            font=("Segoe UI", 9, "bold"),
            fg="#f0f6fc",
            bg="#0d1117"
        ).pack(anchor="w")

        tk.Label(
            card_fps,
            text="Choose your target framerate for in-game video clips and highlights.",
            font=("Segoe UI", 8),
            fg="#8b949e",
            bg="#0d1117"
        ).pack(anchor="w", pady=(2, 10))

        fps_row = tk.Frame(card_fps, bg="#0d1117")
        fps_row.pack(fill="x", pady=(0, 8))

        fps_options = [
            (20, "20 FPS", "Low CPU / Eco"),
            (30, "30 FPS", "Standard (Default)"),
            (60, "60 FPS", "Ultra Smooth")
        ]

        cur_fps = self.current_settings.get("recording_fps", 30)
        self.fps_buttons = {}

        for fps_val, label_text, subtext in fps_options:
            pill_frame = tk.Frame(fps_row, bg="#161b22", highlightthickness=1, highlightbackground="#30363d", padx=10, pady=8)
            pill_frame.pack(side="left", fill="x", expand=True, padx=4)

            lbl_main = tk.Label(
                pill_frame,
                text=label_text,
                font=("Segoe UI", 10, "bold"),
                fg="#c9d1d9",
                bg="#161b22",
                cursor="hand2"
            )
            lbl_main.pack()

            lbl_sub = tk.Label(
                pill_frame,
                text=subtext,
                font=("Segoe UI", 7),
                fg="#8b949e",
                bg="#161b22",
                cursor="hand2"
            )
            lbl_sub.pack()

            for w in (pill_frame, lbl_main, lbl_sub):
                w.bind("<Button-1>", lambda e, f=fps_val: self._select_fps(f))

            self.fps_buttons[fps_val] = (pill_frame, lbl_main, lbl_sub)

        self._update_fps_button_styles(cur_fps)

        # --- CARD 2: GameBar In-Recording Visibility ---
        card_vis = tk.Frame(col_left, bg="#0d1117", highlightthickness=1, highlightbackground="#21262d", padx=16, pady=14)
        card_vis.pack(fill="x")

        tk.Label(
            card_vis,
            text="🎮 GAMEBAR RECORDING VISIBILITY",
            font=("Segoe UI", 9, "bold"),
            fg="#f0f6fc",
            bg="#0d1117"
        ).pack(anchor="w")

        tk.Label(
            card_vis,
            text="Control whether the in-game HUD overlay is captured inside screen recordings.",
            font=("Segoe UI", 8),
            fg="#8b949e",
            bg="#0d1117"
        ).pack(anchor="w", pady=(2, 10))

        chk_frame = tk.Frame(card_vis, bg="#161b22", highlightthickness=1, highlightbackground="#30363d", padx=12, pady=10)
        chk_frame.pack(fill="x")

        chk = tk.Checkbutton(
            chk_frame,
            text=" Include GameBar HUD overlay in video recording",
            variable=self.chk_gamebar_var,
            command=self._on_gamebar_toggle_changed,
            font=("Segoe UI", 9, "bold"),
            fg="#70e1ff",
            bg="#161b22",
            selectcolor="#0d1117",
            activebackground="#161b22",
            activeforeground="#70e1ff",
            cursor="hand2"
        )
        chk.pack(anchor="w")

        # Dynamic shortcut explanation tip
        tip_frame = tk.Frame(card_vis, bg="#080b10", padx=10, pady=8)
        tip_frame.pack(fill="x", pady=(10, 0))

        tk.Label(
            tip_frame,
            text="💡 Hotkey Tip: When enabled, the GameBar appears in your recording. Pressing Ctrl+Shift+X hides the GameBar from your screen and instantly removes it from the recording!",
            font=("Segoe UI", 8),
            fg="#7ee787",
            bg="#080b10",
            wraplength=460,
            justify="left"
        ).pack(anchor="w")

        # --- CARD 3: Video Format ---
        card_fmt = tk.Frame(col_right, bg="#0d1117", highlightthickness=1, highlightbackground="#21262d", padx=16, pady=14)
        card_fmt.pack(fill="x", pady=(0, 16))

        tk.Label(
            card_fmt,
            text="📦 VIDEO ENCODING FORMAT",
            font=("Segoe UI", 9, "bold"),
            fg="#f0f6fc",
            bg="#0d1117"
        ).pack(anchor="w")

        tk.Label(
            card_fmt,
            text="Standard MP4 (H.264 / mp4v) for universal streaming, editing, and sharing.",
            font=("Segoe UI", 8),
            fg="#8b949e",
            bg="#0d1117"
        ).pack(anchor="w", pady=(2, 10))

        fmt_box = tk.Frame(card_fmt, bg="#161b22", highlightthickness=1, highlightbackground="#70e1ff", padx=12, pady=8)
        fmt_box.pack(fill="x")
        tk.Label(
            fmt_box,
            text="✓  MP4 Container (H.264 High Profile / mp4v)",
            font=("Segoe UI", 9, "bold"),
            fg="#70e1ff",
            bg="#161b22"
        ).pack(side="left")
        tk.Label(
            fmt_box,
            text="Discord / YouTube Ready",
            font=("Segoe UI", 7),
            fg="#8b949e",
            bg="#161b22"
        ).pack(side="right")

        # --- CARD 4: Cloud Sync & Website Dashboard ---
        card_sync = tk.Frame(col_right, bg="#0d1117", highlightthickness=1, highlightbackground="#21262d", padx=16, pady=14)
        card_sync.pack(fill="x")

        tk.Label(
            card_sync,
            text="🌐 WEBSITE DASHBOARD SYNC",
            font=("Segoe UI", 9, "bold"),
            fg="#f0f6fc",
            bg="#0d1117"
        ).pack(anchor="w")

        user_label = auth_state.get_user_label()
        is_logged = auth_state.is_logged_in()
        status_text = f"Connected as {user_label}" if is_logged else "Connected as Guest Player"

        tk.Label(
            card_sync,
            text=f"🟢 {status_text}",
            font=("Segoe UI", 8, "bold"),
            fg="#56d364" if is_logged else "#8b949e",
            bg="#0d1117"
        ).pack(anchor="w", pady=(2, 6))

        self.sync_status_lbl = tk.Label(
            card_sync,
            text="Sync FPS & recording preferences with team-noclip.vercel.app",
            font=("Segoe UI", 7),
            fg="#8b949e",
            bg="#0d1117"
        )
        self.sync_status_lbl.pack(anchor="w", pady=(0, 10))

        btn_row = tk.Frame(card_sync, bg="#0d1117")
        btn_row.pack(fill="x")

        # Sync button
        btn_sync = tk.Label(
            btn_row,
            text="🔄 SYNC WITH WEBSITE",
            font=("Segoe UI", 8, "bold"),
            fg="#0d1117",
            bg="#70e1ff",
            cursor="hand2",
            padx=12,
            pady=8
        )
        btn_sync.pack(side="left", fill="x", expand=True, padx=(0, 6))
        btn_sync.bind("<Button-1>", lambda e: self._on_sync_clicked())
        btn_sync.bind("<Enter>", lambda e: btn_sync.config(bg="#38bdf8"))
        btn_sync.bind("<Leave>", lambda e: btn_sync.config(bg="#70e1ff"))

        # Open Web Dashboard button
        btn_open_web = tk.Label(
            btn_row,
            text="🌐 OPEN DASHBOARD",
            font=("Segoe UI", 8, "bold"),
            fg="#f0f6fc",
            bg="#21262d",
            cursor="hand2",
            padx=12,
            pady=8
        )
        btn_open_web.pack(side="left", fill="x", expand=True, padx=(6, 0))
        btn_open_web.bind("<Button-1>", lambda e: self._open_web_dashboard())
        btn_open_web.bind("<Enter>", lambda e: btn_open_web.config(bg="#30363d"))
        btn_open_web.bind("<Leave>", lambda e: btn_open_web.config(bg="#21262d"))

    def _update_fps_button_styles(self, active_fps: int):
        for fps_val, (frame, lbl_main, lbl_sub) in self.fps_buttons.items():
            if fps_val == active_fps:
                frame.config(bg="#70e1ff", highlightbackground="#70e1ff")
                lbl_main.config(fg="#0d1117", bg="#70e1ff")
                lbl_sub.config(fg="#0d1117", bg="#70e1ff")
            else:
                frame.config(bg="#161b22", highlightbackground="#30363d")
                lbl_main.config(fg="#c9d1d9", bg="#161b22")
                lbl_sub.config(fg="#8b949e", bg="#161b22")

    def _select_fps(self, fps: int):
        self.current_settings["recording_fps"] = fps
        update_recording_settings({"recording_fps": fps})
        self._update_fps_button_styles(fps)
        self.on_toast(f"Recording framerate set to {fps} FPS", "#70e1ff")
        if self.on_settings_changed:
            self.on_settings_changed(self.current_settings)

    def _on_gamebar_toggle_changed(self):
        val = bool(self.chk_gamebar_var.get())
        self.current_settings["include_gamebar_in_recording"] = val
        update_recording_settings({"include_gamebar_in_recording": val})
        msg = "GameBar HUD will appear in recordings" if val else "GameBar HUD excluded from recordings"
        self.on_toast(msg, "#70e1ff")
        if self.on_settings_changed:
            self.on_settings_changed(self.current_settings)

    def _on_sync_clicked(self):
        self._update_sync_status("Syncing with website dashboard...", color="#70e1ff")

        def _do_sync():
            token = auth_state.get_auth_token()
            res = sync_settings_with_cloud(token)
            self.after(0, lambda: self._on_sync_complete(res))

        threading.Thread(target=_do_sync, daemon=True).start()

    def _on_sync_complete(self, updated_settings: dict):
        self.current_settings = updated_settings
        cur_fps = updated_settings.get("recording_fps", 30)
        self._update_fps_button_styles(cur_fps)
        self.chk_gamebar_var.set(updated_settings.get("include_gamebar_in_recording", True))
        self._update_sync_status("✓ Successfully synchronized with website dashboard", color="#56d364")
        self.on_toast("Settings synchronized with website dashboard!", "#56d364")
        if self.on_settings_changed:
            self.on_settings_changed(updated_settings)

    def _update_sync_status(self, text: str, color: str = "#8b949e"):
        if self.sync_status_lbl and self.sync_status_lbl.winfo_exists():
            self.sync_status_lbl.config(text=text, fg=color)

    def _open_web_dashboard(self):
        url = WEBSITE_LOGIN_URL.replace("/login", "/dashboard")
        webbrowser.open(url)
