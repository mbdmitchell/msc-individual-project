## Build instructions

- Clone repo
- `pip install .`
- If testing WGSL, build Dawn from source and run via Node. If testing GLSL, ensure you have a compatible GPU and build the ShaderTrap repository. Add the file paths to `config.json`
- If faced with `ModuleNotFound` error, `setenv PYTHONPATH /path/to/root/dir/of/repo` (`setenv` or equivalent)