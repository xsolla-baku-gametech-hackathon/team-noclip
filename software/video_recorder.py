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
from config import RECORDINGS_DIR, ensure_data_dir, get_recording_settings
from capture_utils import grab_screen_with_cursor


class VideoRecorderService:
    def __init__(self, on_state_change: Optional[Callable[[bool, str], None]] = None):
        ensure_data_dir()
        self.on_state_change = on_state_change

        self.is_recording = False
        self.is_paused = False
        self.start_time = 0.0
        self.total_paused_time = 0.0
        self._pause_start = 0.0
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
        # Saves directly to recordings folder
        self.current_filepath = RECORDINGS_DIR / self.current_filename

        self.is_recording = True
        self.is_paused = False
        self.start_time = time.time()
        self.total_paused_time = 0.0
        self._pause_start = 0.0
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

    def pause_recording(self) -> bool:
        """Pauses the active recording."""
        if not self.is_recording or self.is_paused:
            return False
        self.is_paused = True
        self._pause_start = time.time()
        threading.Thread(target=self._play_pause_sound, daemon=True).start()
        print(f"[VideoRecorder] Recording paused at {self.get_duration_str()}")
        if self.on_state_change:
            self.on_state_change(True, self.get_duration_str())
        return True

    def resume_recording(self) -> bool:
        """Resumes a paused recording."""
        if not self.is_recording or not self.is_paused:
            return False
        if self._pause_start > 0:
            self.total_paused_time += (time.time() - self._pause_start)
        self.is_paused = False
        self._pause_start = 0.0
        threading.Thread(target=self._play_resume_sound, daemon=True).start()
        print(f"[VideoRecorder] Recording resumed at {self.get_duration_str()}")
        if self.on_state_change:
            self.on_state_change(True, self.get_duration_str())
        return True

    def toggle_pause(self) -> bool:
        """Toggles pause/resume state."""
        if not self.is_recording:
            return False
        if self.is_paused:
            self.resume_recording()
            return False
        else:
            self.pause_recording()
            return True

    def stop_recording(self) -> Optional[Dict]:
        """Stops video recording and finalizes the MP4 file."""
        if not self.is_recording:
            return None

        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=3.0)
            self._thread = None

        if self.is_paused and self._pause_start > 0:
            elapsed = self._pause_start - self.start_time - self.total_paused_time
        else:
            elapsed = time.time() - self.start_time - self.total_paused_time
        duration_str = self._format_duration(max(0.0, elapsed))

        self.is_recording = False
        self.is_paused = False
        self.total_paused_time = 0.0
        self._pause_start = 0.0

        # Audio stop chime
        threading.Thread(target=self._play_stop_sound, daemon=True).start()

        result = {
            "filename": self.current_filename,
            "path": str(self.current_filepath),
            "duration_sec": int(max(0.0, elapsed)),
            "duration_str": duration_str,
            "frames": self.frame_count,
            "game_name": self.current_game
        }

        print(f"[VideoRecorder] Recording saved: {self.current_filename} ({duration_str}, {self.frame_count} frames)")
        if self.on_state_change:
            self.on_state_change(False, duration_str)

        return result

    def get_duration_str(self) -> str:
        """Returns elapsed active recording duration (MM:SS)."""
        if not self.is_recording:
            return "00:00"
        if self.is_paused and self._pause_start > 0:
            elapsed = self._pause_start - self.start_time - self.total_paused_time
        else:
            elapsed = time.time() - self.start_time - self.total_paused_time
        return self._format_duration(max(0.0, elapsed))

    def _record_loop(self):
        """Grabs frames and writes to MP4Video file."""
        # Grab first frame to determine screen resolution
        try:
            first_img = grab_screen_with_cursor()
            w, h = first_img.size
        except Exception as err:
            print(f"[VideoRecorder] Initial frame grab failed: {err}")
            self.is_recording = False
            if self.on_state_change:
                self.on_state_change(False, "00:00")
            return

        rec_settings = get_recording_settings()
        target_fps = float(rec_settings.get("recording_fps", 30))
        if target_fps <= 0:
            target_fps = 30.0
        frame_interval = 1.0 / target_fps
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        writer = cv2.VideoWriter(str(self.current_filepath), fourcc, target_fps, (w, h))

        if not writer.isOpened():
            print(f"[VideoRecorder] Error opening VideoWriter for {self.current_filepath}")
            self.is_recording = False
            if self.on_state_change:
                self.on_state_change(False, "00:00")
            return

        try:
            next_time = time.time()
            while not self._stop_event.is_set():
                if self.is_paused:
                    time.sleep(0.04)
                    next_time = time.time()
                    continue

                now = time.time()
                if now >= next_time:
                    try:
                        img = grab_screen_with_cursor()
                        frame = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
                        if frame.shape[1] != w or frame.shape[0] != h:
                            frame = cv2.resize(frame, (w, h), interpolation=cv2.INTER_LINEAR)
                        writer.write(frame)
                        self.frame_count += 1
                    except Exception as err:
                        print(f"[VideoRecorder] Frame write error: {err}")

                    next_time += frame_interval
                else:
                    sleep_time = next_time - now
                    if sleep_time > 0.002:
                        time.sleep(min(sleep_time, 0.02))
        finally:
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

    def _play_pause_sound(self):
        try:
            winsound.Beep(1500, 60)
            time.sleep(0.03)
            winsound.Beep(1100, 80)
        except Exception:
            pass

    def _play_resume_sound(self):
        try:
            winsound.Beep(1100, 60)
            time.sleep(0.03)
            winsound.Beep(1500, 80)
        except Exception:
            pass

    def _play_stop_sound(self):
        try:
            winsound.Beep(1600, 70)
            time.sleep(0.04)
            winsound.Beep(1200, 100)
        except Exception:
            pass
