import os
import re
from runner.utils import run_subprocess

def wgsl_output_file_to_list(output_filepath) -> list[int]:
    output_txt = ''
    with open(output_filepath) as f:
        for line in f:
            output_txt += line
    cleaned_txt = re.sub(r'[^\d,]', '', output_txt)
    return [int(x) for x in cleaned_txt.split(',') if x.strip().isdigit()]

def run_wgsl(program, input_directions: list[int], output_filepath):

    # Append 0 to handle edge case where input_directions is empty, ensuring shader uses the input_data binding
    input_directions.append(0)

    dir_arg = str(input_directions)
    expected_path = program.cfg.expected_output_path(input_directions)

    # Run the WGSL script with Node.js
    command_successful, msg = run_subprocess(
        command=['node',
                 '/Users/maxmitchell/Documents/msc-control-flow-fleshing-project/runner/wgsl/run-wgsl-new.js',
                 program.get_file_path(),
                 dir_arg],
        redirect_output=True,
        output_path=output_filepath
    )
    if not command_successful:
        raise RuntimeError("node run-wgsl command was unsuccessful")

    # Compare the actual output with the expected output
    actual_path = wgsl_output_file_to_list(output_filepath)
    is_match = actual_path == expected_path
    return is_match, f'Expected: {expected_path}. Actual: {actual_path}'

