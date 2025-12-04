# AirSim Multi-Agent Trajectory Visualization

A fluid, no-hassle pipeline for visualizing multi-agent drone trajectories in AirSim with automatic coordinate system handling.

## Overview

This visualization system allows you to replay trajectories with:
- **2 Drones**: Defender and Attacker
- **1 Static Object**: Base/Target
- **One-Command Pipeline**: From waypoints JSON to visualization
- **Auto-Configuration**: Coordinate system and units detected automatically
- **No Scaling**: 1:1 mapping from your data to AirSim (centimeters → meters)
- **Trajectory Visualization**: Real-time trajectory trails
- **Configurable Playback**: Speed control, frame ranges, etc.

## Quick Start (One Command!)

```bash
cd visualization/scripts
conda activate swarms
python visualize_waypoints.py ../data/episodes/episode_0001_airsim.json
```

This automatically:
1. ✅ Converts waypoints to episode format
2. ✅ Detects coordinate system (NED) and units (centimeters)
3. ✅ Converts to meters with no scaling (1:1 mapping)
4. ✅ Updates `/tmp/AirSim/settings.json` with starting positions
5. ✅ Runs visualization in AirSim

## Directory Structure

```
visualization/
├── data/
│   └── episodes/                    # Episode JSON files
│       ├── episode_0001_airsim.json      # Input: waypoints format
│       └── episode_0001_converted.json   # Output: episode format
├── scripts/
│   ├── visualize_waypoints.py       # 🚀 ONE-STEP PIPELINE (USE THIS!)
│   ├── visualize_episode.py         # Two-step: visualize episodes
│   ├── convert_waypoints_to_episode.py  # Two-step: convert format
│   ├── config.py                    # Configuration & transforms
│   └── multi_agent_runner.py       # AirSim multi-agent controller
├── settings_multiagent.json         # AirSim settings template (optional)
├── README.md                        # This file
└── requirements.txt                 # Python dependencies
```

## Setup

### 1. Configure AirSim for Multi-Agent

Copy the multi-agent settings to your AirSim settings location:

```bash
cp settings_multiagent.json ~/Documents/AirSim/settings.json
```

**Important**: Make sure to restart Unreal after updating settings.json!

The settings file configures two vehicles:
- `Defender` - Green trajectory
- `Attacker` - Red trajectory

### 2. Install Dependencies

```bash
pip install airsim numpy
```

Or use the requirements file:

```bash
pip install -r requirements.txt
```

### 3. (Optional) Add Base Sphere in Unreal

For better visualization, add a sphere object in your Unreal environment:

1. Open FlatWorld.uproject in Unreal
2. In the editor, add a Sphere actor (Place Actors → Basic → Sphere)
3. Rename it to "Base" in the World Outliner
4. Set its scale to (0.5, 0.5, 0.5) for a nice size
5. Give it a bright color (blue recommended)
6. Set its location to (0, 0, 0)

If you skip this step, the base will be visualized as a blue point.

## Usage

### One-Step Pipeline (Recommended)

Use `visualize_waypoints.py` for the smoothest experience:

```bash
cd visualization/scripts
python visualize_waypoints.py ../data/episodes/episode_0001_airsim.json
```

### Common Options

#### 1. Change Playback Speed

```bash
# 2x speed (faster)
python visualize_waypoints.py ../data/episodes/episode_0001_airsim.json --speed 2.0

# 0.5x speed (slow motion)
python visualize_waypoints.py ../data/episodes/episode_0001_airsim.json --speed 0.5
```

#### 2. Visualize Specific Frame Range

```bash
# Frames 100 to 500
python visualize_waypoints.py ../data/episodes/episode_0001_airsim.json --start-frame 100 --end-frame 500
```

#### 3. Disable Trajectory Trails

```bash
python visualize_waypoints.py ../data/episodes/episode_0001_airsim.json --no-trajectories
```

#### 4. Keep Converted Episode File

```bash
python visualize_waypoints.py ../data/episodes/episode_0001_airsim.json --keep-converted
```

### Two-Step Process (Advanced)

If you need more control:

#### Step 1: Convert Waypoints
```bash
python convert_waypoints_to_episode.py \
    ../data/episodes/episode_0001_airsim.json \
    ../data/episodes/episode_0001_converted.json
```

