from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Any


BRANCH_API_VERSION = "1"
BRANCH_MANIFEST_FILENAME = "branch.json"
ALLOWED_BRANCH_KINDS = {
    "validation",
    "runtime",
    "library",
    "semantic",
    "experimental",
}
ALLOWED_CAPABILITIES = {
    "observe_program",
    "before_compile",
    "after_typecheck",
    "after_compile",
    "vm_builtins",
    "rupantar_rules",
}
BRANCH_STATES = {
    "discovered",
    "verified",
    "registered",
    "quarantined",
}


@dataclass(frozen=True)
class BranchManifest:
    name: str
    version: str
    api_version: str
    kind: str
    entrypoint: str
    capabilities: tuple[str, ...] = ()
    depends_on: tuple[str, ...] = ()
    conflicts_with: tuple[str, ...] = ()
    default_activation: bool = False
    branch_dir: Path = field(default=Path("."), compare=False)
    manifest_path: Path = field(default=Path("."), compare=False)

    @classmethod
    def from_path(cls, manifest_path: Path) -> "BranchManifest":
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        branch_dir = manifest_path.parent
        return cls(
            name=str(data["name"]),
            version=str(data["version"]),
            api_version=str(data["api_version"]),
            kind=str(data["kind"]),
            entrypoint=str(data["entrypoint"]),
            capabilities=tuple(str(item) for item in data.get("capabilities", [])),
            depends_on=tuple(str(item) for item in data.get("depends_on", [])),
            conflicts_with=tuple(str(item) for item in data.get("conflicts_with", [])),
            default_activation=bool(data.get("default_activation", False)),
            branch_dir=branch_dir,
            manifest_path=manifest_path,
        )


@dataclass
class BranchRecord:
    name: str
    state: str
    manifest: BranchManifest | None = None
    issues: list[str] = field(default_factory=list)
    source: str | None = None
    factory_origin: str | None = None

    def as_dict(self) -> dict[str, Any]:
        manifest_payload: dict[str, Any] | None = None
        if self.manifest is not None:
            manifest_payload = {
                "name": self.manifest.name,
                "version": self.manifest.version,
                "api_version": self.manifest.api_version,
                "kind": self.manifest.kind,
                "entrypoint": self.manifest.entrypoint,
                "capabilities": list(self.manifest.capabilities),
                "depends_on": list(self.manifest.depends_on),
                "conflicts_with": list(self.manifest.conflicts_with),
                "default_activation": self.manifest.default_activation,
                "manifest_path": str(self.manifest.manifest_path),
            }
        return {
            "name": self.name,
            "state": self.state,
            "issues": list(self.issues),
            "source": self.source,
            "factory_origin": self.factory_origin,
            "manifest": manifest_payload,
        }


def discover_branch_manifests(branch_root: Path) -> tuple[list[BranchManifest], list[BranchRecord]]:
    manifests: list[BranchManifest] = []
    rejected: list[BranchRecord] = []

    if not branch_root.exists():
        return manifests, rejected

    for entry in sorted(branch_root.iterdir(), key=lambda item: item.name):
        if not entry.is_dir():
            continue
        if entry.name.startswith("__"):
            continue

        manifest_path = entry / BRANCH_MANIFEST_FILENAME
        if not manifest_path.exists():
            rejected.append(
                BranchRecord(
                    name=entry.name,
                    state="quarantined",
                    issues=[f"missing {BRANCH_MANIFEST_FILENAME}"],
                    source=str(entry),
                )
            )
            continue

        try:
            manifest = BranchManifest.from_path(manifest_path)
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            rejected.append(
                BranchRecord(
                    name=entry.name,
                    state="quarantined",
                    issues=[f"invalid manifest: {exc}"],
                    source=str(manifest_path),
                )
            )
            continue

        manifests.append(manifest)

    return manifests, rejected


def validate_manifest(
    manifest: BranchManifest,
    *,
    known_names: set[str] | None = None,
) -> list[str]:
    issues: list[str] = []
    known_names = known_names or set()

    if not manifest.name:
        issues.append("manifest name cannot be empty")
    if manifest.name != manifest.branch_dir.name:
        issues.append("manifest name must match branch directory name")
    if not manifest.version:
        issues.append("manifest version cannot be empty")
    if manifest.api_version != BRANCH_API_VERSION:
        issues.append(
            f"unsupported api_version '{manifest.api_version}' (expected {BRANCH_API_VERSION})"
        )
    if manifest.kind not in ALLOWED_BRANCH_KINDS:
        issues.append(f"unsupported branch kind '{manifest.kind}'")
    if manifest.entrypoint != f"branches.{manifest.name}":
        issues.append("entrypoint must be 'branches.<name>'")
    if not (manifest.branch_dir / "__init__.py").exists():
        issues.append("branch package must define __init__.py")

    unknown_capabilities = sorted(set(manifest.capabilities) - ALLOWED_CAPABILITIES)
    if unknown_capabilities:
        issues.append(
            "unsupported capabilities: " + ", ".join(unknown_capabilities)
        )

    duplicate_deps = sorted(name for name in set(manifest.depends_on) if manifest.depends_on.count(name) > 1)
    if duplicate_deps:
        issues.append("duplicate depends_on entries: " + ", ".join(duplicate_deps))

    duplicate_conflicts = sorted(
        name for name in set(manifest.conflicts_with) if manifest.conflicts_with.count(name) > 1
    )
    if duplicate_conflicts:
        issues.append("duplicate conflicts_with entries: " + ", ".join(duplicate_conflicts))

    if manifest.name in manifest.depends_on:
        issues.append("branch cannot depend on itself")
    if manifest.name in manifest.conflicts_with:
        issues.append("branch cannot conflict with itself")
    if set(manifest.depends_on) & set(manifest.conflicts_with):
        overlap = sorted(set(manifest.depends_on) & set(manifest.conflicts_with))
        issues.append("branch cannot both depend on and conflict with: " + ", ".join(overlap))

    if manifest.default_activation and manifest.kind in {"semantic", "experimental"}:
        issues.append("semantic and experimental branches cannot auto-activate by default")

    unknown_refs = sorted(
        {name for name in (*manifest.depends_on, *manifest.conflicts_with) if name not in known_names}
    )
    if unknown_refs:
        issues.append("unknown branch references: " + ", ".join(unknown_refs))

    return issues
