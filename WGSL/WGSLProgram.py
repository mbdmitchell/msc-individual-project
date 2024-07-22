import os

from Language import Language
from Program import Program
import CFG
from WGSL import WGSLCodeBuilder

class WGSLProgram(Program):
    def __init__(self, cfg: CFG):
        super().__init__(cfg)
        self.builder = WGSLCodeBuilder.WGSLCodeBuilder(cfg)
        self._code = self.builder.build_code()
        self.language = Language.WGSL

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
