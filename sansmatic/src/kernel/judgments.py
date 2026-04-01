from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional
import time

from sansmatic.src.config import SansmaticSettings

from .checker import KernelTypeChecker
from .certificates import KernelCertificateAuthority
from .elaboration import KernelElaborator, KernelJudgment
from .errors import KernelError
from .normalize import normalize
from .syntax import KernelTerm


@dataclass
class KernelProofCertificate:
    judgment: str
    verified: bool
    timestamp: float
    certificate_hash: str
    reason: Optional[str] = None
    payload: Dict[str, Any] = field(default_factory=dict)


class KernelProofVerifier:
    """Verify additive trusted-kernel typing judgments and issue certificates."""

    def __init__(
        self,
        *,
        settings: SansmaticSettings | None = None,
        checker: KernelTypeChecker | None = None,
        elaborator: KernelElaborator | None = None,
    ):
        self.settings = settings or SansmaticSettings.from_env()
        self.checker = checker or KernelTypeChecker()
        self.elaborator = elaborator or KernelElaborator()
        self.certificate_authority = KernelCertificateAuthority(self.settings)

    def verify(self, judgment_spec: KernelJudgment | Dict[str, Any]) -> KernelProofCertificate:
        judgment = self.elaborator.elaborate_judgment(judgment_spec)
        try:
            if judgment.expected_type is None:
                inferred = self.checker.infer(judgment.term, judgment.context)
            else:
                self.checker.check(judgment.term, judgment.expected_type, judgment.context)
                inferred = judgment.expected_type
            verified = True
            reason = None
        except KernelError as error:
            inferred = None
            verified = False
            reason = str(error)

        payload = self.certificate_authority.issue(
            {
                "kind": KernelCertificateAuthority.KIND,
                "version": 1,
                "kernel": "sansmatic-kernel-v1",
                "judgment": judgment.render(),
                "verified": verified,
                "reason": reason,
                "term": str(judgment.term),
                "expected_type": None if judgment.expected_type is None else str(judgment.expected_type),
                "normalized_term": str(normalize(judgment.term)),
                "normalized_type": None if inferred is None else str(normalize(inferred)),
                "context": [
                    {"name": entry.name, "type": str(entry.value_type)}
                    for entry in judgment.context.entries
                ],
            }
        )
        return KernelProofCertificate(
            judgment=judgment.render(),
            verified=verified,
            timestamp=time.time(),
            certificate_hash=payload["hash"],
            reason=reason,
            payload=payload,
        )

    def verify_certificate(self, payload: Any) -> bool:
        return self.certificate_authority.verify(payload)

