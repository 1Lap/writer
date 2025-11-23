# Bug Tracking Index

This file contains an index of all active bugs and feature requests. Each issue has been documented in detail in a separate file.

## Active Bugs

### High Priority

- **[Dialog Window Locking](dialog_window_locking.md)** - Settings and update dialogs can't be dismissed, locking up the application
- **[REST API Game Stuttering](rest_api_game_stuttering.md)** - REST API calls during lap completion cause game stuttering; need to cache track map on session start

### Medium Priority

- **[Branding and Icon Improvements](branding_icon_improvements.md)** - Application and system tray icons need professional design
- **[Update UI Button Height](update_ui_button_height.md)** - ✅ RESOLVED - Buttons in update dialog were too small
- **[Update Check Failure](update_check_failure.md)** - Update check mechanism needs investigation
- **[Read-only Program Files Permissions](readonly_program_files_permissions.md)** - Installer permissions issues with Program Files directory

### Low Priority

- **[FileManager Startup Directory Creation](filemanager_startup_directory_creation.md)** - Output directory creation on startup
- **[Terminal Window on Startup](terminal_window_on_startup.md)** - Console window appears when launching executable
- **[Updater Arguments Error](updater_arguments_error.md)** - Updater script argument handling issues

## Feature Requests

### Low Priority

- **[Open Viewer Menu Option](open_viewer_menu_option.md)** - Add menu item to open web viewer (https://1lap.github.io/viewer/)
- **[Capture Car Setups](capture_car_setups.md)** - Include car setup data in telemetry export

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
