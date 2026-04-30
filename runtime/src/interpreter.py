# वाक् भाषा - दुभाषिया (Interpreter)
# Vak Language - High-level interface (Lexer → Parser → Compiler → VM)

from typing import Any, Optional
from pathlib import Path
from time import perf_counter

from .lexer import Lexer
from .parser import Parser
from .bytecode import Bytecode
from .compiler import Compiler, CompileError
from .vm import VakVM, VMError
from .errors import TranslationError, VakError, format_vak_error_with_suggestions
from .audit import emit_audit_event
from .branching import BranchActivationError
from .code_transformer import TransformResult, VakCodeTransformer
from .codex import CodexResult, build_default_codex
from .performance import VakPerformanceProfile, aggregate_stage_samples
from .rupantar import RupantarResult, VakyaRupantar

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
        deep_meaning_mode: bool = False,
    ):
        self.debug = False
        self.branch_runtime = None
        self.branch_registry = branch_registry
        self.deep_meaning_mode = deep_meaning_mode
        self.last_filename: str | None = None
        self.last_input_source: str = ""
        self.last_prepared_source: str = ""
        self.code_transformer = VakCodeTransformer(deep_meaning_mode=deep_meaning_mode)
        self.last_transform_result = TransformResult("", "", False, 0)
        if active_branches:
            registry = branch_registry
            if registry is None:
                from branches.registry import create_default_registry

                registry = create_default_registry()
            self.branch_registry = registry
            self.branch_runtime = registry.create_runtime(
                list(active_branches),
                include_defaults=True,
            )
        self.vm = VakVM(
            branch_runtime=self.branch_runtime,
            branch_registry=self.branch_registry,
        )
        self.codex = build_default_codex(
            active_branches=self.branch_runtime.active_names() if self.branch_runtime is not None else None,
            branch_registry=self.branch_registry,
            deep_meaning_mode=self.deep_meaning_mode,
        )

    def get_branch_report(self) -> dict[str, dict[str, Any]]:
        if self.branch_runtime is None:
            return {}
        return self.branch_runtime.report()

    def inspect_vm_stack(self) -> list[dict[str, Any]]:
        return self.vm.inspect_stack()

    def rupantar_source(
        self,
        source: str,
        *,
        filename: str | None = None,
    ) -> RupantarResult:
        active_names = None
        if self.branch_runtime is not None:
            active_names = self.branch_runtime.active_names()
        engine = VakyaRupantar(
            active_branches=active_names,
            branch_registry=self.branch_registry,
        )
        return engine.transform_source(source, source_path=filename)

    def codex_source(
        self,
        source: str,
        *,
        filename: str | None = None,
        page: str = "auto",
    ) -> CodexResult:
        return self.codex.transform_source(source, filename=filename, page=page)

    def error_context(self) -> dict[str, Any]:
        return {
            "frame": self.vm.current_frame,
            "globals": self.vm.globals,
            "builtins": self.vm.builtins,
            "filename": self.last_filename,
            "input_source": self.last_input_source,
            "prepared_source": self.last_prepared_source,
            "translation": {
                "language": self.last_transform_result.language,
                "confidence": self.last_transform_result.confidence,
                "transformed": self.last_transform_result.transformed,
                "replacements": self.last_transform_result.replacements,
                "changed_lines": list(self.last_transform_result.changed_lines),
                "features": list(self.last_transform_result.features),
                "blocked_reason": self.last_transform_result.blocked_reason,
                "blocked_line": self.last_transform_result.blocked_line,
                "original_source": self.last_transform_result.original_source,
                "transformed_source": self.last_transform_result.source,
            },
        }

    def prepare_source(self, source: str) -> str:
        self.last_input_source = source
        self.last_transform_result = self.code_transformer.transform(source)
        if self.last_transform_result.blocked_reason:
            raise TranslationError(
                self.last_transform_result.blocked_reason,
                self.last_transform_result.blocked_line,
            )
        self.last_prepared_source = self.last_transform_result.source
        return self.last_transform_result.source

    def translation_status_message(self) -> str | None:
        if self.last_transform_result.transformed:
            return "वाक्य-अनुवाद सफल"
        return None

    def transformed_source(self) -> str | None:
        if self.last_transform_result.transformed:
            return self.last_transform_result.source
        return None

    def _spawn_profile_interpreter(self) -> "VakInterpreter":
        active_names = (
            self.branch_runtime.active_names()
            if self.branch_runtime is not None
            else None
        )
        return VakInterpreter(
            active_branches=active_names,
            branch_registry=self.branch_registry,
            deep_meaning_mode=self.deep_meaning_mode,
        )

    def profile_source(
        self,
        source: str,
        *,
        filename: str | None = None,
        repeat: int = 3,
        execute: bool = True,
        source_prepared: bool = False,
    ) -> VakPerformanceProfile:
        iterations = max(int(repeat), 1)
        samples: dict[str, list[float]] = {
            "prepare": [],
            "lex": [],
            "parse": [],
            "compile": [],
        }
        if execute:
            samples["execute"] = []

        for _ in range(iterations):
            profiler = self._spawn_profile_interpreter()
            profiler.last_filename = filename

            prepared_source = source
            if not source_prepared:
                start = perf_counter()
                prepared_source = profiler.prepare_source(source)
                samples["prepare"].append((perf_counter() - start) * 1000.0)
            else:
                profiler.last_input_source = source
                profiler.last_prepared_source = source
                profiler.last_transform_result = TransformResult(source, source, False, 0)
                samples["prepare"].append(0.0)

            start = perf_counter()
            tokens = Lexer(prepared_source).tokenize()
            samples["lex"].append((perf_counter() - start) * 1000.0)

            start = perf_counter()
            parser = Parser(tokens)
            ast = parser.parse()
            if profiler.branch_runtime is not None:
                profiler.branch_runtime.on_program_parsed(
                    ast,
                    filename=filename,
                    interpreter=profiler,
                )
            samples["parse"].append((perf_counter() - start) * 1000.0)

            start = perf_counter()
            compiler = Compiler(
                branch_runtime=profiler.branch_runtime,
                source_path=filename,
            )
            bytecode = compiler.compile(ast)
            bytecode.source_path = filename
            samples["compile"].append((perf_counter() - start) * 1000.0)

            if execute:
                start = perf_counter()
                previous_suppress = profiler.vm.suppress_output
                profiler.vm.suppress_output = True
                try:
                    profiler.vm.run(bytecode)
                finally:
                    profiler.vm.suppress_output = previous_suppress
                samples["execute"].append((perf_counter() - start) * 1000.0)

        profile = aggregate_stage_samples("source", filename, iterations, samples)
        emit_audit_event(
            "vak.profile.source",
            filename or "<memory>",
            iterations,
            round(profile.total_ms, 6),
        )
        return profile

    def profile_import(
        self,
        module_name: str,
        *,
        filename: str | None = None,
        repeat: int = 3,
    ) -> VakPerformanceProfile:
        source = f"आयात {module_name}\n"
        profile = self.profile_source(
            source,
            filename=filename,
            repeat=repeat,
            execute=True,
            source_prepared=False,
        )
        payload = profile.payload()
        payload["mode"] = "import"
        imported = VakPerformanceProfile(
            mode="import",
            filename=filename or module_name,
            iterations=profile.iterations,
            stages=profile.stages,
            total_ms=profile.total_ms,
        )
        emit_audit_event(
            "vak.profile.import",
            str(module_name),
            repeat,
            round(imported.total_ms, 6),
        )
        return imported

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
        
    def run(
        self,
        source: str,
        debug: bool = False,
        filename: str | None = None,
        *,
        source_prepared: bool = False,
    ) -> any:
        """
        Execute VakyaLang source code.
        
        Pipeline:
        1. Lexical analysis (tokenization)
        2. Parsing (AST generation)
        3. Compilation (Bytecode generation)
        4. Execution (VM)
        """
        self.debug = debug
        self.last_filename = filename
        if not source_prepared:
            self.last_input_source = source
            self.last_prepared_source = ""
        else:
            self.last_prepared_source = source
        emit_audit_event("vak.interpreter.run.start", filename or "<memory>", debug)
        
        try:
            if not source_prepared:
                source = self.prepare_source(source)

            # Step 1: Lexical Analysis
            if debug:
                self._debug_print("=== Stage 1: Lexical Analysis ===")
                if self.last_transform_result.transformed:
                    self._debug_print("=== English → Vak Transformation ===")
                    self._debug_print(self.last_transform_result.source)
                    self._debug_print(
                        f"Changed lines: {list(self.last_transform_result.changed_lines)}"
                    )
                    self._debug_print(
                        f"Features: {list(self.last_transform_result.features)}"
                    )
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
            
    def compile_only(
        self,
        source: str,
        filename: str | None = None,
        *,
        source_prepared: bool = False,
    ) -> 'Bytecode':
        """Compile source to bytecode without executing."""
        emit_audit_event("vak.interpreter.compile.start", filename or "<memory>")
        self.last_filename = filename
        if not source_prepared:
            self.last_input_source = source
            self.last_prepared_source = ""
        else:
            self.last_prepared_source = source
        if not source_prepared:
            source = self.prepare_source(source)
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

    def hydrate_bytecode_functions(
        self,
        bytecode: Any,
        *,
        compiled_path: str | Path | None = None,
    ) -> Any:
        """
        Recover nested function/class bytecode tables for serialized .vakc files.

        This does not alter the bytecode wire format. It recompiles the original
        source when available and copies only the nested bytecode map needed for
        runtime call resolution.
        """
        if getattr(bytecode, "functions", None):
            return bytecode

        companion_path = None
        if compiled_path is not None:
            companion_path = Bytecode.companion_path(compiled_path)
        if companion_path is not None and companion_path.exists():
            try:
                companion = Bytecode.from_abi_json(
                    companion_path.read_text(encoding="utf-8")
                )
            except Exception:
                companion = None
            if companion is not None:
                self._merge_bytecode_metadata(bytecode, companion)
                if getattr(bytecode, "functions", None):
                    return bytecode

        source_candidate = self._resolve_bytecode_source_path(
            bytecode,
            compiled_path=compiled_path,
        )
        if source_candidate is None:
            return bytecode

        try:
            source = source_candidate.read_text(encoding="utf-8")
        except OSError:
            return bytecode

        hydrated = self.compile_only(
            source,
            filename=str(source_candidate),
            source_prepared=False,
        )
        if getattr(hydrated, "functions", None):
            self._merge_bytecode_metadata(bytecode, hydrated)
        return bytecode

    def _resolve_bytecode_source_path(
        self,
        bytecode: Any,
        *,
        compiled_path: str | Path | None = None,
    ) -> Path | None:
        candidates: list[Path] = []

        source_path = getattr(bytecode, "source_path", None)
        if source_path:
            source_candidate = Path(source_path)
            candidates.append(source_candidate)
            if compiled_path is not None and not source_candidate.is_absolute():
                candidates.append(Path(compiled_path).resolve().parent / source_candidate)

        if compiled_path is not None:
            candidates.append(Path(compiled_path).resolve().with_suffix(".vak"))

        for candidate in candidates:
            if candidate.exists():
                return candidate
        return None

    def _merge_bytecode_metadata(self, target: Any, source: Any) -> None:
        if not getattr(target, "functions", None) and getattr(source, "functions", None):
            target.functions = dict(source.functions)
        if not getattr(target, "source_path", None) and getattr(source, "source_path", None):
            target.source_path = source.source_path
        if not getattr(target, "param_names", None) and getattr(source, "param_names", None):
            target.param_names = list(source.param_names)
        if not getattr(target, "defaults", None) and getattr(source, "defaults", None):
            target.defaults = list(source.defaults)
        if not getattr(target, "varargs_name", None) and getattr(source, "varargs_name", None):
            target.varargs_name = source.varargs_name
        if not getattr(target, "type_hints", None) and getattr(source, "type_hints", None):
            target.type_hints = dict(source.type_hints)
        if not getattr(target, "vibhakti_signature", None) and getattr(source, "vibhakti_signature", None):
            target.vibhakti_signature = source.vibhakti_signature

    def _read_repl_source(self) -> str | None:
        line = input("वाक्> ")
        stripped = line.strip()
        if stripped in {'exit', 'quit', 'विराम'}:
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
            print("Type 'debug' to toggle debug mode, 'exit' or 'विराम' to quit")
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
                translation_message = self.translation_status_message()
                if translation_message:
                    print(translation_message)
                if result is not None:
                    print(f"=> {result}")
                    
            except KeyboardInterrupt:
                print("\nUse 'exit' or 'विराम' to quit")
            except EOFError:
                break
            except Exception as e:
                print(format_vak_error_with_suggestions(e, self.error_context()))
                
        print("\nनमस्ते (Goodbye)!")
