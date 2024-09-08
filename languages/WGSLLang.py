from __future__ import annotations

from my_common.CodeType import CodeType
from languages.Language import Language


class WGSLLang(Language):

    def __str__(self):
        return 'wgsl'

    @staticmethod
    def add(*args: str):
        return ' + '.join(args)

    @staticmethod
    def multiply(*args: str):
        return ' * '.join(args)

    @staticmethod
    def assign_to_var(var_name: str, value_or_placeholder: int | str):
        return f'{var_name} = {value_or_placeholder};'

    @staticmethod
    def array_declaration_pre_format():
        return 'const {var_name} = array<i32, {size}>({values_str});'

    # LANGUAGE PROPERTIES

    @property
    def is_shader_language(self) -> bool:
        return True

    @property
    def allows_switch_fallthrough(self) -> bool:
        return False

    def extension(self, human_readable: bool = False) -> str:
        return 'wgsl'

    # CODE

    @property
    def block(self):
        return """
            // ------ BLOCK {n} -------
            output_data[output_ix] = {n};
            output_ix++;
            // ------------------------
            """

    @staticmethod
    def set_and_increment_control() -> str:
        return f"""
                cntrl_ix++;
                {Language.cntrl_val_var_name()} = input_data[cntrl_ix];
                """

    @property
    def continue_code(self) -> str:
        return 'continue;\n'

    @property
    def break_code(self) -> str:
        return f"""
        {Language.cntrl_val_var_name()} = -1;
        continue; // 'break' breaks from switch, not loop. This code works cleaner for the latter.
        """

    @property
    def exit_code(self) -> str:
        return 'return;\n'

    # FULL CODE

    @staticmethod
    def full_program(code_type: CodeType, control_flow_code: str, cntrl_arr_declarations: str = None,
                     is_max_out_degree_lt_two: bool = None, directions: list[int] = None) -> str:
        """
        NB: is_max_out_degree_lt_two needed as WGSL silently discards bindings not used by the shader, then throws an
        error because it's missing the binding it just threw away.
        """

        # is_directions_buffer_used = is_max_out_degree_lt_two

        # Only needed for WGSL
        if code_type == CodeType.GLOBAL_ARRAY:
            prevent_discarding_unused_bindings = "var use_input_data = input_data[0];\n"  # TODO: if is_directions_buffer_used else ''
        else:
            prevent_discarding_unused_bindings = ''

        if code_type == CodeType.HEADER_GUARD:
            return f"""
        @group(0) @binding(0) var<storage, read_write> output_data: array<i32>;
        @group(0) @binding(1) var<storage, read_write> input_data: array<i32>;

        @compute @workgroup_size(1) 
        fn control_flow( @builtin(global_invocation_id) id: vec3u ) {{
            var output_ix: i32 = 0;
            var {Language.cntrl_val_var_name()}: i32;
            {cntrl_arr_declarations}
            {prevent_discarding_unused_bindings}{control_flow_code}
        }}
        """
        elif code_type.is_array_type():
            return f"""
        @group(0) @binding(0) var<storage, read_write> output_data: array<i32>;
        {code_type.if_global('@group(0) @binding(1) var <storage, read_write> input_data: array<i32>;')}

        @compute @workgroup_size(1) 
        fn control_flow( @builtin(global_invocation_id) id: vec3u ) {{
            var cntrl_ix: i32 = -1; // always incremented before use
            var output_ix: i32 = 0;
            var {Language.cntrl_val_var_name()}: i32; // assigned prior to use
            {code_type.if_local(WGSLLang().array_statement(values=directions, arr_name=WGSLLang().input_data_array_name))}
            {prevent_discarding_unused_bindings}{control_flow_code}
        }}
        """
        else:
            raise ValueError("Invalid CodeType")

    # SELECTION

    @staticmethod
    def selection_str_pre_format(code_type: CodeType, block: int) -> str:
        return f"""
            {WGSLLang().cntrl_assignment_str(code_type, block)}
            if ({Language.cntrl_val_var_name()} == 1) {{{{
                {{true_block_code}}
            }}}}
            {{possible_else}}"""

    @staticmethod
    def else_str_pre_format() -> str:
        return """
                else {{
                    {false_block}
                }}
                """

    # SWITCH

    @staticmethod
    def switch_label(switch_label_num: int = None) -> str:
        return ''

    @staticmethod
    def switch_case_str_pre_format() -> str:
        return """
                case {ix}: {{
                    {case_code}
                }}
                """

    @staticmethod
    def switch_default_str_pre_format() -> str:
        return """
                default: {{
                    {default_code}
                }}
                """

    @staticmethod
    def switch_full_str_pre_format(code_type: CodeType, block: int) -> str:
        return f"""
                {WGSLLang().cntrl_assignment_str(code_type, block)}
                switch ({WGSLLang.cntrl_val_var_name()}) {{{{
                    {{cases}}
                    {{default}}
                }}}}"""

    # LOOP

    @staticmethod
    def loop_str_pre_format(code_type: CodeType, block: int) -> str:
        """
            Creates a string representation of a while loop in WGSL.

            Due to WGSL's syntax and the representation of CFG blocks in the generated code,
            a `loop` construct with manual control flow checks is used to handle the loop
            header and body.
        """

        if code_type == CodeType.HEADER_GUARD:
            i: str = WGSLLang.loop_ix_name(block)
            placeholder = WGSLLang.placeholder(block)

            return f"""
                    for (var {i} = 0; {i} <= {placeholder}; {i}++) {{{{
                        {{loop_header}}
                        if ({i} == {placeholder}) {{{{
                            break;
                        }}}}
                        {{loop_body}}
                    }}}}
                    """

        elif code_type.is_array_type():
            return f"""
                        {WGSLLang().cntrl_assignment_str(code_type, block)}
                        loop {{{{
                            {{loop_header}}
                            if {Language.cntrl_val_var_name()} != 1 {{{{
                                break;
                            }}}}
                            {{loop_body}}
                            continuing {{{{
                                if {Language.cntrl_val_var_name()} != -1 {{{{
                                    {WGSLLang.set_and_increment_control()}
                                }}}}
                                break if {Language.cntrl_val_var_name()} == -1; // way to break out of a loop while in a switch (`break` in a switch just leaves switch)
                            }}}}
                        }}}}
                    """
        else:
            raise ValueError("Invalid CodeType")

    # CODE FORMATTING

    @staticmethod
    def format_code_(code: str) -> str:
        from my_common.utils import format_code
        return format_code(code=code,
                           add_line_above=['@compute'],
                           deliminators=('{', '}'),
                           comment_marker='//')
