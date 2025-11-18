# LMU Telemetry Logger Implementation Plan (REVISED)

## Overview
Build a telemetry logger for Le Mans Ultimate that captures real-time game data and exports it to CSV files matching the MVP schema defined in `telemetry_format_analysis.md` (metadata preamble + 12 canonical channels).

**Key Change**: Leverage existing open-source projects to significantly reduce development time from 2-3 weeks to **3-5 days**.

## Architecture

### Components
1. **rF2SharedMemoryMapPlugin** - ✅ Already installed with LMU, just needs enabling
2. **pyRfactor2SharedMemory** - Python library for reading shared memory (open source)
3. **Logger Service (Python)** - Background service that runs continuously
   - Auto-detects when LMU is running
   - Reads telemetry from shared memory
   - Buffers and writes CSV files
4. **CSV Formatter** - Converts raw telemetry to the LMUTelemetry v2 MVP format
5. **File Manager** - Handles CSV file creation and management
6. **System Tray UI (Optional)** - Simple control interface
   - Shows logging status
   - Start/Stop/Configure options
7. **PyInstaller Package** - Single `.exe` deployment, no Python installation needed

### Existing Projects to Leverage

1. **rF2SharedMemoryMapPlugin** by TheIronWolfModding
   - GitHub: https://github.com/TheIronWolfModding/rF2SharedMemoryMapPlugin
   - Already bundled with LMU, located in `Le Mans Ultimate\Plugins\`
   - Exposes all telemetry data to shared memory
   - Just needs to be enabled in `CustomPluginVariables.JSON`

2. **pyRfactor2SharedMemory** by TonyWhitley
   - GitHub: https://github.com/TonyWhitley/pyRfactor2SharedMemory
   - Python library for reading rF2 shared memory
   - Handles low-level memory mapping and data structures
   - Can be installed via pip or used as reference

3. **TinyPedal** (Reference Implementation)
   - GitHub: https://github.com/TinyPedal/TinyPedal
   - LMU Fork: https://github.com/IceNbrn/TinyPedal_LMU
   - Open source (GPL v3) telemetry overlay for LMU
   - Excellent reference for:
     - Session state detection logic
     - Data field mappings
     - Handling LMU-specific quirks

## What Changed From Original Plan?

**Before**: Build everything from scratch (2-3 weeks)
- Write C++ plugin to extract telemetry
- Implement shared memory communication
- Write Python service to read and format data

**After**: Leverage existing tools (3-5 days)
- ✅ Plugin already exists and is installed
- ✅ Python library already handles shared memory
- ✅ Reference implementations available
- **Focus only on**: CSV formatting, session management, file writing, user experience

## Target User Experience

### Zero-Config Setup (Goal)
1. User downloads `LMU_Telemetry_Logger.exe`
2. Double-click to run - service starts in background
3. System tray icon appears showing "Idle" status
4. User launches LMU and starts driving
5. Service auto-detects LMU and begins logging
6. CSV files automatically saved to `Documents/LMU/Telemetry/`
7. When LMU closes, service returns to idle state

### Optional Configuration
- Right-click tray icon → Settings
- Edit simple `config.json` file:
  - Output directory path
  - Auto-start with Windows (yes/no)
  - Logging enabled by default (yes/no)

### User Requirements
- **None** - Single `.exe` file, no Python installation
- Windows 10/11
- Le Mans Ultimate installed with plugin enabled

---

## Summary of Approach

### Key Features
✅ **Zero Installation** - Single `.exe` file, no dependencies
✅ **Auto-Detection** - Automatically starts/stops with LMU
✅ **Background Service** - Runs silently, no intervention needed
✅ **System Tray Control** - Easy status monitoring and control
✅ **Auto-Start** - Optional Windows startup integration
✅ **CSV Format** - Matches LMUTelemetry v2 MVP structure
✅ **Cross-Platform Dev** - Develop on macOS, build/test on Windows

### Technical Stack
- **Language**: Python 3.8+ (compiled to .exe)
- **Plugin**: rF2SharedMemoryMapPlugin (already in LMU)
- **Telemetry API**: pyRfactor2SharedMemory library (Windows only)
- **UI**: pystray (cross-platform: macOS menu bar / Windows system tray)
- **Packaging**: PyInstaller (single executable)
- **Testing**: pytest with mock data (cross-platform)

### Development Time
- **Original estimate** (from scratch): 2-3 weeks
- **Revised estimate** (leveraging existing tools): **4-6 days**
- **Time saved**: ~10 days by using existing plugin and libraries

### Development Environment
- **Primary development**: macOS (Days 1-4)
- **Final testing/build**: Windows (Days 5-6)
- **~90% of code** can be written and tested on macOS using mocks

---

## Cross-Platform Development Strategy

### Overview
Develop **90% of the application on macOS** using mock telemetry data, then move to Windows only for final testing and executable building.

### What Works on macOS
✅ All business logic (CSV formatting, session management, file I/O)
✅ System tray UI (appears in macOS menu bar)
✅ Process monitoring (psutil works on both platforms)
✅ Configuration management
✅ Unit and integration tests with mock data
✅ All Python development and debugging

### What Requires Windows
⚠️ Reading actual shared memory (Windows memory-mapped files)
⚠️ Testing with real LMU game
⚠️ Building final `.exe` with PyInstaller (Windows target)
⚠️ Validating system tray in Windows taskbar

### Platform Detection Pattern

```python
# src/telemetry/telemetry_interface.py
import sys

