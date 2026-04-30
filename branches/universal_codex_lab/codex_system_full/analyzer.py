"""
Codex Code Analyzer.

ANALYZE stage: IR → symbols, shapes, risks, confidence.

Performs:
- Symbol table extraction (functions, classes, variables)
- Construct detection (patterns, anti-patterns)
- Risk assessment (security, complexity, performance)
- Confidence scoring

*Visionary RM (Raj Mitra)* ⚡
"""
from __future__ import annotations

import ast
import re
from typing import Any

from .ir import (
    AnalyzedIR,
    Confidence,
    Construct,
    DecodedIR,
    RiskFinding,
    RiskLevel,
    ShapeFeature,
    SourceLanguage,
    Symbol,
)


# ──────────────────────────────────────────────────────────────
# Symbol Extraction
# ──────────────────────────────────────────────────────────────

def extract_symbols_python(decoded: DecodedIR) -> list[Symbol]:
    """Extract symbols from Python source using AST."""
    symbols: list[Symbol] = []
    try:
        tree = ast.parse(decoded.source)
    except SyntaxError:
        return symbols

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            symbols.append(Symbol(
                name=node.name,
                kind="function",
                line=node.lineno or 0,
                scope=_scope_of(node, tree),
                docstring=ast.get_docstring(node),
            ))
        elif isinstance(node, ast.ClassDef):
            symbols.append(Symbol(
                name=node.name,
                kind="class",
                line=node.lineno or 0,
                scope="global",
                docstring=ast.get_docstring(node),
            ))
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    symbols.append(Symbol(
                        name=target.id,
                        kind="variable",
                        line=node.lineno or 0,
                        scope=_scope_of(node, tree),
                    ))
        elif isinstance(node, ast.Import):
            for alias in node.names:
                symbols.append(Symbol(
                    name=alias.name,
                    kind="module",
                    line=node.lineno or 0,
                ))
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                symbols.append(Symbol(
                    name=node.module,
                    kind="module",
                    line=node.lineno or 0,
                ))

    return symbols


def extract_symbols_generic(decoded: DecodedIR) -> list[Symbol]:
    """Extract symbols using regex heuristics for non-Python languages."""
    symbols: list[Symbol] = []
    for i, line in enumerate(decoded.source.split("\n"), 1):
        stripped = line.strip()

        # Function detection
        m = re.match(r"(?:function|func|fn|def)\s+(\w+)\s*\(([^)]*)\)", stripped)
        if m:
            symbols.append(Symbol(
                name=m.group(1),
                kind="function",
                line=i,
            ))

        # Class detection
        m = re.match(r"(?:class|struct|type)\s+(\w+)", stripped)
        if m:
            symbols.append(Symbol(
                name=m.group(1),
                kind="class",
                line=i,
            ))

        # Variable detection
        m = re.match(r"(?:const|let|var|int|float|string|auto)\s+(\w+)", stripped)
        if m:
            symbols.append(Symbol(
                name=m.group(1),
                kind="variable",
                line=i,
            ))

    return symbols


def _scope_of(node: ast.AST, tree: ast.Module) -> str:
    """Determine the scope of an AST node."""
    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent):
            if child is node and isinstance(parent, ast.ClassDef):
                return parent.name
    return "global"


# ──────────────────────────────────────────────────────────────
# Shape Analysis
# ──────────────────────────────────────────────────────────────

