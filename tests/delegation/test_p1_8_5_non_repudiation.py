"""P1.8.5 — Non-RepudiationRef Binding / Evidence Hook tests."""
from __future__ import annotations

import json
from dataclasses import fields

import pytest

from agentic_runtime.delegation import (
    DelegationAuthorityBindingSet,
    DelegationAuthorityRefKind,
    DelegationAuthorityRefStatus,
    DelegationConstraintKind,
    DelegationConstraintSeverity,
    DelegationDisputeReadinessStatus,
    DelegationEvidenceCompletenessProfile,
    DelegationEvidenceEnvelope,
    DelegationEvidenceKind,
    DelegationEvidenceRef,
    DelegationEvidenceStatus,
    DelegationNonRepudiationBinding,
    DelegationNonRepudiationBindingSet,
    DelegationNonRepudiationClaimRef,
    DelegationNonRepudiationSideEffects,
    DelegationNonRepudiationStatusReport,
    DelegationProofReferenceStatus,
    DelegationRoleKind,
    DelegationSourceLabel,
    DelegationSubjectKind,
    build_delegated_subject_ref,
    build_delegation_authority_binding,
    build_delegation_authority_binding_set,
    build_delegation_authority_ref,
    build_delegation_constraint_binding,
    build_delegation_constraint_ref,
    build_delegation_constraint_set,
    build_delegation_evidence_completeness_profile,
    build_delegation_evidence_envelope,
    build_delegation_evidence_ref,
    build_delegation_identity,
    build_delegation_non_repudiation_binding,
    build_delegation_non_repudiation_binding_set,
    build_delegation_non_repudiation_claim_ref,
    build_delegation_non_repudiation_status_report,
    build_delegation_party_role_ref,
    build_delegation_ref,
    build_delegation_role_binding_set,
    hash_delegation_evidence_completeness_profile,
    hash_delegation_evidence_envelope,
    hash_delegation_evidence_ref,
    hash_delegation_non_repudiation_binding_set,
    hash_delegation_non_repudiation_claim_ref,
    serialize_delegation_evidence_envelope,
    serialize_delegation_non_repudiation_binding_set,
)
from agentic_runtime.delegation.non_repudiation import (
    DelegationValidationError,
    DelegationUnknownFieldError,
)
from agentic_runtime.delegation.foundation import (
    DelegationActorKind,
    DelegationAuthorityKind,
    build_agent_identity_mesh_ref,
    build_delegation_actor_ref,
    build_delegation_authority_ref as build_foundation_authority_ref,
    build_delegation_constraint,
    build_delegation_record,
    build_delegation_subject,
    build_non_repudiation_ref,
)

DEV_FIXTURE_CREATED_AT = "2026-06-27T00:00:00Z"


# -----------------------------------------------------------------------
# DEV_FIXTURE builder chain: P1.8.0 → P1.8.1 → P1.8.2 → P1.8.3 → P1.8.4 → P1.8.5
# -----------------------------------------------------------------------


