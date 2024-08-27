#!/bin/zsh
# NB: Run in build directory

# Check if the build directory exists
if [ ! -d "out/Debug" ]; then
  echo "Error: Build directory out/Debug does not exist. Run build_dawn.sh first."
  exit 1
fi

cd out/Debug || exit 1
ninja dawn.node # Build the Node.js bindings