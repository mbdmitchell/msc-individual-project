from CFG import CFG
from code_builders.ArrayCodeBuilder import ArrayCodeBuilder
from my_common.CodeType import CodeType
from languages import Language


class GlobalArrayCodeBuilder(ArrayCodeBuilder):

    def __init__(self, language: 'Language', cfg: CFG, directions: list[int] = None):
        super().__init__(language, cfg, directions)

    @property
    def code_type(self):
        return CodeType.GLOBAL_ARRAY
