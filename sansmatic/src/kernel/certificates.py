from __future__ import annotations

from typing import Any, Dict
import hmac

from sansmatic.src.certificates import CertificateAuthority
from sansmatic.src.config import SansmaticSettings


class KernelCertificateAuthority:
    """Authenticated certificates for trusted Sansmatic kernel judgments."""

    KIND = "sansmatic_kernel_certificate"
    SIGNATURE_ALGORITHM = "hmac-sha256"

    def __init__(self, settings: SansmaticSettings):
        self.settings = settings

    def issue(self, certificate: Dict[str, Any]) -> Dict[str, Any]:
        payload = dict(certificate)
        body = self._body(payload)
        payload["hash"] = CertificateAuthority._hash_body(body)

        if self.settings.effective_certificate_mode == self.SIGNATURE_ALGORITHM:
            secret = self.settings.require_certificate_secret()
            payload["signature_alg"] = self.SIGNATURE_ALGORITHM
            payload["signature"] = CertificateAuthority._sign_body(body, secret)

        return payload

    def verify(self, certificate: Any) -> bool:
        if not isinstance(certificate, dict):
            return False
        if certificate.get("kind") != self.KIND:
            return False

        expected_hash = certificate.get("hash")
        if not isinstance(expected_hash, str) or not expected_hash:
            return False

        body = self._body(certificate)
        actual_hash = CertificateAuthority._hash_body(body)
        if not hmac.compare_digest(expected_hash, actual_hash):
            return False

        signature = certificate.get("signature")
        signature_alg = certificate.get("signature_alg")
        verified = bool(certificate.get("verified"))
        if signature is None and signature_alg is None:
            return verified and self.settings.allow_legacy_certificates

        if signature_alg != self.SIGNATURE_ALGORITHM or not isinstance(signature, str):
            return False
        try:
            secret = self.settings.require_certificate_secret()
        except ValueError:
            return False
        return verified and hmac.compare_digest(
            signature,
            CertificateAuthority._sign_body(body, secret),
        )

    @staticmethod
    def _body(payload: Dict[str, Any]) -> Dict[str, Any]:
        return {
            key: value
            for key, value in payload.items()
            if key not in {"hash", "signature", "signature_alg"}
        }

