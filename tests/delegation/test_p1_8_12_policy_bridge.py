"""Focused tests for P1.8.12 Delegation Policy/Custos BridgeRef Model.

All bridge, context, decision intent, response placeholder refs are
DEV_FIXTURE unless otherwise noted.
No policy engine call, Custos runtime call, decision request execution,
decision response, allow/deny emission, approval/rejection creation,
authority grant/deny, runtime allow/block, enforcement, trace write,
Ledger write, or runtime mutation is performed.
"""

from __future__ import annotations

import json

import pytest

from agentic_runtime.delegation.foundation import (
    DelegationError,
    DelegationErrorCode,
    DelegationSourceLabel,
    DelegationUnknownFieldError,
    DelegationValidationError,
    stable_hash,
)
from agentic_runtime.delegation.policy_bridge import (
    BRIDGE_BINDING_KNOWN_FIELDS,
    BRIDGE_BINDING_SET_KNOWN_FIELDS,
    BRIDGE_ENVELOPE_KNOWN_FIELDS,
    BRIDGE_READINESS_PROFILE_KNOWN_FIELDS,
    BRIDGE_SIDE_EFFECTS_KNOWN_FIELDS,
    BRIDGE_STATUS_REPORT_KNOWN_FIELDS,
    COMPATIBILITY_MATRIX_ENTRY_KNOWN_FIELDS,
    COMPATIBILITY_MATRIX_PB_KNOWN_FIELDS,
    CUSTOS_BRIDGE_REF_KNOWN_FIELDS,
    CUSTOS_CONTEXT_REF_KNOWN_FIELDS,
    CUSTOS_DECISION_REQUEST_INTENT_REF_KNOWN_FIELDS,
    CUSTOS_DECISION_RESPONSE_PLACEHOLDER_REF_KNOWN_FIELDS,
    POLICY_BRIDGE_REF_KNOWN_FIELDS,
    POLICY_CONTEXT_REF_KNOWN_FIELDS,
    POLICY_DECISION_REQUEST_INTENT_REF_KNOWN_FIELDS,
    POLICY_DECISION_RESPONSE_PLACEHOLDER_REF_KNOWN_FIELDS,
    DELEGATION_POLICY_CUSTOS_BRIDGE_UNAVAILABLE_BINDINGS,
    DelegationCustosBridgeRef,
    DelegationCustosContextKind,
    DelegationCustosContextRef,
    DelegationCustosDecisionRequestIntentRef,
    DelegationCustosDecisionResponsePlaceholderRef,
    DelegationPolicyBridgeRef,
    DelegationPolicyContextKind,
    DelegationPolicyContextRef,
    DelegationPolicyCustosBridgeBinding,
    DelegationPolicyCustosBridgeBindingSet,
    DelegationPolicyCustosBridgeEnvelope,
    DelegationPolicyCustosBridgeKind,
    DelegationPolicyCustosBridgeReadinessProfile,
    DelegationPolicyCustosBridgeReferenceStatus,
    DelegationPolicyCustosBridgeSideEffects,
    DelegationPolicyCustosBridgeStatus,
    DelegationPolicyCustosBridgeStatusReport,
    DelegationPolicyCustosCompatibilityFamily,
    DelegationPolicyCustosCompatibilityMatrix,
    DelegationPolicyCustosCompatibilityMatrixEntry,
    DelegationPolicyDecisionRequestIntentRef,
    DelegationPolicyDecisionResponsePlaceholderRef,
    build_delegation_custos_bridge_ref,
    build_delegation_custos_context_ref,
    build_delegation_custos_decision_request_intent_ref,
    build_delegation_custos_decision_response_placeholder_ref,
    build_delegation_policy_bridge_ref,
    build_delegation_policy_context_ref,
    build_delegation_policy_custos_bridge_binding,
    build_delegation_policy_custos_bridge_binding_set,
    build_delegation_policy_custos_bridge_envelope,
    build_delegation_policy_custos_bridge_readiness_profile,
    build_delegation_policy_custos_bridge_status_report,
    build_delegation_policy_custos_compatibility_matrix,
    build_delegation_policy_custos_compatibility_matrix_entry,
    build_delegation_policy_decision_request_intent_ref,
    build_delegation_policy_decision_response_placeholder_ref,
    hash_delegation_custos_bridge_ref,
    hash_delegation_custos_context_ref,
    hash_delegation_custos_decision_request_intent_ref,
    hash_delegation_custos_decision_response_placeholder_ref,
    hash_delegation_policy_bridge_ref,
    hash_delegation_policy_context_ref,
    hash_delegation_policy_custos_bridge_binding,
    hash_delegation_policy_custos_bridge_binding_set,
    hash_delegation_policy_custos_bridge_envelope,
    hash_delegation_policy_custos_bridge_readiness_profile,
    hash_delegation_policy_custos_bridge_status_report,
    hash_delegation_policy_custos_compatibility_matrix,
    hash_delegation_policy_custos_compatibility_matrix_entry,
    hash_delegation_policy_decision_request_intent_ref,
    hash_delegation_policy_decision_response_placeholder_ref,
    serialize_delegation_policy_custos_bridge_binding_set,
    serialize_delegation_policy_custos_bridge_envelope,
)


