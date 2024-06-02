# Helper functions for class CFG.generate_valid_cfg()

import itertools
import random
from queue import Queue
from CFG import CFG, NodeType


# TODO: Have seed parameter for all

def generate_random_tree(target_depth: int, max_children_per_node: int = 3) -> CFG:
    """Generate CFG with tree structure. Used as foundation for building CFG"""

    def validate_params():
        if target_depth < 0:
            raise ValueError('Negative depth')
        if max_children_per_node < 1:
            raise ValueError('1+ children')

    validate_params()

    cfg = CFG()

    if target_depth == 0:
        return cfg

    assignable_id = itertools.count(1)
    cfg.add_node(next(assignable_id))  # gen start_node

    q1: Queue[int] = Queue()
    q2: Queue[int] = Queue()

    q1.put(1)

    for _ in range(target_depth):
        while not q1.empty():
            current_node = q1.get()
            no_of_children = random.randrange(1, max_children_per_node + 1)
            children = [next(assignable_id) for _ in range(no_of_children)]
            cfg.add_children(children, current_node)
            [q2.put(c) for c in children]
        q1 = q2
        q2 = Queue()

    return cfg


""" TODO: Impl. following, then replace _generate_tree(...) 
1) Not a "connected graph" 2) Doesn't ensure node %1 has in_degree = 0 

http://misailo.web.engr.illinois.edu/courses/526-sp17/lec1.pdf
"""

'''def _generate_random_dag(n: int, p: float):
    """Generate a random DAG (w/ no disconnected components) of n nodes and edge probability p"""
    random_graph = nx.fast_gnp_random_graph(n, p, directed=True)
    # "u < v" ensures no cycles. (Want to add cycles later in a more controlled way)
    random_dag = nx.MultiDiGraph([(u, v) for (u, v) in random_graph.edges() if u < v])


    # incr. nodes so entry node is %1
    mapping = {node: node + 1 for node in random_dag.nodes()}
    nx.relabel_nodes(random_dag, mapping, copy=False)

    return CFG.CFG(graph=random_dag)
'''


def add_back_edges(cfg: CFG, no_of_back_links: int) -> CFG:
    """Add back edges while ensuring valid CFG."""

    candidate_nodes = [
        node_ for node_ in cfg.nodes()
        if not cfg.node_type(node_) == NodeType.END and
           not CFG.is_start_node(node_) and
           len([ancestor for ancestor in cfg.ancestors(node_) if ancestor != 1]) > 0
    ]

    if len(candidate_nodes) == 0:
        return cfg

    edges_to_add: list[tuple[int, int]] = []

    for _ in range(no_of_back_links):
        rand_source = random.choice(candidate_nodes)

        valid_ancestors = [node_ for node_ in cfg.ancestors(rand_source) if node_ != 1]
        rand_dst = random.choice(valid_ancestors)
        edges_to_add.append((rand_source, rand_dst))

    for edge in edges_to_add:
        source, dst = edge
        cfg.add_edge(source, dst)

    return cfg


def add_forward_edges(cfg: CFG, no_of_back_links: int) -> CFG:
    """Add forward edges while ensuring valid CFG."""

    candidate_nodes = [n for n in cfg.nodes() if not cfg.is_end_node(n)]

    if len(candidate_nodes) == 0:
        return cfg

    edges_to_add: list[tuple[int, int]] = []

    for _ in range(no_of_back_links):
        rand_source = random.choice(candidate_nodes)
        rand_dst = random.choice(list(cfg.descendants(rand_source)))
        edges_to_add.append((rand_source, rand_dst))

    for edge in edges_to_add:
        source, dst = edge
        cfg.add_edge(source, dst)

    return cfg


def add_self_loops(cfg: CFG, no_of_self_loops: int) -> CFG:
    """Add self-loops while ensuring valid CFG. Protect start node accidentally becoming child"""

    candidate_nodes = [n for n in cfg.nodes() if not cfg.is_entry_or_exit_node(n)]

    if len(candidate_nodes) == 0:
        return cfg

    for _ in range(no_of_self_loops):
        rand_node = random.choice(candidate_nodes)
        cfg.add_edge(rand_node, rand_node)

    return cfg


def reduce_no_of_exit_nodes_to_n(cfg: CFG, final_exit_node_count: int):
    exit_nodes: list[int] = cfg.exit_nodes()

    """if len(exit_nodes) <= final_exit_node_count:
        print('NB: Redundant call to reduce_no_of_exit_nodes_to_n().\n'
              'Current number of exit nodes: {en}\n'
              'Requested number: {rn}'.format(en=len(exit_nodes), rn=final_exit_node_count))"""

    while len(exit_nodes) > final_exit_node_count:
        src, dst = random.sample(exit_nodes, 2)
        cfg.add_edge(src, dst)
        exit_nodes.remove(src)  # no longer an exit node
