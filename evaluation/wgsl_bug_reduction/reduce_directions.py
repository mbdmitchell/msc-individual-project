import subprocess
from pprint import pprint

program_class_filepath = '/Users/maxmitchell/Documents/msc-control-flow-fleshing-project/evaluation/wgsl_bug_reduction/reduced_program_class.pickle'
script_path = '/Users/maxmitchell/Documents/msc-control-flow-fleshing-project/testing/run_individual_test.py'


def assemble_command(directions: tuple[int]) -> list[str]:
    directions_str = ','.join(map(str, directions))
    command = ['python', script_path, program_class_filepath, directions_str]
    return command


def is_path_mismatch(directions: tuple[int, ...]) -> bool:

    command = assemble_command(directions)
    try:
        result = subprocess.run(command, capture_output=True, text=True)
    except subprocess.TimeoutExpired:
        raise TimeoutError(f"Command timed out for directions: {directions}")
    except Exception as e:
        raise Exception(f"An error occurred: {e}")

    stdout: str = result.stdout.strip()

    if "False" in stdout:  # i.e. if actual path != expected path
        return True
    else:
        return False


def all_directions_with_n_consecutive_elems_removed(lst: tuple[int, ...], no_of_elems: int) -> set[tuple[int, ...]]:
    set_of_tuples = set()
    for i in range(len(lst) - no_of_elems + 1):
        new_tuple = tuple(lst[:i] + lst[i + no_of_elems:])
        set_of_tuples.add(new_tuple)
    return set_of_tuples



def calc_failing_subsequences(directions: tuple[int, ...]) -> set[tuple[int, ...]]:

    tested_subsequences = set()

    def calc_failing_subsequences_aux(_directions: tuple[int, ...], remove_n_consecutive_elems: int) -> set[tuple[int, ...]]:

        if remove_n_consecutive_elems == 0:
            return set()

        print(f"Testing {_directions}, removing {remove_n_consecutive_elems} consecutive elements...")

        # all subsequences for given _directions
        direction_subsequences = all_directions_with_n_consecutive_elems_removed(_directions,
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
            return calc_failing_subsequences_aux(_directions, remove_n_consecutive_elems - 1)
        else:
            print(f"Failing direction subsequence(s) found. Calling failing_subsequences_aux for each... ")
            all_failing = set(failing_direction_subsequences)
            for f in failing_direction_subsequences:
                all_failing.update(calc_failing_subsequences_aux(f, remove_n_consecutive_elems))
            return all_failing

    return calc_failing_subsequences_aux(directions, remove_n_consecutive_elems=12)
    # '12' is specific to code_1083 bug. Could start at as high as len(directions) - 1...
    # but in practise it doesn't help and takes longer


# --------------------------------------------------------------------------------------------------------

# the initial directions that caused cfg_1083_path_6 to fail
# [1, 1, 1, 1, 1, 0, 2, 1, 0, 1, 0, 1, 1, 1, 0, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0,
#  0, 0, 0, 0 ]

# --------------------------------------------------------------------------------------------------------

starting_directions = (1, 1, 1, 1, 1, 0, 2, 1, 0, 1,
                       0, 1, 1, 1, 0, 1, 1, 1, 0, 1,
                       1, 1, 1, 1, 1, 1, 1, 1, 1, 0,
                       0, 0, 0, 1, 0, 1, 0, 0, 0, 0,
                       0, 0, 0)


failing_subsequences: set[tuple[int, ...]] = calc_failing_subsequences(starting_directions)
sorted_tuples: list[tuple[int, ...]] = sorted(failing_subsequences, key=len)

pprint(sorted_tuples)

# --------------------------------------------------------------------------------------------------------

# FROM...

# (1, 1, 1, 1, 1, 0, 2, 1, 0, 1,
#  0, 1, 1, 1, 0, 1, 1, 1, 0, 1,
#  1, 1, 1, 1, 1, 1, 1, 1, 1, 0,
#  0, 0, 0, 1, 0, 1, 0, 0, 0, 0,
#  0, 0, 0)

# FINAL: shortened directions that still fail

# [(1, 1, 1, 1, 1, 0, 1, 0, 1, 0,
#   1, 1, 1, 0, 1, 1, 1, 0, 1, 1,
#   1, 1, 1, 1, 1, 1, 1, 1, 0, 0,
#   0, 0, 1, 0, 1, 0, 0, 0, 0, 0)]
