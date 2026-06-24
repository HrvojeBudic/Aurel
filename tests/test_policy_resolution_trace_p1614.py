"""P1.6.14 Policy Resolution Trace Hook — pure trace object tests."""
from __future__ import annotations

import inspect
import json

import pytest

from agentic_runtime.policy_cards.resolution_trace import (
    PolicyResolutionEvidenceRef,
    PolicyResolutionTraceEnvelope,
    PolicyResolutionTraceEvent,
    PolicyTraceBinding,
    build_policy_resolution_trace_envelope,
    build_policy_resolution_trace_envelope_dict,
    build_policy_resolution_trace_event,
    policy_trace_canonical_dict,
    policy_trace_hash,
)


def _make_event(**kw) -> PolicyResolutionTraceEvent:
    defaults = {
        "registry_hash": "r" * 64,
        "context_hash": "c" * 64,
        "resolution_hash": "p" * 64,
        "conflict_hash": "f" * 64,
        "projection_hash": "j" * 64,
        "runtime_snapshot_hash": "s" * 64,
        "effective_shadow_action": "would_deny",
        "strictest_decision_rank": "DENY",
        "source_family_ids": ("risk_tier", "sandbox"),
        "source_card_ids": ("card-1", "card-2"),
        "reason_codes": ("REASON", "OTHER"),
        "conflict_codes": ("strictness_conflict",),
    }
    defaults.update(kw)
    event = PolicyResolutionTraceEvent(**defaults)
    return event.with_trace_hash()


class TestTraceEventConstruction:
    def test_event_builds_from_minimal(self):
        event = _make_event()
        assert event.trace_event_type == "policy_resolution_trace"
        assert event.shadow_only is True
        assert event.enforced is False
        assert event.resolver_version == "custos-v0-p1614"
        assert event.effective_shadow_action == "would_deny"
        assert event.strictest_decision_rank == "DENY"

    def test_event_trace_id_is_64_chars(self):
        event = _make_event()
        assert len(event.trace_id) == 64
        assert len(event.trace_hash) == 64

    def test_event_shadow_only_cannot_be_false(self):
        with pytest.raises(ValueError, match="shadow_only"):
            PolicyResolutionTraceEvent(shadow_only=False)

    def test_event_enforced_cannot_be_true(self):
        with pytest.raises(ValueError, match="enforced"):
            PolicyResolutionTraceEvent(enforced=True)

    def test_event_type_must_be_stable(self):
        with pytest.raises(ValueError):
            PolicyResolutionTraceEvent(trace_event_type="other")

    def test_builder_sorts_all_collections(self):
        event = build_policy_resolution_trace_event(
            registry_hash="a" * 64,
            source_family_ids=("sandbox", "risk_tier"),
            source_card_ids=("card-b", "card-a"),
            reason_codes=("Z", "A"),
            conflict_codes=("B", "A"),
            effective_shadow_action="would_deny",
            strictest_decision_rank="DENY",
        )
        assert event.source_family_ids == ("risk_tier", "sandbox")
        assert event.source_card_ids == ("card-a", "card-b")
        assert event.reason_codes == ("A", "Z")
        assert event.conflict_codes == ("A", "B")

    def test_missing_optional_hashes_handled(self):
        event = build_policy_resolution_trace_event(
            effective_shadow_action="would_allow", strictest_decision_rank="ALLOW",
        )
        assert event.registry_hash == ""
        assert event.conflict_hash == ""
        assert event.projection_hash == ""


class TestCanonicalizationAndHash:
    def test_same_input_same_hash(self):
        e1 = _make_event()
        e2 = _make_event()
        assert policy_trace_hash(e1) == policy_trace_hash(e2)

    def test_shuffled_families_same_hash(self):
        e1 = _make_event(source_family_ids=("risk_tier", "sandbox"))
        e2 = _make_event(source_family_ids=("sandbox", "risk_tier"))
        assert policy_trace_hash(e1) == policy_trace_hash(e2)

    def test_shuffled_cards_same_hash(self):
        e1 = _make_event(source_card_ids=("card-a", "card-b"))
        e2 = _make_event(source_card_ids=("card-b", "card-a"))
        assert policy_trace_hash(e1) == policy_trace_hash(e2)

    def test_shuffled_reasons_same_hash(self):
        e1 = _make_event(reason_codes=("Z", "A"))
        e2 = _make_event(reason_codes=("A", "Z"))
        assert policy_trace_hash(e1) == policy_trace_hash(e2)

    def test_shuffled_conflicts_same_hash(self):
        e1 = _make_event(conflict_codes=("B", "A"))
        e2 = _make_event(conflict_codes=("A", "B"))
        assert policy_trace_hash(e1) == policy_trace_hash(e2)

    def test_canonical_dict_is_json_safe(self):
        event = _make_event()
        payload = policy_trace_canonical_dict(event, include_hash=True)
        s = json.dumps(payload, sort_keys=True)
        parsed = json.loads(s)
        assert parsed["shadow_only"] is True
        assert parsed["enforced"] is False

    def test_hash_is_64_chars_hex(self):
        event = _make_event()
        h = policy_trace_hash(event)
        assert len(h) == 64
        int(h, 16)

    def test_builder_excludes_trace_hash_from_hash(self):
        # Hash computation excludes trace_hash field; events with
        # different trace_hash values (but otherwise identical) produce same hash
        event = build_policy_resolution_trace_event(
            effective_shadow_action="would_allow", strictest_decision_rank="ALLOW",
        )
        without = policy_trace_hash(event)
        # Modify trace_hash on a copy-like event - hash should stay same
        event2 = PolicyResolutionTraceEvent(
            trace_id=event.trace_id,
            effective_shadow_action="would_allow",
            strictest_decision_rank="ALLOW",
            trace_hash="f" * 64,
        )
        assert policy_trace_hash(event2) == without


