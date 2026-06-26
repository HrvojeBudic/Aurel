"""P1.8.2 — Delegator / Delegate / Subject Model tests."""
from __future__ import annotations

import json
from dataclasses import fields

import pytest

from agentic_runtime.delegation import (
    DELEGATION_IDENTITY_UNAVAILABLE_BINDINGS,
    DELEGATION_IDENTITY_SCHEMA_VERSION,
    DELEGATION_ROLES_UNAVAILABLE_BINDINGS,
    DelegationIdentityKind,
    DelegationIdentitySideEffects,
    DelegationIdentityStatus,
    DelegationPartyRoleRef,
    DelegationRefBindingKind,
    DelegationRoleBinding,
    DelegationRoleBindingSet,
    DelegationRoleBindingStatus,
    DelegationRoleKind,
    DelegationRoleSideEffects,
    DelegationRoleStatusReport,
    DelegationSourceLabel,
    DelegatedSubjectRef,
    build_delegated_subject_ref,
    build_delegation_identity,
    build_delegation_party_role_ref,
    build_delegation_ref,
    build_delegation_role_binding,
    build_delegation_role_binding_set,
    build_delegation_role_status_report,
    hash_delegation_identity,
    hash_delegation_ref,
    hash_delegation_role_binding_set,
    serialize_delegation_role_binding_set,
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
    build_delegation_record,
    build_delegation_subject,
    build_non_repudiation_ref,
    hash_delegation_record,
)
from agentic_runtime.delegation.identity import (
    DelegationIdentity,
    DelegationRef,
)
from agentic_runtime.delegation.roles import (
    DelegationValidationError,
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


def _dev_fixture_p1_8_1_ref():
    """Build P1.8.1 DelegationRef from P1.8.0 DEV_FIXTURE record."""
    record = _dev_fixture_record()
    return build_delegation_ref(
        delegation_id=record.delegation_id,
        record_hash=record.record_hash,
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )


def _dev_fixture_p1_8_1_identity():
    """Build P1.8.1 DelegationIdentity from P1.8.1 ref + record."""
    ref = _dev_fixture_p1_8_1_ref()
    record = _dev_fixture_record()
    return build_delegation_identity(
        delegation_ref=ref.delegation_ref_id,
        subject_ref=record.subject.subject_id,
        record_hash=record.record_hash,
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )


# -----------------------------------------------------------------------
# Test 1: Imports work from agentic_runtime.delegation
# -----------------------------------------------------------------------


def test_p1_8_2_imports_work() -> None:
    import agentic_runtime.delegation as delegation

    assert hasattr(delegation, "DelegationRoleKind")
    assert hasattr(delegation, "DelegationRoleBindingStatus")
    assert hasattr(delegation, "DelegationPartyRoleRef")
    assert hasattr(delegation, "DelegatedSubjectRef")
    assert hasattr(delegation, "DelegationRoleBinding")
    assert hasattr(delegation, "DelegationRoleBindingSet")
    assert hasattr(delegation, "DelegationRoleSideEffects")
    assert hasattr(delegation, "DelegationRoleStatusReport")
    # P1.8.0 exports remain
    assert hasattr(delegation, "DelegationRecord")
    assert hasattr(delegation, "build_delegation_record")
    # P1.8.1 exports remain
    assert hasattr(delegation, "DelegationRef")
    assert hasattr(delegation, "DelegationIdentity")
    assert hasattr(delegation, "DelegationRefBinding")
    assert hasattr(delegation, "hash_delegation_ref")
    assert hasattr(delegation, "hash_delegation_identity")


# -----------------------------------------------------------------------
# Test 2: P1.8.1 DelegationRef / DelegationIdentity can feed P1.8.2 role path
# -----------------------------------------------------------------------


def test_p1_8_1_ref_feeds_p1_8_2_role_path() -> None:
    ref = _dev_fixture_p1_8_1_ref()
    identity = _dev_fixture_p1_8_1_identity()

    delegator_role = build_delegation_party_role_ref(
        delegation_ref_id=ref.delegation_ref_id,
        actor_ref="actor:fixture-delegator-hash",
        role_kind=DelegationRoleKind.DELEGATOR,
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    assert delegator_role.delegation_ref_id == ref.delegation_ref_id
    assert delegator_role.role_kind is DelegationRoleKind.DELEGATOR
    assert delegator_role.source_label is DelegationSourceLabel.DEV_FIXTURE
    assert identity.identity_hash != ""
    assert identity.delegation_ref == ref.delegation_ref_id


# -----------------------------------------------------------------------
# Test 3: Delegator role ref builds deterministically
# -----------------------------------------------------------------------


def test_delegator_role_ref_deterministic() -> None:
    a = build_delegation_party_role_ref(
        delegation_ref_id="ref:aaaa1111",
        actor_ref="actor:delegator-1",
        role_kind=DelegationRoleKind.DELEGATOR,
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    b = build_delegation_party_role_ref(
        delegation_ref_id="ref:aaaa1111",
        actor_ref="actor:delegator-1",
        role_kind=DelegationRoleKind.DELEGATOR,
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    assert a.role_ref_hash == b.role_ref_hash
    assert a.role_ref_id == b.role_ref_id


# -----------------------------------------------------------------------
# Test 4: Delegate role ref builds deterministically
# -----------------------------------------------------------------------


def test_delegate_role_ref_deterministic() -> None:
    a = build_delegation_party_role_ref(
        delegation_ref_id="ref:aaaa1111",
        actor_ref="actor:delegate-1",
        role_kind=DelegationRoleKind.DELEGATE,
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    b = build_delegation_party_role_ref(
        delegation_ref_id="ref:aaaa1111",
        actor_ref="actor:delegate-1",
        role_kind=DelegationRoleKind.DELEGATE,
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    assert a.role_ref_hash == b.role_ref_hash


# -----------------------------------------------------------------------
# Test 5: Delegated subject ref builds deterministically
# -----------------------------------------------------------------------


def test_delegated_subject_ref_deterministic() -> None:
    a = build_delegated_subject_ref(
        delegation_ref_id="ref:aaaa1111",
        subject_ref="subject:abcd",
        subject_kind=DelegationSubjectKind.ACTION,
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    b = build_delegated_subject_ref(
        delegation_ref_id="ref:aaaa1111",
        subject_ref="subject:abcd",
        subject_kind=DelegationSubjectKind.ACTION,
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    assert a.subject_role_hash == b.subject_role_hash
    assert a.subject_role_ref_id == b.subject_role_ref_id


# -----------------------------------------------------------------------
# Test 6: DelegationRoleBinding builds deterministically
# -----------------------------------------------------------------------


def test_delegation_role_binding_deterministic() -> None:
    a = build_delegation_role_binding(
        delegation_ref_id="ref:00001111",
        delegation_identity_hash="a" * 64,
        role_kind=DelegationRoleKind.DELEGATOR,
        role_ref_hash="b" * 64,
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    b = build_delegation_role_binding(
        delegation_ref_id="ref:00001111",
        delegation_identity_hash="a" * 64,
        role_kind=DelegationRoleKind.DELEGATOR,
        role_ref_hash="b" * 64,
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    assert a.binding_hash == b.binding_hash
    assert a.binding_id == b.binding_id


# -----------------------------------------------------------------------
# Test 7: DelegationRoleBindingSet builds deterministically
# -----------------------------------------------------------------------


def test_delegation_role_binding_set_deterministic() -> None:
    ref = _dev_fixture_p1_8_1_ref()
    identity = _dev_fixture_p1_8_1_identity()

    def _build():
        delegator = build_delegation_party_role_ref(
            delegation_ref_id=ref.delegation_ref_id,
            actor_ref="actor:fixture-delegator",
            role_kind=DelegationRoleKind.DELEGATOR,
            source_label=DelegationSourceLabel.DEV_FIXTURE,
        )
        delegate = build_delegation_party_role_ref(
            delegation_ref_id=ref.delegation_ref_id,
            actor_ref="actor:fixture-agent",
            role_kind=DelegationRoleKind.DELEGATE,
            source_label=DelegationSourceLabel.DEV_FIXTURE,
        )
        subject = build_delegated_subject_ref(
            delegation_ref_id=ref.delegation_ref_id,
            subject_ref="subject:fixture-action",
            subject_kind=DelegationSubjectKind.ACTION,
            source_label=DelegationSourceLabel.DEV_FIXTURE,
        )
        return build_delegation_role_binding_set(
            delegator=delegator,
            delegate=delegate,
            subject=subject,
            delegation_ref_id=ref.delegation_ref_id,
            delegation_identity_hash=identity.identity_hash,
            source_label=DelegationSourceLabel.DEV_FIXTURE,
        )

    a = _build()
    b = _build()
    assert a.role_binding_hash == b.role_binding_hash
    assert a.binding_set_id == b.binding_set_id


# -----------------------------------------------------------------------
# Test 8: DelegationRoleStatusReport builds deterministically
# -----------------------------------------------------------------------


def test_delegation_role_status_report_deterministic() -> None:
    a = build_delegation_role_status_report()
    b = build_delegation_role_status_report()
    assert a.status_hash == b.status_hash


# -----------------------------------------------------------------------
# Test 9: Identical DelegationPartyRoleRef input produces identical role_ref_hash
# -----------------------------------------------------------------------


def test_party_role_ref_same_input_same_hash() -> None:
    a = build_delegation_party_role_ref(
        delegation_ref_id="ref:test0000",
        actor_ref="actor:some-actor",
        role_kind=DelegationRoleKind.DELEGATOR,
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    b = build_delegation_party_role_ref(
        delegation_ref_id="ref:test0000",
        actor_ref="actor:some-actor",
        role_kind=DelegationRoleKind.DELEGATOR,
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    assert a.role_ref_hash == b.role_ref_hash


# -----------------------------------------------------------------------
# Test 10: Changed actor_ref changes role_ref_hash
# -----------------------------------------------------------------------


def test_party_role_ref_changed_actor_changes_hash() -> None:
    a = build_delegation_party_role_ref(
        delegation_ref_id="ref:test0000",
        actor_ref="actor:A",
        role_kind=DelegationRoleKind.DELEGATOR,
    )
    b = build_delegation_party_role_ref(
        delegation_ref_id="ref:test0000",
        actor_ref="actor:B",
        role_kind=DelegationRoleKind.DELEGATOR,
    )
    assert a.role_ref_hash != b.role_ref_hash


# -----------------------------------------------------------------------
# Test 11: Identical DelegatedSubjectRef input produces identical subject_role_hash
# -----------------------------------------------------------------------


def test_subject_ref_same_input_same_hash() -> None:
    a = build_delegated_subject_ref(
        delegation_ref_id="ref:test0000",
        subject_ref="subject:task-42",
        subject_kind=DelegationSubjectKind.TASK,
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    b = build_delegated_subject_ref(
        delegation_ref_id="ref:test0000",
        subject_ref="subject:task-42",
        subject_kind=DelegationSubjectKind.TASK,
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    assert a.subject_role_hash == b.subject_role_hash


# -----------------------------------------------------------------------
# Test 12: Changed subject_ref changes subject_role_hash
# -----------------------------------------------------------------------


def test_subject_ref_changed_ref_changes_hash() -> None:
    a = build_delegated_subject_ref(
        delegation_ref_id="ref:test0000",
        subject_ref="subject:task-42",
        subject_kind=DelegationSubjectKind.TASK,
    )
    b = build_delegated_subject_ref(
        delegation_ref_id="ref:test0000",
        subject_ref="subject:task-43",
        subject_kind=DelegationSubjectKind.TASK,
    )
    assert a.subject_role_hash != b.subject_role_hash


# -----------------------------------------------------------------------
# Test 13: Identical DelegationRoleBindingSet input produces identical role_binding_hash
# -----------------------------------------------------------------------


def test_binding_set_same_input_same_hash() -> None:
    ref = _dev_fixture_p1_8_1_ref()
    identity = _dev_fixture_p1_8_1_identity()

    def _build():
        delegator = build_delegation_party_role_ref(
            delegation_ref_id=ref.delegation_ref_id,
            actor_ref="actor:op",
            role_kind=DelegationRoleKind.DELEGATOR,
        )
        delegate = build_delegation_party_role_ref(
            delegation_ref_id=ref.delegation_ref_id,
            actor_ref="actor:ag",
            role_kind=DelegationRoleKind.DELEGATE,
        )
        subject = build_delegated_subject_ref(
            delegation_ref_id=ref.delegation_ref_id,
            subject_ref="subject:ac",
            subject_kind=DelegationSubjectKind.ACTION,
        )
        return build_delegation_role_binding_set(
            delegator=delegator,
            delegate=delegate,
            subject=subject,
            delegation_ref_id=ref.delegation_ref_id,
            delegation_identity_hash=identity.identity_hash,
        )

    a = _build()
    b = _build()
    assert a.role_binding_hash == b.role_binding_hash


# -----------------------------------------------------------------------
# Test 14: Changed delegator changes role_binding_hash
# -----------------------------------------------------------------------


def test_binding_set_changed_delegator_changes_hash() -> None:
    ref = _dev_fixture_p1_8_1_ref()
    identity = _dev_fixture_p1_8_1_identity()

    delegate = build_delegation_party_role_ref(
        delegation_ref_id=ref.delegation_ref_id,
        actor_ref="actor:ag",
        role_kind=DelegationRoleKind.DELEGATE,
    )
    subject = build_delegated_subject_ref(
        delegation_ref_id=ref.delegation_ref_id,
        subject_ref="subject:ac",
        subject_kind=DelegationSubjectKind.ACTION,
    )

    a = build_delegation_role_binding_set(
        delegator=build_delegation_party_role_ref(
            delegation_ref_id=ref.delegation_ref_id,
            actor_ref="actor:op-a",
            role_kind=DelegationRoleKind.DELEGATOR,
        ),
        delegate=delegate,
        subject=subject,
        delegation_ref_id=ref.delegation_ref_id,
        delegation_identity_hash=identity.identity_hash,
    )
    b = build_delegation_role_binding_set(
        delegator=build_delegation_party_role_ref(
            delegation_ref_id=ref.delegation_ref_id,
            actor_ref="actor:op-b",
            role_kind=DelegationRoleKind.DELEGATOR,
        ),
        delegate=delegate,
        subject=subject,
        delegation_ref_id=ref.delegation_ref_id,
        delegation_identity_hash=identity.identity_hash,
    )
    assert a.role_binding_hash != b.role_binding_hash


# -----------------------------------------------------------------------
# Test 15: Changed delegate changes role_binding_hash
# -----------------------------------------------------------------------


def test_binding_set_changed_delegate_changes_hash() -> None:
    ref = _dev_fixture_p1_8_1_ref()
    identity = _dev_fixture_p1_8_1_identity()

    delegator = build_delegation_party_role_ref(
        delegation_ref_id=ref.delegation_ref_id,
        actor_ref="actor:op",
        role_kind=DelegationRoleKind.DELEGATOR,
    )
    subject = build_delegated_subject_ref(
        delegation_ref_id=ref.delegation_ref_id,
        subject_ref="subject:ac",
        subject_kind=DelegationSubjectKind.ACTION,
    )

    a = build_delegation_role_binding_set(
        delegator=delegator,
        delegate=build_delegation_party_role_ref(
            delegation_ref_id=ref.delegation_ref_id,
            actor_ref="actor:ag-a",
            role_kind=DelegationRoleKind.DELEGATE,
        ),
        subject=subject,
        delegation_ref_id=ref.delegation_ref_id,
        delegation_identity_hash=identity.identity_hash,
    )
    b = build_delegation_role_binding_set(
        delegator=delegator,
        delegate=build_delegation_party_role_ref(
            delegation_ref_id=ref.delegation_ref_id,
            actor_ref="actor:ag-b",
            role_kind=DelegationRoleKind.DELEGATE,
        ),
        subject=subject,
        delegation_ref_id=ref.delegation_ref_id,
        delegation_identity_hash=identity.identity_hash,
    )
    assert a.role_binding_hash != b.role_binding_hash


# -----------------------------------------------------------------------
# Test 16: Changed subject changes role_binding_hash
# -----------------------------------------------------------------------


def test_binding_set_changed_subject_changes_hash() -> None:
    ref = _dev_fixture_p1_8_1_ref()
    identity = _dev_fixture_p1_8_1_identity()

    delegator = build_delegation_party_role_ref(
        delegation_ref_id=ref.delegation_ref_id,
        actor_ref="actor:op",
        role_kind=DelegationRoleKind.DELEGATOR,
    )
    delegate = build_delegation_party_role_ref(
        delegation_ref_id=ref.delegation_ref_id,
        actor_ref="actor:ag",
        role_kind=DelegationRoleKind.DELEGATE,
    )

    a = build_delegation_role_binding_set(
        delegator=delegator,
        delegate=delegate,
        subject=build_delegated_subject_ref(
            delegation_ref_id=ref.delegation_ref_id,
            subject_ref="subject:ac-a",
            subject_kind=DelegationSubjectKind.ACTION,
        ),
        delegation_ref_id=ref.delegation_ref_id,
        delegation_identity_hash=identity.identity_hash,
    )
    b = build_delegation_role_binding_set(
        delegator=delegator,
        delegate=delegate,
        subject=build_delegated_subject_ref(
            delegation_ref_id=ref.delegation_ref_id,
            subject_ref="subject:ac-b",
            subject_kind=DelegationSubjectKind.ACTION,
        ),
        delegation_ref_id=ref.delegation_ref_id,
        delegation_identity_hash=identity.identity_hash,
    )
    assert a.role_binding_hash != b.role_binding_hash


# -----------------------------------------------------------------------
# Test 17: Serialization is JSON-safe and deterministic
# -----------------------------------------------------------------------


def test_serialization_json_safe_and_deterministic() -> None:
    ref = _dev_fixture_p1_8_1_ref()
    identity = _dev_fixture_p1_8_1_identity()
    delegator = build_delegation_party_role_ref(
        delegation_ref_id=ref.delegation_ref_id,
        actor_ref="actor:op",
        role_kind=DelegationRoleKind.DELEGATOR,
    )
    delegate = build_delegation_party_role_ref(
        delegation_ref_id=ref.delegation_ref_id,
        actor_ref="actor:ag",
        role_kind=DelegationRoleKind.DELEGATE,
    )
    subject = build_delegated_subject_ref(
        delegation_ref_id=ref.delegation_ref_id,
        subject_ref="subject:ac",
        subject_kind=DelegationSubjectKind.ACTION,
    )
    binding_set = build_delegation_role_binding_set(
        delegator=delegator,
        delegate=delegate,
        subject=subject,
        delegation_ref_id=ref.delegation_ref_id,
        delegation_identity_hash=identity.identity_hash,
    )

    a = serialize_delegation_role_binding_set(binding_set)
    b = serialize_delegation_role_binding_set(binding_set)
    assert a == b

    # Must be valid JSON
    parsed = json.loads(a)
    assert isinstance(parsed, dict)
    assert "delegator" in parsed
    assert "delegate" in parsed
    assert "subject" in parsed


# -----------------------------------------------------------------------
# Test 18: Source/truth labels are visible
# -----------------------------------------------------------------------


def test_source_labels_visible() -> None:
    ref = _dev_fixture_p1_8_1_ref()
    identity = _dev_fixture_p1_8_1_identity()
    delegator = build_delegation_party_role_ref(
        delegation_ref_id=ref.delegation_ref_id,
        actor_ref="actor:op",
        role_kind=DelegationRoleKind.DELEGATOR,
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    delegate = build_delegation_party_role_ref(
        delegation_ref_id=ref.delegation_ref_id,
        actor_ref="actor:ag",
        role_kind=DelegationRoleKind.DELEGATE,
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    subject = build_delegated_subject_ref(
        delegation_ref_id=ref.delegation_ref_id,
        subject_ref="subject:ac",
        subject_kind=DelegationSubjectKind.ACTION,
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    binding_set = build_delegation_role_binding_set(
        delegator=delegator,
        delegate=delegate,
        subject=subject,
        delegation_ref_id=ref.delegation_ref_id,
        delegation_identity_hash=identity.identity_hash,
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )

    assert delegator.source_label is DelegationSourceLabel.DEV_FIXTURE
    assert delegate.source_label is DelegationSourceLabel.DEV_FIXTURE
    assert subject.source_label is DelegationSourceLabel.DEV_FIXTURE
    assert binding_set.source_label is DelegationSourceLabel.DEV_FIXTURE
    assert DelegationSourceLabel.DEV_FIXTURE.value in serialize_delegation_role_binding_set(binding_set)


# -----------------------------------------------------------------------
# Test 19: DEV_FIXTURE path is explicit in tests
# -----------------------------------------------------------------------


def test_dev_fixture_explicit_in_all_role_refs() -> None:
    ref = _dev_fixture_p1_8_1_ref()
    identity = _dev_fixture_p1_8_1_identity()

    delegator = build_delegation_party_role_ref(
        delegation_ref_id=ref.delegation_ref_id,
        actor_ref="actor:op",
        role_kind=DelegationRoleKind.DELEGATOR,
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    delegate = build_delegation_party_role_ref(
        delegation_ref_id=ref.delegation_ref_id,
        actor_ref="actor:ag",
        role_kind=DelegationRoleKind.DELEGATE,
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    subject = build_delegated_subject_ref(
        delegation_ref_id=ref.delegation_ref_id,
        subject_ref="subject:ac",
        subject_kind=DelegationSubjectKind.ACTION,
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    binding_set = build_delegation_role_binding_set(
        delegator=delegator,
        delegate=delegate,
        subject=subject,
        delegation_ref_id=ref.delegation_ref_id,
        delegation_identity_hash=identity.identity_hash,
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    # Verify DEV_FIXTURE labels on all role objects
    assert delegator.source_label is DelegationSourceLabel.DEV_FIXTURE
    assert delegate.source_label is DelegationSourceLabel.DEV_FIXTURE
    assert subject.source_label is DelegationSourceLabel.DEV_FIXTURE
    assert binding_set.source_label is DelegationSourceLabel.DEV_FIXTURE
    # Verify no LIVE leak
    assert DelegationSourceLabel.LIVE.value not in delegator.to_canonical_dict().values()
    assert DelegationSourceLabel.LIVE.value not in delegate.to_canonical_dict().values()
    assert DelegationSourceLabel.LIVE.value not in subject.to_canonical_dict().values()
    # No TRACE_VERIFIED
    assert delegator.source_label is not DelegationSourceLabel.TRACE_VERIFIED
    assert delegate.source_label is not DelegationSourceLabel.TRACE_VERIFIED
    assert subject.source_label is not DelegationSourceLabel.TRACE_VERIFIED
    assert binding_set.source_label is not DelegationSourceLabel.TRACE_VERIFIED


# -----------------------------------------------------------------------
# Test 20: UNAVAILABLE reasons exist for future surfaces
# -----------------------------------------------------------------------


def test_unavailable_reasons_exist() -> None:
    report = build_delegation_role_status_report()
    unavailable = dict(report.unavailable_bindings)

    assert "Projection/API/Event/Read Model" in unavailable
    assert "CLI/Shell/TUI Binding" in unavailable
    assert "Ledger Write" in unavailable
    assert "Global Trace Write" in unavailable
    assert "Policy/Custos Enforcement" in unavailable
    assert "Approval Activation" in unavailable
    assert "Delegation Resolver" in unavailable
    assert "Delegation Chain Resolver" in unavailable
    assert "Authority Bridge" in unavailable
    assert "Identity Mesh Resolver" in unavailable
    assert "Non-Repudiation Verifier" in unavailable
    assert "Runtime Delegation Execution" in unavailable

    for key, reason in unavailable.items():
        assert isinstance(reason, str) and len(reason) > 0, f"Empty reason for {key}"


# -----------------------------------------------------------------------
# Test 21: All DelegationRoleSideEffects booleans are false
# -----------------------------------------------------------------------


def test_side_effects_all_false() -> None:
    se = DelegationRoleSideEffects()
    for f in fields(DelegationRoleSideEffects):
        assert getattr(se, f.name) is False, f"Side effect {f.name} is not False"


# -----------------------------------------------------------------------
# Test 22-28: Boundary / negative tests
# -----------------------------------------------------------------------


def test_delegator_role_does_not_imply_verified_authority() -> None:
    """DelegationPartyRoleRef with DELEGATOR role_kind does not verify authority."""
    role = build_delegation_party_role_ref(
        delegation_ref_id="ref:00001111",
        actor_ref="actor:op",
        role_kind=DelegationRoleKind.DELEGATOR,
    )
    assert "authority" not in role.to_canonical_dict()
    assert not hasattr(role, "authority_verified")


def test_delegate_role_does_not_imply_agent_activation() -> None:
    """DelegationPartyRoleRef with DELEGATE role_kind does not activate agent."""
    role = build_delegation_party_role_ref(
        delegation_ref_id="ref:00001111",
        actor_ref="actor:ag",
        role_kind=DelegationRoleKind.DELEGATE,
    )
    assert "activated" not in role.to_canonical_dict()
    assert not hasattr(role, "agent_activated")


def test_subject_role_does_not_imply_task_execution() -> None:
    """DelegatedSubjectRef does not execute task/action/output."""
    subj = build_delegated_subject_ref(
        delegation_ref_id="ref:00001111",
        subject_ref="subject:task",
        subject_kind=DelegationSubjectKind.TASK,
    )
    assert "executed" not in subj.to_canonical_dict()
    assert not hasattr(subj, "subject_executed")


def test_role_binding_does_not_imply_approval() -> None:
    """DelegationRoleBinding does not imply approval granted."""
    binding = build_delegation_role_binding(
        delegation_ref_id="ref:00001111",
        delegation_identity_hash="a" * 64,
        role_kind=DelegationRoleKind.DELEGATOR,
        role_ref_hash="b" * 64,
    )
    assert "approval" not in binding.to_canonical_dict()


def test_role_binding_does_not_imply_permission_grant() -> None:
    """DelegationRoleBindingSet does not imply permission grant."""
    ref = _dev_fixture_p1_8_1_ref()
    identity = _dev_fixture_p1_8_1_identity()
    binding_set = build_delegation_role_binding_set(
        delegator=build_delegation_party_role_ref(
            delegation_ref_id=ref.delegation_ref_id,
            actor_ref="actor:op",
            role_kind=DelegationRoleKind.DELEGATOR,
        ),
        delegate=build_delegation_party_role_ref(
            delegation_ref_id=ref.delegation_ref_id,
            actor_ref="actor:ag",
            role_kind=DelegationRoleKind.DELEGATE,
        ),
        subject=build_delegated_subject_ref(
            delegation_ref_id=ref.delegation_ref_id,
            subject_ref="subject:ac",
            subject_kind=DelegationSubjectKind.ACTION,
        ),
        delegation_ref_id=ref.delegation_ref_id,
        delegation_identity_hash=identity.identity_hash,
    )
    assert "permission" not in binding_set.to_canonical_dict()


def test_role_binding_does_not_imply_enforcement() -> None:
    """DelegationRoleBindingSet does not imply enforcement."""
    ref = _dev_fixture_p1_8_1_ref()
    identity = _dev_fixture_p1_8_1_identity()
    binding_set = build_delegation_role_binding_set(
        delegator=build_delegation_party_role_ref(
            delegation_ref_id=ref.delegation_ref_id,
            actor_ref="actor:op",
            role_kind=DelegationRoleKind.DELEGATOR,
        ),
        delegate=build_delegation_party_role_ref(
            delegation_ref_id=ref.delegation_ref_id,
            actor_ref="actor:ag",
            role_kind=DelegationRoleKind.DELEGATE,
        ),
        subject=build_delegated_subject_ref(
            delegation_ref_id=ref.delegation_ref_id,
            subject_ref="subject:ac",
            subject_kind=DelegationSubjectKind.ACTION,
        ),
        delegation_ref_id=ref.delegation_ref_id,
        delegation_identity_hash=identity.identity_hash,
    )
    assert binding_set.side_effects.delegation_enforced is False


def test_role_binding_hash_not_trace_verified() -> None:
    """role_binding_hash is labeled DEV_FIXTURE, not TRACE_VERIFIED."""
    ref = _dev_fixture_p1_8_1_ref()
    identity = _dev_fixture_p1_8_1_identity()
    binding_set = build_delegation_role_binding_set(
        delegator=build_delegation_party_role_ref(
            delegation_ref_id=ref.delegation_ref_id,
            actor_ref="actor:op",
            role_kind=DelegationRoleKind.DELEGATOR,
        ),
        delegate=build_delegation_party_role_ref(
            delegation_ref_id=ref.delegation_ref_id,
            actor_ref="actor:ag",
            role_kind=DelegationRoleKind.DELEGATE,
        ),
        subject=build_delegated_subject_ref(
            delegation_ref_id=ref.delegation_ref_id,
            subject_ref="subject:ac",
            subject_kind=DelegationSubjectKind.ACTION,
        ),
        delegation_ref_id=ref.delegation_ref_id,
        delegation_identity_hash=identity.identity_hash,
    )
    assert binding_set.source_label is not DelegationSourceLabel.TRACE_VERIFIED
    # role_binding_hash exists but is not labeled TRACE_VERIFIED
    assert binding_set.role_binding_hash != ""
    assert DelegationSourceLabel.TRACE_VERIFIED.value not in str(binding_set.source_label.value)


# -----------------------------------------------------------------------
# Test 29: Invalid enum/value input fails closed
# -----------------------------------------------------------------------


def test_invalid_role_kind_rejected() -> None:
    with pytest.raises((ValueError, DelegationValidationError)):
        build_delegation_party_role_ref(
            delegation_ref_id="ref:X",
            actor_ref="actor:op",
            role_kind="INVALID_ROLE",
        )


def test_party_role_ref_rejects_non_delegator_delegate_kind() -> None:
    with pytest.raises((ValueError, DelegationValidationError)):
        DelegationPartyRoleRef(
            delegation_ref_id="ref:X",
            actor_ref="actor:op",
            role_kind=DelegationRoleKind.SUBJECT,
        )


def test_invalid_source_label_rejected() -> None:
    with pytest.raises((ValueError, DelegationValidationError)):
        build_delegation_party_role_ref(
            delegation_ref_id="ref:X",
            actor_ref="actor:op",
            role_kind=DelegationRoleKind.DELEGATOR,
            source_label="NOT_A_LABEL",
        )


def test_invalid_binding_status_rejected() -> None:
    with pytest.raises((ValueError, DelegationValidationError)):
        build_delegation_role_binding(
            delegation_ref_id="ref:X",
            delegation_identity_hash="a" * 64,
            role_kind=DelegationRoleKind.DELEGATOR,
            role_ref_hash="b" * 64,
            binding_status="NOT_A_STATUS",
        )


# -----------------------------------------------------------------------
# Test 30: No field implies policy/Custos/approval/Ledger/runtime/non-repudiation
# -----------------------------------------------------------------------


def test_no_policy_custos_approval_ledger_trace_runtime() -> None:
    ref = _dev_fixture_p1_8_1_ref()
    identity = _dev_fixture_p1_8_1_identity()
    binding_set = build_delegation_role_binding_set(
        delegator=build_delegation_party_role_ref(
            delegation_ref_id=ref.delegation_ref_id,
            actor_ref="actor:op",
            role_kind=DelegationRoleKind.DELEGATOR,
        ),
        delegate=build_delegation_party_role_ref(
            delegation_ref_id=ref.delegation_ref_id,
            actor_ref="actor:ag",
            role_kind=DelegationRoleKind.DELEGATE,
        ),
        subject=build_delegated_subject_ref(
            delegation_ref_id=ref.delegation_ref_id,
            subject_ref="subject:ac",
            subject_kind=DelegationSubjectKind.ACTION,
        ),
        delegation_ref_id=ref.delegation_ref_id,
        delegation_identity_hash=identity.identity_hash,
    )
    se = binding_set.side_effects
    assert se.policy_called is False
    assert se.custos_called is False
    assert se.approval_created is False
    assert se.ledger_written is False
    assert se.global_trace_written is False
    assert se.runtime_mutated is False
    assert se.delegation_executed is False
    assert se.delegate_activated is False
    assert se.subject_executed is False
    assert se.authority_verified is False

    # Serialized form must not contain any true side effect
    serialized = serialize_delegation_role_binding_set(binding_set)
    assert '"true"' not in serialized.lower() or "side_effects" not in serialized.lower()

    parsed = json.loads(serialized)
    side_effects = parsed.get("side_effects", {})
    for key, value in side_effects.items():
        assert value is False, f"Side effect {key} is {value}, expected False"


# -----------------------------------------------------------------------
# Test 31: Existing P1.8.0/P1.8.1 exports remain importable
# -----------------------------------------------------------------------


def test_existing_exports_remain_importable() -> None:
    from agentic_runtime.delegation import (
        build_delegation_actor_ref,
        build_delegation_record,
        build_delegation_ref,
        build_delegation_identity,
        build_delegation_ref_binding,
        hash_delegation_record,
        hash_delegation_ref,
        hash_delegation_identity,
        DelegationRecord,
        DelegationRef,
        DelegationIdentity,
        DelegationRefBinding,
        DelegationIdentityKind,
        DelegationIdentityStatus,
        DelegationRefBindingKind,
        DelegationIdentitySideEffects,
        DelegationIdentityStatusReport,
        DelegationSideEffects,
        DelegationSourceLabel,
        DelegationActorKind,
        DelegationSubjectKind,
    )
    # Verify we can still construct P1.8.0 records
    record = _dev_fixture_record()
    assert isinstance(record, DelegationRecord)
    assert record.record_hash != ""

    # Verify we can still construct P1.8.1 refs
    ref = build_delegation_ref(
        delegation_id=record.delegation_id,
        record_hash=record.record_hash,
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    assert isinstance(ref, DelegationRef)
    assert ref.ref_hash != ""
