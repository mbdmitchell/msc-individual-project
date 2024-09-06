from __future__ import annotations

from my_common.CodeType import CodeType
from languages.Language import Language


class GLSLLang(Language):

    def __str__(self):
        return 'glsl'

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
        return 'const int {var_name}[] = int[]({values_str});'

    # LANGUAGE PROPERTIES

    @property
    def is_shader_language(self) -> bool:
        return True

    @property
    def allows_switch_fallthrough(self) -> bool:
        return True

    def extension(self, human_readable: bool = False) -> str:
        return 'glsl'

    # CODE

    @property
    def block(self):
        return f"""
        // ------ BLOCK {{n}} -------
        {Language().output_data_array_name}[output_ix] = {{n}};
        output_ix++; 
        // ------------------------
        """

    @staticmethod
    def set_and_increment_control():
        """For array-based CodeType."""
        return f"""
            cntrl_ix++;
            {Language.cntrl_val_var_name()} = {Language().input_data_array_name}[cntrl_ix];
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

    @staticmethod
    def directions_layout_binding():
        return f"layout(std430, binding = 1) buffer directions {{\n\tuint {Language().input_data_array_name}[];\n}};"

    # FULL CODE

    @staticmethod
    def full_program(code_type: CodeType, control_flow_code: str, cntrl_arr_declarations: str = None,
                     is_max_out_degree_lt_two: bool = None, directions: list[int] = None) -> str:

        program_start = f"""
                    #version 450

                    layout(local_size_x=1, local_size_y=1, local_size_z=1) in;

                    layout(std430, binding = 0) buffer actual_path {{
                        uint {Language().output_data_array_name}[];
                    }};
                    """

        if code_type == CodeType.HEADER_GUARD:
            assert cntrl_arr_declarations
            return f"""
                    {program_start}
                    
                    void main() {{
                        int {Language.cntrl_val_var_name()};
                        {cntrl_arr_declarations}
                        {control_flow_code}
                    }}
                    """

        elif code_type.is_array_type():
            return f"""
                {program_start}
                {code_type.if_global(GLSLLang.directions_layout_binding())}
                void main() {{
                    int cntrl_ix = -1; // always incremented before use
                    int output_ix = 0;
                    int {Language.cntrl_val_var_name()};
                    {code_type.if_local(GLSLLang().array_statement(values=directions, arr_name=Language().input_data_array_name))}
                    {control_flow_code}
                }}
                """

        else:
            raise ValueError("Invalid CodeType")

    # SELECTION

    @staticmethod
    def selection_str_pre_format(code_type: CodeType, block: int):
        return f"""
                {GLSLLang().cntrl_assignment_str(code_type, block)};
                if ({Language.cntrl_val_var_name()} == 1) {{{{
                    {{true_block_code}}
                }}}}
                {{possible_else}}
                """

    @staticmethod
    def else_str_pre_format() -> str:
        return """
                else {{
                    {false_block}
                }}
                """

    # SWITCH

    @staticmethod  # TODO: needs better name
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
        return f"""
                {GLSLLang().cntrl_assignment_str(code_type, block)}
                switch ({GLSLLang.cntrl_val_var_name()}) {{{{
                        {{cases}}
                        {{default}}
                    }}}}
                    """

    # LOOP

    @staticmethod
    def loop_str_pre_format(code_type: CodeType, block: int):
        """Odd-ish structures required as loop header block aren't represented as conditional expressions."""

        if code_type == CodeType.HEADER_GUARD:
            i: str = GLSLLang.loop_ix_name(block)
            placeholder = GLSLLang.placeholder(block)
            return f"""
                        for (int {i} = 0; {i} <= {placeholder}; ++{i}) {{{{
                            {{loop_header}}
                            if ({i} == {placeholder}) {{{{
                                break;
                            }}}}
                            {{loop_body}}
                        }}}}
                        """

        elif code_type.is_array_type():
            return f"""
                        while (true) {{{{
                            {{loop_header}}
                            {GLSLLang.set_and_increment_control()}
                            if ({Language.cntrl_val_var_name()} != 1) {{{{
                                break;
                            }}}}
                            {{loop_body}}
                        }}}}
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
