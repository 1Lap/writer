# Feature: System Tray UI

**Status**: ✅ Implemented
**Priority**: Medium
**Category**: User Interface
**Related Phase**: Phase 5 (System Tray UI & User Controls)
**Implementation Date**: 2025-11-20

---

## Implementation Summary

### What Was Implemented

✅ **Core System Tray Functionality**
- `src/tray_ui.py` - TrayUI class with full system tray integration
- `tray_app.py` - New entry point for running app with system tray
- Icon generation using Pillow (gray/yellow/green/orange/red states)
- Context menu with all required items
- Status tooltips with real-time updates
- Threading integration (telemetry in background, tray in main thread)

✅ **Must Have Requirements Met**
1. System tray icon with state indicators (IDLE=gray, DETECTED=yellow, LOGGING=green, PAUSED=orange, ERROR=red)
2. Context menu with Start/Stop, Pause/Resume, Open Output Folder, Quit
3. Status display via tooltips showing current state, lap number, and sample count
4. Graceful shutdown on Quit (stops telemetry loop, saves data, exits cleanly)

✅ **Nice to Have Requirements Met**
1. Tooltip on hover showing detailed status
2. Dynamic menu item text (Start↔Stop, Pause↔Resume based on state)
3. Pause/Resume menu item enabled only when logging is running

✅ **Testing**
- 15 comprehensive unit tests in `tests/test_tray_ui.py`
- All tests passing
- TDD approach followed (tests written first)

### Usage

```bash
# Run with system tray UI
python tray_app.py

# Open settings dialog first
python tray_app.py --settings
```

### Files Added/Modified

**New Files:**
- `src/tray_ui.py` - System tray UI class
- `tray_app.py` - Entry point with tray integration
- `tests/test_tray_ui.py` - Unit tests for TrayUI

**Dependencies:**
- `pystray>=0.19.0` (already in requirements.txt)
- `Pillow>=10.0.0` (already in requirements.txt)

---

## Original Description

Add system tray/menu bar integration so the application runs in the background with a tray icon instead of as a command-line application.

**Current**: Application runs as `example_app.py` command-line script
**Desired**: Application runs as background service with system tray icon

## User Story

As a user, I want the telemetry logger to run silently in the system tray so that:
- It doesn't clutter my taskbar/desktop
- I can easily see the status at a glance (idle/detecting/logging)
- I can start/stop/pause logging with simple menu clicks
- The app feels like a proper Windows application, not a script

## Requirements

### Must Have

1. **System Tray Icon**
   - Display icon in Windows system tray (or macOS menu bar)
   - Icon should indicate current state:
     - Gray/disabled: Not running or idle
     - Yellow/waiting: Detecting LMU process
     - Green/active: Actively logging telemetry

2. **Context Menu**
   - Right-click menu with basic controls:
     - "Start Logging" / "Stop Logging" (toggle)
     - "Pause Logging" / "Resume Logging" (toggle)
     - "Open Output Folder" (opens telemetry_output directory)
     - "Quit" (exit application)

3. **Status Display**
   - Show current state in menu or tooltip:
     - "Idle - Waiting for LMU"
     - "Detected - LMU running"
     - "Logging - Lap X, Y samples"
   - Update status in real-time

4. **Graceful Shutdown**
   - "Quit" menu item should:
     - Stop telemetry loop
     - Save any buffered data
     - Clean up resources
     - Exit cleanly

### Nice to Have

1. **Tooltip on Hover**
   - Show current status when hovering over tray icon
   - Example: "LMU Telemetry Logger - Logging Lap 5 (234 samples)"

2. **Double-Click Action**
   - Double-click tray icon to open settings or show status window

3. **Balloon Notifications** (Optional)
   - "Lap completed: 1:32.456" notification
   - "LMU detected - logging started" notification
   - "Error: Failed to save lap" notification

4. **Start with Windows** (Optional)
   - Menu option to enable/disable auto-start
   - Add registry entry for Windows startup

## Technical Implementation

### Libraries

- **pystray**: Already in `requirements.txt`, cross-platform system tray support
- **Pillow**: Already in `requirements.txt`, for icon images

### Architecture