# ---------------------------------------------------------------------------
# 1. Imports work
# ---------------------------------------------------------------------------


def test_policy_bridge_imports_work() -> None:
    """P1.8.12 symbols are importable from delegation subpackage."""
    from agentic_runtime.delegation import (
        DelegationPolicyBridgeRef,
        DelegationCustosBridgeRef,
        DelegationPolicyCustosBridgeEnvelope,
        DelegationPolicyCustosBridgeBinding,
        DelegationPolicyCustosBridgeBindingSet,
        DelegationPolicyCustosBridgeSideEffects,
        DelegationPolicyCustosBridgeStatusReport,
    )
    assert DelegationPolicyBridgeRef is not None
    assert DelegationCustosBridgeRef is not None
    assert DelegationPolicyCustosBridgeEnvelope is not None
    assert DelegationPolicyCustosBridgeSideEffects is not None


# ---------------------------------------------------------------------------
# 2. Existing P1.8.0-11 exports remain importable
# ---------------------------------------------------------------------------


def test_existing_p1_8_exports_remain_importable() -> None:
    """P1.8.0 exports remain importable after P1.8.12 additions."""
    from agentic_runtime.delegation.foundation import (
        DelegationRecord,
        DelegationSideEffects,
    )
    assert DelegationRecord is not None
    assert DelegationSideEffects is not None


# ---------------------------------------------------------------------------
# 3-10. Ref determinism
# ---------------------------------------------------------------------------


def test_policy_bridge_ref_builds_deterministically() -> None:
    """Identical inputs produce identical policy_bridge_hashes."""
    r1 = build_delegation_policy_bridge_ref(
        delegation_ref_id="del-test-001",
        policy_bridge_description="test policy bridge",
    )
    r2 = build_delegation_policy_bridge_ref(
        delegation_ref_id="del-test-001",
        policy_bridge_description="test policy bridge",
    )
    assert r1.policy_bridge_hash == r2.policy_bridge_hash


def test_custos_bridge_ref_builds_deterministically() -> None:
    """Identical inputs produce identical custos_bridge_hashes."""
    r1 = build_delegation_custos_bridge_ref(
        delegation_ref_id="del-test-001",
        custos_bridge_description="test custos bridge",
    )
    r2 = build_delegation_custos_bridge_ref(
        delegation_ref_id="del-test-001",
        custos_bridge_description="test custos bridge",
    )
    assert r1.custos_bridge_hash == r2.custos_bridge_hash


def test_policy_context_ref_builds_deterministically() -> None:
    """Identical inputs produce identical policy_context_hashes."""
    r1 = build_delegation_policy_context_ref(
        delegation_ref_id="del-test-001",
        policy_context_kind=DelegationPolicyContextKind.IDENTITY_POLICY_CONTEXT,
    )
    r2 = build_delegation_policy_context_ref(
        delegation_ref_id="del-test-001",
        policy_context_kind=DelegationPolicyContextKind.IDENTITY_POLICY_CONTEXT,
    )
    assert r1.policy_context_hash == r2.policy_context_hash


def test_custos_context_ref_builds_deterministically() -> None:
    """Identical inputs produce identical custos_context_hashes."""
    r1 = build_delegation_custos_context_ref(
        delegation_ref_id="del-test-001",
        custos_context_kind=DelegationCustosContextKind.IDENTITY_CUSTOS_CONTEXT,
    )
    r2 = build_delegation_custos_context_ref(
        delegation_ref_id="del-test-001",
        custos_context_kind=DelegationCustosContextKind.IDENTITY_CUSTOS_CONTEXT,
    )
    assert r1.custos_context_hash == r2.custos_context_hash


def test_policy_decision_request_intent_ref_deterministic() -> None:
    """Identical inputs produce identical request_intent_hashes."""
    r1 = build_delegation_policy_decision_request_intent_ref(
        delegation_ref_id="del-test-001",
        request_intent_description="request policy decision",
    )
    r2 = build_delegation_policy_decision_request_intent_ref(
        delegation_ref_id="del-test-001",
        request_intent_description="request policy decision",
    )
    assert r1.request_intent_hash == r2.request_intent_hash


def test_custos_decision_request_intent_ref_deterministic() -> None:
    """Identical inputs produce identical request_intent_hashes."""
    r1 = build_delegation_custos_decision_request_intent_ref(
        delegation_ref_id="del-test-001",
        request_intent_description="request custos decision",
    )
    r2 = build_delegation_custos_decision_request_intent_ref(
        delegation_ref_id="del-test-001",
        request_intent_description="request custos decision",
    )
    assert r1.request_intent_hash == r2.request_intent_hash


def test_policy_decision_response_placeholder_ref_deterministic() -> None:
    """Identical inputs produce identical response_placeholder_hashes."""
    r1 = build_delegation_policy_decision_response_placeholder_ref(
        delegation_ref_id="del-test-001",
        response_placeholder_description="future policy response",
    )
    r2 = build_delegation_policy_decision_response_placeholder_ref(
        delegation_ref_id="del-test-001",
        response_placeholder_description="future policy response",
    )
    assert r1.response_placeholder_hash == r2.response_placeholder_hash


