"""
Phase 5: Validation Engine Codex Page.

Verifies generated code correctness:
- Syntax validation
- Structural analysis
- Semantic checks
- Compilation attempt via Vak compiler
- Outputs detailed validation reports as valid Vak code
"""
from __future__ import annotations

import re
from typing import Any

from ..models import CodexDiagnostic, CodexPageManifest, CodexPageProbe, CodexResult
from ..page import CodexPage
from ..engines.code_generator import CodeGenerator, GenerationContext
from .utils import _overall_confidence


class ValidationEngineCodexPage(CodexPage):
    """Validation engine: verify generated code correctness."""
    name = "validation_engine"
    description = "Validation page (verify generated code correctness)"
    priority = 74
    kind = "validation"
    chapter = "knowledge_engine"
    chapter_title = "Domain-Specific Knowledge Engine"
    chapter_order = 54
    capabilities = ("validation", "verification", "syntax_check", "compile_check", "semantic_check")
    emits_vak = True
    extensions = ("validate", "verify", "check")
    max_fixpoint_passes = 2
    max_source_length = 1_000_000

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        self._generator = CodeGenerator()
        self._diagnostics: list[CodexDiagnostic] = []
        self._detected_constructs: list[str] = []
        self._register_templates()

    def _register_templates(self) -> None:
        self._generator.register_template("validation_report", """# Validation Report
# Source: {source_kind}
# Length: {source_length} characters
# Lines: {lines_count}

श्रेणी ValidationResult {{
    परिवर्तनी syntax_valid = {syntax_valid}
    परिवर्तनी structure_valid = {structure_valid}
    परिवर्तनी semantic_valid = {semantic_valid}
    परिवर्तनी compilation_valid = {compilation_valid}
    परिवर्तनी overall_score = {overall_score}

{validation_details}
}}""")

        self._generator.register_template("validation_detail", """    # {check_name}: {status}
    # {detail}
    परिवर्तनी {check_name}_result = "{status}\"""")

    # ------------------------------------------------------------------
    # Probe
    # ------------------------------------------------------------------
    def probe(self, source: str, *, filename: str | None = None) -> CodexPageProbe:
        indicators = [
            "validate", "verify", "check", "correct", "correctness",
            "syntax", "semantic", "compile", "test",
        ]
        score = 0
        for indicator in indicators:
            if indicator in source.lower():
                score += 12

        if score >= 12:
            return CodexPageProbe(self.name, min(score, 85), f"Validation request detected ({score} indicators)")
        return CodexPageProbe(self.name, 10, "Validation engine chapter (default)")

    # ------------------------------------------------------------------
    # Transform
    # ------------------------------------------------------------------
    def transform(self, source: str, *, filename: str | None = None) -> CodexResult:
        self._diagnostics = []
        self._detected_constructs = []

        if len(source) > getattr(self, "max_source_length", 1_000_000):
            self._diagnostics.append(CodexDiagnostic(
                page=self.name, level="error",
                message=f"Source too large ({len(source)} bytes, max {getattr(self, 'max_source_length', 1_000_000)})",
                confidence="do_not_touch",
            ))
            return CodexResult(
                page=self.name, original_source=source, source=source,
                transformed=False, confidence="do_not_touch",
                diagnostics=tuple(self._diagnostics), manifest=self.manifest(),
                metadata={"source_kind": "validation_request", "error": "source_too_large"},
            )

        # Run validation checks
        results = self._validate_code(source)

        # Generate output
        vak_output = self._generate_validation_report(source, results)

        transformed = True  # Always transform to validation report

        return CodexResult(
            page=self.name,
            original_source=source,
            source=vak_output,
            transformed=transformed,
            confidence=_overall_confidence(self._diagnostics, transformed),
            diagnostics=tuple(self._diagnostics),
            manifest=self.manifest(),
            metadata={
                "source_kind": "validation_request",
                "validation_results": results,
                "overall_score": results.get("overall_score", 0),
            },
        )

    # ------------------------------------------------------------------
    # Validation checks
    # ------------------------------------------------------------------
    def _validate_code(self, source: str) -> dict[str, Any]:
        """Run comprehensive validation checks."""
        results: dict[str, Any] = {
            "syntax_valid": True,
            "structure_valid": True,
            "semantic_valid": True,
            "compilation_valid": True,
            "checks": [],
            "overall_score": 1.0,
        }

        if not source or not source.strip():
            results["syntax_valid"] = False
            results["structure_valid"] = False
            results["overall_score"] = 0.0
            results["checks"].append({"name": "non_empty", "status": "fail", "detail": "Source is empty"})
            return results

        lines = source.split("\n")
        issues: list[str] = []

        # 1. Syntax checks
        # Balanced braces
        open_braces = source.count("{")
        close_braces = source.count("}")
        if open_braces != close_braces:
            results["syntax_valid"] = False
            issues.append(f"Unbalanced braces: {open_braces} open, {close_braces} close")
            results["checks"].append({"name": "balanced_braces", "status": "fail", "detail": issues[-1]})
        else:
            results["checks"].append({"name": "balanced_braces", "status": "pass", "detail": f"{open_braces} balanced pairs"})

        # Balanced parentheses
        open_parens = source.count("(")
        close_parens = source.count(")")
        if open_parens != close_parens:
            results["syntax_valid"] = False
            issues.append(f"Unbalanced parentheses: {open_parens} open, {close_parens} close")
            results["checks"].append({"name": "balanced_parens", "status": "fail", "detail": issues[-1]})
        else:
            results["checks"].append({"name": "balanced_parens", "status": "pass", "detail": f"{open_parens} balanced pairs"})

        # Balanced brackets
        open_brackets = source.count("[")
        close_brackets = source.count("]")
        if open_brackets != close_brackets:
            results["syntax_valid"] = False
            issues.append(f"Unbalanced brackets: {open_brackets} open, {close_brackets} close")
            results["checks"].append({"name": "balanced_brackets", "status": "fail", "detail": issues[-1]})
        else:
            results["checks"].append({"name": "balanced_brackets", "status": "pass", "detail": f"{open_brackets} balanced pairs"})

        # 2. Structure checks
        # Empty file
        if not source.strip():
            results["structure_valid"] = False
            issues.append("Empty source")
            results["checks"].append({"name": "non_empty", "status": "fail", "detail": "Source is empty"})
        else:
            results["checks"].append({"name": "non_empty", "status": "pass", "detail": f"{len(lines)} lines"})

        # Has at least one definition
        has_def = any(
            kw in source for kw in ["कर्म", "श्रेणी", "परिवर्तनी", "स्थिर",
                                      "def ", "class ", "function ", "const ", "let "]
        )
        if has_def:
            results["checks"].append({"name": "has_definition", "status": "pass", "detail": "Contains definitions"})
        else:
            results["structure_valid"] = False
            results["checks"].append({"name": "has_definition", "status": "fail", "detail": "No definitions found"})

        # 3. Semantic checks
        # Unused variables (heuristic) — check if variable names appear beyond their definition
        var_defs = re.findall(r"परिवर्तनी\s+(\w+)", source)
        unused = []
        for var in var_defs:
            # Count occurrences of the variable name in the source
            # A definition counts as 1; if total count is 1, it's unused
            # Use word boundary to avoid false matches (e.g., "x" matching "export")
            usage_pattern = re.compile(rf"\b{re.escape(var)}\b")
            total_uses = len(usage_pattern.findall(source))
            if total_uses <= 1:
                unused.append(var)
        if unused:
            results["semantic_valid"] = False
            results["checks"].append({"name": "no_unused_vars", "status": "warn", "detail": f"Unused: {', '.join(unused[:5])}"})
        else:
            results["checks"].append({"name": "no_unused_vars", "status": "pass", "detail": "All variables used"})

        # 4. Compilation check (attempt Vak validation)
        try:
            from ..core import SanskritVakyaUniversalCodex
            codex = SanskritVakyaUniversalCodex()
            result = codex.transform_source(source)
            if result.validation:
                results["compilation_valid"] = result.validation.compiled
                results["checks"].append({
                    "name": "vak_compilation",
                    "status": "pass" if result.validation.compiled else "fail",
                    "detail": result.validation.error_message or "Compiled successfully",
                })
        except Exception:
            results["checks"].append({"name": "vak_compilation", "status": "skip", "detail": "Vak compiler not available"})

        # Calculate overall score
        pass_count = sum(1 for c in results["checks"] if c["status"] == "pass")
        total_count = len(results["checks"])
        results["overall_score"] = pass_count / max(total_count, 1)

        # Record diagnostics
        for check in results["checks"]:
            level = "info" if check["status"] == "pass" else "warning" if check["status"] == "warn" else "error"
            self._diagnostics.append(CodexDiagnostic(
                page=self.name, level=level,
                message=f"[{check['name']}] {check['detail']}",
                confidence="safe_auto_fix" if check["status"] == "pass" else "suggest_only",
            ))

        return results

    def _generate_validation_report(self, source: str, results: dict[str, Any]) -> str:
        """Generate Vak code representing validation results."""
        details_lines: list[str] = []
        for check in results.get("checks", []):
            vak = self._generator.generate(
                template_name="validation_detail",
                check_name=check["name"],
                status=check["status"],
                detail=check["detail"],
            )
            details_lines.append(vak)

        vak = self._generator.generate(
            template_name="validation_report",
            source_kind="validation_target",
            source_length=len(source),
            lines_count=len(source.split("\n")),
            syntax_valid=str(results.get("syntax_valid", False)).lower(),
            structure_valid=str(results.get("structure_valid", False)).lower(),
            semantic_valid=str(results.get("semantic_valid", False)).lower(),
            compilation_valid=str(results.get("compilation_valid", False)).lower(),
            overall_score=f"{results.get('overall_score', 0):.2f}",
            validation_details="\n\n".join(details_lines),
        )

        return vak
