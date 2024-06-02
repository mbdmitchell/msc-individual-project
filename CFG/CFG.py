import os
import random
from enum import Enum
from typing import Optional
import networkx as nx
import pickle

from matplotlib import pyplot as plt

class NodeType(Enum):
    def __repr__(self):
        return f"<{self.__class__.__name__}.{self.name}: {self.value}>"

    UNCONDITIONAL = 1
    CONDITIONAL = 2
    SWITCH = 3
    END = 4


class GraphFormat(Enum):
    CFG = 0,
    NX_MULTI_DIGRAPH = 1,
    GRAPH_ML = 2
    PNG = 3


class CFG:
    """
    A simple interface for nx.MultiDiGraph, abstracting its implementation details
    to provide a cleaner interface for CFGs and decouple rest of the project components
    from a specific graph implementation.
    """

    # FILE HANDLING

    def _save_image(cfg, filename: str):
        plt.figure(figsize=(6, 6))
        nx.draw(cfg.graph, with_labels=True, node_size=1000, font_size=20, font_weight='bold', font_color='white', arrowsize=40)
        plt.savefig(filename)
        plt.close()

    def save(self, filepath: str, fmt: GraphFormat = GraphFormat.CFG) -> None:
        """Saves the graph to a file in the specified format."""
        # TODO: Refactor?
        """
        if fmt not in {GraphFormat.NX_MULTI_DIGRAPH, GraphFormat.GRAPH_ML, GraphFormat.CFG}:
            raise TypeError("Chosen GraphFormat not supported")
            
        with open(filepath, 'wb') as file:
            pickle.dump(self.graph, file)
        """

        directory = os.path.dirname(filepath)
        if not os.path.exists(directory):
            os.makedirs(directory)

        if fmt == GraphFormat.GRAPH_ML:
            nx.write_graphml(self.graph, filepath)
        elif fmt == GraphFormat.CFG:
            with open(filepath, 'wb') as file:
                pickle.dump(self, file)
        elif fmt == GraphFormat.NX_MULTI_DIGRAPH:
            with open(filepath, 'wb') as file:
                pickle.dump(self.graph, file)
        elif fmt == GraphFormat.PNG:
            self._save_image(filepath)
        else:
            raise ValueError('Unrecognised GraphFormat')

    def load(self, filepath: str, fmt: GraphFormat = GraphFormat.CFG) -> 'CFG':
        """
        Loads a graph from a file in the specified format.
        """

        if fmt not in {GraphFormat.NX_MULTI_DIGRAPH, GraphFormat.CFG}:
            raise TypeError("Chosen GraphFormat not supported")

        if fmt == GraphFormat.GRAPH_ML:
            self.graph = nx.read_graphml(filepath)
        else:
            with open(filepath, 'rb') as file:
                g = pickle.load(file)
                self._load_cfg(g)

        return self

    def _load_cfg(self, cfg_graph: 'CFG') -> None:
        self.graph = cfg_graph.graph
        # Add additional attributes from CFG graph if it becomes necessary

    # CTOR

    def __init__(self, filepath: Optional[str] = None,
                 graph: Optional[nx.MultiDiGraph] = None):
        """filepath to pickle'd CFG obj"""

        if graph and filepath:
            raise ValueError("Don't include both a graph and filename in the parameters")

        self.graph = nx.MultiDiGraph()

        if graph:
            self.graph = graph
        elif filepath:
            self.load(filepath)

    # GETTERS

    def graph(self) -> nx.MultiDiGraph:  # TODO: def graph_as(fmt: GraphFormat)
        return self.graph

    # ... nodes ...

    def nodes(self) -> list[int]:
        return self.graph.nodes()

    def node_type(self, node: int):
        no_of_children = len(self.children(node))  # don't use self.out_edges as can has multiple edges to same node
        if no_of_children == 0:
            return NodeType.END
        elif no_of_children == 1:
            return NodeType.UNCONDITIONAL
        elif no_of_children == 2:
            return NodeType.CONDITIONAL
        else:
            return NodeType.SWITCH

    @staticmethod
    def is_start_node(node: int):
        return node == 1

    def is_end_node(self, node: int):
        return len(self.graph.out_edges(node)) == 0

    def parents(self, node: int):
        return list(self.graph.predecessors(node))

    def children(self, node: int):
        return list(self.graph.successors(node))

    def entry_notes(self) -> list[int]:
        return [node for node in self.nodes() if not self.parents(node)]

    def exit_nodes(self) -> list[int]:
        return [node for node in self.nodes() if not self.children(node) and self.parents(node)]

    def ancestors(self, node: int):
        return nx.ancestors(self.graph, node)

    def descendants(self, node: int):
        return nx.descendants(self.graph, node)

    # ... count ...

    def number_of_nodes(self) -> int:
        return self.graph.number_of_nodes()

    def number_of_edges(self) -> int:
        return self.graph.number_of_edges()

    # ... edges ...

    # TODO: if you're intent is to decouple program from nx, rethink returning nx.classes.reportviews.XXXXXXXXX

    def out_edges(self, node: int) -> nx.classes.reportviews.OutMultiEdgeView:
        return self.graph.out_edges(node)

    def in_edges(self, node: int) -> nx.classes.reportviews.InMultiEdgeView:
        return self.graph.in_edges(node)

    """
    def out_degree(self, node: int) -> int:
        return self.graph.out_degree(node)  # TODO: "'int' object is not callable"?

    def in_degree(self, node: int) -> int:
        return self.graph.in_degree(node) # TODO: "'int' object is not callable"?
    """

    # VALIDATE

    def is_reachable(self, source: int, destination: int) -> bool:
        return nx.algorithms.has_path(self, source, destination)

    def is_valid(self) -> bool:
        """
        Validates the control flow graph by checking
        - exactly one entry note
        - all nodes are reachable from the entry point.
        - TODO: all nodes have path to an exit node
        """
        if len(self.entry_notes()) != 1:
            return False

        entry_node: int = self.entry_notes()[0]
        all_nodes_reachable: bool = all(nx.algorithms.has_path(self, entry_node, node) for node in self.nodes())

        return all_nodes_reachable

    """def is_valid_input_directions(self, directions: list[int]) -> bool:
        current_node = 1
        
        while current_node not in self.exit_nodes():
            no_of_out_edges = len(self.out_edges(current_node))
            if no_of_out_edges == 0:
                current_node = self.children(current_node)[0]"""


    def is_entry_or_exit_node(self, node: int) -> bool:
        return CFG.is_start_node(node) or self.node_type(node) == NodeType.END

    # MANIPULATION

    def add_node(self, node_to_add: int, **attr):
        """
        Add a single node `node_to_add` and update node attributes.

        Parameters
        ----------
        node_to_add : node
            A node can be any hashable Python object except None.
        attr : keyword arguments, optional
            Set or change node attributes using key=value.

        (Excerpt from networkx's add_node function)
        """
        self.graph.add_node(node_to_add, **attr)

    def add_nodes(self, nodes_to_add: list[int], **attr):
        """
        Add multiple nodes.

        Parameters
        ----------
        nodes_for_adding : iterable container
            A container of nodes (list, dict, set, etc.).
            OR
            A container of (node, attribute dict) tuples.
            Node attributes are updated using the attribute dict.
        attr : keyword arguments, optional (default= no attributes)
            Update attributes for all nodes in nodes.
            Node attributes specified in nodes as a tuple take
            precedence over attributes specified via keyword arguments.

        (Excerpt from networkx's add_nodes function)
        """
        self.graph.add_nodes_from(nodes_to_add, **attr)

    def add_children(self, children: list[int], node: int):
        for child in children:
            self.graph.add_edge(node, child)  # NB: automatically adds child node if not in graph

    def add_edge(self, u: int, v: int, key=None, **attr):
        """c.f. MultiDiGraph's add_edge()"""
        return self.graph.add_edge(u, v, key, **attr)

    def remove_edge(self, u: int, v: int, key=None):
        """Remove an edge between u and v.

        Parameters
        ----------
        u, v : nodes
            Remove an edge between nodes u and v.
        key : hashable identifier, optional (default=None)
            Used to distinguish multiple edges between a pair of nodes.
            If None, remove a single edge between u and v. If there are
            multiple edges, removes the last edge added in terms of
            insertion order.

        (Excerpt from MultiDiGraph's docstring)
        """
        self.graph.remove_edge(u, v, key)

    # GENERATORS

    """
    TODO: consider for generate_valid_cfg
    YARPGen introduces the concept of generation policies [6] with the aim of increasing program diversity.
    The main idea is to sample from different distributions when making decisions in the generator.

    Additionally, YARPGen uses a technique known as parameter shuffling [6] where a random distribution is
    used to seed the main distributions used for the generator’s decisions, before beginning the generation
    process. This enables programs to have very different characteristics between executions of the generator.
    """

    @staticmethod
    def generate_valid_cfg(seed: int = None) -> 'CFG':

        from .cfg_generator \
            import generate_random_tree, \
            reduce_no_of_exit_nodes_to_n, \
            add_back_edges, \
            add_forward_edges, \
            add_self_loops

        # TODO: inform params w/ a seed

        # TODO: change from tree -> directed acyclic graph
        cfg = generate_random_tree(target_depth=3, max_children_per_node=3)
        reduce_no_of_exit_nodes_to_n(cfg, 1)
        add_back_edges(cfg, 3)
        add_forward_edges(cfg, 3)
        # todo: MISC. RANDOM EDGES & CROSS EDGES
        add_self_loops(cfg, 1)

        return cfg

    def generate_valid_input_directions(self, max_length: int = 64) -> list[int]:

        directions: list[int] = []

        current_node = 1  # starting node

        while len(directions) < max_length:

            # TODO: use edges, surely?

            # print("current_node: {id}, type: {type}, {children}".format(id=current_node, type=self.node_type(current_node), children=self.children(current_node)))

            if self.node_type(current_node) == NodeType.END:
                break
            elif self.node_type(current_node) == NodeType.UNCONDITIONAL:
                current_node = self.children(current_node)[0]
                # no choice made so no need to add to input path
            else:
                # TODO: but should I be choosing random EDGE as can be multiple out edges between two nodes?
                random_child_index = random.randint(0, len(self.children(current_node))-1)
                # print(random_child_index)
                directions.append(random_child_index)
                current_node = self.children(current_node)[random_child_index]

        return directions

