#!/bin/zsh

export DREDD_MUTANT_TRACKING_FILE=/Users/maxmitchell/Documents/msc-control-flow-fleshing-project/evaluation/mutation_testing/visitable_mutants.txt
export DAWN_VARIANT=mutant_tracking
python evaluation/run_test_suite.py