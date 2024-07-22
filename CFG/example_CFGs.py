import CFG
import networkx as nx

def _generate_multi_di_graph_from_edges(edges) -> nx.MultiDiGraph:
    """
    Parameters
        edges : container of edges
            Each edge given in the container will be added to the
            graph. The edges must be given as 2-tuples (u, v) or
            3-tuples (u, v, d) where d is a dictionary containing edge data.
    """
    g = nx.MultiDiGraph()
    g.add_edges_from(edges)
    return g


def cfg_0() -> CFG:
    """1->2->3->4"""
    g = _generate_multi_di_graph_from_edges([(1, 2), (2, 3), (3, 4)])
    cfg = CFG.CFG(graph=g, entry_block=1)
    return cfg


# SELECTION

def cfg_if_1() -> CFG:
    """Return simple if-else CFG"""
    g = _generate_multi_di_graph_from_edges([(1, 2), (1, 3), (2, 4), (3, 4)])
    cfg = CFG.CFG(graph=g, entry_block=1)
    cfg.add_node_attribute(1, "SelectionHeader", True)
    cfg.add_node_attribute(1, 'Merge', 4)
    return cfg


def cfg_if_2() -> CFG:
    """
            1
           / \
          2   3
         / \   \
       〈   4   〉
         \  |  /
          \ |/
           5
    """
    g = _generate_multi_di_graph_from_edges([(1, 2), (1, 3),
                                             (2, 5), (2, 4),
                                             (3, 5),
                                             (4, 5)])
    cfg = CFG.CFG(graph=g, entry_block=1)
    cfg.add_node_attribute(1, 'SelectionHeader', True)
    cfg.add_node_attribute(2, 'SelectionHeader', True)
    cfg.add_node_attribute(1, 'Merge', 5)
    cfg.add_node_attribute(2, 'Merge', 5)
    return cfg


def cfg_if_3_nested() -> CFG:
    """
            1
           / \
          2   3
         / \   \
        4   5   〉
         \  |  |
          \ | |
           6 |
            \|
            7
    """
    g = _generate_multi_di_graph_from_edges([(1, 2), (1, 3),
                                             (2, 4), (2, 5),
                                             (3, 7),
                                             (4, 6),
                                             (5, 6),
                                             (6, 7)])
    cfg = CFG.CFG(graph=g, entry_block=1)
    cfg.add_node_attribute(1, 'SelectionHeader', True)
    cfg.add_node_attribute(2, 'SelectionHeader', True)
    cfg.add_node_attribute(1, 'Merge', 7)
    cfg.add_node_attribute(2, 'Merge', 6)
    return cfg


def cfg_if_4_nested() -> CFG:
    """
            1
           / \
          /   \
         2     3
        / \    |
       4  5    |
       \  /   /
        6 <--+
    """
    g = _generate_multi_di_graph_from_edges([(1, 2), (1, 3), (2, 4), (2, 5), (3, 6), (4, 6), (5, 6)])
    cfg = CFG.CFG(graph=g, entry_block=1)
    cfg.add_node_attribute(1, "SelectionHeader", True)
    cfg.add_node_attribute(1, 'Merge', 6)
    cfg.add_node_attribute(2, "SelectionHeader", True)
    cfg.add_node_attribute(2, 'Merge', 6)
    return cfg


def cfg_if_5_nested() -> CFG:
    """
            1
           / \
          /   \
         2     3
        / \   / \
       4  5  6   7
       \  /  \  /
        \/    \/
         \   /
          [8]
    """
    g = _generate_multi_di_graph_from_edges(
        [(1, 2), (1, 3), (2, 4), (2, 5), (3, 6), (3, 7), (4, 8), (5, 8), (6, 8), (7, 8)])
    cfg = CFG.CFG(graph=g, entry_block=1)
    cfg.add_node_attribute(1, "SelectionHeader", True)
    cfg.add_node_attribute(2, "SelectionHeader", True)
    cfg.add_node_attribute(3, "SelectionHeader", True)
    cfg.add_node_attribute(1, 'Merge', 8)
    cfg.add_node_attribute(2, 'Merge', 8)
    cfg.add_node_attribute(3, 'Merge', 8)
    return cfg


