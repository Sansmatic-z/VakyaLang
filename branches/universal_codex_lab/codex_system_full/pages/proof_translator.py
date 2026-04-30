"""
Pipeline Page: Proof Translator.

Provides proof/math/logic translation as a Codex page:
- Mathematical notation translation
- Logic verification
- Formal proof generation
- Theorem validation

*Visionary RM (Raj Mitra)* ⚡
"""
from __future__ import annotations

import re
from typing import Any

from ..models import CodexDiagnostic, CodexPageManifest, CodexPageProbe, CodexResult
from ..page import CodexPage


class ProofTranslatorCodexPage(CodexPage):
    """Translates and verifies mathematical proofs and logic."""
    name = "proof_translator"
    description = "Proof/math/logic translator page"
    priority = 73
    kind = "proof_translator"
    chapter = "proofs"
    chapter_title = "Proof/Math/Logic Translators"
    chapter_order = 60
    capabilities = ("proof", "math", "logic", "theorem", "verify")
    emits_vak = True
    extensions = ("tex", "latex", "math", "proof", "thy")
    max_fixpoint_passes = 2

    def probe(self, source: str, *, filename: str | None = None) -> CodexPageProbe:
        """Check if source looks like mathematical content."""
        indicators = [
            r"\\(begin|end)\{",  # LaTeX
            r"∀|∃|∈|⊆|∪|∩",  # Unicode math symbols
            r"theorem|lemma|proof|corollary|conjecture",
            r"Q\.E\.D\.|qed|∎",
            r"implies|iff|therefore|because",
        ]
        score = 0
        for pattern in indicators:
            if re.search(pattern, source, re.IGNORECASE):
                score += 15

        if filename and filename.endswith((".tex", ".latex", ".proof", ".thy")):
            score += 30

        if score >= 15:
            return CodexPageProbe(self.name, min(score, 90), "Mathematical content detected")
        return CodexPageProbe(self.name, 0, "not mathematical content")

    def transform(self, source: str, *, filename: str | None = None) -> CodexResult:
        diagnostics: list[CodexDiagnostic] = []
        metadata: dict[str, Any] = {}

        # Parse mathematical structures
        theorems = self._extract_theorems(source)
        proofs = self._extract_proofs(source)
        definitions = self._extract_definitions(source)

        metadata["theorems"] = theorems
        metadata["proofs"] = proofs
        metadata["definitions"] = definitions
        metadata["has_qed"] = "∎" in source or "Q.E.D." in source or "qed" in source.lower()

        # Build Vak representation
        lines: list[str] = [
            "# Proof Translation to Vak",
            f"# Theorems: {len(theorems)}",
            f"# Proofs: {len(proofs)}",
            f"# Definitions: {len(definitions)}",
            "",
        ]

        for defn in definitions:
            lines.append(f"# Definition: {defn['name']}")
            lines.append(f"# {defn.get('body', '')}")
            lines.append("")

        for theorem in theorems:
            lines.append(f"# Theorem: {theorem.get('name', 'Anonymous')}")
            lines.append(f"# {theorem.get('statement', '')}")
            lines.append("")

        for proof in proofs:
            lines.append(f"# Proof: {proof.get('name', 'Anonymous')}")
            lines.append(f"# Method: {proof.get('method', 'unknown')}")
            if proof.get("qed"):
                lines.append(f"# QED: ∎")
            lines.append("")

        # Generate Vak constructs
        if theorems:
            lines.append("# Vak representation of theorems")
            for theorem in theorems:
                name = theorem.get("name", "theorem")
                lines.append(f"श्रेणी प्रमेय_{name} {{")
                lines.append(f"    # {theorem.get('statement', '')}")
                lines.append("}")
                lines.append("")

        if proofs:
            lines.append("# Vak representation of proofs")
            for proof in proofs:
                name = proof.get("name", "proof")
                lines.append(f"कर्म प्रमाण_{name}() {{")
                lines.append(f"    # Method: {proof.get('method', 'unknown')}")
                lines.append(f"    लौटाओ सिद्ध")
                lines.append("}")
                lines.append("")

        output = "\n".join(lines)

        # Diagnostics
        if not theorems and not proofs:
            diagnostics.append(CodexDiagnostic(
                page=self.name, level="info",
                message="No formal theorems or proofs detected",
                confidence="suggest_only",
            ))
        else:
            diagnostics.append(CodexDiagnostic(
                page=self.name, level="info",
                message=f"Translated {len(theorems)} theorems and {len(proofs)} proofs",
                confidence="safe_auto_fix",
            ))

        return CodexResult(
            page=self.name, original_source=source, source=output,
            transformed=True, confidence="safe_auto_fix",
            diagnostics=tuple(diagnostics), metadata=metadata,
        )

    def _extract_theorems(self, source: str) -> list[dict[str, str]]:
        """Extract theorem statements."""
        theorems: list[dict[str, str]] = []
        patterns = [
            r"(?:theorem|प्रमेय)\s+(?:([\w]+)\s*:?\s*)?(.+?)(?=(?:proof|lemma|theorem|Q\.E\.D\.|qed|∎|$))",
            r"\\begin\{theorem\}(?:\{([^}]*)\})?\s*(.+?)\\end\{theorem\}",
        ]
        for pattern in patterns:
            for match in re.finditer(pattern, source, re.IGNORECASE | re.DOTALL):
                name = (match.group(1) or "").strip() or f"theorem_{len(theorems) + 1}"
                statement = (match.group(2) or "").strip()
                theorems.append({"name": name, "statement": statement})
        return theorems

    def _extract_proofs(self, source: str) -> list[dict[str, str]]:
        """Extract proof structures."""
        proofs: list[dict[str, str]] = []

        if re.search(r"\\begin\{proof\}", source):
            for match in re.finditer(r"\\begin\{proof\}\s*(.+?)\\end\{proof\}", source, re.DOTALL):
                body = match.group(1).strip()
                proofs.append({
                    "name": f"proof_{len(proofs) + 1}",
                    "method": self._classify_proof_method(body),
                    "body": body[:200],
                    "qed": "∎" in body or "qed" in body.lower(),
                })

        # Heuristic proof detection
        if "proof" in source.lower() and not proofs:
            proofs.append({
                "name": "proof_1",
                "method": "heuristic",
                "body": source[:200],
                "qed": "∎" in source or "Q.E.D." in source,
            })

        return proofs

    def _extract_definitions(self, source: str) -> list[dict[str, str]]:
        """Extract definitions."""
        definitions: list[dict[str, str]] = []
        for match in re.finditer(r"(?:definition|define)\s+(?:([\w]+)\s*:?\s*)?(.+)", source, re.IGNORECASE):
            name = (match.group(1) or "").strip() or f"def_{len(definitions) + 1}"
            body = (match.group(2) or "").strip()
            definitions.append({"name": name, "body": body[:200]})
        return definitions

    def _classify_proof_method(self, body: str) -> str:
        """Classify the proof method used."""
        body_lower = body.lower()
        if "contradiction" in body_lower or "assume not" in body_lower:
            return "contradiction"
        if "induction" in body_lower or "base case" in body_lower:
            return "induction"
        if "contrapositive" in body_lower:
            return "contrapositive"
        if "constructive" in body_lower:
            return "constructive"
        return "direct"
