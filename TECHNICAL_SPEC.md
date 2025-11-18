# LMU Telemetry Logger - Technical Specification

**Version**: 1.0
**Last Updated**: 2025-01-17
**Status**: Draft for Implementation

---

## Table of Contents

1. [Component Specifications](#component-specifications)
2. [Data Schemas](#data-schemas)
3. [API Contracts](#api-contracts)
4. [Configuration Specification](#configuration-specification)
5. [Error Handling](#error-handling)
6. [Performance Requirements](#performance-requirements)
7. [Testing Requirements](#testing-requirements)
8. [Phase Acceptance Criteria](#phase-acceptance-criteria)

---

## Component Specifications

### 1. Telemetry Reader

#### Interface: `TelemetryReaderInterface`

```python
from abc import ABC, abstractmethod
from typing import Dict, Any

class TelemetryReaderInterface(ABC):
    """Abstract interface for telemetry reading"""

    @abstractmethod
    def is_available(self) -> bool:
        """Check if telemetry data is available"""
        pass

    @abstractmethod
    def read(self) -> Dict[str, Any]:
        """Read current telemetry data"""
        pass

    @abstractmethod
    def get_session_info(self) -> Dict[str, Any]:
        """Get session metadata (track, car, event type)"""
        pass
```

#### Implementation: `MockTelemetryReader` (macOS Development)

```python
class MockTelemetryReader(TelemetryReaderInterface):
    """Mock telemetry for development without LMU"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.start_time = time.time()
        self.lap = 1
        self.lap_start_time = self.start_time
        self.track_length = 5386.80  # Default: Bahrain

    def is_available(self) -> bool:
        return True  # Always available for testing

    def read(self) -> Dict[str, Any]:
        """Return mock telemetry matching rF2 structure"""
        # Implementation details in TELEMETRY_LOGGER_PLAN.md
        pass
```

#### Implementation: `RealTelemetryReader` (Windows Production)

```python
class RealTelemetryReader(TelemetryReaderInterface):
    """Real telemetry from pyRfactor2SharedMemory"""

    def __init__(self):
        import pyRfactor2SharedMemory as sm
        self.sm = sm
        self.shared_memory = None

    def is_available(self) -> bool:
        """Check if shared memory is accessible"""
        try:
            # Attempt to read shared memory
            data = self.sm.read_telemetry()
            return data is not None
        except Exception:
            return False

    def read(self) -> Dict[str, Any]:
        """Read from rF2 shared memory"""
        # Map rF2 shared memory to our telemetry dict format
        pass
```

---

### 2. Session Manager

```python
from enum import Enum
from typing import Optional, List

class SessionState(Enum):
    IDLE = "idle"
    DETECTED = "detected"
    LOGGING = "logging"
    PAUSED = "paused"
    ERROR = "error"

class SessionManager:
    """Manages session state and lap tracking"""

    def __init__(self):
        self.state = SessionState.IDLE
        self.current_lap = 0
        self.current_session_id = None
        self.lap_samples = []  # Buffer for current lap

    def update(self, telemetry: Dict[str, Any]) -> Dict[str, str]:
        """
        Update session state based on telemetry

        Returns:
            Dict with events: {'lap_completed': True, 'session_started': True}
        """
        events = {}

        # Detect lap change
        new_lap = telemetry.get('lap', 0)
        if new_lap != self.current_lap and self.current_lap > 0:
            events['lap_completed'] = True

        self.current_lap = new_lap

        return events

    def add_sample(self, telemetry: Dict[str, Any]):
        """Add telemetry sample to current lap buffer"""
        self.lap_samples.append(telemetry)

    def get_lap_data(self) -> List[Dict[str, Any]]:
        """Get all samples for current lap"""
        return self.lap_samples.copy()

    def clear_lap_buffer(self):
        """Clear lap buffer after write"""
        self.lap_samples.clear()

    def generate_session_id(self) -> str:
        """Generate unique session ID"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
        return timestamp
```

---

### 3. CSV Formatter

The formatter writes the MVP LMUTelemetry v2 format (metadata preamble + 12 telemetry columns). Internally it expects:

- **Normalized samples** keyed by the canonical headers defined in `src/mvp_format.py`.
- **Metadata block** already containing the required keys (`Format`, `Version`, `Player`, `TrackName`, `CarName`, `SessionUTC`, `LapTime [s]`, `TrackLen [m]`) plus any optional extras (tyre compound, weather, etc.).

```python
class CSVFormatter:
    """Formats normalized telemetry data into LMUTelemetry v2 CSV."""

    def __init__(self, header: Iterable[str] | None = None):
        self.header = list(header or MVP_TELEMETRY_HEADER)

    def format_lap(
        self,
        lap_data: List[Mapping[str, Any]],
        metadata: Mapping[str, Any],
    ) -> str:
        if not lap_data:
            return ""

        lines = []

        # Metadata rows are emitted first, in canonical order.
        for key in self.metadata_order:
            if key in metadata:
                lines.append(f"{key},{metadata[key]}")
        for key, value in metadata.items():
            if key not in self.metadata_order:
                lines.append(f"{key},{value}")

        lines.append("")  # Blank separator line
        lines.append(",".join(self.header))

        # Telemetry samples sorted by LapDistance [m]
        for sample in sorted(lap_data, key=lambda row: row.get("LapDistance [m]", 0.0)):
            lines.append(self._format_sample_row(sample))

        return "\n".join(lines) + "\n"

    def _format_sample_row(self, sample: Mapping[str, Any]) -> str:
        """Format a single sample according to per-column precision rules."""
        values = []
        for column in self.header:
            # ints => whole numbers, LapDistance/LapTime => ≥3 decimals,
            # other floats => ≥2 decimals, blanks for missing coordinates.
            values.append(self._format_value(column, sample.get(column)))
        return ",".join(values)
```

---

### 4. File Manager

```python
from pathlib import Path

class FileManager:
    """Handles CSV file writing and management"""

    def __init__(self, config: Dict[str, Any]):
        self.output_dir = Path(config.get('output_directory',
                                          Path.home() / 'Documents' / 'LMU' / 'Telemetry'))
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def write_lap(self, csv_content: str, metadata: Dict[str, Any]) -> Path:
        """
        Write lap CSV to file

        Args:
            csv_content: Formatted CSV string
            metadata: Player, track, date for filename

        Returns:
            Path to written file

        Raises:
            IOError: If disk full or write fails
        """
        filename = self._generate_filename(metadata)
        filepath = self.output_dir / filename

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(csv_content)
            return filepath
        except IOError as e:
            raise IOError(f"Failed to write {filepath}: {e}")

    def _generate_filename(self, metadata: Dict[str, Any]) -> str:
        """
        Generate filename from metadata

        Format: {player}_{track}_{date}_{session_id}.csv
        Example: Dean_Davids_Bahrain_20251117_123456789.csv
        """
        player = metadata['player_name'].replace(' ', '_')
        track = metadata['track_name'].replace(' ', '_')
        date = metadata['date'].strftime('%Y%m%d')
        session = metadata['session_id']

        return f"{player}_{track}_{date}_{session}.csv"
```

---

### 5. Process Monitor

```python
import psutil

class ProcessMonitor:
    """Monitors for LMU process (or mock process on macOS)"""

    def __init__(self, config: Dict[str, Any]):
        # On Windows: look for LMU.exe
        # On macOS: configurable test process (e.g., "Chrome")
        self.target_process = config.get('target_process', 'LMU.exe')
        self._process = None

    def is_running(self) -> bool:
        """Check if target process is running"""
        for proc in psutil.process_iter(['name']):
            try:
                if self.target_process.lower() in proc.info['name'].lower():
                    self._process = proc
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return False

    def wait_for_process(self, timeout: Optional[float] = None):
        """Block until process appears"""
        start = time.time()
        while True:
            if self.is_running():
                return True
            if timeout and (time.time() - start) > timeout:
                return False
            time.sleep(1.0)
```

---

### 6. System Tray UI

```python
import pystray
from PIL import Image, ImageDraw

class TrayUI:
    """System tray icon and menu"""

    def __init__(self, on_exit_callback, on_toggle_callback, on_settings_callback):
        self.on_exit = on_exit_callback
        self.on_toggle = on_toggle_callback
        self.on_settings = on_settings_callback

        self.icon = None
        self.enabled = True

    def create_icon(self, color: str = 'gray') -> Image:
        """
        Create tray icon image

        Args:
            color: 'gray' (idle), 'green' (logging), 'red' (error), 'yellow' (paused)
        """
        img = Image.new('RGB', (64, 64), color='white')
        draw = ImageDraw.Draw(img)

        color_map = {
            'gray': (128, 128, 128),
            'green': (0, 255, 0),
            'red': (255, 0, 0),
            'yellow': (255, 255, 0)
        }

        draw.ellipse([8, 8, 56, 56], fill=color_map.get(color, (128, 128, 128)))
        return img

    def create_menu(self) -> pystray.Menu:
        """Create context menu"""
        return pystray.Menu(
            pystray.MenuItem(f"Status: {'Logging' if self.enabled else 'Paused'}",
                           lambda: None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Open Output Folder", self._open_folder),
            pystray.MenuItem("Open Logs", self._open_logs),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Enable Logging" if not self.enabled else "Pause Logging",
                           self._toggle),
            pystray.MenuItem("Settings", self.on_settings),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Add to Startup", self._add_to_startup),
            pystray.MenuItem("Exit", self._exit)
        )

    def update_status(self, status: str):
        """
        Update icon color based on status

        Args:
            status: 'idle', 'logging', 'error', 'paused'
        """
        color_map = {
            'idle': 'gray',
            'logging': 'green',
            'error': 'red',
            'paused': 'yellow'
        }

        if self.icon:
            self.icon.icon = self.create_icon(color_map.get(status, 'gray'))

    def run(self):
        """Start tray icon (blocking)"""
        self.icon = pystray.Icon(
            "LMU Telemetry Logger",
            self.create_icon('gray'),
            "LMU Telemetry Logger",
            self.create_menu()
        )
        self.icon.run()
```

---

## Data Schemas

### Telemetry Data Dictionary

All telemetry readers must return a dictionary with these fields:

```python
{
    # Player/Session Info
    'player_name': str,          # e.g., "Dean Davids"
    'track_name': str,           # e.g., "Bahrain International Circuit"
    'car_name': str,             # e.g., "Toyota GR010"
    'session_type': str,         # "Practice", "Qualifying", "Race"
    'game_version': str,         # e.g., "0.9"
    'date': datetime,            # Session date/time

    # Lap Info
    'lap': int,                  # Current lap number
    'lap_distance': float,       # Distance in current lap (meters)
    'total_distance': float,     # Total distance (meters)
    'lap_time': float,           # Current lap time (seconds)
    'sector1_time': float,       # Sector 1 time (seconds)
    'sector2_time': float,       # Sector 2 time (seconds)
    'sector3_time': float,       # Sector 3 time (seconds)

    # Track Info
    'track_id': int,
    'track_length': float,       # meters
    'track_temp': float,         # Celsius
    'ambient_temp': float,       # Celsius
    'weather': str,              # "Clear", "Rain", etc.
    'wind_speed': float,         # m/s
    'wind_direction': float,     # degrees

    # Car State
    'speed': float,              # km/h
    'rpm': float,
    'gear': int,
    'throttle': float,           # 0.0 to 1.0
    'brake': float,              # 0.0 to 1.0
    'steering': float,           # -1.0 to 1.0
    'clutch': float,             # 0.0 to 1.0
    'drs': int,                  # 0 or 1

    # Position
    'position_x': float,         # meters
    'position_y': float,         # meters
    'position_z': float,         # meters
    'yaw': float,                # radians
    'pitch': float,              # radians
    'roll': float,               # radians

    # Physics
    'g_force_lateral': float,    # G
    'g_force_longitudinal': float,  # G
    'g_force_vertical': float,   # G

    # Wheels (RL, RR, FL, FR)
    'wheel_speed': {
        'rl': float, 'rr': float, 'fl': float, 'fr': float  # km/h
    },
    'tyre_temp': {
        'rl': float, 'rr': float, 'fl': float, 'fr': float  # Celsius
    },
    'tyre_pressure': {
        'rl': float, 'rr': float, 'fl': float, 'fr': float  # PSI
    },
    'tyre_wear': {
        'rl': float, 'rr': float, 'fl': float, 'fr': float  # %
    },
    'brake_temp': {
        'rl': float, 'rr': float, 'fl': float, 'fr': float  # Celsius
    },
    'suspension_position': {
        'rl': float, 'rr': float, 'fl': float, 'fr': float  # meters
    },
    'suspension_velocity': {
        'rl': float, 'rr': float, 'fl': float, 'fr': float  # m/s
    },

    # Hybrid/ERS (for LMH cars)
    'ers_level': float,          # Joules
    'mguk_harvested': float,     # Joules
    'mguh_harvested': float,     # Joules
    'ers_spent': float,          # Joules
    'ers_mode': int,

    # Engine
    'engine_temp': float,        # Celsius
    'fuel_remaining': float,     # liters
    'fuel_mix_mode': int,

    # Car Setup
    'front_wing': float,
    'rear_wing': float,
    'brake_bias': float,         # %

    # Session State
    'race_position': int,
    'in_pits': bool,
    'current_flag': int,         # 0=none, 1=yellow, 2=blue, etc.
    'lap_invalid': bool,
}
```

### CSV File Format

The MVP logger emits the `LMUTelemetry v2` layout described in `telemetry_format_analysis.md`:

1. **Metadata preamble** – Repeated `Key,Value` lines. The required keys are:
   - `Format` (literal `LMUTelemetry v2`)
   - `Version` (`1`)
   - `Player`
   - `TrackName`
   - `CarName`
   - `SessionUTC` (ISO `YYYY-MM-DDTHH:MM:SSZ`)
   - `LapTime [s]` (best lap time, ≥3 decimals)
   - `TrackLen [m]` (official lap length, ≥2 decimals)

   Optional keys (GameVersion, Event, TyreCompound, Weather, FuelAtStart, etc.) follow in the same `Key,Value` form.

2. **Blank separator line.**

3. **Telemetry header** – exactly:

   ```
   LapDistance [m],LapTime [s],Sector [int],Speed [km/h],EngineRevs [rpm],
   ThrottlePercentage [%],BrakePercentage [%],Steer [%],Gear [int],
   X [m],Y [m],Z [m]
   ```

4. **Telemetry samples** – one row per normalized sample sorted by `LapDistance [m]`.

**Per-column formatting rules**

| Column | Rule |
| --- | --- |
| `LapDistance [m]`, `LapTime [s]` | Floats with ≥3 decimals (e.g., `5386.800`). |
| `Speed [km/h]`, `EngineRevs [rpm]`, position axes | Floats with ≥2 decimals (trim trailing zeros beyond the minimum). |
| `ThrottlePercentage [%]`, `BrakePercentage [%]`, `Steer [%]` | Floats 0–100 (steer ±100) with ≥2 decimals. |
| `Sector [int]`, `Gear [int]` | Integers (`Sector` zero-based, `Gear` -1/0/1+). |
| Missing coordinates | Emit empty strings so the viewer reads them as `null`. |

Every CSV file represents a single completed lap.

---

## Configuration Specification

### config.json Schema

```json
{
  "version": "1.0",
  "output_directory": "~/Documents/LMU/Telemetry",
  "logging": {
    "enabled": true,
    "auto_start": true,
    "sampling_rate_hz": 100
  },
  "process": {
    "target_name": "LMU.exe",
    "poll_interval_seconds": 1.0
  },
  "ui": {
    "show_notifications": true,
    "minimize_to_tray": true
  },
  "startup": {
    "add_to_windows_startup": false
  },
  "advanced": {
    "buffer_size_samples": 10000,
    "file_write_on_lap_complete": true,
    "auto_save_interval_seconds": 300
  }
}
```

**Config Loading:**
1. If `config.json` doesn't exist, create with defaults
2. Merge user config with defaults (user values override)
3. Validate all paths and values
4. Log any invalid settings and use defaults

---

## Error Handling

### Error Scenarios

| Scenario | Error Type | Handling | User Notification |
|----------|-----------|----------|-------------------|
| Shared memory unavailable | `TelemetryError` | Log warning, enter idle state | Tray icon: yellow, tooltip: "Waiting for LMU" |
| Disk full | `IOError` | Buffer in memory, retry after 30s | Tray notification: "Disk full, buffering data" |
| Write failed | `IOError` | Retry 3 times, then discard | Tray notification: "Failed to write lap data" |
| Config file corrupt | `JSONDecodeError` | Use defaults, backup corrupt file | Log error, continue with defaults |
| Plugin not enabled | `TelemetryError` | Display help message | Tray notification with instructions |
| Process crashed | `ProcessError` | Detect crash, save buffer, reset | Save current lap, return to idle |
| Invalid telemetry data | `DataError` | Skip sample, log warning | No notification (log only) |

### Exception Hierarchy

```python
class TelemetryLoggerError(Exception):
    """Base exception"""
    pass

class TelemetryError(TelemetryLoggerError):
    """Telemetry reading failed"""
    pass

class DataError(TelemetryLoggerError):
    """Invalid data format"""
    pass

class ProcessError(TelemetryLoggerError):
    """Process monitoring error"""
    pass
```

---

## Performance Requirements

### Targets

| Metric | Requirement | Measurement Method |
|--------|-------------|-------------------|
| CPU usage (idle) | < 1% | Task Manager / Activity Monitor |
| CPU usage (logging) | < 5% | Task Manager / Activity Monitor |
| Memory usage | < 100MB | Task Manager / Activity Monitor |
| Sampling rate | 100 Hz (±5%) | Measure samples per second |
| Lap write time | < 500ms | Time from lap completion to file written |
| Max buffer size | 10,000 samples | ~100 seconds at 100Hz |
| Startup time | < 2 seconds | Time from launch to tray icon visible |

### Optimization Requirements

- **No blocking I/O in main loop** - Use threading for file writes
- **Efficient data structures** - Use deque for sample buffer
- **Minimal memory copies** - Pass references where possible
- **Lazy loading** - Don't import Windows-only modules on macOS

---

## Testing Requirements

### Unit Test Coverage

**Minimum Coverage**: 80% of all code

**Must Test:**
- ✅ CSV formatter (all 6 sections independently)
- ✅ Session state transitions
- ✅ Lap detection logic
- ✅ File naming generation
- ✅ Configuration loading (valid, invalid, missing)
- ✅ Data validation
- ✅ Error handling paths

### Integration Tests

**Test Scenarios:**
1. **Full pipeline with mock data**
   - Mock telemetry → Session manager → CSV → File write
   - Verify CSV matches expected format

2. **Multi-lap session**
   - 3 laps with mock data
   - Verify 3 separate files created
   - Verify lap numbers increment correctly

3. **Error recovery**
   - Disk full simulation (mock)
   - Process crash simulation
   - Verify buffer preservation

4. **Process detection**
   - Test with Chrome on macOS
   - Verify state transitions (idle → detected → logging)

### Live Testing (Windows Only)

**Test Matrix:**

| Session Type | Laps | Validation |
|--------------|------|------------|
| Practice | 1 | CSV matches LMUTelemetry v2 structure |
| Practice | 3 | All 3 laps written correctly |
| Race | 5 | Lap numbers sequential, no gaps |
| Interrupted | Stop mid-lap | Partial lap saved or discarded correctly |

**Performance Validation:**
- Run LMU + Logger for 30 minutes
- Monitor CPU/RAM usage
- Verify < 5% CPU, < 100MB RAM
- No lag in game

---

## Phase Acceptance Criteria

### Phase 1: Setup & Mock System

**Done When:**
- ✅ Git repository initialized
- ✅ Virtual environment created
- ✅ `requirements.txt` created and dependencies installed
- ✅ Project structure matches spec
- ✅ `MockTelemetryReader` implemented and returns valid data dictionary
- ✅ Platform detection works (correctly identifies macOS vs Windows)
- ✅ At least 1 unit test passes for mock telemetry

### Phase 2: Core Logger

**Done When:**
- ✅ `ProcessMonitor` detects Chrome on macOS
- ✅ `SessionManager` tracks session state (idle → detected → logging)
- ✅ Main loop polls at ~100Hz (measured with timing)
- ✅ Lap completion detected correctly (test with mock data changing lap number)
- ✅ Sample buffer stores data correctly
- ✅ Unit tests pass for session state transitions
- ✅ Integration test: mock telemetry → session manager → buffered samples

### Phase 3: CSV Formatter

**Done When:**
- ✅ All 6 CSV sections format correctly
- ✅ Output matches LMUTelemetry v2 format exactly
- ✅ Field precision matches (floating point formatting)
- ✅ Unit tests for each section pass
- ✅ Integration test: full lap data → CSV string → parse and validate
- ✅ Test with 0 samples (edge case)
- ✅ Test with 10,000 samples (max buffer)

### Phase 4: File Management & UI

**Done When:**
- ✅ Files written to correct directory
- ✅ Filename generation matches spec
- ✅ Disk full error handled gracefully
- ✅ Config file loads/creates correctly
- ✅ System tray icon appears on macOS menu bar
- ✅ All menu items work (open folder, settings, etc.)
- ✅ Icon color changes with status
- ✅ Integration test: lap completion → CSV → file write → file exists

### Phase 5: Windows Testing

**Done When:**
- ✅ Repository cloned and running on Windows
- ✅ `RealTelemetryReader` reads from shared memory
- ✅ Plugin enabled in LMU confirmed
- ✅ Live test: 1 practice lap → CSV file created
- ✅ CSV output validated against LMUTelemetry v2 reference
- ✅ Live test: 3 laps → 3 files created
- ✅ Performance validated (< 5% CPU, < 100MB RAM)
- ✅ Auto-detection works (start logger, then LMU)
- ✅ Error handling tested (disconnect, crash)

### Phase 6: Packaging & Documentation

**Done When:**
- ✅ PyInstaller builds `.exe` successfully
- ✅ `.exe` runs on clean Windows machine (no Python)
- ✅ System tray works in Windows
- ✅ Auto-start functionality tested
- ✅ README.md complete with Quick Start
- ✅ Troubleshooting guide covers common issues
- ✅ Developer guide explains macOS + Windows setup
- ✅ Example CSV included in release package
- ✅ GitHub release created with all files

---

## Definition of Done (Overall Project)

**Project is complete when:**

1. ✅ All phase acceptance criteria met
2. ✅ Unit test coverage ≥ 80%
3. ✅ All integration tests pass
4. ✅ Live testing completed on Windows (3+ sessions)
5. ✅ Performance requirements met
6. ✅ `.exe` builds and runs on clean Windows 10/11
7. ✅ Documentation complete (README, troubleshooting, dev guide)
8. ✅ Example CSV output included and validated
9. ✅ GitHub repository public with release
10. ✅ Zero critical bugs outstanding

---

## Appendix: Field Mappings

### rF2 Shared Memory → Our Telemetry Dict

(To be filled in during Phase 1 when studying pyRfactor2SharedMemory)

```python
# Example mapping (to be verified)
{
    'speed': rf2_data.mVehicles[0].mLocalVel,  # Convert to km/h
    'rpm': rf2_data.mVehicles[0].mEngineRPM,
    'lap': rf2_data.mVehicles[0].mTotalLaps,
    # ... complete mapping TBD
}
```

### Telemetry Dict → CSV Columns

Mapping documented in `CSVFormatter` implementation with the exact MVP header order.

---

**End of Technical Specification**