class TelemetryReader:
    def __init__(self):
        if sys.platform == 'win32':
            from .telemetry_real import RealTelemetryReader
            self.reader = RealTelemetryReader()
        else:  # macOS/Linux - use mock for development
            from .telemetry_mock import MockTelemetryReader
            self.reader = MockTelemetryReader()

    def read(self):
        return self.reader.read()
```

### Development Workflow

```
┌─── macOS Development (Days 1-4) ───┐
│ 1. Write code with mock telemetry  │
│ 2. Write comprehensive tests        │
│ 3. Test in macOS menu bar          │
│ 4. Commit to git                   │
└────────────────────────────────────┘
              │
              ▼
┌─── Windows Testing (Days 5-6) ─────┐
│ 1. Clone repo on Windows           │
│ 2. Switch to real telemetry        │
│ 3. Test with LMU                   │
│ 4. Build .exe with PyInstaller     │
│ 5. Final validation                │
└────────────────────────────────────┘
```

### Mock Data Strategy

The mock telemetry system will:
- Study `telemetry_format_analysis.md` to understand the metadata + 12-column layout
- Generate realistic values that change over time
- Simulate lap progression (lap distance incrementing)
- Trigger lap completion events
- Support multiple session types (Practice, Race, etc.)

### Example Mock Implementation

```python
# src/telemetry/telemetry_mock.py
import time
import math
from datetime import datetime

class MockTelemetryReader:
    """Mock telemetry for macOS development"""

    def __init__(self):
        self.start_time = time.time()
        self.lap = 1
        self.lap_start_time = self.start_time
        self.track_length = 5386.80  # Bahrain from the LMU reference lap

    def read(self):
        """Return telemetry data matching rF2 structure"""
        elapsed = time.time() - self.lap_start_time

        # Simulate car progressing around track
        lap_distance = (elapsed * 70) % self.track_length  # ~70m/s avg
        total_distance = 91576.37 + (elapsed * 70)

        # Simulate speed variation (slower in corners)
        speed_variation = math.sin(lap_distance / 1000) * 20
        speed = 256 + speed_variation

        # Check for lap completion
        if lap_distance < 10 and elapsed > 5:
            self.lap += 1
            self.lap_start_time = time.time()

        return {
            # Player/Session info
            'player_name': 'Dev User',
            'track_name': 'Bahrain International Circuit',
            'car_name': 'Toyota GR010',
            'session_type': 'Practice',

            # Lap/Position
            'lap': self.lap,
            'lap_distance': lap_distance,
            'total_distance': total_distance,
            'lap_time': elapsed,

            # Physics
            'speed': speed,
            'rpm': 7267 + (speed_variation * 10),
            'gear': 6,
            'throttle': 1.0 if speed > 200 else 0.5,
            'brake': 0.0,

            # Position (simulate movement)
            'position_x': -269.26 + (lap_distance * 0.01),
            'position_y': 7.30,
            'position_z': -218.97 + (lap_distance * 0.01),

            # ... all other fields defined in telemetry_format_analysis.md
        }
