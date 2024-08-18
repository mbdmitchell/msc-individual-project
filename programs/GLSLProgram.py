from __future__ import annotations

import logging
import os
from typing import Optional

import CFG

from enum import Enum

from languages import GLSLLang
from programs.Program import Program
from my_common.CodeType import CodeType
from code_builders import CodeBuilderFactory


def _list_to_space_separated_values(values: Optional[list[int]]) -> str:

    if not values:
        return ''

    logging.debug("VALUES:", values)
    return str(' '.join(map(str, values)))


def _generate_shader_test_aux(shader_code: str, code_type: CodeType, input_directions=Optional[list[int]],
                              expected_path=list[int]) -> str:
    def if_global(string: str):
        return string if code_type == CodeType.GLOBAL_ARRAY else ''

    # +1 so can detect if somehow actual_path starts identically to expected_path but has extra elems
    path_buffer_size = len(expected_path) + 1

    path_buffer_size_in_bytes = path_buffer_size * 4  # 32-bit uints
    directions_size_in_bytes = 0 if not input_directions else len(input_directions) * 4

    directions_array_buffer = f"CREATE_BUFFER directions SIZE_BYTES {directions_size_in_bytes} INIT_VALUES uint {_list_to_space_separated_values(input_directions)}\n\n"
    directions_binding = "BIND_SHADER_STORAGE_BUFFER BUFFER directions BINDING 1\n"
    buffer_full_of_zeros = _list_to_space_separated_values([0] * path_buffer_size)

    expected_path_padded_with_zeros = _list_to_space_separated_values(
        expected_path[:path_buffer_size] + [0] * (path_buffer_size - len(expected_path))  # TODO: Figure how remove incorrect warning
    )

    return f"""GL 4.5

CREATE_BUFFER actual_path SIZE_BYTES {path_buffer_size_in_bytes} INIT_VALUES
    uint {buffer_full_of_zeros}

{if_global(directions_array_buffer)}CREATE_BUFFER expected_path SIZE_BYTES {path_buffer_size_in_bytes} INIT_VALUES
    uint {expected_path_padded_with_zeros}

BIND_SHADER_STORAGE_BUFFER BUFFER actual_path BINDING 0
{if_global(directions_binding)}
DECLARE_SHADER control_flow KIND COMPUTE

{shader_code}

END

COMPILE_SHADER control_flow_compiled SHADER control_flow
CREATE_PROGRAM control_flow_prog SHADERS control_flow_compiled

RUN_COMPUTE
    PROGRAM control_flow_prog
    NUM_GROUPS 1 1 1

ASSERT_EQUAL BUFFERS expected_path actual_path"""


class GLSLProgram(Program):
    class OutputType(Enum):
        COMP_SHADER = 0,
        SHADER_TEST = 1

    def __init__(self, cfg: CFG, code_type: CodeType, directions: Optional[list[int]] = None):
        super().__init__(cfg)
        self.code_type = code_type
        self.builder = CodeBuilderFactory.create_builder(GLSLLang(), self.cfg, self.code_type, directions)
        self._code = self.builder.build_code()
        self.language = GLSLLang()

    def generate_shader_test(self, input_directions: Optional[list[int]] = None,
                             expected_path: Optional[list[int]] = None) -> str:
        # Optional expected_path to allow for generating (intentionally) incorrect shadertrap tests.
        # Optional input_directions as not needed for CodeType.STATIC programs as path is built in to the code
        if self.code_type == CodeType.GLOBAL_ARRAY:

            if not input_directions:
                raise ValueError("Missing input_directions")

        elif self.code_type == CodeType.HEADER_GUARD:

            if not (expected_path or input_directions):
                raise ValueError("Need either expected_path or input_directions to generate shader test")

        if not expected_path:
            expected_path = self.cfg.expected_output_path(input_directions)
        return _generate_shader_test_aux(
            shader_code=self.get_code(),
            code_type=self.code_type,
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
