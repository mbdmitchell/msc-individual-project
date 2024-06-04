# A runner script to go through the entire test process

import os

from utils import execute_concurrently, test_cfg

os.makedirs('./results', exist_ok=True)

# TESTED: Seed 0 -> 99,999

no_of_cfgs = 10000
no_of_paths = 10

tasks = [test_cfg] * no_of_cfgs

task_args_list = [(seed, no_of_paths) for seed in range(no_of_cfgs)]

elapsed_time = execute_concurrently(tasks, task_args_list)
print(f'Total time taken: {elapsed_time:.2f} seconds')