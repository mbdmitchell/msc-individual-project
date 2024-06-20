from pprint import pprint

from CFG import CFG, CFGFormat

cfg = CFG().load(filepath='alloy-cfgs/ex2.xml', fmt=CFGFormat.ALLOY)

for n in cfg.nodes(data=True):
    pprint(n)
