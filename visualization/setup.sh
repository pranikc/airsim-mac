#!/bin/bash
#
# Setup script for AirSim Multi-Agent Visualization
#
# This script:
# 1. Copies multi-agent settings to AirSim
# 2. Verifies Python dependencies
# 3. Tests the visualization system
#

set -e  # Exit on error

echo "========================================"
echo "AirSim Multi-Agent Visualization Setup"
echo "========================================"
echo ""

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# 1. Copy settings
echo "Step 1: Installing AirSim settings..."
AIRSIM_SETTINGS_DIR="$HOME/Documents/AirSim"
mkdir -p "$AIRSIM_SETTINGS_DIR"

if [ -f "$AIRSIM_SETTINGS_DIR/settings.json" ]; then
    echo "  Backing up existing settings.json..."
    cp "$AIRSIM_SETTINGS_DIR/settings.json" "$AIRSIM_SETTINGS_DIR/settings.json.backup_$(date +%Y%m%d_%H%M%S)"
fi

cp settings_multiagent.json "$AIRSIM_SETTINGS_DIR/settings.json"
echo "  ✓ Settings installed to $AIRSIM_SETTINGS_DIR/settings.json"
echo ""

# 2. Check Python dependencies
echo "Step 2: Checking Python dependencies..."

if ! python3 -c "import airsim" 2>/dev/null; then
    echo "  ⚠️  airsim not found. Installing..."
    pip3 install airsim
fi

if ! python3 -c "import numpy" 2>/dev/null; then
    echo "  ⚠️  numpy not found. Installing..."
    pip3 install numpy
fi

echo "  ✓ All dependencies installed"
echo ""

# 3. Verify data
echo "Step 3: Verifying episode data..."
EPISODE_COUNT=$(ls -1 data/episodes/*.json 2>/dev/null | wc -l)
echo "  Found $EPISODE_COUNT episode files"

if [ $EPISODE_COUNT -eq 0 ]; then
    echo "  ⚠️  No episode files found in data/episodes/"
    echo "  Please add episode JSON files to data/episodes/ directory"
else
    echo "  ✓ Episode data ready"
fi
echo ""

# 4. Test configuration
echo "Step 4: Testing configuration..."
cd scripts
python3 config.py > /dev/null 2>&1 && echo "  ✓ Config module OK" || echo "  ⚠️  Config module failed"
echo ""

# 5. Summary
echo "========================================"
echo "Setup Complete!"
echo "========================================"
echo ""
echo "Next steps:"
echo "  1. ⚠️  RESTART Unreal Engine (required for settings to take effect)"
echo "  2. Open FlatWorld environment"
echo "  3. Press Play in Unreal Editor"
echo "  4. Run visualization:"
echo "     cd scripts"
echo "     python3 visualize_episode.py ../data/episodes/episode_0001.json"
echo ""
echo "See README.md for full documentation"
echo "See QUICKSTART.md for quick reference"
echo ""
