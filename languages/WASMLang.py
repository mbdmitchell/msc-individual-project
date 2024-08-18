from __future__ import annotations

from my_common.CodeType import CodeType
from languages.Language import Language


class WASMLang(Language):

    @staticmethod
    def assign_to_var(var_name: str, value_or_placeholder: int | str):
        return f'(local.set {var_name} (i32.const {str(value_or_placeholder)}))'

    @staticmethod
    def array_declaration_pre_format():
        raise NotImplementedError("Static code option isn't available (yet) for WASM")

    @staticmethod
    def add(*args: str):
        raise NotImplementedError

    @staticmethod
    def multiply(*args: str):
        raise NotImplementedError

    def __str__(self):
        return 'wasm'

    # PROPERTIES

    # language ...

    @property
    def is_shader_language(self) -> bool:
        return False

    @property
    def allows_switch_fallthrough(self) -> bool:
        return True

    def extension(self, human_readable: bool = False) -> str:
        return 'wat' if human_readable else 'wasm'

    # code ...

    @property
    def block(self):
        return """
            ;; ------ BLOCK {n} -------
            (call $store_in_output
                (local.get $output_index)
                (i32.const {n})
            )
            (local.set $output_index
                (call $inc (local.get $output_index))
            )
            ;; ------------------------
            """

    @staticmethod
    def set_and_increment_control() -> str:
        return f"""
                        (local.set $control_index
                            (call $inc (local.get $control_index))
                        )
                        (local.set {WASMLang.cntrl_val_var_name()}
                            (call $calc_cntrl_val (local.get $control_index))
                        )
                        """

    @property
    def continue_code(self) -> str:
        return '(br $while)\n'  # code takes to top of loop

    @property
    def break_code(self) -> str:
        return '(br $comparison)\n'  # code takes to bottom of loop

    @property
    def exit_code(self) -> str:
        return '(return)\n'

    @classmethod
    def cntrl_val_var_name(cls):
        return f'${super().cntrl_val_var_name()}'  # WASM vars must begin with $

    @classmethod
    def cntrl_arr_var_name(cls, block: int) -> str:
        return f'${super().cntrl_arr_var_name(block)}'



    # FULL CODE

    @staticmethod
    def full_program(code_type: CodeType, control_flow_code: str, cntrl_arr_declarations: str = None,
                     is_max_out_degree_lt_two: bool = None, directions: list[int] = None) -> str:

        def func_calc_cntrl_val():
            return """(func $calc_cntrl_val (param $index i32) (result i32)
                                (i32.load
                                    (memory 0)
                                    (call $byte_offset(local.get $index))
                                )
                            )"""

        return f"""(module

                            {code_type.if_global('(import "js" "memory" (memory 0))')}

                            (memory $outputMemory 1)
                            (export "outputMemory" (memory $outputMemory))

                            (global $elem_size i32 (i32.const 4))

                            (func $byte_offset (param $index i32) (result i32)
                                    (i32.mul (local.get $index) (global.get $elem_size))
                            )
                            (func $inc (param $num i32) (result i32)
                                    (i32.add (local.get $num) (i32.const 1))
                            )
                            (func $dec (param $num i32) (result i32)
                                    (i32.sub (local.get $num) (i32.const 1))
                            )
                            {code_type.if_global(func_calc_cntrl_val())}
                            
                            (func $store_in_output (param $index i32) (param $value i32)
                                (i32.store
                                    (memory $outputMemory)
                                    (call $byte_offset (local.get $index))
                                    (local.get $value)
                                )
                            )

                            (func $cf (export "cf")

                                ;; setup

                                (local $output_index i32)
                                {code_type.if_global('(local $control_index i32)')}
                                (local {WASMLang.cntrl_val_var_name()} i32)
                                (local.set $output_index (i32.const 0))
                                {code_type.if_global('(local.set $control_index (i32.const -1)) ;; always incremented before cntrl_val is calculated and used')}

                                ;; control flow code

                                {control_flow_code}

                             )
                        )
                        """

    # SELECTION

    def cntrl_assignment_str(self, code_type: CodeType, block: int):
        if code_type == CodeType.HEADER_GUARD:
            return f'{self.cntrl_val_var_name()} = {self.placeholder(block)};'
        elif code_type == CodeType.GLOBAL_ARRAY:
            return f'{self.set_and_increment_control()}'
        else:
            raise TypeError("Invalid CodeType")

    @staticmethod
    def selection_str_pre_format(code_type: CodeType, block: int):

        return f"""
                {WASMLang().cntrl_assignment_str(code_type, block)}
                (if (i32.eq (local.get {WASMLang.cntrl_val_var_name()}) (i32.const 1))
                    (then
                        {{true_block_code}}
                    )
                        {{possible_else}}
                )"""

    @staticmethod
    def else_str_pre_format() -> str:
        return """
                        (else
                            {false_block}
                        )
                    """

    # SWITCH

    @staticmethod
    def switch_label(switch_label_num: int = None) -> str:
        return f"$switch{switch_label_num}"

    @staticmethod
    def switch_break_label(switch_label_num: int) -> str:
        return f"(br {WASMLang.switch_label(switch_label_num)})"

    @staticmethod
    def switch_case_str_pre_format() -> str:
        return """
                (block
                    {code}
                    ;; Target for (br {ix})
                    {case_code}
                    {possible_switch_break}
                    )
                """

    @staticmethod
    def switch_default_str_pre_format() -> str:
        raise NotImplementedError("NB: Shouldn't need to be called for WASM")

    @staticmethod
    def switch_full_str_pre_format(code_type: CodeType, block: int) -> str:
        raise NotImplementedError("NB: Shouldn't need to be called for WASM")

    @staticmethod
    def build_br_table(cases_: list[int]) -> str:
        """Helper function for representing switch statements in WASM"""
        num_of_cases = len(cases_)

        br_table = ""
        for case in range(num_of_cases):
            br_table += f'{case}\t ;; case == {case} => (br {case})\n'  # add case

        default_br_index = num_of_cases
        br_table += f'{default_br_index}\t ;; default => (br {default_br_index})\n'  # add default

        return br_table

    # LOOP

    @staticmethod
    def loop_str_pre_format(code_type: CodeType, block: int) -> str:
        if code_type == CodeType.HEADER_GUARD:
            raise NotImplementedError

        elif code_type == CodeType.GLOBAL_ARRAY:
            return f"""
                        (block $comparison
                            (loop $while
                                ;; comparison block
                                {{loop_header}}
                                ;; comparison
                                {WASMLang.set_and_increment_control()}
                                (br_if $comparison (i32.eqz (local.get {WASMLang.cntrl_val_var_name()})))              
                                ;; condition TRUE - loop body
                                {{loop_body}}
                                (br $while)
                            )     
                        )
                        ;; condition FALSE - merge block
                        """

        else:
            raise ValueError("Invalid CodeType")

    # CODE FORMATTING

    @staticmethod
    def format_code_(code: str) -> str:
        from my_common.utils import format_code
        return format_code(code=code,
                           add_line_above=[';; setup', ';; control flow code'],
                           deliminators=('(', ')'),
                           comment_marker=';;')



