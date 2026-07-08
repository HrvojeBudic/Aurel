"""Secret boundary — env-only resolution and redaction (P1.1)."""
from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from typing import Optional, Protocol


class SecretBoundaryViolation(ValueError):
    """Raised when secret handling rules are violated (e.g. raw key in config)."""


@dataclass(frozen=True)
class SecretReference:
    env_var: str

    def __post_init__(self) -> None:
        if not self.env_var or not self.env_var.isupper():
            raise SecretBoundaryViolation(
                f"secret reference must name an environment variable: {self.env_var!r}"
            )


@dataclass
class SecretResolutionResult:
    env_var: str
    present: bool
    value: Optional[str] = None
    error: str = ""

    @property
    def ok(self) -> bool:
        return self.present and self.value is not None and not self.error


# F2 — process-wide registry of ACTUAL secret values (fed by SecretStore /
# EnvSecretProvider resolutions). Every SecretRedactor instance redacts these by
# exact match, so a resolved key can never appear un-redacted in logs, traces,
# cassettes, or provider errors — regardless of where the redactor was built.
_KNOWN_SECRET_VALUES: list[str] = []


def register_secret_value(value: str) -> None:
    """Register a real secret value for process-wide exact-match redaction."""
    if value and value not in _KNOWN_SECRET_VALUES:
        _KNOWN_SECRET_VALUES.append(value)


_ENV_KEY_PATTERN = re.compile(
    r"(?i)\b((?:OPENAI|ANTHROPIC|AUREL|AWS|AZURE|GITHUB|GITLAB|HUGGINGFACE|HF)_?"
    r"(?:API_KEY|SECRET|TOKEN|PASSWORD)|[A-Z0-9_]*(?:API_KEY|SECRET|TOKEN))\s*[=:]\s*"
    r"(\S+)"
)
_SK_PATTERN = re.compile(r"\bsk-[A-Za-z0-9_-]{8,}\b")
_BEARER_PATTERN = re.compile(r"\bBearer\s+[A-Za-z0-9._~+/=-]{8,}\b", re.IGNORECASE)
_HIGH_ENTROPY_PATTERN = re.compile(r"\b[A-Za-z0-9+/=_-]{32,}\b")


class EnvSecretProvider:
    """Resolve secrets from environment variables only."""

    def resolve(self, ref: SecretReference) -> SecretResolutionResult:
        value = os.environ.get(ref.env_var)
        if value is None or value == "":
            return SecretResolutionResult(
                env_var=ref.env_var,
                present=False,
                error=f"{ref.env_var} not configured",
            )
        # F2: every resolved secret becomes exact-match redactable process-wide.
        register_secret_value(value)
        return SecretResolutionResult(
            env_var=ref.env_var,
            present=True,
            value=value,
        )

    def resolve_optional(self, env_var: str) -> SecretResolutionResult:
        if not env_var:
            return SecretResolutionResult(env_var="", present=False)
        return self.resolve(SecretReference(env_var))


class SecretRedactor:
    """Redact secret-like values from strings destined for logs/traces/reports."""

    def __init__(self, *, known_values: Optional[list[str]] = None) -> None:
        self._known_values = [v for v in (known_values or []) if v]

    def redact(self, text: str) -> str:
        if not text:
            return text
        # Exact-match known values first, then heuristic patterns.
        out = self.redact_known(text)
        out = _ENV_KEY_PATTERN.sub(r"\1=[REDACTED]", out)
        out = _SK_PATTERN.sub("[REDACTED]", out)
        out = _BEARER_PATTERN.sub("Bearer [REDACTED]", out)
        out = _redact_high_entropy(out)
        return out

    def redact_known(self, text: str) -> str:
        """Exact-match redaction of REGISTERED secret values only — no heuristic
        patterns. F2: use this where the heuristics would corrupt legitimate
        content (e.g. a model cassette's recorded completion may contain long
        token-like strings that are not secrets). It still guarantees that no
        actually-resolved secret value survives in the output."""
        if not text:
            return text
        out = text
        # Instance-supplied values first, then the process-wide registry (F2) —
        # exact-match redaction of every secret the process has ever resolved.
        for value in (*self._known_values, *_KNOWN_SECRET_VALUES):
            if value and value in out:
                out = out.replace(value, "[REDACTED]")
        return out

    def redact_mapping(self, data: dict) -> dict:
        return {k: self.redact(str(v)) if isinstance(v, str) else v for k, v in data.items()}


def _redact_high_entropy(text: str) -> str:
    """Redact long token-like strings while preserving normal words and paths."""

    def _replace(match: re.Match[str]) -> str:
        token = match.group(0)
        if "/" in token or "\\" in token:
            return token
        if token.count(".") > 2:
            return token
        unique = len(set(token))
        if unique < 10 and len(token) < 48:
            return token
        return "[REDACTED]"

    return _HIGH_ENTROPY_PATTERN.sub(_replace, text)


def assert_no_raw_secrets_in_yaml(data: object, *, path: str = "") -> None:
    """Reject YAML documents that embed raw secret fields."""
    forbidden_keys = {
        "api_key",
        "apikey",
        "secret",
        "secret_key",
        "password",
        "token",
        "bearer",
    }
    if isinstance(data, dict):
        for key, value in data.items():
            key_lower = str(key).lower().replace("-", "_")
            if key_lower in forbidden_keys:
                raise SecretBoundaryViolation(
                    f"raw secret field '{key}' not allowed in config at {path or 'root'}"
                )
            child_path = f"{path}.{key}" if path else str(key)
            assert_no_raw_secrets_in_yaml(value, path=child_path)
    elif isinstance(data, list):
        for idx, item in enumerate(data):
            assert_no_raw_secrets_in_yaml(item, path=f"{path}[{idx}]")