def test_custos_decision_response_placeholder_ref_deterministic() -> None:
    """Identical inputs produce identical response_placeholder_hashes."""
    r1 = build_delegation_custos_decision_response_placeholder_ref(
        delegation_ref_id="del-test-001",
        response_placeholder_description="future custos response",
    )
    r2 = build_delegation_custos_decision_response_placeholder_ref(
        delegation_ref_id="del-test-001",
        response_placeholder_description="future custos response",
    )
    assert r1.response_placeholder_hash == r2.response_placeholder_hash


# ---------------------------------------------------------------------------
# 11. Different inputs produce different hashes
# ---------------------------------------------------------------------------


def test_policy_bridge_ref_different_description_produces_different_hash() -> None:
    """Different description produces different hash."""
    r1 = build_delegation_policy_bridge_ref(
        delegation_ref_id="del-test-001",
        policy_bridge_description="description A",
    )
    r2 = build_delegation_policy_bridge_ref(
        delegation_ref_id="del-test-001",
        policy_bridge_description="description B",
    )
    assert r1.policy_bridge_hash != r2.policy_bridge_hash


# ---------------------------------------------------------------------------
# 12-13. Compatibility matrix determinism
# ---------------------------------------------------------------------------


def test_compatibility_matrix_entry_builds_deterministically() -> None:
    """Identical inputs produce identical entry_hashes."""
    e1 = build_delegation_policy_custos_compatibility_matrix_entry(
        delegation_ref_id="del-test-001",
        family=DelegationPolicyCustosCompatibilityFamily.IDENTITY_CONTEXT,
    )
    e2 = build_delegation_policy_custos_compatibility_matrix_entry(
        delegation_ref_id="del-test-001",
        family=DelegationPolicyCustosCompatibilityFamily.IDENTITY_CONTEXT,
    )
    assert e1.entry_hash == e2.entry_hash


def test_compatibility_matrix_builds_deterministically() -> None:
    """Identical entries produce identical matrix_hashes."""
    e1 = build_delegation_policy_custos_compatibility_matrix_entry(
        delegation_ref_id="del-test-001",
        family=DelegationPolicyCustosCompatibilityFamily.IDENTITY_CONTEXT,
    )
    m1 = build_delegation_policy_custos_compatibility_matrix(
        delegation_ref_id="del-test-001",
        entries=[e1],
    )
    m2 = build_delegation_policy_custos_compatibility_matrix(
        delegation_ref_id="del-test-001",
        entries=[e1],
    )
    assert m1.matrix_hash == m2.matrix_hash


# ---------------------------------------------------------------------------
# 14. Empty compatibility matrix
# ---------------------------------------------------------------------------


def test_compatibility_matrix_empty_produces_valid_hash() -> None:
    """Empty matrix produces valid non-empty hash."""
    m = build_delegation_policy_custos_compatibility_matrix(
        delegation_ref_id="del-test-001",
        entries=[],
    )
    assert m.matrix_hash
    assert len(m.matrix_hash) > 0


# ---------------------------------------------------------------------------
# 15. Readiness profile determinism
# ---------------------------------------------------------------------------


def test_bridge_readiness_profile_deterministic() -> None:
    """Identical inputs produce identical readiness_hashes."""
    p1 = build_delegation_policy_custos_bridge_readiness_profile(
        delegation_ref_id="del-test-001",
        has_policy_bridge_refs=True,
        has_custos_bridge_refs=True,
    )
    p2 = build_delegation_policy_custos_bridge_readiness_profile(
        delegation_ref_id="del-test-001",
        has_policy_bridge_refs=True,
        has_custos_bridge_refs=True,
    )
    assert p1.readiness_hash == p2.readiness_hash


# ---------------------------------------------------------------------------
# 16. Envelope determinism
# ---------------------------------------------------------------------------


def test_policy_custos_bridge_envelope_builds_deterministically() -> None:
    """Identical inputs produce identical envelope hashes."""
    pbr = build_delegation_policy_bridge_ref(
        delegation_ref_id="del-test-001",
        policy_bridge_description="test",
    )
    e1 = build_delegation_policy_custos_bridge_envelope(
        delegation_ref_id="del-test-001",
        policy_bridge_refs=[pbr],
    )
    e2 = build_delegation_policy_custos_bridge_envelope(
        delegation_ref_id="del-test-001",
        policy_bridge_refs=[pbr],
    )
    assert e1.policy_custos_bridge_envelope_hash == e2.policy_custos_bridge_envelope_hash


# ---------------------------------------------------------------------------
# 17. Binding determinism
# ---------------------------------------------------------------------------


def test_policy_custos_bridge_binding_deterministic() -> None:
    """Identical envelope produces identical binding hashes."""
    envelope = build_delegation_policy_custos_bridge_envelope(
        delegation_ref_id="del-test-001",
    )
    b1 = build_delegation_policy_custos_bridge_binding(
        delegation_ref_id="del-test-001",
        envelope=envelope,
    )
    b2 = build_delegation_policy_custos_bridge_binding(
        delegation_ref_id="del-test-001",
        envelope=envelope,
    )
    assert b1.binding_hash == b2.binding_hash


