# Codex Pages package — all page implementations
from .english_vak_page import EnglishVakCodexPage
from .math_logic_page import MathLogicCodexPage
from .sanskrit_notation_page import SanskritNotationCodexPage
from .vak_legacy_page import VakLegacyCodexPage
from .vak_module_page import VakModuleCodexPage
from .vak_page import VakCodexPage

# Phase 1: Multi-Language Translators
from .python_to_vak import PythonToVakCodexPage
from .javascript_to_vak import JavaScriptToVakCodexPage
from .pseudocode_to_vak import PseudocodeToVakCodexPage
from .natural_language_to_vak import NaturalLanguageToVakCodexPage

# Phase 2: Pattern & Knowledge
from .design_patterns import DesignPatternsCodexPage
from .algorithm_patterns import AlgorithmPatternsCodexPage
from .architecture_patterns import ArchitecturePatternsCodexPage
from .knowledge_domains import KnowledgeDomainsCodexPage

# Phase 3: System Generators
from .api_generator import APIGeneratorCodexPage
from .cli_generator import CLIGeneratorCodexPage
from .webapp_generator import WebAppGeneratorCodexPage
from .schema_generator import SchemaGeneratorCodexPage

# Phase 4: Language Tools
from .grammar_engine import GrammarEngineCodexPage
from .lexer_generator import LexerGeneratorCodexPage
from .dsl_builder import DSLBuilderCodexPage
from .language_bridge import LanguageBridgeCodexPage

# Phase 5: Knowledge Engine
from .knowledge_graph import KnowledgeGraphCodexPage
from .inference_engine import InferenceEngineCodexPage
from .code_reasoning import CodeReasoningCodexPage
from .learning_system import LearningSystemCodexPage
from .validation_engine import ValidationEngineCodexPage

# Pipeline Pages (new)
from .bytecode_decoder import BytecodeDecoderCodexPage
from .semantic_analyzer import SemanticAnalyzerCodexPage
from .decompiler_page import DecompilerPageCodexPage
from .proof_translator import ProofTranslatorCodexPage
from .compatibility_layer import CompatibilityLayerCodexPage
from .vak_canonical import VakCanonicalCodexPage

__all__ = [
    # Existing pages
    "EnglishVakCodexPage",
    "MathLogicCodexPage",
    "SanskritNotationCodexPage",
    "VakCodexPage",
    "VakLegacyCodexPage",
    "VakModuleCodexPage",
    # Phase 1
    "PythonToVakCodexPage",
    "JavaScriptToVakCodexPage",
    "PseudocodeToVakCodexPage",
    "NaturalLanguageToVakCodexPage",
    # Phase 2
    "DesignPatternsCodexPage",
    "AlgorithmPatternsCodexPage",
    "ArchitecturePatternsCodexPage",
    "KnowledgeDomainsCodexPage",
    # Phase 3
    "APIGeneratorCodexPage",
    "CLIGeneratorCodexPage",
    "WebAppGeneratorCodexPage",
    "SchemaGeneratorCodexPage",
    # Phase 4
    "GrammarEngineCodexPage",
    "LexerGeneratorCodexPage",
    "DSLBuilderCodexPage",
    "LanguageBridgeCodexPage",
    # Phase 5
    "KnowledgeGraphCodexPage",
    "InferenceEngineCodexPage",
    "CodeReasoningCodexPage",
    "LearningSystemCodexPage",
    "ValidationEngineCodexPage",
    # Pipeline pages
    "BytecodeDecoderCodexPage",
    "SemanticAnalyzerCodexPage",
    "DecompilerPageCodexPage",
    "ProofTranslatorCodexPage",
    "CompatibilityLayerCodexPage",
    "VakCanonicalCodexPage",
]