# LOOP:

def cfg_while_1() -> CFG:
    """
         1
         |
      +->2--+
      |  |  |
      |  3  |
      |  |  |
      +--4  |
            |
         5<-+
    """

    g = _generate_multi_di_graph_from_edges([(1, 2),
                                             (2, 5), (2, 3),
                                             (3, 4),
                                             (4, 2)])
    cfg = CFG.CFG(graph=g, entry_block=1)
    cfg.add_node_attribute(2, 'SelectionHeader', True)
    cfg.add_node_attribute(2, 'LoopHeader', True)  # LoopHeaders ARE SelectionHeaders
    cfg.add_node_attribute(2, 'Merge', 5)
    return cfg


def cfg_while_2_nested() -> CFG:
    """
    +--->1---F--+
    |    T      |
    |    v      |
    | +->2--+   |
    | |  T  |   |
    | |  V  |   |
    | +--3  |   |
    |       F   |
    |       |   |
    +----4--+   |
                |
         5<-----+
    """
    g = _generate_multi_di_graph_from_edges([(1, 5), (1, 2), (2, 4), (2, 3), (3, 2), (4, 1)])
    cfg = CFG.CFG(graph=g, entry_block=1)
    cfg.add_node_attribute(1, 'SelectionHeader', True)
    cfg.add_node_attribute(1, 'LoopHeader', True)
    cfg.add_node_attribute(1, 'Merge', 5)
    cfg.add_node_attribute(2, 'SelectionHeader', True)
    cfg.add_node_attribute(2, 'LoopHeader', True)
    cfg.add_node_attribute(2, 'Merge', 4)
    return cfg


def cfg_early_1_continue() -> CFG:
    """ Early continue on $6
          1
          |
      +-->2---+
      |   |   |
      |   3   |
      |  / \  |
      |  \  6 |
      +<--4 | |
      ^     | |
      +-----+ |
              |
          5<--+
    """

    g = _generate_multi_di_graph_from_edges([(1, 2),
                                             (2, 5), (2, 3),
                                             (3, 4), (3, 6),
                                             (4, 2),
                                             (6, 2)])
    cfg = CFG.CFG(graph=g, entry_block=1)
    cfg.add_node_attribute(2, 'SelectionHeader', True)
    cfg.add_node_attribute(2, 'LoopHeader', True)
    cfg.add_node_attribute(2, 'Merge', 5)

    cfg.add_node_attribute(3, 'SelectionHeader', True)
    cfg.add_node_attribute(3, 'Merge', 4)

    cfg.add_node_attribute(6, 'ContinueBlock', True)

    return cfg


def cfg_early_2_break() -> CFG:
    """ Early break on $7
          1
          |
      +-->2--+
      |   |  |
      |   3  |
      |  /\  |
      | 6 7->|
      | \    |
      +<-4   |
             |
          5<-+
    """

    g = _generate_multi_di_graph_from_edges([(1, 2),
                                             (2, 5), (2, 3),
                                             (3, 6), (3, 7),
                                             (4, 2),
                                             (6, 4),
                                             (7, 5)])
    cfg = CFG.CFG(graph=g, entry_block=1)
    cfg.add_node_attribute(2, 'SelectionHeader', True)
    cfg.add_node_attribute(2, 'LoopHeader', True)
    cfg.add_node_attribute(2, 'Merge', 5)

    cfg.add_node_attribute(3, 'SelectionHeader', True)
    cfg.add_node_attribute(3, 'Merge', 4)

    cfg.add_node_attribute(7, 'BreakBlock', True)

    return cfg


