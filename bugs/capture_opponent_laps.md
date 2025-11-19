# Capture Opponent Laps in Multiplayer

**Status**: Enhancement Request
**Priority**: Medium
**Category**: Multiplayer Telemetry

---

## Description

Capture telemetry data for opponent vehicles during multiplayer sessions to enable comparative analysis against other drivers.

## Use Cases

- Compare racing lines with faster opponents
- Analyze braking points and throttle application differences
- Learn from other drivers' techniques
- Training data for AI/ML models
- Post-race analysis and coaching

## Technical Feasibility

The rF2 shared memory API provides access to opponent data through:
- `self.Rf2Scor.mVehicles[index]` - Scoring data (up to 128 vehicles)
- `self.Rf2Tele.mVehicles[index]` - Telemetry data (up to 128 vehicles)

Each vehicle includes:
- `mDriverName` - Driver identification
- `mVehicleName` - Vehicle name
- `mControl` - Control type (-1=nobody, 0=local player, 1=AI, 2=remote, 3=replay)
- Full telemetry data (speed, position, inputs, etc.)

## Implementation Options

### Option 1: Capture All Laps (Simplest MVP)

**Pros**:
- Simplest to implement
- Maximum data availability
- No filtering logic needed

**Cons**:
- Large storage footprint (N drivers × M laps × ~1MB per lap)
- File management complexity
- May capture incomplete laps (DNFs, disconnects)

**Estimated Storage**:
- 20 drivers × 10 laps × 1MB = 200MB per session
- Manageable for most use cases

### Option 2: Fastest Lap Only Per Opponent (Recommended) ✅

**Pros**:
- Controlled storage growth (~20MB per session with 20 drivers)
- Most relevant data for comparison (best performance)
- Built-in quality filter (completed valid laps only)

**Cons**:
- More complex logic (track fastest lap per driver)
- Requires lap completion detection for all vehicles
- Need to handle lap invalidation (track limits, etc.)

**Implementation Notes**:
- Track `best_lap_time` dictionary: `{driver_name: (time, samples)}`
- Only save lap if: valid lap AND faster than current best
- Check `mCountLapFlag` for lap invalidation status

### Option 3: Configurable Capture Strategy

**Pros**:
- Maximum flexibility
- User can choose based on needs (practice vs race)
- Future-proof design

**Cons**:
- Most complex to implement
- Requires UI controls and settings persistence
- More testing scenarios

**Configuration Options**:
- `capture_mode`: `"none"`, `"fastest_only"`, `"all_laps"`, `"top_n_drivers"`
- `max_laps_per_driver`: Integer limit (0 = unlimited)
- `capture_ai`: Boolean (include AI opponents or remote only)
- `min_lap_time`: Filter out invalid/outlier laps

### Option 4: Position-Based Capture (Contextual)

**Pros**:
- Captures most relevant competitors (nearby positions)
- Reduces data volume while maintaining competitive context
- Useful for learning from faster drivers

**Cons**:
- Requires position tracking logic
- May miss data from drivers who had good laps earlier
- Complexity in determining "nearby" (by position vs track distance)

**Criteria Examples**:
- Capture laps from drivers within ±3 positions
- Capture laps from drivers ahead of player only
- Capture laps from drivers within same class (multiclass)

## Data Availability Considerations

### 1. Input Data Availability

- **Remote players**: May not have full input data (throttle/brake/steering)
- **AI drivers**: Full telemetry should be available
- **Local player**: Always full data
- **Fallback**: Capture position/speed/gear even without inputs for "good enough" training signal

### 2. Telemetry Quality

- Network latency may affect remote player data freshness
- Position interpolation may be used for remote players
- Consider marking data source type in CSV metadata

### 3. Lap Validity

- Check `mCountLapFlag` to filter invalid laps (track limits violations)
- Verify lap completion (lap number increment)
- Filter pit laps if desired

## Recommended Implementation Path

### Phase 1 (Quick Win): Option 2 - Fastest lap only ← **IMPLEMENTING THIS**

- Add opponent tracking to `SessionManager`
- Store fastest lap per opponent (dictionary keyed by driver name)
- Save with naming: `{session_id}_lap{lap}_{driver_name}.csv`
- Filter: remote players only (`mControl == 2`), valid laps only

### Phase 2 (Enhancement): Add basic configuration

- Settings: enable/disable opponent capture
- Settings: capture AI vs remote only
- Settings: max laps per opponent (default: 1)

### Phase 3 (Advanced): Option 3 - Full configurability

- UI controls for capture strategy
- Advanced filtering options
- Storage usage monitoring and cleanup

## File Naming Proposal

