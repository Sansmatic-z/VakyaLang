import re

with open("vm_temp.py", "r") as f:
    lines = f.readlines()

new_lines = []
skip = False
for i, line in enumerate(lines):
    if "elif op == OpCode.CALL.value:" in line:
        # Reconstruct OP_CALL block
        new_lines.append(line)
        new_lines.append("                argc = code[frame.pc + 1]\n")
        new_lines.append("                args = [self._pop() for _ in range(argc)]\n")
        new_lines.append("                args.reverse()\n")
        new_lines.append("                func = self._pop()\n")
        new_lines.append("\n")
        new_lines.append("                if isinstance(func, tuple) and func[0] == 'function':\n")
        new_lines.append("                    func_name = func[1]\n")
        new_lines.append("                    if self.jit_enabled and self.jit:\n")
        new_lines.append("                        self.jit.track_call(func_name)\n")
        new_lines.append("                        if func_name in self.jit.compiled_functions:\n")
        new_lines.append("                            compiled_func = self.jit.compiled_functions[func_name]\n")
        new_lines.append("                            try:\n")
        new_lines.append("                                result = compiled_func.execute(self.globals, *args)\n")
        new_lines.append("                                self._push(result)\n")
        new_lines.append("                                frame.pc += 2\n")
        new_lines.append("                                continue\n")
        new_lines.append("                            except Exception as e:\n")
        new_lines.append("                                trace = self._format_stack_trace()\n")
        new_lines.append('                                raise VMError(f"Internal VM Crash: {e}\\n{trace}")\n')
        new_lines.append("\n")
        new_lines.append("                    func_bc = frame.bytecode.functions.get(func_name)\n")
        new_lines.append("                    if not func_bc:\n")
        new_lines.append("                        func_bc = self.frames[0].bytecode.functions.get(func_name)\n")
        new_lines.append("                    if func_bc:\n")
        new_lines.append("                        new_frame = CallFrame(func_bc)\n")
        new_lines.append("                        for j in range(min(len(args), func_bc.num_params)):\n")
        new_lines.append("                            if j < len(new_frame.locals): new_frame.locals[j] = args[j]\n")
        new_lines.append("                        if func_bc.varargs_name and func_bc.num_params < len(new_frame.locals):\n")
        new_lines.append("                            new_frame.locals[func_bc.num_params] = list(args[func_bc.num_params:])\n")
        new_lines.append("                        frame.pc += 2\n")
        new_lines.append("                        self.frames.append(new_frame)\n")
        new_lines.append("                        self.current_frame = new_frame\n")
        new_lines.append("                        frame = new_frame\n")
        new_lines.append("                        code = frame.bytecode.code\n")
        new_lines.append("                        constants = frame.bytecode.constants\n")
        new_lines.append("                        frame.pc = 0\n")
        new_lines.append("                        continue\n")
        new_lines.append("                    else:\n")
        new_lines.append('                        raise VMError(f"Function not found: {func_name}")\n')
        
        # Skip original broken block until next opcode
        skip = True
        continue
    
    if skip:
        if "elif op == OpCode." in line and "CALL.value" not in line:
            skip = False
        else:
            continue
            
    new_lines.append(line)

with open("runtime/src/vm.py", "w") as f:
    f.writelines(new_lines)
