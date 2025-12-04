#!/usr/bin/env python3
"""
Check what objects/assets can be spawned in AirSim.

This script tests spawning various built-in objects to see what's available.
"""

import airsim
import time

# Connect
print("Connecting to AirSim...")
client = airsim.MultirotorClient()
client.confirmConnection()
print("✓ Connected\n")

# List of common asset names to try
test_assets = [
    # Basic shapes (should always work)
    "Cube",
    "Sphere",
    "Cylinder",
    "Cone",

    # Potentially available vehicles
    "SUV",
    "Sedan",
    "SportsCar",
    "Hatchback",
    "Truck",
    "Truck_01",
    "SM_Truck",
    "saint_chamond",
    "saint_chamond_StaticMesh",  # Static mesh version
    "saint_chamond1",             # Possible reimport name

    # AirSim specific
    "Car",
    "PhysXCar",
]

print("Testing available assets...\n")
print("="*60)

available_assets = []
unavailable_assets = []

for asset_name in test_assets:
    object_name = f"Test_{asset_name}"
    pose = airsim.Pose(airsim.Vector3r(0, 0, -1), airsim.to_quaternion(0, 0, 0))

    try:
        # Try spawning with physics disabled for visual-only object
        success = client.simSpawnObject(object_name, asset_name, pose, 1.0, False)

        if success:
            print(f"✓ {asset_name:20s} - AVAILABLE")
            available_assets.append(asset_name)
            time.sleep(0.1)
            # Clean up
            client.simDestroyObject(object_name)
        else:
            print(f"✗ {asset_name:20s} - Not available")
            unavailable_assets.append(asset_name)
    except Exception as e:
        print(f"✗ {asset_name:20s} - Error: {str(e)[:40]}")
        unavailable_assets.append(asset_name)

    time.sleep(0.1)

print("="*60)
print(f"\nSummary:")
print(f"  Available: {len(available_assets)} assets")
print(f"  Unavailable: {len(unavailable_assets)} assets")

if available_assets:
    print(f"\n✓ You can use these assets:")
    for asset in available_assets:
        print(f"    - {asset}")
else:
    print(f"\n⚠️  No special assets found, only basic shapes available")
    print(f"   You'll need to use basic shapes or add custom meshes")

print("\n" + "="*60)
print("Recommendation for car visualization:")
if "SUV" in available_assets or "Sedan" in available_assets or "Car" in available_assets:
    print("  Use: SUV, Sedan, or Car")
elif "Cube" in available_assets:
    print("  Use: Cube (scaled to look car-like)")
    print("  Or: Create custom car mesh")
else:
    print("  Add custom car mesh to Unreal environment")
print("="*60)
