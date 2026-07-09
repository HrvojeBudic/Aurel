"""F3.2 seal — external-executor identity, budget envelope, track record.

An external executor is bounded, never a trusted peer:

  1. Least-privilege identity — the derived card is exactly the grant, never
     wider; defaults are the tightest (no tools, LOW risk, no network/secrets,
     no protected mutation). No self-elevation.
  2. Hard budget — a grant can only tighten: an over-generous grant clamps to the
     platform default; a tight grant applies; the envelope never exceeds base.
  3. Governed track record — append-only, immutable entries; trust is DERIVED,
     never set; a recent failure drops trust; trust can only RESTRICT the
     effective risk ceiling, never widen authority beyond the card.
"""
from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from agentic_runtime.budget import BudgetPolicy
from agentic_runtime.core_types import RiskLevel
from agentic_runtime.external_executor import (
    ExternalExecutorGrant,
    TrackRecordOutcome,
    TrustLevel,
    budget_envelope,
    derive_external_card,
    effective_max_risk,
    make_external_executor,
)


# --------------------------------------------------------------------------- #
# 1. Least-privilege identity.
# --------------------------------------------------------------------------- #
def test_default_grant_is_tightest_possible():
    card = derive_external_card("claude-code-1", ExternalExecutorGrant())
    auth = card.authority
    assert card.allowed_tools == []
    assert auth.max_risk is RiskLevel.LOW
    assert auth.allow_network is False
    assert auth.allow_secrets is False
    assert auth.allow_protected_mutation is False
    assert auth.write_paths == [] and auth.read_paths == []


def test_card_is_exactly_the_grant_never_wider():
    grant = ExternalExecutorGrant(
        allowed_tools=("read_file", "git_status"),
        read_paths=("src",),
        max_risk=RiskLevel.MEDIUM,
    )
    card = derive_external_card("exec", grant)
    assert set(card.allowed_tools) == {"read_file", "git_status"}
    assert card.authority.read_paths == ["src"]
    assert card.authority.write_paths == []          # not granted ⇒ not present
    assert card.authority.max_risk is RiskLevel.MEDIUM
    assert card.authority.allow_protected_mutation is False


def test_no_self_elevation_widening_needs_new_grant():
    prof = make_external_executor("exec", ExternalExecutorGrant())
    # The profile exposes no scope-widening setter.
    assert not hasattr(prof, "grant_tool")
    assert not hasattr(prof, "elevate")
    assert not hasattr(prof, "widen")
    # A wider capability only exists by deriving from a new grant.
    wider = make_external_executor(
        "exec", ExternalExecutorGrant(allowed_tools=("run_tests",))
    )
    assert prof.card.allowed_tools == []
    assert wider.card.allowed_tools == ["run_tests"]


# --------------------------------------------------------------------------- #
# 2. Hard budget envelope.
# --------------------------------------------------------------------------- #
def test_over_generous_grant_clamps_to_platform_default():
    base = BudgetPolicy()
    grant = ExternalExecutorGrant(
        max_commands=10_000_000,
        max_tool_calls=10_000_000,
        max_estimated_tokens=999_999_999,
        max_llm_calls=999_999,
    )
    env = budget_envelope(grant, base)
    assert env.max_commands_per_run == base.max_commands_per_run
    assert env.max_tool_calls_per_run == base.max_tool_calls_per_run
    assert env.max_estimated_tokens == base.max_estimated_tokens
    assert env.max_llm_calls == base.max_llm_calls


def test_tight_grant_applies_and_never_exceeds_base():
    base = BudgetPolicy()
    grant = ExternalExecutorGrant(max_commands=3, max_tool_calls=2, max_llm_calls=1)
    env = budget_envelope(grant, base)
    assert env.max_commands_per_run == 3
    assert env.max_tool_calls_per_run == 2
    assert env.max_llm_calls == 1
    # Untouched caps fall back to the platform default.
    assert env.max_estimated_tokens == base.max_estimated_tokens
    # Nothing exceeds base.
    assert env.max_commands_per_run <= base.max_commands_per_run


# --------------------------------------------------------------------------- #
# 3. Governed track record + derived trust.
# --------------------------------------------------------------------------- #
def _record(prof, outcome, n=1, tool="git_status"):
    for i in range(n):
        prof.ledger.record(
            outcome=outcome, tool=tool, action_ref=f"act_{i}", tick=i
        )


def test_track_record_is_append_only_and_immutable():
    prof = make_external_executor("exec", ExternalExecutorGrant())
    e = prof.ledger.record(
        outcome=TrackRecordOutcome.SUCCESS, tool="git_status", action_ref="a", tick=0
    )
    assert len(prof.ledger.entries) == 1
    # Entries are frozen.
    with pytest.raises(FrozenInstanceError):
        e.outcome = TrackRecordOutcome.FAILURE  # type: ignore[misc]
    # No edit/remove API.
    assert not hasattr(prof.ledger, "delete")
    assert not hasattr(prof.ledger, "edit")


def test_no_record_is_untrusted():
    prof = make_external_executor("exec", ExternalExecutorGrant())
    assert prof.trust is TrustLevel.UNTRUSTED


def test_trust_climbs_with_clean_successes():
    prof = make_external_executor("exec", ExternalExecutorGrant())
    _record(prof, TrackRecordOutcome.SUCCESS, n=1)
    assert prof.trust is TrustLevel.PROBATION
    _record(prof, TrackRecordOutcome.SUCCESS, n=4)  # total 5
    assert prof.trust is TrustLevel.TRUSTED


def test_recent_failure_drops_trust_to_untrusted():
    prof = make_external_executor("exec", ExternalExecutorGrant())
    _record(prof, TrackRecordOutcome.SUCCESS, n=10)
    assert prof.trust is TrustLevel.TRUSTED
    prof.ledger.record(
        outcome=TrackRecordOutcome.FAILURE, tool="run_tests", action_ref="x", tick=99
    )
    assert prof.trust is TrustLevel.UNTRUSTED


def test_trust_only_restricts_never_widens():
    # A HIGH-risk card is capped down while UNTRUSTED, restored once TRUSTED —
    # but never above the card's own ceiling.
    assert effective_max_risk(RiskLevel.HIGH, TrustLevel.UNTRUSTED) is RiskLevel.TRIVIAL
    assert effective_max_risk(RiskLevel.HIGH, TrustLevel.PROBATION) is RiskLevel.LOW
    assert effective_max_risk(RiskLevel.HIGH, TrustLevel.TRUSTED) is RiskLevel.HIGH
    # Trust never widens beyond the card: a LOW card stays LOW even when TRUSTED.
    assert effective_max_risk(RiskLevel.LOW, TrustLevel.TRUSTED) is RiskLevel.LOW


def test_profile_effective_ceiling_uses_trust():
    prof = make_external_executor(
        "exec", ExternalExecutorGrant(max_risk=RiskLevel.MEDIUM)
    )
    assert prof.effective_max_risk is RiskLevel.TRIVIAL   # untrusted → capped
    _record(prof, TrackRecordOutcome.SUCCESS, n=5)
    assert prof.effective_max_risk is RiskLevel.MEDIUM    # trusted → card ceiling


def test_profile_to_dict_serializable():
    prof = make_external_executor("exec", ExternalExecutorGrant())
    d = prof.to_dict()
    assert d["executor_id"] == "exec"
    assert d["trust"] == "untrusted"
    assert d["effective_max_risk"] == "trivial"
    assert d["track_record"]["successes"] == 0
