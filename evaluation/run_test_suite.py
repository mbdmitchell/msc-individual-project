import os
import pickle
import re
import subprocess

from tqdm import tqdm

import WGSL.utils
from evaluation.mutation_testing.utils import get_non_visitable_mutant_ids
from my_common import CodeType


program_directions = list[list[int]]  # all directions to test for, say, a global_array program

evaluation_root = '/Users/maxmitchell/Documents/msc-control-flow-fleshing-project/evaluation'
wgsl_test_suite_root = os.path.join(evaluation_root, 'wgsl_test_suite')


def _get_directions_filepaths(code_type: CodeType):
    return sorted(
        [os.path.join(wgsl_test_suite_root, f'{code_type.value}/directions', file) for file in
         os.listdir(os.path.join(wgsl_test_suite_root, f'{code_type.value}/directions'))])


def _get_program_filepaths(code_type: CodeType):
    return sorted(
        [os.path.join(wgsl_test_suite_root, f'{code_type.value}/program_class', file) for file in
         os.listdir(os.path.join(wgsl_test_suite_root, f'{code_type.value}/program_class'))])


def _get_directions(directions_files: list[str]):
    directions: list[program_directions] = []
    for file in directions_files:
        with open(file, 'rb') as f:
            file_contents: program_directions = pickle.load(f)
            directions.append(file_contents)
    return directions


def _calc_correct_input_directions(code_filepath: str) -> list[int]:
    """return correct input directions for CodeType.LOCAL_ARRAY code"""

    if not os.path.isfile(code_filepath):
        raise FileNotFoundError(f"The file {code_filepath} does not exist.")

    with open(code_filepath, 'r') as file:
        content = file.read()

    # find 'input_data' array in code/shader. NB: currently always one array in entire code/shader
    pattern = r'array<i32, \d+>\(([\d,\s]*)\)'

    match = re.search(pattern, content)
    if not match:
        raise ValueError("No matching pattern found in the file.")

    numbers_str = match.group(1)
    directions = [int(num.strip()) for num in numbers_str.split(',') if num.strip().isdigit()]

    return directions


def _passes_tst_suite_x_array_code(env, code_type: CodeType) -> bool:

    program_files: list[str] = _get_program_filepaths(code_type)
    directions_files: list[str] = _get_directions_filepaths(code_type)
    code_directory = os.path.join(wgsl_test_suite_root, f'{code_type.value}/code')

    directions: list[program_directions] = _get_directions(directions_files)

    # for each program...
    for program_ix, program_path in enumerate(tqdm(program_files, desc="Testing programs...")):

        with open(program_path, "rb") as code_file:
                program = pickle.load(code_file)

        filename = os.path.basename(program.get_file_path())
        code_filepath = os.path.join(code_directory, filename)

        if code_type is CodeType.GLOBAL_ARRAY:

            for direction_ix, input_directions in enumerate(
                    tqdm(directions[program_ix], desc="Testing directions for each program...", leave=False, position=1)
            ):
                expected_path = program.cfg.expected_output_path(input_directions)
                is_match, msg = WGSL.utils.tst_shader(code_filepath, expected_path, input_directions, env=env)

                if not is_match:
                    return False

        elif code_type is CodeType.LOCAL_ARRAY:
            input_directions = _calc_correct_input_directions(code_filepath)
            expected_path = program.cfg.expected_output_path(input_directions)
            is_match, msg = WGSL.utils.tst_shader(code_filepath, expected_path, input_directions, env=env)

            if not is_match:
                return False

    return True


def passes_tst_suite(env, mutant_ids: list[int] = None) -> bool:
    if mutant_ids:
        ids_as_string = ','.join(map(str, mutant_ids))
        os.environ['DREDD_ENABLED_MUTATION'] = ids_as_string

    return _passes_tst_suite_x_array_code(env, CodeType.LOCAL_ARRAY) \
        and _passes_tst_suite_x_array_code(env, CodeType.GLOBAL_ARRAY)

def passes_tst_suite_no_mutants(env) -> bool:
    return passes_tst_suite(env)

def passes_tst_suite_all_non_visitable_mutants(env) -> bool:
    mutant_ids = get_non_visitable_mutant_ids()
    return passes_tst_suite(env, mutant_ids)

def ONE_OF() -> bool:
    """For debugging"""

    assert os.environ['DAWN_VARIANT'] == 'mutant_tracking'

    print(os.environ['DREDD_MUTANT_TRACKING_FILE'])

    for code_type in [CodeType.GLOBAL_ARRAY, CodeType.LOCAL_ARRAY]:
        program_files: list[str] = _get_program_filepaths(code_type)
        directions_files: list[str] = _get_directions_filepaths(code_type)
        code_directory = os.path.join(wgsl_test_suite_root, f'{code_type.value}/code')
        directions: list[program_directions] = _get_directions(directions_files)

        program_filepath = program_files[0]
        with open(program_filepath, "rb") as code_file:
                program = pickle.load(code_file)

        filename = os.path.basename(program.get_file_path())
        code_filepath = os.path.join(code_directory, filename)

        if code_type is CodeType.GLOBAL_ARRAY:

            expected_path = program.cfg.expected_output_path(directions[0][0])
            is_match, msg = WGSL.utils.tst_shader(code_filepath, expected_path, directions[0][0])

            if not is_match:
                print(msg)
                return False

        elif code_type is CodeType.LOCAL_ARRAY:

            input_directions = _calc_correct_input_directions(code_filepath)
            expected_path = program.cfg.expected_output_path(input_directions)
            is_match, msg = WGSL.utils.tst_shader(code_filepath, expected_path, input_directions)

            if not is_match:
                return False

    print(os.environ['DREDD_MUTANT_TRACKING_FILE'])
    return True

def main():

    assert 'DAWN_VARIANT' in os.environ, "'DAWN_VARIANT' environment variable is not defined."
    assert os.environ['DAWN_VARIANT'] in ['normal', 'mutant_tracking', 'meta_mutant']
    assert 'DREDD_MUTANT_TRACKING_FILE' in os.environ

    print(ONE_OF())
    # print(passes_tst_suite())

if __name__ == '__main__':
    main()
