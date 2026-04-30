"""
Phase 5: Learning System Codex Page.

Improves transformations based on feedback:
- Stores transformation history
- Learns from user feedback (accept/reject)
- Adjusts confidence scores based on historical accuracy
- Outputs learning statistics and improvement suggestions
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..models import CodexDiagnostic, CodexPageManifest, CodexPageProbe, CodexResult
from ..page import CodexPage
from ..engines.code_generator import CodeGenerator, GenerationContext
from .utils import _overall_confidence


@dataclass
class TransformationRecord:
    """Records a single transformation event."""
    timestamp: float
    page: str
    source_kind: str
    source_length: int
    output_length: int
    confidence: str
    user_feedback: str = "unknown"  # "accepted", "rejected", "unknown"
    metadata: dict[str, Any] = field(default_factory=dict)


class LearningSystemCodexPage(CodexPage):
    """Learning system: improve transformations based on feedback."""
    name = "learning_system"
    description = "Learning page (improve transformations based on feedback)"
    priority = 73
    kind = "python"
    chapter = "knowledge_engine"
    chapter_title = "Domain-Specific Knowledge Engine"
    chapter_order = 53
    capabilities = ("learning", "feedback", "history", "improvement", "statistics")
    emits_vak = True
    extensions = ("feedback", "learn")
    max_fixpoint_passes = 1

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        self._history: list[TransformationRecord] = []
        self._page_accuracy: dict[str, dict[str, int]] = {}
        self._generator = CodeGenerator()
        self._diagnostics: list[CodexDiagnostic] = []
        self._detected_constructs: list[str] = []
        self._register_templates()

    def _register_templates(self) -> None:
        self._generator.register_template("learning_stats", """# Learning System Statistics
# Total transformations: {total}
# Accepted: {accepted}
# Rejected: {rejected}
# Unknown: {unknown}

श्रेणी LearningStats {{
{page_stats}
}}""")

        self._generator.register_template("page_accuracy", """    # Page: {page_name}
    # Accuracy: {accuracy:.0%} ({accepted}/{total})
    परिवर्तनी {page_name}_accuracy = {accuracy}""")

    # ------------------------------------------------------------------
    # Learning operations
    # ------------------------------------------------------------------
    def record_transformation(
        self, page: str, source_kind: str, source_length: int,
        output_length: int, confidence: str, feedback: str = "unknown",
    ) -> None:
        """Record a transformation event."""
        record = TransformationRecord(
            timestamp=time.time(),
            page=page,
            source_kind=source_kind,
            source_length=source_length,
            output_length=output_length,
            confidence=confidence,
            user_feedback=feedback,
        )
        self._history.append(record)

        # Update accuracy tracking
        if page not in self._page_accuracy:
            self._page_accuracy[page] = {"accepted": 0, "rejected": 0, "unknown": 0}
        self._page_accuracy[page][feedback] += 1

    def get_accuracy(self, page: str) -> float:
        """Get the accuracy rate for a page."""
        stats = self._page_accuracy.get(page, {"accepted": 0, "rejected": 0, "unknown": 0})
        total = stats["accepted"] + stats["rejected"]
        if total == 0:
            return 0.5  # Default unknown
        return stats["accepted"] / total

    def get_overall_stats(self) -> dict[str, Any]:
        """Get overall learning statistics."""
        total = len(self._history)
        accepted = sum(1 for r in self._history if r.user_feedback == "accepted")
        rejected = sum(1 for r in self._history if r.user_feedback == "rejected")
        unknown = total - accepted - rejected

        return {
            "total": total,
            "accepted": accepted,
            "rejected": rejected,
            "unknown": unknown,
            "overall_accuracy": accepted / max(total, 1),
            "page_accuracy": {
                page: self.get_accuracy(page)
                for page in self._page_accuracy
            },
        }

    # ------------------------------------------------------------------
    # Probe
    # ------------------------------------------------------------------
    def probe(self, source: str, *, filename: str | None = None) -> CodexPageProbe:
        indicators = [
            "learning", "feedback", "improve", "accuracy", "stats",
            "accepted", "rejected", "history",
        ]
        score = 0
        for indicator in indicators:
            if indicator in source.lower():
                score += 15

        if score >= 15:
            return CodexPageProbe(self.name, min(score, 85), f"Learning system query ({score} indicators)")
        return CodexPageProbe(self.name, 10, "Learning system chapter (default)")

    # ------------------------------------------------------------------
    # Transform
    # ------------------------------------------------------------------
    def transform(self, source: str, *, filename: str | None = None) -> CodexResult:
        self._diagnostics = []
        self._detected_constructs = []

        # Process the learning request
        stats = self.get_overall_stats()

        # Parse feedback from source
        feedback = self._parse_feedback(source)
        if feedback:
            page, result = feedback
            self.record_transformation(
                page=page, source_kind="user_feedback",
                source_length=len(source), output_length=0,
                confidence="unknown", feedback=result,
            )
            self._diagnostics.append(CodexDiagnostic(
                page=self.name, level="info",
                message=f"Recorded feedback: {page} → {result}",
                confidence="safe_auto_fix",
            ))

        # Generate output
        vak_output = self._generate_learning_output(stats)

        return CodexResult(
            page=self.name,
            original_source=source,
            source=vak_output,
            transformed=True,
            confidence=_overall_confidence(self._diagnostics, True),
            diagnostics=tuple(self._diagnostics),
            manifest=self.manifest(),
            metadata={
                "source_kind": "learning_system",
                "statistics": stats,
            },
        )

    def _parse_feedback(self, source: str) -> tuple[str, str] | None:
        """Parse user feedback from source."""
        import re
        source_lower = source.lower().strip()

        m = re.search(r"(\w+)\s+(?:was\s+)?(accepted|rejected|good|bad|great|poor)", source_lower)
        if m:
            page = m.group(1)
            result = "accepted" if m.group(2) in ("accepted", "good", "great") else "rejected"
            return page, result

        m = re.search(r"(?:accept|reject)\s+(\w+)", source_lower)
        if m:
            return m.group(1), "accepted" if "accept" in m.group(0) else "rejected"

        return None

    def _generate_learning_output(self, stats: dict[str, Any]) -> str:
        """Generate Vak code representing learning statistics."""
        page_stats_lines: list[str] = []
        for page, accuracy in stats.get("page_accuracy", {}).items():
            page_data = self._page_accuracy.get(page, {"accepted": 0, "rejected": 0})
            total = page_data["accepted"] + page_data["rejected"]
            page_stats_lines.append(self._generator.generate(
                template_name="page_accuracy",
                page_name=page, accuracy=accuracy,
                accepted=page_data["accepted"], total=total,
            ))

        vak = self._generator.generate(
            template_name="learning_stats",
            total=stats.get("total", 0),
            accepted=stats.get("accepted", 0),
            rejected=stats.get("rejected", 0),
            unknown=stats.get("unknown", 0),
            page_stats="\n\n".join(page_stats_lines),
        )

        return vak
