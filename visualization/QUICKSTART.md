# Quick Start Guide

Get up and running in 5 minutes!

## 1. Setup AirSim Settings

```bash
cp settings_multiagent.json ~/Documents/AirSim/settings.json
```

**⚠️ Important**: Restart Unreal after this step!

## 2. Open Unreal Environment

```bash
open /Users/pranikchainani/AirSim/Unreal/Environments/FlatWorld/FlatWorld.uproject
```

Wait for Unreal to load, then **Press Play** (▶️)

## 3. Run First Visualization

```bash
cd scripts
python visualize_episode.py ../data/episodes/episode_0001.json
```

Press ENTER when prompted, and watch the episode!

## Common Commands

```bash
# Basic run
python visualize_episode.py ../data/episodes/episode_0001.json

# 2x speed
python visualize_episode.py ../data/episodes/episode_0001.json --speed 2.0

# Specific frames
python visualize_episode.py ../data/episodes/episode_0001.json --start-frame 100 --end-frame 500

# Different episode
python visualize_episode.py ../data/episodes/episode_0002.json
```

## What You'll See

- 🟢 **Green trajectory**: Defender drone
- 🔴 **Red trajectory**: Attacker drone
- 🔵 **Blue point**: Base/Target

## Need Help?

See [README.md](README.md) for full documentation and troubleshooting.
