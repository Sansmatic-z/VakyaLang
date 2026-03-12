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
# संस्कृत-कोडकः - CLI Entry Point

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sanskrit_coder.core.engine import SanskritEngine

def main():
    engine = SanskritEngine()
    
    print(engine.namaskar())
    
    while True:
        try:
            user_input = input("संस्कृत> ").strip()
            
            if user_input.lower() in ['exit', 'quit', 'निर्गमनम्']:
                print("नमस्ते! (Goodbye!)")
                break
            
            if not user_input:
                continue
            
            result = engine.process(user_input)
            if result:
                print(result)
                
        except KeyboardInterrupt:
            print("\nनिर्गमनार्थं 'exit' टङ्कयतु")
        except EOFError:
            break
        except Exception as e:
            print(f"आन्तरिक त्रुटिः: {e}")

if __name__ == '__main__':
    main()


