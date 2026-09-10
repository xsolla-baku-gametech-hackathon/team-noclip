"""
Xsolla Game Recap - Minimalist In-Game GameBar HUD
Lightweight, compact, frameless overlay providing real time game telemetry,
instant snapshot capture, milestone logging, and clean tray minimization.
"""

import time
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
from typing import Optional, Callable

from config import load_config, ASSETS_DIR
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
        """Toggles the GameBar overlay visibility."""
        self.master.after(0, self._do_toggle)

    def _do_toggle(self):
        if self.is_open and self.window and self.window.winfo_exists():
            self.close()
        else:
            self.open()

    def open(self):
        """Displays the lightweight GameBar HUD."""
        if self.window and self.window.winfo_exists():
            self.window.deiconify()
            self.window.lift()
            self.window.focus_force()
            self.is_open = True
            return

        self.is_open = True
        self.window = tk.Toplevel(self.master)
        self.window.title("Xsolla Game Recap")
        self.window.configure(bg="#0c1015")

        # Frameless modern HUD
        self.window.overrideredirect(True)
        self.window.attributes("-topmost", True)

        # Compact Minimalist Dimensions
        width = 520
        height = 360
        sw = self.window.winfo_screenwidth()
        sh = self.window.winfo_screenheight()
        x = (sw - width) // 2
        y = (sh - height) // 2
        self.window.geometry(f"{width}x{height}+{x}+{y}")

        self.window.bind("<Escape>", lambda e: self.close())

        self._build_minimal_hud(width, height)
        self._start_refresh_timer()

        self.window.lift()
        self.window.focus_force()

    def close(self):
        """Minimizes the GameBar HUD to background and tray."""
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

    def quit_entire_app(self):
        """Cleanly terminates the application."""
        self.close()
        if self.on_quit_app:
            self.on_quit_app()
        else:
            self.master.quit()

    def _build_minimal_hud(self, width: int, height: int):
        # Outer Border Box
        outer = tk.Frame(self.window, bg="#0c1015", highlightthickness=1, highlightbackground="#70e1ff")
        outer.pack(fill="both", expand=True)

        # 1. Sleek Header Bar
        titlebar = tk.Frame(outer, bg="#131b24", height=42)
        titlebar.pack(fill="x", side="top")
        titlebar.pack_propagate(False)

        titlebar.bind("<Button-1>", self._start_drag)
        titlebar.bind("<B1-Motion>", self._on_drag)

        # Left: Official Xsolla Logo
        logo_frame = tk.Frame(titlebar, bg="#131b24")
        logo_frame.pack(side="left", padx=10)
        logo_frame.bind("<Button-1>", self._start_drag)
        logo_frame.bind("<B1-Motion>", self._on_drag)

        logo_path = ASSETS_DIR / "xsolla_logo_cropped.png"
        if logo_path.exists():
            try:
                pil_logo = Image.open(str(logo_path))
                h = 22
                w = int(h * (pil_logo.width / pil_logo.height))
                resized = pil_logo.resize((w, h), Image.Resampling.LANCZOS)
                self._logo_photo = ImageTk.PhotoImage(resized)
                lbl_logo = tk.Label(logo_frame, image=self._logo_photo, bg="#131b24")
                lbl_logo.pack(side="left")
                lbl_logo.bind("<Button-1>", self._start_drag)
                lbl_logo.bind("<B1-Motion>", self._on_drag)
            except Exception:
                pass

        lbl_hud = tk.Label(logo_frame, text="GAME RECAP HUD", font=("Segoe UI", 9, "bold"), fg="#70e1ff", bg="#131b24")
        lbl_hud.pack(side="left", padx=8)
        lbl_hud.bind("<Button-1>", self._start_drag)
        lbl_hud.bind("<B1-Motion>", self._on_drag)

        # Center: Live Status Indicator
        self.status_dot = tk.Label(titlebar, text="○ STANDBY", font=("Segoe UI", 8, "bold"),
                                   fg="#94a3b8", bg="#0e141c", padx=8, pady=2)
        self.status_dot.pack(side="left", padx=10)

        # Right: Window Controls
        ctrl_frame = tk.Frame(titlebar, bg="#131b24")
        ctrl_frame.pack(side="right", padx=8)

        shortcut_hint = tk.Label(ctrl_frame, text="[Ctrl+Shift+X]", font=("Segoe UI", 8),
                                 fg="#70e1ff", bg="#0e141c", padx=6, pady=2)
        shortcut_hint.pack(side="left", padx=(0, 6))

        min_btn = tk.Button(ctrl_frame, text="─", font=("Segoe UI", 9, "bold"), fg="#94a3b8", bg="#131b24",
                            activebackground="#1e293b", activeforeground="#ffffff",
                            relief="flat", cursor="hand2", padx=6, pady=1, command=self.close)
        min_btn.pack(side="left", padx=2)

        quit_btn = tk.Button(ctrl_frame, text="✕ QUIT", font=("Segoe UI", 8, "bold"), fg="#ffffff", bg="#e63946",
                             activebackground="#c1121f", activeforeground="#ffffff",
                             relief="flat", cursor="hand2", padx=8, pady=2, command=self.quit_entire_app)
        quit_btn.pack(side="left", padx=2)

        # 2. Main Content Stack
        body = tk.Frame(outer, bg="#0c1015", padx=12, pady=10)
        body.pack(fill="both", expand=True)

        # Active Game Monitor Card
        monitor_card = tk.Frame(body, bg="#131b24", padx=12, pady=8, highlightthickness=1, highlightbackground="#1e293b")
        monitor_card.pack(fill="x", pady=(0, 8))

        top_row = tk.Frame(monitor_card, bg="#131b24")
        top_row.pack(fill="x")

        self.game_title_lbl = tk.Label(top_row, text="🎮 No Active Game Hooked", font=("Segoe UI", 11, "bold"),
                                       fg="#ffffff", bg="#131b24")
        self.game_title_lbl.pack(side="left")

        self.timer_lbl = tk.Label(top_row, text="00:00:00", font=("Consolas", 12, "bold"),
                                  fg="#70e1ff", bg="#0e141c", padx=8, pady=2)
        self.timer_lbl.pack(side="right")

        # Telemetry Stats Line
        self.stats_lbl = tk.Label(monitor_card, text="PID: None  •  RAM: 0 MB  •  CPU: 0.0%",
                                  font=("Segoe UI", 8), fg="#94a3b8", bg="#131b24")
        self.stats_lbl.pack(anchor="w", pady=(4, 0))

        # 3. Action Toolbar
        actions = tk.Frame(body, bg="#0c1015")
        actions.pack(fill="x", pady=(0, 8))

        snap_btn = tk.Button(actions, text="📸 Snapshot", font=("Segoe UI", 8, "bold"),
                             fg="#ffffff", bg="#1e293b", activebackground="#70e1ff", activeforeground="#0c1015",
                             relief="flat", cursor="hand2", padx=10, pady=3, command=self._take_snapshot)
        snap_btn.pack(side="left", padx=(0, 6))

        star_btn = tk.Button(actions, text="⭐ Milestone", font=("Segoe UI", 8, "bold"),
                             fg="#0c1015", bg="#70e1ff", activebackground="#a3f0ff", activeforeground="#0c1015",
                             relief="flat", cursor="hand2", padx=10, pady=3, command=self._quick_milestone)
        star_btn.pack(side="left", padx=(0, 6))

        sync_btn = tk.Button(actions, text="☁️ Sync Cloud", font=("Segoe UI", 8),
                             fg="#ffffff", bg="#1e293b", activebackground="#38ef7d", activeforeground="#0c1015",
                             relief="flat", cursor="hand2", padx=10, pady=3, command=self._sync_saas)
        sync_btn.pack(side="left")

        # 4. Live Event Activity Feed
        feed_box = tk.Frame(body, bg="#0e141c", highlightthickness=1, highlightbackground="#1e293b")
        feed_box.pack(fill="both", expand=True, pady=(0, 8))

        scroller = tk.Scrollbar(feed_box)
        scroller.pack(side="right", fill="y")

        self.events_list = tk.Listbox(feed_box, bg="#0e141c", fg="#cbd5e1", font=("Segoe UI", 8),
                                      selectbackground="#70e1ff", selectforeground="#0c1015",
                                      highlightthickness=0, relief="flat", yscrollcommand=scroller.set)
        self.events_list.pack(fill="both", expand=True, padx=4, pady=4)
        scroller.config(command=self.events_list.yview)

        # 5. Quick Milestone Entry
        entry_row = tk.Frame(body, bg="#0c1015")
        entry_row.pack(fill="x")

        self.entry_note = tk.Entry(entry_row, font=("Segoe UI", 8), bg="#131b24", fg="#ffffff",
                                   insertbackground="#70e1ff", relief="flat")
        self.entry_note.pack(side="left", fill="x", expand=True, padx=(0, 6))
        self.entry_note.insert(0, "Type custom event note and press Enter...")
        self.entry_note.bind("<FocusIn>", self._clear_placeholder)
        self.entry_note.bind("<Return>", lambda e: self._log_custom_event())

        tk.Button(entry_row, text="Log", font=("Segoe UI", 8, "bold"), fg="#ffffff", bg="#1e293b",
                  activebackground="#70e1ff", activeforeground="#0c1015",
                  relief="flat", cursor="hand2", padx=12, pady=2, command=self._log_custom_event).pack(side="right")

    def _start_drag(self, event):
        self._drag_start_x = event.x
        self._drag_start_y = event.y

    def _on_drag(self, event):
        if self.window and self.window.winfo_exists():
            x = self.window.winfo_x() + (event.x - self._drag_start_x)
            y = self.window.winfo_y() + (event.y - self._drag_start_y)
            self.window.geometry(f"+{x}+{y}")

    def _clear_placeholder(self, event):
        if self.entry_note.get().startswith("Type custom"):
            self.entry_note.delete(0, tk.END)

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
            self.status_dot.config(text="● LIVE", fg="#38ef7d")
            self.game_title_lbl.config(text=f"🎮 {active.get('name')}")
            self.timer_lbl.config(text=duration)
            self.stats_lbl.config(text=f"PID: {self.detector.active_pid}  •  RAM: {stats.get('ram_mb')} MB  •  CPU: {stats.get('cpu_pct')}%")
        else:
            self.status_dot.config(text="○ STANDBY", fg="#94a3b8")
            self.game_title_lbl.config(text="🎮 No Active Game Hooked")
            self.timer_lbl.config(text="00:00:00")
            self.stats_lbl.config(text="Standing by  •  Launch any game to begin auto recording")

        curr_session = self.recap_mgr.current_session
        if curr_session:
            events = curr_session.get("events", [])
            if len(events) != self.events_list.size():
                self.events_list.delete(0, tk.END)
                for e in events:
                    self.events_list.insert(tk.END, f"[{e['timestamp']}] {e['text']}")
                self.events_list.see(tk.END)

    def _log_custom_event(self):
        text = self.entry_note.get().strip()
        if not text or text.startswith("Type custom"):
            return
        if not self.recap_mgr.current_session:
            active = self.detector.active_game
            if active:
                self.recap_mgr.start_session(active, self.detector.active_pid or 0, active.get("name"))
            else:
                self.recap_mgr.start_session({"id": "game", "name": "Current Session"}, 0, "Custom Session")

        self.recap_mgr.add_event(f"✨ {text}", event_type="custom")
        self.entry_note.delete(0, tk.END)
        self._update_views()

    def _quick_milestone(self):
        if not self.recap_mgr.current_session:
            self._log_custom_event()
            return
        self.recap_mgr.add_event("⭐ Milestone reached", event_type="milestone")
        self._update_views()

    def _take_snapshot(self):
        if not self.recap_mgr.current_session:
            active = self.detector.active_game
            if active:
                self.recap_mgr.start_session(active, self.detector.active_pid or 0, active.get("name"))
            else:
                self.recap_mgr.start_session({"id": "desktop", "name": "Game Session"}, 0, "Snapshot Session")

        path = self.recap_mgr.capture_screenshot()
        if path:
            messagebox.showinfo("Snapshot Captured", f"Screenshot saved:\n{path}")
        self._update_views()

    def _sync_saas(self):
        res = self.recap_mgr.sync_to_saas()
        msg = res.get("message", "Synced!")
        messagebox.showinfo("Cloud Sync", msg)
