from CFG.CFG import CFG


# G = CFG().load('../CFG/example_cfgs/test0.pickle')
# "_pickle.UnpicklingError: NEWOBJ class argument isn't a type object" (cf. below)

CFG().save('thisworksthough.pickle')
G2 = CFG().load('thisworksthough.pickle')
# WORKS"""

