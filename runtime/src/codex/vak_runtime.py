from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from ..compiler import Compiler
from ..lexer import Lexer
from ..parser import Parser
from ..vm import Cell, UNSET, VakModule, VakVM


class VakCodexModuleRuntime:
    """Load and invoke a real .vak Codex page module."""

    def __init__(
        self,
        module_path: str | Path,
        *,
        module_name: str | None = None,
        active_branches: list[str] | None = None,
        branch_registry: Any = None,
    ):
        self.module_path = Path(module_path).resolve()
        self.module_name = module_name or self.module_path.stem
        self.active_branches = list(active_branches or [])
        self.branch_registry = branch_registry
        self.vm = VakVM(
            active_branches=self.active_branches or None,
            branch_registry=self.branch_registry,
        )
        self.vm.suppress_output = True
        self._module: VakModule | None = None

    def load(self) -> VakModule:
        if self._module is not None:
            return self._module

        source = self.module_path.read_text(encoding="utf-8")
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        program = parser.parse()
        compiler = Compiler(
            branch_runtime=self.vm.branch_runtime,
            source_path=str(self.module_path),
        )
        module_bytecode = compiler.compile(program)
        module_bytecode.source_path = str(self.module_path)
        defined_function_names = set(module_bytecode.functions.keys())

        module_env: dict[str, Any] = {"__bytecode__": module_bytecode}
        for fn_name in defined_function_names:
            fn_bc = module_bytecode.functions[fn_name]
            is_async = getattr(fn_bc, "is_async", False)
            module_env[fn_name] = ("function", fn_name, module_env, is_async)

        cache_key = os.path.normcase(os.path.abspath(str(self.module_path)))
        mod_obj = VakModule(self.module_name, {})
        self.vm.module_cache[cache_key] = mod_obj

        module_vm = VakVM(
            active_branches=self.active_branches or None,
            branch_registry=self.branch_registry,
        )
        module_vm.suppress_output = True
        module_vm.module_cache = self.vm.module_cache
        module_vm.run(module_bytecode)

        exported_attrs: dict[str, Any] = {}
        exportable_names = {
            name
            for name in module_bytecode.var_names
            if not self.vm._is_internal_binding_name(name)
        }

        for name, value in module_vm.globals.items():
            if self.vm._is_internal_binding_name(name):
                continue
            exported_attrs[name] = self.vm._unwrap_cell(value)
        module_env.update(module_vm.globals)

        module_frame = module_vm.frames[0] if module_vm.frames else module_vm.current_frame
        if module_frame and hasattr(module_frame, "locals"):
            for index, name in enumerate(module_bytecode.var_names):
                if index < len(module_frame.locals) and module_frame.locals[index] is not UNSET:
                    raw_value = module_frame.locals[index]
                    module_env[name] = raw_value
                    if not self.vm._is_internal_binding_name(name):
                        exported_attrs[name] = self.vm._unwrap_cell(raw_value)

        if module_frame and hasattr(module_frame, "locals"):
            for index, name in enumerate(module_bytecode.var_names):
                if index >= len(module_frame.locals):
                    continue
                value = module_frame.locals[index]
                if isinstance(value, Cell):
                    value = value.value
                if isinstance(value, tuple) and len(value) >= 3 and value[0] == "function":
                    closure_env = value[2]
                    if isinstance(closure_env, dict):
                        closure_env["__bytecode__"] = module_bytecode

        for fn_name in defined_function_names:
            if fn_name not in exportable_names:
                continue
            fn_bc = module_bytecode.functions[fn_name]
            is_async = getattr(fn_bc, "is_async", False)
            module_env[fn_name] = ("function", fn_name, module_env, is_async)
            exported_attrs[fn_name] = ("function", fn_name, module_env, is_async)

        mod_obj.name = self.module_name
        mod_obj.attrs.clear()
        mod_obj.attrs.update(exported_attrs)
        self._module = mod_obj
        return mod_obj

    def attrs(self) -> dict[str, Any]:
        return self.load().attrs

    def get_export(self, name: str) -> Any:
        return self.attrs().get(name)

    def invoke(self, export_name: str, *args: Any, **kwargs: Any) -> Any:
        func = self.get_export(export_name)
        if func is None:
            raise KeyError(f"Vak Codex export not found: {export_name}")
        return self.vm._invoke_runtime_callable(func, *args, **kwargs)
