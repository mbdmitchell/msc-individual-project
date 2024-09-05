import argparse
import logging
import pickle

from datetime import timedelta, datetime
import random
from TestDirectories import *

from tqdm import tqdm

from CFG.CFGGenerator import GeneratorConfig
from languages import Language, WASMLang
from my_common import generate_program, save_program, load_repo_paths_config, log_execution_time
from my_common.CodeType import CodeType
from CFG import CFGGenerator
from my_test import tst_generated_code


def main():
    args = parse_command_line_args()
    config = load_repo_paths_config()
    setup_logging(args.verbose)

    logging.info(f"Creating folders at {args.output_folder}...")
    test_directories = TestDirectories(f'./{args.output_folder}')

    @log_execution_time()
    def process_cfgs():
        for i_ in tqdm(range(args.no_of_graphs), desc="Fleshing CFGs"):
            cfg_ = pickle.load(open(f'{test_directories.cfg_filepath}/graph_{i_}.pickle', 'rb'))
            flesh_cfgs(args, cfg_, i_, test_directories)

    @log_execution_time()
    def run_tests():
        for g_ix in tqdm(range(args.no_of_graphs), desc="Running tests"):

            paths = pickle.load(open(f'{test_directories.directions_filepath}/directions_{g_ix}.pickle', 'rb'))
            bug_report_memos = []
            g_passes_all_tests = True

            # Load the program once for GLOBAL_ARRAY code type
            if args.code_type is CodeType.GLOBAL_ARRAY:
                program = pickle.load(open(f'{test_directories.program_filepath}/program_class_{g_ix}.pickle', "rb"))

            for d_ix, direction in enumerate(paths):

                p_passes_all_tests = True

                # Load the program per direction for LOCAL_ARRAY code type
                if args.code_type is CodeType.LOCAL_ARRAY:
                    program = pickle.load(open(
                        f'{test_directories.program_filepath}/program_class_{g_ix}_direction_{d_ix}.pickle', "rb"
                    ))

                match, msg = test_code(program, direction, d_ix, g_ix)

                if not match:
                    g_passes_all_tests = False
                    p_passes_all_tests = False
                    report = create_bug_report(direction, d_ix, msg, program, g_ix)
                    bug_report_memos.append(report)

                # Tidy direction-specific test files
                if args.code_type == CodeType.GLOBAL_ARRAY:
                    continue  # there are no direction-specific test files
                if args.tidy:
                    if (p_passes_all_tests and args.tidy_mode == 'working') \
                            or (not p_passes_all_tests and args.tidy_mode == 'non-working'):
                        test_directories.remove_file(FileType.CODE, graph_ix=g_ix, direction_ix=d_ix,
                                                     language=args.language, code_type=args.code_type)
                        test_directories.remove_file(FileType.PROGRAM_CLASS, graph_ix=g_ix, direction_ix=d_ix,
                                                     language=args.language, code_type=args.code_type)

            # Tidy test files
            if args.tidy:
                if (g_passes_all_tests and args.tidy_mode == 'working') \
                        or (not g_passes_all_tests and args.tidy_mode == 'non-working'):
                    test_directories.remove_file(FileType.CFG, graph_ix=g_ix)
                    test_directories.remove_file(FileType.DIRECTIONS, graph_ix=g_ix)
                    if args.code_type == CodeType.GLOBAL_ARRAY:
                        test_directories.remove_file(FileType.CODE, graph_ix=g_ix,
                                                     language=args.language, code_type=args.code_type)
                        test_directories.remove_file(FileType.PROGRAM_CLASS, graph_ix=g_ix,
                                                     language=args.language, code_type=args.code_type)

            if bug_report_memos:
                logging.info(bug_report_memos)

    def create_bug_report(direction_, p_, msg_, program_, g_ix) -> str:
        bug_filename = f'{test_directories.bugs_filepath}/{program_.language.extension()}_bug_cfg_{g_ix}_path{p_}.txt'
        with open(bug_filename, 'w') as bug_file:
            bug_file.write(f'CFG: {test_directories.cfg_filepath}/graph_{g_ix}.pickle\n\n')
            bug_file.write(f"Directions: {direction_}\n\n")
            bug_file.write(msg_)
        return bug_filename

    def test_code(program_, direction_, path_num, g_ix):
        match_, msg_ = tst_generated_code(program_, direction_, config)
        logging.debug(f'cfg_{g_ix}_path_{path_num}: {match_}, {msg_}')
        return match_, msg_

    # ------------

    logging.info("Generating CFGs...")
    generate_cfgs(args, test_directories.cfg_filepath)

    logging.info("Generating directions...")
    generate_direction_paths(args, test_directories.cfg_filepath, test_directories.directions_filepath)

    process_cfgs()
    run_tests()
    logging.info("DONE!")


def flesh_cfgs(args, cfg, i: int, test_directories):
    if args.code_type == CodeType.GLOBAL_ARRAY:
        # All paths use same program
        program = generate_program(args, cfg)
        save_program(program, f'{test_directories.code_filepath}/code_{i}', opt_level=getattr(args, 'opt_level', None))
        pickle.dump(program, open(f'{test_directories.program_filepath}/program_class_{i}.pickle', "wb"))

    elif args.code_type == CodeType.LOCAL_ARRAY:
        # Each path needs its own program
        directions = pickle.load(open(f'{test_directories.directions_filepath}/directions_{i}.pickle', 'rb'))

        for p, directions_list in enumerate(directions):
            program = generate_program(args, cfg, directions_list)
            code_filepath = f'{test_directories.code_filepath}/code_{i}_direction_{p}'
            program_filepath = f'{test_directories.program_filepath}/program_class_{i}_direction_{p}.pickle'
            opt_level = getattr(args, 'opt_level', None)

            save_program(program, code_filepath, opt_level)  # saves code
            pickle.dump(program, open(program_filepath, "wb"))  # saves 'Program' class

    else:
        raise ValueError("Invalid code type")


