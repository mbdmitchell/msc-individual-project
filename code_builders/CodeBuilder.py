from __future__ import annotations
from CFG import *
from abc import ABC, abstractmethod

from my_common.MergeBlockData import MergeBlockData
from languages import Language, WASMLang


class CodeBuilder(ABC):

    def __init__(self, language: Language, cfg: CFG, directions: list[int] = None):
        self.langauge = language
        self.cfg = cfg
        self.added_blocks = set()
        self.directions = directions

    @property
    def language(self):
        return self.langauge

    # ------------------------------------------------------------------------------------------------------------------

    def loop_code(self,
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

        merge_block = self.cfg.merge_block(block)
        true_branch_block = self.cfg.out_edges_destinations(block)[1]

        return self._loop_code_return_str(block, true_branch_block, merge_block, merge_blocks, next_case_block,
                                          switch_label_num)

    # helpers...

    @abstractmethod
    def _loop_code_return_str(self, block, true_branch_block, merge_block, merge_blocks, next_case_block,
                              switch_label_num) -> str:
        """The final string. _loop_code_str().format(...)"""
        pass

    # ------------------------------------------------------------------------------------------------------------------

    def selection_code(self,
                       block: int | None,
                       end_block: int | None,
                       merge_blocks: list[MergeBlockData],
                       switch_label_num: int,
                       next_case_block: int = None) -> str:

        true_branch_block = self.cfg.out_edges_destinations(block)[1]
        merge_block = self.cfg.merge_block(block)

        return self._selection_str(true_branch_block, merge_block, block, merge_blocks, next_case_block,
                                   switch_label_num)

    # helpers...

    def _calc_else_block_code(self, block, merge_blocks, next_case_block, switch_label_num) -> str:
        # when True, the false branch doesn't go straight to merge block
        dst = self.cfg.out_edges_destinations(block)
        false_branch_block = dst[0]
        merge_block = self.cfg.merge_block(block)

        is_if_else_statement = false_branch_block != merge_block

        if not is_if_else_statement:
            return ""

        return self.language.else_str_pre_format().format(
            false_block=self.code_in_block_range(
                block=false_branch_block,
                end_block=merge_block,
                merge_blocks=merge_blocks,
                next_case_block=next_case_block,
                switch_label_num=switch_label_num)
        )

    @abstractmethod
    def _selection_str(self, true_branch_block, merge_block, block, merge_blocks, next_case_block, switch_label_num):
        pass

    # ------------------------------------------------------------------------------------------------------------------

    def _calc_end_block_for_case(self, is_fallthrough, block, next_case):
        if is_fallthrough:
            return next_case
        else:
            return self.cfg.merge_block(block)

    def switch_code(self,
                    block: Optional[int],  # TODO: could rename to header
                    end_block: Optional[int],
                    merge_blocks: list[MergeBlockData],
                    switch_label_num: int,
                    next_case_block: int = None) -> str:

        destinations = [d for d in self.cfg.out_edges_destinations(block)]
        default, cases = destinations[-1], destinations[:-1]  # default = last dst, cases = the rest

        def case_str(ix_: int, code_str: str = None) -> str:
            """Return just that case_str"""
            current_case = cases[ix_]
            next_case = default if ix_ + 1 == len(cases) else cases[ix_ + 1]

            is_fallthrough = self.there_is_path_not_using_loop(block, merge_blocks, current_case, next_case)

            if not self.langauge.allows_switch_fallthrough:
                assert not is_fallthrough

            end_block_ = self._calc_end_block_for_case(is_fallthrough, block, next_case)

            # is WASM

            if isinstance(self.langauge, WASMLang):
                next_label_num_ = switch_label_num + 1
            else:
                next_label_num_ = switch_label_num

            if isinstance(self.langauge, WASMLang):
                return self.language.switch_case_str_pre_format().format(
                    ix=ix_,
                    code=code_str,
                    case_code=self.code_in_block_range(
                        block=current_case,
                        end_block=end_block_,
                        merge_blocks=merge_blocks,
                        switch_label_num=next_label_num_,
                        next_case_block=next_case),
                    possible_switch_break=self.switch_break_str(current_case, is_fallthrough, switch_label_num))
            else:
                return self.language.switch_case_str_pre_format().format(
                    ix=ix_,
                    case_code=self.code_in_block_range(
                        block=current_case,
                        end_block=end_block_,
                        merge_blocks=merge_blocks,
                        switch_label_num=next_label_num_,
                        next_case_block=next_case_block),
                    possible_switch_break=self.switch_break_str(current_case, is_fallthrough, switch_label_num))

        def add_cases(code_str: str = None) -> str:
            # If WASM, add to code_str, else return case code. TODO: think of better name.
            if not isinstance(self.langauge, WASMLang):
                code_ = ''
                for ix in range(len(cases)):
                    code_ += case_str(ix)
                return code_
            else:
                for ix in range(len(cases)):
                    code_str = case_str(ix, code_str)
                return code_str

        def add_default(code_str: str = None) -> str:

            if not isinstance(self.langauge, WASMLang):
                end_block_ = self.calc_end_block_for_default(default, merge_blocks, block)
                return self.language.switch_default_str_pre_format().format(default_code=self.code_in_block_range(
                    block=default,
                    end_block=end_block_,
                    merge_blocks=merge_blocks,
                    switch_label_num=switch_label_num,
                    next_case_block=next_case_block))

            end_block_ = self.calc_end_block_for_default(default, merge_blocks, block)
            return """
                                {cntrl}
                                (block {switch_block_label}
                                    {code}
                                    ;; Target for (br {ix}) => default
                                    {target_code}
                                )
                        """.format(cntrl=self.langauge.set_and_increment_control(),
                                   ix=len(cases),
                                   code=code_str,
                                   target_code=self.code_in_block_range(
                                       block=default,
                                       end_block=end_block_,
                                       merge_blocks=merge_blocks,
                                       switch_label_num=next_label_num,
                                       next_case_block=next_case_block),
                                   switch_block_label=WASMLang.switch_label(switch_label_num))

        if not isinstance(self.langauge, WASMLang):
            case_code = add_cases()
            default_code = add_default()
            return self.switch_full_code_aux(case_code=case_code, default_code=default_code, block=block)
        else:
            next_label_num = switch_label_num + 1

            # inner block
            code = f"""
                                (block (local.get {WASMLang.cntrl_val_var_name()})
                                    (br_table
                                        {WASMLang.build_br_table(cases)}
                                    )
                                    ;; guard from UB
                                    (call $store_in_output (local.get $output_index)(i32.const -1))
                                    (local.set $output_index (call $inc (local.get $output_index)))
                                    (br {WASMLang.switch_label(switch_label_num)})
                                )"""

            code = add_cases(code)
            code = add_default(code)
            return code

    # helpers...

    def switch_break_str(self, target: int, is_fallthrough: bool, switch_num: Optional[int] = None):
        c1 = is_fallthrough  # leaves scope of current case block and fall into scope of next => no switch_break
        c2 = self.cfg.is_exit_block(target)  # "return" added later => no switch_break
        c3 = self.cfg.is_continue_block(target) or self.cfg.is_break_block(target)  # relevant. added later => no S.B.
        if c1 or c2 or c3:
            return ""
        else:
            if isinstance(self.language, WASMLang):
                return WASMLang.switch_break_label(switch_num)
            else:
                return self.language.switch_label(switch_num)

    def calc_end_block_for_default(self, default, merge_blocks, block) -> int:
        """Calculates the appropriate end block for the default case in a switch construct."""

        # If true, it means it's not a *proper* merge (blocks from other cases can't reach it, e.g. tree-like CFGs)
        if default == merge_blocks[-1].merge_block:
            nearest_loop_header = next((b.related_header for b in merge_blocks[-2::-1]
                                        if self.cfg.is_loop_header(b.related_header)), None)
            return nearest_loop_header
        else:
            return self.cfg.merge_block(block)

    def there_is_path_not_using_loop(self, block, merge_blocks, current_case_block, next_case_block):
        """
        Checks if there is a path between `current_case_block` and `next_case_block` in the control flow graph
        that does not pass through a loop header. Needed for checking switch fallthrough.
        """

        is_loop_header_present = any(self.cfg.is_loop_header(bk.related_header) for bk in merge_blocks)

        if not is_loop_header_present or len(merge_blocks) <= 1:
            return nx.has_path(self.cfg.graph, current_case_block, next_case_block)

        closest_loop_header_enclosing_switch = None

        for bk in merge_blocks[-2::-1]:  # Iterate from merge_blocks[-2] to mb[0] (mb[-1].header is always switch)
            if self.cfg.is_loop_header(bk.related_header):
                closest_loop_header_enclosing_switch = bk.related_header
                break

        blocks_to_try = [current_case_block]
        visited = set()

        while len(blocks_to_try) != 0:
            current = blocks_to_try.pop()
            visited.add(current)
            if (current, next_case_block) in self.cfg.out_edges(current):
                return True
            else:
                to_add = [
                    neighbor for neighbor in self.cfg.out_edges_destinations(current)
                    if (neighbor not in visited) and (neighbor != closest_loop_header_enclosing_switch)
                ]

                blocks_to_try.extend(to_add)
        return False

    @abstractmethod
    def switch_full_code_aux(self, case_code: str, default_code: str, block: int):
        pass

    # ------------------------------------------------------------------------------------------------------------------

    def handle_merge_blocks(self, block, merge_blocks) -> None:
        while merge_blocks and block == merge_blocks[-1].merge_block:  # loop for if multiple headers have same merge
            merge_blocks.pop()
        if self.cfg.is_header_block(block):
            merge_blocks.append(MergeBlockData(merge_block=self.cfg.merge_block(block), related_header=block))

    def code_in_block_range(self,
                            block: int | None,
                            end_block: int | None,
                            merge_blocks: list[MergeBlockData],  # treated like a stack DS,
                            next_case_block: int = None,
                            switch_label_num: int = 0) -> str:
        """
        Returns the code for all blocks in range [block, end_block)
        In practice, if `block` is a header, end_block will normally be the corresponding merge block.
        """

        if not block or block == end_block or block in self.added_blocks:
            return ""

        self.handle_merge_blocks(block, merge_blocks)

        # BUILD CODE STRING ...

        code = ''

        # ... visit 'block'
        if not (self.cfg.is_loop_header(block)):  # Loops require additional boilerplate so are handled later
            code += self.add_block(block)

        # ... add the rest
        if self.cfg.is_exit_block(block):

            code += self.language.exit_code

        elif self.cfg.is_basic_block(block):

            is_break = self.cfg.is_break_block(block)
            is_cont = self.cfg.is_continue_block(block)

            if is_break or is_cont:
                code += self.language.break_code if is_break else self.language.continue_code
            else:
                code += self.code_in_block_range(self._calc_dst_block(block), end_block, merge_blocks,
                                                 next_case_block, switch_label_num)

        else:  # is_selection_header

            if self.cfg.is_loop_header(block):
                code_func = self.loop_code
            elif self.cfg.is_switch_block(block):
                code_func = self.switch_code
            else:
                code_func = self.selection_code

            merge_block = self.cfg.merge_block(block)

            # Add code in two sections

            code += code_func(block=block,
                              end_block=merge_block,
                              merge_blocks=merge_blocks,
                              next_case_block=next_case_block,
                              switch_label_num=switch_label_num)

            if merge_block != next_case_block:  # if true, then the code is added later
                code += self.code_in_block_range(block=merge_block,
                                                 end_block=end_block,
                                                 merge_blocks=merge_blocks,
                                                 next_case_block=next_case_block,
                                                 switch_label_num=switch_label_num)

        return code

    # helpers...

    def _calc_dst_block(self, block) -> int | None:
        if self.cfg.out_degree(block) != 0:
            return self.cfg.out_edges_destinations(block)[0]
        else:
            return None

    def add_block(self, n: int) -> str:
        self.added_blocks.add(n)
        return self.langauge.block.format(n=n)

    def build_code(self) -> str:

        self.added_blocks = set()  # Reset the set of added blocks if build_code() is called multiple times

        raw_code = self.code_in_block_range(block=self.cfg.entry_node(),
                                            end_block=None,
                                            merge_blocks=[],
                                            switch_label_num=0)

        program: str = self.full_program_aux(raw_code, self.directions)
        formatted_program: str = self.langauge.format_code_(program)

        return formatted_program

    @abstractmethod
    def full_program_aux(self, control_flow_code, directions: list[int] = None):
        pass
