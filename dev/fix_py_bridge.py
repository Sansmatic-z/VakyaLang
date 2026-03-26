with open("runtime/stdlib/py_bridge.py", "r") as f:
    content = f.read()

# Add __getattr__ to WrappedCallable
new_method = """    def __getattr__(self, name: str) -> Any:
        try:
            attr = getattr(self._func, name)
            if callable(attr):
                return WrappedCallable(attr, self._module_name)
            if not isinstance(attr, (int, float, str, bool, type(None), list, dict)):
                return PythonObjectWrapper(attr, self._module_name)
            return attr
        except AttributeError:
            raise PythonBridgeError(f"Attribute '{name}' not found in {self._module_name}.{self.__name__}")
"""

target = "    def __repr__(self) -> str:"
content = content.replace(target, new_method + "\n" + target)

with open("runtime/stdlib/py_bridge.py", "w") as f:
    f.write(content)
