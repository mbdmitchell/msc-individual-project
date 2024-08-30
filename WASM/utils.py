import logging
import os
import re
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


def run_wasm(program, input_directions, output_filepath: str = None):

    code_filepath = program.get_file_path()
    expected_output = program.cfg.expected_output_path(input_directions)

    with tempfile.NamedTemporaryFile(delete=False, mode='w', suffix='.txt') as temp_file:
        temp_file.write(str(input_directions))
        temp_filepath = temp_file.name

    # Use a temporary file if output_filepath is None
    if output_filepath is None:
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_filepath = temp_file.name
            output_filepath = temp_filepath

    is_valid, msg = run_subprocess(
        ['node', './runner/run_wasm.js', code_filepath, temp_filepath, output_filepath]
    )

    if not is_valid:
        return False, msg

    output_txt = ''
    with open(output_filepath) as f:
        for line in f:
            output_txt += line
    cleaned_txt = re.sub(r'[^\d,]', '', output_txt)
    actual_output = [int(x) for x in cleaned_txt.split(',') if x.strip().isdigit()]

    is_wasm_match: bool = actual_output == expected_output
    msg: str = f'Expected: {expected_output}. Actual: {actual_output}'

    return is_wasm_match, msg


