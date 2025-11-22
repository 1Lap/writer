"""
Analyze the 'type' field in LMU track map waypoints

This script helps us understand what the different type values mean
so we can decide which waypoints to include in CSV exports.

Usage:
    1. Start LMU and load a track (practice/race session)
    2. Run: python test_trackmap_types.py
"""

import json
import sys
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
from collections import Counter, defaultdict
import math


BASE_URL = "http://localhost:6397"


def fetch_trackmap():
    """Fetch track map waypoints"""
    url = f"{BASE_URL}/rest/watch/trackmap"

    try:
        req = Request(url)
        with urlopen(req, timeout=2) as response:
            if response.status == 200:
                return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"Error fetching track map: {e}")
        return None


def analyze_type_distribution(waypoints):
    """Analyze distribution of type values"""
    print("\n" + "=" * 80)
    print("TYPE DISTRIBUTION ANALYSIS")
    print("=" * 80)

    # Count waypoints per type
    type_counts = Counter(w['type'] for w in waypoints)

    print(f"\nTotal waypoints: {len(waypoints)}")
    print(f"Unique type values: {len(type_counts)}")
    print(f"Type range: {min(type_counts.keys())} to {max(type_counts.keys())}")

    # Show top 10 most common types
    print("\nTop 10 most common types:")
    print(f"{'Type':<10} {'Count':<10} {'Percentage':<12} {'Description'}")
    print("-" * 80)

    for type_val, count in type_counts.most_common(10):
        pct = (count / len(waypoints)) * 100
        desc = guess_type_meaning(type_val, count, len(waypoints))
        print(f"{type_val:<10} {count:<10} {pct:>6.2f}%       {desc}")

    # Show all types if not too many
    if len(type_counts) <= 20:
        print("\nComplete type distribution:")
        print(f"{'Type':<10} {'Count':<10} {'Percentage'}")
        print("-" * 80)
        for type_val in sorted(type_counts.keys()):
            count = type_counts[type_val]
            pct = (count / len(waypoints)) * 100
            print(f"{type_val:<10} {count:<10} {pct:>6.2f}%")


def guess_type_meaning(type_val, count, total):
    """Guess what a type value might represent"""
    pct = (count / total) * 100

    # Heuristics based on percentage
    if pct > 80:
        return "Racing line / Track centerline (dominant)"
    elif pct > 40:
        return "Main track feature"
    elif pct > 10:
        return "Secondary feature (track edge?)"
    elif pct > 5:
        return "Tertiary feature (pit lane?)"
    elif pct < 1:
        return "Sparse markers (sector/DRS?)"
    else:
        return "Track feature"


def analyze_spatial_distribution(waypoints):
    """Analyze how types are distributed spatially"""
    print("\n" + "=" * 80)
    print("SPATIAL DISTRIBUTION ANALYSIS")
    print("=" * 80)

    # Group by type
    by_type = defaultdict(list)
    for w in waypoints:
        by_type[w['type']].append(w)

    print(f"\nAnalyzing spatial distribution for each type...")
    print(f"{'Type':<10} {'Count':<10} {'X Range':<30} {'Z Range':<30}")
    print("-" * 80)

    for type_val in sorted(by_type.keys())[:15]:  # First 15 types
        points = by_type[type_val]

        x_coords = [p['x'] for p in points]
        z_coords = [p['z'] for p in points]

        x_range = f"{min(x_coords):>8.2f} to {max(x_coords):>8.2f}"
        z_range = f"{min(z_coords):>8.2f} to {max(z_coords):>8.2f}"

        print(f"{type_val:<10} {len(points):<10} {x_range:<30} {z_range:<30}")


