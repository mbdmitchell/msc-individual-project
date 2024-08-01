## Build instructions

- Clone repo
- `pip install .`
- If testing WGSL, build Dawn from source and run via Node. If testing GLSL, ensure you have a compatible GPU and build the ShaderTrap repository. Add the file paths to `config.json`
- If faced with `ModuleNotFound` error, `setenv PYTHONPATH /path/to/root/dir/of/repo` (`setenv` or equivalent)

## Examples

Once build, you can 

1. generate a set of tests with TestHarness.py

`python ./testing/TestHarness.py wgsl [no_of_graphs] [no_of_paths]`

2. test an individual program

`python ./testing/run_individual_test.py [program_filepath] [directions]`

e.g.
`python ./testing/run_individual_test.py path/to/pickled_program_class 1,2,3,0,0,0`
