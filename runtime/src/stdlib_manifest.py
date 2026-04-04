from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class StdlibModuleSpec:
    name: str
    path: Path
    tier: str = "main"
    canonical: str | None = None
    aliases: tuple[str, ...] = ()
    description: str = ""


_MANUAL_METADATA: dict[str, dict[str, object]] = {
    "colour_lib": {
        "tier": "compatibility",
        "canonical": "रंग_पुस्तकालय",
        "aliases": ("color_lib",),
        "description": "Full repaired compatibility color library; curated API lives in रंग_पुस्तकालय",
    },
    "रंग_पुस्तकालय": {
        "tier": "main",
        "canonical": "रंग_पुस्तकालय",
        "description": "Curated canonical color stdlib",
    },
    "गणित": {
        "canonical": "ganit",
        "aliases": ("ganit",),
        "description": "Legacy Sanskrit alias for ganit",
    },
    "गणित_विस्तारित": {
        "canonical": "ganit_vistarit",
        "aliases": ("ganit_vistarit",),
        "description": "Legacy Sanskrit alias for ganit_vistarit",
    },
    "भाषा_प्रसादन": {
        "canonical": "bhasha_prasadan",
        "aliases": ("bhasha_prasadan",),
    },
    "तर्क_शास्त्र": {
        "canonical": "tarka_shastra",
        "aliases": ("tarka_shastra",),
    },
    "संग्रह": {
        "canonical": "sangrah",
        "aliases": ("sangrah",),
    },
    "संग्रह_विस्तारित": {
        "canonical": "sangrah_vistarit",
        "aliases": ("sangrah_vistarit",),
    },
    "डेटा_संग्रह": {
        "canonical": "data_sangrah",
        "aliases": ("data_sangrah",),
    },
    "कंटेनर_संग्रह": {
        "canonical": "container_sangrah",
        "aliases": ("container_sangrah",),
    },
    "मैट्रिक्स_गणित": {
        "canonical": "matrix_ganit",
        "aliases": ("matrix_ganit",),
    },
    "संभावना": {
        "canonical": "sambhavana",
        "aliases": ("sambhavana",),
    },
    "उपयोगिता": {
        "canonical": "upayogita",
        "aliases": ("upayogita",),
    },
    "रेखा_गणित": {
        "canonical": "rekha_ganit",
        "aliases": ("rekha_ganit",),
    },
    "धागा": {
        "canonical": "dhaaga",
        "aliases": ("dhaaga",),
    },
    "फाइल": {
        "canonical": "file",
        "aliases": ("file",),
    },
    "कूटलेख": {
        "canonical": "kootlekh",
        "aliases": ("kootlekh",),
    },
    "नियमित": {
        "canonical": "niyamit",
        "aliases": ("niyamit",),
    },
    "मूल": {
        "canonical": "mool",
        "aliases": ("mool",),
    },
    "यादृच्छ": {
        "canonical": "yadricha",
        "aliases": ("yadricha",),
    },
    "यादृच्छा": {
        "canonical": "yadricha",
        "aliases": ("yadricha",),
    },
    "पायथन_ब्रिज": {
        "canonical": "py_bridge",
        "aliases": ("py_bridge",),
    },
    "उन्नत_सांख्यिकी": {
        "canonical": "unnata_sankhyiki",
        "aliases": ("unnata_sankhyiki",),
    },
}


def build_stdlib_manifest(stdlib_root: str | Path | None = None) -> dict[str, StdlibModuleSpec]:
    root = Path(stdlib_root) if stdlib_root is not None else Path(__file__).resolve().parent.parent / "stdlib"
    manifest: dict[str, StdlibModuleSpec] = {}

    if root.exists():
        for path in sorted(root.glob("*.vak")):
            name = path.stem
            metadata = _MANUAL_METADATA.get(name, {})
            manifest[name] = StdlibModuleSpec(
                name=name,
                path=path,
                tier=str(metadata.get("tier", "main")),
                canonical=str(metadata.get("canonical", name)),
                aliases=tuple(str(item) for item in metadata.get("aliases", ())),
                description=str(metadata.get("description", "")),
            )

    for alias_name, metadata in _MANUAL_METADATA.items():
        canonical = str(metadata.get("canonical", alias_name))
        canonical_spec = manifest.get(canonical)
        if canonical_spec is None:
            continue
        manifest.setdefault(
            alias_name,
            StdlibModuleSpec(
                name=alias_name,
                path=canonical_spec.path,
                tier=str(metadata.get("tier", "alias")),
                canonical=canonical,
                aliases=tuple(str(item) for item in metadata.get("aliases", ())),
                description=str(metadata.get("description", canonical_spec.description)),
            ),
        )

    return manifest


def module_alias_map(stdlib_root: str | Path | None = None) -> dict[str, str]:
    manifest = build_stdlib_manifest(stdlib_root)
    aliases: dict[str, str] = {}
    for spec in manifest.values():
        canonical = spec.canonical or spec.name
        if spec.name != canonical:
            aliases[spec.name] = canonical
        for alias in spec.aliases:
            aliases[alias] = canonical
            aliases.setdefault(alias.lower(), canonical)
    return aliases


def canonical_module_names(stdlib_root: str | Path | None = None) -> set[str]:
    manifest = build_stdlib_manifest(stdlib_root)
    return {spec.canonical or spec.name for spec in manifest.values()}


def format_stdlib_manifest(stdlib_root: str | Path | None = None) -> str:
    manifest = build_stdlib_manifest(stdlib_root)
    lines = ["वाक् मानक पुस्तकालय मानचित्र"]
    emitted: set[str] = set()
    for spec in sorted(manifest.values(), key=lambda item: (item.tier != "main", item.name)):
        if spec.name in emitted:
            continue
        emitted.add(spec.name)
        canonical = spec.canonical or spec.name
        suffix = ""
        if spec.name != canonical:
            suffix = f" -> canonical {canonical}"
        elif spec.aliases:
            suffix = f" | aliases: {', '.join(spec.aliases)}"
        lines.append(f"- {spec.name} [{spec.tier}]{suffix}")
    return "\n".join(lines)
