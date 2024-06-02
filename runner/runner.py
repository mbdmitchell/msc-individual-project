# A runner script to go through the entire test process

# DONE: Generate CFGs -- ... --> (confirmed valid) wasm programs
# TODO: Inc. generating direction paths for each CFG,
#  + input file for each path,
#  + running all direction paths w/ correspond CFG and confirming match

from CFG import CFG, GraphFormat
import os
import subprocess
from WATProgramModule import WATProgram, WATProgramBuilder
from WATProgramModule.WATProgram import WebAssemblyFormat
import concurrent.futures
import time


def execute_concurrently(tasks, task_args_list):
    """
    Parameters:
        tasks (list): A list of task functions to execute.
        task_args_list (list): A list of tuples, where each tuple contains the arguments for the corresponding task.
    Returns:
        float: The time taken to execute all tasks.
    """
    start_time = time.time()

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(task, *args) for task, args in zip(tasks, task_args_list)]
        for future in concurrent.futures.as_completed(futures):
            try:
                future.result()  # To raise any exceptions that occurred during the processing
            except Exception as e:
                print(f'Exception occurred: {e}')

    end_time = time.time()
    elapsed_time = end_time - start_time
    return elapsed_time


def validate_wasm_files(folder_path):
    all_valid = True
    for filename in os.listdir(folder_path):
        if filename.endswith('.wasm'):
            file_path = os.path.join(folder_path, filename)
            try:
                subprocess.run(['wasm-validate', '--enable-multi-memory', file_path], check=True)
            except subprocess.CalledProcessError:
                print(f"Validation failed: {file_path}")
                all_valid = False
    print('Validation complete.')
    if all_valid:
        print('All wasm files are valid')


def process_file(i, pickle_file):
    cfg = CFG().load(f'./results/generated_cfgs/{pickle_file}')
    program: WATProgram = WATProgramBuilder(filename=f'./results/generated_cfgs/{pickle_file}').build()
    program.save(f'./results/input_programs/code{i}', WebAssemblyFormat.WASM)
    program.save(f'./results/input_programs/code{i}', WebAssemblyFormat.WAT)


def generate_and_save_cfg(i, include_png: bool = False):
    cfg = CFG.generate_valid_cfg()
    cfg.save(f'./results/generated_cfgs/cfg{i}.pickle', GraphFormat.CFG)
    if include_png:
        cfg.save(f'./results/generated_cfgs/images/cfg{i}.png', GraphFormat.PNG)

# -----------


os.makedirs('./results/generated_cfgs/images', exist_ok=True)
os.makedirs('./results/input_programs', exist_ok=True)

# Generate and save CFGs

num_cfgs = 5

tasks = [generate_and_save_cfg] * num_cfgs
task_args_list = [(i,) for i in range(num_cfgs)]
execution_time = execute_concurrently(tasks, task_args_list)
print(f"Time taken to generate and save CFGs: {execution_time:.2f} seconds")

# Load CFGs and generate WAT programs
pickle_files = [f for f in os.listdir('./results/generated_cfgs') if f.endswith('.pickle')]
tasks = [process_file] * len(pickle_files)

task_args_list = [(i, pickle_file) for i, pickle_file in enumerate(pickle_files)]
execution_time = execute_concurrently(tasks, task_args_list)
print(f"Time taken to process files: {execution_time:.2f} seconds")

validate_wasm_files('./results/input_programs/')
