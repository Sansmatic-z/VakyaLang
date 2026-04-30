import re
with open("runtime/src/interpreter.py", "r") as f:
    content = f.read()

content = content.replace("except Exception as e:", "# except Exception as e:")
content = content.replace("raise VakError(f\"Execution error: {e}\")", "# raise VakError(f\"Execution error: {e}\")")

with open("runtime/src/interpreter.py", "w") as f:
    f.write(content)
