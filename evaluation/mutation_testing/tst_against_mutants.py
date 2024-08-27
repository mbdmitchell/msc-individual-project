# NB: Ensure dredd is built prior to running

import logging
import os
import pickle
import subprocess
from typing import Optional

from tqdm import tqdm

from WGSL.utils import run_wgsl
# from pathos.multiprocessing import ProcessingPool as Pool
from testing.TestDirectories import TestDirectories

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("mutation_testing.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def all_tests_pass(_mutant_id: Optional[int], wgsl_test_programs_path: str, env: dict) -> bool:
    env['DREDD_ENABLED_MUTATION'] = '' if _mutant_id is None else str(_mutant_id)

    test_case_directories = [
        directory for directory in os.listdir(wgsl_test_programs_path)
        if not directory.startswith('.')
    ]

    for directory in test_case_directories:

        directory_path = os.path.join(wgsl_test_programs_path, directory)

        test_case_directories = TestDirectories(directory_path, make_dir=False)
        program_class_directory = test_case_directories.program_filepath
        directions_directory = test_case_directories.directions_filepath

        program_class_files = sorted(
            [os.path.join(program_class_directory, file) for file in os.listdir(program_class_directory)]
        )
        directions_files = sorted(
            [os.path.join(directions_directory, file) for file in os.listdir(directions_directory)]
        )

        directions = [pickle.load(open(file, 'rb')) for file in directions_files]

        for program_ix, program_path in enumerate(program_class_files):

            with open(program_path, "rb") as code_file:
                program = pickle.load(code_file)

            for direction_ix, input_directions in enumerate(directions[program_ix]):
                try:
                    shader_full_path = f'{test_case_directories.code_filepath}/{os.path.basename(program.get_file_path())}'
                    # is_match, msg = run_wgsl(program, input_directions, timeout=5, env=env,
                    #                          shader_full_path=shader_full_path)
                    is_match, msg = run_wgsl(program, input_directions, timeout=5, env=env,
                                             shader_full_path=shader_full_path)
                    if not is_match:
                        logger.info(f"Mutant {_mutant_id} killed: Mismatching execution paths. {msg}")
                        return False
                except subprocess.CalledProcessError as e:
                    logger.error(f"Command failed with return code {e.returncode}: {e.stderr}")
                    logger.info(f"Mutant {_mutant_id} killed: {e.stderr}")
                    return False
                except subprocess.TimeoutExpired as e:
                    logger.error(f"Command timed out: {e.stdout}")
                    logger.info(f"Mutant {_mutant_id} killed: Timeout")
                    return False

    return True


def run_test_for_mutant(mutant_id: int, wgsl_test_programs_path: str, env: dict) -> Optional[int]:
    if is_mutant_killed(mutant_id, wgsl_test_programs_path, env):
        return mutant_id
    return None


def is_mutant_killed(_mutant_id: int, wgsl_test_programs_path: str, env: dict):
    return not all_tests_pass(_mutant_id, wgsl_test_programs_path, env)


def main():

    evaluation_root = '/Users/maxmitchell/Documents/msc-control-flow-fleshing-project/evaluation'
    wgsl_test_programs_path = f'{evaluation_root}/wgsl_test_programs'
    env = os.environ.copy()
    num_mutants = 100

    results = []
    for mutant_id in tqdm(range(num_mutants), total=num_mutants):
        logger.info(f"Testing mutant: {mutant_id}")
        result = run_test_for_mutant(mutant_id, wgsl_test_programs_path, env)
        logger.info("Killed" if result is not None else "Survived")
        results.append(result)

    # with Pool() as pool:  # TODO: works via terminal but prints every expected vs actual path msg??
    #     results = list(tqdm(pool.imap(run_test_for_mutant, range(num_mutants),
    #                                  [wgsl_test_programs_path] * num_mutants,
    #                                  [env] * num_mutants),
    #                         total=num_mutants))

    mutants_killed = [mutant_id for mutant_id, result in enumerate(results) if result is not None]
    mutants_survived = [mutant_id for mutant_id in range(num_mutants) if mutant_id not in mutants_killed]

    logger.info(f'Mutants killed: {sorted(mutants_killed)}')
    logger.info(f'Mutants survived: {sorted(mutants_survived)}')

if __name__ == '__main__':
    # multiprocessing.set_start_method('spawn')
    main()
