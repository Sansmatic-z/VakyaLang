import re
with open("runtime/src/vm.py", "r") as f:
    content = f.read()

# Fix indentation of the second CONTAINS implementation
pattern = r'elif op == OpCode\.CONTAINS\.value:\n            b = frame\.stack\.pop\(\)\n            a = frame\.stack\.pop\(\)\n            frame\.stack\.append\(a in b\)\n            frame\.pc \+= 1'
replacement = """elif op == OpCode.CONTAINS.value:
            b = frame.stack.pop()
            a = frame.stack.pop()
            frame.stack.append(a in b)
            frame.pc += 1"""

content = re.sub(pattern, replacement, content)

with open("runtime/src/vm.py", "w") as f:
    f.write(content)