# ---------------------------------------------------------------------------
# 18. Binding set determinism
# ---------------------------------------------------------------------------


def test_policy_custos_bridge_binding_set_deterministic() -> None:
    """Identical bindings produce identical binding_set hashes."""
    envelope = build_delegation_policy_custos_bridge_envelope(
        delegation_ref_id="del-test-001",
    )
    b = build_delegation_policy_custos_bridge_binding(
        delegation_ref_id="del-test-001",
        envelope=envelope,
    )
    bs1 = build_delegation_policy_custos_bridge_binding_set(
        delegation_ref_id="del-test-001",
        bindings=[b],
    )
    bs2 = build_delegation_policy_custos_bridge_binding_set(
        delegation_ref_id="del-test-001",
        bindings=[b],
    )
    assert bs1.policy_custos_bridge_binding_set_hash == bs2.policy_custos_bridge_binding_set_hash


# ---------------------------------------------------------------------------
# 19. Status report determinism
# ---------------------------------------------------------------------------


def test_status_report_deterministic() -> None:
    """Identical inputs produce identical status_hashes."""
    r1 = build_delegation_policy_custos_bridge_status_report()
    r2 = build_delegation_policy_custos_bridge_status_report()
    assert r1.status_hash == r2.status_hash


# ---------------------------------------------------------------------------
# 20-27. Hash convenience wrappers return precomputed hash
# ---------------------------------------------------------------------------


def test_hash_policy_bridge_ref_returns_precomputed() -> None:
    """hash_ wrapper returns the same value as the field."""
    r = build_delegation_policy_bridge_ref(delegation_ref_id="del-test-001")
    assert hash_delegation_policy_bridge_ref(r) == r.policy_bridge_hash


def test_hash_custos_bridge_ref_returns_precomputed() -> None:
    r = build_delegation_custos_bridge_ref(delegation_ref_id="del-test-001")
    assert hash_delegation_custos_bridge_ref(r) == r.custos_bridge_hash


def test_hash_policy_context_ref_returns_precomputed() -> None:
    r = build_delegation_policy_context_ref(delegation_ref_id="del-test-001")
    assert hash_delegation_policy_context_ref(r) == r.policy_context_hash


def test_hash_custos_context_ref_returns_precomputed() -> None:
    r = build_delegation_custos_context_ref(delegation_ref_id="del-test-001")
    assert hash_delegation_custos_context_ref(r) == r.custos_context_hash


def test_hash_policy_decision_request_intent_ref_returns_precomputed() -> None:
    r = build_delegation_policy_decision_request_intent_ref(delegation_ref_id="del-test-001")
    assert hash_delegation_policy_decision_request_intent_ref(r) == r.request_intent_hash


def test_hash_custos_decision_request_intent_ref_returns_precomputed() -> None:
    r = build_delegation_custos_decision_request_intent_ref(delegation_ref_id="del-test-001")
    assert hash_delegation_custos_decision_request_intent_ref(r) == r.request_intent_hash


def test_hash_policy_decision_response_placeholder_ref_returns_precomputed() -> None:
    r = build_delegation_policy_decision_response_placeholder_ref(delegation_ref_id="del-test-001")
    assert hash_delegation_policy_decision_response_placeholder_ref(r) == r.response_placeholder_hash


def test_hash_custos_decision_response_placeholder_ref_returns_precomputed() -> None:
    r = build_delegation_custos_decision_response_placeholder_ref(delegation_ref_id="del-test-001")
    assert hash_delegation_custos_decision_response_placeholder_ref(r) == r.response_placeholder_hash


# ---------------------------------------------------------------------------
# 28-35. Serialize produces valid JSON
# ---------------------------------------------------------------------------


def test_serialize_policy_custos_bridge_envelope_is_valid_json() -> None:
    """Serialized envelope is valid JSON string."""
    envelope = build_delegation_policy_custos_bridge_envelope(
        delegation_ref_id="del-test-001",
        policy_bridge_refs=[build_delegation_policy_bridge_ref(
            delegation_ref_id="del-test-001",
        )],
    )
    s = serialize_delegation_policy_custos_bridge_envelope(envelope)
    assert isinstance(s, str)
    d = json.loads(s)
    assert d["schema_version"] is not None


def test_serialize_policy_custos_bridge_binding_set_is_valid_json() -> None:
    """Serialized binding set is valid JSON string."""
    envelope = build_delegation_policy_custos_bridge_envelope(
        delegation_ref_id="del-test-001",
    )
    binding = build_delegation_policy_custos_bridge_binding(
        delegation_ref_id="del-test-001",
        envelope=envelope,
    )
    bs = build_delegation_policy_custos_bridge_binding_set(
        delegation_ref_id="del-test-001",
        bindings=[binding],
    )
    s = serialize_delegation_policy_custos_bridge_binding_set(bs)
    assert isinstance(s, str)
    d = json.loads(s)
    assert d["schema_version"] is not None


