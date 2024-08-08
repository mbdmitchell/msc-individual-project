from my_common import CodeType
from languages.Language import Language


class GLSLLang(Language):

    def __str__(self):
        return 'glsl'

    # PROPERTIES

    # language ...

    @property
    def is_shader_language(self) -> bool:
        return True

    @property
    def allows_switch_fallthrough(self) -> bool:
        return True

    def extension(self, human_readable: bool = False) -> str:
        return 'glsl'

    # code ...

    @property
    def block(self):
        return """
        // ------ BLOCK {n} -------
        outputData[output_ix] = {n};
        output_ix++; 
        // -----------------------
        """

    @property
    def set_and_increment_control(self):
        """For CodeType.STATIC."""
        return f"""
            cntrl_ix++;
            {Language.cntrl_val_var_name()} = inputData[cntrl_ix];
            """

    @property
    def continue_code(self) -> str:
        return 'continue;\n'

    @property
    def break_code(self) -> str:
        return 'break;\n'

    @property
    def exit_code(self) -> str:
        return 'return;\n'

    def array_declaration_pre_format(self):
        return 'const int {var_name}[] = int[]({values_str});'

    # FULL CODE

    @staticmethod
    def full_program(code_type: CodeType, control_flow_code: str, cntrl_arr_declarations: str = None,
                     is_max_out_degree_lt_two: bool = None) -> str:

        if code_type == CodeType.STATIC:
            assert cntrl_arr_declarations
            return f"""
                    void main() {{
                        int {Language.cntrl_val_var_name()};
                        {cntrl_arr_declarations}
                        {control_flow_code}
                    }}
                    """

        elif code_type == CodeType.GLOBAL_ARRAY:
            return f"""
                void main() {{
                    int cntrl_ix = -1; // always incremented before use
                    int output_ix = 0;
                    int {Language.cntrl_val_var_name()};
                    {control_flow_code}
                }}
                """

        else:
            raise ValueError("Invalid CodeType")

    # SELECTION

    @staticmethod
    def selection_str_pre_format(code_type: CodeType, block: int):

        if code_type == CodeType.STATIC:

            placeholder = Language.placeholder(block)

            return f"""
                    {Language.cntrl_val_var_name()} = {placeholder};
                    if ({Language.cntrl_val_var_name()} == 1) {{{{
                        {{true_block_code}}
                    }}}}
                    {{possible_else}}
                    """

        elif code_type == CodeType.GLOBAL_ARRAY:
            return f"""
                    {{cntrl}}
                    if ({Language.cntrl_val_var_name()} == 1) {{
                        {{true_block_code}}
                    }}
                    {{possible_else}}
                    """

        else:
            raise ValueError("Invalid CodeType")

    @staticmethod
    def else_str_pre_format() -> str:
        return """
                else {{
                    {false_block}
                }}
                """

    # SWITCH

    # TODO: below method needs better naming
    @staticmethod
    def switch_label(switch_label_: str = None) -> str:
        return "break;"

    @staticmethod
    def switch_case_str_pre_format() -> str:
        return """
                    case {ix}: {{
                        {case_code}
                        {possible_switch_break}
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
        if code_type == CodeType.STATIC:
            return f"""
                    {Language.cntrl_val_var_name()} = {Language.placeholder(block)}
                    switch ({Language.cntrl_val_var_name()}) {{{{
                        {{cases}}
                        {{default}}
                    }}}}
                    """
        elif code_type == CodeType.GLOBAL_ARRAY:
            return f"""
                    {{cntrl}}
                        switch ({Language.cntrl_val_var_name()}) {{
                        {{cases}}
                        {{default}}
                    }}"""
        else:
            raise ValueError("Invalid CodeType")

    # LOOP

    @staticmethod
    def loop_str_pre_format(code_type: CodeType, block: int):
        """Odd-ish structures required as loop header block aren't represented as conditional expressions."""

        if code_type == CodeType.STATIC:
            i: str = GLSLLang.loop_ix_name(block)
            placeholder = Language.placeholder(block)
            return f"""
                        for (int {i} = 0; {i} < {placeholder}; ++{i}) {{{{
                            {{loop_header}}
                            if ({i} == {placeholder} - 1) {{{{
                                break;
                            }}}}
                            {{loop_body}}
                        }}}}
                        """

        elif code_type == CodeType.GLOBAL_ARRAY:
            return f"""
                        while (true) {{
                            {{loop_header}}
                            {{cntrl}}
                            if ({Language.cntrl_val_var_name()} != 1) {{
                                break;
                            }}
                            {{loop_body}}
                        }}
                        """

        else:
            raise ValueError("Invalid CodeType")

    # CODE FORMATTING

    @staticmethod
    def format_code_(code: str) -> str:
        from my_common.utils import format_code
        return format_code(code=code,
                           add_line_above=['layout', 'void main()'],
                           deliminators=('{', '}'),
                           comment_marker='//')





