"""
Xsolla Game Recap - High-Performance In-Game Video Recorder
Captures live desktop/gameplay into smooth MP4 videos using OpenCV and Pillow.
Provides real-time recording timer, audio feedback, and local persistence
in Documents/XSOLLA_gamerecap/recordings/.
"""

import time
import re
import datetime
import winsound
import threading
from pathlib import Path
from typing import Optional, Dict, Callable
import cv2
import numpy as np
from PIL import ImageGrab

from config import SCREENSHOTS_DIR, ensure_data_dir


class VideoRecorderService:
    def __init__(self, on_state_change: Optional[Callable[[bool, str], None]] = None):
        ensure_data_dir()
        self.on_state_change = on_state_change

        self.is_recording = False
        self.start_time = 0.0
        self.current_filepath: Optional[Path] = None
        self.current_filename: str = ""
        self.current_game: str = "Game"
        self.frame_count = 0

        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def toggle(self, game_name: str = "Active Game") -> bool:
        """Toggles video recording between start and stop."""
        if self.is_recording:
            self.stop_recording()
            return False
        else:
            return self.start_recording(game_name)

    def start_recording(self, game_name: str = "Active Game") -> bool:
        """Starts background video capture at steady FPS."""
        if self.is_recording:
            return False

        ensure_data_dir()
        self.current_game = game_name
        timestamp = int(time.time())

        clean_name = re.sub(r'[^a-zA-Z0-9_\-]', '', game_name.replace(" ", "_")).lower()
        if not clean_name:
            clean_name = "game"

        self.current_filename = f"clip_{clean_name}_{timestamp}.mp4"
        # Saves directly to captures folder alongside screenshots
        self.current_filepath = SCREENSHOTS_DIR / self.current_filename

        self.is_recording = True
        self.start_time = time.time()
        self.frame_count = 0
        self._stop_event.clear()

        # Audio start chime
        threading.Thread(target=self._play_start_sound, daemon=True).start()

        # Launch recording thread
        self._thread = threading.Thread(target=self._record_loop, daemon=True)
        self._thread.start()

        print(f"[VideoRecorder] Recording started -> {self.current_filename}")
        if self.on_state_change:
            self.on_state_change(True, "00:00")
        return True

    def stop_recording(self) -> Optional[Dict]:
        """Stops video recording and finalizes the MP4 file."""
        if not self.is_recording:
            return None

        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=3.0)
            self._thread = None

        self.is_recording = False
        elapsed = time.time() - self.start_time
        duration_str = self._format_duration(elapsed)

        # Audio stop chime
        threading.Thread(target=self._play_stop_sound, daemon=True).start()

        result = {
            "filename": self.current_filename,
            "path": str(self.current_filepath),
            "duration_sec": int(elapsed),
            "duration_str": duration_str,
            "frames": self.frame_count,
            "game_name": self.current_game
        }

        print(f"[VideoRecorder] Recording saved: {self.current_filename} ({duration_str}, {self.frame_count} frames)")
        if self.on_state_change:
            self.on_state_change(False, duration_str)

        return result

    def get_duration_str(self) -> str:
        """Returns elapsed recording duration (MM:SS)."""
        if not self.is_recording:
            return "00:00"
        return self._format_duration(time.time() - self.start_time)

    def _record_loop(self):
        """Grabs frames and writes to MP4Video file."""
        # Grab first frame to determine screen resolution
        try:
            first_img = ImageGrab.grab()
            w, h = first_img.size
        except Exception as err:
            print(f"[VideoRecorder] Initial frame grab failed: {err}")
            self.is_recording = False
            return

        target_fps = 20.0
        frame_interval = 1.0 / target_fps
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        writer = cv2.VideoWriter(str(self.current_filepath), fourcc, target_fps, (w, h))

        if not writer.isOpened():
            print(f"[VideoRecorder] Error opening VideoWriter for {self.current_filepath}")
            self.is_recording = False
            return

        next_time = time.time()
        while not self._stop_event.is_set():
            now = time.time()
            if now >= next_time:
                try:
                    img = ImageGrab.grab()
                    frame = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
                    writer.write(frame)
                    self.frame_count += 1
                except Exception as err:
                    print(f"[VideoRecorder] Frame write error: {err}")

                next_time += frame_interval
            else:
                sleep_time = next_time - now
                if sleep_time > 0.002:
                    time.sleep(min(sleep_time, 0.02))

        writer.release()

    def _format_duration(self, seconds: float) -> str:
        mins = int(seconds) // 60
        secs = int(seconds) % 60
        return f"{mins:02d}:{secs:02d}"

    def _play_start_sound(self):
        try:
            winsound.Beep(1200, 70)
            time.sleep(0.04)
            winsound.Beep(1600, 100)
        except Exception:
            pass

    def _play_stop_sound(self):
        try:
            winsound.Beep(1600, 70)
            time.sleep(0.04)
            winsound.Beep(1200, 100)
        except Exception:
            pass
