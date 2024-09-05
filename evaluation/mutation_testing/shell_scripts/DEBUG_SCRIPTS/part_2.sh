#!/bin/bash

usage() {
  echo "Usage: $0 --dawn_type={normal, meta_mutant, mutant_tracking}"
  exit 1
}

build_dawn_aux() {
  echo "Building dawn ($type version)..."
  if [[ "$type" == "normal" ]]; then
    cmake ../.. -GNinja -DDAWN_BUILD_NODE_BINDINGS=1
  else
    cmake ../.. -GNinja \
      -DDAWN_BUILD_NODE_BINDINGS=1 \
      -DCMAKE_EXPORT_COMPILE_COMMANDS=ON \
      -DCMAKE_CXX_FLAGS="-Wno-error -Wno-error=keyword-macro -I${GOOGLE_BENCHMARK_DIR}/include"
    ninja -t compdb > compile_commands.json  # Generate compilation database
  fi

  if [[ ! -f "compile_commands.json" ]]; then
    echo "Error: compile_commands.json was not created."
    exit 1
  else
    echo "compile_commands.json was successfully created."
  fi
  echo "Build successful."
}

build_dawn() {
    mkdir -p "${dawn_root_directory}/out/Debug" && cd "${dawn_root_directory}/out/Debug" || exit 1  # Create build directory and move into it
    build_dawn_aux
    cd ../..
}

# ---------------------------------------------------------------------------------------------------------

type="normal"

echo "Validating --dawn_type..."

if [[ "$1" == --dawn_type=* ]]; then
  dawn_type="${1#*=}"
  if [[ "$dawn_type" == "normal" || "$dawn_type" == "meta_mutant" || "$dawn_type" == "mutant_tracking" ]]; then
    type="$dawn_type"
  else
    echo "Invalid value for --dawn_type. Allowed values are 'normal', 'meta_mutant', 'mutant_tracking'."
    usage
  fi
else
  echo "Missing or incorrect option."
  usage
fi

echo "The type is set to: $type"

echo "Setting and validating environment variables..."

dawn_repo_name="dawn_$type"
fleshtest_root="/Users/maxmitchell/Documents/msc-control-flow-fleshing-project"
mutation_testing_directory="${fleshtest_root}/evaluation/mutation_testing"
dawn_root_directory="/Users/maxmitchell/${dawn_repo_name}"

source ${mutation_testing_directory}/shell_scripts/setup_dredd_environment.sh  # Load the Dredd environment

echo "Rebuilding Dawn, now with the mutations / tracking..."
build_dawn


cd out/Debug || exit 1
ninja -k 3000000 dawn.node || exit 1

echo "Success!"