# Bug Tracking Index

This file contains an index of all active bugs and feature requests. Each issue has been documented in detail in a separate file.

## Active Issues

### Enhancement Requests

- **[Branding and Icon Improvements](branding_icon_improvements.md)** - Application and system tray icons need professional design

### Low Priority

- **[FileManager Startup Directory Creation](filemanager_startup_directory_creation.md)** - Output directory creation on startup (low impact)

### Won't Implement

- **[Capture Car Setups](capture_car_setups.md)** - Opponent setups not available via API; player setups have limited value

## Recently Resolved (2025-11-21 to 2025-11-23)

The following bugs have been resolved and their detailed files have been removed:

- **Dialog Window Locking** - Fixed tkinter dialog lifecycle issues (v0.3.2+)
- **REST API Game Stuttering** - Moved API calls to session start instead of lap completion (v0.3.2+)
- **Open Viewer Menu Option** - Added menu item to open web viewer (v0.3.2+)
- **Update UI Button Height** - Fixed button padding in update dialog (v0.3.1+)
- **Update Check Failure** - Added user feedback for manual update checks (v0.3.1+)
- **Updater Arguments Error** - Built updater as separate .exe (v0.3.1+)
- **Terminal Window on Startup** - Confirmed --noconsole flag in build.bat (v0.3.1+)
- **Read-only Program Files Permissions** - Moved config/logs to AppData (v0.3.1)

---

## Bug File Organization

Each bug file follows this structure:
- **Status** - Open or Resolved (with resolution details)
- **Priority** - High, Medium, or Low
- **Description** - What the bug is
- **Expected vs Actual Behavior**
- **Root Cause Analysis**
- **Proposed Solutions**
- **Testing Requirements**
- **Related Files**
- **Impact Assessment**

## How to Use This Index

1. **Reporting a new bug**: Create a new file in `bugs/` following the template from existing files
2. **Updating a bug**: Edit the individual bug file with new findings
3. **Resolving a bug**: Add resolution status to the top of the bug file (see [update_ui_button_height.md](update_ui_button_height.md) for example)
4. **Finding bugs**: Use this index to locate the detailed bug file

## Notes

- **Resolved bugs** are kept for historical reference
- All bugs should have corresponding test cases when fixed
- See `CLAUDE.md` for bug workflow and git commit guidelines
