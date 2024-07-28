from __future__ import annotations

import pickle
import queue
import random
from datetime import timedelta, datetime

from CFG import CFG
import networkx as nx


class BlockData:
    """Little helper so i dont accidentally muddle param order."""
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
    def __init__(self, f, t, m):
        self._false_block = f
        self._true_block = t
        self._merge_block = m

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
    def __init__(self, t, m):
        self._true_block = t
        self._merge_block = m

    def __iter__(self):
        yield self._true_block
        yield self._merge_block

    def true_block(self):
        return self._true_block

    def merge_block(self):
        return self._merge_block


def _generate_cfg(seed,
                  depth,
                  is_complex: bool,
                  allow_fallthrough: bool,
                  min_successors, max_successors,
                  verbose=False,
                  break_continue_probability=0.0):
    random.seed(seed)
    generator = CFGGenerator()._add_simple_cfg(depth, allow_fallthrough, min_successors, max_successors)
    if is_complex:
        generator = generator._add_breaks_and_continues(break_continue_probability)
    cfg = generator.get_cfg()

    if verbose:
        for node in cfg.nodes(data=True):
            print(node)
        for node in cfg.nodes():
            print(node, cfg.out_edges(node))

    return cfg


class CFGGenerator:

    def __init__(self):
        self._next_id = 2
        graph = CFGGenerator._empty_graph(1)
        self._cfg = CFG(graph=graph, entry_block=1)
        self.visited_blocks = set()

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
        return nx.empty_graph(range(1, no_of_nodes+1), create_using)

    def _move_block_successors_to(self, source, target):
        block_successors = self._cfg.out_edges_destinations(source)
        if len(block_successors) == 0:
            return
        if target in block_successors:
            block_successors.remove(target)
        self._cfg.add_successors(block_successors, target)
        self._cfg.remove_edges_from(list(self._cfg.out_edges(source)))

    def _choose_merge_block(self, block_data: BlockData, probability_function=None):
        if not (block_data.outer_header() or block_data.outer_merge()):
            merge_with_outer = False
        elif not self._cfg.is_loop_header(block_data.outer_header()):
            merge_with_outer = False
        elif probability_function is None:
            merge_with_outer = random.choice([True, False]) if block_data.outer_merge() else False
        else:
            merge_with_outer = probability_function()

        return block_data.outer_merge() if merge_with_outer else self._get_id()

    def _make_basic(self, block_data: BlockData) -> list[int]:  # all other _make functions return list
        """
        O->... => O->O->...
        :return new_block
        """

        new_block = self._get_id()

        self._move_block_successors_to(source=block_data.block(), target=new_block)

        block: int = block_data.block()
        self._cfg.add_edge(block, new_block)

        return [new_block]

    def _make_selection(self, block_data: BlockData) -> RelatedBlocksSelection:
        """
        O-> ... O
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

    def _make_switch(self, block_data: BlockData, no_of_branches, allow_fallthrough: bool) -> RelatedBlocksSwitch:
        """ Add switch w/ possible fallthrough
        O-> ... O
               /\
              O O
              \/
              O
        allow_fallthrough: required as some languages, e.g., WGSL don't allow it
        """

        block = block_data.block()

        cases = [self._get_id() for _ in range(no_of_branches-1)]
        default_branch = self._get_id()

        merge_block = self._choose_merge_block(block_data)  # TODO: in tree-like switches, merge_block == default block

        self._move_block_successors_to(source=block, target=merge_block)

        for ix, case_id in enumerate(cases):

            self._cfg.add_edge(block, cases[ix])

            if allow_fallthrough:
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

    def _build_rand_construct(self, block_data: BlockData, allow_fallthrough: bool, min_successors, max_successors):
        choice = random.choice([self._make_selection, self._make_loop, self._make_switch, self._make_basic])
        if choice == self._make_switch:
            return choice(block_data, random.randint(min_successors, max_successors), allow_fallthrough)
        else:
            return choice(block_data)

    def get_cfg(self):
        return self._cfg

    def _add_simple_cfg(self, depth, allow_fallthrough: bool, min_successors, max_successors):
        """Loops, selections, and switches. No continues or breaks."""
        blocks = queue.Queue()
        blocks.put(BlockData(block=1, outer_merge=None, outer_header=None, current_depth=0))

        while not blocks.empty():

            block_data = blocks.get()

            if block_data.current_depth() < depth:
                if block_data.block() in self.visited_blocks:
                    continue
                next_blocks = self._build_rand_construct(block_data, allow_fallthrough, min_successors, max_successors)
                self._visit(block_data.block())
                for nb in next_blocks:
                    if nb in self.visited_blocks:
                        continue
                    blocks.put(BlockData(block=nb,
                                         outer_merge=block_data.outer_merge(),
                                         outer_header=block_data.outer_header(),
                                         current_depth=block_data.current_depth() + 1))
        return self

    def _remove_all_self_loops(self):
        """There is a bug that infrequently causes unintended self loops to be created. This fn removes them until the
        bug can be addressed"""
        for n in self._cfg.nodes():
            while (n, n) in self._cfg.graph.edges(n):
                self._cfg.remove_edge(n, n)

    def _add_continue(self, block, loop_header):
        edges = list(self._cfg.graph.edges(nbunch=block))
        self._cfg.graph.remove_edges_from(ebunch=edges)
        self._cfg.add_edge(block, loop_header)
        self._cfg.add_node_attribute(block, 'ContinueBlock', True)

    def _add_break(self, block, loop_header):
        merge_block = self._cfg.merge_block(loop_header)
        edges = list(self._cfg.graph.edges(nbunch=block))
        self._cfg.graph.remove_edges_from(ebunch=edges)
        self._cfg.add_edge(block, merge_block)
        self._cfg.add_node_attribute(block, 'BreakBlock', True)

    def _add_breaks_and_continues(self, insert_probability: float):

        self._remove_all_self_loops()  # temp bug fix

        loop_headers = [block for block in self._cfg.nodes() if self._cfg.is_loop_header(block)]

        if len(loop_headers) == 0:
            return self

        for header in loop_headers:

            visited = set()
            def is_sole_inblock_for_a_dst_block(block):  # dst block(s) all have multiple blocks pointing to it
                return all(len(self._cfg.in_edges_nx_count(dst)) > 1 for dst in self._cfg.out_edges_destinations(block))

            def out_dst_equals_loop_header(block):
                """true iff out_degree = 1 and the dst = loop header"""
                if self.get_cfg().out_degree(block) != 1:
                    return False
                return self.get_cfg().out_edges_destinations(block)[0] == header

            # todo: replace all self._cfg with self.get_cfg() where poss.

            # calc all blocks in true branch before the merge block (or another loop header)

            true_branch_block = self._cfg.out_edges_destinations(header)[1]

            q = queue.Queue()
            q.put(true_branch_block)

            while not q.empty():

                current_block = q.get()

                if current_block in visited \
                        or self._cfg.merge_block(header) == current_block \
                        or self._cfg.is_loop_header(current_block) \
                        or (not self._cfg.is_end_node(current_block)
                            and self._cfg.out_edges_destinations(current_block)[0] != header):
                    continue

                visited.add(current_block)

                if not (is_sole_inblock_for_a_dst_block(current_block)
                        or self._cfg.is_header_block(current_block)
                        or out_dst_equals_loop_header(current_block)):

                    # do thing with that block, e.g. add break or continue
                    if insert_probability > random.random():
                        br_or_cnt = random.choice([self._add_break, self._add_continue])
                        br_or_cnt(current_block, header)

                # add its successors
                for dst in self._cfg.out_edges_destinations(current_block):
                    if dst not in visited:
                        q.put(dst)

        return self

    def generate_simple(self, seed, depth, allow_fallthrough: bool, verbose=False):
        return _generate_cfg(seed, depth, is_complex=False, allow_fallthrough=allow_fallthrough, verbose=verbose)

    def generate_complex(self, seed, depth, allow_fallthrough: bool, break_continue_probability: float, verbose=False):
        return _generate_cfg(
            seed=seed,
            depth=depth,
            is_complex=True,
            allow_fallthrough=allow_fallthrough,
            break_continue_probability=break_continue_probability,
            verbose=verbose
        )

    def generate_cfgs(self,
                      target_filepath: str,
                      no_of_graphs: int,
                      min_depth: int,
                      max_depth: int,
                      min_successors: int,
                      max_successors: int,
                      allow_fallthrough: bool,
                      is_complex: bool = True,
                      break_continue_probability: float = 0.0,
                      seed: int = None):

        rand = random.Random()
        rand.seed(seed)

        generated_hashes = set()
        TIME_LIMIT = timedelta(seconds=5)  # if it can't generate a new CFG in TIME_LIMIT, early return.

        for i in range(no_of_graphs):

            start_time = datetime.now()
            while True:
                if datetime.now() - start_time > TIME_LIMIT:
                    print(f"Aborted graph generation for graph {i} (>{TIME_LIMIT} elapsed)")
                    return  # or continue, if you want to skip this CFG and try the next one

                depth = rand.randint(min_depth, max_depth)
                cfg = _generate_cfg(seed, depth, is_complex, allow_fallthrough, min_successors, max_successors,
                                         False, break_continue_probability)
                cfg_hash = hash(cfg)
                if cfg_hash not in generated_hashes:
                    generated_hashes.add(cfg_hash)
                    break

            with open(f'{target_filepath}/graph_{i}.pickle', "wb") as f:
                pickle.dump(cfg, f)

