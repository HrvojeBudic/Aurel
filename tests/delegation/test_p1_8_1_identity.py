"""P1.8.1 — Delegation Identity / DelegationRef Schema tests."""
from __future__ import annotations

import json
from dataclasses import fields

import pytest

from agentic_runtime.delegation import (
    DELEGATION_IDENTITY_UNAVAILABLE_BINDINGS,
    DELEGATION_REF_SCHEMA_VERSION,
    DelegationIdentityKind,
    DelegationIdentitySideEffects,
    DelegationIdentityStatus,
    DelegationRefBindingKind,
    DelegationSourceLabel,
    DelegationUnknownFieldError,
    build_delegation_foundation_status,
    build_delegation_identity,
    build_delegation_identity_status_report,
    build_delegation_record,
    build_delegation_ref,
    build_delegation_ref_binding,
    hash_delegation_identity,
    hash_delegation_ref,
    serialize_delegation_identity,
    serialize_delegation_ref,
)
from agentic_runtime.delegation.foundation import (
    DelegationActorKind,
    DelegationAuthorityKind,
    DelegationConstraintKind,
    DelegationSubjectKind,
    NonRepudiationProofStatus,
    build_agent_identity_mesh_ref,
    build_delegation_actor_ref,
    build_delegation_authority_ref,
    build_delegation_constraint,
    build_delegation_subject,
    build_non_repudiation_ref,
    hash_delegation_record,
)

DEV_FIXTURE_CREATED_AT = "2026-06-26T00:00:00Z"


