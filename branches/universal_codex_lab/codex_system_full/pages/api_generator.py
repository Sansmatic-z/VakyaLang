"""
Phase 3: API Generator Codex Page.

Generates complete REST/GraphQL API implementations from specifications:
- Parses API spec (JSON/YAML-like format)
- Generates endpoints, handlers, models, routes
- Outputs valid Vak code with proper routing structure
- Supports REST and GraphQL styles
"""
from __future__ import annotations

import json
import re
from typing import Any

from ..models import CodexDiagnostic, CodexPageManifest, CodexPageProbe, CodexResult
from ..page import CodexPage
from ..engines.code_generator import CodeGenerator, GenerationContext
from .utils import _overall_confidence
from ..vak_surface import normalize_vak_surface


class APIGeneratorCodexPage(CodexPage):
    """Generates REST/GraphQL APIs from specification descriptions."""
    name = "api_generator"
    description = "API generator page (REST/GraphQL from spec)"
    priority = 50
    kind = "api_generator"
    chapter = "generators"
    chapter_title = "System Generators"
    chapter_order = 30
    capabilities = ("generate", "api", "rest", "graphql", "crud")
    emits_vak = True
    extensions = ("json", "yaml", "yml", "api", "spec")
    max_fixpoint_passes = 2
    max_source_length = 200_000

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        self._generator = CodeGenerator()
        self._diagnostics: list[CodexDiagnostic] = []
        self._detected_constructs: list[str] = []
        self._register_templates()

    def _register_templates(self) -> None:
        self._generator.register_template("rest_endpoint", """# REST Endpoint: {method} {path}
कर्म {handler_name}({params}) {{
    # Handle {method} {path}
    # Parameters: {params}
    # Returns: {response_type}
    प्रत्यागच्छ शून्य
}}""")
        self._generator.register_template("rest_router", """# Router: {resource}
वर्ग {resource_class}Router {{
    कर्म routes() {{
        प्रत्यागच्छ {{
{routes}
        }}
    }}
}}""")
        self._generator.register_template("graphql_schema", """# GraphQL Schema
वर्ग {type_name}Type {{
{fields}
}}""")
        self._generator.register_template("model_class", """# Model: {model_name}
वर्ग {model_name} {{
{fields}
    कर्म validate() {{
        # Validation logic
        प्रत्यागच्छ सत्य
    }}
    कर्म to_dict() {{
        प्रत्यागच्छ {{{dict_fields}}}
    }}
}}""")

    # ------------------------------------------------------------------
    # Probe
    # ------------------------------------------------------------------
    def probe(self, source: str, *, filename: str | None = None) -> CodexPageProbe:
        indicators = [
            "endpoint", "route", "api", "REST", "GraphQL", "graphql",
            "GET", "POST", "PUT", "DELETE", "PATCH",
            "schema", "type", "query", "mutation",
            "/api/", "crud", "CRUD",
        ]
        score = 0
        for indicator in indicators:
            if indicator in source:
                score += 10

        if filename and filename.endswith((".json", ".yaml", ".yml", ".api", ".spec")):
            score += 30

        if score >= 20:
            return CodexPageProbe(self.name, min(score, 90), f"API specification detected ({score} indicators)")
        return CodexPageProbe(self.name, 0, "not an API spec candidate")

    # ------------------------------------------------------------------
    # Transform
    # ------------------------------------------------------------------
    def transform(self, source: str, *, filename: str | None = None) -> CodexResult:
        self._diagnostics = []
        self._detected_constructs = []

        if len(source) > getattr(self, "max_source_length", 200_000):
            self._diagnostics.append(CodexDiagnostic(
                page=self.name, level="error",
                message=f"Source too large ({len(source)} bytes, max {getattr(self, 'max_source_length', 200_000)})",
                confidence="do_not_touch",
            ))
            return CodexResult(
                page=self.name, original_source=source, source=source,
                transformed=False, confidence="do_not_touch",
                diagnostics=tuple(self._diagnostics), manifest=self.manifest(),
                metadata={"source_kind": "api_spec", "error": "source_too_large"},
            )

        try:
            # Parse the spec
            spec = self._parse_spec(source)
            if spec is None:
                return self._no_transform(source, "Could not parse API specification")

            # Generate code based on spec type
            if spec.get("type") == "rest":
                vak_code = self._generate_rest_api(spec)
            elif spec.get("type") == "graphql":
                vak_code = self._generate_graphql_api(spec)
            elif spec.get("type") == "mixed":
                vak_code = self._generate_mixed_api(spec)
            else:
                vak_code = self._generate_rest_api(spec)  # Default to REST

            transformed = vak_code != source

            return CodexResult(
                page=self.name,
                original_source=source,
                source=vak_code,
                transformed=transformed,
                confidence=_overall_confidence(self._diagnostics, transformed),
                diagnostics=tuple(self._diagnostics),
                manifest=self.manifest(),
                metadata={
                    "source_kind": "api_spec",
                    "api_type": f"{spec.get('type', 'rest')} {spec.get('endpoints', [{}])[0].get('method', '')}" if spec.get('endpoints') else spec.get('type', 'rest'),
                    "endpoints_count": len(spec.get("endpoints", [])),
                    "models_count": len(spec.get("models", [])),
                },
            )
        except Exception as exc:
            return self._no_transform(source, str(exc))

    def _no_transform(self, source: str, reason: str) -> CodexResult:
        self._diagnostics.append(CodexDiagnostic(
            page=self.name, level="error", message=reason, confidence="do_not_touch",
        ))
        return CodexResult(
            page=self.name, original_source=source, source=source,
            transformed=False, confidence="do_not_touch",
            diagnostics=tuple(self._diagnostics), manifest=self.manifest(),
            metadata={"source_kind": "api_spec", "error": reason},
        )

    # ------------------------------------------------------------------
    # Spec parsing
    # ------------------------------------------------------------------
    def _parse_spec(self, source: str) -> dict[str, Any] | None:
        """Parse API specification from various formats."""
        # Try JSON first
        try:
            data = json.loads(source)
            return self._normalize_spec(data)
        except (json.JSONDecodeError, ValueError):
            pass

        # Try YAML-like format (key: value pairs)
        parsed_yaml = self._parse_yaml_like(source)
        if parsed_yaml and self._looks_like_api_spec(parsed_yaml):
            return self._normalize_spec(parsed_yaml)

        # Try parsing as a descriptive format
        return self._parse_descriptive_spec(source)

    @staticmethod
    def _looks_like_api_spec(data: dict[str, Any]) -> bool:
        """Check if a parsed dict looks like an API specification."""
        api_keys = {"endpoints", "routes", "models", "types", "entities", "api", "rest", "graphql"}
        return bool(api_keys & set(data.keys()))

    def _parse_yaml_like(self, source: str) -> dict[str, Any] | None:
        """Parse a simple YAML-like API specification."""
        try:
            import yaml
            data = yaml.safe_load(source)
            if isinstance(data, dict):
                return data
        except ImportError:
            pass
        except Exception:
            pass

        # Manual YAML-like parsing fallback
        result: dict[str, Any] = {}
        current_section: str | None = None
        current_item: dict[str, Any] | None = None

        for line in source.split("\n"):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue

            # Top-level key
            if not line.startswith(" ") and ":" in stripped:
                key, _, value = stripped.partition(":")
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key in ("endpoints", "routes", "models", "types", "entities"):
                    result[key] = result.get(key, [])
                    current_section = key
                    current_item = None
                else:
                    result[key] = value
                    current_section = None
                    current_item = None
            elif current_section and stripped.startswith("- "):
                # List item
                item_content = stripped[2:].strip()
                if ":" in item_content:
                    key, _, value = item_content.partition(":")
                    current_item = {key.strip(): value.strip().strip('"').strip("'")}
                    result[current_section].append(current_item)
                elif current_item is not None:
                    result[current_section].append(item_content)
            elif current_item and ":" in stripped:
                key, _, value = stripped.partition(":")
                current_item[key.strip()] = value.strip().strip('"').strip("'")

        return result if result else None

    def _normalize_spec(self, data: dict) -> dict[str, Any]:
        """Normalize a parsed JSON spec into our internal format."""
        spec: dict[str, Any] = {
            "type": data.get("type", "rest"),
            "name": data.get("name", "API"),
            "version": data.get("version", "1.0.0"),
            "endpoints": [],
            "models": [],
        }

        # Parse endpoints
        for ep in data.get("endpoints", data.get("routes", [])):
            handler = ep.get("handler", ep.get("function", "")).strip()
            if not handler:
                handler = self._path_to_handler(
                    ep.get("path", ep.get("url", "/")),
                    ep.get("method", "GET").upper(),
                )
            spec["endpoints"].append({
                "method": ep.get("method", "GET").upper(),
                "path": ep.get("path", ep.get("url", "/")),
                "handler": handler,
                "params": ep.get("params", ep.get("parameters", [])),
                "response": ep.get("response", ep.get("returns", {})),
            })

        # Parse models
        for model in data.get("models", data.get("types", data.get("entities", []))):
            spec["models"].append({
                "name": model.get("name", model.get("type", "Model")),
                "fields": model.get("fields", model.get("properties", [])),
            })

        return spec

    def _parse_descriptive_spec(self, source: str) -> dict[str, Any] | None:
        """Parse a natural language API description."""
        spec: dict[str, Any] = {"type": "rest", "name": "API", "version": "1.0.0", "endpoints": [], "models": []}

        for line in source.split("\n"):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue

            # Endpoint: GET /users
            m = re.match(r"(GET|POST|PUT|DELETE|PATCH)\s+(/\S+)", stripped, re.IGNORECASE)
            if m:
                spec["endpoints"].append({
                    "method": m.group(1).upper(),
                    "path": m.group(2),
                    "handler": self._path_to_handler(m.group(2), m.group(1).upper()),
                    "params": [],
                    "response": {},
                })
                continue

            # Model: User { name: string, age: int }
            m = re.match(r"model\s+(\w+)\s*\{?\s*(.+)", stripped, re.IGNORECASE)
            if m:
                fields_str = m.group(2).strip("{} ").strip()
                fields = [f.strip() for f in fields_str.split(",") if f.strip()]
                spec["models"].append({"name": m.group(1), "fields": fields})

        if spec["endpoints"] or spec["models"]:
            return spec
        return None

    @staticmethod
    def _path_to_handler(path: str, method: str) -> str:
        """Convert a URL path to a handler function name."""
        parts = path.strip("/").split("/")
        resource = parts[0] if parts else "root"
        # Singularize
        if resource.endswith("s"):
            resource = resource[:-1]

        action_map = {
            "GET": "get",
            "POST": "create",
            "PUT": "update",
            "DELETE": "delete",
            "PATCH": "patch",
        }
        action = action_map.get(method, "handle")
        return f"{action}_{resource}"

    # ------------------------------------------------------------------
    # Code generation
    # ------------------------------------------------------------------
    def _generate_rest_api(self, spec: dict[str, Any]) -> str:
        """Generate REST API Vak code."""
        lines: list[str] = []
        lines.append(f"# REST API: {spec.get('name', 'API')} v{spec.get('version', '1.0.0')}")
        lines.append("")

        # Generate models
        for model in spec.get("models", []):
            name = model["name"]
            self._detected_constructs.append(f"model:{name}")
            fields = ""
            dict_fields = ""
            for field in model.get("fields", []):
                fname = field.split(":")[0].strip() if ":" in field else field
                fields += f"    चर {fname} = शून्य\n"
                dict_fields += f'"{fname}": {fname}, '
            dict_fields = dict_fields.rstrip(", ")

            vak = self._generator.generate(
                template_name="model_class",
                model_name=name, fields=fields, dict_fields=dict_fields or "{}",
            )
            lines.append(vak)
            lines.append("")

        # Generate endpoints
        for ep in spec.get("endpoints", []):
            method = ep["method"]
            path = ep["path"]
            handler = ep.get("handler", self._path_to_handler(path, method))
            params = ", ".join(ep.get("params", ["request"]))
            response_type = ep.get("response", {}).get("type", "object")

            self._detected_constructs.append(f"endpoint:{method} {path}")
            self._diagnostics.append(CodexDiagnostic(
                page=self.name, level="info",
                message=f"Generated endpoint: {method} {path} → {handler}",
                confidence="safe_auto_fix",
            ))

            vak = self._generator.generate(
                template_name="rest_endpoint",
                method=method, path=path, handler_name=handler,
                params=params, response_type=response_type,
            )
            lines.append(vak)
            lines.append("")

        return normalize_vak_surface("\n".join(lines))

    def _generate_graphql_api(self, spec: dict[str, Any]) -> str:
        """Generate GraphQL API Vak code."""
        lines: list[str] = []
        lines.append(f"# GraphQL API: {spec.get('name', 'API')} v{spec.get('version', '1.0.0')}")
        lines.append("")

        # Generate types
        for model in spec.get("models", []):
            name = model["name"]
            fields = ""
            for field in model.get("fields", []):
                fname = field.split(":")[0].strip() if ":" in field else field
                ftype = field.split(":")[1].strip() if ":" in field else "Any"
                fields += f"    # क्षेत्र {fname}: {ftype}\n"

            vak = self._generator.generate(
                template_name="graphql_schema",
                type_name=name, fields=fields,
            )
            lines.append(vak)
            lines.append("")

        # Generate resolvers
        for ep in spec.get("endpoints", []):
            handler = ep.get("handler", "resolver")
            path = ep["path"]
            self._detected_constructs.append(f"resolver:{path}")
            lines.append(f"कर्म {handler}():")
            lines.append("    # GraphQL resolver")
            lines.append("    प्रत्यागच्छ शून्य")
            lines.append("")

        return normalize_vak_surface("\n".join(lines))

    def _generate_mixed_api(self, spec: dict[str, Any]) -> str:
        """Generate mixed REST + GraphQL API."""
        rest_part = self._generate_rest_api(spec)
        graphql_part = self._generate_graphql_api(spec)
        return f"{rest_part}\n\n# --- GraphQL Layer ---\n\n{graphql_part}"
