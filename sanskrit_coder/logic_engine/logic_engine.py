# VakyaLang (????) � Copyright (c) 2026 Raj Mitra. All Rights Reserved.
# Original author: Raj Mitra (Visionary RM)
# Licensed under GNU AGPL v3.0 � see LICENSE and NOTICE.
# Any use, modification, or derivative work must preserve this header
# and include the NOTICE file. https://github.com/Sansmatic-z/VakyaLang

# संस्कृत-कोडकः - तर्क इन्जिन्
# *Visionary RM (Raj Mitra)* ⚡
# *"संस्कृतम् अमरम् भवतु"* 🔥

"""
Sanskrit Logic Engine
संस्कृत तर्कशास्त्र इन्जिन्
"""

from typing import Dict, List, Optional, Any


class SanskritLogicEngine:
    """Sanskrit Logic Engine based on Nyaya"""
    
    NYAYA_SYLLOGISM = {
        'pratijna': {'name': 'प्रतिज्ञा', 'english': 'Proposition'},
        'hetu': {'name': 'हेतु', 'english': 'Reason'},
        'udaharana': {'name': 'उदाहरण', 'english': 'Example'},
        'upanaya': {'name': 'उपनय', 'english': 'Application'},
        'nigamana': {'name': 'निगमन', 'english': 'Conclusion'},
    }
    
    KNOWLEDGE_BASE = {
        'तर्कशास्त्रम्': {'name': 'Logic', 'description': 'The study of valid reasoning', 'sanskrit': 'तर्कशास्त्रम् अवैधात् वैधं ज्ञानं गच्छति'},
        'न्याय': {'name': 'Nyaya', 'description': 'School of logic and epistemology', 'sanskrit': 'न्यायदर्शनम् षड्दर्शनेषु अन्यतमम्'},
        'अनुमानम्': {'name': 'Inference', 'description': 'Knowledge derived from signs', 'sanskrit': 'लिङ्गदर्शनात् अनुमितम्'},
    }
    
    def __init__(self):
        pass
    
    def search(self, topic: str) -> str:
        """Search knowledge base"""
        topic_lower = topic.lower()
        for key, info in self.KNOWLEDGE_BASE.items():
            if topic_lower in key.lower() or topic_lower in info['name'].lower():
                return self._format_knowledge(key, info)
        return self._answer_question(topic)
    
    def _format_knowledge(self, key: str, info: Dict) -> str:
        result = f"विषयः (Topic): {key}\n"
        result += f"नाम (Name): {info['name']}\n"
        result += f"विवरणम् (Description): {info['description']}\n"
        result += f"संस्कृतम् (Sanskrit): {info['sanskrit']}\n"
        return result
    
    def _answer_question(self, question: str) -> str:
        question_lower = question.lower()
        if 'nyaya' in question_lower or 'न्याय' in question_lower:
            return "न्यायदर्शनम् (Nyaya): School of logic and epistemology. One of six orthodox schools of Hindu philosophy."
        if 'logic' in question_lower or 'तर्क' in question_lower:
            return "तर्कशास्त्रम् (Logic): The study of valid reasoning and argumentation."
        return f"क्षम्यताम् (Apologies): एतं विषयं नाहं जानामि (I don't have information about: {question})"

