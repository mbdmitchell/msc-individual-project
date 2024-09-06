from __future__ import annotations

import json
import logging
import os
import time
from functools import wraps
import platform
from typing import Optional


def parse_int_list(string: str) -> list[int]:
    return [int(x) for x in string.split(',')]


log_file = '../execution_times.txt'

def log_execution_time(file_path=log_file):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)  # execute function
            end_time = time.time()
            execution_time = end_time - start_time
            with open(file_path, 'a') as f:  # log to file
                f.write(f"Function '{func.__name__}' executed in {execution_time:.6f} seconds\n")

            return result

        return wrapper

    return decorator

def load_repo_paths_config():

    current_os = platform.system()

    if current_os == 'Linux':
        # On lab machines you have to pip install after cloning repo so have to
        # explicitly point to the config file, else it searches wrong place
        config_path = '/homes/mbm22/Documents/modules/msc-project/msc-individual-project/config.json'
    else:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(script_dir, '..', 'config.json')

    try:
        with open(config_path, 'r') as config_file:
            config = json.load(config_file)
        logging.info("Configuration file loaded successfully.")
    except FileNotFoundError:
        logging.info(f"Configuration file not found at {config_path}")
        config = {}
    except json.JSONDecodeError:
        logging.error(f"Error decoding JSON from the configuration file at {config_path}")
        config = {}

    return config


def format_code(code: str, add_line_above, deliminators=('{', '}'), comment_marker=';;', ) -> str:

    open_delim = deliminators[0]
    closed_delim = deliminators[1]

    def bracket_count_difference(line: str):
        """Return the number of `(` minus the number of `)`, ignoring all characters after ';;'."""
        # Ignore characters after comment_marker
        comment_index = line.find(comment_marker)
        if comment_index != -1:
            line = line[:comment_index]
        return line.count(open_delim) - line.count(closed_delim)

    lines = code.split('\n')
    formatted_lines = []
    current_indent = 0

    for line in lines:
        stripped_line = line.lstrip()

        if not stripped_line:
            continue

        just_closed_bracket: bool = stripped_line[0] == closed_delim

        if just_closed_bracket:
            current_indent -= 1

        indented_line = '\t' * current_indent + stripped_line
        indented_line = indented_line.rstrip(' \t')

        if any(stripped_line.startswith(prefix) for prefix in add_line_above):
            indented_line = '\n' + indented_line

        formatted_lines.append(indented_line)

        current_indent += bracket_count_difference(stripped_line)

        if just_closed_bracket:
            current_indent += 1

    return '\n'.join(formatted_lines)


def generate_program(args, cfg, directions: list[int] = None):

    from programs.WASMProgram import WASMProgram
    from programs.GLSLProgram import GLSLProgram
    from programs.WGSLProgram import WGSLProgram
    from languages import WASMLang, WGSLLang, GLSLLang

    if isinstance(args.language, WASMLang):
        return WASMProgram(cfg, args.code_type, directions)
    elif isinstance(args.language, WGSLLang):
        return WGSLProgram(cfg, args.code_type, directions)
    elif isinstance(args.language, GLSLLang):
        return GLSLProgram(cfg, args.code_type, directions)
    else:
        raise ValueError("Unsupported language")


def save_program(program, file_path, opt_level: Optional[str] = None):
    """Save program of any supported language"""
    from languages import WASMLang, WGSLLang, GLSLLang

    language = program.get_language()

    if opt_level:
        assert isinstance(language, WASMLang)

    if isinstance(language, WASMLang):
        program.save(file_path, opt_level=opt_level)
    elif isinstance(language, WGSLLang):
        program.save(file_path)
    elif isinstance(language, GLSLLang):
        from programs.GLSLProgram import GLSLProgram
        program.save(file_path, GLSLProgram.OutputType.COMP_SHADER)
    else:
        raise ValueError("Unsupported language")
