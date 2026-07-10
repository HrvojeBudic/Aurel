"""F6.0 seal — the Mandate object + registry (authority as a runtime object)."""
from __future__ import annotations

import pytest

from agentic_runtime.core_types import AuthorityScope, RiskLevel
from agentic_runtime.mandate import (
    DEFAULT_MANDATE_ID,
    Mandate,
    MandateNotFound,
    MandateRegistry,
    MandateScope,
    default_mandate,
    default_registry,
    flag_enabled,
)


def _client_mandate():
    return Mandate.make(
        "v1",
        MandateScope(paths=("clients/x/",), repos=("repoY",), client_id="x",
                     budget_cents=500.0, allowed_tools=("write_file",),
                     max_risk=RiskLevel.MEDIUM),
        persona_ref="advisor",
        policy_card_ids=("pc.risk.v1",),
        memory_zone_rules={"PROJECT_MEMORY": "allow", "CANON_MEMORY": "deny"},
    )


# --- construction / no-overclaim ------------------------------------------------

def test_mandate_requires_declared_scope():
    with pytest.raises(TypeError):
        Mandate(mandate_id="m", version="v1", scope=None)  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        Mandate(mandate_id="", version="v1", scope=MandateScope())
    with pytest.raises(ValueError):
        Mandate(mandate_id="m", version="", scope=MandateScope())


def test_make_mints_id_and_carries_fields():
    m = _client_mandate()
    assert m.mandate_id.startswith("mandate_")
    assert m.scope.paths == ("clients/x/",) and m.scope.client_id == "x"
    assert m.policy_card_ids == ("pc.risk.v1",)
    assert m.memory_zone_rules["CANON_MEMORY"] == "deny"


# --- content hashing / versioning -----------------------------------------------

def test_content_hash_is_deterministic_and_content_addressed():
    a = default_mandate()
    b = default_mandate()
    assert a.content_hash == b.content_hash          # same content ⇒ same hash
    # created_at is excluded from the hash (content identity, not timestamp).
    assert "created_at" not in a._hashable()

    tighter = Mandate(mandate_id="m", version="v1",
                      scope=MandateScope(paths=("a/",)))
    wider = Mandate(mandate_id="m", version="v1",
                    scope=MandateScope(paths=("a/", "b/")))
    assert tighter.content_hash != wider.content_hash  # scope change ⇒ new hash


def test_authority_overrides_participate_in_hash():
    base = Mandate(mandate_id="m", version="v1", scope=MandateScope(client_id="x"))
    with_over = Mandate(mandate_id="m", version="v1", scope=MandateScope(client_id="x"),
                        authority_overrides=AuthorityScope(max_risk=RiskLevel.LOW))
    assert base.content_hash != with_over.content_hash


# --- expiry (fail-closed) -------------------------------------------------------

def test_expiry_is_fail_closed():
    m = Mandate(mandate_id="m", version="v1", scope=MandateScope(client_id="x"),
                expires_at=100.0)
    assert m.is_expired(100.0) is True and m.is_expired(150.0) is True
    assert m.is_expired(50.0) is False
    assert default_mandate().is_expired(1e12) is False  # 0 ⇒ never expires


# --- registry resolution --------------------------------------------------------

def test_registry_resolves_and_fails_closed():
    reg = default_registry()
    assert reg.resolve(DEFAULT_MANDATE_ID).mandate_id == DEFAULT_MANDATE_ID
    assert reg.resolve("nope") is None                 # fail-closed
    with pytest.raises(MandateNotFound):
        reg.resolve_or_raise("nope")
    assert reg.ids() == (DEFAULT_MANDATE_ID,)


def test_registry_hash_deterministic():
    m = _client_mandate()
    r1 = MandateRegistry.from_mandates([default_mandate(), m])
    r2 = MandateRegistry.from_mandates([m, default_mandate()])  # order-independent
    assert r1.canonical_hash() == r2.canonical_hash()


def test_default_mandate_is_permissive_passthrough():
    m = default_mandate()
    assert m.scope.is_permissive() is True  # no path/repo/tool restriction ⇒ F5 behaviour


def test_flag_defaults_off(monkeypatch):
    monkeypatch.delenv("AUREL_MANDATE", raising=False)
    assert flag_enabled() is False
    monkeypatch.setenv("AUREL_MANDATE", "1")
    assert flag_enabled() is True