def cfg_early_3_continue_and_break_in_switch() -> CFG:
    """
            1
            |
      +-----2 ----+
      |     |     |
      |     3     |
      |   / | \   |
      +--4  6  5  |   # case 0, default, and case 1 resp. (ordering tweaked for readability)
      |     |   \ |
      +-----7   | |
                | |
            8<--┴-+
    """

    g = _generate_multi_di_graph_from_edges([
        (1, 2),
        (2, 8), (2, 3),
        (3, 4), (3, 5), (3, 6),
        (4, 2),
        (5, 8),
        (6, 7),
        (7, 2)
    ])

    cfg = CFG.CFG(graph=g, entry_block=1)

    cfg.add_node_attribute(2, 'SelectionHeader', True)
    cfg.add_node_attribute(2, 'LoopHeader', True)
    cfg.add_node_attribute(2, 'Merge', 8)

    cfg.add_node_attribute(3, 'SelectionHeader', True)
    cfg.add_node_attribute(3, 'SwitchBlock', True)
    cfg.add_node_attribute(3, 'Merge', 6)  # in lieu of 'actual' merge block, switches use default case

    cfg.add_node_attribute(4, 'ContinueBlock', True)
    cfg.add_node_attribute(5, 'BreakBlock', True)

    return cfg


# SWITCH
def cfg_switch_1_fallthrough() -> CFG:
    """ Simple switch w/ fallthrough
        1
       / \
      2->3
        /
       4
    """
    g = _generate_multi_di_graph_from_edges([(1, 2), (1, 3), (2, 3), (3, 4)])
    cfg = CFG.CFG(graph=g, entry_block=1)
    cfg.add_node_attribute(1, 'SelectionHeader', True)
    cfg.add_node_attribute(1, 'SwitchBlock', True)
    cfg.add_node_attribute(1, 'Merge', 4)
    return cfg


def cfg_switch_2_nofallthrough() -> CFG:
    """
        1
       /\
      2  3
      \ /
       4
    """
    g = _generate_multi_di_graph_from_edges([(1, 2), (1, 3), (2, 4), (3, 4)])
    cfg = CFG.CFG(graph=g, entry_block=1)
    cfg.add_node_attribute(1, 'SelectionHeader', True)
    cfg.add_node_attribute(1, 'SwitchBlock', True)
    cfg.add_node_attribute(1, 'Merge', 4)
    return cfg


def cfg_switch_3_mix() -> CFG:
    """
         1
       / | \
      2  3  \
      \  \_> 4
       \    /
        \  /
        [5]
    """
    g = _generate_multi_di_graph_from_edges([(1, 2), (1, 3), (1, 4),
                                             (2, 5),
                                             (3, 4),
                                             (4, 5)])
    cfg = CFG.CFG(graph=g, entry_block=1)
    cfg.add_node_attribute(1, 'SelectionHeader', True)
    cfg.add_node_attribute(1, 'SwitchBlock', True)
    cfg.add_node_attribute(1, 'Merge', 5)
    return cfg


def cfg_switch_4_with_loop() -> CFG:
    """
          1
        /  \
     +>2-+  3
     | | |  |
     +-4 |  |
        /   |
       5    |
       \   /
        \ /
         6
    """
    g = _generate_multi_di_graph_from_edges([(1, 2), (1, 3),
                                             (2, 5), (2, 4),
                                             (3, 6),
                                             (4, 2),
                                             (5, 6)])
    cfg = CFG.CFG(graph=g, entry_block=1)

    cfg.add_node_attribute(1, 'SelectionHeader', True)
    cfg.add_node_attribute(1, 'SwitchBlock', True)
    cfg.add_node_attribute(1, 'Merge', 6)

    cfg.add_node_attribute(2, 'SelectionHeader', True)
    cfg.add_node_attribute(2, 'LoopHeader', True)
    cfg.add_node_attribute(2, 'Merge', 5)

    return cfg


def cfg_switch_5_with_loop_and_fallthrough() -> CFG:
    """ loop merge block = next case in switch
         1
       / | \
   +->2  |  \
   |  |\ |   \
   +--3 \|   |
         4   5
         |  /|
         | / |
         |/  6
         |  /
         | /
         7
    """
    g = _generate_multi_di_graph_from_edges([(1, 2), (1, 4), (1, 5),
                                             (2, 4), (2, 3),
                                             (3, 2),
                                             (4, 7),
                                             (5, 7), (5, 6),
                                             (6, 7)])
    cfg = CFG.CFG(graph=g, entry_block=1)

    cfg.add_node_attribute(1, 'SelectionHeader', True)
    cfg.add_node_attribute(1, 'SwitchBlock', True)
    cfg.add_node_attribute(1, 'Merge', 7)

    cfg.add_node_attribute(2, 'SelectionHeader', True)
    cfg.add_node_attribute(2, 'LoopHeader', True)
    cfg.add_node_attribute(2, 'Merge', 4)

    cfg.add_node_attribute(5, 'SelectionHeader', True)
    cfg.add_node_attribute(5, 'Merge', 7)

    return cfg


