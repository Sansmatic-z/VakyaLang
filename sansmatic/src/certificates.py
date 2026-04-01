from __future__ import annotations

from typing import Any, Dict
import hashlib
import hmac
import json

from .config import SansmaticSettings


class CertificateAuthority:
    """
    Handles backward-compatible proof certificate authentication.

    Legacy mode keeps the existing self-hash payloads.
    HMAC mode adds deployment-authenticated signatures without changing
    the existing payload keys that the VM already expects.
    """

    _SIGNATURE_ALGORITHM = "hmac-sha256"

    def __init__(self, settings: SansmaticSettings):
        self.settings = settings

    def issue(self, certificate: Dict[str, Any]) -> Dict[str, Any]:
        payload = dict(certificate)
        body = self._body(payload)
        payload["hash"] = self._hash_body(body)

        if self.settings.effective_certificate_mode == self._SIGNATURE_ALGORITHM:
            secret = self.settings.require_certificate_secret()
            payload["signature_alg"] = self._SIGNATURE_ALGORITHM
            payload["signature"] = self._sign_body(body, secret)

        return payload

    def verify(self, certificate: Any) -> bool:
        if isinstance(certificate, str):
            return certificate.startswith("PROOF_") or certificate.startswith("AXIOMATIC_")

        if not isinstance(certificate, dict):
            return False

        if certificate.get("kind") != "sansmatic_certificate":
            return False

        expected_hash = certificate.get("hash")
        if not expected_hash:
            return False

        body = self._body(certificate)
        actual_hash = self._hash_body(body)
        if not hmac.compare_digest(str(expected_hash), actual_hash):
            return False

        signature = certificate.get("signature")
        signature_alg = certificate.get("signature_alg")
        verified = bool(certificate.get("verified"))
        if signature is None and signature_alg is None:
            return verified and self.settings.allow_legacy_certificates

        if signature_alg != self._SIGNATURE_ALGORITHM or not isinstance(signature, str):
            return False

        try:
            secret = self.settings.require_certificate_secret()
        except ValueError:
            return False

        return verified and hmac.compare_digest(
            signature,
            self._sign_body(body, secret),
        )

    @staticmethod
    def canonical_json(payload: Dict[str, Any]) -> str:
        return json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))

    @classmethod
    def _body(cls, certificate: Dict[str, Any]) -> Dict[str, Any]:
        return {
            key: value
            for key, value in certificate.items()
            if key not in {"hash", "signature", "signature_alg"}
        }

    @classmethod
    def _hash_body(cls, body: Dict[str, Any]) -> str:
        return hashlib.sha256(cls.canonical_json(body).encode("utf-8")).hexdigest()

    @classmethod
    def _sign_body(cls, body: Dict[str, Any], secret: str) -> str:
        digest = hmac.new(
            secret.encode("utf-8"),
            cls.canonical_json(body).encode("utf-8"),
            hashlib.sha256,
        )
        return digest.hexdigest()
