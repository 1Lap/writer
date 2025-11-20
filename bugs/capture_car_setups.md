## Car Setup Capture Feature

### Overview
Capture car setup data for the player's vehicle to enable setup management, lap time correlation, and performance tracking. This helps users identify which setups produce the best lap times and understand the relationship between setup changes and performance.

**Status**: Enhancement
**Priority**: Medium
**Complexity**: Moderate (REST API integration + file management)

---

### What's Technically Available

#### 1. Player Setup Data (✅ Available via REST API)
The LMU REST API provides complete setup information for the **player's car only**:
- **Endpoint**: `GET /rest/garage/setup`
- **Data includes**: Full mechanical setup (suspension, aerodynamics, gearing, differential, brake balance, tire pressures, etc.)
- **Format**: JSON with hierarchical structure
- **Access**: Available when in garage or during session

#### 2. Opponent Setup Data (❌ NOT Available)
**Important limitation**: Opponent car setups are NOT accessible through either shared memory or REST API. This is standard in racing simulators for competitive fairness. You can capture opponent telemetry (inputs, speeds, positions) but not their mechanical setup values.

#### 3. Basic Setup Telemetry (⚠️ Limited)
Shared memory provides a few real-time setup values during driving:
- Brake bias (front/rear balance)
- Wing angles (if adjustable)
- Fuel load
- Tire pressures (live, changes during session)

---

### Feature Design

#### Option 1: Separate Setup Files (Recommended)
**Structure**:
```
telemetry_output/
├── session_20250120_143022/
│   ├── lap001.csv          # Telemetry data
│   ├── lap002.csv
│   ├── lap003.csv
│   └── setup.json          # Car setup (captured once per session)
└── setups/                  # Setup library (optional)
    └── BahrainGP/
        ├── Toyota_GR010_race_20250120.json
        └── Toyota_GR010_quali_20250119.json
```

**Benefits**:
- Clean separation of concerns
- One setup per session (captured on first lap)
- Easy to browse and compare setups
- Doesn't bloat lap CSV files
- Can build setup library over time

**File Format** (setup.json):
```json
{
  "metadata": {
    "capture_time": "2025-01-20T14:30:22Z",
    "session_id": "session_20250120_143022",
    "session_type": "Race",
    "track": "Bahrain International Circuit",
    "car": "Toyota GR010",
    "player": "Username",
    "laps_recorded": 12,
    "best_lap_time": 113.456,
    "best_lap_number": 7
  },
  "setup": {
    "suspension": { /* ... */ },
    "aerodynamics": { /* ... */ },
    "brakes": { /* ... */ },
    "differential": { /* ... */ },
    "gearbox": { /* ... */ },
    "tire_pressures": { /* ... */ }
  }
}
```

#### Option 2: Embedded in Lap CSV (Not Recommended)
Add setup data to the CSV metadata preamble:
```csv
Format,LMUTelemetry
Version,2
Player,Username
Track,Bahrain International Circuit
Car,Toyota GR010
SessionUTC,2025-01-20T14:30:22Z
LapTime [s],113.456
TrackLen [m],5386.80
Setup.BrakeBias,56.5
Setup.FrontWing,5
Setup.RearWing,8
...
LapDistance [m],LapTime [s],Sector,Speed [km/h],... (telemetry columns)
```

**Drawbacks**:
- Bloats every lap file with redundant setup data
- Makes CSV parsing more complex
- Harder to compare setups across sessions
- Setup doesn't change lap-to-lap, so duplication is wasteful

#### Option 3: Setup Library with Performance Tracking (Future Enhancement)
Build a searchable setup database:
```
setups/
├── index.json              # Setup catalog with performance data
├── Toyota_GR010/
│   ├── bahrain_race_20250120.json
│   ├── bahrain_quali_20250119.json
│   └── spa_race_20250115.json
└── Ferrari_499P/
    └── bahrain_race_20250118.json
```

**index.json**:
```json
{
  "setups": [
    {
      "id": "setup_001",
      "file": "Toyota_GR010/bahrain_race_20250120.json",
      "track": "Bahrain International Circuit",
      "car": "Toyota GR010",
      "session_type": "Race",
      "date": "2025-01-20",
      "best_lap": 113.456,
      "avg_lap": 115.234,
      "laps_driven": 12,
      "notes": "Stable in high-speed corners, slight understeer in slow chicanes"
    }
  ]
}
```

---

### Implementation Plan

#### Phase 1: Basic Setup Capture (Core Feature)
**Scope**: Capture player setup once per session

**Components**:
1. **SetupCapture Module** (`src/setup_capture.py`)
   - Fetch setup via REST API (`GET /rest/garage/setup`)
   - Parse and normalize JSON structure
   - Handle API unavailability gracefully
   - Cache setup for session duration

2. **Integration with SessionManager**
   - Capture setup on first lap detection
   - Store setup.json alongside lap CSVs
   - Add best lap time to metadata after session ends

3. **File Structure**:
   ```
   session_YYYYMMDD_HHMMSS/
   ├── setup.json
   ├── lap001.csv
   ├── lap002.csv
   └── ...
   ```

4. **Configuration** (settings UI):
   - `capture_setups` (bool): Enable/disable setup capture
   - `setup_format` (str): "separate" (default) or "embedded"