def analyze_sequential_patterns(waypoints):
    """Analyze if waypoints are sequential or mixed"""
    print("\n" + "=" * 80)
    print("SEQUENTIAL PATTERN ANALYSIS")
    print("=" * 80)

    # Check if same types are clustered together
    runs = []
    current_type = waypoints[0]['type']
    run_length = 1

    for w in waypoints[1:]:
        if w['type'] == current_type:
            run_length += 1
        else:
            runs.append((current_type, run_length))
            current_type = w['type']
            run_length = 1

    runs.append((current_type, run_length))

    print(f"\nTotal runs (consecutive waypoints of same type): {len(runs)}")
    print(f"Average run length: {sum(r[1] for r in runs) / len(runs):.2f}")
    print(f"Max run length: {max(r[1] for r in runs)}")

    # Show first 20 runs to see pattern
    print("\nFirst 20 type sequences:")
    print(f"{'Type':<10} {'Run Length':<15} {'Percentage of Total'}")
    print("-" * 80)

    for type_val, length in runs[:20]:
        pct = (length / len(waypoints)) * 100
        print(f"{type_val:<10} {length:<15} {pct:>6.2f}%")

    # Determine if clustered or mixed
    if len(runs) < len(waypoints) * 0.1:
        print("\n→ Waypoints are HIGHLY CLUSTERED by type (long runs)")
        print("  Likely: Each type represents a section of track")
    elif len(runs) > len(waypoints) * 0.5:
        print("\n→ Waypoints are MIXED (many short runs)")
        print("  Likely: Types represent different features at same location")
    else:
        print("\n→ Waypoints are MODERATELY CLUSTERED")


def calculate_track_distance(waypoints):
    """Calculate approximate track distance from waypoints"""
    total_distance = 0.0

    for i in range(1, len(waypoints)):
        prev = waypoints[i-1]
        curr = waypoints[i]

        dx = curr['x'] - prev['x']
        dz = curr['z'] - prev['z']

        distance = math.sqrt(dx*dx + dz*dz)
        total_distance += distance

    return total_distance


def recommend_filtering_strategy(waypoints):
    """Recommend which waypoints to include based on analysis"""
    print("\n" + "=" * 80)
    print("FILTERING RECOMMENDATION")
    print("=" * 80)

    # Count by type
    type_counts = Counter(w['type'] for w in waypoints)
    total = len(waypoints)

    # Find dominant type (likely racing line)
    dominant_type, dominant_count = type_counts.most_common(1)[0]
    dominant_pct = (dominant_count / total) * 100

    print(f"\nDominant type: {dominant_type}")
    print(f"Waypoints: {dominant_count} ({dominant_pct:.1f}%)")

    if dominant_pct > 70:
        print(f"\n✅ RECOMMENDATION: Use type {dominant_type} only (likely racing line)")
        print(f"   This gives you {dominant_count} waypoints")
        print(f"   Downsample to ~300 for optimal size (~every {dominant_count // 300} waypoints)")
    else:
        print(f"\n⚠️ No clearly dominant type - may need multiple types")
        print(f"   Top 3 types:")
        for type_val, count in type_counts.most_common(3):
            pct = (count / total) * 100
            print(f"   - Type {type_val}: {count} waypoints ({pct:.1f}%)")

    # Calculate track distance
    track_dist = calculate_track_distance(waypoints)
    print(f"\nApproximate track distance: {track_dist:.2f} meters")
    print(f"Average waypoint spacing: {track_dist / len(waypoints):.2f} meters")


def main():
    print("=" * 80)
    print("LMU Track Map Type Analysis")
    print("=" * 80)
    print("\nThis script analyzes the 'type' field in track map waypoints")
    print("to help determine which waypoints to include in CSV exports.\n")

    # Test connection
    try:
        req = Request(f"{BASE_URL}/rest/sessions")
        with urlopen(req, timeout=1) as response:
            print(f"✓ Connected to LMU REST API (status: {response.status})\n")
    except Exception:
        print("✗ Cannot connect to LMU REST API at localhost:6397")
        print("  Make sure LMU is running and you're in a session!\n")
        sys.exit(1)

    # Fetch waypoints
    print("Fetching track map waypoints...")
    waypoints = fetch_trackmap()

    if not waypoints:
        print("Failed to fetch track map data!")
        sys.exit(1)

    print(f"✓ Fetched {len(waypoints)} waypoints\n")

    # Run analyses
    analyze_type_distribution(waypoints)
    analyze_spatial_distribution(waypoints)
    analyze_sequential_patterns(waypoints)
    recommend_filtering_strategy(waypoints)

    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)
    print("\nNext steps:")
    print("  1. Review the analysis above")
    print("  2. Check Swagger docs for type field enum definition")
    print("  3. Decide which types to include in CSV exports")
    print("  4. Implement filtering logic in LMURestAPI class")
    print()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(0)
