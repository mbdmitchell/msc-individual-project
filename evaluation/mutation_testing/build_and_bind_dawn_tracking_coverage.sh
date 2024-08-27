#!/bin/zsh

dredd_variant_name="dawn-mutant-tracking"

fleshtest_root="/Users/maxmitchell/Documents/msc-control-flow-fleshing-project"
mutation_testing_directory="${fleshtest_root}/evaluation/mutation_testing"
dawn_mutate_root_directory="/Users/maxmitchell/${dredd_variant_name}"
dawn_affected_directory="${dawn_mutate_root_directory}/src/tint/lang/msl"

source ${mutation_testing_directory}/setup_dredd_environment.sh

build_dawn() { # Function to set up the build directory and generate compile commands

  mkdir -p "${dawn_mutate_root_directory}/out/Debug" && cd "${dawn_mutate_root_directory}/out/Debug" || exit 1  # Create build directory and move into it
  cmake ../.. -G Ninja \
      -DDAWN_BUILD_NODE_BINDINGS=1 \
      -DCMAKE_EXPORT_COMPILE_COMMANDS=ON \
      -DCMAKE_CXX_FLAGS="-I${GOOGLE_BENCHMARK_DIR}/include -Wno-error=keyword-macro -Wno-error=reserved-identifier" \
      -DCMAKE_EXE_LINKER_FLAGS="-L${GOOGLE_BENCHMARK_DIR}/lib -lbenchmark"  # -lbenchmark ensures library is linked during the dawn.node build.
  ninja -t compdb > compile_commands.json  # Generate compilation database
  cd ../.. > /dev/null
}

REQUIRED_VARS=("DREDD_EXECUTABLE" "GOOGLE_BENCHMARK_DIR")
for var in "${REQUIRED_VARS[@]}"; do
  if [ -z "$(eval echo \$$var)" ]; then
    echo "Error: $var environment variable is not set."
    exit 1
  fi
done

git clone https://dawn.googlesource.com/dawn ~/${dredd_variant_name} && cd ~/${dredd_variant_name} || exit 1
cp scripts/standalone-with-node.gclient .gclient
gclient sync

build_dawn

# Get the list of .cc files to apply mutation tracking
FILES_TO_MUTATE=()
while IFS= read -r -d '' file; do
  FILES_TO_MUTATE+=("$file")
done < <(find "${dawn_affected_directory}" -name '*.cc' -type f -print0 | sort -z)

echo "${FILES_TO_MUTATE[@]}"

# Apply mutation tracking using Dredd
${DREDD_EXECUTABLE} --only-track-mutant-coverage \
  -p "${dawn_mutate_root_directory}/out/Debug/compile_commands.json" \
  --mutation-info-file "${mutation_testing_directory}/dawn-mutant-tracking.json" \
  "${FILES_TO_MUTATE[@]}" > "${mutation_testing_directory}/dredd_output.log" 2>&1

# Check if the JSON file was generated
if [ -f "${mutation_testing_directory}/dawn-mutant-tracking.json" ]; then
  echo "Mutation tracking JSON generated successfully."
else
  echo "Error: Mutation tracking JSON was not generated."
  echo "Check the dredd_output.log file for details."
  exit 1
fi

build_dawn

cd out/Debug || exit 1
ninja -k 0 dawn.node || exit 1

echo "Mutation tracking and building completed."