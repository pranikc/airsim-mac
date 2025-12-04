#!/usr/bin/env python3
"""
AirSim Multi-Agent Episode Visualization with Car Base

This script visualizes multi-agent episodes with drones (defender, attacker)
and a car visual mesh for the base. The car can be stationary or follow a trajectory.

Usage:
    python visualize_episode_with_car.py <episode_json_file> [options]

Examples:
    python visualize_episode_with_car.py ../data/episodes/episode_0001.json
    python visualize_episode_with_car.py ../data/episodes/episode_0001.json --speed 2.0
    python visualize_episode_with_car.py ../data/episodes/episode_0001.json --scale 5.0
    python visualize_episode_with_car.py ../data/episodes/episode_0001.json --car-asset SUV

Requirements:
    - AirSim running in Unreal Engine
    - settings.json with Defender and Attacker vehicles (multirotors)
    - Car asset available (or uses fallback shape)

Author: AirSim Visualization Pipeline
Date: 2025
"""

import airsim
import json
import time
import sys
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add scripts directory to path
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import VisualizationConfig, print_config_summary, transform_position, auto_configure_from_metadata


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


def check_base_trajectory(frames: List[Dict], config: VisualizationConfig) -> bool:
    """
    Check if base has a moving trajectory or is stationary.

    Args:
        frames: List of frame dictionaries
        config: Visualization configuration

    Returns:
        True if base moves, False if stationary
    """
    if len(frames) < 2:
        return False

    first_base = transform_position(frames[0]['base']['pos'], config)

    # Check if any frame has different base position
    for frame in frames[1:]:
        current_base = transform_position(frame['base']['pos'], config)
        # Check if position changed by more than 0.1m
        if abs(current_base[0] - first_base[0]) > 0.1 or \
           abs(current_base[1] - first_base[1]) > 0.1 or \
           abs(current_base[2] - first_base[2]) > 0.1:
            return True

    return False


def spawn_car_object(client: airsim.MultirotorClient, position: airsim.Vector3r,
                     car_asset: str = "Cube", scale: float = 1.0) -> Optional[str]:
    """
    Spawn a car visual object at the specified position.

    Args:
        client: AirSim client
        position: Position to spawn car
        car_asset: Asset name to use (e.g., "SUV", "Cube")
        scale: Scale factor for the object

    Returns:
        Object name if successful, None if failed
    """
    object_name = "BaseCar"

    # Try to destroy existing object first
    try:
        client.simDestroyObject(object_name)
        time.sleep(0.1)
    except:
        pass

    # Pose at ground level
    pose = airsim.Pose(
        airsim.Vector3r(position.x_val, position.y_val, 0.0),
        airsim.to_quaternion(0, 0, 0)
    )

    # Try spawning with physics disabled (visual only)
    try:
        print(f"  Attempting to spawn '{car_asset}' asset...")
        success = client.simSpawnObject(object_name, car_asset, pose, scale, False)

        if success:
            print(f"  ✓ Successfully spawned '{car_asset}' as base car")
            return object_name
        else:
            print(f"  ✗ Failed to spawn '{car_asset}'")
            return None
    except Exception as e:
        print(f"  ✗ Error spawning '{car_asset}': {e}")
        return None


def try_spawn_car_with_fallback(client: airsim.MultirotorClient, position: airsim.Vector3r,
                                 preferred_asset: str = "Cube") -> Optional[str]:
    """
    Try to spawn car with fallback options.

    Args:
        client: AirSim client
        position: Position to spawn car
        preferred_asset: Preferred asset name

    Returns:
        Object name if successful, None if all attempts failed
    """
    print(f"\n{'='*60}")
    print(f"SPAWNING BASE CAR OBJECT")
    print(f"{'='*60}")
    print(f"Position: ({position.x_val:.3f}, {position.y_val:.3f}, 0.0)")

    # Try assets in order of preference
    assets_to_try = []

    # Add user's preferred asset first
    if preferred_asset:
        assets_to_try.append((preferred_asset, 1.0))

    # Fallback options
    fallback_assets = [
        ("SUV", 1.0),
        ("Sedan", 1.0),
        ("Car", 1.0),
        ("Cube", 2.0),  # Scale up cube to be more visible
    ]

    # Add fallbacks that aren't the preferred asset
    for asset, scale in fallback_assets:
        if asset != preferred_asset:
            assets_to_try.append((asset, scale))

    # Try each asset
    for asset_name, scale in assets_to_try:
        result = spawn_car_object(client, position, asset_name, scale)
        if result:
            print(f"{'='*60}\n")
            return result

    print(f"  ⚠️  All spawn attempts failed")
    print(f"  Continuing without car object (will use markers only)")
    print(f"{'='*60}\n")
    return None


