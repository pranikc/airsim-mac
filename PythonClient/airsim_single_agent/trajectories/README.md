# AirSim Trajectory Files

This directory contains predefined trajectories for testing and evaluation.

## JSON Format

```json
{
  "name": "Trajectory Name",
  "description": "What this trajectory does",
  "coordinate_system": "NED",
  "units": "centimeters",
  "velocity": 3.0,
  "waypoints": [
    {
      "id": 0,
      "position": {"x": 0, "y": 0, "z": -200},
      "yaw": 0,
      "wait_time": 1.0,
      "description": "Waypoint description"
    }
  ]
}
```

## Coordinate System

**NED (North-East-Down):**
- **X**: Forward (North) - positive = forward
- **Y**: Right (East) - positive = right
- **Z**: Down - negative = up, positive = down

**Units:** Centimeters (1 meter = 100 cm)

**Example Positions:**
- Ground level at origin: `(0, 0, 0)`
- 2 meters altitude: `(0, 0, -200)`
- 10 meters forward, 2m altitude: `(1000, 0, -200)`
- 5 meters right, 2m altitude: `(0, 500, -200)`

## Fields Explained

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `name` | string | Trajectory name | "Straight Line" |
| `description` | string | What it does | "Forward movement" |
| `velocity` | float | Speed in m/s | 3.0 |
| `waypoints` | array | List of positions | See below |

### Waypoint Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | int | Yes | Sequential waypoint number |
| `position.x` | float | Yes | X coordinate (cm) |
| `position.y` | float | Yes | Y coordinate (cm) |
| `position.z` | float | Yes | Z coordinate (cm, negative=up) |
| `yaw` | float | No | Heading in degrees (0=North) |
| `wait_time` | float | No | Seconds to wait at waypoint |
| `description` | string | No | Waypoint description |

## Available Trajectories

### 1. straight_line.json
Simple forward movement along X axis
- Distance: 50 meters
- Waypoints: 6
- Good for: Basic testing

### 2. square_path.json
Navigate in a square pattern
- Side length: 20 meters
- Waypoints: 5
- Good for: Testing turns

### 3. zigzag_pattern.json
Zigzag for obstacle avoidance practice
- Length: 30 meters
- Amplitude: 5 meters
- Good for: Obstacle avoidance

### 4. vertical_scan.json
Moves up and down while moving forward
- Altitude range: 1m to 3m
- Distance: 30 meters
- Good for: Vertical navigation

### 5. circular_orbit.json
Circle around a central point
- Radius: 10 meters
- Waypoints: 9
- Good for: Circular paths

## Usage

### 1. Run a Trajectory

```bash
# Make sure Unreal Engine is running with AirSim
cd /Users/pranikchainani/AirSim/PythonClient/airsim_single_agent

# Run a predefined trajectory
python run_trajectory.py trajectories/straight_line.json

# Or any other trajectory
python run_trajectory.py trajectories/square_path.json
```

### 2. Create Your Own Trajectory

1. Copy `template.json` to a new file:
   ```bash
   cp trajectories/template.json trajectories/my_trajectory.json
   ```

2. Edit the JSON file with your waypoints

3. Run it:
   ```bash
   python run_trajectory.py trajectories/my_trajectory.json
   ```

## Converting Real-World Coordinates

If you have positions in meters, multiply by 100:

```python
# Meters to centimeters
x_cm = x_meters * 100
y_cm = y_meters * 100
z_cm = z_meters * 100  # Remember: negative = up!
```

**Example:**
- Want drone at 5m forward, 3m right, 2m altitude
- JSON: `{"x": 500, "y": 300, "z": -200}`

## Getting Positions from Unreal

### Method 1: Place Objects in Unreal

1. In Unreal Editor, place an object (sphere, cube, etc.)
2. Name it something like "waypoint_1"
3. Note its position from the Details panel
4. Convert to NED coordinates (Y and Z might be swapped)

### Method 2: Use AirSim API

```python
import airsim

client = airsim.MultirotorClient()
client.confirmConnection()

# Get position of any object
pose = client.simGetObjectPose('object_name')
print(f"X: {pose.position.x_val}")
print(f"Y: {pose.position.y_val}")
print(f"Z: {pose.position.z_val}")

# Or get current drone position
state = client.getMultirotorState()
pos = state.kinematics_estimated.position
print(f"Drone at: {pos.x_val}, {pos.y_val}, {pos.z_val}")
```

## Tips

1. **Start Simple**: Test with straight_line.json first
2. **Altitude Safety**: Keep z < 0 (negative means up!)
3. **Map Bounds**: Make sure positions are within your map
4. **Velocity**: Start with 2-3 m/s, increase as needed
5. **Wait Times**: Add wait_time for better observation
6. **Collision Check**: Script stops if collision detected

## Logs

Trajectory execution logs are saved in `trajectory_logs/`:
- Timestamp
- Target vs actual positions
- Position errors
- Statistics (mean/max error)

## Troubleshooting

### "Connection refused"
- Make sure Unreal Engine is running
- Press Play in Unreal
- Check AirSim settings.json exists

### Drone doesn't move
- Check positions are in centimeters (not meters!)
- Verify z is negative (negative = altitude)
- Check velocity > 0

### Drone crashes
- Reduce velocity
- Increase wait times
- Check for obstacles in path
- Verify all positions are valid

## Example: Custom Search Pattern

```json
{
  "name": "Grid Search",
  "description": "Cover area in grid pattern",
  "velocity": 2.0,
  "waypoints": [
    {"id": 0, "position": {"x": 0, "y": 0, "z": -200}},
    {"id": 1, "position": {"x": 1000, "y": 0, "z": -200}},
    {"id": 2, "position": {"x": 1000, "y": 500, "z": -200}},
    {"id": 3, "position": {"x": 0, "y": 500, "z": -200}},
    {"id": 4, "position": {"x": 0, "y": 1000, "z": -200}},
    {"id": 5, "position": {"x": 1000, "y": 1000, "z": -200}}
  ]
}
```

This creates a lawn-mower pattern covering 10m × 10m area.

Happy flying! 🚁
