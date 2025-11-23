## Status: ✅ RESOLVED

**Resolved:** 2025-11-23
**Solution:** Implemented on_session_start callback to fetch REST API data once per session instead of on every lap completion

**Implementation Details:**
- Added `on_session_start` callback to `TelemetryLoop` (triggered on DETECTED → LOGGING transition)
- Implemented session-level caching in both `example_app.py` and `tray_app.py`
- REST API calls (track map and vehicle metadata) now happen ONCE when session starts
- Lap completion callback now uses cached session data instead of making API calls
- All 198 tests passing, no regressions

**Files Changed:**
- `src/telemetry_loop.py` - Added on_session_start callback support
- `example_app.py` - Implemented session-level caching of REST API data
- `tray_app.py` - Implemented session-level caching of REST API data

---

# REST API Causes Game Stuttering - Cache Track Map on Session Start

**Date Reported:** 2025-11-23
**Priority:** High (RESOLVED)
**Component:** REST API Integration, Session Management
**Type:** Performance Bug

## Description

Calling the LMU REST API during lap completion causes the game (Le Mans Ultimate) to stutter. This is particularly problematic because the track map is fetched on every lap, even though it's cached. The API call or cache check during lap completion impacts game performance.

## Expected Behavior

- REST API should only be called when absolutely necessary
- Track map should be fetched **once per session** (on session start)
- Cached data should be reused for all laps in the same session
- Game performance should not be affected by telemetry logging

## Actual Behavior

- Track map is fetched on **every lap completion** (line 125 in `example_app.py`)
- Even with caching, the code path executes the lookup on each lap
- This causes noticeable game stuttering during racing
- Impacts user experience and race performance

## Root Cause

### Current Implementation

The track map fetch happens in `on_lap_complete()` callback:

```python
# example_app.py lines 122-131 (on EVERY lap)
def on_lap_complete(self, lap_data, lap_summary):
    # ... other code ...

    # Fetch track map (once per track, cached)
    track_name = session_info.get('track_name', '')
    if track_name:
        trackmap_data = self.telemetry_reader.rest_api.get_trackmap(track_name=track_name)
        if trackmap_data:
            # Add track map to session_info for metadata
            session_info['track_map'] = trackmap_data.get('track', [])
            # ... more assignments
```

**Problem:** This runs on every lap completion, even though:
1. The track doesn't change during a session
2. Caching is already implemented in `LMURestAPI.get_trackmap()`
3. The HTTP request or cache check itself may cause stuttering

### Why This Causes Stuttering

1. **Timing-sensitive context** - Lap completion is a critical moment in racing
2. **HTTP overhead** - Even if cached, there's still Python function call overhead
3. **I/O operations** - Any blocking I/O (even fast) can cause frame drops
4. **LMU sensitivity** - Game engine may be sensitive to external processes making network calls

## Proposed Solution

### Option A: Fetch on Session Start (Recommended)

Move track map fetching to session initialization, before logging begins.

**Implementation:**

1. **Detect session start** in `SessionManager`:
   ```python
   # src/session_manager.py
   def on_session_start(self):
       """Called when session first detected"""
       # Fetch track map here, store in session metadata
       if self.rest_api:
           track_name = self.get_track_name()
           self.session_trackmap = self.rest_api.get_trackmap(track_name)
   ```

2. **Store in session context** instead of fetching per lap:
   ```python
   # example_app.py - on_lap_complete()
   # REMOVE the trackmap fetch from here

   # Instead, get it from session context:
   if hasattr(self.telemetry_loop.session_manager, 'session_trackmap'):
       trackmap_data = self.telemetry_loop.session_manager.session_trackmap
       if trackmap_data:
           session_info['track_map'] = trackmap_data.get('track', [])
           # ... etc
   ```

3. **Clear on session end** to free memory:
   ```python
   def on_session_end(self):
       self.session_trackmap = None
   ```

### Option B: Lazy Load Once Per Session

Fetch on first lap only, store in application state:

```python
class TelemetryApp:
    def __init__(self):
        self.session_trackmap_cache = {}  # track_name -> trackmap_data
        self.current_track = None

    def on_lap_complete(self, lap_data, lap_summary):
        track_name = session_info.get('track_name', '')

        # Only fetch if we don't have it for this track yet
        if track_name and track_name not in self.session_trackmap_cache:
            trackmap_data = self.telemetry_reader.rest_api.get_trackmap(track_name)
            self.session_trackmap_cache[track_name] = trackmap_data

        # Use cached data
        trackmap_data = self.session_trackmap_cache.get(track_name, {})
        if trackmap_data:
            session_info['track_map'] = trackmap_data.get('track', [])
```

### Option C: Pre-fetch in Background Thread

Fetch asynchronously when session is detected, before lap completion:

```python
def on_session_detected(self):
    """Background fetch when session detected but before lap 1 completes"""
    if not self.trackmap_loaded:
        threading.Thread(
            target=self._prefetch_trackmap,
            daemon=True
        ).start()

def _prefetch_trackmap(self):
    track_name = self.get_track_name()
    self.rest_api.get_trackmap(track_name)  # Populates cache
    self.trackmap_loaded = True
```