Uses the same format as player laps for consistency:
```
{date}_{time}_{track}_{car}_{driver}_lap{lap}_t{lap_time}s.csv

Examples:
Player lap:
- 2025-11-20_14-30_bahrain-international-circuit_toyota-gr010_dean-davids_lap3_t125.234s.csv

Opponent lap:
- 2025-11-20_14-30_bahrain-international-circuit_ferrari-499p_alice-johnson_lap3_t122.156s.csv
```

Format fields:
- `{date}`: Session date (YYYY-MM-DD)
- `{time}`: Session time (HH-MM)
- `{track}`: Track name (sanitized, lowercase, spaces→hyphens)
- `{car}`: Car name (sanitized, lowercase, spaces→hyphens)
- `{driver}`: Driver name (player or opponent, sanitized)
- `{lap}`: Lap number
- `{lap_time}`: Lap time in seconds (formatted)

## Storage Impact Estimation

```
Scenario: 30-minute race, 20 drivers, 10 laps average
- Option 1 (all laps): 20 drivers × 10 laps × 1MB = 200MB
- Option 2 (fastest only): 20 drivers × 1 lap × 1MB = 20MB
- Option 4 (nearby ±3): ~7 drivers × 10 laps × 1MB = 70MB
```

## Testing Requirements

- Mock implementation for development on macOS
- Integration tests with multiple vehicles in mock data
- Windows testing in actual multiplayer session
- Validate lap timing/filtering logic
- Verify file naming and storage organization

---

## Implementation Status

**Current Phase**: Phase 1 - COMPLETE ✅

### Completed Work

**Implementation Date**: 2025-11-20

✅ **Phase 1: Option 2 - Fastest Lap Only** (COMPLETE)

**Components Implemented**:

1. **OpponentTracker** (`src/opponent_tracker.py`)
   - Tracks fastest lap per opponent
   - Filters by control type (remote players vs AI)
   - 11 unit tests, all passing
   - Stores lap data keyed by driver name
   - Returns only laps faster than previous best

2. **TelemetryReaderInterface** - Added `get_all_vehicles()` method
   - Abstract method for accessing opponent telemetry
   - Returns list of vehicle telemetry dictionaries

3. **MockTelemetryReader** - `get_all_vehicles()` implementation
   - Generates 3 mock opponents for testing
   - 2 remote players + 1 AI driver
   - Simulates realistic lap progression

4. **RealTelemetryReader** - `get_all_vehicles()` implementation
   - Accesses `Rf2Scor.mVehicles[]` and `Rf2Tele.mVehicles[]` arrays
   - Filters out local player
   - Extracts driver name, car, position, lap data
   - Handles up to 128 vehicles from shared memory

5. **TelemetryLoop** - Opponent polling integration
   - Polls opponents each iteration
   - Triggers `on_opponent_lap_complete` callback
   - Configuration options:
     - `track_opponents`: Enable/disable (default: True)
     - `track_opponent_ai`: Include AI opponents (default: False)
   - Non-blocking opponent tracking (doesn't fail main loop)

6. **example_app.py** - Full demonstration
   - `on_opponent_lap_complete()` callback
   - Saves opponent laps with naming: `{session_id}_lap{lap}_{driver_name}_P{position}.csv`
   - Statistics tracking (opponent laps saved, opponents tracked)
   - Status display shows opponent count

**Testing**:
- All 91 tests passing (60 existing + 11 new for OpponentTracker + 20 integration tests)
- OpponentTracker unit tests cover:
  - Initialization and configuration
  - Control type filtering (remote/AI)
  - Lap completion detection
  - Fastest lap tracking (replace slower with faster)
  - Multiple opponents simultaneously
- Integration tested with MockTelemetryReader on macOS

**File Naming**:
- Uses same format as player laps: `{date}_{time}_{track}_{car}_{driver}_lap{lap}_t{lap_time}s.csv`
- Driver field contains opponent name for opponent laps
- Example player: `2025-11-20_14-30_bahrain-international-circuit_toyota-gr010_dean-davids_lap3_t125.234s.csv`
- Example opponent: `2025-11-20_14-30_bahrain-international-circuit_ferrari-499p_alice-johnson_lap3_t122.156s.csv`

**Storage Impact**:
- ~1MB per lap (same as player laps)
- Only fastest lap saved per opponent
- ~20MB for 20-driver session (20 drivers × 1 lap × 1MB)

### Next Steps (Phase 2 - Future Enhancement)

**Not yet implemented**:
- Configuration UI for opponent tracking settings
- Persistent settings storage
- Advanced filtering options (position-based, lap validity checks)
- Storage usage monitoring
- Windows testing with live multiplayer session

**Validation Needed**:
- Windows testing with real LMU multiplayer
- Verify `mControl` values are correct for remote players
- Verify lap timing accuracy for opponents
- Test with >10 opponents
- Verify lap validity flag (`mCountLapFlag`) usage
