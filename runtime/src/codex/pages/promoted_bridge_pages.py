from __future__ import annotations

from branches.universal_codex_lab.translator_pages import (
    JavaScriptToVakExperimentalCodexPage,
    PseudocodeToVakExperimentalCodexPage,
    PythonToVakExperimentalCodexPage,
)


class PythonVakCodexPage(PythonToVakExperimentalCodexPage):
    name = "python_vak"
    description = "Promoted AST-based Python to Vak translator"
    priority = 66
    chapter = "bridges"
    chapter_title = "Bridges"
    chapter_order = 20
    capabilities = ("python", "translate", "ast", "promoted")
    experimental = False


class JavaScriptVakCodexPage(JavaScriptToVakExperimentalCodexPage):
    name = "javascript_vak"
    description = "Promoted JavaScript/TypeScript to Vak translator"
    priority = 67
    chapter = "bridges"
    chapter_title = "Bridges"
    chapter_order = 20
    capabilities = ("javascript", "translate", "regex", "promoted")
    experimental = False


class PseudocodeVakCodexPage(PseudocodeToVakExperimentalCodexPage):
    name = "pseudocode_vak"
    description = "Promoted pseudocode to Vak translator"
    priority = 68
    chapter = "bridges"
    chapter_title = "Bridges"
    chapter_order = 20
    capabilities = ("pseudocode", "translate", "template", "promoted")
    experimental = False
