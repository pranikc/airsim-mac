# Car Base Visualization Setup

This guide explains how to use `visualize_episode_with_car.py` to visualize episodes with a car model as the base instead of a simple sphere marker.

---

## Overview

**Original:** `visualize_episode.py` - Uses sphere marker for base (stationary visual only)

**New:** `visualize_episode_with_car.py` - Uses actual car model that can move along trajectory

---

## Quick Start

### 1. Update AirSim Settings

Copy `settings_with_car.json` to your AirSim settings location:

**Mac/Linux:**
```bash
cp visualization/settings_with_car.json ~/Documents/AirSim/settings.json
```

**Windows:**
```bash
copy visualization\settings_with_car.json %USERPROFILE%\Documents\AirSim\settings.json
```

### 2. Restart Unreal Engine

After updating settings.json, restart Unreal Engine with your environment.

### 3. Run Visualization

```bash
cd visualization/scripts
python visualize_episode_with_car.py ../data/episodes/episode_0001.json
```

---

## Settings.json Configuration

The key difference is adding a third vehicle of type **PhysXCar**:

```json
{
  "SettingsVersion": 1.2,
  "SimMode": "Multirotor",
  "Vehicles": {
    "Defender": {
      "VehicleType": "SimpleFlight",
      "X": 0, "Y": 0, "Z": 0
    },
    "Attacker": {
      "VehicleType": "SimpleFlight",
      "X": 0, "Y": 0, "Z": 0
    },
    "Base": {
      "VehicleType": "PhysXCar",  ← CAR VEHICLE
      "X": 0, "Y": 0, "Z": 0
    }
  }
}
```

---

## How It Works

### Base Trajectory Detection

The script automatically detects if the base moves:

```python
# Checks all frames to see if base position changes
base_is_moving = check_base_trajectory(frames, config)
```

**If STATIONARY (current case):**
- Car positioned at origin once
- Stays in place throughout visualization

**If MOVING (future JSON files):**
- Car position updated every frame
- Follows base trajectory smoothly
- Ground level (Z=0) maintained automatically

### Car Positioning

The car is always placed at ground level (Z=0), regardless of trajectory Z value:

```python
car_pose = airsim.Pose(
    airsim.Vector3r(x, y, 0.0),  # Force Z=0 for ground
    airsim.to_quaternion(0, 0, 0)
)
client.simSetVehiclePose(car_pose, True, vehicle_name="Base")
```

---

## Usage Examples

### Basic Usage

```bash
python visualize_episode_with_car.py ../data/episodes/episode_0001.json
```

### With Custom Scale Factor

```bash
python visualize_episode_with_car.py ../data/episodes/episode_0001.json --scale 5.0
```

### Specific Frame Range

```bash
python visualize_episode_with_car.py ../data/episodes/episode_0001.json --start-frame 100 --end-frame 500
```

### Faster Playback

```bash
python visualize_episode_with_car.py ../data/episodes/episode_0001.json --speed 2.0
```

---

## Differences from Original Script

| Feature | visualize_episode.py | visualize_episode_with_car.py |
|---------|---------------------|-------------------------------|
| Base visualization | Sphere marker (cyan) | Car model (PhysXCar) |
| Base movement | Not supported | Supported (future-proof) |
| Settings.json | 2 vehicles (drones) | 3 vehicles (2 drones + car) |
| Base detection | N/A | Auto-detects moving trajectory |
| Ground positioning | N/A | Auto Z=0 for car |

---

## Troubleshooting

### Error: "Could not find vehicle 'Base'"

**Problem:** Settings.json doesn't have Base vehicle defined

**Solution:**
1. Check settings.json location (see Quick Start)
2. Verify "Base" vehicle exists with VehicleType "PhysXCar"
3. Restart Unreal Engine after modifying settings.json

### Car appears underground or floating

**Problem:** Car Z position incorrect

**Solution:** The script automatically sets Z=0. If still wrong, check:
1. Unreal environment ground plane is at Z=0
2. SCALE_FACTOR isn't causing position issues
3. Try SCALE_FACTOR = 1.0 first

### Car doesn't move even with moving trajectory

**Problem:** Base trajectory detection failed or trajectory too small

**Solution:**
1. Check console output for "Base trajectory: MOVING" or "STATIONARY"
2. Detection threshold is 0.1m - movements smaller than this are ignored
3. Verify base trajectory in JSON actually changes across frames

### Drones work but car doesn't appear

**Problem:** Car vehicle type incompatible or not supported in environment

**Solution:**
1. Verify VehicleType is "PhysXCar" (not "SimpleFlight")
2. Some Unreal environments may not support cars
3. Try using a different environment (Blocks, Neighborhood)

---

## Future Enhancements

When you have JSON files with moving base trajectories:

✅ **Already supported:**
- Automatic detection of moving base
- Frame-by-frame position updates
- Ground-level positioning

🔧 **Potential additions:**
- Car orientation based on movement direction
- Velocity-based car controls instead of pose setting
- Trail/trajectory line for car path
- Multiple base objects (convoy)

---

## When to Use Each Script

**Use `visualize_episode.py`:**
- Simple visualization
- Don't need car model
- Settings.json with only 2 vehicles
- Faster setup

**Use `visualize_episode_with_car.py`:**
- Want realistic car model for base
- Base has moving trajectory
- Need to visualize ground vehicle
- Better visual presentation

---

## Example Output

When running with car base:

```
POSITIONING BASE CAR
══════════════════════════════════════════════════════
Base starting position: (0.000, 0.000, 0.000)
✓ Base car positioned at origin
══════════════════════════════════════════════════════

Base trajectory: STATIONARY

SCALING CONFIGURATION
══════════════════════════════════════════════════════
Scale Factor: 5.0x
Base Velocity: 0.125 m/s
Scaled Velocity: 0.625 m/s
Defender Distance: 96.84m
Expected Flight Time: ~155.0 seconds
══════════════════════════════════════════════════════
```

---

## Additional Resources

- **AirSim Car Documentation:** https://microsoft.github.io/AirSim/apis/#car-apis
- **AirSim Vehicle Settings:** https://microsoft.github.io/AirSim/settings/
- **Main Visualization Guide:** See VISUALIZATION_GUIDE.md

---

**Created:** 2025-12-03
**For Use With:** AirSim Multi-Agent Visualization System v1.1+
