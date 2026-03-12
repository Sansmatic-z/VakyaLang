# Sanskrit Coder — Copyright (c) 2026 Raj Mitra. All Rights Reserved.
# Part of VakyaLang project (https://github.com/Sansmatic-z/VakyaLang)
# Licensed under GNU AGPL v3.0 — see root LICENSE_AGPL and NOTICE.
# Any use or modification must preserve this header and include NOTICE.

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# संस्कृत-कोडकः - मुख्य इन्जिन्
# Sanskrit Coder - Main Engine

import sys
import os
from typing import Union, Dict, List, Any, Optional

from .sanskrit_math_engine import SanskritMathEngine
from .nyaya_logic import NyayaInference, Pancavayava, Hetvabhasa, Pramana
from .sanskrit_grammar import SanskritGrammar, Vibhakti

class SanskritEngine:
    """
    Complete Sanskrit-native computing engine.
    
    Integrates:
    - Sanskrit mathematics (native Devanagari arithmetic)
    - Nyāya logic (five-membered syllogism, inference)
    - Pāṇinian grammar (inflection, sandhi, compounds)
    """

    def __init__(self):
        self.math = SanskritMathEngine()
        self.logic = NyayaInference()
        self.grammar = SanskritGrammar()
        self.language = 'sanskrit'
        
        # Command mappings
        self.commands = {
            # Math commands
            'गणय': self.cmd_calculate,
            'calculate': self.cmd_calculate,
            'समाधत्स्व': self.cmd_solve,
            'solve': self.cmd_solve,
            'वर्गीकरणम्': self.cmd_factorize,
            'factor': self.cmd_factorize,
            
            # Vedic math
            'वैदिकगुणनम्': self.cmd_vedic_multiply,
            'vedic_mul': self.cmd_vedic_multiply,
            'क्षेत्रफलम्': self.cmd_area,
            'area': self.cmd_area,
            
            # Logic commands
            'पञ्चावयवम्': self.cmd_syllogism,
            'syllogism': self.cmd_syllogism,
            'तर्कः': self.cmd_inference,
            'infer': self.cmd_inference,
            'दोषपरीक्षा': self.cmd_check_fallacy,
            'check_fallacy': self.cmd_check_fallacy,
            
            # Grammar commands
            'रूपम्': self.cmd_decline,
            'decline': self.cmd_decline,
            'धातुः': self.cmd_conjugate,
            'conjugate': self.cmd_conjugate,
            'सन्धिः': self.cmd_sandhi,
            'sandhi': self.cmd_sandhi,
            'समासः': self.cmd_compound,
            'compound': self.cmd_compound,
            
            # Info commands
            'पश्य': self.cmd_show,
            'show': self.cmd_show,
            'अन्वेषय': self.cmd_search,
            'search': self.cmd_search,
            'सहायता': self.cmd_help,
            'help': self.cmd_help,
        }
        
        # Session variables
        self.variables = {}
        self.history = []
        
    def process(self, user_input: str) -> str:
        """Process user command."""
        user_input = user_input.strip()
        
        if not user_input:
            return ""
        
        # Find command FIRST
        for cmd_prefix, cmd_func in self.commands.items():
            if user_input.startswith(cmd_prefix):
                args = user_input[len(cmd_prefix):].strip()
                return cmd_func(args)
                
        # Check for direct assignment (variable = value)
        if ' = ' in user_input or '=' in user_input:
            return self._handle_assignment(user_input)
        
        # Default: try as math expression
        return self.cmd_calculate(user_input)
    
    def _handle_assignment(self, expr: str) -> str:
        """Handle variable assignment."""
        parts = expr.split('=', 1)
        if len(parts) != 2:
            return "त्रुटिः असमीचीनं समर्पणम्"
        
        var_name = parts[0].strip()
        value_expr = parts[1].strip()
        
        # Evaluate right side
        try:
            result = self.math.calculate(value_expr)
            # Extract numeric value
            num_val = result.split()[0]
            self.variables[var_name] = float(num_val) if '.' in num_val else int(num_val)
            return f"{var_name} = {result}"
        except Exception as e:
            return f"त्रुटिः {str(e)}"
    
    # ── Math Commands ─────────────────────────────────────────────────────────
    
    def cmd_calculate(self, args: str) -> str:
        """Calculate mathematical expression."""
        if not args:
            return "उपयोगः: गणय <expression>"
        
        # Substitute variables
        for var, val in self.variables.items():
            args = args.replace(var, str(val))
        
        try:
            return self.math.calculate(args)
        except Exception as e:
            return f"गणना त्रुटिः {str(e)}"
    
    def cmd_solve(self, args: str) -> str:
        """Solve equation."""
        if not args:
            return "उपयोगः: समाधत्स्व <equation>"
        
        try:
            return self.math.solve_equation(args)
        except Exception as e:
            return f"समाधान त्रुटिः {str(e)}"
    
    def cmd_factorize(self, args: str) -> str:
        """Factorize number or expression."""
        if not args:
            return "उपयोगः: वर्गीकरणम् <number>"
        
        try:
            # Parse number
            n = self.math.parse_sanskrit_number(args)
            n = int(n)
            
            # Simple factorization
            factors = []
            d = 2
            while d * d <= n:
                while n % d == 0:
                    factors.append(d)
                    n //= d
                d += 1
            if n > 1:
                factors.append(n)
            
            factor_str = ' × '.join(self.math.to_sanskrit_number(f) for f in factors)
            return f"वर्गीकरणम्: {factor_str}"
        except Exception as e:
            return f"वर्गीकरण त्रुटिः {str(e)}"
    
    def cmd_vedic_multiply(self, args: str) -> str:
        """Vedic multiplication."""
        if not args:
            return "उपयोगः: वैदिकगुणनम् <a> <b>"
        
        parts = args.split()
        if len(parts) != 2:
            return "द्वे संख्ये आवश्यके"
        
        try:
            return self.math.vedic_multiply(parts[0], parts[1])
        except Exception as e:
            return f"वैदिक गुणन त्रुटिः {str(e)}"
    
    def cmd_area(self, args: str) -> str:
        """Calculate area."""
        if not args:
            return "उपयोगः: क्षेत्रफलम् <shape> <parameters>"
        
        parts = args.split()
        shape = parts[0]
        params = {}
        
        # Parse parameters (key=value)
        for p in parts[1:]:
            if '=' in p:
                k, v = p.split('=', 1)
                params[k] = v
        
        try:
            return self.math.calculate_area(shape, **params)
        except Exception as e:
            return f"क्षेत्रफल त्रुटिः {str(e)}"
    
    # ── Logic Commands ────────────────────────────────────────────────────────
    
    def cmd_syllogism(self, args: str) -> str:
        """Construct five-membered syllogism."""
        if not args:
            # Interactive mode
            return self._interactive_syllogism()
        
        # Parse: paksha sadhya hetu drishtanta
        parts = args.split('|')
        if len(parts) != 4:
            return "उपयोगः: पञ्चावयवम् पक्षः|साध्य|हेतु|दृष्टान्त"
        
        paksha, sadhya, hetu, drishtanta = [p.strip() for p in parts]
        
        pancha = Pancavayava()
        return pancha.construct(paksha, sadhya, hetu, drishtanta)
    
    def _interactive_syllogism(self) -> str:
        """Interactive syllogism construction."""
        return """
पञ्चावयवम् निर्माणम् (Five-membered Syllogism):

प्रतिज्ञा (Proposition):
  Format: <subject> <predicate> अस्ति
  Example: पर्वतो वह्निमान् अस्ति

हेतु (Reason):
  Format: <hetu> कारणात्
  Example: धूमवत्त्वात्

उदाहरण (Example):
  Format: यः <hetu>वान् सः <sadhya> अस्ति, यथा <example>
  Example: यो धूमवान् स वह्निमान्, यथा महानसम्

उपयोग (Application):
  Format: अयं <subject> तथा
  Example: अयं पर्वतस्तथा

निगमन (Conclusion):
  Format: तस्मात् <subject> <sadhya> अस्ति
  Example: तस्मात् पर्वतो वह्निमान् अस्ति
"""
    
    def cmd_inference(self, args: str) -> str:
        """Perform inference."""
        if not args:
            return "उपयोगः: तर्कः <observation> | <known_relation>"
        
        parts = args.split('|')
        if len(parts) != 2:
            return "अवलोकनम् | ज्ञातसम्बन्धः"
        
        observation = parts[0].strip()
        relation = parts[1].strip()
        
        inferences = self.logic.infer(observation, relation)
        
        if not inferences:
            return "कोऽपि अनुमानं न प्राप्तम्"
        
        result = "अनुमानम् (Inference):\n"
        for inf in inferences:
            result += f"  {inf['conclusion']} (विश्वासः {inf['confidence']})\n"
        
        return result
    
    def cmd_check_fallacy(self, args: str) -> str:
        """Check for logical fallacies."""
        if not args:
            return "उपयोगः: दोषपरीक्षा <hetu> | <paksha> | <sadhya>"
        
        parts = args.split('|')
        if len(parts) != 3:
            return "हेतुः | पक्षः | साध्यम्"
        
        hetu, paksha, sadhya = [p.strip() for p in parts]
        
        analysis = self.logic.hetvabhasa.analyze(hetu, paksha, sadhya)
        
        if not analysis:
            return "कोऽपि दोषो न दृष्टः (No fallacies detected)"
        
        result = "हेत्वाभासाः (Fallacies):\n"
        for code, info in analysis.items():
            result += f"  {info['name']}: {info['desc']}\n"
            result += f"    {info['example']}\n"
        
        return result
    
    # ── Grammar Commands ──────────────────────────────────────────────────────
    
    def cmd_decline(self, args: str) -> str:
        """Decline noun."""
        if not args:
            return "उपयोगः: रूपम् <stem> <gender> <case> <number>"
        
        parts = args.split()
        if len(parts) < 4:
            return "प्रातिपदिकम् लिङ्गं विभक्तिः वचनम्"
        
        stem = parts[0]
        gender = parts[1]
        case_name = parts[2]
        number = int(parts[3])
        
        case_map = {
            '1': Vibhakti.PRATHAMA, 'प्रथमा': Vibhakti.PRATHAMA,
            '2': Vibhakti.DVITIYA, 'द्वितीया': Vibhakti.DVITIYA,
            '3': Vibhakti.TRITIYA, 'तृतीया': Vibhakti.TRITIYA,
            '4': Vibhakti.CHATURTHI, 'चतुर्थी': Vibhakti.CHATURTHI,
            '5': Vibhakti.PANCHAMI, 'पञ्चमी': Vibhakti.PANCHAMI,
            '6': Vibhakti.SHASHHTHI, 'षष्ठी': Vibhakti.SHASHHTHI,
            '7': Vibhakti.SAPTAMI, 'सप्तमी': Vibhakti.SAPTAMI,
            '8': Vibhakti.SAMBODHANA, 'सम्बोधन': Vibhakti.SAMBODHANA,
        }
        
        case = case_map.get(case_name, Vibhakti.PRATHAMA)
        
        try:
            result = self.grammar.decline(stem, gender, case, number)
            return f"रूपम्: {result}"
        except Exception as e:
            return f"रूपनिर्माण त्रुटिः {str(e)}"
    
    def cmd_conjugate(self, args: str) -> str:
        """Conjugate verb."""
        if not args:
            return "उपयोगः: धातुः <root> <tense> <person> <number>"
        
        parts = args.split()
        if len(parts) < 4:
            return "धातुः लकारः पुरुषः वचनम्"
        
        root = parts[0]
        tense = parts[1]
        person = int(parts[2])
        number = int(parts[3])
        
        try:
            result = self.grammar.conjugate(root, tense, person, number)
            return f"धातुरूपम्: {result}"
        except Exception as e:
            return f"धातुरूप त्रुटिः {str(e)}"
    
    def cmd_sandhi(self, args: str) -> str:
        """Apply sandhi."""
        if not args:
            return "उपयोगः: सन्धिः <word1> <word2>"
        
        parts = args.split()
        if len(parts) != 2:
            return "द्वौ पदौ आवश्यकौ"
        
        try:
            result = self.grammar.apply_sandhi(parts[0], parts[1])
            return f"सन्धिः: {result}"
        except Exception as e:
            return f"सन्धि त्रुटिः {str(e)}"
    
    def cmd_compound(self, args: str) -> str:
        """Analyze compound."""
        if not args:
            return "उपयोगः: समासः <compound_word>"
        
        try:
            result = self.grammar.analyze_compound(args)
            return f"समासविश्लेषणम्:\n  प्रकारः: {result['type']}\n  अवयवाः: {', '.join(result['components'])}\n  अर्थः: {result['meaning']}"
        except Exception as e:
            return f"समास त्रुटिः {str(e)}"
    
    # ── Info Commands ─────────────────────────────────────────────────────────
    
    def cmd_show(self, args: str) -> str:
        """Show formula or constant."""
        if not args:
            return self.math.lookup_formula("all")
        
        return self.math.lookup_formula(args)
    
    def cmd_search(self, args: str) -> str:
        """Search knowledge base."""
        if not args:
            return "अन्वेषणार्थं पदं देहि"
        
        results = []
        
        # Search formulas
        for category, formulas in self.math.formulas.items():
            for name, formula in formulas.items():
                if args in name or args in formula:
                    results.append(f"{category} - {name}: {formula}")
        
        # Search constants
        for name, value in self.math.constants.items():
            if args in name:
                results.append(f"{name} = {value}")
        
        if not results:
            return f"\"{args}\" इति न लब्धम्"
        
        return "\n".join(results)
    
    def cmd_help(self, args: str) -> str:
        """Show help."""
        help_text = """
🕉️ संस्कृत-कोडकः - Sanskrit Coder

गणितम् (Mathematics):
  गणय <expression>       - Calculate (e.g., ५ + ३, पञ्च योगः त्रीणि)
  समाधत्स्व <equation>   - Solve equation (e.g., २x + ३ = ७)
  वर्गीकरणम् <number>     - Factorize number
  वैदिकगुणनम् <a> <b>     - Vedic multiplication
  क्षेत्रफलम् <shape>     - Calculate area

तर्कशास्त्रम् (Logic):
  पञ्चावयवम्             - Construct syllogism
  तर्कः <obs> | <rel>    - Inference
  दोषपरीक्षा <h|p|s>     - Check for fallacies

व्याकरणम् (Grammar):
  रूपम् <s> <g> <c> <n>  - Decline noun
  धातुः <r> <t> <p> <n>  - Conjugate verb
  सन्धिः <w1> <w2>        - Apply sandhi
  समासः <word>            - Analyze compound

सामान्यम् (General):
  पश्य <topic>            - Show formula
  अन्वेषय <term>          - Search
  <var> = <value>         - Set variable
  सहायता                 - This help

Examples:
  गणय १० × ५ + २५
  समाधत्स्व x² - ५x + ६ = ०
  पञ्चावयवम् पर्वतः|वह्निमान्|धूमवत्त्वात्|महानसम्
  रूपम् देव पुं १ १
"""
        return help_text
    
    def set_language(self, lang: str):
        """Set output language."""
        self.language = lang.lower()
    
    def namaskar(self) -> str:
        """Welcome message."""
        return """
🕉️ संस्कृत-कोडकः (Sanskrit Coder) - संस्करणम् २.०.० (v2.0.0)
स्वागतम्!

एतत् संस्कृत गणित-तर्क-व्याकरण तन्त्रम् अस्ति।

आदेशाः:
  गणय <expression>      - गणना कर्तुम्
  समाधत्स्व <equation>  - समीकरणं समाधातुम्
  पञ्चावयवम्            - पञ्चावयवं निर्मातुम्
  रूपम्                 - पदरूपं द्रष्टुम्
  सहायता               - सहायतां द्रष्टुम्

जयतु संस्कृतम्! 🙏
"""

    # ── Compatibility Methods (for tests) ─────────────────────────────────────

    def calculate(self, expr: str) -> str:
        """Calculate expression - compatibility method for tests."""
        return self.cmd_calculate(expr)

    def process_command(self, cmd: str) -> str:
        """Process command - compatibility method for tests."""
        return self.process(cmd)

    def convert(self, value: str, from_unit: str, to_unit: str) -> str:
        """Convert units - compatibility method for tests."""
        # Simple unit conversion
        conversions = {
            ('km', 'm'): 1000,
            ('m', 'km'): 0.001,
            ('kg', 'g'): 1000,
            ('g', 'kg'): 0.001,
            ('m', 'cm'): 100,
            ('cm', 'm'): 0.01,
            ('m', 'mm'): 1000,
            ('mm', 'm'): 0.001,
            ('ft', 'm'): 0.3048,
            ('m', 'ft'): 3.28084,
            ('in', 'cm'): 2.54,
            ('cm', 'in'): 0.393701,
        }
        
        try:
            val = float(value)
            key = (from_unit.lower(), to_unit.lower())
            if key in conversions:
                result = val * conversions[key]
                return f"{result} {to_unit}"
            else:
                return f"Unknown conversion: {from_unit} to {to_unit}"
        except Exception as e:
            return f"Conversion error: {e}"
