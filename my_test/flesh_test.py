import os
import random
from itertools import product
import pytest
import tempfile

import GLSL
import WASM
import WGSL

from CFG import CFGGenerator
from CFG.CFGGenerator import GeneratorConfig
from .cfg_utilities import all_cfg_and_language_combos
from common import Language, generate_program, save_program

def tst_generated_code(program,
                       input_directions: list[int],
                       config,
                       clear_files_after=True):

    language = program.get_language()
    code_filepath = program.get_file_path()

    output_filepath = f'{code_filepath.rsplit("/", 1)[0]}/output.txt'

    try:

        # VALIDATE
        if language == Language.WASM:
            is_command_successful, msg = WASM.validate_wasm(code_filepath)
            if not is_command_successful:
                return is_command_successful, msg

        # RUN
        if language == Language.WASM:
            is_match, msg = WASM.run_wasm(program, input_directions, output_filepath)
        elif language == Language.WGSL:
            is_match, msg = WGSL.run_wgsl(program, input_directions, output_filepath)
        elif language == Language.GLSL:
            is_match, msg = GLSL.run_glsl(program, input_directions, config)

        return is_match, msg

    finally:
        if clear_files_after:
            if os.path.exists(output_filepath):
                os.remove(output_filepath)


def test_direction(program, direction):
    match, msg = tst_generated_code(program,
                                    direction,
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

    cfg = CFGGenerator(generator_config=GeneratorConfig.allow_all(language)).generate(4, 3, 5)

    test_cfg(cfg, language)
    tested_configs.add((seed, language))


if __name__ == "__main__":
    pytest.main()
