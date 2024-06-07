import concurrent.futures
import logging
import os
import shutil
import subprocess
import time

from CFG import CFG
from WATProgramModule import WATProgramBuilder
from WATProgramModule.WATProgram import WebAssemblyFormat
from threading import Lock

print_lock = Lock()
processed_cfgs_lock = Lock()
processed_cfgs = set()

logging.basicConfig(
    filename='./runner/results/mismatch_log.txt',   # Log file name
    level=logging.INFO,            # Log level
    format='%(message)s',  # Log format
    filemode='a'
)


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


def run_subprocess(command, verbose = False):
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            check=True,
            text=True
        )
        if verbose:
            print(f"{command} succeeded.", result.stdout)
    except subprocess.CalledProcessError as e:
        if verbose:
            print(f"{command} failed:", e.stderr)
            print("Command that failed:", e.cmd)
            print("Return code:", e.returncode)
        return False
    return True


def test_cfg(seed: int, no_of_paths: int = None, verbose: bool = False):

    global processed_cfgs

    def in_processed_cfgs(cfg_hash):
        with processed_cfgs_lock:
            return cfg_hash in processed_cfgs

    def calc_no_of_paths(cfg: CFG):
        graph_complexity = (cfg.number_of_edges() + cfg.number_of_nodes()) // 2  # an approx measure of complexity
        max_no_of_paths = 50
        return min(graph_complexity, max_no_of_paths)

    cfg = CFG.generate_valid_cfg(seed)

    # TODO: change so number of paths based on complexity of CFG

    # ... hash

    cfg_hash = hash(cfg)
    if in_processed_cfgs(cfg_hash):
        return
    else:
        processed_cfgs.add(cfg_hash)

    # ... generate wasm binary

    os.makedirs(f'./results/cfg{seed}', exist_ok=True)

    program = WATProgramBuilder(cfg=cfg).build()
    program.save(os.path.join(f'./results/cfg{seed}', 'code'), WebAssemblyFormat.WASM)
    program.save(os.path.join(f'./results/cfg{seed}', 'code'), WebAssemblyFormat.WAT)  # for debugging

    # ... validate wasm binary

    run_subprocess(['wasm-validate', '--enable-multi-memory', f'./runner/results/cfg{seed}/code.wasm'])

    # ... run for each input direction

    if no_of_paths is None:
        no_of_paths = calc_no_of_paths(cfg)

    input_directions = [cfg.generate_valid_input_directions(seed + j) for j in range(no_of_paths)]

    for d in input_directions:

        with open(f'./results/cfg{seed}/directions.txt', 'w') as file:
            file.write(str(d))

        # ... run wasm module (w/ directions.txt in same folder as code.wasm)

        run_subprocess(['node', './runner/run_manual_cf.js', f'./results/cfg{seed}/code.wasm'])

        # ... actual & expected output path

        with open(f'./results/cfg{seed}/output.txt') as f:
            output_txt = f.readline()

        actual_output_path = [int(x) for x in output_txt.split(",")]
        expected_output_path = cfg.expected_output_path(d)

        # ... display results

        is_match: bool = actual_output_path == expected_output_path

        if not is_match:
            msg: str = f'CFG SEED {seed}! Directions: {d}. Expected: {expected_output_path}. Actual: {actual_output_path}'
            with print_lock:
                print(msg)
                logging.info(msg)


    shutil.rmtree(f'./results/cfg{seed}')

    if verbose:
        with print_lock:
            print(f'Done: CFG SEED {seed}')


def manual_test_cfg(cfg_seed: int, input_directions: list[int], verbose: bool = False):

    cfg = CFG.generate_valid_cfg(cfg_seed)

    # TODO: change so number of paths based on complexity of CFG

    # ... generate wasm binary

    os.makedirs(f'./results/cfg{cfg_seed}', exist_ok=True)

    program = WATProgramBuilder(cfg=cfg).build()
    program.save(os.path.join(f'./results/cfg{cfg_seed}', 'code'), WebAssemblyFormat.WASM)
    program.save(os.path.join(f'./results/cfg{cfg_seed}', 'code'), WebAssemblyFormat.WAT)  # for debugging

    # ... validate wasm binary

    run_subprocess(['wasm-validate', '--enable-multi-memory', f'./runner/results/cfg{cfg_seed}/code.wasm'])


    with open(f'./results/cfg{cfg_seed}/directions.txt', 'w') as file:
        file.write(str(input_directions))

    # ... run wasm module (w/ directions.txt in same folder as code.wasm)

    run_subprocess(['node', './runner/run_manual_cf.js', f'./results/cfg{cfg_seed}/code.wasm'])

    # ... actual & expected output path

    with open(f'./results/cfg{cfg_seed}/output.txt') as f:
        output_txt = f.readline()

    actual_output_path = [int(x) for x in output_txt.split(",")]
    expected_output_path = cfg.expected_output_path(input_directions)

    # ... display results

    is_match: bool = actual_output_path == expected_output_path

    msg: str = f'CFG SEED {cfg_seed}. Directions: {input_directions}. Expected: {expected_output_path}. Actual: {actual_output_path}'
    print(msg)