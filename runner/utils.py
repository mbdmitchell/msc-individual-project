import concurrent.futures
import logging
import subprocess
import time

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


def run_subprocess(command, output_path=None, redirect_output=False, verbose=False):
    """Run a subprocess command and handle errors."""
    try:
        if redirect_output and output_path:
            with open(output_path, 'w') as output_file:
                result = subprocess.run(command, stdout=output_file, stderr=subprocess.PIPE, check=True, text=True)
        else:
            result = subprocess.run(command, capture_output=True, check=True, text=True)
            if output_path:
                with open(output_path, 'w') as output_file:
                    output_file.write(result.stdout)

        #logging.debug(f"{command} succeeded.", result.stdout if not redirect_output else "")

        return True, result.stdout if not redirect_output else None
    except subprocess.CalledProcessError as e:
        if verbose:
            #logging.debug(f"{command} failed:", e.stderr)
            logging.debug("Command that failed:", e.cmd)
            logging.debug("Return code:", e.returncode)
        return False, e.stderr
