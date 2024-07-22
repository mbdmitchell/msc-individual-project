from enum import Enum

class Language(Enum):
    WASM = 0
    WGSL = 1
    GLSL = 2

    @staticmethod
    def is_shader_language(language: 'Language') -> bool:
        return language != Language.WASM

    @staticmethod
    def allows_switch_fallthrough(language: 'Language') -> bool:
        return language != Language.WGSL

    @staticmethod
    def all_languages() -> list['Language']:
        return list(Language)

    def __str__(self):
        return self.name