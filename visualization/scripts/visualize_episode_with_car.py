#!/usr/bin/env python3
"""
AirSim Waypoint Visualization with Custom FBX Base Model

This script provides visualization for AirSim waypoint trajectories with
a custom FBX model representing the base (tank).

Usage:
    python visualize_episode_with_car.py <waypoints_json> [options]

Examples:
    python visualize_episode_with_car.py ../data/airsim_waypoints/episode_0001_airsim.json
    python visualize_episode_with_car.py ../data/airsim_waypoints/episode_0001_airsim.json --speed 2.0
    python visualize_episode_with_car.py ../data/airsim_waypoints/episode_0001_airsim.json --fbx-asset TankMesh

Author: AirSim Visualization Pipeline
Date: 2025
"""

import sys
import argparse
from pathlib import Path
import tempfile
import os
import airsim
import time

# Add scripts directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from convert_waypoints_to_episode import convert_waypoints_to_episode
from visualize_episode import update_settings_with_frame_0, load_episode
from config import VisualizationConfig, print_config_summary, auto_configure_from_metadata, transform_position


def spawn_fbx_model(client: airsim.MultirotorClient, position: airsim.Vector3r,
                    asset_name: str = "TankMesh", scale: float = 1.0):
    """
    Spawn the FBX model at the specified position.

    Args:
        client: AirSim client
        position: Position to spawn the model
        asset_name: Name of the imported asset in Unreal (default: "TankMesh")
        scale: Scale factor for the model

    Returns:
        Object name if successful, None if failed
    """
    object_name = "BaseTank"

    # Try to destroy existing object first
    try:
        client.simDestroyObject(object_name)
        time.sleep(0.1)
    except:
        pass

    # Pose at ground level (positive Z = down in NED, so 0.5 puts it slightly below to touch floor)
    pose = airsim.Pose(
        airsim.Vector3r(position.x_val, position.y_val, 0.5),
        airsim.to_quaternion(0, 0, 0)
    )

    # Try spawning the FBX model
    try:
        print(f"  Attempting to spawn '{asset_name}' FBX model...")
        # Scale must be a Vector3r, not a float
        scale_vec = airsim.Vector3r(scale, scale, scale)
        success = client.simSpawnObject(object_name, asset_name, pose, scale_vec, False)

        if success:
            print(f"  ✓ Successfully spawned '{asset_name}' as base model")
            return object_name
        else:
            print(f"  ✗ Failed to spawn '{asset_name}'")
            print(f"  NOTE: Make sure the FBX is imported in Unreal and the asset name is correct")
            return None
    except Exception as e:
        print(f"  ✗ Error spawning '{asset_name}': {e}")
        return None


def update_model_position(client: airsim.MultirotorClient, object_name: str,
                         position: airsim.Vector3r):
    """
    Update model object position.

    Args:
        client: AirSim client
        object_name: Name of the model object
        position: New position
    """
    pose = airsim.Pose(
        airsim.Vector3r(position.x_val, position.y_val, 0.5),
        airsim.to_quaternion(0, 0, 0)
    )
    try:
        client.simSetObjectPose(object_name, pose)
    except:
        pass  # Silently fail if object doesn't exist


def check_base_trajectory(frames: list, config: VisualizationConfig) -> bool:
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
        # Check if position changed by more than 0.01m (1cm) - lowered threshold for slow movement
        if abs(current_base[0] - first_base[0]) > 0.01 or \
           abs(current_base[1] - first_base[1]) > 0.01 or \
           abs(current_base[2] - first_base[2]) > 0.01:
            return True

    return False


