import subprocess


def get_visitable_mutant_ids():
    try:
        with open('./visitable_mutants.txt', 'r') as file:
            lines = file.readlines()
    except FileNotFoundError:
        raise AssertionError("'./visitable_mutants.txt' does not exist.")

    if not lines:
        raise AssertionError("'./visitable_mutants.txt' is empty.")

    return [int(line.strip()) for line in lines]

def get_non_visitable_mutant_ids():

    visitable = set(get_visitable_mutant_ids())
    largest_mutant_id = get_largest_mutant_id()

    if largest_mutant_id is None:
        print("Error: Could not retrieve the largest mutant ID.")
        return None

    not_visitable = [i for i in range(largest_mutant_id + 1) if i not in visitable]

    return not_visitable

def get_largest_mutant_id():
    command = ["python3", "/Users/maxmitchell/dredd/scripts/query_mutant_info.py",
               "/Users/maxmitchell/Documents/msc-control-flow-fleshing-project/evaluation/mutation_testing/mutant_info_mutant_tracking.json",
               "--largest-mutant-id"]
    result = subprocess.run(command, capture_output=True, text=True)

    if result.returncode == 0:
        try:
            largest_mutant_id = int(result.stdout.strip())
            return largest_mutant_id
        except ValueError:
            print("Error: Could not parse the largest mutant ID.")
            return None
    else:
        print("Error: Script did not run successfully.")
        return None