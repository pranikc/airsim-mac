#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
pushd "$SCRIPT_DIR" >/dev/null

set -e
set -x

rm -rf Binaries
rm -rf Intermediate
rm -rf Saved
rm -rf Plugins/AirSim/Binaries
rm -rf Plugins/AirSim/Intermediate
rm -rf Plugins/AirSim/Saved
rm -f CMakeLists.txt
rm -f Makefile

popd >/dev/null
