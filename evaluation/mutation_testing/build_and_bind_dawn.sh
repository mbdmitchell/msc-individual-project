#!/bin/zsh

source /Users/maxmitchell/Documents/msc-control-flow-fleshing-project/evaluation/mutation_testing/setup_dredd_environment.sh

execute_and_check() {
  $1
  if [ $? -ne 0 ]; then
    echo "Error: $2"
    exit 1
  fi
}

if [ -z "$1" ]; then
  echo "Usage: $0 <repo-name> <make_mutant>"
  echo "Example: $0 my_repo true"
  exit 1
fi

repo_name=$1
make_mutant=$2

if [ "$make_mutant" = "true" ]; then
  execute_and_check ./build_dawn_meta_mutant.sh "$repo_name"
else
  execute_and_check  ./build_dawn.sh "$repo_name"
fi

execute_and_check ./bind_dawn_to_node.sh

echo "Dawn has been successfully built and bound to Node.js."
