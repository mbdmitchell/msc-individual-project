
from CFG import CFG, GraphFormat, NodeType
from textwrap import dedent, indent

# TODO: decouple code formatting from code generation


class ProgramBuilder:

    is_built: bool = False
    code: str = ''

    def __init__(self, cfg: CFG = None, filename: str = None):
        """Construct WATProgramBuilder from CFG or file w/ serialised CFG"""

        if cfg and filename:
            raise ValueError("Can't include both CFG and filename parameters")
        if cfg is None and filename is None:
            self.cfg = CFG()
        elif filename:
            self.cfg = self.cfg = CFG().load(filename, GraphFormat.CFG)
        else:
            self.cfg = cfg

    # TODO: re-add ```-> 'ProgramBuilder'```
    def _start_of_program(self):
        """
        Adds the initial boilerplate and setup code for the WebAssembly Text (WAT) program.

        This includes memory import, memory allocation, global variable declaration,
        and function definitions necessary for the program's execution.
        """
        self.code += dedent('''\
            (module

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
                    (local $state i32)
                
                    (local.set $output_index (i32.const 0))
                    (local.set $control_index (i32.const 0))
                
                    (local.set $state (i32.const 1)) ;; set state to starting node
                
                    (block $to_end             
                        (loop $to_start
                
                            ;; IF STATE==0, break
                            (i32.eqz (local.get $state))  
                            (if (then (br $to_end)))
            ''')
        return self

    def _end_of_program(self):
        """
        Adds the closing structure for the WebAssembly Text (WAT) program.

        This includes closing the loop and block structures and finalizing the module.
        """
        self.code += dedent('''\n\n\
                        ) ;; $to_start
                    ) ;; $to_end
                )
            )
            ''')
        return self

    @staticmethod
    def _node_label(node: int) -> str:
        """Generates a label comment for a given node."""
        return '\n\n\t\t\t\t;; NODE %{id}'.format(id=node)

    def _start_of_node(self, node: int):
        """Starts the code block for a specific node in the WebAssembly Text (WAT) program."""
        self.code += self._node_label(node)
        self.code += dedent('''\n\t\
            (i32.eq (local.get $state)(i32.const {id}))
                (if (then
                    (call $store_in_output 
                        (local.get $output_index) 
                        (i32.const {id})
                    )
                    (local.set $output_index 
                        (call $inc (local.get $output_index))
                    )''').format(id=node)
        return self

    def _end_of_node(self):
        """Ends the code block for a node in the WebAssembly Text (WAT) program."""
        self.code += '''\n\t\t\t\t\t(br $to_start)\n'''
        self.code += '\t\t\t\t))'
        return self

    def _end_node_body(self):
        """Appends code to set the WAT program's $state to 0, signifying an end node."""
        self.code += '''\n\t\t\t\t\t(local.set $state (i32.const 0))'''
        return self

    def _unconditional_node_body(self, node: int):
        """Appends code to unconditionally set the state to the successor node."""
        if self.cfg.node_type(node) != NodeType.UNCONDITIONAL:
            raise ValueError('Expected different node type')
        opt = self.cfg.children(node)[0]
        self.code += '''\n\t\t\t\t\t(local.set $state (i32.const {id}))'''.format(id=opt)
        return self

    def _conditional_node_body(self, node: int):
        """Appends code to set the state to a successor node, depending on the WAT code's $control_val variable."""
        if self.cfg.node_type(node) != NodeType.CONDITIONAL:
            raise ValueError('Expected different node type')
        opt1, opt2 = self.cfg.children(node)[0], self.cfg.children(node)[1]
        self.code += '''
                    (local.set $control_val 
                        (call $calc_cntrl_val (local.get $control_index))
                    ) 
                    (local.set $control_index 
                        (call $inc (local.get $control_index))
                    )         

                    (i32.eqz (local.get $control_val))
                    (if 
                        (then (local.set $state (i32.const {op1}))) ;; FALSE BRANCH
                        (else (local.set $state (i32.const {op2}))) ;; TRUE BRANCH
                    )
                '''.format(op1=opt1, op2=opt2)
        return self

    def _switch_node_body(self, node: int):
        """Appends code to set the state to a successor node, depending on the WAT code's $control_val variable."""
        if self.cfg.node_type(node) != NodeType.SWITCH:
            raise ValueError('Expected different node type')
        self.code += indent(dedent('''
            (local.set $control_val 
                (call $calc_cntrl_val (local.get $control_index))
            ) 
            (local.set $control_index 
                (call $inc (local.get $control_index))
            )         
        '''), '\t\t\t\t\t')
        for index, node in enumerate(self.cfg.children(node)):
            self.code += indent(dedent('''
            (i32.eq (local.get $control_val) (i32.const {ix}))
            (if (then (local.set $state (i32.const {id}))))
        '''.format(ix=index, id=node)), '\t\t\t\t\t')
        return self

    def add_node(self, node: int, **attr):
        """Adds a node to the list of nodes."""
        self.cfg.add_node(node, **attr)
        return self

    def add_nodes(self, nodes: list[int], **attr):
        """Adds nodes to the list of nodes."""
        self.cfg.add_nodes(nodes, **attr)
        return self

    def _add_node_code(self, node: int, with_edge_aggregation: bool = False):
        """Adds the appropriate code for a node based on its type. Performs edge aggregation if requested."""

        def node_with_multiple_out_edges(node: int):
            return (self._start_of_node(node)
                    ._multi_outedge_node_body(node)
                    ._end_of_node())

        node_type: NodeType = self.cfg.node_type(node)

        if with_edge_aggregation:

            if node_type == NodeType.CONDITIONAL:
                return self._conditional_node(node)
            elif node_type == NodeType.SWITCH:
                return self._switch_node(node)
            elif node_type == NodeType.UNCONDITIONAL:
                return self._unconditional_node(node)
            elif node_type == NodeType.END:
                return self._end_node(node)
            else:
                raise ValueError('Unrecognised NodeType')

        else:

            out_edge_degree = self.cfg.out_degree(node)

            if out_edge_degree == 0:
                return self._end_node(node)
            elif out_edge_degree == 1:
                return self._unconditional_node(node)
            else:
                return node_with_multiple_out_edges(node)

    def _multi_outedge_node_body(self, node: int):
        """Appends code to set the state to a successor node, depending on the WAT code's $control_val variable."""
        if self.cfg.out_degree(node) < 2:
            raise ValueError("Invalid usage: called _multi_outedge_node_body for node with <2 out edges")
        self.code += '''
                    (local.set $control_val 
                        (call $calc_cntrl_val (local.get $control_index))
                    ) 
                    (local.set $control_index 
                        (call $inc (local.get $control_index))
                    )         
                    '''
        current_control_val = 0

        for edge in self.cfg.out_edges(node):
            _, dst = edge
            self.code += indent(dedent('''
                    (i32.eq (local.get $control_val) (i32.const {cv}))
                    (if (then (local.set $state (i32.const {id}))))
                '''.format(cv=current_control_val, id=dst)), '\t\t\t\t\t')
            current_control_val += 1

        return self

    def _unconditional_node(self, node: int):
        """Generates code for an unconditional node."""
        assert self.cfg.node_type(node) == NodeType.UNCONDITIONAL  # Redundant if coming from add_node_code(node)
        return (self._start_of_node(node)
                ._unconditional_node_body(node)
                ._end_of_node())

    def _conditional_node(self, node: int):
        """Generates code for a conditional node."""
        assert self.cfg.node_type(node) == NodeType.CONDITIONAL  # Redundant if coming from add_node_code(node)
        return (self._start_of_node(node)
                ._conditional_node_body(node)
                ._end_of_node())

    def _switch_node(self, node: int):  # Redundant if coming from add_node_code(node)
        """Generates code for a switch node."""
        assert self.cfg.node_type(node) == NodeType.SWITCH
        return (self._start_of_node(node)
                ._switch_node_body(node)
                ._end_of_node())

    def _end_node(self, node: int):
        """Generates code for an end node."""
        assert self.cfg.node_type(node) == NodeType.END  # Redundant if coming from add_node_code(node)
        return (self._start_of_node(node)
                ._end_node_body()
                ._end_of_node())

    def _validate(self):
        """Validates that the nodes will result in a valid generated program."""

        all_successors = {child for node in self.cfg.nodes() for child in self.cfg.children(node)}

        unknown_node: bool = any(s not in self.cfg.nodes() for s in all_successors)
        uses_node_id_corresponding_to_wat_exit_state: bool = any(s == 0 for s in self.cfg.nodes())
        has_starting_node: bool = any(s == 1 for s in self.cfg.nodes())

        if unknown_node:  # TODO: check if handled by nx.MultiDiGraph (underlying graph type in CFG) already
            raise Exception('One or more successors do not correspond to an existing node')
        if uses_node_id_corresponding_to_wat_exit_state:
            raise Exception('uses_node_id_corresponding_to_wat_exit_state')
        if not has_starting_node:
            raise Exception('No node with id "n1" (default starting node id)')

    def build(self, with_edge_aggregation: bool = False):
        """Builds the WebAssembly Text (WAT) program."""
        from .Program import Program  # Deferred import to avoid circular dependency

        self._validate()

        # BUILD
        self._start_of_program()
        for node in self.cfg.nodes():
            self._add_node_code(node, with_edge_aggregation)
        self._end_of_program()

        self.is_built = True

        return Program(self)
