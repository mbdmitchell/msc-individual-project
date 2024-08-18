from __future__ import annotations

import logging
import pickle
import queue
import random
from datetime import timedelta, datetime

from CFG import CFG
import networkx as nx

from languages import Language


class BlockData:
    """
    A helper class to manage block data and ensure parameter order is maintained.

    block (int): The block identifier.
    outer_merge (int | None): The outer merge block identifier, if any.
    outer_header (int | None): The outer header block identifier, if any.
    current_depth (int): The current depth of the block in the control flow graph.
    """

    def __init__(self, block: int, outer_merge: int | None, outer_header: int | None, current_depth: int):
        self._block = block
        self._outer_merge = outer_merge
        self._outer_header = outer_header
        self._current_depth = current_depth

    def __iter__(self):
        yield self._block
        yield self._outer_merge
        yield self._outer_header
        yield self._current_depth

    def block(self) -> int:
        return self._block

    def outer_merge(self):
        return self._outer_merge

    def outer_header(self):
        return self._outer_header

    def current_depth(self):
        return self._current_depth


# NB: I have intentionally not make a `RelatedBlocks` parent class.
# "Premature inheritance is the root of all evil" -- not Knuth

class RelatedBlocksSwitch:
    def __init__(self, cases: list[int], default_block: int, merge_block: int):
        self._cases = cases
        self._default_block = default_block
        self._merge_block = merge_block

    def __iter__(self):
        for case in self._cases:
            yield case
        yield self._default_block
        yield self._merge_block

    def cases(self):
        return self._cases

    def default_block(self):
        return self._default_block

    def merge_block(self):
        return self._merge_block


class RelatedBlocksSelection:
    def __init__(self, false_block, true_block, merge_block):
        self._false_block = false_block
        self._true_block = true_block
        self._merge_block = merge_block

    def __iter__(self):
        yield self._true_block
        yield self._false_block
        yield self._merge_block

    def false_block(self):
        return self._false_block

    def true_block(self):
        return self._true_block

    def merge_block(self):
        return self._merge_block


class RelatedBlocksLoop:
    def __init__(self, true_block, merge_block):
        self._true_block = true_block
        self._merge_block = merge_block

    def __iter__(self):
        yield self._true_block
        yield self._merge_block

    def true_block(self):
        return self._true_block

    def merge_block(self):
        return self._merge_block


class GeneratorConfig:
    """Dictates which CFG features are and aren't allowed in the CFG generation"""

    def __init__(self,
                 basic: bool,
                 loop: bool,
                 selection: bool,
                 switch_fallthrough: bool,
                 switch_default: bool,
                 break_: bool,
                 continue_: bool):
        self.allow_basic = basic
        self.allow_loop = loop
        self.allow_selection = selection
        self.allow_switch_fallthrough = switch_fallthrough
        self.allow_switch_default = switch_default
        self.allow_break = break_
        self.allow_continue = continue_

    @staticmethod
    def allow_all(language: Language) -> 'GeneratorConfig':
        """Allow all options for a given language"""
        return GeneratorConfig(basic=True,
                               loop=True,
                               selection=True,
                               switch_fallthrough=language.allows_switch_fallthrough,
                               switch_default=True,
                               break_=True,
                               continue_=True)

    @staticmethod
    def random(language: Language) -> 'GeneratorConfig':
        """Return random GeneratorConfig. Choose one attr to definitely set to True so cfg can always be created)"""

        flags = [False] * 4

        chosen_index = random.choice(range(4))
        flags[chosen_index] = True

        flags = [flag or random.choice([True, False]) for flag in flags]

        return GeneratorConfig(
            basic=flags[0],
            loop=flags[1],
            selection=flags[2],
            switch_fallthrough=random.choice([language.allows_switch_fallthrough, False]),
            switch_default=flags[3],
            break_=random.choice([True, False]),
            continue_=random.choice([True, False])
        )

    def no_constructs_allowed(self) -> bool:
        return not any([self.allow_basic, self.allow_loop, self.allow_selection, self.allow_switch_fallthrough,
                        self.allow_switch_default])


