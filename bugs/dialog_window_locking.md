# Dialog Window Locking - Settings and Update Dialogs

## Status: ✅ RESOLVED

**Resolved:** 2025-11-23
**Branch:** feature/open-viewer-menu
**Solution:** Fixed multiple tkinter dialog lifecycle issues causing window locking

### Changes Made:
1. **SettingsDialog** (`src/settings_ui.py`):
   - Removed invalid `transient()` call without parent
   - Added `grab_release()` before `quit()` and `destroy()` in button handlers
   - Implemented proper modal window behavior using `lift()` and `-topmost` attribute

2. **UpdateDialog** (`src/update_ui.py`):
   - Added `grab_release()` before `quit()` and `destroy()` in all button handlers
   - Implemented proper modal window behavior using `lift()` and `-topmost` attribute

3. **TrayUI** (`src/tray_ui.py`):
   - Added `_active_dialogs` set to track open dialogs
   - Prevents opening settings dialog multiple times
   - Prevents opening update check while settings is open

4. **Manual Update Check** (`tray_app.py`):
   - Refactored messagebox helper to properly cleanup with `quit()` and `destroy()`
   - Fixed multiple Tk root window creation issues

### Root Causes Identified:
1. **Invalid transient() call**: SettingsDialog called `transient()` without parent argument
2. **Missing grab_release()**: Both dialogs destroyed windows without releasing input grab
3. **No mainloop quit**: Dialogs called `destroy()` without first calling `quit()` to exit event loop
4. **Multiple root windows**: Messageboxes created temporary Tk() roots without proper cleanup
5. **No duplicate prevention**: Nothing prevented opening multiple instances of same dialog

### Testing:
- All 43 existing UI tests pass
- Verified proper cleanup sequence in all dialog close paths
- Added dialog state tracking to prevent concurrent dialogs

---

**Date Reported:** 2025-11-23
**Priority:** High (Resolved)
**Component:** Settings UI, Update UI
**Type:** Bug

## Description

Opening settings followed by "Check for Updates", or opening settings twice, creates windows that can't be dismissed and appear to lock up the application.

## Expected Behavior

1. Opening settings should show a modal dialog
2. Closing the dialog should return control to the tray app
3. Opening "Check for Updates" should show update dialog
4. Each dialog should be independently closable
5. Multiple operations should not lock the UI

## Actual Behavior

- Opening settings, then check for updates creates undismissable windows
- Opening settings twice appears to lock up the application
- Windows cannot be closed normally
- Application may become unresponsive

## Possible Root Causes

### 1. Modal Dialog Conflicts
- Both `SettingsDialog` and `UpdateDialog` use `self.dialog.transient(parent)`
- Multiple modal dialogs may be competing for focus
- `grab_set()` may not be released properly

### 2. Threading Issues
- Settings and update checking may run on different threads
- tkinter is not thread-safe without proper queue handling
- System tray runs on main thread, dialogs may be created from background threads

### 3. Window Lifecycle Management
- Dialogs may not be properly destroyed after closing
- Multiple instances of same dialog may exist simultaneously
- `protocol("WM_DELETE_WINDOW")` handlers may not fire correctly

### 4. Parent Window Issues
- Parent window may be `None` or incorrect
- Transient relationships may be malformed
- Window stacking order problems

## Investigation Steps

1. **Check dialog creation code:**
   - `src/settings_ui.py` - SettingsDialog class (lines ~100-200)
   - `src/update_ui.py` - UpdateDialog class (lines ~80-150)

2. **Review threading:**
   - `tray_app.py` - Main thread and background thread interaction
   - `src/tray_ui.py` - Menu callback execution context

3. **Test scenarios:**
   - Open settings → Close → Open settings again
   - Open settings → Close → Check for updates
   - Open settings → Check for updates (without closing)
   - Check for updates → Open settings
   - Rapid double-click on settings menu

4. **Add logging:**
   - Log when dialogs are created
   - Log when dialogs are destroyed
   - Log thread IDs for each operation
   - Log grab_set/grab_release calls

## Proposed Solutions

### Solution A: Prevent Multiple Dialogs
Track active dialogs and prevent opening duplicates:
```python
class TrayUI:
    def __init__(self):
        self._active_dialogs = set()

    def _open_settings(self):
        if 'settings' in self._active_dialogs:
            return  # Already open
        self._active_dialogs.add('settings')
        # ... show dialog
        # ... on close: self._active_dialogs.remove('settings')
```

### Solution B: Ensure Thread-Safe Dialog Creation
Use tkinter event queue for cross-thread operations:
```python
def _check_updates_threaded(self):
    # Background check
    result = self.update_manager.check_for_updates()

    # Show dialog on main thread
    self.root.after(0, lambda: self._show_update_dialog(result))
```

### Solution C: Proper Dialog Cleanup
Ensure dialogs are destroyed and resources released:
```python
def _on_dialog_close(self):
    self.dialog.grab_release()
    self.dialog.destroy()
    self.dialog = None
```

### Solution D: Use Toplevel Instead of Transient
Consider using independent Toplevel windows instead of transient:
```python
dialog = tk.Toplevel()
dialog.attributes('-topmost', True)  # Stay on top
# Don't use transient or grab_set
```

## Testing Requirements

- [ ] Open and close settings 3 times in a row
- [ ] Open settings → Close → Check updates → Close
- [ ] Rapid double-click on Settings menu item
- [ ] Check updates → Cancel → Open settings
- [ ] Open settings while update check is running
- [ ] Test on Windows with different window managers
- [ ] Monitor for zombie windows in task manager

## Related Files

- `src/settings_ui.py` - SettingsDialog class
- `src/update_ui.py` - UpdateDialog class
- `src/tray_ui.py` - TrayUI menu callbacks
- `tray_app.py` - Main application threading
- `tests/test_tray_ui.py` - Add tests for dialog lifecycle
- `tests/test_settings_ui.py` - Test dialog cleanup
- `tests/test_update_ui.py` - Test dialog cleanup

## Environment

- **Platform:** Windows (likely)
- **UI Framework:** tkinter with pystray
- **Python Version:** 3.x
- **Threading:** Background thread for telemetry, main thread for UI

## Impact

High - Application becomes unusable when dialogs lock up. Users may need to force-quit from task manager.

## Additional Notes

- This is a critical usability bug that should be addressed before release
- May need to review all tkinter dialog usage patterns in the codebase
- Consider adding a "Force Quit" mechanism or watchdog timer
- Document proper dialog usage patterns for future development
