"""
Universal Codex Engine — Enhanced Core Package.

This package provides the complete Universal Codex Engine for VakyaLang
with 5 phases of capabilities:
  Phase 1: Multi-Language Translators
  Phase 2: Pattern & Knowledge Encoding
  Phase 3: System Generators
  Phase 4: Language Creation Tools
  Phase 5: Domain-Specific Knowledge Engine
"""
from .core import SanskritVakyaUniversalCodex, build_default_codex
from .models import (
    CodexChapterManifest,
    CodexDiagnostic,
    CodexPageManifest,
    CodexPageProbe,
    CodexResult,
    CodexRuleEvent,
    CodexValidation,
)
from .page import CodexPage
from .promotion import CodexPromotionGate, CodexPromotionReport, evaluate_promotion_candidate

# Engine exports
from .engines import (
    ASTBuilder,
    ASTNode,
    ASTNodeType,
    CodeGenerator,
    GenerationContext,
    GrammarParser,
    GrammarRule,
    KnowledgeBase,
    KnowledgeEntry,
    KnowledgeQuery,
    ParseError,
    PatternMatch,
    PatternMatcher,
    PatternRegistry,
)

# Page exports (Phase 1–5)
from .pages import (
    # Existing pages
    EnglishVakCodexPage,
    MathLogicCodexPage,
    SanskritNotationCodexPage,
    VakCodexPage,
    VakLegacyCodexPage,
    VakModuleCodexPage,
    # Phase 1: Translators
    PythonToVakCodexPage,
    JavaScriptToVakCodexPage,
    PseudocodeToVakCodexPage,
    NaturalLanguageToVakCodexPage,
    # Phase 2: Patterns
    DesignPatternsCodexPage,
    AlgorithmPatternsCodexPage,
    ArchitecturePatternsCodexPage,
    KnowledgeDomainsCodexPage,
    # Phase 3: Generators
    APIGeneratorCodexPage,
    CLIGeneratorCodexPage,
    WebAppGeneratorCodexPage,
    SchemaGeneratorCodexPage,
    # Phase 4: Language Tools
    GrammarEngineCodexPage,
    LexerGeneratorCodexPage,
    DSLBuilderCodexPage,
    LanguageBridgeCodexPage,
    # Phase 5: Knowledge Engine
    KnowledgeGraphCodexPage,
    InferenceEngineCodexPage,
    CodeReasoningCodexPage,
    LearningSystemCodexPage,
    ValidationEngineCodexPage,
)

__version__ = "2.0.0"
__all__ = [
    # Core
    "SanskritVakyaUniversalCodex",
    "build_default_codex",
    "CodexPage",
    # Models
    "CodexChapterManifest",
    "CodexDiagnostic",
    "CodexPageManifest",
    "CodexPageProbe",
    "CodexResult",
    "CodexRuleEvent",
    "CodexValidation",
    "CodexPromotionGate",
    "CodexPromotionReport",
    "evaluate_promotion_candidate",
    # Engines
    "ASTBuilder",
    "ASTNode",
    "ASTNodeType",
    "CodeGenerator",
    "GenerationContext",
    "GrammarParser",
    "GrammarRule",
    "KnowledgeBase",
    "KnowledgeEntry",
    "KnowledgeQuery",
    "ParseError",
    "PatternMatch",
    "PatternMatcher",
    "PatternRegistry",
    # Existing Pages
    "EnglishVakCodexPage",
    "MathLogicCodexPage",
    "SanskritNotationCodexPage",
    "VakCodexPage",
    "VakLegacyCodexPage",
    "VakModuleCodexPage",
    # Phase 1: Translators
    "PythonToVakCodexPage",
    "JavaScriptToVakCodexPage",
    "PseudocodeToVakCodexPage",
    "NaturalLanguageToVakCodexPage",
    # Phase 2: Patterns
    "DesignPatternsCodexPage",
    "AlgorithmPatternsCodexPage",
    "ArchitecturePatternsCodexPage",
    "KnowledgeDomainsCodexPage",
    # Phase 3: Generators
    "APIGeneratorCodexPage",
    "CLIGeneratorCodexPage",
    "WebAppGeneratorCodexPage",
    "SchemaGeneratorCodexPage",
    # Phase 4: Language Tools
    "GrammarEngineCodexPage",
    "LexerGeneratorCodexPage",
    "DSLBuilderCodexPage",
    "LanguageBridgeCodexPage",
    # Phase 5: Knowledge Engine
    "KnowledgeGraphCodexPage",
    "InferenceEngineCodexPage",
    "CodeReasoningCodexPage",
    "LearningSystemCodexPage",
    "ValidationEngineCodexPage",
]
