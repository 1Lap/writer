# Windows Setup Checklist

Quick reference for continuing development on Windows (Phase 6).

## Prerequisites

- [ ] Python 3.9+ installed on Windows
- [ ] Git installed
- [ ] Le Mans Ultimate installed
- [ ] **LMU Runtime Dependencies installed** (see below)
- [ ] GitHub authentication configured

### Install LMU Runtime Dependencies

⚠️ **Required for pyRfactor2SharedMemory to work**

The telemetry library requires Visual C++ runtimes to access LMU's shared memory. These ship with LMU:

1. Navigate to: `C:\Program Files (x86)\Steam\steamapps\common\Le Mans Ultimate\support\runtimes\`
2. Install all runtime installers in this folder:
   - `vc_redist.x64.exe` (Visual C++ Redistributable)
   - Any other installers present
3. Restart your computer (recommended)

**Note**: If you've already played LMU, these may already be installed.

## Initial Setup

### 1. Clone Repository
```bash
git clone git@github.com:1Lap/writer.git
cd writer
```

### 2. Create Virtual Environment
```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies
```bash
# Core dependencies
pip install -r requirements.txt

# Development dependencies
pip install -r requirements-dev.txt

# Windows-specific dependencies (includes pyRfactor2SharedMemory)
pip install -r requirements-windows.txt
```

### 4. Verify Setup
```bash
# Run all tests (should see 61 passing)
pytest -v

# Check if everything works
python example_app.py
# Should start but won't collect data (LMU not running)
# Press Ctrl+C to exit
```

## Phase 6 Tasks

### Implement RealTelemetryReader

1. **Study the library:**
   ```python
   # In Python REPL:
   import pyRfactor2SharedMemory as sm
   help(sm)
   ```

2. **Edit `src/telemetry/telemetry_real.py`:**
   - Import pyRfactor2SharedMemory
   - Implement `is_available()` - check if shared memory accessible
   - Implement `read()` - read data and map to our dict format
   - Implement `get_session_info()` - get track, car, session details

   **Reference:** See `src/telemetry/telemetry_mock.py` for the exact dict structure expected

3. **Key fields to map:**
   - Basic: lap, speed, engine_rpm, throttle, brake, steering, gear
   - Position: position_x, position_y, position_z, lap_distance
   - Wheel data: brake_temp, tyre_temp, wheel_speed (all have fl/fr/rl/rr)
   - Suspension: suspension_position, suspension_velocity, suspension_acceleration
   - See `telemetry_mock.py` lines 40-200 for complete field list

### Testing with LMU

1. **Start LMU:**
   - Launch Le Mans Ultimate
   - Start a practice session
   - Don't need to drive yet

2. **Test telemetry reading:**
   ```bash
   # Quick test script
   python -c "from src.telemetry.telemetry_interface import get_telemetry_reader; r = get_telemetry_reader(); print('Available:', r.is_available()); print('Data:', r.read())"
   ```

3. **Run example app:**
   ```bash
   python example_app.py
   ```

   Expected behavior:
   - Detects LMU.exe process ✓
   - Reads telemetry ✓
   - Shows status updates every 5s
   - Drive a lap in LMU
   - Should detect lap completion and save CSV

4. **Verify CSV output:**
   - Check `telemetry_output/` directory
   - Compare output CSV with the LMUTelemetry v2 reference (`example.csv` updated MVP sample)
   - Verify all 6 sections present
   - Check field values make sense

### Write Tests (TDD)

If adding new functionality:

1. Write test first in `tests/test_telemetry_real.py`
2. Run test - should fail
3. Implement feature
4. Run test - should pass
5. Don't modify test unless absolutely necessary

### Common Issues

**Shared memory not available:**
- LMU must be running
- Check if LMU plugin is enabled (should be by default)
- **Install LMU runtimes** (see Prerequisites above) - most common cause
- Try restarting LMU

**Import errors or DLL load failures:**
- Verify `pip install -r requirements-windows.txt` succeeded
- Check virtual environment is activated
- **Install LMU runtimes** from `LMU/support/runtimes/` (see Prerequisites above)
- Ensure you installed the x64 version of Visual C++ Redistributable

**CSV format mismatches:**
- Compare field-by-field with the MVP reference CSV
- Check CSVFormatter section order
- Verify all wheel data is in correct order (rl, rr, fl, fr)

**Tests failing:**
- Run `pytest -v` to see which specific test
- Check if platform detection works: `python -c "import sys; print(sys.platform)"`
- Should print 'win32' on Windows

## Quick Commands

```bash
# Activate venv
venv\Scripts\activate

# Run tests
pytest -v

# Run example app
python example_app.py

# Check git status
git status

# Commit changes
git add -A
pytest -v  # Verify tests pass first!
git commit -m "your message"
git push
```

## Success Criteria for Phase 6

- [ ] `RealTelemetryReader` implemented
- [ ] Reads live data from LMU shared memory
- [ ] `example_app.py` works with LMU running
- [ ] CSV files generated in `telemetry_output/`
- [ ] CSV format matches LMUTelemetry v2 schema
- [ ] All 61 tests still passing
- [ ] Can complete a lap and get saved CSV

## Need Help?

1. Check `.claude/CLAUDE.md` for full project context
2. Check `TECHNICAL_SPEC.md` for component details
3. Look at `telemetry_mock.py` for expected data structure
4. Compare with the MVP reference CSV for format compliance
5. Ask Claude for guidance - reference the CLAUDE.md file

---

**Next:** Once Phase 6 is complete, move to Phase 7 (PyInstaller .exe build)
