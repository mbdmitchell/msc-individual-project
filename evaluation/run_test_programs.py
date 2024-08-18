import os
import pickle
import subprocess

from WGSL.utils import wgsl_output_file_to_list
from my_common import load_repo_paths_config
# from my_test import tst_generated_code  # TODO: refactor using tst_generated_code

tests_passed = []
tests_failed = []
config = load_repo_paths_config()

evaluation_root = '/Users/maxmitchell/Documents/msc-control-flow-fleshing-project/evaluation'

program_files = [os.path.join(evaluation_root, 'wgsl_test_programs/program_class', file)
                 for file in os.listdir(os.path.join(evaluation_root, 'wgsl_test_programs/program_class'))]

program_files.sort()

directions_files = [os.path.join(evaluation_root, 'wgsl_test_programs/directions', file)
                    for file in os.listdir(os.path.join(evaluation_root, 'wgsl_test_programs/directions'))]

directions_files.sort()

directions = []
for file in directions_files:
    with open(file, 'rb') as f:
        directions.append(pickle.load(f))

# MUTATE
env = os.environ.copy()
# mutation_values = ','.join(map(str, range(3)))
mutation_values = ''
env['DREDD_ENABLED_MUTATION'] = mutation_values

for program_ix, program_path in enumerate(program_files):

    with open(program_path, "rb") as code_file:
        program = pickle.load(code_file)

    for direction_ix, input_directions in enumerate(directions[program_ix]):

        code_directory = os.path.dirname(program.get_file_path())
        output_filepath = os.path.abspath(os.path.join(code_directory, 'output.txt'))

        program_path = os.path.abspath(program.get_file_path())

        # TEMP FIX for evaluation
        output_filepath = output_filepath.replace('/evaluation/evaluation/', '/evaluation/')
        program_path = program_path.replace('/evaluation/evaluation/', '/evaluation/')

        input_directions.append(0)

        command = [
            'node',
            '/Users/maxmitchell/Documents/msc-control-flow-fleshing-project/runner/wgsl/run-wgsl-new.js',
            program_path,
            str(input_directions)
        ]

        timeout_duration = 5  # seconds

        try:
            with open(output_filepath, 'w') as output_file:
                subprocess.run(command, stdout=output_file, stderr=subprocess.PIPE,
                               check=True, text=True, env=env, timeout=timeout_duration)
        except subprocess.CalledProcessError as e:
            print(f"Command failed with return code {e.returncode}")
            print(f"Error output:\n{e.stderr}")
        except subprocess.TimeoutExpired as e:
            print(f"Command timed out after {timeout_duration} seconds")
            print(f"Partial output:\n{e.stdout}")

        actual_path = wgsl_output_file_to_list(output_filepath)
        expected_path = program.cfg.expected_output_path(input_directions)
        is_match = actual_path == expected_path

        if is_match:
            tests_passed.append((program_ix, direction_ix))
        else:
            tests_failed.append((program_ix, direction_ix))
        print(f'{is_match}: Expected: {expected_path}. Actual: {actual_path}')
