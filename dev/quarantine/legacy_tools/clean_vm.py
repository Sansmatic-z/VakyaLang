import re
with open("runtime/src/vm.py", "r") as f:
    content = f.read()

# Fix the double except block
content = re.sub(r'except Exception as e:.*?    def _execute\(self\) -> Any:', 
                 '            except Exception as e:\n                import traceback; traceback.print_exc()\n                trace = self._format_stack_trace()\n                raise VMError(f"Internal VM Crash: {e}\\n{trace}")\n\n    def _execute(self) -> Any:', 
                 content, flags=re.DOTALL)

with open("runtime/src/vm.py", "w") as f:
    f.write(content)
