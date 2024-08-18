import re
import subprocess
import tempfile

from runner.utils import run_subprocess

def wgsl_output_file_to_list(output_filepath) -> list[int]:
    output_txt = ''
    with open(output_filepath) as f:
        for line in f:
            output_txt += line
    cleaned_txt = re.sub(r'[^\d,]', '', output_txt)
    return [int(x) for x in cleaned_txt.split(',') if x.strip().isdigit()]

def run_wgsl(program, input_directions: list[int] = None, output_filepath: str = None, expected_path: list[int] = None):

    # Use a temporary file if output_filepath is None
    if output_filepath is None:
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_filepath = temp_file.name
            output_filepath = temp_filepath

    command = [
        'node',
        '/Users/maxmitchell/Documents/msc-control-flow-fleshing-project/runner/wgsl/run-wgsl-new.js',
        program.get_file_path()
    ]

    if input_directions is not None:
        # Append 0 to handle edge case where input_directions is empty, ensuring shader uses the input_data binding

        input_directions.append(0)
        command.append(str(input_directions))

    with open(output_filepath, 'w') as output_file:
        subprocess.run(command, stdout=output_file, stderr=subprocess.PIPE, check=True, text=True)

    # Compare the actual output with the expected output
    actual_path = wgsl_output_file_to_list(output_filepath)

    if input_directions is not None and expected_path is None:
        expected_path = program.cfg.expected_output_path(input_directions)

    is_match = actual_path == expected_path
    return is_match, f'Expected: {expected_path}. Actual: {actual_path}'

