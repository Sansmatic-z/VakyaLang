# VakyaLang (????) � Copyright (c) 2026 Raj Mitra. All Rights Reserved.
# Original author: Raj Mitra (Visionary RM)
# Licensed under GNU AGPL v3.0 � see LICENSE and NOTICE.
# Any use, modification, or derivative work must preserve this header
# and include the NOTICE file. https://github.com/Sansmatic-z/VakyaLang

# संस्कृत-कोडकः - सजीव-विशेषता-परीक्षा (Live Features Test)
import sys
import os

base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, base_path)
sys.path.insert(0, os.path.join(base_path, 'core'))

from core.engine import SanskritEngine

def run_live_tests():
    engine = SanskritEngine()
    print("🕉️ Sanskrit Coder - Live Features Test\n")

    # 1. Complex Arithmetic with Sanskrit terms
    print("1. संकीर्ण-गणितम् (Complex Math):")
    expr = "दश गुणनम् (पञ्च प्लस ५)"
    print(f"Input: {expr}")
    result = engine.process_command(f"गणय {expr}")
    print(f"Result: {result}\n")

    # 2. Equation Solving
    print("2. समीकरण-समाधानम् (Equation Solving):")
    eq = "४x + ८ = २८"
    print(f"Input: {eq}")
    result = engine.process_command(f"समाधत्स्व {eq}")
    print(f"Result: {result}\n")

    # 3. Unit Conversion
    print("3. एकक-परिवर्तनम् (Unit Conversion):")
    print("Input: 5 km to m")
    result = engine.convert("5", "km", "m")
    print(f"Result: {result}\n")

    # 4. Formula Lookup
    print("4. सूत्र-अन्वेषणम् (Formula Lookup):")
    query = "E = mc^2"
    print(f"Input: {query}")
    result = engine.process_command(f"पश्य {query}")
    print(f"Result: {result}\n")

    # 5. Nyaya Logic Search
    print("5. न्याय-तर्क-अन्वेषणम् (Logic Search):")
    topic = "न्याय"
    print(f"Input: {topic}")
    result = engine.process_command(f"अन्वेषय {topic}")
    print(f"Result: {result}\n")

if __name__ == "__main__":
    run_live_tests()

