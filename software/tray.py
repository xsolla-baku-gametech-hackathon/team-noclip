"""
Xsolla Game Recap - System Tray Integration
Runs the official Xsolla icon in the Windows taskbar notification area.
Provides right click access to open the GameBar, take a visual memory, view album,
log in/out, or quit.
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
                 on_quit: Callable[[], None],
                 on_capture: Optional[Callable[[], None]] = None,
                 on_open_album: Optional[Callable[[], None]] = None,
                 on_toggle_record: Optional[Callable[[], None]] = None,
                 on_login: Optional[Callable[[], None]] = None,
                 on_logout: Optional[Callable[[], None]] = None,
                 is_logged_in: Optional[Callable[[], bool]] = None):
        self.on_open_gamebar = on_open_gamebar
        self.on_test_banner = on_test_banner
        self.on_quit = on_quit
        self.on_capture = on_capture
        self.on_open_album = on_open_album
        self.on_toggle_record = on_toggle_record
        self.on_login = on_login
        self.on_logout = on_logout
        self.is_logged_in = is_logged_in or (lambda: False)

        self.icon = None
        self._thread: Optional[threading.Thread] = None

    def _load_icon_image(self) -> Image.Image:
        icon_path = ASSETS_DIR / "xsolla_mascot_clean.png"
        if not icon_path.exists():
            icon_path = ASSETS_DIR / "xsolla_robot_mascot.png"
        if not icon_path.exists():
            icon_path = ASSETS_DIR / "xsolla_emblem.png"

        try:
            img = Image.open(str(icon_path)).convert("RGBA")
            return img.resize((64, 64), Image.Resampling.LANCZOS)
        except Exception:
            return Image.new("RGBA", (64, 64), (112, 225, 255, 255))

    def _login_logout_text(self, _item) -> str:
        return "Sign Out" if self.is_logged_in() else "Login to Xsolla"

    def _handle_login_logout(self):
        if self.is_logged_in():
            if self.on_logout:
                self.on_logout()
        else:
            if self.on_login:
                self.on_login()

    def start(self):
        """Starts the system tray icon in a dedicated background thread."""
        img = self._load_icon_image()

        menu_items = [
            item("Open GameBar (Ctrl+Shift+X)", lambda: self.on_open_gamebar(), default=True),
        ]

        if self.on_capture:
            menu_items.append(item("📸 Take Screenshot (F11)", lambda: self.on_capture()))
        if self.on_toggle_record:
            menu_items.append(item("🔴 Toggle Video Recording (F9)", lambda: self.on_toggle_record()))
        if self.on_open_album:
            menu_items.append(item("🖼️ Captures Gallery", lambda: self.on_open_album()))

        menu_items.append(Menu.SEPARATOR)

        if self.on_login or self.on_logout:
            menu_items.append(item(self._login_logout_text, lambda: self._handle_login_logout()))

        menu_items.extend([
            item("Test Watching Banner", lambda: self.on_test_banner()),
            Menu.SEPARATOR,
            item("Quit Xsolla Game Recap", lambda: self.on_quit())
        ])

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
