"""Quick test of LMU telemetry connection"""
import sys
print(f"Python version: {sys.version}")
print(f"Platform: {sys.platform}")

try:
    from src.telemetry.telemetry_interface import get_telemetry_reader
    print("Creating telemetry reader...")
    reader = get_telemetry_reader()
    print(f"Reader type: {type(reader).__name__}")

    print("Checking if available...")
    avail = reader.is_available()
    print(f"Shared memory available: {avail}")

    if avail:
        print("Reading telemetry...")
        data = reader.read()
        if data:
            print(f"SUCCESS! Got telemetry data:")
            print(f"  Speed: {data.get('speed', 'N/A')} km/h")
            print(f"  RPM: {data.get('rpm', 'N/A')}")
            print(f"  Lap: {data.get('lap', 'N/A')}")
            print(f"  Player: {data.get('player_name', 'N/A')}")
        else:
            print("No data returned")
    else:
        print("Shared memory not available - is LMU running and on track?")

except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
