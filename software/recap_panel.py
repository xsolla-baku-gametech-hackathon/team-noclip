"""
Xsolla Game Recap - In-Game Recap Dashboard (Cyberpunk / AAA GameBar Redesign)
Interactive, high-energy gaming recap powered by OpenRouter AI (gpt-4o-mini).
Displays "Previously On...", session accomplishments, and actionable quest objectives.
Universally supports any game hooked or monitored by the client.
"""

import threading
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
        self.is_regenerating = False

        self._build_ui()

    def _build_ui(self):
        for widget in self.winfo_children():
            widget.destroy()

        active = self.get_active_game()
        target_game = active.get("name") if active else "Current Game"

        # 1. Top Header Navbar
        header = tk.Frame(self, bg="#0d1117", height=52, padx=18)
        header.pack(fill="x", side="top")
        header.pack_propagate(False)

        # Left: Title & Game Badge
        left_header = tk.Frame(header, bg="#0d1117")
        left_header.pack(side="left", fill="y")

        tk.Label(
            left_header,
            text="⚡ XSOLLA GAME RECAP",
            font=("Segoe UI", 11, "bold"),
            fg="#70e1ff",
            bg="#0d1117"
        ).pack(side="left", pady=14)

        game_badge = tk.Frame(left_header, bg="#161b22", padx=10, pady=4, highlightthickness=1, highlightbackground="#70e1ff")
        game_badge.pack(side="left", padx=12, pady=11)
        tk.Label(
            game_badge,
            text=f"🎮 {target_game.upper()}",
            font=("Segoe UI", 8, "bold"),
            fg="#ffffff",
            bg="#161b22"
        ).pack(side="left")

        live_tag = tk.Label(
            left_header,
            text="● LIVE AI ENGINE",
            font=("Segoe UI", 7, "bold"),
            fg="#34d399",
            bg="#0d1117"
        )
        live_tag.pack(side="left", padx=(4, 0), pady=16)

        # Right Controls: Regenerate, Copy, User status, Close
        right_header = tk.Frame(header, bg="#0d1117")
        right_header.pack(side="right", fill="y")

        # Regenerate AI Recap Button
        self.btn_regenerate = tk.Label(
            right_header,
            text="🔄 Regenerate Story",
            font=("Segoe UI", 8, "bold"),
            fg="#f0f6fc",
            bg="#1f293d",
            cursor="hand2",
            padx=10,
            pady=4,
            highlightthickness=1,
            highlightbackground="#30363d"
        )
        self.btn_regenerate.pack(side="left", pady=11, padx=4)
        self.btn_regenerate.bind("<Button-1>", lambda e: self._on_regenerate_click(target_game))
        self.btn_regenerate.bind("<Enter>", lambda e: self.btn_regenerate.config(bg="#70e1ff", fg="#0d1117"))
        self.btn_regenerate.bind("<Leave>", lambda e: self.btn_regenerate.config(bg="#1f293d", fg="#f0f6fc"))

        # Copy Recap Button
        btn_copy_hdr = tk.Label(
            right_header,
            text="📋 Copy",
            font=("Segoe UI", 8, "bold"),
            fg="#8b949e",
            bg="#161b22",
            cursor="hand2",
            padx=9,
            pady=4,
            highlightthickness=1,
            highlightbackground="#30363d"
        )
        btn_copy_hdr.pack(side="left", pady=11, padx=4)
        btn_copy_hdr.bind("<Button-1>", lambda e: self._copy_recap())
        btn_copy_hdr.bind("<Enter>", lambda e: btn_copy_hdr.config(fg="#f0f6fc", bg="#21262d"))
        btn_copy_hdr.bind("<Leave>", lambda e: btn_copy_hdr.config(fg="#8b949e", bg="#161b22"))

        # User Profile indicator
        if auth_state.is_logged_in():
            user = auth_state.get_user_label()
            user_lbl = tk.Label(
                right_header,
                text=f"🟢 {user}",
                font=("Segoe UI", 8, "bold"),
                fg="#56d364",
                bg="#161b22",
                padx=9,
                pady=4,
                highlightthickness=1,
                highlightbackground="#238636"
            )
            user_lbl.pack(side="left", pady=11, padx=4)
        else:
            btn_login = tk.Label(
                right_header,
                text="🔑 Log In",
                font=("Segoe UI", 8, "bold"),
                fg="#0d1117",
                bg="#70e1ff",
                cursor="hand2",
                padx=10,
                pady=4
            )
            btn_login.pack(side="left", pady=11, padx=4)
            if self.on_login_request:
                btn_login.bind("<Button-1>", lambda e: self.on_login_request())

        # Top border accent divider
        tk.Frame(self, bg="#1a2230", height=1).pack(fill="x", side="top")

        # 2. Main Content Container
        self.content_container = tk.Frame(self, bg="#080b10", padx=20, pady=14)
        self.content_container.pack(fill="both", expand=True)

        if not auth_state.is_logged_in():
            self._render_login_required()
        else:
            self._load_and_render_recap(target_game)

    def _render_login_required(self):
        card = tk.Frame(self.content_container, bg="#0d1117", highlightthickness=1, highlightbackground="#30363d", padx=40, pady=40)
        card.pack(anchor="center", expand=True)

        tk.Label(card, text="🔒", font=("Segoe UI", 32), bg="#0d1117").pack(pady=(0, 12))
        tk.Label(
            card,
            text="Connect Your Xsolla Account",
            font=("Segoe UI", 14, "bold"),
            fg="#f0f6fc",
            bg="#0d1117"
        ).pack(pady=(0, 8))

        tk.Label(
            card,
            text="Log in with your Xsolla account to unlock live OpenRouter AI story recaps,\nsession telemetry, and active quest tracking.",
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

    def _on_regenerate_click(self, target_game: str):
        if self.is_regenerating:
            return
        self.is_regenerating = True
        self.btn_regenerate.config(text="⏳ Generating with AI...", bg="#21262d", fg="#70e1ff")

        def _worker():
            try:
                analysis = save_analyzer.analyze_game_save(target_game)
                recap = ai_recap.generate_recap(analysis)
                self.master.after(0, lambda: self._apply_regenerated_recap(analysis, recap))
            except Exception as err:
                print(f"[RecapPanel] Regenerate error: {err}")
                self.master.after(0, lambda: self._finish_regenerating())

        threading.Thread(target=_worker, daemon=True).start()

    def _apply_regenerated_recap(self, analysis: Dict[str, Any], recap: Dict[str, Any]):
        self.current_analysis = analysis
        self.current_recap = recap
        self._finish_regenerating()
        self._build_ui()
        if self.on_toast:
            self.on_toast("Story recap refreshed with live OpenRouter AI!", "#34d399")

    def _finish_regenerating(self):
        self.is_regenerating = False
        if self.btn_regenerate and self.btn_regenerate.winfo_exists():
            self.btn_regenerate.config(text="🔄 Regenerate Story", bg="#1f293d", fg="#f0f6fc")

    def _load_and_render_recap(self, target_game: str):
        if not self.current_analysis or not self.current_recap:
            self.current_analysis = save_analyzer.analyze_game_save(target_game)
            self.current_recap = ai_recap.generate_recap(self.current_analysis)

        analysis = self.current_analysis
        recap = self.current_recap

        # 1. Previously On... Cinematic Story Card
        story_card = tk.Frame(
            self.content_container,
            bg="#0f172a",
            highlightthickness=1,
            highlightbackground="#70e1ff",
            padx=18,
            pady=12
        )
        story_card.pack(fill="x", side="top", pady=(0, 10))

        # Accent top bar inside card
        card_header = tk.Frame(story_card, bg="#0f172a")
        card_header.pack(fill="x", pady=(0, 4))

        tk.Label(
            card_header,
            text=f"🎬 PREVIOUSLY ON {analysis['game_name'].upper()} • STORYLINE BRIDGE",
            font=("Segoe UI", 9, "bold"),
            fg="#70e1ff",
            bg="#0f172a"
        ).pack(side="left")

        engine_source = recap.get("source", "recap_engine")
        source_badge_text = "AI GENERATED (gpt-4o-mini)" if engine_source in ("openrouter_ai", "recap_engine") else "LOCAL SESSION"
        tk.Label(
            card_header,
            text=source_badge_text,
            font=("Segoe UI", 7, "bold"),
            fg="#a855f7",
            bg="#1e1b4b",
            padx=6,
            pady=2
        ).pack(side="right")

        # Narrative Story Text
        tk.Label(
            story_card,
            text=recap.get("previously_on", ""),
            font=("Segoe UI", 10),
            fg="#f0f6fc",
            bg="#0f172a",
            wraplength=930,
            justify="left"
        ).pack(anchor="w")

        # 2. Telemetry Stat Tiles Row
        stats = analysis.get("stats", {})
        stats_row = tk.Frame(self.content_container, bg="#080b10")
        stats_row.pack(fill="x", pady=(0, 10))

        self._build_stat_tile(stats_row, "CURRENT RUN", analysis["game_name"])
        self._build_stat_tile(stats_row, "SESSION TIME", stats.get("duration", "Active Run"))
        self._build_stat_tile(stats_row, "CHECKPOINTS", f"{stats.get('events_count', 0)} logged")
        self._build_stat_tile(stats_row, "VAULT ARCHIVE", f"{stats.get('screenshots_count', 0)} captures")

        # 3. Two-Column Dashboard (Accomplishments & Active Quest Journal)
        split_frame = tk.Frame(self.content_container, bg="#080b10")
        split_frame.pack(fill="both", expand=True, side="top")

        # Left Column: What You Were Up To
        left_col = tk.Frame(split_frame, bg="#0d1117", highlightthickness=1, highlightbackground="#21262d", padx=14, pady=10)
        left_col.pack(side="left", fill="both", expand=True, padx=(0, 6))

        tk.Label(
            left_col,
            text="📌 WHAT YOU WERE UP TO (PROGRESS & HIGHLIGHTS)",
            font=("Segoe UI", 8, "bold"),
            fg="#8b949e",
            bg="#0d1117"
        ).pack(anchor="w", pady=(0, 6))

        for item in recap.get("what_you_were_up_to", []):
            item_card = tk.Frame(left_col, bg="#161b22", padx=8, pady=6, highlightthickness=1, highlightbackground="#21262d")
            item_card.pack(fill="x", pady=3)
            tk.Label(
                item_card,
                text="▸",
                font=("Segoe UI", 10, "bold"),
                fg="#70e1ff",
                bg="#161b22"
            ).pack(side="left", anchor="n", padx=(0, 6))
            tk.Label(
                item_card,
                text=item,
                font=("Segoe UI", 9),
                fg="#f0f6fc",
                bg="#161b22",
                wraplength=410,
                justify="left"
            ).pack(side="left", fill="x", expand=True, anchor="w")

        # Right Column: Active Quest Journal & Objectives
        right_col = tk.Frame(split_frame, bg="#0d1117", highlightthickness=1, highlightbackground="#21262d", padx=14, pady=10)
        right_col.pack(side="left", fill="both", expand=True, padx=(6, 0))

        tk.Label(
            right_col,
            text="⚔️ ACTIVE MISSION JOURNAL & OBJECTIVES",
            font=("Segoe UI", 8, "bold"),
            fg="#8b949e",
            bg="#0d1117"
        ).pack(anchor="w", pady=(0, 6))

        self.checklist_vars = []
        raw_objs = recap.get("raw_objectives") or []
        fallback_objs = recap.get("next_objectives", [])

        for i in range(max(len(raw_objs), len(fallback_objs))):
            obj_data = raw_objs[i] if i < len(raw_objs) else None
            text_desc = fallback_objs[i] if i < len(fallback_objs) else ""

            title = obj_data.get("title") if isinstance(obj_data, dict) else ""
            desc = obj_data.get("description") if isinstance(obj_data, dict) else text_desc
            priority = (obj_data.get("priority") if isinstance(obj_data, dict) else None) or ("HIGH" if i == 0 else ("MEDIUM" if i == 1 else "OPTIONAL"))

            if not title and ":" in text_desc:
                parts = text_desc.split(":", 1)
                title = parts[0].strip()
                desc = parts[1].strip()
            elif not title:
                title = f"Objective {i + 1}"

            obj_card = tk.Frame(right_col, bg="#161b22", padx=10, pady=7, highlightthickness=1, highlightbackground="#30363d")
            obj_card.pack(fill="x", pady=3)

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
            cb.pack(side="left", anchor="n", padx=(0, 8))

            text_frame = tk.Frame(obj_card, bg="#161b22")
            text_frame.pack(side="left", fill="x", expand=True)

            # Priority Tag
            tag_color = "#ff5c5c" if priority.upper() == "HIGH" else ("#f0883e" if priority.upper() == "MEDIUM" else "#70e1ff")
            tag_lbl = tk.Label(
                text_frame,
                text=f"● {priority.upper()}",
                font=("Segoe UI", 6, "bold"),
                fg=tag_color,
                bg="#161b22"
            )
            tag_lbl.pack(anchor="w")

            title_lbl = tk.Label(
                text_frame,
                text=title,
                font=("Segoe UI", 9, "bold"),
                fg="#f0f6fc",
                bg="#161b22"
            )
            title_lbl.pack(anchor="w")

            desc_lbl = tk.Label(
                text_frame,
                text=desc,
                font=("Segoe UI", 8),
                fg="#8b949e",
                bg="#161b22",
                wraplength=380,
                justify="left"
            )
            desc_lbl.pack(anchor="w")

            def make_toggle(v, tl, dl, card):
                def toggle():
                    if v.get():
                        tl.config(fg="#484f58")
                        dl.config(fg="#30363d")
                        card.config(highlightbackground="#21262d")
                    else:
                        tl.config(fg="#f0f6fc")
                        dl.config(fg="#8b949e")
                        card.config(highlightbackground="#30363d")
                return toggle

            cb.config(command=make_toggle(var, title_lbl, desc_lbl, obj_card))

        # 4. Bottom Footer Bar
        footer = tk.Frame(self.content_container, bg="#080b10")
        footer.pack(fill="x", side="bottom", pady=(10, 0))

        tk.Label(
            footer,
            text="⚡ Powered by OpenRouter AI (gpt-4o-mini) • Live Telemetry Active",
            font=("Segoe UI", 8),
            fg="#6e7681",
            bg="#080b10"
        ).pack(side="left")

        tk.Label(
            footer,
            text="Toggle HUD: [Ctrl+Shift+X] • Close: [ESC]",
            font=("Segoe UI", 8),
            fg="#484f58",
            bg="#080b10"
        ).pack(side="right")

    def _build_stat_tile(self, parent: tk.Widget, label: str, val: str):
        tile = tk.Frame(parent, bg="#161b22", padx=10, pady=5, highlightthickness=1, highlightbackground="#30363d")
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
            self.on_toast("Story recap copied to clipboard!", "#70e1ff")

    def refresh(self):
        self.current_analysis = None
        self.current_recap = None
        self._build_ui()
