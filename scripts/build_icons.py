#!/usr/bin/env python
"""
Icon Builder Script for 1Lap Telemetry Logger

Converts SVG icons to PNG and ICO formats for use in the application.
Requires: cairosvg, Pillow

Usage:
    python scripts/build_icons.py
"""

import os
from pathlib import Path

try:
    import cairosvg
    from PIL import Image
except ImportError as e:
    print(f"Error: Required package not found: {e}")
    print("Please install: pip install cairosvg Pillow")
    exit(1)


def svg_to_png(svg_path, png_path, size):
    """Convert SVG to PNG at specified size."""
    cairosvg.svg2png(
        url=str(svg_path),
        write_to=str(png_path),
        output_width=size,
        output_height=size
    )
    print(f"  ✓ Created {png_path.name} ({size}x{size})")


def create_ico_from_svg(svg_path, ico_path, sizes=[16, 24, 32, 48, 256]):
    """Create multi-resolution ICO file from SVG."""
    # Create temp PNGs at different sizes
    temp_pngs = []
    temp_dir = ico_path.parent / "temp"
    temp_dir.mkdir(exist_ok=True)

    for size in sizes:
        temp_png = temp_dir / f"temp_{size}.png"
        svg_to_png(svg_path, temp_png, size)
        temp_pngs.append(Image.open(temp_png))

    # Save as ICO with multiple resolutions
    temp_pngs[0].save(
        ico_path,
        format='ICO',
        sizes=[(img.width, img.height) for img in temp_pngs],
        append_images=temp_pngs[1:]
    )
    print(f"  ✓ Created {ico_path.name} with sizes: {sizes}")

    # Cleanup temp files
    for temp_png in temp_dir.glob("temp_*.png"):
        temp_png.unlink()
    temp_dir.rmdir()


def main():
    # Setup paths
    root_dir = Path(__file__).parent.parent
    svg_dir = root_dir / "assets" / "icons"

    print("Building icons for 1Lap Telemetry Logger\n")
    print("=" * 50)

    # Create main app icon (ICO for Windows)
    print("\n1. Creating main application icon (1Lap.ico)...")
    create_ico_from_svg(
        svg_dir / "1Lap_icon.svg",
        svg_dir / "1Lap.ico",
        sizes=[16, 24, 32, 48, 256]
    )

    # Create tray state icons (PNG format for pystray)
    print("\n2. Creating system tray icons (PNG format)...")
    tray_icons = [
        "icon_idle.svg",
        "icon_detecting.svg",
        "icon_logging.svg",
        "icon_error.svg",
        "icon_paused.svg"
    ]

    for icon_name in tray_icons:
        svg_path = svg_dir / icon_name
        png_path = svg_dir / icon_name.replace('.svg', '.png')

        # Create at 256x256 (high quality for system scaling)
        svg_to_png(svg_path, png_path, 256)

    print("\n" + "=" * 50)
    print("✓ All icons built successfully!")
    print(f"\nGenerated files in: {svg_dir}")
    print("  - 1Lap.ico (main app icon)")
    print("  - icon_*.png (system tray icons)")


if __name__ == "__main__":
    main()