# ---------------------------------------------------------------------------
# 36. SideEffects: all False
# ---------------------------------------------------------------------------


def test_policy_custos_bridge_side_effects_all_default_false() -> None:
    """All side effect booleans default to False."""
    se = DelegationPolicyCustosBridgeSideEffects()
    assert se.policy_engine_called is False
    assert se.custos_runtime_called is False
    assert se.decision_requested is False
    assert se.decision_response_received is False
    assert se.allow_decision_emitted is False
    assert se.deny_decision_emitted is False
    assert se.approval_created is False
    assert se.rejection_created is False
    assert se.authority_granted is False
    assert se.authority_denied is False
    assert se.runtime_allowed is False
    assert se.runtime_blocked is False
    assert se.enforcement_performed is False
    assert se.ledger_written is False
    assert se.global_trace_written is False
    assert se.runtime_mutated is False


# ---------------------------------------------------------------------------
# 37-40. StatusReport contains all contracts
# ---------------------------------------------------------------------------


def test_status_report_contains_all_contracts() -> None:
    """StatusReport lists all 16 contracts."""
    report = build_delegation_policy_custos_bridge_status_report()
    assert "DelegationPolicyBridgeRef" in report.available_contracts
    assert "DelegationCustosBridgeRef" in report.available_contracts
    assert "DelegationPolicyContextRef" in report.available_contracts
    assert "DelegationCustosContextRef" in report.available_contracts
    assert "DelegationPolicyDecisionRequestIntentRef" in report.available_contracts
    assert "DelegationCustosDecisionRequestIntentRef" in report.available_contracts
    assert "DelegationPolicyDecisionResponsePlaceholderRef" in report.available_contracts
    assert "DelegationCustosDecisionResponsePlaceholderRef" in report.available_contracts
    assert "DelegationPolicyCustosCompatibilityMatrixEntry" in report.available_contracts
    assert "DelegationPolicyCustosCompatibilityMatrix" in report.available_contracts
    assert "DelegationPolicyCustosBridgeReadinessProfile" in report.available_contracts
    assert "DelegationPolicyCustosBridgeEnvelope" in report.available_contracts
    assert "DelegationPolicyCustosBridgeBinding" in report.available_contracts
    assert "DelegationPolicyCustosBridgeBindingSet" in report.available_contracts
    assert "DelegationPolicyCustosBridgeSideEffects" in report.available_contracts
    assert "DelegationPolicyCustosBridgeStatusReport" in report.available_contracts


def test_status_report_side_effects_all_false() -> None:
    """StatusReport side effects all False."""
    report = build_delegation_policy_custos_bridge_status_report()
    se = report.side_effects
    assert se.policy_engine_called is False
    assert se.custos_runtime_called is False
    assert se.decision_requested is False
    assert se.decision_response_received is False
    assert se.allow_decision_emitted is False
    assert se.deny_decision_emitted is False
    assert se.approval_created is False
    assert se.rejection_created is False


def test_status_report_unavailable_bindings_entry() -> None:
    """StatusReport includes unavailable bindings dict."""
    report = build_delegation_policy_custos_bridge_status_report()
    assert isinstance(report.unavailable_bindings, dict)
    assert "Policy Engine" in report.unavailable_bindings
    assert "Custos Runtime" in report.unavailable_bindings


def test_status_report_to_canonical_dict() -> None:
    """StatusReport to_canonical_dict is JSON-safe."""
    report = build_delegation_policy_custos_bridge_status_report()
    d = report.to_canonical_dict()
    json.dumps(d)
    assert "available_contracts" in d
    assert "unavailable_bindings" in d
    assert "side_effects" in d


# ---------------------------------------------------------------------------
# 41-52. Invalid enum raises DelegationError
# ---------------------------------------------------------------------------


def test_invalid_reference_status_string_in_builder_raises_delegation_error() -> None:
    """Builder with invalid reference_status string raises DelegationError."""
    with pytest.raises(DelegationError):
        build_delegation_policy_bridge_ref(
            delegation_ref_id="del-test-001",
            reference_status="INVALID_STATUS",  # type: ignore[arg-type]
        )


def test_invalid_bridge_status_string_in_builder_raises_delegation_error() -> None:
    """Builder with invalid bridge_status string raises DelegationError."""
    with pytest.raises(DelegationError):
        build_delegation_policy_bridge_ref(
            delegation_ref_id="del-test-001",
            bridge_status="INVALID_STATUS",  # type: ignore[arg-type]
        )


def test_invalid_policy_context_kind_string_in_builder_raises_delegation_error() -> None:
    with pytest.raises(DelegationError):
        build_delegation_policy_context_ref(
            delegation_ref_id="del-test-001",
            policy_context_kind="INVALID_KIND",  # type: ignore[arg-type]
        )


def test_invalid_custos_context_kind_string_in_builder_raises_delegation_error() -> None:
    with pytest.raises(DelegationError):
        build_delegation_custos_context_ref(
            delegation_ref_id="del-test-001",
            custos_context_kind="INVALID_KIND",  # type: ignore[arg-type]
        )


