"""
Visualize LMU track map waypoints to validate type hypothesis

Creates a top-down 2D view of the track showing:
- Type 0 (racing line) in one color
- Type 1 (track edge) in another color
- Types 2+ (markers) as points

Saves output as trackmap_visualization.png

Usage:
    1. Start LMU and load a track (practice/race session)
    2. Run: python visualize_trackmap.py
    3. View: trackmap_visualization.png
"""

import json
import sys
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from collections import defaultdict


BASE_URL = "http://localhost:6397"


def fetch_trackmap():
    """Fetch track map waypoints from REST API"""
    url = f"{BASE_URL}/rest/watch/trackmap"

    try:
        req = Request(url)
        with urlopen(req, timeout=2) as response:
            if response.status == 200:
                return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"Error fetching track map: {e}")
        return None


def visualize_trackmap(waypoints, output_file='trackmap_visualization.png'):
    """
    Create a 2D visualization of track map waypoints

    Args:
        waypoints: List of waypoint dicts with type, x, y, z fields
        output_file: Output image filename
    """
    print(f"\nCreating visualization with {len(waypoints)} waypoints...")

    # Group waypoints by type
    by_type = defaultdict(list)
    for w in waypoints:
        by_type[w['type']].append(w)

    # Sort types by count (most common first)
    sorted_types = sorted(by_type.keys(), key=lambda t: len(by_type[t]), reverse=True)

    print(f"Found {len(sorted_types)} unique types")
    print(f"  Type 0: {len(by_type.get(0, []))} waypoints")
    print(f"  Type 1: {len(by_type.get(1, []))} waypoints")
    print(f"  Other types: {len(waypoints) - len(by_type.get(0, [])) - len(by_type.get(1, []))} waypoints")

    # Create figure
    fig, ax = plt.subplots(figsize=(16, 12))
    ax.set_aspect('equal')

    # Plot Type 0 (racing line) - thick blue line
    if 0 in by_type:
        type0_points = by_type[0]
        x_coords = [p['x'] for p in type0_points]
        z_coords = [p['z'] for p in type0_points]
        ax.plot(x_coords, z_coords, 'b-', linewidth=3, label=f'Type 0 (Racing Line) - {len(type0_points)} pts', zorder=2)

    # Plot Type 1 (track edge) - thick red line
    if 1 in by_type:
        type1_points = by_type[1]
        x_coords = [p['x'] for p in type1_points]
        z_coords = [p['z'] for p in type1_points]
        ax.plot(x_coords, z_coords, 'r-', linewidth=3, label=f'Type 1 (Track Edge) - {len(type1_points)} pts', zorder=2)

    # Plot other types as scatter points (markers)
    other_types = [t for t in sorted_types if t not in [0, 1]]
    if other_types:
        # Use different colors for first few types
        colors = ['green', 'orange', 'purple', 'cyan', 'magenta', 'yellow']

        # Plot first 6 types individually
        for i, type_val in enumerate(other_types[:6]):
            points = by_type[type_val]
            x_coords = [p['x'] for p in points]
            z_coords = [p['z'] for p in points]
            color = colors[i % len(colors)]
            ax.scatter(x_coords, z_coords, c=color, s=50, alpha=0.7,
                      label=f'Type {type_val} - {len(points)} pts', zorder=3)

        # Plot remaining types as gray
        if len(other_types) > 6:
            remaining_points = []
            for type_val in other_types[6:]:
                remaining_points.extend(by_type[type_val])

            if remaining_points:
                x_coords = [p['x'] for p in remaining_points]
                z_coords = [p['z'] for p in remaining_points]
                ax.scatter(x_coords, z_coords, c='gray', s=30, alpha=0.5,
                          label=f'Types {other_types[6]}-{other_types[-1]} - {len(remaining_points)} pts', zorder=1)

    # Add grid and labels
    ax.grid(True, alpha=0.3)
    ax.set_xlabel('X Position (meters)', fontsize=12)
    ax.set_ylabel('Z Position (meters)', fontsize=12)
    ax.set_title('LMU Track Map Visualization\nTop-Down View (X/Z Plane)', fontsize=14, fontweight='bold')

    # Add legend
    ax.legend(loc='upper right', fontsize=10, framealpha=0.9)

    # Add statistics box
    total = len(waypoints)
    type0_count = len(by_type.get(0, []))
    type1_count = len(by_type.get(1, []))
    other_count = total - type0_count - type1_count

    stats_text = f"""Statistics:
Total: {total} waypoints
Type 0: {type0_count} ({type0_count/total*100:.1f}%)
Type 1: {type1_count} ({type1_count/total*100:.1f}%)
Others: {other_count} ({other_count/total*100:.1f}%)"""

    ax.text(0.02, 0.98, stats_text, transform=ax.transAxes,
            fontsize=10, verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

    # Adjust layout and save
    plt.tight_layout()
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"\n✓ Saved visualization to: {output_file}")
    print(f"  Image size: 150 DPI, ~{16*150}x{12*150} pixels")

    # Also create a zoomed view of a corner to show detail
    create_detail_view(waypoints, by_type, 'trackmap_detail.png')


