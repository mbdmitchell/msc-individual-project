import logging
import os
import subprocess
import tempfile

from runner.utils import run_subprocess


def validate_wasm(code_filepath):
    validate_command = ['wasm-validate', '--enable-multi-memory', os.path.abspath(code_filepath)]
    is_valid, validate_output = run_subprocess(validate_command)

    if not is_valid:
        return False, f"Invalid wasm module (`wasm-validate`) {code_filepath}"

    return is_valid, ''


def optimise_wasm(unoptimised_wasm: str, opt_option: str, output_filepath: str = None, verbose=False):
    """Generate optimised wasm binary"""

    if opt_option not in {"O", "O1", "O2", "O3", "O4", "Os", "Oz"}:
        raise ValueError("Invalid opt_option")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".wasm") as tmp_file:
        tmp_file.write(unoptimised_wasm.encode('utf-8'))
        unoptimised_wasm_filepath = tmp_file.name

    try:
        # If no output_filepath is provided, print to stdout
        if output_filepath is None:
            cmd = ["wasm-opt", "--enable-multimemory", unoptimised_wasm_filepath, f"-{opt_option}"]
        else:
            # Construct the output file path if provided
            cmd = ["wasm-opt", "--enable-multimemory", unoptimised_wasm_filepath, f"-{opt_option}", "-o",
                   output_filepath]

        if verbose:
            logging.info(f"Running command: {' '.join(cmd)}")

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            logging.error(f"Error optimizing {unoptimised_wasm_filepath}: {result.stderr}")
        elif output_filepath is None:
            print(result.stdout)  # Print the output to stdout
        else:
            if verbose:
                print(f"Optimized WASM saved to {output_filepath}")

    finally:
        os.remove(unoptimised_wasm_filepath)


def run_wasm(code_filepath, directions_path, output_path):
    command_successful, msg = run_subprocess(
        ['node', './runner/run_wasm.js', code_filepath, directions_path, output_path]
    )
    return command_successful, msg
