# Known Bugs and Issues

## Data Quality

### ✅ FIXED: Wrong Scale
**Status**: Fixed
**Fixed**: 2025-11-18

Throttle/brake/steering were captured as 0.00-1.00 values, but telemetry analysis expected 0-100%.

**Solution**: Implemented `SampleNormalizer` in `src/mvp_format.py` to automatically scale inputs to 0-100% range.

**Verification**: Live test confirmed correct scaling (brake: 61.26%, steer: -1.63%)


## Performance Issues

### Low Capture Rate (~43Hz instead of 100Hz)
**Status**: Open
**Priority**: Medium
**Discovered**: 2025-11-18
**Updated**: 2025-11-18

**Description**:
The telemetry logger is capturing data at approximately 43Hz instead of the target 100Hz polling rate.

**Evidence**:
- Initial test (old format): ~20Hz (10,915 samples / 537s)
- Latest test (MVP format): ~43Hz (12,972 samples / 302s)
- Configuration specifies `poll_interval: 0.01` (100Hz)
- Improvement: 2.1x faster than initial implementation

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
