import subprocess
import tempfile
from programs.GLSLProgram import GLSLProgram


def run_glsl(program: GLSLProgram, input_directions: list[int], config) -> (bool, str):

    expected_path: list[int] = program.cfg.expected_output_path(input_directions)
    shadertrap_test: str = program.generate_shader_test(input_directions, expected_path)

    permanent_filepath = '/homes/mbm22/Documents/modules/msc-project/msc-individual-project/test.shadertrap'

    with open(permanent_filepath, 'w', encoding='utf-8') as file:
        file.write(shadertrap_test)

    shadertrap_exe_filepath = config['SHADERTRAP_PATH']

    result = subprocess.run([shadertrap_exe_filepath, permanent_filepath], capture_output=True, text=True)

    return result.returncode == 0, result.stderr