**Effort**: ~2-3 days
- REST API client extension: 0.5 day
- Setup capture module: 1 day
- Integration + testing: 1 day
- Documentation: 0.5 day

#### Phase 2: Setup Performance Tracking (Future)
**Scope**: Track setup performance over time

**Features**:
- Setup library organization
- Performance statistics (best lap, avg lap, consistency)
- Setup comparison tool (CLI or GUI)
- Export/import setups
- Setup notes and tags

**Effort**: ~3-4 days

#### Phase 3: Setup Comparison UI (Future)
**Scope**: Visual setup comparison

**Features**:
- Side-by-side setup comparison
- Highlight differences
- Performance delta visualization
- Setup recommendations

**Effort**: ~5-7 days (GUI development)

---

### User Experience

#### Scenario 1: Casual User (Phase 1)
1. User runs telemetry logger as normal
2. Each session automatically captures setup
3. Files organized in session folders:
   - `telemetry_output/session_20250120_143022/`
   - Contains: `setup.json` + lap CSVs
4. User can review setup later to remember what worked

#### Scenario 2: Setup Experimenter (Phase 2)
1. User tries different setups across multiple sessions
2. Setup library builds automatically
3. User reviews `setups/index.json` to find best-performing setups
4. User can compare setups for same track/car combination

#### Scenario 3: Analyst/Engineer (Phase 3)
1. User runs comparison tool: `python compare_setups.py`
2. Selects two setups to compare
3. Views side-by-side diff with performance data
4. Exports report for sharing with team

---

### Technical Considerations

#### REST API Integration
**Current state**: `LMURestAPI` class exists for vehicle metadata
**Extension needed**:
```python
class LMURestAPI:
    def fetch_setup_data(self) -> Dict[str, Any]:
        """
        Fetch current car setup from REST API

        Returns:
            Setup data dictionary or empty dict if unavailable
        """
        try:
            req = Request(f"{self.base_url}/rest/garage/setup")
            with urlopen(req, timeout=2) as response:
                return json.loads(response.read().decode('utf-8'))
        except Exception as e:
            print(f"[WARNING] Setup data unavailable: {e}")
            return {}
```

#### Timing of Setup Capture
**Options**:
1. **On first lap** (recommended): Captures setup as used during session
2. **On session start**: May miss if user enters track before setup is loaded
3. **On demand**: Requires user interaction

**Decision**: Capture on first lap detection (when telemetry logging starts)

#### Handling Setup Changes Mid-Session
- Most sessions don't allow setup changes during running
- If changes are allowed (practice), capture new setup.json with version suffix:
  - `setup_v1.json` (initial)
  - `setup_v2.json` (after change)
- Track which laps used which setup version

#### Error Handling
- REST API unavailable → Skip setup capture, log warning
- Malformed API response → Log error, save raw response for debugging
- File write failure → Log error, don't crash telemetry capture

---

### Configuration Options

**Settings UI additions**:
```python
# Setup Capture Section
[X] Capture car setups
    Output format: [ Separate files (setup.json) v]
    [ ] Build setup library (organize by track/car)
    [ ] Add setup notes after session
```

**config.json**:
```json
{
  "capture_setups": true,
  "setup_output_format": "separate",
  "setup_library_enabled": false,
  "setup_notes_prompt": false
}
```

---

### Testing Strategy

1. **Unit Tests**:
   - `test_setup_capture.py`: REST API fetching, parsing, file writing
   - Mock API responses for testing

2. **Integration Tests**:
   - Capture setup during real session
   - Verify setup.json created alongside lap CSVs
   - Test API unavailability handling

3. **Manual Testing**:
   - Various cars/tracks
   - Different session types (practice, qualifying, race)
   - API timeout/error scenarios

---

### Documentation Updates

**Files to update**:
1. `USER_GUIDE.md`: Setup capture feature section
2. `CLAUDE.md`: Development instructions for setup capture
3. `TECHNICAL_SPEC.md`: SetupCapture component specification
4. `example_app.py`: Demonstrate setup capture integration

---

### Future Enhancements

#### 1. Setup Recommendations
- Analyze setup library to suggest optimal setups for track/car
- ML-based recommendations based on driving style

#### 2. Setup Sharing
- Export/import setup files
- Share setups with team members
- Community setup database integration

#### 3. Live Setup Monitoring
- Track setup-related telemetry (tire pressures, brake temps)
- Alert when values exceed optimal ranges
- Suggest setup adjustments mid-session

#### 4. Opponent Telemetry Analysis (Alternative)
Since opponent setups aren't available, analyze their telemetry to infer setup characteristics:
- Brake points → brake balance hints
- Corner speeds → aero balance hints
- Tire wear patterns → pressure hints
- Not as accurate as actual setup, but provides useful insights

---

### Summary

**Recommended Approach**: Phase 1 (Separate Setup Files)
- ✅ Technically feasible with REST API
- ✅ User-friendly organization
- ✅ Doesn't complicate existing CSV format
- ✅ Foundation for future setup management features
- ⚠️ Player setups only (opponent setups not available)

**Key Value**: Users can track which setups produce best lap times, experiment systematically, and build a personal setup library over time.

