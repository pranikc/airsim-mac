#!/usr/bin/env python3
"""
AirSim Multi-Agent Episode Visualization

This script visualizes multi-agent episodes (defender, attacker, base) in AirSim.

Usage:
    python visualize_episode.py <episode_json_file> [options]

Examples:
    python visualize_episode.py ../data/episodes/episode_0001.json
    python visualize_episode.py ../data/episodes/episode_0001.json --speed 2.0
    python visualize_episode.py ../data/episodes/episode_0001.json --no-takeoff
    python visualize_episode.py ../data/episodes/episode_0001.json --start-frame 100 --end-frame 500

Author: AirSim Visualization Pipeline
Date: 2025
"""

import airsim
import json
import time
import sys
import argparse
from pathlib import Path
from typing import Dict, Any

# Add scripts directory to path
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import VisualizationConfig, print_config_summary, get_frame_timing, transform_position, auto_configure_from_metadata
from multi_agent_runner import MultiAgentRunner


def load_episode(json_file: str) -> Dict[str, Any]:
    """
    Load episode data from JSON file.

    Args:
        json_file: Path to episode JSON file

    Returns:
        Episode data dictionary

    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If JSON is invalid
    """
    json_path = Path(json_file)

    if not json_path.exists():
        raise FileNotFoundError(f"Episode file not found: {json_file}")

    print(f"\nLoading episode from: {json_path.name}")

    with open(json_path, 'r') as f:
        episode_data = json.load(f)

    # Validate structure
    if 'metadata' not in episode_data or 'frames' not in episode_data:
        raise ValueError("Invalid episode format: missing 'metadata' or 'frames'")

    metadata = episode_data['metadata']
    frames = episode_data['frames']

    print(f"✓ Loaded Episode {metadata['episode']}")
    print(f"  Outcome: {metadata['outcome']}")
    print(f"  Total Reward: {metadata['total_reward']:.2f}")
    print(f"  Total Frames: {len(frames)}")
    print(f"  Duration: {frames[-1]['t']:.2f}s")
    print(f"  Coordinate System: {metadata.get('coordinate_system', 'Unknown')}")
    print(f"  Units: {metadata.get('converted_units', 'meters')}")

    return episode_data


