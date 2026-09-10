"""
Xsolla Game Recap - System Tray Integration
Runs the official Xsolla icon in the Windows taskbar notification area.
Provides right click access to open the GameBar, test the banner, or quit.
"""

import threading
from typing import Callable, Optional
from PIL import Image
import pystray
from pystray import MenuItem as item, Menu

from config import ASSETS_DIR


class SystemTrayIcon:
    def __init__(self,
                 on_open_gamebar: Callable[[], None],
                 on_test_banner: Callable[[], None],
                 on_quit: Callable[[], None]):
        self.on_open_gamebar = on_open_gamebar
        self.on_test_banner = on_test_banner
        self.on_quit = on_quit

        self.icon = None
        self._thread: Optional[threading.Thread] = None

    def _load_icon_image(self) -> Image.Image:
        icon_path = ASSETS_DIR / "xsolla_emblem.png"
        if not icon_path.exists():
            icon_path = ASSETS_DIR / "xsolla_logo.png"

        try:
            img = Image.open(str(icon_path)).convert("RGBA")
            return img.resize((64, 64), Image.Resampling.LANCZOS)
        except Exception:
            return Image.new("RGBA", (64, 64), (112, 225, 255, 255))

    def start(self):
        """Starts the system tray icon in a dedicated background thread."""
        img = self._load_icon_image()

        menu_items = [
            item("Open GameBar (Ctrl+Shift+X)", lambda: self.on_open_gamebar(), default=True),
            item("Test Watching Banner", lambda: self.on_test_banner()),
            Menu.SEPARATOR,
            item("Quit Xsolla Game Recap", lambda: self.on_quit())
        ]

        self.icon = pystray.Icon(
            "xsolla_game_recap",
            img,
            "Xsolla Game Recap",
            menu=Menu(*menu_items)
        )

        self._thread = threading.Thread(target=self.icon.run, daemon=True)
        self._thread.start()
        print("[Tray] System Tray icon active.")

    def stop(self):
        """Removes tray icon from taskbar."""
        if self.icon:
            try:
                self.icon.stop()
            except Exception:
                pass
            self.icon = None
