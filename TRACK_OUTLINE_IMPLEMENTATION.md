# Track Outline Implementation Plan

## Goal
Enhance lap telemetry CSV files with **track outline data** so the lap viewer can show:
- ✅ **Driven line** (from X/Z telemetry samples) - where the driver actually went
- ✅ **Track outline** (from track map data) - the track boundaries, apex points, etc.

This allows drivers to analyze:
- Did I hit the apex?
- Did I use all available track width?
- How close did I get to track limits?
- Is my line optimal compared to track geometry?

## Two Approaches to Consider

### Approach 1: LMU REST API Trackmap Endpoint (RECOMMENDED TO TEST FIRST)

**How it works:**
- Fetch track outline from `GET http://localhost:6397/rest/watch/trackmap`
- Include waypoints in CSV metadata section
- Lap viewer renders both driven line + track outline

**Pros:**
- ✅ No need to build/maintain track library
- ✅ Always up-to-date with game data
- ✅ Works for all tracks automatically
- ✅ Can fetch during telemetry session

**Cons:**
- ❌ Requires REST API running during session
- ❌ Need to understand waypoint format first
- ❌ Unknown: waypoint density, accuracy, format

**Next steps:**
1. Run `test_trackmap_endpoint.py` with LMU to see waypoint structure
2. Check Swagger docs at `http://localhost:6397/swagger/index.html`
3. Analyze waypoint format (X/Z coordinates? How many per track?)

---

### Approach 2: Record Track Maps Like TinyPedal

**How TinyPedal does it:**
- Records track maps as **SVG files** by capturing position data during driving
- Stores in `TinyPedal\trackmap` folder (default)
- SVG contains two coordinate paths:
  - Global X,Y position path (for track outline)
  - Track distance and elevation path
  - Sector position indices

**How we could do it:**
- Create a "track map recording mode" that captures clean track outline
- Save as JSON/SVG in a track library
- Include track map in CSV metadata (or reference by track name)
- Build library over time as users drive different tracks

**Pros:**
- ✅ Full control over data format
- ✅ Can optimize/smooth the outline
- ✅ Works offline (no REST API needed)
- ✅ Can enhance with racing line, braking points, etc.

**Cons:**
- ❌ Need to record each track variant
- ❌ Requires separate "mapping" tool/mode
- ❌ Track library maintenance
- ❌ What if track gets updated by game?

---

## Data Structure Recommendations

### Option A: Embed Waypoints in CSV Metadata

Add to metadata section:
```csv
Format,LMUTelemetry v3
Version,1
Player,Dean Davids
TrackName,Bahrain International Circuit
TrackLen [m],5386.80
TrackMap,[[x1,z1],[x2,z2],[x3,z3],...]  # JSON array of waypoints
TrackMapSource,LMU_REST_API  # or RECORDED, or COMMUNITY

LapDistance [m],Sector [int],Speed [km/h],...
```

**Pros:** Self-contained CSV file
**Cons:** Larger file size (but probably <50KB for waypoints)

---

### Option B: Separate Track Map Library

CSV references track by name:
```csv
TrackName,Bahrain International Circuit
TrackMapHash,abc123def456  # Optional: verify correct map version
```

Lap viewer loads track map from separate file/library:
```
trackmaps/
  bahrain_international_circuit.json
  spa_francorchamps.json
  le_mans.json
```

**Pros:** Smaller CSV, shared maps across laps
**Cons:** Requires external files, breaks offline workflow

---

### Option C: Hybrid (RECOMMENDED)

**Default:** Embed waypoints in CSV metadata (Option A)
**Optimization:** Lap viewer can cache track maps by TrackName to avoid re-parsing

This gives us:
- ✅ Self-contained CSV (always works)
- ✅ Lap viewer optimization (cache maps)
- ✅ Optional community track library (future enhancement)

---

## Implementation Steps

### Phase 1: Investigation (NOW)
1. ✅ Create test script (`test_trackmap_endpoint.py`)
2. ⏳ Run script with LMU to see waypoint format
3. ⏳ Document waypoint structure (fields, density, coordinate system)
4. ⏳ Check Swagger docs at `http://localhost:6397/swagger/index.html`

### Phase 2: Data Structure (AFTER TESTING)
1. Design track map data structure for CSV metadata
2. Update CSV formatter to include track map waypoints
3. Update MVP format specification
4. Add track map fetch to session manager

### Phase 3: REST API Integration
1. Add `get_trackmap()` method to `LMURestAPI` class
2. Fetch track map once per session (cache by track name)
3. Include in CSV metadata as JSON array
4. Test with multiple tracks

### Phase 4: Fallback & Enhancement
1. Add track map recording mode (like TinyPedal)
2. Build community track library
3. Allow manual track map upload/override