def update_settings_with_frame_0(episode_data: Dict[str, Any], config: VisualizationConfig, settings_path: str = "/tmp/AirSim/settings.json"):
    """
    Update AirSim settings.json with starting positions from frame 0.

    Args:
        episode_data: Episode data dictionary
        config: Visualization configuration
        settings_path: Path to settings.json file (default: ~/Documents/AirSim/settings.json)
    """
    try:
        frames = episode_data['frames']
        if not frames:
            print("⚠️  No frames found in episode data")
            return

        frame_0 = frames[0]

        # Load existing settings
        settings_file = Path(settings_path).expanduser()
        if settings_file.exists():
            with open(settings_file, 'r') as f:
                settings = json.load(f)
        else:
            # Create minimal settings if doesn't exist
            settings = {
                "SettingsVersion": 1.2,
                "SimMode": "Multirotor",
                "ClockSpeed": 20,
                "ViewMode": "SpringArmChase",
                "Vehicles": {}
            }

        # Ensure Vehicles section exists
        if "Vehicles" not in settings:
            settings["Vehicles"] = {}

        # Update defender position
        if "defender" in frame_0:
            defender_pos = transform_position(frame_0["defender"]["pos"], config)
            defender_rpy = frame_0["defender"]["rpy"]

            # AirSim uses meters (same as training data after scaling)
            settings["Vehicles"]["Defender"] = {
                "VehicleType": "SimpleFlight",
                "X": defender_pos[0],
                "Y": defender_pos[1],
                "Z": defender_pos[2],
                "Yaw": defender_rpy[2]  # Use yaw from RPY
            }

        # Update attacker position
        if "attacker" in frame_0:
            attacker_pos = transform_position(frame_0["attacker"]["pos"], config)
            attacker_rpy = frame_0["attacker"]["rpy"]

            # AirSim uses meters (same as training data after scaling)
            settings["Vehicles"]["Attacker"] = {
                "VehicleType": "SimpleFlight",
                "X": attacker_pos[0],
                "Y": attacker_pos[1],
                "Z": attacker_pos[2],
                "Yaw": attacker_rpy[2]  # Use yaw from RPY
            }

        # Write updated settings
        settings_file.parent.mkdir(parents=True, exist_ok=True)
        with open(settings_file, 'w') as f:
            json.dump(settings, f, indent=2)

        print(f"\n{'='*60}")
        print(f"SETTINGS.JSON UPDATE - CRITICAL FOR ALIGNMENT")
        print(f"{'='*60}")
        print(f"File: {settings_file}")
        print(f"\nFrame 0 positions (RAW from episode data):")
        print(f"  Defender: {frame_0['defender']['pos']}")
        print(f"  Attacker: {frame_0['attacker']['pos']}")
        print(f"\nTransformation settings:")
        print(f"  Scale Factor: {config.SCALE_FACTOR}x")
        print(f"  Invert Z-axis: {config.INVERT_Z}")
        print(f"\nAfter transform_position (written to settings.json):")
        print(f"  Defender: X={settings['Vehicles']['Defender']['X']:.3f}, "
              f"Y={settings['Vehicles']['Defender']['Y']:.3f}, "
              f"Z={settings['Vehicles']['Defender']['Z']:.3f} {'(negative = altitude in NED)' if settings['Vehicles']['Defender']['Z'] < 0 else '⚠️ POSITIVE Z = BELOW GROUND!'}")
        print(f"  Attacker: X={settings['Vehicles']['Attacker']['X']:.3f}, "
              f"Y={settings['Vehicles']['Attacker']['Y']:.3f}, "
              f"Z={settings['Vehicles']['Attacker']['Z']:.3f} {'(negative = altitude in NED)' if settings['Vehicles']['Attacker']['Z'] < 0 else '⚠️ POSITIVE Z = BELOW GROUND!'}")
        print(f"\n⚠️  YOU MUST RESTART UNREAL for these positions to take effect!")
        print(f"{'='*60}\n")

    except Exception as e:
        print(f"⚠️  Warning: Could not update settings.json: {e}")


