# CFG -> Program conversion

from __future__ import annotations

from CFG import *

from CodeBuilder import CodeBuilder
from MergeBlockData import MergeBlockData
from utils import format_code

class WGSLCodeBuilder(CodeBuilder):

    def __init__(self, cfg: CFG):
        super().__init__(cfg)

    @staticmethod
    def _full_program(control_flow_code: str):
        """Wrap control_flow_code in the code needed to emit a full compute shader"""
        return """
    @group(0) @binding(0) var<storage, read_write> input_data: array<i32>;
    @group(0) @binding(1) var<storage, read_write> output_data: array<i32>;

    @compute @workgroup_size(1) 
    fn control_flow( @builtin(global_invocation_id) id: vec3u ) {{
        var cntrl_ix: i32 = -1; // always incremented before use
        var output_ix: i32 = 0;
        var cntrl_val: i32;
        
        {control_flow_code}
    }}
    """.format(control_flow_code=control_flow_code)

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
        return 'break;\n'

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
        """Odd structure required to represent while(loop_header){loop_body...} as loop
        header block aren't represented as conditional expressions."""

        return """
        while true {{
            {loop_header}
            {cntrl}
            if cntrl_val != 1 {{
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

    def _calc_else_block_code(self, block, merge_blocks, next_case_block, switch_label_num) -> str:
        """Override base class"""

        # when True, the false branch doesn't go straight to merge block
        dst = self.cfg.out_edges_destinations(block)
        false_branch_block = dst[0]
        merge_block = self.cfg.merge_block(block)

        is_if_else_statement = false_branch_block != merge_blocks[0].merge_block

        if not is_if_else_statement:
            return ""

        return self._else_code_str().format(false_block=self.code_in_block_range(
            block=false_branch_block,
            end_block=merge_block,
            merge_blocks=merge_blocks,
            next_case_block=next_case_block,
            switch_label_num=switch_label_num)
        )

    def _selection_code(self,
                        block: int | None,
                        end_block: int | None,
                        merge_blocks: list[MergeBlockData],
                        switch_label_num: int,
                        next_case_block: int = None) -> str:

        true_branch_block = self.cfg.out_edges_destinations(block)[1]
        merge_block = self.cfg.merge_block(block)

        return """
                {cntrl}
                if (cntrl_val == 1) {{
                    {true_block_code}
                }}
                {possible_else}
                """.format(cntrl=self._set_and_increment_control(),
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
        return format_code(code=code,
                           add_line_above=['@compute'],
                           deliminators=('{', '}'),
                           comment_marker='//')