def test_invalid_compatibility_family_string_in_builder_raises_delegation_error() -> None:
    with pytest.raises(DelegationError):
        build_delegation_policy_custos_compatibility_matrix_entry(
            delegation_ref_id="del-test-001",
            family="INVALID_FAMILY",  # type: ignore[arg-type]
        )


def test_missing_delegation_ref_id_raises_error() -> None:
    """Missing delegation_ref_id raises DelegationError."""
    with pytest.raises(DelegationError):
        build_delegation_policy_bridge_ref(delegation_ref_id="")


# ---------------------------------------------------------------------------
# 53-54. Frozen dataclass prevents mutation
# ---------------------------------------------------------------------------


def test_policy_bridge_ref_is_frozen() -> None:
    """PolicyBridgeRef is frozen (immutable)."""
    r = build_delegation_policy_bridge_ref(delegation_ref_id="del-test-001")
    with pytest.raises(Exception):
        r.policy_bridge_hash = "overwritten"  # type: ignore[misc]


def test_custos_bridge_ref_is_frozen() -> None:
    """CustosBridgeRef is frozen (immutable)."""
    r = build_delegation_custos_bridge_ref(delegation_ref_id="del-test-001")
    with pytest.raises(Exception):
        r.custos_bridge_hash = "overwritten"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# 55-56. Schema versions are strings
# ---------------------------------------------------------------------------


def test_schema_versions_are_strings() -> None:
    """All schema_version fields are strings."""
    r = build_delegation_policy_bridge_ref(delegation_ref_id="del-test-001")
    assert isinstance(r.schema_version, str)
    assert r.schema_version == "delegation_policy_bridge_ref.v1"

    envelope = build_delegation_policy_custos_bridge_envelope(delegation_ref_id="del-test-001")
    assert isinstance(envelope.schema_version, str)
    assert envelope.schema_version == "delegation_policy_custos_bridge_envelope.v1"


# ---------------------------------------------------------------------------
# 57-58. to_canonical_dict produces JSON-safe dict
# ---------------------------------------------------------------------------


def test_policy_bridge_ref_to_canonical_dict() -> None:
    """to_canonical_dict is JSON-safe."""
    r = build_delegation_policy_bridge_ref(
        delegation_ref_id="del-test-001",
        policy_bridge_description="test desc",
    )
    d = r.to_canonical_dict()
    json.dumps(d)
    assert d["delegation_ref_id"] == "del-test-001"
    assert d["policy_bridge_description"] == "test desc"
    assert d["source_label"] == "DEV_FIXTURE"


def test_custos_bridge_ref_to_canonical_dict() -> None:
    """to_canonical_dict is JSON-safe."""
    r = build_delegation_custos_bridge_ref(
        delegation_ref_id="del-test-001",
        custos_bridge_description="custos desc",
    )
    d = r.to_canonical_dict()
    json.dumps(d)
    assert d["delegation_ref_id"] == "del-test-001"
    assert d["custos_bridge_description"] == "custos desc"


# ---------------------------------------------------------------------------
# 59. Policy bridge ref hashes encompass description change
# ---------------------------------------------------------------------------


def test_policy_bridge_ref_description_changes_hash() -> None:
    """Different description produces different hash."""
    r1 = build_delegation_policy_bridge_ref(
        delegation_ref_id="del-test-001",
        policy_bridge_description="desc a",
    )
    r2 = build_delegation_policy_bridge_ref(
        delegation_ref_id="del-test-001",
        policy_bridge_description="desc b",
    )
    assert r1.policy_bridge_hash != r2.policy_bridge_hash


# ---------------------------------------------------------------------------
# 60. Binding set side_effects are included in hash
# ---------------------------------------------------------------------------


def test_binding_set_side_effects_all_false() -> None:
    """BindingSet side_effects all False."""
    envelope = build_delegation_policy_custos_bridge_envelope(
        delegation_ref_id="del-test-001",
    )
    b = build_delegation_policy_custos_bridge_binding(
        delegation_ref_id="del-test-001",
        envelope=envelope,
    )
    bs = build_delegation_policy_custos_bridge_binding_set(
        delegation_ref_id="del-test-001",
        bindings=[b],
    )
    se = bs.side_effects
    assert se.policy_engine_called is False
    assert se.custos_runtime_called is False
    assert se.decision_requested is False
    assert se.enforcement_performed is False
    assert se.ledger_written is False
    assert se.global_trace_written is False
    assert se.runtime_mutated is False


# ---------------------------------------------------------------------------
# 61-67. Closed-world validation
# ---------------------------------------------------------------------------


def test_policy_bridge_ref_known_fields_validate() -> None:
    """PolicyBridgeRef validates against known fields."""
    r = build_delegation_policy_bridge_ref(delegation_ref_id="del-test-001")
    d = r.to_canonical_dict()
    from agentic_runtime.delegation.foundation import validate_known_fields
    validate_known_fields(d, POLICY_BRIDGE_REF_KNOWN_FIELDS, label="PolicyBridgeRef")


def test_custos_bridge_ref_known_fields_validate() -> None:
    r = build_delegation_custos_bridge_ref(delegation_ref_id="del-test-001")
    d = r.to_canonical_dict()
    from agentic_runtime.delegation.foundation import validate_known_fields
    validate_known_fields(d, CUSTOS_BRIDGE_REF_KNOWN_FIELDS, label="CustosBridgeRef")


