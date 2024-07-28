# CFG -> Program conversion

from __future__ import annotations

from CFG import *

from common.CodeBuilder import CodeBuilder
from common.MergeBlockData import MergeBlockData

class WGSLCodeBuilder(CodeBuilder):

    def __init__(self, cfg: CFG):
        super().__init__(cfg)

    @staticmethod
    def _switch_label(switch_label: str = None) -> str:
        raise ValueError("Shouldn't be here!")

    def _prevent_discarding_bindings(self) -> str:
        """WGSL silently discards bindings not used by the shader, then throws an error because it's missing the binding
        it just threw away.

        This function adds a statement to use the input_data binding iff unused in the shader
        (e.g., A CFG w/ no selection headers)
        """

        is_input_data_unused = all(not self.cfg.is_header_block(node) for node in self.cfg.nodes())

        if is_input_data_unused:
            return "var use_input_data = input_data[0];"
        else:
            return ''

    def _full_program(self, control_flow_code: str):
        """Wrap control_flow_code in the code needed to emit a full compute shader"""
        return """
    @group(0) @binding(0) var<storage, read_write> input_data: array<i32>;
    @group(0) @binding(1) var<storage, read_write> output_data: array<i32>;

    @compute @workgroup_size(1) 
    fn control_flow( @builtin(global_invocation_id) id: vec3u ) {{
        var cntrl_ix: i32 = -1; // always incremented before use
        var output_ix: i32 = 0;
        var cntrl_val: i32;
        
        {prevent_discarding_unused_bindings}
        {control_flow_code}
    }}
    """.format(control_flow_code=control_flow_code,
               prevent_discarding_unused_bindings=self._prevent_discarding_bindings())

    @staticmethod
    def _set_and_increment_control():
        return """
                cntrl_ix++;
                cntrl_val = input_data[cntrl_ix];
                """

    @staticmethod
    def _continue_code() -> str:
        return 'continue;\n'

    @staticmethod
    def _break_code() -> str:
        return """
        cntrl_val = -1;
		continue; // 'break' breaks from switch, not loop. This code works cleaner for the latter.
        """

    @staticmethod
    def _exit_code() -> str:
        return 'return;\n'

    def _get_block(self, n: int) -> str:
        self.added_blocks.add(n)
        return """
        // ------ BLOCK {n} -------
        output_data[output_ix] = {n};
        output_ix++;
        // -----------------------
        """.format(n=n)

    def _switch_code(self,
                     block: int | None,  # TODO: rename to header, no???
                     end_block: int | None,  # TODO: remove end_block from all _n_code functions?!
                     merge_blocks: list[MergeBlockData],
                     switch_label_num: int,
                     next_case_block: int = None) -> str:

        destinations = [d for d in self.cfg.out_edges_destinations(block)]
        default, cases = destinations[-1], destinations[:-1]  # default = last dst, cases = the rest

        def case_str(ix_: int) -> str:

            current_case = cases[ix_]
            next_case = default if ix_ + 1 == len(cases) else cases[ix_ + 1]

            # WGSL doesn't accept switches w/ fallthrough
            assert not self._there_is_path_not_using_loop(block, merge_blocks, current_case, next_case)

            return """
            case {ix}: {{
                {case_code}
            }}
            """.format(ix=ix_,
                       case_code=self.code_in_block_range(
                           block=current_case,
                           end_block=self.cfg.merge_block(block),
                           merge_blocks=merge_blocks,
                           switch_label_num=switch_label_num
                       ))

        def add_cases() -> str:
            cases_ = str()
            for ix in range(len(cases)):
                cases_ += case_str(ix)
            return cases_

        def add_default() -> str:

            end_block_ = self.calc_end_block_for_default(default, merge_blocks, block)

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
        """Odd structure required to represent while(loop_header){loop_body...} as loop
        header block aren't represented as conditional expressions."""

        return """
        {cntrl}
        loop {{
            {loop_header}
            if cntrl_val != 1 {{
                break;
            }}
            {loop_body}
            continuing {{
                if cntrl_val != -1 {{
                    {cntrl}
                }} 
                break if cntrl_val == -1; // way to break out of a loop while in a switch (`break` in a switch just leaves switch)
            }}
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
        from common.utils import format_code
        return format_code(code=code,
                           add_line_above=['@compute'],
                           deliminators=('{', '}'),
                           comment_marker='//')
