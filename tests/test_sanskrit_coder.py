# VakyaLang (????) � Copyright (c) 2026 Raj Mitra. All Rights Reserved.
# Original author: Raj Mitra (Visionary RM)
# Licensed under GNU AGPL v3.0 � see LICENSE and NOTICE.
# Any use, modification, or derivative work must preserve this header
# and include the NOTICE file. https://github.com/Sansmatic-z/VakyaLang

# संस्कृत-कोडकः - परीक्षा
# *Visionary RM (Raj Mitra)* ⚡
# *"संस्कृतम् अमरम् भवतु"* 🔥

"""
Sanskrit Coder - Test Suite
संस्कृत-कोडकः परीक्षा
"""

import sys
import os

# Add paths for imports
base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, base_path)
sys.path.insert(0, os.path.join(base_path, 'core'))
sys.path.insert(0, os.path.join(base_path, 'numbers'))
sys.path.insert(0, os.path.join(base_path, 'grammar'))
sys.path.insert(0, os.path.join(base_path, 'math_engine'))
sys.path.insert(0, os.path.join(base_path, 'logic_engine'))

# Import all modules
from numbers import SanskritNumbers
from grammar import SanskritGrammar
from math_engine import SanskritMathEngine
from logic_engine import SanskritLogicEngine
from translator import SanskritTranslator
from core.engine import SanskritEngine


