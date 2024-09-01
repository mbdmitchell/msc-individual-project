import pickle

import CFG
import programs
from my_common import CodeType

# Original CFG/Program

cfg = CFG.CFG("bug/attempt0/graph_2439.pickle")
program = programs.WGSLProgram(cfg, CodeType.GLOBAL_ARRAY)
program.save('/Users/maxmitchell/Documents/msc-control-flow-fleshing-project/evaluation/wgsl_bug_reduction/bug/attempt0/code_2439')

with open('bug/attempt0/program_class.pickle', 'wb') as file:
    pickle.dump(program, file)

# Prune CFG/Program

# ... prune unvisited blocks

cfg.remove_nodes_from([10, 21, 20])
cfg.remove_edges_from([(6, 11)])
cfg.add_edge(6, 12)
cfg.add_edge(6, 11)

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
reduced_program.save('/Users/maxmitchell/Documents/msc-control-flow-fleshing-project/evaluation/wgsl_bug_reduction/bug/attempt1-reduce-cfg/reduced_code_2439')

with open('bug/attempt1-reduce-cfg/reduced_program_class_2439.pickle', 'wb') as file:
    pickle.dump(reduced_program, file)
