import os
import random
import re
from itertools import product

import pytest
import tempfile
import CFG
import GLSL
import WAT
import WGSL
from CFG.CFGGenerator import CFGGenerator
from GLSL import test_glsl
from cfg_utilities import all_cfg_and_language_combos
from utils import generate_program, Language, save_program


def tst_generated_code(language: Language,
                       code_filepath: str,
                       input_directions: list[int],
                       expected_output: list[int],
                       clear_files_after=True):

    directions_path = f'{code_filepath.rsplit("/", 1)[0]}/directions.txt'
    output_path = f'{code_filepath.rsplit("/", 1)[0]}/output.txt'

    if language == Language.WASM:  # temporarily just focusing on removing IO for WGSL tests as not a noticeable bottleneck for WASM
        with open(directions_path, 'w') as file:
            file.write(str(input_directions))

    try:

        # VALIDATE
        if language == Language.WASM:
            is_command_successful, msg = WAT.validate_wasm(code_filepath)
            if not is_command_successful:
                return is_command_successful, msg

        # RUN
        if language == Language.WASM:
            is_valid, msg = WAT.run_wasm(code_filepath, directions_path, output_path)
            if not is_valid:
                return False, msg
            output_txt = ''
            with open(output_path) as f:
                for line in f:
                    output_txt += line
            cleaned_txt = re.sub(r'[^\d,]', '', output_txt)
            actual_output = [int(x) for x in cleaned_txt.split(',') if x.strip().isdigit()]

            is_wasm_match: bool = actual_output == expected_output
            msg: str = f'Expected: {expected_output}. Actual: {actual_output}'

            return is_wasm_match, msg

        elif language == Language.WGSL:
            # read result from run_wgsl
            is_match, msg = WGSL.run_wgsl(code_filepath, input_directions, expected_output, output_path)
            return is_match, msg

        elif language == Language.GLSL:
            is_match, msg = test_glsl(code_filepath, directions_path, output_path)
            return is_match, msg

    finally:
        if clear_files_after:
            if os.path.exists(directions_path):
                os.remove(directions_path)
            if os.path.exists(output_path):
                os.remove(output_path)


def _test_direction(program, direction):
    expected_output = program.cfg.expected_output_path(direction)
    match, msg = tst_generated_code(program.get_language(),
                                    program.get_file_path(),
                                    direction,
                                    expected_output,
                                    clear_files_after=True)
    assert match, msg


@pytest.mark.parametrize("cfg, language", all_cfg_and_language_combos())
def test_cfg(cfg, language):

    # GENERATE INPUT DIRECTIONS

    # TODO: write cfg.generate_n_valid_input_directions(n) taking even spread of paths w/ all guaranteed distinct
    input_directions = [cfg.generate_valid_input_directions() for _ in range(10)]
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
            _test_direction(program, direction)

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
