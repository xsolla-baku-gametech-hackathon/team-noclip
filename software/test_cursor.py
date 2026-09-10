import win32gui
import win32ui
import win32con
from PIL import Image, ImageGrab, ImageDraw
from pathlib import Path
import time

log = Path(__file__).parent / "cursor_test_log.txt"

_cursor_cache = {}

def get_cursor_rgba(hcursor):
    if hcursor in _cursor_cache:
        return _cursor_cache[hcursor]
        
    try:
        info = win32gui.GetIconInfo(hcursor)
        x_hot = info[1]
        y_hot = info[2]
        w, h = 32, 32
        
        hdc = win32gui.GetDC(0)
        hcdc = win32gui.CreateCompatibleDC(hdc)
        
        hbmp_b = win32gui.CreateCompatibleBitmap(hdc, w, h)
        hOld = win32gui.SelectObject(hcdc, hbmp_b)
        brush_b = win32gui.CreateSolidBrush(0x000000)
        win32gui.FillRect(hcdc, (0, 0, w, h), brush_b)
        win32gui.DeleteObject(brush_b)
        win32gui.DrawIconEx(hcdc, 0, 0, hcursor, w, h, 0, 0, win32con.DI_NORMAL)
        
        bmp = win32ui.CreateBitmapFromHandle(hbmp_b)
        img_b = Image.frombuffer('RGB', (w, h), bmp.GetBitmapBits(True), 'raw', 'BGRX', 0, 1)
        
        brush_w = win32gui.CreateSolidBrush(0xFFFFFF)
        win32gui.FillRect(hcdc, (0, 0, w, h), brush_w)
        win32gui.DeleteObject(brush_w)
        win32gui.DrawIconEx(hcdc, 0, 0, hcursor, w, h, 0, 0, win32con.DI_NORMAL)
        
        bmp2 = win32ui.CreateBitmapFromHandle(hbmp_b)
        img_w = Image.frombuffer('RGB', (w, h), bmp2.GetBitmapBits(True), 'raw', 'BGRX', 0, 1)
        
        win32gui.SelectObject(hcdc, hOld)
        win32gui.DeleteObject(hbmp_b)
        win32gui.DeleteDC(hcdc)
        win32gui.ReleaseDC(0, hdc)
        
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
    except Exception as e:
        # Fallback sleek pointer arrow
        w, h = 32, 32
        fb = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(fb)
        pts = [(0, 0), (0, 18), (5, 14), (8, 21), (11, 20), (8, 13), (14, 13)]
        draw.polygon(pts, fill=(255, 255, 255, 255), outline=(0, 0, 0, 255))
        res = (fb, 0, 0)
        _cursor_cache[hcursor] = res
        return res

def capture_screen_with_cursor():
    img = ImageGrab.grab()
    try:
        flags, hcursor, (cx, cy) = win32gui.GetCursorInfo()
        if flags == 1 and hcursor:
            rgba, x_hot, y_hot = get_cursor_rgba(hcursor)
            if rgba:
                img.paste(rgba, (cx - x_hot, cy - y_hot), rgba)
    except Exception as e:
        pass
    return img

t0 = time.time()
shot = capture_screen_with_cursor()
t1 = time.time()
shot_path = Path(__file__).parent / "screenshot_with_cursor.png"
shot.save(str(shot_path))
log.write_text(f"SUCCESS: Screenshot with cursor saved in {(t1-t0)*1000:.2f}ms! Size: {shot.size}\n")
