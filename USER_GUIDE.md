# LMU Telemetry Logger - User Guide

## What is this?

This is a background telemetry logger for **Le Mans Ultimate (LMU)** that automatically captures and saves your telemetry data to CSV files.

## Features

- ✅ Automatically detects when LMU is running
- ✅ Captures telemetry at ~43Hz while you drive
- ✅ Saves complete lap data to CSV when you cross the finish line
- ✅ MVP format output (12 essential channels, ~1MB per lap)
- ✅ Compatible with browser-based telemetry viewers
- ✅ No configuration needed - just enable the plugin and drive!

## Requirements

- Windows 10/11
- Le Mans Ultimate installed
- **Visual C++ Runtimes installed** (see below)
- The telemetry plugin must be enabled in LMU (see Setup section)

### Installing LMU Runtime Dependencies

⚠️ **Important**: The telemetry logger requires Visual C++ runtimes to access LMU's shared memory. These runtimes ship with LMU but need to be installed separately.

**Steps:**

1. Navigate to your LMU installation folder (default: `C:\Program Files (x86)\Steam\steamapps\common\Le Mans Ultimate\`)
2. Open the `support\runtimes\` folder
3. Install **all** the runtime installers in this folder:
   - `vc_redist.x64.exe` (Visual C++ Redistributable)
   - Any other runtime installers present
4. Follow the installation prompts for each installer
5. **Restart your computer** after installation (recommended)

**Note**: You only need to do this once. If you've already run LMU successfully, these runtimes may already be installed.

## Quick Start

### 1. Enable LMU Telemetry Plugin (First Time Only)

⚠️ **Important**: The rF2SharedMemoryMapPlugin is already installed with LMU, but you need to enable it once.

**Steps:**

1. Navigate to: `C:\Users\<YourName>\Documents\Studio 397\UserData\<YourPlayerName>\`
2. Open `CustomPluginVariables.JSON` in a text editor (Notepad works fine)
3. Find the `"rF2SharedMemoryMapPlugin"` section
4. Change `"Enabled"` from `0` to `1`
5. Save the file and close the editor
6. **Restart LMU** if it's already running

**Example (what to look for in the file):**
```json
{
  "rF2SharedMemoryMapPlugin": {
    "Enabled": 1    ← Change this from 0 to 1
  }
}
```

**Note**: You only need to do this once. The setting persists across LMU sessions.

### 2. Run the Logger

1. **Start LMU** and load into a practice session
2. **Run `LMU_Telemetry_Logger.exe`**
3. You'll see a console window showing the logger status
4. **Drive your laps** - the logger will automatically capture data
5. **Check the output** - CSV files are saved to `telemetry_output/` folder

### 3. Stop the Logger

- Press `Ctrl+C` in the console window to stop
- Or just close the window

## Output Files

CSV files are saved with the naming format:
```
telemetry_output/<SessionID>_lap<LapNumber>.csv
```

Example: `20251118083646537645_lap3.csv`

### What's in the CSV?

Each CSV file uses the **LMUTelemetry v2 MVP format**:

**Metadata section:**
- Player name, track name, car name
- Session timestamp (UTC)
- Lap time and track length
- Format version (for compatibility)

**Telemetry data (12 essential channels):**
Captured ~43 times per second:
- **LapDistance [m]** - Distance around the lap
- **LapTime [s]** - Time into the lap
- **Sector [int]** - Current sector (0-3)
- **Speed [km/h]** - Vehicle speed
- **EngineRevs [rpm]** - Engine RPM
- **ThrottlePercentage [%]** - Throttle input (0-100%)
- **BrakePercentage [%]** - Brake input (0-100%)
- **Steer [%]** - Steering input (-100 to +100%)
- **Gear [int]** - Current gear
- **X, Y, Z [m]** - Position coordinates

## Understanding the Console Output

The logger shows real-time status updates:

```
[logging] Process: YES | Telemetry: YES | Lap: 2 | Samples: 1543
```

- **Process**: Whether LMU is detected
- **Telemetry**: Whether shared memory is available
- **Lap**: Current lap number
- **Samples**: Number of telemetry samples collected for current lap

When you complete a lap:
```
*** Lap 2 completed!
    Lap time: 94.532s
    Samples: 1893
    [OK] Saved to: telemetry_output/20251118083646537645_lap2.csv
```

## Troubleshooting

### "Shared memory not available"

**Problem**: The logger can't connect to LMU's telemetry.

**Solutions**:
1. Make sure LMU is actually running
2. Check that you've enabled the plugin (see Setup section above)
3. **Install the LMU runtimes** (see Requirements section above) - this is the most common cause
4. Try loading into a track/session (not just the main menu)
5. Restart LMU after enabling the plugin

### "Failed to load shared memory library" or DLL errors

**Problem**: The pyRfactor2SharedMemory library can't load.

**Solutions**:
1. **Install the LMU runtimes** from `LMU/support/runtimes/` (see Requirements section)
2. Make sure you installed the x64 version of the Visual C++ Redistributable
3. Restart your computer after installing runtimes
4. Verify LMU itself runs properly (if LMU doesn't work, the logger won't either)

### "Process: NO"

**Problem**: Logger can't find LMU.

**Solutions**:
1. Make sure LMU.exe is actually running
2. Check Task Manager to verify "Le Mans Ultimate.exe" is there
3. Try restarting the logger

### No CSV files being created

**Problem**: Laps aren't being saved.

**Solutions**:
1. Make sure you're completing full laps (crossing start/finish)
2. Check the console for error messages
3. Verify the `telemetry_output/` folder exists

### CSV file size

**Answer**: A typical 5-minute lap generates:
- ~13,000 samples (at 43Hz)
- 12 channels per sample
- Result: ~1 MB per lap

This is the MVP format - streamlined for browser-based analysis while maintaining all essential telemetry data.

## Tips

- **One logger per session**: Don't run multiple instances
- **Let it run**: Keep the logger running for your entire session
- **Review later**: Analyze the CSV files after your session
- **Import to Excel/MoTeC**: The CSV format is compatible with most analysis tools

## Analyzing Your Data

The CSV files can be imported into:
- **Microsoft Excel**: For basic analysis and charts
- **MoTeC i2**: Professional telemetry analysis software
- **Python/pandas**: For custom analysis scripts
- **Any tool that reads CSV files**

### Recommended Fields for Analysis

- **Speed vs Distance**: See your speed trace around the lap
- **Brake/Throttle vs Distance**: Analyze your braking points
- **Tire Temps**: Monitor tire temperature evolution
- **G-Forces**: Understand cornering forces
- **Steering Angle**: Review your inputs

## Known Issues

- **Track length shows 0.00**:
  - Currently not extracted from shared memory
  - Doesn't affect viewer compatibility (optional field)
  - Fix planned for future versions

## Performance Notes

- **Capture rate is ~43Hz**
  - This is **working as expected** and is not a bug
  - The rF2SharedMemoryMapPlugin updates at 50Hz maximum
  - We're achieving **86% of the maximum possible rate** (43/50 Hz)
  - More than sufficient for all sim racing telemetry analysis
  - Performance has improved 2.1x from initial versions

## Support

For issues or questions:
1. Check this guide first
2. Check `BUGS.md` for known issues
3. Check the project repository for updates

## Version

**Current Version**: v0.1.1 - MVP Format Release

**Changes in this version:**
- LMUTelemetry v2 MVP format (12 channels)
- 43Hz capture rate (2.1x improvement)
- ~1MB per lap (down from ~11MB)
- Compatible with browser-based telemetry viewers
- 60/60 tests passing
- Tested on Windows with live LMU

**Built with**: Python 3.13, pyRfactor2SharedMemory

---

**Happy racing and data analyzing!** 🏁📊
