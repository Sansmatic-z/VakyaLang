with open("runtime/src/vm.py", "r") as f:
    content = f.read()

content = content.replace("# op_name = OPCODE_NAMES.get(op, f\"UNKNOWN({op})\")", "op_name = OPCODE_NAMES.get(op, f\"UNKNOWN({op})\")")
content = content.replace("# print(f\"TRACE: pc={frame.pc:04d} op={op_name:15} stack={frame.stack}\")", "print(f\"TRACE: pc={frame.pc:04d} op={op_name:15} stack={frame.stack}\")")

with open("runtime/src/vm.py", "w") as f:
    f.write(content)
