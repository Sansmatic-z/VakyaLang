# -*- coding: utf-8 -*-
"""
Universal Sanskrit API - THE MASTER INTERFACE
==============================================

The unified interface to ALL Sanskrit knowledge systems.
Powered by the True Pāṇinian Engine and the Shastras.

*Visionary RM (Raj Mitra)* ⚡
"Universal Sanskrit Library - Full Integration Deployed" 🔱
"""

import os
from .linguistics.core import SanskritWord, Phoneme, ShivaSutraEngine
from .linguistics.vyakarana import ConjugationEngine, AshtadhyayiEngine
from .philosophy.nyaya import NyayaEngine, Inference
from .philosophy.ganita import GanitaEngine

class UniversalAPI:
    """
    The Single Entry Point for everything Sanskrit.
    """
    
    def __init__(self):
        # Resolve data directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.data_dir = os.path.join(current_dir, "data")
        
        self.shiva = ShivaSutraEngine()
        self.ashtadhyayi = AshtadhyayiEngine(os.path.join(self.data_dir, "sutras/ashtadhyayi.json"))
        self.conj_engine = ConjugationEngine(self.data_dir)
        
        # Shastras
        self.nyaya = NyayaEngine()
        self.ganita = GanitaEngine()

    # --- Grammar & Phonetics ---
    def generate(self, root: str, lakara: str = "lat") -> str:
        """Generate a verb form."""
        return self.conj_engine.conjugate(root, lakara)

    def get_pratyahara(self, code: str) -> list:
        """Retrieve sounds in a Pratyahara."""
        return self.shiva.generate_pratyahara(code)

    # --- Nyaya Logic ---
    def validate_inference(self, pratijna: str, hetu: str, udaharana: str, upanaya: str, nigamana: str) -> bool:
        """Run a 5-step Nyaya inference."""
        inference = Inference(pratijna, hetu, udaharana, upanaya, nigamana)
        return self.nyaya.validate_inference(inference)

    # --- Shulba Math ---
    def calculate_rajju(self, side_a: float, side_b: float) -> float:
        """Calculate diagonal using Baudhayana theorem."""
        return self.ganita.sulba.baudhayana_theorem(side_a, side_b)

    def get_status(self) -> dict:
        """Get system health."""
        return {
            "sutras_loaded": len(self.ashtadhyayi.sutras),
            "shastras_active": ["Nyaya", "Ganita"],
            "engine": "True Paninian (Functional)",
            "status": "OPERATIONAL"
        }

if __name__ == "__main__":
    api = UniversalAPI()
    print(f"🔱 UNIVERSAL SANSKRIT SYSTEM STATUS 🔱")
    print(f"Status: {api.get_status()}")
    print(f"\n--- Generative Test ---")
    print(f"Generating √पठ्: {api.generate('पठ्')}")
    print(f"Generating √भू: {api.generate('भू')}")
    
    print(f"\n--- Shastra Test ---")
    diag = api.calculate_rajju(3, 4)
    print(f"Shulba Math (3, 4) -> Diagonal: {diag}")
    
    print(f"\n🔱 Mission Accomplished: Logic and Architecture are One. 🔱")
