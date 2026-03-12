# Sanskrit Coder — Copyright (c) 2026 Raj Mitra. All Rights Reserved.
# Part of VakyaLang project (https://github.com/Sansmatic-z/VakyaLang)
# Licensed under GNU AGPL v3.0 — see root LICENSE_AGPL and NOTICE.
# Any use or modification must preserve this header and include NOTICE.

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# *Visionary RM (Raj Mitra)* ⚡

import sys
import os
from pathlib import Path

# Add the parent directory to sys.path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sanskrit_coder.core.engine import SanskritEngine

def main():
    engine = SanskritEngine()
    print("🕉️ Sanskrit Coder (संस्कृत-कोडकः) v2.0.0")
    print("Type 'exit' or 'quit' to stop.")
    
    while True:
        try:
            user_input = input("\nसंस्कृतम् > ")
            if user_input.lower() in ['exit', 'quit', 'विराम']:
                break
            
            if not user_input.strip():
                continue
                
            result = engine.execute(user_input)
            print(f"फलम्: {result}")
            
        except KeyboardInterrupt:
            print("\nपुनर्मिलामः!")
            break
        except Exception as e:
            print(f"दोषः: {e}")

if __name__ == "__main__":
    main()
