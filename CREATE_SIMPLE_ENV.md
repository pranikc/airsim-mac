# Creating a Simple Custom Unreal Environment for AirSim Testing

This guide will help you create a minimal custom Unreal environment with AirSim plugin for testing your single-agent drone RL.

## Option 1: Create New Minimal Environment (Recommended)

### Step 1: Create New Unreal Project

1. **Open Unreal Engine** (from Epic Games Launcher or directly)

2. **Create New Project:**
   - Click "New Project"
   - Select "Games" category
   - Choose "Blank" template
   - Project Settings:
     - Blueprint (not C++)
     - Maximum Quality
     - Raytracing: Disabled (for better performance)
     - No Starter Content (keeps it minimal)
   - Project Location: `/Users/pranikchainani/AirSim/Unreal/Environments/`
   - Project Name: `SimpleTest`
   - Click "Create"

### Step 2: Add AirSim Plugin to Your Project

Once your project is created:

1. **Close Unreal Engine** (if it auto-opened)

2. **Copy the AirSim plugin:**
   ```bash
   mkdir -p /Users/pranikchainani/AirSim/Unreal/Environments/SimpleTest/Plugins
   cp -r /Users/pranikchainani/AirSim/Unreal/Plugins/AirSim /Users/pranikchainani/AirSim/Unreal/Environments/SimpleTest/Plugins/
   ```

3. **Edit the .uproject file to enable the plugin:**
   ```bash
   # Open the SimpleTest.uproject file
   nano /Users/pranikchainani/AirSim/Unreal/Environments/SimpleTest/SimpleTest.uproject
   ```

   Add this to the file (before the closing `}`):
   ```json
   "Plugins": [
       {
           "Name": "AirSim",
           "Enabled": true
       }
   ]
   ```

   The complete file should look like:
   ```json
   {
       "FileVersion": 3,
       "EngineAssociation": "4.27",
       "Category": "",
       "Description": "",
       "Plugins": [
           {
               "Name": "AirSim",
               "Enabled": true
           }
       ]
   }
   ```

4. **Generate project files:**
   ```bash
   cd /Users/pranikchainani/AirSim/Unreal/Environments/SimpleTest
   # Right-click on SimpleTest.uproject and select "Generate Xcode Project"
   # Or if you have Unreal Engine command line tools:
   # /Path/To/UnrealEngine/Engine/Build/BatchFiles/Mac/GenerateProjectFiles.sh -project="$(pwd)/SimpleTest.uproject" -game
   ```

5. **Open the project in Unreal:**
   - Double-click `SimpleTest.uproject`
   - If asked to rebuild, click "Yes"
   - Wait for compilation (first time may take 5-10 minutes)

### Step 3: Set Up Simple Test Environment

Once Unreal opens:

1. **Create a simple floor:**
   - In the "Place Actors" panel (left side), search for "Plane"
   - Drag a "Plane" into the viewport
   - In Details panel (right), set:
     - Scale: X=10, Y=10, Z=1 (makes a large flat surface)
     - Location: X=0, Y=0, Z=0

2. **Add some obstacles (optional):**
   - Drag a few "Cubes" from Place Actors
   - Scale and position them around the environment
   - These will serve as obstacles for the drone

3. **Add a target object:**
   - Drag a "Sphere" from Place Actors
   - Name it "target" in the World Outliner
   - Set a bright color (red/green) in Details → Materials
   - Position it somewhere: e.g., X=5000, Y=0, Z=200

4. **Lighting:**
   - Should already have a "Directional Light" by default
   - If not, add one from Place Actors