```

---

## Phase 1: Setup & Cross-Platform Development Foundation

### 1.1 Development Environment Setup (macOS)
- **Tools needed**:
  - Python 3.8+ (for logger service)
  - Git
  - Code editor (VS Code recommended)
  - pytest for testing
- **Initial setup**:
  - Create project repository
  - Setup virtual environment (`python -m venv venv`)
  - Create `requirements.txt` and `requirements-dev.txt`
  - Initialize git repository

### 1.2 Create Mock Telemetry System (macOS Development)
- **Purpose**: Allows development without Windows/LMU
- **Tasks**:
  - Study `telemetry_format_analysis.md` to understand data structure
  - Review rF2SharedMemoryMapPlugin documentation for field mapping
  - Create `src/telemetry/mock_telemetry.py`:
    - Mock all fields from the MVP schema
    - Generate realistic values (speed, position, RPM, etc.)
    - Support multiple lap scenarios
    - Simulate session state changes
  - Create `src/telemetry/telemetry_interface.py`:
    - Abstract interface for telemetry reading
    - Platform detection (macOS vs Windows)
    - Conditional import of mock vs real telemetry

### 1.3 Project Structure
```
lmu-telemetry-logger/
├── src/
│   ├── telemetry/
│   │   ├── __init__.py
│   │   ├── telemetry_interface.py  # Abstract interface
│   │   ├── telemetry_mock.py       # macOS: mock data
│   │   └── telemetry_real.py       # Windows: pyRfactor2SharedMemory
│   ├── csv_formatter.py            # Cross-platform
│   ├── session_manager.py          # Cross-platform
│   ├── file_manager.py             # Cross-platform
│   ├── process_monitor.py          # Cross-platform (psutil)
│   ├── tray_ui.py                  # Cross-platform (pystray)
│   ├── config.py                   # Cross-platform
│   └── main.py                     # Entry point
├── tests/
│   ├── test_csv_formatter.py
│   ├── test_session_manager.py
│   ├── test_file_manager.py
│   └── mock_data/                  # Sample telemetry data
├── requirements.txt                # Production dependencies
├── requirements-dev.txt            # Dev dependencies
├── build.py                        # PyInstaller build script
└── README.md
```

### 1.4 Windows Setup (Later - Days 5-6)
- **Only needed for final testing and building**
- **Tasks**:
  - Install Python 3.8+ on Windows
  - Clone repository
  - Install `pyRfactor2SharedMemory`
  - Verify rF2SharedMemoryMapPlugin in LMU
  - Edit `CustomPluginVariables.JSON` to enable plugin

## Phase 2: Core Logger Service Development

### 2.1 Create Background Service with Auto-Detection
- **Technology**: Python 3.8+
- **Core features**:
  - **LMU Process Monitor**: Detect when LMU is running
    - Check for process name (e.g., "LMU.exe" or similar)
    - Monitor shared memory availability
    - State transitions: Idle → Detected → Logging → Idle
  - **Main service loop**:
    - Runs continuously in background
    - Low CPU usage when idle (sleep/wait)
    - Activates when LMU detected
  - **Telemetry collection**:
    - Use pyRfactor2SharedMemory to read shared memory
    - Poll at appropriate frequency (~100Hz when logging)
    - Buffer samples in memory
    - Detect session/lap changes
    - Trigger CSV file writes
- **Main components**:
  - Process monitor (psutil library)
  - Telemetry reader (using pyRfactor2SharedMemory)
  - Session state machine
  - Data buffer manager
  - CSV writer trigger

### 2.2 Session Management
- **State tracking**:
  - Detect new session start (reference TinyPedal for logic)
  - Track current lap number
  - Detect lap completion
  - Handle session end
- **File naming**: Generate unique filenames per session/lap
  - Pattern: `{player}_{track}_{date}_{session_id}.csv`
  - Match example: `player,v8,Dean Davids,0,2025111417168338`

### 2.3 Data Buffering
- **In-memory buffer**:
  - Store telemetry samples for current lap (list of dicts)
  - Store lap summary data
  - Store car setup data (from first sample)
  - Clear buffer after lap completion/write
  - Handle buffer overflow (circular buffer or max lap time limit)
- **Performance**: Optimize for ~100 samples/second

## Phase 3: CSV Formatter Implementation

### 3.1 Build CSV Writer
- **Format sections** (matching LMUTelemetry v2 MVP spec):
  1. Metadata preamble (Format/Version/Player/Track/Car/SessionUTC/LapTime/TrackLen + extras)
  2. Blank separator line
  3. Telemetry header for the 12 required channels
  4. Telemetry samples sorted by LapDistance [m]
- **Reference**: Study `telemetry_format_analysis.md` for exact header text and ordering

### 3.2 Data Mapping
- **Create mapping layer**:
  - Map pyRfactor2SharedMemory data fields to canonical headers (`LapDistance [m]`, `ThrottlePercentage [%]`, ...)
  - Handle unit conversions (m/s → km/h, 0–1 inputs → 0–100 %)
  - Enforce per-column precision rules (LapDistance/LapTime ≥3 decimals, inputs ≥2)
  - Emit blanks for missing coordinates (viewer reads them as nulls)
- **Reference TinyPedal** for field mappings

### 3.3 Field Calculations
- **Derived fields**:
  - Sector times (S1, S2, S3, S4+)
  - Total lap time
  - Total distance traveled
  - Lap distance (resets each lap)
  - Timestamp calculations

## Phase 4: File Management & Configuration

### 4.1 File Writing Strategy
- **Triggers**:
  - Write lap data when lap completes
  - Optional: Auto-save during long laps (every N seconds)
- **Output location**: Configurable directory
  - Default: `Documents/LMU/Telemetry/`
  - Create subdirectories by date or session if needed

### 4.2 Configuration File
- **Format**: JSON or config.ini
- **Settings**:
  - Output directory path
  - Sampling rate (default: match game ~100Hz)
  - Auto-save interval
  - File naming pattern
  - Enable/disable logging by default
  - Fields to include/exclude (optional)

### 4.3 Error Handling
- **Disk I/O**:
  - Handle disk full errors gracefully
  - Retry logic for write failures
  - Keep buffer in memory during errors
  - Log errors to file

### 4.4 Default Configuration Generation
- **First run**:
  - Auto-generate `config.json` with sensible defaults
  - Create output directory if it doesn't exist
  - Provide sample config with comments

## Phase 5: System Tray UI & User Controls

### 5.1 System Tray Icon (Optional but Recommended)
- **Library**: `pystray` (lightweight, cross-platform)
- **Features**:
  - Icon with status indicator:
    - Gray: Idle (LMU not running)
    - Green: Logging (actively recording)
    - Red: Error state
    - Yellow: Paused
  - Right-click context menu:
    - "Status: [Idle/Logging/Error]"
    - "Open Output Folder"
    - "Open Logs"
    - Separator
    - "Enable/Disable Logging"
    - "Settings" (opens config file)
    - Separator
    - "Add to Startup"
    - "Exit"
- **Notifications** (optional):
  - Toast notification when logging starts/stops
  - Error notifications

### 5.2 No-GUI Mode
- **Command-line option**: `--no-gui` flag
- Runs as pure background service (no tray icon)
- Useful for running as scheduled task or service

### 5.3 Auto-Start Integration
- **Menu option**: "Add to Startup"
- Creates shortcut in Windows Startup folder
- `%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup`

## Phase 6: Testing

### 6.1 Unit Tests (TDD Approach)
- **Test coverage**:
  - CSV formatter (each section independently)
  - Data mapping/conversions
  - Buffer management
  - Field calculations (sector times, distances)
  - File writing
  - Process detection logic
- **Write tests BEFORE implementing each component**
- **Tools**: pytest or unittest

### 6.2 Integration Tests
- **End-to-end tests**:
  - Shared Memory → Logger → CSV pipeline
  - Multiple lap scenarios
  - Session transitions (practice → race)
  - Error recovery (disk full, plugin disabled)
  - Service auto-detection and state transitions
- **Mock data**: Create mock shared memory data for testing without game
- **Process simulation**: Mock LMU process for testing detection

### 6.3 Live Testing
- **In-game testing**:
  - Practice sessions (single lap)
  - Race sessions (multiple laps)
  - Verify CSV output matches the LMUTelemetry v2 MVP format
  - Compare with existing telemetry tools for accuracy
  - Performance monitoring (CPU/memory usage should be minimal)
  - Test auto-start/stop behavior
  - Test system tray functionality

## Phase 7: Packaging & Deployment

### 7.1 PyInstaller Executable Build
- **Primary deployment method**: Single `.exe` file
- **PyInstaller configuration**:
  - `--onefile`: Single executable
  - `--windowed`: No console window (background service)
  - `--icon=lmu_logger.ico`: Custom icon for tray
  - Include data files: default config, README
  - Optimize size with UPX compression
- **Testing**:
  - Test on clean Windows machine (no Python installed)
  - Verify all dependencies bundled correctly
  - Test auto-detection and logging functionality
  - Verify system tray icon works

### 7.2 Documentation
- **User guide** (README.md):
  - **Quick Start** (for .exe users):
    - Download `LMU_Telemetry_Logger.exe`
    - Run the executable
    - (Optional) Configure output directory
    - Launch LMU and drive
  - **Advanced**:
    - Enabling rF2SharedMemoryMapPlugin in LMU (if not enabled)
    - Configuration file options
    - Running from Python source (for developers)
  - **Troubleshooting**:
    - Plugin not enabled
    - No telemetry detected
    - Output directory issues
- **Developer documentation** (CONTRIBUTING.md):
  - Setting up development environment
  - Code architecture
  - Adding new fields to CSV
  - Building from source
  - Contributing guidelines

### 7.3 Distribution Package
- **Release bundle includes**:
  - `LMU_Telemetry_Logger.exe` (main executable)
  - `README.md` (user guide)
  - `config.json.example` (example configuration)
  - `LICENSE` (if open-sourcing)
- **Distribution channels**:
  - GitHub Releases (recommended)
  - OverTake.gg forum (LMU community)
  - Optional: RaceDepartment
- **GitHub repository structure**:
  ```
  lmu-telemetry-logger/
  ├── src/               # Python source code
  ├── tests/             # Test suite
  ├── dist/              # Built executables
  ├── docs/              # Documentation
  ├── examples/          # Example CSV outputs
  ├── requirements.txt   # Python dependencies
  ├── build.py           # PyInstaller build script
  └── README.md          # Main documentation
  ```

## Technical Considerations

### Data Accuracy
- Ensure timestamp synchronization
- Handle data gaps gracefully
- Validate data ranges

### Performance
- Minimize CPU overhead in game
- Optimize memory usage
- Async file I/O to prevent game stuttering

### Compatibility
- Test with different LMU versions
- Handle API changes gracefully
- Support different cars/tracks

## Deliverables

1. ~~LMU plugin DLL~~ ✅ Already exists (rF2SharedMemoryMapPlugin)
2. **`LMU_Telemetry_Logger.exe`** - Single executable, no installation required
3. Python source code (for developers/contributors)
4. System tray UI with status indicators and controls
5. Configuration file template with defaults (`config.json`)
6. Comprehensive documentation:
   - User guide (Quick Start for .exe users)
   - Developer guide (building from source)
   - Troubleshooting guide
7. Test suite (unit + integration tests)
8. Example CSV outputs matching LMUTelemetry v2 MVP format

---

## Revised Timeline

**Estimated Implementation Time**: 4-6 days (reduced from 2-3 weeks)

### 🍎 macOS Development Phase (Days 1-4)

#### Day 1: Setup & Mock System (6-7 hours) - macOS
- **Phase 1.1**: Development environment setup (1 hour)
  - Python venv, git init, project structure
- **Phase 1.2**: Create mock telemetry system (3-4 hours)
  - Follow `telemetry_format_analysis.md` for the trimmed schema
  - Implement MockTelemetryReader with realistic data
  - Platform detection and abstraction layer
- **Phase 1.3**: Study references (2-3 hours)
  - Review TinyPedal code for session detection
  - Map telemetry fields to CSV columns

#### Day 2: Core Logger (7-8 hours) - macOS
- **Phase 2.1**: Background service with auto-detection (4-5 hours)
  - Process monitor (works with any process, test with Chrome/etc)
  - Main telemetry loop with mock data
  - State machine (Idle → Detected → Logging)
- **Phase 2.2-2.3**: Session management and buffering (2 hours)
- **Write unit tests** for all components (2 hours)

#### Day 3: CSV Formatter (7-8 hours) - macOS
- **Phase 3.1**: CSV writer implementation (4-5 hours)
  - Metadata block + 12-column rows per MVP spec
  - Test with mock data
- **Phase 3.2**: Data mapping layer (2 hours)
- **Phase 3.3**: Field calculations (sector times, distances) (2 hours)
- **Write comprehensive tests** (built into work above)

#### Day 4: UI & File Management (7-8 hours) - macOS
- **Phase 4**: File management, config, error handling (2-3 hours)
  - Default config generation
  - File writing with error handling
- **Phase 5**: System tray UI (4-5 hours)
  - macOS menu bar implementation (same API as Windows tray)
  - Status icons, menu, notifications
  - Test with mock process detection
- **Integration tests** with full pipeline (1-2 hours)

### 🪟 Windows Testing & Build Phase (Days 5-6)

#### Day 5: Windows Setup & Live Testing (7-8 hours) - Windows
- **Phase 1.4**: Windows environment setup (1 hour)
  - Clone repo, install dependencies
  - Install pyRfactor2SharedMemory
  - Enable rF2SharedMemoryMapPlugin in LMU
- **Phase 2**: Switch to real telemetry (1 hour)
  - Verify telemetry_real.py works
  - Test platform detection
- **Phase 6.3**: Live testing with LMU (5-6 hours)
  - Practice sessions (multiple laps)
  - Race sessions
  - Verify CSV output matches LMUTelemetry v2 MVP format
  - Test auto-detection, error handling
  - Performance monitoring

#### Day 6: Packaging & Documentation (6-7 hours) - Windows
- **Phase 7.1**: PyInstaller build (2-3 hours)
  - Build .exe with proper flags
  - Test on clean Windows machine
  - Verify system tray icon
  - Test auto-start functionality
- **Phase 7.2**: Documentation (3-4 hours)
  - README with Quick Start
  - User guide, troubleshooting
  - Developer guide (macOS + Windows setup)
- **Phase 7.3**: Final validation (1-2 hours)
  - End-to-end testing
  - Release package preparation

**Key Time Savings**:
- No C++ plugin development (saved ~5 days)
- Existing shared memory library (saved ~3 days)
- Reference implementation available (saved ~2 days)
- Cross-platform development (saved debugging time)

**Development Advantages**:
- ✅ Use preferred macOS development environment
- ✅ Fast iteration without VM/dual-boot overhead
- ✅ Comprehensive testing before Windows deployment
- ✅ Only need Windows for 2 days (final testing + build)
- ✅ All unit tests run on macOS CI/CD if needed

This plan follows a test-driven development approach with unit tests written before implementation, and integration tests validating the full pipeline before live game testing.

---

## Cross-Platform Development Summary

### Why This Approach Works

**Separation of Concerns:**
- Telemetry reading (platform-specific) is abstracted behind interface
- All business logic (CSV, session, files) is pure Python (cross-platform)
- System tray library (`pystray`) works identically on both platforms
- Tests use mock data, so they run anywhere

### What You Get

**On macOS (Days 1-4):**
- ✅ Full application development
- ✅ Complete test suite
- ✅ Working system tray UI in menu bar
- ✅ Verified CSV output with mock data
- ✅ All bugs caught early

**On Windows (Days 5-6):**
- ✅ Drop-in real telemetry (just swap mock for real)
- ✅ Live validation with LMU
- ✅ Final `.exe` build
- ✅ Minimal debugging (most bugs already fixed)

### Testing Process Monitor on macOS

Since `psutil` works on both platforms, you can test process detection on macOS by monitoring any application:

```python
# Test on macOS by detecting Chrome, VS Code, etc.
if psutil.process_iter(['name']):
    for proc in psutil.process_iter(['name']):
        if 'Chrome' in proc.info['name']:  # Use Chrome for testing
            print("Process detected!")
            # Your logging logic here