#### Step 2: Visualize
```bash
python visualize_episode.py ../data/episodes/episode_0001_converted.json
```

### All Options

```bash
python visualize_episode.py --help
```

Output:
```
usage: visualize_episode.py [-h] [--speed SPEED] [--start-frame START_FRAME]
                           [--end-frame END_FRAME] [--no-takeoff]
                           [--scale SCALE] [--no-trajectories]
                           episode_file

Options:
  episode_file              Path to episode JSON file
  --speed SPEED            Playback speed multiplier (default: 1.0)
  --start-frame START_FRAME Starting frame index (default: 0)
  --end-frame END_FRAME    Ending frame index (default: last frame)
  --no-takeoff             Skip takeoff sequence
  --scale SCALE            Position scale factor (default: 100.0)
  --no-trajectories        Disable trajectory visualization
```

## Workflow

### Step-by-Step Visualization

1. **Open Unreal Environment**
   ```bash
   open /Users/pranikchainani/AirSim/Unreal/Environments/FlatWorld/FlatWorld.uproject
   ```

2. **Press Play** in Unreal Editor (▶️ button)

3. **Run Visualization**
   ```bash
   cd /Users/pranikchainani/AirSim/visualization/scripts
   python visualize_episode.py ../data/episodes/episode_0001.json
   ```

4. **Watch the Episode!**
   - Green trajectory = Defender
   - Red trajectory = Attacker
   - Blue point/sphere = Base

5. **Try Other Episodes**
   ```bash
   python visualize_episode.py ../data/episodes/episode_0002.json
   python visualize_episode.py ../data/episodes/episode_0003.json
   ```

## Data Format

Episodes are stored in JSON format:

```json
{
  "metadata": {
    "episode": 1,
    "total_reward": 499.39,
    "steps": 1044,
    "outcome": "capture"
  },
  "frames": [
    {
      "t": 0.0,
      "defender": {
        "pos": [x, y, z],
        "vel": [vx, vy, vz],
        "rpy": [roll, pitch, yaw]
      },
      "attacker": {
        "pos": [x, y, z],
        "vel": [vx, vy, vz],
        "rpy": [roll, pitch, yaw]
      },
      "base": {
        "pos": [x, y, z]
      }
    },
    ...
  ]
}
```

## Coordinate System

### NED (North-East-Down) - Used by Both Input and AirSim

Both your input data and AirSim use NED coordinates:
- **X**: North (forward)
- **Y**: East (right)
- **Z**: Down (negative is up)

Example: `z = -200 cm` in your JSON means **200 cm altitude** (2 meters up)

### No Transformations Needed

Since both input and AirSim use NED, the pipeline automatically:
1. ✅ **Converts units**: centimeters → meters (divide by 100)
2. ✅ **Preserves coordinates**: No Z-axis inversion (`INVERT_Z = False`)
3. ✅ **No scaling**: 1:1 mapping (`SCALE_FACTOR = 1.0`)
4. ✅ **Direct mapping**: Your data appears exactly as specified (after unit conversion)

Example transformation:
- Input: `defender.position = {x: 17.2 cm, y: 83.4 cm, z: -200 cm}` (NED)
- Output: `defender.pos = [0.172 m, 0.834 m, -2.0 m]` (NED)
- No scaling, no axis flips!

## Configuration

The pipeline auto-configures based on your episode metadata, but you can customize `scripts/config.py`:

```python
class VisualizationConfig:
    # Coordinate transformation (auto-configured from metadata)
    SCALE_FACTOR = 1.0          # No scaling (1:1 mapping)
    INVERT_Z = False            # No Z inversion for NED→NED
    Z_OFFSET = 0.0              # No offset

    # Vehicle names (must match AirSim settings.json)
    DEFENDER_NAME = "Defender"
    ATTACKER_NAME = "Attacker"

    # Visualization
    SHOW_TRAJECTORIES = True
    TRAJECTORY_COLOR_DEFENDER = [0.0, 1.0, 0.0, 1.0]  # Green
    TRAJECTORY_COLOR_ATTACKER = [1.0, 0.0, 0.0, 1.0]  # Red
    TRAJECTORY_COLOR_BASE = [0.0, 0.5, 1.0, 1.0]      # Cyan
    TRAJECTORY_THICKNESS = 2.0

    # Logging
    LOG_EVERY_N_FRAMES = 10
```

