#!/bin/bash

usage() {
  echo "Usage: $0 --dawn_type={normal, meta_mutant, mutant_tracking}"
  exit 1
}

build_dawn_aux() {
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
}

build_dawn() {
    mkdir -p "${dawn_root_directory}/out/Debug" && cd "${dawn_root_directory}/out/Debug" || exit 1  # Create build directory and move into it
    build_dawn_aux
    cd ../..
}


mutate() {
  local additional_args="$1"
  ${DREDD_EXECUTABLE} \
    "${additional_args}" \
    -p "${compile_commands}" \
    --mutation-info-file "${mutation_info_json}" \
    "${FILES_TO_MUTATE[@]}" > "${output_log}" 2>&1
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
tint_mutatable_directory="${dawn_root_directory}/src/tint/lang/msl"

source ${mutation_testing_directory}/shell_scripts/setup_dredd_environment.sh  # Load the Dredd environment

if [[ "$type" != "normal" ]]; then
  REQUIRED_VARS=("DREDD_EXECUTABLE" "GOOGLE_BENCHMARK_DIR")
  for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "$(eval echo \$$var)" ]; then
      echo "Error: $var environment variable is not set."
      exit 1
    fi
  done
fi

echo "...Done"

if [ ! -d ~/${dawn_repo_name} ]; then
  git clone https://dawn.googlesource.com/dawn ~/${dawn_repo_name} && cd ~/${dawn_repo_name} || exit 1
else
  cd ~/${dawn_repo_name} || exit 1
  git reset --hard origin
fi

cp scripts/standalone-with-node.gclient .gclient
gclient sync
build_dawn

if [[ "$type" == "normal" ]]; then
  # no mutations needed, just bind to node
  cd out/Debug || exit 1
  ninja dawn.node || exit 1
  exit 0
fi

# mutate tint's .cc files

EXCLUDED_FILE="${tint_mutatable_directory}/writer/writer_bench.cc"  # including it causes fatal error

tmp_file=$(mktemp)
find "${tint_mutatable_directory}" -name '*.cc' -type f -print0 | sort -z > "$tmp_file"

while IFS= read -r -d '' file; do
  if [[ "$file" != "$EXCLUDED_FILE" ]]; then
    FILES_TO_MUTATE+=("$file")
  fi
done < "$tmp_file"

rm "$tmp_file"

echo "Number of files to mutate: ${#FILES_TO_MUTATE[@]}"

# dredd's mutants cause errors. This wraps the files in #pragma directives to supress them
WRAP_SCRIPT_PATH="/Users/maxmitchell/Documents/msc-control-flow-fleshing-project/evaluation/mutation_testing/shell_scripts/wrap_error_causing_cc_files.sh"
for file in "${FILES_TO_MUTATE[@]}"; do
  $WRAP_SCRIPT_PATH "$file"
done

# apply mutation / tracking
output_log="${mutation_testing_directory}/dredd_output_${type}.log"
mutation_info_json="${mutation_testing_directory}/mutant_info_${type}.json"
compile_commands="${dawn_root_directory}/out/Debug/compile_commands.json"

if [[ "$type" == "meta_mutant" ]]; then
  echo "Mutating tint files..."
  mutate ""
else
  echo "Applying mutation tracking to tint files..."
  mutate "--only-track-mutant-coverage"  # apply mutation tracking
fi

echo "Done."

if [ -f "${mutation_info_json}" ]; then
  echo "Mutation info JSON generated successfully."
else
  echo "Error: Mutation info JSON was not generated."
  echo "Check the dredd_output_${type}.log file for details."
  exit 1
fi

# bad syntax...

ADD_BAD_SYNTAX="/Users/maxmitchell/Documents/msc-control-flow-fleshing-project/evaluation/mutation_testing/shell_scripts/DEBUG_SCRIPTS/cc_insert_bad_syntax.sh"
CONFIRMED_TINT_FILES="/Users/maxmitchell/Documents/msc-control-flow-fleshing-project/evaluation/mutation_testing/shell_scripts/DEBUG_SCRIPTS/included_tint_files.txt"

files_to_remove=()
while IFS= read -r line; do
    files_to_remove+=("$line")
done < ${CONFIRMED_TINT_FILES}

# remove files_to_remove
for file in "${files_to_remove[@]}"; do
    FILES_TO_MUTATE=("${FILES_TO_MUTATE[@]/$file}")
done

# Remove empty lines (blank entries) from FILES_TO_MUTATE
mapfile -t FILES_TO_MUTATE < <(printf "%s\n" "${FILES_TO_MUTATE[@]}" | sed '/^$/d')

# Display the remaining files in FILES_TO_MUTATE
echo "Remaining files in FILES_TO_MUTATE:"
for file in "${FILES_TO_MUTATE[@]}"; do
    echo "$file"
done



for file in "${FILES_TO_MUTATE[@]}"; do
  $ADD_BAD_SYNTAX "$file"
done

echo "Done. Now run part_2.sh, checking for build errors"