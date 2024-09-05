import os
from enum import Enum

from languages import Language

from my_common.CodeType import CodeType


class FileType(Enum):
    CFG = 'cfg'
    DIRECTIONS = 'directions'
    PROGRAM_CLASS = 'program_class'
    CODE = 'code'
    BUG_REPORT = 'bugs'

    def get_filepath(self, base_path: str) -> str:
        """Returns the file path associated with the FileType."""
        return f"{base_path}/{self.value}"


class TestDirectories:
    def __init__(self, base_path: str, make_dir: bool = True):
        self._base_path = base_path
        self._cfg_filepath = FileType.CFG.get_filepath(base_path)
        self._directions_filepath = FileType.DIRECTIONS.get_filepath(base_path)
        self._program_filepath = FileType.PROGRAM_CLASS.get_filepath(base_path)
        self._code_filepath = FileType.CODE.get_filepath(base_path)
        self._bugs_filepath = FileType.BUG_REPORT.get_filepath(base_path)
        if make_dir:
            self.make_directories()

    def __iter__(self):
        yield self.cfg_filepath
        yield self.directions_filepath
        yield self.program_filepath
        yield self.code_filepath
        yield self.bugs_filepath

    @property
    def base_path(self):
        return self._base_path

    @property
    def cfg_filepath(self):
        return self._cfg_filepath

    @property
    def directions_filepath(self):
        return self._directions_filepath

    @property
    def program_filepath(self):
        return self._program_filepath

    @property
    def code_filepath(self):
        return self._code_filepath

    @property
    def bugs_filepath(self):
        return self._bugs_filepath

    @staticmethod
    def file_name(file_type: FileType, graph_ix: int, code_type: CodeType = None,
                  direction_ix: int = None, language: Language = None) -> str:

        if code_type == CodeType.HEADER_GUARD:
            assert direction_ix is not None
        if file_type is FileType.PROGRAM_CLASS:
            if direction_ix is not None:
                return f'{file_type.value}_{graph_ix}_direction_{direction_ix}.pickle'
            else:
                return f'{file_type.value}_{graph_ix}.pickle'
        elif file_type is FileType.CODE:
            assert Language is not None
            if code_type is CodeType.GLOBAL_ARRAY:
                return f'{file_type.value}_{graph_ix}.{language.extension()}'
            else:
                return f'{file_type.value}_{graph_ix}_direction_{direction_ix}.{language.extension()}'
        elif file_type is FileType.DIRECTIONS:
            return f'{file_type.value}_{graph_ix}.pickle'
        elif file_type is FileType.BUG_REPORT:
            return f'{language.extension()}_bug_graph_{graph_ix}_direction_{direction_ix}.txt'
        else:  # file_type == FileType.CFG
            return f'graph_{graph_ix}.pickle'

    def full_path(self, file_type: FileType, graph_ix: int, code_type: CodeType = None, direction_ix: int = None,
                  language: Language = None):
        file_name = self.file_name(file_type, graph_ix, code_type, direction_ix, language)
        return f'{file_type.get_filepath(self.base_path)}/{file_name}'

    def _all_directories_non_existent_or_empty(self) -> bool:
        for directory in self:
            if os.path.exists(directory) and os.listdir(directory):
                return False
        return True

    def make_directories(self):
        if not self._all_directories_non_existent_or_empty():
            raise ValueError("One or more directories already exist and are not empty")
        for directory in self:
            os.makedirs(directory, exist_ok=True)

    def remove_file(self, file_type: FileType, graph_ix: int, direction_ix: int = None, code_type: CodeType = None,
                    language: Language = None):
        os.remove(self.full_path(file_type, graph_ix, code_type, direction_ix, language))
