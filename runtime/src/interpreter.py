# वाक् भाषा - क्रियान्वयक (Interpreter)
# Vak Language - Tree-Walk Interpreter

import math
import time
import os

from .ast_nodes import *
from .environment import Environment
from .errors import (VakRuntimeError, VakTypeError, VakNameError,
                      VakIndexError, ReturnException, BreakException,
                      ContinueException, ThrowException)


# ── Runtime value types ───────────────────────────────────────────────────────

class VakNull:
    """Represents शून्य (null)."""
    _instance = None
    def __new__(cls):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance
    def __repr__(self): return "शून्य"
    def __bool__(self): return False

VAK_NULL = VakNull()


class VakFunction:
    """A user-defined function (कर्म)."""
    def __init__(self, decl: FuncDecl, closure: Environment,
                 is_initializer=False):
        self.decl           = decl
        self.closure        = closure
        self.is_initializer = is_initializer

    def bind(self, instance: "VakInstance") -> "VakFunction":
        """Bind स्वयं (self) for method calls."""
        env = self.closure.child("method")
        env.define("स्वयं", instance)
        return VakFunction(self.decl, env, self.is_initializer)

    def __repr__(self):
        return f"<कर्म {self.decl.name}>"


class VakClass:
    """A user-defined class (वर्ग)."""
    def __init__(self, name: str, superclass, methods: dict):
        self.name       = name
        self.superclass = superclass
        self.methods    = methods

    def find_method(self, name: str):
        if name in self.methods:
            return self.methods[name]
        if self.superclass:
            return self.superclass.find_method(name)
        return None

    def __repr__(self):
        return f"<वर्ग {self.name}>"


class VakInstance:
    """An instance of a VakClass."""
    def __init__(self, klass: VakClass):
        self.klass  = klass
        self.fields = {}

    def get(self, name: str, line=None):
        if name in self.fields:
            return self.fields[name]
        method = self.klass.find_method(name)
        if method:
            return method.bind(self)
        raise VakNameError(
            f"'{self.klass.name}' में '{name}' नहीं मिला", line)

    def set(self, name: str, value):
        self.fields[name] = value

    def __repr__(self):
        return f"<{self.klass.name} उदाहरण>"


class VakModule:
    """A module (आयातित मॉड्यूल)."""
    def __init__(self, name: str, env: Environment):
        self.name = name
        self.env  = env

    def get(self, name: str, line=None):
        try:
            return self.env.get(name, line)
        except VakNameError:
            raise VakNameError(f"मॉड्यूल '{self.name}' में '{name}' नहीं मिला", line)

    def __repr__(self):
        return f"<मॉड्यूल {self.name}>"


class BuiltinFunction:
    """A native/built-in function."""
    def __init__(self, name: str, fn):
        self.name = name
        self.fn   = fn

    def __repr__(self):
        return f"<अन्तर्निर्मित {self.name}>"


# ── Interpreter ───────────────────────────────────────────────────────────────

