from __future__ import annotations

import os
import CFG

from enum import Enum

from common.Language import Language
from common.Program import Program
from GLSL import GLSLCodeBuilder

def _list_to_space_separated_values(values: list[int]) -> str:
    return ' '.join(map(str, values))

def _generate_shader_test_aux(shader_code, input_directions, expected_path) -> str:

    path_buffer_size = len(expected_path) + 1  # +1 so can detect if somehow actual_path starts identically to expected_path but has extra elems
    path_buffer_size_in_bytes = path_buffer_size * 4  # 32-bit uints
    directions_size_in_bytes = len(input_directions) * 4

    return """GL 4.5

CREATE_BUFFER directions SIZE_BYTES {directions_size_in_bytes} INIT_VALUES uint {directions}

CREATE_BUFFER actual_path SIZE_BYTES {path_size_in_bytes} INIT_VALUES
    uint {buffer_full_of_zeros}

CREATE_BUFFER expected_path SIZE_BYTES {path_size_in_bytes} INIT_VALUES
    uint {expected_path_padded_with_zeros}

BIND_SHADER_STORAGE_BUFFER BUFFER directions BINDING 0
BIND_SHADER_STORAGE_BUFFER BUFFER actual_path BINDING 1

DECLARE_SHADER test_shader KIND COMPUTE
#version 450

layout(local_size_x=1, local_size_y=1, local_size_z=1) in;

layout(std430, binding = 0) buffer inputData {{
  uint directions[];
}};

layout(std430, binding = 1) buffer outputData {{
  uint actual_path[];
}};

{shader_code}

END

COMPILE_SHADER control_flow_compiled SHADER control_flow
CREATE_PROGRAM control_flow_prog SHADERS control_flow_compiled

RUN_COMPUTE
    PROGRAM control_flow_prog
    NUM_GROUPS 1 1 1

ASSERT_EQUAL BUFFERS expected_path actual_path""".format(
        shader_code=shader_code,
        directions_size_in_bytes=directions_size_in_bytes,
        directions=_list_to_space_separated_values(input_directions),
        path_size_in_bytes=path_buffer_size_in_bytes,
        buffer_full_of_zeros=_list_to_space_separated_values([0] * path_buffer_size),
        expected_path_padded_with_zeros=_list_to_space_separated_values(expected_path[:path_buffer_size] + [0] * (path_buffer_size - len(expected_path)))
    )

class GLSLProgram(Program):

    class OutputType(Enum):
        COMP_SHADER = 0,
        SHADER_TEST = 1
    def __init__(self, cfg: CFG):
        super().__init__(cfg)
        self.builder = GLSLCodeBuilder.GLSLCodeBuilder(cfg)
        self._code = self.builder.build_code()
        self.language = Language.GLSL

    def generate_shader_test(self, input_directions, expected_path: list[int] | None = None) -> str:
        # Optional expected_path to allow for generating (intentionally) incorrect shadertrap tests.
        if not expected_path:
            expected_path = self.cfg.expected_output_path(input_directions)
        return _generate_shader_test_aux(
            shader_code=self.get_code(),
            input_directions=input_directions,
            expected_path=expected_path
        )

    def save(self, file_path, output_type: OutputType, input_directions=None, expected_path=None, verbose=False):
        directory = os.path.dirname(file_path)

        if output_type == GLSLProgram.OutputType.SHADER_TEST:
            if not (expected_path and input_directions):
                raise ValueError("input_directions and/or expected_path equals None")

        if not os.path.exists(directory):
            os.makedirs(directory)

        if output_type == GLSLProgram.OutputType.COMP_SHADER:
            file_extension = 'glsl'  # NB: There's no official extension in the GLSL spec.
            file_content = self.get_code()
        elif output_type == GLSLProgram.OutputType.SHADER_TEST:
            file_extension = 'shadertrap'
            file_content = self.generate_shader_test(input_directions, expected_path)
        else:
            raise ValueError("Unsupported output type")

        new_file_path = f"{file_path}.{file_extension}"

        with open(new_file_path, "w") as file:
            file.write(file_content)

        self._file_path = new_file_path

        if verbose:
            print("Saved to {path}".format(path=new_file_path))
