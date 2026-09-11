"""
Generates high-resolution Xsolla branding assets, icons, and .ico files.
Creates official-grade multi-size icons for the Windows executable and UI.
"""

import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ASSETS_DIR = Path(__file__).resolve().parent / "assets"
ASSETS_DIR.mkdir(parents=True, exist_ok=True)


import struct
import io


def make_windows_ico(src_image: Image.Image, out_path: Path):
    """Encodes a multi-resolution Windows ICO with standard 32-bit DIB entries and 256px PNG."""
    sizes = [16, 24, 32, 48, 64, 128, 256]
    entries = []
    data_blobs = []

    for s in sizes:
        resized = src_image.resize((s, s), Image.Resampling.LANCZOS).convert('RGBA')
        if s == 256:
            buf = io.BytesIO()
            resized.save(buf, format='PNG')
            blob = buf.getvalue()
        else:
            w, h = s, s
            header = struct.pack(
                '<IIIHHIIIIII',
                40,           # biSize
                w,            # biWidth
                h * 2,        # biHeight (XOR mask + AND mask)
                1,            # biPlanes
                32,           # biBitCount
                0,            # biCompression (BI_RGB)
                w * h * 4,    # biSizeImage
                0, 0, 0, 0    # resolution & colors
            )
            pixels = []
            for y in range(h - 1, -1, -1):
                for x in range(w):
                    r, g, b, a = resized.getpixel((x, y))
                    pixels.append(struct.pack('BBBB', b, g, r, a))
            xor_mask = b''.join(pixels)

            and_bytes = []
            row_bytes_len = (w + 31) // 32 * 4
            for y in range(h - 1, -1, -1):
                row_bits = 0
                for x in range(w):
                    a = resized.getpixel((x, y))[3]
                    if a < 128:
                        row_bits |= (1 << (7 - (x % 8)))
                    if (x % 8 == 7) or (x == w - 1):
                        and_bytes.append(struct.pack('B', row_bits))
                        row_bits = 0
                cur_len = len(and_bytes) % row_bytes_len
                if cur_len != 0:
                    and_bytes.append(b'\x00' * (row_bytes_len - cur_len))
            and_mask = b''.join(and_bytes)
            blob = header + xor_mask + and_mask

        data_blobs.append(blob)
        b_w = 0 if s == 256 else s
        b_h = 0 if s == 256 else s
        entries.append({
            'width': b_w,
            'height': b_h,
            'color_count': 0,
            'reserved': 0,
            'planes': 1,
            'bit_count': 32,
            'size': len(blob)
        })

    icondir = struct.pack('<HHH', 0, 1, len(sizes))
    offset = 6 + len(sizes) * 16
    direntries = []
    for entry in entries:
        direntries.append(struct.pack(
            '<BBBBHHII',
            entry['width'],
            entry['height'],
            entry['color_count'],
            entry['reserved'],
            entry['planes'],
            entry['bit_count'],
            entry['size'],
            offset
        ))
        offset += entry['size']

    with open(str(out_path), 'wb') as f:
        f.write(icondir)
        for de in direntries:
            f.write(de)
        for blob in data_blobs:
            f.write(blob)
    print(f"[Assets] Created standard multi-size Windows robot icon: {out_path} ({offset} bytes)")


def create_xsolla_icon():
    """Generates official-grade robot mascot assets and multi-size Windows .ico."""
    trans_path = ASSETS_DIR / "xsolla_transparent.png"
    if trans_path.exists():
        import numpy as np
        from scipy.ndimage import label

        img = Image.open(str(trans_path))
        arr = np.array(img)
        arr_alpha = arr[:, :, 3] > 10
        labeled, num = label(arr_alpha)
        # Component 1 (body) and 6, 7 (eyes)
        robot_mask = (labeled == 1) | (labeled == 6) | (labeled == 7)
        arr_robot = arr.copy()
        arr_robot[~robot_mask] = 0
        y_indices, x_indices = np.where(robot_mask)
        cropped = arr_robot[y_indices.min():y_indices.max() + 1, x_indices.min():x_indices.max() + 1]
        h, w, c = cropped.shape

        # Create centered square canvas with subtle padding
        max_dim = max(w, h) + 8
        sq_arr = np.zeros((max_dim, max_dim, 4), dtype=np.uint8)
        y_off = (max_dim - h) // 2
        x_off = (max_dim - w) // 2
        sq_arr[y_off:y_off + h, x_off:x_off + w] = cropped

        robot_img = Image.fromarray(sq_arr)
        robot_256 = robot_img.resize((256, 256), Image.Resampling.LANCZOS)

        # Save clean mascot PNGs
        clean_path = ASSETS_DIR / "xsolla_mascot_clean.png"
        robot_path = ASSETS_DIR / "xsolla_robot_mascot.png"
        emblem_path = ASSETS_DIR / "xsolla_emblem.png"

        robot_256.save(str(clean_path), "PNG")
        robot_256.save(str(robot_path), "PNG")
        robot_256.save(str(emblem_path), "PNG")
        print(f"[Assets] Created clean robot mascot PNGs: {clean_path}")

        # Save Standard Multi-Resolution Windows ICO from the robot mascot
        ico_path = ASSETS_DIR / "xsolla_icon.ico"
        make_windows_ico(robot_img, ico_path)
        return

    # Fallback if transparent source is missing
    size = 256
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    margin = 8
    draw.rounded_rectangle([margin, margin, size - margin, size - margin], radius=48, fill="#0d1117", outline="#70e1ff", width=4)
    png_path = ASSETS_DIR / "xsolla_mascot_clean.png"
    img.save(str(png_path), "PNG")
    ico_path = ASSETS_DIR / "xsolla_icon.ico"
    make_windows_ico(img, ico_path)
    print(f"[Assets] Created fallback icon: {ico_path}")


if __name__ == "__main__":
    create_xsolla_icon()

