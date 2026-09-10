"""
Xsolla Game Recap - Captures & Recordings Gallery
A sleek, custom frameless gallery window displaying captured high-quality screenshots and
video recordings, with category filters (ALL / PHOTOS / VIDEOS), 1-click preview,
native playback, custom draggable title strip, and smooth animated kinetic scrolling
with a custom neon capsule scrollbar.
All captures are saved directly in Documents/XSOLLA_gamerecap/captures/.
"""

import os
import sys
import ctypes
import subprocess
import tkinter as tk
from pathlib import Path
from typing import Optional, Callable, List
import cv2
from PIL import Image, ImageTk, ImageDraw, ImageFont

try:
    import win32gui
    import win32con
    import win32com.client
except ImportError:
    win32gui = None
    win32con = None
    win32com = None

from config import SCREENSHOTS_DIR, make_window_invisible_to_capture
from polaroid_service import PolaroidService


def force_foreground_hwnd(hwnd: int):
    """
    Brings a target window handle to the absolute front on Windows,
    bypassing foreground locks and OS focus restrictions.
    """
    if not hwnd or sys.platform != "win32":
        return
    try:
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32

        if not user32.IsWindow(hwnd):
            return

        # Restore window if minimized (SW_RESTORE = 9)
        user32.ShowWindow(hwnd, 9)

        # Bypass Windows SetForegroundWindow restrictions by attaching thread input
        current_thread = kernel32.GetCurrentThreadId()
        fg_hwnd = user32.GetForegroundWindow()
        fg_thread = user32.GetWindowThreadProcessId(fg_hwnd, None) if fg_hwnd else 0

        if fg_thread and fg_thread != current_thread:
            user32.AttachThreadInput(current_thread, fg_thread, True)

        # Bring to top of Z-order:
        # HWND_TOPMOST (-1) temporarily floats it above everything
        user32.SetWindowPos(hwnd, -1, 0, 0, 0, 0, 0x0001 | 0x0002)
        # HWND_NOTOPMOST (-2) drops persistent topmost while leaving it at the front of standard windows
        user32.SetWindowPos(hwnd, -2, 0, 0, 0, 0, 0x0001 | 0x0002)
        user32.BringWindowToTop(hwnd)
        user32.SetForegroundWindow(hwnd)
        user32.SetActiveWindow(hwnd)

        if fg_thread and fg_thread != current_thread:
            user32.AttachThreadInput(current_thread, fg_thread, False)
    except Exception as e:
        print(f"[Album] Failed to force foreground: {e}")



