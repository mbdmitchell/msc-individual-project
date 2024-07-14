import subprocess
import os

def optimise_wasm(unoptimised_wasm_filepath: str, opt_option: str, verbose=False):
    """Generate optimised wasm binary"""

    if opt_option not in {"O", "O1", "O2", "O3", "O4", "Os", "Oz"}:
        raise ValueError("Invalid opt_option")

    # Extract directory from the input file path
    directory = os.path.dirname(unoptimised_wasm_filepath)

    # Generate the output file path in the same directory as the input file
    output_filepath = os.path.join(directory, f"opt{opt_option}.wasm")

    command = [
        "/opt/homebrew/Cellar/binaryen/117/bin/wasm-opt",
        "--enable-multimemory",
        unoptimised_wasm_filepath,
        "-o",
        output_filepath,
        f"-{opt_option}"
    ]

    result = subprocess.run(command, capture_output=True, text=True)

    if verbose:
        if result.returncode == 0:
            print(f"Optimization completed successfully. Output file: {output_filepath}")
        else:
            print(f"Optimization failed with return code {result.returncode}")
            print(result.stderr)