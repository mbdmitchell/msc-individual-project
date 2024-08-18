from abc import abstractmethod

from CFG import CFG
from code_builders import CodeBuilder
from languages import Language


class ArrayCodeBuilder(CodeBuilder):
    def __init__(self, language: 'Language', cfg: CFG, directions: list[int] = None):
        super().__init__(language, cfg, directions)

    @property
    @abstractmethod
    def code_type(self):
        pass

    def _loop_code_return_str(self, block, true_branch_block, merge_block, merge_blocks, next_case_block,
                              switch_label_num) -> str:
        pre_format_str = self.language.loop_str_pre_format(self.code_type, block)
        return pre_format_str.format(
            loop_header=self.add_block(block),
            loop_body=self.code_in_block_range(
                block=true_branch_block,
                end_block=merge_block,
                merge_blocks=merge_blocks,
                next_case_block=next_case_block,
                switch_label_num=switch_label_num)
        )

    def _selection_str(self, true_branch_block, merge_block, block, merge_blocks, next_case_block, switch_label_num) -> str:
        pre_format_str = self.langauge.selection_str_pre_format(self.code_type, block)
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
        return self.language.switch_full_str(code_type=self.code_type, case_code=case_code,
                                             default_code=default_code, block=block)

    def full_program_aux(self, control_flow_code, directions: list[int] = None):
        return self.language.full_program(self.code_type, control_flow_code, directions=directions)
