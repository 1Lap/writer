# Track Map Waypoint Analysis

## Test Results (2025-11-22)

### Endpoint Response
- **URL**: `http://localhost:6397/rest/watch/trackmap`
- **Status**: 200 OK ✅
- **Waypoint count**: 1,347
- **Format**: JSON array of waypoint objects

### Waypoint Structure

Each waypoint has 4 fields:

```json
{
  "type": 0,              // Integer: 0-143 (waypoint type/category)
  "x": -112.66978,        // Float: X coordinate (meters)
  "y": 38.81134,          // Float: Y coordinate (elevation, meters)
  "z": -100.92450         // Float: Z coordinate (meters)
}
```

### Coordinate System

**Matches our telemetry system!** ✅

- **X/Z**: 2D plane coordinates (horizontal position)
- **Y**: Elevation (vertical position)
- **Units**: Meters
- **Same as**: Our telemetry `X [m]`, `Z [m]` from shared memory

**Coordinate ranges (example track):**
- X: -152.14 to 501.74 meters
- Y: ~38-39 meters (elevation)
- Z: Track depth dimension
- Type: 0 to 143 (see analysis below)

### Waypoint Density

- **1,347 waypoints** for ~5km track
- **~3.7 meters** between waypoints
- **Very high density** - excellent for accurate track outline

### Type Field Analysis

The `type` field ranges from **0 to 143**. This likely indicates:

**Hypothesis 1: Waypoint Categories**
- `0`: Racing line / track centerline
- `1-50`: Track boundaries (left/right edges)
- `51-100`: Pit lane
- `101-143`: Sector markers, DRS zones, other features

**Hypothesis 2: Distance Markers**
- `type` could be distance along track in some unit
- Would need to verify with track length

**Hypothesis 3: Multiple Racing Lines**
- Different `type` values = different racing lines (slow/fast)
- Or: Different track layout variants

### Next Steps to Understand Type Field

Create a follow-up test to analyze the `type` field:

1. **Group waypoints by type**
   - How many waypoints per type value?
   - Are they clustered or distributed?

2. **Plot type vs. position**
   - Does type correlate with track distance?
   - Are certain types at specific locations (pit entry/exit)?

3. **Check Swagger documentation**
   - Look for type field enum/documentation
   - `http://localhost:6397/swagger/index.html`

## Data Structure Recommendations

### Option A: Include All Waypoints (Full Fidelity)

Embed complete waypoint array in CSV metadata:

```csv
TrackMapWaypoints,1347
TrackMapData,[{"type":0,"x":-112.67,"y":38.81,"z":-100.92},...]
```

**Pros:**
- ✅ Full track detail (racing line, boundaries, pit lane)
- ✅ Can render multiple features (not just outline)
- ✅ Type field preserved for future analysis

**Cons:**
- ⚠️ Larger metadata (~40-80KB for 1347 waypoints)
- ⚠️ More complex parsing in lap viewer

**Size estimate:**
- 1347 waypoints × ~60 bytes/waypoint = ~80KB
- Still only ~8% of 1MB CSV file

---

### Option B: Simplified Track Outline (Filtered)

Filter waypoints to just track centerline/outline:

```csv
TrackMap,[[-112.67,-100.92],[-111.46,-105.79],...]
TrackMapWaypoints,300
```

**Filtering logic:**
- Keep only `type == 0` (likely racing line)
- Or: Downsample to every ~15-20 meters
- Result: ~300 waypoints instead of 1347

**Pros:**
- ✅ Smaller metadata (~6KB)
- ✅ Simpler lap viewer parsing
- ✅ Sufficient for track outline visualization

**Cons:**
- ❌ Lose track boundary, pit lane, sector data
- ❌ Can't show track width/limits

---

### Option C: Hybrid - Multiple Waypoint Sets

Include multiple waypoint types:

```csv
TrackMapRacingLine,[[-112.67,-100.92],...]
TrackMapLeftEdge,[[-115.23,-101.45],...]
TrackMapRightEdge,[[-110.11,-100.39],...]
TrackMapPitLane,[[-95.44,-88.21],...]
```

