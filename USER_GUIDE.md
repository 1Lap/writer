# LMU Telemetry Logger - User Guide

## What is this?

This is a background telemetry logger for **Le Mans Ultimate (LMU)** that automatically captures and saves your telemetry data to CSV files.

## Features

- ✅ Automatically detects when LMU is running
- ✅ Captures telemetry at ~20Hz while you drive
- ✅ Saves complete lap data to CSV when you cross the finish line
- ✅ No configuration needed - just run and drive!

## Requirements

- Windows 10/11
- Le Mans Ultimate installed
- The telemetry plugin must be enabled in LMU (see Setup section)

## Quick Start

### 1. Enable LMU Telemetry Plugin

Before first use, you need to enable LMU's shared memory plugin:

1. Navigate to: `C:\Users\<YourName>\Documents\Studio 397\UserData\<YourPlayerName>\`
2. Open `CustomPluginVariables.JSON` in a text editor
3. Find the rF2SharedMemoryMapPlugin section
4. Change `"Enabled"` from `0` to `1`
5. Save the file

**Example:**
```json
{
  "rF2SharedMemoryMapPlugin": {
    "Enabled": 1
  }
}
```

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

Each CSV file contains:
- **Player info**: Your name, session ID
- **Lap summary**: Lap time, sector times, track/car info
- **Session data**: Track temperature, weather, etc.
- **Car setup**: Wing settings, tire pressures (where available)
- **Telemetry samples**: Detailed data captured ~20 times per second:
  - Speed, RPM, throttle, brake, steering
  - Tire temperatures, brake temperatures, tire wear
  - Suspension position, G-forces
  - Position coordinates (X, Y, Z)
  - And 100+ more fields!

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
3. Try loading into a track/session (not just the main menu)
4. Restart LMU after enabling the plugin

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

### CSV files are huge

**Answer**: This is normal! A 2-minute lap can generate:
- ~2,400 samples (at 20Hz)
- 100+ fields per sample
- Result: 10-15 MB per lap

This gives you extremely detailed telemetry data for analysis.

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

- **Capture rate is ~20Hz** instead of the target 100Hz
  - Impact: Slightly lower resolution data
  - Still perfectly usable for lap analysis
  - Fix planned for future versions

- **Some fields show zeros**:
  - Oil pressure, wind data not available from game
  - Car setup data partially unavailable
  - This is a limitation of LMU's shared memory

## Support

For issues or questions:
1. Check this guide first
2. Check `BUGS.md` for known issues
3. Check the project repository for updates

## Version

Current Version: 1.0 (Phase 6 - Windows Testing Complete)

Built with: Python 3.13, pyRfactor2SharedMemory

---

**Happy racing and data analyzing!** 🏁📊
