import re
with open("runtime/src/vm.py", "r") as f:
    content = f.read()

run_method = """
    def run(self, bytecode: Bytecode) -> Any:
        \"\"\"Execute bytecode and return result.\"\"\"
        frame = CallFrame(bytecode)
        self.frames = [frame]
        self.current_frame = frame
        
        try:
            return self._execute()
        except VMError:
            raise
        except Exception as e:
            import traceback; traceback.print_exc()
            trace = self._format_stack_trace()
            raise VMError(f"Internal VM Crash: {e}\\n{trace}")

    def _pop(self) -> Any:
        \"\"\"Pop a value from the current frame's stack with safety check.\"\"\"
        if not self.current_frame or not self.current_frame.stack:
            raise VMError("Stack Underflow: Attempted to pop from an empty stack")
        return self.current_frame.stack.pop()

    def _push(self, value: Any) -> None:
        \"\"\"Push a value onto the current frame's stack.\"\"\"
        if self.current_frame is not None:
            self.current_frame.stack.append(value)
"""

content = content.replace("    def _execute(self) -> Any:", run_method + "\n    def _execute(self) -> Any:")

with open("runtime/src/vm.py", "w") as f:
    f.write(content)