---

## File Format Examples

### Example: Embedded Track Map in CSV

```csv
Format,LMUTelemetry v3
Version,1
Player,Dean Davids
TrackName,Bahrain International Circuit
TrackLen [m],5386.80
TrackMap,[[-269.27,-218.97],[-268.11,-218.52],[-265.42,-217.01],...]
TrackMapWaypoints,156
TrackMapSource,LMU_REST_API

LapDistance [m],Sector [int],Speed [km/h],EngineRevs [rpm],...
0.000,0,0.00,0.00,...
```

### Example: Separate Track Map JSON

```json
{
  "trackName": "Bahrain International Circuit",
  "trackLength": 5386.80,
  "waypoints": [
    {"x": -269.27, "z": -218.97, "distance": 0.0},
    {"x": -268.11, "z": -218.52, "distance": 50.0},
    {"x": -265.42, "z": -217.01, "distance": 100.0}
  ],
  "sectors": [0, 1800, 3600],
  "pitEntry": 1234.5,
  "pitExit": 1456.7,
  "source": "LMU_REST_API",
  "recordedDate": "2025-11-22"
}
```

---

## Questions to Answer (Testing Phase)

1. **Waypoint format**: What fields does each waypoint have?
   - Just X/Z coordinates?
   - Distance along track?
   - Sector markers?
   - Track boundaries (left/right edges)?

2. **Waypoint density**: How many waypoints per track?
   - 100? 1000? 10000?
   - Is it consistent across tracks?
   - Do we need to downsample?

3. **Coordinate system**: Do waypoints use same X/Z as telemetry?
   - Can we directly overlay them?
   - Any transformations needed?

4. **Track variants**: How are different layouts handled?
   - Separate track maps per variant?
   - Single map with variant flags?

5. **API availability**: Is REST API always available?
   - Only during session?
   - Only in certain modes?

---

## Success Criteria

After implementation, lap viewer should be able to:

1. ✅ Display track outline as a background
2. ✅ Overlay driven line (from X/Z samples) on top
3. ✅ Show driver deviations from track center/edges
4. ✅ Highlight apex usage
5. ✅ Compare multiple laps on same track outline
6. ✅ Work offline with embedded track data

---

## References

- [TinyPedal User Guide](https://github.com/TinyPedal/TinyPedal/wiki/User-Guide) - Track map recording and SVG format
- [TinyPedal Track Map Widget](https://github.com/IceNbrn/TinyPedal_LMU/blob/6a37edace5a0230fba4245f609416717710644b4/tinypedal/widget/track_map.py) - Implementation reference
- [lmu-steward-companion](https://github.com/supaflyENJOY/lmu-steward-companion/blob/13cdd75a714d34ca7d060def69be470fb18af5f5/src-tauri/src/lmu_rest_api/client.rs#L491) - REST API usage example
- LMU REST API Swagger: `http://localhost:6397/swagger/index.html` (when LMU running)

---

## Next Steps

### ✅ COMPLETED:
1. ✅ Run `python test_trackmap_endpoint.py` - **Done!**
2. ✅ Analyze waypoint structure - **Done!**
3. ✅ Verify coordinate system compatibility - **Confirmed!**

### 🔄 IN PROGRESS:
4. ⏳ Analyze type field distribution
   - Run: `python test_trackmap_types.py`
   - Determine which types to include (racing line vs all)
   - Check Swagger docs: `http://localhost:6397/swagger/index.html`

### 📋 TODO:
5. ⬜ Design data structure (after type analysis)
   - Choose filtering strategy (all types vs dominant type)
   - Decide on downsampling rate
   - Finalize CSV metadata format

6. ⬜ Implement REST API integration
   - Add `get_trackmap()` to `LMURestAPI` class
   - Implement filtering/downsampling logic
   - Add caching by track name

7. ⬜ Update CSV formatter
   - Add `TrackMap` to metadata section
   - JSON serialization for waypoint array
   - Handle missing track map gracefully

8. ⬜ Update session manager
   - Fetch track map once per session (on first lap)
   - Include in lap metadata
   - Cache for subsequent laps on same track

9. ⬜ Write tests
   - Test track map fetch and caching
   - Test filtering logic
   - Test CSV format with track map

10. ⬜ Update documentation
    - Update `telemetry_format_analysis.md`
    - Add track map section to `TECHNICAL_SPEC.md`
    - Update user guide

11. ⬜ Lap viewer integration (separate codebase)
    - Parse track map from CSV metadata
    - Render track outline
    - Overlay driven line
    - Add apex analysis features

---

**Updated:** 2025-11-22 (After waypoint testing)