def visualize_episode(
    episode_data: Dict[str, Any],
    config: VisualizationConfig,
    start_frame: int = 0,
    end_frame: int = None,
    skip_takeoff: bool = False,
    playback_speed: float = 1.0
):
    """
    Visualize episode in AirSim.

    Args:
        episode_data: Episode data dictionary
        config: Visualization configuration
        start_frame: Starting frame index (default: 0)
        end_frame: Ending frame index (default: last frame)
        skip_takeoff: If True, skip takeoff and start directly
        playback_speed: Playback speed multiplier
    """
    frames = episode_data['frames']
    if end_frame is None or end_frame > len(frames):
        end_frame = len(frames)

    print("\n" + "="*60)
    print(f"STARTING VISUALIZATION")
    print("="*60)
    print(f"Frames: {start_frame} to {end_frame} (total: {end_frame - start_frame})")
    print(f"Playback Speed: {playback_speed}x")
    print("="*60)

    # Simple initialization
    print("\nConnecting to AirSim...")
    client = airsim.MultirotorClient()
    client.confirmConnection()
    print("✓ Connected")

    # Enable API control and arm
    print("\nEnabling API control...")
    client.enableApiControl(True, "Defender")
    client.enableApiControl(True, "Attacker")
    print("✓ API control enabled")

    print("\nArming drones...")
    client.armDisarm(True, "Defender")
    client.armDisarm(True, "Attacker")
    print("✓ Drones armed")

    # Clear all old markers/trajectories from previous runs
    print("\nClearing old visualizations...")
    try:
        client.simFlushPersistentMarkers()
        print("✓ Cleared old markers")
    except:
        print("✓ Marker clearing not supported (old AirSim version)")

    # Takeoff to get airborne
    print("\nTaking off...")
    f1 = client.takeoffAsync(vehicle_name="Defender")
    f2 = client.takeoffAsync(vehicle_name="Attacker")
    f1.join()
    f2.join()
    print("✓ Takeoff complete")
    time.sleep(3)  # Longer wait for stabilization

    # SIMPLE APPROACH: Use ACTUAL drone positions and build relative paths
    print("\n" + "="*60)
    print("BUILDING PATHS FROM ACTUAL DRONE POSITIONS")
    print("="*60)

    # Get where drones actually are after takeoff
    def_state = client.getMultirotorState(vehicle_name="Defender")
    att_state = client.getMultirotorState(vehicle_name="Attacker")
    def_actual = def_state.kinematics_estimated.position
    att_actual = att_state.kinematics_estimated.position

    print(f"\n✓ ACTUAL Defender position: ({def_actual.x_val:.3f}, {def_actual.y_val:.3f}, {def_actual.z_val:.3f})")
    print(f"✓ ACTUAL Attacker position: ({att_actual.x_val:.3f}, {att_actual.y_val:.3f}, {att_actual.z_val:.3f})")
    print(f"\nUsing these as the starting points for trajectories (guaranteed correct!)")
    print("="*60)

    try:
        # Main visualization loop
        print("\n" + "="*60)
        print("PLAYBACK STARTED")
        print("="*60)
        print("Press Ctrl+C to stop\n")

        # Build complete path using RELATIVE movements (this makes drones follow correctly)
        print("\nBuilding flight paths using relative movements from episode data...")

        # Colors for visualization
        COLOR_DEFENDER = [0.0, 1.0, 0.0, 1.0]  # Green
        COLOR_ATTACKER = [1.0, 0.0, 0.0, 1.0]  # Red
        COLOR_BASE = [0.0, 0.5, 1.0, 1.0]      # Cyan

        episode_frames = frames[start_frame:end_frame]

        # Start with ACTUAL drone positions (this was working!)
        defender_path = [airsim.Vector3r(def_actual.x_val, def_actual.y_val, def_actual.z_val)]
        attacker_path = [airsim.Vector3r(att_actual.x_val, att_actual.y_val, att_actual.z_val)]

        # Build relative movements between frames
        for i in range(1, len(episode_frames)):
            prev_frame = episode_frames[i-1]
            curr_frame = episode_frames[i]

            # Calculate RELATIVE movement (delta) between frames
            def_delta_x = (curr_frame['defender']['pos'][0] - prev_frame['defender']['pos'][0]) * config.SCALE_FACTOR
            def_delta_y = (curr_frame['defender']['pos'][1] - prev_frame['defender']['pos'][1]) * config.SCALE_FACTOR
            def_delta_z = (curr_frame['defender']['pos'][2] - prev_frame['defender']['pos'][2]) * config.SCALE_FACTOR

            att_delta_x = (curr_frame['attacker']['pos'][0] - prev_frame['attacker']['pos'][0]) * config.SCALE_FACTOR
            att_delta_y = (curr_frame['attacker']['pos'][1] - prev_frame['attacker']['pos'][1]) * config.SCALE_FACTOR
            att_delta_z = (curr_frame['attacker']['pos'][2] - prev_frame['attacker']['pos'][2]) * config.SCALE_FACTOR

            # Apply relative movement to previous position
            prev_def = defender_path[-1]
            prev_att = attacker_path[-1]

            defender_path.append(airsim.Vector3r(
                prev_def.x_val + def_delta_x,
                prev_def.y_val + def_delta_y,
                prev_def.z_val + def_delta_z
            ))
            attacker_path.append(airsim.Vector3r(
                prev_att.x_val + att_delta_x,
                prev_att.y_val + att_delta_y,
                prev_att.z_val + att_delta_z
            ))

        print(f"✓ Built paths: {len(defender_path)} waypoints (for drone flight)")

        # Build SEPARATE paths for visualization (X/Y scaled, Z NOT scaled - matches markers)
        defender_path_visual = []
        attacker_path_visual = []

        for frame in episode_frames:
            def_pos = frame['defender']['pos']
            att_pos = frame['attacker']['pos']

            defender_path_visual.append(airsim.Vector3r(
                def_pos[0] * config.SCALE_FACTOR,  # Scale X
                def_pos[1] * config.SCALE_FACTOR,  # Scale Y
                def_pos[2]                          # Don't scale Z
            ))
            attacker_path_visual.append(airsim.Vector3r(
                att_pos[0] * config.SCALE_FACTOR,  # Scale X
                att_pos[1] * config.SCALE_FACTOR,  # Scale Y
                att_pos[2]                          # Don't scale Z
            ))

        print(f"✓ Built visual paths: {len(defender_path_visual)} waypoints (for trajectory lines)\n")

        # Draw persistent markers for base, defender, and attacker
        print("Drawing position markers...")

        # Get base position from first frame (scale X/Y but NOT Z)
        base_pos = episode_frames[0]['base']['pos']
        base_scaled = airsim.Vector3r(
            base_pos[0] * config.SCALE_FACTOR,
            base_pos[1] * config.SCALE_FACTOR,
            base_pos[2]  # Don't scale Z
        )

        # Draw BASE marker (cyan sphere)
        client.simPlotPoints(
            points=[base_scaled],
            color_rgba=[0.0, 1.0, 1.0, 1.0],  # Cyan
            size=25.0,
            duration=9999.0,
            is_persistent=True
        )
        try:
            client.simPlotStrings(
                strings=["BASE"],
                positions=[airsim.Vector3r(base_scaled.x_val, base_scaled.y_val, base_scaled.z_val - 2.0)],
                scale=5.0,  # Larger text
                color_rgba=[0.0, 1.0, 1.0, 1.0],  # Cyan
                duration=9999.0
            )
            print(f"  ✓ BASE (cyan) at: ({base_scaled.x_val:.2f}, {base_scaled.y_val:.2f}, {base_scaled.z_val:.2f}) [text shown]")
        except Exception as e:
            print(f"  ✓ BASE (cyan) at: ({base_scaled.x_val:.2f}, {base_scaled.y_val:.2f}, {base_scaled.z_val:.2f}) [text not supported]")

        # Draw DEFENDER starting marker (green sphere)
        def_start_pos = episode_frames[0]['defender']['pos']
        def_start_scaled = airsim.Vector3r(
            def_start_pos[0] * config.SCALE_FACTOR,
            def_start_pos[1] * config.SCALE_FACTOR,
            def_start_pos[2]  # Don't scale Z
        )
        client.simPlotPoints(
            points=[def_start_scaled],
            color_rgba=[0.0, 1.0, 0.0, 1.0],  # Green
            size=25.0,
            duration=9999.0,
            is_persistent=True
        )
        try:
            client.simPlotStrings(
                strings=["DEFENDER"],
                positions=[airsim.Vector3r(def_start_scaled.x_val, def_start_scaled.y_val, def_start_scaled.z_val - 2.0)],
                scale=5.0,  # Larger text
                color_rgba=[0.0, 1.0, 0.0, 1.0],  # Green
                duration=9999.0
            )
            print(f"  ✓ DEFENDER (green) at: ({def_start_scaled.x_val:.2f}, {def_start_scaled.y_val:.2f}, {def_start_scaled.z_val:.2f}) [text shown]")
        except Exception as e:
            print(f"  ✓ DEFENDER (green) at: ({def_start_scaled.x_val:.2f}, {def_start_scaled.y_val:.2f}, {def_start_scaled.z_val:.2f}) [text not supported]")

        # Draw ATTACKER starting marker (red sphere)
        att_start_pos = episode_frames[0]['attacker']['pos']
        att_start_scaled = airsim.Vector3r(
            att_start_pos[0] * config.SCALE_FACTOR,
            att_start_pos[1] * config.SCALE_FACTOR,
            att_start_pos[2]  # Don't scale Z
        )
        client.simPlotPoints(
            points=[att_start_scaled],
            color_rgba=[1.0, 0.0, 0.0, 1.0],  # Red
            size=25.0,
            duration=9999.0,
            is_persistent=True
        )
        try:
            client.simPlotStrings(
                strings=["ATTACKER"],
                positions=[airsim.Vector3r(att_start_scaled.x_val, att_start_scaled.y_val, att_start_scaled.z_val - 2.0)],
                scale=5.0,  # Larger text
                color_rgba=[1.0, 0.0, 0.0, 1.0],  # Red
                duration=9999.0
            )
            print(f"  ✓ ATTACKER (red) at: ({att_start_scaled.x_val:.2f}, {att_start_scaled.y_val:.2f}, {att_start_scaled.z_val:.2f}) [text shown]")
        except Exception as e:
            print(f"  ✓ ATTACKER (red) at: ({att_start_scaled.x_val:.2f}, {att_start_scaled.y_val:.2f}, {att_start_scaled.z_val:.2f}) [text not supported]")
        print()

        # Draw trajectory lines for both drones (using visual paths with unscaled Z)
        print("Drawing trajectory lines...")

        # Defender trajectory (green line)
        try:
            client.simPlotLineStrip(
                points=defender_path_visual,
                color_rgba=[0.0, 1.0, 0.0, 1.0],  # Green
                thickness=5.0,
                duration=9999.0,
                is_persistent=True
            )
            print(f"  ✓ DEFENDER trajectory (green) - {len(defender_path_visual)} waypoints")
        except Exception as e:
            print(f"  ✗ Failed to draw DEFENDER trajectory: {e}")

        # Attacker trajectory (red line)
        try:
            client.simPlotLineStrip(
                points=attacker_path_visual,
                color_rgba=[1.0, 0.0, 0.0, 1.0],  # Red
                thickness=5.0,
                duration=9999.0,
                is_persistent=True
            )
            print(f"  ✓ ATTACKER trajectory (red) - {len(attacker_path_visual)} waypoints")
        except Exception as e:
            print(f"  ✗ Failed to draw ATTACKER trajectory: {e}")

        print()

        print(f"Starting flight...")
        print(f"Showing waypoint progress with drone positions\n")

        # Start both drones on their smooth paths simultaneously
        # Velocity scales with SCALE_FACTOR for consistent visual speed
        base_velocity = 0.25  # m/s base speed (2x faster than previous 0.125)
        flight_velocity = base_velocity * config.SCALE_FACTOR  # Scale velocity with positions

        # Calculate expected flight time
        defender_distance = ((defender_path[-1].x_val - defender_path[0].x_val)**2 +
                            (defender_path[-1].y_val - defender_path[0].y_val)**2 +
                            (defender_path[-1].z_val - defender_path[0].z_val)**2)**0.5
        expected_time = defender_distance / flight_velocity

        print(f"\n{'='*60}")
        print(f"SCALING CONFIGURATION")
        print(f"{'='*60}")
        print(f"Scale Factor: {config.SCALE_FACTOR}x")
        print(f"Base Velocity: {base_velocity} m/s")
        print(f"Scaled Velocity: {flight_velocity} m/s")
        print(f"Defender Distance: {defender_distance:.2f}m")
        print(f"Expected Flight Time: ~{expected_time:.1f} seconds")
        print(f"{'='*60}\n")

        # Use moveOnPath with TIGHT lookahead for precise waypoint following
        # Small lookahead (1m) ensures drones hit waypoints accurately
        f_def = client.moveOnPathAsync(
            path=defender_path,
            velocity=flight_velocity,
            drivetrain=airsim.DrivetrainType.MaxDegreeOfFreedom,
            yaw_mode=airsim.YawMode(is_rate=False, yaw_or_rate=0),
            lookahead=1.0,  # 1 meter lookahead for precise waypoints
            adaptive_lookahead=0,  # Disable adaptive - follow path exactly
            vehicle_name="Defender"
        )

        f_att = client.moveOnPathAsync(
            path=attacker_path,
            velocity=flight_velocity,
            drivetrain=airsim.DrivetrainType.MaxDegreeOfFreedom,
            yaw_mode=airsim.YawMode(is_rate=False, yaw_or_rate=0),
            lookahead=1.0,  # 1 meter lookahead for precise waypoints
            adaptive_lookahead=0,  # Disable adaptive - follow path exactly
            vehicle_name="Attacker"
        )

        # Monitor progress and draw visualizations while drones fly
        defender_trajectory = []
        attacker_trajectory = []

        print("Drones flying smooth interpolated paths...\n")

        # Get final target positions
        final_def = defender_path[-1]
        final_att = attacker_path[-1]

        # Monitor until both drones reach their final positions
        def distance(pos, target):
            return ((pos.x_val - target.x_val)**2 +
                    (pos.y_val - target.y_val)**2 +
                    (pos.z_val - target.z_val)**2)**0.5

        max_iterations = 10000  # Safety limit
        iteration = 0

        # Track which waypoint we should be near (estimate based on time)
        waypoint_index = 0

        while iteration < max_iterations:
            # Get current positions
            def_state = client.getMultirotorState(vehicle_name="Defender")
            att_state = client.getMultirotorState(vehicle_name="Attacker")
            def_actual = def_state.kinematics_estimated.position
            att_actual = att_state.kinematics_estimated.position

            # Store trajectory points
            defender_trajectory.append([def_actual.x_val, def_actual.y_val, def_actual.z_val])
            attacker_trajectory.append([att_actual.x_val, att_actual.y_val, att_actual.z_val])

            # Show waypoint progress for ALL frames - display ABSOLUTE positions from JSON
            if iteration < len(episode_frames):
                frame = episode_frames[iteration]

                # Get ABSOLUTE positions from JSON (scaled)
                def_json_pos = frame['defender']['pos']
                att_json_pos = frame['attacker']['pos']

                def_json_scaled = (def_json_pos[0] * config.SCALE_FACTOR,
                                  def_json_pos[1] * config.SCALE_FACTOR,
                                  def_json_pos[2] * config.SCALE_FACTOR)
                att_json_scaled = (att_json_pos[0] * config.SCALE_FACTOR,
                                  att_json_pos[1] * config.SCALE_FACTOR,
                                  att_json_pos[2] * config.SCALE_FACTOR)

                print(f"[{iteration:3d}] DEF: ({def_actual.x_val:7.2f},{def_actual.y_val:7.2f},{def_actual.z_val:7.2f}) | "
                      f"WP:({def_json_scaled[0]:7.2f},{def_json_scaled[1]:7.2f},{def_json_scaled[2]:7.2f}) || "
                      f"ATT: ({att_actual.x_val:7.2f},{att_actual.y_val:7.2f},{att_actual.z_val:7.2f}) | "
                      f"WP:({att_json_scaled[0]:7.2f},{att_json_scaled[1]:7.2f},{att_json_scaled[2]:7.2f})")

            # Check if both drones reached their final positions (within 1 meter for more accuracy)
            def_dist = distance(def_actual, final_def)
            att_dist = distance(att_actual, final_att)


            if def_dist < 1.0 and att_dist < 1.0:
                # Calculate distance between drones
                drone_dist = ((def_actual.x_val - att_actual.x_val)**2 +
                             (def_actual.y_val - att_actual.y_val)**2 +
                             (def_actual.z_val - att_actual.z_val)**2)**0.5

                print(f"\n✓ Both drones near final positions!")
                print(f"  Defender: ({def_actual.x_val:.2f}, {def_actual.y_val:.2f}, {def_actual.z_val:.2f}) - {def_dist:.2f}m from target")
                print(f"  Attacker: ({att_actual.x_val:.2f}, {att_actual.y_val:.2f}, {att_actual.z_val:.2f}) - {att_dist:.2f}m from target")
                print(f"  Distance between drones: {drone_dist:.2f}m")
                print(f"  Expected final distance: 0.49m")
                break

            time.sleep(0.05)  # Update visualization at 20Hz
            iteration += 1

        # Wait for async operations to complete
        f_def.join()
        f_att.join()

        print("✓ Smooth flight paths completed!")

        # Cancel any remaining movement commands to ensure clean landing
        client.cancelLastTask("Defender")
        client.cancelLastTask("Attacker")
        time.sleep(0.5)

        # Final frame
        print("\n" + "="*60)
        print("PLAYBACK COMPLETE")
        print("="*60)

        # Wait a bit before landing
        print("\nWaiting 2 seconds before landing...")
        time.sleep(2)

    except KeyboardInterrupt:
        print("\n\n⚠️  Visualization interrupted by user")

    except Exception as e:
        print(f"\n\n⚠️  ERROR during visualization: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # Land and disarm drones
        try:
            print("\nLanding...")
            f1 = client.landAsync(vehicle_name="Defender")
            f2 = client.landAsync(vehicle_name="Attacker")
            f1.join()
            f2.join()

            client.armDisarm(False, "Defender")
            client.armDisarm(False, "Attacker")
            client.enableApiControl(False, "Defender")
            client.enableApiControl(False, "Attacker")
            print("✓ Landed and disarmed")
        except:
            print("⚠️  Could not land properly")
            client.reset()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Visualize multi-agent episodes in AirSim',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage
  python visualize_episode.py ../data/episodes/episode_0001.json

  # 2x speed playback
  python visualize_episode.py ../data/episodes/episode_0001.json --speed 2.0

  # Visualize specific frame range
  python visualize_episode.py ../data/episodes/episode_0001.json --start-frame 100 --end-frame 500

  # Skip takeoff (if drones already airborne)
  python visualize_episode.py ../data/episodes/episode_0001.json --no-takeoff
        """
    )

    parser.add_argument(
        'episode_file',
        type=str,
        help='Path to episode JSON file'
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
        '--scale',
        type=float,
        default=1.0,
        help='Position scale factor (default: 1.0 = no scaling)'
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
        default='~/Documents/AirSim/settings.json',
        help='Path to AirSim settings.json to update (default: ~/Documents/AirSim/settings.json)'
    )

    args = parser.parse_args()

    # Load episode first
    try:
        episode_data = load_episode(args.episode_file)
    except Exception as e:
        print(f"\n⚠️  ERROR loading episode: {e}")
        sys.exit(1)

    # Create and auto-configure based on episode metadata
    config = VisualizationConfig()
    config = auto_configure_from_metadata(episode_data['metadata'], config)

    # Apply command-line overrides
    if args.scale != 1.0:
        print(f"\n⚠️  Warning: Overriding scale factor to {args.scale}x (default is 1.0 for no scaling)")
        config.SCALE_FACTOR = args.scale
    config.SHOW_TRAJECTORIES = not args.no_trajectories
    config.SHOW_VEHICLE_MARKERS = not args.no_markers

    # Print configuration
    print_config_summary(config)

    # Update settings.json with frame 0 positions
    update_settings_with_frame_0(episode_data, config, args.settings_path)

    # Confirm start
    input("\nPress ENTER to start visualization (make sure Unreal is running with Play pressed)...")

    # Run visualization
    visualize_episode(
        episode_data=episode_data,
        config=config,
        start_frame=args.start_frame,
        end_frame=args.end_frame,
        skip_takeoff=args.no_takeoff,
        playback_speed=args.speed
    )

    print("\n✓ Visualization complete!")


if __name__ == "__main__":
    main()
