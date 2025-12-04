# AirSim Setup and Scaling Guide

## How AirSim Integration Works

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Unreal Engine Project                     │
│  (e.g., Blocks.uproject)                                     │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │          AirSim Plugin                              │    │
│  │  (Unreal/Plugins/AirSim/)                           │    │
│  │                                                      │    │
│  │  - Reads: /tmp/AirSim/settings.json                 │    │
│  │  - Spawns: Drone actors in scene                    │    │
│  │  - Provides: RPC API (port 41451)                   │    │
│  │  - Handles: Physics, sensors, control               │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
│  Scene: 3D environment (buildings, terrain, etc.)           │
└─────────────────────────────────────────────────────────────┘
                              ↕ RPC API
┌─────────────────────────────────────────────────────────────┐
│              Python Client (gym-flock)                       │
│  - Connects to: localhost:41451                              │
│  - Sends: Control commands (velocities, accelerations)       │
│  - Receives: State (positions, velocities, sensor data)      │
└─────────────────────────────────────────────────────────────┘
```

---

## How Blocks.uproject Knows to Use AirSim

### 1. Plugin Installation

The `Blocks.uproject` file references the AirSim plugin:

**Location**: `/Users/pranikchainani/AirSim/Unreal/Environments/Blocks/Blocks.uproject`

**Content** (simplified):
```json
{
  "FileVersion": 3,
  "EngineAssociation": "4.27",
  "Plugins": [
    {
      "Name": "AirSim",
      "Enabled": true
    }
  ]
}
```

### 2. Plugin Location

The AirSim plugin is located at:
```
/Users/pranikchainani/AirSim/Unreal/Plugins/AirSim/
```

When Unreal opens `Blocks.uproject`, it:
1. Reads the .uproject file
2. Finds "AirSim" in the Plugins list
3. Looks for the plugin in:
   - `Blocks/Plugins/AirSim/` (project-specific)
   - OR `AirSim/Unreal/Plugins/AirSim/` (if linked via .uproject)
4. Loads the plugin's code

### 3. Plugin Startup Sequence

When the AirSim plugin loads, it:

**Step 1: Read Settings**
```cpp
// In SimHUD.cpp
std::string settings_path = FileSystem::getAppDataFolder();
// Returns: /tmp/AirSim/ (after our fix)
std::string settings_file = settings_path + "/settings.json";
```

**Step 2: Parse Vehicle Configuration**
```cpp
// Parse settings.json
for (auto& vehicle : settings["Vehicles"]) {
    std::string name = vehicle.first;   // "Drone1", "Drone2", ...
    Vector3 position = vehicle["X"], vehicle["Y"], vehicle["Z"];
    // Spawn drone actor at position
}
```

**Step 3: Spawn Actors**
- Creates Unreal `APawn` actors for each vehicle
- Attaches physics components (SimpleFlight controller)
- Sets up sensors (cameras, IMU, GPS)
- Initializes at specified X, Y, Z positions

**Step 4: Start RPC Server**
- Starts listening on `localhost:41451`
- Waits for Python client connections
- Handles API calls: `enableApiControl()`, `moveByVelocity()`, etc.

---

## Setting Up AirSim in a New Unreal Project

### Option 1: Copy Blocks Environment (Easiest)

```bash
# Copy entire Blocks project
cp -r /Users/pranikchainani/AirSim/Unreal/Environments/Blocks \
      /Users/pranikchainani/MyNewProject

# Rename project file
mv /Users/pranikchainani/MyNewProject/Blocks.uproject \
   /Users/pranikchainani/MyNewProject/MyProject.uproject

# Edit MyProject.uproject to change project name
# Open in Unreal Editor
open /Users/pranikchainani/MyNewProject/MyProject.uproject
```

### Option 2: Add AirSim to Existing Project

#### Step 1: Create Plugins Directory
```bash
cd /path/to/YourProject
mkdir -p Plugins
```

#### Step 2: Link or Copy AirSim Plugin
```bash
# Option A: Symbolic link (saves space)
ln -s /Users/pranikchainani/AirSim/Unreal/Plugins/AirSim \
      Plugins/AirSim

# Option B: Copy plugin (independent)
cp -r /Users/pranikchainani/AirSim/Unreal/Plugins/AirSim \
      Plugins/AirSim
```

#### Step 3: Edit .uproject File
Add AirSim to the plugins list in `YourProject.uproject`:
```json
{
  "FileVersion": 3,
  "Plugins": [
    {
      "Name": "AirSim",
      "Enabled": true
    }
  ],
  "Modules": [
    {
      "Name": "AirSim",
      "Type": "Runtime",
      "LoadingPhase": "Default"
    }
  ]
}
```

#### Step 4: Regenerate Project Files
```bash
cd /path/to/YourProject
# macOS
/Users/pranikchainani/AirSim/Unreal/Environments/Blocks/GenerateProjectFiles.sh

