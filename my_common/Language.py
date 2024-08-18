from enum import Enum

class Language(Enum):
    WASM = 'wasm'
    WGSL = 'wgsl'
    GLSL = 'glsl'

    @staticmethod
    def is_shader_language(language: 'Language') -> bool:
        return language != Language.WASM

    @staticmethod
    def allows_switch_fallthrough(language: 'Language') -> bool:
        return language != Language.WGSL

    @staticmethod
    def all_languages() -> list['Language']:
        return list(Language)

    def extension(self, human_readable: bool = False):
        if self == Language.WASM:
            return 'wat' if human_readable else 'wasm'
        elif self == Language.WGSL:
            return 'wgsl'
        elif self == Language.GLSL:
            return 'glsl'
        else:
            raise ValueError("Langauge not supported")

    def __str__(self):
        return self.name