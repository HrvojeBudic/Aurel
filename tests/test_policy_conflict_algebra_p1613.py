"""P1.6.13 Policy Conflict Algebra — pure module tests.

Covers: ranking, strictest-wins matrix, determinism, conflict taxonomy,
specificity scoring, and non-enforcement guarantees.
"""
from __future__ import annotations

import inspect
import json

import pytest

from agentic_runtime.policy_cards.conflict_algebra import (
    PolicyConflict,
    PolicyConflictResolution,
    PolicyConflictResolutionStrategy,
    PolicyConflictSet,
    PolicyConflictSeverity,
    PolicyConflictType,
    PolicyDecisionRank,
    PolicyPrecedenceRule,
    PolicySpecificityScore,
    StrictestWinsResult,
    _fd_to_dict,
    classify_policy_conflicts,
    compute_specificity_score,
    decision_rank_value,
    normalize_policy_decision_rank,
    rank_is_stricter,
    resolve_policy_conflicts_strictest_wins,
    stable_decision_sort_key,
    strictest_rank,
)

from agentic_runtime.policy_cards import (
    EnforcementMode,
    FamilyDecision,
    PolicyFamily,
    PolicyFamilyDecision,
    ShadowAction,
)


def _fd(
    family: PolicyFamily,
    decision: FamilyDecision,
    *,
    reasons: tuple[str, ...] = (),
    card_ids: tuple[str, ...] = (),
    approval: tuple[str, ...] = (),
    violations: tuple[str, ...] = (),
) -> PolicyFamilyDecision:
    shadow_map = {
        FamilyDecision.ALLOW: ShadowAction.WOULD_ALLOW,
        FamilyDecision.WARN: ShadowAction.WOULD_WARN,
        FamilyDecision.REQUIRE_APPROVAL: ShadowAction.WOULD_REQUIRE_APPROVAL,
        FamilyDecision.DENY: ShadowAction.WOULD_DENY,
        FamilyDecision.NOT_APPLICABLE: ShadowAction.WOULD_NOT_APPLY,
        FamilyDecision.ERROR: ShadowAction.WOULD_ERROR,
    }
    return PolicyFamilyDecision(
        family=family,
        decision=decision,
        effective_shadow_action=shadow_map[decision],
        reason_codes=reasons,
        applicable_card_ids=card_ids,
        approval_requirements=approval,
        violations=violations,
    )


def _make(family: PolicyFamily, decision: FamilyDecision, card: str = "a",
          reasons: tuple[str, ...] = (),
          approval: tuple[str, ...] = (),
          violations: tuple[str, ...] = ()) -> PolicyFamilyDecision:
    return _fd(family, decision, card_ids=(card,), reasons=reasons or ("REASON",),
               approval=approval, violations=violations)


def _allow(f: PolicyFamily = PolicyFamily.RISK_TIER, c: str = "a") -> PolicyFamilyDecision:
    return _make(f, FamilyDecision.ALLOW, c)

def _warn(f: PolicyFamily = PolicyFamily.RISK_TIER, c: str = "a") -> PolicyFamilyDecision:
    return _make(f, FamilyDecision.WARN, c)

def _approval(f: PolicyFamily = PolicyFamily.RISK_TIER, c: str = "a") -> PolicyFamilyDecision:
    return _make(f, FamilyDecision.REQUIRE_APPROVAL, c)

def _deny(f: PolicyFamily = PolicyFamily.RISK_TIER, c: str = "a") -> PolicyFamilyDecision:
    return _make(f, FamilyDecision.DENY, c)

def _error(f: PolicyFamily = PolicyFamily.RISK_TIER, c: str = "a") -> PolicyFamilyDecision:
    return _make(f, FamilyDecision.ERROR, c, reasons=("ADAPTER_ERROR",))

def _na(f: PolicyFamily = PolicyFamily.RISK_TIER, c: str = "a") -> PolicyFamilyDecision:
    return _make(f, FamilyDecision.NOT_APPLICABLE, c, reasons=("NA",))


# ── ranking ──

