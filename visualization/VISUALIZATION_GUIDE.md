# AirSim Drone Visualization System - Complete Guide

## Overview

This system visualizes multi-agent drone trajectories in AirSim, allowing you to replay and analyze episodes with proper scaling, markers, and trajectory lines.

**Key Components:**
- `visualize_waypoints.py` - Main entry point, handles conversion and workflow
- `visualize_episode.py` - Core visualization engine
- `config.py` - Configuration and coordinate transformations
- Episode JSON files - Contain waypoint data in meters

## Quick Start

```bash
python visualize_waypoints.py data/episodes/episode_0001_airsim.json --scale 10
```

**Workflow:**
1. Script converts waypoints to episode format
2. Updates `/tmp/AirSim/settings.json` with scaled spawn positions
3. Prompts you to restart Unreal Engine
4. Press ENTER after Unreal is running and Play is pressed
5. Visualization runs with markers, trajectories, and position tracking

## Critical Concepts

### 1. Coordinate Systems

**Episode Data (JSON):**
- **System:** NED (North-East-Down)
- **Units:** Meters (converted from centimeters)
- **Z-axis:** Negative values = altitude (e.g., Z=-2.0 means 2m high)

**AirSim:**
- **System:** NED (North-East-Down)
- **Units:** Meters
- **Z-axis:** Negative values = altitude (matches episode data)

**✅ Both use NED - No coordinate conversion needed!**

### 2. The Scaling System

#### What Gets Scaled?

**For Drone Flight Paths (defender_path, attacker_path):**
```python
# X, Y, Z ALL scaled for drone flight
def_delta_x = (curr_pos[0] - prev_pos[0]) * SCALE_FACTOR
def_delta_y = (curr_pos[1] - prev_pos[1]) * SCALE_FACTOR
def_delta_z = (curr_pos[2] - prev_pos[2]) * SCALE_FACTOR  # Z is scaled!
```

**For Visual Markers & Trajectories:**
```python
# X, Y scaled, Z NOT scaled
marker = airsim.Vector3r(
    pos[0] * SCALE_FACTOR,   # Scale X
    pos[1] * SCALE_FACTOR,   # Scale Y
    pos[2]                   # Don't scale Z!
)
```

#### Why Different Scaling?

| Component | X/Y Scaling | Z Scaling | Reason |
|-----------|-------------|-----------|--------|
| Drone spawn positions | ✅ Yes | ✅ Yes | Must match scaled environment |
| Drone flight paths | ✅ Yes | ✅ Yes | Drones follow scaled movements |
| Visual markers | ✅ Yes | ❌ No | Keep at correct altitude for visibility |
| Trajectory lines | ✅ Yes | ❌ No | Must align with markers |

**Key Insight:** Drones fly in 3D scaled space, but visual markers stay at original altitude for clarity.

### 3. Two Path Systems

The code maintains **two separate path arrays**:

#### A. Flight Paths (for drone movement)
```python
defender_path = [...]  # Built using relative deltas, Z scaled
attacker_path = [...]  # Drones actually follow these
```
- Start from actual drone position after takeoff
- Use relative movements between frames
- Z-axis IS scaled
- **Purpose:** Make drones fly correctly

#### B. Visual Paths (for trajectory lines)
```python
defender_path_visual = [...]  # Built from absolute positions, Z not scaled
attacker_path_visual = [...]  # Used for drawing trajectory lines
```
- Built from absolute JSON positions
- X/Y scaled, Z not scaled
- **Purpose:** Show trajectory lines that align with markers

**This separation is critical!** Mixing them causes misalignment.

## Common Pitfalls & Solutions

### ❌ Pitfall 1: Markers/Trajectories Below Floor

**Symptom:** Everything appears underground

**Causes:**
1. Using positive Z values (positive = below ground in NED)
2. Scaling Z for visual elements
3. Wrong coordinate system conversion

**Solution:**
```python
# ✅ Correct - Don't scale Z for visuals
marker_pos = airsim.Vector3r(
    pos[0] * SCALE_FACTOR,
    pos[1] * SCALE_FACTOR,
    pos[2]  # NO scaling!
)

# ❌ Wrong - This puts markers too deep
marker_pos = airsim.Vector3r(
    pos[0] * SCALE_FACTOR,
    pos[1] * SCALE_FACTOR,
    pos[2] * SCALE_FACTOR  # Too deep!
)
```

