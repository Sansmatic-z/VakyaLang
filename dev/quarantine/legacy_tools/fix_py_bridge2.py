with open("runtime/stdlib/py_bridge.py", "r") as f:
    content = f.read()

# Fix __getattr__ recursion
safe_getattr = """    def __getattr__(self, name: str) -> Any:
        if name in ['_func', '_module_name', '__name__', '__class__']:
            raise AttributeError()
        try:
            attr = getattr(self._func, name)
            if callable(attr):
                return WrappedCallable(attr, self._module_name)
            if not isinstance(attr, (int, float, str, bool, type(None), list, dict)):
                return PythonObjectWrapper(attr, self._module_name)
            return attr
        except AttributeError:
            raise PythonBridgeError(f"Attribute '{name}' not found in {self._module_name}")
"""
content = content.replace("    def __getattr__(self, name: str) -> Any:\n        try:\n            attr = getattr(self._func, name)\n            if callable(attr):\n                return WrappedCallable(attr, self._module_name)\n            if not isinstance(attr, (int, float, str, bool, type(None), list, dict)):\n                return PythonObjectWrapper(attr, self._module_name)\n            return attr\n        except AttributeError:\n            raise PythonBridgeError(f\"Attribute '{name}' not found in {self._module_name}.{self.__name__}\")\n", safe_getattr)

with open("runtime/stdlib/py_bridge.py", "w") as f:
    f.write(content)
