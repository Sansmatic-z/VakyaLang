# संस्कृत-कोडकः - मुख्य इन्जिन्
# *Visionary RM (Raj Mitra)* ⚡
# *"संस्कृतम् अमरम् भवतु"* 🔥

"""
Sanskrit Coder - Main Engine Implementation
"""

import sys
import os
from typing import Union, Dict, List, Any

# Add paths
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'numbers'))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'grammar'))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'math_engine'))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logic_engine'))

from translator import SanskritTranslator
from numbers import SanskritNumbers
from grammar import SanskritGrammar
from math_engine import SanskritMathEngine
from logic_engine import SanskritLogicEngine


class SanskritEngine:
    """Main Sanskrit Execution Engine"""
    
    def __init__(self):
        """Initialize engine"""
        self.translator = SanskritTranslator()
        self.numbers = SanskritNumbers()
        self.grammar = SanskritGrammar()
        self.math = SanskritMathEngine()
        self.logic = SanskritLogicEngine()
        self.language = 'sanskrit'
        
        # Command mappings - use ASCII method names
        self.commands = {
            'गणय': self.calculate,
            'calculate': self.calculate,
            'समाधत्स्व': self.solve,
            'solve': self.solve,
            'पश्य': self.show,
            'show': self.show,
            'अन्वेषय': self.search,
            'search': self.search,
            'परिवर्तय': self.convert,
            'convert': self.convert,
        }
    
    def calculate(self, expression: str) -> str:
        """Calculate mathematical expression"""
        try:
            if self.translator.is_sanskrit(expression):
                expr_en = self.translator.sanskrit_to_english_math(expression)
            else:
                expr_en = expression
            
            result = self.math.calculate(expr_en)
            
            if self.language == 'sanskrit':
                sanskrit_num = self.numbers.number_to_sanskrit(result)
                return f"{result} ({sanskrit_num})"
            return str(result)
        except Exception as e:
            if self.language == 'sanskrit':
                return f"त्रुटि: गणना असमर्थम् - {str(e)}"
            return f"Error: Cannot calculate - {str(e)}"
    
    def solve(self, equation: str) -> str:
        """Solve equation"""
        try:
            if self.translator.is_sanskrit(equation):
                eq_en = self.translator.sanskrit_to_english_math(equation)
            else:
                eq_en = equation
            
            result = self.math.solve_equation(eq_en)
            
            if self.language == 'sanskrit':
                return self.translator.english_to_sanskrit(result)
            return result
        except Exception as e:
            if self.language == 'sanskrit':
                return f"त्रुटि: समाधानम् असमर्थम् - {str(e)}"
            return f"Error: Cannot solve - {str(e)}"
    
    def show(self, query: str) -> str:
        """Show/Lookup formula"""
        try:
            if self.translator.is_sanskrit(query):
                query_en = self.translator.translate(query)
            else:
                query_en = query
            
            result = self.math.lookup_formula(query_en)
            
            if self.language == 'sanskrit':
                return self.translator.english_to_sanskrit(result)
            return result
        except Exception as e:
            if self.language == 'sanskrit':
                return f"त्रुटि: सूत्रं न लब्धम् - {str(e)}"
            return f"Error: Formula not found - {str(e)}"
    
    def search(self, topic: str) -> str:
        """Search for information"""
        try:
            if self.translator.is_sanskrit(topic):
                topic_en = self.translator.translate(topic)
            else:
                topic_en = topic
            
            result = self.logic.search(topic_en)
            
            if self.language == 'sanskrit':
                return self.translator.english_to_sanskrit(result)
            return result
        except Exception as e:
            if self.language == 'sanskrit':
                return f"त्रुटि: न लब्धम् - {str(e)}"
            return f"Error: Not found - {str(e)}"
    
    def convert(self, value: str, from_unit: str, to_unit: str) -> str:
        """Convert units"""
        try:
            result = self.math.convert_units(value, from_unit, to_unit)
            
            if self.language == 'sanskrit':
                return self.translator.english_to_sanskrit(result)
            return result
        except Exception as e:
            if self.language == 'sanskrit':
                return f"त्रुटि: परिवर्तनम् असमर्थम् - {str(e)}"
            return f"Error: Cannot convert - {str(e)}"
    
    def set_language(self, lang: str):
        """Set output language"""
        self.language = lang.lower()
    
    def namaskar(self) -> str:
        """Welcome message"""
        if self.language == 'sanskrit':
            return """
🕉️ संस्कृत-कोडकः - स्वागतम्!
            
एतत् संस्कृत गणित-तर्क तन्त्रम् अस्ति।

आह्वानं कुर्वन्तु:
  गणय [expression]     - गणना कर्तुम्
  समाधत्स्व [equation] - समीकरणं समाधातुम्
  पश्य [formula]       - सूत्रं द्रष्टुम्
  अन्वेषय [topic]      - अन्वेषणं कर्तुम्
  भाषा [language]      - भाषां परिवर्तयितुम्
  सहायता              - सहायतां द्रष्टुम्

जयतु संस्कृतम्! 🙏
"""
        else:
            return """
🕉️ Sanskrit Coder - Welcome!
            
This is a Sanskrit Mathematics and Logic System.

Commands:
  calculate [expression]  - To calculate
  solve [equation]        - To solve equations
  show [formula]          - To view formulas
  search [topic]          - To search
  language [lang]         - Change language
  help                    - Show help

Jaiatu Sanskritam! 🙏
"""
    
    def process_command(self, user_input: str) -> str:
        """Process user command"""
        user_input = user_input.strip()
        
        for cmd_prefix, cmd_func in self.commands.items():
            if user_input.startswith(cmd_prefix):
                args = user_input[len(cmd_prefix):].strip()
                return cmd_func(args)
        
        return self.calculate(user_input)
