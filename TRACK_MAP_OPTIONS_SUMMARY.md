# Track Map Options - Summary & Recommendation

## ⚠️ UPDATED UNDERSTANDING

**Goal:** ENHANCE the driven line by adding track outline data (not replace it!)

This allows drivers to analyze:
- Did I hit the apex?
- Did I use all available track width?
- How close to track limits?
- Is my line optimal vs track geometry?

---

## What We Discovered

### The lmu-steward-companion Approach
Uses the LMU REST API endpoint:
```
GET http://localhost:6397/rest/watch/trackmap
```

Returns waypoints representing the **track outline**.

### TinyPedal Approach
Records track maps as **SVG files** ([see User Guide](https://github.com/TinyPedal/TinyPedal/wiki/User-Guide)):
- Stores in `TinyPedal\trackmap` folder
- SVG contains: X,Y position path + distance/elevation path + sector indices
- Records by driving laps (mapping module)

### Our Current Approach
We capture X/Z coordinates from LMU shared memory for every telemetry sample:
- **Frequency**: ~100Hz (~11,000 per lap)
- **Fields**: `X [m]`, `Z [m]` (driven line)
- **Source**: `mPos` field from shared memory

**This is good! We need to KEEP this data for the driven line.**

---

## NEW Goal: Add Track Outline to Driven Line

### Recommended Approach: REST API + Embedded Waypoints

**Fetch track waypoints from REST API, embed in CSV metadata, keep X/Z samples**

```
✅ Track outline + actual driven line (both!)
✅ Analyze apex usage, track width usage
✅ Self-contained CSV files (no external dependencies)
✅ REST API fetch happens during session (when it's running anyway)
✅ Lap viewer can cache maps to avoid re-parsing
✅ Works offline after data is embedded

⚠️ Slightly larger CSV files (+ waypoints in metadata)
⚠️ Need to test REST API endpoint format first
⚠️ Moderate implementation effort
```

---

## Implementation Plan

### Step 1: Test REST API Endpoint (NOW)
Run with LMU to see waypoint format:
```bash
python test_trackmap_endpoint.py
```

Also check Swagger docs: `http://localhost:6397/swagger/index.html`

### Step 2: Design Data Structure
Add to CSV metadata:
```csv
Format,LMUTelemetry v3
TrackMap,[[-269.27,-218.97],[-268.11,-218.52],...]
TrackMapSource,LMU_REST_API
```

### Step 3: Implement
1. Add `get_trackmap()` to `LMURestAPI` class
2. Fetch once per session, cache by track name
3. Include in CSV metadata
4. Update CSV formatter

### Step 4: Lap Viewer Integration
- Render track outline as background
- Overlay driven line (from X/Z samples)
- Show deviations and apex analysis

---

## Alternative: TinyPedal-Style Recording

If REST API doesn't provide good data, we can:
1. Create "track map recording mode"
2. Save maps as JSON/SVG files
3. Build library over time
4. See [TinyPedal approach](https://github.com/TinyPedal/TinyPedal/wiki/User-Guide) for reference

---

## Why This is Better Than Status Quo

**Current:**

- Only shows driven line (X/Z samples)
- Can't see track outline, apex points, track limits

**With track outline:**
- ✅ Shows driven line AND track outline
- ✅ Analyze apex usage ("did I hit it?")
- ✅ Track width usage ("did I use all available space?")
- ✅ Compare optimal vs actual line
- ✅ Better coaching and self-improvement tool

**File size impact:**
- Waypoints: ~150-300 waypoints × 2 coords = ~600-1200 bytes (~1KB!)
- Negligible compared to ~1MB CSV file
- Total increase: < 0.1%

---

## Next Steps - Testing Required!

### 1. Test REST API Endpoint
```bash
python test_trackmap_endpoint.py
```

**Questions to answer:**
- How many waypoints per track?
- What fields are in each waypoint?
- Do coordinates match our X/Z system?
- Is there sector/racing line data?

### 2. Check Swagger Documentation
Visit `http://localhost:6397/swagger/index.html` while LMU is running

### 3. Share Results
Post the output so we can design the optimal data structure

---

## Files Created

- ✅ **`TRACK_OUTLINE_IMPLEMENTATION.md`** - Complete implementation plan
- ✅ **`test_trackmap_endpoint.py`** - Test script for REST API
- ✅ **`TRACK_MAP_APPROACH_ANALYSIS.md`** - Detailed analysis
- ✅ **`TRACK_MAP_OPTIONS_SUMMARY.md`** - This summary (updated)

---

## Sources

- [TinyPedal User Guide](https://github.com/TinyPedal/TinyPedal/wiki/User-Guide) - Track map recording and SVG format
- [TinyPedal Track Map Widget](https://github.com/IceNbrn/TinyPedal_LMU/blob/6a37edace5a0230fba4245f609416717710644b4/tinypedal/widget/track_map.py) - Implementation reference
- [lmu-steward-companion](https://github.com/supaflyENJOY/lmu-steward-companion/blob/13cdd75a714d34ca7d060def69be470fb18af5f5/src-tauri/src/lmu_rest_api/client.rs#L491) - REST API example
- [Le Mans Ultimate Community - REST API Discussion](https://community.lemansultimate.com/index.php?threads%2Frest-api-documentation.3278%2F=)

---

**Updated:** 2025-11-22 - Corrected to reflect goal of ENHANCING driven line with track outline (not replacing)
