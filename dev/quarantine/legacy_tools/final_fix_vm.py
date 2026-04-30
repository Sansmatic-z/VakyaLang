import os

with open("runtime/src/vm.py", "r") as f:
    lines = f.readlines()

new_lines = []
for i, line in enumerate(lines):
    ln = i + 1
    if ln >= 726 and ln <= 745:
        # Correctly indent the regular function call block
        stripped = line.strip()
        if stripped:
            if stripped.startswith("if") or stripped.startswith("else") or stripped.startswith("for") or stripped.startswith("frame.pc") or stripped.startswith("self.frames") or stripped.startswith("self.current_frame") or stripped.startswith("frame =") or stripped.startswith("code =") or stripped.startswith("constants =") or stripped.startswith("continue"):
                new_lines.append("                        " + stripped + "\n")
            elif stripped.startswith("new_frame") or stripped.startswith("func_bc"):
                new_lines.append("                        " + stripped + "\n")
            else:
                new_lines.append("                        " + stripped + "\n")
        else:
            new_lines.append(line)
    elif ln == 746:
        new_lines.append("            elif op == OpCode.RETURN.value:\n")
    else:
        new_lines.append(line)

with open("runtime/src/vm.py", "w") as f:
    f.writelines(new_lines)
