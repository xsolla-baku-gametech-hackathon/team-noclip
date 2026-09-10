"""
Xsolla Game Recap - Global In-Game Hotkey Listener
Uses the native Win32 RegisterHotKey API to detect shortcuts (Ctrl+Shift+X or Alt+X)
even when high-performance full-screen games or cracked games are actively running!
"""

import ctypes
import threading
from typing import Callable, Optional

# Win32 Constants
WM_HOTKEY = 0x0312
MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_NOREPEAT = 0x4000

HOTKEY_ID_PRIMARY = 101
HOTKEY_ID_SECONDARY = 102

user32 = ctypes.windll.user32


class GlobalHotkeyListener:
    def __init__(self, on_hotkey: Callable[[], None]):
        self.on_hotkey = on_hotkey
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def start(self):
        """Start listening for the global overlay shortcut."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._message_loop, daemon=True)
        self._thread.start()
        print("[Hotkey] Global hotkey listener activated (Ctrl+Shift+X and Alt+X).")

    def stop(self):
        """Stop hotkey listening and unregister from Windows."""
        self._running = False
        try:
            user32.UnregisterHotKey(None, HOTKEY_ID_PRIMARY)
            user32.UnregisterHotKey(None, HOTKEY_ID_SECONDARY)
            # Post quit message to unblock GetMessageW
            user32.PostQuitMessage(0)
        except Exception:
            pass

    def _message_loop(self):
        # Register Primary: Ctrl + Shift + X (VK_X is 0x58)
        vk_x = 0x58
        reg1 = user32.RegisterHotKey(
            None,
            HOTKEY_ID_PRIMARY,
            MOD_CONTROL | MOD_SHIFT | MOD_NOREPEAT,
            vk_x
        )
        if not reg1:
            print("[Hotkey] Warning: Primary hotkey Ctrl+Shift+X could not be registered (may be in use).")

        # Register Secondary / Convenient Fallback: Alt + X
        reg2 = user32.RegisterHotKey(
            None,
            HOTKEY_ID_SECONDARY,
            MOD_ALT | MOD_NOREPEAT,
            vk_x
        )
        if not reg2:
            print("[Hotkey] Warning: Secondary hotkey Alt+X could not be registered.")

        # Win32 Message Loop
        msg = ctypes.wintypes.MSG()
        while self._running:
            b_ret = user32.GetMessageW(ctypes.byref(msg), None, 0, 0)
            if b_ret == 0 or b_ret == -1:
                break

            if msg.message == WM_HOTKEY:
                if msg.wParam in (HOTKEY_ID_PRIMARY, HOTKEY_ID_SECONDARY):
                    print(f"[Hotkey] Shortcut pressed! Toggling GameBar Overlay...")
                    if self.on_hotkey:
                        self.on_hotkey()

            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))

        user32.UnregisterHotKey(None, HOTKEY_ID_PRIMARY)
        user32.UnregisterHotKey(None, HOTKEY_ID_SECONDARY)
