"""
Test the LMU REST API /rest/watch/trackmap endpoint

This script explores the trackmap endpoint to see what waypoint data
is available that we could use for track map visualization.

Usage:
    1. Start LMU and load a track (practice/race session)
    2. Run: python test_trackmap_endpoint.py
"""

import json
import sys
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError


BASE_URL = "http://localhost:6397"


def test_trackmap_endpoint():
    """Fetch and display trackmap waypoints"""
    url = f"{BASE_URL}/rest/watch/trackmap"

    print("=" * 80)
    print("Testing LMU REST API /rest/watch/trackmap endpoint")
    print("=" * 80)
    print(f"\nURL: {url}\n")

    try:
        req = Request(url)
        with urlopen(req, timeout=2) as response:
            if response.status == 200:
                data = json.loads(response.read().decode('utf-8'))

                print(f"Status: {response.status} OK")
                print(f"Response type: {type(data).__name__}")
                print(f"Number of waypoints: {len(data) if isinstance(data, list) else 'N/A'}")
                print("\n" + "=" * 80)
                print("Full response (first 3 waypoints):")
                print("=" * 80)

                if isinstance(data, list) and len(data) > 0:
                    # Show first 3 waypoints
                    for i, waypoint in enumerate(data[:3]):
                        print(f"\nWaypoint {i}:")
                        print(json.dumps(waypoint, indent=2))

                    if len(data) > 3:
                        print(f"\n... and {len(data) - 3} more waypoints")

                    # Analyze structure
                    print("\n" + "=" * 80)
                    print("Analysis:")
                    print("=" * 80)

                    if data:
                        first = data[0]
                        print(f"\nWaypoint fields: {list(first.keys())}")

                        # Check if we have coordinate fields
                        coord_fields = [k for k in first.keys() if any(
                            c in k.lower() for c in ['x', 'y', 'z', 'pos', 'coord', 'lat', 'lon']
                        )]
                        if coord_fields:
                            print(f"Coordinate-like fields: {coord_fields}")

                        # Statistics
                        print(f"\nTotal waypoints: {len(data)}")
                        if coord_fields and len(coord_fields) >= 2:
                            # Try to estimate track bounds
                            x_field = coord_fields[0]
                            z_field = coord_fields[1] if len(coord_fields) > 1 else coord_fields[0]

                            x_values = [w.get(x_field, 0) for w in data if isinstance(w.get(x_field), (int, float))]
                            z_values = [w.get(z_field, 0) for w in data if isinstance(w.get(z_field), (int, float))]

                            if x_values and z_values:
                                print(f"{x_field} range: {min(x_values):.2f} to {max(x_values):.2f}")
                                print(f"{z_field} range: {min(z_values):.2f} to {max(z_values):.2f}")
                else:
                    print(json.dumps(data, indent=2))

                return data
            else:
                print(f"Status: {response.status}")
                print("Unexpected response code")
                return None

    except (URLError, HTTPError) as e:
        print(f"Connection failed: {e}")
        print("\nMake sure:")
        print("  1. LMU is running")
        print("  2. You are in a session (practice/race) with a track loaded")
        print("  3. The REST API is enabled (should be by default)")
        return None
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    print("\nLMU REST API Track Map Test")
    print("=" * 80)
    print("\nThis script fetches track map waypoints from the LMU REST API.")
    print("The waypoints can be used to draw a track outline in visualizations.\n")

    # Test connection first
    try:
        req = Request(f"{BASE_URL}/rest/sessions")
        with urlopen(req, timeout=1) as response:
            print(f"✓ Connected to LMU REST API (status: {response.status})\n")
    except Exception:
        print("✗ Cannot connect to LMU REST API at localhost:6397")
        print("  Make sure LMU is running and you're in a session!\n")
        sys.exit(1)

    # Fetch trackmap
    data = test_trackmap_endpoint()

    if data:
        print("\n" + "=" * 80)
        print("SUCCESS!")
        print("=" * 80)
        print("\nNext steps:")
        print("  1. Review the waypoint structure above")
        print("  2. Determine if this data is useful for track visualization")
        print("  3. Consider if we should:")
        print("     a) Include waypoints in CSV metadata")
        print("     b) Build a library of track maps")
        print("     c) Continue using X/Z from telemetry samples")
    else:
        print("\n" + "=" * 80)
        print("FAILED - Could not retrieve track map data")
        print("=" * 80)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(0)
