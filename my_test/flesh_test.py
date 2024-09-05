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
from WGSL.utils import tst_shader
from .cfg_utilities import all_cfg_and_language_combos
from my_common import generate_program, save_program, load_repo_paths_config
from languages import Language, WASMLang, WGSLLang, GLSLLang

def tst_generated_code(program,
                       input_directions: list[int],
                       config,
                       clear_files_after=True):

    language = program.get_language()

    # RUN
    if isinstance(language, WASMLang):
        is_match, msg = WASM.run_wasm(program, input_directions)
    elif isinstance(language, WGSLLang):
        code_filepath = os.path.join('/Users/maxmitchell/Documents/msc-control-flow-fleshing-project', program.get_file_path())  # TODO: address underlying issue w/ get_file_path()
        expected_directions = program.cfg.expected_output_path(input_directions)
        try:
            is_match, msg = tst_shader(code_filepath, expected_directions, os.environ.copy(), input_directions)
        except Exception as e:
            return False, f"An error occurred: {e}"


    elif isinstance(language, GLSLLang):
        is_match, msg = GLSL.run_glsl(program, input_directions, config)
    else:
        raise ValueError("Language not handled")

    return is_match, msg


def test_direction(program, direction):
    match, msg = tst_generated_code(program,
                                    direction,
                                    load_repo_paths_config(),
                                    clear_files_after=True)
    assert match, msg


@pytest.mark.parametrize("cfg, language", all_cfg_and_language_combos())
def test_cfg(cfg, language, config):

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

        if language.is_shader_language:
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
def test_generated_cfgs(seed, language, tested_configs, config):
    if (seed, language) in tested_configs:
        pytest.skip(f"Seed {seed} for language {language} already tested")

    random.seed(seed)

    cfg = CFGGenerator(generator_config=GeneratorConfig.allow_all(language)).generate(4, 3, 5)

    test_cfg(cfg, language, config)
    tested_configs.add((seed, language))


if __name__ == "__main__":
    pytest.main()
