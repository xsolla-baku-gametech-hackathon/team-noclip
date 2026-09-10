"""
Xsolla Game Recap - Futuristic In-Game GameBar HUD
Sleek, minimalist, frameless overlay modeled directly after Nvidia GeForce Experience & Xbox Game Bar.
Features official Xsolla branding, live game session tracking, snapshot capture, and clean tray minimization.
"""

import time
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
from typing import Optional, Callable

from config import load_config, add_custom_game, ASSETS_DIR
from detector import GameDetector
from recap_manager import RecapManager


class GameBarOverlay:
    def __init__(self,
                 master: tk.Tk,
                 detector: GameDetector,
                 recap_mgr: RecapManager,
                 on_test_banner: Optional[Callable] = None,
                 on_quit_app: Optional[Callable] = None):
        self.master = master
        self.detector = detector
        self.recap_mgr = recap_mgr
        self.on_test_banner = on_test_banner
        self.on_quit_app = on_quit_app

        self.window: Optional[tk.Toplevel] = None
        self.is_open = False
        self._timer_job = None
        self._logo_photo = None
        self._drag_start_x = 0
        self._drag_start_y = 0

    def toggle(self):
        """Toggle the GameBar overlay visibility."""
        self.master.after(0, self._do_toggle)

    def _do_toggle(self):
        if self.is_open and self.window and self.window.winfo_exists():
            self.close()
        else:
            self.open()

    def open(self):
        """Open the sleek GameBar overlay HUD."""
        if self.window and self.window.winfo_exists():
            self.window.deiconify()
            self.window.lift()
            self.window.focus_force()
            self.is_open = True
            return

        self.is_open = True
        self.window = tk.Toplevel(self.master)
        self.window.title("Xsolla Game Recap")
        self.window.configure(bg="#12181f")

        # Frameless modern HUD (no clunky OS window borders!)
        self.window.overrideredirect(True)
        self.window.attributes("-topmost", True)

        # Dimensions & Centering
        width = 860
        height = 540
        sw = self.window.winfo_screenwidth()
        sh = self.window.winfo_screenheight()
        x = (sw - width) // 2
        y = (sh - height) // 2
        self.window.geometry(f"{width}x{height}+{x}+{y}")

        # Bind hotkeys
        self.window.bind("<Escape>", lambda e: self.close())

        self._build_hud(width, height)
        self._start_refresh_timer()

        self.window.lift()
        self.window.focus_force()
        print("[GameBar] Frameless HUD opened.")

    def close(self):
        """Hide/Minimize the GameBar HUD to tray."""
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
        print("[GameBar] HUD minimized to background/tray.")

    def quit_entire_app(self):
        """Cleanly terminate the application."""
        if messagebox.askyesno("Exit Xsolla Game Recap", "Are you sure you want to completely shut down the Game Recap service?"):
            self.close()
            if self.on_quit_app:
                self.on_quit_app()
            else:
                self.master.quit()

    def _build_hud(self, width: int, height: int):
        # Outer Glowing Border Frame
        outer = tk.Frame(self.window, bg="#12181f", highlightthickness=2, highlightbackground="#70e1ff")
        outer.pack(fill="both", expand=True)

        # 1. Custom Draggable Titlebar (Nvidia Style)
        titlebar = tk.Frame(outer, bg="#18222b", height=52)
        titlebar.pack(fill="x", side="top")
        titlebar.pack_propagate(False)

        # Drag Window Handlers
        titlebar.bind("<Button-1>", self._start_drag)
        titlebar.bind("<B1-Motion>", self._on_drag)

        # Left: Official Xsolla Logo
        logo_frame = tk.Frame(titlebar, bg="#18222b")
        logo_frame.pack(side="left", padx=14)
        logo_frame.bind("<Button-1>", self._start_drag)
        logo_frame.bind("<B1-Motion>", self._on_drag)

        logo_path = ASSETS_DIR / "xsolla_logo_cropped.png"
        if logo_path.exists():
            try:
                pil_logo = Image.open(str(logo_path))
                h = 28
                w = int(h * (pil_logo.width / pil_logo.height))
                resized = pil_logo.resize((w, h), Image.Resampling.LANCZOS)
                self._logo_photo = ImageTk.PhotoImage(resized)
                lbl_logo = tk.Label(logo_frame, image=self._logo_photo, bg="#18222b")
                lbl_logo.pack(side="left")
                lbl_logo.bind("<Button-1>", self._start_drag)
                lbl_logo.bind("<B1-Motion>", self._on_drag)
            except Exception:
                pass

        lbl_hud = tk.Label(logo_frame, text="GAME RECAP HUD", font=("Segoe UI", 10, "bold"), fg="#70e1ff", bg="#18222b")
        lbl_hud.pack(side="left", padx=10)
        lbl_hud.bind("<Button-1>", self._start_drag)
        lbl_hud.bind("<B1-Motion>", self._on_drag)

        # Center: Active Hook Status Pill
        center_frame = tk.Frame(titlebar, bg="#18222b")
        center_frame.pack(side="left", padx=20)
        center_frame.bind("<Button-1>", self._start_drag)
        center_frame.bind("<B1-Motion>", self._on_drag)

        self.status_lbl = tk.Label(center_frame, text="⚪ Standing By - Ready to hook games",
                                   font=("Segoe UI", 9, "bold"), fg="#94a3b8", bg="#10171d", padx=12, pady=4)
        self.status_lbl.pack(side="left")

        # Right: Window Controls
        ctrl_frame = tk.Frame(titlebar, bg="#18222b")
        ctrl_frame.pack(side="right", padx=12)

        shortcut_hint = tk.Label(ctrl_frame, text="[Ctrl+Shift+X]", font=("Segoe UI", 8, "bold"), fg="#70e1ff", bg="#10171d", padx=8, pady=3)
        shortcut_hint.pack(side="left", padx=(0, 10))

        min_btn = tk.Button(ctrl_frame, text="─", font=("Segoe UI", 10, "bold"), fg="#94a3b8", bg="#18222b",
                            activebackground="#263542", activeforeground="#ffffff",
                            relief="flat", cursor="hand2", padx=10, pady=2, command=self.close)
        min_btn.pack(side="left", padx=2)

        quit_btn = tk.Button(ctrl_frame, text="✕ QUIT APP", font=("Segoe UI", 9, "bold"), fg="#ffffff", bg="#e63946",
                             activebackground="#d90429", activeforeground="#ffffff",
                             relief="flat", cursor="hand2", padx=10, pady=3, command=self.quit_entire_app)
        quit_btn.pack(side="left", padx=4)

        # 2. Main Dashboard Content (2-Column Minimalist Layout)
        body = tk.Frame(outer, bg="#12181f", padx=16, pady=12)
        body.pack(fill="both", expand=True)

        # --- LEFT COLUMN: Live Session & Highlights ---
        col_left = tk.Frame(body, bg="#161f28", padx=14, pady=12, highlightthickness=1, highlightbackground="#22303c")
        col_left.pack(side="left", fill="both", expand=True, padx=(0, 8))

        # Session Header inside Left Col
        hdr_left = tk.Frame(col_left, bg="#161f28")
        hdr_left.pack(fill="x", pady=(0, 8))

        self.game_title_lbl = tk.Label(hdr_left, text="🎮 No Active Game", font=("Segoe UI", 13, "bold"), fg="#ffffff", bg="#161f28")
        self.game_title_lbl.pack(side="left")

        self.timer_lbl = tk.Label(hdr_left, text="00:00:00", font=("Consolas", 12, "bold"), fg="#70e1ff", bg="#10171e", padx=8, pady=2)
        self.timer_lbl.pack(side="right")

        # Events Listbox
        tk.Label(col_left, text="Live Captured Milestones:", font=("Segoe UI", 9, "bold"), fg="#70e1ff", bg="#161f28").pack(anchor="w", pady=(4, 2))

        list_wrap = tk.Frame(col_left, bg="#10171e")
        list_wrap.pack(fill="both", expand=True, pady=4)

        scroller = tk.Scrollbar(list_wrap)
        scroller.pack(side="right", fill="y")

        self.events_list = tk.Listbox(list_wrap, bg="#10171e", fg="#e2e8f0", font=("Segoe UI", 9),
                                      selectbackground="#70e1ff", selectforeground="#0c1015",
                                      highlightthickness=0, relief="flat", yscrollcommand=scroller.set)
        self.events_list.pack(fill="both", expand=True, padx=4, pady=4)
        scroller.config(command=self.events_list.yview)

        # Quick Action Toolbar (Snapshot & Milestone)
        tools = tk.Frame(col_left, bg="#161f28")
        tools.pack(fill="x", pady=(6, 0))

        snap_btn = tk.Button(tools, text="📸 Snapshot", font=("Segoe UI", 9, "bold"),
                             fg="#ffffff", bg="#26384a", activebackground="#70e1ff", activeforeground="#0c1015",
                             relief="flat", cursor="hand2", padx=10, pady=4, command=self._take_snapshot)
        snap_btn.pack(side="left", padx=(0, 6))

        star_btn = tk.Button(tools, text="⭐ Add Highlight", font=("Segoe UI", 9),
                             fg="#0c1015", bg="#70e1ff", activebackground="#a3f0ff", activeforeground="#0c1015",
                             relief="flat", cursor="hand2", padx=10, pady=4, command=self._trigger_sample_milestone)
        star_btn.pack(side="left")

        # Manual entry
        self.entry_log = tk.Entry(tools, font=("Segoe UI", 9), bg="#10171e", fg="#ffffff", insertbackground="#70e1ff", relief="flat")
        self.entry_log.pack(side="left", fill="x", expand=True, padx=6)
        self.entry_log.bind("<Return>", lambda e: self._log_manual_event())

        tk.Button(tools, text="Log", font=("Segoe UI", 8, "bold"), fg="#ffffff", bg="#e63946",
                  relief="flat", cursor="hand2", padx=8, pady=3, command=self._log_manual_event).pack(side="right")

        # --- RIGHT COLUMN: Story Recap & Supported Library ---
        col_right = tk.Frame(body, bg="#161f28", padx=14, pady=12, highlightthickness=1, highlightbackground="#22303c")
        col_right.pack(side="right", fill="both", expand=True, padx=(8, 0))

        # Story Card
        card = tk.Frame(col_right, bg="#10171e", padx=14, pady=10, highlightthickness=1, highlightbackground="#70e1ff")
        card.pack(fill="x", pady=(0, 10))

        self.story_head = tk.Label(card, text="✨ XSOLLA STORY RECAP", font=("Segoe UI", 11, "bold"), fg="#70e1ff", bg="#10171e")
        self.story_head.pack(anchor="w")

        self.story_vibe = tk.Label(card, text="Persona: The Unstoppable Challenger", font=("Segoe UI", 9), fg="#cbd5e1", bg="#10171e")
        self.story_vibe.pack(anchor="w", pady=(2, 6))

        self.story_highlight = tk.Label(card, text="Top Highlight: 'Cleared Night 5 with 0 Flashlight battery!'",
                                        font=("Segoe UI", 9, "italic"), fg="#38ef7d", bg="#10171e", wraplength=340, justify="left")
        self.story_highlight.pack(anchor="w", pady=(0, 6))

        sync_btn = tk.Button(card, text="☁️ Sync Session to SaaS Web App", font=("Segoe UI", 9, "bold"),
                             fg="#0c1015", bg="#70e1ff", activebackground="#a3f0ff", activeforeground="#0c1015",
                             relief="flat", cursor="hand2", padx=12, pady=5, command=self._sync_saas)
        sync_btn.pack(fill="x", pady=(4, 2))

        # Testing & Quick Launch Toolbar
        tk.Label(col_right, text="Quick Demo & Game Simulators:", font=("Segoe UI", 9, "bold"), fg="#70e1ff", bg="#161f28").pack(anchor="w", pady=(8, 4))

        sim_box = tk.Frame(col_right, bg="#161f28")
        sim_box.pack(fill="x", pady=2)

        tk.Button(sim_box, text="🚪 Hello Neighbor", font=("Segoe UI", 8, "bold"),
                  fg="#ffffff", bg="#2a3b4c", activebackground="#70e1ff", activeforeground="#0c1015",
                  relief="flat", cursor="hand2", padx=8, pady=4, command=lambda: self._simulate_game("hello_neighbor")).pack(side="left", padx=(0, 4))

        tk.Button(sim_box, text="🐻 Custom Night", font=("Segoe UI", 8, "bold"),
                  fg="#ffffff", bg="#2a3b4c", activebackground="#70e1ff", activeforeground="#0c1015",
                  relief="flat", cursor="hand2", padx=8, pady=4, command=lambda: self._simulate_game("ultimate_custom_night")).pack(side="left", padx=4)

        tk.Button(sim_box, text="🌾 Stardew", font=("Segoe UI", 8, "bold"),
                  fg="#ffffff", bg="#2a3b4c", activebackground="#70e1ff", activeforeground="#0c1015",
                  relief="flat", cursor="hand2", padx=8, pady=4, command=lambda: self._simulate_game("stardew_valley")).pack(side="left", padx=4)

        # Test Banner Button
        banner_btn = tk.Button(col_right, text="🔔 Trigger 'Watching' Banner", font=("Segoe UI", 9, "bold"),
                               fg="#ffffff", bg="#1d4ed8", activebackground="#3b82f6", activeforeground="#ffffff",
                               relief="flat", cursor="hand2", padx=10, pady=5, command=self._trigger_test_banner)
        banner_btn.pack(fill="x", pady=(8, 4))

        # Hook Custom Game Row
        custom_frame = tk.Frame(col_right, bg="#161f28")
        custom_frame.pack(fill="x", pady=(8, 0))

        tk.Label(custom_frame, text="Hook Custom / Cracked .exe:", font=("Segoe UI", 8), fg="#94a3b8", bg="#161f28").pack(anchor="w")

        add_row = tk.Frame(custom_frame, bg="#161f28")
        add_row.pack(fill="x", pady=2)

        self.custom_name_entry = tk.Entry(add_row, font=("Segoe UI", 8), bg="#10171e", fg="#ffffff", insertbackground="#70e1ff", relief="flat")
        self.custom_name_entry.pack(side="left", fill="x", expand=True, padx=(0, 4))
        self.custom_name_entry.insert(0, "Game Name")

        self.custom_exe_entry = tk.Entry(add_row, font=("Segoe UI", 8), bg="#10171e", fg="#ffffff", insertbackground="#70e1ff", relief="flat")
        self.custom_exe_entry.pack(side="left", fill="x", expand=True, padx=4)
        self.custom_exe_entry.insert(0, "game.exe")

        tk.Button(add_row, text="➕ Add", font=("Segoe UI", 8, "bold"), fg="#0c1015", bg="#70e1ff",
                  relief="flat", cursor="hand2", padx=8, pady=2, command=self._add_custom_game_action).pack(side="right")

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
            self._timer_job = self.master.after(1000, self._start_refresh_timer)

    def _update_views(self):
        if not self.window or not self.window.winfo_exists():
            return

        active = self.detector.active_game
        if active:
            duration = self.detector.get_session_duration_str()
            self.status_lbl.config(text=f"🟢 HOOKED: {active.get('name')} (PID {self.detector.active_pid})", fg="#38ef7d")
            self.game_title_lbl.config(text=f"🎮 {active.get('name')}")
            self.timer_lbl.config(text=duration)
        else:
            self.status_lbl.config(text="⚪ Standing By - Ready to hook games", fg="#94a3b8")
            self.game_title_lbl.config(text="🎮 No Active Game Hooked")
            self.timer_lbl.config(text="00:00:00")

        curr_session = self.recap_mgr.current_session
        if curr_session:
            events = curr_session.get("events", [])
            if len(events) != self.events_list.size():
                self.events_list.delete(0, tk.END)
                for e in events:
                    self.events_list.insert(tk.END, f"[{e['timestamp']}] {e['text']}")
                self.events_list.see(tk.END)

    def _log_manual_event(self):
        text = self.entry_log.get().strip()
        if not text:
            return
        if not self.recap_mgr.current_session:
            self.detector.simulate_launch("hello_neighbor")
        self.recap_mgr.add_event(f"✨ {text}", event_type="manual")
        self.entry_log.delete(0, tk.END)
        self._update_views()

    def _trigger_sample_milestone(self):
        if not self.recap_mgr.current_session:
            self.detector.simulate_launch("hello_neighbor")
        self.recap_mgr.inject_random_milestone()
        self._update_views()

    def _take_snapshot(self):
        if not self.recap_mgr.current_session:
            self.detector.simulate_launch("hello_neighbor")
        path = self.recap_mgr.capture_screenshot()
        if path:
            messagebox.showinfo("Snapshot Saved", f"High-res screenshot saved to:\n{path}")
        self._update_views()

    def _sync_saas(self):
        res = self.recap_mgr.sync_to_saas()
        msg = res.get("message", "Synced!")
        messagebox.showinfo("SaaS Cloud Sync", msg)

    def _add_custom_game_action(self):
        name = self.custom_name_entry.get().strip()
        exe = self.custom_exe_entry.get().strip()
        if not name or not exe or name == "Game Name" or exe == "game.exe":
            messagebox.showwarning("Incomplete", "Please enter both the game name and .exe filename.")
            return

        add_custom_game(name, exe)
        messagebox.showinfo("Game Added", f"'{name}' ({exe}) is now registered! The watcher will immediately detect it when running.")

    def _trigger_test_banner(self):
        if self.on_test_banner:
            self.on_test_banner()

    def _simulate_game(self, game_id: str):
        self.detector.simulate_launch(game_id)
        self._update_views()
