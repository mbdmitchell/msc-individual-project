import os
import pickle
import subprocess
from pprint import pprint

import WGSL.utils
from CFG import CFG

program_class_filepath = ...
script_path = '../../testing/run_individual_test_via_program.py'

with open('/evaluation/wgsl_bug_reduction/bug/graph_2439.pickle', 'rb') as file:
    cfg: CFG = pickle.load(file)

def assemble_command(directions: tuple[int]) -> list[str]:
    directions_str = ','.join(map(str, directions))
    command = ['python', script_path, program_class_filepath, directions_str]
    return command


def is_path_mismatch(input_directions: tuple[int, ...]) -> bool:

    try:
        input_directions = list(input_directions)
        shader_filepath = ...
        code_type = WGSL.utils.classify_shader_code_type(shader_filepath)
        expected_path = cfg.expected_output_path(input_directions)
        env = os.environ.copy()

        is_match, msg = WGSL.utils.tst_shader(shader_filepath, expected_path, env, input_directions)
        return not is_match
    except Exception as e:
        raise Exception(f"An error occurred: {e}")


def all_directions_with_n_consecutive_elems_removed(lst: tuple[int, ...], no_of_elems: int) -> set[tuple[int, ...]]:
    set_of_tuples = set()
    for i in range(len(lst) - no_of_elems + 1):
        new_tuple = tuple(lst[:i] + lst[i + no_of_elems:])
        set_of_tuples.add(new_tuple)
    return set_of_tuples


def calc_failing_subsequences(directions: tuple[int, ...]) -> set[tuple[int, ...]]:

    tested_subsequences = set()

    def calc_failing_subsequences_aux(remove_n_consecutive_elems: int) -> set[tuple[int, ...]]:

        if remove_n_consecutive_elems == 0:
            return set()

        print(f"Testing {directions}, removing {remove_n_consecutive_elems} consecutive elements...")

        # all subsequences for given _directions
        direction_subsequences = all_directions_with_n_consecutive_elems_removed(directions,
                                                                                 remove_n_consecutive_elems)

        # calc failing subsequences
        failing_direction_subsequences = set()
        for d in direction_subsequences:
            if d in tested_subsequences:
                print(f"Skipping direction {d}")
                continue
            print(f"Testing direction {d}...")
            tested_subsequences.add(d)
            if is_path_mismatch(d):
                failing_direction_subsequences.add(d)
                print(f"Mismatch: {d}")
            else:
                # NB: This doesn't mean it's definitely a match, it could be that d caused IndexError due to running out
                # of directions before reaching the end of the shader
                print(f"Not mismatch")

        if len(failing_direction_subsequences) == 0:
            print(f"No failing direction subsequences. Trying again direction again... ")
            return calc_failing_subsequences_aux(remove_n_consecutive_elems - 1)
        else:
            print(f"Failing direction subsequence(s) found. Calling failing_subsequences_aux for each... ")
            all_failing = set(failing_direction_subsequences)
            for f in failing_direction_subsequences:
                all_failing.update(calc_failing_subsequences_aux(remove_n_consecutive_elems))
            return all_failing

    # start by trying to remove half the directions (number arbitrary)
    return calc_failing_subsequences_aux(len(directions)//2)


# --------------------------------------------------------------------------------------------------------

starting_directions = (...)  # tuple of directions


failing_subsequences: set[tuple[int, ...]] = calc_failing_subsequences(starting_directions)
sorted_tuples: list[tuple[int, ...]] = sorted(failing_subsequences, key=len)

pprint(sorted_tuples)
