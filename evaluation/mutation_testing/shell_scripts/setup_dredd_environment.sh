#!/bin/bash

# NB: run with `source ./setup_dredd_env.sh`

export DREDD_CHECKOUT=/Users/maxmitchell/dredd
export DREDD_CLANG_BIN_DIR=${DREDD_CHECKOUT}/third_party/clang+llvm/bin
export DREDD_EXECUTABLE=${DREDD_CLANG_BIN_DIR}/dredd


export CC="${DREDD_CLANG_BIN_DIR}/clang"
export CXX="${DREDD_CLANG_BIN_DIR}/clang++"
export GOOGLE_BENCHMARK_DIR="/opt/homebrew/opt/google-benchmark/"
echo "Environment setup complete."