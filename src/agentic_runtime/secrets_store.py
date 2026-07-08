"""F2 SecretStore — per-provider API-key storage with an honest backend chain.

Backend chain (read order): **env** → **OS keyring** → **file-0600**.

* ``env`` — the environment variable each provider already documents
  (``ANTHROPIC_API_KEY``, ``DEEPSEEK_API_KEY``, ``DASHSCOPE_API_KEY``,
  ``MOONSHOT_API_KEY``, …). Read-only: the process environment is never written.
* ``keyring`` — the real OS credential store via its native CLI
  (``secret-tool`` on Linux/libsecret, ``security`` on macOS). Available only
  when the binary probe succeeds. Windows Credential Manager has no stdlib-safe
  read path (``cmdkey`` cannot print secrets), so on Windows the keyring backend
  is HONESTLY unavailable rather than faked.
* ``file`` — ``~/.config/aurel/secrets/<provider>`` with ``chmod 0600`` (dir
  ``0700``). **Plaintext with honest posture**: no home-rolled crypto pretending
  to be security. The permission bits are the boundary, and ``status()`` says
  ``file-0600`` so the operator knows exactly what they have.

A Tauri-keychain backend is a declared F5 seam — named here, not implemented,
never reported as available. Values never appear in ``status()`` output: only a
masked sha256 fingerprint. Every value read is registered with the central
redactor (see ``secrets.register_secret_value``) so logs/traces/errors can
redact it by exact match.
"""

from __future__ import annotations

import hashlib
import os
import shutil
import subprocess  # nosec B404 - native OS keyring CLIs, fixed argv, no shell
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .secrets import register_secret_value

# Provider → canonical env var. Extensible via SecretStore(extra_providers=...).
DEFAULT_PROVIDER_KEY_ENVS: dict[str, str] = {
    "anthropic": "ANTHROPIC_API_KEY",
    "deepseek": "DEEPSEEK_API_KEY",
    "qwen": "DASHSCOPE_API_KEY",
    "kimi": "MOONSHOT_API_KEY",
    "openai": "OPENAI_API_KEY",
}

_KEYRING_SERVICE = "aurel"


class SecretStoreError(ValueError):
    """Raised for unknown providers or backend failures on ``set``."""


@dataclass(frozen=True)
class SecretStatus:
    provider: str
    env_var: str
    present: bool
    backend: str          # "env" | "keyring" | "file-0600" | ""
    fingerprint: str      # masked sha256[:8] of the value; NEVER the value

    def to_dict(self) -> dict:
        return {
            "provider": self.provider,
            "env_var": self.env_var,
            "present": self.present,
            "backend": self.backend,
            "fingerprint": self.fingerprint,
        }


def _fingerprint(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:8]


def default_secrets_dir() -> Path:
    return Path(os.environ.get("AUREL_SECRETS_DIR",
                               str(Path.home() / ".config" / "aurel" / "secrets")))


class _KeyringCli:
    """Native OS keyring via its CLI. Available only when the binary exists."""

    def __init__(self) -> None:
        self._tool: Optional[str] = None
        if sys.platform.startswith("linux") and shutil.which("secret-tool"):
            self._tool = "secret-tool"
        elif sys.platform == "darwin" and shutil.which("security"):
            self._tool = "security"
        # Windows: no honest stdlib read path (cmdkey cannot print secrets).

    @property
    def available(self) -> bool:
        return self._tool is not None

    def get(self, provider: str) -> Optional[str]:
        if self._tool == "secret-tool":
            argv = ["secret-tool", "lookup", "service", _KEYRING_SERVICE,
                    "account", provider]
        elif self._tool == "security":
            argv = ["security", "find-generic-password", "-s", _KEYRING_SERVICE,
                    "-a", provider, "-w"]
        else:
            return None
        try:
            out = subprocess.run(  # nosec B603 - fixed argv, no shell
                argv, capture_output=True, text=True, timeout=10)
        except (OSError, subprocess.TimeoutExpired):
            return None
        if out.returncode != 0:
            return None
        value = out.stdout.strip()
        return value or None

    def set(self, provider: str, value: str) -> bool:
        if self._tool == "secret-tool":
            argv = ["secret-tool", "store", f"--label=aurel {provider} API key",
                    "service", _KEYRING_SERVICE, "account", provider]
            try:
                out = subprocess.run(  # nosec B603
                    argv, input=value, capture_output=True, text=True, timeout=10)
            except (OSError, subprocess.TimeoutExpired):
                return False
            return out.returncode == 0
        if self._tool == "security":
            argv = ["security", "add-generic-password", "-U",
                    "-s", _KEYRING_SERVICE, "-a", provider, "-w", value]
            try:
                out = subprocess.run(  # nosec B603
                    argv, capture_output=True, text=True, timeout=10)
            except (OSError, subprocess.TimeoutExpired):
                return False
            return out.returncode == 0
        return False