def _dev_fixture_record(created_at: str = DEV_FIXTURE_CREATED_AT):
    """P1.8.0 DEV_FIXTURE DelegationRecord → record_hash."""
    delegator = build_delegation_actor_ref(
        DelegationActorKind.OPERATOR,
        "fixture-operator",
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    delegate = build_delegation_actor_ref(
        DelegationActorKind.AGENT,
        "fixture-agent",
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    subject = build_delegation_subject(
        DelegationSubjectKind.ACTION,
        "fixture-action-ref",
        description="DEV_FIXTURE delegated action subject",
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    authority_ref = build_delegation_authority_ref(
        DelegationAuthorityKind.OPERATOR_DECLARED,
        "operator-declared fixture authority context",
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    constraints = [
        build_delegation_constraint(
            DelegationConstraintKind.SCOPE_BOUND,
            "fixture-scope",
            required_review=True,
            source_label=DelegationSourceLabel.DEV_FIXTURE,
        ),
    ]
    non_repudiation_ref = build_non_repudiation_ref(
        proof_status=NonRepudiationProofStatus.REFERENCE_ONLY,
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    identity_mesh_ref = build_agent_identity_mesh_ref(
        "fixture-agent-ref",
        "fixture-identity-ref",
        "fixture-mesh-scope",
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    return build_delegation_record(
        delegator,
        delegate,
        subject,
        authority_ref,
        constraints,
        non_repudiation_ref,
        identity_mesh_ref,
        created_at=created_at,
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )


# -----------------------------------------------------------------------
# Test 1: Imports work from agentic_runtime.delegation
# -----------------------------------------------------------------------


def test_p1_8_1_imports_work() -> None:
    import agentic_runtime.delegation as delegation

    assert hasattr(delegation, "DelegationRef")
    assert hasattr(delegation, "DelegationIdentity")
    assert hasattr(delegation, "DelegationRefBinding")
    assert hasattr(delegation, "DelegationIdentitySideEffects")
    assert hasattr(delegation, "DelegationIdentityStatusReport")
    # P1.8.0 exports remain
    assert hasattr(delegation, "DelegationRecord")
    assert hasattr(delegation, "build_delegation_record")
    assert hasattr(delegation, "hash_delegation_record")


# -----------------------------------------------------------------------
# Test 2: P1.8.0 DelegationRecord can feed P1.8.1 identity/ref path
# -----------------------------------------------------------------------


def test_p1_8_0_record_feeds_p1_8_1_ref() -> None:
    record = _dev_fixture_record()
    delegation_ref = build_delegation_ref(
        delegation_id=record.delegation_id,
        record_hash=record.record_hash,
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    assert delegation_ref.delegation_id == record.delegation_id
    assert delegation_ref.record_hash == record.record_hash
    assert delegation_ref.source_label is DelegationSourceLabel.DEV_FIXTURE


# -----------------------------------------------------------------------
# Test 3: DelegationRef builds deterministically
# -----------------------------------------------------------------------


def test_delegation_ref_builds_deterministically() -> None:
    record = _dev_fixture_record()
    first = build_delegation_ref(
        delegation_id=record.delegation_id,
        record_hash=record.record_hash,
        identity_kind=DelegationIdentityKind.RECORD_REF,
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    second = build_delegation_ref(
        delegation_id=record.delegation_id,
        record_hash=record.record_hash,
        identity_kind=DelegationIdentityKind.RECORD_REF,
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    assert first == second
    assert first.ref_hash == second.ref_hash
    assert first.delegation_ref_id == second.delegation_ref_id


# -----------------------------------------------------------------------
# Test 4: DelegationIdentity builds deterministically
# -----------------------------------------------------------------------


def test_delegation_identity_builds_deterministically() -> None:
    first = build_delegation_identity(
        delegation_ref="ref:test",
        subject_ref="subject:test",
        record_hash="abc123",
        delegator_ref="actor:delegator",
        delegate_ref="actor:delegate",
        authority_ref="authority:test",
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    second = build_delegation_identity(
        delegation_ref="ref:test",
        subject_ref="subject:test",
        record_hash="abc123",
        delegator_ref="actor:delegator",
        delegate_ref="actor:delegate",
        authority_ref="authority:test",
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    assert first == second
    assert first.identity_hash == second.identity_hash


# -----------------------------------------------------------------------
# Test 5: DelegationRefBinding builds deterministically
# -----------------------------------------------------------------------


def test_ref_binding_builds_deterministically() -> None:
    first = build_delegation_ref_binding(
        delegation_ref_id="ref:abc",
        delegation_id="delegation:def",
        record_hash="record-hash-here",
        binding_kind=DelegationRefBindingKind.RECORD_HASH_BINDING,
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    second = build_delegation_ref_binding(
        delegation_ref_id="ref:abc",
        delegation_id="delegation:def",
        record_hash="record-hash-here",
        binding_kind=DelegationRefBindingKind.RECORD_HASH_BINDING,
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    assert first == second
    assert first.binding_hash == second.binding_hash
    assert first.binding_id == second.binding_id


# -----------------------------------------------------------------------
# Test 6: DelegationIdentityStatusReport builds deterministically
# -----------------------------------------------------------------------


def test_status_report_builds_deterministically() -> None:
    first = build_delegation_identity_status_report()
    second = build_delegation_identity_status_report()
    assert first.status_hash == second.status_hash
    assert first.status_label is DelegationSourceLabel.DEV_FIXTURE


# -----------------------------------------------------------------------
# Test 7: Identical DelegationRef input produces identical ref_hash
# -----------------------------------------------------------------------


def test_identical_ref_input_produces_identical_ref_hash() -> None:
    record = _dev_fixture_record()
    ref_a = build_delegation_ref(
        delegation_id=record.delegation_id,
        record_hash=record.record_hash,
    )
    ref_b = build_delegation_ref(
        delegation_id=record.delegation_id,
        record_hash=record.record_hash,
    )
    assert ref_a.ref_hash == ref_b.ref_hash
    assert hash_delegation_ref(ref_a) == hash_delegation_ref(ref_b)
    assert len(ref_a.ref_hash) == 64


# -----------------------------------------------------------------------
# Test 8: Changed delegation_id or record_hash changes ref_hash
# -----------------------------------------------------------------------


def test_changed_id_or_record_changes_ref_hash() -> None:
    record = _dev_fixture_record()
    base = build_delegation_ref(
        delegation_id=record.delegation_id,
        record_hash=record.record_hash,
    )
    changed_id = build_delegation_ref(
        delegation_id="delegation:different-id",
        record_hash=record.record_hash,
    )
    changed_record = build_delegation_ref(
        delegation_id=record.delegation_id,
        record_hash="different-record-hash",
    )
    assert changed_id.ref_hash != base.ref_hash
    assert changed_record.ref_hash != base.ref_hash


# -----------------------------------------------------------------------
# Test 9: Identical DelegationIdentity input produces identical identity_hash
# -----------------------------------------------------------------------


def test_identical_identity_input_produces_identical_identity_hash() -> None:
    first = build_delegation_identity(
        delegation_ref="ref:test",
        subject_ref="subject:test",
        record_hash="abc123",
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    second = build_delegation_identity(
        delegation_ref="ref:test",
        subject_ref="subject:test",
        record_hash="abc123",
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    assert first.identity_hash == second.identity_hash
    assert hash_delegation_identity(first) == hash_delegation_identity(second)
    assert len(first.identity_hash) == 64


# -----------------------------------------------------------------------
# Test 10: Changed delegator/delegate/subject/record_hash changes identity_hash
# -----------------------------------------------------------------------


def test_changed_identity_fields_change_identity_hash() -> None:
    base = build_delegation_identity(
        delegation_ref="ref:base",
        subject_ref="subject:base",
        record_hash="abc123",
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    changed_delegator = build_delegation_identity(
        delegation_ref="ref:base",
        subject_ref="subject:base",
        record_hash="abc123",
        delegator_ref="actor:different",
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    changed_subject = build_delegation_identity(
        delegation_ref="ref:base",
        subject_ref="subject:different",
        record_hash="abc123",
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    changed_record = build_delegation_identity(
        delegation_ref="ref:base",
        subject_ref="subject:base",
        record_hash="different",
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    assert changed_delegator.identity_hash != base.identity_hash
    assert changed_subject.identity_hash != base.identity_hash
    assert changed_record.identity_hash != base.identity_hash


# -----------------------------------------------------------------------
# Test 11: Serialization is JSON-safe and deterministic
# -----------------------------------------------------------------------


def test_serialization_is_json_safe_and_deterministic() -> None:
    record = _dev_fixture_record()
    ref = build_delegation_ref(
        delegation_id=record.delegation_id,
        record_hash=record.record_hash,
    )
    first_json = serialize_delegation_ref(ref)
    second_json = serialize_delegation_ref(ref)
    assert first_json == second_json
    decoded = json.loads(first_json)
    assert decoded["ref_hash"] == ref.ref_hash
    assert decoded["delegation_id"] == record.delegation_id

    identity = build_delegation_identity(
        delegation_ref=ref.delegation_ref_id,
        subject_ref="subject:test",
        record_hash=record.record_hash,
    )
    id_json = serialize_delegation_identity(identity)
    id_decoded = json.loads(id_json)
    assert id_decoded["identity_hash"] == identity.identity_hash


# -----------------------------------------------------------------------
# Test 12: Source/truth labels are visible
# -----------------------------------------------------------------------


def test_source_and_truth_labels_are_visible() -> None:
    record = _dev_fixture_record()
    ref = build_delegation_ref(
        delegation_id=record.delegation_id,
        record_hash=record.record_hash,
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    identity = build_delegation_identity(
        delegation_ref=ref.delegation_ref_id,
        subject_ref="subject:test",
        record_hash=record.record_hash,
    )
    status = build_delegation_identity_status_report()

    assert ref.source_label is DelegationSourceLabel.DEV_FIXTURE
    assert identity.source_label is DelegationSourceLabel.DEV_FIXTURE
    assert status.status_label is DelegationSourceLabel.DEV_FIXTURE
    assert status.available_contracts["DelegationRef"] == DelegationSourceLabel.LIVE.value


# -----------------------------------------------------------------------
# Test 13: DEV_FIXTURE path is explicit in tests
# -----------------------------------------------------------------------


def test_dev_fixture_path_is_explicit() -> None:
    record = _dev_fixture_record()
    ref = build_delegation_ref(
        delegation_id=record.delegation_id,
        record_hash=record.record_hash,
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    binding = build_delegation_ref_binding(
        delegation_ref_id=ref.delegation_ref_id,
        delegation_id=record.delegation_id,
        record_hash=record.record_hash,
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    identity = build_delegation_identity(
        delegation_ref=ref.delegation_ref_id,
        subject_ref="subject:test",
        record_hash=record.record_hash,
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    status = build_delegation_identity_status_report()

    assert ref.source_label is DelegationSourceLabel.DEV_FIXTURE
    assert binding.source_label is DelegationSourceLabel.DEV_FIXTURE
    assert identity.source_label is DelegationSourceLabel.DEV_FIXTURE
    assert status.status_label is DelegationSourceLabel.DEV_FIXTURE
    assert record.source_label is DelegationSourceLabel.DEV_FIXTURE


# -----------------------------------------------------------------------
# Test 14: UNAVAILABLE reasons exist for future surfaces
# -----------------------------------------------------------------------


def test_unavailable_reasons_exist_for_future_surfaces() -> None:
    status = build_delegation_identity_status_report()
    assert status.unavailable_bindings == DELEGATION_IDENTITY_UNAVAILABLE_BINDINGS
    assert "Projection/API/Event/Read Model" in status.unavailable_bindings
    assert "CLI/Shell/TUI Binding" in status.unavailable_bindings
    assert "Ledger Write" in status.unavailable_bindings
    assert "Global Trace Write" in status.unavailable_bindings
    assert "Policy/Custos Enforcement" in status.unavailable_bindings
    assert "Approval Activation" in status.unavailable_bindings
    assert "Identity Resolver" in status.unavailable_bindings
    assert "Non-Repudiation Verifier" in status.unavailable_bindings
    assert "Runtime Delegation Execution" in status.unavailable_bindings


# -----------------------------------------------------------------------
# Test 15: All DelegationIdentitySideEffects booleans are false
# -----------------------------------------------------------------------


def test_all_identity_side_effects_booleans_are_false() -> None:
    status = build_delegation_identity_status_report()
    se = DelegationIdentitySideEffects()
    for side_effects in (status.side_effects, se):
        for item in fields(side_effects):
            assert getattr(side_effects, item.name) is False, (
                f"{item.name} should be False"
            )


# -----------------------------------------------------------------------
# Test 16: DelegationRef does not imply approval
# -----------------------------------------------------------------------


def test_delegation_ref_does_not_imply_approval() -> None:
    record = _dev_fixture_record()
    ref = build_delegation_ref(
        delegation_id=record.delegation_id,
        record_hash=record.record_hash,
    )
    payload = ref.to_canonical_dict()
    assert "approved" not in payload
    assert "authorized" not in payload
    assert "permission" not in payload
    assert DelegationSourceLabel.TRACE_VERIFIED.value not in payload.values()


# -----------------------------------------------------------------------
# Test 17: DelegationIdentity does not imply verification
# -----------------------------------------------------------------------


def test_delegation_identity_does_not_imply_verification() -> None:
    record = _dev_fixture_record()
    identity = build_delegation_identity(
        delegation_ref="ref:test",
        subject_ref="subject:test",
        record_hash=record.record_hash,
    )
    payload = identity.to_canonical_dict()
    assert "verified" not in payload
    assert "TRACE_VERIFIED" not in str(payload.values())
    assert identity.identity_status is DelegationIdentityStatus.REFERENCE_ONLY


# -----------------------------------------------------------------------
# Test 18: DelegationRefBinding does not imply trace proof
# -----------------------------------------------------------------------


def test_ref_binding_does_not_imply_trace_proof() -> None:
    record = _dev_fixture_record()
    ref = build_delegation_ref(
        delegation_id=record.delegation_id,
        record_hash=record.record_hash,
    )
    binding = build_delegation_ref_binding(
        delegation_ref_id=ref.delegation_ref_id,
        delegation_id=record.delegation_id,
        record_hash=record.record_hash,
    )
    payload = binding.to_canonical_dict()
    assert "trace" not in payload
    assert "verified" not in payload
    assert "proof" not in payload


# -----------------------------------------------------------------------
# Test 19: record_hash is not treated as TRACE_VERIFIED
# -----------------------------------------------------------------------


def test_record_hash_is_not_trace_verified() -> None:
    record = _dev_fixture_record()
    ref = build_delegation_ref(
        delegation_id=record.delegation_id,
        record_hash=record.record_hash,
    )
    identity = build_delegation_identity(
        delegation_ref=ref.delegation_ref_id,
        subject_ref="subject:test",
        record_hash=record.record_hash,
    )
    # Neither object claims TRACE_VERIFIED
    assert ref.source_label is not DelegationSourceLabel.TRACE_VERIFIED
    assert identity.source_label is not DelegationSourceLabel.TRACE_VERIFIED
    # record_hash string is not TRACE_VERIFIED
    assert "TRACE_VERIFIED" not in ref.to_canonical_dict().get("record_hash", "")
    assert "TRACE_VERIFIED" not in identity.to_canonical_dict().get("record_hash", "")


# -----------------------------------------------------------------------
# Test 20: identity_hash is not treated as proof
# -----------------------------------------------------------------------


def test_identity_hash_is_not_proof() -> None:
    identity = build_delegation_identity(
        delegation_ref="ref:test",
        subject_ref="subject:test",
        record_hash="abc123",
    )
    payload = identity.to_canonical_dict()
    assert "proof" not in payload
    assert identity.identity_status is not DelegationIdentityStatus.ACTIVE_SCHEMA
    # identity_hash exists as data but is not a claim of proof
    assert len(identity.identity_hash) == 64


# -----------------------------------------------------------------------
# Test 21: Invalid enum/value input fails closed
# -----------------------------------------------------------------------


def test_invalid_enum_or_value_input_fails_closed() -> None:
    record = _dev_fixture_record()

    with pytest.raises(Exception):
        build_delegation_ref(
            delegation_id=record.delegation_id,
            record_hash=record.record_hash,
            identity_kind="NOT_A_KIND",
        )

    payload = build_delegation_ref(
        delegation_id=record.delegation_id,
        record_hash=record.record_hash,
    ).to_canonical_dict()
    payload["shadow_authorization"] = True
    with pytest.raises(DelegationUnknownFieldError):
        from agentic_runtime.delegation.identity import DelegationRef
        DelegationRef.from_dict(payload)


# -----------------------------------------------------------------------
# Test 22: No field implies permission, enforcement, runtime execution,
#          approval, or non-repudiation verification
# -----------------------------------------------------------------------


def test_no_field_implies_approval_permission_enforcement_or_verification() -> None:
    record = _dev_fixture_record()
    ref = build_delegation_ref(
        delegation_id=record.delegation_id,
        record_hash=record.record_hash,
    )
    identity = build_delegation_identity(
        delegation_ref=ref.delegation_ref_id,
        subject_ref="subject:test",
        record_hash=record.record_hash,
    )

    forbidden_names = frozenset({
        "approved", "authorized", "permission_granted", "enforced",
        "verified", "executed",
    })

    ref_fields = {item.name for item in fields(ref)}
    identity_fields = {item.name for item in fields(identity)}
    assert forbidden_names.isdisjoint(ref_fields)
    assert forbidden_names.isdisjoint(identity_fields)

    side_effect_fields = {item.name for item in fields(DelegationIdentitySideEffects())}
    assert side_effect_fields == {
        "policy_called",
        "custos_called",
        "approval_created",
        "ledger_written",
        "global_trace_written",
        "runtime_mutated",
        "delegation_executed",
        "delegation_enforced",
        "identity_resolved",
        "non_repudiation_verified",
    }
    for name in side_effect_fields:
        assert getattr(DelegationIdentitySideEffects(), name) is False


# -----------------------------------------------------------------------
# Test 23: Full DEV_FIXTURE chain from record to status
# -----------------------------------------------------------------------


def test_full_dev_fixture_chain() -> None:
    record = _dev_fixture_record()
    assert record.source_label is DelegationSourceLabel.DEV_FIXTURE

    ref = build_delegation_ref(
        delegation_id=record.delegation_id,
        record_hash=record.record_hash,
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    assert ref.schema_version == DELEGATION_REF_SCHEMA_VERSION
    assert len(ref.ref_hash) == 64

    binding = build_delegation_ref_binding(
        delegation_ref_id=ref.delegation_ref_id,
        delegation_id=record.delegation_id,
        record_hash=record.record_hash,
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    assert binding.binding_kind is DelegationRefBindingKind.RECORD_HASH_BINDING
    assert len(binding.binding_hash) == 64

    identity = build_delegation_identity(
        delegation_ref=ref.delegation_ref_id,
        subject_ref="subject:test",
        record_hash=record.record_hash,
        delegator_ref="actor:op",
        delegate_ref="actor:agt",
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    assert identity.identity_status is DelegationIdentityStatus.REFERENCE_ONLY
    assert len(identity.identity_hash) == 64

    status = build_delegation_identity_status_report()
    assert status.status_label is DelegationSourceLabel.DEV_FIXTURE
    assert len(status.status_hash) == 64
    assert status.available_contracts["DelegationRef"] == DelegationSourceLabel.LIVE.value
    assert "CLI/Shell/TUI Binding" in status.unavailable_bindings

    for item in fields(status.side_effects):
        assert getattr(status.side_effects, item.name) is False
