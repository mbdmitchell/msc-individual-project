__version__ = "1.0.0"
__author__ = "Max Mitchell"

from .CFG import *
from .CFGGenerator import CFGGenerator
from .example_CFGs import (
    cfg_0,
    cfg_if_1,
    cfg_if_2,
    cfg_if_3_nested,
    cfg_if_4_nested,
    cfg_if_5_nested,
    cfg_while_1,
    cfg_while_2_nested,
    cfg_early_1_continue,
    cfg_early_2_break,
    cfg_early_3_continue_and_break_in_switch,
    cfg_switch_1_fallthrough,
    cfg_switch_2_nofallthrough,
    cfg_switch_3_mix,
    cfg_switch_4_with_loop,
    cfg_switch_5_with_loop_and_fallthrough,
    cfg_switch_6_nested,
    cfg_switch_loop_if_combo,
    cfg_merge_which_is_also_header_1_selection,
    cfg_merge_which_is_also_header_2_loop)

# from .alloy_to_cfg import alloy_to_cfg  # TODO: Remove after testing / not for final version