class AnimatedScrollBar(tk.Canvas):
    """
    Sleek, minimalist animated scrollbar with smooth rounded capsule thumb,
    neon hover glow, direct track jumping, and real-time canvas synchronization.
    """
    def __init__(self, parent, target_canvas: tk.Canvas, width: int = 10, bg: str = "#080b10", **kwargs):
        super().__init__(parent, width=width, bg=bg, highlightthickness=0, bd=0, **kwargs)
        self.target_canvas = target_canvas
        self.bar_width = width
        self.thumb_color_idle = "#28303e"
        self.thumb_color_hover = "#70e1ff"
        self.thumb_color_active = "#38bdf8"
        self.current_thumb_color = self.thumb_color_idle

        self._thumb_y0 = 0
        self._thumb_y1 = 30
        self._is_dragging = False
        self._is_hovered = False
        self._drag_start_y = 0
        self._start_thumb_y0 = 0

        self.bind("<Configure>", lambda e: self.update_thumb())
        self.bind("<Enter>", self._on_hover_enter)
        self.bind("<Leave>", self._on_hover_leave)
        self.bind("<Button-1>", self._on_press)
        self.bind("<B1-Motion>", self._on_drag)
        self.bind("<ButtonRelease-1>", self._on_release)

    def _on_hover_enter(self, event):
        self._is_hovered = True
        if not self._is_dragging:
            self.current_thumb_color = self.thumb_color_hover
            self.update_thumb()

    def _on_hover_leave(self, event):
        self._is_hovered = False
        if not self._is_dragging:
            self.current_thumb_color = self.thumb_color_idle
            self.update_thumb()

    def _on_press(self, event):
        if self._thumb_y0 <= event.y <= self._thumb_y1:
            self._is_dragging = True
            self._drag_start_y = event.y
            self._start_thumb_y0 = self._thumb_y0
            self.current_thumb_color = self.thumb_color_active
            self.update_thumb()
        else:
            # Clicked track: jump view smoothly
            h = self.winfo_height()
            if h > 10:
                frac = max(0.0, min(1.0, event.y / h))
                self.target_canvas.yview_moveto(frac)
                self.update_thumb()

    def _on_drag(self, event):
        if not self._is_dragging:
            return
        h = self.winfo_height()
        thumb_h = self._thumb_y1 - self._thumb_y0
        avail_h = h - thumb_h
        if avail_h <= 0:
            return
        delta_y = event.y - self._drag_start_y
        new_y0 = max(0, min(avail_h, self._start_thumb_y0 + delta_y))
        frac = new_y0 / avail_h
        self.target_canvas.yview_moveto(frac)
        self.update_thumb()

    def _on_release(self, event):
        self._is_dragging = False
        self.current_thumb_color = self.thumb_color_hover if self._is_hovered else self.thumb_color_idle
        self.update_thumb()

    def update_thumb(self):
        """Redraws the rounded capsule scrollbar thumb based on target canvas view."""
        try:
            h = self.winfo_height()
            if h <= 10:
                return

            yview = self.target_canvas.yview()
            top_frac, bot_frac = yview[0], yview[1]

            # If all content fits, hide the thumb
            if top_frac <= 0.0 and bot_frac >= 1.0:
                self.delete("all")
                return

            thumb_h = max(32, (bot_frac - top_frac) * h)
            avail_h = h - thumb_h
            thumb_y0 = top_frac * avail_h
            thumb_y1 = thumb_y0 + thumb_h

            self._thumb_y0 = thumb_y0
            self._thumb_y1 = thumb_y1

            self.delete("all")

            # Draw capsule thumb
            cx = self.bar_width // 2
            r = max(2, self.bar_width // 2 - 2)
            self.create_line(
                cx, thumb_y0 + r, cx, thumb_y1 - r,
                width=r * 2,
                fill=self.current_thumb_color,
                capstyle="round"
            )
        except Exception:
            pass


class AlbumViewerWindow:
    def __init__(self,
                 master: tk.Tk,
                 polaroid_svc: PolaroidService,
                 on_capture_request: Optional[Callable] = None,
                 on_record_request: Optional[Callable] = None,
                 on_pause_request: Optional[Callable] = None,
                 video_recorder: Optional[object] = None):
        self.master = master
        self.polaroid_svc = polaroid_svc
        self.on_capture_request = on_capture_request
        self.on_record_request = on_record_request
        self.on_pause_request = on_pause_request
        self.video_recorder = video_recorder
        self.window: Optional[tk.Toplevel] = None
        self._thumbnails = []

        # Current active filter: "ALL", "PHOTOS", "VIDEOS"
        self.current_filter = "ALL"

        # UI filter references
        self.btn_filter_all = None
        self.btn_filter_photos = None
        self.btn_filter_videos = None
        self.subtitle_lbl = None
        self.canvas = None
        self.scroll_frame = None
        self.scrollbar = None

        # Drag state for custom title strip
        self._drag_start_x = 0
        self._drag_start_y = 0

        # Smooth scrolling animation state
        self._target_scroll_y = 0.0
        self._scroll_animating = False

    def open(self):
        """Displays the stripped, custom frameless Visual Memories Album."""
        if self.window and self.window.winfo_exists():
            self.window.attributes("-topmost", True)
            self.window.deiconify()
            self.window.lift()
            self.window.focus_force()
            self._refresh_content()
            return

        self.window = tk.Toplevel(self.master)
        self.window.title("Xsolla Captures & Recordings Gallery")
        self.window.configure(bg="#080b10")

        # Strip standard Windows OS window bar & borders
        self.window.overrideredirect(True)
        self.window.attributes("-topmost", True)

        width = 900
        height = 650
        sw = self.window.winfo_screenwidth()
        sh = self.window.winfo_screenheight()
        x = (sw - width) // 2
        y = (sh - height) // 2
        self.window.geometry(f"{width}x{height}+{x}+{y}")

        # Shortcuts
        self.window.bind("<F5>", lambda e: self._refresh_content())
        self.window.bind("<Escape>", lambda e: self.close())

        self._build_ui()
        self._refresh_content()
        make_window_invisible_to_capture(self.window)

    def close(self):
        """Closes or hides the Album window."""
        if self.window and self.window.winfo_exists():
            self.window.withdraw()

    def _set_filter(self, filter_name: str):
        """Switches the active category filter (ALL / PHOTOS / VIDEOS)."""
        if self.current_filter == filter_name:
            return
        self.current_filter = filter_name
        self._update_filter_tabs_ui()
        self._refresh_content()

    def _update_filter_tabs_ui(self):
        """Updates the active visual highlight on filter tabs."""
        tabs = [
            ("ALL", self.btn_filter_all, "#70e1ff", "#080b10"),
            ("PHOTOS", self.btn_filter_photos, "#38bdf8", "#080b10"),
            ("VIDEOS", self.btn_filter_videos, "#ff005b", "#ffffff")
        ]
        for name, btn, active_bg, active_fg in tabs:
            if not btn or not btn.winfo_exists():
                continue
            if self.current_filter == name:
                btn.config(bg=active_bg, fg=active_fg)
            else:
                btn.config(bg="#141924", fg="#8b949e")

    def _build_ui(self):
        # Outer Border Frame (1px cyber border)
        main_border = tk.Frame(self.window, bg="#1e2633", padx=1, pady=1)
        main_border.pack(fill="both", expand=True)

        inner_container = tk.Frame(main_border, bg="#080b10")
        inner_container.pack(fill="both", expand=True)

        # 1. Custom Draggable Title Strip (Stripped Window Bar)
        title_strip = tk.Frame(inner_container, bg="#101520", height=38, padx=14)
        title_strip.pack(fill="x")
        title_strip.pack_propagate(False)

        title_strip.bind("<Button-1>", self._start_drag)
        title_strip.bind("<B1-Motion>", self._on_drag)

        title_left = tk.Frame(title_strip, bg="#101520")
        title_left.pack(side="left", fill="y")
        title_left.bind("<Button-1>", self._start_drag)
        title_left.bind("<B1-Motion>", self._on_drag)

        icon_lbl = tk.Label(
            title_left,
            text="⚡",
            font=("Segoe UI", 11, "bold"),
            fg="#70e1ff",
            bg="#101520"
        )
        icon_lbl.pack(side="left", padx=(0, 6))
        icon_lbl.bind("<Button-1>", self._start_drag)
        icon_lbl.bind("<B1-Motion>", self._on_drag)

        name_lbl = tk.Label(
            title_left,
            text="XSOLLA VISUAL MEMORIES",
            font=("Segoe UI", 10, "bold"),
            fg="#f0f6fc",
            bg="#101520"
        )
        name_lbl.pack(side="left")
        name_lbl.bind("<Button-1>", self._start_drag)
        name_lbl.bind("<B1-Motion>", self._on_drag)

        badge_lbl = tk.Label(
            title_left,
            text="GALLERY",
            font=("Segoe UI", 7, "bold"),
            fg="#8b949e",
            bg="#1b2230",
            padx=6,
            pady=1
        )
        badge_lbl.pack(side="left", padx=8)
        badge_lbl.bind("<Button-1>", self._start_drag)
        badge_lbl.bind("<B1-Motion>", self._on_drag)

        # Right window controls: Minimize & Close
        controls_right = tk.Frame(title_strip, bg="#101520")
        controls_right.pack(side="right", fill="y")

        btn_min = tk.Label(
            controls_right,
            text="—",
            font=("Segoe UI", 10),
            fg="#8b949e",
            bg="#101520",
            cursor="hand2",
            padx=10,
            pady=6
        )
        btn_min.pack(side="left")
        btn_min.bind("<Button-1>", lambda e: self.close())
        btn_min.bind("<Enter>", lambda e: btn_min.config(bg="#21262d", fg="#f0f6fc"))
        btn_min.bind("<Leave>", lambda e: btn_min.config(bg="#101520", fg="#8b949e"))

        btn_close = tk.Label(
            controls_right,
            text="✕",
            font=("Segoe UI", 10, "bold"),
            fg="#8b949e",
            bg="#101520",
            cursor="hand2",
            padx=10,
            pady=6
        )
        btn_close.pack(side="left")
        btn_close.bind("<Button-1>", lambda e: self.close())
        btn_close.bind("<Enter>", lambda e: btn_close.config(bg="#da3633", fg="#ffffff"))
        btn_close.bind("<Leave>", lambda e: btn_close.config(bg="#101520", fg="#8b949e"))

        # Thin divider under title strip
        tk.Frame(inner_container, bg="#1a2230", height=1).pack(fill="x")

        # 2. Controls & Filter Bar (Record/Snap removed; Category Filters added)
        header = tk.Frame(inner_container, bg="#0d111a", padx=20, pady=12)
        header.pack(fill="x")

        # Left: Title and subtitle
        title_box = tk.Frame(header, bg="#0d111a")
        title_box.pack(side="left")

        tk.Label(
            title_box,
            text="📸 CAPTURES & RECORDINGS",
            font=("Segoe UI", 12, "bold"),
            fg="#70e1ff",
            bg="#0d111a"
        ).pack(anchor="w")

        self.subtitle_lbl = tk.Label(
            title_box,
            text="Documents/XSOLLA_gamerecap/captures/",
            font=("Segoe UI", 9),
            fg="#8b949e",
            bg="#0d111a"
        )
        self.subtitle_lbl.pack(anchor="w", pady=(2, 0))

        # Center / Right: Media Category Filters (ALL / PHOTOS / VIDEOS)
        filter_frame = tk.Frame(header, bg="#141924", padx=2, pady=2, highlightthickness=1, highlightbackground="#1e2633")
        filter_frame.pack(side="left", padx=24)

        self.btn_filter_all = tk.Label(
            filter_frame,
            text="⚡ ALL",
            font=("Segoe UI", 9, "bold"),
            bg="#70e1ff",
            fg="#080b10",
            cursor="hand2",
            padx=12,
            pady=5
        )
        self.btn_filter_all.pack(side="left")
        self.btn_filter_all.bind("<Button-1>", lambda e: self._set_filter("ALL"))

        self.btn_filter_photos = tk.Label(
            filter_frame,
            text="📸 PHOTOS",
            font=("Segoe UI", 9, "bold"),
            bg="#141924",
            fg="#8b949e",
            cursor="hand2",
            padx=12,
            pady=5
        )
        self.btn_filter_photos.pack(side="left")
        self.btn_filter_photos.bind("<Button-1>", lambda e: self._set_filter("PHOTOS"))

        self.btn_filter_videos = tk.Label(
            filter_frame,
            text="🎬 VIDEOS",
            font=("Segoe UI", 9, "bold"),
            bg="#141924",
            fg="#8b949e",
            cursor="hand2",
            padx=12,
            pady=5
        )
        self.btn_filter_videos.pack(side="left")
        self.btn_filter_videos.bind("<Button-1>", lambda e: self._set_filter("VIDEOS"))

        # Right: Utility Actions (Open Folder & Refresh)
        btn_box = tk.Frame(header, bg="#0d111a")
        btn_box.pack(side="right")

        btn_folder = tk.Button(
            btn_box,
            text="📂 Open Folder",
            font=("Segoe UI", 9, "bold"),
            bg="#21262d",
            fg="#f0f6fc",
            activebackground="#30363d",
            activeforeground="#70e1ff",
            bd=0,
            padx=10,
            pady=5,
            cursor="hand2",
            command=self._open_captures_folder
        )
        btn_folder.pack(side="left", padx=4)
        btn_folder.bind("<Button-1>", lambda e: self._open_captures_folder())

        btn_refresh = tk.Button(
            btn_box,
            text="🔄 Refresh",
            font=("Segoe UI", 9),
            bg="#161b22",
            fg="#8b949e",
            activebackground="#21262d",
            activeforeground="#f0f6fc",
            bd=0,
            padx=8,
            pady=5,
            cursor="hand2",
            command=self._refresh_content
        )
        btn_refresh.pack(side="left", padx=4)

        # 3. Scrollable Gallery Body with Custom Animated Scrollbar
        gallery_wrapper = tk.Frame(inner_container, bg="#080b10")
        gallery_wrapper.pack(fill="both", expand=True, padx=16, pady=10)

        self.canvas = tk.Canvas(gallery_wrapper, bg="#080b10", highlightthickness=0)
        self.scroll_frame = tk.Frame(self.canvas, bg="#080b10")

        self.scroll_frame.bind(
            "<Configure>",
            lambda e: self._on_scroll_frame_configure()
        )

        self.canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        self.canvas.pack(side="left", fill="both", expand=True)

        # Custom Animated Neon Scrollbar
        self.scrollbar = AnimatedScrollBar(gallery_wrapper, target_canvas=self.canvas, width=10, bg="#080b10")
        self.scrollbar.pack(side="right", fill="y", padx=(6, 0))

        # Mouse wheel smooth kinetic scroll binding
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _start_drag(self, event):
        if self.window and self.window.winfo_exists():
            self.window.lift()
        self._drag_start_x = event.x
        self._drag_start_y = event.y

    def _on_drag(self, event):
        if self.window and self.window.winfo_exists():
            x = self.window.winfo_x() + (event.x - self._drag_start_x)
            y = self.window.winfo_y() + (event.y - self._drag_start_y)
            self.window.geometry(f"+{x}+{y}")

    def _on_scroll_frame_configure(self):
        if self.canvas and self.canvas.winfo_exists():
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
            if self.scrollbar:
                self.scrollbar.update_thumb()

    def _on_mousewheel(self, event):
        """Smooth animated kinetic scrolling with ease-out interpolation."""
        if not self.window or not self.window.winfo_exists() or not self.canvas.winfo_exists():
            return

        step = -1.0 * (event.delta / 120.0) * 0.075
        current_y = self.canvas.yview()[0]

        if not self._scroll_animating:
            self._target_scroll_y = current_y

        yview = self.canvas.yview()
        view_size = yview[1] - yview[0]
        max_scroll = max(0.0, 1.0 - view_size)
        self._target_scroll_y = max(0.0, min(max_scroll, self._target_scroll_y + step))

        if not self._scroll_animating:
            self._scroll_animating = True
            self._animate_smooth_scroll()

    def _animate_smooth_scroll(self):
        """60 FPS smooth lerp ease-out scroll animation."""
        if not self.window or not self.window.winfo_exists() or not self.canvas.winfo_exists():
            self._scroll_animating = False
            return

        current_y = self.canvas.yview()[0]
        diff = self._target_scroll_y - current_y

        if abs(diff) > 0.001:
            new_y = current_y + diff * 0.26
            self.canvas.yview_moveto(new_y)
            if self.scrollbar:
                self.scrollbar.update_thumb()
            self.window.after(16, self._animate_smooth_scroll)
        else:
            self.canvas.yview_moveto(self._target_scroll_y)
            if self.scrollbar:
                self.scrollbar.update_thumb()
            self._scroll_animating = False

    def _open_captures_folder(self):
        """Opens the captures directory in Windows File Explorer and forces it to the absolute front."""
        folder_path = SCREENSHOTS_DIR.resolve()
        folder_str = str(folder_path)

        # 1. Lower Album window so it won't obscure the newly opened explorer window
        if self.window and self.window.winfo_exists():
            self.window.attributes("-topmost", False)
            self.window.lower()

        # 2. Open folder directly via Windows ShellExecute (os.startfile) or explorer.exe
        try:
            os.startfile(folder_str)
        except Exception:
            try:
                subprocess.Popen(["explorer.exe", folder_str])
            except Exception as err:
                print(f"[Album] Error opening captures folder: {err}")

        # 3. Schedule locating and forcing the Explorer window to the front
        for delay in (120, 350, 700, 1200):
            if self.window and self.window.winfo_exists():
                self.window.after(delay, lambda f=folder_str: self._locate_and_focus_explorer(f))

    def _locate_and_focus_explorer(self, folder_str: str):
        """Finds the Explorer window for the captures directory and pulls it to the front."""
        target_hwnd = None
        if win32com:
            try:
                shell = win32com.client.Dispatch("Shell.Application")
                for w in shell.Windows():
                    try:
                        url = getattr(w, "LocationURL", "") or ""
                        url_norm = url.replace("file:///", "").replace("/", "\\").lower()
                        name = getattr(w, "LocationName", "") or ""
                        if folder_str.lower() in url_norm or "captures" in name.lower() or "captures" in url_norm:
                            target_hwnd = w.HWND
                            break
                    except Exception:
                        pass
            except Exception:
                pass

        if not target_hwnd and win32gui:
            try:
                def enum_cb(hwnd, extra):
                    if win32gui.IsWindowVisible(hwnd):
                        cls = win32gui.GetClassName(hwnd)
                        if cls == "CabinetWClass":
                            title = win32gui.GetWindowText(hwnd).lower()
                            if "captures" in title or "xsolla" in title:
                                extra.append(hwnd)
                found = []
                win32gui.EnumWindows(enum_cb, found)
                if found:
                    target_hwnd = found[0]
            except Exception:
                pass

        if target_hwnd:
            force_foreground_hwnd(target_hwnd)

    def _open_media(self, media_path: Path):
        """Opens a screenshot or video file and yields foreground focus to the media viewer."""
        if self.window and self.window.winfo_exists():
            self.window.attributes("-topmost", False)
            self.window.lower()
        try:
            os.startfile(str(media_path))
        except Exception as e:
            print(f"[Album] Error opening media {media_path}: {e}")

    def _extract_video_thumbnail(self, video_path: Path, target_w: int = 360) -> Optional[Image.Image]:
        """Extracts a high-quality video thumbnail with an overlaid duration badge and play icon."""
        try:
            cap = cv2.VideoCapture(str(video_path))
            if not cap.isOpened():
                return None

            fps = cap.get(cv2.CAP_PROP_FPS) or 20.0
            count = cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0
            if count > 8:
                cap.set(cv2.CAP_PROP_POS_FRAMES, min(4, int(count - 1)))
            ret, frame = cap.read()
            cap.release()

            if not ret or frame is None:
                return None

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(rgb)
            target_h = int(pil_img.height * (target_w / pil_img.width))
            pil_img = pil_img.resize((target_w, target_h), Image.Resampling.LANCZOS)

            # Draw translucent play icon and duration badge
            draw = ImageDraw.Draw(pil_img, "RGBA")
            cx, cy = target_w // 2, target_h // 2
            r = 24
            # Center frosted play circle
            draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(0, 0, 0, 160), outline=(255, 255, 255, 220), width=2)
            # Center play triangle
            draw.polygon([(cx - 7, cy - 12), (cx - 7, cy + 12), (cx + 13, cy)], fill=(255, 255, 255, 240))

            # Duration badge in top-left
            dur_sec = int(count / fps) if fps > 0 else 0
            dur_str = f"{dur_sec // 60:02d}:{dur_sec % 60:02d}"
            badge_w = 84
            draw.rounded_rectangle((8, 8, 8 + badge_w, 30), radius=5, fill=(255, 0, 91, 230))
            font = ImageFont.load_default()
            draw.text((16, 12), f"VIDEO {dur_str}", fill="white", font=font)

            return pil_img
        except Exception as err:
            print(f"[Album] Error extracting video thumbnail for {video_path}: {err}")
            return None

    def _refresh_content(self):
        """Filters memories based on current_filter and renders cards."""
        if not self.scroll_frame or not self.scroll_frame.winfo_exists():
            return

        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
        self._thumbnails.clear()

        # Reset scroll view to top on refresh/filter change
        self.canvas.yview_moveto(0.0)
        self._target_scroll_y = 0.0

        all_memories = self.polaroid_svc.get_recent_memories(limit=100)
        photos = [p for p in all_memories if p.suffix.lower() in ('.png', '.jpg', '.jpeg')]
        videos = [p for p in all_memories if p.suffix.lower() in ('.mp4', '.mkv', '.avi', '.mov')]

        # Update tab counts
        if self.btn_filter_all and self.btn_filter_all.winfo_exists():
            self.btn_filter_all.config(text=f"⚡ ALL ({len(all_memories)})")
        if self.btn_filter_photos and self.btn_filter_photos.winfo_exists():
            self.btn_filter_photos.config(text=f"📸 PHOTOS ({len(photos)})")
        if self.btn_filter_videos and self.btn_filter_videos.winfo_exists():
            self.btn_filter_videos.config(text=f"🎬 VIDEOS ({len(videos)})")

        self._update_filter_tabs_ui()

        # Filter items
        if self.current_filter == "PHOTOS":
            items_to_display = photos
            empty_title = "NO SCREENSHOTS CAPTURED YET"
            empty_desc = "Press [F11] in any game to take instant high-quality screenshots!"
        elif self.current_filter == "VIDEOS":
            items_to_display = videos
            empty_title = "NO VIDEO RECORDINGS YET"
            empty_desc = "Press [F9] in any game to start recording smooth gameplay clips!"
        else:
            items_to_display = all_memories
            empty_title = "NO CAPTURES OR RECORDINGS YET"
            empty_desc = "Press [F11] for screenshot or [F9] for video recording in any game!"

        if self.subtitle_lbl and self.subtitle_lbl.winfo_exists():
            self.subtitle_lbl.config(
                text=f"Showing {len(items_to_display)} items • [F11] Screenshot • [F9] Video Record"
            )

        if not items_to_display:
            empty_box = tk.Frame(self.scroll_frame, bg="#080b10", pady=70)
            empty_box.pack(fill="both", expand=True)

            tk.Label(
                empty_box,
                text=empty_title,
                font=("Segoe UI", 12, "bold"),
                fg="#6e7681",
                bg="#080b10"
            ).pack()

            tk.Label(
                empty_box,
                text=empty_desc,
                font=("Segoe UI", 10),
                fg="#484f58",
                bg="#080b10",
                pady=10
            ).pack()
            return

        # Render Cards in a 2-column grid
        columns = 2
        for idx, media_path in enumerate(items_to_display):
            row = idx // columns
            col = idx % columns
            is_video = media_path.suffix.lower() in ('.mp4', '.mkv', '.avi', '.mov')

            card_border = "#ff005b" if is_video else "#1a2230"
            card_box = tk.Frame(
                self.scroll_frame,
                bg="#0f141f",
                padx=8,
                pady=8,
                highlightthickness=1,
                highlightbackground=card_border
            )
            card_box.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")

            try:
                if is_video:
                    pil_img = self._extract_video_thumbnail(media_path, target_w=370)
                    if not pil_img:
                        pil_img = Image.new("RGB", (370, 208), color="#161b24")
                        draw = ImageDraw.Draw(pil_img)
                        draw.text((130, 98), "🎬 [Video Clip]", fill="white", font=ImageFont.load_default())
                else:
                    pil_img = Image.open(str(media_path))
                    target_w = 370
                    target_h = int(pil_img.height * (target_w / pil_img.width))
                    pil_img = pil_img.resize((target_w, target_h), Image.Resampling.LANCZOS)

                tk_thumb = ImageTk.PhotoImage(pil_img)
                self._thumbnails.append(tk_thumb)

                img_lbl = tk.Label(card_box, image=tk_thumb, bg="#0f141f", cursor="hand2")
                img_lbl.pack()
                img_lbl.bind("<Button-1>", lambda e, p=media_path: self._open_media(p))

                # Card footer bar
                footer_bar = tk.Frame(card_box, bg="#0f141f", pady=5)
                footer_bar.pack(fill="x")

                display_name = media_path.stem
                if len(display_name) > 30:
                    display_name = display_name[:27] + "..."

                lbl_name = tk.Label(
                    footer_bar,
                    text=display_name,
                    font=("Consolas", 8),
                    fg="#8b949e",
                    bg="#0f141f"
                )
                lbl_name.pack(side="left")

                if is_video:
                    btn_act = tk.Label(
                        footer_bar,
                        text="▶ Play Video",
                        font=("Segoe UI", 8, "bold"),
                        fg="#ff5c5c",
                        bg="#0f141f",
                        cursor="hand2"
                    )
                else:
                    btn_act = tk.Label(
                        footer_bar,
                        text="View Photo ↗",
                        font=("Segoe UI", 8, "bold"),
                        fg="#70e1ff",
                        bg="#0f141f",
                        cursor="hand2"
                    )

                btn_act.pack(side="right")
                btn_act.bind("<Button-1>", lambda e, p=media_path: self._open_media(p))

            except Exception as err:
                print(f"[Album] Error loading {media_path}: {err}")

        # Update scrollbar after content rendered
        self.window.after(50, lambda: self.scrollbar.update_thumb() if self.scrollbar else None)
