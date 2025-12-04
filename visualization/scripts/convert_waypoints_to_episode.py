#!/usr/bin/env python3
"""
Convert AirSim waypoint JSON to multi-agent episode format.

This script converts single-agent waypoint trajectories into the multi-agent
episode format expected by visualize_episode.py.

Usage:
    python convert_waypoints_to_episode.py <input_json> <output_json>

Example:
    python convert_waypoints_to_episode.py ../data/airsim_waypoints/episode_0010_airsim.json ../data/episodes/episode_0010.json
"""

import json
import sys
import re
from pathlib import Path


def extract_time_from_description(description: str) -> float:
    """Extract time value from waypoint description."""
    match = re.search(r't=([\d.]+)s', description)
    if match:
        return float(match.group(1))
    return 0.0


def convert_waypoints_to_episode(input_file: str, output_file: str):
    """
    Convert waypoint JSON to multi-agent episode format.

    Args:
        input_file: Path to input waypoint JSON
        output_file: Path to output episode JSON
    """
    print(f"Loading waypoints from: {input_file}")

    with open(input_file, 'r') as f:
        waypoint_data = json.load(f)

    waypoints = waypoint_data.get('waypoints', [])

    if not waypoints:
        raise ValueError("No waypoints found in input file")

    print(f"Found {len(waypoints)} waypoints")

    # Extract metadata from file name and content
    episode_num = 0
    match = re.search(r'episode_(\d+)', input_file)
    if match:
        episode_num = int(match.group(1))

    # Determine outcome from description
    description = waypoint_data.get('description', '').lower()
    if 'capture' in description:
        outcome = 'capture'
    elif 'escape' in description:
        outcome = 'escape'
    elif 'timeout' in description:
        outcome = 'timeout'
    else:
        outcome = 'unknown'

    # Get coordinate system info
    coordinate_system = waypoint_data.get('coordinate_system', 'NED')
    units = waypoint_data.get('units', 'centimeters')

    print(f"Coordinate system: {coordinate_system}, Units: {units}")

    # Convert waypoints to frames
    frames = []
    total_reward = 0.0

    for waypoint in waypoints:
        # Get time directly from waypoint (new format has 't' field)
        t = waypoint.get('t', 0.0)

        # Helper function to convert position based on units
        def convert_position(pos_dict):
            """Convert position dict to list with unit conversion."""
            if units == 'centimeters':
                # Convert cm to meters
                return [pos_dict['x'] / 100.0, pos_dict['y'] / 100.0, pos_dict['z'] / 100.0]
            else:
                return [pos_dict['x'], pos_dict['y'], pos_dict['z']]

        # Check if new format (has defender/attacker/base) or old format (has single position)
        if 'defender' in waypoint and 'attacker' in waypoint:
            # New multi-agent format
            defender_pos = convert_position(waypoint['defender']['position'])
            defender_yaw = waypoint['defender'].get('yaw', 0.0)

            attacker_pos = convert_position(waypoint['attacker']['position'])
            attacker_yaw = waypoint['attacker'].get('yaw', 0.0)

            base_pos = convert_position(waypoint['base']['position'])

            # Create frame with multi-agent data
            frame = {
                't': t,
                'defender': {
                    'pos': defender_pos,
                    'vel': [0.0, 0.0, 0.0],  # Unknown velocity
                    'rpy': [0.0, 0.0, defender_yaw]
                },
                'attacker': {
                    'pos': attacker_pos,
                    'vel': [0.0, 0.0, 0.0],  # Unknown velocity
                    'rpy': [0.0, 0.0, attacker_yaw]
                },
                'base': {
                    'pos': base_pos
                }
            }
        else:
            # Old single-agent format
            t = extract_time_from_description(waypoint.get('description', ''))
            pos = waypoint['position']
            defender_pos = convert_position(pos)
            yaw = waypoint.get('yaw', 0.0)

            # Create frame with multi-agent data (attacker at distant location)
            frame = {
                't': t,
                'defender': {
                    'pos': defender_pos,
                    'vel': [0.0, 0.0, 0.0],
                    'rpy': [0.0, 0.0, yaw]
                },
                'attacker': {
                    'pos': [-5.0, 5.0, 3.0],
                    'vel': [0.0, 0.0, 0.0],
                    'rpy': [0.0, 0.0, 0.0]
                },
                'base': {
                    'pos': [0.0, 0.0, 0.0]
                }
            }

        frames.append(frame)

        # Calculate simple reward (based on successful completion)
        if outcome == 'capture':
            total_reward += 1.0

    # Create episode data structure
    episode_data = {
        'metadata': {
            'episode': episode_num,
            'total_reward': total_reward,
            'steps': len(frames),
            'outcome': outcome,
            'coordinate_system': coordinate_system,
            'source_units': units,
            'converted_units': 'meters'
        },
        'frames': frames
    }

    # Save converted episode
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"\nWriting episode to: {output_file}")
    with open(output_file, 'w') as f:
        json.dump(episode_data, f, indent=2)

    print(f"\n✓ Conversion complete!")
    print(f"  Episode: {episode_num}")
    print(f"  Outcome: {outcome}")
    print(f"  Total Frames: {len(frames)}")
    print(f"  Duration: {frames[-1]['t']:.2f}s")
    print(f"  Total Reward: {total_reward:.2f}")


def main():
    """Main entry point."""
    if len(sys.argv) != 3:
        print("Usage: python convert_waypoints_to_episode.py <input_json> <output_json>")
        print("\nExample:")
        print("  python convert_waypoints_to_episode.py ../data/airsim_waypoints/episode_0010_airsim.json ../data/episodes/episode_0010.json")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]

    if not Path(input_file).exists():
        print(f"Error: Input file not found: {input_file}")
        sys.exit(1)

    try:
        convert_waypoints_to_episode(input_file, output_file)
    except Exception as e:
        print(f"\n⚠️  ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
