import os
import subprocess
from pathlib import Path
from typing import Optional

from my_common import load_repo_paths_config


def get_visitable_mutant_ids() -> list[int]:

    # this prevents "File not found" error
    current_dir = Path(__file__).parent
    file_path = current_dir / 'visitable_mutants.txt'

    try:
        with open(file_path, 'r') as file:
            lines = file.readlines()
    except FileNotFoundError:
        raise AssertionError("'./visitable_mutants.txt' does not exist.")

    if not lines:
        raise AssertionError("'./visitable_mutants.txt' is empty.")

    ids = [int(line.strip()) for line in lines]

    return list(set(ids))  # removes duplicates


def get_non_visitable_mutant_ids() -> list[int]:

    visitable = set(get_visitable_mutant_ids())
    largest_mutant_id = get_largest_mutant_id()

    if largest_mutant_id is None:
        raise LookupError("Could not retrieve the largest mutant ID.")

    not_visitable = [i for i in range(largest_mutant_id + 1) if i not in visitable]

    return not_visitable


def get_largest_mutant_id() -> int:
    command = ["python3", "/Users/maxmitchell/dredd/scripts/query_mutant_info.py",
               "/Users/maxmitchell/Documents/msc-control-flow-fleshing-project/evaluation/mutation_testing"
               "/mutant_info_mutant_tracking.json",
               "--largest-mutant-id"]
    result = subprocess.run(command, capture_output=True, text=True)

    if result.returncode == 0:
        try:
            largest_mutant_id = int(result.stdout.strip())
            return largest_mutant_id
        except ValueError:
            raise ValueError("Could not parse the largest mutant ID.")
    else:
        raise RuntimeError("Error: Script did not run successfully.")

