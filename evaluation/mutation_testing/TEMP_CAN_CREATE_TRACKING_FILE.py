import os
import subprocess

# First, BUILD TINT WITH:
# cd /Users/maxmitchell/dawn_mutant_tracking/src/tint
# gn gen out/Default
# ninja -C out/Default

assert 'DAWN_VARIANT' in os.environ, "'DAWN_VARIANT' environment variable is not defined."
assert os.environ['DAWN_VARIANT'] in ['normal', 'mutant_tracking', 'meta_mutant']
assert 'DREDD_MUTANT_TRACKING_FILE' in os.environ

input_file = '/Users/maxmitchell/Documents/msc-control-flow-fleshing-project/evaluation/wgsl_test_suite/global_array/code/code_0.wgsl'
output_file = '/Users/maxmitchell/Documents/msc-control-flow-fleshing-project/evaluation/TEMP.metal'
tint = '/Users/maxmitchell/dawn_mutant_tracking/src/tint/out/Default/tint'

# Run example command
command = [
    tint,
    '--format', 'msl',
    '--output-name',
    output_file,
    input_file
]

result = subprocess.run(command, env=os.environ, capture_output=True, text=True)

# Step 5: Check the result of the command
if result.returncode != 0:
    print(f"Error: {result.stderr}")
else:
    print(f"Shader conversion successful. Output saved to {output_file}")
    print(result.stdout)