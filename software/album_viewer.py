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

        # Bring Explorer on top of everything without lowering the navbar
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
                        if "recording" in txt or "xsolla" in txt:
                            target_hwnds.append(hwnd)
                    return True

                cb = WNDENUMPROC(enum_cb)
                user32.EnumWindows(cb, 0)

                fore_hwnd = user32.GetForegroundWindow()
                fore_tid = user32.GetWindowThreadProcessId(fore_hwnd, None)
                app_tid = ctypes.windll.kernel32.GetCurrentThreadId()

                for hwnd in target_hwnds:
                    if user32.IsIconic(hwnd):
                        user32.ShowWindow(hwnd, 9)  # SW_RESTORE
                    else:
                        user32.ShowWindow(hwnd, 5)  # SW_SHOW

                    if fore_tid and fore_tid != app_tid:
                        user32.AttachThreadInput(app_tid, fore_tid, True)
                        user32.BringWindowToTop(hwnd)
                        user32.SetForegroundWindow(hwnd)
                        user32.AttachThreadInput(app_tid, fore_tid, False)
                    else:
                        user32.BringWindowToTop(hwnd)
                        user32.SetForegroundWindow(hwnd)

                    # Elevate Explorer window to topmost
                    user32.SetWindowPos(hwnd, -1, 0, 0, 0, 0, 0x0001 | 0x0002 | 0x0040)
            except Exception as e:
                print(f"[Album] Exception elevating Explorer: {e}")

        for delay in (150, 350, 700, 1200):
            self.after(delay, _bring_explorer_on_top)

    def _open_media(self, media_path: Path):
        """Opens a media file without closing or hiding the navbar."""
        if self.on_media_opened:
            try:
                self.on_media_opened()
            except Exception:
                pass
        try:
            os.startfile(str(media_path))
        except Exception:
            try:
                subprocess.Popen(["explorer.exe", str(media_path)])
            except Exception:
                pass

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
