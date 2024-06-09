# A runner script to go through the entire test process

from utils import execute_concurrently, test_cfg

starting_seed = 100000  # TESTED: 0 -> 99,999

no_of_cfgs = 10
specified_no_of_paths = None  # if None, test_cfg will calc an approx no of paths to follow based on graph complexity

tasks = [test_cfg] * no_of_cfgs

task_args_list = [(starting_seed + inc, './results', specified_no_of_paths, True) for inc in range(no_of_cfgs)]

elapsed_time = execute_concurrently(tasks, task_args_list)
print(f'Total time taken: {elapsed_time:.2f} seconds')

# TEST individual CFG
# result = test_cfg(10000, './results', no_of_paths=specified_no_of_paths, verbose=True)
# print(result)