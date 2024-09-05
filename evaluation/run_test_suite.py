import argparse
import os
import pickle
import re
import time
import random
from enum import Enum

from tqdm import tqdm

import WGSL.utils
from evaluation.mutation_testing.utils import get_non_visitable_mutant_ids, get_visitable_mutant_ids
from my_common import CodeType


class TestResult(Enum):
    PASS = 0
    FAIL_COMPILER_CRASH = 1
    FAIL_PATH_MISMATCH = 2

    def __str__(self):
        return self.name


program_directions = list[list[int]]  # all directions to test for, say, a global_array program

evaluation_root = '/Users/maxmitchell/Documents/msc-control-flow-fleshing-project/evaluation'


def _get_test_suite_path(is_reduced: bool):
    if is_reduced:
        return os.path.join(evaluation_root, 'wgsl_test_suite_reduced')
    else:
        return os.path.join(evaluation_root, 'wgsl_test_suite')


def _get_directions_filepaths(code_type: CodeType, is_reduced: bool):
    return sorted(
        [os.path.join(_get_test_suite_path(is_reduced=is_reduced), f'{code_type.value}/directions', file) for file in
         os.listdir(os.path.join(_get_test_suite_path(is_reduced=is_reduced), f'{code_type.value}/directions'))])


def _get_program_filepaths(code_type: CodeType, is_reduced: bool):
    return sorted(
        [os.path.join(_get_test_suite_path(is_reduced=is_reduced), f'{code_type.value}/program_class', file) for file in
         os.listdir(os.path.join(_get_test_suite_path(is_reduced=is_reduced), f'{code_type.value}/program_class'))])


def _get_directions(directions_files: list[str]):
    directions: list[program_directions] = []
    for file in directions_files:
        with open(file, 'rb') as f:
            file_contents: program_directions = pickle.load(f)
            directions.append(file_contents)
    return directions


def _fetch_correct_input_directions(code_filepath: str) -> list[int]:
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


def _passes_tst_suite_x_array_code(env, code_type: CodeType, is_reduced: bool) -> TestResult:

    program_files: list[str] = _get_program_filepaths(code_type, is_reduced)
    directions_files: list[str] = _get_directions_filepaths(code_type, is_reduced)
    code_directory = os.path.join(_get_test_suite_path(is_reduced=is_reduced), f'{code_type.value}/code')

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
                is_match, msg = WGSL.utils.tst_shader(code_filepath, expected_path, env, input_directions)

                if not is_match:
                    return TestResult.FAIL_PATH_MISMATCH

        elif code_type is CodeType.LOCAL_ARRAY:
            input_directions = _fetch_correct_input_directions(code_filepath)
            expected_path = program.cfg.expected_output_path(input_directions)
            is_match, msg = WGSL.utils.tst_shader(code_filepath, expected_path, env, input_directions)

            if not is_match:
                return TestResult.FAIL_PATH_MISMATCH

    return TestResult.PASS


def passes_tst_suite(env, is_reduced: bool, mutant_ids: list[int] = None) -> TestResult:
    if mutant_ids:
        ids_as_string = ','.join(map(str, mutant_ids))
        env['DREDD_ENABLED_MUTATION'] = ids_as_string

    try:
        is_pass = _passes_tst_suite_x_array_code(env, CodeType.LOCAL_ARRAY, is_reduced) \
            and _passes_tst_suite_x_array_code(env, CodeType.GLOBAL_ARRAY, is_reduced)
        return is_pass
    except Exception:
        return TestResult.FAIL_COMPILER_CRASH


def passes_tst_suite_no_mutants(env, is_reduced: bool) -> TestResult:
    return passes_tst_suite(env, is_reduced)


def passes_tst_suite_all_non_visitable_mutants(env, is_reduced: bool) -> TestResult:
    mutant_ids = get_non_visitable_mutant_ids()
    return passes_tst_suite(env, is_reduced, mutant_ids)


def main():

    parser = argparse.ArgumentParser(description='For mutant tracking file creation [OPTIONAL].')
    parser.add_argument('--create-mutant-tracking-file', action='store_true', default=False, help='Create a mutant tracking file.')
    parser.add_argument('--reduced-test-suite', action='store_true', default=False, help='Run of the reduced test suite.')
    parser.add_argument('--seed', type=int, default=None, help='Seed for random number generator.')

    args = parser.parse_args()

    if 'DAWN_VARIANT' not in os.environ:
        os.environ['DAWN_VARIANT'] = 'meta_mutant'

    assert os.environ['DAWN_VARIANT'] in ['normal', 'mutant_tracking', 'meta_mutant'], \
        f"Invalid DAWN_VARIANT value: {os.environ['DAWN_VARIANT']}"

    # if user wants mutant tracking file...
    if args.create_mutant_tracking_file:
        os.environ['DAWN_VARIANT'] = 'mutant_tracking'
        assert 'DREDD_MUTANT_TRACKING_FILE' in os.environ, \
            "'DREDD_MUTANT_TRACKING_FILE' must be set when --create-mutant-tracking-file is used."

    if args.seed is not None:
        random.seed(args.seed)

    def random_index(lst):
        return random.randint(0, len(lst) - 1)

    # --------

    env = os.environ.copy()

    time_limit_in_seconds = 2 * 60 * 60  # 2 hours

    print("Running test suite: \n"
          f"\tDAWN_VARIANT: {env['DAWN_VARIANT']}\n"
          f"\tREDUCED_TEST_SUITE: {args.reduced_test_suite}\n"
          f"\tRUNNING FOR: {time_limit_in_seconds//60} minutes\n"
          f"\tSEED: {args.seed}")

    start_time = time.time()
    visitable_mutant_ids = get_visitable_mutant_ids()

    killed_mutants_compiler_crash = []
    killed_mutants_path_mismatch = []
    killed_mutants_unknown_cause = []
    survived_mutants = []

    while time.time() - start_time < time_limit_in_seconds and len(visitable_mutant_ids) > 0:
        mutant_id = visitable_mutant_ids.pop(random_index(visitable_mutant_ids))

        print(f"Testing mutant {mutant_id}...")
        result: TestResult = passes_tst_suite(env, args.reduced_test_suite, [mutant_id])
        if result is TestResult.PASS:
            print(f"\nMutant {mutant_id} survived")
            survived_mutants.append(mutant_id)
        else:
            print(f"\nMutant {mutant_id} was killed. Cause: {str(result)}")
            if result is TestResult.FAIL_COMPILER_CRASH:
                killed_mutants_compiler_crash.append(mutant_id)
            elif result is TestResult.FAIL_PATH_MISMATCH:
                killed_mutants_path_mismatch.append(mutant_id)
            else:
                killed_mutants_unknown_cause.append(mutant_id)

    print('survived_mutants:', survived_mutants)
    print('killed_mutants_compiler_crash:', killed_mutants_compiler_crash)
    print('killed_mutants_path_mismatch:', killed_mutants_path_mismatch)
    print('killed_mutants_unknown_cause:', killed_mutants_unknown_cause)


if __name__ == '__main__':
    main()