# This regenerates XCode project with plugin
```

#### Step 5: Rebuild Project
```bash
# Open in Unreal Editor
open YourProject.uproject

# Unreal will prompt to rebuild - click "Yes"
# Wait for compilation (5-10 minutes)
```

#### Step 6: Verify Plugin Loaded
In Unreal Editor:
1. Edit → Plugins
2. Search for "AirSim"
3. Should show as "Enabled"

---

## Scaling to More Drones

### Current System Limits

| Component | Practical Limit | Why |
|-----------|----------------|-----|
| **settings.json** | Unlimited | Just JSON text |
| **AirSim Plugin** | ~500 drones | Memory/CPU for physics |
| **Unreal Rendering** | ~100-200 drones | GPU rendering overhead |
| **Python Client** | Unlimited | Only sends commands |
| **Network (RPC)** | ~1000 drones | Bandwidth for state updates |

**Bottleneck**: Usually Unreal Engine rendering (FPS drops)

### Performance vs Drone Count

| Drones | FPS | Usability | Recommended For |
|--------|-----|-----------|-----------------|
| 1-10   | 60+ | Excellent | Development, debugging |
| 10-50  | 30-60 | Good | Training, demonstrations |
| 50-100 | 10-30 | Usable | Research, large-scale tests |
| 100-200 | 5-15 | Slow | Benchmarking only |
| 200+ | <5 | Impractical | Use pure Python simulation |

### Scaling Strategies

#### Strategy 1: Increase Drone Count (Same Hardware)

**Generate settings for N drones:**
```python
import json

def generate_settings(n_drones, spacing=4):
    """Generate settings.json for n_drones in square grid"""
    settings = {
        "SettingsVersion": 1.2,
        "SimMode": "Multirotor",
        "Vehicles": {}
    }

    grid_size = int(n_drones ** 0.5) + 1  # Ceiling of sqrt

    drone_num = 1
    for i in range(grid_size):
        for j in range(grid_size):
            if drone_num > n_drones:
                break

            drone_name = f"Drone{drone_num}"
            settings["Vehicles"][drone_name] = {
                "VehicleType": "SimpleFlight",
                "X": i * spacing,
                "Y": j * spacing,
                "Z": 0
            }
            drone_num += 1

    return settings

# Generate for 200 drones
settings = generate_settings(200, spacing=5)

with open('/tmp/AirSim/settings.json', 'w') as f:
    json.dump(settings, f, indent=2)

print(f"Generated settings for {len(settings['Vehicles'])} drones")
```

**Run:**
```bash
python generate_settings.py
# Restart Unreal Editor
# Press Play
```

#### Strategy 2: Reduce Rendering Load

**Use "headless" mode** (no graphics):

Edit `settings.json`:
```json
{
  "SettingsVersion": 1.2,
  "SimMode": "Multirotor",
  "ViewMode": "",  // No camera rendering
  "Vehicles": { ... }
}
```

Or run Unreal with `-RenderOffScreen` flag (requires Linux).

#### Strategy 3: Multiple Unreal Instances

For >200 drones, split across multiple Unreal instances:

**Instance 1** (port 41451): Drones 1-100
```json
// /tmp/AirSim/settings.json
{
  "Vehicles": {
    "Drone1": {...},
    ...
    "Drone100": {...}
  }
}
```

**Instance 2** (port 41452): Drones 101-200
```json
// /tmp/AirSim2/settings.json
{
  "Vehicles": {
    "Drone101": {...},
    ...
    "Drone200": {...}
  },
  "ApiServerPort": 41452
}
```

Connect Python clients to both ports.

#### Strategy 4: Switch to Pure Simulation

For >200 drones, use **gym-flock Python simulation** (no graphics):

```python
import gym
import gym_flock

# Fast pure-Python simulation (no AirSim)
env = gym.make('FlockingRelative-v0')
env.env.n_agents = 500  # Can handle 1000+ agents!

