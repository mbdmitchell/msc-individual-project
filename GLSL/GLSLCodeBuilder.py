# CFG -> Program conversion

from __future__ import annotations

from CFG import *

from CodeBuilder import CodeBuilder
from MergeBlockData import MergeBlockData


class GLSLCodeBuilder(CodeBuilder):

    def __init__(self, cfg: CFG):
        super().__init__(cfg)

    def _full_program(self, control_flow_code: str) -> str:
        return """
        #version 450

        layout(local_size_x=1, local_size_y=1, local_size_z=1) in;
        
        layout(std430, binding = 0) buffer inputData {{
          uint directions[];
        }};
        
        layout(std430, binding = 1) buffer outputData {{
          uint actual_path[];
        }};
        
        void main() {{
            uint cntrl_ix = -1; // always incremented before use
            uint output_ix = 0;
            uint cntrl_val;
            {control_flow_code}
        }}
        """.format(control_flow_code=control_flow_code)

    @staticmethod
    def _set_and_increment_control():
        return """
                cntrl_ix++;
                cntrl_val = inputData[cntrl_ix];
                """

    @staticmethod
    def _continue_code() -> str:
        return 'continue;\n'

    @staticmethod
    def _break_code() -> str:
        return 'break;\n'

    @staticmethod
    def _exit_code() -> str:
        return 'return;\n'

    def _get_block(self, n: int) -> str:
        self.added_blocks.add(n)
        return """
        // ------ BLOCK {n} -------
        outputData[output_ix] = {n};
        output_ix++;
        // -----------------------
        """.format(n=n)

    @staticmethod
    def _switch_label(switch_label: str = None):
        return "break;"

    def _switch_code(self,
                     block: int | None,  # TODO: remove code duplication between GLSL and WGSLCodeBuilder
                     end_block: int | None,
                     merge_blocks: list[MergeBlockData],
                     switch_label_num: int,
                     next_case_block: int = None) -> str:

        destinations = [d for d in self.cfg.out_edges_destinations(block)]
        default, cases = destinations[-1], destinations[:-1]  # default = last dst, cases = the rest

        def case_str(ix_: int) -> str:
            current_case = cases[ix_]
            next_case = default if ix_ + 1 == len(cases) else cases[ix_ + 1]

            is_fallthrough = self._there_is_path_not_using_loop(block, merge_blocks, current_case, next_case)

            if is_fallthrough:
                end_block_ = next_case
            else:
                end_block_ = self.cfg.merge_block(block)

            return """
            case {ix}: {{
                {case_code}
                {possible_switch_break}
            }}
            """.format(ix=ix_,
                       case_code=self.code_in_block_range(
                           block=current_case,
                           end_block=end_block_,
                           merge_blocks=merge_blocks,
                           switch_label_num=switch_label_num,
                           next_case_block=next_case_block),
                       possible_switch_break=self.switch_break_str(current_case, is_fallthrough))

        def add_cases() -> str:
            cases_ = str()
            for ix in range(len(cases)):
                cases_ += case_str(ix)
            return cases_

        def add_default() -> str:

            # if true, it's not a true merge (in the sense that blocks from other cases can't reach it)
            if default == merge_blocks[-1].merge_block:
                nearest_loop_header = next((b.related_header for b in merge_blocks[-2::-1]
                                            if self.cfg.is_loop_header(b.related_header)), None)

                end_block_ = nearest_loop_header
            else:
                end_block_ = self.cfg.merge_block(block)

            return """
            default: {{
                {default_code}
            }}
            """.format(default_code=self.code_in_block_range(
                block=default,
                end_block=end_block_,
                merge_blocks=merge_blocks,
                switch_label_num=switch_label_num,
                next_case_block=next_case_block))

        return """
            {cntrl}
            switch (cntrl_val) {{
                {cases}
                {default}
            }}""".format(cntrl=self._set_and_increment_control(),
                         cases=add_cases(),
                         default=add_default())

    @staticmethod
    def _loop_code_str() -> str:
        """Odd structure required to represent while(loop_header){loop_body...}
        as loop header block aren't represented as conditional expressions."""

        return """
        while (true) {{
            {loop_header}
            {cntrl}
            if (cntl_val != 1) {{
                break;
            }}
            {loop_body}
        }}
        """

    @staticmethod
    def _else_code_str() -> str:
        return """
            else {{
                {false_block}
            }}"""

    def _selection_str(self, true_branch_block, merge_block, block, merge_blocks, next_case_block, switch_label_num):
        return """
            {cntrl}
            if (cntrl_val == 1) {{
                {true_block_code}
            }}
            {possible_else}""".format(cntrl=self._set_and_increment_control(),
                                      possible_else=self._calc_else_block_code(
                                          block=block,
                                          merge_blocks=merge_blocks,
                                          next_case_block=next_case_block,
                                          switch_label_num=switch_label_num),
                                      true_block_code=self.code_in_block_range(
                                          block=true_branch_block,
                                          end_block=merge_block,
                                          merge_blocks=merge_blocks,
                                          next_case_block=next_case_block,
                                          switch_label_num=switch_label_num)
                                      )

    @staticmethod
    def _format_code(code: str) -> str:
        from utils import format_code
        return format_code(code=code,
                           add_line_above=['layout', 'void main()'],
                           deliminators=('{', '}'),
                           comment_marker='//')
