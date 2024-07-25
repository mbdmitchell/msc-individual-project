# CFG -> Program conversion

from __future__ import annotations

from CFG import *

from CodeBuilder import CodeBuilder
from MergeBlockData import MergeBlockData

import logging

# change level to get debug info
logging.basicConfig(level=logging.CRITICAL,
                    format='%(asctime)s - %(levelname)s - %(message)s')

logger = logging.getLogger('simple_logger')

class WebAssemblyCodeBuilder(CodeBuilder):

    def __init__(self, cfg: CFG):
        super().__init__(cfg)

    @staticmethod
    def _full_program(control_flow_code: str):
        """Wrap control_flow_code in the code needed to emit a full working program"""
        return """(module

            (import "js" "memory" (memory 0))

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
            (func $calc_cntrl_val (param $index i32) (result i32)
                (i32.load
                    (memory 0)
                    (call $byte_offset(local.get $index))
                )
            )
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
                (local $control_index i32)
                (local $control_val i32)
                (local.set $output_index (i32.const 0))
                (local.set $control_index (i32.const -1)) ;; always incremented before cntrl_val is calculated and used

                ;; control flow code

                {control_flow_code}

             )
        )
        """.format(control_flow_code=control_flow_code)

    @staticmethod
    def _set_and_increment_control():
        return """
            (local.set $control_index
                (call $inc (local.get $control_index))
            )
            (local.set $control_val
                (call $calc_cntrl_val (local.get $control_index))
            )
            """

    @staticmethod
    def _continue_code() -> str:
        return '(br $while)\n'  # code takes to top of loop

    @staticmethod
    def _break_code() -> str:
        return '(br $comparison)\n'  # code takes to bottom of loop

    @staticmethod
    def _exit_code() -> str:
        return '(return)\n'

    def _get_block(self, n: int) -> str:
        self.added_blocks.add(n)
        return """
        ;; ------ BLOCK {n} -------
        (call $store_in_output
            (local.get $output_index)
            (i32.const {n})
        )
        (local.set $output_index
            (call $inc (local.get $output_index))
        )
        ;; -----------------------
        """.format(n=n)

    # ------------------------------------------------------------------------------------------------------------------

    @staticmethod
    def _loop_code_str() -> str:
        return """
            (block $comparison
                (loop $while
                    ;; comparison block
                    {loop_header}
                    ;; comparison
                    {cntrl}
                    (br_if $comparison (i32.eqz (local.get $control_val)))              
                    ;; condition TRUE - loop body
                    {loop_body}
                    (br $while)
                )     
            )
            ;; condition FALSE - merge block
            """

    @staticmethod
    def _else_code_str() -> str:
        return """
            (else
                {false_block}
            )
        """

    def _selection_str(self, true_branch_block, merge_block, block, merge_blocks, next_case_block, switch_label_num):
        return """
            {cntrl}
            (if (i32.eq (local.get $control_val) (i32.const 1))
                (then
                    {true_block_code}
                )
                {possible_else}
            )""".format(cntrl=self._set_and_increment_control(),
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
    def _switch_label(switch_label_: str = None) -> str:
        return "(br {switch_label})".format(switch_label=switch_label_)

    def _switch_code(self,
                     block: int | None,  # TODO: rename to header, no???
                     end_block: int | None,  # TODO: remove end_block from all _n_code functions?!
                     merge_blocks: list[MergeBlockData],
                     switch_label_num: int,
                     next_case_block: int = None) -> str:

        destinations = [d for d in self.cfg.out_edges_destinations(block)]
        default, cases = destinations[-1], destinations[:-1]  # default = last dst, cases = the rest

        def build_br_table(cases_: list[int]) -> str:

            num_of_cases = len(cases_)

            br_table = ""
            for case in range(num_of_cases):
                br_table += f'{case}\t ;; case == {case} => (br {case})\n'  # add case

            default_br_index = num_of_cases
            br_table += f'{default_br_index}\t ;; default => (br {default_br_index})\n'  # add default

            return br_table

        def add_case(ix_: int, code_str) -> str:
            """Return code_str + new case"""
            next_case_block_: int = default if ix_ + 1 == len(cases) else cases[ix_ + 1]

            logger.info(f"Fallthrough test: Finding path from {cases[ix_]} to {next_case_block_}...")

            is_fallthrough = self._there_is_path_not_using_loop(block=block,
                                                                merge_blocks=merge_blocks,
                                                                current_case_block=cases[ix_],
                                                                next_case_block=next_case_block_)
            if is_fallthrough:
                end_block_ = next_case_block_
            else:
                end_block_ = self.cfg.merge_block(block)

            return """
                    (block
                        {code}
                        ;; Target for (br {ix})
                        {target_code}
                        {possible_switch_break}
                    )
                    """.format(ix=ix_,
                               code=code_str,
                               target_code=self.code_in_block_range(
                                   block=cases[ix_],
                                   end_block=end_block_,
                                   merge_blocks=merge_blocks,
                                   switch_label_num=next_label_num,
                                   next_case_block=next_case_block_),
                               possible_switch_break=self.switch_break_str(cases[ix_], is_fallthrough, switch_label))

        def add_default(code_str) -> str:

            end_block_ = self.calc_end_block_for_default(default, merge_blocks, block)

            return """
                {cntrl}
                (block {switch_block_label}
                    {code}
                    ;; Target for (br {ix}) => default
                    {target_code}
                )
        """.format(cntrl=WebAssemblyCodeBuilder._set_and_increment_control(),
                   ix=len(cases),
                   code=code_str,
                   target_code=self.code_in_block_range(
                       block=default,
                       end_block=end_block_,
                       merge_blocks=merge_blocks,
                       switch_label_num=next_label_num,
                       next_case_block=next_case_block),
                   switch_block_label=switch_label)

        switch_label: str = "$switch{current_switch_label_num}".format(current_switch_label_num=switch_label_num)
        next_label_num = switch_label_num + 1

        # inner block
        code = """
                    (block (local.get $control_val)
                        (br_table
                            {br_table}
                        )
                        ;; guard from UB
                        (call $store_in_output (local.get $output_index)(i32.const -1))
                        (local.set $output_index (call $inc (local.get $output_index)))
                        (br {label})
                    )""".format(br_table=build_br_table(cases),
                                label=switch_label)

        # wrap block in case + default branch code
        for ix in range(len(cases)):
            code = add_case(ix, code)

        code = add_default(code)

        return code

    @staticmethod
    def _format_code(code: str) -> str:
        from utils import format_code
        return format_code(
            code=code,
            add_line_above=[";; setup", ";; control flow code"],
            deliminators=('(', ')'),
            comment_marker=';;')
