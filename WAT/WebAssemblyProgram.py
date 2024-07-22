import os
import subprocess

from Language import Language
from Program import Program
import CFG
from WAT import WACodeBuilder


class WebAssemblyProgram(Program):
    def __init__(self, cfg: CFG):
        super().__init__(cfg)
        self.builder = WACodeBuilder.WebAssemblyCodeBuilder(cfg)
        self._code = self.builder.build_code()
        self.language = Language.WASM

    @staticmethod
    def compile(source_code_path, target_binary_path):
        subprocess.run(["wat2wasm", "--enable-multi-memory", source_code_path, "-o", target_binary_path])

    def save(self, file_path: str, save_as_executable: bool, verbose=False):

        directory = os.path.dirname(file_path)
        if not os.path.exists(directory):
            os.makedirs(directory)

        source_code_path = f"{file_path}.wat"
        binary_path = f"{file_path}.wasm"

        source_code_file_already_existed: bool = os.path.exists(source_code_path)
        up_to_date: bool = self._is_up_to_date(source_code_path)

        if not save_as_executable:
            with open(source_code_path, "w") as file:
                file.write(self.get_code())
            self._file_path = source_code_path

        else:
            if not source_code_file_already_existed or not up_to_date:
                with open(source_code_path, "w") as file:
                    file.write(self.get_code())

            self.compile(source_code_path, binary_path)

            if not source_code_file_already_existed:
                os.remove(source_code_path)

            self._file_path = binary_path

        if verbose:
            print("Saved to {path}".format(path=binary_path if save_as_executable else source_code_path))
