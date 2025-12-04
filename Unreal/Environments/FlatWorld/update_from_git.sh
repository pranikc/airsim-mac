#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
pushd "$SCRIPT_DIR" >/dev/null

set -e
set -x

./clean.sh

rsync -a --exclude 'temp' --delete ../../Plugins/AirSim Plugins/
rsync -a --exclude 'temp' --delete ../../../AirLib Plugins/AirSim/Source/

popd >/dev/null
