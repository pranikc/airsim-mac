"""
Multi-agent AirSim controller for episode visualization.

This module handles:
- Multiple drone control (Defender, Attacker)
- Base sphere visualization
- Trajectory rendering
- Synchronized movement
"""

import airsim
import numpy as np
import time
from typing import Dict, List, Tuple, Any, Optional
from config import VisualizationConfig, transform_position, transform_orientation, calculate_velocity_magnitude


class MultiAgentRunner:
    """
    Controls multiple AirSim vehicles for episode visualization.
    """

    def __init__(self, config: Optional[VisualizationConfig] = None):
        """
        Initialize multi-agent runner.

        Args:
            config: VisualizationConfig instance (uses default if None)
        """
        self.config = config if config is not None else VisualizationConfig()
        self.client = None
        self.defender_name = self.config.DEFENDER_NAME
        self.attacker_name = self.config.ATTACKER_NAME

        # Trajectory storage for visualization
        self.defender_trajectory = []
        self.attacker_trajectory = []
        self.base_position = None

        # Statistics
        self.frame_count = 0
        self.start_time = None

    def connect(self):
        """Connect to AirSim simulator."""
        print("Connecting to AirSim...")
        self.client = airsim.MultirotorClient()
        self.client.confirmConnection()
        print("✓ Connected to AirSim")

        # Verify vehicles exist
        self._verify_vehicles()

    def _verify_vehicles(self):
        """Verify that both vehicles are configured in AirSim."""
        print(f"\nVerifying vehicles...")
        try:
            # Try to get state of both vehicles
            defender_state = self.client.getMultirotorState(vehicle_name=self.defender_name)
            attacker_state = self.client.getMultirotorState(vehicle_name=self.attacker_name)
            print(f"✓ Found vehicle: {self.defender_name}")
            print(f"✓ Found vehicle: {self.attacker_name}")
        except Exception as e:
            print(f"\n⚠️  ERROR: Could not find vehicles!")
            print(f"Make sure your AirSim settings.json has vehicles named:")
            print(f"  - {self.defender_name}")
            print(f"  - {self.attacker_name}")
            print(f"\nSee visualization/settings_multiagent.json for example configuration.")
            raise

    def setup(self):
        """Initialize both drones for flight."""
        print("\nSetting up vehicles...")

        # Enable API control
        self.client.enableApiControl(True, self.defender_name)
        self.client.enableApiControl(True, self.attacker_name)

        # Arm drones
        self.client.armDisarm(True, self.defender_name)
        self.client.armDisarm(True, self.attacker_name)

        print(f"✓ {self.defender_name} armed and ready")
        print(f"✓ {self.attacker_name} armed and ready")

    def takeoff(self):
        """Take off both drones."""
        print("\nTaking off...")

        # Takeoff both drones simultaneously
        f1 = self.client.takeoffAsync(vehicle_name=self.defender_name)
        f2 = self.client.takeoffAsync(vehicle_name=self.attacker_name)

        f1.join()
        f2.join()

        time.sleep(2)  # Let drones stabilize
        print("✓ Both vehicles airborne")

    def move_to_frame(self, frame_data: Dict[str, Any], wait: bool = True):
        """
        Move both drones to positions specified in frame data.

        Args:
            frame_data: Frame dictionary with 'defender', 'attacker', 'base' positions
            wait: If True, wait for movements to complete
        """
        # Extract positions
        defender_pos_raw = frame_data['defender']['pos']
        attacker_pos_raw = frame_data['attacker']['pos']
        base_pos_raw = frame_data['base']['pos']

        # Transform coordinates
        def_x, def_y, def_z = transform_position(defender_pos_raw, self.config)
        att_x, att_y, att_z = transform_position(attacker_pos_raw, self.config)
        base_x, base_y, base_z = transform_position(base_pos_raw, self.config)

        # Store base position for visualization (first time only)
        if self.base_position is None:
            self.base_position = [base_x, base_y, base_z]
            self._visualize_base()

        # Debug: Print positions being sent
        if self.frame_count % 5 == 0:  # Print every 5 waypoints
            print(f"    → Defender target: ({def_x:.2f}, {def_y:.2f}, {def_z:.2f})")
            print(f"    → Attacker target: ({att_x:.2f}, {att_y:.2f}, {att_z:.2f})")

        # Move drones using moveToPositionAsync with reasonable velocity
        velocity = 5.0  # m/s - moderate velocity for smooth following
        f_def = self.client.moveToPositionAsync(
            def_x, def_y, def_z,
            velocity,
            timeout_sec=30,  # Longer timeout to prevent premature cancellation
            vehicle_name=self.defender_name
        )
        f_att = self.client.moveToPositionAsync(
            att_x, att_y, att_z,
            velocity,
            timeout_sec=30,
            vehicle_name=self.attacker_name
        )

        # Wait for movement to complete if requested
        if wait:
            f_def.join()
            f_att.join()

        # Store trajectory points
        self.defender_trajectory.append([def_x, def_y, def_z])
        self.attacker_trajectory.append([att_x, att_y, att_z])

        # Draw trajectories periodically
        if self.config.SHOW_TRAJECTORIES and len(self.defender_trajectory) % 10 == 0:
            self._draw_trajectories()

        # Draw identification markers at TARGET positions (where drones should be going)
        self._draw_vehicle_markers(def_x, def_y, def_z, att_x, att_y, att_z)

        self.frame_count += 1

    def _draw_vehicle_markers(self, def_x, def_y, def_z, att_x, att_y, att_z):
        """
        Draw colored identification markers above each vehicle.

        Args:
            def_x, def_y, def_z: Defender position
            att_x, att_y, att_z: Attacker position
        """
        if not self.config.SHOW_VEHICLE_MARKERS:
            return

        # Height offset above drone
        marker_offset = self.config.VEHICLE_MARKER_OFFSET

        # Defender marker (Green) - floating sphere above drone
        defender_marker_pos = airsim.Vector3r(def_x, def_y, def_z + marker_offset)
        self.client.simPlotPoints(
            points=[defender_marker_pos],
            color_rgba=self.config.TRAJECTORY_COLOR_DEFENDER,
            size=self.config.VEHICLE_MARKER_SIZE,
            duration=0.5,  # Short duration, updated every frame
            is_persistent=False
        )

        # Attacker marker (Red) - floating sphere above drone
        attacker_marker_pos = airsim.Vector3r(att_x, att_y, att_z + marker_offset)
        self.client.simPlotPoints(
            points=[attacker_marker_pos],
            color_rgba=self.config.TRAJECTORY_COLOR_ATTACKER,
            size=self.config.VEHICLE_MARKER_SIZE,
            duration=0.5,
            is_persistent=False
        )

        # Draw text labels (if supported in AirSim version)
        try:
            # Defender label
            self.client.simPlotStrings(
                strings=["DEFENDER"],
                positions=[airsim.Vector3r(def_x, def_y, def_z + marker_offset - 0.3)],
                scale=2.0,
                color_rgba=[0.0, 1.0, 0.0, 1.0],
                duration=0.5
            )

            # Attacker label
            self.client.simPlotStrings(
                strings=["ATTACKER"],
                positions=[airsim.Vector3r(att_x, att_y, att_z + marker_offset - 0.3)],
                scale=2.0,
                color_rgba=[1.0, 0.0, 0.0, 1.0],
                duration=0.5
            )
        except:
            # Text labels not supported in this AirSim version
            pass

    def _visualize_base(self):
        """
        Visualize base/target position with an unmissable marker tower.
        """
        if self.base_position is None:
            return

        bx, by, bz = self.base_position

        print(f"\n{'='*60}")
        print(f"BASE MARKER AT ORIGIN")
        print(f"{'='*60}")
        print(f"Base position: X={bx:.3f}, Y={by:.3f}, Z={bz:.3f}")

        # Draw a TINY marker - just barely above the floor for identification
        # In NED: negative Z is up, so -0.3 means 30cm above ground

        base_color = self.config.TRAJECTORY_COLOR_BASE

        # Single small sphere just above ground
        sphere_pos = airsim.Vector3r(bx, by, -0.3)  # 30cm above ground
        self.client.simPlotPoints(
            points=[sphere_pos],
            color_rgba=base_color,
            size=30.0,  # Small, subtle marker
            duration=99999.0,
            is_persistent=True
        )
        print(f"Drawing small cyan sphere at ground level (Z=-0.3m)")

        # Draw small "BASE" text label
        try:
            label_pos = airsim.Vector3r(bx, by, -0.6)  # 60cm high
            self.client.simPlotStrings(
                strings=["BASE"],
                positions=[label_pos],
                scale=1.5,  # Small, subtle text
                color_rgba=base_color,
                duration=99999.0
            )
            print(f"'BASE' label at Z=-0.6m")
        except:
            pass

        print(f"{'='*60}\n")

    def _draw_trajectories(self):
        """Draw trajectory trails for both drones."""
        if not self.config.SHOW_TRAJECTORIES:
            return

        # Draw defender trajectory (green)
        if len(self.defender_trajectory) > 1:
            points_def = [airsim.Vector3r(p[0], p[1], p[2]) for p in self.defender_trajectory]
            self.client.simPlotLineStrip(
                points=points_def,
                color_rgba=self.config.TRAJECTORY_COLOR_DEFENDER,
                thickness=self.config.TRAJECTORY_THICKNESS,
                duration=5.0,  # Persist for 5 seconds
                is_persistent=False
            )

        # Draw attacker trajectory (red)
        if len(self.attacker_trajectory) > 1:
            points_att = [airsim.Vector3r(p[0], p[1], p[2]) for p in self.attacker_trajectory]
            self.client.simPlotLineStrip(
                points=points_att,
                color_rgba=self.config.TRAJECTORY_COLOR_ATTACKER,
                thickness=self.config.TRAJECTORY_THICKNESS,
                duration=5.0,
                is_persistent=False
            )

    def get_current_positions(self) -> Dict[str, Tuple[float, float, float]]:
        """
        Get current positions of both vehicles.

        Returns:
            Dictionary with 'defender' and 'attacker' positions
        """
        def_state = self.client.getMultirotorState(vehicle_name=self.defender_name)
        att_state = self.client.getMultirotorState(vehicle_name=self.attacker_name)

        return {
            'defender': (
                def_state.kinematics_estimated.position.x_val,
                def_state.kinematics_estimated.position.y_val,
                def_state.kinematics_estimated.position.z_val
            ),
            'attacker': (
                att_state.kinematics_estimated.position.x_val,
                att_state.kinematics_estimated.position.y_val,
                att_state.kinematics_estimated.position.z_val
            )
        }

    def land_and_disarm(self):
        """Safely land both drones and clean up."""
        print("\nLanding vehicles...")

        # Land both simultaneously
        f1 = self.client.landAsync(vehicle_name=self.defender_name)
        f2 = self.client.landAsync(vehicle_name=self.attacker_name)

        f1.join()
        f2.join()

        # Disarm
        self.client.armDisarm(False, self.defender_name)
        self.client.armDisarm(False, self.attacker_name)

        # Disable API control
        self.client.enableApiControl(False, self.defender_name)
        self.client.enableApiControl(False, self.attacker_name)

        print("✓ Both vehicles landed and disarmed")

    def reset(self):
        """Reset simulation."""
        print("\nResetting simulation...")
        self.client.reset()
        self.defender_trajectory = []
        self.attacker_trajectory = []
        self.base_position = None
        self.frame_count = 0
        print("✓ Simulation reset")

    def print_statistics(self, episode_data: Dict[str, Any]):
        """Print episode statistics."""
        if self.start_time is None:
            return

        elapsed_time = time.time() - self.start_time
        total_frames = len(episode_data['frames'])

        print("\n" + "="*60)
        print("EPISODE STATISTICS")
        print("="*60)
        print(f"Episode: {episode_data['metadata']['episode']}")
        print(f"Outcome: {episode_data['metadata']['outcome']}")
        print(f"Total Reward: {episode_data['metadata']['total_reward']:.2f}")
        print(f"Frames Processed: {self.frame_count}/{total_frames}")
        print(f"Execution Time: {elapsed_time:.2f}s")
        print(f"Average FPS: {self.frame_count/elapsed_time:.1f}")
        print("="*60 + "\n")


if __name__ == "__main__":
    # Test connection
    runner = MultiAgentRunner()
    runner.connect()
    print("✓ Multi-agent runner initialized successfully")
