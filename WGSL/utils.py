import re
from runner.utils import run_subprocess

def wgsl_output_file_to_list(output_filepath) -> list[int]:
    output_txt = ''
    with open(output_filepath) as f:
        for line in f:
            output_txt += line
    cleaned_txt = re.sub(r'[^\d,]', '', output_txt)
    return [int(x) for x in cleaned_txt.split(',') if x.strip().isdigit()]

def run_wgsl(abs_code_filepath, input_directions: list[int], expected_output: list[int], output_filepath):
    input_directions.append(0)  # <-- Reason: In the rare case when the input_directions is empty (i.e. all CFG blocks
    # out degree == 1), left unaltered, the generated shader doesn't use the input_data binding. As WGSL silently
    # discards bindings not used by the shader (and then throws an error 'cause it's surprised by what it just did...)
    # the WGSLCodeBuilder checks for an unused input_data binding. If unused, it adds an assignment of an (unused)
    # variable to input_data[0] to the shader to circumvent this. Because of this, input_directions requires length 1

    dir_arg = str(input_directions)
    command_successful, msg = run_subprocess(
        command=['node', '../runner/wgsl/run-wgsl-new.js', abs_code_filepath, dir_arg],
        redirect_output=True,
        output_path=output_filepath,
        verbose=True
    )
    if not command_successful:
        raise RuntimeError("node run-wgsl command was unsuccessful")

    actual_output = wgsl_output_file_to_list(output_filepath)
    is_match = actual_output == expected_output
    return is_match, f'Expected: {expected_output}. Actual: {actual_output}'

