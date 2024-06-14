from pprint import pprint

from CFG import CFG, alloy_to_cfg

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


def construct_switch_code(block):
    pass


def block_code(block: int) -> str:
    """Add block and all nested blocks within it"""

    bc = visit_block(block)

    if cfg.is_exit_block(block):
        print(block, ": is_exit_block")
        bc += "\nreturn"
    elif cfg.is_header_block(block):
        if cfg.is_switch_header(block):
            bc += construct_switch_code(block)
            print(block, ": is_switch_header")
        elif cfg.is_selection_header(block):
            bc += set_and_handle_control()
            print(block, ": is_selection_header")

            destinations = out_edges_destinations(cfg, block)

            bc += """
            (if (i32.eqz (local.get $control_val))
                (then
                    {false_block}
                )
                (else
                    {true_block}
                )
            )
            """.format(false_block=block_code(destinations[0]),
                       true_block=block_code(destinations[1]))
    elif cfg.is_basic_block(block):
        print(block, ": is_basic_block")
        bc += block_code(out_edges_destinations(cfg, block)[0])

    return bc


def calc_control_flow_code(cfg):
    # TODO: what's up with merges though??
    # TODO: Handle unreachable (but still structurally reachable) code blocks
    return block_code(cfg.entry_node())

# WORKING: cfg = alloy_to_cfg('../alloy-cfgs/ex1.xml')
cfg = alloy_to_cfg('../alloy-cfgs/ex2.xml', convert_to_wasm_friendly_cfg=True)


for n in cfg.nodes(data=True):
    pprint(n)




# calc_control_flow_code(cfg)

# print(full_program(calc_control_flow_code(cfg)))