class TestRanking:
    def test_deny_outranks_require_approval(self):
        assert rank_is_stricter(PolicyDecisionRank.DENY, PolicyDecisionRank.REQUIRE_APPROVAL)

    def test_require_approval_outranks_warn(self):
        assert rank_is_stricter(PolicyDecisionRank.REQUIRE_APPROVAL, PolicyDecisionRank.WARN)

    def test_warn_outranks_allow(self):
        assert rank_is_stricter(PolicyDecisionRank.WARN, PolicyDecisionRank.ALLOW)

    def test_allow_outranks_not_applicable(self):
        assert rank_is_stricter(PolicyDecisionRank.ALLOW, PolicyDecisionRank.NOT_APPLICABLE)

    def test_error_is_highest_rank(self):
        assert rank_is_stricter(PolicyDecisionRank.ERROR, PolicyDecisionRank.DENY)

    def test_rank_values_monotonic(self):
        ranks = [PolicyDecisionRank.NOT_APPLICABLE, PolicyDecisionRank.ALLOW,
                 PolicyDecisionRank.WARN, PolicyDecisionRank.REQUIRE_APPROVAL,
                 PolicyDecisionRank.DENY, PolicyDecisionRank.ERROR]
        for i in range(len(ranks) - 1):
            assert decision_rank_value(ranks[i]) < decision_rank_value(ranks[i + 1])

    def test_normalize_family_decision(self):
        assert normalize_policy_decision_rank(FamilyDecision.DENY) == PolicyDecisionRank.DENY
        assert normalize_policy_decision_rank(FamilyDecision.ALLOW) == PolicyDecisionRank.ALLOW
        assert normalize_policy_decision_rank(FamilyDecision.ERROR) == PolicyDecisionRank.ERROR

    def test_normalize_shadow_action(self):
        assert normalize_policy_decision_rank(ShadowAction.WOULD_DENY) == PolicyDecisionRank.DENY
        assert normalize_policy_decision_rank(ShadowAction.WOULD_ERROR) == PolicyDecisionRank.ERROR

    def test_normalize_raw_strings(self):
        assert normalize_policy_decision_rank("deny") == PolicyDecisionRank.DENY
        assert normalize_policy_decision_rank("block") == PolicyDecisionRank.DENY
        assert normalize_policy_decision_rank("approval_required") == PolicyDecisionRank.REQUIRE_APPROVAL
        assert normalize_policy_decision_rank("adapter_error") == PolicyDecisionRank.ERROR

    def test_unknown_present_value_is_error(self):
        assert normalize_policy_decision_rank("gobbledygook") == PolicyDecisionRank.ERROR

    def test_none_is_not_applicable(self):
        assert normalize_policy_decision_rank(None) == PolicyDecisionRank.NOT_APPLICABLE

    def test_empty_string_is_not_applicable(self):
        assert normalize_policy_decision_rank("") == PolicyDecisionRank.NOT_APPLICABLE

    def test_strictest_rank(self):
        assert strictest_rank([PolicyDecisionRank.ALLOW, PolicyDecisionRank.DENY]) == PolicyDecisionRank.DENY
        assert strictest_rank([]) == PolicyDecisionRank.NOT_APPLICABLE


# ── strictest-wins matrix ──

