# वाक् भाषा - पायथन ब्रिज मॉड्यूल
# Vak Language - Python Bridge Module
# Enables VakyaLang to import and call Python libraries

"""
Python Bridge for VakyaLang
═══════════════════════════════════════════════════════════════
This module provides seamless interoperability between VakyaLang
and Python libraries. It allows VakyaLang code to:

1. Import any Python module using पायथन_आयात()
2. Call Python functions with automatic type conversion
3. Access Python classes and create instances
4. Handle exceptions across language boundaries

Usage in VakyaLang:
    आयात पायथन_ब्रिज
    
    # Import Python module
    चर गणित = पायथन_आयात("math")
    चर परिणाम = गणित.sqrt(१६)
    
    # Import with alias
    चर np = पायथन_आयात("numpy")
    चर सरणी = np.array([१, २, ३])
"""

import sys
import importlib
import inspect
from typing import Any, Dict, List, Callable, Optional
from dataclasses import dataclass


class PythonBridgeError(Exception):
    """Error in Python bridge operations"""
    pass


@dataclass
class PythonClassWrapper:
    """Wrapper for Python classes"""
    cls: type
    module_name: str
    
    def __call__(self, *args, **kwargs):
        """Create instance of Python class"""
        try:
            instance = self.cls(*args, **kwargs)
            return PythonObjectWrapper(instance, self.module_name)
        except Exception as e:
            raise PythonBridgeError(f"Error creating {self.cls.__name__}: {e}")


class PythonObjectWrapper:
    """Wrapper for Python objects to enable dot notation access"""
    
    def __init__(self, obj: Any, module_name: str = "python"):
        self._obj = obj
        self._module_name = module_name
        self._cache: Dict[str, Any] = {}
    
    def __getattr__(self, name: str) -> Any:
        """Get attribute or method from wrapped object"""
        if name.startswith('_'):
            raise AttributeError(f"Cannot access private attribute: {name}")
        
        if name in self._cache:
            return self._cache[name]
        
        try:
            attr = getattr(self._obj, name)
            
            # Cache the attribute
            self._cache[name] = attr
            
            # If it's callable, wrap it
            if callable(attr):
                return WrappedCallable(attr, self._module_name)
            
            # If it's an object, wrap it
            if not isinstance(attr, (int, float, str, bool, type(None), list, dict)):
                return PythonObjectWrapper(attr, self._module_name)
            
            return attr
            
        except AttributeError:
            raise PythonBridgeError(f"Attribute '{name}' not found in {self._module_name}")
        except Exception as e:
            raise PythonBridgeError(f"Error accessing '{name}': {e}")
    
    def __repr__(self) -> str:
        return f"PythonObject({self._module_name}.{type(self._obj).__name__})"
    
    def __str__(self) -> str:
        return str(self._obj)
    
    def __call__(self, *args, **kwargs):
        """Call the object if it's callable"""
        if callable(self._obj):
            try:
                result = self._obj(*convert_to_python(args), **convert_to_python(kwargs))
                return convert_to_vak(result)
            except Exception as e:
                raise PythonBridgeError(f"Error calling {self._module_name}: {e}")
        raise PythonBridgeError(f"Object {self._module_name} is not callable")


class WrappedCallable:
    """Wrapper for Python callable objects"""
    
    def __init__(self, func, module_name: str):
        self._func = func
        self._module_name = module_name
        self.__name__ = getattr(func, '__name__', 'unknown')

    def __getattr__(self, name: str):
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
            raise Exception(f"Attribute '{name}' not found")
    
    def __call__(self, *args, **kwargs):
        """Call the wrapped function with type conversion"""
        try:
            py_args = convert_to_python(args)
            py_kwargs = convert_to_python(kwargs)
            result = self._func(*py_args, **py_kwargs)
            return convert_to_vak(result)
        except Exception as e:
            raise Exception(f"Error in {self._module_name}.{self.__name__}: {e}")
    
    def __repr__(self) -> str:
        return f"PythonFunction({self._module_name}.{self.__name__})"

def convert_to_python(value: Any) -> Any:
    """Convert VakyaLang types to Python types"""
    if value is None:
        return None
    
    if isinstance(value, (int, float, str, bool)):
        return value
    
    if isinstance(value, list):
        return [convert_to_python(item) for item in value]
    
    if isinstance(value, dict):
        return {convert_to_python(k): convert_to_python(v) for k, v in value.items()}
    
    # Unwrap Python objects
    if isinstance(value, PythonObjectWrapper):
        return value._obj
    
    if isinstance(value, WrappedCallable):
        return value._func
    
    return value


def convert_to_vak(value: Any) -> Any:
    """Convert Python types to VakyaLang types"""
    if value is None:
        return None
    
    if isinstance(value, (int, float, str, bool)):
        return value
    
    if isinstance(value, (list, tuple)):
        return [convert_to_vak(item) for item in value]
    
    if isinstance(value, dict):
        return {convert_to_vak(k): convert_to_vak(v) for k, v in value.items()}
    
    if isinstance(value, type):
        # Return class wrapper
        return PythonClassWrapper(value, "python")
    
    if callable(value):
        return WrappedCallable(value, "python")
    
    # Wrap Python objects
    return PythonObjectWrapper(value, "python")


