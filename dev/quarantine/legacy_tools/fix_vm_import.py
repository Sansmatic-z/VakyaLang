import re

with open("runtime/src/vm.py", "r") as f:
    content = f.read()

# Fix module execution to properly copy module functions to the main VM's bytecode object
pattern = r'# Extract exported values\n\s+exported_attrs = module_vm\.globals\.copy\(\)\n\s+module_obj = VakModule\(module_name, exported_attrs\)'
replacement = """# Extract exported values
                exported_attrs = module_vm.globals.copy()
                module_obj = VakModule(module_name, exported_attrs)
                
                # Copy module functions to the global bytecode function dictionary
                # so they can be looked up when called via module_obj.func_name
                if self.frames and hasattr(self.frames[0], 'bytecode'):
                    for func_name, func_bc in module_bytecode.functions.items():
                        self.frames[0].bytecode.functions[func_name] = func_bc
"""

content = re.sub(pattern, replacement, content)

with open("runtime/src/vm.py", "w") as f:
    f.write(content)
