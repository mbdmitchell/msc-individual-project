from __future__ import annotations

import os
import random
from enum import Enum
from typing import Optional
import networkx as nx
import pickle

from matplotlib import pyplot as plt

from threading import Lock

# Lock for thread safety when saving images
save_lock = Lock()

class CFGFormat(Enum):
    CFG = 0,
    NX_MULTI_DIGRAPH = 1,
    GRAPH_ML = 2
    PNG = 3
    ALLOY = 4

# TODO: Remove old multi-edge functionality
# TODO: refactor to use DiGraph, a better fit

class CFG:
    """
    A simple interface for nx.MultiDiGraph, abstracting its implementation details
    to provide a cleaner interface for CFGs and decouple rest of the project components
    from a specific graph implementation.
    """

    def __init__(self, filepath: Optional[str] = None,
                 graph: Optional[nx.MultiDiGraph] = None,
                 entry_block: Optional[int] = None):
        """
        filepath: filepath to pickle'd CFG obj
        graph: graph with no node attributes (except possibly EntryBlock)
        """

        def has_entry_block_attr(g: nx.MultiDiGraph) -> bool:
            entry_block_count = sum(1 for _, attrs in g.nodes(data=True) if 'EntryBlock' in attrs)
            return entry_block_count == 1

        if graph and filepath:
            raise ValueError("Don't include both a graph and filename in the parameters")

        self.graph = nx.MultiDiGraph()

        if graph:
            # TODO: Ensure graph has no node attributes, except possibly EntryBlock
            self.graph = graph
            if entry_block is None and not has_entry_block_attr(graph):
                raise ValueError("No provided entry block: must be in either graph, or the entry_block param")
            if isinstance(entry_block, int):
                self.add_node_attribute(entry_block, "EntryBlock", True)
            self.graph = graph
        elif filepath:
            self.load(filepath)

    def __eq__(self, other):
        if not isinstance(other, CFG):
            return False
        if self.graph.nodes(data=True) != other.graph.nodes(data=True):
            return False
        if list(self.graph.edges(data=True)) != list(other.graph.edges(data=True)):
            return False

        return True

    def __hash__(self):
        nodes = frozenset((n, frozenset(d.items())) for n, d in self.graph.nodes(data=True))
        edges = frozenset((u, v, frozenset(d.items())) for u, v, d in self.graph.edges(data=True))
        return hash((nodes, edges))

    # FILE HANDLING

    def _save_image(cfg, filename: str):
        with save_lock:
            plt.figure(figsize=(10, 10))
            # pos = nx.nx_agraph.graphviz_layout(cfg.graph, prog="twopi", root=1)
            pos = nx.spring_layout(cfg.graph)  # or any other layout algorithm
            nx.draw(cfg.graph, pos, with_labels=True, font_color='white')

            plt.axis('off')
            plt.savefig(filename, format='png', bbox_inches='tight', pad_inches=0.1)
            plt.close()

    def save(self, filepath: str, fmt: CFGFormat = CFGFormat.CFG) -> None:
        """Saves the graph to a file in the specified format."""

        directory = os.path.dirname(filepath)
        if not os.path.exists(directory):
            os.makedirs(directory)

        if fmt == CFGFormat.GRAPH_ML:
            nx.write_graphml(self.graph, filepath)
        elif fmt == CFGFormat.CFG:
            with open(filepath, 'wb') as file:
                pickle.dump(self, file)
        elif fmt == CFGFormat.NX_MULTI_DIGRAPH:
            with open(filepath, 'wb') as file:
                pickle.dump(self.graph, file)
        elif fmt == CFGFormat.PNG:
            self._save_image(filepath)
        else:
            raise ValueError('Unsupported CFGFormat')

    def load(self, filepath: str, fmt: CFGFormat = CFGFormat.CFG, load_as_wasm_friendly_cfg: bool = True) -> 'CFG':
        """Loads a graph from a file in the specified format."""

        from CFG.alloy_to_cfg import alloy_to_cfg

        if fmt not in {CFGFormat.NX_MULTI_DIGRAPH, CFGFormat.CFG, CFGFormat.ALLOY}:
            raise TypeError("Unsupported CFGFormat")

        if fmt == CFGFormat.GRAPH_ML:
            self.graph = nx.read_graphml(filepath)
            return self
        elif fmt == CFGFormat.ALLOY:
            cfg = alloy_to_cfg(filepath, load_as_wasm_friendly_cfg)
        else:
            with open(filepath, 'rb') as file:
                cfg = pickle.load(file)

        self._load_cfg(cfg)

        return self

    def _load_cfg(self, cfg_graph: 'CFG') -> None:
        self.graph = cfg_graph.graph
        # Add additional attributes from CFG graph if it becomes necessary

    # GETTERS

    def graph(self) -> nx.MultiDiGraph:
        return self.graph

    # ... nodes ...

    def is_basic_block(self, block) -> bool:
        if block is None:
            return False
        return self.out_degree(block) == 1

    def is_exit_block(self, block) -> bool:
        if block is None:
            return False
        return self.out_degree(block) == 0

    def is_selection_header(self, block) -> bool:
        if block is None:
            return False
        return self.graph.nodes[block].get('SelectionHeader', False)

    def is_loop_header(self, block) -> bool:
        if block is None:
            return False
        return self.graph.nodes[block].get('LoopHeader', False)

    def nodes(self, data=False) -> list[int]:
        return self.graph.nodes(data)

    def is_merge_block(self, block: int):
        """Return if block is a merge for any (header) node(s)"""
        return any(self.graph.nodes[n].get("Merge") == block for n in self.nodes())

    def out_edges_destinations(self, block) -> list[int]:
        return [e[1] for e in self.out_edges(block)]

    def in_edges_sources(self, block) -> list[int]:
        return [e[0] for e in self.in_edges_nx_count(block)]

    def is_end_node(self, block: int):
        if block is None:
            return False
        return len(self.graph.out_edges(block)) == 0

    def entry_node(self) -> int:
        nodes = self.nodes(data=True)
        for n, data in nodes:
            if 'EntryBlock' in data:
                return n  # return the key of the node
        raise ValueError("EntryBlock not found")

    def ancestors(self, node: int):
        return nx.ancestors(self.graph, node)

    def descendants(self, node: int):
        return nx.descendants(self.graph, node)

    def node_attributes(self, node):
        if node not in self.graph:
            raise RuntimeError(f"No node with id {node}")

        attrs = []
        for attr, value in self.graph.nodes[node].items():
            attrs.append(f"{attr}: {value}")
        return attrs

    def add_node_attribute(self, node, attr_label: str, value: bool | int):
        # TODO: if attr not in {, , , , , ,} throw
        if node not in self.graph.nodes:
            raise RuntimeError(f"Node {node} does not exist in the graph")
        if attr_label in self.graph.nodes[node]:
            raise RuntimeError(f"{attr_label} already in CFG node")
        # TODO: If attr_label == Break & cont == TRUE in node, throw and vice versa

        self.graph.nodes[node][attr_label] = value

    def _add_edge_attribute(self, edge, attr_label: str, value: bool | int):
        # TODO: if attr not in {, , , , , ,} throw
        if edge not in self.graph.edges:
            raise RuntimeError(f"Edge {edge} does not exist in the graph")
        if attr_label in self.graph.edges[edge]:
            raise RuntimeError(f"{attr_label} already in CFG edge")
        if len(edge) == 2:
            edge = (*edge, 0)

        self.graph.edges[edge][attr_label] = value

    def update_node_attribute(self, node, attr_label: str, value: bool | int):
        # TODO: if attr not in {, , , , , ,} throw
        if node not in self.graph.nodes:
            raise RuntimeError(f"Node {node} does not exist in the graph")
        if attr_label not in self.graph.nodes[node]:
            raise RuntimeError(f"Can't update {attr_label}: not in CFG node")

        self.graph.nodes[node][attr_label] = value

    def update_edge_attribute(self, edge, attr_label: str, value: bool | int):
        # TODO: if attr not in {, , , , , ,} throw
        if edge not in self.graph.edges:
            raise RuntimeError(f"Edge {edge} does not exist in the graph")
        if attr_label not in self.graph.edges[edge]:
            raise RuntimeError(f"Can't update {attr_label}: not in CFG edge")

        self.graph.edges[edge][attr_label] = value

    # ... edges ...

    # TODO: if you're intent is to decouple program from nx, rethink returning nx.classes.reportviews.XXXXXXXXX

    def out_edges(self, node: int) -> nx.classes.reportviews.OutMultiEdgeView:
        return self.graph.out_edges(node)

    def in_edges_nx_count(self, node: int) -> nx.classes.reportviews.InMultiEdgeView:
        return self.graph.in_edges(node)

    def out_degree(self, block: int) -> int:
        """
        Returns out degree of node.
        NB: Safe to ignore "'int' object is not callable" warning
        """
        if not self.contains_multi_edge(block):
            return self.graph.out_degree(block)  # pylint: disable=not-callable
        return sum(
            self.no_of_edges_represented_by_edge(e)
            for e in self.graph.out_edges(nbunch=block)
        )

    def in_degree(self, block: int) -> int:
        """
        Returns in degree of node.
        NB: Safe to ignore "'int' object is not callable" warning
        """
        if not self.contains_multi_edge(block):
            return self.graph.in_degree(block)  # pylint: disable=not-callable
        return sum(
            self.no_of_edges_represented_by_edge(e)
            for e in self.graph.in_edges(nbunch=block)
        )

    # VALIDATE

    def is_reachable(self, source: int, destination: int) -> bool:
        return nx.algorithms.has_path(self.graph, source, destination)

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

    def add_successors(self, children: list[int], node: int):
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

    def remove_edges_from(self, ebunch: list):
        """Wrapper func
        ebunch: list or container of edge tuples
            Each edge given in the list or container will be removed
            from the graph. The edges can be:

                - 2-tuples (u, v) A single edge between u and v is removed.
                - 3-tuples (u, v, key) The edge identified by key is removed.
                - 4-tuples (u, v, key, data) where data is ignored.
        """
        self.graph.remove_edges_from(ebunch)

    def edge_index_to_dst_block(self, src_block: int, edge_ix: int):

        edges = self.graph.out_edges(nbunch=src_block)

        cumulative_count = -1
        for true_edge_ix, edge in enumerate(edges):
            cumulative_count += self.no_of_edges_represented_by_edge(edge)
            if cumulative_count >= edge_ix:
                return self.out_edges_destinations(src_block)[true_edge_ix]

        raise IndexError("Index out of range")

    def generate_valid_input_directions(self, seed: int = None, max_length: int = 64) -> list[int]:
        # TODO: add param to return n distinct valid_input_directions as list[list[int]]
        if seed is None:
            seed = random.randint(0, 2 ** 32 - 1)
        random.seed(seed)


        MAX_ATTEMPTS = 16

        for _ in range(MAX_ATTEMPTS):

            directions: list[int] = []
            current_node = self.entry_node()

            length_remaining = max_length

            while length_remaining > 0:

                if self.is_end_node(current_node):
                    break
                elif self.out_degree(current_node) == 1:
                    edge_index = 0
                    # no choice made so it doesn't require a direction
                else:
                    edge_index = random.randint(0, self.out_degree(current_node) - 1)
                    directions.append(edge_index)
                    length_remaining -= 1

                dst = self.edge_index_to_dst_block(current_node, edge_index)
                current_node = dst

            # if directions results in full path, return
            if self.is_end_node(current_node):
                return directions
            else:
                continue

        # TODO: ATTEMPTS is silly. If we are not at exit node by max_length, just find and follow shortest path to exit

        raise RuntimeError(f'Failed to generate input directions of max length {max_length}. '
                           'Check CFG end nodes are always reachable or increase max_length parameter')

    def expected_output_path(self, input_directions: list[int]) -> list[int]:

        current_node = self.entry_node()
        input_ix = 0

        path: list[int] = [current_node]

        length = len(input_directions)

        while input_ix <= length:
            if self.is_end_node(current_node):
                break
            elif self.out_degree(current_node) == 1:
                edge_index = 0
            else:
                edge_index = input_directions[input_ix]
                input_ix += 1

            current_node = self.edge_index_to_dst_block(current_node, edge_index)

            path.append(current_node)

        if not self.is_end_node(current_node) and input_ix != len(input_directions):
            raise RuntimeError("Error")  # todo more descriptive

        return path

    def is_multi_edge(self, edge):
        if not edge:
            return False
        if len(edge) == 2:
            edge = (*edge, 0)  # internally, networkx multidigraph edges have three attrs
        if edge not in self.graph.edges:
            return False
        multi_edge_value = self.graph.edges[edge].get("MultiEdge", None)
        return isinstance(multi_edge_value, int)

    def no_of_edges_represented_by_edge(self, edge):
        if not self.is_multi_edge(edge):
            return 1
        if len(edge) == 2:
            edge = (*edge, 0)  # internally, networkx multidigraph edges have three attrs
        return self.graph.edges[edge].get("MultiEdge", None)

    def is_switch_block(self, block):
        if not block:
            return False
        return self.graph.nodes[block].get("SwitchBlock", False) is not False

    def is_continue_block(self, block):
        if block is None:
            return False
        is_cont = self.graph.nodes[block].get("ContinueBlock", False) is not False
        if is_cont:
            assert self.is_basic_block(block)
        return is_cont

    def is_break_block(self, block):
        if block is None:
            return False
        is_br = self.graph.nodes[block].get("BreakBlock", False) is not False
        if is_br:
            assert self.is_basic_block(block)
        return is_br

    def contains_merge_instruction(self, block):
        return self.graph.nodes[block].get("Merge") != []

    def merge_block(self, block):
        if not self.contains_merge_instruction(block):
            raise ValueError("No merge block")
        m_blk = self.graph.nodes[block]["Merge"]
        return m_blk

    def is_header_block(self, block) -> bool:
        if block is None:
            return False
        return self.is_selection_header(block) or self.is_loop_header(block)

    def contains_multi_edge(self, block) -> bool:
        return any(self.is_multi_edge(e) for e in self.graph.edges(nbunch=block))