def visualize_episode_with_fbx(
    episode_data: dict,
    config: VisualizationConfig,
    start_frame: int = 0,
    end_frame: int = None,
    skip_takeoff: bool = False,
    playback_speed: float = 1.0,
    fbx_asset_name: str = "TankMesh",
    fbx_scale: float = 1.0
):
    """
    Visualize episode in AirSim with FBX model for base.

    Args:
        episode_data: Episode data dictionary
        config: Visualization configuration
        start_frame: Starting frame index
        end_frame: Ending frame index
        skip_takeoff: Skip takeoff sequence
        playback_speed: Playback speed multiplier
        fbx_asset_name: Name of the FBX asset in Unreal
        fbx_scale: Scale factor for the FBX model
    """
    frames = episode_data['frames']
    metadata = episode_data['metadata']

    if end_frame is None or end_frame > len(frames):
        end_frame = len(frames)

    print("\n" + "="*60)
    print("STARTING VISUALIZATION WITH FBX BASE MODEL")
    print("="*60)
    print(f"Episode: {metadata['episode']}")
    print(f"Outcome: {metadata['outcome']}")
    print(f"Frames: {start_frame} to {end_frame} (total: {end_frame - start_frame})")
    print(f"Playback Speed: {playback_speed}x")
    print(f"FBX Asset: {fbx_asset_name}")
    print(f"FBX Scale: {fbx_scale}x")
    print("="*60)

    # Connect to AirSim
    print("\nConnecting to AirSim...")
    client = airsim.MultirotorClient()
    client.confirmConnection()
    print("✓ Connected")

    # Check if base has moving trajectory
    base_is_moving = check_base_trajectory(frames[start_frame:end_frame], config)
    print(f"\nBase trajectory: {'MOVING' if base_is_moving else 'STATIONARY'}")

    # Get vehicle names from metadata
    vehicle_names = metadata.get('vehicle_names', ['Defender', 'Attacker'])
    print(f"\nVehicles: {', '.join(vehicle_names)}")

    # Clear all old markers/trajectories from previous runs
    print("\nClearing old visualizations...")
    try:
        client.simFlushPersistentMarkers()
        print("✓ Cleared old markers")
    except:
        print("✓ Marker clearing not supported (old AirSim version)")

    # Enable API control for all vehicles
    print("\nEnabling API control...")
    for vehicle in vehicle_names:
        client.enableApiControl(True, vehicle)
        client.armDisarm(True, vehicle)

    # Takeoff if not skipped
    if not skip_takeoff:
        print("\nTaking off vehicles...")
        futures = [client.takeoffAsync(vehicle_name=v) for v in vehicle_names]
        for f in futures:
            f.join()
        print("Waiting 3 seconds after takeoff...")
        time.sleep(3)

    # Colors for visualization
    COLOR_DEFENDER = [0.0, 1.0, 0.0, 1.0]  # Green
    COLOR_ATTACKER = [1.0, 0.0, 0.0, 1.0]  # Red
    COLOR_BASE = [0.0, 0.5, 1.0, 1.0]      # Cyan

    colors = [COLOR_DEFENDER, COLOR_ATTACKER]

    fbx_object_name = None

    try:
        # Build paths for all entities
        print("\nPreparing flight paths...")
        paths = {vehicle: [] for vehicle in vehicle_names}
        base_path = []

        for frame in frames[start_frame:end_frame]:
            # Drone paths
            for vehicle in vehicle_names:
                key = vehicle.lower()
                if key in frame:
                    pos = transform_position(frame[key]['pos'], config)
                    paths[vehicle].append(airsim.Vector3r(pos[0], pos[1], pos[2]))

            # Base path
            if 'base' in frame:
                base_pos = transform_position(frame['base']['pos'], config)
                base_path.append(airsim.Vector3r(base_pos[0], base_pos[1], base_pos[2]))

        # Spawn FBX model at base starting location
        if base_path:
            base_start = base_path[0]
            print(f"\n{'='*60}")
            print(f"SPAWNING FBX BASE MODEL")
            print(f"{'='*60}")
            print(f"Position: ({base_start.x_val:.3f}, {base_start.y_val:.3f}, 0.0)")
            fbx_object_name = spawn_fbx_model(client, base_start, fbx_asset_name, fbx_scale)
            print(f"{'='*60}\n")

        # Get actual drone positions after takeoff
        print("\nGetting actual drone positions after takeoff...")
        actual_positions = {}
        for vehicle in vehicle_names:
            state = client.getMultirotorState(vehicle_name=vehicle)
            pos = state.kinematics_estimated.position
            actual_positions[vehicle] = pos
            print(f"  {vehicle}: ({pos.x_val:.3f}, {pos.y_val:.3f}, {pos.z_val:.3f})")

        print("\nBuilding flight paths using relative movements from episode data...")

        # Rebuild paths using RELATIVE movements (like visualize_waypoints.py)
        episode_frames = frames[start_frame:end_frame]
        relative_paths = {}

        for vehicle in vehicle_names:
            key = vehicle.lower()
            if key in episode_frames[0]:
                # Start from actual position
                relative_paths[vehicle] = [airsim.Vector3r(
                    actual_positions[vehicle].x_val,
                    actual_positions[vehicle].y_val,
                    actual_positions[vehicle].z_val
                )]

                # Build relative movements between frames
                for i in range(1, len(episode_frames)):
                    prev_frame = episode_frames[i-1]
                    curr_frame = episode_frames[i]

                    # Calculate RELATIVE movement (delta)
                    delta_x = (curr_frame[key]['pos'][0] - prev_frame[key]['pos'][0]) * config.SCALE_FACTOR
                    delta_y = (curr_frame[key]['pos'][1] - prev_frame[key]['pos'][1]) * config.SCALE_FACTOR
                    delta_z = (curr_frame[key]['pos'][2] - prev_frame[key]['pos'][2]) * config.SCALE_FACTOR

                    # Apply relative movement
                    prev_pos = relative_paths[vehicle][-1]
                    relative_paths[vehicle].append(airsim.Vector3r(
                        prev_pos.x_val + delta_x,
                        prev_pos.y_val + delta_y,
                        prev_pos.z_val + delta_z
                    ))

        # Use relative paths instead of absolute paths
        paths = relative_paths

        print(f"✓ Built paths: {len(paths[vehicle_names[0]])} waypoints")

        # Draw persistent starting markers and trajectory lines (like visualize_episode.py)
        print("\nDrawing position markers and trajectories...")

        # DEFENDER starting marker (green sphere)
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
                scale=5.0,
                color_rgba=[0.0, 1.0, 0.0, 1.0],
                duration=9999.0
            )
            print(f"  ✓ DEFENDER (green) at: ({def_start_scaled.x_val:.2f}, {def_start_scaled.y_val:.2f}, {def_start_scaled.z_val:.2f}) [text shown]")
        except Exception as e:
            print(f"  ✓ DEFENDER (green) at: ({def_start_scaled.x_val:.2f}, {def_start_scaled.y_val:.2f}, {def_start_scaled.z_val:.2f}) [text not supported]")

        # ATTACKER starting marker (red sphere)
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
                scale=5.0,
                color_rgba=[1.0, 0.0, 0.0, 1.0],
                duration=9999.0
            )
            print(f"  ✓ ATTACKER (red) at: ({att_start_scaled.x_val:.2f}, {att_start_scaled.y_val:.2f}, {att_start_scaled.z_val:.2f}) [text shown]")
        except Exception as e:
            print(f"  ✓ ATTACKER (red) at: ({att_start_scaled.x_val:.2f}, {att_start_scaled.y_val:.2f}, {att_start_scaled.z_val:.2f}) [text not supported]")

        # Build visual paths for trajectory lines (scale X/Y, not Z)
        defender_path_visual = []
        attacker_path_visual = []
        for frame in episode_frames:
            def_pos = frame['defender']['pos']
            att_pos = frame['attacker']['pos']
            defender_path_visual.append(airsim.Vector3r(
                def_pos[0] * config.SCALE_FACTOR,
                def_pos[1] * config.SCALE_FACTOR,
                def_pos[2]  # Don't scale Z
            ))
            attacker_path_visual.append(airsim.Vector3r(
                att_pos[0] * config.SCALE_FACTOR,
                att_pos[1] * config.SCALE_FACTOR,
                att_pos[2]  # Don't scale Z
            ))

        # Draw trajectory lines
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

        print("\nStarting smooth flight...")
        print("Press Ctrl+C to stop\n")

        # Calculate velocity - slower for smoother visualization
        base_velocity = 0.1  # m/s base speed (slower for smooth movement)
        flight_velocity = base_velocity * config.SCALE_FACTOR  # Don't divide by playback_speed here

        # Start async movement for all drones
        drone_futures = []
        for vehicle in vehicle_names:
            if paths[vehicle]:
                f = client.moveOnPathAsync(
                    path=paths[vehicle],
                    velocity=flight_velocity,
                    drivetrain=airsim.DrivetrainType.MaxDegreeOfFreedom,
                    yaw_mode=airsim.YawMode(is_rate=False, yaw_or_rate=0),
                    lookahead=-1,
                    adaptive_lookahead=1,
                    vehicle_name=vehicle
                )
                drone_futures.append((vehicle, f))

        # Monitor progress and update visualizations
        trajectories = {vehicle: [] for vehicle in vehicle_names}
        iteration = 0
        max_iterations = 10000

        while iteration < max_iterations:
            all_complete = True

            for i, vehicle in enumerate(vehicle_names):
                # Get current position
                state = client.getMultirotorState(vehicle_name=vehicle)
                pos = state.kinematics_estimated.position

                # Store trajectory
                trajectories[vehicle].append([pos.x_val, pos.y_val, pos.z_val])

                # No moving markers - using persistent markers from start

                # Check if reached end
                if paths[vehicle]:
                    final = paths[vehicle][-1]
                    dist = ((pos.x_val - final.x_val)**2 +
                           (pos.y_val - final.y_val)**2 +
                           (pos.z_val - final.z_val)**2)**0.5

                    if dist >= 1.0:
                        all_complete = False

            # Update FBX model position if base is moving (with interpolation)
            if base_is_moving and fbx_object_name and len(base_path) > 1:
                # Calculate interpolated position based on elapsed time
                elapsed_time = iteration * 0.05  # Each iteration is 0.05 seconds

                # Find which waypoint segment we're in
                # Assuming waypoints are 1 second apart
                waypoint_interval = 1.0  # seconds between waypoints
                waypoint_index = elapsed_time / waypoint_interval

                # Get the two waypoints to interpolate between
                idx1 = int(waypoint_index)
                idx2 = min(idx1 + 1, len(base_path) - 1)

                if idx1 < len(base_path):
                    # Calculate interpolation factor (0.0 to 1.0)
                    t = waypoint_index - idx1

                    # Linear interpolation between waypoints
                    pos1 = base_path[idx1]
                    pos2 = base_path[idx2]

                    interpolated_pos = airsim.Vector3r(
                        pos1.x_val + (pos2.x_val - pos1.x_val) * t,
                        pos1.y_val + (pos2.y_val - pos1.y_val) * t,
                        pos1.z_val + (pos2.z_val - pos1.z_val) * t
                    )

                    update_model_position(client, fbx_object_name, interpolated_pos)

                    # Debug: Print position every 50 iterations
                    if iteration % 50 == 0:
                        print(f"  Base position update [{iteration}]: ({interpolated_pos.x_val:.2f}, {interpolated_pos.y_val:.2f}, {interpolated_pos.z_val:.2f})")

            # Check if all drones completed AND we've processed all base positions
            # Don't exit early if base is still moving
            if all_complete and (not base_is_moving or iteration >= len(base_path) - 1):
                print("\n✓ All vehicles reached final positions!")
                if base_is_moving:
                    print(f"✓ Base completed movement ({iteration + 1}/{len(base_path)} positions)")
                break

            time.sleep(0.05)
            iteration += 1

        # Wait for async operations
        for vehicle, f in drone_futures:
            f.join()

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
        # Clean up FBX object
        if fbx_object_name:
            try:
                print(f"\nCleaning up FBX model...")
                client.simDestroyObject(fbx_object_name)
                print(f"✓ FBX model removed")
            except:
                pass

        # Land and disarm drones
        try:
            print("\nLanding vehicles...")
            futures = [client.landAsync(vehicle_name=v) for v in vehicle_names]
            for f in futures:
                f.join()

            # Wait for landing to complete
            print("Waiting for landing to complete...")
            time.sleep(3)

            for vehicle in vehicle_names:
                client.armDisarm(False, vehicle)
                client.enableApiControl(False, vehicle)
            print("✓ Vehicles landed and disarmed")
        except Exception as e:
            print(f"⚠️  Could not land properly: {e}")
            try:
                client.reset()
            except:
                pass


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Visualize AirSim waypoints with custom FBX base model',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage
  python visualize_episode_with_car.py ../data/airsim_waypoints/episode_0001_airsim.json

  # 2x speed playback
  python visualize_episode_with_car.py ../data/airsim_waypoints/episode_0001_airsim.json --speed 2.0

  # Custom FBX asset name (if you renamed it in Unreal)
  python visualize_episode_with_car.py ../data/airsim_waypoints/episode_0001_airsim.json --fbx-asset MyTankMesh

  # Scale the FBX model
  python visualize_episode_with_car.py ../data/airsim_waypoints/episode_0001_airsim.json --fbx-scale 2.0
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
        help='Scale factor for positions (overrides config.py value)'
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
        help='Disable colored identification markers'
    )

    parser.add_argument(
        '--settings-path',
        type=str,
        default='/tmp/AirSim/settings.json',
        help='Path to AirSim settings.json (default: /tmp/AirSim/settings.json)'
    )

    parser.add_argument(
        '--fbx-asset',
        type=str,
        default='TankMesh',
        help='Name of the FBX asset in Unreal (default: TankMesh)'
    )

    parser.add_argument(
        '--fbx-scale',
        type=float,
        default=1.0,
        help='Scale factor for the FBX model (default: 1.0)'
    )

    parser.add_argument(
        '--keep-converted',
        action='store_true',
        help='Keep the converted episode file'
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
    print("AIRSIM WAYPOINT VISUALIZATION WITH FBX MODEL")
    print("="*60)
    print(f"Input: {waypoints_path.name}")
    print(f"FBX Model: {args.fbx_asset}")
    print("="*60 + "\n")

    # Step 1: Convert waypoints to episode format
    print("Step 1: Converting waypoints to episode format...")

    if args.output_converted:
        converted_path = args.output_converted
        keep_converted = True
    elif args.keep_converted:
        converted_path = str(waypoints_path.parent / f"{waypoints_path.stem}_converted.json")
        keep_converted = True
    else:
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

    # Step 3: Auto-configure
    print("\nStep 3: Auto-configuring from episode metadata...")
    config = VisualizationConfig()
    config = auto_configure_from_metadata(episode_data['metadata'], config, episode_data)

    # Override scale if provided
    if args.scale is not None:
        config.SCALE_FACTOR = args.scale
        print(f"✓ Scale factor overridden to {args.scale}x")

    config.SHOW_TRAJECTORIES = not args.no_trajectories
    config.SHOW_VEHICLE_MARKERS = not args.no_markers

    # Print configuration
    print_config_summary(config)

    # Step 4: Update settings.json
    print("\nStep 4: Updating AirSim settings.json...")
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

    print("\nStep 5: Running visualization with FBX model...")
    try:
        visualize_episode_with_fbx(
            episode_data=episode_data,
            config=config,
            start_frame=args.start_frame,
            end_frame=args.end_frame,
            skip_takeoff=args.no_takeoff,
            playback_speed=args.speed,
            fbx_asset_name=args.fbx_asset,
            fbx_scale=args.fbx_scale
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
