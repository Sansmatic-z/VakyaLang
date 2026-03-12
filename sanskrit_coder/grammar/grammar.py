# Sanskrit Coder — Copyright (c) 2026 Raj Mitra. All Rights Reserved.
# Part of VakyaLang project (https://github.com/Sansmatic-z/VakyaLang)
# Licensed under GNU AGPL v3.0 — see root LICENSE_AGPL and NOTICE.
# Any use or modification must preserve this header and include NOTICE.

"""
Sanskrit Grammar Engine
संस्कृत व्याकरण इन्जिन्
"""

from typing import Dict, List, Optional, Tuple


class SanskritGrammar:
    """Sanskrit Grammar Handler"""
    
    VIBHAKTAYAH = {
        'prathama': {'name': 'प्रथमा', 'english': 'Nominative', 'usage': 'कर्ता (Subject)'},
        'dvitiya': {'name': 'द्वितीया', 'english': 'Accusative', 'usage': 'कर्म (Object)'},
        'trtiya': {'name': 'तृतीया', 'english': 'Instrumental', 'usage': 'करणम्'},
        'caturthi': {'name': 'चतुर्थी', 'english': 'Dative', 'usage': 'सम्प्रदानम्'},
        'pancami': {'name': 'पञ्चमी', 'english': 'Ablative', 'usage': 'अपादानम्'},
        'sasthi': {'name': 'षष्ठी', 'english': 'Genitive', 'usage': 'सम्बन्धः'},
        'saptami': {'name': 'सप्तमी', 'english': 'Locative', 'usage': 'अधिकरणम्'},
        'sambodhana': {'name': 'सम्बोधन', 'english': 'Vocative', 'usage': 'आमन्त्रणम्'},
    }
    
    LAKARAH = {
        'lat': {'name': 'लट्', 'english': 'Present', 'sanskrit': 'वर्तमानकालः'},
        'lang': {'name': 'लङ्', 'english': 'Past', 'sanskrit': 'भूतकालः'},
        'lrit': {'name': 'लृट्', 'english': 'Future', 'sanskrit': 'भविष्यत्कालः'},
        'lot': {'name': 'लोट्', 'english': 'Imperative', 'sanskrit': 'आज्ञार्थः'},
    }
    
    def __init__(self):
        pass
    
    def get_vibhakti(self, name: str) -> Dict:
        return self.VIBHAKTAYAH.get(name.lower(), {})
    
    def get_lakara(self, name: str) -> Dict:
        return self.LAKARAH.get(name.lower(), {})
    
    def parse_command(self, command: str) -> Dict:
        result = {'command': command, 'verb': None, 'object': None, 'parameters': [], 'type': 'unknown'}
        words = command.split()
        if not words:
            return result
        result['verb'] = words[0]
        if len(words) > 1:
            result['parameters'] = words[1:]
            result['object'] = ' '.join(words[1:])
        verb = result['verb']
        if verb in ['गणय', 'calculate']:
            result['type'] = 'calculation'
        elif verb in ['समाधत्स्व', 'solve']:
            result['type'] = 'equation solving'
        elif verb in ['पश्य', 'दर्शय', 'show']:
            result['type'] = 'lookup'
        elif verb in ['अन्वेषय', 'search']:
            result['type'] = 'search'
        return result