def test_policy_context_ref_known_fields_validate() -> None:
    r = build_delegation_policy_context_ref(delegation_ref_id="del-test-001")
    d = r.to_canonical_dict()
    from agentic_runtime.delegation.foundation import validate_known_fields
    validate_known_fields(d, POLICY_CONTEXT_REF_KNOWN_FIELDS, label="PolicyContextRef")


def test_custos_context_ref_known_fields_validate() -> None:
    r = build_delegation_custos_context_ref(delegation_ref_id="del-test-001")
    d = r.to_canonical_dict()
    from agentic_runtime.delegation.foundation import validate_known_fields
    validate_known_fields(d, CUSTOS_CONTEXT_REF_KNOWN_FIELDS, label="CustosContextRef")


def test_envelope_known_fields_validate() -> None:
    envelope = build_delegation_policy_custos_bridge_envelope(
        delegation_ref_id="del-test-001",
    )
    d = envelope.to_canonical_dict()
    from agentic_runtime.delegation.foundation import validate_known_fields
    validate_known_fields(d, BRIDGE_ENVELOPE_KNOWN_FIELDS, label="BridgeEnvelope")


def test_unknown_field_raises_error() -> None:
    """Extra unknown field in dict raises DelegationUnknownFieldError."""
    from agentic_runtime.delegation.foundation import validate_known_fields
    with pytest.raises(DelegationUnknownFieldError):
        validate_known_fields({"extra_field": True}, POLICY_BRIDGE_REF_KNOWN_FIELDS, label="Test")


def test_side_effects_known_fields_validate() -> None:
    from agentic_runtime.delegation.foundation import validate_known_fields
    validate_known_fields(
        {
            "policy_engine_called": False,
            "custos_runtime_called": False,
            "decision_requested": False,
            "decision_response_received": False,
            "allow_decision_emitted": False,
            "deny_decision_emitted": False,
            "approval_created": False,
            "rejection_created": False,
            "authority_granted": False,
            "authority_denied": False,
            "runtime_allowed": False,
            "runtime_blocked": False,
            "enforcement_performed": False,
            "ledger_written": False,
            "global_trace_written": False,
            "runtime_mutated": False,
        },
            BRIDGE_SIDE_EFFECTS_KNOWN_FIELDS,
            label="SideEffects",
        )


# ---------------------------------------------------------------------------
# 68. Non-decisioning guarantee (PolicyBridgeRef != policy evaluated)
# ---------------------------------------------------------------------------


def test_policy_bridge_ref_does_not_imply_policy_evaluated() -> None:
    """PolicyBridgeRef existence does not mean policy was evaluated."""
    r = build_delegation_policy_bridge_ref(
        delegation_ref_id="del-test-001",
    )
    assert r.reference_status == DelegationPolicyCustosBridgeReferenceStatus.POLICY_BRIDGE_REFERENCED
    # POLICY_BRIDGE_REFERENCED is not policy evaluated per docstring contract
    assert r.reference_status.value != "POLICY_EVALUATED"


def test_custos_bridge_ref_does_not_imply_custos_called() -> None:
    """CustosBridgeRef existence does not mean Custos was called."""
    r = build_delegation_custos_bridge_ref(
        delegation_ref_id="del-test-001",
    )
    assert r.reference_status == DelegationPolicyCustosBridgeReferenceStatus.CUSTOS_BRIDGE_REFERENCED


def test_decision_request_intent_does_not_execute_request() -> None:
    """DecisionRequestIntentRef does not execute a decision request."""
    r = build_delegation_policy_decision_request_intent_ref(
        delegation_ref_id="del-test-001",
    )
    assert r.reference_status == (
        DelegationPolicyCustosBridgeReferenceStatus.POLICY_DECISION_REQUEST_INTENT_REFERENCED
    )


def test_decision_response_placeholder_does_not_contain_response() -> None:
    """ResponsePlaceholderRef is a placeholder, not a response."""
    r = build_delegation_policy_decision_response_placeholder_ref(
        delegation_ref_id="del-test-001",
    )
    assert r.reference_status == (
        DelegationPolicyCustosBridgeReferenceStatus
        .POLICY_DECISION_RESPONSE_PLACEHOLDER_REFERENCED
    )


# ---------------------------------------------------------------------------
# 69. Envelope contains all ref ID tuples
# ---------------------------------------------------------------------------


def test_envelope_collects_all_ref_id_tuples() -> None:
    """Envelope collects policy_bridge, custos_bridge, context, decision intent
    and response placeholder ref IDs."""
    pbr = build_delegation_policy_bridge_ref(delegation_ref_id="del-test-001")
    cbr = build_delegation_custos_bridge_ref(delegation_ref_id="del-test-001")
    envelope = build_delegation_policy_custos_bridge_envelope(
        delegation_ref_id="del-test-001",
        policy_bridge_refs=[pbr],
        custos_bridge_refs=[cbr],
    )
    assert pbr.policy_bridge_ref_id in envelope.policy_bridge_ref_ids
    assert cbr.custos_bridge_ref_id in envelope.custos_bridge_ref_ids


