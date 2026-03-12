# वाक् भाषा - दुभाषिया (Interpreter)
# Vak Language - High-level interface (Lexer → Parser → Compiler → VM)

from .lexer import Lexer
from .parser import Parser
from .compiler import Compiler, CompileError
from .vm import VakVM, VMError
from .errors import VakError

class VakInterpreter:
    """
    High-level interpreter that orchestrates the full pipeline:
    Source Code → Lexer → Parser → AST → Compiler → Bytecode → VM → Result
    """
    
    def __init__(self):
        self.vm = VakVM()
        self.debug = False
        
    def run(self, source: str, debug: bool = False) -> any:
        """
        Execute VakyaLang source code.
        
        Pipeline:
        1. Lexical analysis (tokenization)
        2. Parsing (AST generation)
        3. Compilation (Bytecode generation)
        4. Execution (VM)
        """
        self.debug = debug
        
        try:
            # Step 1: Lexical Analysis
            if debug:
                print("=== Stage 1: Lexical Analysis ===")
            lexer = Lexer(source)
            tokens = lexer.tokenize()
            if debug:
                print(f"Tokens: {len(tokens)}")
                for tok in tokens[:20]:  # Show first 20
                    print(f"  {tok}")
                if len(tokens) > 20:
                    print(f"  ... and {len(tokens)-20} more")
                    
            # Step 2: Parsing
            if debug:
                print("\n=== Stage 2: Parsing ===")
            parser = Parser(tokens)
            ast = parser.parse()
            if debug:
                print(f"AST generated: {type(ast).__name__}")
                
            # Step 3: Compilation
            if debug:
                print("\n=== Stage 3: Compilation ===")
            compiler = Compiler()
            bytecode = compiler.compile(ast)
            if debug:
                print(f"Bytecode: {len(bytecode.code)} bytes")
                print(f"Constants: {len(bytecode.constants)}")
                print(f"Variables: {bytecode.var_names}")
                print("\nDisassembly:")
                print(bytecode.disassemble())
                
            # Step 4: Execution
            if debug:
                print("\n=== Stage 4: Execution ===")
            result = self.vm.run(bytecode)
            
            if debug:
                print(f"\nResult: {result}")
                
            return result
            
        except VakError as e:
            raise
        except Exception as e:
            raise VakError(f"Execution error: {e}")
            
    def compile_only(self, source: str) -> 'Bytecode':
        """Compile source to bytecode without executing."""
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        compiler = Compiler()
        return compiler.compile(ast)
        
    def run_bytecode(self, bytecode) -> any:
        """Execute pre-compiled bytecode."""
        return self.vm.run(bytecode)
        
    def repl(self):
        """Interactive REPL."""
        print("🕉️ वाक् भाषा - आभासी यन्त्र (VakyaLang VM)")
        print("Version 2.0 - Bytecode Edition")
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
            except Exception as e:
                print(f"त्रुटि (Error): {e}")
                
        print("\nनमस्ते (Goodbye)!")
