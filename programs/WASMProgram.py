from __future__ import annotations

import os
import shutil
import subprocess
from typing import Optional

from code_builders import CodeBuilderFactory
from languages import WASMLang
from my_common.CodeType import CodeType
from programs.Program import Program
import CFG


class WASMProgram(Program):
    def __init__(self, cfg: CFG, code_type: CodeType, directions: Optional[list[int]] = None):
        super().__init__(cfg)
        self.code_type = code_type
        self.builder = CodeBuilderFactory.create_builder(WASMLang(), self.cfg, self.code_type, directions)
        self._wat_code = self.builder.build_code()
        self.language = WASMLang()

    @staticmethod
    def compile(source_code_path, target_binary_path):
        subprocess.run(["wat2wasm", "--enable-multi-memory", source_code_path, "-o", target_binary_path])

    def get_code(self) -> str:
        return self._wat_code

    def save(self, file_path: str, save_as_executable: bool = True, opt_level: Optional[str] = None, verbose=False):

        directory = os.path.dirname(os.path.abspath(file_path))
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

            if opt_level:
                self.optimise(opt_level, store_at_filepath=binary_path)

            if not source_code_file_already_existed:
                os.remove(source_code_path)

            self._file_path = binary_path

        if verbose:
            print("Saved to {path}".format(path=binary_path if save_as_executable else source_code_path))

    def optimise(self, opt_level: str, store_at_filepath: Optional[str] = None) -> bytes | None:
        """Optimize the wasm file. If store_at_filepath is None, print to stdout."""

        if opt_level not in ["O", "O1", "O2", "O3", "O4", "Os", "Oz"]:
            raise ValueError("Invalid opt_level")

        self.save("./temppath", save_as_executable=True)

        # Run wasm-opt command
        subprocess.run(["wasm-opt", "--enable-multimemory", "./temppath.wasm", f"-{opt_level}", "-o",
                        "temppath.wasm"], check=True)

        if store_at_filepath:
            shutil.copy("./temppath.wasm", store_at_filepath)
            os.remove("./temppath.wasm")
            return None
        else:
            with open("./temppath.wasm", "rb") as f:
                content = f.read()
            os.remove("./temppath.wasm")
            return content
