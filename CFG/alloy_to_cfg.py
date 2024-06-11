from __future__ import annotations

import xml.etree.ElementTree as ET
import networkx as nx
from .CFG import CFG


def _extract_xml_sections(root: ET.Element, label_name: str):
    """All xml sections w/ label"""
    xml_sections = []

    for field in root.findall('.//field'):
        if field.attrib.get('label') == label_name:
            xml_sections.append(field)

    for sig in root.findall('.//sig'):
        if sig.attrib.get('label') == label_name:
            xml_sections.append(sig)

    for skolem in root.findall('.//skolem'):
        if skolem.attrib.get('label') == label_name:
            xml_sections.append(skolem)

    return xml_sections


def _extract_blocks_with_label(root: ET.Element, label_name: str):
    """Find all blocks with a given label."""
    xml_sections = _extract_xml_sections(root, label_name)

    atom_labels = []
    for section in xml_sections:
        atom_labels.extend(atom.attrib['label'] for atom in section.findall('.//atom'))

    return atom_labels


def _extract_edges_with_label(root: ET.Element, label_name: str):
    """Return edge as list [src, dst, (label)]"""
    def has_edge_label(info: list[str]):
        """Assumes len(info) > 1"""
        return info[1].isdigit()  # 1,4,7,... are indices of (numeric) id, if there is one

    info = _extract_blocks_with_label(root, label_name)  # messy list [block, id, block, block, id, block, ,,,]

    if len(info) == 0:
        return None

    edges = []

    if has_edge_label(info):
        for i in range(0, len(info), 3):
            edge = ((info[i], info[i + 2]), info[i + 1])
            edges.append(edge)
    else:
        for i in range(0, len(info), 2):
            edge = ((info[i], info[i + 1]), _standardise_label_name(label_name))
            edges.append(edge)

    return edges


def _get_edges(root: ET.Element):
    # TODO: give edges multiple labels/attrs (eg. [(('LoopHeader$0', 'LoopHeader$0'), ['BackEdge', '0'])])
    back_edges = _extract_edges_with_label(root, "$this/backEdge") or []  # subset of branch edges

    back_edges_set = set(back_edges) if back_edges else set()  # Convert to set for fast lookup

    # all branch edges not already in back_edges_set
    branch_edges = [
        (edge, label) for (edge, label) in (_extract_edges_with_label(root, "branch") or [])  # Ensure it's a list (not None)
        if edge not in {e[0] for e in back_edges_set}
    ]

    return back_edges + branch_edges


def _standardise_label_name(old_name: str) -> str:
    """Standardise the labels from Alloy CFGs
    (eg. this/SwitchBlock -> SwitchBlock, $this/exitBlocks -> ExitBlock"""
    new_name = old_name.split('/')[-1]
    new_name = new_name[0].upper() + new_name[1:]  # exitBlocks -> ExitBlocks so consistent

    # label-specific transformation
    if old_name == "$this/exitBlocks":
        new_name = new_name[:-1]

    return new_name


def _get_node_data(root: ET.Element):

    block_attrs: dict[str, dict[str, bool | list[str]]] = {}

    def add_attr(raw_label: str, predicate = lambda atom, block: True):
        extracted_sections = _extract_xml_sections(root, raw_label)
        label_name = _standardise_label_name(raw_label)

        for block in block_attrs:
            # Extracting all second atom labels in tuples within the sections
            block_labels = [
                atom.attrib['label'] for section in extracted_sections
                for tuple_elem in section.findall('.//tuple')
                if tuple_elem.findall('.//atom')[0].attrib['label'] == block
                for atom in tuple_elem.findall('.//atom')[1:]
                if predicate(atom, block)  # Apply the predicate
            ]

            block_attrs[block][label_name] = block_labels

    block_labels = ["this/LoopHeader", "this/SelectionHeader", "this/HeaderBlock",
                    "this/Block", "this/EntryBlock", "this/SwitchBlock", "$this/exitBlocks"]

    for label in block_labels:
        blocks = _extract_blocks_with_label(root, label)
        for b in blocks:
            if b not in block_attrs:
                block_attrs[b] = {}
            label_name = _standardise_label_name(label)
            block_attrs[b][label_name] = True

    struc_reachable = "this/StructurallyReachableBlock"
    sr_blocks = _extract_blocks_with_label(root, struc_reachable)
    label_name = _standardise_label_name(struc_reachable)
    for block in block_attrs:
        block_attrs[block][label_name] = block in sr_blocks

    add_attr("$this/structurallyDominates")
    add_attr("$this/structurallyPostDominates")
    add_attr("$this/contains")
    add_attr("continue")
    add_attr("merge")
    add_attr("$this/strictlyStructurallyDominates", predicate=lambda atom, block: atom.attrib['label'] != block)

    """ TODO: 
    <skolem label="$this/backEdgeSeq"
    <skolem label="$this/exitEdge"
    branchSet
    """

    return block_attrs


def transform_labels(data, label_mapping):
    """
    Recursively transforms labels in the given data using the provided label mapping.

    Args:
        data: The data structure (str, list, or dict) containing the labels to be transformed.
        label_mapping (dict): A dictionary mapping original labels to their transformed values.

    Returns:
        The data structure with labels transformed according to the label_mapping.
    """
    if isinstance(data, str):
        return label_mapping.get(data, data)
    elif isinstance(data, list):
        return [transform_labels(item, label_mapping) for item in data]
    elif isinstance(data, dict):
        return {key: transform_labels(value, label_mapping) for key, value in data.items()}
    return data


def alloy_to_cfg(xml_filepath: str) -> CFG:

    xml = ET.parse(xml_filepath)
    root = xml.getroot()

    raw_node_data = _get_node_data(root)

    # Map node labels to numerical IDs to conform with preexisting CFG->WASM conversion code
    node_label_to_id: dict[str, str] = {key: i + 1 for i, key in enumerate(raw_node_data)}

    # Transform node data keys to numerical IDs and update the attributes
    nodes = {node_label_to_id[key]: transform_labels(value, node_label_to_id) for key, value in raw_node_data.items()}

    # Transform edges to use numerical IDs
    edges = [[(node_label_to_id[a], node_label_to_id[b]), c] for [(a, b), c] in _get_edges(root)]

    graph = nx.MultiDiGraph()

    for node, attrs in nodes.items():
        graph.add_node(node, **attrs)

    for edge, edge_label in edges:
        scr, dst = edge
        graph.add_edge(scr, dst, edge_label)

    return CFG(graph=graph)
