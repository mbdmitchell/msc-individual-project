import subprocess

import CFG
from CFG import *
from WAT.Program import WebAssemblyFormat
from runner.utils import run_subprocess
from WAT import *
from CFG.example_CFGs import example_cfg_misc

# TODO: Convert to script:
# eg. `./script.py <program_class_file> <optimisation_level> <directions_file> > out.txt`
# (NB TO SELF: '>' redirects stdout externally from the shell)


# ----
input_directions = [[1], [0,1], [2, 1], [2, 0, 1], [2, 0, 0, 0, 0]]

program: Program = ProgramBuilder(example_cfg_misc()).build(with_edge_aggregation=False)
program.save('./unoptimised', WebAssemblyFormat.WASM)
# ----

optimization_options = ["O", "O1", "O2", "O3", "O4", "Os", "Oz"]

for opt in optimization_options:
    optimise("./unoptimised.wasm", opt)

for d in input_directions:

    with open(f'./directions.txt', 'w') as file:
        file.write(str(d))

    for opt in optimization_options:
        run_subprocess(['node', './runner/run_manual_cf.js', f'./opt{opt}.wasm'])

        # ... actual & expected output path

        with open(f'./output.txt') as f:
            output_txt = f.readline()

        expected_output_path = program.cfg.expected_output_path(d)
        actual_output_path = [int(x) for x in output_txt.split(",")]

        # ... display results

        is_match: bool = actual_output_path == expected_output_path

        msg: str = f'{opt}: {is_match}. Directions: {d}. Expected: {expected_output_path}. Actual: {actual_output_path}'
        print(msg)


