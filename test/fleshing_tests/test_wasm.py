import os

import pytest
import tempfile

from WAT import WebAssemblyProgram, optimise_wasm
from CFG.CFGGenerator import CFGGenerator
from example_cfgs.example_CFGs import *
from runner.utils import run_subprocess

def tst_wasm(abs_wasm_filepath: str,
              input_directions: list[int],
              expected_output_path: list[int],
              clear_files_after=True):

    directions_path = f'{abs_wasm_filepath.rsplit("/", 1)[0]}/directions.txt'
    output_path = f'{abs_wasm_filepath.rsplit("/", 1)[0]}/output.txt'

    with open(directions_path, 'w') as file:
        file.write(str(input_directions))

    try:
        validate_command = ['wasm-validate', '--enable-multi-memory', abs_wasm_filepath]
        is_valid, validate_output = run_subprocess(validate_command)

        if not is_valid:
            return False, f"Invalid wasm module (`wasm-validate`) {abs_wasm_filepath}"

        is_valid, msg = run_subprocess(
            ['node', '../runner/run_manual_cf.js', abs_wasm_filepath, directions_path],
            output_path,
            redirect_output=True,  # Set to True to use direct redirection
            verbose=True
        )

        if not is_valid:
            return False, msg

        # ... actual & expected output path

        with open(output_path) as f:
            output_txt = f.readline()

        contains_digits = any(char.isdigit() for char in output_txt)

        actual_output_path = [int(x) for x in output_txt.split(",")] if contains_digits else []

        is_match: bool = actual_output_path == expected_output_path
        msg: str = f'Expected: {expected_output_path}. Actual: {actual_output_path}'

        if is_match:
            return True, msg
        else:
            return False, msg

    finally:
        if clear_files_after:
            if os.path.exists(directions_path):
                os.remove(directions_path)
            if os.path.exists(output_path):
                os.remove(output_path)

# TODO: change so each opt level is own test
@pytest.mark.parametrize("cfg", [
    cfg_0(),
    cfg_early_1_continue(),
    cfg_early_2_break(),
    cfg_early_3_continue_and_break_in_switch(),
    cfg_if_1(),
    cfg_if_2(),
    cfg_if_3_nested(),
    cfg_if_4_nested(),
    cfg_if_5_nested(),
    cfg_while_1(),
    cfg_while_2_nested(),
    cfg_switch_1_fallthrough(),
    cfg_switch_2_nofallthrough(),
    cfg_switch_3_mix(),
    cfg_switch_4_with_loop(),
    cfg_switch_5_with_loop_and_fallthrough(),
    cfg_switch_6_nested(),
    cfg_switch_loop_if_combo(),
    cfg_merge_which_is_also_header_1_selection(),
    cfg_merge_which_is_also_header_2_loop()
])
def test_wasm_and_optimisations(cfg, with_optimisations=False):

    input_directions = [cfg.generate_valid_input_directions() for _ in range(10)]
    # todo: cfg.generate_all_valid_input_directions(max_depth=6)

    optimization_options = ["O", "O1", "O2", "O3", "O4", "Os", "Oz"]
    # optimization_options = ["O"]

    with tempfile.TemporaryDirectory() as temp_dir:

        # file location(s)
        wasm_path = os.path.join(temp_dir, 'unoptimised.wasm')
        directions_path = os.path.join(temp_dir, 'directions.txt')

        # file generation
        program = WebAssemblyProgram(cfg)
        program.save(os.path.join(temp_dir, 'unoptimised'), save_as_executable=True)

        for opt in optimization_options:
            optimise_wasm(wasm_path, opt)

        passed = True

        # testing
        for d in input_directions:
            try:

                with open(directions_path, 'w') as temp_file:
                    temp_file.write(str(d))

                expected_output_path = program.cfg.expected_output_path(d)

                # unoptimised wasm test
                match, msg = tst_wasm(wasm_path, d, expected_output_path, clear_files_after=True)
                if not match:
                    passed = False
                    print(msg)

                if with_optimisations:
                    # optimised wasm test(s)
                    for opt in optimization_options:
                        opt_path = os.path.join(temp_dir, f'opt{opt}.wasm')
                        match, msg = tst_wasm(opt_path, d, expected_output_path, clear_files_after=True)
                        if not match:
                            passed = False
                            print(msg)

            finally:
                if os.path.exists(directions_path):
                    os.remove(directions_path)  # Clean up the temporary file

        print(f'{d}, {msg}')

        assert passed

@pytest.mark.parametrize("seed", range(100))
def test_generated_cfgs(seed):

    cfg = CFGGenerator().generate_simple(seed=seed, depth=3, verbose=True)

    try:
        test_wasm_and_optimisations(cfg)
    except AssertionError as e:
        print(f"An assertion error occurred with seed {seed}: {e}")
        assert False



if __name__ == "__main__":
    pytest.main()
