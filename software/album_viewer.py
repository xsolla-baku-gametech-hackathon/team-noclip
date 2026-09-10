"""
Xsolla Game Recap - Captures & Recordings Gallery
A sleek, dark gallery window displaying captured high-quality screenshots and
video recordings, with 1-click preview, native playback, and folder access.
All captures are saved directly in Documents/XSOLLA_gamerecap/captures/.
"""

import os
import subprocess
import tkinter as tk
from pathlib import Path
from typing import Optional, Callable
import cv2
from PIL import Image, ImageTk, ImageDraw, ImageFont

from config import SCREENSHOTS_DIR, make_window_invisible_to_capture
from polaroid_service import PolaroidService


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
        self.btn_folder = None
        self.btn_refresh = None
        self.btn_snap = None
        self.btn_pause_top = None
        self.btn_record_top = None

    def open(self):
        """Displays the Visual Memories Album."""
        if self.window and self.window.winfo_exists():
            self.window.deiconify()
            self.window.lift()
            self.window.focus_force()
            self._refresh_content()
            return

        self.window = tk.Toplevel(self.master)
        self.window.title("Xsolla Captures & Recordings Gallery")
        self.window.configure(bg="#0b0e14")
        self.window.attributes("-topmost", True)

        width = 860
        height = 640
        sw = self.window.winfo_screenwidth()
        sh = self.window.winfo_screenheight()
        x = (sw - width) // 2
        y = (sh - height) // 2
        self.window.geometry(f"{width}x{height}+{x}+{y}")
        self.window.minsize(700, 500)

        # Bind F5 to refresh
        self.window.bind("<F5>", lambda e: self._refresh_content())

        self._build_ui()
        self._refresh_content()
        make_window_invisible_to_capture(self.window)

    def _build_ui(self):
        # 1. Header Bar
        header = tk.Frame(self.window, bg="#10151f", padx=20, pady=12)
        header.pack(fill="x")

        title_box = tk.Frame(header, bg="#10151f")
        title_box.pack(side="left")

        tk.Label(
            title_box,
            text="📸 CAPTURES & RECORDINGS GALLERY",
            font=("Segoe UI", 13, "bold"),
            fg="#70e1ff",
            bg="#10151f"
        ).pack(anchor="w")

        self.subtitle_lbl = tk.Label(
            title_box,
            text="All screenshots and video clips saved in Documents/XSOLLA_gamerecap/captures/",
            font=("Segoe UI", 9),
            fg="#8b949e",
            bg="#10151f"
        )
        self.subtitle_lbl.pack(anchor="w", pady=(2, 0))

        # Actions on the right
        btn_box = tk.Frame(header, bg="#10151f")
        btn_box.pack(side="right")

        # Open Folder button
        self.btn_folder = tk.Button(
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
        self.btn_folder.pack(side="left", padx=4)

        # Refresh button
        self.btn_refresh = tk.Button(
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
        self.btn_refresh.pack(side="left", padx=4)

        # Snap button
        if self.on_capture_request:
            self.btn_snap = tk.Button(
                btn_box,
                text="📸 Snap (F11)",
                font=("Segoe UI", 9, "bold"),
                bg="#238636",
                fg="#ffffff",
                activebackground="#2ea043",
                activeforeground="#ffffff",
                bd=0,
                padx=10,
                pady=5,
                cursor="hand2",
                command=self._handle_manual_capture
            )
            self.btn_snap.pack(side="left", padx=4)
        else:
            self.btn_snap = None

        # Video Pause button (only active during recording)
        self.btn_pause_top = tk.Button(
            btn_box,
            text="⏸️ Pause",
            font=("Segoe UI", 9, "bold"),
            bg="#21262d",
            fg="#f0f6fc",
            activebackground="#30363d",
            activeforeground="#ffffff",
            bd=0,
            padx=10,
            pady=5,
            cursor="hand2",
            command=self._handle_manual_pause
        )

        # Video Record / Stop button
        if self.on_record_request:
            self.btn_record_top = tk.Button(
                btn_box,
                text="🔴 Record (F9)",
                font=("Segoe UI", 9, "bold"),
                bg="#ff005b",
                fg="#ffffff",
                activebackground="#d1004b",
                activeforeground="#ffffff",
                bd=0,
                padx=10,
                pady=5,
                cursor="hand2",
                command=self._handle_manual_record
            )
            self.btn_record_top.pack(side="left", padx=4)
        else:
            self.btn_record_top = None

        # 2. Scrollable Gallery Body
        container = tk.Frame(self.window, bg="#0b0e14")
        container.pack(fill="both", expand=True, padx=16, pady=12)

        self.canvas = tk.Canvas(container, bg="#0b0e14", highlightthickness=0)
        self.scrollbar = tk.Scrollbar(container, orient="vertical", command=self.canvas.yview)
        self.scroll_frame = tk.Frame(self.canvas, bg="#0b0e14")

        self.scroll_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # Mouse wheel scroll binding
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _on_mousewheel(self, event):
        if self.window and self.window.winfo_exists() and self.canvas.winfo_exists():
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _handle_manual_capture(self):
        if self.on_capture_request:
            self.on_capture_request()
            self.window.after(600, self._refresh_content)

    def _handle_manual_record(self):
        if self.on_record_request:
            self.on_record_request()
            self.window.after(400, self._refresh_content)

    def _handle_manual_pause(self):
        if self.on_pause_request:
            self.on_pause_request()
            self.window.after(100, self._refresh_content)

    def _open_captures_folder(self):
        try:
            os.startfile(str(SCREENSHOTS_DIR))
        except Exception:
            subprocess.Popen(["explorer", str(SCREENSHOTS_DIR)])

    def _extract_video_thumbnail(self, video_path: Path, target_w: int = 350) -> Optional[Image.Image]:
        """Extracts a high-quality video thumbnail with an overlaid duration badge and play icon."""
        try:
            cap = cv2.VideoCapture(str(video_path))
            if not cap.isOpened():
                return None

            fps = cap.get(cv2.CAP_PROP_FPS) or 20.0
            count = cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0
            # Read frame slightly after start to avoid black fade-in if any
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
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
        self._thumbnails.clear()

        # Update top recording bar controls dynamically
        is_rec = bool(self.video_recorder and getattr(self.video_recorder, "is_recording", False))
        is_paused = bool(self.video_recorder and getattr(self.video_recorder, "is_paused", False))
        dur_str = self.video_recorder.get_duration_str() if self.video_recorder else "00:00"

        if is_rec:
            # Hide Open Folder and Snap buttons during recording
            if self.btn_folder and self.btn_folder.winfo_ismapped():
                self.btn_folder.pack_forget()
            if self.btn_snap and self.btn_snap.winfo_ismapped():
                self.btn_snap.pack_forget()

            # Show Pause button
            if self.btn_pause_top and not self.btn_pause_top.winfo_ismapped():
                self.btn_pause_top.pack(side="left", padx=4)
            if self.btn_pause_top:
                if is_paused:
                    self.btn_pause_top.config(text=f"▶️ Resume ({dur_str})", bg="#238636")
                else:
                    self.btn_pause_top.config(text=f"⏸️ Pause ({dur_str})", bg="#21262d")

            # Show Stop button
            if self.btn_record_top:
                self.btn_record_top.config(text="⏹ Stop REC", bg="#da3633")
                if not self.btn_record_top.winfo_ismapped():
                    self.btn_record_top.pack(side="left", padx=4)
        else:
            # Hide pause button
            if self.btn_pause_top and self.btn_pause_top.winfo_ismapped():
                self.btn_pause_top.pack_forget()

            # Restore Open Folder, Refresh, and Snap buttons
            if self.btn_folder and not self.btn_folder.winfo_ismapped():
                self.btn_folder.pack(side="left", padx=4)
            if self.btn_refresh and not self.btn_refresh.winfo_ismapped():
                self.btn_refresh.pack(side="left", padx=4)
            if self.btn_snap and not self.btn_snap.winfo_ismapped():
                self.btn_snap.pack(side="left", padx=4)
            if self.btn_record_top:
                self.btn_record_top.config(text="🔴 Record (F9)", bg="#ff005b")
                if not self.btn_record_top.winfo_ismapped():
                    self.btn_record_top.pack(side="left", padx=4)

        memories = self.polaroid_svc.get_recent_memories(limit=36)
        num_screens = sum(1 for p in memories if p.suffix.lower() in ('.png', '.jpg', '.jpeg'))
        num_vids = sum(1 for p in memories if p.suffix.lower() in ('.mp4', '.mkv', '.avi', '.mov'))

        self.subtitle_lbl.config(
            text=f"{len(memories)} Captures ({num_screens} Screenshots, {num_vids} Video Clips) • [F11] Snap • [F9] Record"
        )

        if not memories:
            empty_box = tk.Frame(self.scroll_frame, bg="#0b0e14", pady=60)
            empty_box.pack(fill="both", expand=True)

            tk.Label(
                empty_box,
                text="NO CAPTURES OR RECORDINGS YET",
                font=("Segoe UI", 12, "bold"),
                fg="#6e7681",
                bg="#0b0e14"
            ).pack()

            tk.Label(
                empty_box,
                text="Press [F11] to capture instant screenshot or [F9] to record gameplay clips in any game!\nAll files automatically save to Documents/XSOLLA_gamerecap/captures/.",
                font=("Segoe UI", 10),
                fg="#484f58",
                bg="#0b0e14",
                pady=10
            ).pack()
            return

        # Render Cards in a 2-column grid
        columns = 2
        for idx, media_path in enumerate(memories):
            row = idx // columns
            col = idx % columns
            is_video = media_path.suffix.lower() in ('.mp4', '.mkv', '.avi', '.mov')

            card_border = "#ff005b" if is_video else "#21262d"
            card_box = tk.Frame(self.scroll_frame, bg="#131822", padx=8, pady=8, highlightthickness=1, highlightbackground=card_border)
            card_box.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")

            try:
                if is_video:
                    pil_img = self._extract_video_thumbnail(media_path, target_w=350)
                    if not pil_img:
                        pil_img = Image.new("RGB", (350, 196), color="#1a202c")
                        draw = ImageDraw.Draw(pil_img)
                        draw.text((120, 90), "🎬 [Video Clip]", fill="white", font=ImageFont.load_default())
                else:
                    pil_img = Image.open(str(media_path))
                    target_w = 350
                    target_h = int(pil_img.height * (target_w / pil_img.width))
                    pil_img = pil_img.resize((target_w, target_h), Image.Resampling.LANCZOS)

                tk_thumb = ImageTk.PhotoImage(pil_img)
                self._thumbnails.append(tk_thumb)

                img_lbl = tk.Label(card_box, image=tk_thumb, bg="#131822", cursor="hand2")
                img_lbl.pack()
                # Clicking opens file directly in Windows default player / photo viewer
                img_lbl.bind("<Button-1>", lambda e, p=media_path: os.startfile(str(p)))

                # Card footer bar
                footer_bar = tk.Frame(card_box, bg="#131822", pady=5)
                footer_bar.pack(fill="x")

                # Short clean title
                display_name = media_path.stem
                if len(display_name) > 30:
                    display_name = display_name[:27] + "..."

                lbl_name = tk.Label(
                    footer_bar,
                    text=display_name,
                    font=("Consolas", 8),
                    fg="#8b949e",
                    bg="#131822"
                )
                lbl_name.pack(side="left")

                # Action button on right
                if is_video:
                    btn_act = tk.Label(
                        footer_bar,
                        text="▶ Play Video",
                        font=("Segoe UI", 8, "bold"),
                        fg="#ff5c5c",
                        bg="#131822",
                        cursor="hand2"
                    )
                else:
                    btn_act = tk.Label(
                        footer_bar,
                        text="View Photo ↗",
                        font=("Segoe UI", 8, "bold"),
                        fg="#70e1ff",
                        bg="#131822",
                        cursor="hand2"
                    )

                btn_act.pack(side="right")
                btn_act.bind("<Button-1>", lambda e, p=media_path: os.startfile(str(p)))

            except Exception as err:
                print(f"[Album] Error loading {media_path}: {err}")
