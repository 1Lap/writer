# Bug: Missing LMU Runtime Installation Instructions

**Status**: FIXED ✅
**Priority**: High (prevents telemetry from working)
**Fixed**: 2025-11-20

---

## Original Issue

Installation instructions should mention that LMU ships with "support/runtimes/" and those all need to be installed for pyRfactor2SharedMemory to work.

## Resolution

**Files Updated**:

1. **USER_GUIDE.md**:
   - Added "Installing LMU Runtime Dependencies" section in Requirements
   - Added detailed steps to install Visual C++ runtimes from LMU's `support/runtimes/` folder
   - Added troubleshooting entries for "Failed to load shared memory library" errors
   - Updated existing troubleshooting to mention runtime installation as primary solution

2. **WINDOWS_SETUP.md**:
   - Added runtime installation to Prerequisites section
   - Added step-by-step instructions for developers
   - Updated Common Issues section to mention runtime installation

**What Users Need to Do**:

1. Navigate to: `C:\Program Files (x86)\Steam\steamapps\common\Le Mans Ultimate\support\runtimes\`
2. Install all runtime installers (especially `vc_redist.x64.exe`)
3. Restart computer (recommended)

**Result**:
- ✅ Clear installation instructions for end users
- ✅ Developer setup guide updated
- ✅ Troubleshooting guidance added
- ✅ Prevents "shared memory not available" errors due to missing runtimes
