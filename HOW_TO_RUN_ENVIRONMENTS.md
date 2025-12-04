# AirSim Environment Guide

## 🤔 Wait, Why Did We Use .xcworkspace Earlier?

**Short Answer:** We had to build AirSim from source and fix a bug. Now that it's built, just use `.uproject` files!

**Long Answer:**
- **First time setup**: When building AirSim from source, you MUST compile the C++ code using Xcode
- **We had a bug**: The Info.plist error required fixing the Xcode project and rebuilding
- **Going forward**: After building once, just double-click `.uproject` files to run

### Think of it like this:
- **`.xcworkspace`** = Building a car in a factory 🏭 (one-time setup)
- **`.uproject`** = Driving the car 🚗 (daily use)

### When to Use Each:

| File Type | When to Use | What It Does |
|-----------|-------------|--------------|
| `.uproject` | **99% of the time** | Opens environment in Unreal Editor |
| `.xcworkspace` | Only when modifying C++ code | Compiles AirSim plugin code |

---

## Quick Start - Running an Environment

### Option 1: Launch Directly (Recommended)
Just double-click the `.uproject` file:
```
/Users/pranikchainani/AirSim/Unreal/Environments/Blocks/Blocks.uproject
```

Or from terminal:
```bash
"/Users/Shared/Epic Games/UE_4.27/Engine/Binaries/Mac/UE4Editor.app/Contents/MacOS/UE4Editor" \
  "/Users/pranikchainani/AirSim/Unreal/Environments/Blocks/Blocks.uproject"
```

### Option 2: Using Xcode (For Development)
Use the `.xcworkspace` file only when you need to:
- Debug C++ code
- Modify AirSim plugin code
- Build the project from source

```bash
open Blocks.xcworkspace
# Then press the Play button in Xcode
```

## File Types Explained

| File | Purpose | When to Use |
|------|---------|-------------|
| `.uproject` | Unreal Project File | **Use this to run the environment** |
| `.xcworkspace` | Xcode Workspace | Only for development/debugging |

## 🌍 Getting New Environments

### Currently Installed:
Your environments are located in:
```
/Users/pranikchainani/AirSim/Unreal/Environments/
```

You currently have:
- **Blocks** ✅ - Simple block world (good for testing, fast loading)

### Recommended Environments to Download:

#### 1. **LandscapeMountains** (Official AirSim)
- **What**: Mountain terrain with forests
- **Best for**: Drone racing, outdoor navigation
- **Download**: https://github.com/Microsoft/AirSim/releases
- **Size**: ~500 MB

#### 2. **AirSimNH** (Neighborhood - Official)
- **What**: Suburban neighborhood with houses and roads
- **Best for**: Car simulation, urban drone flight
- **Download**: https://github.com/Microsoft/AirSim/releases
- **Size**: ~1.5 GB

#### 3. **ModularNeighborhood** (Community)
- **What**: City environment with buildings
- **Best for**: Advanced testing, realistic scenarios
- **Download**: Unreal Marketplace (free)
- **Size**: ~2 GB

#### 4. **Africa** (Community)
- **What**: Large open savanna environment
- **Best for**: Long-distance flight testing
- **Download**: Search "Africa environment" on Unreal Marketplace
- **Size**: ~3 GB

### How to Add a New Environment:

#### Method 1: Download Pre-built AirSim Environments
```bash
# Example: Download LandscapeMountains
cd /Users/pranikchainani/AirSim/Unreal/Environments/
# Download from AirSim releases page and extract here
# Then just double-click the .uproject file!
```

#### Method 2: Add AirSim Plugin to Any Unreal Environment

1. **Get an Unreal environment** (Unreal Marketplace or create your own)

2. **Copy the AirSim plugin:**
   ```bash
   # Create Plugins folder in your environment
   mkdir -p /path/to/YourEnvironment/Plugins

   # Copy AirSim plugin
   cp -r /Users/pranikchainani/AirSim/Unreal/Plugins/AirSim \
         /path/to/YourEnvironment/Plugins/
   ```

3. **Edit the .uproject file** to include AirSim:
   ```json
   {
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
   "/Users/Shared/Epic Games/UE_4.27/Engine/Build/BatchFiles/Mac/GenerateProjectFiles.sh" \
     -project="/path/to/YourEnvironment.uproject" -game
   ```

5. **Open and build** the environment

### Switching Between Environments:

**Option 1: Use Finder (Easiest)**
1. Navigate to `/Users/pranikchainani/AirSim/Unreal/Environments/`
2. Go into the environment folder you want
3. Double-click the `.uproject` file

**Option 2: Command Line**
```bash
# Launch Blocks
open /Users/pranikchainani/AirSim/Unreal/Environments/Blocks/Blocks.uproject

# Launch another environment (when you have it)
open /Users/pranikchainani/AirSim/Unreal/Environments/LandscapeMountains/LandscapeMountains.uproject
```

