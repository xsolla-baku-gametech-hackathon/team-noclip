"""
Generates high-resolution Xsolla branding assets, icons, and .ico files.
Creates official-grade multi-size icons for the Windows executable and UI.
Extracts the official Xsolla Sol mascot from the vector-clean branding logo.
"""

import os
from pathlib import Path
from PIL import Image, ImageDraw
import numpy as np
from scipy.ndimage import label

BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"
ASSETS_DIR.mkdir(parents=True, exist_ok=True)


def extract_sol_mascot() -> Image.Image:
    """Extracts the pristine Xsolla Sol mascot emblem from official branding assets."""
    # Check high-res website logo sources first
    candidates = [
        BASE_DIR.parent / "website" / "public" / "xsolla-logo.png",
        BASE_DIR.parent / "website" / "dist" / "xsolla-logo.png",
        BASE_DIR.parent / "website" / "images" / "xsolla-logo.png",
        ASSETS_DIR / "xsolla_transparent.png",
    ]

    for cand in candidates:
        if cand.exists():
            img = Image.open(str(cand)).convert("RGBA")
            arr = np.array(img)
            labeled, num = label(arr[:, :, 3] > 10)

            # In website logo (1000x508), Sol mascot consists of body (2) and pupils (8, 9)
            for body_id in (2, 1):
                if body_id > num:
                    continue
                pupil_ids = [i for i in range(1, num + 1) if i != body_id and np.sum(labeled == i) < 400]
                sol_mask = (labeled == body_id)
                for pid in pupil_ids:
                    # Only include components that are within the bounding box of the body
                    ys_b, xs_b = np.where(labeled == body_id)
                    ys_p, xs_p = np.where(labeled == pid)
                    if xs_p.min() >= xs_b.min() and xs_p.max() <= xs_b.max() and ys_p.min() >= ys_b.min() and ys_p.max() <= ys_b.max():
                        sol_mask |= (labeled == pid)

                sol_arr = np.where(sol_mask[:, :, None], arr, 0)
                ys, xs = np.where(sol_mask)
                if len(ys) > 0 and len(xs) > 0:
                    w = xs.max() - xs.min() + 1
                    h = ys.max() - ys.min() + 1
                    # Sol mascot has roughly 1:1 aspect ratio (w ~ h)
                    if 0.8 <= (w / h) <= 1.25 and w > 40:
                        cropped = sol_arr[ys.min():ys.max() + 1, xs.min():xs.max() + 1]

                        # Center on a balanced square canvas with 8% padding
                        max_dim = int(max(w, h) * 1.16)
                        sq = np.zeros((max_dim, max_dim, 4), dtype=np.uint8)
                        y_off = (max_dim - h) // 2
                        x_off = (max_dim - w) // 2
                        sq[y_off:y_off + h, x_off:x_off + w] = cropped

                        mascot = Image.fromarray(sq)
                        print(f"[Assets] Extracted clean Sol mascot from {cand.name}: {w}x{h} -> {max_dim}x{max_dim}")
                        return mascot

    # Fallback geometric Sol mascot generation if no asset source is found
    size = 256
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    cyan = (112, 225, 255, 255)
    # 4 rounded lobes
    draw.rounded_rectangle([28, 64, 228, 192], radius=48, fill=cyan)
    draw.rounded_rectangle([64, 28, 192, 228], radius=48, fill=cyan)
    # Eye cutouts
    draw.ellipse([65, 95, 125, 155], fill=(0, 0, 0, 0))
    draw.ellipse([131, 95, 191, 155], fill=(0, 0, 0, 0))
    # Pupils
    draw.rectangle([83, 113, 107, 137], fill=cyan)
    draw.rectangle([149, 113, 173, 137], fill=cyan)
    return img


def create_xsolla_icon():
    """Generates official-grade robot mascot assets and multi-size Windows .ico."""
    mascot_img = extract_sol_mascot()
    mascot_256 = mascot_img.resize((256, 256), Image.Resampling.LANCZOS)

    # Save clean mascot PNGs
    clean_path = ASSETS_DIR / "xsolla_mascot_clean.png"
    robot_path = ASSETS_DIR / "xsolla_robot_mascot.png"
    emblem_path = ASSETS_DIR / "xsolla_emblem.png"

    mascot_256.save(str(clean_path), "PNG")
    mascot_256.save(str(robot_path), "PNG")
    mascot_256.save(str(emblem_path), "PNG")
    print(f"[Assets] Saved clean robot mascot PNGs: {clean_path}")

    # Save Standard Multi-Resolution Windows ICO for PyInstaller & Windows Explorer
    # Resolutions: 16x16, 24x24, 32x32, 48x48, 64x64, 256x256
    # Note: 128x128 is omitted intentionally to avoid PyInstaller's signed-char bWidth overflow bug (-128)
    ico_path = ASSETS_DIR / "xsolla_icon.ico"
    mascot_256.save(
        str(ico_path),
        format="ICO",
        sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (256, 256)]
    )
    print(f"[Assets] Generated official multi-resolution Windows robot icon: {ico_path} ({ico_path.stat().st_size} bytes)")


if __name__ == "__main__":
    create_xsolla_icon()
