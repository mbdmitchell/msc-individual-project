from CFG import CFG
from code_builders.ArrayCodeBuilder import ArrayCodeBuilder
from languages import Language
from my_common import CodeType


class LocalArrayCodeBuilder(ArrayCodeBuilder):

    def __init__(self, language: 'Language', cfg: CFG, directions: list[int] = None):
        super().__init__(language, cfg, directions)

    @property
    def code_type(self):
        return CodeType.LOCAL_ARRAY