def setup_logging(verbose: bool):
    """Sets up the logging configuration."""
    log_format = "%(asctime)s - %(levelname)s - %(message)s"
    root_logger = logging.getLogger()
    if root_logger.hasHandlers():
        root_logger.handlers.clear()
    logging.basicConfig(level=logging.DEBUG if verbose else logging.INFO, format=log_format)


def generate_cfg_paths(cfg, graph_no, no_of_paths):
    time_when_last_path_found = datetime.now()
    TIME_LIMIT = timedelta(seconds=1)

    paths_set = set()

    aborted_path = False

    def within_time_limit():
        return datetime.now() - time_when_last_path_found < TIME_LIMIT

    while len(paths_set) < no_of_paths and within_time_limit():
        path = cfg.generate_valid_input_directions(max_length=512)
        if tuple(path) not in paths_set:  # (tuple to make hashable)
            time_when_last_path_found = datetime.now()
            paths_set.add(tuple(path))

    logging.debug(f'Paths for graph {graph_no}: {paths_set}')

    if len(paths_set) < no_of_paths:
        aborted_path = True
        logging.info(f"Aborted path generation for CFG {graph_no} (>1 seconds since found a distinct path)")

    return [list(path) for path in paths_set], aborted_path


@log_execution_time()
def generate_cfgs(args, cfg_filepath: str):
    if args.cfg_source == 'random':
        CFGGenerator(GeneratorConfig.allow_all(args.language)).generate_cfgs_method_uniform(
            target_filepath=cfg_filepath, no_of_graphs=args.no_of_graphs,
            min_depth=args.min_depth, max_depth=args.max_depth
        )
    elif args.cfg_source == 'swarm':
        CFGGenerator.generate_cfgs_method_swarm(
            language=args.language, target_filepath=cfg_filepath, no_of_graphs=args.no_of_graphs,
            min_depth=args.min_depth, max_depth=args.max_depth
        )
    else:
        raise ValueError("cfg_source not handled")  # shouldn't get here anyway 'cause throws if invalid at start


@log_execution_time()
def generate_direction_paths(args, cfg_filepath, directions_filepath):
    aborted_paths = []

    for i in tqdm(range(args.no_of_graphs), desc="Generating directions"):
        cfg = pickle.load(open(f'{cfg_filepath}/graph_{i}.pickle', 'rb'))
        paths, aborted_path = generate_cfg_paths(cfg, graph_no=i, no_of_paths=args.no_of_paths)

        if aborted_path:
            aborted_paths.append(i)

        pickle.dump(paths, open(f'{directions_filepath}/directions_{i}.pickle', "wb"))

    if len(aborted_paths) > 0:
        logging.debug(f"Aborted path generation for CFGs {aborted_paths} (>1 seconds since found a distinct path)")


def parse_command_line_args():
    parser = argparse.ArgumentParser()

    # Compulsory args
    parser.add_argument("language", type=Language.from_str,
                        help="The language to use (e.g., wasmlang, wgsllang, glsllang)")
    parser.add_argument("no_of_graphs", type=int)
    parser.add_argument("no_of_paths", type=int)
    parser.add_argument("cfg_source",
                        type=str,
                        choices=["random", "swarm"],
                        help=(
                            "Specify the source for configuration generation:\n"
                            "- 'random': Generates a truly random configuration.\n"
                            "- 'swarm': Uses a random subset of possible features; used for swarm testing."
                        ))
    parser.add_argument("code_type", type=CodeType.from_str, help=(
        "The type of code you want to generate for the tests:\n"
        "- 'global_array': The control flow path is dictated by a global 'directions' array in memory buffer\n"
        "- 'local_array': Similar to global_array, but the array is in the program"
        "- 'header_guard': The path is built-in to the program, so not passing and directions to the program"
    ))

    # Optional args
    parser.add_argument("--seed", type=int, help="Seed for randomness", default=None)
    parser.add_argument("--min_depth", type=int, default=3)
    parser.add_argument("--max_depth", type=int, default=5)
    parser.add_argument("--output_folder", type=str)
    parser.add_argument("--verbose", action="store_true", help="Print results for every test")
    parser.add_argument("--tidy", type=bool, nargs='?', const=True, default=True,
                        help="Clean up after the tests. Defaults to True if not specified.")
    parser.add_argument("--tidy_mode", type=str, choices=["working", "non-working"], default="working",
                        help="Specify whether to tidy working programs/tests or non-working ones. "
                             "Choose 'working' to keep only non-working programs (useful for debugging), "
                             "or 'non-working' to keep only working programs (useful for building a test suite)."
                        )
    args = parser.parse_args()

    # Language specific args
    if isinstance(args.language, WASMLang):
        parser.add_argument("--opt_level", type=str, choices=["O", "O1", "O2", "O3", "O4", "Os", "Oz"], default=None,
                            help="Optimization level for WASM")
        args = parser.parse_args()

    # Confirm valid args
    if args.min_depth > args.max_depth:
        parser.error("args.min_depth > args.max_depth")
    if args.code_type == 'header_guard':
        parser.error("The 'header_guard' code type is not fully supported yet")

    # Final arg assignment
    if args.output_folder is None:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
        opt_level_str = f'-{args.opt_level}' if hasattr(args, 'opt_level') and args.opt_level else ''
        args.output_folder = f'./{timestamp}_{args.language}_{opt_level_str}_TEST'
    if args.seed is not None:
        random.seed(args.seed)

    return args


if __name__ == "__main__":
    main()
