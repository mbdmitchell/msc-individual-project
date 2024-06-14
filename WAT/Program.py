from enum import Enum
import subprocess
import os


class WebAssemblyFormat(Enum):
    WAT = 0,
    WASM = 1


class Program:

    def __init__(self, program_builder: 'ProgramBuilder'):
        """
        Initializes the WATProgram with code from the provided program builder.

        Note: To ensure valid WATProgram, this constructor should only be called
        by WATProgramBuilder. Direct instantiation of WATProgram is not recommended.
        """
        if not isinstance(program_builder, ProgramBuilder):
            raise TypeError("WRONG TYPE")
        if not program_builder.is_built:
            raise ValueError("The provided program builder has not completed building the program.")
        self.code = program_builder.code
        self.cfg = program_builder.cfg
        self.language = 'WAT'

    def get_wat_code(self) -> str:
        """Returns the generated WebAssembly Text (WAT) code."""
        return self.code

    def _is_up_to_date(self, path: str) -> bool:
        try:
            with open(path, "r") as file:
                existing_code = file.read()
            return existing_code == self.code
        except FileNotFoundError:
            return False

    def save(self, file_path: str, fmt: WebAssemblyFormat):
        """
    Generates and manages WebAssembly files based on the specified format.

    This method creates a .wat or .wasm file at the given path. For .wasm files,
    it also converts .wat to .wasm and conditionally removes the .wat file after conversion.

    Parameters:
        file_path (str): Base path for the output file(s), with directories created as needed.
        fmt (WebAssemblyFormat): Specifies the output format (WAT or WASM).

    Raises:
        subprocess.CalledProcessError: If the wat2wasm conversion fails.
        PermissionError: For issues with directory or file access permissions.
    """
        directory = os.path.dirname(file_path)
        if not os.path.exists(directory):
            os.makedirs(directory)

        wat_path = f"{file_path}.wat"
        wasm_path = f"{file_path}.wasm"

        wat_file_already_existed: bool = os.path.exists(wat_path)
        up_to_date: bool = self._is_up_to_date(wat_path)

        if fmt == WebAssemblyFormat.WAT:
            with open(wat_path, "w") as file:
                file.write(self.code)

        elif fmt == WebAssemblyFormat.WASM:
            if not wat_file_already_existed or not up_to_date:
                with open(wat_path, "w") as file:
                    file.write(self.code)

            subprocess.run(["wat2wasm", "--enable-multi-memory", wat_path, "-o", wasm_path])

            if not wat_file_already_existed:
                os.remove(wat_path)


from .ProgramBuilder import ProgramBuilder
