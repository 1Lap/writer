# Track Map Type Field Analysis Results

## Test Results (2025-11-22)

### Summary Statistics
- **Total waypoints**: 1,347
- **Unique type values**: 78 (range 0-143)
- **Track distance**: 7,983.80 meters
- **Average spacing**: 5.93 meters between waypoints

### Type Distribution

#### Dominant Types (88.7% of all waypoints)

**Type 0: Racing Line / Track Centerline** (63.4%)
- **Waypoints**: 854
- **Spatial coverage**: Full track (X: -152.14 to 501.74, Z: -449.12 to 588.49)
- **Sequential pattern**: ONE continuous run of 854 waypoints
- **Interpretation**: Primary racing line or track centerline

**Type 1: Track Edge / Alternative Line** (25.3%)
- **Waypoints**: 341
- **Spatial coverage**: Full track (X: -144.61 to 473.56, Z: -423.79 to 372.94)
- **Sequential pattern**: ONE continuous run of 341 waypoints
- **Interpretation**: Track boundary, edge, or alternative racing line

**Types 2-143: Markers & Features** (11.3%)
- **Waypoints**: 2 each (152 total across 76 different types)
- **Spatial coverage**: Highly localized (small X/Z ranges)
- **Sequential pattern**: Small runs of 2 waypoints each
- **Interpretation**: Distance markers, sector boundaries, or track features

### Key Insights

#### 1. Two Main Track Lines
The data clearly shows **two complete track paths**:
- **Type 0**: 854 waypoints covering the full track (likely racing line)
- **Type 1**: 341 waypoints covering the full track (likely track edge or inner/outer boundary)

Together these represent **88.7%** of all waypoints and provide complete track coverage.

#### 2. Sequential Structure
The waypoints are **highly clustered by type**:
- Type 0: Single run of 854 consecutive waypoints
- Type 1: Single run of 341 consecutive waypoints
- Types 2+: Pairs of waypoints (likely markers every X meters)

This suggests the API returns waypoints in **type-sequential order** rather than distance order.

#### 3. Sparse Markers
Types 2-143 are **distance/sector markers**:
- Each type appears exactly twice (2 waypoints)
- Highly localized positions
- 78 different type values for 152 waypoints
- Likely represents markers every ~50-100 meters along track

### Recommended Filtering Strategies

#### **Option A: Racing Line Only (Type 0)**

```python
waypoints = [w for w in data if w['type'] == 0]
# Result: 854 waypoints, ~5.5m spacing
```

**Pros:**
- ✅ Primary racing line
- ✅ Still high density (854 waypoints)
- ✅ Smaller file size (~20KB)

**Cons:**
- ❌ No track boundaries for width analysis
- ❌ Missing alternative line comparison

**Use case:** Basic track outline for lap overlay

---

#### **Option B: Racing Line + Track Edge (Types 0 & 1)** ⭐ RECOMMENDED

```python
waypoints = [w for w in data if w['type'] in [0, 1]]
# Result: 1,195 waypoints (854 + 341)
```

**Pros:**
- ✅ Racing line AND track boundary
- ✅ Enables track width analysis
- ✅ Can show if driver used full track
- ✅ Two reference lines for comparison
- ✅ Still manageable size (~30KB)

**Cons:**
- ⚠️ Slightly larger than Option A

**Use case:** Track outline + width/apex analysis (PERFECT for your goal!)

---

#### **Option C: All Waypoints (All Types)**

```python
waypoints = data  # All 1,347 waypoints
```

**Pros:**
- ✅ Complete data set
- ✅ Includes sector/distance markers
- ✅ Maximum detail

**Cons:**
- ⚠️ Larger file size (~80KB)
- ⚠️ Needs type-aware rendering in lap viewer
- ⚠️ Complexity in parsing/filtering

**Use case:** Advanced features (sector visualization, distance markers)

---

#### **Option D: Downsampled Racing Line**

```python
racing_line = [w for w in data if w['type'] == 0]
waypoints = racing_line[::3]  # Every 3rd waypoint
# Result: ~285 waypoints, ~16.5m spacing
```

**Pros:**
- ✅ Minimal file size (~7KB)
- ✅ Still sufficient for track outline

**Cons:**
- ❌ Lower detail (may miss tight corners)
- ❌ No track boundaries

**Use case:** If file size is critical (not necessary for you)

---