def update_car_position(client: airsim.MultirotorClient, object_name: str,
                       position: airsim.Vector3r):
    """
    Update car object position.

    Args:
        client: AirSim client
        object_name: Name of the car object
        position: New position
    """
    pose = airsim.Pose(
        airsim.Vector3r(position.x_val, position.y_val, 0.0),
        airsim.to_quaternion(0, 0, 0)
    )
    try:
        client.simSetObjectPose(object_name, pose)
    except:
        pass  # Silently fail if object doesn't exist


def visualize_episode(
    episode_data: Dict[str, Any],
    config: VisualizationConfig,
    start_frame: int = 0,
    end_frame: int = None,
    playback_speed: float = 1.0,
    car_asset: str = "Cube"
):
    """
    Visualize episode in AirSim with car base.

    Args:
        episode_data: Episode data dictionary
        config: Visualization configuration
        start_frame: Starting frame index (default: 0)
        end_frame: Ending frame index (default: last frame)
        playback_speed: Playback speed multiplier
        car_asset: Asset name for car (e.g., "SUV", "Cube")
    """
    frames = episode_data['frames']
    if end_frame is None or end_frame > len(frames):
        end_frame = len(frames)

    print("\n" + "="*60)
    print(f"STARTING VISUALIZATION WITH CAR BASE")
    print("="*60)
    print(f"Frames: {start_frame} to {end_frame} (total: {end_frame - start_frame})")
    print(f"Playback Speed: {playback_speed}x")
    print(f"Car Asset: {car_asset}")
    print("="*60)

    # Connect to AirSim
    print("\nConnecting to AirSim...")
    client = airsim.MultirotorClient()
    client.confirmConnection()
    print("✓ Connected")

    # Check if base has moving trajectory
    base_is_moving = check_base_trajectory(frames[start_frame:end_frame], config)
    print(f"\nBase trajectory: {'MOVING' if base_is_moving else 'STATIONARY'}")

    # Enable API control for drones
    print("\nEnabling API control for drones...")
    client.enableApiControl(True, "Defender")
    client.enableApiControl(True, "Attacker")

    # Arm drones
    print("Arming drones...")
    client.armDisarm(True, "Defender")
    client.armDisarm(True, "Attacker")

    # Takeoff drones
    print("Taking off drones...")
    f1 = client.takeoffAsync(vehicle_name="Defender")
    f2 = client.takeoffAsync(vehicle_name="Attacker")
    f1.join()
    f2.join()

    print("Waiting 3 seconds after takeoff...")
    time.sleep(3)

    # Check positions after takeoff
    def_state = client.getMultirotorState(vehicle_name="Defender")
    att_state = client.getMultirotorState(vehicle_name="Attacker")
    def_pos_after_takeoff = def_state.kinematics_estimated.position
    att_pos_after_takeoff = att_state.kinematics_estimated.position

    print(f"After takeoff:")
    print(f"  Defender: ({def_pos_after_takeoff.x_val:.2f}, {def_pos_after_takeoff.y_val:.2f}, {def_pos_after_takeoff.z_val:.2f})")
    print(f"  Attacker: ({att_pos_after_takeoff.x_val:.2f}, {att_pos_after_takeoff.y_val:.2f}, {att_pos_after_takeoff.z_val:.2f})")

    # Spawn car object at base location
    car_object_name = None

    try:
        # Main visualization loop
        print("\n" + "="*60)
        print("PLAYBACK STARTED")
        print("="*60)
        print("Press Ctrl+C to stop\n")

        # Build complete paths
        print("\nPreparing smooth flight paths...")

        # Colors for visualization
        COLOR_DEFENDER = [0.0, 1.0, 0.0, 1.0]  # Green
        COLOR_ATTACKER = [1.0, 0.0, 0.0, 1.0]  # Red
        COLOR_BASE = [0.0, 0.5, 1.0, 1.0]      # Cyan

        # Collect all waypoints for drones and base
        defender_path = []
        attacker_path = []
        base_path = []

        for frame in frames[start_frame:end_frame]:
            def_pos = transform_position(frame['defender']['pos'], config)
            att_pos = transform_position(frame['attacker']['pos'], config)
            base_pos = transform_position(frame['base']['pos'], config)

            defender_path.append(airsim.Vector3r(def_pos[0], def_pos[1], def_pos[2]))
            attacker_path.append(airsim.Vector3r(att_pos[0], att_pos[1], att_pos[2]))
            base_path.append(airsim.Vector3r(base_pos[0], base_pos[1], base_pos[2]))

        # Spawn car at base starting location
        base_start = base_path[0]
        car_object_name = try_spawn_car_with_fallback(client, base_start, car_asset)

        print(f"✓ Built paths: {len(defender_path)} waypoints")
        print(f"\nFirst waypoint - Defender: ({defender_path[0].x_val:.2f}, {defender_path[0].y_val:.2f}, {defender_path[0].z_val:.2f})")
        print(f"First waypoint - Attacker: ({attacker_path[0].x_val:.2f}, {attacker_path[0].y_val:.2f}, {attacker_path[0].z_val:.2f})")
        print(f"Last waypoint - Defender: ({defender_path[-1].x_val:.2f}, {defender_path[-1].y_val:.2f}, {defender_path[-1].z_val:.2f})")
        print(f"Last waypoint - Attacker: ({attacker_path[-1].x_val:.2f}, {attacker_path[-1].y_val:.2f}, {attacker_path[-1].z_val:.2f})")

        # Move drones to starting positions first
        print(f"\nMoving drones to SCALED starting positions...")
        print(f"  Target Defender: ({defender_path[0].x_val:.2f}, {defender_path[0].y_val:.2f}, {defender_path[0].z_val:.2f})")
        print(f"  Target Attacker: ({attacker_path[0].x_val:.2f}, {attacker_path[0].y_val:.2f}, {attacker_path[0].z_val:.2f})")

        f1 = client.moveToPositionAsync(
            defender_path[0].x_val, defender_path[0].y_val, defender_path[0].z_val,
            velocity=5.0,
            vehicle_name="Defender"
        )
        f2 = client.moveToPositionAsync(
            attacker_path[0].x_val, attacker_path[0].y_val, attacker_path[0].z_val,
            velocity=5.0,
            vehicle_name="Attacker"
        )
        f1.join()
        f2.join()
        time.sleep(2)

        # VERIFY drones reached starting positions
        def_state = client.getMultirotorState(vehicle_name="Defender")
        att_state = client.getMultirotorState(vehicle_name="Attacker")
        def_actual = def_state.kinematics_estimated.position
        att_actual = att_state.kinematics_estimated.position

        def_error = ((def_actual.x_val - defender_path[0].x_val)**2 +
                     (def_actual.y_val - defender_path[0].y_val)**2 +
                     (def_actual.z_val - defender_path[0].z_val)**2)**0.5
        att_error = ((att_actual.x_val - attacker_path[0].x_val)**2 +
                     (att_actual.y_val - attacker_path[0].y_val)**2 +
                     (att_actual.z_val - attacker_path[0].z_val)**2)**0.5

        print(f"\n✓ Position verification:")
        print(f"  Defender actual: ({def_actual.x_val:.2f}, {def_actual.y_val:.2f}, {def_actual.z_val:.2f}) - Error: {def_error:.2f}m")
        print(f"  Attacker actual: ({att_actual.x_val:.2f}, {att_actual.y_val:.2f}, {att_actual.z_val:.2f}) - Error: {att_error:.2f}m")

        if def_error > 2.0 or att_error > 2.0:
            print(f"\n⚠️  WARNING: Drones didn't reach starting positions accurately!")
            print(f"   This may cause markers to not match drone positions during flight.")
            print(f"   Consider: 1) Using smaller SCALE_FACTOR, 2) Checking environment for obstacles")
            input("   Press ENTER to continue anyway, or Ctrl+C to stop...")

        print(f"\nStarting smooth flight along interpolated paths...")
        print("Press Ctrl+C to stop\n")

        # Velocity scaling with SCALE_FACTOR
        base_velocity = 0.125  # m/s base speed
        flight_velocity = base_velocity * config.SCALE_FACTOR

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

        # Use moveOnPath for smooth flight
        f_def = client.moveOnPathAsync(
            path=defender_path,
            velocity=flight_velocity,
            drivetrain=airsim.DrivetrainType.MaxDegreeOfFreedom,
            yaw_mode=airsim.YawMode(is_rate=False, yaw_or_rate=0),
            lookahead=-1,
            adaptive_lookahead=1,
            vehicle_name="Defender"
        )

        f_att = client.moveOnPathAsync(
            path=attacker_path,
            velocity=flight_velocity,
            drivetrain=airsim.DrivetrainType.MaxDegreeOfFreedom,
            yaw_mode=airsim.YawMode(is_rate=False, yaw_or_rate=0),
            lookahead=-1,
            adaptive_lookahead=1,
            vehicle_name="Attacker"
        )

        # Monitor progress and draw visualizations
        defender_trajectory = []
        attacker_trajectory = []

        print("Drones flying smooth interpolated paths...\n")

        final_def = defender_path[-1]
        final_att = attacker_path[-1]

        def distance(pos, target):
            return ((pos.x_val - target.x_val)**2 +
                    (pos.y_val - target.y_val)**2 +
                    (pos.z_val - target.z_val)**2)**0.5

        max_iterations = 10000
        iteration = 0

        while iteration < max_iterations:
            # Get current positions
            def_state = client.getMultirotorState(vehicle_name="Defender")
            att_state = client.getMultirotorState(vehicle_name="Attacker")
            def_actual = def_state.kinematics_estimated.position
            att_actual = att_state.kinematics_estimated.position

            # Store trajectory points
            defender_trajectory.append([def_actual.x_val, def_actual.y_val, def_actual.z_val])
            attacker_trajectory.append([att_actual.x_val, att_actual.y_val, att_actual.z_val])

            # Update car position if moving and object exists
            if base_is_moving and car_object_name and iteration < len(base_path):
                update_car_position(client, car_object_name, base_path[iteration])

            # Draw trajectories
            if len(defender_trajectory) > 1 and len(defender_trajectory) % 10 == 0:
                points_def = [airsim.Vector3r(p[0], p[1], p[2]) for p in defender_trajectory]
                client.simPlotLineStrip(
                    points=points_def,
                    color_rgba=COLOR_DEFENDER,
                    thickness=2.0,
                    duration=5.0,
                    is_persistent=False
                )

                points_att = [airsim.Vector3r(p[0], p[1], p[2]) for p in attacker_trajectory]
                client.simPlotLineStrip(
                    points=points_att,
                    color_rgba=COLOR_ATTACKER,
                    thickness=2.0,
                    duration=5.0,
                    is_persistent=False
                )

            # Draw identification markers at EXACT drone positions
            def_marker = airsim.Vector3r(def_actual.x_val, def_actual.y_val, def_actual.z_val)
            client.simPlotPoints(
                points=[def_marker],
                color_rgba=COLOR_DEFENDER,
                size=50.0,
                duration=1.0,
                is_persistent=False
            )

            att_marker = airsim.Vector3r(att_actual.x_val, att_actual.y_val, att_actual.z_val)
            client.simPlotPoints(
                points=[att_marker],
                color_rgba=COLOR_ATTACKER,
                size=50.0,
                duration=1.0,
                is_persistent=False
            )

            # Draw text labels
            try:
                client.simPlotStrings(
                    strings=["DEFENDER"],
                    positions=[airsim.Vector3r(def_actual.x_val, def_actual.y_val, def_actual.z_val)],
                    scale=3.0,
                    color_rgba=COLOR_DEFENDER,
                    duration=1.0
                )

                client.simPlotStrings(
                    strings=["ATTACKER"],
                    positions=[airsim.Vector3r(att_actual.x_val, att_actual.y_val, att_actual.z_val)],
                    scale=3.0,
                    color_rgba=COLOR_ATTACKER,
                    duration=1.0
                )
            except:
                pass

            # Check if both drones reached final positions
            def_dist = distance(def_actual, final_def)
            att_dist = distance(att_actual, final_att)

            # Print progress
            if len(defender_trajectory) % 20 == 0:
                current_drone_dist = ((def_actual.x_val - att_actual.x_val)**2 +
                                     (def_actual.y_val - att_actual.y_val)**2 +
                                     (def_actual.z_val - att_actual.z_val)**2)**0.5
                print(f"Flying... Defender: ({def_actual.x_val:.2f}, {def_actual.y_val:.2f}, {def_actual.z_val:.2f}) | {def_dist:.2f}m to target")
                print(f"          Attacker: ({att_actual.x_val:.2f}, {att_actual.y_val:.2f}, {att_actual.z_val:.2f}) | {att_dist:.2f}m to target")
                print(f"          Distance between drones: {current_drone_dist:.2f}m\n")

            if def_dist < 1.0 and att_dist < 1.0:
                drone_dist = ((def_actual.x_val - att_actual.x_val)**2 +
                             (def_actual.y_val - att_actual.y_val)**2 +
                             (def_actual.z_val - att_actual.z_val)**2)**0.5

                print(f"\n✓ Both drones near final positions!")
                print(f"  Defender: ({def_actual.x_val:.2f}, {def_actual.y_val:.2f}, {def_actual.z_val:.2f}) - {def_dist:.2f}m from target")
                print(f"  Attacker: ({att_actual.x_val:.2f}, {att_actual.y_val:.2f}, {att_actual.z_val:.2f}) - {att_dist:.2f}m from target")
                print(f"  Distance between drones: {drone_dist:.2f}m")
                break

            time.sleep(0.05)
            iteration += 1

        # Wait for async operations
        f_def.join()
        f_att.join()

        print("✓ Smooth flight paths completed!")

        print("\n" + "="*60)
        print("PLAYBACK COMPLETE")
        print("="*60)

        print("\nWaiting 3 seconds before landing...")
        time.sleep(3)

    except KeyboardInterrupt:
        print("\n\n⚠️  Visualization interrupted by user")

    except Exception as e:
        print(f"\n\n⚠️  ERROR during visualization: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # Clean up car object
        if car_object_name:
            try:
                print(f"\nCleaning up car object...")
                client.simDestroyObject(car_object_name)
                print(f"✓ Car object removed")
            except:
                pass

        # Land and disarm drones
        try:
            print("\nLanding drones...")
            f1 = client.landAsync(vehicle_name="Defender")
            f2 = client.landAsync(vehicle_name="Attacker")
            f1.join()
            f2.join()

            client.armDisarm(False, "Defender")
            client.armDisarm(False, "Attacker")
            client.enableApiControl(False, "Defender")
            client.enableApiControl(False, "Attacker")
            print("✓ Drones landed and disarmed")
        except:
            print("⚠️  Could not land properly")
            client.reset()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Visualize multi-agent episodes in AirSim with car base',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage (uses Cube by default)
  python visualize_episode_with_car.py ../data/episodes/episode_0001.json

  # Use SUV asset if available
  python visualize_episode_with_car.py ../data/episodes/episode_0001.json --car-asset SUV

  # Custom scale factor
  python visualize_episode_with_car.py ../data/episodes/episode_0001.json --scale 5.0

  # Check available assets first
  python check_available_assets.py
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
        help='Playback speed multiplier (default: 1.0)'
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
        '--scale',
        type=float,
        default=None,
        help='Position scale factor (default: use config.py value)'
    )

    parser.add_argument(
        '--car-asset',
        type=str,
        default='Cube',
        help='Asset name for car (e.g., "SUV", "Sedan", "Cube"). Default: Cube'
    )

    parser.add_argument(
        '--no-trajectories',
        action='store_true',
        help='Disable trajectory visualization'
    )

    parser.add_argument(
        '--no-markers',
        action='store_true',
        help='Disable colored identification markers'
    )

    args = parser.parse_args()

    # Load episode
    try:
        episode_data = load_episode(args.episode_file)
    except Exception as e:
        print(f"\n⚠️  ERROR loading episode: {e}")
        sys.exit(1)

    # Create config
    config = VisualizationConfig()
    config = auto_configure_from_metadata(episode_data['metadata'], config)

    # Apply command-line overrides
    if args.scale is not None:
        if args.scale != config.SCALE_FACTOR:
            print(f"\n⚠️  Overriding scale factor to {args.scale}x")
        config.SCALE_FACTOR = args.scale
    config.SHOW_TRAJECTORIES = not args.no_trajectories
    config.SHOW_VEHICLE_MARKERS = not args.no_markers

    # Print configuration
    print_config_summary(config)

    # Confirm start
    input("\nPress ENTER to start visualization (Unreal must be running)...")

    # Run visualization
    visualize_episode(
        episode_data=episode_data,
        config=config,
        start_frame=args.start_frame,
        end_frame=args.end_frame,
        playback_speed=args.speed,
        car_asset=args.car_asset
    )

    print("\n✓ Visualization complete!")


if __name__ == "__main__":
    main()
