**Process**: systematically add syntax errors into the mutated tint files and check for build errors to make sure they're being included in the final `dawn.node`. 

- Run part_1.sh
- Clear terminal (optional but makes it easier to Cntrl-F later)
- Run part_2.sh
- Add any file causing build errors and add to included_tint_files.txt
- Repeat until `dawn.node` builds, i.e., part_1 doesn't add a syntax error to any files included in the final `dawn.node`.

**Results**: All mutated tint files (excluding `*_test.cc` files) are included in the final `dawn.node`.