# ── Main Bridge Functions ─────────────────────────────────────────────────────

def पायथन_आयात(*args) -> Any:
    module_name = args[-1]
    """
    Import a Python module and return a wrapped version.
    
    Usage in VakyaLang:
        चर math = पायथन_आयात("math")
        चर result = math.sqrt(16)
    
    Args:
        module_name: Name of the Python module to import
    
    Returns:
        Wrapped module with all functions/classes accessible
    """
    try:
        module = importlib.import_module(module_name)
        return PythonObjectWrapper(module, module_name)
    except ImportError as e:
        raise PythonBridgeError(f"Cannot import module '{module_name}': {e}")
    except Exception as e:
        raise PythonBridgeError(f"Error importing '{module_name}': {e}")


def पायथन_चलाओ(*args) -> Any:
    code = args[0]
    globals_dict = args[1] if len(args) > 1 else None
    """
    Execute arbitrary Python code and return result.
    
    Usage:
        result = पायथन_चलाओ("import math; math.sqrt(16)")
    
    Args:
        code: Python code string to execute
        globals_dict: Optional globals dictionary
    
    Returns:
        Result of code execution (converted to VakyaLang types)
    """
    try:
        if globals_dict is None:
            globals_dict = {}
        
        # Execute the code
        exec(code, globals_dict)
        
        # Return the globals (can access results from there)
        return PythonObjectWrapper(globals_dict, "exec")
        
    except Exception as e:
        raise PythonBridgeError(f"Error executing Python code: {e}")


def पायथन_मूल्यांकन(*args) -> Any:
    expression = args[-1]
    """
    Evaluate a Python expression and return result.
    
    Usage:
        result = पायथन_मूल्यांकन("math.sqrt(16) + 5")
    
    Args:
        expression: Python expression string
    
    Returns:
        Result of evaluation (converted to VakyaLang types)
    """
    try:
        result = eval(expression)
        return convert_to_vak(result)
    except Exception as e:
        raise PythonBridgeError(f"Error evaluating '{expression}': {e}")


# ── Convenience Functions ─────────────────────────────────────────────────────

def requests_get(url: str, **kwargs) -> Any:
    """Quick HTTP GET request using requests library"""
    try:
        requests = importlib.import_module("requests")
        response = requests.get(url, **kwargs)
        return PythonObjectWrapper(response, "requests.Response")
    except ImportError:
        raise PythonBridgeError("requests library not installed. Run: pip install requests")
    except Exception as e:
        raise PythonBridgeError(f"HTTP GET failed: {e}")


def json_loads(json_string: str) -> Any:
    """Parse JSON string to Python dict/list"""
    try:
        import json
        result = json.loads(json_string)
        return convert_to_vak(result)
    except Exception as e:
        raise PythonBridgeError(f"JSON parse error: {e}")


def json_dumps(obj: Any, **kwargs) -> str:
    """Convert Python object to JSON string"""
    try:
        import json
        py_obj = convert_to_python(obj)
        return json.dumps(py_obj, **kwargs)
    except Exception as e:
        raise PythonBridgeError(f"JSON dump error: {e}")


# ── Module Info ───────────────────────────────────────────────────────────────

def पायथन_संस्करण() -> str:
    """Get Python version string"""
    return sys.version


def पायथन_मॉड्यूल_सूची() -> List[str]:
    """Get list of available Python modules"""
    return list(sys.modules.keys())


def पायथन_मॉड्यूल_जानकारी(module_name: str) -> Dict[str, Any]:
    """Get information about a Python module"""
    try:
        module = importlib.import_module(module_name)
        
        info = {
            "name": module.__name__,
            "file": getattr(module, '__file__', 'built-in'),
            "doc": getattr(module, '__doc__', None),
            "version": getattr(module, '__version__', 'unknown'),
        }
        
        # Get public attributes
        public_attrs = []
        for name in dir(module):
            if not name.startswith('_'):
                public_attrs.append(name)
        
        info["attributes"] = public_attrs[:100]  # Limit to first 100
        
        return info
        
    except Exception as e:
        raise PythonBridgeError(f"Error getting module info: {e}")


# ── Initialization ────────────────────────────────────────────────────────────

def main():
    """CLI interface for Python bridge"""
    print("🐍 वाक् पायथन ब्रिज (Vak Python Bridge)")
    print("=" * 50)
    print(f"Python Version: {पायथन_संस्करण()}")
    print(f"Loaded Modules: {len(पायथन_मॉड्यूल_सूची())}")
    print("\nUsage:")
    print("  from py_bridge import पायथन_आयात")
    print('  math = पायथन_आयात("math")')
    print("  result = math.sqrt(16)")
    print("=" * 50)


if __name__ == "__main__":
    main()
