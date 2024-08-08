import copy
import re

from CFG import CFG
from my_common import CodeType, MergeBlockData
from code_builders import CodeBuilder
from languages import Language


class StaticCodeBuilder(CodeBuilder):

    def __init__(self, language: 'Language', cfg: CFG, directions: list[int]):
        super().__init__(language, cfg)
        self.directions = directions

        # All the info about the path of execution needed to flesh the skeleton program.
        self.fleshing_info = self._calc_fleshing_info()

    # ------------------------------------------------------------------------------------------------------------------

    @property
    def enclosing_loops(self) -> dict:
        """Construct dict. For each header, calc list of loop headers that enclose it, from outer to innermost"""

        loops_dict = {}
        merge_blocks: list[MergeBlockData] = []
        visited_blocks = set()

        self._enclosing_loops_aux(self.cfg.entry_node(), None, loops_dict, merge_blocks, visited_blocks)

        return loops_dict

    # helpers for enclosing_loops ...

    def _enclosing_loops_aux(self, block, end_block, loops_dict, merge_blocks, visited_blocks):
        """Helper function to recursively traverse blocks and calculate enclosing loops."""

        # Visit block
        if not block or block == end_block or block in visited_blocks:
            return
        visited_blocks.add(block)

        # Early exit
        if self.cfg.is_exit_block(block):
            return

        # Add merge info for current block (if header) to dict.
        self.handle_merge_blocks(block, merge_blocks)
        if self.cfg.is_header_block(block) or self.cfg.is_break_block(
                block):  # useful to know the outer loop of break blocks
            loops_dict[block] = copy.deepcopy(merge_blocks)  # Deep copy to prevent modifications.

        # Call enclosing_loops_aux for block's descendants

        if self.cfg.is_basic_block(block):
            self._process_basic_block(block, end_block, merge_blocks, loops_dict, visited_blocks)
        elif self.cfg.is_loop_header(block):
            self._process_loop_header(block, merge_blocks, loops_dict, visited_blocks)
        elif self.cfg.is_switch_block(block):
            self._process_switch_block(block, merge_blocks, loops_dict, visited_blocks)
        else:
            self._process_selection_header(block, merge_blocks, loops_dict, visited_blocks)

        if self.cfg.contains_merge_instruction(block):
            merge_block = self.cfg.merge_block(block)
            self._enclosing_loops_aux(merge_block, end_block, loops_dict, merge_blocks, visited_blocks)

    def _process_basic_block(self, block, end_block, merge_blocks, loops_dict, visited_blocks):
        self._enclosing_loops_aux(self._calc_dst_block(block), end_block, loops_dict, merge_blocks, visited_blocks)

    def _process_loop_header(self, block, merge_blocks, loops_dict, visited_blocks):
        true_branch_block = self.cfg.out_edges_destinations(block)[1]
        self._enclosing_loops_aux(true_branch_block, block, loops_dict, merge_blocks, visited_blocks)

    def _process_switch_block(self, block, merge_blocks, loops_dict, visited_blocks):
        destinations = [d for d in self.cfg.out_edges_destinations(block)]
        default, cases = destinations[-1], destinations[:-1]  # default = last dst, cases = the rest

        for ix in range(len(cases)):
            current_case = cases[ix]
            next_case = default if ix + 1 == len(cases) else cases[ix + 1]
            is_fallthrough = self.there_is_path_not_using_loop(block, merge_blocks, current_case, next_case)
            if not self.language.allows_switch_fallthrough:
                assert not is_fallthrough

            end_block = self._calc_end_block_for_case(is_fallthrough, block, next_case)
            self._enclosing_loops_aux(current_case, end_block, loops_dict, merge_blocks, visited_blocks)

        end_block = self.calc_end_block_for_default(default, merge_blocks, block)
        self._enclosing_loops_aux(default, end_block, loops_dict, merge_blocks, visited_blocks)

    def _process_selection_header(self, block, merge_blocks, loops_dict, visited_blocks):
        end_block = self.cfg.merge_block(block)
        dst = self.cfg.out_edges_destinations(block)
        self._enclosing_loops_aux(dst[0], end_block, loops_dict, merge_blocks, visited_blocks)
        self._enclosing_loops_aux(dst[1], end_block, loops_dict, merge_blocks, visited_blocks)

    # ------------------------------------------------------------------------------------------------------------------

    # fleshing functions and helpers

    class _FleshingInfo:
        """If header is a loop, cntrl_vals is the # of iterations performed else it's an ordered list of the
        edge indices taken"""

        def __init__(self, block, cntrl_val: int = 0):
            self.current_ix = 0
            self._block = block
            self.cntrl_vals = [cntrl_val]

        @property
        def block(self):
            return self._block

        def append(self, direction: int):
            self.cntrl_vals.append(direction)
            self.increment_ix()

        def increment_last_elem(self):
            """Increments the element at the current index, or appends a 0 if the index is out of bounds."""
            if self.current_ix < len(self.cntrl_vals):
                self.cntrl_vals[self.current_ix] += 1
            else:
                self.cntrl_vals.append(0)

        def increment_ix(self):
            if self.current_ix >= len(self.cntrl_vals):  # self.cntrl_vals[self.current_ix] out of bounds
                self.cntrl_vals.append(0)
            self.current_ix += 1

    def _blocks_enclosed_in(self, block):
        affected = []
        for block_key in self.enclosing_loops:
            if block_key == block:
                continue
            if block in [elem.related_header for elem in self.enclosing_loops[block_key]]:
                affected.append(block_key)

        return affected

    def _update_fleshing_info(self, current_block, edge_index, fleshing_info):
        if current_block not in fleshing_info:
            fleshing_info[current_block] = self._FleshingInfo(current_block)
        elif self.cfg.is_loop_header(current_block):

            blocks = self._blocks_enclosed_in(current_block)
            for b in blocks:
                if b in fleshing_info:
                    fleshing_info[b].increment_ix()

            fleshing_info[current_block].increment_last_elem()
        else:
            fleshing_info[current_block].append(edge_index)

    def _calc_fleshing_info(self):

        fleshing_info = {}

        current_block = self.cfg.entry_node()
        directions_ix = 0

        while directions_ix < len(self.directions):

            if self.cfg.is_end_node(current_block):
                break

            # calculate edge ix
            if self.cfg.out_degree(current_block) == 1:
                edge_index = 0
            else:
                edge_index = self.directions[directions_ix]
                directions_ix += 1

            # handle non-headers
            if not self.cfg.is_header_block(current_block):

                if self.cfg.is_break_block(current_block):
                    # The number of iterations a loop does is calculated by incrementing each time the path returns to
                    # the loop header. As break causes early exit, an additional increment is needed
                    fleshing_info[self.enclosing_loops[current_block]].increment_last_elem()

                current_block = self.cfg.edge_index_to_dst_block(current_block, edge_index)
                continue

            # update fleshing info
            if current_block not in fleshing_info:
                if self.cfg.is_loop_header(current_block):
                    fleshing_info[current_block] = self._FleshingInfo(current_block)
                else:
                    fleshing_info[current_block] = self._FleshingInfo(current_block, edge_index)
            elif self.cfg.is_loop_header(current_block):

                blocks = self._blocks_enclosed_in(current_block)
                for b in blocks:
                    if b in fleshing_info:
                        fleshing_info[b].increment_ix()

                fleshing_info[current_block].increment_last_elem()
            else:
                fleshing_info[current_block].append(edge_index)

            # set next block
            current_block = self.cfg.edge_index_to_dst_block(current_block, edge_index)

        return fleshing_info

    def _build_dict_of_control_arrays(self):
        arr_dict = {}

        for key in self.fleshing_info:
            arr_dict[key] = self.fleshing_info[key].cntrl_vals

        return arr_dict

    def _loop_code_return_str(self, block: int, true_branch_block, merge_block, merge_blocks, next_case_block,
                              switch_label_num) -> str:
        pre_format_str = self.language.loop_str_pre_format(CodeType.STATIC, block)
        return pre_format_str.format(
            loop_header=self.add_block(block),
            loop_body=self.code_in_block_range(
                block=true_branch_block,
                end_block=merge_block,
                merge_blocks=merge_blocks,
                next_case_block=next_case_block,
                switch_label_num=switch_label_num)
        )

    def _selection_str(self, true_branch_block, merge_block, block, merge_blocks, next_case_block, switch_label_num):
        pre_format_str = self.langauge.selection_str_pre_format(CodeType.STATIC, block)

        return pre_format_str.format(
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

    def switch_full_code_aux(self, case_code: str, default_code: str, block: int):
        return self.language.switch_full_str(code_type=CodeType.STATIC, case_code=case_code,
                                             default_code=default_code, block=block)

    def _convert_to_arr_declarations(self, cntrl_arrays: dict):
        code: str = ''
        for key in cntrl_arrays:
            code += self.language.array_statement(key, cntrl_arrays[key]) + '\n'
        return code

    def full_program_aux(self, control_flow_code):
        cntrl_arrays = self._build_dict_of_control_arrays()
        cntrl_arr_declarations = self._convert_to_arr_declarations(cntrl_arrays)
        code_skeleton: str = self.language.full_program(CodeType.STATIC, control_flow_code, cntrl_arr_declarations)
        return self._flesh(code_skeleton)

    def _flesh(self, code_skeleton: str) -> str:

        def intended_str_for_placeholder(match) -> str:
            block = int(match.group(1))

            if block not in self.fleshing_info:
                # value is arbitrary as, if not in fleshing_info, flow of execution never goes to that block
                return str(-1)
            elif len(self.fleshing_info[block].cntrl_vals) == 1:  # i.e. No enclosing loops other than itself
                return str(self.fleshing_info[block].cntrl_vals[0])
            else:
                enclosing_loop = self.enclosing_loops[block][-2].related_header
                return f'{self.language.cntrl_arr_var_name(block)}[{self.language.loop_ix_name(enclosing_loop)}]'

        # before a code skeleton is fleshed, header guards have placeholder of form:
        placeholder_pattern = re.compile(r"\$\$(\d+)\$\$")

        fleshed_code = placeholder_pattern.sub(intended_str_for_placeholder, code_skeleton)

        return fleshed_code
