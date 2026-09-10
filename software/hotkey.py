"""
Xsolla Game Recap - Global In-Game Hotkey Listener
Uses native Win32 RegisterHotKey API to detect shortcuts:
- [Ctrl + Shift + X] or [Alt + X]: Toggle in-game GameBar overlay
- [F11] or [Ctrl + Shift + S]: Capture instant high-quality screenshot
- [F9] or [Ctrl + Shift + R]: Toggle video recording (Start / Stop)
"""

import ctypes
import ctypes.wintypes
import threading
from typing import Callable, Optional

# Win32 Constants
WM_HOTKEY = 0x0312
MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_NOREPEAT = 0x4000

HOTKEY_ID_PRIMARY = 101        # Ctrl + Shift + X
HOTKEY_ID_SECONDARY = 102      # Alt + X
HOTKEY_ID_CAPTURE_F11 = 103    # F11
HOTKEY_ID_CAPTURE_COMBO = 104  # Ctrl + Shift + S
HOTKEY_ID_RECORD_F9 = 105      # F9
HOTKEY_ID_RECORD_COMBO = 106   # Ctrl + Shift + R

VK_X = 0x58
VK_S = 0x53
VK_R = 0x52
VK_F9 = 0x78
VK_F11 = 0x7A

user32 = ctypes.windll.user32


class GlobalHotkeyListener:
    def __init__(self,
                 on_hotkey: Callable[[], None],
                 on_capture: Optional[Callable[[], None]] = None,
                 on_record: Optional[Callable[[], None]] = None):
        self.on_hotkey = on_hotkey
        self.on_capture = on_capture
        self.on_record = on_record
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def start(self):
        """Start listening for global shortcuts."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._message_loop, daemon=True)
        self._thread.start()
        print("[Hotkey] Global hotkeys active: [Ctrl+Shift+X] Overlay, [F11] Screenshot, [F9] Video Record.")

    def stop(self):
        """Stop hotkey listening and unregister from Windows."""
        self._running = False
        try:
            user32.UnregisterHotKey(None, HOTKEY_ID_PRIMARY)
            user32.UnregisterHotKey(None, HOTKEY_ID_SECONDARY)
            user32.UnregisterHotKey(None, HOTKEY_ID_CAPTURE_F11)
            user32.UnregisterHotKey(None, HOTKEY_ID_CAPTURE_COMBO)
            user32.UnregisterHotKey(None, HOTKEY_ID_RECORD_F9)
            user32.UnregisterHotKey(None, HOTKEY_ID_RECORD_COMBO)
            user32.PostQuitMessage(0)
        except Exception:
            pass

    def _message_loop(self):
        # 1. Overlay Hotkeys
        user32.RegisterHotKey(None, HOTKEY_ID_PRIMARY, MOD_CONTROL | MOD_SHIFT | MOD_NOREPEAT, VK_X)
        user32.RegisterHotKey(None, HOTKEY_ID_SECONDARY, MOD_ALT | MOD_NOREPEAT, VK_X)

        # 2. Screenshot Capture Hotkeys
        user32.RegisterHotKey(None, HOTKEY_ID_CAPTURE_F11, MOD_NOREPEAT, VK_F11)
        user32.RegisterHotKey(None, HOTKEY_ID_CAPTURE_COMBO, MOD_CONTROL | MOD_SHIFT | MOD_NOREPEAT, VK_S)

        # 3. Video Record Hotkeys
        user32.RegisterHotKey(None, HOTKEY_ID_RECORD_F9, MOD_NOREPEAT, VK_F9)
        user32.RegisterHotKey(None, HOTKEY_ID_RECORD_COMBO, MOD_CONTROL | MOD_SHIFT | MOD_NOREPEAT, VK_R)

        msg = ctypes.wintypes.MSG()
        while self._running:
            b_ret = user32.GetMessageW(ctypes.byref(msg), None, 0, 0)
            if b_ret == 0 or b_ret == -1:
                break

            if msg.message == WM_HOTKEY:
                if msg.wParam in (HOTKEY_ID_PRIMARY, HOTKEY_ID_SECONDARY):
                    print("[Hotkey] Shortcut pressed: Toggling GameBar Overlay...")
                    if self.on_hotkey:
                        self.on_hotkey()
                elif msg.wParam in (HOTKEY_ID_CAPTURE_F11, HOTKEY_ID_CAPTURE_COMBO):
                    print("[Hotkey] Screenshot hotkey pressed: Capturing Screenshot...")
                    if self.on_capture:
                        self.on_capture()
                elif msg.wParam in (HOTKEY_ID_RECORD_F9, HOTKEY_ID_RECORD_COMBO):
                    print("[Hotkey] Record hotkey pressed: Toggling Video Recording...")
                    if self.on_record:
                        self.on_record()

            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))

        user32.UnregisterHotKey(None, HOTKEY_ID_PRIMARY)
        user32.UnregisterHotKey(None, HOTKEY_ID_SECONDARY)
        user32.UnregisterHotKey(None, HOTKEY_ID_CAPTURE_F11)
        user32.UnregisterHotKey(None, HOTKEY_ID_CAPTURE_COMBO)
        user32.UnregisterHotKey(None, HOTKEY_ID_RECORD_F9)
        user32.UnregisterHotKey(None, HOTKEY_ID_RECORD_COMBO)