class CFGGenerator:

    def __init__(self, generator_config=None):
        self._generator_config = generator_config
        self._next_id = 2
        self._cfg = CFG(graph=CFGGenerator._empty_graph(1), entry_block=1)
        self.visited_blocks = set()

    def _reset(self):
        self._next_id = 2
        self._cfg = CFG(graph=CFGGenerator._empty_graph(1), entry_block=1)
        self.visited_blocks = set()

    @property
    def _allowed_construct_functions(self):
        construct_conditions = [
            (self._generator_config.allow_selection, self._make_selection),
            (self._generator_config.allow_loop, self._make_loop),
            (self._generator_config.allow_switch_default or self._generator_config.allow_switch_fallthrough,
             self._make_switch),
            (self._generator_config.allow_basic, self._make_basic)
        ]
        return [construct for condition, construct in construct_conditions if condition]

    @property
    def _allowed_break_continue_functions(self):
        conditions = [
            (self._generator_config.allow_break, self._add_break),
            (self._generator_config.allow_continue, self._add_continue)
        ]
        return [construct for condition, construct in conditions if condition]

    @property
    def _is_allowed_break_or_continue(self):
        return len(self._allowed_break_continue_functions) != 0

    def _get_id(self) -> int:
        val = self._next_id
        self._next_id += 1
        return val

    def _visit(self, block):
        if block in self.visited_blocks:
            raise ValueError("Already visited")
        self.visited_blocks.add(block)

    @staticmethod
    def _empty_graph(no_of_nodes: int, create_using=nx.MultiDiGraph):
        return nx.empty_graph(range(1, no_of_nodes + 1), create_using)

    def _move_block_successors_to(self, source, target):
        block_successors = self.get_cfg().out_edges_destinations(source)
        if len(block_successors) == 0:
            return
        if target in block_successors:
            block_successors.remove(target)
        self.get_cfg().add_successors(block_successors, target)
        self.get_cfg().remove_edges_from(list(self.get_cfg().out_edges(source)))

    def _choose_merge_block(self, block_data: BlockData):
        # TODO: add merge behaviour to generator_config
        if not (block_data.outer_header() or block_data.outer_merge()):
            merge_with_outer = False
        elif not self.get_cfg().is_loop_header(block_data.outer_header()):
            merge_with_outer = False
        else:
            merge_with_outer = random.choice([block_data.outer_merge(), False])

        return block_data.outer_merge() if merge_with_outer else self._get_id()

    def _make_basic(self, block_data: BlockData) -> list[int]:
        """
        Converts a basic block structure from O->... to O->O->...

        This function creates a new block, moves the successors of the existing block to the new block,
        and then connects the existing block to the new block.
        """

        new_block = self._get_id()

        self._move_block_successors_to(source=block_data.block(), target=new_block)

        block: int = block_data.block()
        self.get_cfg().add_edge(block, new_block)

        return [new_block]

    def _make_selection(self, block_data: BlockData) -> RelatedBlocksSelection:
        """
        Creates a selection (if-else) structure in the control flow graph.

        The function constructs a control flow structure that branches into two paths (true and false),
        both of which merge back into a single block.

        The structure is visualized as:
            O -> ... O
                    /\
                   O O
                   \/
                   O
        """

        false_block = self._get_id()
        true_block = self._get_id()
        merge_block = self._choose_merge_block(block_data)

        block = block_data.block()

        self._move_block_successors_to(source=block, target=merge_block)

        self._cfg.add_edge(block, false_block)
        self._cfg.add_edge(block, true_block)
        self._cfg.add_edge(false_block, merge_block)
        self._cfg.add_edge(true_block, merge_block)

        self._cfg.add_node_attribute(block, "SelectionHeader", True)
        self._cfg.add_node_attribute(block, 'Merge', merge_block)

        return RelatedBlocksSelection(false_block, true_block, merge_block)

    def _make_switch(self, block_data: BlockData, no_of_branches) -> RelatedBlocksSwitch:
        """
        Adds a switch construct with possible fallthrough to the control flow graph.

        The function constructs a switch control flow structure that branches into multiple cases
        and a default branch. Each branch can optionally fall through to the next case or merge
        back into a single block.

        The structure is visualized as:
            O -> ... O
                    /\
                   O O
                   \/
                   O

        allow_fallthrough (bool): Determines whether fallthrough between cases is allowed.
                                  Required as some languages (e.g., WGSL) don't allow fallthrough.
        """

        block = block_data.block()

        cases = [self._get_id() for _ in range(no_of_branches - 1)]
        default_branch = self._get_id()

        merge_block = self._choose_merge_block(block_data)  # TODO: in tree-like switches, merge_block == default block

        self._move_block_successors_to(source=block, target=merge_block)

        for ix, case_id in enumerate(cases):

            self._cfg.add_edge(block, cases[ix])

            if self._generator_config.allow_switch_fallthrough:
                fallthrough = random.choice([True, False])
            else:
                fallthrough = False

            if fallthrough:
                if ix + 1 in range(len(cases)):
                    target = cases[ix + 1]
                else:
                    target = default_branch
                self._cfg.add_edge(case_id, target)
            else:
                self._cfg.add_edge(case_id, merge_block)

        self._cfg.add_edge(block, default_branch)
        self._cfg.add_edge(default_branch, merge_block)

        self._cfg.add_node_attribute(block, "SelectionHeader", True)
        self._cfg.add_node_attribute(block, "SwitchBlock", True)
        self._cfg.add_node_attribute(block, 'Merge', merge_block)

        return RelatedBlocksSwitch(cases, default_branch, merge_block)

    def _make_loop(self, block_data: BlockData) -> RelatedBlocksLoop:
        """
        The function constructs a loop control flow structure with a single entry point, a body (true block),
        and a merge block.
        O-> ...     +>O--+
                    | |  |
                    +-O  |
                         |
                      O<-+
                      |
                      V
                     ...
        """

        block = block_data.block()

        merge_block = self._choose_merge_block(block_data)
        true_block = self._get_id()

        self._move_block_successors_to(source=block, target=merge_block)

        self._cfg.add_edge(block, merge_block)

        self._cfg.add_edge(block, true_block)
        self._cfg.add_edge(true_block, block)

        self._cfg.add_node_attribute(block, "SelectionHeader", True)
        self._cfg.add_node_attribute(block, "LoopHeader", True)
        self._cfg.add_node_attribute(block, 'Merge', merge_block)

        return RelatedBlocksLoop(true_block, merge_block)

    def get_cfg(self):
        return self._cfg

    # -----------------------------------------------------------------------------------------------------------------

    def build_random_construct(self, block_data, min_successors, max_successors):

        if len(self._allowed_construct_functions) == 0:
            return None

        choice = random.choice(self._allowed_construct_functions)
        if choice == self._make_switch:
            return choice(block_data, random.randint(min_successors, max_successors))
        else:
            return choice(block_data)

    def generate(self, depth, min_successors, max_successors):

        self._reset()

        blocks = queue.Queue()
        blocks.put(BlockData(block=1, outer_merge=None, outer_header=None, current_depth=0))

        while not blocks.empty():

            block_data = blocks.get()

            if block_data.current_depth() < depth:
                if block_data.block() in self.visited_blocks:
                    continue
                next_blocks = self.build_random_construct(block_data, min_successors, max_successors)
                self._visit(block_data.block())
                for nb in next_blocks:
                    if nb in self.visited_blocks:
                        continue
                    blocks.put(BlockData(block=nb,
                                         outer_merge=block_data.outer_merge(),
                                         outer_header=block_data.outer_header(),
                                         current_depth=block_data.current_depth() + 1))

        self._remove_all_self_loops()  # TODO: don't *think* this is needed now, it's harmless so keep until can know
        self._add_breaks_and_continues(insert_probability=1)

        return self.get_cfg()

    # -----------------------------------------------------------------------------------------------------------------

    def _remove_all_self_loops(self):
        """There is (was?) a rare bug that causes unintended self loops to be created. This fn removes them until
        the root cause can be addressed"""
        for n in self.get_cfg().nodes():
            while (n, n) in self.get_cfg().graph.edges(n):
                self.get_cfg().remove_edge(n, n)

    def _add_continue(self, block, loop_header):
        edges = list(self.get_cfg().graph.edges(nbunch=block))
        self.get_cfg().graph.remove_edges_from(ebunch=edges)
        self.get_cfg().add_edge(block, loop_header)
        self.get_cfg().add_node_attribute(block, 'ContinueBlock', True)

    def _add_break(self, block, loop_header):
        merge_block = self.get_cfg().merge_block(loop_header)
        edges = list(self.get_cfg().graph.edges(nbunch=block))
        self.get_cfg().graph.remove_edges_from(ebunch=edges)
        self.get_cfg().add_edge(block, merge_block)
        self.get_cfg().add_node_attribute(block, 'BreakBlock', True)

    def _add_breaks_and_continues(self, insert_probability: float):

        if not self._is_allowed_break_or_continue:
            return self

        loop_headers = [block for block in self.get_cfg().nodes() if self.get_cfg().is_loop_header(block)]

        if len(loop_headers) == 0:
            return self

        for header in loop_headers:

            visited = set()

            def is_sole_inblock_for_a_dst_block(block):  # dst block(s) all have multiple blocks pointing to it
                return all(len(self.get_cfg().in_edges_nx_count(dst)) > 1 for dst in self.get_cfg().out_edges_destinations(block))

            def out_dst_equals_loop_header(block):
                """true iff out_degree = 1 and the dst = loop header"""
                if self.get_cfg().out_degree(block) != 1:
                    return False
                return self.get_cfg().out_edges_destinations(block)[0] == header

            # calc all blocks in true branch before the merge block (or another loop header)

            true_branch_block = self.get_cfg().out_edges_destinations(header)[1]

            q = queue.Queue()
            q.put(true_branch_block)

            while not q.empty():

                current_block = q.get()

                if current_block in visited \
                        or self.get_cfg().merge_block(header) == current_block \
                        or self.get_cfg().is_loop_header(current_block) \
                        or (not self.get_cfg().is_end_node(current_block)
                            and self.get_cfg().out_edges_destinations(current_block)[0] != header):
                    continue

                visited.add(current_block)

                if not (is_sole_inblock_for_a_dst_block(current_block)
                        or self.get_cfg().is_header_block(current_block)
                        or out_dst_equals_loop_header(current_block)):

                    # do thing with that block, e.g. add break or continue
                    if insert_probability > random.random():
                        br_or_cnt = random.choice(self._allowed_break_continue_functions)
                        br_or_cnt(current_block, header)

                # add its successors
                for dst in self.get_cfg().out_edges_destinations(current_block):
                    if dst not in visited:
                        q.put(dst)

        return self

    def generate_cfgs_method_uniform(self,
                                     target_filepath: str,
                                     no_of_graphs: int,
                                     min_depth: int,
                                     max_depth: int):

        generated_hashes = set()
        TIME_LIMIT = timedelta(seconds=5)  # if it can't generate a new CFG in TIME_LIMIT, early return.

        for i in range(no_of_graphs):

            start_time = datetime.now()

            found_new_cfg = False
            while datetime.now() - start_time < TIME_LIMIT:

                depth = random.randint(min_depth, max_depth)
                cfg = self.generate(depth, min_successors=3, max_successors=5)
                cfg_hash = hash(cfg)

                if cfg_hash not in generated_hashes:
                    found_new_cfg = True
                    generated_hashes.add(cfg_hash)
                    with open(f'{target_filepath}/graph_{i}.pickle', "wb") as f:
                        pickle.dump(cfg, f)
                    break

            if not found_new_cfg:
                logging.info(f"Aborted graph generation (>{TIME_LIMIT} elapsed)")
                return

    @staticmethod
    def generate_cfgs_method_swarm(language,
                                   target_filepath,
                                   no_of_graphs,
                                   min_depth,
                                   max_depth):

        generated_hashes = set()
        TIME_LIMIT = timedelta(seconds=5)  # if it can't generate a new CFG in TIME_LIMIT, early return.

        for i in range(no_of_graphs):

            start_time = datetime.now()
            found_new_cfg = False

            while datetime.now() - start_time < TIME_LIMIT:

                cfg_generator = CFGGenerator(GeneratorConfig.random(language))

                depth = random.randint(min_depth, max_depth)
                cfg = cfg_generator.generate(depth, min_successors=3, max_successors=5)
                cfg_hash = hash(cfg)

                if cfg_hash not in generated_hashes:
                    found_new_cfg = True
                    generated_hashes.add(cfg_hash)
                    with open(f'{target_filepath}/graph_{i}.pickle', "wb") as f:
                        pickle.dump(cfg, f)
                    break

            if not found_new_cfg:
                logging.info(f"Aborted graph generation (>{TIME_LIMIT} elapsed)")
                return
