import re
with open("runtime/src/vm.py", "r") as f:
    content = f.read()

# Add CONTAINS implementation to both loops
if "OpCode.CONTAINS.value" not in content:
    content = content.replace("elif op == OpCode.GTE.value:", "elif op == OpCode.CONTAINS.value:\n                b = self._pop()\n                a = self._pop()\n                frame.stack.append(a in b)\n                frame.pc += 1\n\n            elif op == OpCode.GTE.value:")
    content = content.replace("elif op == OpCode.GTE.value:", "elif op == OpCode.CONTAINS.value:\n            b = frame.stack.pop()\n            a = frame.stack.pop()\n            frame.stack.append(a in b)\n            frame.pc += 1\n\n        elif op == OpCode.GTE.value:", 1) # Only first occurrence after the previous replace

with open("runtime/src/vm.py", "w") as f:
    f.write(content)