class TestStrictestWins:
    def test_empty_returns_no_applicable_policy(self):
        r = resolve_policy_conflicts_strictest_wins(family_decisions=())
        assert r.winning_rank == PolicyDecisionRank.NOT_APPLICABLE
        assert r.strategy == PolicyConflictResolutionStrategy.NO_APPLICABLE_POLICY

    def test_single_returns_itself(self):
        r = resolve_policy_conflicts_strictest_wins(family_decisions=(_allow(),))
        assert r.winning_rank == PolicyDecisionRank.ALLOW
        assert r.winning_family == "risk_tier"

    def test_allow_plus_warn_gives_warn(self):
        r = resolve_policy_conflicts_strictest_wins(family_decisions=(_allow(), _warn()))
        assert r.winning_rank == PolicyDecisionRank.WARN

    def test_allow_plus_require_approval(self):
        r = resolve_policy_conflicts_strictest_wins(family_decisions=(_allow(), _approval()))
        assert r.winning_rank == PolicyDecisionRank.REQUIRE_APPROVAL

    def test_allow_plus_deny(self):
        r = resolve_policy_conflicts_strictest_wins(family_decisions=(_allow(), _deny()))
        assert r.winning_rank == PolicyDecisionRank.DENY

    def test_warn_plus_deny(self):
        r = resolve_policy_conflicts_strictest_wins(family_decisions=(_warn(), _deny()))
        assert r.winning_rank == PolicyDecisionRank.DENY

    def test_approval_plus_deny(self):
        r = resolve_policy_conflicts_strictest_wins(family_decisions=(_approval(), _deny()))
        assert r.winning_rank == PolicyDecisionRank.DENY

    def test_na_plus_allow(self):
        r = resolve_policy_conflicts_strictest_wins(family_decisions=(_na(), _allow()))
        assert r.winning_rank == PolicyDecisionRank.ALLOW

    def test_all_na(self):
        r = resolve_policy_conflicts_strictest_wins(
            family_decisions=(_na(), _na(PolicyFamily.SANDBOX)))
        assert r.winning_rank == PolicyDecisionRank.NOT_APPLICABLE

    def test_error_plus_allow_gives_error(self):
        r = resolve_policy_conflicts_strictest_wins(family_decisions=(_error(), _allow()))
        assert r.winning_rank == PolicyDecisionRank.ERROR

    def test_mixed_three_strictest_wins(self):
        r = resolve_policy_conflicts_strictest_wins(family_decisions=(
            _allow(PolicyFamily.RISK_TIER, "r1"),
            _warn(PolicyFamily.TOOL_PERMISSION, "t1"),
            _deny(PolicyFamily.SANDBOX, "s1"),
        ))
        assert r.winning_rank == PolicyDecisionRank.DENY
        assert r.winning_family == "sandbox"

    def test_preserves_all_evidence(self):
        r = resolve_policy_conflicts_strictest_wins(
            family_decisions=(_deny(c="d"), _allow(c="a")))
        assert len(r.all_decisions) == 2


# ── determinism ──

class TestDeterminism:
    def test_same_input_same_hash(self):
        fds = (_allow(), _deny())
        h1 = resolve_policy_conflicts_strictest_wins(family_decisions=fds).compute_hash()
        h2 = resolve_policy_conflicts_strictest_wins(family_decisions=fds).compute_hash()
        assert h1 == h2
        assert len(h1) == 64

    def test_shuffled_same_winner(self):
        fds_a = (_allow(c="a"), _warn(c="b"), _deny(c="c"))
        fds_b = (_deny(c="c"), _allow(c="a"), _warn(c="b"))
        r1 = resolve_policy_conflicts_strictest_wins(family_decisions=fds_a)
        r2 = resolve_policy_conflicts_strictest_wins(family_decisions=fds_b)
        assert r1.winning_rank == r2.winning_rank
        assert r1.winning_family == r2.winning_family

    def test_canonical_dict_json_safe(self):
        cr = resolve_policy_conflicts_strictest_wins(family_decisions=(_allow(), _deny()))
        payload = cr.to_canonical_dict()
        s = json.dumps(payload, sort_keys=True)
        parsed = json.loads(s)
        assert parsed["winning_rank"] == "DENY"

    def test_conflict_set_hash_deterministic(self):
        cs = classify_policy_conflicts(family_decisions=(_allow(), _deny()))
        assert cs.compute_hash() == cs.compute_hash()

    def test_canonical_hash_is_64_chars(self):
        r = resolve_policy_conflicts_strictest_wins(family_decisions=(_allow(), _deny()))
        assert len(r.compute_hash()) == 64


# ── conflict taxonomy ──

