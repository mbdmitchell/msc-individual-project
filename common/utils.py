from __future__ import annotations

import json
import logging
import os
from typing import Optional
from common import Language

def load_config():

    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, '..', 'config.json')

    # Load the configuration data from config.json
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


def generate_program(language, cfg):
    from WASM.WASMProgram import WASMProgram
    from GLSL.GLSLProgram import GLSLProgram
    from WGSL.WGSLProgram import WGSLProgram
    if language == Language.WASM:
        return WASMProgram(cfg)
    elif language == Language.WGSL:
        return WGSLProgram(cfg)
    elif language == Language.GLSL:
        return GLSLProgram(cfg)
    else:
        raise ValueError("Unsupported language")


def save_program(program, file_path, opt_level: Optional[str] = None):
    """Save program of any supported language"""

    if opt_level:
        assert program.get_language() == Language.WASM

    language = program.get_language()
    if language == Language.WASM:
        program.save(file_path, opt_level=opt_level)
    elif language == Language.WGSL:
        program.save(file_path)
    elif language == Language.GLSL:
        from GLSL.GLSLProgram import GLSLProgram
        program.save(file_path, GLSLProgram.OutputType.COMP_SHADER)
    else:
        raise ValueError("Unsupported language")