```

This lets you verify the auto-detection logic works before ever touching Windows!

---

## Resources & Links

### Essential
- **rF2SharedMemoryMapPlugin**: https://github.com/TheIronWolfModding/rF2SharedMemoryMapPlugin
- **pyRfactor2SharedMemory**: https://github.com/TonyWhitley/pyRfactor2SharedMemory
- **TinyPedal (Main)**: https://github.com/TinyPedal/TinyPedal
- **TinyPedal (LMU Fork)**: https://github.com/IceNbrn/TinyPedal_LMU

### References
- **C# Monitor Example**: Included in rF2SharedMemoryMapPlugin repo
- **rF2 Shared Memory Structure**: See rF2SharedMemoryMapPlugin documentation

### Community
- **OverTake.gg LMU Forum**: https://www.overtake.gg/forums/le-mans-ultimate.376/
- **LMU Community**: https://community.lemansultimate.com/

---

## Python Dependencies

### Cross-Platform Libraries (macOS + Windows)
```
# Core functionality
psutil>=5.9.0              # Process detection (both platforms)
pystray>=0.19.0            # System tray/menu bar (both platforms)
Pillow>=10.0.0             # Icon images for pystray (both platforms)

# Development/Testing
pytest>=7.4.0              # Testing framework
pytest-cov>=4.1.0          # Coverage reports
```

### Windows-Only Libraries
```
pyRfactor2SharedMemory     # Shared memory reading (Windows only)
pyinstaller>=6.0.0         # Build .exe (run on Windows)
```

### Standard Library (No Install Required)
- `csv` - CSV file writing
- `json` - Configuration files
- `datetime` - Timestamps
- `pathlib` - File path handling
- `threading` - Background service
- `time` - Sleep/delays
- `logging` - Error logging
- `os` - Environment variables, startup folder
- `sys` - Platform detection

### Optional Dependencies
- `win10toast` or `winotify` - Windows toast notifications (Windows only)

### requirements.txt (macOS Development)
```txt
# requirements.txt - for macOS development
psutil>=5.9.0
pystray>=0.19.0
Pillow>=10.0.0
```

### requirements-windows.txt (Windows Build)
```txt
# requirements-windows.txt - for Windows final build
psutil>=5.9.0
pystray>=0.19.0
Pillow>=10.0.0
pyRfactor2SharedMemory
pyinstaller>=6.0.0
```

### requirements-dev.txt (Development)
```txt
# requirements-dev.txt - testing/development
pytest>=7.4.0
pytest-cov>=4.1.0
black>=23.0.0              # Code formatting
flake8>=6.0.0              # Linting
```
