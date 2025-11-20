## Status: FIXED ✅
**Priority**: Medium
**Fixed**: 2025-11-20

---

## Original Issue

I notice that we are saving more than one opponent lap per opponent, maybe because of the timestamp in the filename?

eg:

in one session just then we saved two from the same driver:

2025-11-20_17-24_sebring-international-raceway_gt3_unknown_felicio-tamaja_lap1_t129s
2025-11-20_17-26_sebring-international-raceway_gt3_unknown_felicio-tamaja_lap2_t127s


If use the "session id" instead of the date/time would help us keep just one opponent lap per session, we should move to that.

---

## Resolution Summary

**Root Cause:**
The opponent tracking system correctly returns only faster laps (OpponentTracker working as designed), but each lap was saved with a unique filename because:
1. The default filename format used `{date}_{time}` which changed for each lap
2. The format also included `{lap}` and `{lap_time}` which were different for each lap
3. Result: lap1 and lap2 had different filenames, so both were saved instead of lap2 overwriting lap1

**Solution Implemented:**
1. Modified `FileManager.save_lap()` to accept an optional `filename_format` parameter
2. Modified `example_app.py` to use a custom format for opponent laps: `{session_id}_{track}_{car}_{driver}_fastest.csv`
3. This ensures each opponent has exactly ONE file per session that gets overwritten with faster laps

**Files Changed:**
- `src/file_manager.py`: Added optional `filename_format` parameter to `save_lap()` and `_generate_filename()`
- `example_app.py`: Uses custom opponent filename format to ensure overwrites

**Result:**
- ✅ Only one opponent lap file per opponent per session
- ✅ Faster laps automatically overwrite previous laps (same filename)
- ✅ Player laps unaffected (still use default date/time format)
- ✅ All 93 tests passing

**Example Behavior (After Fix):**
- Opponent lap 1 (129s): Saved as `session123_sebring_gt3_car_felicio-tamaja_fastest.csv`
- Opponent lap 2 (127s): Overwrites with `session123_sebring_gt3_car_felicio-tamaja_fastest.csv` (same filename!)
- Result: Only the fastest lap (127s) remains
