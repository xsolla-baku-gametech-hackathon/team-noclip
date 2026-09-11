"""
Xsolla Game Recap - Screen & Cursor Capture Utility
Provides high-performance screen grabbing with hardware cursor overlay support.
Extracts native Windows cursor with transparency, caches handles, and falls back
gracefully to a high-DPI vector pointer if needed.
"""

from typing import Tuple, Optional
from PIL import Image, ImageGrab, ImageDraw
import win32gui
import win32ui
import win32con


_cursor_cache = {}


def get_cursor_rgba(hcursor: int) -> Tuple[Optional[Image.Image], int, int]:
    """
    Extracts the native Windows cursor as a 32x32 RGBA PIL Image with hotspot coordinates.
    Caches the result by hcursor handle for ultra-fast frame rates during video recording.
    """
    if hcursor in _cursor_cache:
        return _cursor_cache[hcursor]

    hdc = None
    hcdc = None
    hbmp_b = None
    hbmp_w = None
    hbm_mask = None
    hbm_color = None
    try:
        info = win32gui.GetIconInfo(hcursor)
        x_hot = info[1]
        y_hot = info[2]
        hbm_mask = info[3]
        hbm_color = info[4]
        w, h = 32, 32

        hdc = win32gui.GetDC(0)
        hcdc = win32gui.CreateCompatibleDC(hdc)

        # Draw on black background
        hbmp_b = win32gui.CreateCompatibleBitmap(hdc, w, h)
        hOld = win32gui.SelectObject(hcdc, hbmp_b)
        brush_b = win32gui.CreateSolidBrush(0x000000)
        win32gui.FillRect(hcdc, (0, 0, w, h), brush_b)
        win32gui.DeleteObject(brush_b)
        win32gui.DrawIconEx(hcdc, 0, 0, hcursor, w, h, 0, 0, win32con.DI_NORMAL)

        bmp_b = win32ui.CreateBitmapFromHandle(hbmp_b)
        img_b = Image.frombuffer('RGB', (w, h), bmp_b.GetBitmapBits(True), 'raw', 'BGRX', 0, 1)

        # Draw on white background with distinct bitmap to calculate exact alpha mask
        hbmp_w = win32gui.CreateCompatibleBitmap(hdc, w, h)
        win32gui.SelectObject(hcdc, hbmp_w)
        brush_w = win32gui.CreateSolidBrush(0xFFFFFF)
        win32gui.FillRect(hcdc, (0, 0, w, h), brush_w)
        win32gui.DeleteObject(brush_w)
        win32gui.DrawIconEx(hcdc, 0, 0, hcursor, w, h, 0, 0, win32con.DI_NORMAL)

        bmp_w = win32ui.CreateBitmapFromHandle(hbmp_w)
        img_w = Image.frombuffer('RGB', (w, h), bmp_w.GetBitmapBits(True), 'raw', 'BGRX', 0, 1)

        win32gui.SelectObject(hcdc, hOld)
        win32gui.DeleteObject(hbmp_b)
        hbmp_b = None
        win32gui.DeleteObject(hbmp_w)
        hbmp_w = None
        win32gui.DeleteDC(hcdc)
        hcdc = None
        win32gui.ReleaseDC(0, hdc)
        hdc = None

        # Compute alpha channel
        rgba = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        pb = img_b.load()
        pw = img_w.load()
        prgba = rgba.load()

        for y in range(h):
            for x in range(w):
                rb, gb, bb = pb[x, y]
                rw, gw, bw = pw[x, y]
                if rb == 0 and gb == 0 and bb == 0 and rw == 255 and gw == 255 and bw == 255:
                    prgba[x, y] = (0, 0, 0, 0)
                else:
                    prgba[x, y] = (rb, gb, bb, 255)

        res = (rgba, x_hot, y_hot)
        _cursor_cache[hcursor] = res
        return res
    except Exception:
        # Fallback to high-DPI sleek cursor pointer
        w, h = 32, 32
        fb = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(fb)
        pts = [(0, 0), (0, 18), (5, 14), (8, 21), (11, 20), (8, 13), (14, 13)]
        draw.polygon(pts, fill=(255, 255, 255, 255), outline=(0, 0, 0, 255))
        res = (fb, 0, 0)
        _cursor_cache[hcursor] = res
        return res
    finally:
        if hbm_mask:
            win32gui.DeleteObject(hbm_mask)
        if hbm_color:
            win32gui.DeleteObject(hbm_color)
        if hbmp_b:
            win32gui.DeleteObject(hbmp_b)
        if hbmp_w:
            win32gui.DeleteObject(hbmp_w)
        if hcdc:
            win32gui.DeleteDC(hcdc)
        if hdc:
            win32gui.ReleaseDC(0, hdc)


def overlay_cursor_on_image(img: Image.Image) -> Image.Image:
    """
    Overlays the current active Windows mouse cursor onto a PIL Image at its live screen position.
    """
    try:
        flags, hcursor, (cx, cy) = win32gui.GetCursorInfo()
        # flags == 1 means CURSOR_SHOWING
        if flags == 1 and hcursor:
            rgba, x_hot, y_hot = get_cursor_rgba(hcursor)
            if rgba:
                # Ensure paste coordinates are within screen boundaries
                px = cx - x_hot
                py = cy - y_hot
                img.paste(rgba, (px, py), rgba)
    except Exception:
        pass
    return img


_INPUT_DESKTOP_HANDLE = None

def _ensure_input_desktop():
    """Ensure current thread is attached to the interactive input desktop if needed."""
    global _INPUT_DESKTOP_HANDLE
    try:
        import ctypes
        user32 = ctypes.windll.user32
        if not _INPUT_DESKTOP_HANDLE:
            h_input = user32.OpenInputDesktop(0, False, 0x01FF)
            if h_input:
                _INPUT_DESKTOP_HANDLE = h_input
                user32.SetThreadDesktop(h_input)
        else:
            user32.SetThreadDesktop(_INPUT_DESKTOP_HANDLE)
    except Exception:
        pass


def grab_screen_with_cursor(include_cursor: bool = True) -> Image.Image:
    """
    Captures native resolution screen with optional live cursor overlay.
    Includes layered and alpha-blended windows (e.g. Xsolla GameBar & Login launcher).
    """
    _ensure_input_desktop()
    img = None
    try:
        img = ImageGrab.grab(all_screens=True, include_layered_windows=True)
    except Exception:
        try:
            img = ImageGrab.grab(include_layered_windows=True)
        except Exception:
            try:
                img = ImageGrab.grab()
            except Exception:
                pass

    if img is None:
        import threading
        box = [None]
        def _bg_grab():
            try:
                import ctypes
                user32 = ctypes.windll.user32
                h = user32.OpenInputDesktop(0, False, 0x01FF)
                if h:
                    user32.SetThreadDesktop(h)
                box[0] = ImageGrab.grab(all_screens=True, include_layered_windows=True)
            except Exception:
                try:
                    box[0] = ImageGrab.grab(include_layered_windows=True)
                except Exception:
                    try:
                        box[0] = ImageGrab.grab()
                    except Exception:
                        pass
        t = threading.Thread(target=_bg_grab)
        t.start()
        t.join(timeout=2.0)
        img = box[0]

    if img is None:
        img = ImageGrab.grab()

    if include_cursor and img:
        img = overlay_cursor_on_image(img)
    return img
