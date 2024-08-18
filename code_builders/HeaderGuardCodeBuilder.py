import re

from CFG import CFG
from my_common import MergeBlockData
from my_common.CodeType import CodeType
from code_builders import CodeBuilder
from languages import Language, WASMLang


class _FleshingInfo:
    """For use by StaticCodeBuilder only.

    NB: If header is a loop, cntrl_vals is the # of iterations performed else it's an ordered list of the
    edge indices taken"""

    _unused_cntrl_val = -1

    def __init__(self, block):
        self._current_ix = 0
        self._block = block
        self._cntrl_vals = [self.unused_cntrl_val]

    def __len__(self):
        return len(self._cntrl_vals)

    def sum_of_used_cntrl_vals(self):
        return sum(e for e in self._cntrl_vals if e > 0)

    @property
    def block(self):
        return self._block

    @property
    def unused_cntrl_val(self):
        return self._unused_cntrl_val

    def inc_last_elem(self):
        self._cntrl_vals[-1] += 1

    def append_new_unused_cntrl_val(self):
        self._cntrl_vals.append(self.unused_cntrl_val)

    def block_visited_on_latest_iteration(self) -> bool:
        return self._cntrl_vals[-1] != self.unused_cntrl_val


class HeaderGuardCodeBuilder(CodeBuilder):

    def __init__(self, language: 'Language', cfg: CFG, directions: list[int]):
        super().__init__(language, cfg)
        self.directions = directions

        # All the info about the path of execution needed to flesh the skeleton program.
        self.fleshing_info = self._calc_fleshing_info()

    # ------------------------------------------------------------------------------------------------------------------

    @property
    def enclosing_loops_inclusive(self) -> dict:
        """Construct dict. For each header, calc list of loop headers that enclose it, from outer to innermost.
        Inclusive - for, e.g., enclosing_loops[block n] include block n if it's a loop header"""

        loops_dict = {}
        merge_blocks: list[MergeBlockData] = []
        visited_blocks = set()

        self._enclosing_loops_aux(self.cfg.entry_node(), None, loops_dict, merge_blocks, visited_blocks)

        return loops_dict

    @property
    def enclosing_loops_exclusive(self) -> dict:
        """Filter out any MergeBlockData elements where key == MergeBlockData.related_header"""
        return {key: [elem for elem in value if elem.related_header != key]
                for key, value in self.enclosing_loops_inclusive.items()}

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
            loops_dict[block] = [m for m in merge_blocks if self.cfg.is_loop_header(m.related_header)]

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

    def _blocks_enclosed_in(self, block):
        affected = []
        for block_key in self.enclosing_loops_inclusive:
            if block_key == block:
                continue
            if block in [elem.related_header for elem in self.enclosing_loops_inclusive[block_key]]:
                affected.append(block_key)

        return affected

    def _calc_fleshing_info(self):

        # Init fleshing_info: all headers start w/ empty _FleshingInfo objects
        fleshing_info = {key: _FleshingInfo(block=key) for key, _ in self.enclosing_loops_exclusive}

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

            # HANDLE NON-HEADERS

            if not self.cfg.is_header_block(current_block):

                if self.cfg.is_break_block(current_block):
                    # The number of iterations a loop does is calculated by incrementing each time the path returns to
                    # the loop header. As a break statement causes control flow not to return to the header,
                    # an additional increment is needed.
                    fleshing_info[self.enclosing_loops_inclusive[current_block]].inc_last_elem()

                current_block = self.cfg.edge_index_to_dst_block(current_block, edge_index)
                continue

            # HANDLE HEADERS (update fleshing info)

            assert current_block in fleshing_info

            if self.cfg.is_loop_header(current_block):
                if fleshing_info[current_block].block_visited_on_latest_iteration():
                    blocks = self._blocks_enclosed_in(current_block)
                    for b in blocks:
                        if b in fleshing_info:
                            fleshing_info[b].append_new_unused_cntrl_val()
                fleshing_info[current_block].inc_last_elem()
            else:
                fleshing_info[current_block][-1] = edge_index

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
        pre_format_str = self.language.loop_str_pre_format(CodeType.HEADER_GUARD, block)
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
        pre_format_str = self.langauge.selection_str_pre_format(CodeType.HEADER_GUARD, block)

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

        if isinstance(self.language, WASMLang):
            raise NotImplementedError("WASM static code for switches not written yet")

        return self.language.switch_full_str(code_type=CodeType.HEADER_GUARD, case_code=case_code,
                                             default_code=default_code, block=block)

    def _convert_to_arr_declarations(self, cntrl_arrays: dict):
        code: str = ''
        for key in cntrl_arrays:
            code += self.language.array_statement(values=cntrl_arrays[key], block=key) + '\n'
        return code

    def full_program_aux(self, control_flow_code, directions: list[int] = None):
        cntrl_arrays = self._build_dict_of_control_arrays()
        cntrl_arr_declarations = self._convert_to_arr_declarations(cntrl_arrays)
        code_skeleton: str = self.language.full_program(CodeType.HEADER_GUARD, control_flow_code, cntrl_arr_declarations)
        return self._flesh(code_skeleton)

    def _flesh(self, code_skeleton: str) -> str:

        def correct_ix_val(block):

            if len(self.enclosing_loops_exclusive[block]) == 0:
                return self.language.loop_ix_name(block)

            enclosing_loop = self.enclosing_loops_exclusive[block][-1].related_header



            # if len(self.enclosing_loops_exclusive[block]) == 0:
            #     return str(self.fleshing_info[block].cntrl_vals[0])
            #
            # enclosing_loop = self.enclosing_loops_exclusive[block][-1].related_header
            # enclosing_loop_ix_name = self.language.loop_ix_name(enclosing_loop)
            #
            # if len(self.enclosing_loops_exclusive[block]) == 0:
            #     return str(self.fleshing_info[block].cntrl_vals[0])

        def intended_str_for_placeholder(match) -> str:
            """Return the correct number or 'arr[ix]' string for a given placeholder"""
            block = int(match.group(1))

            # return number: no outer loop or not in fleshing_info
            if block not in self.fleshing_info:
                return str(_FleshingInfo.unused_cntrl_val)
            elif len(self.enclosing_loops_exclusive[block]) == 0:
                return str(self.fleshing_info[block].cntrl_vals[0])

            # return 'arr[...]'
            cntrl_arr_var_name = self.language.cntrl_arr_var_name(block)
            return f'{cntrl_arr_var_name}[{correct_ix_val(block)}]'

        # before a code skeleton is fleshed, header guards have placeholder of form:
        placeholder_pattern = re.compile(r"\$\$(\d+)\$\$")

        fleshed_code = placeholder_pattern.sub(intended_str_for_placeholder, code_skeleton)

        return fleshed_code