**Pros:**
- ✅ Best of both worlds
- ✅ Lap viewer can choose what to render
- ✅ Enables advanced features (track limits, pit detection)

**Cons:**
- ⚠️ Requires understanding type field meaning
- ⚠️ More complex implementation

---

## Recommended Approach: **Option B (Filtered)**

**Why:**

1. **Sufficient for current goal** - Track outline for apex/width analysis
2. **Reasonable size** - ~6KB for 300 waypoints (0.6% overhead)
3. **Simpler implementation** - Less lap viewer complexity
4. **Future-proof** - Can upgrade to Option C later if needed

**Implementation:**

```python
def get_trackmap_outline(waypoints: List[Dict]) -> List[List[float]]:
    """
    Extract simplified track outline from waypoint data

    Strategy:
    - Filter to type == 0 (likely racing line)
    - Downsample to ~15-20m spacing (~300 waypoints)
    - Return as [[x, z], [x, z], ...] array
    """
    # Filter by type (if type 0 is racing line)
    racing_line = [w for w in waypoints if w['type'] == 0]

    # If no type 0, use all waypoints
    if not racing_line:
        racing_line = waypoints

    # Downsample if still too many
    if len(racing_line) > 400:
        step = len(racing_line) // 300
        racing_line = racing_line[::step]

    # Extract X/Z coordinates only (ignore Y elevation for 2D map)
    return [[w['x'], w['z']] for w in racing_line]
```

**CSV Format:**

```csv
Format,LMUTelemetry v3
Version,1
Player,Dean Davids
TrackName,Bahrain International Circuit
TrackLen [m],5386.80
TrackMap,[[-112.67,-100.92],[-111.46,-105.79],...]
TrackMapWaypoints,300
TrackMapSource,LMU_REST_API

LapDistance [m],Sector [int],...,X [m],Z [m]
```

---

## File Size Impact

### Current CSV: ~1MB
- Metadata: ~500 bytes
- Telemetry: ~11,000 rows × ~90 bytes = ~990KB

### With Track Map (Option B):
- Track map waypoints: ~6KB (300 waypoints)
- **Total increase: 0.6%**
- New total: ~1.006MB

### With Track Map (Option A - Full):
- Track map waypoints: ~80KB (1347 waypoints)
- **Total increase: 8%**
- New total: ~1.08MB

**Both are acceptable** - modern file sizes, compress well with gzip.

---

## Action Items

1. ✅ **Waypoint structure analyzed**
   - 4 fields: type, x, y, z
   - Coordinates match our telemetry system
   - 1347 waypoints, high density

2. ⏳ **Investigate type field**
   - Create analysis script to group by type
   - Check Swagger docs for type enum
   - Determine which types to include

3. ⏳ **Design filtering logic**
   - Which waypoint types to include?
   - Downsampling strategy
   - Error handling (if no waypoints available)

4. ⏳ **Implement in LMURestAPI**
   - Add `get_trackmap()` method
   - Add filtering/downsampling
   - Cache by track name

5. ⏳ **Update CSV formatter**
   - Add TrackMap to metadata section
   - JSON array serialization
   - Size optimization

6. ⏳ **Update session manager**
   - Fetch track map once per session
   - Include in lap metadata
   - Handle REST API unavailability gracefully

---

## Open Questions

1. **What do the type values mean?**
   - Need to analyze type distribution
   - Check Swagger documentation
   - Test with multiple tracks

2. **Should we include elevation (Y)?**
   - Lap viewer is 2D (X/Z plane)
   - But elevation could be useful for future 3D viewer
   - Trade-off: +33% size for future-proofing

3. **How to handle track variants?**
   - Do different layouts have different waypoints?
   - Should we include layout name in cache key?

4. **What if REST API unavailable?**
   - Graceful degradation: CSV without track map
   - Lap viewer shows driven line only
   - Optional: Fall back to TinyPedal-style recording

---

**Date:** 2025-11-22
**Track Tested:** Unknown (from user's LMU session)
**Waypoints:** 1,347
**Status:** ✅ Ready for implementation
