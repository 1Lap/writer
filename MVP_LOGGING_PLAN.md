## MVP Telemetry Logging Plan

### Goals
- Emit the trimmed CSV layout defined in `telemetry_format_analysis.md`: metadata preamble + the 12 required channels (LapDistance, LapTime, Sector, Speed, EngineRevs, Throttle%, Brake%, Steer%, Gear, X, Y, Z).
- Ensure values follow the specified units and ranges (e.g., throttle/brake 0–100 %, steering ±100 %, distances/time monotonic).
- Keep the existing pipeline (TelemetryLoop → SessionManager → CSVFormatter → FileManager) while adapting the formatter and data normalisation to the MVP contract.

### 1. Data Normalisation Layer
1. Add a helper (new module or within `SessionManager`) that converts raw telemetry samples into canonical fields:
   - `lap_distance_m`, `lap_time_s`, `sector_index`, `speed_kmh`, `engine_rpm`, `throttle_pct`, `brake_pct`, `steer_pct`, `gear`, `pos_x_m`, `pos_y_m`, `pos_z_m`.
2. Apply scaling inside this helper so upstream callers don’t repeat logic:
   - Multiply fractional throttle/brake (0–1) by 100 and clamp to `[0, 100]`.
   - Convert steering values to ±100 %.
   - Ensure coordinates use metres and return `None` when the sim omits them.
3. Use this helper either when buffering samples in `SessionManager.add_sample` or just before formatting to guarantee consistent structure for every lap file.

### 2. Metadata Collection
1. Extend `SessionManager` or introduce a `MetadataCollector` to capture session-level info:
   - Player, car, track, lap length, lap time, session timestamp, session ID.
2. On lap completion, compute:
   - `LapTime [s]`: last sample’s `lap_time_s`.
   - `TrackLen [m]`: max `lap_distance_m` or `track_length` from telemetry.
3. Ensure `session_info` passed to the formatter contains the required metadata block fields (`Format`, `Version`, `Player`, etc.) in addition to any optional entries.

### 3. CSV Formatter Rewrite
1. Replace `CSVFormatter.format_lap` so it emits:
   - Metadata lines (`Key,Value`) in the order specified (Format, Version, Player, TrackName, CarName, SessionUTC, LapTime [s], TrackLen [m], …).
   - A single telemetry header line `LapDistance [m],LapTime [s],…`.
   - One row per normalized sample with fixed precision (e.g., `f"{value:.2f}"` for floats) and empty strings for missing coordinates.
2. Remove the legacy multi-section format (player line, session metadata table, 90-column header) or guard it behind a feature flag if backward compatibility is required later.
3. Make sure the formatter sorts/validates samples by `lap_distance_m` before writing, even though the buffer should already be ordered.

### 4. Telemetry Loop Integration
1. When buffering samples:
   - Either store the normalized structure directly or convert the buffered list right before formatting.
2. Update the lap-completion callback to pass enriched `session_info` (with the metadata block fields) to `CSVFormatter`.
3. Adjust `example_app.py` to mention the MVP output format and ensure it still prints useful summary info (lap time, sample count).

### 5. Mock Telemetry Adjustments
1. Update `MockTelemetryReader` to emit the same units the MVP expects:
   - Return throttle/brake in 0–100 % instead of 0–1.
   - Provide steering in percent, not radians, or ensure the normaliser converts it.
2. Confirm `get_session_info` supplies all metadata keys the formatter now needs (player, car, track, track length).

### 6. Testing
1. Add unit tests for the normalization helper to cover:
   - Fractional inputs → 0–100 scaling.
   - Steering conversion and clamping.
   - Null-handling for coordinates.
2. Update `tests/test_csv_formatter.py` with expectations for:
   - Metadata block order.
   - Header string and number of columns.
   - Sample rows (precision, blank cells).
3. Extend integration tests (`tests/test_telemetry_loop.py`) to simulate a lap and verify the saved CSV matches the MVP structure (line counts, header, sample formatting).
4. Replace `example.csv` with an MVP-format reference file to support tests/doc examples.

### 7. Documentation
- Update `README.md`, `TECHNICAL_SPEC.md`, and `TELEMETRY_LOGGER_PLAN.md` to describe the new schema, emphasise 0–100 input scaling, and link to the full spec in `telemetry_format_analysis.md`.
- Document the expected file size (~0.6 MB per lap) and mention optional “extended” exports that retain full Telemetry Tool parity when needed.

### 8. Rollout Checklist
- [ ] Implement normalization helper and integrate it.
- [ ] Rewrite `CSVFormatter` to emit the MVP structure.
- [ ] Adjust mock telemetry values and metadata.
- [ ] Update docs/tests/examples.
- [ ] Run `pytest -v` and manually inspect a generated lap file to confirm the 12-column output and metadata block.
