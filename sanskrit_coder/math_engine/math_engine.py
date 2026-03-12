# Sanskrit Coder — Copyright (c) 2026 Raj Mitra. All Rights Reserved.
# Part of VakyaLang project (https://github.com/Sansmatic-z/VakyaLang)
# Licensed under GNU AGPL v3.0 — see root LICENSE_AGPL and NOTICE.
# Any use or modification must preserve this header and include NOTICE.

"""
Sanskrit Math Engine
संस्कृत गणित इन्जिन्
"""

import re
import math
from typing import Union, Dict, List, Optional


class SanskritMathEngine:
    """Sanskrit Mathematics Engine"""
    
    FORMULAS = {
        'F = ma': {
            'sanskrit': 'बलम् = द्रव्यमानम् × त्वरणम्',
            'name': "Newton's Second Law",
            'sanskrit_name': 'न्यूटनस्य द्वितीय नियमः',
            'variables': {
                'F': {'name': 'Force', 'sanskrit': 'बलम्', 'unit': 'Newtons'},
                'm': {'name': 'Mass', 'sanskrit': 'द्रव्यमानम्', 'unit': 'kg'},
                'a': {'name': 'Acceleration', 'sanskrit': 'त्वरणम्', 'unit': 'm/s²'},
            },
        },
        'E = mc^2': {
            'sanskrit': 'शक्तिः = द्रव्यमानम् × प्रकाशवेगः²',
            'name': "Mass-Energy Equivalence",
            'sanskrit_name': 'द्रव्यमान-शक्ति समतुल्यता',
            'variables': {
                'E': {'name': 'Energy', 'sanskrit': 'शक्तिः', 'unit': 'Joules'},
                'm': {'name': 'Mass', 'sanskrit': 'द्रव्यमानम्', 'unit': 'kg'},
                'c': {'name': 'Speed of Light', 'sanskrit': 'प्रकाशवेगः', 'unit': 'm/s'},
            },
        },
        'A = πr^2': {
            'sanskrit': 'वृत्तस्य क्षेत्रफलम् = π × त्रिज्या²',
            'name': 'Area of Circle',
            'sanskrit_name': 'वृत्तस्य क्षेत्रफलम्',
            'variables': {
                'A': {'name': 'Area', 'sanskrit': 'क्षेत्रफलम्', 'unit': 'm²'},
                'r': {'name': 'Radius', 'sanskrit': 'त्रिज्या', 'unit': 'm'},
            },
        },
    }
    
    def __init__(self):
        pass
    
    def calculate(self, expression: str) -> Union[int, float]:
        """Calculate mathematical expression"""
        try:
            expression = expression.strip()
            expression = expression.replace('×', '*')
            expression = expression.replace('÷', '/')
            expression = expression.replace('^', '**')
            
            allowed_names = {'math': math, 'sqrt': math.sqrt, 'pi': math.pi}
            result = eval(expression, {"__builtins__": {}}, allowed_names)
            return result
        except ZeroDivisionError:
            raise ValueError("शून्येन विभाजनम् असम्भवम् (Division by zero)")
        except Exception as e:
            raise ValueError(f"गणना त्रुटि: {str(e)}")
    
    def solve_equation(self, equation: str) -> str:
        """Solve algebraic equation"""
        try:
            equation = equation.replace(' ', '')
            if '=' not in equation:
                raise ValueError("समीकरणे '=' नास्ति")
            left, right = equation.split('=')
            x_match = re.search(r'(\d*)x', left)
            if x_match:
                a_str = x_match.group(1)
                a = int(a_str) if a_str else 1
                left_simplified = left.replace(f'{a_str}x', '0')
                b = eval(left_simplified) if left_simplified.strip() else 0
                c = eval(right)
                x = (c - b) / a
                if x == int(x):
                    return f"x = {int(x)}"
                return f"x = {x}"
            left_val = eval(left)
            right_val = eval(right)
            if left_val == right_val:
                return "सत्यम् (True)"
            else:
                return "असत्यम् (False)"
        except Exception as e:
            raise ValueError(f"समाधानम् असमर्थम्: {str(e)}")
    
    def lookup_formula(self, query: str) -> str:
        """Lookup formula by name or variables"""
        query_lower = query.lower()
        for formula, info in self.FORMULAS.items():
            if query_lower in formula.lower():
                return self._format_formula(formula, info)
            if query_lower in info['name'].lower():
                return self._format_formula(formula, info)
            for var, var_info in info['variables'].items():
                if query_lower in var_info['name'].lower():
                    return self._format_formula(formula, info)
        return f"सूत्रं न लब्धम्: {query}"
    
    def _format_formula(self, formula: str, info: Dict) -> str:
        result = f"सूत्रम् (Formula): {formula}\n"
        result += f"संस्कृतम् (Sanskrit): {info['sanskrit']}\n"
        result += f"नाम (Name): {info['name']}\n\n"
        result += "चराः (Variables):\n"
        for var, var_info in info['variables'].items():
            result += f"  {var} = {var_info['name']} ({var_info['sanskrit']}) - {var_info['unit']}\n"
        return result
    
    def convert_units(self, value: str, from_unit: str, to_unit: str) -> str:
        """Convert between units"""
        try:
            val = float(value)
            conversions = {'m': 1, 'km': 1000, 'cm': 0.01, 'mm': 0.001, 'kg': 1, 'g': 0.001, 's': 1, 'min': 60, 'h': 3600}
            from_base = conversions.get(from_unit.lower(), 1)
            to_base = conversions.get(to_unit.lower(), 1)
            result = val * from_base / to_base
            return f"{val} {from_unit} = {result} {to_unit}"
        except Exception as e:
            return f"परिवर्तनम् असमर्थम्: {str(e)}"


