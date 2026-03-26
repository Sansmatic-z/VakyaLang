# वाक् भाषा - दुभाषिया (Interpreter)
# Vak Language - High-level interface (Lexer → Parser → Compiler → VM)

from .lexer import Lexer
from .parser import Parser
from .compiler import Compiler, CompileError
from .vm import VakVM, VMError
from .errors import VakError
from .audit import emit_audit_event

class VakInterpreter:
    """
    High-level interpreter that orchestrates the full pipeline:
    Source Code → Lexer → Parser → AST → Compiler → Bytecode → VM → Result
    """
    
    def __init__(self):
        self.vm = VakVM()
        self.debug = False

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
            if debug:
                self._debug_print(f"AST generated: {type(ast).__name__}")
                
            # Step 3: Compilation
            if debug:
                self._debug_print("\n=== Stage 3: Compilation ===")
            compiler = Compiler()
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
        # except Exception as e:
            # raise VakError(f"Execution error: {e}")
            
    def compile_only(self, source: str, filename: str | None = None) -> 'Bytecode':
        """Compile source to bytecode without executing."""
        emit_audit_event("vak.interpreter.compile.start", filename or "<memory>")
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        compiler = Compiler()
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
        
    def repl(self, banner: str = None):
        """Interactive REPL."""
        if banner:
            print(banner)
        else:
            print("🕉️ वाक् भाषा - आभासी यन्त्र (VakyaLang VM)")
            print("Type 'debug' to toggle debug mode, 'exit' to quit\n")
        
        while True:
            try:
                line = input("वाक्> ")
                if line.strip() == 'exit':
                    break
                if line.strip() == 'debug':
                    self.debug = not self.debug
                    print(f"Debug mode: {'ON' if self.debug else 'OFF'}")
                    continue
                if not line.strip():
                    continue
                    
                result = self.run(line, debug=self.debug)
                if result is not None:
                    print(f"=> {result}")
                    
            except KeyboardInterrupt:
                print("\nUse 'exit' to quit")
            except EOFError:
                break
            # except Exception as e:
                print(f"त्रुटि (Error): {e}")
                
        print("\nनमस्ते (Goodbye)!")
