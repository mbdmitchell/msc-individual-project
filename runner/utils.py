import concurrent.futures
import os
import subprocess
import time

from CFG import CFG
from WAT import ProgramBuilder
from WAT.Program import WebAssemblyFormat
from threading import Lock

print_lock = Lock()
processed_cfgs_lock = Lock()
processed_cfgs: dict[int, bool] = {}

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


def test_cfg(seed: int, save_to_folder: str, no_of_paths: int = None, verbose: bool = False) -> bool:
    """
    seed: used to generate CFG
    save_to_folder: path of folder that results will be saved to
    no_of_paths: specify number of cfg paths to test
    """

    global processed_cfgs

    def calc_no_of_paths(cfg: CFG):
        """Approx. based on graph complexity"""
        graph_complexity = (cfg.number_of_edges() + cfg.number_of_nodes()) // 2
        max_no_of_paths = 50  # arbitrary
        return min(graph_complexity, max_no_of_paths)

    cfg = CFG.generate_valid_cfg(seed)

    mismatch_log_path = f'{save_to_folder.rsplit("/", 1)[0]}/mismatch_log.txt'
    cfg_results_folder_path = f'{save_to_folder}/cfg{seed}'
    os.makedirs(f'{save_to_folder}/cfg{seed}', exist_ok=True)

    # ... hash

    cfg_hash = hash(cfg)
    if cfg_hash in processed_cfgs:
        return processed_cfgs[cfg_hash]

    # ... generate wasm binary



    program = ProgramBuilder(cfg=cfg).build()
    program.save(os.path.join(cfg_results_folder_path, 'code'), WebAssemblyFormat.WASM)
    program.save(os.path.join(cfg_results_folder_path, 'code'), WebAssemblyFormat.WAT)  # for debugging

    # ... validate wasm binary

    wasm_filepath = f'{cfg_results_folder_path}/code.wasm'

    run_subprocess(['wasm-validate', '--enable-multi-memory', wasm_filepath])

    # ... run for each input direction

    if no_of_paths is None:
        no_of_paths = calc_no_of_paths(cfg)

    input_directions = [cfg.generate_valid_input_directions(seed + j) for j in range(no_of_paths)]

    processed_cfgs[seed] = True
    all_match = True

    for d in input_directions:

        is_match, msg = test_wasm(wasm_filepath, d, cfg.expected_output_path(d))
        if not is_match:
            processed_cfgs[seed] = is_match
            all_match = False
            with open(mismatch_log_path, 'a') as log_file:
                log_file.write(f'{msg}\n')

    if verbose:
        with print_lock:
            print(f'Done: CFG SEED {seed}')

    return all_match

def test_wasm(filepath: str, input_directions: list[int], expected_output_path: list[int], clear_files_after = True) -> (bool, str):
    """filepath = filepath to wasm module"""

    directions_path = f'{filepath.rsplit("/", 1)[0]}/directions.txt'
    output_path = f'{filepath.rsplit("/", 1)[0]}/output.txt'

    try:
        with open(directions_path, 'w') as file:
            file.write(str(input_directions))

        is_valid = run_subprocess(['wasm-validate', '--enable-multi-memory', filepath])

        if not is_valid:
            return False, "Invalid wasm module (`wasm-validate`)"

        is_valid = run_subprocess(['node', './runner/run_manual_cf.js', filepath])
        if not is_valid:
            return False, f"FAILED: node ./runner/run_manual_cf.js {filepath}"

        # ... actual & expected output path

        with open(output_path) as f:
            output_txt = f.readline()

        actual_output_path = [int(x) for x in output_txt.split(",")]

        is_match: bool = actual_output_path == expected_output_path

        if is_match:
            return True, ""
        else:
            msg: str = f'Expected: {expected_output_path}. Actual: {actual_output_path}'
            return False, msg

    finally:
        if clear_files_after:
            if os.path.exists(directions_path):
                os.remove(directions_path)
            if os.path.exists(output_path):
                os.remove(output_path)