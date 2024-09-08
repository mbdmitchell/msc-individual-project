def parse_file(filename: str) -> list[int]:
    with open(filename, 'r') as file:
        integer_set = set(int(line.strip()) for line in file)
    return list(sorted(integer_set))


def main():

    dawn_test_visitable_mutants_filepath = '/Users/maxmitchell/Documents/msc-control-flow-fleshing-project/evaluation/mutation_testing/visitable-mutants-tint-end-to-end-tests.txt'
    dawn_test_visitable_mutants = set(parse_file(dawn_test_visitable_mutants_filepath))

    control_flow_fleshing_visitable_mutants_filepath = '/evaluation/mutation_testing/visitable-mutants-cff-suite.txt'
    control_flow_fleshing_visitable_mutants = set(parse_file(control_flow_fleshing_visitable_mutants_filepath))

    distinct_cff_mutants = control_flow_fleshing_visitable_mutants - dawn_test_visitable_mutants
    distinct_dawn_mutants = dawn_test_visitable_mutants - control_flow_fleshing_visitable_mutants

    print(f"dawn_test_visitable_mutants[{len(dawn_test_visitable_mutants)}]: {dawn_test_visitable_mutants}", )
    print(f"control_flow_fleshing_visitable_mutants[{len(control_flow_fleshing_visitable_mutants)}]: {control_flow_fleshing_visitable_mutants}", )
    print(f"distinct_cff_mutants[{len(distinct_cff_mutants)}]: {distinct_cff_mutants}")
    print(f"distinct_dawn_mutants[{len(distinct_dawn_mutants)}]: {distinct_dawn_mutants}")


if __name__ == '__main__':
    main()
