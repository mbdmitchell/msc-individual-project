from pprint import pprint

from CFG import CFG, CFGFormat

cfg = CFG().load(filepath='alloy-cfgs/minimal-loop.xml', fmt=CFGFormat.ALLOY)

for n in cfg.nodes(data=True):
    pprint(n)

def selection_construct(cfg: CFG, section_header):
    """
    Selection construct: The blocks structurally dominated by a selection header, while excluding blocks structurally
    dominated by the selection header’s merge block [SPIR-V 1.6r2, §2.11.1]
    """
    assert cfg.is_selection_header(section_header)
    merge_block = cfg.merge_block(section_header)

    merge_doms: set = cfg.structurally_dominates(merge_block)
    header_doms: set = cfg.structurally_dominates(section_header)

    return header_doms - merge_doms


print(selection_construct(cfg, 2))