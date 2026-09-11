"""
Xsolla Game Recap - In-Game Recap Panel
Interactive, cyberpunk styled recap dashboard embedded directly inside the GameBar.
Displays "Previously On...", session milestones from gameplay, and actionable next objectives.
Universally supports any game hooked or monitored by the client.
"""

import tkinter as tk
from typing import Optional, Callable, Dict, Any, List

from config import make_window_invisible_to_capture
import auth_state
import save_analyzer
import ai_recap


class GameRecapTab(tk.Frame):
    def __init__(self,
                 parent: tk.Widget,
                 on_close_tab: Optional[Callable[[], None]] = None,
                 on_login_request: Optional[Callable[[], None]] = None,
                 get_active_game: Optional[Callable[[], Optional[Dict]]] = None,
                 on_toast: Optional[Callable[[str, str], None]] = None):
        super().__init__(parent, bg="#080b10")
        self.on_close_tab = on_close_tab
        self.on_login_request = on_login_request
        self.get_active_game = get_active_game or (lambda: None)
        self.on_toast = on_toast

        self.current_analysis: Optional[Dict[str, Any]] = None
        self.current_recap: Optional[Dict[str, Any]] = None
        self.checklist_vars: List[tk.BooleanVar] = []

        self._build_ui()

    def _build_ui(self):
        # Clear children
        for widget in self.winfo_children():
            widget.destroy()

        active = self.get_active_game()
        target_game = active.get("name") if active else "Current Game"

        # 1. Top Header Bar
        header = tk.Frame(self, bg="#0d1117", height=48, padx=16)
        header.pack(fill="x", side="top")
        header.pack_propagate(False)

        title_frame = tk.Frame(header, bg="#0d1117")
        title_frame.pack(side="left", fill="y")

        tk.Label(
            title_frame,
            text="✨ GAME RECAP BY XSOLLA",
            font=("Segoe UI", 11, "bold"),
            fg="#70e1ff",
            bg="#0d1117"
        ).pack(side="left", pady=12)

        # Active Game Badge (No hardcoded pills)
        game_badge = tk.Frame(header, bg="#161b22", padx=10, pady=4, highlightthickness=1, highlightbackground="#30363d")
        game_badge.pack(side="left", padx=14, pady=9)
        tk.Label(
            game_badge,
            text=f"🎮 {target_game.upper()}",
            font=("Segoe UI", 8, "bold"),
            fg="#f0f6fc",
            bg="#161b22"
        ).pack()

        # Right Controls: Auth Status, Refresh, Close
        right_frame = tk.Frame(header, bg="#0d1117")
        right_frame.pack(side="right", fill="y")

        if auth_state.is_logged_in():
            user = auth_state.get_user_label()
            user_lbl = tk.Label(
                right_frame,
                text=f"🟢 {user}",
                font=("Segoe UI", 9, "bold"),
                fg="#56d364",
                bg="#161b22",
                padx=10,
                pady=4
            )
            user_lbl.pack(side="left", pady=10, padx=6)
        else:
            btn_login = tk.Label(
                right_frame,
                text="🔑 Log In",
                font=("Segoe UI", 9, "bold"),
                fg="#70e1ff",
                bg="#1f293d",
                cursor="hand2",
                padx=10,
                pady=4
            )
            btn_login.pack(side="left", pady=10, padx=6)
            if self.on_login_request:
                btn_login.bind("<Button-1>", lambda e: self.on_login_request())

        btn_refresh = tk.Label(
            right_frame,
            text="🔄 Refresh",
            font=("Segoe UI", 9),
            fg="#8b949e",
            bg="#161b22",
            cursor="hand2",
            padx=10,
            pady=4
        )
        btn_refresh.pack(side="left", pady=10, padx=4)
        btn_refresh.bind("<Button-1>", lambda e: self.refresh())
        btn_refresh.bind("<Enter>", lambda e: btn_refresh.config(fg="#f0f6fc", bg="#21262d"))
        btn_refresh.bind("<Leave>", lambda e: btn_refresh.config(fg="#8b949e", bg="#161b22"))

        btn_close = tk.Label(
            right_frame,
            text="✕",
            font=("Segoe UI", 10, "bold"),
            fg="#8b949e",
            bg="#0d1117",
            cursor="hand2",
            padx=8,
            pady=4
        )
        btn_close.pack(side="left", pady=10, padx=(4, 0))
        if self.on_close_tab:
            btn_close.bind("<Button-1>", lambda e: self.on_close_tab())
        btn_close.bind("<Enter>", lambda e: btn_close.config(fg="#ff5c5c", bg="#21262d"))
        btn_close.bind("<Leave>", lambda e: btn_close.config(fg="#8b949e", bg="#0d1117"))

        # Thin divider
        tk.Frame(self, bg="#1a2230", height=1).pack(fill="x", side="top")

        # 2. Main Content Area
        self.content_container = tk.Frame(self, bg="#080b10", padx=24, pady=16)
        self.content_container.pack(fill="both", expand=True)

        if not auth_state.is_logged_in():
            self._render_login_required()
        else:
            self._load_and_render_recap(target_game)

    def _render_login_required(self):
        card = tk.Frame(self.content_container, bg="#0d1117", highlightthickness=1, highlightbackground="#30363d", padx=40, pady=40)
        card.pack(anchor="center", expand=True)

        tk.Label(
            card,
            text="🔒",
            font=("Segoe UI", 32),
            bg="#0d1117"
        ).pack(pady=(0, 12))

        tk.Label(
            card,
            text="Connect Your Xsolla Account",
            font=("Segoe UI", 14, "bold"),
            fg="#f0f6fc",
            bg="#0d1117"
        ).pack(pady=(0, 8))

        tk.Label(
            card,
            text="Log in with your Xsolla account to view your personalized game recap,\nsession milestones, and next objectives.",
            font=("Segoe UI", 10),
            fg="#8b949e",
            bg="#0d1117",
            justify="center"
        ).pack(pady=(0, 24))

        btn = tk.Label(
            card,
            text="🚀 Log In with Xsolla",
            font=("Segoe UI", 11, "bold"),
            fg="#0d1117",
            bg="#70e1ff",
            cursor="hand2",
            padx=24,
            pady=10
        )
        btn.pack()
        if self.on_login_request:
            btn.bind("<Button-1>", lambda e: self.on_login_request())
        btn.bind("<Enter>", lambda e: btn.config(bg="#38bdf8"))
        btn.bind("<Leave>", lambda e: btn.config(bg="#70e1ff"))

    def _load_and_render_recap(self, target_game: str):
        # Universal game analysis
        self.current_analysis = save_analyzer.analyze_game_save(target_game)
        self.current_recap = ai_recap.generate_recap(self.current_analysis)

        analysis = self.current_analysis
        recap = self.current_recap

        # 1. Previously On... Narrative Banner (Zero technical AI wording)
        narrative_box = tk.Frame(
            self.content_container,
            bg="#0f172a",
            highlightthickness=1,
            highlightbackground="#70e1ff",
            padx=18,
            pady=14
        )
        narrative_box.pack(fill="x", side="top", pady=(0, 14))

        tk.Label(
            narrative_box,
            text=f"PREVIOUSLY ON {analysis['game_name'].upper()}",
            font=("Segoe UI", 9, "bold"),
            fg="#70e1ff",
            bg="#0f172a"
        ).pack(anchor="w", pady=(0, 4))

        tk.Label(
            narrative_box,
            text=recap.get("previously_on", ""),
            font=("Segoe UI", 10),
            fg="#f0f6fc",
            bg="#0f172a",
            wraplength=910,
            justify="left"
        ).pack(anchor="w")

        # 2. Split View (Left: Status & Highlights | Right: Next Objectives)
        split_frame = tk.Frame(self.content_container, bg="#080b10")
        split_frame.pack(fill="both", expand=True, side="top")

        # Left Column: What You Were Up To
        left_col = tk.Frame(split_frame, bg="#0d1117", highlightthickness=1, highlightbackground="#21262d", padx=16, pady=12)
        left_col.pack(side="left", fill="both", expand=True, padx=(0, 8))

        tk.Label(
            left_col,
            text="WHAT YOU WERE UP TO",
            font=("Segoe UI", 8, "bold"),
            fg="#8b949e",
            bg="#0d1117"
        ).pack(anchor="w", pady=(0, 8))

        # Universal stat tiles row
        stats = analysis.get("stats", {})
        stats_frame = tk.Frame(left_col, bg="#0d1117")
        stats_frame.pack(fill="x", pady=(0, 10))

        self._build_stat_tile(stats_frame, "GAME", analysis["game_name"])
        self._build_stat_tile(stats_frame, "SESSION", stats.get("duration", "Active"))
        self._build_stat_tile(stats_frame, "HIGHLIGHTS", f"{stats.get('events_count', 0)} logged")
        self._build_stat_tile(stats_frame, "MEMORIES", f"{stats.get('screenshots_count', 0)} saved")

        # Up to items
        for item in recap.get("what_you_were_up_to", []):
            item_row = tk.Frame(left_col, bg="#0d1117")
            item_row.pack(fill="x", pady=4)
            tk.Label(item_row, text="•", font=("Segoe UI", 10, "bold"), fg="#70e1ff", bg="#0d1117").pack(side="left", anchor="n", padx=(0, 6))
            tk.Label(item_row, text=item, font=("Segoe UI", 9), fg="#c9d1d9", bg="#0d1117", wraplength=410, justify="left").pack(side="left", anchor="w")

        # Right Column: Next Objectives Checklist
        right_col = tk.Frame(split_frame, bg="#0d1117", highlightthickness=1, highlightbackground="#21262d", padx=16, pady=12)
        right_col.pack(side="left", fill="both", expand=True, padx=(8, 0))

        tk.Label(
            right_col,
            text="NEXT OBJECTIVES (CHECKLIST)",
            font=("Segoe UI", 8, "bold"),
            fg="#8b949e",
            bg="#0d1117"
        ).pack(anchor="w", pady=(0, 8))

        self.checklist_vars = []
        for i, obj in enumerate(recap.get("next_objectives", [])):
            obj_card = tk.Frame(right_col, bg="#161b22", padx=10, pady=8, highlightthickness=1, highlightbackground="#30363d")
            obj_card.pack(fill="x", pady=4)

            var = tk.BooleanVar(value=False)
            self.checklist_vars.append(var)

            cb = tk.Checkbutton(
                obj_card,
                variable=var,
                bg="#161b22",
                activebackground="#161b22",
                selectcolor="#0d1117",
                highlightthickness=0,
                bd=0
            )
            cb.pack(side="left", anchor="n", padx=(0, 6))

            text_frame = tk.Frame(obj_card, bg="#161b22")
            text_frame.pack(side="left", fill="x", expand=True)

            priority_tag = "HIGH" if i == 0 else ("MEDIUM" if i == 1 else "OPTIONAL")
            tag_color = "#ff5c5c" if i == 0 else ("#f0883e" if i == 1 else "#70e1ff")

            tag_lbl = tk.Label(
                text_frame,
                text=priority_tag,
                font=("Segoe UI", 6, "bold"),
                fg=tag_color,
                bg="#21262d",
                padx=4,
                pady=1
            )
            tag_lbl.pack(anchor="w", pady=(0, 2))

            obj_lbl = tk.Label(
                text_frame,
                text=obj,
                font=("Segoe UI", 9),
                fg="#f0f6fc",
                bg="#161b22",
                wraplength=380,
                justify="left"
            )
            obj_lbl.pack(anchor="w")

            def make_toggle(v, l):
                def toggle():
                    if v.get():
                        l.config(fg="#6e7681")
                    else:
                        l.config(fg="#f0f6fc")
                return toggle

            cb.config(command=make_toggle(var, obj_lbl))

        # 3. Bottom Action Bar
        bottom_bar = tk.Frame(self.content_container, bg="#080b10")
        bottom_bar.pack(fill="x", side="bottom", pady=(12, 0))

        btn_copy = tk.Label(
            bottom_bar,
            text="📋 Copy Recap to Clipboard",
            font=("Segoe UI", 9, "bold"),
            fg="#0d1117",
            bg="#70e1ff",
            cursor="hand2",
            padx=14,
            pady=6
        )
        btn_copy.pack(side="left", padx=(0, 8))
        btn_copy.bind("<Button-1>", lambda e: self._copy_recap())
        btn_copy.bind("<Enter>", lambda e: btn_copy.config(bg="#38bdf8"))
        btn_copy.bind("<Leave>", lambda e: btn_copy.config(bg="#70e1ff"))

        tk.Label(
            bottom_bar,
            text="📁 Live Game Session Telemetry",
            font=("Segoe UI", 8),
            fg="#6e7681",
            bg="#080b10"
        ).pack(side="right", pady=6)

    def _build_stat_tile(self, parent: tk.Widget, label: str, val: str):
        tile = tk.Frame(parent, bg="#161b22", padx=10, pady=6, highlightthickness=1, highlightbackground="#30363d")
        tile.pack(side="left", fill="both", expand=True, padx=3)
        tk.Label(tile, text=label, font=("Segoe UI", 6, "bold"), fg="#8b949e", bg="#161b22").pack(anchor="w")
        tk.Label(tile, text=val, font=("Segoe UI", 9, "bold"), fg="#70e1ff", bg="#161b22").pack(anchor="w")

    def _copy_recap(self):
        if not self.current_recap:
            return
        text = self.current_recap.get("raw_text", "")
        self.clipboard_clear()
        self.clipboard_append(text)
        if self.on_toast:
            self.on_toast("Game recap copied to clipboard!", "#70e1ff")

    def refresh(self):
        self._build_ui()
