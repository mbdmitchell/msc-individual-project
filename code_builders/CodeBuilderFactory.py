from typing import Optional

from CFG import CFG
from .GlobalArrayCodeBuilder import GlobalArrayCodeBuilder
from .StaticCodeBuilder import StaticCodeBuilder
from my_common import CodeType
from languages import Language


class CodeBuilderFactory:
    @staticmethod
    def create_builder(language: Language, cfg: CFG, code_type: CodeType, directions: Optional[list[int]] = None):
        if code_type == CodeType.GLOBAL_ARRAY:
            return GlobalArrayCodeBuilder(language, cfg)
        elif code_type == CodeType.STATIC:
            return StaticCodeBuilder(language, cfg, directions)
        else:
            raise ValueError(f"Unsupported CodeType: {code_type}")
