import os
import random
import re
import sys
from itertools import product

import pytest
import tempfile

import GLSL
import WASM
import WGSL
from CFG.CFGGenerator import CFGGenerator

from common.utils import generate_program, Language, save_program

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from test.cfg_utilities import all_cfg_and_language_combos


# TODO: Refactor so run_wasm and run_wgsl use program as param

def tst_generated_code(program,
                       input_directions: list[int],
                       expected_output: list[int],
                       clear_files_after=True):

    language = program.get_language()
    code_filepath = program.get_file_path()

    directions_filepath = f'{code_filepath.rsplit("/", 1)[0]}/directions.txt'
    output_filepath = f'{code_filepath.rsplit("/", 1)[0]}/output.txt'

    if language == Language.WASM:  # temporarily not focusing on reducing IO / file handling for WASM as not noticeable bottleneck, unlike for WGSL
        with open(directions_filepath, 'w') as file:
            file.write(str(input_directions))

    try:

        # VALIDATE
        if language == Language.WASM:
            is_command_successful, msg = WASM.validate_wasm(code_filepath)
            if not is_command_successful:
                return is_command_successful, msg

        # RUN
        if language == Language.WASM:
            is_valid, msg = WASM.run_wasm(os.path.abspath(code_filepath), os.path.abspath(directions_filepath), os.path.abspath(output_filepath))
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

        elif language == Language.WGSL:
            is_match, msg = WGSL.run_wgsl(code_filepath, input_directions, expected_output, output_filepath)
            return is_match, msg

        elif language == Language.GLSL:
            is_match, msg = GLSL.run_glsl(program, input_directions)
            return is_match, msg

    finally:
        if clear_files_after:
            if os.path.exists(directions_filepath):
                os.remove(directions_filepath)
            if os.path.exists(output_filepath):
                os.remove(output_filepath)


def test_direction(program, direction):
    expected_output = program.cfg.expected_output_path(direction)
    match, msg = tst_generated_code(program,
                                    direction,
                                    expected_output,
                                    clear_files_after=True)
    assert match, msg


@pytest.mark.parametrize("cfg, language", all_cfg_and_language_combos())
def test_cfg(cfg, language):

    # GENERATE INPUT DIRECTIONS

    # TODO: write cfg.generate_n_valid_input_directions(n) taking even spread of paths w/ all guaranteed distinct
    input_directions = [cfg.generate_valid_input_directions(max_length=512) for _ in range(100)]
    # remove duplicates. TODO: Remove once generate_n_valid_input_directions is written
    seen = set()
    unique_inputs = []
    for item in input_directions:
        hashable_item = tuple(item)
        if hashable_item not in seen:
            unique_inputs.append(item)
            seen.add(hashable_item)
    input_directions = unique_inputs

    with tempfile.TemporaryDirectory() as temp_dir:

        if Language.is_shader_language(language):
            program_name = 'shader'
        else:
            program_name = 'program'

        program = generate_program(language, cfg)
        save_program(program, os.path.join(temp_dir, program_name))

        for direction in input_directions:
            test_direction(program, direction)

@pytest.fixture(scope="session")
def tested_configs():
    return set()


@pytest.mark.parametrize("seed,language", list(product(range(10), Language.all_languages())))
def test_generated_cfgs(seed, language, tested_configs):
    if (seed, language) in tested_configs:
        pytest.skip(f"Seed {seed} for language {language} already tested")

    random.seed(seed)

    cfg = CFGGenerator().generate_complex(
        seed=seed,
        depth=4,
        break_continue_probability=1,
        allow_fallthrough=Language.allows_switch_fallthrough(language),
        verbose=True
    )

    test_cfg(cfg, language)
    tested_configs.add((seed, language))


if __name__ == "__main__":
    pytest.main()
