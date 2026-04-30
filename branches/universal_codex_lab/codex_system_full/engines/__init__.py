# Shared engine infrastructure for the Universal Codex Engine
from .grammar_parser import GrammarParser, GrammarRule, ParseError
from .ast_builder import ASTBuilder, ASTNode, ASTNodeType
from .pattern_matcher import PatternMatcher, PatternMatch, PatternRegistry
from .code_generator import CodeGenerator, GenerationContext
from .knowledge_base import KnowledgeBase, KnowledgeEntry, KnowledgeQuery

__all__ = [
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
]