def cfg_switch_6_nested() -> CFG:
    """Tree-like CFG w/ with switch branches that don't *really* merge back together
          ___1___
         /   |   \
        2   _3_   4
       /\  /| |\   \
      5 6 7 8 9 10  11
    """

    g = _generate_multi_di_graph_from_edges([(1, 2), (1, 3), (1, 4),
                                             (2, 5), (2, 6),
                                             (3, 7), (3, 8), (3, 9), (3, 10),
                                             (4, 11)])

    cfg = CFG.CFG(graph=g, entry_block=1)
    cfg.add_node_attribute(1, 'SelectionHeader', True)
    cfg.add_node_attribute(1, 'SwitchBlock', True)
    cfg.add_node_attribute(1, 'Merge', 4)

    cfg.add_node_attribute(2, 'SelectionHeader', True)
    cfg.add_node_attribute(2, 'SwitchBlock', True)
    cfg.add_node_attribute(2, 'Merge', 6)

    cfg.add_node_attribute(3, 'SelectionHeader', True)
    cfg.add_node_attribute(3, 'SwitchBlock', True)
    cfg.add_node_attribute(3, 'Merge', 10)

    return cfg


# COMBOS

def cfg_switch_loop_if_combo() -> CFG:
    """Return combo_all_cfs CFG"""
    g = _generate_multi_di_graph_from_edges([(1, 2), (1, 3),
                                             (2, 8), (2, 4),
                                             (3, 5), (3, 6), (3, 7),
                                             (4, 2),
                                             (5, 9),
                                             (6, 9),
                                             (7, 9),
                                             (8, 10),
                                             (9, 10)])

    cfg = CFG.CFG(graph=g, entry_block=1)

    cfg.add_node_attribute(1, 'SelectionHeader', True)
    cfg.add_node_attribute(1, 'Merge', 10)

    cfg.add_node_attribute(2, 'SelectionHeader', True)
    cfg.add_node_attribute(2, 'LoopHeader', True)
    cfg.add_node_attribute(2, 'Merge', 8)

    cfg.add_node_attribute(3, 'SelectionHeader', True)
    cfg.add_node_attribute(3, 'SwitchBlock', True)
    cfg.add_node_attribute(3, 'Merge', 9)

    return cfg

def cfg_merge_which_is_also_header_1_selection() -> CFG:
    g = _generate_multi_di_graph_from_edges([
        (1,2), (1,3),
        (2,4),
        (3,4),
        (4,5), (4,6),
        (5,7),
        (6,7)
    ])

    cfg = CFG.CFG(graph=g, entry_block=1)

    cfg.add_node_attribute(1, 'SelectionHeader', True)
    cfg.add_node_attribute(1, 'Merge', 4)

    cfg.add_node_attribute(4, 'SelectionHeader', True)
    cfg.add_node_attribute(4, 'Merge', 7)

    return cfg


def cfg_merge_which_is_also_header_2_loop() -> CFG:
    g = _generate_multi_di_graph_from_edges([
        (1,2), (1,3),
        (2,4), (2,5),
        (3,1),
        (4,6),
        (5,6)
    ])

    cfg = CFG.CFG(graph=g, entry_block=1)

    cfg.add_node_attribute(1, 'SelectionHeader', True)
    cfg.add_node_attribute(1, 'LoopHeader', True)
    cfg.add_node_attribute(1, 'Merge', 2)

    cfg.add_node_attribute(2, 'SelectionHeader', True)
    cfg.add_node_attribute(2, 'Merge', 6)

    return cfg

# -----------------------------------------------------------------------------------------------------------------------
