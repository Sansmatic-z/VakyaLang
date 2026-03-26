import re
with open("runtime/src/vm.py", "r") as f:
    content = f.read()

# Add traceback print to the general exception handler
pattern = r'(            except Exception as e:)\n(                import traceback; traceback\.print_exc\(\)\n)?(                trace = self\._format_stack_trace\(\)\n)?(                raise VMError\(f"Internal VM Crash: \{e\}\\n\{trace\}"\))'
replacement = r'\1\n                import traceback; traceback.print_exc()\n                trace = self._format_stack_trace()\n                raise VMError(f"Internal VM Crash: {e}\\n{trace}")'

# If pattern not found, try a simpler one
if not re.search(pattern, content):
    content = content.replace("            except Exception as e:", "            except Exception as e:\n                import traceback; traceback.print_exc()")

with open("runtime/src/vm.py", "w") as f:
    f.write(content)
