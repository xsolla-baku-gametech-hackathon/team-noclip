"""
Generates high-resolution Xsolla branding assets, icons, and .ico files.
Creates official-grade multi-size icons for the Windows executable and UI.
"""

import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ASSETS_DIR = Path(__file__).resolve().parent / "assets"
ASSETS_DIR.mkdir(parents=True, exist_ok=True)


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

        # Save Multi-Resolution Windows ICO from the robot mascot
        ico_path = ASSETS_DIR / "xsolla_icon.ico"
        sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
        robot_256.save(str(ico_path), format="ICO", sizes=sizes)
        print(f"[Assets] Created multi-size Windows robot icon: {ico_path}")
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
    img.save(str(ico_path), format="ICO", sizes=[(64, 64), (128, 128), (256, 256)])
    print(f"[Assets] Created fallback icon: {ico_path}")


if __name__ == "__main__":
    create_xsolla_icon()