def _dev_fixture_record(created_at: str = DEV_FIXTURE_CREATED_AT):
    """P1.8.0 DEV_FIXTURE DelegationRecord."""
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
    authority_ref = build_foundation_authority_ref(
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


def _dev_fixture_ref():
    """P1.8.1 DEV_FIXTURE DelegationRef."""
    record = _dev_fixture_record()
    return build_delegation_ref(
        delegation_id=record.delegation_id,
        record_hash=record.record_hash,
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )


def _dev_fixture_identity():
    """P1.8.1 DEV_FIXTURE DelegationIdentity."""
    ref = _dev_fixture_ref()
    record = _dev_fixture_record()
    return build_delegation_identity(
        delegation_ref=ref.delegation_ref_id,
        subject_ref=record.subject.subject_id,
        record_hash=record.record_hash,
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )


def _dev_fixture_role_binding_set():
    """P1.8.2 DEV_FIXTURE DelegationRoleBindingSet."""
    ref = _dev_fixture_ref()
    identity = _dev_fixture_identity()
    delegator = build_delegation_party_role_ref(
        delegation_ref_id=ref.delegation_ref_id,
        actor_ref="actor:0000000000000000",
        role_kind=DelegationRoleKind.DELEGATOR,
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    delegate = build_delegation_party_role_ref(
        delegation_ref_id=ref.delegation_ref_id,
        actor_ref="actor:1111111111111111",
        role_kind=DelegationRoleKind.DELEGATE,
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    subject = build_delegated_subject_ref(
        delegation_ref_id=ref.delegation_ref_id,
        subject_ref="subj:aaaaaaaaaaaaaaaa",
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


def _dev_fixture_constraint_set():
    """P1.8.3 DEV_FIXTURE DelegationConstraintSet."""
    ref = _dev_fixture_ref()
    identity = _dev_fixture_identity()
    roles = _dev_fixture_role_binding_set()
    cr = build_delegation_constraint_ref(
        delegation_ref_id=ref.delegation_ref_id,
        constraint_kind=DelegationConstraintKind.SCOPE_BOUND,
        constraint_value="DEV_FIXTURE scope",
        constraint_severity=DelegationConstraintSeverity.MEDIUM,
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    cb = build_delegation_constraint_binding(
        delegation_ref_id=ref.delegation_ref_id,
        delegation_identity_hash=identity.identity_hash,
        role_binding_hash=roles.role_binding_hash,
        constraint_ref_id=cr.constraint_ref_id,
        constraint_hash=cr.constraint_hash,
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    return build_delegation_constraint_set(
        delegation_ref_id=ref.delegation_ref_id,
        delegation_identity_hash=identity.identity_hash,
        role_binding_hash=roles.role_binding_hash,
        constraints=[cr],
        bindings=[cb],
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )


def _dev_fixture_authority_binding_set():
    """P1.8.4 DEV_FIXTURE DelegationAuthorityBindingSet."""
    ref = _dev_fixture_ref()
    identity = _dev_fixture_identity()
    roles = _dev_fixture_role_binding_set()
    constraints = _dev_fixture_constraint_set()
    ar = build_delegation_authority_ref(
        delegation_ref_id=ref.delegation_ref_id,
        authority_kind=DelegationAuthorityRefKind.OPERATOR_DECLARED,
        authority_basis="DEV_FIXTURE operator-declared authority",
        policy_context_ref="policy_ctx:fixture",
        path_authority_ref="path_auth:fixture",
        constraint_context_ref="cons_ctx:fixture",
        source_label=DelegationSourceLabel.DEV_FIXTURE,
        authority_status=DelegationAuthorityRefStatus.REFERENCE_ONLY,
    )
    ab = build_delegation_authority_binding(
        delegation_ref_id=ref.delegation_ref_id,
        delegation_identity_hash=identity.identity_hash,
        role_binding_hash=roles.role_binding_hash,
        constraint_set_hash=constraints.constraint_set_hash,
        authority_ref_id=ar.authority_ref_id,
        authority_ref_hash=ar.authority_ref_hash,
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    return build_delegation_authority_binding_set(
        delegation_ref_id=ref.delegation_ref_id,
        delegation_identity_hash=identity.identity_hash,
        role_binding_hash=roles.role_binding_hash,
        constraint_set_hash=constraints.constraint_set_hash,
        authority_refs=[ar],
        bindings=[ab],
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )


# -----------------------------------------------------------------------
# Test 1: Imports work
# -----------------------------------------------------------------------


def test_p185_imports_all_exist():
    """All P1.8.5 symbols importable from agentic_runtime.delegation."""
    assert DelegationEvidenceKind is not None
    assert DelegationEvidenceStatus is not None
    assert DelegationProofReferenceStatus is not None
    assert DelegationDisputeReadinessStatus is not None
    assert DelegationEvidenceRef is not None
    assert DelegationNonRepudiationClaimRef is not None
    assert DelegationEvidenceEnvelope is not None
    assert DelegationEvidenceCompletenessProfile is not None
    assert DelegationNonRepudiationBinding is not None
    assert DelegationNonRepudiationBindingSet is not None
    assert DelegationNonRepudiationSideEffects is not None
    assert DelegationNonRepudiationStatusReport is not None
    assert build_delegation_evidence_ref is not None
    assert build_delegation_non_repudiation_claim_ref is not None
    assert build_delegation_evidence_envelope is not None
    assert build_delegation_evidence_completeness_profile is not None
    assert build_delegation_non_repudiation_binding is not None
    assert build_delegation_non_repudiation_binding_set is not None
    assert build_delegation_non_repudiation_status_report is not None
    assert serialize_delegation_evidence_envelope is not None
    assert serialize_delegation_non_repudiation_binding_set is not None
    assert hash_delegation_evidence_ref is not None
    assert hash_delegation_non_repudiation_claim_ref is not None
    assert hash_delegation_evidence_envelope is not None
    assert hash_delegation_evidence_completeness_profile is not None
    assert hash_delegation_non_repudiation_binding_set is not None


def test_p185_existing_p180_exports_remain():
    """P1.8.0 exports still importable."""
    from agentic_runtime.delegation import (
        DelegationRecord,
        DelegationActorKind,
        build_delegation_record,
    )
    assert DelegationRecord is not None
    assert DelegationActorKind is not None
    assert build_delegation_record is not None


def test_p185_existing_p181_exports_remain():
    """P1.8.1 exports still importable."""
    from agentic_runtime.delegation import (
        DelegationRef,
        DelegationIdentity,
        build_delegation_ref,
    )
    assert DelegationRef is not None
    assert DelegationIdentity is not None
    assert build_delegation_ref is not None


def test_p185_existing_p182_exports_remain():
    """P1.8.2 exports still importable."""
    from agentic_runtime.delegation import (
        DelegationRoleBindingSet,
        DelegationPartyRoleRef,
    )
    assert DelegationRoleBindingSet is not None
    assert DelegationPartyRoleRef is not None


def test_p185_existing_p183_exports_remain():
    """P1.8.3 exports still importable."""
    from agentic_runtime.delegation import (
        DelegationConstraintSet,
        DelegationConstraintRef,
    )
    assert DelegationConstraintSet is not None
    assert DelegationConstraintRef is not None


def test_p185_existing_p184_exports_remain():
    """P1.8.4 exports still importable."""
    from agentic_runtime.delegation import (
        DelegationAuthorityBindingSet,
        DelegationAuthorityRef,
    )
    assert DelegationAuthorityBindingSet is not None
    assert DelegationAuthorityRef is not None


# -----------------------------------------------------------------------
# Test: P1.8.4 authority binding set feeds P1.8.5 evidence path
# -----------------------------------------------------------------------


def test_p185_p184_authority_binding_set_feeds_evidence():
    """P1.8.4 DEV_FIXTURE DelegationAuthorityBindingSet can feed P1.8.5
       evidence/non-repudiation chain."""
    auth_set = _dev_fixture_authority_binding_set()
    ref = _dev_fixture_ref()
    identity = _dev_fixture_identity()
    roles = _dev_fixture_role_binding_set()
    constraints = _dev_fixture_constraint_set()

    evidence_ref = build_delegation_evidence_ref(
        delegation_ref_id=ref.delegation_ref_id,
        evidence_kind=DelegationEvidenceKind.DOCUMENT_REF,
        evidence_description="DEV_FIXTURE evidence document",
        evidence_uri_ref="file:///dev/fixture/evidence.log",
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    assert evidence_ref is not None
    assert evidence_ref.source_label == DelegationSourceLabel.DEV_FIXTURE
    assert evidence_ref.evidence_ref_hash != ""

    envelope = build_delegation_evidence_envelope(
        delegation_ref_id=ref.delegation_ref_id,
        delegation_identity_hash=identity.identity_hash,
        role_binding_hash=roles.role_binding_hash,
        constraint_set_hash=constraints.constraint_set_hash,
        authority_binding_set_hash=auth_set.authority_binding_set_hash,
        evidence_refs=[evidence_ref],
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    assert envelope is not None
    assert envelope.authority_binding_set_hash == auth_set.authority_binding_set_hash


# -----------------------------------------------------------------------
# Test: DelegationEvidenceRef builds deterministically
# -----------------------------------------------------------------------


def test_p185_evidence_ref_builds_deterministically():
    """DelegationEvidenceRef builds deterministically."""
    ref = _dev_fixture_ref()
    er1 = build_delegation_evidence_ref(
        delegation_ref_id=ref.delegation_ref_id,
        evidence_kind=DelegationEvidenceKind.DOCUMENT_REF,
        evidence_description="DEV_FIXTURE evidence document",
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    er2 = build_delegation_evidence_ref(
        delegation_ref_id=ref.delegation_ref_id,
        evidence_kind=DelegationEvidenceKind.DOCUMENT_REF,
        evidence_description="DEV_FIXTURE evidence document",
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    assert er1.evidence_ref_hash == er2.evidence_ref_hash
    assert er1.evidence_ref_id == er2.evidence_ref_id


# -----------------------------------------------------------------------
# Test: DelegationNonRepudiationClaimRef builds deterministically
# -----------------------------------------------------------------------


def test_p185_claim_ref_builds_deterministically():
    """DelegationNonRepudiationClaimRef builds deterministically."""
    ref = _dev_fixture_ref()
    cr1 = build_delegation_non_repudiation_claim_ref(
        delegation_ref_id=ref.delegation_ref_id,
        claim_subject_ref="subj:claim_fixture",
        claim_statement="DEV_FIXTURE claim: delegation occurred as recorded",
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    cr2 = build_delegation_non_repudiation_claim_ref(
        delegation_ref_id=ref.delegation_ref_id,
        claim_subject_ref="subj:claim_fixture",
        claim_statement="DEV_FIXTURE claim: delegation occurred as recorded",
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    assert cr1.claim_ref_hash == cr2.claim_ref_hash
    assert cr1.claim_ref_id == cr2.claim_ref_id


# -----------------------------------------------------------------------
# Test: DelegationEvidenceEnvelope builds deterministically
# -----------------------------------------------------------------------


def test_p185_evidence_envelope_builds_deterministically():
    """DelegationEvidenceEnvelope builds deterministically."""
    ref = _dev_fixture_ref()
    identity = _dev_fixture_identity()
    roles = _dev_fixture_role_binding_set()
    constraints = _dev_fixture_constraint_set()
    auth_set = _dev_fixture_authority_binding_set()

    def _build_envelope():
        return build_delegation_evidence_envelope(
            delegation_ref_id=ref.delegation_ref_id,
            delegation_identity_hash=identity.identity_hash,
            role_binding_hash=roles.role_binding_hash,
            constraint_set_hash=constraints.constraint_set_hash,
            authority_binding_set_hash=auth_set.authority_binding_set_hash,
            source_label=DelegationSourceLabel.DEV_FIXTURE,
        )

    e1 = _build_envelope()
    e2 = _build_envelope()
    assert e1.evidence_envelope_hash == e2.evidence_envelope_hash
    assert e1.evidence_envelope_id == e2.evidence_envelope_id


# -----------------------------------------------------------------------
# Test: DelegationEvidenceCompletenessProfile builds deterministically
# -----------------------------------------------------------------------


def test_p185_completeness_profile_builds_deterministically():
    """DelegationEvidenceCompletenessProfile builds deterministically."""
    ref = _dev_fixture_ref()
    envelope = build_delegation_evidence_envelope(
        delegation_ref_id=ref.delegation_ref_id,
        delegation_identity_hash=_dev_fixture_identity().identity_hash,
        role_binding_hash=_dev_fixture_role_binding_set().role_binding_hash,
        constraint_set_hash=_dev_fixture_constraint_set().constraint_set_hash,
        authority_binding_set_hash=_dev_fixture_authority_binding_set().authority_binding_set_hash,
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )

    p1 = build_delegation_evidence_completeness_profile(
        delegation_ref_id=ref.delegation_ref_id,
        evidence_envelope_hash=envelope.evidence_envelope_hash,
        has_delegation_identity=True,
        has_role_binding=True,
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    p2 = build_delegation_evidence_completeness_profile(
        delegation_ref_id=ref.delegation_ref_id,
        evidence_envelope_hash=envelope.evidence_envelope_hash,
        has_delegation_identity=True,
        has_role_binding=True,
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    assert p1.profile_hash == p2.profile_hash
    assert p1.profile_id == p2.profile_id


# -----------------------------------------------------------------------
# Test: DelegationNonRepudiationBinding builds deterministically
# -----------------------------------------------------------------------


def test_p185_non_repudiation_binding_builds_deterministically():
    """DelegationNonRepudiationBinding builds deterministically."""
    ref = _dev_fixture_ref()
    identity = _dev_fixture_identity()
    roles = _dev_fixture_role_binding_set()
    constraints = _dev_fixture_constraint_set()
    auth_set = _dev_fixture_authority_binding_set()
    envelope = build_delegation_evidence_envelope(
        delegation_ref_id=ref.delegation_ref_id,
        delegation_identity_hash=identity.identity_hash,
        role_binding_hash=roles.role_binding_hash,
        constraint_set_hash=constraints.constraint_set_hash,
        authority_binding_set_hash=auth_set.authority_binding_set_hash,
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    profile = build_delegation_evidence_completeness_profile(
        delegation_ref_id=ref.delegation_ref_id,
        evidence_envelope_hash=envelope.evidence_envelope_hash,
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )

    b1 = build_delegation_non_repudiation_binding(
        delegation_ref_id=ref.delegation_ref_id,
        delegation_identity_hash=identity.identity_hash,
        role_binding_hash=roles.role_binding_hash,
        constraint_set_hash=constraints.constraint_set_hash,
        authority_binding_set_hash=auth_set.authority_binding_set_hash,
        evidence_envelope_hash=envelope.evidence_envelope_hash,
        completeness_profile_hash=profile.profile_hash,
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    b2 = build_delegation_non_repudiation_binding(
        delegation_ref_id=ref.delegation_ref_id,
        delegation_identity_hash=identity.identity_hash,
        role_binding_hash=roles.role_binding_hash,
        constraint_set_hash=constraints.constraint_set_hash,
        authority_binding_set_hash=auth_set.authority_binding_set_hash,
        evidence_envelope_hash=envelope.evidence_envelope_hash,
        completeness_profile_hash=profile.profile_hash,
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    assert b1.binding_hash == b2.binding_hash
    assert b1.binding_id == b2.binding_id


# -----------------------------------------------------------------------
# Test: DelegationNonRepudiationBindingSet builds deterministically
# -----------------------------------------------------------------------


def test_p185_non_repudiation_binding_set_builds_deterministically():
    """DelegationNonRepudiationBindingSet builds deterministically."""
    ref = _dev_fixture_ref()
    identity = _dev_fixture_identity()
    roles = _dev_fixture_role_binding_set()
    constraints = _dev_fixture_constraint_set()
    auth_set = _dev_fixture_authority_binding_set()
    envelope = build_delegation_evidence_envelope(
        delegation_ref_id=ref.delegation_ref_id,
        delegation_identity_hash=identity.identity_hash,
        role_binding_hash=roles.role_binding_hash,
        constraint_set_hash=constraints.constraint_set_hash,
        authority_binding_set_hash=auth_set.authority_binding_set_hash,
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    profile = build_delegation_evidence_completeness_profile(
        delegation_ref_id=ref.delegation_ref_id,
        evidence_envelope_hash=envelope.evidence_envelope_hash,
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    binding = build_delegation_non_repudiation_binding(
        delegation_ref_id=ref.delegation_ref_id,
        delegation_identity_hash=identity.identity_hash,
        role_binding_hash=roles.role_binding_hash,
        constraint_set_hash=constraints.constraint_set_hash,
        authority_binding_set_hash=auth_set.authority_binding_set_hash,
        evidence_envelope_hash=envelope.evidence_envelope_hash,
        completeness_profile_hash=profile.profile_hash,
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )

    bs1 = build_delegation_non_repudiation_binding_set(
        delegation_ref_id=ref.delegation_ref_id,
        delegation_identity_hash=identity.identity_hash,
        role_binding_hash=roles.role_binding_hash,
        constraint_set_hash=constraints.constraint_set_hash,
        authority_binding_set_hash=auth_set.authority_binding_set_hash,
        bindings=[binding],
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    bs2 = build_delegation_non_repudiation_binding_set(
        delegation_ref_id=ref.delegation_ref_id,
        delegation_identity_hash=identity.identity_hash,
        role_binding_hash=roles.role_binding_hash,
        constraint_set_hash=constraints.constraint_set_hash,
        authority_binding_set_hash=auth_set.authority_binding_set_hash,
        bindings=[binding],
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    assert bs1.non_repudiation_binding_set_hash == bs2.non_repudiation_binding_set_hash
    assert bs1.non_repudiation_binding_set_id == bs2.non_repudiation_binding_set_id


# -----------------------------------------------------------------------
# Test: DelegationNonRepudiationStatusReport builds deterministically
# -----------------------------------------------------------------------


def test_p185_status_report_builds_deterministically():
    """DelegationNonRepudiationStatusReport builds deterministically."""
    sr1 = build_delegation_non_repudiation_status_report()
    sr2 = build_delegation_non_repudiation_status_report()
    assert sr1.status_hash == sr2.status_hash


# -----------------------------------------------------------------------
# Test: Identical evidence input gives identical hash
# -----------------------------------------------------------------------


def test_p185_identical_evidence_gives_same_hash():
    """Identical evidence input gives identical evidence_ref_hash."""
    ref = _dev_fixture_ref()
    er1 = build_delegation_evidence_ref(
        delegation_ref_id=ref.delegation_ref_id,
        evidence_kind=DelegationEvidenceKind.ARTIFACT_REF,
        evidence_description="DEV_FIXTURE artifact",
        evidence_uri_ref="https://fixture.example/artifact",
        evidence_hash_ref="sha256:abcdef1234567890",
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    er2 = build_delegation_evidence_ref(
        delegation_ref_id=ref.delegation_ref_id,
        evidence_kind=DelegationEvidenceKind.ARTIFACT_REF,
        evidence_description="DEV_FIXTURE artifact",
        evidence_uri_ref="https://fixture.example/artifact",
        evidence_hash_ref="sha256:abcdef1234567890",
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    assert er1.evidence_ref_hash == er2.evidence_ref_hash
    assert hash_delegation_evidence_ref(er1) == hash_delegation_evidence_ref(er2)


# -----------------------------------------------------------------------
# Test: Changed evidence kind/ref/description changes hash
# -----------------------------------------------------------------------


def test_p185_changed_evidence_kind_changes_hash():
    """Changed evidence kind changes evidence_ref_hash."""
    ref = _dev_fixture_ref()
    er1 = build_delegation_evidence_ref(
        delegation_ref_id=ref.delegation_ref_id,
        evidence_kind=DelegationEvidenceKind.DOCUMENT_REF,
        evidence_description="DEV_FIXTURE evidence",
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    er2 = build_delegation_evidence_ref(
        delegation_ref_id=ref.delegation_ref_id,
        evidence_kind=DelegationEvidenceKind.ARTIFACT_REF,
        evidence_description="DEV_FIXTURE evidence",
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    assert er1.evidence_ref_hash != er2.evidence_ref_hash


def test_p185_changed_evidence_description_changes_hash():
    """Changed evidence description changes evidence_ref_hash."""
    ref = _dev_fixture_ref()
    er1 = build_delegation_evidence_ref(
        delegation_ref_id=ref.delegation_ref_id,
        evidence_kind=DelegationEvidenceKind.DOCUMENT_REF,
        evidence_description="DEV_FIXTURE evidence A",
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    er2 = build_delegation_evidence_ref(
        delegation_ref_id=ref.delegation_ref_id,
        evidence_kind=DelegationEvidenceKind.DOCUMENT_REF,
        evidence_description="DEV_FIXTURE evidence B",
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    assert er1.evidence_ref_hash != er2.evidence_ref_hash


# -----------------------------------------------------------------------
# Test: Changed claim content/context changes hash
# -----------------------------------------------------------------------


def test_p185_changed_claim_statement_changes_hash():
    """Changed claim statement changes claim_ref_hash."""
    ref = _dev_fixture_ref()
    cr1 = build_delegation_non_repudiation_claim_ref(
        delegation_ref_id=ref.delegation_ref_id,
        claim_subject_ref="subj:claim_fixture",
        claim_statement="DEV_FIXTURE claim: delegation occurred as recorded v1",
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    cr2 = build_delegation_non_repudiation_claim_ref(
        delegation_ref_id=ref.delegation_ref_id,
        claim_subject_ref="subj:claim_fixture",
        claim_statement="DEV_FIXTURE claim: delegation occurred as recorded v2",
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    assert cr1.claim_ref_hash != cr2.claim_ref_hash


def test_p185_changed_claim_context_changes_hash():
    """Changed claim context ref changes claim_ref_hash."""
    ref = _dev_fixture_ref()
    cr1 = build_delegation_non_repudiation_claim_ref(
        delegation_ref_id=ref.delegation_ref_id,
        claim_subject_ref="subj:claim_fixture",
        claim_statement="DEV_FIXTURE claim",
        claim_context_ref="ctx:alpha",
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    cr2 = build_delegation_non_repudiation_claim_ref(
        delegation_ref_id=ref.delegation_ref_id,
        claim_subject_ref="subj:claim_fixture",
        claim_statement="DEV_FIXTURE claim",
        claim_context_ref="ctx:beta",
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    assert cr1.claim_ref_hash != cr2.claim_ref_hash


# -----------------------------------------------------------------------
# Test: Identical evidence envelope gives identical hash
# -----------------------------------------------------------------------


def test_p185_identical_envelope_gives_same_hash():
    """Identical evidence envelope gives identical evidence_envelope_hash."""
    ref = _dev_fixture_ref()
    identity = _dev_fixture_identity()
    roles = _dev_fixture_role_binding_set()
    constraints = _dev_fixture_constraint_set()
    auth_set = _dev_fixture_authority_binding_set()
    er = build_delegation_evidence_ref(
        delegation_ref_id=ref.delegation_ref_id,
        evidence_kind=DelegationEvidenceKind.DOCUMENT_REF,
        evidence_description="DEV_FIXTURE evidence",
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )

    e1 = build_delegation_evidence_envelope(
        delegation_ref_id=ref.delegation_ref_id,
        delegation_identity_hash=identity.identity_hash,
        role_binding_hash=roles.role_binding_hash,
        constraint_set_hash=constraints.constraint_set_hash,
        authority_binding_set_hash=auth_set.authority_binding_set_hash,
        evidence_refs=[er],
        attestation_refs=["attest:fixture"],
        signature_refs=["sig:fixture"],
        trace_refs=["trace:fixture"],
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    e2 = build_delegation_evidence_envelope(
        delegation_ref_id=ref.delegation_ref_id,
        delegation_identity_hash=identity.identity_hash,
        role_binding_hash=roles.role_binding_hash,
        constraint_set_hash=constraints.constraint_set_hash,
        authority_binding_set_hash=auth_set.authority_binding_set_hash,
        evidence_refs=[er],
        attestation_refs=["attest:fixture"],
        signature_refs=["sig:fixture"],
        trace_refs=["trace:fixture"],
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    assert e1.evidence_envelope_hash == e2.evidence_envelope_hash


# -----------------------------------------------------------------------
# Test: Changed evidence envelope membership changes hash
# -----------------------------------------------------------------------


def test_p185_changed_envelope_evidence_changes_hash():
    """Changed evidence refs member changes evidence_envelope_hash."""
    ref = _dev_fixture_ref()
    identity = _dev_fixture_identity()
    roles = _dev_fixture_role_binding_set()
    constraints = _dev_fixture_constraint_set()
    auth_set = _dev_fixture_authority_binding_set()
    er1 = build_delegation_evidence_ref(
        delegation_ref_id=ref.delegation_ref_id,
        evidence_kind=DelegationEvidenceKind.DOCUMENT_REF,
        evidence_description="DEV_FIXTURE evidence A",
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    er2 = build_delegation_evidence_ref(
        delegation_ref_id=ref.delegation_ref_id,
        evidence_kind=DelegationEvidenceKind.ARTIFACT_REF,
        evidence_description="DEV_FIXTURE evidence B",
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )

    e1 = build_delegation_evidence_envelope(
        delegation_ref_id=ref.delegation_ref_id,
        delegation_identity_hash=identity.identity_hash,
        role_binding_hash=roles.role_binding_hash,
        constraint_set_hash=constraints.constraint_set_hash,
        authority_binding_set_hash=auth_set.authority_binding_set_hash,
        evidence_refs=[er1],
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    e2 = build_delegation_evidence_envelope(
        delegation_ref_id=ref.delegation_ref_id,
        delegation_identity_hash=identity.identity_hash,
        role_binding_hash=roles.role_binding_hash,
        constraint_set_hash=constraints.constraint_set_hash,
        authority_binding_set_hash=auth_set.authority_binding_set_hash,
        evidence_refs=[er2],
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    assert e1.evidence_envelope_hash != e2.evidence_envelope_hash


# -----------------------------------------------------------------------
# Test: Evidence envelope ordering is deterministic
# -----------------------------------------------------------------------


def test_p185_envelope_ordering_is_deterministic():
    """Evidence refs in envelope are deterministically ordered."""
    ref = _dev_fixture_ref()
    identity = _dev_fixture_identity()
    roles = _dev_fixture_role_binding_set()
    constraints = _dev_fixture_constraint_set()
    auth_set = _dev_fixture_authority_binding_set()

    er_a = build_delegation_evidence_ref(
        delegation_ref_id=ref.delegation_ref_id,
        evidence_kind=DelegationEvidenceKind.DOCUMENT_REF,
        evidence_description="DEV_FIXTURE evidence A",
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    er_b = build_delegation_evidence_ref(
        delegation_ref_id=ref.delegation_ref_id,
        evidence_kind=DelegationEvidenceKind.ARTIFACT_REF,
        evidence_description="DEV_FIXTURE evidence B",
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )

    e1 = build_delegation_evidence_envelope(
        delegation_ref_id=ref.delegation_ref_id,
        delegation_identity_hash=identity.identity_hash,
        role_binding_hash=roles.role_binding_hash,
        constraint_set_hash=constraints.constraint_set_hash,
        authority_binding_set_hash=auth_set.authority_binding_set_hash,
        evidence_refs=[er_a, er_b],
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    e2 = build_delegation_evidence_envelope(
        delegation_ref_id=ref.delegation_ref_id,
        delegation_identity_hash=identity.identity_hash,
        role_binding_hash=roles.role_binding_hash,
        constraint_set_hash=constraints.constraint_set_hash,
        authority_binding_set_hash=auth_set.authority_binding_set_hash,
        evidence_refs=[er_b, er_a],
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    assert e1.evidence_envelope_hash == e2.evidence_envelope_hash


# -----------------------------------------------------------------------
# Test: Identical completeness profile gives identical hash
# -----------------------------------------------------------------------


def test_p185_identical_completeness_profile_gives_same_hash():
    """Identical completeness profile gives identical profile_hash."""
    ref = _dev_fixture_ref()
    identity = _dev_fixture_identity()
    roles = _dev_fixture_role_binding_set()
    constraints = _dev_fixture_constraint_set()
    auth_set = _dev_fixture_authority_binding_set()
    envelope = build_delegation_evidence_envelope(
        delegation_ref_id=ref.delegation_ref_id,
        delegation_identity_hash=identity.identity_hash,
        role_binding_hash=roles.role_binding_hash,
        constraint_set_hash=constraints.constraint_set_hash,
        authority_binding_set_hash=auth_set.authority_binding_set_hash,
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )

    p1 = build_delegation_evidence_completeness_profile(
        delegation_ref_id=ref.delegation_ref_id,
        evidence_envelope_hash=envelope.evidence_envelope_hash,
        has_delegation_identity=True,
        has_role_binding=True,
        has_constraints=True,
        missing_components=["Missing: Signature Refs", "Missing: Trace Refs"],
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    p2 = build_delegation_evidence_completeness_profile(
        delegation_ref_id=ref.delegation_ref_id,
        evidence_envelope_hash=envelope.evidence_envelope_hash,
        has_delegation_identity=True,
        has_role_binding=True,
        has_constraints=True,
        missing_components=["Missing: Signature Refs", "Missing: Trace Refs"],
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    assert p1.profile_hash == p2.profile_hash


# -----------------------------------------------------------------------
# Test: Completeness profile reports present/missing components
# -----------------------------------------------------------------------


def test_p185_completeness_profile_reports_present_components():
    """Completeness profile reports present components."""
    profile = build_delegation_evidence_completeness_profile(
        delegation_ref_id="ref:test",
        evidence_envelope_hash="hash:test",
        has_delegation_identity=True,
        has_role_binding=True,
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    assert profile.has_delegation_identity is True
    assert profile.has_role_binding is True
    assert profile.has_constraints is False


def test_p185_completeness_profile_reports_missing_components():
    """Completeness profile reports missing components."""
    profile = build_delegation_evidence_completeness_profile(
        delegation_ref_id="ref:test",
        evidence_envelope_hash="hash:test",
        has_delegation_identity=True,
        has_signature_refs=False,
        missing_components=["Missing: Signature Refs"],
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    assert "Missing: Signature Refs" in profile.missing_components


def test_p185_completeness_profile_missing_components_ordered():
    """Missing components are deterministically ordered."""
    p1 = build_delegation_evidence_completeness_profile(
        delegation_ref_id="ref:test",
        evidence_envelope_hash="hash:test",
        missing_components=["B", "A", "C"],
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    p2 = build_delegation_evidence_completeness_profile(
        delegation_ref_id="ref:test",
        evidence_envelope_hash="hash:test",
        missing_components=["C", "B", "A"],
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    assert p1.profile_hash == p2.profile_hash
    assert list(p1.missing_components) == ["A", "B", "C"]


# -----------------------------------------------------------------------
# Test: Identical non-repudiation binding set gives identical hash
# -----------------------------------------------------------------------


def test_p185_identical_binding_set_gives_same_hash():
    """Identical non-repudiation binding set gives identical hash."""
    ref = _dev_fixture_ref()
    identity = _dev_fixture_identity()
    roles = _dev_fixture_role_binding_set()
    constraints = _dev_fixture_constraint_set()
    auth_set = _dev_fixture_authority_binding_set()
    envelope = build_delegation_evidence_envelope(
        delegation_ref_id=ref.delegation_ref_id,
        delegation_identity_hash=identity.identity_hash,
        role_binding_hash=roles.role_binding_hash,
        constraint_set_hash=constraints.constraint_set_hash,
        authority_binding_set_hash=auth_set.authority_binding_set_hash,
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    profile = build_delegation_evidence_completeness_profile(
        delegation_ref_id=ref.delegation_ref_id,
        evidence_envelope_hash=envelope.evidence_envelope_hash,
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    binding = build_delegation_non_repudiation_binding(
        delegation_ref_id=ref.delegation_ref_id,
        delegation_identity_hash=identity.identity_hash,
        role_binding_hash=roles.role_binding_hash,
        constraint_set_hash=constraints.constraint_set_hash,
        authority_binding_set_hash=auth_set.authority_binding_set_hash,
        evidence_envelope_hash=envelope.evidence_envelope_hash,
        completeness_profile_hash=profile.profile_hash,
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )

    bs1 = build_delegation_non_repudiation_binding_set(
        delegation_ref_id=ref.delegation_ref_id,
        delegation_identity_hash=identity.identity_hash,
        role_binding_hash=roles.role_binding_hash,
        constraint_set_hash=constraints.constraint_set_hash,
        authority_binding_set_hash=auth_set.authority_binding_set_hash,
        bindings=[binding],
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    bs2 = build_delegation_non_repudiation_binding_set(
        delegation_ref_id=ref.delegation_ref_id,
        delegation_identity_hash=identity.identity_hash,
        role_binding_hash=roles.role_binding_hash,
        constraint_set_hash=constraints.constraint_set_hash,
        authority_binding_set_hash=auth_set.authority_binding_set_hash,
        bindings=[binding],
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    assert bs1.non_repudiation_binding_set_hash == bs2.non_repudiation_binding_set_hash


# -----------------------------------------------------------------------
# Test: Changed binding membership changes hash
# -----------------------------------------------------------------------


def test_p185_changed_binding_set_membership_changes_hash():
    """Changed binding membership changes non_repudiation_binding_set_hash."""
    ref = _dev_fixture_ref()
    identity = _dev_fixture_identity()
    roles = _dev_fixture_role_binding_set()
    constraints = _dev_fixture_constraint_set()
    auth_set = _dev_fixture_authority_binding_set()

    def _make_envelope():
        return build_delegation_evidence_envelope(
            delegation_ref_id=ref.delegation_ref_id,
            delegation_identity_hash=identity.identity_hash,
            role_binding_hash=roles.role_binding_hash,
            constraint_set_hash=constraints.constraint_set_hash,
            authority_binding_set_hash=auth_set.authority_binding_set_hash,
            source_label=DelegationSourceLabel.DEV_FIXTURE,
        )

    def _make_profile(env):
        return build_delegation_evidence_completeness_profile(
            delegation_ref_id=ref.delegation_ref_id,
            evidence_envelope_hash=env.evidence_envelope_hash,
            source_label=DelegationSourceLabel.DEV_FIXTURE,
        )

    env_a = _make_envelope()
    env_b = build_delegation_evidence_envelope(
        delegation_ref_id=ref.delegation_ref_id,
        delegation_identity_hash=identity.identity_hash,
        role_binding_hash=roles.role_binding_hash,
        constraint_set_hash=constraints.constraint_set_hash,
        authority_binding_set_hash=auth_set.authority_binding_set_hash,
        attestation_refs=["attest:changed"],
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    profile_a = _make_profile(env_a)
    profile_b = _make_profile(env_b)

    b_a = build_delegation_non_repudiation_binding(
        delegation_ref_id=ref.delegation_ref_id,
        delegation_identity_hash=identity.identity_hash,
        role_binding_hash=roles.role_binding_hash,
        constraint_set_hash=constraints.constraint_set_hash,
        authority_binding_set_hash=auth_set.authority_binding_set_hash,
        evidence_envelope_hash=env_a.evidence_envelope_hash,
        completeness_profile_hash=profile_a.profile_hash,
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    b_b = build_delegation_non_repudiation_binding(
        delegation_ref_id=ref.delegation_ref_id,
        delegation_identity_hash=identity.identity_hash,
        role_binding_hash=roles.role_binding_hash,
        constraint_set_hash=constraints.constraint_set_hash,
        authority_binding_set_hash=auth_set.authority_binding_set_hash,
        evidence_envelope_hash=env_b.evidence_envelope_hash,
        completeness_profile_hash=profile_b.profile_hash,
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )

    bs1 = build_delegation_non_repudiation_binding_set(
        delegation_ref_id=ref.delegation_ref_id,
        delegation_identity_hash=identity.identity_hash,
        role_binding_hash=roles.role_binding_hash,
        constraint_set_hash=constraints.constraint_set_hash,
        authority_binding_set_hash=auth_set.authority_binding_set_hash,
        bindings=[b_a],
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    bs2 = build_delegation_non_repudiation_binding_set(
        delegation_ref_id=ref.delegation_ref_id,
        delegation_identity_hash=identity.identity_hash,
        role_binding_hash=roles.role_binding_hash,
        constraint_set_hash=constraints.constraint_set_hash,
        authority_binding_set_hash=auth_set.authority_binding_set_hash,
        bindings=[b_b],
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    assert bs1.non_repudiation_binding_set_hash != bs2.non_repudiation_binding_set_hash


# -----------------------------------------------------------------------
# Test: ProofReferenceStatus ladder values
# -----------------------------------------------------------------------


def test_p185_proof_reference_status_ladder():
    """ProofReferenceStatus enum includes all required values."""
    values = [s.value for s in DelegationProofReferenceStatus]
    assert "REFERENCE_ONLY" in values
    assert "EVIDENCE_REFERENCED" in values
    assert "CLAIM_REFERENCED" in values
    assert "ATTESTATION_REFERENCED" in values
    assert "SIGNATURE_REFERENCED" in values
    assert "TRACE_REFERENCED" in values
    assert "VERIFIER_UNAVAILABLE" in values
    assert "UNAVAILABLE" in values
    assert "ERROR" in values
    assert "UNKNOWN" in values


# -----------------------------------------------------------------------
# Test: Boundary assertions — referenced ≠ verified
# -----------------------------------------------------------------------


def test_p185_trace_referenced_not_trace_verified():
    """TRACE_REFERENCED is not TRACE_VERIFIED."""
    assert DelegationProofReferenceStatus.TRACE_REFERENCED.value != "TRACE_VERIFIED"
    assert "TRACE_VERIFIED" not in [
        s.value for s in DelegationProofReferenceStatus
    ]


def test_p185_signature_referenced_not_signature_verified():
    """SIGNATURE_REFERENCED is not signature verified."""
    assert (
        DelegationProofReferenceStatus.SIGNATURE_REFERENCED.value
        != "SIGNATURE_VERIFIED"
    )


def test_p185_evidence_referenced_not_evidence_verified():
    """EVIDENCE_REFERENCED is not evidence verified."""
    assert (
        DelegationProofReferenceStatus.EVIDENCE_REFERENCED.value
        != "EVIDENCE_VERIFIED"
    )


def test_p185_claim_referenced_not_claim_proven():
    """CLAIM_REFERENCED is not claim proven."""
    assert (
        DelegationProofReferenceStatus.CLAIM_REFERENCED.value
        != "CLAIM_PROVEN"
    )


def test_p185_attestation_referenced_not_attestation_verified():
    """ATTESTATION_REFERENCED is not attestation verified."""
    assert (
        DelegationProofReferenceStatus.ATTESTATION_REFERENCED.value
        != "ATTESTATION_VERIFIED"
    )


# -----------------------------------------------------------------------
# Test: Serialization is JSON-safe and deterministic
# -----------------------------------------------------------------------


def test_p185_serialization_is_json_safe():
    """Serialization produces valid JSON."""
    ref = _dev_fixture_ref()
    evidence_ref = build_delegation_evidence_ref(
        delegation_ref_id=ref.delegation_ref_id,
        evidence_kind=DelegationEvidenceKind.DOCUMENT_REF,
        evidence_description="DEV_FIXTURE evidence",
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    raw = evidence_ref.to_canonical_dict()
    json_str = json.dumps(raw, sort_keys=True)
    parsed = json.loads(json_str)
    assert parsed["evidence_kind"] == "DOCUMENT_REF"
    assert parsed["source_label"] == "DEV_FIXTURE"


def test_p185_envelope_serialization_is_deterministic():
    """Envelope serialization is deterministic via to_canonical_json."""
    ref = _dev_fixture_ref()
    identity = _dev_fixture_identity()
    roles = _dev_fixture_role_binding_set()
    constraints = _dev_fixture_constraint_set()
    auth_set = _dev_fixture_authority_binding_set()

    def _make():
        return build_delegation_evidence_envelope(
            delegation_ref_id=ref.delegation_ref_id,
            delegation_identity_hash=identity.identity_hash,
            role_binding_hash=roles.role_binding_hash,
            constraint_set_hash=constraints.constraint_set_hash,
            authority_binding_set_hash=auth_set.authority_binding_set_hash,
            source_label=DelegationSourceLabel.DEV_FIXTURE,
        )

    s1 = serialize_delegation_evidence_envelope(_make())
    s2 = serialize_delegation_evidence_envelope(_make())
    assert s1 == s2


# -----------------------------------------------------------------------
# Test: Closed-world validation rejects unknown fields
# -----------------------------------------------------------------------


def test_p185_evidence_ref_closed_world():
    """DelegationEvidenceRef validates known field set."""
    with pytest.raises(DelegationUnknownFieldError):
        DelegationEvidenceRef.from_dict({
            "delegation_ref_id": "ref:test",
            "evidence_kind": "DOCUMENT_REF",
            "evidence_description": "test",
            "unknown_extra_field": "bad",
        })


def test_p185_claim_ref_closed_world():
    """DelegationNonRepudiationClaimRef validates known field set."""
    with pytest.raises(DelegationUnknownFieldError):
        DelegationNonRepudiationClaimRef.from_dict({
            "delegation_ref_id": "ref:test",
            "claim_subject_ref": "subj:test",
            "claim_statement": "test",
            "unknown_bad": "x",
        })


def test_p185_envelope_closed_world():
    """DelegationEvidenceEnvelope validates known field set."""
    with pytest.raises(DelegationUnknownFieldError):
        DelegationEvidenceEnvelope.from_dict({
            "delegation_ref_id": "ref:test",
            "delegation_identity_hash": "hash:id",
            "role_binding_hash": "hash:role",
            "constraint_set_hash": "hash:const",
            "authority_binding_set_hash": "hash:auth",
            "unknown_field": "bad",
        })


# -----------------------------------------------------------------------
# Test: Source/truth labels are visible
# -----------------------------------------------------------------------


def test_p185_source_labels_are_visible():
    """All constructed objects expose DEV_FIXTURE source label."""
    ref = _dev_fixture_ref()
    er = build_delegation_evidence_ref(
        delegation_ref_id=ref.delegation_ref_id,
        evidence_kind=DelegationEvidenceKind.DOCUMENT_REF,
        evidence_description="DEV_FIXTURE evidence",
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    cr = build_delegation_non_repudiation_claim_ref(
        delegation_ref_id=ref.delegation_ref_id,
        claim_subject_ref="subj:fixture",
        claim_statement="DEV_FIXTURE claim",
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    assert er.source_label == DelegationSourceLabel.DEV_FIXTURE
    assert cr.source_label == DelegationSourceLabel.DEV_FIXTURE


# -----------------------------------------------------------------------
# Test: UNAVAILABLE reasons exist
# -----------------------------------------------------------------------


def test_p185_status_report_has_unavailable_reasons():
    """Status report includes unavailable binding reasons."""
    sr = build_delegation_non_repudiation_status_report()
    reasons = dict(sr.unavailable_bindings)
    assert "Crypto Verifier" in reasons
    assert "Signature Verifier" in reasons
    assert "Trace Verifier" in reasons
    assert "Evidence Truth Verifier" in reasons
    assert "Claim Verifier" in reasons
    assert "Attestation Verifier" in reasons
    assert "Legal Non-Repudiation Engine" in reasons
    assert "Dispute Resolver" in reasons
    assert "Output Passport / P1.9" in reasons
    assert "Identity Mesh Binding / P1.8.6" in reasons
    assert "CLI/Shell/TUI Binding" in reasons
    assert "Projection/API/Event/Read Model" in reasons
    assert "Ledger Write" in reasons
    assert "Global Trace Write" in reasons


# -----------------------------------------------------------------------
# Test: All side-effect booleans are false
# -----------------------------------------------------------------------


def test_p185_side_effects_all_false():
    """All DelegationNonRepudiationSideEffects booleans are false."""
    se = DelegationNonRepudiationSideEffects()
    for item in fields(se):
        assert getattr(se, item.name) is False, f"{item.name} must be False"


def test_p185_binding_set_side_effects_default_all_false():
    """NonRepudiationBindingSet side_effects default all false."""
    ref = _dev_fixture_ref()
    identity = _dev_fixture_identity()
    roles = _dev_fixture_role_binding_set()
    constraints = _dev_fixture_constraint_set()
    auth_set = _dev_fixture_authority_binding_set()
    bs = build_delegation_non_repudiation_binding_set(
        delegation_ref_id=ref.delegation_ref_id,
        delegation_identity_hash=identity.identity_hash,
        role_binding_hash=roles.role_binding_hash,
        constraint_set_hash=constraints.constraint_set_hash,
        authority_binding_set_hash=auth_set.authority_binding_set_hash,
        bindings=[],
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    se = bs.side_effects
    assert se.crypto_verified is False
    assert se.signature_verified is False
    assert se.trace_verified is False
    assert se.evidence_verified is False
    assert se.claim_verified is False
    assert se.attestation_verified is False
    assert se.ledger_written is False
    assert se.global_trace_written is False
    assert se.policy_called is False
    assert se.custos_called is False
    assert se.approval_created is False
    assert se.runtime_mutated is False
    assert se.non_repudiation_proven is False
    assert se.legal_finality_claimed is False


# -----------------------------------------------------------------------
# Test: Status report available contracts
# -----------------------------------------------------------------------


def test_p185_status_report_available_contracts():
    """Status report declares available P1.8.5 contracts as LIVE."""
    sr = build_delegation_non_repudiation_status_report()
    contracts = dict(sr.available_contracts)
    assert "DelegationEvidenceRef" in contracts
    assert "DelegationNonRepudiationClaimRef" in contracts
    assert "DelegationEvidenceEnvelope" in contracts
    assert "DelegationEvidenceCompletenessProfile" in contracts
    assert "DelegationNonRepudiationBinding" in contracts
    assert "DelegationNonRepudiationBindingSet" in contracts
    assert "DelegationNonRepudiationSideEffects" in contracts
    assert "DelegationNonRepudiationStatusReport" in contracts


# -----------------------------------------------------------------------
# Test: from_dict roundtrip
# -----------------------------------------------------------------------


def test_p185_evidence_ref_from_dict_roundtrip():
    """DelegationEvidenceRef from_dict roundtrips."""
    ref = _dev_fixture_ref()
    er = build_delegation_evidence_ref(
        delegation_ref_id=ref.delegation_ref_id,
        evidence_kind=DelegationEvidenceKind.DOCUMENT_REF,
        evidence_description="DEV_FIXTURE evidence",
        evidence_uri_ref="file:///dev/fixture/ev.log",
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    data = er.to_canonical_dict()
    er2 = DelegationEvidenceRef.from_dict(data)
    assert er2.evidence_ref_hash == er.evidence_ref_hash
    assert er2.evidence_ref_id == er.evidence_ref_id
    assert er2.evidence_kind == er.evidence_kind


def test_p185_claim_ref_from_dict_roundtrip():
    """DelegationNonRepudiationClaimRef from_dict roundtrips."""
    ref = _dev_fixture_ref()
    cr = build_delegation_non_repudiation_claim_ref(
        delegation_ref_id=ref.delegation_ref_id,
        claim_subject_ref="subj:fixture",
        claim_statement="DEV_FIXTURE claim",
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    data = cr.to_canonical_dict()
    cr2 = DelegationNonRepudiationClaimRef.from_dict(data)
    assert cr2.claim_ref_hash == cr.claim_ref_hash
    assert cr2.claim_ref_id == cr.claim_ref_id


# -----------------------------------------------------------------------
# Test: Full operator-testable DEV_FIXTURE chain
# -----------------------------------------------------------------------


def test_p185_full_dev_fixture_chain():
    """Full operator-testable P1.8.5 DEV_FIXTURE chain:
       P1.8.4 AuthorityBindingSet → evidence refs → claim refs →
       EvidenceEnvelope → CompletenessProfile → NonRepudiationBinding →
       NonRepudiationBindingSet → StatusReport."""
    # Gather P1.8.0–P1.8.4 context
    ref = _dev_fixture_ref()
    identity = _dev_fixture_identity()
    roles = _dev_fixture_role_binding_set()
    constraints = _dev_fixture_constraint_set()
    auth_set = _dev_fixture_authority_binding_set()

    # Step 1: Build evidence references
    er_doc = build_delegation_evidence_ref(
        delegation_ref_id=ref.delegation_ref_id,
        evidence_kind=DelegationEvidenceKind.DOCUMENT_REF,
        evidence_description="DEV_FIXTURE delegation log document",
        evidence_uri_ref="file:///dev/fixture/delegation_log.json",
        evidence_hash_ref="sha256:aaaaaaaaaaaaaaaa",
        proof_status=DelegationProofReferenceStatus.EVIDENCE_REFERENCED,
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    er_artifact = build_delegation_evidence_ref(
        delegation_ref_id=ref.delegation_ref_id,
        evidence_kind=DelegationEvidenceKind.ARTIFACT_REF,
        evidence_description="DEV_FIXTURE delegation artifact bundle",
        evidence_uri_ref="file:///dev/fixture/artifact.tar.gz",
        evidence_hash_ref="sha256:bbbbbbbbbbbbbbbb",
        proof_status=DelegationProofReferenceStatus.EVIDENCE_REFERENCED,
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )

    # Step 2: Build claim references
    cr = build_delegation_non_repudiation_claim_ref(
        delegation_ref_id=ref.delegation_ref_id,
        claim_subject_ref="subj:delegation_action",
        claim_statement=(
            "DEV_FIXTURE claim: operator delegated action to agent "
            "under explicit scope bound, with operator-declared authority, "
            "on 2026-06-27"
        ),
        claim_context_ref="ctx:delegation_p1_8_5_fixture",
        proof_status=DelegationProofReferenceStatus.CLAIM_REFERENCED,
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )

    # Step 3: Build evidence envelope
    envelope = build_delegation_evidence_envelope(
        delegation_ref_id=ref.delegation_ref_id,
        delegation_identity_hash=identity.identity_hash,
        role_binding_hash=roles.role_binding_hash,
        constraint_set_hash=constraints.constraint_set_hash,
        authority_binding_set_hash=auth_set.authority_binding_set_hash,
        evidence_refs=[er_doc, er_artifact],
        claim_refs=[cr],
        attestation_refs=["attest:operator_fixture_20260627"],
        signature_refs=["sig:operator_key_fixture"],
        trace_refs=["trace:delegation_event_fixture"],
        proof_status=DelegationProofReferenceStatus.TRACE_REFERENCED,
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    assert envelope.evidence_envelope_hash != ""
    assert envelope.evidence_envelope_id.startswith("evenv:")

    # Step 4: Build completeness profile
    profile = build_delegation_evidence_completeness_profile(
        delegation_ref_id=ref.delegation_ref_id,
        evidence_envelope_hash=envelope.evidence_envelope_hash,
        has_delegation_identity=True,
        has_role_binding=True,
        has_constraints=True,
        has_authority_refs=True,
        has_evidence_refs=True,
        has_claim_refs=True,
        has_attestation_refs=True,
        has_signature_refs=True,
        has_trace_refs=True,
        missing_components=[
            "Missing: Crypto Verifier",
            "Missing: Non-Repudiation Prover",
        ],
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    assert profile.profile_hash != ""
    assert profile.profile_id.startswith("cmpprof:")
    assert profile.has_delegation_identity is True
    assert "Missing: Crypto Verifier" in profile.missing_components

    # Step 5: Build non-repudiation binding
    binding = build_delegation_non_repudiation_binding(
        delegation_ref_id=ref.delegation_ref_id,
        delegation_identity_hash=identity.identity_hash,
        role_binding_hash=roles.role_binding_hash,
        constraint_set_hash=constraints.constraint_set_hash,
        authority_binding_set_hash=auth_set.authority_binding_set_hash,
        evidence_envelope_hash=envelope.evidence_envelope_hash,
        completeness_profile_hash=profile.profile_hash,
        proof_status=DelegationProofReferenceStatus.TRACE_REFERENCED,
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    assert binding.binding_hash != ""
    assert binding.binding_id.startswith("nrbind:")

    # Step 6: Build non-repudiation binding set
    binding_set = build_delegation_non_repudiation_binding_set(
        delegation_ref_id=ref.delegation_ref_id,
        delegation_identity_hash=identity.identity_hash,
        role_binding_hash=roles.role_binding_hash,
        constraint_set_hash=constraints.constraint_set_hash,
        authority_binding_set_hash=auth_set.authority_binding_set_hash,
        bindings=[binding],
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    assert binding_set.non_repudiation_binding_set_hash != ""
    assert binding_set.non_repudiation_binding_set_id.startswith("nrbset:")

    # Step 7: Build status report
    sr = build_delegation_non_repudiation_status_report()
    assert sr.status_hash != ""
    assert sr.status_label == DelegationSourceLabel.DEV_FIXTURE

    # Step 8: Verify side effects all false
    se = binding_set.side_effects
    for item in fields(se):
        assert getattr(se, item.name) is False

        # Step 9: Verify all source labels are DEV_FIXTURE
        for obj in [er_doc, er_artifact, cr, envelope, profile, binding, binding_set]:
            assert obj.source_label == DelegationSourceLabel.DEV_FIXTURE
        assert sr.status_label == DelegationSourceLabel.DEV_FIXTURE


# -----------------------------------------------------------------------
# Test: Serialization roundtrip for binding set
# -----------------------------------------------------------------------


def test_p185_binding_set_serialization_roundtrip():
    """NonRepudiationBindingSet serialization is roundtrip-safe."""
    ref = _dev_fixture_ref()
    identity = _dev_fixture_identity()
    roles = _dev_fixture_role_binding_set()
    constraints = _dev_fixture_constraint_set()
    auth_set = _dev_fixture_authority_binding_set()
    envelope = build_delegation_evidence_envelope(
        delegation_ref_id=ref.delegation_ref_id,
        delegation_identity_hash=identity.identity_hash,
        role_binding_hash=roles.role_binding_hash,
        constraint_set_hash=constraints.constraint_set_hash,
        authority_binding_set_hash=auth_set.authority_binding_set_hash,
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    profile = build_delegation_evidence_completeness_profile(
        delegation_ref_id=ref.delegation_ref_id,
        evidence_envelope_hash=envelope.evidence_envelope_hash,
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    binding = build_delegation_non_repudiation_binding(
        delegation_ref_id=ref.delegation_ref_id,
        delegation_identity_hash=identity.identity_hash,
        role_binding_hash=roles.role_binding_hash,
        constraint_set_hash=constraints.constraint_set_hash,
        authority_binding_set_hash=auth_set.authority_binding_set_hash,
        evidence_envelope_hash=envelope.evidence_envelope_hash,
        completeness_profile_hash=profile.profile_hash,
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    bs = build_delegation_non_repudiation_binding_set(
        delegation_ref_id=ref.delegation_ref_id,
        delegation_identity_hash=identity.identity_hash,
        role_binding_hash=roles.role_binding_hash,
        constraint_set_hash=constraints.constraint_set_hash,
        authority_binding_set_hash=auth_set.authority_binding_set_hash,
        bindings=[binding],
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    json_str = serialize_delegation_non_repudiation_binding_set(bs)
    parsed = json.loads(json_str)
    assert parsed["delegation_ref_id"] == ref.delegation_ref_id
    assert parsed["source_label"] == "DEV_FIXTURE"


# -----------------------------------------------------------------------
# Test: Envelope hash is deterministic serialization artifact
# -----------------------------------------------------------------------


def test_p185_envelope_hash_is_deterministic():
    """Envelope hash survives repeated construction with identical inputs."""
    ref = _dev_fixture_ref()
    identity = _dev_fixture_identity()
    roles = _dev_fixture_role_binding_set()
    constraints = _dev_fixture_constraint_set()
    auth_set = _dev_fixture_authority_binding_set()

    def _build():
        return build_delegation_evidence_envelope(
            delegation_ref_id=ref.delegation_ref_id,
            delegation_identity_hash=identity.identity_hash,
            role_binding_hash=roles.role_binding_hash,
            constraint_set_hash=constraints.constraint_set_hash,
            authority_binding_set_hash=auth_set.authority_binding_set_hash,
            source_label=DelegationSourceLabel.DEV_FIXTURE,
        )

    assert hash_delegation_evidence_envelope(_build()) == hash_delegation_evidence_envelope(_build())


# -----------------------------------------------------------------------
# Test: DelegationDisputeReadinessStatus values
# -----------------------------------------------------------------------


def test_p185_dispute_readiness_status_values():
    """DelegationDisputeReadinessStatus has expected values."""
    assert DelegationDisputeReadinessStatus.NOT_EVALUATED.value == "NOT_EVALUATED"
    assert DelegationDisputeReadinessStatus.DISPUTE_REF_AVAILABLE.value == "DISPUTE_REF_AVAILABLE"
    assert DelegationDisputeReadinessStatus.UNAVAILABLE.value == "UNAVAILABLE"
    assert DelegationDisputeReadinessStatus.UNKNOWN.value == "UNKNOWN"


# -----------------------------------------------------------------------
# Test: EvidenceKind values
# -----------------------------------------------------------------------


def test_p185_evidence_kind_values():
    """DelegationEvidenceKind has expected values."""
    assert DelegationEvidenceKind.DOCUMENT_REF.value == "DOCUMENT_REF"
    assert DelegationEvidenceKind.TRACE_REF.value == "TRACE_REF"
    assert DelegationEvidenceKind.SIGNATURE_REF.value == "SIGNATURE_REF"
    assert DelegationEvidenceKind.ATTESTATION_REF.value == "ATTESTATION_REF"
    assert DelegationEvidenceKind.UNKNOWN.value == "UNKNOWN"
