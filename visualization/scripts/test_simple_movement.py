#!/usr/bin/env python3
"""
Simple test to verify basic AirSim movement works.
"""

import airsim
import time

# Connect
print("Connecting to AirSim...")
client = airsim.MultirotorClient()
client.confirmConnection()
print("✓ Connected")

# Enable API control
print("\nEnabling API control...")
client.enableApiControl(True, "Defender")
client.enableApiControl(True, "Attacker")

# Arm
print("Arming...")
client.armDisarm(True, "Defender")
client.armDisarm(True, "Attacker")

# Takeoff
print("Taking off...")
f1 = client.takeoffAsync(vehicle_name="Defender")
f2 = client.takeoffAsync(vehicle_name="Attacker")
f1.join()
f2.join()

print("Waiting 3 seconds after takeoff...")
time.sleep(3)

# Check positions
def_state = client.getMultirotorState(vehicle_name="Defender")
att_state = client.getMultirotorState(vehicle_name="Attacker")
def_pos = def_state.kinematics_estimated.position
att_pos = att_state.kinematics_estimated.position

print(f"\nAfter takeoff:")
print(f"  Defender: ({def_pos.x_val:.2f}, {def_pos.y_val:.2f}, {def_pos.z_val:.2f})")
print(f"  Attacker: ({att_pos.x_val:.2f}, {att_pos.y_val:.2f}, {att_pos.z_val:.2f})")

# Try simple movement - move Defender 2 meters forward (positive X)
print("\n\nTEST: Moving Defender 2m forward...")
target_x = def_pos.x_val + 2.0
target_y = def_pos.y_val
target_z = def_pos.z_val

print(f"Current: ({def_pos.x_val:.2f}, {def_pos.y_val:.2f}, {def_pos.z_val:.2f})")
print(f"Target:  ({target_x:.2f}, {target_y:.2f}, {target_z:.2f})")

f = client.moveToPositionAsync(target_x, target_y, target_z, 2.0, vehicle_name="Defender")
print("Waiting for movement to complete...")
f.join()

print("Movement command completed")
time.sleep(1)

# Check new position
def_state = client.getMultirotorState(vehicle_name="Defender")
def_pos = def_state.kinematics_estimated.position
print(f"Final:   ({def_pos.x_val:.2f}, {def_pos.y_val:.2f}, {def_pos.z_val:.2f})")

# Land
print("\n\nLanding...")
f1 = client.landAsync(vehicle_name="Defender")
f2 = client.landAsync(vehicle_name="Attacker")
f1.join()
f2.join()

print("✓ Test complete")
