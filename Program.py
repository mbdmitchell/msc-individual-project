# [CFG -> Program]. Can then compile, save, and return the code of Program

from abc import ABC, abstractmethod
from CFG import *

class Program(ABC):
    def __init__(self, cfg):
        self._code = None
        self.cfg = cfg
        self.has_binary_format: bool
        self._file_path = None

    def get_code(self) -> str:
        return self._code

    def _is_up_to_date(self, path: str) -> bool:
        try:
            with open(path, "r") as file:
                existing_code = file.read()
            return existing_code == self._code
        except FileNotFoundError:
            return False

    def get_file_path(self) -> str:
        if not self._file_path:
            raise ValueError("Program hasn't been saved. No filepath")
        else:
            return self._file_path