## Recommended Approach

**Option A (Session Start)** is recommended because:
1. ✅ Completely eliminates API calls during racing
2. ✅ Track map available from lap 1
3. ✅ Simplest to implement and understand
4. ✅ No threading complexity
5. ✅ Minimal code changes

## Implementation Steps

1. **Add session start hook to SessionManager**:
   - Detect when session transitions from IDLE → DETECTED
   - Add callback for session initialization
   - Store track map in session context

2. **Update TelemetryApp to use session start**:
   - Register session start callback
   - Fetch track map in callback (once)
   - Store in session manager or app state

3. **Remove track map fetch from lap completion**:
   - Delete lines 122-131 from `example_app.py`
   - Replace with session context lookup
   - Add fallback for edge cases (track map not loaded)

4. **Test performance**:
   - Run with live LMU
   - Verify no stuttering during lap completion
   - Confirm track map data is present in CSV
   - Check multiple tracks in same session

## Testing Requirements

### Functional Tests
- [ ] Track map fetched on session start (before lap 1)
- [ ] Track map present in all lap CSV files
- [ ] Track map correct for multi-track sessions
- [ ] Graceful handling if API unavailable
- [ ] Cache persists across multiple laps
- [ ] No duplicate API calls per session

### Performance Tests
- [ ] No game stuttering during lap completion
- [ ] No frame drops when lap completes
- [ ] Background telemetry logging imperceptible
- [ ] CPU usage minimal during racing
- [ ] Memory usage stable (no leaks)

### Edge Cases
- [ ] Session start with API unavailable → no crash
- [ ] Track change mid-session → fetch new track map
- [ ] Session restart → clear old track map
- [ ] Multiple sessions → separate track maps
- [ ] Empty track name → no API call

## Related Files

- `example_app.py` - **Lines 122-131** (REMOVE trackmap fetch from lap completion)
- `tray_app.py` - Same issue if using track map
- `src/session_manager.py` - Add session start callback
- `src/lmu_rest_api.py` - Already has caching (no changes needed)
- `src/telemetry_loop.py` - May need session start event
- `tests/test_session_manager.py` - Add tests for session start
- `tests/test_example_app_integration.py` - Update integration tests

## Environment

- **Platform:** Windows
- **Game:** Le Mans Ultimate (LMU)
- **API:** LMU REST API (localhost:6397)
- **Impact:** All users during active racing

## Performance Impact

### Current Impact (Negative)
- **Game stuttering** during lap completion
- **Poor user experience** during critical racing moments
- **Potential for crashes/incidents** due to frame drops
- **Professional appearance** compromised

### Expected Improvement
- **Zero stuttering** during lap completion
- **Seamless telemetry logging** in background
- **Better user experience** and race performance
- **No noticeable impact** on game performance

## Additional Notes

### Other REST API Usage

Review all REST API calls for similar issues:

1. **Vehicle metadata fetch** (`fetch_vehicle_data()`):
   - Also in `example_app.py` (line 111)
   - Should also be moved to session start
   - Vehicle list doesn't change during session

2. **Session endpoint** (`is_available()`):
   - Used for API availability check
   - Acceptable for one-time checks
   - Don't call repeatedly during racing

### REST API Call Inventory

Current REST API endpoints used:
- `/rest/sessions` - Availability check (OK, minimal)
- `/rest/sessions/getAllVehicles` - Vehicle metadata (MOVE to session start)
- `/rest/watch/trackmap` - Track map waypoints (MOVE to session start - **THIS BUG**)

### Best Practices for REST API Integration

1. **Fetch at session boundaries** (start/end), not during racing
2. **Cache aggressively** - data rarely changes mid-session
3. **Use background threads** for non-critical fetches
4. **Fail gracefully** - telemetry should work without REST API
5. **Minimize calls** - combine data where possible

### Future Enhancements

- **Pre-warming cache** on application startup
- **Persistent cache** across application restarts
- **Background refresh** during menu/pit stops (safe times)
- **GraphQL batching** if API supports it
- **WebSocket subscription** for real-time updates (instead of polling)

## Acceptance Criteria

This bug is resolved when:
1. Track map is fetched **once per session** (not per lap)
2. No REST API calls occur during lap completion
3. Game performance is unaffected by telemetry logging
4. No stuttering observed during racing
5. Track map data correctly appears in all lap CSV files
6. Tests verify session-start fetching behavior
7. Code is cleaner and more efficient

## Related Issues

- Performance optimization (BUGS.md mentions 20Hz vs 100Hz issue)
- Vehicle metadata caching (same pattern should be applied)
- API reliability and error handling

## Priority Justification

**High Priority** because:
- Directly impacts user experience during racing
- Causes stuttering at critical moments (lap completion)
- Affects core value proposition (background telemetry)
- Simple fix with significant impact
- User-reported issue requiring quick resolution
