#!/usr/bin/env python3
"""
Quick script to adjust AirSim simulation speed.

Usage:
    python set_sim_speed.py 5.0    # Set ClockSpeed to 5x
    python set_sim_speed.py 1.0    # Reset to normal speed
"""

import json
import sys
from pathlib import Path

def set_clock_speed(settings_path: str, clock_speed: float):
    """Update ClockSpeed in AirSim settings.json"""

    settings_file = Path(settings_path)

    if settings_file.exists():
        with open(settings_file, 'r') as f:
            settings = json.load(f)
    else:
        print(f"⚠️  Settings file not found: {settings_path}")
        print("Creating new settings file...")
        settings = {
            "SettingsVersion": 1.2,
            "SimMode": "Multirotor",
            "Vehicles": {}
        }

    # Update ClockSpeed
    settings["ClockSpeed"] = clock_speed

    # Write back
    settings_file.parent.mkdir(parents=True, exist_ok=True)
    with open(settings_file, 'w') as f:
        json.dump(settings, f, indent=2)

    print(f"✓ Updated ClockSpeed to {clock_speed}x in {settings_path}")
    print(f"\n⚠️  IMPORTANT: Restart Unreal Engine for changes to take effect!")

    if clock_speed > 10:
        print(f"\n⚠️  Warning: ClockSpeed > 10 may cause simulation instability")

def main():
    if len(sys.argv) < 2:
        print("Usage: python set_sim_speed.py <clock_speed>")
        print("\nExamples:")
        print("  python set_sim_speed.py 1.0   # Normal speed")
        print("  python set_sim_speed.py 5.0   # 5x faster")
        print("  python set_sim_speed.py 10.0  # 10x faster")
        sys.exit(1)

    try:
        clock_speed = float(sys.argv[1])
    except ValueError:
        print(f"Error: '{sys.argv[1]}' is not a valid number")
        sys.exit(1)

    if clock_speed <= 0:
        print(f"Error: ClockSpeed must be positive (got {clock_speed})")
        sys.exit(1)

    settings_path = "/tmp/AirSim/settings.json"
    set_clock_speed(settings_path, clock_speed)

if __name__ == "__main__":
    main()
