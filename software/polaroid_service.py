"""
Xsolla Game Recap - High Quality In-Game Screenshot Service
Captures pure, lossless, full-resolution screenshots directly from the game screen.
Zero watermarks, zero borders, zero overlays - 100% original image quality.
"""

import time
import re
import datetime
import winsound
import threading
from pathlib import Path
from typing import Optional, Dict, List
from config import SCREENSHOTS_DIR, ensure_data_dir
from capture_utils import grab_screen_with_cursor


class PolaroidService:
    def __init__(self):
        ensure_data_dir()

    def capture_memory(self,
                       game_name: str = "Active Game",
                       session_duration: str = "00:00:00",
                       notes: str = "") -> Optional[Dict]:
        """
        Captures full-screen in pure original high-quality resolution (lossless PNG),
        plays shutter sound feedback, and saves directly to Documents/XSOLLA_gamerecap/captures/.
        """
        ensure_data_dir()
        timestamp = int(time.time())
        now = datetime.datetime.now()
        date_str = now.strftime("%d %b %Y").upper()
        time_str = now.strftime("%H:%M:%S")

        # Clean game tag for filename
        clean_name = re.sub(r'[^a-zA-Z0-9_\-]', '', game_name.replace(" ", "_")).lower()
        if not clean_name:
            clean_name = "game"

        # 1. Capture pristine, full-resolution screen with mouse cursor
        try:
            # Grabs the exact full desktop at native monitor resolution with live cursor
            img = grab_screen_with_cursor()
        except Exception as err:
            print(f"[Screenshot] Screen grab error: {err}")
            return None

        # Play camera shutter audio cue asynchronously
        threading.Thread(target=self._play_shutter_sound, daemon=True).start()

        # 2. Save pure, uncompressed high-quality PNG with zero watermarks or overlays
        filename = f"screenshot_{clean_name}_{timestamp}.png"
        filepath = SCREENSHOTS_DIR / filename
        try:
            img.save(str(filepath), "PNG", compress_level=1)
        except Exception as err:
            print(f"[Screenshot] Save error: {err}")
            return None

        result = {
            "timestamp": timestamp,
            "game_name": game_name,
            "date": date_str,
            "time": time_str,
            "duration": session_duration,
            "path": str(filepath),
            "filename": filename,
            "width": img.width,
            "height": img.height
        }
        print(f"[Screenshot] High-quality capture saved ({img.width}x{img.height}): {filename}")
        return result

    def _play_shutter_sound(self):
        """Crisp camera shutter sound feedback."""
        try:
            winsound.Beep(1400, 60)
            time.sleep(0.04)
            winsound.Beep(1800, 90)
        except Exception:
            pass

    def get_recent_memories(self, limit: int = 40) -> List[Path]:
        """Returns sorted list of captured high-quality screenshots and video clips (newest first)."""
        ensure_data_dir()
        if not SCREENSHOTS_DIR.exists():
            return []

        # Find screenshots and video recordings
        files = []
        for pattern in ("screenshot_*.png", "capture_*.png", "polaroid_*.png", "*.png", "*.jpg", "*.mp4", "*.mkv"):
            files.extend(list(SCREENSHOTS_DIR.glob(pattern)))

        # Remove duplicates if any and sort newest first
        unique_files = list({p.resolve(): p for p in files}.values())
        unique_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        return unique_files[:limit]