def analyze_shapes(decoded: DecodedIR) -> list[ShapeFeature]:
    """Compute structural metrics for the source."""
    shapes: list[ShapeFeature] = []
    lines = decoded.source.split("\n")

    # Lines of code
    non_empty = [l for l in lines if l.strip() and not l.strip().startswith("#")]
    shapes.append(ShapeFeature(
        kind="loc", value=len(non_empty),
        description=f"{len(non_empty)} non-empty lines",
    ))

    # Max nesting depth (approximate via indentation for Python-like code)
    if decoded.language == SourceLanguage.PYTHON:
        max_indent = 0
        for line in lines:
            if line.strip():
                indent = len(line) - len(line.lstrip())
                # Assume 4-space indentation
                depth = indent // 4
                max_indent = max(max_indent, depth)
        shapes.append(ShapeFeature(
            kind="nesting_depth", value=float(max_indent),
            threshold=5.0,
            description=f"Maximum nesting depth: {max_indent}",
        ))

    # Cyclomatic complexity (approximate for Python)
    if decoded.language == SourceLanguage.PYTHON:
        complexity = 1  # Base complexity
        for line in lines:
            stripped = line.strip()
            if re.match(r"\b(if|elif|for|while|except|and|or)\b", stripped):
                complexity += 1
        shapes.append(ShapeFeature(
            kind="cyclomatic", value=float(complexity),
            threshold=10.0,
            description=f"Cyclomatic complexity: {complexity}",
        ))

    # Fan-in / Fan-out (function call counts)
    call_sites = len(re.findall(r"\w+\s*\(", decoded.source))
    shapes.append(ShapeFeature(
        kind="fan_out", value=float(call_sites),
        description=f"Approximate function call sites: {call_sites}",
    ))

    return shapes


# ──────────────────────────────────────────────────────────────
# Risk Assessment
# ──────────────────────────────────────────────────────────────

