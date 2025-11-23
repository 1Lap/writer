# Open Viewer Menu Option - Feature Request

**Date Reported:** 2025-11-23
**Priority:** Low
**Component:** System Tray UI
**Type:** Enhancement

## Description

Add a menu option to the system tray that opens the 1Lap web viewer (https://1lap.github.io/viewer/) in the default browser.

## Expected Behavior

When user clicks "Open Viewer" in the system tray menu:
1. Default web browser should open
2. Navigate to https://1lap.github.io/viewer/
3. User can view their telemetry data in the web interface

## Proposed Implementation

### Menu Addition
Add a new menu item to `TrayUI` in `src/tray_ui.py`:
- Label: "Open Viewer"
- Position: Between "Open Output Folder" and "Settings"
- Action: Open URL in default browser

### Code Changes

**File:** `src/tray_ui.py`

Add method to handle opening viewer:
```python
def _open_viewer(self):
    """Open the 1Lap web viewer in default browser."""
    import webbrowser
    webbrowser.open('https://1lap.github.io/viewer/')
```

Update menu creation to include new item:
```python
pystray.MenuItem('Open Viewer', self._open_viewer),
```

### Platform Compatibility

The `webbrowser` module is cross-platform and works on:
- Windows (uses default browser registry)
- macOS (uses `open` command)
- Linux (uses xdg-open or fallback)

## Testing Requirements

- [ ] Menu item appears in system tray
- [ ] Clicking opens default browser
- [ ] URL navigates to viewer correctly
- [ ] Works on Windows
- [ ] Works on macOS (if testing available)
- [ ] No errors if browser fails to open (graceful fallback)

## Related Files

- `src/tray_ui.py` - TrayUI class and menu creation
- `tests/test_tray_ui.py` - Add test for open viewer action

## Impact

Low - Nice-to-have feature that improves user experience by providing quick access to the web viewer.

## Additional Notes

- Consider adding error handling if browser fails to open
- Could show a brief notification "Opening viewer..." (optional)
- Future enhancement: Could pass session ID or file path as URL parameter for direct loading
