"""
Phase 3: Web App Generator Codex Page.

Generates complete web applications from specifications:
- Parses web app spec (pages, routes, components, state)
- Generates routing, components, state management
- Outputs valid Vak code with proper web app structure
"""
from __future__ import annotations

import json
import re
from typing import Any

from ..models import CodexDiagnostic, CodexPageManifest, CodexPageProbe, CodexResult
from ..page import CodexPage
from ..engines.code_generator import CodeGenerator, GenerationContext
from .utils import _overall_confidence


class WebAppGeneratorCodexPage(CodexPage):
    """Generates web applications from specification descriptions."""
    name = "webapp_generator"
    description = "Web application generator page"
    priority = 52
    kind = "python"
    chapter = "generators"
    chapter_title = "System Generators"
    chapter_order = 32
    capabilities = ("generate", "webapp", "web", "spa", "routing", "components")
    emits_vak = True
    extensions = ("json", "yaml", "yml", "web", "spec")
    max_fixpoint_passes = 2

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        self._generator = CodeGenerator()
        self._diagnostics: list[CodexDiagnostic] = []
        self._detected_constructs: list[str] = []
        self._register_templates()

    def _register_templates(self) -> None:
        self._generator.register_template("webapp_main", """# Web Application: {app_name}
# Version: {version}

कर्म init_app() {{
    router = create_router()
    store = create_store()
    लौटाओ {{router: router, store: store}}
}}""")

        self._generator.register_template("webapp_route", """# Route: {path}
कर्म {handler_name}() {{
    # Render {page_name}
    लौटाओ render_component("{component_name}")
}}""")

        self._generator.register_template("webapp_component", """# Component: {component_name}
श्रेणी {component_name} {{
    परिवर्तनी state = {}
    परिवर्तनी props = {}

    कर्म render() {{
        # Render {component_name}
        लौटाओ html
    }}

    कर्म update(new_state) {{
        state = new_state
        render()
    }}
}}""")

        self._generator.register_template("webapp_store", """# State Store: {store_name}
श्रेणी {store_name} {{
    परिवर्तनी state = {initial_state}

    कर्म get(key) {{
        लौटाओ state.get(key)
    }}

    कर्म set(key, value) {{
        state[key] = value
        notify_subscribers()
    }}

    कर्म subscribe(callback) {{
        subscribers.जोड़ें(callback)
    }}
}}""")

    # ------------------------------------------------------------------
    # Probe
    # ------------------------------------------------------------------
    def probe(self, source: str, *, filename: str | None = None) -> CodexPageProbe:
        indicators = [
            "webapp", "web_app", "webapp", "SPA", "spa",
            "component", "route", "page", "view",
            "state", "store", "reducer", "action",
            "react", "vue", "angular", "html",
        ]
        score = 0
        for indicator in indicators:
            if indicator in source.lower():
                score += 10

        if filename and filename.endswith((".json", ".yaml", ".yml", ".web", ".spec")):
            score += 30

        if score >= 20:
            return CodexPageProbe(self.name, min(score, 90), f"Web app specification detected ({score} indicators)")
        return CodexPageProbe(self.name, 0, "not a web app spec candidate")

    # ------------------------------------------------------------------
    # Transform
    # ------------------------------------------------------------------
    def transform(self, source: str, *, filename: str | None = None) -> CodexResult:
        self._diagnostics = []
        self._detected_constructs = []

        try:
            spec = self._parse_spec(source)
            if spec is None:
                return self._no_transform(source, "Could not parse web app specification")

            vak_code = self._generate_webapp(spec)

            return CodexResult(
                page=self.name,
                original_source=source,
                source=vak_code,
                transformed=True,
                confidence=_overall_confidence(self._diagnostics, True),
                diagnostics=tuple(self._diagnostics),
                manifest=self.manifest(),
                metadata={
                    "source_kind": "webapp_spec",
                    "app_name": spec.get("name", "unknown"),
                    "routes_count": len(spec.get("routes", [])),
                    "components_count": len(spec.get("components", [])),
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
            metadata={"source_kind": "webapp_spec", "error": reason},
        )

    # ------------------------------------------------------------------
    # Spec parsing
    # ------------------------------------------------------------------
    def _parse_spec(self, source: str) -> dict[str, Any] | None:
        try:
            data = json.loads(source)
            return self._normalize_spec(data)
        except (json.JSONDecodeError, ValueError):
            pass

        return self._parse_descriptive_spec(source)

    def _normalize_spec(self, data: dict) -> dict[str, Any]:
        return {
            "name": data.get("name", data.get("app_name", "webapp")),
            "version": data.get("version", "1.0.0"),
            "description": data.get("description", "Web application"),
            "routes": data.get("routes", data.get("pages", [])),
            "components": data.get("components", []),
            "state": data.get("state", data.get("store", {})),
        }

    def _parse_descriptive_spec(self, source: str) -> dict[str, Any] | None:
        spec: dict[str, Any] = {
            "name": "webapp", "version": "1.0.0",
            "description": "Web application", "routes": [],
            "components": [], "state": {},
        }

        for line in source.split("\n"):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue

            m = re.match(r"(?:route|page)\s+(/\S+)\s*(?:-|:)\s*(.+)", stripped, re.IGNORECASE)
            if m:
                spec["routes"].append({
                    "path": m.group(1),
                    "description": m.group(2),
                    "component": self._path_to_component(m.group(1)),
                })
                continue

            m = re.match(r"component\s+(\w+)", stripped, re.IGNORECASE)
            if m:
                spec["components"].append({"name": m.group(1)})

        if spec["routes"] or spec["components"]:
            return spec
        return None

    @staticmethod
    def _path_to_component(path: str) -> str:
        parts = path.strip("/").split("/")
        name = parts[0].capitalize() if parts else "Home"
        return f"{name}Page"

    # ------------------------------------------------------------------
    # Code generation
    # ------------------------------------------------------------------
    def _generate_webapp(self, spec: dict[str, Any]) -> str:
        lines: list[str] = []
        app_name = spec.get("name", "webapp")
        version = spec.get("version", "1.0.0")

        # Main entry
        lines.append(self._generator.generate(
            template_name="webapp_main",
            app_name=app_name, version=version,
        ))
        lines.append("")

        # Routes
        for route in spec.get("routes", []):
            path = route["path"]
            component = route.get("component", self._path_to_component(path))
            handler = f"route_{path.strip('/').replace('/', '_')}" or "route_home"

            self._detected_constructs.append(f"route:{path}")
            self._diagnostics.append(CodexDiagnostic(
                page=self.name, level="info",
                message=f"Generated route: {path} → {component}",
                confidence="safe_auto_fix",
            ))

            vak = self._generator.generate(
                template_name="webapp_route",
                path=path, handler_name=handler,
                page_name=path, component_name=component,
            )
            lines.append(vak)
            lines.append("")

        # Components
        for comp in spec.get("components", []):
            name = comp["name"]
            self._detected_constructs.append(f"component:{name}")

            vak = self._generator.generate(
                template_name="webapp_component",
                component_name=name,
            )
            lines.append(vak)
            lines.append("")

        # State store
        if spec.get("state"):
            lines.append(self._generator.generate(
                template_name="webapp_store",
                store_name="AppStore",
                initial_state=json.dumps(spec["state"]),
            ))

        return "\n".join(lines)
