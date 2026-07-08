"""F1 — enforcement profiles seal.

A profile is a coherent bundle over the G0–G5 scale, applied by
build_runtime(profile=…). These tests pin the invariants that make 'standard'
the real, runnable default without weakening the library's permissive default:

  * profile=None is byte-identical to today (no explicit enforcement),
  * standard (G2) wires the full fail-closed bundle and blocks execution on an
    unsafe sandbox — the security posture is real, not advisory,
  * dev (G4) stays advisory and runs on an unsafe sandbox (any host),
  * explicit build_runtime kwargs always override profile-derived defaults,
  * AUREL_PROFILE selects the active profile; env feature flags use setdefault.

Tests are host-independent: they assert wiring and unsafe-sandbox blocking
(unsafe is always available), never execution success on bubblewrap/docker.
"""
from __future__ import annotations

import os

import pytest

from agentic_runtime import AgentCard, AgentClass, AuthorityScope, build_runtime
from agentic_runtime.core_types import CommandEnvelope, RiskLevel
from agentic_runtime.governance.enforcement_profiles import (
    EnforcementProfileError, load_profiles, profile_process_env, profile_spec,
    resolve_profile_name)
from agentic_runtime.governance.profile import GovernanceLevel
from agentic_runtime.governance_enforcement import GovernanceEnforcementMode
from agentic_runtime.sandbox import UnsafeLocalSandbox


def _card():
    return AgentCard.make(
        name="t", mission="test", agent_class=AgentClass.EXECUTION,
        authority=AuthorityScope(read_paths=["*"], write_paths=["*"]),
        allowed_tools=["read_file", "write_file"])


def _read_cmd(card):
    return CommandEnvelope.make(
        issuer_card_id=card.id, tool="read_file", args={"path": "README.md"},
        rationale="t", expected_effect="t", declared_risk=RiskLevel.LOW)


# ---------------------------------------------------------------- yaml load
def test_profiles_define_dev_standard_hardened():
    profiles, default = load_profiles()
    assert default == "standard"
    assert set(profiles) == {"dev", "standard", "hardened"}
    assert profiles["dev"].level is GovernanceLevel.G4
    assert profiles["standard"].level is GovernanceLevel.G2
    assert profiles["hardened"].level is GovernanceLevel.G1
    # standard/hardened require hard isolation; dev allows unsafe.
    assert profiles["standard"].require_hard_sandbox is True
    assert profiles["hardened"].require_hard_sandbox is True
    assert profiles["dev"].allow_unsafe is True
    # standard turns the Track-A / dual-kernel flags on.
    assert profiles["standard"].durable_memory is True
    assert profiles["standard"].dual_kernel is True


# ---------------------------------------------------------------- profile=None
def test_profile_none_keeps_permissive_default():
    kernel = build_runtime()
    assert kernel.runtime._governance_enforcement_explicit is False


# ---------------------------------------------------------------- standard bundle
def test_standard_profile_wires_fail_closed_bundle():
    # Explicit unsafe sandbox keeps this host-independent (no bubblewrap needed);
    # we assert the *wiring*, not execution success.
    kernel = build_runtime(profile="standard", sandbox=UnsafeLocalSandbox(root="."))
    rt = kernel.runtime
    assert rt._governance_enforcement_explicit is True
    assert rt.governance_enforcement_config.mode is GovernanceEnforcementMode.ENFORCE_FAIL_CLOSED
    assert rt.identity_context_loader is not None
    assert rt.policy_card_registry is not None


def test_standard_profile_blocks_execution_on_unsafe_sandbox():
    kernel = build_runtime(profile="standard", sandbox=UnsafeLocalSandbox(root="."))
    card = _card()
    res = kernel.runtime.submit(_read_cmd(card), card)
    assert res.ok is False
    assert "sandbox" in (res.observation.stderr or "").lower()


# ---------------------------------------------------------------- dev bundle
def test_dev_profile_is_advisory_and_runs_on_unsafe():
    kernel = build_runtime(profile="dev", workspace_root=".")
    rt = kernel.runtime
    assert rt.governance_enforcement_config.mode is GovernanceEnforcementMode.ADVISORY
    card = _card()
    res = rt.submit(_read_cmd(card), card)
    assert res.ok is True  # advisory never blocks on an unsafe sandbox


# ---------------------------------------------------------------- overrides
def test_explicit_kwargs_override_profile():
    from agentic_runtime.hitl import DenyAllApprover

    gate = DenyAllApprover()
    kernel = build_runtime(profile="standard", sandbox=UnsafeLocalSandbox(root="."),
                           approval_gate=gate)
    # the explicitly-passed approver survives; the profile does not replace it.
    assert kernel.runtime.approval_gate is gate


# ---------------------------------------------------------------- name resolution
def test_env_profile_override_selects_profile(monkeypatch):
    monkeypatch.setenv("AUREL_PROFILE", "dev")
    assert resolve_profile_name() == "dev"
    assert profile_spec().name == "dev"


def test_explicit_name_beats_env(monkeypatch):
    monkeypatch.setenv("AUREL_PROFILE", "dev")
    assert resolve_profile_name("hardened") == "hardened"


def test_unknown_profile_raises():
    with pytest.raises(EnforcementProfileError):
        resolve_profile_name("nonexistent")


# ---------------------------------------------------------------- process env flags
# These pass a throwaway env mapping so the real os.environ is never mutated —
# leaking AUREL_DURABLE_MEMORY / AUREL_DUAL_KERNEL would break flag-sensitive
# tests (durable memory, dual kernel) that run later in the same process.
def test_profile_process_env_setdefault_semantics():
    env: dict[str, str] = {}
    applied = profile_process_env(profile_spec("standard"), env)
    assert applied.get("AUREL_DURABLE_MEMORY") == "1"
    assert applied.get("AUREL_DUAL_KERNEL") == "1"
    assert env == {"AUREL_DURABLE_MEMORY": "1", "AUREL_DUAL_KERNEL": "1"}


def test_profile_process_env_respects_explicit_env():
    env = {"AUREL_DURABLE_MEMORY": "0"}  # operator override
    applied = profile_process_env(profile_spec("standard"), env)
    # explicit value wins: setdefault does not overwrite, so it is not re-applied.
    assert "AUREL_DURABLE_MEMORY" not in applied
    assert env["AUREL_DURABLE_MEMORY"] == "0"


def test_dev_profile_does_not_set_feature_flags():
    env: dict[str, str] = {}
    applied = profile_process_env(profile_spec("dev"), env)
    assert applied == {}
    assert env == {}


def test_profile_process_env_does_not_touch_global_environ(monkeypatch):
    # Belt-and-suspenders: the default (real os.environ) path must remain
    # opt-in for the CLI, and the test-facing env override must isolate.
    monkeypatch.delenv("AUREL_DURABLE_MEMORY", raising=False)
    monkeypatch.delenv("AUREL_DUAL_KERNEL", raising=False)
    profile_process_env(profile_spec("standard"), {})
    assert "AUREL_DURABLE_MEMORY" not in os.environ
    assert "AUREL_DUAL_KERNEL" not in os.environ
