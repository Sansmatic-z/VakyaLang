"""
Codex Intermediate Representation (IR).

Defines the canonical data structures flowing through the
Codex Transformation Pipeline:

    DECODE → ANALYZE → NORMALIZE → TRANSFORM → VERIFY → ENCODE → DECOMPILE

Each stage consumes and produces IR nodes, maintaining provenance,
confidence scores, and diagnostic trails across the entire pipeline.

*Visionary RM (Raj Mitra)* ⚡
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


# ──────────────────────────────────────────────────────────────
# Language & Format Enumerations
# ──────────────────────────────────────────────────────────────

class SourceLanguage(str, Enum):
    """Recognised source languages for decoding."""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    C = "c"
    CPP = "cpp"
    JAVA = "java"
    GO = "go"
    RUST = "rust"
    VAK = "vak"
    JSON = "json"
    YAML = "yaml"
    TOML = "toml"
    XML = "xml"
    EBNF = "ebnf"
    PEG = "peg"
    NATURAL = "natural"
    UNKNOWN = "unknown"


class TargetFormat(str, Enum):
    """Supported output encoding formats."""
    VAK_SOURCE = "vak_source"
    VAK_BYTECODE = "vak_bytecode"
    JSON_ABI = "json_abi"
    DOCUMENTATION = "documentation"
    REPORT = "report"
    PYTHON = "python"
    JAVASCRIPT = "javascript"


class RiskLevel(str, Enum):
    """Security / safety risk classification."""
    SAFE = "safe"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Confidence(str, Enum):
    """Pipeline confidence levels (ordered low → high)."""
    DO_NOT_TOUCH = "do_not_touch"
    SUGGEST_ONLY = "suggest_only"
    SAFE_AUTO_FIX = "safe_auto_fix"
    VERIFIED = "verified"
    PROVEN = "proven"


# ──────────────────────────────────────────────────────────────
# Core IR Nodes
# ──────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class Symbol:
    """A single symbol extracted during analysis."""
    name: str
    kind: str  # "function", "class", "variable", "module", "type", etc.
    line: int = 0
    scope: str = "global"
    type_hint: str | None = None
    docstring: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ShapeFeature:
    """Structural feature of the source (complexity metrics)."""
    kind: str  # "nesting_depth", "cyclomatic", "loc", "fan_in", "fan_out"
    value: float
    threshold: float | None = None
    line: int = 0
    description: str = ""


@dataclass(frozen=True)
class RiskFinding:
    """A risk identified during analysis."""
    level: RiskLevel
    category: str  # "security", "complexity", "performance", "maintainability"
    message: str
    line: int = 0
    cwe_id: str | None = None  # Common Weakness Enumeration
    recommendation: str = ""


@dataclass(frozen=True)
class Construct:
    """A detected language construct (pattern, anti-pattern, idiom)."""
    name: str
    kind: str  # "design_pattern", "algorithm", "anti_pattern", "idiom"
    confidence: float  # 0.0 – 1.0
    line: int = 0
    captures: dict[str, str] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


# ──────────────────────────────────────────────────────────────
# Pipeline Stage Artifacts
# ──────────────────────────────────────────────────────────────

@dataclass
class DecodedIR:
    """Output of the DECODE stage — source → structured IR."""
    language: SourceLanguage
    source: str
    filename: str | None = None
    encoding: str = "utf-8"
    syntax_tree: dict[str, Any] | None = None  # Parsed AST (language-specific)
    tokens: list[dict[str, Any]] = field(default_factory=list)
    raw_metadata: dict[str, Any] = field(default_factory=dict)
    decode_errors: list[str] = field(default_factory=list)
    decode_warnings: list[str] = field(default_factory=list)

    @property
    def source_id(self) -> str:
        """Deterministic hash of the source for provenance tracking."""
        return hashlib.sha256(self.source.encode("utf-8")).hexdigest()[:16]


@dataclass
class AnalyzedIR:
    """Output of the ANALYZE stage — IR → symbols, shapes, risks, confidence."""
    decoded: DecodedIR
    symbols: list[Symbol] = field(default_factory=list)
    shapes: list[ShapeFeature] = field(default_factory=list)
    risks: list[RiskFinding] = field(default_factory=list)
    constructs: list[Construct] = field(default_factory=list)
    overall_confidence: Confidence = Confidence.SUGGEST_ONLY
    analysis_metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def symbol_table(self) -> dict[str, Symbol]:
        """Build a name → Symbol lookup."""
        return {s.name: s for s in self.symbols}

    @property
    def max_risk_level(self) -> RiskLevel:
        """Return the highest risk level found."""
        order = [RiskLevel.CRITICAL, RiskLevel.HIGH, RiskLevel.MEDIUM, RiskLevel.LOW, RiskLevel.SAFE]
        for level in order:
            if any(r.level == level for r in self.risks):
                return level
        return RiskLevel.SAFE


@dataclass
class NormalizedIR:
    """Output of the NORMALIZE stage — IR → canonical form."""
    analyzed: AnalyzedIR
    normalized_source: str
    repairs_applied: list[str] = field(default_factory=list)
    style: str = "canonical"  # "canonical", "pep8", "google", etc.
    is_valid: bool = True
    validation_errors: list[str] = field(default_factory=list)
    normalization_metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class TransformedIR:
    """Output of the TRANSFORM stage — IR → target IR (usually Vak)."""
    normalized: NormalizedIR | None
    target_source: str
    target_language: SourceLanguage = SourceLanguage.VAK
    constructs_mapped: list[str] = field(default_factory=list)
    transforms_applied: list[str] = field(default_factory=list)
    transform_metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class VerificationResult:
    """Output of the VERIFY stage — target → validation results."""
    transformed: TransformedIR
    parse_valid: bool = True
    compile_valid: bool = True
    type_valid: bool = True
    proof_valid: bool = True
    audit_valid: bool = True
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    verification_metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def all_valid(self) -> bool:
        return all([
            self.parse_valid, self.compile_valid,
            self.type_valid, self.proof_valid, self.audit_valid,
        ])


@dataclass
class EncodedArtifact:
    """Output of the ENCODE stage — target IR → output artifacts."""
    verified: VerificationResult
    format: TargetFormat
    content: bytes | str
    filename: str
    checksum: str = ""
    encoding_metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.checksum and self.content:
            data = self.content if isinstance(self.content, bytes) else self.content.encode("utf-8")
            self.checksum = hashlib.sha256(data).hexdigest()[:16]


@dataclass
class DecompiledResult:
    """Output of the DECOMPILE stage — bytecode → source."""
    artifact: EncodedArtifact | None
    decompiled_source: str
    confidence: float  # 0.0 – 1.0
    decompiler_name: str = ""
    decompiler_version: str = ""
    warnings: list[str] = field(default_factory=list)
    unsupported_ops: list[str] = field(default_factory=list)
    decompile_metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_faithful(self) -> bool:
        """Whether the decompiled source is likely faithful to the original."""
        return self.confidence >= 0.8 and len(self.unsupported_ops) == 0


# ──────────────────────────────────────────────────────────────
# Pipeline Configuration & Manifest
# ──────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class PipelineConfig:
    """Configuration for a full pipeline run."""
    source_language: SourceLanguage = SourceLanguage.UNKNOWN
    target_format: TargetFormat = TargetFormat.VAK_SOURCE
    target_language: SourceLanguage = SourceLanguage.VAK
    max_passes: int = 3
    timeout_seconds: float = 30.0
    strict_mode: bool = False  # Fail on any warning
    skip_decompile: bool = True
    skip_proof: bool = False
    style_guide: str = "canonical"
    extra_options: dict[str, Any] = field(default_factory=dict)


@dataclass
class PipelineManifest:
    """End-to-end pipeline execution manifest."""
    source_id: str
    config: PipelineConfig
    stages_run: list[str] = field(default_factory=list)
    stages_skipped: list[str] = field(default_factory=list)
    total_time_ms: float = 0.0
    diagnostics: list[str] = field(default_factory=list)

    def payload(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "config": {
                "source_language": self.config.source_language.value,
                "target_format": self.config.target_format.value,
                "target_language": self.config.target_language.value,
                "max_passes": self.config.max_passes,
                "strict_mode": self.config.strict_mode,
            },
            "stages_run": self.stages_run,
            "stages_skipped": self.stages_skipped,
            "total_time_ms": self.total_time_ms,
            "diagnostics": self.diagnostics,
        }
