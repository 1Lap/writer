**Status**: FIXED ✅ (Duplicate of opponent_tracking_depends_on_player_state.md)
**Fixed**: 2025-11-20 (v0.2.1)

## Issue

opponent laps are only detected if the local player is driving.

and they are discarded if the local player stops driving.

## Resolution

This issue was fixed in v0.2.1 by moving opponent tracking outside of player session logic. See `bugs/opponent_tracking_depends_on_player_state.md` for full details.

**Changes Made**:
- Opponent tracking now runs independently of player state
- Opponents are tracked even when player is in garage or suspended
- All 93 tests passing
