from CFG import CFG
from code_builders import CodeBuilder
from my_common import CodeType
from languages import Language


class GlobalArrayCodeBuilder(CodeBuilder):

    def __init__(self, language: 'Language', cfg: CFG):
        super().__init__(language, cfg)

    def _loop_code_return_str(self, block, true_branch_block, merge_block, merge_blocks, next_case_block,
                              switch_label_num) -> str:
        pre_format_str = self.language.loop_str_pre_format(CodeType.GLOBAL_ARRAY, block)
        return pre_format_str.format(
            loop_header=self.add_block(block),
            cntrl=self.language.set_and_increment_control,
            loop_body=self.code_in_block_range(
                block=true_branch_block,
                end_block=merge_block,
                merge_blocks=merge_blocks,
                next_case_block=next_case_block,
                switch_label_num=switch_label_num)
        )

    def _selection_str(self, true_branch_block, merge_block, block, merge_blocks, next_case_block, switch_label_num) -> str:
        return self.langauge.selection_str_pre_format(CodeType.GLOBAL_ARRAY, block).format(
            cntrl=self.language.set_and_increment_control,
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
        return self.language.switch_full_str(code_type=CodeType.GLOBAL_ARRAY, case_code=case_code,
                                             default_code=default_code, block=block)

    def full_program_aux(self, control_flow_code):
        return self.language.full_program(CodeType.GLOBAL_ARRAY, control_flow_code)