class TestConflictTaxonomy:
    def test_rank_mismatch_strictness_conflict(self):
        cs = classify_policy_conflicts(family_decisions=(_allow(), _deny()))
        assert any(c.conflict_type == PolicyConflictType.STRICTNESS_CONFLICT for c in cs.conflicts)

    def test_family_disagreement(self):
        cs = classify_policy_conflicts(family_decisions=(
            _allow(PolicyFamily.RISK_TIER), _allow(PolicyFamily.TOOL_PERMISSION)))
        assert any(c.conflict_type == PolicyConflictType.FAMILY_CONFLICT for c in cs.conflicts)

    def test_risk_conflict(self):
        fd = _fd(PolicyFamily.RISK_TIER, FamilyDecision.DENY, reasons=("RISK_TIER_DENIED",))
        cs = classify_policy_conflicts(family_decisions=(fd,))
        assert any(c.conflict_type == PolicyConflictType.RISK_MAPPING_CONFLICT for c in cs.conflicts)

    def test_approval_conflict(self):
        fd = _fd(PolicyFamily.HUMAN_OVERSIGHT, FamilyDecision.REQUIRE_APPROVAL,
                 reasons=("OVERSIGHT_REVIEW",), approval=("operator_approval",))
        cs = classify_policy_conflicts(family_decisions=(fd,))
        assert any(c.conflict_type == PolicyConflictType.APPROVAL_REQUIREMENT_CONFLICT for c in cs.conflicts)

    def test_sandbox_conflict(self):
        fd = _fd(PolicyFamily.SANDBOX, FamilyDecision.DENY, reasons=("SANDBOX_BACKEND_DENIED",))
        cs = classify_policy_conflicts(family_decisions=(fd,))
        assert any(c.conflict_type == PolicyConflictType.SANDBOX_POSTURE_CONFLICT for c in cs.conflicts)

    def test_data_conflict(self):
        fd = _fd(PolicyFamily.DATA_RESIDENCY, FamilyDecision.DENY, reasons=("DATA_EGRESS_DENIED",))
        cs = classify_policy_conflicts(family_decisions=(fd,))
        assert any(c.conflict_type == PolicyConflictType.DATA_RESIDENCY_CONFLICT for c in cs.conflicts)

    def test_tool_conflict(self):
        fd = _fd(PolicyFamily.TOOL_PERMISSION, FamilyDecision.DENY, reasons=("TOOL_DENIED",))
        cs = classify_policy_conflicts(family_decisions=(fd,))
        assert any(c.conflict_type == PolicyConflictType.TOOL_PERMISSION_CONFLICT for c in cs.conflicts)

    def test_prompt_conflict(self):
        fd = _fd(PolicyFamily.PROMPT, FamilyDecision.DENY, reasons=("PROMPT_DENIED",))
        cs = classify_policy_conflicts(family_decisions=(fd,))
        assert any(c.conflict_type == PolicyConflictType.PROMPT_AUTHORITY_CONFLICT for c in cs.conflicts)

    def test_memory_conflict(self):
        fd = _fd(PolicyFamily.MEMORY_WRITE, FamilyDecision.DENY, reasons=("MEMORY_WRITE_FORBIDDEN",))
        cs = classify_policy_conflicts(family_decisions=(fd,))
        assert any(c.conflict_type == PolicyConflictType.MEMORY_WRITE_CONFLICT for c in cs.conflicts)

    def test_adapter_error_conflict(self):
        fd = _error()
        cs = classify_policy_conflicts(family_decisions=(fd,))
        assert any(c.conflict_type == PolicyConflictType.ADAPTER_ERROR for c in cs.conflicts)

    def test_insufficient_context(self):
        from agentic_runtime.policy_cards import PolicyResolutionContext
        ctx = PolicyResolutionContext(context_id="c")
        fd = _allow()
        cs = classify_policy_conflicts(family_decisions=(fd,), context=ctx)
        assert any(c.conflict_type == PolicyConflictType.INSUFFICIENT_CONTEXT for c in cs.conflicts)

    def test_empty_input_empty_set(self):
        cs = classify_policy_conflicts(family_decisions=())
        assert cs.total_decisions == 0


# ── specificity ──

