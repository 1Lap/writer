# 1Lap Icons

This directory contains all icon assets for the 1Lap telemetry logger application.

## Icon Design

The icon features a tilted track (ellipse rotated 20°) with a centered "1" and a position dot, representing:
- The "1" - Brand identity (1Lap)
- The tilted track - Racing circuit/lap
- The position dot - Current telemetry position/car location

The design works well in both full color and monochrome, with clear silhouette recognition at small sizes.

## Icon Files

### Main Application Icon
- **1Lap.ico** - Multi-resolution Windows icon (16×16, 24×24, 32×32, 48×48, 256×256)
  - Used for: Application window, taskbar, desktop shortcut, file associations
  - Full color version (cyan track, white "1" and dot)

### System Tray State Icons (PNG, 256×256)
- **icon_idle.png** - Grey (not running, waiting for LMU)
- **icon_detecting.png** - Yellow (LMU detected, waiting for session)
- **icon_logging.png** - Green (actively logging telemetry)
- **icon_paused.png** - Orange with pause bars (logging paused)
- **icon_error.png** - Red (error state)

### Source SVG Files
All SVG source files are included for easy editing and regeneration:
- `1Lap_icon.svg` - Main app icon (full color)
- `icon_idle.svg` - Idle state
- `icon_detecting.svg` - Detecting state
- `icon_logging.svg` - Logging state
- `icon_paused.svg` - Paused state (with pause bar overlay)
- `icon_error.svg` - Error state

## Color Palette

The icon colors follow UI-safe conventions for clear state indication:

| State     | Color    | Hex Code | RGB           |
|-----------|----------|----------|---------------|
| Idle      | Grey     | #9CA3AF  | (156,163,175) |
| Detecting | Yellow   | #F59E0B  | (245,158,11)  |
| Logging   | Green    | #22C55E  | (34,197,94)   |
| Paused    | Orange   | #F97316  | (249,115,22)  |
| Error     | Red      | #EF4444  | (239,68,68)   |
| Brand     | Cyan     | #00E5FF  | (0,229,255)   |
| Text      | White    | #FFFFFF  | (255,255,255) |
| BG        | Dark     | #0B0E14  | (11,14,20)    |

## Regenerating Icons

If you modify the SVG files and need to regenerate PNG/ICO formats:

```bash
# Install dependencies (if not already installed)
pip install cairosvg Pillow

# Run the build script
python scripts/build_icons.py
```

This will:
1. Convert all SVG files to PNG at 256×256 resolution
2. Create multi-resolution 1Lap.ico from the main icon SVG
3. Output files to this directory

## Integration

### System Tray (tray_ui.py)
The TrayUI class automatically loads icons from this directory based on the current state:
- Icons are loaded via `_create_icon_image()` method
- Fallback to simple colored circles if PNG files are not found
- Handles both script mode and frozen executable (PyInstaller)

### Build Process (build.bat)
PyInstaller bundles the icons automatically:
```batch
--icon="assets\icons\1Lap.ico"           # Main app icon
--add-data "assets;assets"                # Bundle entire assets directory
```

### Installer (installer/1Lap_Setup.iss)
The Inno Setup installer includes all files from the dist directory, which contains the bundled assets folder.

## Design Rationale

### Why the tilt?
- Adds dynamic feel (motion/speed)
- Reduces overlap between "1" and track
- Creates more distinct silhouette for monochrome display
- Makes the "1" more prominent in system tray

### Pause Indicator
The pause icon includes two vertical bars overlaid on the position dot:
- Bar dimensions: 25px wide × 66px tall (60% of dot diameter)
- Rounded corners (5px radius) for visual consistency
- Dark background color (#0B0E14) to create contrast against orange track

### Fallback Strategy
The code includes fallback rendering if PNG files are missing:
- Creates simple 64×64 colored circles using PIL
- Ensures the app still runs even if icon files are corrupted/missing
- Uses the same color palette for consistency

## File Sizes
- 1Lap.ico: ~30 KB (multi-resolution)
- Each PNG icon: ~15-20 KB (256×256, optimized)
- Each SVG source: ~1-2 KB (vector format)

Total assets directory size: ~200 KB
