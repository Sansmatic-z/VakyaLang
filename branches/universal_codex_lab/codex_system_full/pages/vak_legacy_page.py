from __future__ import annotations

from .vak_page import VakCodexPage
from ..models import CodexPageProbe


_LEGACY_MARKERS = (
    "जबतक",
    "अन्यथा_यदि",
    "के प्रकार",
    "विच्छेद",
    "निरंतर",
)


class VakLegacyCodexPage(VakCodexPage):
    name = "vak_legacy"
    description = "Legacy and drifted Vak compatibility page"
    priority = 5
    chapter = "vak_core"
    chapter_title = "Vak Core"
    chapter_order = 10
    capabilities = ("vak", "legacy", "normalize", "repair")
    extensions = ("vak",)
    max_fixpoint_passes = 2

    def probe(self, source: str, *, filename: str | None = None) -> CodexPageProbe:
        if any(marker in source for marker in _LEGACY_MARKERS):
            return CodexPageProbe(self.name, 120, "legacy Vak markers detected")
        return CodexPageProbe(self.name, 0, "not a legacy Vak candidate")
