import pickle
import sys

from my_common import load_repo_paths_config
from my_test.flesh_test import tst_generated_code


def parse_directions(_directions_str):
    return [int(x) for x in _directions_str.split(',')]


def main(program_class_path, _directions_str):

    program = pickle.load(open(program_class_path, "rb"))
    direction = parse_directions(_directions_str)
    match, msg = tst_generated_code(program, direction, load_repo_paths_config())

    print(match, msg)


if __name__ == "__main__":

    if len(sys.argv) != 3:
        print("Usage: python run_individual_test.py path/to/program_class directions_str")
        sys.exit(1)

    program_class_filepath = sys.argv[1]
    directions_str = sys.argv[2]

    main(program_class_filepath, directions_str)