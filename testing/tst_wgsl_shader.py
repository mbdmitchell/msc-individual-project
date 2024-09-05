import os
import sys
from pprint import pprint

from my_common import CodeType
from my_common.utils import parse_int_list
from WGSL.utils import tst_shader, classify_shader_code_type

import sys
import json


def read_json(json_path):
    """Read and return the contents of the JSON file."""
    with open(json_path, 'r') as file:
        data = json.load(file)
    return data


def main(json_path: str):

    env = os.environ.copy()

    data = read_json(json_path)

    wgsl_shader_filepath = data.get('wgsl_shader_path')
    expected_path: list[int] = parse_int_list(data.get('expected_path_str'))
    input_directions: list[int] = parse_int_list(data.get('input_directions_str'))

    is_match, msg = tst_shader(wgsl_shader_filepath, expected_path, env, input_directions)

    print(is_match, str(msg))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python tst_wgsl_shader.py path/to/config.json")
        sys.exit(1)

    _json_path = sys.argv[1]
    main(_json_path)

