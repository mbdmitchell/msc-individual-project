import logging

from CFG import *
from CFG.CFGGenerator import GeneratorConfig
from GLSL import GLSLProgram
from WASM import WASMProgram
from WGSL import WGSLProgram
from languages import GLSLLang, WGSLLang
from my_common import CodeType

# logging.basicConfig(level=logging.DEBUG)

random.seed(1)

language = GLSLLang()
cfg = cfg_while_3_nested()
directions = [1,1,1,0,1,1,0,0,1,1,0,0,1,1,0,0,0]

print(cfg.expected_output_path(directions))
program = GLSLProgram(cfg=cfg, code_type=CodeType.STATIC, directions=directions)

print(program.generate_shader_test(input_directions=directions,
                                   expected_path=program.cfg.expected_output_path(directions)))

# print(program.get_code())