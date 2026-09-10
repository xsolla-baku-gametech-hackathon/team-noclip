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
import win32gui
import win32con

from config import load_config


class WatchingBanner:
    def __init__(self, master: tk.Tk):
        self.master = master
        self.window = None
        self.is_showing = False

    def show(self, game_name: str, shortcut: str = "Ctrl+Shift+X"):
        """Trigger the animated 'Xsolla Game Recap is Watching' notification banner."""
        # Always run on main Tkinter GUI thread
        self.master.after(0, lambda: self._create_and_animate(game_name, shortcut))

    def _play_chime(self):
        """Subtle high-tech cybernetic chime in background thread."""
        try:
            cfg = load_config()
            if not cfg.get("enable_toast_sound", True):
                return
            # Ascending two-tone pleasant chime
            winsound.Beep(987, 80)   # B5
            time.sleep(0.04)
            winsound.Beep(1318, 120)  # E6
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
        self.window.configure(bg="#0b0d13")

        # Dimensions & Screen Placement
        width = 460
        height = 84
        screen_w = self.window.winfo_screenwidth()
        x_pos = (screen_w - width) // 2  # Centered at the top

        target_y = 28
        start_y = -height - 10
        self.window.geometry(f"{width}x{height}+{x_pos}+{start_y}")

        # Set Windows WS_EX_NOACTIVATE & WS_EX_TOOLWINDOW so it NEVER interrupts game focus
        self.window.update_idletasks()
        try:
            hwnd = win32gui.GetParent(self.window.winfo_id())
            if not hwnd:
                hwnd = self.window.winfo_id()
            style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
            style |= win32con.WS_EX_NOACTIVATE | win32con.WS_EX_TOOLWINDOW | win32con.WS_EX_TOPMOST
            win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, style)
        except Exception as err:
            print(f"[Banner] Style flag note: {err}")

        # Cyberpunk Glassmorphism Canvas
        canvas = tk.Canvas(self.window, width=width, height=height, bg="#0b0d13", highlightthickness=0)
        canvas.pack(fill="both", expand=True)

        # Outer Neon Border with rounded corners effect
        canvas.create_rectangle(2, 2, width-2, height-2, outline="#00f5d4", width=2)
        canvas.create_rectangle(4, 4, width-4, height-4, outline="#7928ca", width=1)

        # Glowing Header Pill
        canvas.create_rectangle(14, 12, 128, 28, fill="#161b26", outline="#00f5d4", width=1)
        # Pulsing Green Dot
        canvas.create_oval(20, 17, 26, 23, fill="#00ff88", outline="#00ff88")
        canvas.create_text(32, 20, text="XSOLLA RECAP", fill="#00f5d4", font=("Segoe UI", 8, "bold"), anchor="w")

        # Hotkey Pill (Top Right)
        canvas.create_rectangle(width-140, 12, width-14, 28, fill="#1c162b", outline="#ff007f", width=1)
        canvas.create_text(width-77, 20, text=f"PRESS [{shortcut}]", fill="#ff70a6", font=("Segoe UI", 8, "bold"), anchor="center")

        # Core Punchy Banner Text
        canvas.create_text(16, 44, text="⚡ Xsolla Game Recap is Watching", fill="#ffffff", font=("Segoe UI", 12, "bold"), anchor="w")

        # Subtitle with game name
        short_game = (game_name[:24] + '...') if len(game_name) > 24 else game_name
        canvas.create_text(16, 64, text=f"Hooked: {short_game}  •  Capturing live highlights & stats", fill="#94a3b8", font=("Segoe UI", 9), anchor="w")

        # Play chime
        threading.Thread(target=self._play_chime, daemon=True).start()

        # Smooth Slide-In Animation (Physics Ease-Out)
        current_y = start_y
        steps = 18

        def slide_in(step=0):
            nonlocal current_y
            if not self.window or not self.window.winfo_exists():
                return
            progress = (step + 1) / steps
            # Smooth ease-out curve
            eased = 1 - math.pow(1 - progress, 3)
            current_y = int(start_y + (target_y - start_y) * eased)
            self.window.geometry(f"{width}x{height}+{x_pos}+{current_y}")

            if step + 1 < steps:
                self.master.after(16, lambda: slide_in(step + 1))
            else:
                # Hold visible for configured duration, then slide out
                cfg = load_config()
                duration = cfg.get("toast_duration_ms", 4000)
                self.master.after(duration, lambda: slide_out(0))

        def slide_out(step=0):
            nonlocal current_y
            if not self.window or not self.window.winfo_exists():
                return
            progress = (step + 1) / 14
            # Ease-in curve
            eased = math.pow(progress, 2)
            current_y = int(target_y - (target_y - start_y) * eased)
            self.window.geometry(f"{width}x{height}+{x_pos}+{current_y}")

            if step + 1 < 14:
                self.master.after(16, lambda: slide_out(step + 1))
            else:
                try:
                    self.window.destroy()
                except Exception:
                    pass
                self.window = None

        slide_in(0)
