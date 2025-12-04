"""
Configuration and coordinate transformation utilities for AirSim visualization.

This module handles:
- Coordinate system conversions between training environment and AirSim
- Scaling parameters
- Visualization settings
"""

import numpy as np
from typing import Tuple, Dict, Any


class VisualizationConfig:
    """Configuration for episode visualization"""

    # Coordinate transformation
    # Data converted from cm to meters (100cm = 1m in AirSim)
    # SCALE_FACTOR: Multiplies all coordinates for visualization
    #   1.0 = Original scale (2m trajectory stays 2m)
    #   2.0 = 2x larger (2m trajectory becomes 4m)
    #   5.0 = 5x larger (2m trajectory becomes 10m)
    # WARNING: Large scale factors (>2.0) may cause:
    #   - Drones spawning underground relative to trajectory
    #   - Environment boundary issues
    #   - Camera/viewing difficulties
    SCALE_FACTOR = 1.0  # 1x scale (1:1 original size)
    INVERT_Z = False  # Both data and AirSim use NED - no inversion
    Z_OFFSET = 0.0  # Additional Z offset in meters (rarely needed)

    # Playback settings
    DEFAULT_PLAYBACK_SPEED = 1.0  # 1.0 = real-time, 2.0 = 2x speed, 0.5 = slow-mo
    VELOCITY_THRESHOLD = 0.5  # m/s - for determining hover vs. movement

    # Movement smoothness settings
    MIN_DRONE_VELOCITY = 5.0  # m/s - minimum velocity for smooth movement (higher = smoother)
    MOVEMENT_LOOKAHEAD = 1.0  # meters - lookahead distance for path smoothing
    MOVEMENT_TIMEOUT = 1.0  # seconds - timeout for each movement command

    # Vehicle names (must match settings.json)
    DEFENDER_NAME = "Defender"
    ATTACKER_NAME = "Attacker"
    BASE_OBJECT_NAME = "Base"  # If sphere object exists in Unreal scene

    # Visualization settings
    SHOW_TRAJECTORIES = True  # Draw trajectory trails
    SHOW_VEHICLE_MARKERS = True  # Show colored markers above vehicles
    TRAJECTORY_COLOR_DEFENDER = [0.0, 1.0, 0.0, 1.0]  # Green
    TRAJECTORY_COLOR_ATTACKER = [1.0, 0.0, 0.0, 1.0]  # Red
    TRAJECTORY_COLOR_BASE = [0.0, 0.5, 1.0, 1.0]  # Bright Blue/Cyan
    TRAJECTORY_THICKNESS = 2.0
    BASE_MARKER_SIZE = 20.0  # Size of base marker point
    VEHICLE_MARKER_SIZE = 30.0  # Size of vehicle identification markers
    VEHICLE_MARKER_OFFSET = 0.0  # Height offset from vehicle (0 = exact position)

    # Logging
    LOG_EVERY_N_FRAMES = 10  # Print status every N frames
    SAVE_EXECUTION_LOG = True


def transform_position(pos: list, config: VisualizationConfig = None) -> Tuple[float, float, float]:
    """
    Transform position from training coordinate system to AirSim NED.

    Training data format: [x, y, z] in METERS (already converted by convert script)
    AirSim format: [x, y, z] in METERS (z is down, negative is up)

    Args:
        pos: Position [x, y, z] from episode data in METERS
        config: VisualizationConfig instance (uses default if None)

    Returns:
        Tuple of (x, y, z) in AirSim coordinates (scaled meters)
    """
    if config is None:
        config = VisualizationConfig()

    x, y, z = pos[0], pos[1], pos[2]

    # Apply scaling (data is already in meters from convert script)
    x_airsim = x * config.SCALE_FACTOR
    y_airsim = y * config.SCALE_FACTOR
    z_airsim = z * config.SCALE_FACTOR

    # Invert Z axis if needed (both use NED, so no inversion)
    if config.INVERT_Z:
        z_airsim = -z_airsim

    # Apply Z offset (to adjust overall altitude)
    z_airsim += config.Z_OFFSET

    return (x_airsim, y_airsim, z_airsim)


def transform_orientation(rpy: list) -> Tuple[float, float, float]:
    """
    Transform orientation from training data to AirSim.

    Args:
        rpy: [roll, pitch, yaw] in radians from training data

    Returns:
        Tuple of (roll, pitch, yaw) in degrees for AirSim
    """
    roll, pitch, yaw = rpy[0], rpy[1], rpy[2]

    # Convert radians to degrees
    roll_deg = np.degrees(roll)
    pitch_deg = np.degrees(pitch)
    yaw_deg = np.degrees(yaw)

    return (roll_deg, pitch_deg, yaw_deg)