# ---------------------------------------------------------------------------
# 70. Readiness profile missing_components list
# ---------------------------------------------------------------------------


def test_readiness_profile_reports_missing_components() -> None:
    """ReadinessProfile with nothing present reports all as missing."""
    profile = build_delegation_policy_custos_bridge_readiness_profile(
        delegation_ref_id="del-test-001",
    )
    assert len(profile.missing_components) == 13
    assert "policy_bridge_refs" in profile.missing_components
    assert "custos_bridge_refs" in profile.missing_components
    assert "operator_review_context" in profile.missing_components


def test_readiness_profile_with_all_present() -> None:
    """ReadinessProfile with all present has empty missing_components."""
    profile = build_delegation_policy_custos_bridge_readiness_profile(
        delegation_ref_id="del-test-001",
        has_policy_bridge_refs=True,
        has_custos_bridge_refs=True,
        has_policy_context_refs=True,
        has_custos_context_refs=True,
        has_policy_decision_request_intent_refs=True,
        has_custos_decision_request_intent_refs=True,
        has_policy_decision_response_placeholders=True,
        has_custos_decision_response_placeholders=True,
        has_operator_review_context=True,
        has_shadow_resolver_context=True,
        has_authority_context=True,
        has_scope_context=True,
        has_evidence_context=True,
    )
    assert len(profile.missing_components) == 0


# ---------------------------------------------------------------------------
# 71-72. Unavailable reason strings
# ---------------------------------------------------------------------------


def test_readiness_profile_unavailable_reasons_are_non_empty() -> None:
    """All unavailable reasons are non-empty strings."""
    profile = build_delegation_policy_custos_bridge_readiness_profile(
        delegation_ref_id="del-test-001",
    )
    assert len(profile.policy_engine_unavailable_reason) > 0
    assert len(profile.custos_runtime_unavailable_reason) > 0
    assert len(profile.decision_engine_unavailable_reason) > 0
    assert len(profile.enforcement_unavailable_reason) > 0
    assert len(profile.trace_unavailable_reason) > 0
    assert len(profile.ledger_unavailable_reason) > 0


def test_unavailable_bindings_dict_populated() -> None:
    """Unavailable bindings dict contains expected keys."""
    assert "Policy Engine" in DELEGATION_POLICY_CUSTOS_BRIDGE_UNAVAILABLE_BINDINGS
    assert "Custos Runtime" in DELEGATION_POLICY_CUSTOS_BRIDGE_UNAVAILABLE_BINDINGS
    assert "Decision Engine" in DELEGATION_POLICY_CUSTOS_BRIDGE_UNAVAILABLE_BINDINGS
    assert "Enforcement Engine" in DELEGATION_POLICY_CUSTOS_BRIDGE_UNAVAILABLE_BINDINGS
    assert "P1.8.13 Runtime/Execution ReadinessRef Model" in DELEGATION_POLICY_CUSTOS_BRIDGE_UNAVAILABLE_BINDINGS
    assert "Output Passport / P1.9" in DELEGATION_POLICY_CUSTOS_BRIDGE_UNAVAILABLE_BINDINGS


# ---------------------------------------------------------------------------
# 73. Binding collects all context hashes
# ---------------------------------------------------------------------------


def test_binding_collects_all_context_hashes() -> None:
    """Binding collects P1.8 context hashes plus bridge envelope hash."""
    envelope = build_delegation_policy_custos_bridge_envelope(
        delegation_ref_id="del-test-001",
        delegation_identity_hash="a" * 40,
        role_binding_hash="b" * 40,
    )
    binding = build_delegation_policy_custos_bridge_binding(
        delegation_ref_id="del-test-001",
        envelope=envelope,
        delegation_identity_hash="a" * 40,
        role_binding_hash="b" * 40,
    )
    assert binding.delegation_identity_hash == "a" * 40
    assert binding.role_binding_hash == "b" * 40
    assert binding.policy_custos_bridge_envelope_hash == envelope.policy_custos_bridge_envelope_hash


# ---------------------------------------------------------------------------
# 74. Binding set collects binding IDs
# ---------------------------------------------------------------------------


def test_binding_set_collects_binding_ids() -> None:
    """BindingSet tuple contains binding IDs from all bindings."""
    envelope = build_delegation_policy_custos_bridge_envelope(
        delegation_ref_id="del-test-001",
    )
    b1 = build_delegation_policy_custos_bridge_binding(
        delegation_ref_id="del-test-001",
        envelope=envelope,
        binding_id="binding-a",
    )
    b2 = build_delegation_policy_custos_bridge_binding(
        delegation_ref_id="del-test-001",
        envelope=envelope,
        binding_id="binding-b",
    )
    bs = build_delegation_policy_custos_bridge_binding_set(
        delegation_ref_id="del-test-001",
        bindings=[b2, b1],
    )
    assert len(bs.bindings) == 2
    assert bs.bindings[0].binding_id == "binding-a"
    assert bs.bindings[1].binding_id == "binding-b"