## Final Recommendation: **Option B (Types 0 & 1)**

### Why This is Perfect for Your Use Case:

1. **Answers "Did I hit the apex?"**
   - Type 0 shows ideal racing line
   - Your driven line shows where you actually went
   - Compare the two!

2. **Answers "Did I use all available track?"**
   - Type 1 shows track boundary/edge
   - See if you got close to the edge in corners
   - Analyze track width usage

3. **Manageable Size**
   - 1,195 waypoints = ~30KB
   - Only 3% of 1MB CSV file
   - Negligible impact

4. **Simple Implementation**
   - Just filter `type in [0, 1]`
   - No complex downsampling logic
   - Two distinct lines for visualization

### Implementation Approach

```python
def get_trackmap_for_csv(waypoints: List[Dict]) -> Dict[str, Any]:
    """
    Extract track map data for CSV export

    Returns both racing line (type 0) and track edge (type 1)
    for apex and track width analysis
    """
    # Filter to racing line and track edge
    track_data = [w for w in waypoints if w['type'] in [0, 1]]

    # Group by type for structured output
    racing_line = [[w['x'], w['z']] for w in waypoints if w['type'] == 0]
    track_edge = [[w['x'], w['z']] for w in waypoints if w['type'] == 1]

    return {
        'racing_line': racing_line,      # 854 waypoints
        'track_edge': track_edge,        # 341 waypoints
        'waypoint_count': len(track_data),
        'source': 'LMU_REST_API'
    }
```

### CSV Format

**Option B1: Separate Lines (Structured)**
```csv
TrackMapRacingLine,[[-152.14,-449.12],[-150.23,-445.67],...]
TrackMapEdge,[[-144.61,-423.79],[-142.45,-420.11],...]
TrackMapWaypoints,1195
TrackMapSource,LMU_REST_API
```

**Option B2: Combined with Type (Flexible)**
```csv
TrackMap,[{"t":0,"x":-152.14,"z":-449.12},{"t":0,"x":-150.23,"z":-445.67},...]
TrackMapWaypoints,1195
TrackMapSource,LMU_REST_API
```

**Recommendation: Option B1 (Structured)** - Easier for lap viewer to parse

---

## What About Types 2-143?

These appear to be **distance/sector markers**:
- 2 waypoints per type value
- Highly localized (small spatial clusters)
- Could represent:
  - Distance markers every 50-100m
  - Sector boundaries
  - DRS zones
  - Marshal posts
  - Other track features

**For now: IGNORE these types** for basic track outline. They can be added later for advanced features.

---

## Size Impact Analysis

### File Sizes:

| Option | Waypoints | Estimated Size | % of 1MB CSV | Use Case |
|--------|-----------|----------------|--------------|----------|
| Option A (Type 0) | 854 | ~20KB | 2% | Basic outline |
| **Option B (Types 0+1)** | **1,195** | **~30KB** | **3%** | **Outline + width** ⭐ |
| Option C (All types) | 1,347 | ~80KB | 8% | Full detail |
| Option D (Downsampled) | ~285 | ~7KB | 0.7% | Minimal |

**All options are acceptable** - even 80KB is only 8% overhead on a 1MB CSV.

---

## Next Steps

1. ✅ **Type field analyzed** - Types 0 & 1 are the key data
2. ⏳ **Implement Option B** in `LMURestAPI.get_trackmap()`
3. ⏳ **Update CSV formatter** to include both racing line and track edge
4. ⏳ **Update lap viewer** to render both lines
5. ⏳ **Test with multiple tracks** to confirm pattern holds

---

## Open Questions

1. **Is Type 1 the inner or outer edge?**
   - Spatial analysis shows it's slightly smaller range
   - Could be inner edge (apex side)
   - Or: alternative racing line for different conditions

2. **What do the numbered types (2-143) represent?**
   - Check Swagger docs for enum definition
   - Test with different tracks to see if pattern consistent
   - Potential for future enhancement (sector markers, DRS zones)

3. **Does the pattern hold for all tracks?**
   - Test with different circuits
   - Some tracks may have different type distributions
   - Implementation should gracefully handle variations

---

**Date:** 2025-11-22
**Track Tested:** Unknown (from user's LMU session)
**Total Waypoints:** 1,347
**Recommendation:** ⭐ **Option B - Types 0 & 1 (Racing Line + Track Edge)**
**Status:** ✅ Ready for implementation
