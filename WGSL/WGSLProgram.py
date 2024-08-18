import os
from typing import Optional

from code_builders import CodeBuilderFactory
from my_common.CodeType import CodeType
from languages import WGSLLang
from my_common.Program import Program
import CFG


class WGSLProgram(Program):
    def __init__(self, cfg: CFG, code_type: CodeType, directions: Optional[list[int]] = None):
        super().__init__(cfg)
        self.code_type = code_type
        self.builder = CodeBuilderFactory.create_builder(WGSLLang(), self.cfg, self.code_type, directions)
        self._code = self.builder.build_code()
        self.language = WGSLLang()

    def save(self, file_path, verbose=False):
        directory = os.path.dirname(file_path)
        if not os.path.exists(directory):
            os.makedirs(directory)

        source_code_path = f"{file_path}.wgsl"

        with open(source_code_path, "w") as file:
            file.write(self.get_code())

        self._file_path = source_code_path

        if verbose:
            print("Saved to {path}".format(path=source_code_path))