class SecretStore:
    """Per-provider secret resolution + storage over the honest backend chain."""

    def __init__(self, *, secrets_dir: Optional[Path] = None,
                 extra_providers: Optional[dict[str, str]] = None,
                 keyring: Optional[_KeyringCli] = None) -> None:
        self.providers = dict(DEFAULT_PROVIDER_KEY_ENVS)
        if extra_providers:
            self.providers.update(extra_providers)
        self._dir = Path(secrets_dir) if secrets_dir else default_secrets_dir()
        self._keyring = keyring if keyring is not None else _KeyringCli()

    # -- resolution ------------------------------------------------------ #
    def env_var_for(self, provider: str) -> str:
        env_var = self.providers.get(provider)
        if not env_var:
            raise SecretStoreError(
                f"unknown provider {provider!r}; known: {sorted(self.providers)}")
        return env_var

    def get(self, provider: str) -> tuple[Optional[str], str]:
        """Resolve ``provider``'s key. Returns ``(value, backend)``;
        ``(None, "")`` when absent everywhere. Every hit is registered with the
        central redactor so the value can never appear un-redacted in output."""
        env_var = self.env_var_for(provider)
        value = os.environ.get(env_var)
        if value:
            register_secret_value(value)
            return value, "env"
        if self._keyring.available:
            value = self._keyring.get(provider)
            if value:
                register_secret_value(value)
                return value, "keyring"
        file_value = self._read_file(provider)
        if file_value:
            register_secret_value(file_value)
            return file_value, "file-0600"
        return None, ""

    # -- storage ---------------------------------------------------------- #
    def set(self, provider: str, value: str) -> str:
        """Store ``provider``'s key; returns the backend used ("keyring" or
        "file-0600"). The environment is never written. No fake crypto: when the
        OS keyring is unavailable the file backend is used and named honestly."""
        self.env_var_for(provider)          # validate the provider name
        value = value.strip()
        if not value:
            raise SecretStoreError("refusing to store an empty secret")
        register_secret_value(value)
        if self._keyring.available and self._keyring.set(provider, value):
            return "keyring"
        self._write_file(provider, value)
        return "file-0600"

    # -- status ------------------------------------------------------------ #
    def status(self) -> list[SecretStatus]:
        """Per-provider presence + backend + masked fingerprint. NEVER values."""
        rows = []
        for provider in sorted(self.providers):
            value, backend = self.get(provider)
            rows.append(SecretStatus(
                provider=provider,
                env_var=self.providers[provider],
                present=value is not None,
                backend=backend,
                fingerprint=_fingerprint(value) if value else "",
            ))
        return rows

    # -- file backend (honest 0600, no fake crypto) ----------------------- #
    def _file_for(self, provider: str) -> Path:
        return self._dir / provider

    def _read_file(self, provider: str) -> Optional[str]:
        path = self._file_for(provider)
        try:
            if not path.is_file():
                return None
            return path.read_text(encoding="utf-8").strip() or None
        except OSError:
            return None

    def _write_file(self, provider: str, value: str) -> None:
        self._dir.mkdir(parents=True, exist_ok=True)
        os.chmod(self._dir, 0o700)
        path = self._file_for(provider)
        path.write_text(value + "\n", encoding="utf-8")
        os.chmod(path, 0o600)


__all__ = [
    "DEFAULT_PROVIDER_KEY_ENVS",
    "SecretStore",
    "SecretStoreError",
    "SecretStatus",
    "default_secrets_dir",
]
