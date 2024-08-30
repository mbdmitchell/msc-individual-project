import pickle

import CFG
import programs
from my_common import CodeType

# Original CFG/Program

cfg = CFG.CFG("dupious_bug/attempt0/graph_1083.pickle")
program = programs.WGSLProgram(cfg, CodeType.GLOBAL_ARRAY)
program.save('/Users/maxmitchell/Documents/msc-control-flow-fleshing-project/evaluation/wgsl_bug_reduction/shader')

with open('dupious_bug/attempt0/program_class.pickle', 'wb') as file:
    pickle.dump(program, file)

# Prune CFG/Program

# ... prune unvisited blocks

cfg.remove_nodes_from([11, 24])
cfg.add_edge(4, 23)

cfg.remove_nodes_from([14, 27, 28, 29, 13, 30, 31, 32, 33, 34])
cfg.remove_node_attribute(7, "LoopHeader")
cfg.remove_node_attribute(7, "SelectionHeader")
cfg.remove_node_attribute(7, "Merge")
cfg.add_edge(7, 2)

cfg.remove_nodes_from([35, 36, 37])
cfg.remove_node_attribute(16, "SelectionHeader")
cfg.add_edge(16, 6)

# ... combine blocks: e.g. ->1->...->5-> becomes ->1->  AMAZINGLY, DOING THIS MAKES THE BUG DISAPPEAR??
# cfg.remove_nodes_from([8, 17])
# cfg.add_edge(5, 3)

# ... change 12's merge block to enclosing loop header, removing block 25. AGAIN, DOING THIS MAKES THE BUG DISAPPEAR??
# cfg.update_node_attribute(12, "Merge", 1)
# cfg.remove_nodes_from([25])
# cfg.remove_edges_from([(12, 26)])  # delete and re-add so remains ix1
# cfg.add_edge(12, 1)
# cfg.add_edge(12, 26)

reduced_program = programs.WGSLProgram(cfg, CodeType.GLOBAL_ARRAY)
reduced_program.save('/Users/maxmitchell/Documents/msc-control-flow-fleshing-project/evaluation/wgsl_bug_reduction/reduced_shader')

with open('dupious_bug/attempt1/reduced_program_class.pickle', 'wb') as file:
    pickle.dump(reduced_program, file)