def calculate_velocity_magnitude(vel: list) -> float:
    """
    Calculate velocity magnitude from velocity vector.

    Args:
        vel: [vx, vy, vz] velocity vector

    Returns:
        Speed in m/s
    """
    return np.linalg.norm(vel)


def get_frame_timing(episode_data: Dict[str, Any], frame_idx: int, playback_speed: float = 1.0) -> float:
    """
    Calculate wait time for a frame based on timestamp and playback speed.

    Args:
        episode_data: Full episode data dictionary
        frame_idx: Current frame index
        playback_speed: Playback speed multiplier (1.0 = real-time)

    Returns:
        Wait time in seconds
    """
    frames = episode_data['frames']

    if frame_idx >= len(frames) - 1:
        return 0.1  # Default wait for last frame

    current_t = frames[frame_idx]['t']
    next_t = frames[frame_idx + 1]['t']

    dt = next_t - current_t

    # Adjust for playback speed (higher speed = less wait)
    adjusted_dt = dt / playback_speed

    # Ensure minimum wait time
    return max(adjusted_dt, 0.001)


def auto_configure_from_metadata(metadata: Dict[str, Any], config: VisualizationConfig = None, episode_data: Dict[str, Any] = None) -> VisualizationConfig:
    """
    Auto-configure visualization based on episode metadata.

    Args:
        metadata: Episode metadata dictionary
        config: Existing config to update (creates new if None)
        episode_data: Full episode data (optional, for auto-detecting Z inversion)

    Returns:
        Updated VisualizationConfig
    """
    if config is None:
        config = VisualizationConfig()

    # Check coordinate system
    coord_system = metadata.get('coordinate_system', 'NED').upper()

    # Auto-detect Z inversion if episode data provided
    if episode_data and 'frames' in episode_data:
        # Sample some Z values from the episode data
        sample_z_values = []
        for i in range(0, min(10, len(episode_data['frames'])), max(1, len(episode_data['frames']) // 10)):
            frame = episode_data['frames'][i]
            if 'defender' in frame and 'pos' in frame['defender']:
                sample_z_values.append(frame['defender']['pos'][2])
            if 'attacker' in frame and 'pos' in frame['attacker']:
                sample_z_values.append(frame['attacker']['pos'][2])

        # If most Z values are positive, assume Z+ up system and invert
        if sample_z_values:
            avg_z = sum(sample_z_values) / len(sample_z_values)
            if avg_z > 1.0:  # If average Z is significantly positive (>1m)
                print(f"\n⚠️  Auto-detected Z+ up coordinate system (avg Z = {avg_z:.2f}m)")
                print(f"   Setting INVERT_Z = True to convert to NED (negative Z = up)")
                config.INVERT_Z = True
            else:
                print(f"\n✓ Z values appear to be in NED (avg Z = {avg_z:.2f}m, negative = up)")
                config.INVERT_Z = False
    else:
        # Fallback to metadata
        if coord_system == 'NED':
            config.INVERT_Z = False
        else:
            # For non-NED systems, assume Z+ up and invert
            config.INVERT_Z = True

    # Keep existing scale factor (don't override)
    # config.SCALE_FACTOR is already set in the class definition
    config.Z_OFFSET = 0.0  # No offset needed

    return config


def print_config_summary(config: VisualizationConfig = None):
    """Print configuration summary for debugging."""
    if config is None:
        config = VisualizationConfig()

    print("\n" + "="*60)
    print("VISUALIZATION CONFIGURATION")
    print("="*60)
    print(f"Scale Factor: {config.SCALE_FACTOR}x")
    print(f"Invert Z-axis: {config.INVERT_Z}")
    print(f"Playback Speed: {config.DEFAULT_PLAYBACK_SPEED}x")
    print(f"Defender Vehicle: {config.DEFENDER_NAME} (Green)")
    print(f"Attacker Vehicle: {config.ATTACKER_NAME} (Red)")
    print(f"Base: {config.BASE_OBJECT_NAME} (Cyan)")
    print(f"Show Trajectories: {config.SHOW_TRAJECTORIES}")
    print(f"Show Vehicle Markers: {config.SHOW_VEHICLE_MARKERS}")
    print("="*60 + "\n")


if __name__ == "__main__":
    # Test coordinate transformation
    config = VisualizationConfig()
    print_config_summary(config)

    # Example transformation
    training_pos = [0.245, -0.883, 2.0]
    airsim_pos = transform_position(training_pos, config)
    print(f"Training position: {training_pos}")
    print(f"AirSim position: {airsim_pos}")

    training_rpy = [0.0, 0.0, 1.57]  # 90 degrees yaw in radians
    airsim_rpy = transform_orientation(training_rpy)
    print(f"Training RPY (rad): {training_rpy}")
    print(f"AirSim RPY (deg): {airsim_rpy}")
