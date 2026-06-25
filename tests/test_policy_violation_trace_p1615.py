"""P1.6.15 Policy Violation Trace Hook — pure violation object tests."""
from __future__ import annotations

import inspect
import json

import pytest

from agentic_runtime.policy_cards.violation_trace import (
    PolicyViolationBinding,
    PolicyViolationEvidenceRef,
    PolicyViolationSeverity,
    PolicyViolationStatus,
    PolicyViolationTraceEnvelope,
    PolicyViolationTraceEvent,
    PolicyViolationType,
    build_policy_violation_trace_envelope,
    build_policy_violation_trace_event,
    classify_policy_violation,
    policy_violation_canonical_dict,
    policy_violation_hash,
    stable_policy_violation_trace_id,
)


def _full_hashes() -> dict[str, str]:
    return {
        "context_hash": "c" * 64,
        "policy_resolution_trace_id": "t" * 64,
        "policy_resolution_hash": "h" * 64,
        "conflict_hash": "f" * 64,
        "projection_hash": "j" * 64,
        "runtime_snapshot_hash": "s" * 64,
        "registry_hash": "r" * 64,
    }


def _make_event(**kw) -> PolicyViolationTraceEvent:
    defaults = {
        "violation_type": PolicyViolationType.CUSTOS_STRICTER_THAN_RUNTIME.value,
        "violation_severity": PolicyViolationSeverity.HIGH.value,
        "violation_status": PolicyViolationStatus.CANDIDATE.value,
        "p0_verdict": "allow",
        "custos_shadow_action": "would_deny",
        **_full_hashes(),
        "source_family_ids": ("risk_tier", "sandbox"),
        "source_card_ids": ("card-1", "card-2"),
        "reason_codes": ("REASON", "OTHER"),
        "conflict_codes": ("strictness_conflict",),
    }
    defaults.update(kw)
    event = PolicyViolationTraceEvent(**defaults)
    return event.with_violation_hash()


class TestViolationEnvelopeConstruction:
    def test_envelope_builds_from_minimal(self):
        event = build_policy_violation_trace_event(
            violation_type=PolicyViolationType.CUSTOS_STRICTER_THAN_RUNTIME.value,
            violation_severity=PolicyViolationSeverity.HIGH.value,
            violation_status=PolicyViolationStatus.CANDIDATE.value,
            p0_verdict="allow",
            custos_shadow_action="would_deny",
        )
        assert event.violation_type == PolicyViolationType.CUSTOS_STRICTER_THAN_RUNTIME.value
        assert event.violation_severity == PolicyViolationSeverity.HIGH.value
        assert event.violation_status == PolicyViolationStatus.CANDIDATE.value
        assert event.shadow_only is True
        assert event.enforced is False

    def test_p0_and_custos_present_when_provided(self):
        event = _make_event()
        assert event.p0_verdict == "allow"
        assert event.custos_shadow_action == "would_deny"

    def test_violation_trace_id_is_64_chars(self):
        event = _make_event()
        assert len(event.violation_trace_id) == 64
        assert len(event.violation_hash) == 64

    def test_shadow_only_cannot_be_false(self):
        with pytest.raises(ValueError, match="shadow_only"):
            PolicyViolationTraceEvent(shadow_only=False)

    def test_enforced_cannot_be_true(self):
        with pytest.raises(ValueError, match="enforced"):
            PolicyViolationTraceEvent(enforced=True)

    def test_builder_sorts_collections(self):
        event = build_policy_violation_trace_event(
            source_family_ids=("sandbox", "risk_tier"),
            source_card_ids=("card-b", "card-a"),
            reason_codes=("Z", "A"),
            conflict_codes=("B", "A"),
        )
        assert event.source_family_ids == ("risk_tier", "sandbox")
        assert event.source_card_ids == ("card-a", "card-b")
        assert event.reason_codes == ("A", "Z")
        assert event.conflict_codes == ("A", "B")


class TestCanonicalizationAndHash:
    def test_same_input_same_hash(self):
        e1 = _make_event()
        e2 = _make_event()
        assert policy_violation_hash(e1) == policy_violation_hash(e2)

    def test_shuffled_families_same_hash(self):
        e1 = _make_event(source_family_ids=("risk_tier", "sandbox"))
        e2 = _make_event(source_family_ids=("sandbox", "risk_tier"))
        assert policy_violation_hash(e1) == policy_violation_hash(e2)

    def test_shuffled_cards_same_hash(self):
        e1 = _make_event(source_card_ids=("card-a", "card-b"))
        e2 = _make_event(source_card_ids=("card-b", "card-a"))
        assert policy_violation_hash(e1) == policy_violation_hash(e2)

    def test_shuffled_reasons_same_hash(self):
        e1 = _make_event(reason_codes=("Z", "A"))
        e2 = _make_event(reason_codes=("A", "Z"))
        assert policy_violation_hash(e1) == policy_violation_hash(e2)

    def test_shuffled_conflicts_same_hash(self):
        e1 = _make_event(conflict_codes=("B", "A"))
        e2 = _make_event(conflict_codes=("A", "B"))
        assert policy_violation_hash(e1) == policy_violation_hash(e2)

    def test_canonical_dict_json_safe(self):
        payload = policy_violation_canonical_dict(_make_event(), include_hash=True)
        parsed = json.loads(json.dumps(payload, sort_keys=True))
        assert parsed["shadow_only"] is True
        assert parsed["enforced"] is False

    def test_stable_trace_id_matches_hash(self):
        event = _make_event()
        assert stable_policy_violation_trace_id(event) == policy_violation_hash(event)


