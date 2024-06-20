__version__ = "1.0.0"
__author__ = "Max Mitchell"

from .CFG import *
from .alloy_to_cfg import alloy_to_cfg  # TODO: Remove after testing / not for final version
from .example_CFGs \
    import example_cfg_if_else, \
    example_cfg_while_loop, \
    example_cfg_switch_while_combo, \
    example_cfg_multigraph, \
    example_cfg_nested_switches
