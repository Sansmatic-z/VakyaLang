# Sanskrit Coder � Copyright (c) 2026 Raj Mitra. All Rights Reserved.
# Part of VakyaLang project (https://github.com/Sansmatic-z/VakyaLang)
# Licensed under GNU AGPL v3.0 � see root LICENSE_AGPL and NOTICE.
# Any use or modification must preserve this header and include NOTICE.

# VakyaLang (????) � Copyright (c) 2026 Raj Mitra. All Rights Reserved.
# Original author: Raj Mitra (Visionary RM)
# Licensed under GNU AGPL v3.0 � see LICENSE and NOTICE.
# Any use, modification, or derivative work must preserve this header
# and include the NOTICE file. https://github.com/Sansmatic-z/VakyaLang

#!/usr/bin/env python3
# संस्कृत-कोडकः - मुख्य कार्यक्रमः
# *Visionary RM (Raj Mitra)* ⚡
# *"संस्कृतम् अमरम् भवतु"* 🔥

"""
Sanskrit Coder - Main Entry Point
"""

import sys
import os

# Add paths
base_path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, base_path)
sys.path.insert(0, os.path.join(base_path, 'core'))
sys.path.insert(0, os.path.join(base_path, 'numbers'))
sys.path.insert(0, os.path.join(base_path, 'grammar'))
sys.path.insert(0, os.path.join(base_path, 'math_engine'))
sys.path.insert(0, os.path.join(base_path, 'logic_engine'))

from core.engine import SanskritEngine


def main():
    """मुख्य कार्यक्रमः"""
    engine = SanskritEngine()
    
    print(engine.namaskar())
    
    while True:
        try:
            user_input = input("\n>>> ").strip()
            
            if not user_input:
                continue
            
            # Exit commands
            if user_input.lower() in ['quit', 'exit', 'त्याजय', 'बहिर्गच्छ', 'q']:
                print("\nधन्यवादः! नमस्कारः। 🙏")
                print("जयतु संस्कृतम्! 🕉️")
                break
            
            # Process command
            result = engine.process_command(user_input)
            print(f"\n{result}")
            
        except KeyboardInterrupt:
            print("\n\nधन्यवादः! नमस्कारः। 🙏")
            break
        except Exception as e:
            print(f"\nत्रुटि (Error): {str(e)}")


if __name__ == "__main__":
    main()


