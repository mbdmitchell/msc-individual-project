import os

import pkg_resources

from GLSL import GLSLProgram

import json
import subprocess
import tempfile


def run_glsl(program: GLSLProgram, input_directions: list[int]) -> bool:

    expected_path = program.cfg.expected_output_path(input_directions)
    shadertrap_test: str = program.generate_shader_test(input_directions, expected_path)

    with tempfile.NamedTemporaryFile(delete=False, suffix='.shadertrap') as temp_file:
        temp_file.write(shadertrap_test.encode('utf-8'))
        shadertrap_test_filepath = temp_file.name

    # Get the absolute path of the config.json file to ensure the correct path is used
    # regardless of the current working directory when the script is run.
    config_path = pkg_resources.resource_filename(__name__, '../config.json')

    with open(config_path, 'r') as config_file:
        config = json.load(config_file)
        shadertrap_exe_filepath = config['SHADERTRAP_PATH']

    result = subprocess.run([shadertrap_exe_filepath, shadertrap_test_filepath], capture_output=True, text=True)

    return result.returncode == 0