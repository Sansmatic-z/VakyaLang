# वाक् भाषा - दुभाषिया (Interpreter)
# Vak Language - High-level interface (Lexer → Parser → Compiler → VM)

from typing import Any, Optional

from .lexer import Lexer
from .parser import Parser
from .compiler import Compiler, CompileError
from .vm import VakVM, VMError
from .errors import VakError, format_vak_error_with_suggestions
from .audit import emit_audit_event
from .branching import BranchActivationError

class VakInterpreter:
    """
    High-level interpreter that orchestrates the full pipeline:
    Source Code → Lexer → Parser → AST → Compiler → Bytecode → VM → Result
    """
    
    def __init__(
        self,
        *,
        active_branches: Optional[list[str]] = None,
        branch_registry: Any = None,
    ):
        self.debug = False
        self.branch_runtime = None
        if active_branches:
            registry = branch_registry
            if registry is None:
                from branches.registry import create_default_registry

                registry = create_default_registry()
            self.branch_runtime = registry.create_runtime(
                list(active_branches),
                include_defaults=True,
            )
        self.vm = VakVM(
            branch_runtime=self.branch_runtime,
            branch_registry=branch_registry,
        )

    def get_branch_report(self) -> dict[str, dict[str, Any]]:
        if self.branch_runtime is None:
            return {}
        return self.branch_runtime.report()

    def inspect_vm_stack(self) -> list[dict[str, Any]]:
        return self.vm.inspect_stack()

    def error_context(self) -> dict[str, Any]:
        return {
            "frame": self.vm.current_frame,
            "globals": self.vm.globals,
            "builtins": self.vm.builtins,
        }

    def _debug_print(self, text: str) -> None:
        try:
            print(text)
        except UnicodeEncodeError:
            import sys

            encoding = sys.stdout.encoding or 'utf-8'
            safe_text = text.encode(encoding, errors='backslashreplace').decode(
                encoding,
                errors='replace',
            )
            sys.stdout.write(f"{safe_text}\n")
        
    def run(self, source: str, debug: bool = False, filename: str | None = None) -> any:
        """
        Execute VakyaLang source code.
        
        Pipeline:
        1. Lexical analysis (tokenization)
        2. Parsing (AST generation)
        3. Compilation (Bytecode generation)
        4. Execution (VM)
        """
        self.debug = debug
        emit_audit_event("vak.interpreter.run.start", filename or "<memory>", debug)
        
        try:
            # Step 1: Lexical Analysis
            if debug:
                self._debug_print("=== Stage 1: Lexical Analysis ===")
            lexer = Lexer(source)
            tokens = lexer.tokenize()
            if debug:
                self._debug_print(f"Tokens: {len(tokens)}")
                for tok in tokens[:20]:  # Show first 20
                    self._debug_print(f"  {tok}")
                if len(tokens) > 20:
                    self._debug_print(f"  ... and {len(tokens)-20} more")
                    
            # Step 2: Parsing
            if debug:
                self._debug_print("\n=== Stage 2: Parsing ===")
            parser = Parser(tokens)
            ast = parser.parse()
            if self.branch_runtime is not None:
                self.branch_runtime.on_program_parsed(
                    ast,
                    filename=filename,
                    interpreter=self,
                )
            if debug:
                self._debug_print(f"AST generated: {type(ast).__name__}")
                
            # Step 3: Compilation
            if debug:
                self._debug_print("\n=== Stage 3: Compilation ===")
            compiler = Compiler(
                branch_runtime=self.branch_runtime,
                source_path=filename,
            )
            bytecode = compiler.compile(ast)
            bytecode.source_path = filename
            emit_audit_event(
                "vak.interpreter.compile.complete",
                filename or "<memory>",
                len(bytecode.code),
                len(bytecode.constants),
            )
            if debug:
                self._debug_print(f"Bytecode: {len(bytecode.code)} bytes")
                self._debug_print(f"Constants: {len(bytecode.constants)}")
                self._debug_print(f"Variables: {bytecode.var_names}")
                self._debug_print("\nDisassembly:")
                self._debug_print(bytecode.disassemble())
                
            # Step 4: Execution
            if debug:
                self._debug_print("\n=== Stage 4: Execution ===")
            result = self.vm.run(bytecode)
            emit_audit_event("vak.interpreter.run.complete", filename or "<memory>")
            
            if debug:
                self._debug_print(f"\nResult: {result}")
                
            return result
            
        except VakError as e:
            emit_audit_event("vak.interpreter.run.error", filename or "<memory>", str(e))
            raise
        except BranchActivationError as e:
            emit_audit_event("vak.interpreter.run.error", filename or "<memory>", str(e))
            raise
        # except Exception as e:
            # raise VakError(f"Execution error: {e}")
            
    def compile_only(self, source: str, filename: str | None = None) -> 'Bytecode':
        """Compile source to bytecode without executing."""
        emit_audit_event("vak.interpreter.compile.start", filename or "<memory>")
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        if self.branch_runtime is not None:
            self.branch_runtime.on_program_parsed(
                ast,
                filename=filename,
                interpreter=self,
            )
        compiler = Compiler(
            branch_runtime=self.branch_runtime,
            source_path=filename,
        )
        bytecode = compiler.compile(ast)
        bytecode.source_path = filename
        emit_audit_event(
            "vak.interpreter.compile.complete",
            filename or "<memory>",
            len(bytecode.code),
            len(bytecode.constants),
        )
        return bytecode
        
    def run_bytecode(self, bytecode) -> any:
        """Execute pre-compiled bytecode."""
        emit_audit_event("vak.interpreter.bytecode.run", getattr(bytecode, "name", "<unknown>"))
        return self.vm.run(bytecode)

    def _read_repl_source(self) -> str | None:
        line = input("वाक्> ")
        stripped = line.strip()
        if stripped in {'exit', 'quit'}:
            return None
        if not stripped:
            return ""
        if not stripped.endswith(':'):
            return line

        lines = [line]
        while True:
            continuation = input("... ")
            if not continuation.strip():
                break
            lines.append(continuation)
        return "\n".join(lines)
        
    def repl(self, banner: str = None):
        """Interactive REPL."""
        if banner:
            print(banner)
        else:
            print("🕉️ वाक् भाषा - आभासी यन्त्र (VakyaLang VM)")
            print("Type 'debug' to toggle debug mode, 'exit' to quit")
            print("End an indented block with an empty line.\n")
        
        while True:
            try:
                source = self._read_repl_source()
                if source is None:
                    break
                if source.strip() == 'debug':
                    self.debug = not self.debug
                    print(f"Debug mode: {'ON' if self.debug else 'OFF'}")
                    continue
                if not source.strip():
                    continue
                    
                result = self.run(source, debug=self.debug, filename="<repl>")
                if result is not None:
                    print(f"=> {result}")
                    
            except KeyboardInterrupt:
                print("\nUse 'exit' to quit")
            except EOFError:
                break
            except Exception as e:
                print(format_vak_error_with_suggestions(e, self.error_context()))
                
        print("\nनमस्ते (Goodbye)!")
