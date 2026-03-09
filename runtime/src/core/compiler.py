# वाक् भाषा - संकलक (Bytecode Compiler)
# Vak Language - AST to Bytecode Compiler

from ..ast_nodes import *
from .opcodes import OpCode
from dataclasses import dataclass, field
from typing import Any, List, Dict

@dataclass
class CodeObject:
    """A compiled unit of execution."""
    name: str
    instructions: List[tuple] = field(default_factory=list)
    constants: List[Any] = field(default_factory=list)
    
    def emit(self, opcode: OpCode, operand: Any = None):
        self.instructions.append((opcode, operand))
        return len(self.instructions) - 1

    def patch(self, index: int, operand: Any):
        op, _ = self.instructions[index]
        self.instructions[index] = (op, operand)

    def add_const(self, value: Any) -> int:
        for i, c in enumerate(self.constants):
            if c == value: return i
        self.constants.append(value)
        return len(self.constants) - 1

class Compiler:
    """
    Compiles an AST into a CodeObject (Bytecode).
    """
    def __init__(self):
        self.code = CodeObject(name="<main>")

    def compile(self, program: Program) -> CodeObject:
        for stmt in program.body:
            self._gen_stmt(stmt)
        self.code.emit(OpCode.HALT)
        return self.code

    def _gen_stmt(self, node: Node):
        t = type(node)

        if t is VarDecl:
            if node.value:
                self._gen_expr(node.value)
            else:
                self.code.emit(OpCode.LOAD_CONST, self.code.add_const(None))
            self.code.emit(OpCode.DEFINE_VAR, node.name)

        elif t is ConstDecl:
            self._gen_expr(node.value)
            self.code.emit(OpCode.DEFINE_CONST, node.name)

        elif t is PrintStmt:
            for val in node.values:
                self._gen_expr(val)
            self.code.emit(OpCode.PRINT, len(node.values))

        elif t is ExprStmt:
            self._gen_expr(node.expr)
            self.code.emit(OpCode.POP)

        elif t is IfStmt:
            self._gen_if(node)

        elif t is WhileStmt:
            self._gen_while(node)

        elif t is ReturnStmt:
            if node.value:
                self._gen_expr(node.value)
            else:
                self.code.emit(OpCode.LOAD_CONST, self.code.add_const(None))
            self.code.emit(OpCode.RETURN)

        elif t is Block:
            for stmt in node.stmts:
                self._gen_stmt(stmt)

        elif t is FuncDecl:
            self._gen_func(node)

        elif t is ClassDecl:
            self._gen_class(node)
            
        elif t is ImportStmt:
            self.code.emit(OpCode.IMPORT, (node.module, node.names))

    def _gen_expr(self, node: Node):
        t = type(node)

        if t is NumberLiteral or t is StringLiteral or t is BoolLiteral:
            idx = self.code.add_const(node.value)
            self.code.emit(OpCode.LOAD_CONST, idx)
        
        elif t is NullLiteral:
            idx = self.code.add_const(None)
            self.code.emit(OpCode.LOAD_CONST, idx)

        elif t is IdentifierExpr:
            self.code.emit(OpCode.LOAD_VAR, node.name)

        elif t is BinaryExpr:
            self._gen_expr(node.left)
            self._gen_expr(node.right)
            op_map = {
                '+': OpCode.ADD, '-': OpCode.SUB, '*': OpCode.MUL,
                '/': OpCode.DIV, '//': OpCode.IDIV, '%': OpCode.MOD,
                '**': OpCode.POW, '==': OpCode.EQ, '!=': OpCode.NEQ,
                '<': OpCode.LT, '>': OpCode.GT, '<=': OpCode.LTE,
                '>=': OpCode.GTE, 'अन्तर्गत': OpCode.IN
            }
            self.code.emit(op_map[node.op])

        elif t is UnaryExpr:
            self._gen_expr(node.operand)
            if node.op == '-': self.code.emit(OpCode.NEG)
            if node.op == 'न': self.code.emit(OpCode.NOT)

        elif t is CallExpr:
            self._gen_expr(node.callee)
            for arg in node.args:
                self._gen_expr(arg)
            self.code.emit(OpCode.CALL, len(node.args))

        elif t is ListLiteral:
            for el in node.elements:
                self._gen_expr(el)
            self.code.emit(OpCode.MAKE_LIST, len(node.elements))

        elif t is MemberExpr:
            self._gen_expr(node.obj)
            self.code.emit(OpCode.GET_MEMBER, node.attr)

        elif t is AssignExpr:
            self._gen_expr(node.value)
            if isinstance(node.target, IdentifierExpr):
                self.code.emit(OpCode.STORE_VAR, node.target.name)
            elif isinstance(node.target, MemberExpr):
                self._gen_expr(node.target.obj)
                self.code.emit(OpCode.SET_MEMBER, node.target.attr)

    def _gen_if(self, node: IfStmt):
        # 1. Condition
        self._gen_expr(node.condition)
        jump_to_else = self.code.emit(OpCode.JUMP_IF_FALSE, 0)
        self.code.emit(OpCode.POP) # pop condition result

        # 2. Then body
        self._gen_stmt(node.then_body)
        jump_to_end = self.code.emit(OpCode.JUMP, 0)

        # 3. Patch condition jump to here
        self.code.patch(jump_to_else, len(self.code.instructions))
        self.code.emit(OpCode.POP)

        # 4. Handle elifs and else
        if node.else_body:
            self._gen_stmt(node.else_body)
        
        self.code.patch(jump_to_end, len(self.code.instructions))

    def _gen_while(self, node: WhileStmt):
        loop_start = len(self.code.instructions)
        self._gen_expr(node.condition)
        exit_jump = self.code.emit(OpCode.JUMP_IF_FALSE, 0)
        self.code.emit(OpCode.POP)

        self._gen_stmt(node.body)
        self.code.emit(OpCode.LOOP, loop_start)

        self.code.patch(exit_jump, len(self.code.instructions))
        self.code.emit(OpCode.POP)

    def _gen_func(self, node: FuncDecl):
        # Functions are compiled into separate code objects
        old_code = self.code
        self.code = CodeObject(name=node.name)
        
        # In a real compiler, we'd handle params here
        # For this bridge, we'll keep it simple
        self._gen_stmt(node.body)
        self.code.emit(OpCode.LOAD_CONST, self.code.add_const(None))
        self.code.emit(OpCode.RETURN)
        
        func_code = self.code
        self.code = old_code
        
        idx = self.code.add_const(func_code)
        self.code.emit(OpCode.LOAD_CONST, idx)
        self.code.emit(OpCode.MAKE_FUNC, node.name)

    def _gen_class(self, node: ClassDecl):
        # Similar to functions, compile body
        # For now, classes define methods in their own namespace
        self.code.emit(OpCode.MAKE_CLASS, (node.name, node.superclass.name if node.superclass else None))
