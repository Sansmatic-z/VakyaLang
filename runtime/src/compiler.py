# वाक् भाषा - संकलक (Compiler)
# Vak Language - AST to Bytecode Compiler

from typing import Any
from .bytecode import Bytecode
from .opcodes import OpCode
from .ast_nodes import *


class Compiler:
    """
    Compiles VakyaLang AST into bytecode.

    Single-pass compiler with jump patching.
    Maintains variable scope and constant pool.
    
    Compilation phases:
    1. Macro Expansion (सूत्र विस्तार) - Expand compile-time macros
    2. Bytecode Generation - Convert AST to bytecode
    """

    def __init__(self):
        self.bytecode = Bytecode()
        self.loop_stack = []  # For break/continue

    def compile(self, node: Node) -> Bytecode:
        """
        Compile AST node to bytecode.
        
        Phases:
        1. MACRO EXPANSION: Expand all सूत्र (macros) before bytecode generation
        2. BYTECODE GENERATION: Convert expanded AST to bytecode
        """
        import math

        # ─────────────────────────────────────────────────────────────────────
        # PHASE 1: MACRO EXPANSION (सूत्र विस्तार)
        # ─────────────────────────────────────────────────────────────────────
        # Expand all macros BEFORE bytecode generation
        # This is compile-time transformation - no runtime overhead
        if isinstance(node, Program):
            from .macro_expander import MacroExpander
            expander = MacroExpander()
            node = expander.expand(node)

        # ─────────────────────────────────────────────────────────────────────
        # PHASE 2: BYTECODE GENERATION
        # ─────────────────────────────────────────────────────────────────────
        
        # Inject PI constant
        pi_idx = self.bytecode.add_constant(math.pi)
        self.bytecode.emit_16bit(OpCode.LOAD_CONST, pi_idx)
        pi_slot = self.bytecode.get_var_slot('पाई')
        self.bytecode.emit(OpCode.STORE_VAR, pi_slot)

        self._compile_node(node)
        self.bytecode.emit(OpCode.HALT)
        return self.bytecode

    def _compile_node(self, node: Node):
        """Dispatch to appropriate compile method."""
        method_name = f'_compile_{type(node).__name__}'
        method = getattr(self, method_name, self._compile_generic)
        method(node)

    def _compile_generic(self, node: Node):
        """Fallback for unhandled nodes."""
        raise CompileError(f"Cannot compile {type(node).__name__}", node.line)

    def _compile_Program(self, node: Program):
        for stmt in node.body:
            self._compile_node(stmt)

    def _compile_VarDecl(self, node: VarDecl):
        if node.value:
            self._compile_node(node.value)
        else:
            self.bytecode.emit_16bit(OpCode.LOAD_CONST, self.bytecode.add_constant(None))

        if len(node.names) == 1:
            slot = self.bytecode.get_var_slot(node.names[0])
            self.bytecode.emit(OpCode.STORE_VAR, slot)
        else:
            self.bytecode.emit(OpCode.UNPACK_SEQUENCE, len(node.names))
            for name in node.names:
                slot = self.bytecode.get_var_slot(name)
                self.bytecode.emit(OpCode.STORE_VAR, slot)

    def _compile_ConstDecl(self, node: ConstDecl):
        self._compile_node(node.value)
        slot = self.bytecode.get_var_slot(node.name)
        self.bytecode.emit(OpCode.STORE_VAR, slot)

    def _compile_GlobalStmt(self, node: GlobalStmt):
        for name in node.names:
            self.bytecode.global_names.add(name)
            # Ensure it has a slot so STORE_VAR/LOAD_VAR work
            self.bytecode.get_var_slot(name)

    def _compile_NonlocalStmt(self, node: NonlocalStmt):
        # For now, treat nonlocal as global or just record it
        # True nonlocal requires upvalue tracking
        pass

    def _compile_FuncDecl(self, node: FuncDecl):
        # Create separate bytecode for function
        func_compiler = Compiler()
        func_compiler.bytecode.name = node.name
        func_compiler.bytecode.is_async = node.is_async  # Mark as async coroutine

        # Add parameters as local variables
        for param_pair in node.params:
            p_name = param_pair[0] if isinstance(param_pair, tuple) else param_pair
            p_type = param_pair[1] if isinstance(param_pair, tuple) else None
            func_compiler.bytecode.get_var_slot(p_name)
            if p_type:
                func_compiler.bytecode.type_hints[p_name] = p_type
        func_compiler.bytecode.num_params = len(node.params)

        # Handle variadic argument
        if node.varargs:
            func_compiler.bytecode.varargs_name = node.varargs
            func_compiler.bytecode.get_var_slot(node.varargs)

        # Handle default values
        # We need to evaluate defaults in the CURRENT scope
        # For simplicity, we currently only support constant defaults in this implementation
        # A full implementation would compile the default expressions and evaluate them at func-definition time
        for default_node in node.defaults:
            if default_node is None:
                func_compiler.bytecode.defaults.append(None)
            elif isinstance(default_node, (NumberLiteral, StringLiteral, BoolLiteral, NullLiteral)):
                func_compiler.bytecode.defaults.append(getattr(default_node, 'value', None))
            else:
                # For complex expressions, we might need a mini-evaluation
                # For now, let's just mark them as unsupported or try a simple eval
                func_compiler.bytecode.defaults.append(None)

        # Compile function body
        func_compiler._compile_node(node.body)

        # Ensure function returns
        if not func_compiler.bytecode.code or func_compiler.bytecode.code[-1] != OpCode.RETURN.value:
            func_compiler.bytecode.emit_16bit(OpCode.LOAD_CONST, func_compiler.bytecode.add_constant(None))
            func_compiler.bytecode.emit(OpCode.RETURN)

        # Store function bytecode and flatten inner functions
        self.bytecode.functions[node.name] = func_compiler.bytecode
        self.bytecode.functions.update(func_compiler.bytecode.functions)

        # Load function reference with environment capture
        # We pass the current list of variables as the initial environment
        # The VM will resolve these names at call-time or creation-time
        env = {name: None for name in self.bytecode.var_names}
        
        # Mark function as coroutine if async
        if node.is_async:
            idx = self.bytecode.add_constant(('coroutine', node.name, env))
        else:
            idx = self.bytecode.add_constant(('function', node.name, env))
        
        self.bytecode.emit_16bit(OpCode.LOAD_CONST, idx)
        slot = self.bytecode.get_var_slot(node.name)
        self.bytecode.emit(OpCode.STORE_VAR, slot)

    def _compile_LambdaExpr(self, node: LambdaExpr):
        # Generate a unique name for the lambda
        lambda_name = f"<lambda_{id(node)}>"

        func_compiler = Compiler()
        func_compiler.bytecode.name = lambda_name

        # Add parameters
        for param_pair in node.params:
            p_name = param_pair[0] if isinstance(param_pair, tuple) else param_pair
            p_type = param_pair[1] if isinstance(param_pair, tuple) else None
            func_compiler.bytecode.get_var_slot(p_name)
            if p_type:
                func_compiler.bytecode.type_hints[p_name] = p_type
        func_compiler.bytecode.num_params = len(node.params)

        # Handle variadic argument
        if node.varargs:
            func_compiler.bytecode.varargs_name = node.varargs
            func_compiler.bytecode.get_var_slot(node.varargs)

        # Compile body (which is a Block containing a ReturnStmt)
        func_compiler._compile_node(node.body)

        # Ensure return
        if not func_compiler.bytecode.code or func_compiler.bytecode.code[-1] != OpCode.RETURN.value:
            func_compiler.bytecode.emit_16bit(OpCode.LOAD_CONST, func_compiler.bytecode.add_constant(None))
            func_compiler.bytecode.emit(OpCode.RETURN)

        # Store in parent
        self.bytecode.functions[lambda_name] = func_compiler.bytecode
        self.bytecode.functions.update(func_compiler.bytecode.functions)

        # Push function tuple to stack with environment capture
        env = {name: None for name in self.bytecode.var_names}
        idx = self.bytecode.add_constant(('function', lambda_name, env))
        self.bytecode.emit_16bit(OpCode.LOAD_CONST, idx)

    def _compile_ReturnStmt(self, node: ReturnStmt):
        if node.value:
            self._compile_node(node.value)
            self.bytecode.emit(OpCode.RETURN)
        else:
            self.bytecode.emit(OpCode.RETURN_VOID)

    def _compile_PrintStmt(self, node: PrintStmt):
        for i, val in enumerate(node.values):
            if i > 0:
                # Load space separator
                idx = self.bytecode.add_constant(' ')
                self.bytecode.emit_16bit(OpCode.LOAD_CONST, idx)
                self.bytecode.emit(OpCode.PRINT)
            self._compile_node(val)
            self.bytecode.emit(OpCode.PRINT)
        # Print newline
        idx = self.bytecode.add_constant('\n')
        self.bytecode.emit_16bit(OpCode.LOAD_CONST, idx)
        self.bytecode.emit(OpCode.PRINT)

    def _compile_IfStmt(self, node: IfStmt):
        # Compile condition
        self._compile_node(node.condition)

        # Jump to else if false
        jump_else = self.bytecode.get_current_offset()
        self.bytecode.emit_16bit(OpCode.JUMP_IF_FALSE, 0)  # Placeholder

        # Compile then block
        self._compile_node(node.then_body)

        # Jump over else
        jump_end = self.bytecode.get_current_offset()
        self.bytecode.emit_16bit(OpCode.JUMP, 0)  # Placeholder

        # Patch else jump
        else_offset = self.bytecode.get_current_offset()
        self.bytecode.patch_jump(jump_else + 1, else_offset)

        # Compile elif clauses
        for elif_cond, elif_body in node.elif_clauses:
            self._compile_node(elif_cond)
            jump_next = self.bytecode.get_current_offset()
            self.bytecode.emit_16bit(OpCode.JUMP_IF_FALSE, 0)
            self._compile_node(elif_body)
            jump_end_elif = self.bytecode.get_current_offset()
            self.bytecode.emit_16bit(OpCode.JUMP, 0)
            # Patch to next elif
            next_offset = self.bytecode.get_current_offset()
            self.bytecode.patch_jump(jump_next + 1, next_offset)
            jump_end = jump_end_elif

        # Compile else block
        if node.else_body:
            self._compile_node(node.else_body)

        # Patch end jump
        end_offset = self.bytecode.get_current_offset()
        self.bytecode.patch_jump(jump_end + 1, end_offset)

    def _compile_WhileStmt(self, node: WhileStmt):
        loop_start = self.bytecode.get_current_offset()

        # Compile condition
        self._compile_node(node.condition)

        # Jump to end if false
        jump_end = self.bytecode.get_current_offset()
        self.bytecode.emit_16bit(OpCode.JUMP_IF_FALSE, 0)

        # Track loop for break/continue
        self.loop_stack.append((loop_start, jump_end))

        # Compile body
        self._compile_node(node.body)

        self.loop_stack.pop()

        # Jump back to start
        current_pos = self.bytecode.get_current_offset()
        self.bytecode.emit_16bit(OpCode.JUMP, loop_start - (current_pos + 3))

        # Patch end jump
        end_offset = self.bytecode.get_current_offset()
        self.bytecode.patch_jump(jump_end + 1, end_offset)

    def _compile_ForStmt(self, node: ForStmt):
        # 1. Compile iterable and get iterator
        self._compile_node(node.iterable)
        self.bytecode.emit(OpCode.GET_ITER)

        loop_start = self.bytecode.get_current_offset()

        # 2. Iteration step
        jump_end = self.bytecode.get_current_offset()
        self.bytecode.emit_16bit(OpCode.FOR_ITER, 0) # Placeholder

        # 3. Store current item in the loop variable
        var_slot = self.bytecode.get_var_slot(node.var_name)
        self.bytecode.emit(OpCode.STORE_VAR, var_slot)

        # 4. Compile body
        self.loop_stack.append((loop_start, jump_end))
        self._compile_node(node.body)
        self.loop_stack.pop()

        # 5. Loop back
        # The jump back is from the current position to the start of FOR_ITER
        # vm.py: pc += 3 + offset
        current_pos = self.bytecode.get_current_offset()
        back_jump_dist = loop_start - (current_pos + 3)
        self.bytecode.emit_16bit(OpCode.JUMP, back_jump_dist)

        # 6. Patch the FOR_ITER exit jump
        # This will jump past the back-jump instruction
        loop_end = self.bytecode.get_current_offset()
        self.bytecode.patch_jump(jump_end + 1, loop_end)

    def _compile_BreakStmt(self, node: BreakStmt):
        if not self.loop_stack:
            raise CompileError("विराम (break) outside loop", node.line)
        _, jump_end = self.loop_stack[-1]
        self.bytecode.emit_16bit(OpCode.JUMP, 0)  # Will be patched

    def _compile_ContinueStmt(self, node: ContinueStmt):
        if not self.loop_stack:
            raise CompileError("अग्रे (continue) outside loop", node.line)
        loop_start, _ = self.loop_stack[-1]
        self.bytecode.emit_16bit(OpCode.JUMP, loop_start - self.bytecode.get_current_offset())

    def _compile_ClassDecl(self, node: ClassDecl):
        # We need to compile the class body into a dictionary of methods/attributes
        class_compiler = Compiler()
        class_compiler.bytecode.name = f"<class {node.name}>"

        # Compile methods inside the class body
        if hasattr(node.body, 'stmts'):
            for stmt in node.body.stmts:
                class_compiler._compile_node(stmt)

        # Ensure it returns
        class_compiler.bytecode.emit(OpCode.RETURN_VOID)

        # Store class initialization bytecode
        self.bytecode.functions[node.name] = class_compiler.bytecode

        # Push parent class if any, else None
        if hasattr(node, 'superclass') and node.superclass:
            if isinstance(node.superclass, IdentifierExpr):
                slot = self.bytecode.get_var_slot(node.superclass.name)
                self.bytecode.emit(OpCode.LOAD_VAR, slot)
            else:
                self._compile_node(node.superclass)
        else:
            idx = self.bytecode.add_constant(None)
            self.bytecode.emit_16bit(OpCode.LOAD_CONST, idx)

        # Push class name
        idx = self.bytecode.add_constant(node.name)
        self.bytecode.emit_16bit(OpCode.LOAD_CONST, idx)

        # Emit BUILD_CLASS
        self.bytecode.emit(OpCode.BUILD_CLASS)

        slot = self.bytecode.get_var_slot(node.name)
        self.bytecode.emit(OpCode.STORE_VAR, slot)

    def _compile_TryStmt(self, node: TryStmt):
        # Setup exception handler jump
        jump_catch = self.bytecode.get_current_offset()
        self.bytecode.emit_16bit(OpCode.SETUP_EXCEPT, 0) # Placeholder for catch block

        # Compile try block
        self._compile_node(node.try_body)

        # Pop exception handler if try succeeded
        self.bytecode.emit(OpCode.POP_EXCEPT)

        # Jump over catch block
        jump_end = self.bytecode.get_current_offset()
        self.bytecode.emit_16bit(OpCode.JUMP, 0)

        # Patch exception jump to here (Start of catch block)
        catch_offset = self.bytecode.get_current_offset()
        self.bytecode.patch_jump(jump_catch + 1, catch_offset)

        if node.catch_body:
            if node.catch_var:
                # The exception object is pushed to stack by the VM
                slot = self.bytecode.get_var_slot(node.catch_var)
                self.bytecode.emit(OpCode.STORE_VAR, slot)
            else:
                self.bytecode.emit(OpCode.POP) # Discard exception object
            self._compile_node(node.catch_body)

        # Patch end jump to here (After catch block)
        end_offset = self.bytecode.get_current_offset()
        self.bytecode.patch_jump(jump_end + 1, end_offset)

        if node.finally_body:
            self._compile_node(node.finally_body)

    def _compile_WithStmt(self, node: WithStmt):
        # Evaluate context manager
        self._compile_node(node.expr)

        # Store in hidden local for cleanup
        hidden_name = f"<ctx_{id(node)}>"
        slot = self.bytecode.get_var_slot(hidden_name)
        self.bytecode.emit(OpCode.DUP)
        self.bytecode.emit(OpCode.STORE_VAR, slot)

        # Store in user variable if provided
        if node.var_name:
            # We don't need DUP here because we already have one on stack
            # Wait, STORE_VAR pops. So we need another DUP if we want to store in TWO places.
            self.bytecode.emit(OpCode.DUP)
            user_slot = self.bytecode.get_var_slot(node.var_name)
            self.bytecode.emit(OpCode.STORE_VAR, user_slot)

        # Body doesn't need the object on the evaluation stack
        self.bytecode.emit(OpCode.POP)

        # Execute body
        self._compile_node(node.body)

        # Load for cleanup
        self.bytecode.emit(OpCode.LOAD_VAR, slot)
        self.bytecode.emit(OpCode.WITH_CLEANUP)

    def _compile_ThrowStmt(self, node: ThrowStmt):
        self._compile_node(node.value)
        self.bytecode.emit(OpCode.THROW)

    def _compile_ImportStmt(self, node: ImportStmt):
        idx = self.bytecode.add_constant(node.module)
        self.bytecode.emit_16bit(OpCode.IMPORT_NAME, idx)

        if node.names:
            # We would extract specific names from the imported module here
            pass
        else:
            # Store module object in local variable
            slot = self.bytecode.get_var_slot(node.module)
            self.bytecode.emit(OpCode.STORE_VAR, slot)
            
    def _compile_Block(self, node: Block):
        for stmt in node.stmts:
            self._compile_node(stmt)

    def _compile_ExprStmt(self, node: ExprStmt):
        self._compile_node(node.expr)
        self.bytecode.emit(OpCode.POP)  # Discard result

    def _compile_BinaryExpr(self, node: BinaryExpr):
        self._compile_node(node.left)
        self._compile_node(node.right)

        op_map = {
            '+': OpCode.ADD,
            '-': OpCode.SUB,
            '*': OpCode.MUL,
            '/': OpCode.DIV,
            '//': OpCode.IDIV,  # Integer division
            '%': OpCode.MOD,
            '**': OpCode.POW,
            '&': OpCode.BAND,
            '|': OpCode.BOR,
            '^': OpCode.BXOR,
            '<<': OpCode.LSHIFT,
            '>>': OpCode.RSHIFT,
            '==': OpCode.EQ,
            '!=': OpCode.NEQ,
            '<': OpCode.LT,
            '>': OpCode.GT,
            '<=': OpCode.LTE,
            '>=': OpCode.GTE,
            'और': OpCode.AND,
            'अथवा': OpCode.OR,
            'अन्तर्गत': OpCode.CALL_BUILTIN,  # Membership test
        }

        if node.op in op_map:
            self.bytecode.emit(op_map[node.op])
        else:
            raise CompileError(f"Unknown operator: {node.op}", node.line)

    def _compile_UnaryExpr(self, node: UnaryExpr):
        self._compile_node(node.operand)

        if node.op == '-':
            self.bytecode.emit(OpCode.NEG)
        elif node.op == 'न':
            self.bytecode.emit(OpCode.NOT)
        elif node.op == '~':
            self.bytecode.emit(OpCode.BNOT)
        else:
            raise CompileError(f"Unknown unary operator: {node.op}", node.line)
            
    def _compile_AssignExpr(self, node: AssignExpr):
        # Determine value to store
        if node.op == '=':
            self._compile_node(node.value)
        else:
            # Compound assignment (+=, -=, etc.)
            # First load the current value
            if isinstance(node.target, IdentifierExpr):
                slot = self.bytecode.get_var_slot(node.target.name)
                self.bytecode.emit(OpCode.LOAD_VAR, slot)
            elif isinstance(node.target, IndexExpr):
                self._compile_node(node.target.obj)
                self._compile_node(node.target.index)
                self.bytecode.emit(OpCode.INDEX_GET)
            elif isinstance(node.target, MemberExpr):
                self._compile_node(node.target.obj)
                idx = self.bytecode.add_constant(node.target.attr)
                self.bytecode.emit_16bit(OpCode.ATTR_GET, idx)

            # Compile right side value
            self._compile_node(node.value)

            # Apply operator
            op_map = {'+=': OpCode.ADD, '-=': OpCode.SUB, '*=': OpCode.MUL, '/=': OpCode.DIV, '%=': OpCode.MOD, ':=': None}
            if node.op in op_map:
                if op_map[node.op]:
                    self.bytecode.emit(op_map[node.op])
            else:
                raise CompileError(f"Unknown assignment operator: {node.op}", node.line)

        # Store the computed value
        if isinstance(node.target, IdentifierExpr):
            slot = self.bytecode.get_var_slot(node.target.name)
            self.bytecode.emit(OpCode.STORE_VAR, slot)
            self.bytecode.emit(OpCode.LOAD_VAR, slot)  # Assignment returns value
        elif isinstance(node.target, IndexExpr):
            # Target stack needs to be: obj, index, value
            # But value is currently on top.
            # We need to temporarily pop value, push obj, push index, push value

            # Since our ISA doesn't have deep stack manipulation, we can use a temp variable
            temp_val_slot = self.bytecode.get_var_slot("__temp_assign_val")
            self.bytecode.emit(OpCode.STORE_VAR, temp_val_slot)

            self._compile_node(node.target.obj)
            self._compile_node(node.target.index)
            self.bytecode.emit(OpCode.LOAD_VAR, temp_val_slot)

            self.bytecode.emit(OpCode.INDEX_SET)
            self.bytecode.emit(OpCode.LOAD_VAR, temp_val_slot) # Return value
        elif isinstance(node.target, MemberExpr):
            temp_val_slot = self.bytecode.get_var_slot("__temp_assign_val")
            self.bytecode.emit(OpCode.STORE_VAR, temp_val_slot)

            self._compile_node(node.target.obj)
            self.bytecode.emit(OpCode.LOAD_VAR, temp_val_slot)

            idx = self.bytecode.add_constant(node.target.attr)
            self.bytecode.emit_16bit(OpCode.ATTR_SET, idx)

            self.bytecode.emit(OpCode.LOAD_VAR, temp_val_slot) # Return value
        else:
            raise CompileError("Invalid assignment target", node.line)

    def _compile_CallExpr(self, node: CallExpr):
        # Check if it's a builtin call
        builtins_list = [
            'पाठ_कर', 'str', 'परास', 'range', 'दीर्घता', 'len', 'प्रकार', 'type',
            'संख्या', 'int', 'दशमलव', 'float', 'मुद्रय', 'print',
            'पठन', 'लेखन', 'अस्तित्व', 'मिटाओ', 'सूची_निर्देशिका', 'बनाओ_निर्देशिका',
            'परिवेश_प्राप्त', 'परिवेश_सेट', 'प्रणाली_कमांड', 'मंच', 'कार्य_निर्देशिका',
            'संयोग', 'विभाजन', 'छाँटो', 'उच्च', 'निम्न', 'पूर्णांक_कर',
            'क्रमबद्ध', 'योग', 'अधिकतम', 'न्यूनतम', 'कुंजियाँ', 'मान', 'वर्गमूल',
            'परिभाषय', 'दावा', 'नियम', 'मूल्यांकन', 'सिद्ध_है',
            'आत्म_मूल्य', 'भाव_पढ़ो', 'अवस्था_पढ़ो', 'सभी_भाव', 'सभी_अवस्था', 'आत्म_इतिहास', 'आत्म_है', 'आत्म_भाव', 'आत्म_अवस्था', 'आत्म_मूल'
        ]
        if isinstance(node.callee, IdentifierExpr) and node.callee.name in builtins_list:
            # Check if it's shadowed by a local or global variable
            is_shadowed = node.callee.name in self.bytecode.var_names or node.callee.name in self.bytecode.global_names
            if not is_shadowed:
                # Compile args left-to-right for builtins
                for arg in node.args:
                    self._compile_node(arg)
                builtin_idx = self._get_builtin_index(node.callee.name)
                self.bytecode.emit(OpCode.CALL_BUILTIN, builtin_idx, len(node.args))
                return

        is_method_call = isinstance(node.callee, MemberExpr)

        # Compile callee FIRST
        if isinstance(node.callee, IdentifierExpr):
            slot = self.bytecode.get_var_slot(node.callee.name)
            self.bytecode.emit(OpCode.LOAD_VAR, slot)
        elif is_method_call:
            # MemberExpr: push obj, then push attr string
            self._compile_node(node.callee.obj)
            idx = self.bytecode.add_constant(node.callee.attr)
            self.bytecode.emit_16bit(OpCode.LOAD_CONST, idx)
        else:
            self._compile_node(node.callee)

        # Compile arguments left-to-right
        for arg in node.args:
            self._compile_node(arg)

        if is_method_call:
            self.bytecode.emit(OpCode.CALL_METHOD, len(node.args))
        else:
            self.bytecode.emit(OpCode.CALL, len(node.args))

    def _compile_MemberExpr(self, node: MemberExpr):
        self._compile_node(node.obj)
        idx = self.bytecode.add_constant(node.attr)
        self.bytecode.emit_16bit(OpCode.ATTR_GET, idx)

    def _compile_IndexExpr(self, node: IndexExpr):
        self._compile_node(node.obj)
        self._compile_node(node.index)
        self.bytecode.emit(OpCode.INDEX_GET)

    def _compile_SliceExpr(self, node: SliceExpr):
        self._compile_node(node.obj)

        if node.start:
            self._compile_node(node.start)
        else:
            self.bytecode.emit_16bit(OpCode.LOAD_CONST, self.bytecode.add_constant(None))

        if node.stop:
            self._compile_node(node.stop)
        else:
            self.bytecode.emit_16bit(OpCode.LOAD_CONST, self.bytecode.add_constant(None))

        if node.step:
            self._compile_node(node.step)
        else:
            self.bytecode.emit_16bit(OpCode.LOAD_CONST, self.bytecode.add_constant(None))

        self.bytecode.emit(OpCode.MAKE_SLICE)
        self.bytecode.emit(OpCode.INDEX_GET)

    def _compile_IdentifierExpr(self, node: IdentifierExpr):
        slot = self.bytecode.get_var_slot(node.name)
        self.bytecode.emit(OpCode.LOAD_VAR, slot)

    def _compile_NumberLiteral(self, node: NumberLiteral):
        idx = self.bytecode.add_constant(node.value)
        self.bytecode.emit_16bit(OpCode.LOAD_CONST, idx)

    def _compile_StringLiteral(self, node: StringLiteral):
        idx = self.bytecode.add_constant(node.value)
        self.bytecode.emit_16bit(OpCode.LOAD_CONST, idx)

    def _compile_FStringExpr(self, node: FStringExpr):
        for part in node.parts:
            self._compile_node(part)
        self.bytecode.emit(OpCode.BUILD_STRING, len(node.parts))

    def _compile_BoolLiteral(self, node: BoolLiteral):
        idx = self.bytecode.add_constant(node.value)
        self.bytecode.emit_16bit(OpCode.LOAD_CONST, idx)

    def _compile_NullLiteral(self, node: NullLiteral):
        idx = self.bytecode.add_constant(None)
        self.bytecode.emit_16bit(OpCode.LOAD_CONST, idx)

    def _compile_ListLiteral(self, node: ListLiteral):
        for el in node.elements:
            self._compile_node(el)
        self.bytecode.emit(OpCode.BUILD_LIST, len(node.elements))

    def _compile_ListComp(self, node: ListComp):
        # Create an empty list
        self.bytecode.emit(OpCode.BUILD_LIST, 0)

        # Evaluate iterable and get iterator
        self._compile_node(node.iterable)
        self.bytecode.emit(OpCode.GET_ITER)

        # Loop start
        loop_start = self.bytecode.get_current_offset()
        self.bytecode.emit_16bit(OpCode.FOR_ITER, 0)
        jump_exit = self.bytecode.get_current_offset() - 2

        # Store loop variable
        slot = self.bytecode.get_var_slot(node.var_name)
        self.bytecode.emit(OpCode.STORE_VAR, slot)

        # Evaluate expression
        self._compile_node(node.expr)

        # Append to list (stack: [... list, iter, val])
        # We need to rearrange stack or use a specific LIST_APPEND that expects this
        # Actually, LIST_APPEND pops val, and assumes list is at stack[-2].
        # But wait, stack is: list, iter, val.
        # So LIST_APPEND needs to operate on stack[-3]. Let's just emit SWAP, then rot? No.
        # Let's fix LIST_APPEND in VM to append stack[-1] to stack[-3].
        self.bytecode.emit(OpCode.LIST_APPEND)

        # Jump to loop start
        jump_dist = loop_start - (self.bytecode.get_current_offset() + 3)
        if jump_dist < 0:
            jump_dist += 65536
        self.bytecode.emit_16bit(OpCode.JUMP, jump_dist)

        # Patch exit
        exit_offset = self.bytecode.get_current_offset()
        self.bytecode.patch_jump(jump_exit, exit_offset)

    def _compile_DictLiteral(self, node: DictLiteral):
        for key, val in node.pairs:
            self._compile_node(val)
            self._compile_node(key)
        self.bytecode.emit(OpCode.BUILD_DICT, len(node.pairs))

    def _compile_SetLiteral(self, node: SetLiteral):
        for el in node.elements:
            self._compile_node(el)
        self.bytecode.emit(OpCode.BUILD_SET, len(node.elements))

    def _compile_AwaitExpr(self, node: AwaitExpr):
        """
        Compile await expression (प्रतीक्षा).
        
        The await keyword suspends the coroutine until the awaited
        coroutine completes, then pushes the result onto the stack.
        """
        # Compile the operand (should be a coroutine)
        self._compile_node(node.operand)
        # Emit AWAIT opcode to suspend and wait for result
        self.bytecode.emit(OpCode.AWAIT)

    def _get_builtin_index(self, name: str) -> int:
        """Get index of builtin function."""
        builtins_list = [
            'पाठ_कर', 'str', 'परास', 'range', 'दीर्घता', 'len', 'प्रकार', 'type',
            'संख्या', 'int', 'दशमलव', 'float', 'मुद्रय', 'print',
            'पठन', 'लेखन', 'अस्तित्व', 'मिटाओ', 'सूची_निर्देशिका', 'बनाओ_निर्देशिका',
            'परिवेश_प्राप्त', 'परिवेश_सेट', 'प्रणाली_कमांड', 'मंच', 'कार्य_निर्देशिका',
            'संयोग', 'विभाजन', 'छाँटो', 'उच्च', 'निम्न', 'पूर्णांक_कर',
            'क्रमबद्ध', 'योग', 'अधिकतम', 'न्यूनतम', 'कुंजियाँ', 'मान', 'वर्गमूल',
            'जाल_लाओ', 'जाल_भेजो', 'समय', 'निद्रा', 'धागा_शुरू',
            'रेगेक्स_खोज', 'रेगेक्स_बदलो', 'जेसन_लिखो', 'जेसन_पढ़ो',
            'परिभाषय', 'दावा', 'नियम', 'मूल्यांकन', 'सिद्ध_है',
            'आत्म_मूल्य', 'भाव_पढ़ो', 'अवस्था_पढ़ो', 'सभी_भाव', 'सभी_अवस्था', 'आत्म_इतिहास', 'आत्म_है', 'आत्म_भाव', 'आत्म_अवस्था', 'आत्म_मूल'
        ]
        try:
            return builtins_list.index(name)
        except ValueError:
            return 0

class CompileError(Exception):
    def __init__(self, message: str, line: int = 0):
        self.message = message
        self.line = line
        super().__init__(f"[Line {line}] {message}")
