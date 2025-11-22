# Track Map Options - Summary & Recommendation

## What We Discovered

### The lmu-steward-companion Approach
The referenced project uses the LMU REST API endpoint:
```
GET http://localhost:6397/rest/watch/trackmap
```

This returns a collection of `Waypoint` objects that represent the track outline.

**Unknown details** (need testing to determine):
- Waypoint structure (X/Z coordinates? How many per track?)
- Whether it includes racing line, sector markers, etc.
- How it compares to our current X/Z position data

### Our Current Approach
We capture X/Z coordinates from LMU shared memory for every telemetry sample:
- **Frequency**: ~100Hz (every sample, ~11,000 per lap)
- **Fields**: `X [m]`, `Z [m]` (2D plane for track mapping)
- **Source**: `mPos` field from shared memory
- **Size**: 2 columns × 11,000 rows = part of our ~1MB CSV

**Lap viewer requirements**:
- Browser-based tool (drag CSV onto `index.html`)
- Needs X/Z coordinates to draw track map
- Uses position data to show driven line and car location during replay

## Three Options to Consider

### Option 1: Status Quo (RECOMMENDED)
**Keep using X/Z from telemetry samples**

```
✅ Already working
✅ Shows actual driven line (not just track outline)
✅ No REST API dependency
✅ Works offline
✅ Self-contained CSV files
✅ Shows off-track excursions, pit lane, variants

❌ Larger CSV files (~1MB per lap)
❌ Redundant if multiple laps on same track
```

**Best for**: Current use case where we want to see exactly where the driver went

---

### Option 2: Replace with Track Map Library
**Fetch track maps via REST API, build a library, reference by track name**

```
✅ Smaller CSV files (remove X/Z columns)
✅ Standardized track outlines
✅ Could enhance with racing line, sectors, DRS zones

❌ Loses actual driven line
❌ Requires REST API running during session
❌ Need to build/maintain track map library
❌ Breaks offline workflow
❌ Can't see where driver went off-track
❌ Doesn't work for track variants or pit lane
```

**Best for**: If file size is critical AND you only need track outline (not actual driven path)

---

### Option 3: Hybrid Approach
**Include track map waypoints in metadata + keep X/Z in samples**

```
✅ Best of both worlds
✅ Track outline + actual driven line
✅ Can highlight deviations from ideal line
✅ Fallback if track map not available

❌ Largest CSV files (waypoints in metadata + X/Z in samples)
❌ More complex lap viewer logic
❌ REST API dependency
❌ Additional implementation effort
```

**Best for**: Advanced analysis (compare driven line vs. ideal line)

---

## Recommendation: **Keep Status Quo (Option 1)**

**Why:**

1. **Actual driven line is valuable**
   - See exactly where the driver went
   - Identify off-track excursions
   - Show pit lane entry/exit
   - Handle track variants correctly

2. **File size is not a problem**
   - ~1MB per lap is small by modern standards
   - Storage is cheap
   - CSV compresses well (gzip can reduce by 70-80%)

3. **Simplicity**
   - One data source (shared memory)
   - No REST API dependency
   - Works offline
   - Self-contained files

4. **Already working**
   - No implementation effort
   - No risk of regression
   - Proven in production

**When to reconsider:**

- **If file size becomes critical** (unlikely - 1MB is tiny)
- **If we add racing line analysis** (then consider Option 3)
- **If lap viewer needs standardized track outlines** (for track limits, sector markers)
- **If building multi-session analysis tools** (shared track maps reduce redundancy)

---

## Testing Next Steps (Optional)

If you want to explore the REST API approach anyway:

1. **Run the test script on Windows**:
   ```bash
   python test_trackmap_endpoint.py
   ```

2. **Analyze the waypoint structure**:
   - How many waypoints per track?
   - What fields are included?
   - How do they compare to our X/Z samples?

3. **Share the output** so we can evaluate if waypoints provide value

4. **If waypoints look useful**, we could:
   - Add optional track map waypoints to metadata (Option 3)
   - Keep X/Z in samples for driven line
   - Enhance lap viewer to show both track outline + driven line

---

## Implementation Effort Comparison

| Option | Effort | Risk | Value |
|--------|--------|------|-------|
| **Option 1 (Status Quo)** | None ✅ | None ✅ | High (actual driven line) ✅ |
| **Option 2 (Library)** | High (REST client, library, lap viewer changes) | High (lose driven line data) | Low (marginal file size savings) |
| **Option 3 (Hybrid)** | High (REST client, metadata format, lap viewer changes) | Medium (added complexity) | Medium (racing line comparison) |

---

## Conclusion

**Stick with the current approach.** We already capture X/Z coordinates from shared memory, which provides:
- Accurate representation of the actual driven line
- Self-contained CSV files that work offline
- Proven functionality with the lap viewer
- Acceptable file size (~1MB per lap)

The REST API track map approach might be useful for:
- Building a separate track database
- Adding racing line reference data
- Multi-lap session analysis

But for our current use case (single lap telemetry export), the added complexity doesn't justify the marginal benefits.

---

## Files Created for Reference

- **`test_trackmap_endpoint.py`** - Test script to explore the REST API endpoint
- **`TRACK_MAP_APPROACH_ANALYSIS.md`** - Detailed analysis of all approaches
- **`TRACK_MAP_OPTIONS_SUMMARY.md`** - This summary document

If you want to proceed with testing the REST API approach, run the test script and share the output!
