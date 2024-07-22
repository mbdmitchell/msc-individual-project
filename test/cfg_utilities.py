from CFG.example_CFGs import *
from utils import Language
from itertools import product


def example_cfgs_with_fallthrough():
    return [cfg_switch_1_fallthrough(), cfg_switch_3_mix(), cfg_switch_5_with_loop_and_fallthrough()]


def example_cfgs_without_fallthrough():
    return [cfg_0(),
            cfg_early_1_continue(),
            cfg_early_2_break(),
            cfg_early_3_continue_and_break_in_switch(),
            cfg_if_1(),
            cfg_if_2(),
            cfg_if_3_nested(),
            cfg_if_4_nested(),
            cfg_if_5_nested(),
            cfg_while_1(),
            cfg_while_2_nested(),
            cfg_switch_2_nofallthrough(),
            cfg_switch_4_with_loop(),
            cfg_switch_6_nested(),
            cfg_switch_loop_if_combo(),
            cfg_merge_which_is_also_header_1_selection(),
            cfg_merge_which_is_also_header_2_loop()]


def all_example_cfgs():
    return example_cfgs_with_fallthrough() + example_cfgs_without_fallthrough()


def all_viable_cfgs(language: Language):
    if Language.allows_switch_fallthrough(language):
        return all_example_cfgs()
    else:
        return example_cfgs_without_fallthrough()


def all_cfg_and_language_combos():
    l = []
    for language in Language.all_languages():
        l += list(product(all_viable_cfgs(language), [language]))
    return l
