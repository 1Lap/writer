# Track Map Approach Analysis

## Current Situation

Our telemetry logger currently captures X and Z coordinates (position data) for every telemetry sample:
- **Field names**: `X [m]`, `Z [m]` (using X/Z as 2D plane, Y is height)
- **Source**: LMU shared memory (`mPos` field)
- **Frequency**: ~100Hz (every telemetry sample)
- **Size impact**: ~2 columns × ~11,000 samples per lap = part of the ~1MB CSV size

The lap viewer uses these X/Z coordinates to:
1. Render the track map showing the driven line
2. Project the car position on the track during replay
3. Overlay multiple laps on the same track map

## Proposed Alternative: REST API Track Maps

The lmu-steward-companion project uses the LMU REST API endpoint:
```
GET http://localhost:6397/rest/watch/trackmap
```

This returns a collection of waypoints representing the track outline.

### Potential Approaches

#### **Approach 1: Replace X/Z with Track Map Reference**
- Fetch track map via REST API once per session
- Remove X/Z coordinates from telemetry samples
- Reference track map by track name in metadata
- Build a library of track maps (keyed by track name)

**Pros:**
- Smaller CSV files (remove 2 columns × 11k rows)
- Standardized track outlines across all laps
- Could include racing line, sector markers, etc.

**Cons:**
- Loses actual driven line (can't see where driver went off-track)
- Requires REST API to be running
- Need to build/maintain track map library
- Track map may not match actual driven line (pit lane, variants, etc.)

#### **Approach 2: Hybrid - Include Both**
- Keep X/Z coordinates in telemetry samples (actual driven line)
- Add track map waypoints to metadata section
- Lap viewer can show both:
  - Track outline (from waypoints)
  - Actual driven line (from X/Z samples)

**Pros:**
- Best of both worlds
- Can highlight deviations from ideal line
- Fallback if track map not available

**Cons:**
- Larger CSV files (waypoints in metadata + X/Z in samples)
- More complex lap viewer logic

#### **Approach 3: Library of Pre-Built Track Maps**
- Fetch track maps via REST API (manually or on-demand)
- Build a separate repository of track maps (JSON files)
- CSV only references track by name
- Lap viewer loads track map separately

**Pros:**
- Much smaller CSV files (no X/Z coordinates)
- Track maps can be shared across applications
- Can enhance with additional data (sectors, DRS zones, pit lane)

**Cons:**
- Loses actual driven line
- Requires separate track map distribution
- What if track gets updated?
- Offline workflow broken (need track map files)

#### **Approach 4: Status Quo - Keep X/Z in Samples**
- Continue using X/Z from shared memory
- No REST API dependency
- Track map is inherently accurate to driven line

**Pros:**
- Already working
- No additional complexity
- Perfect representation of actual driven line
- Works offline
- No external dependencies

**Cons:**
- Larger CSV files
- Each lap has its own map data (not shared)

## Investigation Required

Before making a decision, we should:

1. **Test the endpoint** - Run `test_trackmap_endpoint.py` with LMU to see:
   - What fields are in each waypoint?
   - How many waypoints per track?
   - How does it compare to our X/Z data?
   - Is there sector/racing line data?

2. **Analyze lap viewer needs** - Does the viewer need:
   - Just a track outline? (REST API waypoints sufficient)
   - Actual driven line? (Need X/Z from samples)
   - Both for comparison?

3. **Measure size impact**:
   - Current: X/Z in samples (~1MB per lap)
   - With waypoints: How much do waypoints add to metadata?
   - Without X/Z: How much do we save?

## Recommendation (Preliminary)

**Keep Approach 4 (Status Quo)** unless testing reveals compelling reasons to change.

**Why:**
1. **Actual driven line is valuable** - Shows exactly where the driver went, including:
   - Off-track excursions
   - Pit lane entry/exit
   - Track variant taken
   - Racing line vs. mistake

2. **No dependencies** - Works without REST API running

3. **Simplicity** - One data source, one representation

4. **File size is acceptable** - ~1MB per lap is small by modern standards

5. **Offline workflow** - CSV is self-contained

**When to reconsider:**
- If lap viewer needs standardized track outlines (e.g., for track limits, sector markers)
- If we want to add racing line comparison
- If file size becomes a real problem (unlikely)
- If we're building multi-lap session analysis (shared track map reduces redundancy)

## Next Steps

1. **Run test script on Windows with LMU**:
   ```bash
   python test_trackmap_endpoint.py
   ```

2. **Share output** to analyze waypoint structure

3. **If waypoints look useful**, consider Approach 2 (hybrid):
   - Add optional track map waypoints to metadata
   - Keep X/Z in samples for driven line
   - Enhance lap viewer to show both

4. **If waypoints not useful**, keep current approach

## Open Questions

- What format are waypoints in? (X/Z coordinates? Lat/lon?)
- How many waypoints per track? (100? 1000? 10000?)
- Do waypoints include additional data (sector markers, pit lane, racing line)?
- Can we correlate our X/Z samples to waypoints?
- Does the track map change based on layout variant?
