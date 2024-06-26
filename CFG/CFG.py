from __future__ import annotations

import os
import random
from enum import Enum
from typing import Optional
import networkx as nx
import pickle
import pygraphviz

from matplotlib import pyplot as plt

from threading import Lock

# Lock for thread safety when saving images
save_lock = Lock()


class NodeType(Enum): # TODO: Depreciate. (Use node attributes)
    def __repr__(self):
        return f"<{self.__class__.__name__}.{self.name}: {self.value}>"

    UNCONDITIONAL = 1
    CONDITIONAL = 2
    SWITCH = 3
    END = 4


class CFGFormat(Enum):
    CFG = 0,
    NX_MULTI_DIGRAPH = 1,
    GRAPH_ML = 2
    PNG = 3
    ALLOY = 4


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
            self.graph = graph
            # TODO: Ensure graph has no node attributes, except possibly EntryBlock
            if not (entry_block or has_entry_block_attr(graph)):
                raise ValueError("No provided entry block: must be in either graph, or the entry_block param")
            if entry_block:
                self.add_node_attribute(entry_block, "EntryBlock", True)
            # TODO: Calculate and add all other needed attrs, e.g. LoopHeader, SelectionHeader, ExitBlock.
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

            """ TODO: 1) Fix the multi edge issue where many edges from n to m are represented w/ just one
            2) eg. n <--> m displays only one edge label
            # Generate edge labels with indices
            edge_labels = {}
            for node in cfg.graph.nodes():
                out_edges = list(cfg.graph.out_edges(node))
                if len(out_edges) > 1:  # the edges of nodes with out_degree <= 1 should have not label
                    for idx, edge in enumerate(out_edges):
                        edge_labels[edge] = str(idx)
                        
            nx.draw_networkx_edge_labels(cfg.graph, pos, edge_labels=edge_labels, font_color='red')
            """

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

    def nodes(self, data=False) -> list[int]:
        return self.graph.nodes(data)

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
        # TODO: THIS IS WRONG NOW
        return node == 1

    def is_end_node(self, node: int):
        return len(self.graph.out_edges(node)) == 0

    def parents(self, node: int):
        return list(self.graph.predecessors(node))

    def children(self, node: int):
        return list(self.graph.successors(node))

    def entry_node(self) -> int:
        # TODO: if there is an entry_block label, use. Else...
        return next((node for node in self.nodes() if not self.parents(node)), None)

    def exit_nodes(self) -> list[int]:
        return [node for node in self.nodes() if not self.children(node) and self.parents(node)]

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
        if node not in self.graph.nodes:
            raise RuntimeError(f"Node {node} does not exist in the graph")
        if attr_label in self.graph.nodes[node]:
            raise RuntimeError(f"{attr_label} already in CFG")

        self.graph.nodes[node][attr_label] = value

    def update_node_attribute(self, node, attr_label: str, value: bool | int):
        if node not in self.graph.nodes:
            raise RuntimeError(f"Node {node} does not exist in the graph")
        if attr_label not in self.graph.nodes[node]:
            raise RuntimeError(f"Can't update {attr_label}: not in CFG")

        self.graph.nodes[node][attr_label] = value


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

    def out_degree(self, node: int) -> int:
        """
        Returns out degree of node.
        NB: Safe to ignore "'int' object is not callable" warning
        """
        return self.graph.out_degree(node)

    def in_degree(self, node: int) -> int:
        """
        Returns in degree of node.
        NB: Safe to ignore "'int' object is not callable" warning
        """
        return self.graph.in_degree(node)

    # VALIDATE

    def is_reachable(self, source: int, destination: int) -> bool:
        return nx.algorithms.has_path(self, source, destination)

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
        """
        NB: Currently, CFGs generated w/ this function don't include necessary labels for optimal CFG->code conversion.
        Generate CFGs with Alloy model and use cfg = CFG().load(filepath='./alloy-cfgs/cfg2.xml', fmt=CFGFormat.ALLOY)
        """
        if seed is None:
            seed = random.randint(0, 2 ** 32 - 1)
        random.seed(seed)

        from .cfg_generator_OLD import generate_random_tree, \
            reduce_no_of_exit_nodes_to_n, \
            add_back_edges, \
            add_forward_edges, \
            add_self_loops

        # initial cfg

        tree_depth = random.choice(range(2, 6))
        tree_max_children = random.choice(range(2, 6))

        cfg = generate_random_tree(target_depth=tree_depth, max_children_per_node=tree_max_children)

        # assign parameters, all determined by seed

        org_no_of_end_nodes = sum(1 for node in cfg.nodes() if cfg.node_type(node) == NodeType.END)

        no_of_end_nodes = random.choice(range(1, 1 + org_no_of_end_nodes))
        no_of_nodes = len(cfg.nodes())
        no_of_back_edges = random.choice(range(0, 1 + no_of_nodes // 2))
        no_of_forward_edges = random.choice(range(0, 1 + no_of_nodes // 2))
        no_of_self_loops = random.choice(range(0, 1 + no_of_nodes // 4))

        # transform

        reduce_no_of_exit_nodes_to_n(cfg, no_of_end_nodes)
        add_back_edges(cfg, no_of_back_edges)
        add_forward_edges(cfg, no_of_forward_edges)
        add_self_loops(cfg, no_of_self_loops)
        # todo: MISC. RANDOM EDGES & CROSS EDGES

        return cfg

    def generate_valid_input_directions(self, seed: int = None, max_length: int = 64) -> list[int]:

        if seed is None:
            seed = random.randint(0, 2 ** 32 - 1)
        random.seed(seed)

        MAX_ATTEMPTS = 16

        for _ in range(MAX_ATTEMPTS):

            directions: list[int] = []
            current_node = self.entry_node()

            length_remaining = max_length

            while length_remaining > 0:

                if self.node_type(current_node) == NodeType.END:
                    break
                elif self.out_degree(current_node) == 1:
                    edge_index = 0
                    # no choice made so it doesn't require a direction
                else:
                    edge_index = random.randint(0, self.out_degree(current_node) - 1)
                    directions.append(edge_index)
                    length_remaining -= 1

                _, dst = list(self.out_edges(current_node))[edge_index]
                current_node = dst

            # if directions results in full path, return
            if self.node_type(current_node) == NodeType.END:
                return directions
            else:
                continue

        # TODO: ATTEMPTS is silly. If we are not at exit node by max_length, just find and follow shortest path to exit

        raise RuntimeError(f'Failed to generate input directions of max length {max_length}. '
                           'Check CFG end nodes are always reachable or increase max_length parameter')

    def expected_output_path(self, input_directions: list[int]) -> list[int]:

        current_node = 1
        input_ix = 0

        path: list[int] = [current_node]

        length = len(input_directions)

        while input_ix <= length:

            if self.node_type(current_node) == NodeType.END:
                break
            elif self.out_degree(current_node) == 1:
                edge_index = 0
            else:
                edge_index = input_directions[input_ix]
                input_ix += 1

            _, current_node = list(self.out_edges(current_node))[edge_index]

            path.append(current_node)

        if self.node_type(current_node) != NodeType.END and input_ix != len(input_directions):
            raise RuntimeError("Error") # todo more descriptive

        return path

    # ... block attributes + misc. details from alloy CFGs

    def continue_attribute(self, block):
        return self.graph.nodes[block]["Continue"]

    def contains_attribute(self, block):
        return self.graph.nodes[block]["Contains"]

    def structurally_dominates(self, block):
        return set(self.graph.nodes[block]["StructurallyDominates"])

    def strictly_structurally_dominates(self, block):
        return set(self.graph.nodes[block]["StrictlyStructurallyDominates"])

    def structurally_post_dominates(self, block):
        return set(self.graph.nodes[block]["StructurallyPostDominates"])

    def is_loop_header(self, block):
        return self.graph.nodes[block].get("LoopHeader", False) is not False

    def is_selection_header(self, block):
        return self.graph.nodes[block].get("SelectionHeader", False) is not False

    def is_switch_header(self, block):
        return self.graph.nodes[block].get("SwitchBlock", False) is not False
    def is_entry_block(self, block):
        return self.graph.nodes[block].get("EntryBlock", False) is not False

    def is_exit_block(self, block):
        return self.graph.nodes[block].get("ExitBlock", False) is not False

    def is_basic_block(self, block):
        return self.graph.nodes[block].get("Block", False) is not False

    def contains_merge_instruction(self, block):
        return self.graph.nodes[block].get("Merge") != []

    def merge_block(self, block):
        if not self.contains_merge_instruction(block):
            raise ValueError("No merge block")
        block: list = self.graph.nodes[block]["Merge"]
        return block[0]

    def is_structurally_reachable(self, block) -> bool:
        return self.graph.nodes[block].get("StructurallyReachableBlock", False) is not False

    def is_header_block(self, block) -> bool:
        return self.contains_merge_instruction(block)

    # TODO: Probably missing switch attrs or something