**Option 3: Direct Command**
```bash
"/Users/Shared/Epic Games/UE_4.27/Engine/Binaries/Mac/UE4Editor.app/Contents/MacOS/UE4Editor" \
  "/Users/pranikchainani/AirSim/Unreal/Environments/[EnvironmentName]/[EnvironmentName].uproject"
```

## Running Your Environment

### Method 1: Editor Mode (Default)
Opens the Unreal Editor where you can:
- Modify the environment
- Place objects
- Click "Play" to start simulation

```bash
"/Users/Shared/Epic Games/UE_4.27/Engine/Binaries/Mac/UE4Editor.app/Contents/MacOS/UE4Editor" \
  "/path/to/YourEnvironment.uproject"
```

### Method 2: Game Mode (Standalone)
Launches directly into the simulation:

```bash
"/Users/Shared/Epic Games/UE_4.27/Engine/Binaries/Mac/UE4Editor.app/Contents/MacOS/UE4Editor" \
  "/path/to/YourEnvironment.uproject" -game
```

## Common Issues & Fixes

### Issue: Metal Toolchain Error
```
error: cannot execute tool 'metal' due to missing Metal Toolchain
```

**Fix:**
```bash
xcodebuild -downloadComponent MetalToolchain
```

### Issue: Code Signing Error
```
Cannot code sign because the target does not have an Info.plist file
```

**Fix:** This was already fixed in the Blocks project. If you encounter this in other environments, regenerate project files:
```bash
"/Users/Shared/Epic Games/UE_4.27/Engine/Build/BatchFiles/Mac/GenerateProjectFiles.sh" \
  -project="/path/to/YourEnvironment.uproject" -game
```

### Issue: Build Fails
Rebuild the project:
```bash
cd /Users/pranikchainani/AirSim
./build.sh
```

## AirSim Settings

Your AirSim settings are located at:
```
~/Documents/AirSim/settings.json
```

Edit this file to configure:
- Vehicle type (drone/car)
- Camera settings
- Physics parameters
- API settings

## 📋 Quick Reference Summary

### Daily Workflow (What You'll Actually Do):

```bash
# 1. To run Blocks (or any environment):
open /Users/pranikchainani/AirSim/Unreal/Environments/Blocks/Blocks.uproject

# 2. Click Play button in Unreal Editor

# 3. That's it! 🎉
```

### File Types Quick Reference:

| What You Want | What You Open | Example |
|---------------|---------------|---------|
| **Run simulation** | `.uproject` file | Double-click `Blocks.uproject` |
| **Switch environment** | Different `.uproject` file | Open `LandscapeMountains.uproject` |
| **Modify C++ code** | `.xcworkspace` (rare) | Only for plugin development |
| **Build from source** | Run `./build.sh` (one-time) | Only needed after code changes |

### Common Scenarios:

**"I want to fly a drone in Blocks"**
```bash
open ~/AirSim/Unreal/Environments/Blocks/Blocks.uproject
# Wait for editor → Click Play button
```

**"I want to try a different environment"**
```bash
# Download environment from AirSim releases
# Extract to ~/AirSim/Unreal/Environments/
# Double-click the new .uproject file
```

**"I want to test my Python code with AirSim"**
```bash
# 1. Start any environment (.uproject file)
# 2. Click Play in editor
# 3. Run your Python script in another terminal
python your_airsim_script.py
```

**"I modified AirSim C++ plugin code"**
```bash
# Rebuild AirSim
cd ~/AirSim
./build.sh

# Reopen your environment
open ~/AirSim/Unreal/Environments/Blocks/Blocks.uproject
```

### The Golden Rule:

> **99% of the time: Just double-click the `.uproject` file** ✨
>
> The `.xcworkspace` was needed for the initial build/fix.
> You don't need it anymore unless you're modifying C++ code.

---

## 🔗 Useful Links

- **AirSim Documentation**: https://microsoft.github.io/AirSim/
- **AirSim GitHub**: https://github.com/Microsoft/AirSim
- **Download Environments**: https://github.com/Microsoft/AirSim/releases
- **Unreal Marketplace** (free environments): https://www.unrealengine.com/marketplace/
- **AirSim Settings Guide**: https://microsoft.github.io/AirSim/settings/
- **Python API Docs**: https://microsoft.github.io/AirSim/api_docs/html/

## 💡 Pro Tips

1. **Use Blocks for testing** - It loads the fastest
2. **Settings persist** - Your `~/Documents/AirSim/settings.json` works across all environments
3. **Multiple environments** - You can have many environments, just switch between `.uproject` files
4. **API stays running** - When you start the simulation, the API server starts automatically on port 41451
5. **Create shortcuts** - Add `.uproject` files to your Dock for quick access
