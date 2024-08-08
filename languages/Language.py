import argparse
from abc import ABC, abstractmethod

from my_common import CodeType
from languages.LanguageMeta import LanguageMeta


class Language(ABC, metaclass=LanguageMeta):

    @abstractmethod
    def __str__(self):
        pass

    # CLASS METHODS

    @classmethod
    def all_languages(cls):
        """Return all language subclasses."""
        return LanguageMeta.get_languages()

    @classmethod
    def from_str(cls, language_str: str):
        """Find a subclass that matches the string representation. If no match is found, raise an error."""
        for language_class in cls.all_languages():
            if language_class.__name__.upper() == language_str.upper():
                return language_class()

        valid_languages = ', '.join(lang.__name__.lower() for lang in cls.all_languages())
        raise argparse.ArgumentTypeError(
            f"Invalid language: {language_str}. Choose from: {valid_languages}."
        )

    # PROPERTIES

    # language ...

    @property
    @abstractmethod
    def is_shader_language(self) -> bool:
        pass

    @property
    @abstractmethod
    def allows_switch_fallthrough(self) -> bool:
        pass

    @abstractmethod
    def extension(self, human_readable: bool = False) -> str:
        pass

    # code ...

    @property
    @abstractmethod
    def block(self):
        pass

    @property
    @abstractmethod
    def set_and_increment_control(self) -> str:
        pass

    @property
    @abstractmethod
    def continue_code(self) -> str:
        pass

    @property
    @abstractmethod
    def break_code(self) -> str:
        pass

    @property
    @abstractmethod
    def exit_code(self) -> str:
        pass

    @staticmethod
    def loop_ix_name(block):
        return f'ix_{block}'

    @staticmethod
    def placeholder(block: int):
        """For static code skeleton"""
        return f'$${block}$$'

    @staticmethod
    def cntrl_val_var_name():
        return 'cntrl_val'

    @staticmethod
    def cntrl_arr_var_name(block: int):
        return f'cntrl_arr_block_{block}'

    def array_statement(self, block: int, values: list[int]):
        var_name = self.cntrl_arr_var_name(block)
        values_str = ", ".join(map(str, values))
        size = len(values)
        return self.array_declaration_pre_format().format(var_name=var_name,
                                                          values_str=values_str,
                                                          size=size)

    @staticmethod
    @abstractmethod
    def array_declaration_pre_format():
        pass

    # FULL CODE

    @staticmethod
    @abstractmethod
    def full_program(code_type: CodeType, control_flow_code: str, cntrl_arr_declarations: str = None,
                     is_max_out_degree_lt_two: bool = None) -> str:
        """
        is_max_out_degree_lt_two:
        - needed for WGSL. If True, requires some extra code so that it doesn't wrongly remove a buffer
        cntrl_arr_declarations:
        - needed for building the static code
        """
        pass

    # SELECTION

    @staticmethod
    @abstractmethod
    def selection_str_pre_format(code_type: CodeType, block: int) -> str:
        pass

    @staticmethod
    @abstractmethod
    def else_str_pre_format() -> str:
        pass

    # SWITCH

    @staticmethod
    @abstractmethod
    def switch_label(switch_label_num: int = None) -> str:
        """Breaking within a case can sometimes need something other that normal break_code()"""
        pass

    @staticmethod
    @abstractmethod
    def switch_case_str_pre_format() -> str:
        pass

    @staticmethod
    @abstractmethod
    def switch_default_str_pre_format() -> str:
        pass

    @staticmethod
    @abstractmethod
    def switch_full_str_pre_format(code_type: CodeType, block: int) -> str:
        pass

    def switch_full_str(self, code_type: CodeType, case_code: str, default_code: str, block: int) -> str:

        if code_type == CodeType.STATIC:
            return self.switch_full_str_pre_format(CodeType.STATIC, block).format(
                cases=case_code,
                default=default_code
            )
        elif code_type == CodeType.GLOBAL_ARRAY:
            return self.switch_full_str_pre_format(CodeType.GLOBAL_ARRAY, block).format(
                cntrl=self.set_and_increment_control,
                cases=case_code,
                default=default_code
            )
        else:
            raise ValueError("Invalid CodeType")

    # LOOP

    @staticmethod
    @abstractmethod
    def loop_str_pre_format(code_type: CodeType, block: int) -> str:
        pass

    # CODE FORMATTING

    @staticmethod
    @abstractmethod
    def format_code_(code: str) -> str:
        pass


# TODO: Language NotImplementedError