### ❌ Pitfall 2: Trajectory Lines Don't Match Markers

**Symptom:** Green/red lines don't pass through starting markers

**Cause:** Using flight paths (Z-scaled) instead of visual paths (Z-unscaled)

**Solution:**
```python
# ✅ Correct - Use visual paths
client.simPlotLineStrip(points=defender_path_visual, ...)

# ❌ Wrong - Uses Z-scaled flight paths
client.simPlotLineStrip(points=defender_path, ...)
```

### ❌ Pitfall 3: Drones Don't Follow Trajectories

**Symptom:** Drones fly to different locations than shown in trajectory

**Cause:** Using visual paths (Z-unscaled) for drone movement

**Solution:**
```python
# ✅ Correct - Use flight paths with scaled Z
client.moveOnPathAsync(path=defender_path, ...)

# ❌ Wrong - Drones won't reach correct altitude
client.moveOnPathAsync(path=defender_path_visual, ...)
```

### ❌ Pitfall 4: Settings.json Not Updated

**Symptom:** Drones spawn at (0,0,0) instead of correct positions

**Cause:** Not restarting Unreal after settings.json update

**Solution:**
1. Let script update `/tmp/AirSim/settings.json`
2. **Close Unreal completely**
3. Restart Unreal
4. Press Play
5. Return to script and press ENTER

**Critical:** AirSim only reads settings.json on startup!

### ❌ Pitfall 5: Attacker Freezes Mid-Air After Flight

**Symptom:** Defender lands, but Attacker hovers

**Cause:** Async movement not cancelled before landing

**Solution:**
```python
# Cancel any remaining tasks before landing
client.cancelLastTask("Defender")
client.cancelLastTask("Attacker")
time.sleep(0.5)

# Then land
client.landAsync(vehicle_name="Defender")
client.landAsync(vehicle_name="Attacker")
```

## Settings.json Structure

**Location:** `/tmp/AirSim/settings.json`

**What Gets Written:**
```json
{
  "Vehicles": {
    "Defender": {
      "VehicleType": "SimpleFlight",
      "X": 1.72,    // pos[0] * SCALE_FACTOR
      "Y": 8.34,    // pos[1] * SCALE_FACTOR
      "Z": -20.0,   // pos[2] * SCALE_FACTOR (negative = up!)
      "Yaw": 0.0
    },
    "Attacker": {
      "VehicleType": "SimpleFlight",
      "X": -13.27,  // pos[0] * SCALE_FACTOR
      "Y": -7.73,   // pos[1] * SCALE_FACTOR
      "Z": -21.28,  // pos[2] * SCALE_FACTOR
      "Yaw": 0.0
    }
  }
}
```

**Verification:**
- Negative Z values = correct (altitude)
- Positive Z values = wrong (underground)

## Visual Elements

### Markers
- **BASE:** Cyan sphere (size 25) at origin
- **DEFENDER:** Green sphere (size 25) at starting position
- **ATTACKER:** Red sphere (size 25) at starting position
- All use **unscaled Z** for correct altitude

### Trajectory Lines
- **DEFENDER:** Green line (thickness 5)
- **ATTACKER:** Red line (thickness 5)
- Both use **visual paths** (unscaled Z)
- Persistent throughout flight

### Text Labels
- "BASE", "DEFENDER", "ATTACKER"
- Scale 5.0, positioned 2m above markers
- May not be supported in all AirSim versions

## Output Format

**Console Display:**
```
[  0] DEF: (  1.72,   8.34, -20.00) | WP:(  1.72,   8.34,  -2.00) || ATT: (-13.27,  -7.73, -21.28) | WP:(-13.27,  -7.73,  -2.13)
[  1] DEF: (  1.70,   8.32, -20.05) | WP:(  1.72,   8.34,  -2.00) || ATT: (-13.25,  -7.71, -21.30) | WP:(-13.27,  -7.73,  -2.13)
```

**Format:**
- `[N]` - Frame number
- `DEF: (x,y,z)` - Actual defender position (from getMultirotorState)
- `WP:(x,y,z)` - Waypoint position (from JSON, scaled)
- `ATT: (x,y,z)` - Actual attacker position
- `WP:(x,y,z)` - Waypoint position

**What to Check:**
- Actual positions should gradually approach waypoint positions
- Z values should be negative (altitude)
- If actual ≈ waypoint, drones are following correctly

## Planning Future Experiments

### Scaling Strategy

**Choose your scale factor based on environment size:**

