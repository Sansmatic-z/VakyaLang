from __future__ import annotations

from dataclasses import dataclass
import os
from typing import Mapping


_TRUE_VALUES = {"1", "true", "yes", "on", "enabled"}
_FALSE_VALUES = {"0", "false", "no", "off", "disabled"}
_VALID_CERTIFICATE_MODES = {"auto", "legacy-hash", "hmac-sha256"}


def _parse_bool(value: str, *, env_name: str) -> bool:
    normalized = value.strip().lower()
    if normalized in _TRUE_VALUES:
        return True
    if normalized in _FALSE_VALUES:
        return False
    raise ValueError(f"{env_name} must be one of: {sorted(_TRUE_VALUES | _FALSE_VALUES)}")


@dataclass(frozen=True)
class SansmaticSettings:
    """
    Runtime configuration for the Sansmatic proof subsystem.

    The defaults preserve current local behavior while allowing deployments
    to opt into authenticated proof certificates without code changes.
    """

    certificate_mode: str = "auto"
    certificate_secret: str | None = None
    allow_legacy_certificates: bool = True
    strict_proof_registration: bool = True
    log_level: str = "INFO"

    def __post_init__(self) -> None:
        mode = self.certificate_mode.strip().lower()
        if mode not in _VALID_CERTIFICATE_MODES:
            raise ValueError(
                "certificate_mode must be one of: "
                f"{sorted(_VALID_CERTIFICATE_MODES)}"
            )
        object.__setattr__(self, "certificate_mode", mode)

        level = self.log_level.strip().upper()
        object.__setattr__(self, "log_level", level)

        secret = self.certificate_secret.strip() if self.certificate_secret else None
        object.__setattr__(self, "certificate_secret", secret or None)

    @property
    def effective_certificate_mode(self) -> str:
        if self.certificate_mode == "auto":
            return "hmac-sha256" if self.certificate_secret else "legacy-hash"
        return self.certificate_mode

    def require_certificate_secret(self) -> str:
        if not self.certificate_secret:
            raise ValueError(
                "SANSMATIC_CERTIFICATE_SECRET is required when "
                "certificate_mode resolves to hmac-sha256"
            )
        return self.certificate_secret

    @classmethod
    def from_env(
        cls,
        env: Mapping[str, str] | None = None,
    ) -> "SansmaticSettings":
        source = os.environ if env is None else env

        certificate_mode = source.get("SANSMATIC_CERTIFICATE_MODE", "auto")
        certificate_secret = source.get("SANSMATIC_CERTIFICATE_SECRET")
        allow_legacy_raw = source.get("SANSMATIC_ALLOW_LEGACY_CERTIFICATES", "true")
        strict_registration_raw = source.get("SANSMATIC_STRICT_PROOF_REGISTRATION", "true")
        log_level = source.get("SANSMATIC_LOG_LEVEL", "INFO")

        return cls(
            certificate_mode=certificate_mode,
            certificate_secret=certificate_secret,
            allow_legacy_certificates=_parse_bool(
                allow_legacy_raw,
                env_name="SANSMATIC_ALLOW_LEGACY_CERTIFICATES",
            ),
            strict_proof_registration=_parse_bool(
                strict_registration_raw,
                env_name="SANSMATIC_STRICT_PROOF_REGISTRATION",
            ),
            log_level=log_level,
        )
