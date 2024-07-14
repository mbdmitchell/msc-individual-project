# CFG -> Program conversion

from __future__ import annotations

from CFG import *
from WAT.CodeFormatter import format_code

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
        return WebAssemblyCodeBuilder._increment_control() + '\n' + WebAssemblyCodeBuilder._set_control()

    @staticmethod
    def _set_control():
        return """
            (local.set $control_val
                (call $calc_cntrl_val (local.get $control_index))
            )"""

    @staticmethod
    def _increment_control():
        return """
            (local.set $control_index
                (call $inc (local.get $control_index))
            )"""

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

    def _calc_dst_block(self, block) -> int | None:
        if self.cfg.out_degree(block) != 0:
            return self.cfg.out_edges_destinations(block)[0]
        else:
            return None

    # ------------------------------------------------------------------------------------------------------------------

    def _loop_code(self,
                   block: int | None,
                   end_block: int | None,
                   merge_blocks: list[MergeBlockData],
                   switch_label_num: int,
                   next_case_block: int = None) -> str:

        if not self.cfg.is_loop_header(block):
            raise RuntimeError("shouldn't be here")
        elif self.cfg.out_degree(block) != 2:
            raise RuntimeError("Loop headers must have out degree == 2")
        elif 'Merge' not in self.cfg.graph.nodes[block]:
            raise RuntimeError('Invalid loop construct (missing a labeled merge block)')

        merge_block = self.cfg.merge_block(block)  # TODO: isn't merge_block always just end_block? ...

        true_branch_block = self.cfg.out_edges_destinations(block)[1]

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
                """.format(loop_header=self._get_block(block),
                           cntrl=WebAssemblyCodeBuilder._set_and_increment_control(),
                           loop_body=self.code_in_block_range(
                               block=true_branch_block,
                               end_block=merge_block,
                               merge_blocks=merge_blocks,
                               next_case_block=next_case_block,
                               switch_label_num=switch_label_num))

    def _selection_code(self,
                        block: int | None,
                        end_block: int | None,
                        merge_blocks: list[MergeBlockData],
                        switch_label_num: int,
                        next_case_block: int = None) -> str:
        """NB: When selection type == switch, use switch_code() instead"""
        dst = self.cfg.out_edges_destinations(block)

        false_branch_block = dst[0]
        true_branch_block = dst[1]

        merge_block = self.cfg.merge_block(block)

        def calc_else_block_code():
            # when True, the false branch doesn't go straight to merge block
            is_if_else_statement = dst[0] != merge_blocks[0].merge_block

            if not is_if_else_statement:
                return ""

            return """
                (else
                    {false_block}
                )
                """.format(cntrl=WebAssemblyCodeBuilder._set_and_increment_control(),
                           false_block=self.code_in_block_range(block=false_branch_block,
                                                                end_block=merge_block,
                                                                merge_blocks=merge_blocks,
                                                                next_case_block=next_case_block,
                                                                switch_label_num=switch_label_num))
        return """
                {cntrl}
                (if (i32.eq (local.get $control_val) (i32.const 1))
                    (then
                        {true_block_code}
                    )
                    {possible_else}
                )""".format(
                cntrl=WebAssemblyCodeBuilder._set_and_increment_control(),
                possible_else=calc_else_block_code(),
                true_block_code=self.code_in_block_range(
                    block=true_branch_block,
                    end_block=merge_block,
                    merge_blocks=merge_blocks,
                    next_case_block=next_case_block,
                    switch_label_num=switch_label_num)
                )

    def _switch_code(self,
                     block: int | None,  # TODO: rename to header, no???
                     end_block: int | None,
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

        def build_switch_break(target: int, is_fallthrough_: bool):
            c1 = is_fallthrough_  # leaves scope of current case block and fall into scope of next => no switch_break
            c2 = self.cfg.is_exit_block(target)  # "(return)" added later => no switch_break
            c3 = self.cfg.is_continue_block(target) or self.cfg.is_break_block(target)  # relevant. added later => no SB
            if c1 or c2 or c3:
                return ""
            else:
                return "(br {switch_label})".format(switch_label=switch_label)

        def add_case(ix_: int, code_str) -> str:
            """Return code_str + new case"""
            next_case_block_: int = default if ix_ + 1 == len(cases) else cases[ix_ + 1]

            logger.info(f"Fallthrough test: Finding path from {cases[ix_]} to {next_case_block_}...")

            # calc is_fallthrough. NB: can't simply use nx.has_path as, e.g., a switch inside a loop finds path by going
            # through till back to loop header, then at the switch follows the branch corresponding to next_case_block_

            is_loop_header_present = any(self.cfg.is_loop_header(bk.related_header) for bk in merge_blocks)

            if is_loop_header_present:
                try:
                    paths = list(nx.all_simple_edge_paths(self.cfg.graph, cases[ix_], next_case_block_))
                    is_fallthrough = any(all(block not in edge for edge in path) for path in paths)
                except nx.NetworkXNoPath:
                    is_fallthrough = False
            else:
                is_fallthrough = nx.has_path(self.cfg.graph, cases[ix_], next_case_block_)

            if is_fallthrough:
                end_block = next_case_block_
            else:
                end_block = self.cfg.merge_block(block)

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
                                   end_block=end_block,
                                   merge_blocks=merge_blocks,
                                   switch_label_num=next_label_num,
                                   next_case_block=next_case_block_),
                               possible_switch_break=build_switch_break(cases[ix_], is_fallthrough))

        def add_default(code_str) -> str:
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
                       end_block=end_block,
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

    # ------------------------------------------------------------------------------------------------------------------
    def code_in_block_range(self,
                            block: int | None,
                            end_block: int | None,
                            merge_blocks: list[MergeBlockData],  # treated like a stack DS,
                            next_case_block: int = None,
                            switch_label_num: int = 0) -> str:
        """
        Returns the code for all blocks between start_ and end_block (exclusive)
        In practice, if start_block is a header, end_block will be the corresponding merge block.
        """

        if not block or block == end_block or block in self.added_blocks:
            return ""

        # handle merge_blocks
        while merge_blocks and block == merge_blocks[-1].merge_block:  # loop for if multiple headers have same merge
            merge_blocks.pop()
        if self.cfg.is_header_block(block):
            merge_blocks.append(MergeBlockData(merge_block=self.cfg.merge_block(block), related_header=block))

        # BUILD CODE STRING ...

        code = ''

        # ... visit 'block'
        if not (self.cfg.is_loop_header(block)):  # Loops require additional boilerplate so are handled later
            code += self._get_block(block)

        # ... add the rest
        if self.cfg.is_exit_block(block):

            code += self._exit_code()

        elif self.cfg.is_basic_block(block):

            is_break = self.cfg.is_break_block(block)
            is_cont = self.cfg.is_continue_block(block)

            if is_break or is_cont:
                code += self._break_code() if is_break else self._continue_code()
            else:
                code += self.code_in_block_range(self._calc_dst_block(block), end_block, merge_blocks, next_case_block)

        else:  # is_selection_header

            if self.cfg.is_loop_header(block):
                code_func = self._loop_code
            elif self.cfg.is_switch_block(block):
                code_func = self._switch_code
            else:
                code_func = self._selection_code

            merge_block = self.cfg.merge_block(block)

            # Add code in two sections

            code += code_func(block=block,
                              end_block=merge_block,
                              merge_blocks=merge_blocks,
                              next_case_block=next_case_block,
                              switch_label_num=switch_label_num)

            if merge_block != next_case_block:  # if ==, then the code is added later
                code += self.code_in_block_range(block=merge_block,
                                                 end_block=end_block,
                                                 merge_blocks=merge_blocks,
                                                 next_case_block=next_case_block,
                                                 switch_label_num=switch_label_num)

        return code

    def build_code(self) -> str:

        self.added_blocks = set()  # if user wants to call build_code() >1 times

        raw_code = self.code_in_block_range(block=self.cfg.entry_node(),
                                            end_block=None,
                                            merge_blocks=[],  # solely *needed* for `is_loop_header_present`. TODO: explore if can refactor out
                                            switch_label_num=0,
                                            next_case_block=None)

        code = format_code(self._full_program(raw_code))

        return code