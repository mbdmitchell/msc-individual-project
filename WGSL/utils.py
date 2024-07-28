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

def run_wgsl(code_filepath, input_directions: list[int], expected_output: list[int], output_filepath):

    # Append 0 to handle edge case where input_directions is empty, ensuring shader uses the input_data binding
    input_directions.append(0)

    dir_arg = str(input_directions)
    abs_path = os.path.abspath(code_filepath)

    # Run the WGSL script with Node.js
    command_successful, msg = run_subprocess(
        command=['node', '/Users/maxmitchell/Documents/msc-control-flow-fleshing-project/runner/wgsl/run-wgsl-new.js', abs_path, dir_arg],
        redirect_output=True,
        output_path=output_filepath
    )
    if not command_successful:
        raise RuntimeError("node run-wgsl command was unsuccessful")

    # Compare the actual output with the expected output
    actual_output = wgsl_output_file_to_list(output_filepath)
    is_match = actual_output == expected_output
    return is_match, f'Expected: {expected_output}. Actual: {actual_output}'

