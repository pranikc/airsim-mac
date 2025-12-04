#!/usr/bin/env python3
"""
Run predefined trajectories from JSON files in AirSim (auto mode - no prompts)
Usage: python run_trajectory_auto.py trajectories/straight_line.json
"""

import airsim
import json
import time
import sys
import os
import numpy as np
from pathlib import Path

class TrajectoryRunner:
    def __init__(self):
        """Initialize AirSim connection"""
        print("Connecting to AirSim...")
        self.client = airsim.MultirotorClient()
        self.client.confirmConnection()
        print("✓ Connected to AirSim")

        self.trajectory_data = None
        self.start_time = None
        self.positions_log = []

    def load_trajectory(self, json_file):
        """Load trajectory from JSON file"""
        print(f"\nLoading trajectory from: {json_file}")

        if not os.path.exists(json_file):
            raise FileNotFoundError(f"Trajectory file not found: {json_file}")

        with open(json_file, 'r') as f:
            self.trajectory_data = json.load(f)

        print(f"✓ Loaded: {self.trajectory_data['name']}")
        print(f"  Description: {self.trajectory_data['description']}")
        print(f"  Waypoints: {len(self.trajectory_data['waypoints'])}")
        print(f"  Velocity: {self.trajectory_data['velocity']} m/s")

    def setup_drone(self):
        """Initialize drone for flight"""
        print("\nSetting up drone...")
        self.client.reset()
        self.client.enableApiControl(True)
        self.client.armDisarm(True)

        # Take off to first waypoint
        first_waypoint = self.trajectory_data['waypoints'][0]
        z = first_waypoint['position']['z'] / 100  # Convert cm to meters
        print(f"Taking off to {-z}m altitude...")
        self.client.takeoffAsync().join()
        self.client.moveToZAsync(z, 2).join()

        time.sleep(1)
        print("✓ Drone ready")

    def run_trajectory(self, save_log=True):
        """Execute the trajectory"""
        print("\n" + "="*60)
        print(f"STARTING TRAJECTORY: {self.trajectory_data['name']}")
        print("="*60)

        self.start_time = time.time()
        waypoints = self.trajectory_data['waypoints']
        velocity = self.trajectory_data['velocity']

        for i, wp in enumerate(waypoints):
            print(f"\n[Waypoint {wp['id']}/{len(waypoints)-1}] {wp['description']}")

            # Extract position (convert cm to meters for AirSim API)
            x = wp['position']['x'] / 100
            y = wp['position']['y'] / 100
            z = wp['position']['z'] / 100
            yaw = wp.get('yaw', 0)
            wait_time = wp.get('wait_time', 0.5)

            print(f"  Target: ({x:.2f}, {y:.2f}, {z:.2f}) m, Yaw: {yaw}°")

            # Move to position
            self.client.moveToPositionAsync(
                x, y, z,
                velocity=velocity,
                yaw_mode=airsim.YawMode(is_rate=False, yaw_or_rate=yaw)
            ).join()

            # Log current position
            current_pos = self.client.simGetVehiclePose().position
            self.positions_log.append({
                'waypoint_id': wp['id'],
                'timestamp': time.time() - self.start_time,
                'target': {'x': x, 'y': y, 'z': z},
                'actual': {
                    'x': current_pos.x_val,
                    'y': current_pos.y_val,
                    'z': current_pos.z_val
                },
                'error': np.linalg.norm([
                    current_pos.x_val - x,
                    current_pos.y_val - y,
                    current_pos.z_val - z
                ])
            })

            print(f"  Reached: ({current_pos.x_val:.2f}, {current_pos.y_val:.2f}, {current_pos.z_val:.2f}) m")
            print(f"  Position error: {self.positions_log[-1]['error']:.3f} m")

            # Check for collision
            collision_info = self.client.simGetCollisionInfo()
            if collision_info.has_collided:
                print(f"  ⚠️  COLLISION DETECTED!")
                break

            # Wait at waypoint
            if wait_time > 0:
                print(f"  Waiting {wait_time}s...")
                time.sleep(wait_time)

        total_time = time.time() - self.start_time

        print("\n" + "="*60)
        print(f"TRAJECTORY COMPLETE")
        print(f"Total time: {total_time:.2f}s")
        print(f"Waypoints reached: {len(self.positions_log)}/{len(waypoints)}")
        print("="*60)

        # Calculate statistics
        if len(self.positions_log) > 0:
            errors = [log['error'] for log in self.positions_log]
            print(f"\nPosition Accuracy:")
            print(f"  Mean error: {np.mean(errors):.3f} m")
            print(f"  Max error: {np.max(errors):.3f} m")
            print(f"  Min error: {np.min(errors):.3f} m")

            # Save log
            if save_log:
                self.save_log()

    def save_log(self):
        """Save trajectory execution log"""
        log_dir = Path("trajectory_logs")
        log_dir.mkdir(exist_ok=True)

        timestamp = time.strftime("%Y%m%d_%H%M%S")
        traj_name = self.trajectory_data['name'].replace(' ', '_').lower()
        log_file = log_dir / f"{traj_name}_{timestamp}.json"

        log_data = {
            'trajectory': self.trajectory_data['name'],
            'timestamp': timestamp,
            'total_time_seconds': time.time() - self.start_time,
            'waypoints': self.positions_log,
            'statistics': {
                'mean_error_m': float(np.mean([log['error'] for log in self.positions_log])),
                'max_error_m': float(np.max([log['error'] for log in self.positions_log])),
                'waypoints_completed': len(self.positions_log),
                'waypoints_total': len(self.trajectory_data['waypoints'])
            }
        }

        with open(log_file, 'w') as f:
            json.dump(log_data, f, indent=2)

        print(f"\n✓ Log saved to: {log_file}")

    def land_and_disarm(self):
        """Safely land the drone"""
        print("\nLanding...")
        self.client.landAsync().join()
        self.client.armDisarm(False)
        self.client.enableApiControl(False)
        print("✓ Drone landed and disarmed")


def main():
    """Main execution"""
    if len(sys.argv) < 2:
        print("Usage: python run_trajectory_auto.py <trajectory_json_file>")
        sys.exit(1)

    trajectory_file = sys.argv[1]

    try:
        runner = TrajectoryRunner()
        runner.load_trajectory(trajectory_file)
        runner.setup_drone()
        runner.run_trajectory(save_log=True)
        runner.land_and_disarm()

    except KeyboardInterrupt:
        print("\n\nTrajectory interrupted by user")
        try:
            runner.land_and_disarm()
        except:
            pass
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()
        try:
            runner.land_and_disarm()
        except:
            pass


if __name__ == "__main__":
    main()
