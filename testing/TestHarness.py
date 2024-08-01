import argparse
import logging
import os
import pickle
from datetime import timedelta, datetime
import random

from tqdm import tqdm

from CFG.CFGGenerator import GeneratorConfig
from common import Language, generate_program, save_program, load_config
from CFG import CFGGenerator
from my_test import tst_generated_code


def setup_logging(verbose: bool):
    """Sets up the logging configuration."""
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
        # logging.info(f"Aborted path generation for CFG {graph_no} (>1 seconds since found a distinct path)")

    return [list(path) for path in paths_set], aborted_path


def generate_cfgs(args, cfg_filepath: str):
    if args.cfg_source == 'random':

        generator_config = GeneratorConfig.allow_all(args.language)

        CFGGenerator(generator_config).generate_cfgs_method_uniform(target_filepath=cfg_filepath,
                                                                    no_of_graphs=args.no_of_graphs,
                                                                    min_depth=args.min_depth,
                                                                    max_depth=args.max_depth)

    elif args.cfg_source == 'swarm':

        CFGGenerator.generate_cfgs_method_swarm(language=args.language,
                                                target_filepath=cfg_filepath,
                                                no_of_graphs=args.no_of_graphs,
                                                min_depth=args.min_depth,
                                                max_depth=args.max_depth)

    else:
        raise ValueError("cfg_source not handled")  # shouldn't get here anyway 'cause throws if invalid at start


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

# TODO: Refactor: In a large testing campaign, you wouldn't want to necessarily generate 1,000,000+ CFGs, THEN all paths
#   , THEN test. Refactor so (1) parallelisable (2) tidies as you go so dont need folder w/ a bajillion files


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("language", type=language_type, help="The language to use (e.g., wasm, wgsl, glsl)")
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
    # parser.add_argument("static_code_level", type=int)  # 0 = global memory, 1 = static

    parser.add_argument("--opt_level", type=str, choices=["O", "O1", "O2", "O3", "O4", "Os", "Oz"], default=None,
                        help="Optimization level for WASM")
    parser.add_argument("--seed", type=int, help="Seed for randomness", default=None)
    parser.add_argument("--min_depth", type=int, default=3)
    parser.add_argument("--max_depth", type=int, default=5)
    parser.add_argument("--output_folder", type=str)
    parser.add_argument("--verbose", action="store_true", help="Print results for every test")

    args = parser.parse_args()
    if args.output_folder is None:
        args.output_folder = f'./{datetime.now().strftime("%Y-%m-%d, %H:%M:%S")}, ' \
                             f'{args.language.name} ' \
                             f'{("-" + args.opt_level) if args.opt_level else ""} ' \
                             '- TEST'

    if args.min_depth > args.max_depth:
        parser.error("min depth > max depth")

    config = load_config()

    if args.seed is not None:
        random.seed(args.seed)
    if args.opt_level and args.language != Language.WASM:
        parser.error("The --opt_level argument can only be used when the language is 'wasm'")

    setup_logging(args.verbose)

    logging.info("Creating folders...")

    base_path = f'./{args.output_folder}'
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
    generate_cfgs(args, cfg_filepath)

    logging.info("Generating directions...")
    generate_direction_paths(args, cfg_filepath, directions_filepath)

    for i in tqdm(range(args.no_of_graphs), desc="Fleshing CFGs"):
        cfg = pickle.load(open(f'{cfg_filepath}/graph_{i}.pickle', 'rb'))

        program = generate_program(args.language, cfg)
        save_program(program, f'{code_filepath}/code_{i}', opt_level=args.opt_level)

        pickle.dump(program, open(f'{program_filepath}/program_class_{i}.pickle', "wb"))

    for g in tqdm(range(args.no_of_graphs), desc="Running tests"):

        g_passes_all_tests = True

        program = pickle.load(open(f'{program_filepath}/program_class_{g}.pickle', "rb"))
        paths = pickle.load(open(f'{directions_filepath}/directions_{g}.pickle', 'rb'))

        bug_report_memos = []

        for p in range(len(paths)):
            direction = paths[p]
            match, msg = tst_generated_code(program,
                                            direction,
                                            config,
                                            clear_files_after=True)

            logging.debug(f'cfg_{g}_path_{p}: {match}, {msg}')

            if not match:
                g_passes_all_tests = False

                bug_filename = f'{bugs_filepath}/{program.language.extension()}_bug_cfg_{g}_path{p}.txt'
                with open(bug_filename, 'w') as bug_file:
                    bug_file.write(f'CFG: {cfg_filepath}/graph_{g}.pickle\n\n')
                    bug_file.write(f"Directions: {direction}\n\n")
                    bug_file.write(msg)

                bug_report_memos.append(f'Bug found: report written to {bug_filename}')

        if g_passes_all_tests:
            os.remove(f'{cfg_filepath}/graph_{g}.pickle')
            os.remove(f'{directions_filepath}/directions_{g}.pickle')
            os.remove(f'{program_filepath}/program_class_{g}.pickle')
            os.remove(f'{code_filepath}/code_{g}.{args.langauge.extension()}')

        if len(bug_report_memos) > 0:
            logging.info(bug_report_memos)

    logging.info("DONE!")
    # TODO: Add report.txt w/ all bugs (if any) found, any paths aborted, all harness params --min_depth=2 --max_depth=3


if __name__ == "__main__":
    main()
