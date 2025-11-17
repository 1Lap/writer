# Known Bugs and Issues

## Performance Issues

### Low Capture Rate (~20Hz instead of 100Hz)
**Status**: Open
**Priority**: Medium
**Discovered**: 2025-11-18

**Description**:
The telemetry logger is capturing data at approximately 20Hz instead of the target 100Hz polling rate.

**Evidence**:
- Lap 3: 10,915 samples over 537 seconds = ~20.3 Hz
- Lap 4: Similar sample count (11 MB file size)
- Configuration specifies `poll_interval: 0.01` (100Hz)

**Potential Causes**:
1. Shared memory API may be slow to read
2. CSV formatting/buffering may be blocking the loop
3. Process detection or telemetry availability checks taking too long
4. Python GIL or sleep precision issues

**Impact**:
- Lower resolution telemetry data
- May miss fast transients (spikes in G-force, quick steering inputs)
- Still functional for lap analysis but not ideal for detailed analysis

**Next Steps**:
- Profile the telemetry loop to identify bottlenecks
- Consider moving CSV formatting to a background thread
- Investigate if shared memory reads can be optimized
- Test with different poll intervals

---

## Future Enhancements

### Car Setup Data Not Captured
**Status**: Enhancement
**Priority**: Low

Currently the car setup section shows all zeros. Need to map setup data from shared memory if available.

### Some Telemetry Fields Default to Zero
**Status**: Enhancement
**Priority**: Low

Fields not available in shared memory:
- Oil pressure
- Wind speed/direction
- DRS availability
- Suspension acceleration
- Some wheel/tire metrics

These are set to default values (0.0) in the output.
