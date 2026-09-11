"""
Xsolla Game Recap - Visual Memories Tab & Gallery
A sleek, integrated Visual Memories tab panel embedded directly inside
the Xsolla GameBar navbar overlay. Zero clutter, responsive 2-column
grid, category filter tabs, custom kinetic scrollbar, and non-blocking
folder access that opens recordings on top without closing the navbar.
All captures are saved directly in Documents/XSOLLA_gamerecap/recordings/.
"""

import os
import subprocess
import tkinter as tk
from pathlib import Path
from typing import Optional, Callable, List
import cv2
from PIL import Image, ImageTk, ImageDraw, ImageFont

from config import RECORDINGS_DIR, SCREENSHOTS_DIR, ensure_data_dir, make_window_invisible_to_capture
from polaroid_service import PolaroidService



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


class VisualMemoriesTab(tk.Frame):
    """
    The integrated Visual Memories tab component embedded directly in the GameBar navbar.
    Displays screenshots and video recordings in a 2-column card grid, supports categories,
    and opens the recordings folder in foreground without closing the navbar.
    """
    def __init__(self,
                 parent,
                 polaroid_svc: PolaroidService,
                 on_capture_request: Optional[Callable] = None,
                 on_record_request: Optional[Callable] = None,
                 on_pause_request: Optional[Callable] = None,
                 on_close_tab: Optional[Callable] = None,
                 on_open_folder: Optional[Callable] = None,
                 on_media_opened: Optional[Callable] = None,
                 get_backdrop_hwnd: Optional[Callable] = None,
                 get_window_hwnd: Optional[Callable] = None,
                 video_recorder: Optional[object] = None,
                 **kwargs):
        super().__init__(parent, bg="#080b10", **kwargs)
        self.polaroid_svc = polaroid_svc
        self.on_capture_request = on_capture_request
        self.on_record_request = on_record_request
        self.on_pause_request = on_pause_request
        self.on_close_tab = on_close_tab
        self.on_open_folder = on_open_folder
        self.on_media_opened = on_media_opened
        self.get_backdrop_hwnd = get_backdrop_hwnd
        self.get_window_hwnd = get_window_hwnd
        self.video_recorder = video_recorder

        self._thumbnails = []
        self.current_filter = "ALL"

        self.btn_filter_all = None
        self.btn_filter_photos = None
        self.btn_filter_videos = None
        self.subtitle_lbl = None
        self.canvas = None
        self.scroll_frame = None
        self.scrollbar = None

        self._target_scroll_y = 0.0
        self._scroll_animating = False

        # In-Overlay Media Viewer & Player State
        self.is_viewer_active = False
        self.viewer_frame: Optional[tk.Frame] = None
        self._video_cap: Optional[cv2.VideoCapture] = None
        self._video_timer_id: Optional[str] = None
        self._video_is_playing: bool = False
        self._video_seeking: bool = False
        self._video_total_frames: int = 0
        self._video_fps: float = 30.0
        self._current_photo_list: List[Path] = []
        self._current_photo_idx: int = 0
        self._current_photo_tk = None
        self._current_video_tk = None
        self._updating_scrubber: bool = False

        self._build_ui()

    def _build_ui(self):
        # 1. Header & Filter Strip
        header = tk.Frame(self, bg="#0d111a", padx=16, pady=10)
        header.pack(fill="x")

        # Left: Title and subtitle
        title_box = tk.Frame(header, bg="#0d111a")
        title_box.pack(side="left")

        tk.Label(
            title_box,
            text="📸 VISUAL MEMORIES",
            font=("Segoe UI", 11, "bold"),
            fg="#70e1ff",
            bg="#0d111a"
        ).pack(anchor="w")

        self.subtitle_lbl = tk.Label(
            title_box,
            text="Documents/XSOLLA_gamerecap/recordings/",
            font=("Segoe UI", 8),
            fg="#8b949e",
            bg="#0d111a"
        )
        self.subtitle_lbl.pack(anchor="w", pady=(2, 0))

        # Center / Left: Category Filter Tabs
        filter_frame = tk.Frame(header, bg="#141924", padx=2, pady=2, highlightthickness=1, highlightbackground="#1e2633")
        filter_frame.pack(side="left", padx=18)

        self.btn_filter_all = tk.Label(
            filter_frame,
            text="⚡ ALL",
            font=("Segoe UI", 9, "bold"),
            bg="#70e1ff",
            fg="#080b10",
            cursor="hand2",
            padx=10,
            pady=4
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
            padx=10,
            pady=4
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
            padx=10,
            pady=4
        )
        self.btn_filter_videos.pack(side="left")
        self.btn_filter_videos.bind("<Button-1>", lambda e: self._set_filter("VIDEOS"))

        # Right: Utility Actions (Open Folder, Refresh, Close Tab)
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
            pady=4,
            cursor="hand2",
            command=self._on_folder_btn_click
        )
        btn_folder.pack(side="left", padx=3)

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
            pady=4,
            cursor="hand2",
            command=self.refresh
        )
        btn_refresh.pack(side="left", padx=3)

        if self.on_close_tab:
            btn_close = tk.Label(
                btn_box,
                text="✕",
                font=("Segoe UI", 10, "bold"),
                fg="#8b949e",
                bg="#0d111a",
                cursor="hand2",
                padx=8,
                pady=4
            )
            btn_close.pack(side="left", padx=(4, 0))
            btn_close.bind("<Button-1>", lambda e: self.on_close_tab())
            btn_close.bind("<Enter>", lambda e: btn_close.config(fg="#ff5c5c", bg="#21262d"))
            btn_close.bind("<Leave>", lambda e: btn_close.config(fg="#8b949e", bg="#0d111a"))

        # 2. Scrollable Gallery Body
        gallery_wrapper = tk.Frame(self, bg="#080b10")
        gallery_wrapper.pack(fill="both", expand=True, padx=14, pady=8)

        self.canvas = tk.Canvas(gallery_wrapper, bg="#080b10", highlightthickness=0)
        self.scroll_frame = tk.Frame(self.canvas, bg="#080b10")

        self.scroll_frame.bind(
            "<Configure>",
            lambda e: self._on_scroll_frame_configure()
        )

        self.canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.scrollbar = AnimatedScrollBar(gallery_wrapper, target_canvas=self.canvas, width=10, bg="#080b10")
        self.scrollbar.pack(side="right", fill="y", padx=(6, 0))

        # Mouse wheel bindings scoped to tab canvas and frame
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.bind("<MouseWheel>", self._on_mousewheel)

    def _set_filter(self, filter_name: str):
        if self.current_filter == filter_name:
            return
        self.current_filter = filter_name
        self._update_filter_tabs_ui()
        self.refresh()

    def _update_filter_tabs_ui(self):
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

    def _on_scroll_frame_configure(self):
        if self.canvas and self.canvas.winfo_exists():
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
            if self.scrollbar:
                self.scrollbar.update_thumb()

    def _on_mousewheel(self, event):
        if not self.canvas or not self.canvas.winfo_exists():
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
        if not self.winfo_exists() or not self.canvas.winfo_exists():
            self._scroll_animating = False
            return

        current_y = self.canvas.yview()[0]
        diff = self._target_scroll_y - current_y

        if abs(diff) > 0.001:
            new_y = current_y + diff * 0.26
            self.canvas.yview_moveto(new_y)
            if self.scrollbar:
                self.scrollbar.update_thumb()
            self.after(16, self._animate_smooth_scroll)
        else:
            self.canvas.yview_moveto(self._target_scroll_y)
            if self.scrollbar:
                self.scrollbar.update_thumb()
            self._scroll_animating = False

    def _on_folder_btn_click(self):
        """Called when user clicks 'Open Folder'. Delegates to custom handler or opens directly."""
        if self.on_open_folder:
            try:
                self.on_open_folder()
                return
            except Exception:
                pass
        self._open_recordings_folder()

    def _open_recordings_folder(self):
        """
        Opens the recordings folder in Windows File Explorer and elevates it to topmost
        in the foreground WITHOUT closing, withdrawing, or lowering the navbar.
        """
        ensure_data_dir()
        folder_path = str(RECORDINGS_DIR.resolve())

        import ctypes
        user32 = ctypes.windll.user32
        user32.AllowSetForegroundWindow(-1)

        try:
            subprocess.Popen(["explorer.exe", folder_path])
        except Exception:
            try:
                os.startfile(folder_path)
            except Exception as err:
                print(f"[Album] Error opening recordings folder: {err}")

        # Bring Explorer on top of everything (above the Xsolla overlay and backdrop)
        def _bring_explorer_on_top():
            try:
                user32.AllowSetForegroundWindow(-1)
                WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_void_p)
                target_hwnds = []

                def enum_cb(hwnd, lparam):
                    if not user32.IsWindowVisible(hwnd):
                        return True
                    cbuf = ctypes.create_unicode_buffer(256)
                    user32.GetClassNameW(hwnd, cbuf, 256)
                    if cbuf.value in ("CabinetWClass", "ExploreWClass"):
                        tbuf = ctypes.create_unicode_buffer(256)
                        user32.GetWindowTextW(hwnd, tbuf, 256)
                        txt = tbuf.value.lower()
                        if "recording" in txt or "xsolla" in txt or "explorer" in txt:
                            target_hwnds.append(hwnd)
                    return True

                cb = WNDENUMPROC(enum_cb)
                user32.EnumWindows(cb, 0)

                # Secondary check via Shell COM if title matching didn't catch it
                if not target_hwnds:
                    try:
                        import win32com.client
                        shell = win32com.client.Dispatch("Shell.Application")
                        for w in shell.Windows():
                            loc_url = str(getattr(w, "LocationURL", "")).lower()
                            loc_name = str(getattr(w, "LocationName", "")).lower()
                            if "recording" in loc_url or "xsolla" in loc_url or "recording" in loc_name or "xsolla" in loc_name:
                                h = getattr(w, "HWND", 0)
                                if h and user32.IsWindowVisible(h):
                                    target_hwnds.append(h)
                    except Exception:
                        pass

                fore_hwnd = user32.GetForegroundWindow()
                fore_tid = user32.GetWindowThreadProcessId(fore_hwnd, None)
                app_tid = ctypes.windll.kernel32.GetCurrentThreadId()

                w_hwnd = self.get_window_hwnd() if self.get_window_hwnd else None
                b_hwnd = self.get_backdrop_hwnd() if self.get_backdrop_hwnd else None

                for hwnd in target_hwnds:
                    target_tid = user32.GetWindowThreadProcessId(hwnd, None)
                    if user32.IsIconic(hwnd):
                        user32.ShowWindow(hwnd, 9)  # SW_RESTORE
                    else:
                        user32.ShowWindow(hwnd, 5)  # SW_SHOW

                    if fore_tid and fore_tid != app_tid:
                        user32.AttachThreadInput(app_tid, fore_tid, True)
                    if target_tid and target_tid != app_tid:
                        user32.AttachThreadInput(app_tid, target_tid, True)

                    # 1. Elevate Explorer window to TOP OF EVERYTHING (HWND_TOPMOST = -1)
                    user32.SetWindowPos(hwnd, -1, 0, 0, 0, 0, 0x0001 | 0x0002 | 0x0040)
                    user32.BringWindowToTop(hwnd)
                    user32.SetForegroundWindow(hwnd)
                    try:
                        user32.SwitchToThisWindow(hwnd, True)
                    except Exception:
                        pass

                    # 2. Position the GameBar navbar overlay immediately BEHIND Explorer
                    if w_hwnd and w_hwnd != hwnd:
                        user32.SetWindowPos(w_hwnd, hwnd, 0, 0, 0, 0, 0x0001 | 0x0002 | 0x0010)

                    # 3. Position the dim backdrop shadow immediately BEHIND the navbar overlay
                    if b_hwnd and b_hwnd != hwnd:
                        insert_behind = w_hwnd if (w_hwnd and w_hwnd != hwnd) else hwnd
                        user32.SetWindowPos(b_hwnd, insert_behind, 0, 0, 0, 0, 0x0001 | 0x0002 | 0x0010)

                    if target_tid and target_tid != app_tid:
                        user32.AttachThreadInput(app_tid, target_tid, False)
                    if fore_tid and fore_tid != app_tid:
                        user32.AttachThreadInput(app_tid, fore_tid, False)
            except Exception as e:
                print(f"[Album] Exception elevating Explorer: {e}")

        for delay in (100, 250, 450, 750, 1200):
            self.after(delay, _bring_explorer_on_top)

    def _open_media(self, media_path: Path):
        """Opens a media file directly in-overlay (in-game photo viewer or video player)."""
        is_video = media_path.suffix.lower() in ('.mp4', '.mkv', '.avi', '.mov')
        if is_video:
            self._show_video_player(media_path)
        else:
            self._show_photo_viewer(media_path)

    # -------------------------------------------------------------------------
    # In-Overlay Photo Viewer
    # -------------------------------------------------------------------------
    def _show_photo_viewer(self, media_path: Path):
        """Displays high-resolution screenshot viewer directly inside the in-game overlay."""
        self.close_viewer()
        self.is_viewer_active = True

        all_memories = self.polaroid_svc.get_recent_memories(limit=100)
        self._current_photo_list = [p for p in all_memories if p.suffix.lower() in ('.png', '.jpg', '.jpeg')]
        if media_path in self._current_photo_list:
            self._current_photo_idx = self._current_photo_list.index(media_path)
        else:
            self._current_photo_list = [media_path]
            self._current_photo_idx = 0

        self.viewer_frame = tk.Frame(self, bg="#080b10")
        self.viewer_frame.place(x=0, y=0, relwidth=1, relheight=1)

        # Header Bar
        header = tk.Frame(self.viewer_frame, bg="#0d111a", padx=16, pady=8)
        header.pack(fill="x")

        btn_back = tk.Button(
            header,
            text="⬅ BACK TO ALBUM",
            font=("Segoe UI", 9, "bold"),
            bg="#21262d",
            fg="#70e1ff",
            activebackground="#30363d",
            activeforeground="#ffffff",
            bd=0,
            padx=12,
            pady=4,
            cursor="hand2",
            command=self.close_viewer
        )
        btn_back.pack(side="left")

        self.photo_title_lbl = tk.Label(
            header,
            text="",
            font=("Segoe UI", 9, "bold"),
            fg="#f0f6fc",
            bg="#0d111a"
        )
        self.photo_title_lbl.pack(side="left", padx=16)

        btn_box = tk.Frame(header, bg="#0d111a")
        btn_box.pack(side="right")

        self.btn_copy = tk.Button(
            btn_box,
            text="📋 Copy Image",
            font=("Segoe UI", 9),
            bg="#161b22",
            fg="#c9d1d9",
            activebackground="#21262d",
            activeforeground="#f0f6fc",
            bd=0,
            padx=10,
            pady=4,
            cursor="hand2",
            command=self._copy_current_photo
        )
        self.btn_copy.pack(side="left", padx=3)

        btn_folder = tk.Button(
            btn_box,
            text="📂 Open Folder",
            font=("Segoe UI", 9),
            bg="#161b22",
            fg="#c9d1d9",
            activebackground="#21262d",
            activeforeground="#f0f6fc",
            bd=0,
            padx=10,
            pady=4,
            cursor="hand2",
            command=self._open_recordings_folder
        )
        btn_folder.pack(side="left", padx=3)

        btn_close = tk.Label(
            btn_box,
            text="✕",
            font=("Segoe UI", 11, "bold"),
            fg="#8b949e",
            bg="#0d111a",
            cursor="hand2",
            padx=8,
            pady=4
        )
        btn_close.pack(side="left", padx=(4, 0))
        btn_close.bind("<Button-1>", lambda e: self.close_viewer())
        btn_close.bind("<Enter>", lambda e: btn_close.config(fg="#ff5c5c", bg="#21262d"))
        btn_close.bind("<Leave>", lambda e: btn_close.config(fg="#8b949e", bg="#0d111a"))

        # Main Viewport
        viewport = tk.Frame(self.viewer_frame, bg="#05070a")
        viewport.pack(fill="both", expand=True)

        btn_prev = tk.Label(
            viewport,
            text="❮",
            font=("Segoe UI", 24, "bold"),
            fg="#6e7681",
            bg="#05070a",
            cursor="hand2",
            padx=14
        )
        btn_prev.pack(side="left", fill="y")
        btn_prev.bind("<Button-1>", lambda e: self._navigate_photo(-1))
        btn_prev.bind("<Enter>", lambda e: btn_prev.config(fg="#70e1ff", bg="#101520"))
        btn_prev.bind("<Leave>", lambda e: btn_prev.config(fg="#6e7681", bg="#05070a"))

        btn_next = tk.Label(
            viewport,
            text="❯",
            font=("Segoe UI", 24, "bold"),
            fg="#6e7681",
            bg="#05070a",
            cursor="hand2",
            padx=14
        )
        btn_next.pack(side="right", fill="y")
        btn_next.bind("<Button-1>", lambda e: self._navigate_photo(1))
        btn_next.bind("<Enter>", lambda e: btn_next.config(fg="#70e1ff", bg="#101520"))
        btn_next.bind("<Leave>", lambda e: btn_next.config(fg="#6e7681", bg="#05070a"))

        self.photo_display_lbl = tk.Label(viewport, bg="#05070a")
        self.photo_display_lbl.pack(fill="both", expand=True, padx=6, pady=6)

        # Bind keyboard shortcuts
        self._bind_viewer_keys()
        self._render_current_photo()

    def _render_current_photo(self):
        if not self._current_photo_list or not self.photo_display_lbl:
            return
        photo_path = self._current_photo_list[self._current_photo_idx]
        total = len(self._current_photo_list)
        idx_str = f"({self._current_photo_idx + 1}/{total})"

        try:
            with Image.open(str(photo_path)) as raw_img:
                avail_w = max(400, self.winfo_width() - 140) if self.winfo_width() > 100 else 840
                avail_h = max(280, self.winfo_height() - 90) if self.winfo_height() > 100 else 520

                ratio = min(avail_w / raw_img.width, avail_h / raw_img.height, 1.0)
                target_w = max(10, int(raw_img.width * ratio))
                target_h = max(10, int(raw_img.height * ratio))

                disp_img = raw_img.resize((target_w, target_h), Image.Resampling.LANCZOS)
                self._current_photo_tk = ImageTk.PhotoImage(disp_img)
                self.photo_display_lbl.config(image=self._current_photo_tk)

                self.photo_title_lbl.config(
                    text=f"📸 {photo_path.stem}  {idx_str}  [{raw_img.width}x{raw_img.height}]"
                )
        except Exception as err:
            self.photo_title_lbl.config(text=f"Error loading {photo_path.name}: {err}")

    def _navigate_photo(self, delta: int):
        if not self._current_photo_list:
            return
        self._current_photo_idx = (self._current_photo_idx + delta) % len(self._current_photo_list)
        self._render_current_photo()

    def _copy_current_photo(self):
        if not self._current_photo_list:
            return
        photo_path = self._current_photo_list[self._current_photo_idx]
        try:
            import io
            import win32clipboard
            with Image.open(str(photo_path)) as img:
                output = io.BytesIO()
                img.convert("RGB").save(output, "BMP")
                data = output.getvalue()[14:]  # Strip BMP header for CF_DIB
                output.close()
                win32clipboard.OpenClipboard()
                win32clipboard.EmptyClipboard()
                win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
                win32clipboard.CloseClipboard()
            if self.btn_copy and self.btn_copy.winfo_exists():
                self.btn_copy.config(text="✓ Copied to Clipboard!", fg="#3fb950")
                self.after(2000, lambda: self.btn_copy.config(text="📋 Copy Image", fg="#c9d1d9") if self.btn_copy and self.btn_copy.winfo_exists() else None)
        except Exception as err:
            print(f"[Album] Clipboard copy error: {err}")

    # -------------------------------------------------------------------------
    # In-Overlay Video Player
    # -------------------------------------------------------------------------
    def _show_video_player(self, video_path: Path):
        """Plays recorded gameplay MP4 clip directly inside the in-game overlay."""
        self.close_viewer()
        self.is_viewer_active = True

        self._video_cap = cv2.VideoCapture(str(video_path))
        if not self._video_cap.isOpened():
            print(f"[Album] Cannot open video: {video_path}")
            return

        self._video_total_frames = int(self._video_cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 1
        self._video_fps = self._video_cap.get(cv2.CAP_PROP_FPS) or 30.0
        self._video_is_playing = True
        self._video_seeking = False

        self.viewer_frame = tk.Frame(self, bg="#080b10")
        self.viewer_frame.place(x=0, y=0, relwidth=1, relheight=1)

        # Header Bar
        header = tk.Frame(self.viewer_frame, bg="#0d111a", padx=16, pady=8)
        header.pack(fill="x")

        btn_back = tk.Button(
            header,
            text="⬅ BACK TO ALBUM",
            font=("Segoe UI", 9, "bold"),
            bg="#21262d",
            fg="#ff005b",
            activebackground="#30363d",
            activeforeground="#ffffff",
            bd=0,
            padx=12,
            pady=4,
            cursor="hand2",
            command=self.close_viewer
        )
        btn_back.pack(side="left")

        w_v = int(self._video_cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 1920
        h_v = int(self._video_cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 1080
        total_sec = int(self._video_total_frames / self._video_fps)
        total_str = f"{total_sec // 60:02d}:{total_sec % 60:02d}"

        tk.Label(
            header,
            text=f"🎬 {video_path.stem}  [{w_v}x{h_v} • {int(self._video_fps)} FPS • {total_str}]",
            font=("Segoe UI", 9, "bold"),
            fg="#f0f6fc",
            bg="#0d111a"
        ).pack(side="left", padx=16)

        btn_box = tk.Frame(header, bg="#0d111a")
        btn_box.pack(side="right")

        btn_folder = tk.Button(
            btn_box,
            text="📂 Open Folder",
            font=("Segoe UI", 9),
            bg="#161b22",
            fg="#c9d1d9",
            activebackground="#21262d",
            activeforeground="#f0f6fc",
            bd=0,
            padx=10,
            pady=4,
            cursor="hand2",
            command=self._open_recordings_folder
        )
        btn_folder.pack(side="left", padx=3)

        btn_close = tk.Label(
            btn_box,
            text="✕",
            font=("Segoe UI", 11, "bold"),
            fg="#8b949e",
            bg="#0d111a",
            cursor="hand2",
            padx=8,
            pady=4
        )
        btn_close.pack(side="left", padx=(4, 0))
        btn_close.bind("<Button-1>", lambda e: self.close_viewer())
        btn_close.bind("<Enter>", lambda e: btn_close.config(fg="#ff5c5c", bg="#21262d"))
        btn_close.bind("<Leave>", lambda e: btn_close.config(fg="#8b949e", bg="#0d111a"))

        # Video Display Canvas
        self.video_display_lbl = tk.Label(self.viewer_frame, bg="#000000")
        self.video_display_lbl.pack(fill="both", expand=True, padx=8, pady=(4, 0))
        self.video_display_lbl.bind("<Button-1>", lambda e: self._toggle_video_play())

        # Controls Bar at Bottom
        ctrl_bar = tk.Frame(self.viewer_frame, bg="#0d111a", padx=16, pady=8)
        ctrl_bar.pack(fill="x", side="bottom")

        self.btn_play_pause = tk.Button(
            ctrl_bar,
            text="⏸ PAUSE",
            font=("Segoe UI", 9, "bold"),
            bg="#ff005b",
            fg="#ffffff",
            activebackground="#ff3377",
            activeforeground="#ffffff",
            bd=0,
            padx=14,
            pady=4,
            cursor="hand2",
            command=self._toggle_video_play
        )
        self.btn_play_pause.pack(side="left")

        btn_replay = tk.Button(
            ctrl_bar,
            text="↺ REPLAY",
            font=("Segoe UI", 9),
            bg="#21262d",
            fg="#f0f6fc",
            activebackground="#30363d",
            activeforeground="#70e1ff",
            bd=0,
            padx=10,
            pady=4,
            cursor="hand2",
            command=self._replay_video
        )
        btn_replay.pack(side="left", padx=8)

        self.video_time_lbl = tk.Label(
            ctrl_bar,
            text=f"00:00 / {total_str}",
            font=("Consolas", 9, "bold"),
            fg="#70e1ff",
            bg="#0d111a"
        )
        self.video_time_lbl.pack(side="left", padx=8)

        # Scrubber Scale Slider
        self.video_scrubber = tk.Scale(
            ctrl_bar,
            from_=0,
            to=max(1, self._video_total_frames - 1),
            orient="horizontal",
            showvalue=False,
            bg="#0d111a",
            fg="#70e1ff",
            troughcolor="#1e2633",
            activebackground="#ff005b",
            highlightthickness=0,
            bd=0,
            cursor="hand2",
            command=self._on_scrub
        )
        self.video_scrubber.pack(side="left", fill="x", expand=True, padx=12)
        self.video_scrubber.bind("<Button-1>", lambda e: self._on_scrub_start())
        self.video_scrubber.bind("<ButtonRelease-1>", lambda e: self._on_scrub_end())

        self._bind_viewer_keys()
        self._next_video_frame()

    def _next_video_frame(self):
        if not self.is_viewer_active or not self._video_cap or not self._video_cap.isOpened():
            return

        if self._video_is_playing and not self._video_seeking:
            ret, frame = self._video_cap.read()
            if ret and frame is not None:
                cur_frame = int(self._video_cap.get(cv2.CAP_PROP_POS_FRAMES))

                self._updating_scrubber = True
                if self.video_scrubber and self.video_scrubber.winfo_exists():
                    self.video_scrubber.set(cur_frame)
                self._updating_scrubber = False

                cur_sec = int(cur_frame / self._video_fps)
                tot_sec = int(self._video_total_frames / self._video_fps)
                if self.video_time_lbl and self.video_time_lbl.winfo_exists():
                    self.video_time_lbl.config(
                        text=f"{cur_sec // 60:02d}:{cur_sec % 60:02d} / {tot_sec // 60:02d}:{tot_sec % 60:02d}"
                    )

                avail_w = max(400, self.winfo_width() - 32) if self.winfo_width() > 100 else 880
                avail_h = max(240, self.winfo_height() - 110) if self.winfo_height() > 100 else 460

                f_h, f_w = frame.shape[:2]
                scale = min(avail_w / f_w, avail_h / f_h, 1.0)
                new_w = max(10, int(f_w * scale))
                new_h = max(10, int(f_h * scale))

                resized = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
                rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
                self._current_video_tk = ImageTk.PhotoImage(Image.fromarray(rgb))
                if self.video_display_lbl and self.video_display_lbl.winfo_exists():
                    self.video_display_lbl.config(image=self._current_video_tk)
            else:
                self._video_is_playing = False
                if self.btn_play_pause and self.btn_play_pause.winfo_exists():
                    self.btn_play_pause.config(text="▶ PLAY", bg="#238636")

        delay_ms = max(15, int(1000.0 / self._video_fps))
        self._video_timer_id = self.after(delay_ms, self._next_video_frame)

    def _toggle_video_play(self):
        if not self._video_cap:
            return
        if self._video_is_playing:
            self._video_is_playing = False
            if self.btn_play_pause and self.btn_play_pause.winfo_exists():
                self.btn_play_pause.config(text="▶ PLAY", bg="#238636")
        else:
            cur = int(self._video_cap.get(cv2.CAP_PROP_POS_FRAMES))
            if cur >= self._video_total_frames - 1:
                self._video_cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            self._video_is_playing = True
            if self.btn_play_pause and self.btn_play_pause.winfo_exists():
                self.btn_play_pause.config(text="⏸ PAUSE", bg="#ff005b")

    def _replay_video(self):
        if self._video_cap:
            self._video_cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            self._video_is_playing = True
            if self.btn_play_pause and self.btn_play_pause.winfo_exists():
                self.btn_play_pause.config(text="⏸ PAUSE", bg="#ff005b")

    def _on_scrub(self, val):
        if getattr(self, "_updating_scrubber", False):
            return
        if self._video_cap:
            target = int(float(val))
            self._video_cap.set(cv2.CAP_PROP_POS_FRAMES, target)
            ret, frame = self._video_cap.read()
            if ret and frame is not None:
                avail_w = max(400, self.winfo_width() - 32) if self.winfo_width() > 100 else 880
                avail_h = max(240, self.winfo_height() - 110) if self.winfo_height() > 100 else 460
                f_h, f_w = frame.shape[:2]
                scale = min(avail_w / f_w, avail_h / f_h, 1.0)
                new_w = max(10, int(f_w * scale))
                new_h = max(10, int(f_h * scale))
                resized = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
                rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
                self._current_video_tk = ImageTk.PhotoImage(Image.fromarray(rgb))
                if self.video_display_lbl and self.video_display_lbl.winfo_exists():
                    self.video_display_lbl.config(image=self._current_video_tk)
                cur_sec = int(target / self._video_fps)
                tot_sec = int(self._video_total_frames / self._video_fps)
                if self.video_time_lbl and self.video_time_lbl.winfo_exists():
                    self.video_time_lbl.config(
                        text=f"{cur_sec // 60:02d}:{cur_sec % 60:02d} / {tot_sec // 60:02d}:{tot_sec % 60:02d}"
                    )

    def _on_scrub_start(self):
        self._video_seeking = True

    def _on_scrub_end(self):
        self._video_seeking = False

    def _bind_viewer_keys(self):
        try:
            top = self.winfo_toplevel()
            top.bind("<Left>", self._on_key_left)
            top.bind("<Right>", self._on_key_right)
            top.bind("<space>", self._on_key_space)
        except Exception:
            pass

    def _on_key_left(self, event=None):
        if not self.is_viewer_active:
            return
        if self._video_cap:
            cur_frame = int(self._video_cap.get(cv2.CAP_PROP_POS_FRAMES))
            step = int(self._video_fps * 3)
            self._on_scrub(max(0, cur_frame - step))
        elif self._current_photo_list:
            self._navigate_photo(-1)

    def _on_key_right(self, event=None):
        if not self.is_viewer_active:
            return
        if self._video_cap:
            cur_frame = int(self._video_cap.get(cv2.CAP_PROP_POS_FRAMES))
            step = int(self._video_fps * 3)
            self._on_scrub(min(self._video_total_frames - 1, cur_frame + step))
        elif self._current_photo_list:
            self._navigate_photo(1)

    def _on_key_space(self, event=None):
        if self.is_viewer_active and self._video_cap:
            self._toggle_video_play()

    def close_viewer(self):
        """Closes any active in-overlay photo viewer or video player and returns to gallery."""
        self.is_viewer_active = False
        if self._video_timer_id:
            try:
                self.after_cancel(self._video_timer_id)
            except Exception:
                pass
            self._video_timer_id = None

        if self._video_cap:
            try:
                self._video_cap.release()
            except Exception:
                pass
            self._video_cap = None

        self._current_photo_list = []
        self._current_photo_tk = None
        self._current_video_tk = None

        if self.viewer_frame and self.viewer_frame.winfo_exists():
            try:
                self.viewer_frame.destroy()
            except Exception:
                pass
            self.viewer_frame = None

    def _extract_video_thumbnail(self, video_path: Path, target_w: int = 400) -> Optional[Image.Image]:
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

            draw = ImageDraw.Draw(pil_img, "RGBA")
            cx, cy = target_w // 2, target_h // 2
            r = 24
            draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(0, 0, 0, 160), outline=(255, 255, 255, 220), width=2)
            draw.polygon([(cx - 7, cy - 12), (cx - 7, cy + 12), (cx + 13, cy)], fill=(255, 255, 255, 240))

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

    def refresh(self):
        """Refreshes and renders visual memories cards."""
        if not self.scroll_frame or not self.scroll_frame.winfo_exists():
            return

        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
        self._thumbnails.clear()

        self.canvas.yview_moveto(0.0)
        self._target_scroll_y = 0.0

        all_memories = self.polaroid_svc.get_recent_memories(limit=100)
        photos = [p for p in all_memories if p.suffix.lower() in ('.png', '.jpg', '.jpeg')]
        videos = [p for p in all_memories if p.suffix.lower() in ('.mp4', '.mkv', '.avi', '.mov')]

        if self.btn_filter_all and self.btn_filter_all.winfo_exists():
            self.btn_filter_all.config(text=f"⚡ ALL ({len(all_memories)})")
        if self.btn_filter_photos and self.btn_filter_photos.winfo_exists():
            self.btn_filter_photos.config(text=f"📸 PHOTOS ({len(photos)})")
        if self.btn_filter_videos and self.btn_filter_videos.winfo_exists():
            self.btn_filter_videos.config(text=f"🎬 VIDEOS ({len(videos)})")

        self._update_filter_tabs_ui()

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

        columns = 2
        card_w = 440
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
                    pil_img = self._extract_video_thumbnail(media_path, target_w=card_w)
                    if not pil_img:
                        pil_img = Image.new("RGB", (card_w, 220), color="#161b24")
                        draw = ImageDraw.Draw(pil_img)
                        draw.text((160, 100), "🎬 [Video Clip]", fill="white", font=ImageFont.load_default())
                else:
                    with Image.open(str(media_path)) as raw_img:
                        target_w = card_w
                        target_h = int(raw_img.height * (target_w / raw_img.width))
                        pil_img = raw_img.resize((target_w, target_h), Image.Resampling.LANCZOS)

                tk_thumb = ImageTk.PhotoImage(pil_img)
                self._thumbnails.append(tk_thumb)

                img_lbl = tk.Label(card_box, image=tk_thumb, bg="#0f141f", cursor="hand2")
                img_lbl.pack()
                img_lbl.bind("<Button-1>", lambda e, p=media_path: self._open_media(p))

                footer_bar = tk.Frame(card_box, bg="#0f141f", pady=5)
                footer_bar.pack(fill="x")

                display_name = media_path.stem
                if len(display_name) > 32:
                    display_name = display_name[:29] + "..."

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

        self.after(50, lambda: self.scrollbar.update_thumb() if self.scrollbar else None)


class AlbumViewerWindow:
    """
    Backwards-compatible standalone window wrapper for the VisualMemoriesTab.
    Can either delegate directly to GameBar's integrated tab or open standalone.
    """
    def __init__(self,
                 master: tk.Tk,
                 polaroid_svc: PolaroidService,
                 on_capture_request: Optional[Callable] = None,
                 on_record_request: Optional[Callable] = None,
                 on_pause_request: Optional[Callable] = None,
                 video_recorder: Optional[object] = None,
                 delegate_open: Optional[Callable] = None):
        self.master = master
        self.polaroid_svc = polaroid_svc
        self.on_capture_request = on_capture_request
        self.on_record_request = on_record_request
        self.on_pause_request = on_pause_request
        self.video_recorder = video_recorder
        self.delegate_open = delegate_open
        self.window: Optional[tk.Toplevel] = None
        self.tab: Optional[VisualMemoriesTab] = None

    def open(self):
        """Opens Visual Memories. If a delegate (GameBar) is registered, opens as navbar tab."""
        if self.delegate_open:
            self.delegate_open()
            return

        if self.window and self.window.winfo_exists():
            self.window.attributes("-topmost", True)
            self.window.deiconify()
            self.window.lift()
            if self.tab:
                self.tab.refresh()
            return

        self.window = tk.Toplevel(self.master)
        self.window.title("Xsolla Visual Memories")
        self.window.configure(bg="#080b10")
        self.window.overrideredirect(True)
        self.window.attributes("-topmost", True)

        width, height = 980, 660
        sw = self.window.winfo_screenwidth()
        x = (sw - width) // 2
        y = 20
        self.window.geometry(f"{width}x{height}+{x}+{y}")

        border = tk.Frame(self.window, bg="#1e2633", padx=1, pady=1)
        border.pack(fill="both", expand=True)

        self.tab = VisualMemoriesTab(
            border,
            self.polaroid_svc,
            on_capture_request=self.on_capture_request,
            on_record_request=self.on_record_request,
            on_pause_request=self.on_pause_request,
            on_close_tab=self.close,
            video_recorder=self.video_recorder
        )
        self.tab.pack(fill="both", expand=True)
        self.tab.refresh()
        make_window_invisible_to_capture(self.window)

    def close(self):
        if self.window and self.window.winfo_exists():
            self.window.withdraw()

    def _refresh_content(self):
        if self.tab:
            self.tab.refresh()
