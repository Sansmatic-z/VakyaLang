from __future__ import annotations

import importlib
from pathlib import Path
from typing import Callable

from branches.admission import (
    BranchManifest,
    BranchRecord,
    discover_branch_manifests,
    validate_manifest,
)
from runtime.src.audit import emit_audit_event
from runtime.src.branching import BranchActivationError, BranchRuntime, VakBranch


BranchFactory = Callable[[], VakBranch]


class BranchRegistry:
    """Load Vak branches without creating a dependency from trunk to any branch."""

    def __init__(self, branch_root: Path | None = None):
        self.branch_root = branch_root or Path(__file__).resolve().parent
        self._factories: dict[str, BranchFactory] = {}
        self._records: dict[str, BranchRecord] = {}
        self._discover_and_register_manifests()

    def register_factory(self, name: str, factory: BranchFactory) -> None:
        if not name:
            raise BranchActivationError("Branch name cannot be empty")
        self._factories[name] = factory
        emit_audit_event("vak.branch.factory.register", name, getattr(factory, "__name__", repr(factory)))
        record = self._records.get(name)
        if record is None:
            self._records[name] = BranchRecord(
                name=name,
                state="registered",
                source="runtime",
                factory_origin=getattr(factory, "__name__", repr(factory)),
            )
        else:
            record.factory_origin = getattr(factory, "__name__", repr(factory))
            if record.state != "quarantined":
                record.state = "registered"

    def register_branch_class(self, branch_class: type[VakBranch]) -> None:
        self.register_factory(branch_class.name, branch_class)

    def default_branch_names(self) -> tuple[str, ...]:
        return tuple(
            name
            for name, record in sorted(self._records.items())
            if record.state == "registered"
            and record.manifest is not None
            and record.manifest.default_activation
        )

    def branch_report(self) -> dict[str, dict[str, object]]:
        return {
            name: record.as_dict()
            for name, record in sorted(self._records.items())
        }

    def manifest_for(self, name: str) -> BranchManifest | None:
        record = self._records.get(name)
        return None if record is None else record.manifest

    def resolve_names(
        self,
        names: list[str] | None = None,
        *,
        include_defaults: bool = False,
    ) -> list[str]:
        ordered_names: list[str] = []
        seen: set[str] = set()

        sources = []
        if include_defaults:
            sources.append(self.default_branch_names())
        if names:
            sources.append(names)

        def add_name(name: str) -> None:
            if name in seen:
                return

            record = self._require_registered_record(name)
            manifest = record.manifest

            if manifest is not None:
                for dep_name in manifest.depends_on:
                    add_name(dep_name)

            ordered_names.append(name)
            seen.add(name)

        for source in sources:
            for name in source:
                add_name(name)

        self._validate_conflicts(ordered_names)
        return ordered_names

    def create(self, name: str) -> VakBranch:
        self._require_registered_record(name)
        factory = self._factories.get(name)
        if factory is None:
            factory = self._load_factory(name)
            self._factories[name] = factory

        branch = factory()
        if not isinstance(branch, VakBranch):
            raise BranchActivationError(
                f"Branch '{name}' did not produce a VakBranch instance"
            )
        if branch.name != name:
            raise BranchActivationError(
                f"Branch factory mismatch: requested '{name}', got '{branch.name}'"
            )
        return branch

    def create_runtime(
        self,
        names: list[str] | None = None,
        *,
        include_defaults: bool = False,
    ) -> BranchRuntime:
        branches = [
            self.create(name)
            for name in self.resolve_names(
                names,
                include_defaults=include_defaults,
            )
        ]
        return BranchRuntime(branches)

    def _load_factory(self, name: str) -> BranchFactory:
        record = self._require_registered_record(name)
        if record.manifest is None:
            module_name = f"branches.{name}"
        else:
            module_name = record.manifest.entrypoint
        try:
            module = importlib.import_module(module_name)
        except ModuleNotFoundError as exc:
            if exc.name == module_name:
                raise BranchActivationError(f"Unknown Vak branch: {name}") from exc
            raise

        factory = getattr(module, "create_branch", None)
        if callable(factory):
            return factory

        branch_class = getattr(module, "BRANCH_CLASS", None)
        if isinstance(branch_class, type) and issubclass(branch_class, VakBranch):
            return branch_class

        raise BranchActivationError(
            f"Branch module '{module_name}' must expose create_branch() or BRANCH_CLASS"
        )

    def _discover_and_register_manifests(self) -> None:
        manifests, rejected = discover_branch_manifests(self.branch_root)
        for record in rejected:
            self._records[record.name] = record

        known_names = {manifest.name for manifest in manifests}
        for manifest in manifests:
            issues = validate_manifest(manifest, known_names=known_names)
            if issues:
                self._records[manifest.name] = BranchRecord(
                    name=manifest.name,
                    state="quarantined",
                    manifest=manifest,
                    issues=issues,
                    source=str(manifest.manifest_path),
                )
                emit_audit_event("vak.branch.quarantine", manifest.name, issues)
                continue

            self._records[manifest.name] = BranchRecord(
                name=manifest.name,
                state="registered",
                manifest=manifest,
                source=str(manifest.manifest_path),
            )
            emit_audit_event("vak.branch.manifest.registered", manifest.name, manifest.kind)

        self._quarantine_dependency_cycles()

    def _require_registered_record(self, name: str) -> BranchRecord:
        record = self._records.get(name)
        if record is None:
            raise BranchActivationError(f"Unknown Vak branch: {name}")
        if record.state == "quarantined":
            details = "; ".join(record.issues) if record.issues else "verification failed"
            raise BranchActivationError(
                f"Vak branch '{name}' is quarantined: {details}"
            )
        if record.state != "registered":
            raise BranchActivationError(
                f"Vak branch '{name}' is not registered (state={record.state})"
            )
        return record

    def _validate_conflicts(self, names: list[str]) -> None:
        active = set(names)
        for name in names:
            manifest = self.manifest_for(name)
            if manifest is None:
                continue
            conflicts = sorted(active & set(manifest.conflicts_with))
            if conflicts:
                raise BranchActivationError(
                    f"Vak branch '{name}' conflicts with active branches: {', '.join(conflicts)}"
                )

    def _quarantine_dependency_cycles(self) -> None:
        manifests = {
            name: record.manifest
            for name, record in self._records.items()
            if record.state == "registered" and record.manifest is not None
        }
        visit_state: dict[str, int] = {}
        stack: list[str] = []
        cycle_names: set[str] = set()

        def visit(name: str) -> None:
            state = visit_state.get(name, 0)
            if state == 1:
                if name in stack:
                    cycle_names.update(stack[stack.index(name):])
                return
            if state == 2:
                return

            visit_state[name] = 1
            stack.append(name)
            manifest = manifests.get(name)
            if manifest is not None:
                for dep_name in manifest.depends_on:
                    if dep_name in manifests:
                        visit(dep_name)
            stack.pop()
            visit_state[name] = 2

        for name in sorted(manifests):
            visit(name)

        for name in sorted(cycle_names):
            record = self._records[name]
            record.state = "quarantined"
            record.issues.append("dependency cycle detected")
            emit_audit_event("vak.branch.quarantine", name, record.issues)


def create_default_registry() -> BranchRegistry:
    return BranchRegistry()
