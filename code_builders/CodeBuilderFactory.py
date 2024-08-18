from typing import Optional

from CFG import CFG
from .GlobalArrayCodeBuilder import GlobalArrayCodeBuilder
from .HeaderGuardCodeBuilder import HeaderGuardCodeBuilder
from my_common.CodeType import CodeType
from languages import Language
from .LocalArrayCodeBuilder import LocalArrayCodeBuilder


class CodeBuilderFactory:
    @staticmethod
    def create_builder(language: Language, cfg: CFG, code_type: CodeType, directions: Optional[list[int]] = None):
        if code_type == CodeType.GLOBAL_ARRAY:
            return GlobalArrayCodeBuilder(language, cfg, directions)
        elif code_type == CodeType.HEADER_GUARD:
            return HeaderGuardCodeBuilder(language, cfg, directions)
        elif code_type == CodeType.LOCAL_ARRAY:
            return LocalArrayCodeBuilder(language, cfg, directions)
        else:
            raise ValueError(f"Unsupported CodeType: {code_type}")