class Interpreter:
    """
    Walks the AST and evaluates each node.
    """

    def __init__(self):
        self.globals = Environment(name="global")
        self._register_builtins()

    # ── Built-in functions ────────────────────────────────────────────────────

    def _register_builtins(self):
        g = self.globals

        def _len(args, kwargs):
            self._arity("दीर्घता", args, 1)
            v = args[0]
            if isinstance(v, (str, list, dict)):
                return len(v)
            raise VakTypeError("दीर्घता: केवल तार/सूची/शब्दकोश (string/list/dict)")

        def _type(args, kwargs):
            self._arity("प्रकार", args, 1)
            v = args[0]
            type_map = {
                int: "पूर्णांक", float: "दशमलव", str: "तार",
                bool: "बूलियन", list: "सूची", dict: "शब्दकोश",
            }
            if isinstance(v, VakNull):    return "शून्य"
            if isinstance(v, VakFunction):return "कर्म"
            if isinstance(v, VakClass):   return "वर्ग"
            if isinstance(v, VakInstance):return v.klass.name
            return type_map.get(type(v), str(type(v)))

        def _int(args, kwargs):
            self._arity("पूर्णांक_कर", args, 1)
            try: return int(args[0])
            except: raise VakTypeError(f"पूर्णांक नहीं बना सकते: {args[0]!r}")

        def _float(args, kwargs):
            self._arity("दशमलव_कर", args, 1)
            try: return float(args[0])
            except: raise VakTypeError(f"दशमलव नहीं बना सकते: {args[0]!r}")

        def _str(args, kwargs):
            self._arity("पाठ_कर", args, 1)
            return self._stringify(args[0])

        def _input(args, kwargs):
            prompt = args[0] if args else ""
            return input(self._stringify(prompt))

        def _range(args, kwargs):
            if len(args) == 1:
                return list(range(int(args[0])))
            elif len(args) == 2:
                return list(range(int(args[0]), int(args[1])))
            elif len(args) == 3:
                return list(range(int(args[0]), int(args[1]), int(args[2])))
            raise VakTypeError("परास को 1-3 तर्क चाहिए")

        def _append(args, kwargs):
            self._arity("जोड़ो", args, 2)
            if not isinstance(args[0], list):
                raise VakTypeError("जोड़ो: पहला तर्क सूची होनी चाहिए")
            args[0].append(args[1])
            return VAK_NULL

        def _remove(args, kwargs):
            self._arity("हटाओ", args, 2)
            if not isinstance(args[0], list):
                raise VakTypeError("हटाओ: पहला तर्क सूची होनी चाहिए")
            try: args[0].remove(args[1])
            except ValueError: pass
            return VAK_NULL

        def _pop(args, kwargs):
            if len(args) < 1:
                raise VakTypeError("निकालो: सूची चाहिए")
            lst = args[0]
            idx = int(args[1]) if len(args) > 1 else -1
            try: return lst.pop(idx)
            except IndexError: raise VakIndexError("सूची खाली है")

        def _keys(args, kwargs):
            self._arity("कुंजियाँ", args, 1)
            if not isinstance(args[0], dict):
                raise VakTypeError("कुंजियाँ: शब्दकोश चाहिए")
            return list(args[0].keys())

        def _values(args, kwargs):
            self._arity("मान", args, 1)
            if not isinstance(args[0], dict):
                raise VakTypeError("मान: शब्दकोश चाहिए")
            return list(args[0].values())

        def _sqrt(args, kwargs):
            self._arity("वर्गमूल", args, 1)
            try: return math.sqrt(float(args[0]))
            except: raise VakTypeError("वर्गमूल: संख्या चाहिए")

        def _abs(args, kwargs):
            self._arity("परम", args, 1)
            try: return abs(args[0])
            except: raise VakTypeError("परम: संख्या चाहिए")

        def _floor(args, kwargs):
            self._arity("तल", args, 1)
            return math.floor(args[0])

        def _ceil(args, kwargs):
            self._arity("छत", args, 1)
            return math.ceil(args[0])

        def _max(args, kwargs):
            if not args: raise VakTypeError("अधिक: तर्क चाहिए")
            return max(args[0] if len(args)==1 and isinstance(args[0],list) else args)

        def _min(args, kwargs):
            if not args: raise VakTypeError("न्यून: तर्क चाहिए")
            return min(args[0] if len(args)==1 and isinstance(args[0],list) else args)

        def _sum(args, kwargs):
            self._arity("योग", args, 1)
            return sum(args[0])

        def _sort(args, kwargs):
            self._arity("क्रमबद्ध", args, 1)
            lst = list(args[0])
            lst.sort()
            return lst

        def _reverse(args, kwargs):
            self._arity("उलटो", args, 1)
            return list(reversed(args[0]))

        def _split(args, kwargs):
            self._arity("विभाजन", args, 2)
            return args[0].split(args[1])

        def _join(args, kwargs):
            self._arity("संयोग", args, 2)
            return args[1].join(str(x) for x in args[0])

        def _upper(args, kwargs):
            self._arity("उच्च", args, 1)
            return str(args[0]).upper()

        def _lower(args, kwargs):
            self._arity("निम्न", args, 1)
            return str(args[0]).lower()

        def _strip(args, kwargs):
            self._arity("छाँटो", args, 1)
            return str(args[0]).strip()

        def _time(args, kwargs):
            return time.time()

        def _exit(args, kwargs):
            code = int(args[0]) if args else 0
            raise SystemExit(code)

        def _assert(args, kwargs):
            self._arity("दृढ़ता", args, 1)
            msg = self._stringify(args[1]) if len(args) > 1 else "दृढ़ता विफल"
            if not args[0]:
                raise ThrowException(msg)
            return VAK_NULL

        # Register all built-ins
        builtins = {
            "दीर्घता":    _len,       # len
            "प्रकार":     _type,      # type
            "पूर्णांक_कर": _int,      # int()
            "दशमलव_कर":  _float,     # float()
            "पाठ_कर":    _str,       # str()
            "प्रवेश":     _input,     # input()
            "परास":       _range,     # range()
            "जोड़ो":      _append,    # list.append
            "हटाओ":      _remove,    # list.remove
            "निकालो":    _pop,       # list.pop
            "कुंजियाँ":   _keys,      # dict.keys
            "मान":        _values,    # dict.values
            "वर्गमूल":   _sqrt,      # sqrt
            "परम":        _abs,       # abs
            "तल":         _floor,     # floor
            "छत":         _ceil,      # ceil
            "अधिकतम":    _max,       # max
            "न्यूनतम":   _min,       # min
            "योग":        _sum,       # sum
            "क्रमबद्ध":  _sort,      # sorted
            "उलटो":      _reverse,   # reversed
            "विभाजन":    _split,     # split
            "संयोग":     _join,      # join
            "उच्च":       _upper,     # upper
            "निम्न":      _lower,     # lower
            "छाँटो":     _strip,     # strip
            "काल":        _time,      # time
            "निर्गम":    _exit,      # exit
            "दृढ़ता":    _assert,    # assert
            # Math constants
            "पाई":        math.pi,    # π
            "प्रकृतिक_आधार": math.e, # e
        }

        for name, fn in builtins.items():
            if callable(fn):
                g.define(name, BuiltinFunction(name, fn))
            else:
                g.define(name, fn)

        # Register system bridge built-ins
        from .bridge.system import register_system_bridge
        register_system_bridge(g)

    def _arity(self, name, args, expected):
        if len(args) != expected:
            raise VakTypeError(
                f"{name}: {expected} तर्क चाहिए, {len(args)} मिले")

    # ── Execution entry point ─────────────────────────────────────────────────

    def execute(self, program: Program):
        env = self.globals
        for stmt in program.body:
            self._exec(stmt, env)

    def execute_block(self, block: Block, env: Environment):
        for stmt in block.stmts:
            self._exec(stmt, env)

    # ── Statement dispatch ────────────────────────────────────────────────────

    def _exec(self, node: Node, env: Environment):
        t = type(node)

        if t is VarDecl:
            value = self._eval(node.value, env) if node.value is not None else VAK_NULL
            env.define(node.name, value, constant=False)

        elif t is ConstDecl:
            value = self._eval(node.value, env)
            env.define(node.name, value, constant=True)

        elif t is FuncDecl:
            fn = VakFunction(node, env)
            env.define(node.name, fn)

        elif t is ClassDecl:
            superclass = None
            if node.superclass:
                superclass = self._eval(node.superclass, env)
                if not isinstance(superclass, VakClass):
                    raise VakTypeError(
                        f"'{node.name}' का अभिभावक वर्ग नहीं है", node.line)

            methods = {}
            class_env = env.child(f"class:{node.name}")
            if superclass:
                class_env.define("अभिभावक", superclass)
            for stmt in node.body.stmts:
                if isinstance(stmt, FuncDecl):
                    is_init = stmt.name in ("प्रारम्भ", "__init__")
                    methods[stmt.name] = VakFunction(stmt, class_env, is_init)

            klass = VakClass(node.name, superclass, methods)
            env.define(node.name, klass)

        elif t is PrintStmt:
            parts = [self._stringify(self._eval(v, env)) for v in node.values]
            print(' '.join(parts))

        elif t is IfStmt:
            if self._truthy(self._eval(node.condition, env)):
                child = env.child("if")
                self.execute_block(node.then_body, child)
            else:
                handled = False
                for cond, body in node.elif_clauses:
                    if self._truthy(self._eval(cond, env)):
                        child = env.child("elif")
                        self.execute_block(body, child)
                        handled = True
                        break
                if not handled and node.else_body:
                    child = env.child("else")
                    self.execute_block(node.else_body, child)

        elif t is WhileStmt:
            while self._truthy(self._eval(node.condition, env)):
                try:
                    child = env.child("while")
                    self.execute_block(node.body, child)
                except BreakException:
                    break
                except ContinueException:
                    continue

        elif t is ForStmt:
            iterable = self._eval(node.iterable, env)
            if not hasattr(iterable, '__iter__'):
                raise VakTypeError("प्रत्येक: पुनरावर्तनीय नहीं है", node.line)
            for item in iterable:
                try:
                    child = env.child("for")
                    child.define(node.var_name, item)
                    self.execute_block(node.body, child)
                except BreakException:
                    break
                except ContinueException:
                    continue

        elif t is ReturnStmt:
            value = self._eval(node.value, env) if node.value else VAK_NULL
            raise ReturnException(value)

        elif t is BreakStmt:
            raise BreakException()

        elif t is ContinueStmt:
            raise ContinueException()

        elif t is ThrowStmt:
            value = self._eval(node.value, env)
            raise ThrowException(value)

        elif t is TryStmt:
            try:
                child = env.child("try")
                self.execute_block(node.try_body, child)
            except ThrowException as e:
                if node.catch_body:
                    child = env.child("catch")
                    if node.catch_var:
                        child.define(node.catch_var, e.value)
                    self.execute_block(node.catch_body, child)
            except VakRuntimeError as e:
                if node.catch_body:
                    child = env.child("catch")
                    if node.catch_var:
                        child.define(node.catch_var, str(e.message))
                    self.execute_block(node.catch_body, child)
            finally:
                if node.finally_body:
                    child = env.child("finally")
                    self.execute_block(node.finally_body, child)

        elif t is ImportStmt:
            self._handle_import(node, env)

        elif t is ExprStmt:
            self._eval(node.expr, env)

        elif t is Block:
            self.execute_block(node, env)

        else:
            raise VakRuntimeError(f"अज्ञात कथन: {type(node).__name__}", 0)

    # ── Expression evaluation ─────────────────────────────────────────────────

    def _eval(self, node: Node, env: Environment):
        t = type(node)

        if t is NumberLiteral:  return node.value
        if t is StringLiteral:  return node.value
        if t is BoolLiteral:    return node.value
        if t is NullLiteral:    return VAK_NULL

        if t is IdentifierExpr:
            return env.get(node.name, node.line)

        if t is ListLiteral:
            return [self._eval(e, env) for e in node.elements]

        if t is DictLiteral:
            return {self._eval(k, env): self._eval(v, env)
                    for k, v in node.pairs}

        if t is UnaryExpr:
            return self._eval_unary(node, env)

        if t is BinaryExpr:
            return self._eval_binary(node, env)

        if t is AssignExpr:
            return self._eval_assign(node, env)

        if t is CallExpr:
            return self._eval_call(node, env)

        if t is MemberExpr:
            return self._eval_member(node, env)

        if t is IndexExpr:
            return self._eval_index(node, env)

        raise VakRuntimeError(
            f"अज्ञात भाव-प्रकार: {type(node).__name__}", getattr(node,'line',0))

    def _eval_unary(self, node: UnaryExpr, env):
        val = self._eval(node.operand, env)
        if node.op == '-':
            if isinstance(val, (int, float)):
                return -val
            raise VakTypeError("ऋण: केवल संख्या पर", node.line)
        if node.op == 'न':
            return not self._truthy(val)
        raise VakRuntimeError(f"अज्ञात एकल-संक्रिया: {node.op}", node.line)

    def _eval_binary(self, node: BinaryExpr, env):
        op = node.op

        # Short-circuit logic
        if op == 'और':
            left = self._eval(node.left, env)
            return left if not self._truthy(left) else self._eval(node.right, env)
        if op == 'अथवा':
            left = self._eval(node.left, env)
            return left if self._truthy(left) else self._eval(node.right, env)

        left  = self._eval(node.left,  env)
        right = self._eval(node.right, env)

        if op == '+':
            if isinstance(left, (int, float)) and isinstance(right, (int, float)):
                return left + right
            if isinstance(left, str) or isinstance(right, str):
                return self._stringify(left) + self._stringify(right)
            if isinstance(left, list) and isinstance(right, list):
                return left + right
            raise VakTypeError(f"'+' इन प्रकारों पर नहीं: {type(left).__name__}", node.line)
        if op == '-':
            return self._num(left, node.line) - self._num(right, node.line)
        if op == '*':
            if isinstance(left, (int,float)) and isinstance(right, (int,float)):
                return left * right
            if isinstance(left, str) and isinstance(right, int):
                return left * right
            raise VakTypeError("'*' इन प्रकारों पर नहीं", node.line)
        if op == '/':
            r = self._num(right, node.line)
            if r == 0: raise VakRuntimeError("शून्य से भाग नहीं (division by zero)", node.line)
            return self._num(left, node.line) / r
        if op == '//':
            r = self._num(right, node.line)
            if r == 0: raise VakRuntimeError("शून्य से भाग नहीं", node.line)
            return self._num(left, node.line) // r
        if op == '%':
            r = self._num(right, node.line)
            if r == 0: raise VakRuntimeError("शून्य से भाग नहीं", node.line)
            return self._num(left, node.line) % r
        if op == '**':
            return self._num(left, node.line) ** self._num(right, node.line)

        # Comparisons
        if op == '==':  return self._equal(left, right)
        if op == '!=':  return not self._equal(left, right)
        if op == '<':   return self._num(left,node.line) <  self._num(right,node.line)
        if op == '>':   return self._num(left,node.line) >  self._num(right,node.line)
        if op == '<=':  return self._num(left,node.line) <= self._num(right,node.line)
        if op == '>=':  return self._num(left,node.line) >= self._num(right,node.line)
        if op == 'अन्तर्गत':
            if isinstance(right, (list, str, dict)):
                return left in right
            raise VakTypeError("'अन्तर्गत': सूची/तार/शब्दकोश चाहिए", node.line)

        raise VakRuntimeError(f"अज्ञात संक्रिया: {op}", node.line)

    def _eval_assign(self, node: AssignExpr, env):
        value = self._eval(node.value, env)
        target = node.target

        if node.op != '=':
            # Compound assignment: +=, -=, *=, /=
            op_map = {'+=': '+', '-=': '-', '*=': '*', '/=': '/'}
            op = op_map[node.op]
            current = self._eval(target, env)
            dummy = BinaryExpr(op=op, left=NumberLiteral(current),
                                right=NumberLiteral(value), line=node.line)
            value = self._eval_binary(dummy, env)

        if isinstance(target, IdentifierExpr):
            env.assign(target.name, value, node.line)
        elif isinstance(target, MemberExpr):
            obj = self._eval(target.obj, env)
            if isinstance(obj, VakInstance):
                obj.set(target.attr, value)
            elif isinstance(obj, dict):
                obj[target.attr] = value
            else:
                raise VakTypeError("सदस्य असाइनमेंट इस प्रकार पर नहीं", node.line)
        elif isinstance(target, IndexExpr):
            obj = self._eval(target.obj, env)
            idx = self._eval(target.index, env)
            if isinstance(obj, list):
                obj[int(idx)] = value
            elif isinstance(obj, dict):
                obj[idx] = value
            else:
                raise VakTypeError("इंडेक्स असाइनमेंट इस प्रकार पर नहीं", node.line)
        else:
            raise VakRuntimeError("अमान्य असाइनमेंट लक्ष्य", node.line)

        return value

    def _eval_call(self, node: CallExpr, env):
        callee = self._eval(node.callee, env)
        args   = [self._eval(a, env) for a in node.args]
        kwargs = {k: self._eval(v, env) for k, v in node.kwargs.items()}

        if isinstance(callee, BuiltinFunction):
            return callee.fn(args, kwargs)

        if isinstance(callee, VakFunction):
            return self._call_function(callee, args, kwargs, node.line)

        if isinstance(callee, VakClass):
            instance = VakInstance(callee)
            init = callee.find_method("प्रारम्भ")
            if init:
                bound = init.bind(instance)
                self._call_function(bound, args, kwargs, node.line)
            return instance

        raise VakTypeError(
            f"'{self._stringify(callee)}' को कॉल नहीं किया जा सकता", node.line)

    def _call_function(self, fn: VakFunction, args, kwargs, line):
        decl = fn.decl
        env  = fn.closure.child(f"fn:{decl.name}")

        # Skip स्वयं (self) param if it's already defined in the closure (bound method)
        params   = list(decl.params)
        defaults = list(decl.defaults)
        if params and params[0] == 'स्वयं' and fn.closure.has('स्वयं'):
            params   = params[1:]
            defaults = defaults[1:]

        # Bind parameters
        for i, (param, default) in enumerate(zip(params, defaults)):
            if i < len(args):
                env.define(param, args[i])
            elif param in kwargs:
                env.define(param, kwargs[param])
            elif default is not None:
                env.define(param, self._eval(default, fn.closure))
            else:
                raise VakTypeError(
                    f"'{decl.name}': पैरामीटर '{param}' के लिए मान नहीं मिला", line)

        try:
            self.execute_block(decl.body, env)
        except ReturnException as r:
            if fn.is_initializer:
                return fn.closure.get("स्वयं")
            return r.value

        if fn.is_initializer:
            return fn.closure.get("स्वयं")
        return VAK_NULL

    def _eval_member(self, node: MemberExpr, env):
        obj = self._eval(node.obj, env)

        if isinstance(obj, VakInstance):
            return obj.get(node.attr, node.line)

        if isinstance(obj, VakModule):
            return obj.get(node.attr, node.line)

        if isinstance(obj, dict):
            if node.attr in obj:
                return obj[node.attr]
            raise VakNameError(f"शब्दकोश में '{node.attr}' नहीं", node.line)

        if isinstance(obj, list):
            list_methods = {
                "दीर्घता": lambda: len(obj),
                "जोड़ो":   lambda v: obj.append(v) or VAK_NULL,
                "निकालो":  lambda: obj.pop(),
                "उलटो":   lambda: obj.reverse() or VAK_NULL,
            }
            if node.attr in list_methods:
                m = list_methods[node.attr]
                return BuiltinFunction(node.attr, lambda args, kw: m(*args))

        if isinstance(obj, str):
            str_methods = {
                "दीर्घता":  lambda: len(obj),
                "उच्च":     lambda: obj.upper(),
                "निम्न":    lambda: obj.lower(),
                "छाँटो":   lambda: obj.strip(),
                "विभाजन":  lambda sep="": obj.split(sep) if sep else obj.split(),
            }
            if node.attr in str_methods:
                m = str_methods[node.attr]
                return BuiltinFunction(node.attr, lambda args, kw: m(*args))

        raise VakNameError(
            f"'{self._stringify(obj)}' में '{node.attr}' नहीं मिला", node.line)

    def _eval_index(self, node: IndexExpr, env):
        obj = self._eval(node.obj, env)
        idx = self._eval(node.index, env)

        if isinstance(obj, list):
            try: return obj[int(idx)]
            except IndexError:
                raise VakIndexError(f"सूची अनुक्रमणिका सीमा से बाहर: {idx}", node.line)

        if isinstance(obj, dict):
            if idx in obj: return obj[idx]
            raise VakIndexError(f"शब्दकोश में कुंजी नहीं: {idx!r}", node.line)

        if isinstance(obj, str):
            try: return obj[int(idx)]
            except IndexError:
                raise VakIndexError(f"तार अनुक्रमणिका सीमा से बाहर: {idx}", node.line)

        raise VakTypeError("इंडेक्स योग्य नहीं", node.line)

    # ── Import handling ───────────────────────────────────────────────────────

    def _handle_import(self, node: ImportStmt, env: Environment):
        """
        Basic import: looks for a .vak file relative to cwd.
        """
        mod_path = node.module.replace('.', os.sep) + '.vak'
        if not os.path.exists(mod_path):
            raise VakRuntimeError(
                f"मॉड्यूल नहीं मिला: '{node.module}' ({mod_path})", node.line)

        with open(mod_path, encoding='utf-8') as f:
            source = f.read()

        from .lexer import Lexer
        from .parser import Parser as VakParser

        tokens  = Lexer(source).tokenize()
        program = VakParser(tokens).parse()
        mod_env = Environment(parent=self.globals, name=node.module)
        for stmt in program.body:
            self._exec(stmt, mod_env)

        module_obj = VakModule(node.module, mod_env)

        if node.names:
            # 'आयात name से module'
            for name in node.names:
                env.define(name, mod_env.get(name, node.line))
        else:
            # Regular 'आयात a.b.c'
            # We want to create 'a' if it doesn't exist, and put 'b' inside it, etc.
            parts = node.module.split('.')
            current_env = env
            for i, part in enumerate(parts):
                if i == len(parts) - 1:
                    # Final part is the module itself
                    current_env.define(part, module_obj)
                else:
                    # Create or get intermediate module
                    if current_env.has(part):
                        existing = current_env.get(part)
                        if isinstance(existing, VakModule):
                            current_env = existing.env
                        else:
                            raise VakRuntimeError(
                                f"अमान्य मॉड्यूल पथ: '{part}' पहले से ही परिभाषित है", node.line)
                    else:
                        new_mod_env = Environment(parent=self.globals, name=part)
                        new_mod = VakModule(part, new_mod_env)
                        current_env.define(part, new_mod)
                        current_env = new_mod_env

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _truthy(self, val) -> bool:
        if isinstance(val, VakNull): return False
        if isinstance(val, bool):   return val
        if isinstance(val, (int, float)): return val != 0
        if isinstance(val, (str, list, dict)): return len(val) > 0
        return True

    def _equal(self, a, b) -> bool:
        if isinstance(a, VakNull) and isinstance(b, VakNull): return True
        if isinstance(a, VakNull) or isinstance(b, VakNull):  return False
        return a == b

    def _num(self, val, line=None):
        if isinstance(val, (int, float)) and not isinstance(val, bool):
            return val
        raise VakTypeError(
            f"संख्या चाहिए, मिला '{self._stringify(val)}'", line)

    def _stringify(self, val) -> str:
        if isinstance(val, VakNull):  return "शून्य"
        if isinstance(val, bool):     return "सत्य" if val else "असत्य"
        if isinstance(val, float):
            if val == int(val): return str(int(val))
            return str(val)
        if isinstance(val, list):
            return "[" + ", ".join(self._stringify(x) for x in val) + "]"
        if isinstance(val, dict):
            pairs = ", ".join(
                f"{self._stringify(k)}: {self._stringify(v)}"
                for k, v in val.items()
            )
            return "{" + pairs + "}"
        return str(val)
