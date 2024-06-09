import subprocess


def optimise(unoptimised_wasm_filepath: str, opt_option: str, verbose=False):
    """Generate optimised wasm binary"""

    if opt_option not in {"O", "O1", "O2", "O3", "O4", "Os", "Oz"}:
        raise ValueError("Invalid opt_option")

    output_filepath = f"./opt{opt_option}.wasm"

    command = [
        "/opt/homebrew/Cellar/binaryen/117/bin/wasm-opt",  # TODO <- eww
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