| Environment | Scale Factor | Use Case |
|-------------|--------------|----------|
| Small (Blocks) | 1x - 2x | Testing, debugging |
| Medium (City) | 5x - 10x | Normal experiments |
| Large (Mountain) | 20x+ | Long-range scenarios |

**Test Workflow:**
1. Start with `--scale 1` to verify trajectories are correct
2. Increase scale incrementally (1→2→5→10)
3. Check that markers/trajectories align at each scale
4. Verify drones complete the trajectory

### Adding New Agents

**To add a third drone (e.g., "Observer"):**

1. **Update settings.json** in `update_settings_with_frame_0()`:
```python
if "observer" in frame_0:
    obs_pos = transform_position(frame_0["observer"]["pos"], config)
    settings["Vehicles"]["Observer"] = {
        "VehicleType": "SimpleFlight",
        "X": obs_pos[0],
        "Y": obs_pos[1],
        "Z": obs_pos[2],
        "Yaw": 0.0
    }
```

2. **Build flight path**:
```python
observer_path = [airsim.Vector3r(obs_actual.x_val, obs_actual.y_val, obs_actual.z_val)]
# ... add delta calculations ...
```

3. **Build visual path**:
```python
for frame in episode_frames:
    obs_pos = frame['observer']['pos']
    observer_path_visual.append(airsim.Vector3r(
        obs_pos[0] * config.SCALE_FACTOR,
        obs_pos[1] * config.SCALE_FACTOR,
        obs_pos[2]  # Don't scale Z!
    ))
```

4. **Add marker & trajectory**:
```python
# Marker (blue)
client.simPlotPoints(points=[obs_start], color_rgba=[0.0, 0.0, 1.0, 1.0], ...)

# Trajectory line
client.simPlotLineStrip(points=observer_path_visual, color_rgba=[0.0, 0.0, 1.0, 1.0], ...)
```

### Debugging Checklist

**When things don't look right:**

- [ ] Check console output for `[text shown]` or `[text not supported]`
- [ ] Verify Z values are negative in console output
- [ ] Confirm settings.json has negative Z values
- [ ] Check that markers appear at correct altitude (not underground)
- [ ] Verify trajectory lines pass through starting markers
- [ ] Ensure Unreal was restarted after settings.json update
- [ ] Compare actual drone position vs waypoint position in console
- [ ] Check SCALE_FACTOR matches your expectation

**Common Z-value errors:**
```
Z = -20.0  ✅ Correct (20m altitude)
Z = 20.0   ❌ Wrong (20m underground)
Z = 0.0    ⚠️  Ground level (may clip through floor)
```

### Performance Considerations

**Frame rate:**
- Monitor loop runs at 20Hz (50ms sleep)
- 432 waypoints ≈ 22 seconds at 20Hz
- Adjust `time.sleep(0.05)` to change update rate

**Velocity scaling:**
```python
base_velocity = 0.25  # m/s
flight_velocity = base_velocity * SCALE_FACTOR
```
- Larger scales = faster flight speed
- Keeps visual speed consistent across scales

**Trajectory rendering:**
- Lines are persistent (drawn once)
- Markers have limited duration (1 second for real-time, 9999 for static)
- No performance impact from trajectory complexity

## Key Files Reference

```
visualization/
├── scripts/
│   ├── visualize_waypoints.py    # Main entry point
│   ├── visualize_episode.py      # Core engine (THIS IS KEY!)
│   ├── config.py                 # Transform functions
│   └── convert_to_episode.py     # Waypoint→episode conversion
├── data/
│   ├── episodes/                 # Original episode files
│   │   ├── episode_0001_airsim.json
│   │   └── episode_0001_converted.json
│   └── airsim_waypoints/         # Alternative format
└── VISUALIZATION_GUIDE.md        # This file
```

## Summary

**Remember:**
1. ✅ **Markers & trajectories:** Scale X/Y, NOT Z
2. ✅ **Drone flight paths:** Scale X/Y/Z (all dimensions)
3. ✅ **Always restart Unreal** after settings.json changes
4. ✅ **Use visual paths** for drawing, **flight paths** for movement
5. ✅ **Negative Z** = altitude in NED coordinate system
6. ✅ **Cancel tasks** before landing to avoid freezing

**Golden Rule:** When in doubt, check if Z is being scaled - that's usually the issue!

---

*Last Updated: Based on working system with proper marker/trajectory alignment*
