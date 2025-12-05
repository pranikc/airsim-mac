#!/usr/bin/env python3
"""Debug coordinate transformations"""
import json
import sys

if len(sys.argv) < 2:
    print("Usage: python debug_coordinates.py <waypoints_json>")
    sys.exit(1)

with open(sys.argv[1], 'r') as f:
    data = json.load(f)

waypoint = data['waypoints'][0]
scale = 10.0

print("\n" + "="*60)
print("COORDINATE TRANSFORMATION DEBUG")
print("="*60)

# Raw data
def_raw = waypoint['defender']['position']
att_raw = waypoint['attacker']['position']
base_raw = waypoint['base']['position']

print(f"\nRAW DATA (centimeters):")
print(f"  Defender: x={def_raw['x']}, y={def_raw['y']}, z={def_raw['z']}")
print(f"  Attacker: x={att_raw['x']}, y={att_raw['y']}, z={att_raw['z']}")
print(f"  Base: x={base_raw['x']}, y={base_raw['y']}, z={base_raw['z']}")

# Convert to meters
def_m = [def_raw['x']/100, def_raw['y']/100, def_raw['z']/100]
att_m = [att_raw['x']/100, att_raw['y']/100, att_raw['z']/100]
base_m = [base_raw['x']/100, base_raw['y']/100, base_raw['z']/100]

print(f"\nCONVERTED TO METERS:")
print(f"  Defender: x={def_m[0]:.3f}, y={def_m[1]:.3f}, z={def_m[2]:.3f}")
print(f"  Attacker: x={att_m[0]:.3f}, y={att_m[1]:.3f}, z={att_m[2]:.3f}")
print(f"  Base: x={base_m[0]:.3f}, y={base_m[1]:.3f}, z={base_m[2]:.3f}")

print(f"\nCURRENT TRANSFORMATION (X/Y swap, scale={scale}):")
print(f"  data Y → AirSim X (flipped), data X → AirSim Y")

def_airsim = [-def_m[1]*scale, def_m[0]*scale, def_m[2]]
att_airsim = [-att_m[1]*scale, att_m[0]*scale, att_m[2]]

print(f"  Defender: X={def_airsim[0]:.2f}, Y={def_airsim[1]:.2f}, Z={def_airsim[2]:.2f}")
print(f"  Attacker: X={att_airsim[0]:.2f}, Y={att_airsim[1]:.2f}, Z={att_airsim[2]:.2f}")

print(f"\nALTERNATIVE: No swap, just scale (X→X, Y→Y):")
def_alt = [def_m[0]*scale, def_m[1]*scale, def_m[2]]
att_alt = [att_m[0]*scale, att_m[1]*scale, att_m[2]]
print(f"  Defender: X={def_alt[0]:.2f}, Y={def_alt[1]:.2f}, Z={def_alt[2]:.2f}")
print(f"  Attacker: X={att_alt[0]:.2f}, Y={att_alt[1]:.2f}, Z={att_alt[2]:.2f}")

print(f"\nALTERNATIVE: Flip Y only (X→X, -Y→Y):")
def_alt2 = [def_m[0]*scale, -def_m[1]*scale, def_m[2]]
att_alt2 = [att_m[0]*scale, -att_m[1]*scale, att_m[2]]
print(f"  Defender: X={def_alt2[0]:.2f}, Y={def_alt2[1]:.2f}, Z={def_alt2[2]:.2f}")
print(f"  Attacker: X={att_alt2[0]:.2f}, Y={att_alt2[1]:.2f}, Z={att_alt2[2]:.2f}")

print("="*60 + "\n")