class TestSanskritCoder:
    """Test Suite for Sanskrit Coder"""
    
    def __init__(self):
        self.engine = SanskritEngine()
        self.numbers = SanskritNumbers()
        self.translator = SanskritTranslator()
        self.grammar = SanskritGrammar()
        self.math = SanskritMathEngine()
        self.logic = SanskritLogicEngine()
        self.passed = 0
        self.failed = 0
    
    def run_all_tests(self):
        """Run all tests"""
        print("🕉️ संस्कृत-कोडकः - परीक्षा आरम्भः\n")
        print("=" * 50)
        
        self.test_numbers()
        self.test_translator()
        self.test_math()
        self.test_grammar()
        self.test_engine()
        
        print("\n" + "=" * 50)
        print(f"परीक्षा समाप्तम्!")
        print(f"उत्तीर्णः (Passed): {self.passed}")
        print(f"अनुत्तीर्णः (Failed): {self.failed}")
        if self.passed + self.failed > 0:
            print(f"यशः (Success Rate): {self.passed/(self.passed+self.failed)*100:.1f}%")
    
    def test_numbers(self):
        """Test Sanskrit numbers"""
        print("\n📊 संख्या परीक्षा (Number Tests)")
        print("-" * 30)
        
        # Test digit conversion
        try:
            assert self.numbers.to_sanskrit_digits("123") == "१२३", "Sanskrit digits failed"
            self.passed += 1
            print("✓ Sanskrit digits conversion")
        except AssertionError as e:
            self.failed += 1
            print(f"✗ Sanskrit digits: {e}")
        
        try:
            assert self.numbers.to_arabic_digits("१२३") == "123", "Arabic digits failed"
            self.passed += 1
            print("✓ Arabic digits conversion")
        except AssertionError as e:
            self.failed += 1
            print(f"✗ Arabic digits: {e}")
        
        # Test number words
        try:
            assert self.numbers.number_to_sanskrit(5) == "पञ्च", "Number word failed"
            self.passed += 1
            print("✓ Number to Sanskrit word (5)")
        except AssertionError as e:
            self.failed += 1
            print(f"✗ Number word (5): {e}")
        
        try:
            assert self.numbers.number_to_sanskrit(10) == "दश", "Number word failed"
            self.passed += 1
            print("✓ Number to Sanskrit word (10)")
        except AssertionError as e:
            self.failed += 1
            print(f"✗ Number word (10): {e}")
        
        # Test expression parsing
        try:
            result = self.numbers.parse_sanskrit_expression("५ प्लस ३")
            assert result == "5 + 3", f"Expression parsing failed: {result}"
            self.passed += 1
            print("✓ Sanskrit expression parsing")
        except AssertionError as e:
            self.failed += 1
            print(f"✗ Expression parsing: {e}")
    
    def test_translator(self):
        """Test translator"""
        print("\n📚 अनुवादक परीक्षा (Translator Tests)")
        print("-" * 30)
        
        # Test Sanskrit detection
        try:
            assert self.translator.is_sanskrit("५ प्लस ३") == True, "Sanskrit detection failed"
            self.passed += 1
            print("✓ Sanskrit text detection")
        except AssertionError as e:
            self.failed += 1
            print(f"✗ Sanskrit detection: {e}")
        
        try:
            assert self.translator.is_sanskrit("5 plus 3") == False, "English detection failed"
            self.passed += 1
            print("✓ English text detection")
        except AssertionError as e:
            self.failed += 1
            print(f"✗ English detection: {e}")
        
        # Test translation
        try:
            result = self.translator.sanskrit_to_english("प्लस")
            assert result == "plus", f"Translation failed: {result}"
            self.passed += 1
            print("✓ Sanskrit to English translation")
        except AssertionError as e:
            self.failed += 1
            print(f"✗ Translation: {e}")
    
    def test_math(self):
        """Test math engine"""
        print("\n🔢 गणित परीक्षा (Math Tests)")
        print("-" * 30)
        
        # Test basic calculation
        try:
            result = self.math.calculate("2 + 3")
            assert result == 5, f"Addition failed: {result}"
            self.passed += 1
            print("✓ Addition (2 + 3 = 5)")
        except (AssertionError, Exception) as e:
            self.failed += 1
            print(f"✗ Addition: {e}")
        
        try:
            result = self.math.calculate("10 - 4")
            assert result == 6, f"Subtraction failed: {result}"
            self.passed += 1
            print("✓ Subtraction (10 - 4 = 6)")
        except (AssertionError, Exception) as e:
            self.failed += 1
            print(f"✗ Subtraction: {e}")
        
        try:
            result = self.math.calculate("3 * 4")
            assert result == 12, f"Multiplication failed: {result}"
            self.passed += 1
            print("✓ Multiplication (3 * 4 = 12)")
        except (AssertionError, Exception) as e:
            self.failed += 1
            print(f"✗ Multiplication: {e}")
        
        try:
            result = self.math.calculate("20 / 4")
            assert result == 5.0, f"Division failed: {result}"
            self.passed += 1
            print("✓ Division (20 / 4 = 5)")
        except (AssertionError, Exception) as e:
            self.failed += 1
            print(f"✗ Division: {e}")
        
        # Test formula lookup
        try:
            result = self.math.lookup_formula("F = ma")
            assert "बलम्" in result, "Formula lookup failed"
            self.passed += 1
            print("✓ Formula lookup (F = ma)")
        except (AssertionError, Exception) as e:
            self.failed += 1
            print(f"✗ Formula lookup: {e}")
    
    def test_grammar(self):
        """Test grammar engine"""
        print("\n📝 व्याकरण परीक्षा (Grammar Tests)")
        print("-" * 30)
        
        # Test vibhakti lookup
        try:
            result = self.grammar.get_vibhakti('prathama')
            assert result['name'] == 'प्रथमा', "Vibhakti lookup failed"
            self.passed += 1
            print("✓ Vibhakti lookup (Prathama)")
        except (AssertionError, Exception) as e:
            self.failed += 1
            print(f"✗ Vibhakti lookup: {e}")
        
        # Test lakara lookup
        try:
            result = self.grammar.get_lakara('lat')
            assert result['name'] == 'लट्', "Lakara lookup failed"
            self.passed += 1
            print("✓ Lakara lookup (Lat)")
        except (AssertionError, Exception) as e:
            self.failed += 1
            print(f"✗ Lakara lookup: {e}")
        
        # Test command parsing
        try:
            result = self.grammar.parse_command("गणय ५ प्लस ३")
            assert result['type'] == 'calculation', f"Command parsing failed: {result}"
            self.passed += 1
            print("✓ Command parsing")
        except (AssertionError, Exception) as e:
            self.failed += 1
            print(f"✗ Command parsing: {e}")
    
    def test_engine(self):
        """Test main engine"""
        print("\n⚙️ इन्जिन् परीक्षा (Engine Tests)")
        print("-" * 30)
        
        # Test calculation
        try:
            result = self.engine.calculate("5 + 3")
            assert "8" in result, f"Engine calculation failed: {result}"
            self.passed += 1
            print("✓ Engine calculation")
        except (AssertionError, Exception) as e:
            self.failed += 1
            print(f"✗ Engine calculation: {e}")
        
        # Test welcome message
        try:
            result = self.engine.namaskar()
            assert "संस्कृत" in result, "Welcome message failed"
            self.passed += 1
            print("✓ Welcome message")
        except (AssertionError, Exception) as e:
            self.failed += 1
            print(f"✗ Welcome message: {e}")
        
        # Test command processing
        try:
            result = self.engine.process_command("गणय १० ऋण ४")
            assert "6" in result, f"Command processing failed: {result}"
            self.passed += 1
            print("✓ Command processing")
        except (AssertionError, Exception) as e:
            self.failed += 1
            print(f"✗ Command processing: {e}")


def run_tests():
    """Run all tests"""
    tester = TestSanskritCoder()
    tester.run_all_tests()


if __name__ == "__main__":
    run_tests()

