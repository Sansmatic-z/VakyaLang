from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class StageTiming:
    name: str
    total_ms: float
    average_ms: float
    min_ms: float
    max_ms: float
    iterations: int

    def payload(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "total_ms": round(self.total_ms, 6),
            "average_ms": round(self.average_ms, 6),
            "min_ms": round(self.min_ms, 6),
            "max_ms": round(self.max_ms, 6),
            "iterations": self.iterations,
        }


@dataclass(frozen=True)
class VakPerformanceProfile:
    mode: str
    filename: str | None
    iterations: int
    stages: tuple[StageTiming, ...]
    total_ms: float

    def payload(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "filename": self.filename,
            "iterations": self.iterations,
            "total_ms": round(self.total_ms, 6),
            "stages": [stage.payload() for stage in self.stages],
        }

    def text(self) -> str:
        lines = [
            "वाक् प्रदर्शन प्रोफ़ाइल",
            f"मोड: {self.mode}",
            f"फ़ाइल: {self.filename or '<memory>'}",
            f"आवृत्तियाँ: {self.iterations}",
            f"कुल समय (ms): {round(self.total_ms, 3)}",
            "चरण:",
        ]
        for stage in self.stages:
            lines.append(
                "  - "
                f"{stage.name}: avg={round(stage.average_ms, 3)} ms, "
                f"min={round(stage.min_ms, 3)} ms, "
                f"max={round(stage.max_ms, 3)} ms, "
                f"total={round(stage.total_ms, 3)} ms"
            )
        return "\n".join(lines)


def aggregate_stage_samples(
    mode: str,
    filename: str | None,
    iterations: int,
    samples: dict[str, list[float]],
) -> VakPerformanceProfile:
    ordered_names = [name for name, values in samples.items() if values]
    stages = []
    for name in ordered_names:
        values = samples[name]
        total = sum(values)
        stages.append(
            StageTiming(
                name=name,
                total_ms=total,
                average_ms=total / len(values),
                min_ms=min(values),
                max_ms=max(values),
                iterations=len(values),
            )
        )
    total_ms = sum(stage.total_ms for stage in stages)
    return VakPerformanceProfile(
        mode=mode,
        filename=filename,
        iterations=iterations,
        stages=tuple(stages),
        total_ms=total_ms,
    )
