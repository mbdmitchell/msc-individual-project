# [CFG -> Program]. Can then compile, save, and return the code of Program

from abc import ABC, abstractmethod
from CFG import *


class Program(ABC):
    def __init__(self, cfg):
        self._code = None
        self.cfg = cfg
        self.has_binary_format: bool

    def get_code(self) -> str:
        return self._code

    def _is_up_to_date(self, path: str) -> bool:
        try:
            with open(path, "r") as file:
                existing_code = file.read()
            return existing_code == self._code
        except FileNotFoundError:
            return False

    @staticmethod
    @abstractmethod
    def compile(source_code_path, target_binary_path):
        pass

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

        else:
            if not source_code_file_already_existed or not up_to_date:
                with open(source_code_path, "w") as file:
                    file.write(self.get_code())

            self.compile(source_code_path, binary_path)

            if not source_code_file_already_existed:
                os.remove(source_code_path)

        if verbose:
            print("Saved to {path}".format(path=binary_path if save_as_executable else source_code_path))