```python
# New file: src/tray_ui.py

class TrayUI:
    """System tray UI for telemetry logger"""

    def __init__(self, telemetry_app):
        self.app = telemetry_app
        self.icon = None

    def create_icon(self):
        """Create tray icon with menu"""
        # Create icon image (or load from file)
        # Create menu with items
        # Return pystray.Icon object

    def start(self):
        """Start tray icon (blocking)"""
        # Run pystray icon.run()

    def update_status(self, status):
        """Update icon and tooltip based on status"""
        # Change icon color/image
        # Update tooltip text

    def on_start_stop(self):
        """Handle Start/Stop menu click"""

    def on_pause_resume(self):
        """Handle Pause/Resume menu click"""

    def on_open_folder(self):
        """Handle Open Output Folder menu click"""

    def on_quit(self):
        """Handle Quit menu click"""
```

### Integration Points

1. **Modify `example_app.py`** (or create new `tray_app.py`):
   - Create TrayUI instance
   - Pass TelemetryApp to TrayUI
   - Run tray icon (blocking) instead of loop

2. **Status Updates**:
   - TelemetryLoop calls `tray_ui.update_status()` on state changes
   - Update from: IDLE → DETECTED → LOGGING → lap complete

3. **Threading**:
   - Telemetry loop runs in background thread
   - Tray icon runs in main thread (required by pystray)

### Icon States

Create 3 icon images (or use colored dots):
- **idle.png**: Gray icon (16x16, 32x32)
- **detecting.png**: Yellow icon
- **logging.png**: Green icon

Or generate programmatically using Pillow:
```python
from PIL import Image, ImageDraw

def create_icon(color):
    img = Image.new('RGB', (64, 64), color='white')
    draw = ImageDraw.Draw(img)
    draw.ellipse([8, 8, 56, 56], fill=color)
    return img
```

## Testing Requirements

### Manual Testing

1. **Windows**:
   - Run app, verify icon appears in system tray
   - Right-click, verify menu shows correctly
   - Test Start/Stop/Pause/Resume
   - Test "Open Output Folder"
   - Test "Quit" - verify clean shutdown

2. **macOS** (if supporting):
   - Same tests but in menu bar
   - Verify icon adapts to light/dark mode

### Automated Testing

- Unit tests for TrayUI class (mock pystray)
- Integration test: create tray icon, verify menu structure
- Test status updates without actually showing UI

## Dependencies

- **Already in requirements.txt**:
  - `pystray>=0.19.0`
  - `Pillow>=10.0.0`

- **New (if needed)**:
  - None

## Files to Create

- `src/tray_ui.py` - Main system tray UI class
- `icons/idle.png` - Gray icon (or generate programmatically)
- `icons/detecting.png` - Yellow icon
- `icons/logging.png` - Green icon
- `tray_app.py` - New entry point using tray UI (alternative to example_app.py)

## Files to Modify

- `example_app.py` - Add tray UI integration (or create new tray_app.py)
- `src/telemetry_loop.py` - Add status update callbacks (may already exist)
- `tests/test_tray_ui.py` - New test file

## Implementation Steps

1. **Create basic tray icon** (1-2 hours)
   - Create `src/tray_ui.py` with minimal pystray icon
   - Show icon with simple menu (Quit only)
   - Verify icon appears on Windows

2. **Add menu items** (2-3 hours)
   - Add Start/Stop, Pause/Resume, Open Folder
   - Wire up callbacks to TelemetryApp methods
   - Test each menu item

3. **Implement status updates** (2-3 hours)
   - Create icon images for each state
   - Implement `update_status()` method
   - Connect to TelemetryLoop state changes
   - Test status transitions

4. **Polish and test** (2-4 hours)
   - Add tooltips
   - Test on Windows
   - Test edge cases (LMU not installed, permission errors)
   - Write unit tests

## Acceptance Criteria

- [ ] Tray icon appears when app starts
- [ ] Icon color/image changes based on state (idle/detecting/logging)
- [ ] Right-click menu shows all required items
- [ ] Start/Stop menu item toggles logging
- [ ] Pause/Resume menu item works correctly
- [ ] "Open Output Folder" opens correct directory
- [ ] "Quit" stops app cleanly (saves buffered data)
- [ ] Tooltip shows current status
- [ ] No console window when running (packaged as .exe)
- [ ] All existing functionality still works

## Notes

- **Independent of Settings UI**: This feature does NOT include a settings dialog. It provides basic controls only. Configuration would be handled separately (see `feature_settings_ui.md`)
- **Cross-platform**: pystray supports Windows, macOS, and Linux
- **PyInstaller**: Ensure icons are bundled correctly in .exe
- **No console**: Use `pythonw.exe` or `--windowed` flag to hide console window

## Related Issues

- `feature_settings_ui.md` - Settings dialog (could add "Settings..." menu item)
- `feature_auto_update.md` - Auto-update (could add update check on startup)
- Phase 5 in `CLAUDE.md` - This is one component of Phase 5