# 100x faster than AirSim
# No visualization, but useful for training
```

**Use AirSim only for**:
- Final validation
- Demonstrations
- Testing with realistic physics

---

## Configuration Files

### /tmp/AirSim/settings.json

**Purpose**: Configures all vehicles and AirSim settings

**When it's read**: Unreal Editor startup (before pressing Play)

**Key sections**:
```json
{
  "SettingsVersion": 1.2,
  "SimMode": "Multirotor",        // Or "Car", "ComputerVision"

  "ClockSpeed": 1.0,               // Simulation speed multiplier

  "ViewMode": "SpringArmChase",    // Camera mode

  "Vehicles": {
    "Drone1": {
      "VehicleType": "SimpleFlight",  // Flight controller type
      "X": 0, "Y": 0, "Z": 0,         // Initial position (meters)
      "Yaw": 0, "Pitch": 0, "Roll": 0 // Initial orientation (degrees)
    }
  },

  "ApiServerPort": 41451           // RPC port for Python client
}
```

### Why /tmp/AirSim/?

**Original AirSim**: Uses `~/Documents/AirSim/`

**This modified version**: Uses `/tmp/AirSim/`

**Reason**: macOS Application Sandboxing blocks Unreal from accessing Documents folder

**The fix** (already applied):
```cpp
// AirLib/include/common/common_utils/FileSystem.hpp:58
static std::string getAppDataFolder()
{
    // Use /tmp instead of Documents to avoid macOS sandboxing
    return ensureFolder(std::string("/tmp/") + ProductFolderName);
}
```

---

## Troubleshooting

### "IndexError: list index out of range"

**Cause**: gym-flock expects N drones, but AirSim only spawned M < N

**Fix**: Restart Unreal Editor (not just Stop Play)
```bash
pkill -f UE4Editor
open Blocks.uproject
# Wait for full startup, then Press Play
```

### "Connection refused" from Python

**Cause**: AirSim RPC server not running

**Check**:
```bash
# See if AirSim is listening
lsof -i :41451

# Should show: UE4Editor ... LISTEN
```

**Fix**: Press Play in Unreal (API only starts when playing)

### Slow FPS with Many Drones

**Options**:
1. Reduce drone count
2. Lower Unreal graphics settings (Edit → Project Settings → Rendering)
3. Use smaller level (less geometry)
4. Disable shadows (settings.json: `"CaptureSettings": [{"ImageType": 0}]`)

### Drones Not Visible

**Check**:
1. Camera position: Move camera in Unreal (WASD keys)
2. Drone spawn height: Set `"Z": -2` to spawn lower
3. Scale: Drones might be very small - zoom in

### Settings Changes Not Applied

**Remember**: Settings only read at Editor startup!

**Must do**:
1. Modify `/tmp/AirSim/settings.json`
2. **Close Unreal Editor completely** (Cmd+Q)
3. Reopen: `open Blocks.uproject`
4. Press Play

---

## Performance Optimization Tips

### 1. Disable Unused Features

```json
{
  "Vehicles": {
    "Drone1": {
      "Cameras": {},              // No cameras = faster
      "Sensors": {}               // No sensors = faster
    }
  }
}
```

### 2. Lower Simulation Rate

```json
{
  "ClockSpeed": 1.0,              // Real-time
  // or
  "ClockSpeed": 0.5               // Half-speed (more stable with many drones)
}
```

### 3. Reduce Physics Quality

In Unreal Editor:
- Edit → Project Settings → Physics
- Lower "Max Substep Delta Time"
- Disable "Substepping"

### 4. Use Simpler Environment

```bash
# Blocks has simple geometry (fast)
cd AirSim/Unreal/Environments/Blocks

# LandscapeMountains has complex terrain (slow)
cd AirSim/Unreal/Environments/LandscapeMountains
```

---

## Quick Reference Commands

### Generate Settings for N Drones
```bash
python3 << EOF
import json
n = 100
spacing = 4
grid = int(n**0.5) + 1
vehicles = {f"Drone{i+j*grid+1}": {"VehicleType": "SimpleFlight",
            "X": i*spacing, "Y": j*spacing, "Z": 0}
            for i in range(grid) for j in range(grid) if i+j*grid < n}
json.dump({"SettingsVersion": 1.2, "SimMode": "Multirotor", "Vehicles": vehicles},
          open('/tmp/AirSim/settings.json', 'w'), indent=2)
print(f"Created {len(vehicles)} drones")
EOF
```

### Check Current Configuration
```bash
# Count drones in settings
cat /tmp/AirSim/settings.json | grep -c "Drone"

# Check if AirSim is running
lsof -i :41451

# Kill Unreal
pkill -f UE4Editor
```

### Launch Test
```bash
# 1. Start Unreal
open /Users/pranikchainani/AirSim/Unreal/Environments/Blocks/Blocks.uproject

# 2. Wait 30 seconds for startup

# 3. Press Play (or Alt+P)

# 4. Run Python test
cd /Users/pranikchainani/multiagent_gnn_policies
python test_airsim_100.py
```

---

## Summary

**How it works**:
1. AirSim is a **plugin** added to Unreal projects via `.uproject` file
2. Plugin reads `/tmp/AirSim/settings.json` at **Editor startup**
3. Plugin spawns drone actors based on settings
4. Plugin starts RPC server for Python control
5. Python client (gym-flock) connects and sends commands

**To scale**:
- Edit `settings.json` to add more drones
- Restart Unreal Editor (not just Stop/Play)
- Expect performance degradation >100 drones
- Use pure Python simulation for large-scale training

**Key insight**: AirSim provides **realistic physics + visualization** but is slow. Use it for testing/demo, not large-scale training!
