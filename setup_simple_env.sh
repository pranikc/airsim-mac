#!/bin/bash

# Script to set up a simple test environment for AirSim
# This automates the file setup for Option 1

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[94m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}AirSim Simple Test Environment Setup${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

AIRSIM_DIR="/Users/pranikchainani/AirSim"
ENV_DIR="$AIRSIM_DIR/Unreal/Environments/SimpleTest"
PLUGIN_DIR="$AIRSIM_DIR/Unreal/Plugins/AirSim"

# Check if AirSim plugin exists
if [ ! -d "$PLUGIN_DIR" ]; then
    echo -e "${RED}Error: AirSim plugin not found at $PLUGIN_DIR${NC}"
    exit 1
fi

echo -e "${GREEN}✓ AirSim plugin found${NC}"

# Check if environment already exists
if [ -d "$ENV_DIR" ]; then
    echo -e "${YELLOW}Warning: SimpleTest environment already exists at $ENV_DIR${NC}"
    read -p "Do you want to replace it? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}Backing up existing environment...${NC}"
        mv "$ENV_DIR" "${ENV_DIR}_backup_$(date +%Y%m%d_%H%M%S)"
    else
        echo -e "${YELLOW}Exiting without changes${NC}"
        exit 0
    fi
fi

echo ""
echo -e "${BLUE}Step 1: Creating project directory structure${NC}"
mkdir -p "$ENV_DIR/Content/Maps"
mkdir -p "$ENV_DIR/Plugins"
echo -e "${GREEN}✓ Directory structure created${NC}"

echo ""
echo -e "${BLUE}Step 2: Copying AirSim plugin${NC}"
cp -r "$PLUGIN_DIR" "$ENV_DIR/Plugins/"
echo -e "${GREEN}✓ AirSim plugin copied${NC}"

echo ""
echo -e "${BLUE}Step 3: Creating .uproject file${NC}"

cat > "$ENV_DIR/SimpleTest.uproject" << 'UPROJECT'
{
    "FileVersion": 3,
    "EngineAssociation": "4.27",
    "Category": "",
    "Description": "Simple test environment for AirSim",
    "Plugins": [
        {
            "Name": "AirSim",
            "Enabled": true
        }
    ]
}
UPROJECT

echo -e "${GREEN}✓ .uproject file created${NC}"

echo ""
echo -e "${BLUE}Step 4: Creating AirSim settings.json${NC}"

cat > ~/Documents/AirSim/settings.json << 'SETTINGS'
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
SETTINGS

echo -e "${GREEN}✓ settings.json created at ~/Documents/AirSim/${NC}"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Setup Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo ""
echo "1. Open the Unreal project:"
echo -e "   ${GREEN}open $ENV_DIR/SimpleTest.uproject${NC}"
echo ""
echo "2. When Unreal opens, it will ask to rebuild modules - click ${GREEN}Yes${NC}"
echo ""
echo "3. Once opened, you need to:"
echo "   a. Create a simple environment in the level editor:"
echo "      - Add a large Plane (floor)"
echo "      - Add some Cube obstacles"
echo "      - Add a Sphere named 'target' with bright color"
echo "      - Set GameMode to AirSimGameMode (Edit → Project Settings)"
echo "   b. Save the map (File → Save Current As... → TestMap)"
echo "   c. Set as default map (Edit → Project Settings → Default Maps)"
echo ""
echo "4. Press ${GREEN}Play ▶️${NC} to test"
echo ""
echo "5. Test Python connection:"
echo -e "   ${GREEN}cd /Users/pranikchainani/AirSim/PythonClient/airsim_single_agent${NC}"
echo -e "   ${GREEN}conda activate swarms${NC}"
echo -e "   ${GREEN}python -c \"import airsim; c = airsim.MultirotorClient(); c.confirmConnection(); print('Connected!')\"${NC}"
echo ""
echo -e "${BLUE}Alternative: Use existing Blocks environment instead${NC}"
echo -e "   ${GREEN}open $AIRSIM_DIR/Unreal/Environments/Blocks/Blocks.uproject${NC}"
echo ""
echo -e "For detailed instructions, see: ${GREEN}$AIRSIM_DIR/CREATE_SIMPLE_ENV.md${NC}"
echo ""
