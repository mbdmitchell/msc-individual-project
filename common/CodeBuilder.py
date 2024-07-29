from __future__ import annotations
from CFG import *
from abc import ABC, abstractmethod

from common import MergeBlockData


class CodeBuilder(ABC):

    def __init__(self, cfg: CFG):
        self.cfg = cfg
        self.added_blocks = set()

    def _calc_dst_block(self, block) -> int | None:
        if self.cfg.out_degree(block) != 0:
            return self.cfg.out_edges_destinations(block)[0]
        else:
            return None

    @staticmethod
    @abstractmethod
    def _full_program(control_flow_code: str) -> str:
        pass

    @staticmethod
    @abstractmethod
    def _set_and_increment_control() -> str:
        pass

    @staticmethod
    @abstractmethod
    def _continue_code() -> str:
        pass

    @staticmethod
    @abstractmethod
    def _break_code() -> str:
        pass

    @staticmethod
    @abstractmethod
    def _exit_code() -> str:
        pass

    @abstractmethod
    def _get_block(self, n: int) -> str:
        pass

    # ===================================================================

    @staticmethod
    @abstractmethod
    def _loop_code_str() -> str:
        pass

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

        merge_block = self.cfg.merge_block(block)
        true_branch_block = self.cfg.out_edges_destinations(block)[1]

        return self._loop_code_str().format(
            loop_header=self._get_block(block),
            cntrl=self._set_and_increment_control(),
            loop_body=self.code_in_block_range(
                block=true_branch_block,
                end_block=merge_block,
                merge_blocks=merge_blocks,
                next_case_block=next_case_block,
                switch_label_num=switch_label_num)
            )

    # ===================================================================

    @staticmethod
    @abstractmethod
    def _else_code_str() -> str:
        pass

    def _calc_else_block_code(self, block, merge_blocks, next_case_block, switch_label_num) -> str:
        # when True, the false branch doesn't go straight to merge block
        dst = self.cfg.out_edges_destinations(block)
        false_branch_block = dst[0]
        merge_block = self.cfg.merge_block(block)

        is_if_else_statement = false_branch_block != merge_block

        if not is_if_else_statement:
            return ""

        return self._else_code_str().format(
            cntrl=self._set_and_increment_control(),
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

    def _selection_code(self,
                        block: int | None,
                        end_block: int | None,
                        merge_blocks: list[MergeBlockData],
                        switch_label_num: int,
                        next_case_block: int = None) -> str:

        true_branch_block = self.cfg.out_edges_destinations(block)[1]
        merge_block = self.cfg.merge_block(block)

        return self._selection_str(true_branch_block, merge_block, block, merge_blocks, next_case_block,
                                   switch_label_num)

    # ===================================================================

    def _there_is_path_not_using_loop(self, block, merge_blocks, current_case_block, next_case_block):
        """
        Checks if there is a path between `current_case_block` and `next_case_block` in the control flow graph
        that does not pass through a loop header. Needed for checking switch fallthrough.
        """

        is_loop_header_present = any(self.cfg.is_loop_header(bk.related_header) for bk in merge_blocks)

        if not is_loop_header_present or len(merge_blocks) <= 1:
            return nx.has_path(self.cfg.graph, current_case_block, next_case_block)

        closest_loop_header_enclosing_switch = None

        for bk in merge_blocks[-2::-1]:  # Iterate from merge_blocks[-2] to merge_blocks[0] ([-1].header always switch)
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
    def _switch_code(self,
                     block: int | None,
                     end_block: int | None,
                     merge_blocks: list[MergeBlockData],
                     switch_label_num: int,
                     next_case_block: int = None) -> str:
        pass

    @staticmethod
    @abstractmethod
    def _switch_label(switch_label: str = None) -> str:
        pass

    def switch_break_str(self, target: int, is_fallthrough: bool, switch_label: str = None):
        c1 = is_fallthrough  # leaves scope of current case block and fall into scope of next => no switch_break
        c2 = self.cfg.is_exit_block(target)  # "(return)" added later => no switch_break
        c3 = self.cfg.is_continue_block(target) or self.cfg.is_break_block(target)  # relevant. added later => no S.B.
        if c1 or c2 or c3:
            return ""
        else:
            return self._switch_label(switch_label)

    def calc_end_block_for_default(self, default, merge_blocks, block) -> int:
        """Calculates the appropriate end block for the default case in a switch construct."""

        # If true, it means it's not a *proper* merge (blocks from other cases can't reach it, e.g. tree-like CFGs)
        if default == merge_blocks[-1].merge_block:
            nearest_loop_header = next((b.related_header for b in merge_blocks[-2::-1]
                                        if self.cfg.is_loop_header(b.related_header)), None)

            return nearest_loop_header
        else:
            return self.cfg.merge_block(block)

    # ------------------------------------------------------------------------------------------------------------------

    def code_in_block_range(self,
                            block: int | None,
                            end_block: int | None,
                            merge_blocks: list[MergeBlockData],  # treated like a stack DS,
                            next_case_block: int = None,
                            switch_label_num: int = 0) -> str:
        """
        Returns the code for all blocks in range [block, end_block)
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

            if merge_block != next_case_block:  # if true, then the code is added later
                code += self.code_in_block_range(block=merge_block,
                                                 end_block=end_block,
                                                 merge_blocks=merge_blocks,
                                                 next_case_block=next_case_block,
                                                 switch_label_num=switch_label_num)

        return code

    @staticmethod
    @abstractmethod
    def _format_code(code: str) -> str:
        pass

    def build_code(self) -> str:

        self.added_blocks = set()  # Reset the set of added blocks if build_code() is called multiple times

        raw_code = self.code_in_block_range(block=self.cfg.entry_node(),
                                            end_block=None,
                                            merge_blocks=[],
                                            switch_label_num=0,
                                            next_case_block=None)

        program: str = self._full_program(raw_code)
        formatted_program: str = self._format_code(program)

        return formatted_program