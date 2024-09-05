import os
import re
import subprocess
import sys
import tempfile

from my_common import CodeType, load_repo_paths_config


def wgsl_output_file_to_list(output_filepath) -> list[int]:
    cleaned_txt = re.sub(r'[^\d,]', '', _file_to_text(output_filepath))
    return [int(x) for x in cleaned_txt.split(',') if x.strip().isdigit()]


def _file_to_text(output_filepath) -> str:
    output_txt = ''
    with open(output_filepath) as f:
        for line in f:
            output_txt += line
    return output_txt


def tst_shader(shader_filepath: str,
               expected_path: list[int],
               env: dict,
               input_directions: list[int] = None,
               timeout: int = 5):

    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_filepath = temp_file.name
        output_filepath = temp_filepath

    command = [
        'node',
        '/Users/maxmitchell/Documents/msc-control-flow-fleshing-project/runner/wgsl/run-wgsl-new.js',
        shader_filepath
    ]

    code_type = classify_shader_code_type(shader_filepath)

    if code_type is CodeType.GLOBAL_ARRAY:
        assert input_directions is not None
        input_directions.append(0)
        command.append(str(input_directions))

    with open(output_filepath, 'w') as output_file:
        try:
            subprocess.run(
                command,
                stdout=output_file,
                stderr=subprocess.PIPE,
                check=True,
                text=True,
                timeout=timeout,
                env=env
            )
        except subprocess.CalledProcessError as e:
            return False, f"subprocess.CalledProcessError: {e}"
        except FileNotFoundError:
            return False, "FileNotFoundError"
        except Exception as e:
            return False, f"Exception {e}"

    actual_path = wgsl_output_file_to_list(output_filepath)
    is_match = actual_path == expected_path

    if is_match:
        msg = f'Expected & Actual: {expected_path}'
    else:
        msg = f'Expected: {expected_path}.\nActual: {_file_to_text(output_filepath)}'

    return is_match, msg


def classify_shader_code_type(wgsl_shader_filepath: str) -> CodeType:
    """Given shader file path, return the CodeType of the shader"""
    with open(wgsl_shader_filepath, 'r') as file:
        shader_code = file.read()

    compute_position = shader_code.find('@compute')

    if compute_position == -1:
        raise ValueError("'@compute' not found. This function is only intended for compute shaders")

    # NB: only global_array_code has two bindings
    global_condition: bool = '@binding(1)' in shader_code[:compute_position]

    if global_condition:
        return CodeType.GLOBAL_ARRAY
    else:
        return CodeType.LOCAL_ARRAY
