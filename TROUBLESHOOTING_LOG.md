# AirSim Troubleshooting Log - macOS Sequoia M1

## System Information
- **Mac**: M1 (arm64)
- **macOS**: Sequoia (24.6.0 / Darwin 24.6.0)
- **Xcode**: 16.1.1 (Build 17B100)
- **Unreal Engine**: 4.27
- **CMake**: 3.31.0

## Issues Encountered

### 1. Code Signing Error (RESOLVED)
**Error**: `Cannot code sign because the target does not have an Info.plist file`

**Solution Applied**:
- Added `INFOPLIST_FILE` settings to Development Editor and DebugGame Editor configurations
- Files modified:
  - `/Users/pranikchainani/AirSim/Unreal/Environments/Blocks/Intermediate/ProjectFiles/Blocks.xcodeproj/project.pbxproj:7192`
  - `/Users/pranikchainani/AirSim/Unreal/Environments/Blocks/Intermediate/ProjectFiles/Blocks.xcodeproj/project.pbxproj:7148`

### 2. Metal Toolchain Missing (RESOLVED)
**Error**: `error: cannot execute tool 'metal' due to missing Metal Toolchain`

**Solution Applied**:
```bash
xcodebuild -downloadComponent MetalToolchain
```
Successfully downloaded 704.6 MB Metal Toolchain.

### 3. Runtime Crash when Starting Simulation (NOT RESOLVED)
**Error**: Crash in `ASimHUD::readSettingsTextFromFile` when pressing Play in Unreal Editor

**Stack Trace**:
```
ASimHUD::readSettingsTextFromFile(FString const&, std::__1::basic_string<char, std::__1::char_traits<char>, std::__1::allocator<char>>&)
ASimHUD::getSettingsText(std::__1::basic_string<char, std::__1::char_traits<char>, std::__1::allocator<char>>&)
ASimHUD::initializeSettings() [SimHUD.cpp:222]
ASimHUD::BeginPlay() [SimHUD.cpp:26]
```

**Attempted Solutions**:
1. Created minimal settings.json file
2. Removed extended attributes from settings.json
3. Verified file permissions
4. None resolved the crash

### 4. AirSim Build Failures (RESOLVED ✅)
**Issue**: Build fails at 82% completion with exit code 2

**Root Cause**: CMake was linking x86_64 binaries with arm64 libc++ from Homebrew's LLVM
- Error: `ld: warning: ignoring file '/opt/homebrew/opt/llvm/lib/c++/libc++.dylib': found architecture 'arm64', required architecture 'x86_64'`
- This caused undefined symbol errors during linking

**Solution Applied**:
Modified `/Users/pranikchainani/AirSim/cmake/cmake-modules/CommonSetup.cmake` (lines 52-57):
- Commented out Homebrew LLVM library paths
- Use system libc++ instead which supports both architectures
- Changed from: `set(CMAKE_EXE_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS} -L${LLVM_PREFIX}/lib/c++ -Wl,-rpath,${LLVM_PREFIX}/lib/c++")`
- To: Use default system libc++ (no explicit path)

**Result**: Build completes successfully at 100%!

**Build Configuration**:
- Building for x86_64 architecture (for Rosetta compatibility)
- Using Apple Clang 17.0.0.17000404
- Compiler: `/usr/bin/clang` and `/usr/bin/clang++`
- Using system libc++ (not Homebrew's)

## Warnings (Non-blocking)
- Deprecation warnings for C++17 features (expected with newer Xcode)
- Unused variable warnings in MavLink code
- Override warnings in rpclib

## Known Working Configuration (Other M1 Mac)
**Status**: User reports AirSim works on another M1 Mac
**Details needed**:
- Exact Unreal Engine version
- macOS version
- Xcode version
- Any special build steps or forks used

## GitHub Issues Referenced
- [#4922](https://github.com/microsoft/AirSim/issues/4922) - Building Blocks on macOS Sonoma with Apple Silicon
  - Suggests using Rosetta with x86_64 architecture (we're doing this)
  - Some success reported with Xcode 14.3.1 instead of newer versions

## Files Modified
1. `/Users/pranikchainani/AirSim/Unreal/Environments/Blocks/Intermediate/ProjectFiles/Blocks.xcodeproj/project.pbxproj`
   - Added INFOPLIST_FILE settings for Editor configurations

2. `/Users/pranikchainani/Documents/AirSim/settings.json`
   - Simplified to minimal configuration
   - Removed extended attributes

3. `/Users/pranikchainani/AirSim/build.sh`
   - Already had correct x86_64 settings (no changes needed)

4. `/Users/pranikchainani/AirSim/cmake/cmake-modules/CommonSetup.cmake` ⭐ **KEY FIX**
   - Commented out Homebrew LLVM linker paths (lines 52-57)
   - Use system libc++ instead for x86_64 cross-compilation on Apple Silicon
   - This fixed the build failure at 82%

## Next Steps to Try
1. Get exact working configuration from other M1 Mac
2. Consider downgrading Xcode to 14.3.1 if that's what worked
3. Try specific Unreal Engine 4.27.x version that worked
4. Look for community forks with Sequoia fixes
5. Consider using virtual machine with compatible macOS/Xcode versions

## Useful Commands
```bash
# Clean and rebuild
cd /Users/pranikchainani/AirSim
./clean.sh && ./setup.sh && ./build.sh

# Regenerate Xcode project
"/Users/Shared/Epic Games/UE_4.27/Engine/Build/BatchFiles/Mac/GenerateProjectFiles.sh" \
  -project="/Users/pranikchainani/AirSim/Unreal/Environments/Blocks/Blocks.uproject" -game

# Launch Blocks environment
open /Users/pranikchainani/AirSim/Unreal/Environments/Blocks/Blocks.uproject

# Check architecture
lipo -info /path/to/binary
```

## Resources
- Official AirSim Build Guide: https://microsoft.github.io/AirSim/build_macos/
- GitHub Issues: https://github.com/microsoft/AirSim/issues?q=is%3Aissue+macOS+M1
- Environment Guide: `/Users/pranikchainani/AirSim/HOW_TO_RUN_ENVIRONMENTS.md`
