import subprocess
from Program import Program
import CFG
from WAT import WACodeBuilder


class WebAssemblyProgram(Program):
    def __init__(self, cfg: CFG):
        super().__init__(cfg)
        self.builder = WACodeBuilder.WebAssemblyCodeBuilder(cfg)
        self._code = self.builder.build_code()

    @staticmethod
    def compile(source_code_path, target_binary_path):
        subprocess.run(["wat2wasm", "--enable-multi-memory", source_code_path, "-o", target_binary_path])

    # see Program class for rest of functions
