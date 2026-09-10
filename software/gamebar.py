"""
Xsolla Game Recap - In-Game GameBar Overlay Dashboard
Sleek, futuristic Nvidia GameBar / Xbox Game Bar style in-game overlay.
Allows players to view live event timelines, log highlights, take snapshots,
generate Story-style recaps, and sync directly to the SaaS cloud.
"""

import time
import tkinter as tk
from tkinter import ttk, messagebox
import json
from typing import Optional, Callable

from config import load_config, add_custom_game
from detector import GameDetector
from recap_manager import RecapManager


class GameBarOverlay:
    def __init__(self, master: tk.Tk, detector: GameDetector, recap_mgr: RecapManager, on_test_banner: Optional[Callable] = None):
        self.master = master
        self.detector = detector
        self.recap_mgr = recap_mgr
        self.on_test_banner = on_test_banner

        self.window: Optional[tk.Toplevel] = None
        self.is_open = False
        self._timer_job = None

    def toggle(self):
        """Toggle the GameBar overlay visibility."""
        self.master.after(0, self._do_toggle)

    def _do_toggle(self):
        if self.is_open and self.window and self.window.winfo_exists():
            self.close()
        else:
            self.open()

    def open(self):
        """Open and bring the GameBar to front."""
        if self.window and self.window.winfo_exists():
            self.window.lift()
            self.window.focus_force()
            return

        self.is_open = True
        self.window = tk.Toplevel(self.master)
        self.window.title("Xsolla Game Recap // In-Game GameBar")
        self.window.attributes("-topmost", True)
        self.window.configure(bg="#0c0e14")

        # Dimensions & Centering
        width = 860
        height = 560
        sw = self.window.winfo_screenwidth()
        sh = self.window.winfo_screenheight()
        x = (sw - width) // 2
        y = (sh - height) // 2
        self.window.geometry(f"{width}x{height}+{x}+{y}")
        self.window.minsize(780, 500)

        # Bind close keys
        self.window.bind("<Escape>", lambda e: self.close())
        self.window.protocol("WM_DELETE_WINDOW", self.close)

        self._build_ui()
        self._start_refresh_timer()

        # Lift and take focus
        self.window.lift()
        self.window.focus_force()
        print("[GameBar] Overlay opened.")

    def close(self):
        """Close the GameBar overlay."""
        self.is_open = False
        if self._timer_job:
            try:
                self.master.after_cancel(self._timer_job)
            except Exception:
                pass
            self._timer_job = None

        if self.window and self.window.winfo_exists():
            try:
                self.window.destroy()
            except Exception:
                pass
        self.window = None
        print("[GameBar] Overlay closed.")

    def _build_ui(self):
        # Top Header Bar
        header = tk.Frame(self.window, bg="#131722", height=54)
        header.pack(fill="x", side="top")

        # Branding & Pulse Icon
        brand_frame = tk.Frame(header, bg="#131722")
        brand_frame.pack(side="left", padx=16, pady=10)

        badge = tk.Label(brand_frame, text="⚡ XSOLLA", font=("Segoe UI", 11, "bold"), fg="#00f5d4", bg="#1b2230", padx=8, pady=2)
        badge.pack(side="left", padx=(0, 10))

        title_lbl = tk.Label(brand_frame, text="GAME RECAP OVERLAY", font=("Segoe UI", 11, "bold"), fg="#ffffff", bg="#131722")
        title_lbl.pack(side="left")

        # Active Game Status Indicator (Middle)
        self.status_lbl = tk.Label(header, text="⚪ Standby - No Active Game Hooked", font=("Segoe UI", 10), fg="#94a3b8", bg="#131722")
        self.status_lbl.pack(side="left", padx=24)

        # Close button & Shortcut reminder (Right)
        right_frame = tk.Frame(header, bg="#131722")
        right_frame.pack(side="right", padx=16)

        esc_hint = tk.Label(right_frame, text="Press [ESC] to Exit", font=("Segoe UI", 9), fg="#64748b", bg="#131722")
        esc_hint.pack(side="left", padx=12)

        close_btn = tk.Button(right_frame, text="✕", font=("Segoe UI", 11, "bold"), fg="#ff0055", bg="#1f2430",
                              activebackground="#ff0055", activeforeground="#ffffff",
                              relief="flat", cursor="hand2", padx=10, pady=2, command=self.close)
        close_btn.pack(side="left")

        # Notebook Tabs
        style = ttk.Style(self.window)
        style.theme_use("default")
        style.configure("TNotebook", background="#0c0e14", borderwidth=0)
        style.configure("TNotebook.Tab", background="#1a202c", foreground="#cbd5e1",
                        font=("Segoe UI", 10, "bold"), padding=[18, 8])
        style.map("TNotebook.Tab", background=[("selected", "#00f5d4")], foreground=[("selected", "#0c0e14")])

        notebook = ttk.Notebook(self.window)
        notebook.pack(fill="both", expand=True, padx=16, pady=(12, 12))

        # Tab 1: Live Session & Timeline
        tab_timeline = tk.Frame(notebook, bg="#0f121a")
        notebook.add(tab_timeline, text="🎮 Live Session & Timeline")
        self._build_timeline_tab(tab_timeline)

        # Tab 2: Story Recap (Spotify Wrapped Style)
        tab_recap = tk.Frame(notebook, bg="#0f121a")
        notebook.add(tab_recap, text="✨ Xsolla Story Recap")
        self._build_recap_tab(tab_recap)

        # Tab 3: Supported Games & Custom Cracked Game Adder
        tab_games = tk.Frame(notebook, bg="#0f121a")
        notebook.add(tab_games, text="⚙️ Supported & Cracked Games")
        self._build_games_tab(tab_games)

    def _build_timeline_tab(self, parent: tk.Frame):
        # Top Action Bar in Tab 1
        action_bar = tk.Frame(parent, bg="#161b26", padx=12, pady=10)
        action_bar.pack(fill="x", side="top", padx=10, pady=(10, 6))

        # Session Timer
        self.timer_display = tk.Label(action_bar, text="Session Time: 00:00:00", font=("Segoe UI", 11, "bold"), fg="#00f5d4", bg="#161b26")
        self.timer_display.pack(side="left", padx=8)

        # Snapshot Button
        snap_btn = tk.Button(action_bar, text="📸 Instant Screenshot", font=("Segoe UI", 9, "bold"),
                             fg="#ffffff", bg="#7928ca", activebackground="#9d4edd", activeforeground="#ffffff",
                             relief="flat", cursor="hand2", padx=12, pady=4, command=self._take_snapshot)
        snap_btn.pack(side="right", padx=6)

        # Simulate Milestone Button
        sim_btn = tk.Button(action_bar, text="⭐ Add Sample Event", font=("Segoe UI", 9),
                            fg="#0c0e14", bg="#00f5d4", activebackground="#38ef7d", activeforeground="#0c0e14",
                            relief="flat", cursor="hand2", padx=10, pady=4, command=self._trigger_sample_milestone)
        sim_btn.pack(side="right", padx=6)

        # Middle: Timeline Events Listbox
        list_frame = tk.Frame(parent, bg="#0f121a")
        list_frame.pack(fill="both", expand=True, padx=10, pady=6)

        lbl = tk.Label(list_frame, text="Captured In-Game Events & Highlights:", font=("Segoe UI", 10, "bold"), fg="#94a3b8", bg="#0f121a")
        lbl.pack(anchor="w", pady=(0, 4))

        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side="right", fill="y")

        self.events_listbox = tk.Listbox(list_frame, bg="#141824", fg="#e2e8f0", font=("Consolas", 10),
                                         selectbackground="#7928ca", selectforeground="#ffffff",
                                         highlightthickness=1, highlightbackground="#2d3748",
                                         relief="flat", yscrollcommand=scrollbar.set)
        self.events_listbox.pack(fill="both", expand=True)
        scrollbar.config(command=self.events_listbox.yview)

        # Bottom: Manual Event Logger
        bottom_box = tk.Frame(parent, bg="#161b26", padx=12, pady=10)
        bottom_box.pack(fill="x", side="bottom", padx=10, pady=(6, 10))

        lbl_log = tk.Label(bottom_box, text="Quick Log Milestone:", font=("Segoe UI", 9, "bold"), fg="#ffffff", bg="#161b26")
        lbl_log.pack(side="left", padx=(0, 8))

        self.manual_entry = tk.Entry(bottom_box, font=("Segoe UI", 10), bg="#0f121a", fg="#ffffff",
                                     insertbackground="#00f5d4", relief="flat", highlightthickness=1, highlightbackground="#334155")
        self.manual_entry.pack(side="left", fill="x", expand=True, padx=8)
        self.manual_entry.bind("<Return>", lambda e: self._log_manual_event())

        log_btn = tk.Button(bottom_box, text="Log Highlight", font=("Segoe UI", 9, "bold"),
                            fg="#ffffff", bg="#ff0055", activebackground="#ff3377", activeforeground="#ffffff",
                            relief="flat", cursor="hand2", padx=12, pady=4, command=self._log_manual_event)
        log_btn.pack(side="right")

    def _build_recap_tab(self, parent: tk.Frame):
        # Story Card Display
        card_outer = tk.Frame(parent, bg="#0f121a", padx=20, pady=12)
        card_outer.pack(fill="both", expand=True)

        # Cyberpunk Story Card Canvas
        self.recap_card = tk.Frame(card_outer, bg="#131826", highlightthickness=2, highlightbackground="#00f5d4")
        self.recap_card.pack(fill="both", expand=True, pady=(0, 12))

        self.story_title = tk.Label(self.recap_card, text="🎮 XSOLLA GAME RECAP // STORY HIGHLIGHTS", font=("Segoe UI", 14, "bold"), fg="#00f5d4", bg="#131826")
        self.story_title.pack(anchor="w", padx=20, pady=(16, 6))

        self.story_vibe = tk.Label(self.recap_card, text="Gamer Persona: Cozy Mastermind • Stardew Valley", font=("Segoe UI", 11), fg="#cbd5e1", bg="#131826")
        self.story_vibe.pack(anchor="w", padx=20, pady=(0, 12))

        # Stats Grid inside Story Card
        stats_frame = tk.Frame(self.recap_card, bg="#1a2030", padx=16, pady=12)
        stats_frame.pack(fill="x", padx=20, pady=8)

        self.stat_time = tk.Label(stats_frame, text="⏱️ Session Time: 0m", font=("Segoe UI", 10, "bold"), fg="#ffffff", bg="#1a2030")
        self.stat_time.pack(side="left", padx=12)

        self.stat_events = tk.Label(stats_frame, text="⭐ Milestones: 0", font=("Segoe UI", 10, "bold"), fg="#ffffff", bg="#1a2030")
        self.stat_events.pack(side="left", padx=12)

        self.stat_xp = tk.Label(stats_frame, text="🏆 XP Earned: +250 XP", font=("Segoe UI", 10, "bold"), fg="#ffb703", bg="#1a2030")
        self.stat_xp.pack(side="left", padx=12)

        self.story_highlight = tk.Label(self.recap_card, text="Highlight of the Run:\n'Harvested 24 Quality Parsnips'",
                                        font=("Segoe UI", 11, "italic"), fg="#38ef7d", bg="#131826", wraplength=700, justify="left")
        self.story_highlight.pack(anchor="w", padx=20, pady=12)

        self.sync_status_lbl = tk.Label(self.recap_card, text="Cloud Status: Ready to sync with SaaS Web Dashboard", font=("Segoe UI", 9), fg="#94a3b8", bg="#131826")
        self.sync_status_lbl.pack(anchor="w", padx=20, pady=(0, 16))

        # Bottom Buttons
        btn_bar = tk.Frame(card_outer, bg="#0f121a")
        btn_bar.pack(fill="x", side="bottom")

        sync_btn = tk.Button(btn_bar, text="☁️ Sync to SaaS Web App", font=("Segoe UI", 10, "bold"),
                             fg="#ffffff", bg="#00b4d8", activebackground="#90e0ef", activeforeground="#000000",
                             relief="flat", cursor="hand2", padx=16, pady=6, command=self._sync_saas)
        sync_btn.pack(side="left", padx=(0, 10))

        regen_btn = tk.Button(btn_bar, text="🔄 Refresh Story Recap", font=("Segoe UI", 10),
                              fg="#ffffff", bg="#334155", activebackground="#475569", activeforeground="#ffffff",
                              relief="flat", cursor="hand2", padx=14, pady=6, command=self._refresh_story_card)
        regen_btn.pack(side="left")

    def _build_games_tab(self, parent: tk.Frame):
        container = tk.Frame(parent, bg="#0f121a", padx=16, pady=12)
        container.pack(fill="both", expand=True)

        # Add Custom / Cracked Game Box
        add_box = tk.LabelFrame(container, text=" Add Any Game / Cracked Executable ", font=("Segoe UI", 10, "bold"),
                                fg="#00f5d4", bg="#141824", padx=14, pady=10, relief="groove")
        add_box.pack(fill="x", pady=(0, 14))

        row1 = tk.Frame(add_box, bg="#141824")
        row1.pack(fill="x", pady=4)

        tk.Label(row1, text="Game Name:", font=("Segoe UI", 9), fg="#ffffff", bg="#141824", width=14, anchor="w").pack(side="left")
        self.new_game_name = tk.Entry(row1, font=("Segoe UI", 9), bg="#0f121a", fg="#ffffff", insertbackground="#00f5d4", relief="flat")
        self.new_game_name.pack(side="left", fill="x", expand=True, padx=6)

        row2 = tk.Frame(add_box, bg="#141824")
        row2.pack(fill="x", pady=4)

        tk.Label(row2, text="Executable (.exe):", font=("Segoe UI", 9), fg="#ffffff", bg="#141824", width=14, anchor="w").pack(side="left")
        self.new_game_exe = tk.Entry(row2, font=("Segoe UI", 9), bg="#0f121a", fg="#ffffff", insertbackground="#00f5d4", relief="flat")
        self.new_game_exe.pack(side="left", fill="x", expand=True, padx=6)

        add_btn = tk.Button(add_box, text="➕ Hook New Game", font=("Segoe UI", 9, "bold"),
                            fg="#0c0e14", bg="#00f5d4", activebackground="#38ef7d", activeforeground="#0c0e14",
                            relief="flat", cursor="hand2", padx=12, pady=4, command=self._add_custom_game_action)
        add_btn.pack(side="right", pady=(4, 0))

        # Testing & Simulation Toolbar
        test_box = tk.LabelFrame(container, text=" Testing & Hackathon Demo Controls ", font=("Segoe UI", 10, "bold"),
                                 fg="#ff70a6", bg="#141824", padx=14, pady=10, relief="groove")
        test_box.pack(fill="x", pady=(0, 14))

        test_row = tk.Frame(test_box, bg="#141824")
        test_row.pack(fill="x")

        banner_test_btn = tk.Button(test_row, text="🔔 Test 'Watching' Banner", font=("Segoe UI", 9, "bold"),
                                    fg="#ffffff", bg="#7928ca", activebackground="#9d4edd", activeforeground="#ffffff",
                                    relief="flat", cursor="hand2", padx=10, pady=4, command=self._trigger_test_banner)
        banner_test_btn.pack(side="left", padx=(0, 8))

        stardew_btn = tk.Button(test_row, text="🌾 Simulate Stardew Valley", font=("Segoe UI", 9),
                                fg="#ffffff", bg="#2a9d8f", activebackground="#52b788", activeforeground="#ffffff",
                                relief="flat", cursor="hand2", padx=10, pady=4,
                                command=lambda: self._simulate_game("stardew_valley"))
        stardew_btn.pack(side="left", padx=8)

        undertale_btn = tk.Button(test_row, text="❤️ Simulate Undertale", font=("Segoe UI", 9),
                                  fg="#ffffff", bg="#e63946", activebackground="#ff4d6d", activeforeground="#ffffff",
                                  relief="flat", cursor="hand2", padx=10, pady=4,
                                  command=lambda: self._simulate_game("undertale"))
        undertale_btn.pack(side="left", padx=8)

        stop_btn = tk.Button(test_row, text="🛑 End Session", font=("Segoe UI", 9),
                             fg="#ffffff", bg="#475569", activebackground="#64748b", activeforeground="#ffffff",
                             relief="flat", cursor="hand2", padx=10, pady=4, command=self._stop_simulated_game)
        stop_btn.pack(side="right")

    def _start_refresh_timer(self):
        self._update_views()
        if self.is_open:
            self._timer_job = self.master.after(1000, self._start_refresh_timer)

    def _update_views(self):
        if not self.window or not self.window.winfo_exists():
            return

        # Update Header & Timer
        active = self.detector.active_game
        if active:
            duration = self.detector.get_session_duration_str()
            self.status_lbl.config(text=f"🟢 {active.get('name')} [Hooked] • PID: {self.detector.active_pid}", fg="#00ff88")
            self.timer_display.config(text=f"Session Time: {duration}")
        else:
            self.status_lbl.config(text="⚪ Standby - No Active Game Hooked", fg="#94a3b8")
            self.timer_display.config(text="Session Time: 00:00:00")

        # Refresh Listbox if session active
        curr_session = self.recap_mgr.current_session
        if curr_session:
            current_count = self.events_listbox.size()
            events = curr_session.get("events", [])
            if len(events) != current_count:
                self.events_listbox.delete(0, tk.END)
                for e in events:
                    self.events_listbox.insert(tk.END, f"[{e['timestamp']}] {e['text']}")
                self.events_listbox.see(tk.END)

    def _log_manual_event(self):
        text = self.manual_entry.get().strip()
        if not text:
            return
        if not self.recap_mgr.current_session:
            # Auto-hook mock session if user manually logs
            self.detector.simulate_launch("stardew_valley")
        self.recap_mgr.add_event(f"✨ {text}", event_type="manual")
        self.manual_entry.delete(0, tk.END)
        self._update_views()

    def _trigger_sample_milestone(self):
        if not self.recap_mgr.current_session:
            self.detector.simulate_launch("stardew_valley")
        self.recap_mgr.inject_random_milestone()
        self._update_views()

    def _take_snapshot(self):
        if not self.recap_mgr.current_session:
            self.detector.simulate_launch("stardew_valley")
        path = self.recap_mgr.capture_screenshot()
        if path:
            messagebox.showinfo("Snapshot Captured", f"Screenshot saved to:\n{path}")
        self._update_views()

    def _refresh_story_card(self):
        story = self.recap_mgr.generate_story_recap()
        self.story_title.config(text=f"🎮 {story.get('title', 'Game Recap')}")
        self.story_vibe.config(text=f"Gamer Persona: {story.get('vibe')} • {story.get('game_name')}")
        self.stat_time.config(text=f"⏱️ Session: {story.get('session_time')}")
        self.stat_events.config(text=f"⭐ Milestones: {story.get('total_events')}")
        self.stat_xp.config(text=f"🏆 XP Earned: {story.get('xsolla_points')}")
        self.story_highlight.config(text=f"Highlight of the Run:\n'{story.get('top_highlight')}'")

    def _sync_saas(self):
        res = self.recap_mgr.sync_to_saas()
        msg = res.get("message", "Synced!")
        self.sync_status_lbl.config(text=f"Cloud Status: {msg}", fg="#38ef7d")
        messagebox.showinfo("SaaS Cloud Sync", msg)

    def _add_custom_game_action(self):
        name = self.new_game_name.get().strip()
        exe = self.new_game_exe.get().strip()
        if not name or not exe:
            messagebox.showwarning("Missing Fields", "Please enter both the Game Name and Executable (.exe) name.")
            return

        add_custom_game(name, exe)
        self.new_game_name.delete(0, tk.END)
        self.new_game_exe.delete(0, tk.END)
        messagebox.showinfo("Game Added", f"'{name}' ({exe}) is now registered! The watcher will immediately detect it when launched.")

    def _trigger_test_banner(self):
        if self.on_test_banner:
            self.on_test_banner()

    def _simulate_game(self, game_id: str):
        self.detector.simulate_launch(game_id)
        self._update_views()
        self._refresh_story_card()

    def _stop_simulated_game(self):
        self.detector.simulate_close()
        self.recap_mgr.end_session()
        self._update_views()
