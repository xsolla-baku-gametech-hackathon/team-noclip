"""
Xsolla Game Recap - Mandatory App Login Window
Presents a dedicated, desktop-launcher style rectangular window (440x570px)
requiring user authentication before the in-game Xsolla bar and background detection are unlocked.
"""

import tkinter as tk
from PIL import Image, ImageTk
from typing import Optional, Callable

from config import ASSETS_DIR, WEBSITE_LOGIN_URL, make_window_invisible_to_capture
import auth_state
import auth_server


class LoginWindow:
    def __init__(self,
                 master: tk.Tk,
                 on_login_success: Callable[[str, str, str], None],
                 on_cancel: Optional[Callable[[], None]] = None):
        self.master = master
        self.on_login_success = on_login_success
        self.on_cancel = on_cancel or (lambda: master.destroy())

        self.window: Optional[tk.Toplevel] = None
        self._logo_photo = None
        self._mascot_photo = None
        self._drag_start_x = 0
        self._drag_start_y = 0
        self.is_waiting_browser = False

    def show(self):
        """Builds and displays the rectangular launcher login window."""
        if self.window and self.window.winfo_exists():
            self.window.deiconify()
            self.window.lift()
            self.window.focus_force()
            return

        self.window = tk.Toplevel(self.master)
        self.window.title("Xsolla Game Recap — Login")
        self.window.configure(bg="#080b10")
        self.window.overrideredirect(True)
        self.window.attributes("-topmost", True)

        # Center on screen
        width = 440
        height = 580
        sw = self.window.winfo_screenwidth()
        sh = self.window.winfo_screenheight()
        x = (sw - width) // 2
        y = (sh - height) // 2
        self.window.geometry(f"{width}x{height}+{x}+{y}")

        # Ensure excluded from screen capture
        make_window_invisible_to_capture(self.window)

        self._build_ui()
        self.window.lift()
        self.window.focus_force()

    def hide(self):
        if self.window and self.window.winfo_exists():
            self.window.withdraw()

    def destroy(self):
        if self.window and self.window.winfo_exists():
            try:
                self.window.destroy()
            except Exception:
                pass
            self.window = None

    def _start_drag(self, event):
        self._drag_start_x = event.x
        self._drag_start_y = event.y

    def _on_drag(self, event):
        if self.window and self.window.winfo_exists():
            x = self.window.winfo_x() + (event.x - self._drag_start_x)
            y = self.window.winfo_y() + (event.y - self._drag_start_y)
            self.window.geometry(f"+{x}+{y}")

    def _build_ui(self):
        # Outer Border Frame (with cyan accent outline)
        outer = tk.Frame(self.window, bg="#080b10", highlightthickness=1, highlightbackground="#70e1ff")
        outer.pack(fill="both", expand=True)

        # 1. Custom Title Bar
        titlebar = tk.Frame(outer, bg="#0d1117", height=38, padx=12)
        titlebar.pack(fill="x", side="top")
        titlebar.pack_propagate(False)
        titlebar.bind("<Button-1>", self._start_drag)
        titlebar.bind("<B1-Motion>", self._on_drag)

        # Left: App Name
        lbl_title = tk.Label(
            titlebar,
            text="⚡ XSOLLA GAME RECAP",
            font=("Segoe UI", 9, "bold"),
            fg="#70e1ff",
            bg="#0d1117"
        )
        lbl_title.pack(side="left", pady=8)
        lbl_title.bind("<Button-1>", self._start_drag)
        lbl_title.bind("<B1-Motion>", self._on_drag)

        # Right: Close Button
        btn_close = tk.Label(
            titlebar,
            text="✕",
            font=("Segoe UI", 10, "bold"),
            fg="#8b949e",
            bg="#0d1117",
            cursor="hand2",
            padx=8,
            pady=4
        )
        btn_close.pack(side="right", pady=6)
        btn_close.bind("<Button-1>", lambda e: self.on_cancel())
        btn_close.bind("<Enter>", lambda e: btn_close.config(fg="#ff5c5c", bg="#21262d"))
        btn_close.bind("<Leave>", lambda e: btn_close.config(fg="#8b949e", bg="#0d1117"))

        # 2. Main Body Container
        body = tk.Frame(outer, bg="#080b10", padx=28, pady=24)
        body.pack(fill="both", expand=True)
        body.bind("<Button-1>", self._start_drag)
        body.bind("<B1-Motion>", self._on_drag)

        # Centered Sol Mascot Icon
        mascot_path = ASSETS_DIR / "xsolla_mascot_clean.png"
        if not mascot_path.exists():
            mascot_path = ASSETS_DIR / "xsolla_robot_mascot.png"

        if mascot_path.exists():
            try:
                with Image.open(str(mascot_path)) as img:
                    resized = img.resize((76, 76), Image.Resampling.LANCZOS)
                    self._mascot_photo = ImageTk.PhotoImage(resized)
                    lbl_mascot = tk.Label(body, image=self._mascot_photo, bg="#080b10")
                    lbl_mascot.pack(pady=(4, 12))
            except Exception:
                pass

        # App Heading & Subtitle
        tk.Label(
            body,
            text="Xsolla Game Recap",
            font=("Segoe UI", 17, "bold"),
            fg="#ffffff",
            bg="#080b10"
        ).pack(pady=(0, 4))

        tk.Label(
            body,
            text="AI-Powered Game Save Recap & Memory Vault",
            font=("Segoe UI", 9),
            fg="#70e1ff",
            bg="#080b10"
        ).pack(pady=(0, 16))

        # Thin Cyberpunk Divider
        tk.Frame(body, bg="#1a2230", height=1).pack(fill="x", pady=(0, 18))

        # Feature Highlights Card
        features_card = tk.Frame(body, bg="#0d1117", highlightthickness=1, highlightbackground="#21262d", padx=16, pady=12)
        features_card.pack(fill="x", pady=(0, 20))

        highlights = [
            ("🌱", "Save File Telemetry", "Stardew Valley, Undertale, & Auto-Detection"),
            ("🧠", "OpenRouter AI Recap", "Instant 'Previously On...' narrative & priorities"),
            ("📸", "In-Game GameBar HUD", "F11 instant screenshots & F9 clip recording")
        ]

        for icon, title, desc in highlights:
            row = tk.Frame(features_card, bg="#0d1117")
            row.pack(fill="x", pady=4)
            tk.Label(row, text=icon, font=("Segoe UI", 11), bg="#0d1117").pack(side="left", padx=(0, 8))
            text_frame = tk.Frame(row, bg="#0d1117")
            text_frame.pack(side="left", fill="x", expand=True)
            tk.Label(text_frame, text=title, font=("Segoe UI", 9, "bold"), fg="#f0f6fc", bg="#0d1117").pack(anchor="w")
            tk.Label(text_frame, text=desc, font=("Segoe UI", 7), fg="#8b949e", bg="#0d1117").pack(anchor="w")

        # Action / Status Section
        self.action_frame = tk.Frame(body, bg="#080b10")
        self.action_frame.pack(fill="x", pady=(4, 0))

        # Big Glowing Primary Login Button
        self.btn_login = tk.Label(
            self.action_frame,
            text="🌐  LOG IN WITH XSOLLA",
            font=("Segoe UI", 11, "bold"),
            fg="#0d1117",
            bg="#70e1ff",
            cursor="hand2",
            padx=16,
            pady=12
        )
        self.btn_login.pack(fill="x", pady=(0, 10))
        self.btn_login.bind("<Button-1>", lambda e: self._on_browser_login_click())
        self.btn_login.bind("<Enter>", lambda e: self.btn_login.config(bg="#38bdf8"))
        self.btn_login.bind("<Leave>", lambda e: self.btn_login.config(bg="#70e1ff"))

        # Status Label (Shows "Waiting for browser login..." when clicked)
        self.status_lbl = tk.Label(
            self.action_frame,
            text="Sign in via browser to unlock in-game recap overlay",
            font=("Segoe UI", 8),
            fg="#8b949e",
            bg="#080b10"
        )
        self.status_lbl.pack(pady=(0, 12))

        # Secondary / Demo Access Button
        btn_guest = tk.Label(
            self.action_frame,
            text="⚡ Quick Demo / Guest Access",
            font=("Segoe UI", 9),
            fg="#70e1ff",
            bg="#161b22",
            cursor="hand2",
            padx=12,
            pady=8,
            highlightthickness=1,
            highlightbackground="#30363d"
        )
        btn_guest.pack(fill="x", pady=(0, 12))
        btn_guest.bind("<Button-1>", lambda e: self._on_guest_click())
        btn_guest.bind("<Enter>", lambda e: btn_guest.config(bg="#21262d", fg="#ffffff"))
        btn_guest.bind("<Leave>", lambda e: btn_guest.config(bg="#161b22", fg="#70e1ff"))

        # Footer
        tk.Label(
            body,
            text="Connected to team-noclip.vercel.app",
            font=("Segoe UI", 7),
            fg="#48546a",
            bg="#080b10"
        ).pack(side="bottom")

    def _on_browser_login_click(self):
        """Starts loopback server and opens user's browser to the login page."""
        self.is_waiting_browser = True
        self.btn_login.config(text="⏳  WAITING FOR BROWSER LOGIN...", bg="#21262d", fg="#70e1ff")
        self.status_lbl.config(
            text="Complete login in your browser window.\nThis app will connect and unlock automatically.",
            fg="#70e1ff"
        )

        auth_server.start_login_flow(
            on_success=self._on_auth_success_callback,
            base_url=WEBSITE_LOGIN_URL
        )

    def _on_guest_click(self):
        """Allows instant demo login for hackathon evaluation."""
        self.btn_login.config(text="✓  AUTHENTICATING GUEST...", bg="#238636", fg="#ffffff")
        self.status_lbl.config(text="Launching Xsolla Game Recap...", fg="#56d364")
        self.master.after(400, lambda: self._complete_login("Guest Player", "guest@xsolla.com", "demo_guest_token"))

    def _on_auth_success_callback(self, token: str, user: str, email: str):
        """Invoked from auth_server thread when browser callback is received."""
        # Thread-safe dispatch to Tkinter event loop
        self.master.after(0, lambda: self._show_success_and_unlock(user, email, token))

    def _show_success_and_unlock(self, user: str, email: str, token: str):
        if self.window and self.window.winfo_exists():
            self.btn_login.config(text=f"✓  AUTHENTICATION VERIFIED", bg="#238636", fg="#ffffff")
            self.status_lbl.config(text=f"Welcome, {user}! Launching Xsolla overlay...", fg="#56d364")
            self.master.after(600, lambda: self._complete_login(user, email, token))
        else:
            self._complete_login(user, email, token)

    def _complete_login(self, user: str, email: str, token: str):
        auth_state.log_in(user_label=user, email=email, token=token)
        self.destroy()
        self.on_login_success(token, user, email)
