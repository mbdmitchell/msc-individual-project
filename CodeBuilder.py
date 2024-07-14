from __future__ import annotations
from MergeBlockData import MergeBlockData
from CFG import *
from abc import ABC, abstractmethod
from collections import deque


class CodeBuilder(ABC):

    def __init__(self, cfg: CFG):
        self.cfg = cfg
        self.added_blocks = set()

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

    @abstractmethod
    def _loop_code(self,
                   block: int | None,
                   end_block: int | None,
                   merge_blocks: list[MergeBlockData],
                   switch_label_num: int,
                   next_case_block: int = None) -> str:
        pass

    @abstractmethod
    def _selection_code(self,
                        block: int | None,
                        end_block: int | None,
                        merge_blocks: list[MergeBlockData],
                        switch_label_num: int,
                        next_case_block: int = None) -> str:
        pass

    @abstractmethod
    def _switch_code(self,
                     block: int | None,
                     end_block: int | None,
                     merge_blocks: list[MergeBlockData],
                     switch_label_num: int,
                     next_case_block: int = None) -> str:
        pass

    @abstractmethod
    def code_in_block_range(self,
                            block: int | None,
                            end_block: int | None,
                            merge_blocks: list[MergeBlockData],  # treated like a stack DS,
                            switch_label_num: int,
                            next_case_block: int = None) -> str:
        pass

    @abstractmethod
    def build_code(self) -> str:
        pass
