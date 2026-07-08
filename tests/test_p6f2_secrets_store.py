"""F2 seal — SecretStore backend chain (env → keyring → file-0600) + masking.

Proves: env wins the chain; keyring is used only when its binary probe succeeds
(subprocess mocked — no real keyring is touched); the file backend round-trips
with 0600/0700 permissions and is named honestly (no fake crypto); ``status()``
exposes only masked fingerprints (never a value); unknown providers fail closed;
the provider registry is extensible; and every resolved value becomes
process-wide redactable.
"""

from __future__ import annotations

import stat

from agentic_runtime.secrets import SecretRedactor
from agentic_runtime.secrets_store import (DEFAULT_PROVIDER_KEY_ENVS,
                                           SecretStore, SecretStoreError,
                                           _KeyringCli)
import pytest


class _NoKeyring(_KeyringCli):
    def __init__(self) -> None:          # never probes the real OS
        self._tool = None


class _FakeKeyring(_KeyringCli):
    def __init__(self) -> None:
        self._tool = "fake"
        self.stored: dict[str, str] = {}

    @property
    def available(self) -> bool:
        return True

    def get(self, provider: str):
        return self.stored.get(provider)

    def set(self, provider: str, value: str) -> bool:
        self.stored[provider] = value
        return True


def _store(tmp_path, keyring=None):
    return SecretStore(secrets_dir=tmp_path / "secrets",
                       keyring=keyring or _NoKeyring())


def test_env_wins_the_chain(tmp_path, monkeypatch):
    monkeypatch.setenv("DASHSCOPE_API_KEY", "sk-env-qwen")
    store = _store(tmp_path, keyring=_FakeKeyring())
    store._keyring.stored["qwen"] = "sk-keyring-qwen"    # would be 2nd in chain
    value, backend = store.get("qwen")
    assert (value, backend) == ("sk-env-qwen", "env")


def test_keyring_before_file(tmp_path, monkeypatch):
    monkeypatch.delenv("MOONSHOT_API_KEY", raising=False)
    fake = _FakeKeyring()
    store = _store(tmp_path, keyring=fake)
    assert store.set("kimi", "sk-keyring-kimi") == "keyring"
    value, backend = store.get("kimi")
    assert (value, backend) == ("sk-keyring-kimi", "keyring")


def test_file_0600_round_trip_and_permissions(tmp_path, monkeypatch):
    monkeypatch.delenv("DASHSCOPE_API_KEY", raising=False)
    store = _store(tmp_path)                             # no keyring available
    assert store.set("qwen", "sk-file-qwen") == "file-0600"
    value, backend = store.get("qwen")
    assert (value, backend) == ("sk-file-qwen", "file-0600")
    f = tmp_path / "secrets" / "qwen"
    assert stat.S_IMODE(f.stat().st_mode) == 0o600
    assert stat.S_IMODE(f.parent.stat().st_mode) == 0o700
    # Honest plaintext — the file contains the value, no fake crypto pretence.
    assert f.read_text().strip() == "sk-file-qwen"


def test_status_masks_values(tmp_path, monkeypatch):
    for env_var in DEFAULT_PROVIDER_KEY_ENVS.values():
        monkeypatch.delenv(env_var, raising=False)
    store = _store(tmp_path)
    store.set("qwen", "sk-super-secret-qwen-value")
    rows = {r.provider: r for r in store.status()}
    assert rows["qwen"].present is True
    assert rows["qwen"].backend == "file-0600"
    assert len(rows["qwen"].fingerprint) == 8            # masked sha256[:8]
    assert rows["kimi"].present is False and rows["kimi"].fingerprint == ""
    # The value itself appears NOWHERE in any status field.
    dump = str([r.to_dict() for r in store.status()])
    assert "sk-super-secret-qwen-value" not in dump


def test_unknown_provider_fails_closed(tmp_path):
    store = _store(tmp_path)
    with pytest.raises(SecretStoreError):
        store.get("nonexistent")
    with pytest.raises(SecretStoreError):
        store.set("nonexistent", "x")
    with pytest.raises(SecretStoreError):
        store.set("qwen", "   ")                          # empty value refused


def test_extensible_provider_registry(tmp_path, monkeypatch):
    monkeypatch.setenv("MYPROVIDER_API_KEY", "sk-custom")
    store = SecretStore(secrets_dir=tmp_path / "s",
                        extra_providers={"myprovider": "MYPROVIDER_API_KEY"},
                        keyring=_NoKeyring())
    value, backend = store.get("myprovider")
    assert (value, backend) == ("sk-custom", "env")


def test_resolved_values_become_redactable(tmp_path, monkeypatch):
    monkeypatch.delenv("MOONSHOT_API_KEY", raising=False)
    store = _store(tmp_path)
    store.set("kimi", "sk-must-never-leak-kimi")
    store.get("kimi")
    # A fresh redactor (no explicit known values) still redacts it exactly.
    out = SecretRedactor().redact("error: auth sk-must-never-leak-kimi failed")
    assert "sk-must-never-leak-kimi" not in out
    assert "[REDACTED]" in out
