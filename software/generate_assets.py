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
    size = 256
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 1. Dark Rounded Squircle Base (#0c0e14 with #1b2130 border)
    margin = 8
    draw.rounded_rectangle(
        [margin, margin, size - margin, size - margin],
        radius=48,
        fill="#0d1117",
        outline="#ff0055",
        width=4
    )

    # Subtle inner glow line
    draw.rounded_rectangle(
        [margin + 4, margin + 4, size - margin - 4, size - margin - 4],
        radius=44,
        outline="#242c3d",
        width=2
    )

    # 2. Iconic Geometric Xsolla "X" (Signature vibrant crimson & cyan cuts)
    # Left diagonal stroke (Red/Crimson #ff0055)
    poly_left = [
        (62, 54),
        (104, 54),
        (194, 202),
        (152, 202)
    ]
    draw.polygon(poly_left, fill="#ff0055")

    # Right diagonal stroke (Deep Coral #ff3366 with white highlight cut)
    poly_right_top = [
        (194, 54),
        (152, 54),
        (116, 114),
        (138, 132)
    ]
    draw.polygon(poly_right_top, fill="#ffffff")

    poly_right_bot = [
        (118, 124),
        (140, 142),
        (104, 202),
        (62, 202)
    ]
    draw.polygon(poly_right_bot, fill="#00f5d4")

    # 3. Center Cyber Accent
    draw.ellipse([118, 118, 138, 138], fill="#ff0055", outline="#ffffff", width=2)

    # Save PNG
    png_path = ASSETS_DIR / "xsolla_logo.png"
    img.save(str(png_path), "PNG")
    print(f"[Assets] Created {png_path}")

    # Save Multi-Resolution Windows ICO
    ico_path = ASSETS_DIR / "xsolla_icon.ico"
    sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    img.save(str(ico_path), format="ICO", sizes=sizes)
    print(f"[Assets] Created multi-size Windows icon: {ico_path}")


if __name__ == "__main__":
    create_xsolla_icon()
