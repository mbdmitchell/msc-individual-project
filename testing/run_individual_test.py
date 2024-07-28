# $ python run_individual_test.py path/to/program_class [directions]
# e.g. directions = '1,2,3,2,0,0,1'
import os
import pickle
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from test.flesh_test import tst_generated_code

def parse_directions(directions_str):
    # Parse the directions string into a list of integers
    return [int(x) for x in directions_str.split(',')]


def main(program_class_path, directions_filepath):
    # Load the program class object from the pickle file
    program = pickle.load(open(program_class_path, "rb"))

    # Parse the directions string
    with open(directions_filepath, "r") as file:
        dir_str = file.read()
    direction = parse_directions(dir_str)

    # Get the expected output path based on the direction
    expected_output = program.cfg.expected_output_path(direction)

    # Derive the code path from the program class path
    code_path_base = program_class_path.replace('program_classes/program_class_', 'code/code_').replace('.pickle', '')
    code_path = f'{code_path_base}.{program.language.extension()}'

    # Run the test
    match, msg = tst_generated_code(program.language,
                                    code_path,
                                    direction,
                                    expected_output,
                                    clear_files_after=True)

    # Print the result
    print(match, msg)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python run_individual_test.py path/to/program_class [directions]")
        sys.exit(1)

    program_class_path = sys.argv[1]
    directions_str = sys.argv[2]

    main(program_class_path, directions_str)