5. **Player Start:**
   - Delete any existing "Player Start" (we don't need it for AirSim)

### Step 4: Configure for AirSim

1. **Set game mode to AirSim:**
   - Go to Edit → Project Settings
   - Search for "Game Mode"
   - Under "Maps & Modes" → "Default GameMode"
   - Select "AirSimGameMode" from dropdown

2. **Save the map:**
   - File → Save Current As...
   - Name it "TestMap"
   - Set as default map: Edit → Project Settings → Maps & Modes → Default Maps
   - Set both Editor Startup Map and Game Default Map to "TestMap"

3. **Save and close Unreal**

### Step 5: Configure AirSim Settings

The settings.json should already be at `~/Documents/AirSim/settings.json`:

```bash
cat > ~/Documents/AirSim/settings.json << 'EOF'
{
  "SeeDocsAt": "https://github.com/Microsoft/AirSim/blob/main/docs/settings.md",
  "SettingsVersion": 1.2,
  "LocalHostIp": "127.0.0.1",
  "SimMode": "Multirotor",
  "ClockSpeed": 20,
  "ViewMode": "SpringArmChase",
  "Vehicles": {
      "drone0": {
          "VehicleType": "SimpleFlight",
          "X": 0.0,
          "Y": 0.0,
          "Z": -200.0,
          "Yaw": 0.0
      }
  },
  "CameraDefaults": {
      "CaptureSettings": [
          {
              "ImageType": 0,
              "Width": 84,
              "Height": 84,
              "FOV_Degrees": 120
          },
          {
              "ImageType": 2,
              "Width": 84,
              "Height": 84,
              "FOV_Degrees": 120
          }
      ]
  }
}
EOF
```

### Step 6: Test the Environment

1. **Open the project:**
   ```bash
   open /Users/pranikchainani/AirSim/Unreal/Environments/SimpleTest/SimpleTest.uproject
   ```

2. **Press Play** (▶️ button in toolbar)

3. **Verify AirSim is working:**
   - You should see a drone spawn
   - Camera view should appear
   - Check Unreal console for "AirSim" messages

4. **Test Python connection:**
   ```bash
   cd /Users/pranikchainani/AirSim/PythonClient/airsim_single_agent
   conda activate swarms
   python -c "import airsim; c = airsim.MultirotorClient(); c.confirmConnection(); print('✓ Connected!')"
   ```

5. **Get target coordinates:**
   ```bash
   python -c "import airsim; c = airsim.MultirotorClient(); c.confirmConnection(); t = c.simGetObjectPose('target'); print(f'Target: X={t.position.x_val:.2f}, Y={t.position.y_val:.2f}, Z={t.position.z_val:.2f}')"
   ```

6. **Update env_config.yml** with your target coordinates:
   ```bash
   nano /Users/pranikchainani/AirSim/PythonClient/airsim_single_agent/scripts/env_config.yml
   ```

## Option 2: Use Existing Blocks Environment

If you want to skip creating a new environment, you can use the existing Blocks:

1. **Open Blocks:**
   ```bash
   open /Users/pranikchainani/AirSim/Unreal/Environments/Blocks/Blocks.uproject
   ```

2. **Press Play**

3. **The Blocks environment already has:**
   - Multiple obstacles (blocks)
   - Good for testing navigation
   - Known working environment

4. **Add a target object:**
   - In Unreal Editor, add a Sphere actor
   - Name it "target"
   - Give it a bright color
   - Note its position

5. **Update settings and configs as above**

## Quick Setup Script

I'll create a script to automate Option 1...

## Troubleshooting

### "Plugin 'AirSim' failed to load"
- Make sure you copied the plugin correctly
- Rebuild the project: Right-click .uproject → Services → Generate Xcode Project
- Try opening with Unreal Engine directly from Epic Games Launcher

### "Game mode not found"
- Make sure AirSim plugin loaded successfully
- Check Edit → Plugins, search for "AirSim", make sure it's enabled

### Unreal crashes on Play
- Reduce ClockSpeed in settings.json to 10
- Check Unreal logs in `~/Library/Logs/Unreal Engine/`
- Try with simpler scene (fewer objects)

### Can't find target object
- Make sure it's named exactly "target" (lowercase)
- Check it's in the World Outliner
- Try with a simple coordinate first: X=1000, Y=0, Z=0

## Environment Coordinates Guide

For a 10x10 plane with scale:
- **Unreal Units**: 1 unit = 1 cm in real world
- **Typical ranges**:
  - X: -50000 to 50000 (500 meters)
  - Y: -50000 to 50000 (500 meters)
  - Z: -1000 to 1000 (10 meters altitude)

**Example spawn and target:**
- Drone spawn: X=0, Y=0, Z=-200 (2 meters above ground)
- Target: X=5000, Y=0, Z=-200 (50 meters forward)

Update in `env_config.yml`:
```yaml
TrainEnv:
  sections:
  - target:
    - 5000  # X coordinate
    - 0     # Y coordinate
    offset:
    - 0
```

And in `airsim_env.py` (lines 67-68):
```python
y_pos = (np.random.rand()-0.5)*2*1000  # ±10 meters
z_pos = (np.random.rand()-0.5)*2*200   # ±2 meters from -200
```

## Next Steps After Environment Setup

1. ✅ Environment created and AirSim plugin working
2. ✅ Can press Play and see drone
3. ✅ Python can connect to AirSim
4. ✅ Target object placed and coordinates noted
5. ✅ Updated env_config.yml with target coordinates
6. ✅ Updated spawn ranges in airsim_env.py
7. → **Run training:** `python train.py`

Good luck!