def assess_risks(decoded: DecodedIR) -> list[RiskFinding]:
    """Identify security, complexity, and performance risks."""
    risks: list[RiskFinding] = []
    source = decoded.source
    lines = source.split("\n")

    # Security risks
    for i, line in enumerate(lines, 1):
        stripped = line.strip()

        # eval/exec usage
        if re.search(r"\beval\s*\(", stripped) or re.search(r"\bexec\s*\(", stripped):
            risks.append(RiskFinding(
                level=RiskLevel.CRITICAL,
                category="security",
                message="Use of eval/exec — potential code injection",
                line=i,
                cwe_id="CWE-95",
                recommendation="Avoid eval/exec; use safe alternatives like ast.literal_eval",
            ))

        # Hardcoded secrets
        if re.search(r"(?i)(password|secret|api_key|token)\s*=\s*['\"].+['\"]", stripped):
            risks.append(RiskFinding(
                level=RiskLevel.HIGH,
                category="security",
                message="Hardcoded secret or credential detected",
                line=i,
                cwe_id="CWE-798",
                recommendation="Use environment variables or a secrets manager",
            ))

        # SQL injection risk
        if re.search(r"(?i)(execute|query|cursor)\s*\(.*[\"'].*%", stripped):
            risks.append(RiskFinding(
                level=RiskLevel.HIGH,
                category="security",
                message="Possible SQL injection via string formatting",
                line=i,
                cwe_id="CWE-89",
                recommendation="Use parameterized queries",
            ))

        # Hardcoded IP addresses
        if re.search(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b", stripped):
            risks.append(RiskFinding(
                level=RiskLevel.LOW,
                category="security",
                message="Hardcoded IP address detected",
                line=i,
                recommendation="Use configuration files or environment variables",
            ))

    # Complexity risks
    if decoded.language == SourceLanguage.PYTHON:
        try:
            tree = ast.parse(source)
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    body_len = len(list(ast.walk(node)))
                    if body_len > 50:
                        risks.append(RiskFinding(
                            level=RiskLevel.MEDIUM,
                            category="complexity",
                            message=f"Function '{node.name}' has {body_len} AST nodes (large)",
                            line=node.lineno or 0,
                            recommendation="Break into smaller functions",
                        ))
        except SyntaxError:
            pass

    return risks


# ──────────────────────────────────────────────────────────────
# Construct Detection
# ──────────────────────────────────────────────────────────────

def detect_constructs(decoded: DecodedIR) -> list[Construct]:
    """Detect design patterns, anti-patterns, and idioms."""
    constructs: list[Construct] = []
    source = decoded.source

    # Singleton detection
    if re.search(r"(?i)(_instance|getInstance|_singleton)", source):
        constructs.append(Construct(
            name="singleton", kind="design_pattern",
            confidence=0.7,
        ))

    # Factory detection
    if re.search(r"(?i)(factory|create_\w+|make_\w+)", source) and "class" in source:
        constructs.append(Construct(
            name="factory", kind="design_pattern",
            confidence=0.6,
        ))

    # Observer detection
    if re.search(r"(?i)(subscribe|notify|observer|on_\w+|emit)", source):
        constructs.append(Construct(
            name="observer", kind="design_pattern",
            confidence=0.6,
        ))

    # God class anti-pattern
    if decoded.language == SourceLanguage.PYTHON:
        try:
            tree = ast.parse(source)
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    method_count = sum(
                        1 for n in ast.walk(node)
                        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                    )
                    if method_count > 20:
                        constructs.append(Construct(
                            name="god_class", kind="anti_pattern",
                            confidence=0.8,
                            metadata={"class": node.name, "methods": method_count},
                        ))
        except SyntaxError:
            pass

    # Long function anti-pattern
    if decoded.language == SourceLanguage.PYTHON:
        try:
            tree = ast.parse(source)
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    body_lines = (node.end_lineno or node.lineno) - (node.lineno or 0)
                    if body_lines > 50:
                        constructs.append(Construct(
                            name="long_function", kind="anti_pattern",
                            confidence=0.7,
                            metadata={"function": node.name, "lines": body_lines},
                        ))
        except SyntaxError:
            pass

    return constructs


# ──────────────────────────────────────────────────────────────
# Confidence Computation
# ──────────────────────────────────────────────────────────────

def compute_confidence(
    decoded: DecodedIR,
    risks: list[RiskFinding],
    constructs: list[Construct],
) -> Confidence:
    """Compute overall confidence based on analysis results."""
    if decoded.decode_errors:
        return Confidence.SUGGEST_ONLY

    max_risk = RiskLevel.SAFE
    for r in risks:
        if r.level in (RiskLevel.CRITICAL, RiskLevel.HIGH):
            return Confidence.SUGGEST_ONLY

    if not decoded.decode_warnings and decoded.syntax_tree is not None:
        return Confidence.SAFE_AUTO_FIX

    return Confidence.SUGGEST_ONLY


# ──────────────────────────────────────────────────────────────
# Main Analyzer Facade
# ──────────────────────────────────────────────────────────────

class CodexAnalyzer:
    """
    Code analysis engine.

    Usage:
        analyzer = CodexAnalyzer()
        analyzed = analyzer.analyze(decoded)
        print(analyzed.symbols)
        print(analyzed.risks)
    """

    def analyze(self, decoded: DecodedIR) -> AnalyzedIR:
        """
        Run full analysis pipeline on decoded source.

        Args:
            decoded: The decoded IR from the decoder stage.

        Returns:
            AnalyzedIR with symbols, shapes, risks, constructs, and confidence.
        """
        # Symbol extraction
        if decoded.language == SourceLanguage.PYTHON:
            symbols = extract_symbols_python(decoded)
        else:
            symbols = extract_symbols_generic(decoded)

        # Shape analysis
        shapes = analyze_shapes(decoded)

        # Risk assessment
        risks = assess_risks(decoded)

        # Construct detection
        constructs = detect_constructs(decoded)

        # Confidence computation
        confidence = compute_confidence(decoded, risks, constructs)

        return AnalyzedIR(
            decoded=decoded,
            symbols=symbols,
            shapes=shapes,
            risks=risks,
            constructs=constructs,
            overall_confidence=confidence,
            analysis_metadata={
                "symbol_count": len(symbols),
                "risk_count": len(risks),
                "construct_count": len(constructs),
            },
        )