class TestClassification:
    def test_p0_allow_custos_deny(self):
        env = classify_policy_violation(
            p0_verdict="allow",
            custos_shadow_action="would_deny",
            ** _full_hashes(),
        )
        assert env.trace_event.violation_type == (
            PolicyViolationType.CUSTOS_STRICTER_THAN_RUNTIME.value
        )
        assert env.trace_event.violation_severity in {
            PolicyViolationSeverity.HIGH.value,
            PolicyViolationSeverity.CRITICAL.value,
        }

    def test_p0_allow_custos_require_approval(self):
        env = classify_policy_violation(
            p0_verdict="allow",
            custos_shadow_action="would_require_approval",
            ** _full_hashes(),
        )
        assert env.trace_event.violation_type == (
            PolicyViolationType.CUSTOS_STRICTER_THAN_RUNTIME.value
        )

    def test_p0_deny_custos_allow(self):
        env = classify_policy_violation(
            p0_verdict="deny",
            custos_shadow_action="would_allow",
            ** _full_hashes(),
        )
        assert env.trace_event.violation_type == (
            PolicyViolationType.RUNTIME_STRICTER_THAN_CUSTOS.value
        )
        assert env.trace_event.violation_severity in {
            PolicyViolationSeverity.INFO.value,
            PolicyViolationSeverity.LOW.value,
        }

    def test_both_allow_alignment_info(self):
        env = classify_policy_violation(
            p0_verdict="allow",
            custos_shadow_action="would_allow",
            alignment_status="ALIGNED",
            ** _full_hashes(),
        )
        assert env.trace_event.violation_severity == PolicyViolationSeverity.INFO.value

    def test_adapter_error(self):
        env = classify_policy_violation(
            p0_verdict="allow",
            custos_shadow_action="would_allow",
            reason_codes=("ADAPTER_ERROR",),
            ** _full_hashes(),
        )
        assert env.trace_event.violation_type == PolicyViolationType.POLICY_ADAPTER_ERROR.value

    def test_missing_context(self):
        env = classify_policy_violation(
            p0_verdict="allow",
            custos_shadow_action="would_allow",
            context_hash="",
            policy_resolution_trace_id="t" * 64,
            policy_resolution_hash="h" * 64,
        )
        assert env.trace_event.violation_type == PolicyViolationType.POLICY_CONTEXT_MISSING.value

    def test_missing_trace(self):
        env = classify_policy_violation(
            p0_verdict="allow",
            custos_shadow_action="would_allow",
            context_hash="c" * 64,
            policy_resolution_trace_id="",
            policy_resolution_hash="",
        )
        assert env.trace_event.violation_type == (
            PolicyViolationType.POLICY_TRACE_INCOMPLETE.value
        )

    def test_unresolved_conflict(self):
        env = classify_policy_violation(
            p0_verdict="allow",
            custos_shadow_action="would_allow",
            conflict_codes=("policy_conflict_unresolved",),
            ** _full_hashes(),
        )
        assert env.trace_event.violation_type == (
            PolicyViolationType.POLICY_CONFLICT_UNRESOLVED.value
        )

    def test_unknown_decision_vocabulary(self):
        env = classify_policy_violation(
            p0_verdict="totally_unknown_verdict",
            custos_shadow_action="would_allow",
            ** _full_hashes(),
        )
        assert env.trace_event.violation_type in {
            PolicyViolationType.GOVERNANCE_DRIFT_SIGNAL.value,
            PolicyViolationType.POLICY_DESIGN_ERROR.value,
        }


class TestSafety:
    def test_no_enforce_methods(self):
        for cls in (
            PolicyViolationTraceEvent,
            PolicyViolationTraceEnvelope,
            PolicyViolationEvidenceRef,
            PolicyViolationBinding,
        ):
            methods = {n for n, _ in inspect.getmembers(cls) if callable(getattr(cls, n, None))}
            assert not {
                "enforce",
                "block",
                "apply",
                "approve",
                "submit",
                "write_ledger",
                "execute",
            } & methods

    def test_module_has_no_runtime_import(self):
        import agentic_runtime.policy_cards.violation_trace as vt

        for name in dir(vt):
            obj = getattr(vt, name, None)
            if obj is not None and hasattr(obj, "__module__"):
                module = getattr(obj, "__module__", "")
                assert "agentic_runtime.runtime" not in module

    def test_metadata_strips_secrets_and_command_body(self):
        env = classify_policy_violation(
            p0_verdict="allow",
            custos_shadow_action="would_deny",
            metadata={
                "password": "secret-value",
                "command_body": "rm -rf /",
                "safe_id": "card-1",
            },
            ** _full_hashes(),
        )
        meta = dict(env.trace_event.metadata)
        assert "password" not in meta
        assert "command_body" not in meta
        assert meta.get("safe_id") == "card-1"


class TestInvariants:
    def test_missing_hashes_explicit_empty(self):
        event = build_policy_violation_trace_event(
            violation_type=PolicyViolationType.POLICY_TRACE_INCOMPLETE.value,
            violation_severity=PolicyViolationSeverity.MEDIUM.value,
            violation_status=PolicyViolationStatus.CANDIDATE.value,
        )
        assert event.context_hash == ""
        assert event.registry_hash == ""
        assert event.conflict_hash == ""
        assert event.projection_hash == ""

    def test_envelope_builds_with_binding(self):
        event = _make_event()
        binding = PolicyViolationBinding(
            policy_resolution_trace_id="t" * 64,
            violation_trace_id=event.violation_trace_id,
            violation_hash=event.violation_hash or "",
        )
        envelope = build_policy_violation_trace_envelope(event, binding=binding)
        assert envelope.violation_binding is binding
