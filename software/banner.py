"""
Xsolla Game Recap - Watching Toast Banner
Minimalist notification overlay sliding and fading in from the right edge.
Non-activating Win32 flags ensure games never lose window focus.
"""

import time
import math
import winsound
import threading
import tkinter as tk
from PIL import Image, ImageTk
import win32gui
import win32con

from config import load_config, ASSETS_DIR, make_window_invisible_to_capture


class WatchingBanner:
    def __init__(self, master: tk.Tk):
        self.master = master
        self.window = None
        self._logo_photo = None
        self._animating = False

    def show(self, game_name: str, shortcut: str = "Ctrl+Shift+X"):
        """Triggers the right edge slide and fade in toast notification."""
        self.master.after(0, lambda: self._create_and_animate(
            title="Xsolla Game Recap is Watching",
            subtitle=f"Hooked: {game_name}  |  Press {shortcut}"
        ))

    def show_capture(self, game_name: str, hint: str = "Saved in High Quality • [F11]"):
        """Triggers toast notification when a high-quality screenshot is captured."""
        self.master.after(0, lambda: self._create_and_animate(
            title="📸 Screenshot Saved!",
            subtitle=f"{game_name}  |  {hint}",
            title_color="#70e1ff"
        ))

    def show_record_started(self, game_name: str, shortcut: str = "F9"):
        """Triggers toast notification when video recording begins."""
        self.master.after(0, lambda: self._create_and_animate(
            title="🔴 Video Recording Started",
            subtitle=f"{game_name}  |  Press [{shortcut}] to stop & save",
            title_color="#ff453a"
        ))

    def show_record_stopped(self, filename: str, duration_str: str):
        """Triggers toast notification when video recording finishes and saves."""
        self.master.after(0, lambda: self._create_and_animate(
            title="💾 Video Saved Successfully!",
            subtitle=f"{filename} ({duration_str})  |  Saved to Captures",
            title_color="#30d158"
        ))

    def show_record_paused(self, game_name: str):
        """Triggers toast notification when video recording is paused."""
        self.master.after(0, lambda: self._create_and_animate(
            title="⏸️ Video Recording Paused",
            subtitle=f"{game_name}  |  Click Resume or press [F10]",
            title_color="#ffcc00"
        ))

    def show_record_resumed(self, game_name: str):
        """Triggers toast notification when video recording resumes."""
        self.master.after(0, lambda: self._create_and_animate(
            title="▶️ Video Recording Resumed",
            subtitle=f"{game_name}  |  Recording gameplay",
            title_color="#30d158"
        ))

    def _play_chime(self):
        try:
            cfg = load_config()
            if not cfg.get("enable_toast_sound", True):
                return
            winsound.Beep(1046, 50)
            time.sleep(0.03)
            winsound.Beep(1318, 70)
        except Exception:
            pass

    def _create_and_animate(self, title: str, subtitle: str, title_color: str = "#ffffff"):
        if self.window and self.window.winfo_exists():
            try:
                self.window.destroy()
            except Exception:
                pass

        self.window = tk.Toplevel(self.master)
        self.window.overrideredirect(True)
        self.window.attributes("-topmost", True)
        self.window.attributes("-alpha", 0.0)
        self.window.configure(bg="#0c1015")

        # Dimensions & Right-Edge Alignment
        width = 410
        height = 68
        screen_w = self.window.winfo_screenwidth()
        target_x = screen_w - width - 24
        target_y = 28
        start_x = screen_w + 10

        self.window.geometry(f"{width}x{height}+{start_x}+{target_y}")

        # Non activating window style
        self.window.update_idletasks()
        try:
            hwnd = win32gui.GetParent(self.window.winfo_id())
            if not hwnd:
                hwnd = self.window.winfo_id()
            style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
            style |= win32con.WS_EX_NOACTIVATE | win32con.WS_EX_TOOLWINDOW | win32con.WS_EX_TOPMOST
            win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, style)
        except Exception:
            pass
        make_window_invisible_to_capture(self.window)

        # Sleek Minimalist Canvas
        canvas = tk.Canvas(self.window, width=width, height=height, bg="#0c1015", highlightthickness=0)
        canvas.pack(fill="both", expand=True)

        # Outer Neon Border
        canvas.create_rectangle(1, 1, width - 1, height - 1, outline="#70e1ff", width=1)

        # Official Xsolla Logo
        logo_path = ASSETS_DIR / "xsolla_logo_cropped.png"
        text_x = 18
        if logo_path.exists():
            try:
                pil_logo = Image.open(str(logo_path))
                h = 24
                w = int(h * (pil_logo.width / pil_logo.height))
                resized = pil_logo.resize((w, h), Image.Resampling.LANCZOS)
                self._logo_photo = ImageTk.PhotoImage(resized)
                canvas.create_image(16, height // 2, image=self._logo_photo, anchor="w")
                text_x = 16 + w + 14
            except Exception:
                self._logo_photo = None

        # Clean Typography
        canvas.create_text(text_x, 22, text=title,
                           fill=title_color, font=("Segoe UI", 10, "bold"), anchor="w")

        short_sub = (subtitle[:36] + "...") if len(subtitle) > 36 else subtitle
        canvas.create_text(text_x, 46, text=short_sub,
                           fill="#8ba4b6", font=("Segoe UI", 9), anchor="w")

        # Subtle audio cue
        threading.Thread(target=self._play_chime, daemon=True).start()

        # Fade and Slide In from Right
        in_steps = 14
        fade_target = 0.96

        def fade_in_step(step=0):
            if not self.window or not self.window.winfo_exists():
                return
            progress = (step + 1) / in_steps
            eased = 1.0 - math.pow(1.0 - progress, 3)
            curr_x = int(start_x + (target_x - start_x) * eased)
            alpha = min(fade_target, progress * fade_target)

            try:
                self.window.attributes("-alpha", alpha)
                self.window.geometry(f"{width}x{height}+{curr_x}+{target_y}")
            except Exception:
                return

            if step + 1 < in_steps:
                self.master.after(16, lambda: fade_in_step(step + 1))
            else:
                cfg = load_config()
                hold_duration = cfg.get("toast_duration_ms", 3200)
                self.master.after(hold_duration, lambda: fade_out_step(0))

        # Fade and Slide Out to Right
        out_steps = 12

        def fade_out_step(step=0):
            if not self.window or not self.window.winfo_exists():
                return
            progress = (step + 1) / out_steps
            eased = math.pow(progress, 2)
            curr_x = int(target_x + 30 * eased)
            alpha = max(0.0, fade_target * (1.0 - progress))

            try:
                self.window.attributes("-alpha", alpha)
                self.window.geometry(f"{width}x{height}+{curr_x}+{target_y}")
            except Exception:
                return

            if step + 1 < out_steps:
                self.master.after(16, lambda: fade_out_step(step + 1))
            else:
                try:
                    self.window.destroy()
                except Exception:
                    pass
                self.window = None

        fade_in_step(0)
