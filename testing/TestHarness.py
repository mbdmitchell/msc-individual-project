import argparse
import logging
import os
import pickle
import sys
from datetime import timedelta, datetime
import random

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from test.flesh_test import tst_generated_code
from common.utils import generate_program, save_program
from CFG import CFGGenerator
from common.Language import Language

# TODO: select language, opt-level(s) (if applicable)
def setup_logging(verbose: bool):
    """
    Sets up the logging configuration.
    """
    log_format = "%(asctime)s - %(levelname)s - %(message)s"
    root_logger = logging.getLogger()
    if root_logger.hasHandlers():
        root_logger.handlers.clear()
    logging.basicConfig(level=logging.DEBUG if verbose else logging.INFO, format=log_format)

def language_type(language_str):
    try:
        return Language[language_str.upper()]
    except KeyError:
        raise argparse.ArgumentTypeError(
            f"Invalid language: {language_str}. Choose from {[l.name.lower() for l in Language]}.")


def generate_paths(cfg, graph_no, no_of_paths):

    time_when_last_path_found = datetime.now()
    TIME_LIMIT = timedelta(seconds=1)

    paths_set = set()

    while len(paths_set) < no_of_paths and datetime.now() - time_when_last_path_found < TIME_LIMIT:
        path = cfg.generate_valid_input_directions(max_length=512)
        if tuple(path) not in paths_set:  # (tuple to make hashable)
            time_when_last_path_found = datetime.now()
            paths_set.add(tuple(path))

    logging.info(f'Paths for graph {graph_no}: {paths_set}')

    if len(paths_set) < no_of_paths:
        logging.info(f"Aborted path generation for CFG {graph_no} (>1 seconds since found a distinct path)")

    return [list(path) for path in paths_set]


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("language", type=language_type, help="The language to use (e.g., wasm, wgsl, glsl)")
    parser.add_argument("no_of_graphs", type=int)
    parser.add_argument("no_of_paths", type=int)
    # parser.add_argument("min_depth", type=int)
    # parser.add_argument("max_depth", type=int)
    parser.add_argument("folder", type=str)
    parser.add_argument("--opt_level", type=str, choices=["O", "O1", "O2", "O3", "O4", "Os", "Oz"], default=None, help="Optimization level for WASM")

    parser.add_argument("--verbose", action="store_true", help="Print results for every test")
    parser.add_argument("--seed", type=int, help="Seed for randomness", default=None)
    # parser.add_argument("--cfg_generation_approach", type=str)
    # parser.add_argument("--static_code_level", type=int)  # 0 = big directions array, 1 = inbuilt stuff

    args = parser.parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    setup_logging(args.verbose)

    logging.info("Creating folders...")

    base_path = f'./{args.folder}'
    cfg_filepath = f"{base_path}/cfgs"
    directions_filepath = f"{base_path}/paths"
    program_filepath = f"{base_path}/program_classes"
    code_filepath = f"{base_path}/code"
    bugs_filepath = f"{base_path}/bugs"

    directories = [base_path, cfg_filepath, directions_filepath, program_filepath, bugs_filepath, code_filepath]

    for directory in directories:
        if os.path.exists(directory) and os.listdir(directory):
            raise Exception(f"Directory {directory} is not empty.")

    for directory in directories:
        os.makedirs(directory, exist_ok=True)

    logging.info("Generating CFGs...")

    CFGGenerator().generate_cfgs(target_filepath=cfg_filepath,
                                 no_of_graphs=args.no_of_graphs,
                                 min_depth=3,
                                 max_depth=4,
                                 min_successors=2,
                                 max_successors=5,
                                 allow_fallthrough=Language.allows_switch_fallthrough(args.language),
                                 is_complex=True,
                                 break_continue_probability=1)

    logging.info("Generating directions...")

    for i in range(args.no_of_graphs):
        cfg = pickle.load(open(f'{cfg_filepath}/graph_{i}.pickle', 'rb'))
        paths = generate_paths(cfg, graph_no=i, no_of_paths=args.no_of_paths)
        pickle.dump(paths, open(f'{directions_filepath}/directions_{i}.pickle', "wb"))

    logging.info("Fleshing CFGs... ")

    for i in range(args.no_of_graphs):

        cfg = pickle.load(open(f'{cfg_filepath}/graph_{i}.pickle', 'rb'))
        program = generate_program(args.language, cfg)
        pickle.dump(program, open(f'{program_filepath}/program_class_{i}.pickle', "wb"))

        if args.opt_level:
            assert args.language == Language.WASM
            opt_wasm: bytes = program.optimise(args.opt_level)
            with open(f'{code_filepath}/code_{i}.wasm', 'wb') as f:
                f.write(opt_wasm)
        else:
            save_program(program, f'{code_filepath}/code_{i}')

    logging.info("Running tests... ")

    for g in range(args.no_of_graphs):

        logging.info(f"Testing graph {g}")

        g_passes_all_tests = True

        program = pickle.load(open(f'{program_filepath}/program_class_{g}.pickle', "rb"))
        paths = pickle.load(open(f'{directions_filepath}/directions_{g}.pickle', 'rb'))

        for p in range(len(paths)):
            direction = paths[p]
            expected_output = program.cfg.expected_output_path(direction)
            match, msg = tst_generated_code(args.language,
                                            f'{code_filepath}/code_{g}.{program.language.extension()}',
                                            direction,
                                            expected_output,
                                            clear_files_after=True)

            logging.debug(f'cfg_{g}_path_{p}: {match}, {msg}')

            if not match:

                g_passes_all_tests = False

                bug_filename = f'{bugs_filepath}/{program.language.extension()}_bug_cfg_{g}_path{p}.txt'
                with open(bug_filename, 'w') as bug_file:
                    bug_file.write(f'CFG: {cfg_filepath}/graph_{g}.pickle\n\n')
                    bug_file.write(f"Directions: {direction}\n\n")
                    bug_file.write(msg)

                logging.info(f'Bug report written to {bug_filename}')

        if g_passes_all_tests:
            os.remove(f'{cfg_filepath}/graph_{g}.pickle')
            os.remove(f'{directions_filepath}/directions_{g}.pickle')
            os.remove(f'{program_filepath}/program_class_{g}.pickle')

    logging.info("DONE!")


if __name__ == "__main__":
    main()
