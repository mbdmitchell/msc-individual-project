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


def example_cfg_if_else() -> CFG:
    """Return if-else CFG"""
    g = _generate_multi_di_graph_from_edges([(1, 2), (1, 3), (2, 4), (3, 4)])
    return CFG.CFG(graph=g)


def example_cfg_while_loop() -> CFG:
    """Return while CFG"""
    g = _generate_multi_di_graph_from_edges([(1, 2), (2, 4), (2, 3), (3, 2)])
    return CFG.CFG(graph=g)


def example_cfg_switch_while_combo() -> CFG:
    """Return combo_all_cfs CFG"""
    g = _generate_multi_di_graph_from_edges([(1, 2), (1, 3), (2, 8), (2, 4), (3, 5), (3, 6), (3, 7),
                                             (4, 2), (5, 9), (6, 9), (7, 9), (8, 10), (9, 10)])
    return CFG.CFG(graph=g)

def example_cfg_multigraph() -> CFG:
    g = _generate_multi_di_graph_from_edges([(1, 2), (1, 2), (1, 2), (1, 3)])
    return CFG.CFG(graph=g)

if __name__ == '__main__':
    cfgs = [example_cfg_if_else(), example_cfg_while_loop(), example_cfg_switch_while_combo()]
    for ix, cfg in enumerate(cfgs):
        cfg.save_as(f'test{ix}.pickle', CFG.GraphFormat.CFG)
