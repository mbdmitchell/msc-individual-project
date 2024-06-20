from pprint import pprint

from CFG import CFG, CFGFormat
from WAT import ProgramBuilder
from WAT.Program import WebAssemblyFormat

cfg = CFG().load(filepath='./alloy-cfgs/ex8.xml', fmt=CFGFormat.ALLOY, load_as_wasm_friendly_cfg=False)

for n in cfg.nodes(data=True):
    pprint(n)