def create_detail_view(waypoints, by_type, output_file='trackmap_detail.png'):
    """
    Create a zoomed-in view of a section to show waypoint detail

    Args:
        waypoints: List of all waypoints
        by_type: Dict of waypoints grouped by type
        output_file: Output filename
    """
    print(f"\nCreating detail view...")

    # Find a section with good density (pick middle 10% of track)
    all_x = [w['x'] for w in waypoints]
    all_z = [w['z'] for w in waypoints]

    x_range = max(all_x) - min(all_x)
    z_range = max(all_z) - min(all_z)

    # Pick a 20% window in the middle
    x_center = (max(all_x) + min(all_x)) / 2
    z_center = (max(all_z) + min(all_z)) / 2

    x_min = x_center - x_range * 0.15
    x_max = x_center + x_range * 0.15
    z_min = z_center - z_range * 0.15
    z_max = z_center + z_range * 0.15

    # Create figure
    fig, ax = plt.subplots(figsize=(12, 10))
    ax.set_aspect('equal')

    # Plot Type 0 (racing line)
    if 0 in by_type:
        type0_points = by_type[0]
        x_coords = [p['x'] for p in type0_points]
        z_coords = [p['z'] for p in type0_points]
        ax.plot(x_coords, z_coords, 'b-', linewidth=4, label=f'Type 0 (Racing Line)', zorder=2, alpha=0.8)

        # Mark individual waypoints
        ax.scatter(x_coords, z_coords, c='blue', s=20, alpha=0.5, zorder=3)

    # Plot Type 1 (track edge)
    if 1 in by_type:
        type1_points = by_type[1]
        x_coords = [p['x'] for p in type1_points]
        z_coords = [p['z'] for p in type1_points]
        ax.plot(x_coords, z_coords, 'r-', linewidth=4, label=f'Type 1 (Track Edge)', zorder=2, alpha=0.8)

        # Mark individual waypoints
        ax.scatter(x_coords, z_coords, c='red', s=20, alpha=0.5, zorder=3)

    # Set zoom window
    ax.set_xlim(x_min, x_max)
    ax.set_ylim(z_min, z_max)

    # Add grid and labels
    ax.grid(True, alpha=0.3)
    ax.set_xlabel('X Position (meters)', fontsize=12)
    ax.set_ylabel('Z Position (meters)', fontsize=12)
    ax.set_title('Track Map Detail View\nShowing Individual Waypoints', fontsize=14, fontweight='bold')

    # Add legend
    ax.legend(loc='upper right', fontsize=11, framealpha=0.9)

    # Save
    plt.tight_layout()
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"✓ Saved detail view to: {output_file}")


def main():
    print("=" * 80)
    print("LMU Track Map Visualization")
    print("=" * 80)
    print("\nThis script creates a 2D top-down view of the track map")
    print("to validate the hypothesis about waypoint types.\n")

    # Check matplotlib is available
    try:
        import matplotlib
        print(f"✓ Using matplotlib version {matplotlib.__version__}")
    except ImportError:
        print("✗ Error: matplotlib not installed")
        print("  Install with: pip install matplotlib")
        sys.exit(1)

    # Test connection
    try:
        req = Request(f"{BASE_URL}/rest/sessions")
        with urlopen(req, timeout=1) as response:
            print(f"✓ Connected to LMU REST API (status: {response.status})")
    except Exception:
        print("✗ Cannot connect to LMU REST API at localhost:6397")
        print("  Make sure LMU is running and you're in a session!")
        sys.exit(1)

    # Fetch waypoints
    print("\nFetching track map waypoints...")
    waypoints = fetch_trackmap()

    if not waypoints:
        print("✗ Failed to fetch track map data!")
        sys.exit(1)

    print(f"✓ Fetched {len(waypoints)} waypoints")

    # Create visualization
    visualize_trackmap(waypoints)

    print("\n" + "=" * 80)
    print("VISUALIZATION COMPLETE")
    print("=" * 80)
    print("\nGenerated files:")
    print("  1. trackmap_visualization.png - Full track view")
    print("  2. trackmap_detail.png - Zoomed detail view")
    print("\nWhat to look for:")
    print("  - Type 0 (blue) should show the racing line")
    print("  - Type 1 (red) should show track edge/boundary")
    print("  - Both should form complete track outlines")
    print("  - Other types (green/orange/etc) should be sparse markers")
    print()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
