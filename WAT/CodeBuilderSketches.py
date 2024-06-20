from pprint import pprint

import networkx as nx

from CFG import CFG, example_cfg_nested_switches, example_cfg_if_else, CFGFormat
from CodeFormatter import format_code


def full_program(control_flow_code: str):
    return"""(module
    
        (import "js" "memory" (memory 0))
    
        (memory $outputMemory 1)
        (export "outputMemory" (memory $outputMemory))
    
        (global $elem_size i32 (i32.const 4))
    
        (func $byte_offset (param $index i32) (result i32)
                (i32.mul (local.get $index) (global.get $elem_size))
        )
        (func $inc (param $num i32) (result i32)
                (i32.add (local.get $num) (i32.const 1))
        )
        (func $calc_cntrl_val (param $index i32) (result i32)
            (i32.load 
                (memory 0)
                (call $byte_offset(local.get $index))
            )
        )
        (func $store_in_output (param $index i32) (param $value i32)
            (i32.store 
                (memory $outputMemory)
                (call $byte_offset (local.get $index))
                (local.get $value)
            )
        )
    
        (func $cf (export "cf")
    
            ;; setup
    
            (local $output_index i32)
            (local $control_index i32)
            (local $control_val i32)
            (local.set $output_index (i32.const 0))
            (local.set $control_index (i32.const 0))
            (local.set $control_val (call $calc_cntrl_val (local.get $control_index)))
            
            ;; control flow code
            
            {control_flow_code}
            
         )
    )
    """.format(control_flow_code=control_flow_code)

def visit_block(n: int):
    return """
    ;; NODE {n}
    (call $store_in_output
        (local.get $output_index)
        (i32.const {n})
    )
    (local.set $output_index
        (call $inc (local.get $output_index))
    )
    """.format(n=n)


def _set_control_value():
    return """
    (local.set $control_val 
        (call $calc_cntrl_val (local.get $control_index))
    )         
    """

def _increment_control_index():
    return """
    (local.set $control_index 
        (call $inc (local.get $control_index))
    )         
    """


def set_and_handle_control():
    return _set_control_value() + _increment_control_index()

def out_edges_destinations(cfg, block) -> list[int]:
    return [e[1] for e in cfg.out_edges(block)]

def block_code(cfg: CFG, block: int, switch_label_num: int = 0) -> str:
    """Add block and all nested blocks within it"""

    def is_basic_block() -> bool:
        return cfg.out_degree(block) == 1

    def is_exit_block(blk) -> bool:
        return cfg.out_degree(blk) == 0

    # HEADERS

    def is_header() -> bool:
        return cfg.out_degree(block) > 1

    def is_selection_header() -> bool:
        return cfg.out_degree(block) == 2

    def is_switch_header() -> bool:
        # TODO: switch block doesn't have to have out degree > 2
        return cfg.out_degree(block) > 2

    def selection_code() -> str:
        destinations = out_edges_destinations(cfg, block)
        # TODO: selection_header doesn't always have two different dst
        return set_and_handle_control() + """
            (if (i32.eqz (local.get $control_val))
                (then
                    {false_block}
                )
                (else
                    {true_block}
                )
            )
            """.format(false_block=block_code(cfg, destinations[0], switch_label_num),
                       true_block=block_code(cfg, destinations[1], switch_label_num))

    def switch_code() -> str:
        """switch_block_label: unique label for outermost block in switch"""
        # TODO: switch block doesn't have to have out degree > 2
        # TODO: handle fall through

        switch_label: str = "$switch{current_switch_label_num}".format(current_switch_label_num=switch_label_num)
        next_num = switch_label_num + 1

        def build_br_table(cases_: list[int]) -> str:

            num_of_cases = len(cases_)

            def case_line(case: int):
                return f'{case}\t ;; case == {case} => (br {case})\n'

            def default_line():
                br_index = num_of_cases
                return f'{br_index}\t ;; default => (br {br_index})\n'

            br_table = ""
            for c in range(num_of_cases):
                br_table += case_line(c)

            br_table += default_line()

            return br_table

        def build_switch_break(target: int):
            if is_exit_block(target):
                return ""
            else:
                return "(br {switch_label})".format(switch_label=switch_label)

        destinations = out_edges_destinations(cfg, block)
        default, cases = destinations[-1], destinations[:-1]  # default = last dst, cases = the rest

        inner_block = """
            (block (local.get $control_val)
                (br_table
                    {br_table}
                )
                ;; guard from UB
                (call $store_in_output (local.get $output_index)(i32.const -1))
                (local.set $output_index (call $inc (local.get $output_index)))
                (br {label})
            )""".format(br_table=build_br_table(cases),
                        label=switch_label)

        code = inner_block

        # wrap block
        for ix in range(len(cases)):
            code = """
            (block
                {code}
                ;; Target for (br {ix})
                {target_code}
                {switch_break}
            )
            """.format(ix=ix,
                       code=code,
                       target_code=block_code(cfg, cases[ix], next_num),
                       switch_break=build_switch_break(cases[ix]))

        # wrap default
        code = """
        (local.set $control_index 
		    (call $inc (local.get $control_index))
		)      
        (block {switch_block_label}
            {code}
            ;; Target for (br {ix}) => default
            {target_code}
        )
        """.format(ix=len(cases),
                   code=code,
                   target_code=block_code(cfg, default, next_num),
                   switch_block_label=switch_label)

        return code

    # ... code

    bc = visit_block(block)

    if is_exit_block(block):
        bc += "\n(return)"
    elif is_basic_block():
        bc += block_code(cfg, out_edges_destinations(cfg, block)[0], switch_label_num)
    elif is_header():

        # find merge point

        if is_switch_header():
            bc += switch_code()
        elif is_selection_header():
            """
            if is_loop_header():
                ...
            else:
                bc += selection_code()
            """
            bc += selection_code()

        # bc += block_code(merge_point)

        #elif _is_loop_header(block):


    return bc


def calc_control_flow_code(cfg):
    """So, this works great if all blocks have in degree of 1, else we'll have node duplication"""
    return block_code(cfg, cfg.entry_node())

# WORKING: cfg = alloy_to_cfg('../alloy-cfgs/ex1.xml')

def generate_multi_di_graph_from_edges(edges) -> nx.MultiDiGraph:
    """
    Parameters
        edges : container of edges
            Each edge given in the container will be added to the
            graph. The edges must be given as 2-tuples (u, v) or
            3-tuples (u, v, d) where d is a dictionary containing edge data.
    """
    g = nx.MultiDiGraph()
    g.add_edges_from(edges)
    return g

def main():
    cfg = example_cfg_nested_switches()
    print(format_code(full_program(calc_control_flow_code(cfg))))

if __name__ == "__main__":
    main()
