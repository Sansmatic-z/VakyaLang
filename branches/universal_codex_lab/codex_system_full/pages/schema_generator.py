"""
Phase 3: Database Schema Generator Codex Page.

Generates database schemas from requirements:
- Parses schema requirements (tables, relationships, constraints)
- Generates table definitions, indexes, relationships
- Outputs valid Vak code with proper data structures
"""
from __future__ import annotations

import json
import re
from typing import Any

from ..models import CodexDiagnostic, CodexPageManifest, CodexPageProbe, CodexResult
from ..page import CodexPage
from ..engines.code_generator import CodeGenerator, GenerationContext
from .utils import _overall_confidence


class SchemaGeneratorCodexPage(CodexPage):
    """Generates database schemas from requirement descriptions."""
    name = "schema_generator"
    description = "Database schema generator page"
    priority = 53
    kind = "python"
    chapter = "generators"
    chapter_title = "System Generators"
    chapter_order = 33
    capabilities = ("generate", "database", "schema", "sql", "tables", "relationships")
    emits_vak = True
    extensions = ("json", "yaml", "yml", "sql", "schema", "spec")
    max_fixpoint_passes = 2

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        self._generator = CodeGenerator()
        self._diagnostics: list[CodexDiagnostic] = []
        self._detected_constructs: list[str] = []
        self._register_templates()

    def _register_templates(self) -> None:
        self._generator.register_template("table_def", """# Table: {table_name}
श्रेणी {table_name} {{
    # Primary key: {primary_key}
{columns}
    कर्म validate() {{
        # Validate constraints
        लौटाओ सत्य
    }}
}}""")

        self._generator.register_template("column_def", """    परिवर्तनी {col_name}: {col_type}  # {constraints}""")

        self._generator.register_template("relationship", """# Relationship: {from_table}.{from_col} -> {to_table}.{to_col}
कर्म {rel_name}({from_table}_id) {{
    # Fetch related {to_table} records
    लौटाओ related_records
}}""")

        self._generator.register_template("index_def", """# Index: {table_name}_{col_name}_idx
कर्म create_{index_name}_index() {{
    # Create index on {table_name}({col_name})
    लौटाओ index_created
}}""")

    # ------------------------------------------------------------------
    # Probe
    # ------------------------------------------------------------------
    def probe(self, source: str, *, filename: str | None = None) -> CodexPageProbe:
        indicators = [
            "table", "schema", "database", "column", "primary key",
            "foreign key", "index", "relationship", "CREATE TABLE",
            "varchar", "integer", "boolean", "timestamp",
            "many_to_many", "one_to_many", "belongs_to",
        ]
        score = 0
        for indicator in indicators:
            if indicator.lower() in source.lower():
                score += 10

        if filename and filename.endswith((".json", ".yaml", ".yml", ".sql", ".schema", ".spec")):
            score += 30

        if score >= 20:
            return CodexPageProbe(self.name, min(score, 90), f"Database schema detected ({score} indicators)")
        return CodexPageProbe(self.name, 0, "not a schema candidate")

    # ------------------------------------------------------------------
    # Transform
    # ------------------------------------------------------------------
    def transform(self, source: str, *, filename: str | None = None) -> CodexResult:
        self._diagnostics = []
        self._detected_constructs = []

        try:
            spec = self._parse_spec(source)
            if spec is None:
                return self._no_transform(source, "Could not parse database schema specification")

            vak_code = self._generate_schema(spec)

            return CodexResult(
                page=self.name,
                original_source=source,
                source=vak_code,
                transformed=True,
                confidence=_overall_confidence(self._diagnostics, True),
                diagnostics=tuple(self._diagnostics),
                manifest=self.manifest(),
                metadata={
                    "source_kind": "database_schema",
                    "tables_count": len(spec.get("tables", [])),
                    "relationships_count": len(spec.get("relationships", [])),
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
            metadata={"source_kind": "database_schema", "error": reason},
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
            "name": data.get("name", data.get("database", "schema")),
            "tables": data.get("tables", data.get("models", [])),
            "relationships": data.get("relationships", data.get("relations", [])),
            "indexes": data.get("indexes", []),
        }

    def _parse_descriptive_spec(self, source: str) -> dict[str, Any] | None:
        spec: dict[str, Any] = {
            "name": "schema", "tables": [], "relationships": [], "indexes": [],
        }

        current_table: dict[str, Any] | None = None

        for line in source.split("\n"):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue

            # Table definition
            m = re.match(r"table\s+(\w+)", stripped, re.IGNORECASE)
            if m:
                current_table = {"name": m.group(1), "columns": [], "primary_key": "id"}
                spec["tables"].append(current_table)
                continue

            # Column definition
            if current_table:
                m = re.match(r"(\w+)\s+(\w+)(.*)", stripped)
                if m:
                    col_name = m.group(1)
                    col_type = m.group(2)
                    constraints = m.group(3).strip()
                    if "primary" in constraints.lower() or "pk" in constraints.lower():
                        current_table["primary_key"] = col_name
                    current_table["columns"].append({
                        "name": col_name, "type": col_type, "constraints": constraints,
                    })

        if spec["tables"]:
            return spec
        return None

    # ------------------------------------------------------------------
    # Code generation
    # ------------------------------------------------------------------
    def _generate_schema(self, spec: dict[str, Any]) -> str:
        lines: list[str] = []
        lines.append(f"# Database Schema: {spec.get('name', 'schema')}")
        lines.append("")

        # Tables
        for table in spec.get("tables", []):
            name = table["name"]
            pk = table.get("primary_key", "id")
            columns_lines: list[str] = []

            # Add primary key
            columns_lines.append(f"    परिवर्तनी {pk}: integer  # primary key, auto_increment")

            for col in table.get("columns", []):
                col_name = col["name"]
                col_type = self._map_type(col.get("type", "string"))
                constraints = col.get("constraints", "")
                if col_name == pk:
                    continue

                columns_lines.append(self._generator.generate(
                    template_name="column_def",
                    col_name=col_name, col_type=col_type, constraints=constraints,
                ))

            self._detected_constructs.append(f"table:{name}")
            self._diagnostics.append(CodexDiagnostic(
                page=self.name, level="info",
                message=f"Generated table: {name} ({len(table.get('columns', []))} columns)",
                confidence="safe_auto_fix",
            ))

            vak = self._generator.generate(
                template_name="table_def",
                table_name=name, primary_key=pk,
                columns="\n".join(columns_lines),
            )
            lines.append(vak)
            lines.append("")

        # Relationships
        for rel in spec.get("relationships", []):
            from_table = rel.get("from_table", rel.get("source", ""))
            to_table = rel.get("to_table", rel.get("target", ""))
            from_col = rel.get("from_col", rel.get("source_key", f"{from_table}_id"))
            to_col = rel.get("to_col", rel.get("target_key", "id"))

            rel_name = f"get_{to_table.lower()}"
            self._detected_constructs.append(f"relationship:{from_table}->{to_table}")

            vak = self._generator.generate(
                template_name="relationship",
                from_table=from_table, from_col=from_col,
                to_table=to_table, to_col=to_col, rel_name=rel_name,
            )
            lines.append(vak)
            lines.append("")

        return "\n".join(lines)

    @staticmethod
    def _map_type(type_str: str) -> str:
        """Map common type names to Vak types."""
        type_map = {
            "string": "string", "str": "string", "varchar": "string",
            "int": "integer", "integer": "integer", "number": "number",
            "float": "decimal", "double": "decimal", "decimal": "decimal",
            "bool": "boolean", "boolean": "boolean",
            "datetime": "datetime", "date": "date", "time": "time",
            "text": "text", "blob": "binary", "json": "json",
        }
        return type_map.get(type_str.lower(), type_str)
