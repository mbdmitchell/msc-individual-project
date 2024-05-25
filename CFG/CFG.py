from enum import Enum
from typing import Optional
import networkx as nx
import pickle

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


class CFG:
    """
    A simple interface for nx.MultiDiGraph, abstracting its implementation details
    to provide a cleaner interface for CFGs and decouple rest of the project components
    from a specific graph implementation.
    """

    # FILE HANDLING

    def save(self, filepath: str, fmt: GraphFormat = GraphFormat.CFG) -> None:
        """Saves the graph to a file in the specified format."""
        # TODO: Refactor?
        """
        if fmt not in {GraphFormat.NX_MULTI_DIGRAPH, GraphFormat.GRAPH_ML, GraphFormat.CFG}:
            raise TypeError("Chosen GraphFormat not supported")
            
        with open(filepath, 'wb') as file:
            pickle.dump(self.graph, file)
        """
        if fmt == GraphFormat.GRAPH_ML:
            nx.write_graphml(self.graph, filepath)
        elif fmt == GraphFormat.CFG:
            with open(filepath, 'wb') as file:
                pickle.dump(self, file)
        elif fmt == GraphFormat.NX_MULTI_DIGRAPH:
            with open(filepath, 'wb') as file:
                pickle.dump(self.graph, file)
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
        no_of_children = len(self.children(node))
        if no_of_children == 0:
            return NodeType.END
        elif no_of_children == 1:
            return NodeType.UNCONDITIONAL
        elif no_of_children == 2:
            return NodeType.CONDITIONAL
        else:
            return NodeType.SWITCH

    @staticmethod
    def root() -> int:
        """Root node is given id 1."""
        return 1

    def parents(self, node: int) -> list[int]:
        return self.graph.predecessors(node)

    def children(self, node: int) -> list[int]:
        return self.graph.successors(node)

    def entry_notes(self) -> list[int]:
        return [node for node in self.nodes() if not self.parents(node)]

    def exit_nodes(self) -> list[int]:
        return [node for node in self.nodes() if not self.children(node) and self.parents(node)]

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
        """
        if len(self.entry_notes()) != 1:
            return False

        entry_node: int = self.entry_notes()[0]
        all_nodes_reachable: bool = all(nx.algorithms.has_path(self, entry_node, node) for node in self.nodes())

        return all_nodes_reachable

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
