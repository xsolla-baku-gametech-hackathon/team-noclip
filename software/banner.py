"""
Xsolla Game Recap - "Is Watching" Animated Toast Banner
Presents a high-tech, futuristic notification overlay when games launch.
Uses Win32 non-activating window flags so it never steals focus from games!
"""

import time
import math
import winsound
import threading
import tkinter as tk
from PIL import Image, ImageTk
import win32gui
import win32con

from config import load_config, ASSETS_DIR


class WatchingBanner:
    def __init__(self, master: tk.Tk):
        self.master = master
        self.window = None
        self._logo_photo = None

    def show(self, game_name: str, shortcut: str = "Ctrl+Shift+X"):
        """Trigger the animated 'Xsolla Game Recap is Watching' notification banner."""
        self.master.after(0, lambda: self._create_and_animate(game_name, shortcut))

    def _play_chime(self):
        try:
            cfg = load_config()
            if not cfg.get("enable_toast_sound", True):
                return
            # Subtle pleasant cyber chime
            winsound.Beep(1046, 60)   # C6
            time.sleep(0.04)
            winsound.Beep(1318, 90)   # E6
        except Exception:
            pass

    def _create_and_animate(self, game_name: str, shortcut: str):
        if self.window and self.window.winfo_exists():
            try:
                self.window.destroy()
            except Exception:
                pass

        self.window = tk.Toplevel(self.master)
        self.window.overrideredirect(True)
        self.window.attributes("-topmost", True)
        self.window.configure(bg="#141c22")

        # Dimensions & Screen Placement
        width = 470
        height = 76
        screen_w = self.window.winfo_screenwidth()
        x_pos = (screen_w - width) // 2

        target_y = 24
        start_y = -height - 10
        self.window.geometry(f"{width}x{height}+{x_pos}+{start_y}")

        # Non-activating & topmost style
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

        # Sleek Minimalist Canvas
        canvas = tk.Canvas(self.window, width=width, height=height, bg="#141c22", highlightthickness=0)
        canvas.pack(fill="both", expand=True)

        # Outer Neon Border
        canvas.create_rectangle(1, 1, width-1, height-1, outline="#70e1ff", width=2)
        canvas.create_rectangle(3, 3, width-3, height-3, outline="#223340", width=1)

        # Load & display official Xsolla logo image
        logo_path = ASSETS_DIR / "xsolla_logo_cropped.png"
        if logo_path.exists():
            try:
                pil_logo = Image.open(str(logo_path))
                # Scale nicely to height ~26px
                h = 26
                w = int(h * (pil_logo.width / pil_logo.height))
                pil_resized = pil_logo.resize((w, h), Image.Resampling.LANCZOS)
                self._logo_photo = ImageTk.PhotoImage(pil_resized)
                canvas.create_image(18, 25, image=self._logo_photo, anchor="w")
                text_x = 18 + w + 16
            except Exception:
                self._logo_photo = None
                text_x = 20
        else:
            text_x = 20

        # Status badge pill (Top Right)
        canvas.create_rectangle(width-138, 12, width-14, 28, fill="#1c2730", outline="#70e1ff", width=1)
        canvas.create_text(width-76, 20, text=f"[{shortcut}] TO OPEN", fill="#70e1ff", font=("Segoe UI", 8, "bold"), anchor="center")

        # Main Punchy Toast Message
        canvas.create_text(text_x, 24, text="⚡ Xsolla Game Recap is Watching", fill="#ffffff", font=("Segoe UI", 11, "bold"), anchor="w")

        # Subtitle with Clean Game Name
        short_game = (game_name[:28] + '...') if len(game_name) > 28 else game_name
        canvas.create_text(text_x, 50, text=f"Hooked: {short_game}  •  Capturing live events", fill="#8ba4b6", font=("Segoe UI", 9), anchor="w")

        # Play subtle chime
        threading.Thread(target=self._play_chime, daemon=True).start()

        # Physics Slide-In Animation
        current_y = start_y
        steps = 16

        def slide_in(step=0):
            nonlocal current_y
            if not self.window or not self.window.winfo_exists():
                return
            progress = (step + 1) / steps
            eased = 1 - math.pow(1 - progress, 3)
            current_y = int(start_y + (target_y - start_y) * eased)
            self.window.geometry(f"{width}x{height}+{x_pos}+{current_y}")

            if step + 1 < steps:
                self.master.after(16, lambda: slide_in(step + 1))
            else:
                cfg = load_config()
                duration = cfg.get("toast_duration_ms", 3800)
                self.master.after(duration, lambda: slide_out(0))

        def slide_out(step=0):
            nonlocal current_y
            if not self.window or not self.window.winfo_exists():
                return
            progress = (step + 1) / 12
            eased = math.pow(progress, 2)
            current_y = int(target_y - (target_y - start_y) * eased)
            self.window.geometry(f"{width}x{height}+{x_pos}+{current_y}")

            if step + 1 < 12:
                self.master.after(16, lambda: slide_out(step + 1))
            else:
                try:
                    self.window.destroy()
                except Exception:
                    pass
                self.window = None

        slide_in(0)