class TestSafety:
    def test_event_has_no_enforce_methods(self):
        for cls in (PolicyResolutionTraceEvent, PolicyResolutionTraceEnvelope,
                     PolicyResolutionEvidenceRef, PolicyTraceBinding):
            methods = {n for n, _ in inspect.getmembers(cls) if callable(getattr(cls, n, None))}
            assert not {"enforce", "block", "apply", "approve", "submit", "write_ledger", "execute"} & methods

    def test_module_has_no_runtime_import(self):
        import agentic_runtime.policy_cards.resolution_trace as rt
        for name in dir(rt):
            obj = getattr(rt, name, None)
            if obj is not None and hasattr(obj, "__module__"):
                m = getattr(obj, "__module__", "")
                assert "agentic_runtime.runtime" not in m

    def test_trace_payload_prefers_hashes(self):
        event = _make_event()
        payload = policy_trace_canonical_dict(event, include_hash=True)
        for field in ("registry_hash", "context_hash", "resolution_hash",
                       "conflict_hash", "projection_hash", "runtime_snapshot_hash", "trace_hash"):
            assert field in payload


class TestInvariants:
    def test_shadow_only_always_true(self):
        event = _make_event()
        payload = policy_trace_canonical_dict(event)
        assert payload["shadow_only"] is True

    def test_enforced_always_false(self):
        event = _make_event()
        payload = policy_trace_canonical_dict(event)
        assert payload["enforced"] is False

    def test_missing_registry_hash_explicit_empty(self):
        event = build_policy_resolution_trace_event(
            effective_shadow_action="would_allow", strictest_decision_rank="ALLOW")
        assert event.registry_hash == ""

    def test_missing_context_hash_explicit_empty(self):
        event = build_policy_resolution_trace_event(
            context_hash="", effective_shadow_action="would_allow", strictest_decision_rank="ALLOW")
        assert event.context_hash == ""

    def test_missing_conflict_hash_explicit_empty(self):
        event = build_policy_resolution_trace_event(
            conflict_hash="", effective_shadow_action="would_allow", strictest_decision_rank="ALLOW")
        assert event.conflict_hash == ""

    def test_missing_projection_hash_explicit_empty(self):
        event = build_policy_resolution_trace_event(
            projection_hash="", effective_shadow_action="would_allow", strictest_decision_rank="ALLOW")
        assert event.projection_hash == ""


class TestEnvelopeAndBinding:
    def test_envelope_builds(self):
        event = build_policy_resolution_trace_event(
            effective_shadow_action="would_deny", strictest_decision_rank="DENY",
            source_family_ids=("risk_tier",),
        )
        env = build_policy_resolution_trace_envelope(event)
        assert env.trace_event is event
        assert env.generated_at

    def test_envelope_with_binding(self):
        event = build_policy_resolution_trace_event(
            effective_shadow_action="would_deny", strictest_decision_rank="DENY",
        )
        binding = PolicyTraceBinding(
            resolution_trace_id=event.trace_id, resolution_trace_hash=event.trace_hash,
            resolution_id="rps-1",
        )
        env = build_policy_resolution_trace_envelope(event, binding=binding)
        p = build_policy_resolution_trace_envelope_dict(env)
        assert p["trace_binding"]["resolution_trace_id"] == event.trace_id

    def test_envelope_dict_json_safe(self):
        event = build_policy_resolution_trace_event(
            registry_hash="r" * 64, context_hash="c" * 64,
            effective_shadow_action="would_deny", strictest_decision_rank="DENY",
        )
        env = build_policy_resolution_trace_envelope(event)
        p = build_policy_resolution_trace_envelope_dict(env)
        json.dumps(p, sort_keys=True)

    def test_evidence_ref_canonical(self):
        ref = PolicyResolutionEvidenceRef(
            evidence_type="resolution", evidence_hash="a" * 64, label="test")
        p = ref.to_canonical_dict()
        assert p["evidence_hash"] == "a" * 64

    def test_evidence_ref_requires_hash(self):
        with pytest.raises(ValueError):
            PolicyResolutionEvidenceRef(evidence_type="t", evidence_hash="")

    def test_trace_binding_canonical(self):
        b = PolicyTraceBinding(resolution_trace_id="a" * 64, registry_hash="r" * 64)
        p = b.to_canonical_dict()
        assert p["resolution_trace_id"] == "a" * 64
        assert p["registry_hash"] == "r" * 64
