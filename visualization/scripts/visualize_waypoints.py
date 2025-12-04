#!/usr/bin/env python3
"""
One-step visualization pipeline for AirSim waypoint trajectories.

This script provides a fluid pipeline that:
1. Converts waypoint JSON to episode format
2. Auto-configures based on metadata (coordinate system, units)
3. Updates AirSim settings.json
4. Runs visualization in AirSim

Usage:
    python visualize_waypoints.py <waypoints_json> [options]

Examples:
    python visualize_waypoints.py ../data/episodes/episode_0001_airsim.json
    python visualize_waypoints.py ../data/episodes/episode_0001_airsim.json --speed 2.0
    python visualize_waypoints.py ../data/episodes/episode_0001_airsim.json --start-frame 100 --end-frame 300

Author: AirSim Visualization Pipeline
Date: 2025
"""

import sys
import argparse
from pathlib import Path
import tempfile
import os

# Add scripts directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from convert_waypoints_to_episode import convert_waypoints_to_episode
from visualize_episode import visualize_episode, update_settings_with_frame_0, load_episode
from config import VisualizationConfig, print_config_summary, auto_configure_from_metadata


def main():
    """Main entry point for the fluid visualization pipeline."""
    parser = argparse.ArgumentParser(
        description='One-step visualization of AirSim waypoint trajectories',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage
  python visualize_waypoints.py ../data/episodes/episode_0001_airsim.json

  # 2x speed playback
  python visualize_waypoints.py ../data/episodes/episode_0001_airsim.json --speed 2.0

  # Visualize specific frame range
  python visualize_waypoints.py ../data/episodes/episode_0001_airsim.json --start-frame 100 --end-frame 300

  # Skip takeoff (if drones already airborne)
  python visualize_waypoints.py ../data/episodes/episode_0001_airsim.json --no-takeoff

  # Keep converted episode file
  python visualize_waypoints.py ../data/episodes/episode_0001_airsim.json --keep-converted
        """
    )

    parser.add_argument(
        'waypoints_file',
        type=str,
        help='Path to waypoints JSON file'
    )

    parser.add_argument(
        '--scale',
        type=float,
        default=None,
        help='Scale factor for positions (e.g., 2.0 = 2x scale). If not specified, uses value from config.py'
    )

    parser.add_argument(
        '--speed',
        type=float,
        default=1.0,
        help='Playback speed multiplier (default: 1.0 = real-time)'
    )

    parser.add_argument(
        '--start-frame',
        type=int,
        default=0,
        help='Starting frame index (default: 0)'
    )

    parser.add_argument(
        '--end-frame',
        type=int,
        default=None,
        help='Ending frame index (default: last frame)'
    )

    parser.add_argument(
        '--no-takeoff',
        action='store_true',
        help='Skip takeoff sequence'
    )

    parser.add_argument(
        '--no-trajectories',
        action='store_true',
        help='Disable trajectory visualization'
    )

    parser.add_argument(
        '--no-markers',
        action='store_true',
        help='Disable colored identification markers above vehicles'
    )

    parser.add_argument(
        '--settings-path',
        type=str,
        default='/tmp/AirSim/settings.json',
        help='Path to AirSim settings.json to update (default: /tmp/AirSim/settings.json)'
    )

    parser.add_argument(
        '--keep-converted',
        action='store_true',
        help='Keep the converted episode file (saves to same directory with _converted suffix)'
    )

    parser.add_argument(
        '--output-converted',
        type=str,
        default=None,
        help='Custom path for converted episode file (implies --keep-converted)'
    )

    args = parser.parse_args()

    # Validate input file
    waypoints_path = Path(args.waypoints_file)
    if not waypoints_path.exists():
        print(f"\n⚠️  ERROR: Waypoints file not found: {args.waypoints_file}")
        sys.exit(1)

    print("\n" + "="*60)
    print("AIRSIM WAYPOINT VISUALIZATION PIPELINE")
    print("="*60)
    print(f"Input: {waypoints_path.name}")
    print("="*60 + "\n")

    # Step 1: Convert waypoints to episode format
    print("Step 1: Converting waypoints to episode format...")

    if args.output_converted:
        converted_path = args.output_converted
        keep_converted = True
    elif args.keep_converted:
        # Save next to original with _converted suffix
        converted_path = str(waypoints_path.parent / f"{waypoints_path.stem}_converted.json")
        keep_converted = True
    else:
        # Use temporary file
        temp_fd, converted_path = tempfile.mkstemp(suffix='.json', prefix='airsim_episode_')
        os.close(temp_fd)
        keep_converted = False

    try:
        convert_waypoints_to_episode(str(waypoints_path), converted_path)
    except Exception as e:
        print(f"\n⚠️  ERROR during conversion: {e}")
        if not keep_converted:
            os.unlink(converted_path)
        sys.exit(1)

    # Step 2: Load converted episode
    print("\nStep 2: Loading converted episode...")
    try:
        episode_data = load_episode(converted_path)
    except Exception as e:
        print(f"\n⚠️  ERROR loading converted episode: {e}")
        if not keep_converted:
            os.unlink(converted_path)
        sys.exit(1)

    # Step 3: Auto-configure based on metadata
    print("\nStep 3: Auto-configuring from episode metadata...")
    config = VisualizationConfig()
    config = auto_configure_from_metadata(episode_data['metadata'], config, episode_data)

    # Override scale factor if provided
    if args.scale is not None:
        config.SCALE_FACTOR = args.scale
        print(f"✓ Scale factor overridden to {args.scale}x")

    config.SHOW_TRAJECTORIES = not args.no_trajectories
    config.SHOW_VEHICLE_MARKERS = not args.no_markers

    # Print configuration
    print_config_summary(config)

    # Step 4: Update settings.json with correct spawn positions
    print("Step 4: Updating AirSim settings.json with scaled positions...")
    update_settings_with_frame_0(episode_data, config, args.settings_path)

    print("\n" + "="*60)
    print("⚠️  IMPORTANT: You MUST restart Unreal Engine now!")
    print("="*60)
    print("1. Close Unreal Engine completely")
    print("2. Restart Unreal Engine")
    print("3. Press Play in Unreal")
    print("4. Come back here and press ENTER")
    print("="*60)

    input("\nPress ENTER after you've restarted Unreal and pressed Play...")

    print("\nStep 5: Running visualization...")
    try:
        visualize_episode(
            episode_data=episode_data,
            config=config,
            start_frame=args.start_frame,
            end_frame=args.end_frame,
            skip_takeoff=args.no_takeoff,
            playback_speed=args.speed
        )

        print("\n✓ Visualization complete!")

        if keep_converted:
            print(f"\n✓ Converted episode saved to: {converted_path}")

    except KeyboardInterrupt:
        print("\n\n⚠️  Visualization interrupted by user")
    except Exception as e:
        print(f"\n⚠️  ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Clean up temporary file if not keeping
        if not keep_converted and os.path.exists(converted_path):
            os.unlink(converted_path)
            print(f"\n✓ Cleaned up temporary converted file")


if __name__ == "__main__":
    main()