class TestSpecificity:
    def test_specificity_minimal(self):
        score = compute_specificity_score(_allow(c="a"))
        assert isinstance(score, PolicySpecificityScore)
        assert score.total_score >= 0

    def test_tool_scoped_beats_generic(self):
        s1 = compute_specificity_score(_fd(PolicyFamily.TOOL_PERMISSION, FamilyDecision.WARN,
            reasons=("TOOL_CONSTRAINED",), card_ids=("tool-card-1",))).total_score
        s2 = compute_specificity_score(_allow()).total_score
        assert s1 > s2

    def test_sandbox_scoped_high(self):
        score = compute_specificity_score(_fd(PolicyFamily.SANDBOX, FamilyDecision.DENY,
            reasons=("SANDBOX_BACKEND_DENIED",), card_ids=("s1", "s2"))).total_score
        assert score > 0

    def test_specific_allow_loses_to_general_deny(self):
        r = resolve_policy_conflicts_strictest_wins(family_decisions=(
            _allow(PolicyFamily.TOOL_PERMISSION, "specific-tool"),
            _deny(PolicyFamily.RISK_TIER, "general-risk"),
        ))
        assert r.winning_rank == PolicyDecisionRank.DENY

    def test_specific_warn_loses_to_deny(self):
        r = resolve_policy_conflicts_strictest_wins(family_decisions=(
            _warn(PolicyFamily.TOOL_PERMISSION, "t"), _deny(PolicyFamily.SANDBOX, "s")))
        assert r.winning_rank == PolicyDecisionRank.DENY

    def test_specific_approval_loses_to_deny(self):
        r = resolve_policy_conflicts_strictest_wins(family_decisions=(
            _approval(PolicyFamily.HUMAN_OVERSIGHT, "o"), _deny(PolicyFamily.SANDBOX, "s")))
        assert r.winning_rank == PolicyDecisionRank.DENY

    def test_specific_allow_loses_to_approval(self):
        r = resolve_policy_conflicts_strictest_wins(family_decisions=(
            _allow(PolicyFamily.TOOL_PERMISSION, "t"), _approval(PolicyFamily.HUMAN_OVERSIGHT, "o")))
        assert r.winning_rank == PolicyDecisionRank.REQUIRE_APPROVAL

    def test_lexical_tie_break_same_rank_same_family(self):
        fd_a = _fd(PolicyFamily.SANDBOX, FamilyDecision.DENY,
                   reasons=("SANDBOX_BACKEND_DENIED",), card_ids=("card-a",))
        fd_b = _fd(PolicyFamily.SANDBOX, FamilyDecision.DENY,
                   reasons=("SANDBOX_BACKEND_DENIED",), card_ids=("card-b",))
        r = resolve_policy_conflicts_strictest_wins(family_decisions=(fd_a, fd_b))
        assert r.winning_rank == PolicyDecisionRank.DENY
        r2 = resolve_policy_conflicts_strictest_wins(family_decisions=(fd_a, fd_b))
        assert r.winning_card_ids == r2.winning_card_ids


# ── non-enforcement ──

class TestNonEnforcement:
    def test_no_runtime_imports(self):
        import agentic_runtime.policy_cards.conflict_algebra as ca
        for name in dir(ca):
            obj = getattr(ca, name, None)
            if obj is not None and hasattr(obj, "__module__"):
                m = getattr(obj, "__module__", "")
                assert "agentic_runtime.runtime" not in m

    def test_no_enforce_methods(self):
        for cls in (PolicyConflict, PolicyConflictSet, PolicyConflictResolution, StrictestWinsResult):
            methods = {n for n, _ in inspect.getmembers(cls) if callable(getattr(cls, n, None))}
            assert not {"enforce", "block", "apply", "approve", "execute", "submit"} & methods

    def test_resolve_does_not_mutate_input(self):
        fd = _allow()
        before = fd.decision
        resolve_policy_conflicts_strictest_wins(family_decisions=(fd,))
        assert fd.decision == before

    def test_classify_does_not_mutate_input(self):
        fd = _allow()
        before = fd.decision
        classify_policy_conflicts(family_decisions=(fd,))
        assert fd.decision == before


# ── precedence / result ──

class TestPrecedenceAndResult:
    def test_precedence_rule_canonical(self):
        rule = PolicyPrecedenceRule(rank_priority=1, specificity_priority=2,
                                     family_priority=3, card_priority="a")
        p = rule.to_canonical_dict()
        assert p["rank_priority"] == 1

    def test_strictest_wins_result_full(self):
        cr = resolve_policy_conflicts_strictest_wins(family_decisions=(_deny(),))
        swr = StrictestWinsResult(resolution=cr, conflict_hash=cr.compute_hash(),
                                   family_decision_count=1)
        p = swr.to_canonical_dict()
        assert "resolution" in p
        assert len(p["conflict_hash"]) == 64
        assert p["family_decision_count"] == 1
