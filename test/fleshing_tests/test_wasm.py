import json
import os
import re
from enum import Enum

import pytest
import tempfile

from WAT import WebAssemblyProgram, optimise_wasm
from CFG.CFGGenerator import CFGGenerator
from WGSL.WGSLProgram import WGSLProgram
from example_cfgs.example_CFGs import *
from runner.utils import run_subprocess

class Language(Enum):
    WASM = 0,
    WGSL = 1

def _validate_wasm(abs_code_filepath, directions_path, output_path):
    validate_command = ['wasm-validate', '--enable-multi-memory', abs_code_filepath]
    is_valid, validate_output = run_subprocess(validate_command)

    if not is_valid:
        return False, f"Invalid wasm module (`wasm-validate`) {abs_code_filepath}"

    return is_valid, ''

def _run_wasm(abs_code_filepath, directions_path, output_path):
    is_valid, msg = run_subprocess(
        ['node', '../runner/run_wasm.js', abs_code_filepath, directions_path],
        output_path,
        redirect_output=True,  # Set to True to use direct redirection
        verbose=True
    )
    return is_valid, msg

def _run_wgsl(abs_code_filepath, directions_path, output_path):
    is_valid, msg = run_subprocess(
        ['node', '../runner/wgsl/run-wgsl-new.js', abs_code_filepath, directions_path],
        output_path,
        redirect_output=True,  # Set to True to use direct redirection
        verbose=True
    )
    return is_valid, msg

def tst_generated_code(language: Language,
                       abs_code_filepath: str,
                       input_directions: list[int],
                       expected_output_path: list[int],
                       clear_files_after=True):

    directions_path = f'{abs_code_filepath.rsplit("/", 1)[0]}/directions.txt'
    output_path = f'{abs_code_filepath.rsplit("/", 1)[0]}/output.txt'

    with open(directions_path, 'w') as file:
        file.write(str(input_directions))

    try:

        if language == Language.WASM:
            validate_func = _validate_wasm
            run_func = _run_wasm
        elif language == Language.WGSL:
            validate_func = None
            run_func = _run_wgsl
        else:
            raise ValueError("Testing code of an unsupported language")


        if validate_func:
            is_valid, msg = validate_func(abs_code_filepath, directions_path, output_path)
        else:
            is_valid, msg = True, 'Validation skipped'

        if not is_valid:
            return is_valid, msg

        # run shader

        is_valid, msg = run_func(abs_code_filepath, directions_path, output_path)

        if not is_valid:
            return False, msg

        # ... actual & expected output path

        output_txt = ''
        with open(output_path) as f:
            for line in f:
                output_txt += line
        cleaned_txt = re.sub(r'[^\d,]', '', output_txt)
        actual_output_path = [int(x) for x in cleaned_txt.split(',') if x.strip().isdigit()]

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
                match, msg = tst_generated_code(Language.WASM, wasm_path, d, expected_output_path, clear_files_after=True)
                if not match:
                    passed = False
                    print(msg)

                if with_optimisations:
                    # optimised wasm test(s)
                    for opt in optimization_options:
                        opt_path = os.path.join(temp_dir, f'opt{opt}.wasm')
                        match, msg = tst_generated_code(Language.WASM, opt_path, d, expected_output_path, clear_files_after=True)
                        if not match:
                            passed = False
                            print(msg)

            finally:
                if os.path.exists(directions_path):
                    os.remove(directions_path)  # Clean up the temporary file

        print(f'{d}, {msg}')

        assert passed

@pytest.mark.parametrize("cfg", [
    # cfg_0(),
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
def test_wgsl(cfg):
    # TODO: refactor to remove code dup.
    input_directions = [cfg.generate_valid_input_directions() for _ in range(10)]

    with tempfile.TemporaryDirectory() as temp_dir:

        # file location(s)
        wgsl_path = os.path.join(temp_dir, 'shader.wgsl')
        directions_path = os.path.join(temp_dir, 'directions.txt')

        # file generation
        program = WGSLProgram(cfg)
        program.save(os.path.join(temp_dir, 'shader'))

        passed = True

        # testing
        for d in input_directions:
            try:

                # with open(directions_path, 'w') as temp_file:
                #     temp_file.write(str(d))

                expected_output_path = program.cfg.expected_output_path(d)

                match, msg = tst_generated_code(Language.WGSL, wgsl_path, d, expected_output_path, clear_files_after=True)
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

    cfg = CFGGenerator().generate_simple(seed=seed, depth=3, allow_fallthrough=True, verbose=True)

    try:
        test_wasm_and_optimisations(cfg)
    except AssertionError as e:
        print(f"An assertion error occurred with seed {seed}: {e}")
        assert False



if __name__ == "__main__":
    pytest.main()
