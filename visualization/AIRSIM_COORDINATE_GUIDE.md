# AirSim Coordinate System Guide for Training

A complete guide for designing training environments that map seamlessly to AirSim visualization.

## 1. Coordinate System: NED (North-East-Down)

AirSim uses the **NED coordinate system**:

```
X-axis = North (forward)
Y-axis = East (right)
Z-axis = Down (negative is UP!)
```

**Critical:** In AirSim:
- **Negative Z = altitude ABOVE ground** (e.g., Z = -2.0 means 2 meters UP)
- **Positive Z = below ground** (don't use this for drones!)
- **Z = 0 = ground level**

### Training Environment Setup:

Your training code should use:
```python
# Training coordinate system
x: float  # forward/backward position
y: float  # left/right position
z: float  # altitude ABOVE ground (positive up)
```

### Conversion to AirSim:

```python
# In your AirSim visualization code
airsim_x = training_x
airsim_y = training_y
airsim_z = -training_z  # NEGATE to convert altitude to NED Down
```

---

## 2. Units: ALWAYS USE METERS

**Everything in AirSim uses METERS:**
- Positions: meters
- Velocities: meters/second
- Settings.json spawn positions: meters
- moveToPositionAsync() API: meters

**Your Training Should Output:**
```json
{
  "position": [x, y, z],  // in METERS
  "velocity": [vx, vy, vz],  // in METERS/SECOND
  "orientation": [roll, pitch, yaw]  // in RADIANS (convert to degrees for AirSim)
}
```

**DO NOT use:**
- ❌ Centimeters
- ❌ Feet
- ❌ Arbitrary normalized units [-1, 1]

---

## 3. Recommended Environment Dimensions

### Small Arena (Easy to Visualize):
```
Floor size: 10m × 10m
Altitude range: 0-5m
Agent operating area: 8m × 8m (leave 1m border)
```

**Training bounds:**
```python
X: -5.0 to +5.0 meters (centered on origin)
Y: -5.0 to +5.0 meters
Z: 0.0 to 5.0 meters (altitude)
```

### Medium Arena:
```
Floor size: 20m × 20m
Altitude range: 0-10m
Agent operating area: 16m × 16m
```

### Large Arena:
```
Floor size: 50m × 50m
Altitude range: 0-20m
Agent operating area: 40m × 40m
```

**Rule of thumb:** Keep your training environment ≤50m × 50m for easy visualization.

---

## 4. Ground Reference Point

**Critical:** Always set **Z = 0 as your ground level** in training.

```python
# Example positions
base = [0.0, 0.0, 0.0]        # Ground level, center
drone = [1.5, -2.3, 2.0]      # 2m altitude, offset from center
target = [5.0, 5.0, 0.0]      # Ground level, corner
```

**In Unreal:**
- Your floor plane should be at Z = 0
- Set floor actor's Location Z = 0 in Details panel

---

## 5. Waypoint Data Format

### Recommended JSON Structure:

```json
{
  "metadata": {
    "episode": 1,
    "duration_seconds": 45.2,
    "outcome": "success"
  },
  "frames": [
    {
      "t": 0.0,
      "agent_name": {
        "pos": [x, y, z],           // meters, z = altitude
        "vel": [vx, vy, vz],        // meters/second
        "rpy": [roll, pitch, yaw]   // radians
      },
      "target": {
        "pos": [x, y, z]
      }
    }
  ]
}
```

### Units Checklist:
- ✅ Positions: meters
- ✅ Velocities: meters/second
- ✅ Time: seconds
- ✅ Angles: radians (will convert to degrees for AirSim)
- ✅ Z = altitude above ground (positive up)

---

## 6. AirSim Settings.json Configuration

### Spawn Positions (in meters):

```json
{
  "Vehicles": {
    "Defender": {
      "VehicleType": "SimpleFlight",
      "X": 0.0,      // meters
      "Y": 0.0,      // meters
      "Z": -2.0,     // 2m altitude (negative = up!)
      "Yaw": 0.0     // degrees
    },
    "Attacker": {
      "VehicleType": "SimpleFlight",
      "X": 5.0,
      "Y": 5.0,
      "Z": -2.0,
      "Yaw": 0.0
    }
  }
}
```

**Rules:**
- X, Y, Z in **meters**
- Z is **negative** for altitude (NED system)
- Spawn drones at Z = -2.0 to -5.0 (2-5m altitude) for good visibility

---

## 7. Visualization Scale Factor

If your training already uses meters with Z=0 ground:

```python
# In config.py
SCALE_FACTOR = 1.0  # No scaling needed!
Z_OFFSET = 0.0      # No offset needed!
```

**Only use SCALE_FACTOR > 1 if:**
- Your training uses very small dimensions (< 5m × 5m)
- You want to magnify the visualization

**Only use Z_OFFSET if:**
- You want to artificially lower/raise everything for viewing

---

## 8. Unreal Environment Setup

### Floor Setup:
```
Actor: Plane (or custom mesh)
Location: (0, 0, 0)
Rotation: (0, 0, 0)
Scale: (10, 10, 1)  // 10m × 10m floor
```

**Scale calculation:**
- Default plane is 100 units × 100 units (1m × 1m)
- Scale 10 = 1000 units × 1000 units = 10m × 10m
- For 20m × 20m: Scale (20, 20, 1)

### Lighting:
- Add Directional Light (sun)
- Add Sky Sphere for better visuals

### Camera:
- Start position: (0, 0, -500) = 5m above origin, looking down
- For top-down view: Point camera straight down

---

## 9. Common Pitfalls to Avoid

### ❌ DON'T:
```python
# Using centimeters
position = [245.0, -883.0, 200.0]  # Too large!

# Using normalized coordinates
position = [0.245, -0.883, 0.2]  # If your arena is 100m, this is wrong

# Positive Z for altitude
position = [1.0, 2.0, 2.0]  # Then negating in AirSim → Z = -2.0 ✓
```

### ✅ DO:
```python
# Use meters directly
position_meters = [1.5, -2.3, 2.0]  # 1.5m forward, 2.3m left, 2m altitude

# Set Z = 0 as ground
ground = 0.0
altitude = 2.0  # 2 meters above ground

# For AirSim
airsim_z = -altitude  # = -2.0 (negative = up in NED)
```

---

## 10. Quick Validation Checklist

Before training, verify:

- [ ] Environment dimensions ≤ 50m × 50m
- [ ] All positions in **meters**
- [ ] Z = 0 is **ground level** in training
- [ ] Altitude values are **positive** (2.0 = 2m up)
- [ ] Velocities in **meters/second**
- [ ] Angles in **radians** (or specify degrees)
- [ ] Reasonable altitude range (0.5m - 10m)
- [ ] Agents stay within bounds

After generating waypoints:

- [ ] Check JSON structure matches format above
- [ ] Verify units are meters
- [ ] Test with visualization script
- [ ] SCALE_FACTOR = 1.0 works without adjustment
- [ ] Drones visible and at correct positions

---

## 11. Example: Perfect Training Setup

```python
class TrainingEnvironment:
    """Training environment designed for direct AirSim visualization"""

    def __init__(self):
        # Environment bounds (meters)
        self.x_min, self.x_max = -5.0, 5.0   # 10m width
        self.y_min, self.y_max = -5.0, 5.0   # 10m depth
        self.z_min, self.z_max = 0.5, 5.0    # 0.5-5m altitude

        # Ground reference
        self.ground_level = 0.0

        # Positions (meters)
        self.base_pos = [0.0, 0.0, 0.0]      # Ground center
        self.defender_spawn = [0.0, -2.0, 2.0]  # 2m altitude
        self.attacker_spawn = [-3.0, 2.0, 2.5]  # 2.5m altitude

    def get_state(self, agent):
        """Return state in meters, Z = altitude"""
        return {
            'pos': [agent.x, agent.y, agent.z],  # meters
            'vel': [agent.vx, agent.vy, agent.vz],  # m/s
            'rpy': [agent.roll, agent.pitch, agent.yaw]  # radians
        }

    def save_trajectory(self, episode_data, filename):
        """Save in AirSim-ready format"""
        trajectory = {
            'metadata': {
                'episode': episode_data['ep_num'],
                'duration': episode_data['duration'],
                'outcome': episode_data['outcome']
            },
            'frames': []
        }

        for frame in episode_data['frames']:
            trajectory['frames'].append({
                't': frame['time'],  # seconds
                'defender': {
                    'pos': frame['defender']['pos'],  # [x, y, z] meters
                    'vel': frame['defender']['vel'],  # [vx, vy, vz] m/s
                    'rpy': frame['defender']['rpy']   # [r, p, y] radians
                },
                'attacker': {
                    'pos': frame['attacker']['pos'],
                    'vel': frame['attacker']['vel'],
                    'rpy': frame['attacker']['rpy']
                },
                'base': {
                    'pos': self.base_pos  # [0, 0, 0]
                }
            })

        with open(filename, 'w') as f:
            json.dump(trajectory, f, indent=2)
```

### Visualization (No Changes Needed!):
```python
# config.py
SCALE_FACTOR = 1.0  # Perfect 1:1 mapping
Z_OFFSET = 0.0      # No adjustment needed
INVERT_Z = True     # Altitude → NED Down

# Just works! ✓
```

---

## 12. Summary Table

| Parameter | Training | AirSim | Conversion |
|-----------|----------|--------|------------|
| Units | Meters | Meters | None (1:1) |
| X-axis | Forward | North | Same |
| Y-axis | Right | East | Same |
| Z-axis | Up (altitude) | Down | **Negate** |
| Ground | Z = 0 | Z = 0 | Same |
| 2m altitude | Z = 2.0 | Z = -2.0 | Multiply by -1 |
| Velocities | m/s | m/s | Same |
| Angles | Radians | Degrees | × 180/π |
| Spawn positions | [0, 0, 2.0] | [0, 0, -2.0] | Negate Z |

---

## 13. Testing Your Setup

### Quick Test:
```bash
# 1. Generate one test trajectory
python your_training.py --test --save test_trajectory.json

# 2. Verify format
cat test_trajectory.json | head -50

# 3. Visualize in AirSim
python visualize_episode.py test_trajectory.json

# 4. Check positions
# - Drones should be at 2-5m altitude (visible)
# - Should stay within your floor bounds
# - Movements should look correct (not inverted/scaled)
```

### Expected Results:
- ✓ Drones spawn at reasonable altitude
- ✓ Movements match training behavior
- ✓ Stay within environment bounds
- ✓ No scaling artifacts (teleporting, clipping, etc.)

---

## Key Takeaways

1. **Use meters everywhere** - no conversions needed
2. **Z = 0 is ground** in both training and AirSim
3. **Negate Z when converting** to AirSim (altitude → NED Down)
4. **Keep environment ≤ 50m × 50m** for easy visualization
5. **Design training to match AirSim** from the start
6. **SCALE_FACTOR = 1.0** should work without adjustment

**Golden Rule:** If you need SCALE_FACTOR ≠ 1.0, your training units don't match AirSim units. Fix the training environment instead!

---

Created: December 2025
For: AirSim Multi-Agent Visualization Pipeline