**Note**: SCALE_FACTOR and INVERT_Z are automatically set based on the `coordinate_system` field in your episode metadata. For NED input, no scaling or inversion is applied.

## Troubleshooting

### "Could not find vehicles" Error

**Problem**: AirSim settings.json doesn't have Defender and Attacker configured.

**Solution**:
```bash
cp settings_multiagent.json ~/Documents/AirSim/settings.json
```
Then restart Unreal.

### Drones at Wrong Position

**Problem**: Drones appear at unexpected locations.

**Possible causes**:
1. Check that your JSON has `coordinate_system: "NED"` and `units: "centimeters"`
2. Verify frame 0 positions were written to `/tmp/AirSim/settings.json`
3. Restart Unreal Engine to load new settings.json
4. Check that positions are reasonable (e.g., z=-200 cm = 2m altitude)

**Solution**: The pipeline auto-detects coordinate system. Verify with:
```bash
python visualize_waypoints.py ../data/episodes/episode_0001_airsim.json
# Check output shows: "Coordinate System: NED" and "INVERT_Z: False"
```

### Drones Not Moving

**Problem**: Drones takeoff but don't move to positions.

**Possible causes**:
1. Verify converted episode data is valid (check frames have different positions)
2. Check AirSim console for errors
3. Ensure positions are not identical across all frames

### Connection Failed

**Problem**: Cannot connect to AirSim.

**Solution**:
1. Make sure Unreal is running
2. Press Play (▶️) in Unreal Editor
3. Wait a few seconds for AirSim to initialize
4. Try running the script again

### Trajectories Not Showing

**Problem**: No trajectory trails visible.

**Solution**:
- Check `SHOW_TRAJECTORIES = True` in config.py
- Try without `--no-trajectories` flag
- Trajectories update every 10 frames, wait a bit

## Adding New Episodes

Simply copy your episode JSON files to `data/episodes/`:

```bash
cp /path/to/new_episode.json visualization/data/episodes/
```

Then visualize:

```bash
cd visualization/scripts
python visualize_episode.py ../data/episodes/new_episode.json
```

## Advanced Usage

### Batch Visualize All Episodes

Create a simple bash script:

```bash
#!/bin/bash
cd /Users/pranikchainani/AirSim/visualization/scripts

for episode in ../data/episodes/*.json; do
    echo "Visualizing $episode..."
    python visualize_episode.py "$episode" --speed 2.0
    sleep 5
done
```

### Record Video

Use AirSim's built-in recording by enabling in settings.json:

```json
"Recording": {
    "RecordOnMove": true,
    "RecordInterval": 0.05
}
```

### Custom Trajectory Colors

Edit `scripts/config.py`:

```python
TRAJECTORY_COLOR_DEFENDER = [0.0, 1.0, 1.0, 1.0]  # Cyan
TRAJECTORY_COLOR_ATTACKER = [1.0, 0.0, 1.0, 1.0]  # Magenta
```

## Tips

1. **Speed Control**: Use `--speed 2.0` for quick previews, `--speed 0.5` for detailed analysis
2. **Frame Ranges**: Use `--start-frame` and `--end-frame` to focus on interesting parts
3. **Multiple Runs**: The script safely lands and resets, so you can run multiple episodes sequentially
4. **Camera View**: Switch between camera views in Unreal while running (F1-F12 keys)

## Files Overview

| File | Purpose |
|------|---------|
| `visualize_episode.py` | Main entry point, CLI interface |
| `multi_agent_runner.py` | Controls multiple drones in AirSim |
| `config.py` | Configuration and coordinate transforms |
| `settings_multiagent.json` | AirSim multi-agent configuration template |
| `data/episodes/*.json` | Episode data files |

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Verify your AirSim settings match `settings_multiagent.json`
3. Test with `episode_0001.json` first (smallest file)

## Future Enhancements

Possible additions:
- [ ] Pause/resume during playback
- [ ] Real-time statistics overlay
- [ ] Camera following modes
- [ ] Collision detection visualization
- [ ] Export to video file
- [ ] Interactive scrubbing (jump to frame)

---

**Author**: AirSim Visualization Pipeline
**Version**: 1.0
**Date**: December 2025
