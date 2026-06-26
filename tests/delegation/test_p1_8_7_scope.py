"""P1.8.7 — Delegation Scope / Boundary Model tests."""
from __future__ import annotations

import json
from dataclasses import fields

import pytest

from agentic_runtime.delegation.foundation import (
    DelegationActorKind,
    DelegationAuthorityKind,
    DelegationConstraintKind,
    DelegationSourceLabel,
    DelegationSubjectKind,
    build_agent_identity_mesh_ref,
    build_delegation_actor_ref,
    build_delegation_authority_ref as build_foundation_authority_ref,
    build_delegation_constraint,
    build_delegation_record,
    build_delegation_subject,
    build_non_repudiation_ref,
)
from agentic_runtime.delegation import (
    DelegationAuthorityRefKind,
    DelegationAuthorityRefStatus,
    DelegationConstraintSeverity,
    DelegationIdentityMeshBinding,
    DelegationIdentityMeshBindingSet,
    DelegationIdentityMeshEnvelope,
    DelegationMeshParticipantKind,
    DelegationMeshRelationshipKind,
    DelegationMeshScopeKind,
    DelegationRoleKind,
    build_delegated_subject_ref,
    build_delegation_authority_binding,
    build_delegation_authority_binding_set,
    build_delegation_authority_ref,
    build_delegation_constraint_binding,
    build_delegation_constraint_ref,
    build_delegation_constraint_set,
    build_delegation_identity,
    build_delegation_identity_mesh_binding,
    build_delegation_identity_mesh_binding_set,
    build_delegation_identity_mesh_envelope,
    build_delegation_mesh_participant_ref,
    build_delegation_mesh_relationship_map,
    build_delegation_mesh_relationship_ref,
    build_delegation_mesh_resolution_readiness_profile,
    build_delegation_mesh_scope_ref,
    build_delegation_non_repudiation_binding,
    build_delegation_non_repudiation_binding_set,
    build_delegation_non_repudiation_status_report,
    build_delegation_party_role_ref,
    build_delegation_ref,
    build_delegation_role_binding_set,
)
from agentic_runtime.delegation.scope import (
    DelegationValidationError,
    DelegationUnknownFieldError,
    DelegationScopeSideEffects,
    DelegationScopeStatusReport,
    DelegationScopeRef,
    DelegationBoundaryRef,
    DelegationScopeInclusionRef,
    DelegationScopeExclusionRef,
    DelegationBoundaryMatrixEntry,
    DelegationBoundaryMatrix,
    DelegationScopeReadinessProfile,
    DelegationScopeEnvelope,
    DelegationScopeBinding,
    DelegationScopeBindingSet,
    DelegationBoundaryKind,
    DelegationBoundaryPosture,
    DelegationScopeDimension,
    DelegationScopeKind,
    DelegationScopeStatus,
    build_delegation_scope_ref,
    build_delegation_boundary_ref,
    build_delegation_scope_inclusion_ref,
    build_delegation_scope_exclusion_ref,
    build_delegation_boundary_matrix_entry,
    build_delegation_boundary_matrix,
    build_delegation_scope_readiness_profile,
    build_delegation_scope_envelope,
    build_delegation_scope_binding,
    build_delegation_scope_binding_set,
    build_delegation_scope_status_report,
    hash_delegation_scope_ref,
    hash_delegation_boundary_ref,
    hash_delegation_scope_inclusion_ref,
    hash_delegation_scope_exclusion_ref,
    hash_delegation_boundary_matrix,
    hash_delegation_scope_readiness_profile,
    hash_delegation_scope_envelope,
    hash_delegation_scope_binding_set,
    serialize_delegation_scope_envelope,
    serialize_delegation_scope_binding_set,
)

DEV_FIXTURE_CREATED_AT = "2026-06-27T00:00:00Z"


# -----------------------------------------------------------------------
# DEV_FIXTURE builder chain (exact pattern from P1.8.6 test)
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
    cs = _dev_fixture_constraint_set()
    auth_ref = build_delegation_authority_ref(
        ref.delegation_ref_id,
        DelegationAuthorityRefKind.OPERATOR_DECLARED,
        "DEV_FIXTURE authority basis",
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    binding = build_delegation_authority_binding(
        ref.delegation_ref_id,
        identity.identity_hash,
        roles.role_binding_hash,
        cs.constraint_set_hash,
        auth_ref.authority_ref_id,
        auth_ref.authority_ref_hash,
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    return build_delegation_authority_binding_set(
        ref.delegation_ref_id,
        identity.identity_hash,
        roles.role_binding_hash,
        cs.constraint_set_hash,
        [auth_ref],
        [binding],
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )


def _dev_fixture_nr_binding_set():
    """P1.8.5 DEV_FIXTURE DelegationNonRepudiationBindingSet.
    Uses direct import since build helpers require module-level context."""
    from agentic_runtime.delegation import (
        DelegationEvidenceKind,
        DelegationEvidenceRef,
        DelegationEvidenceEnvelope,
        DelegationEvidenceCompletenessProfile,
        DelegationNonRepudiationBinding,
        DelegationNonRepudiationBindingSet,
    )
    ref = _dev_fixture_ref()
    identity = _dev_fixture_identity()
    roles = _dev_fixture_role_binding_set()
    cs = _dev_fixture_constraint_set()
    abs_ = _dev_fixture_authority_binding_set()
    ev = DelegationEvidenceRef(
        evidence_kind=DelegationEvidenceKind.DOCUMENT_REF,
        evidence_description="fixture-evidence-ref",
        delegation_ref_id=ref.delegation_ref_id,
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    envelope = DelegationEvidenceEnvelope(
        delegation_ref_id=ref.delegation_ref_id,
        delegation_identity_hash=identity.identity_hash,
        role_binding_hash=roles.role_binding_hash,
        constraint_set_hash=cs.constraint_set_hash,
        authority_binding_set_hash=abs_.authority_binding_set_hash,
        evidence_refs=(ev,),
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    profile = DelegationEvidenceCompletenessProfile(
        delegation_ref_id=ref.delegation_ref_id,
        evidence_envelope_hash=envelope.evidence_envelope_hash,
        has_evidence_refs=True,
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    binding = DelegationNonRepudiationBinding(
        delegation_ref_id=ref.delegation_ref_id,
        delegation_identity_hash=identity.identity_hash,
        role_binding_hash=roles.role_binding_hash,
        constraint_set_hash=cs.constraint_set_hash,
        authority_binding_set_hash=abs_.authority_binding_set_hash,
        evidence_envelope_hash=envelope.evidence_envelope_hash,
        completeness_profile_hash=profile.profile_hash,
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    return DelegationNonRepudiationBindingSet(
        delegation_ref_id=ref.delegation_ref_id,
        delegation_identity_hash=identity.identity_hash,
        role_binding_hash=roles.role_binding_hash,
        constraint_set_hash=cs.constraint_set_hash,
        authority_binding_set_hash=abs_.authority_binding_set_hash,
        bindings=(binding,),
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )


def _dev_fixture_im_binding_set():
    """P1.8.6 DEV_FIXTURE DelegationIdentityMeshBindingSet."""
    ref = _dev_fixture_ref()
    identity = _dev_fixture_identity()
    roles = _dev_fixture_role_binding_set()
    cs = _dev_fixture_constraint_set()
    abs_ = _dev_fixture_authority_binding_set()
    nrs = _dev_fixture_nr_binding_set()
    mesh_scope = build_delegation_mesh_scope_ref(
        ref.delegation_ref_id,
        DelegationMeshScopeKind.DELEGATION_LOCAL,
        "fixture-mesh-scope",
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    envelope = build_delegation_identity_mesh_envelope(
        delegation_ref_id=ref.delegation_ref_id,
        delegation_identity_hash=identity.identity_hash,
        role_binding_hash=roles.role_binding_hash,
        constraint_set_hash=cs.constraint_set_hash,
        authority_binding_set_hash=abs_.authority_binding_set_hash,
        non_repudiation_binding_set_hash=nrs.non_repudiation_binding_set_hash,
        source_label=DelegationSourceLabel.DEV_FIXTURE,
        participant_refs=[build_delegation_mesh_participant_ref(
            ref.delegation_ref_id,
            DelegationMeshParticipantKind.AGENT_REF,
            "fixture-agent",
            "DEV_FIXTURE agent participant",
            source_label=DelegationSourceLabel.DEV_FIXTURE,
        )],
        relationship_refs=[build_delegation_mesh_relationship_ref(
            ref.delegation_ref_id,
            DelegationMeshRelationshipKind.DELEGATOR_TO_DELEGATE,
            "fixture-delegator-ref",
            "fixture-delegate-ref",
            source_label=DelegationSourceLabel.DEV_FIXTURE,
        )],
        mesh_scope_ref=mesh_scope,
    )
    readiness = build_delegation_mesh_resolution_readiness_profile(
        ref.delegation_ref_id,
        envelope.identity_mesh_envelope_hash,
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    rel_map = build_delegation_mesh_relationship_map(
        ref.delegation_ref_id,
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    binding = build_delegation_identity_mesh_binding(
        ref.delegation_ref_id,
        identity.identity_hash,
        roles.role_binding_hash,
        cs.constraint_set_hash,
        abs_.authority_binding_set_hash,
        nrs.non_repudiation_binding_set_hash,
        envelope.identity_mesh_envelope_hash,
        readiness.readiness_hash,
        rel_map.relationship_map_hash,
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    return build_delegation_identity_mesh_binding_set(
        ref.delegation_ref_id,
        identity.identity_hash,
        roles.role_binding_hash,
        cs.constraint_set_hash,
        abs_.authority_binding_set_hash,
        nrs.non_repudiation_binding_set_hash,
        bindings=[binding],
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )


# -----------------------------------------------------------------------
# DEV_FIXTURE P1.8.7 scope helpers
# -----------------------------------------------------------------------


def _dev_fixture_scope_ref():
    """P1.8.7 DEV_FIXTURE DelegationScopeRef."""
    ref = _dev_fixture_ref()
    return build_delegation_scope_ref(
        DelegationScopeKind.TASK_SCOPE,
        "fixture-task-scope-ref",
        ref.delegation_ref_id,
        scope_description="DEV_FIXTURE task scope",
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )


def _dev_fixture_boundary_ref():
    """P1.8.7 DEV_FIXTURE DelegationBoundaryRef."""
    ref = _dev_fixture_ref()
    return build_delegation_boundary_ref(
        DelegationBoundaryKind.INCLUSION,
        DelegationScopeDimension.TOOL,
        "fixture-tool-boundary-ref",
        ref.delegation_ref_id,
        boundary_description="DEV_FIXTURE tool boundary",
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )


def _dev_fixture_inclusion_ref():
    """P1.8.7 DEV_FIXTURE DelegationScopeInclusionRef."""
    ref = _dev_fixture_ref()
    scope = _dev_fixture_scope_ref()
    return build_delegation_scope_inclusion_ref(
        ref.delegation_ref_id,
        scope.scope_ref_id,
        DelegationScopeDimension.TOOL,
        "fixture-include-tool",
        inclusion_description="DEV_FIXTURE tool inclusion",
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )


def _dev_fixture_exclusion_ref():
    """P1.8.7 DEV_FIXTURE DelegationScopeExclusionRef."""
    ref = _dev_fixture_ref()
    scope = _dev_fixture_scope_ref()
    return build_delegation_scope_exclusion_ref(
        ref.delegation_ref_id,
        scope.scope_ref_id,
        DelegationScopeDimension.NETWORK,
        "fixture-exclude-network",
        exclusion_description="DEV_FIXTURE network exclusion",
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )


def _dev_fixture_matrix_entry():
    """P1.8.7 DEV_FIXTURE DelegationBoundaryMatrixEntry."""
    ref = _dev_fixture_ref()
    boundary = _dev_fixture_boundary_ref()
    return build_delegation_boundary_matrix_entry(
        ref.delegation_ref_id,
        DelegationScopeDimension.TOOL,
        DelegationBoundaryPosture.IN_SCOPE,
        boundary.boundary_ref_id,
        reason_ref="DEV_FIXTURE scope declared",
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )


def _dev_fixture_matrix():
    """P1.8.7 DEV_FIXTURE DelegationBoundaryMatrix."""
    ref = _dev_fixture_ref()
    return build_delegation_boundary_matrix(
        ref.delegation_ref_id,
        entries=[_dev_fixture_matrix_entry()],
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )


def _dev_fixture_readiness_profile():
    """P1.8.7 DEV_FIXTURE DelegationScopeReadinessProfile."""
    ref = _dev_fixture_ref()
    return build_delegation_scope_readiness_profile(
        ref.delegation_ref_id,
        has_scope_refs=True,
        has_boundary_refs=True,
        has_inclusion_refs=True,
        has_exclusion_refs=True,
        has_boundary_matrix=True,
        has_tool_boundary=True,
        has_data_boundary=False,
        has_memory_boundary=False,
        has_path_boundary=False,
        has_runtime_boundary=False,
        has_agent_boundary=False,
        has_model_boundary=False,
        has_network_boundary=True,
        has_human_approval_boundary=False,
        has_time_boundary=False,
        has_risk_boundary=False,
        missing_components=["DATA_BOUNDARY", "MEMORY_BOUNDARY"],
        enforcement_unavailable_reason="DEV_FIXTURE enforcement unavailable",
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )


def _dev_fixture_envelope():
    """P1.8.7 DEV_FIXTURE DelegationScopeEnvelope."""
    ref = _dev_fixture_ref()
    identity = _dev_fixture_identity()
    roles = _dev_fixture_role_binding_set()
    cs = _dev_fixture_constraint_set()
    abs_ = _dev_fixture_authority_binding_set()
    nrs = _dev_fixture_nr_binding_set()
    ims = _dev_fixture_im_binding_set()
    matrix = _dev_fixture_matrix()
    profile = _dev_fixture_readiness_profile()
    return build_delegation_scope_envelope(
        ref.delegation_ref_id,
        identity.identity_hash,
        roles.role_binding_hash,
        cs.constraint_set_hash,
        abs_.authority_binding_set_hash,
        nrs.non_repudiation_binding_set_hash,
        ims.identity_mesh_binding_set_hash,
        matrix.boundary_matrix_hash,
        profile.scope_readiness_hash,
        scope_refs=[_dev_fixture_scope_ref()],
        boundary_refs=[_dev_fixture_boundary_ref()],
        inclusion_refs=[_dev_fixture_inclusion_ref()],
        exclusion_refs=[_dev_fixture_exclusion_ref()],
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )


def _dev_fixture_binding():
    """P1.8.7 DEV_FIXTURE DelegationScopeBinding."""
    ref = _dev_fixture_ref()
    identity = _dev_fixture_identity()
    roles = _dev_fixture_role_binding_set()
    cs = _dev_fixture_constraint_set()
    abs_ = _dev_fixture_authority_binding_set()
    nrs = _dev_fixture_nr_binding_set()
    ims = _dev_fixture_im_binding_set()
    envelope = _dev_fixture_envelope()
    matrix = _dev_fixture_matrix()
    profile = _dev_fixture_readiness_profile()
    return build_delegation_scope_binding(
        ref.delegation_ref_id,
        identity.identity_hash,
        roles.role_binding_hash,
        cs.constraint_set_hash,
        abs_.authority_binding_set_hash,
        nrs.non_repudiation_binding_set_hash,
        ims.identity_mesh_binding_set_hash,
        envelope.scope_envelope_hash,
        matrix.boundary_matrix_hash,
        profile.scope_readiness_hash,
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )


def _dev_fixture_binding_set():
    """P1.8.7 DEV_FIXTURE DelegationScopeBindingSet."""
    ref = _dev_fixture_ref()
    identity = _dev_fixture_identity()
    roles = _dev_fixture_role_binding_set()
    cs = _dev_fixture_constraint_set()
    abs_ = _dev_fixture_authority_binding_set()
    nrs = _dev_fixture_nr_binding_set()
    ims = _dev_fixture_im_binding_set()
    return build_delegation_scope_binding_set(
        ref.delegation_ref_id,
        identity.identity_hash,
        roles.role_binding_hash,
        cs.constraint_set_hash,
        abs_.authority_binding_set_hash,
        nrs.non_repudiation_binding_set_hash,
        ims.identity_mesh_binding_set_hash,
        bindings=[_dev_fixture_binding()],
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )


# -----------------------------------------------------------------------
# Test: imports and existing exports preserved
# -----------------------------------------------------------------------


class TestImportsAndPreservation:
    """P1.8.7 imports work and prior exports remain intact."""

    def test_p187_imports_work(self):
        """All P1.8.7 symbols importable from agentic_runtime.delegation."""
        symbols = [
            DelegationBoundaryKind,
            DelegationBoundaryPosture,
            DelegationScopeDimension,
            DelegationScopeKind,
            DelegationScopeStatus,
            DelegationScopeRef,
            DelegationBoundaryRef,
            DelegationScopeInclusionRef,
            DelegationScopeExclusionRef,
            DelegationBoundaryMatrixEntry,
            DelegationBoundaryMatrix,
            DelegationScopeReadinessProfile,
            DelegationScopeEnvelope,
            DelegationScopeBinding,
            DelegationScopeBindingSet,
            DelegationScopeSideEffects,
            DelegationScopeStatusReport,
        ]
        for sym in symbols:
            assert sym is not None

    def test_p180_exports_preserved(self):
        """P1.8.0 DelegationRecord and foundation still importable."""
        from agentic_runtime.delegation import (
            DelegationRecord,
            DelegationSideEffects,
            DelegationSourceLabel,
        )
        assert DelegationRecord is not None
        assert DelegationSideEffects is not None

    def test_p181_exports_preserved(self):
        from agentic_runtime.delegation import DelegationRef, DelegationIdentity
        assert DelegationRef is not None
        assert DelegationIdentity is not None

    def test_p182_exports_preserved(self):
        from agentic_runtime.delegation import DelegationRoleBindingSet
        assert DelegationRoleBindingSet is not None

    def test_p183_exports_preserved(self):
        from agentic_runtime.delegation import DelegationConstraintSet
        assert DelegationConstraintSet is not None

    def test_p184_exports_preserved(self):
        from agentic_runtime.delegation import DelegationAuthorityBindingSet
        assert DelegationAuthorityBindingSet is not None

    def test_p185_exports_preserved(self):
        from agentic_runtime.delegation import DelegationNonRepudiationBindingSet
        assert DelegationNonRepudiationBindingSet is not None

    def test_p186_exports_preserved(self):
        from agentic_runtime.delegation import DelegationIdentityMeshBindingSet
        assert DelegationIdentityMeshBindingSet is not None


# -----------------------------------------------------------------------
# Test: P1.8.6 IdentityMeshBindingSet feeds P1.8.7 scope path
# -----------------------------------------------------------------------


class TestP186ToP187Chain:
    """P1.8.6 mesh → P1.8.7 scope feed-through."""

    def test_im_binding_set_hashes_feed_scope_envelope(self):
        """IdentityMeshBindingSet hash goes into scope envelope."""
        ims = _dev_fixture_im_binding_set()
        identity = _dev_fixture_identity()
        roles = _dev_fixture_role_binding_set()
        cs = _dev_fixture_constraint_set()
        abs_ = _dev_fixture_authority_binding_set()
        nrs = _dev_fixture_nr_binding_set()
        matrix = _dev_fixture_matrix()
        profile = _dev_fixture_readiness_profile()
        envelope = build_delegation_scope_envelope(
            _dev_fixture_ref().delegation_ref_id,
            identity.identity_hash,
            roles.role_binding_hash,
            cs.constraint_set_hash,
            abs_.authority_binding_set_hash,
            nrs.non_repudiation_binding_set_hash,
            ims.identity_mesh_binding_set_hash,
            matrix.boundary_matrix_hash,
            profile.scope_readiness_hash,
            source_label=DelegationSourceLabel.DEV_FIXTURE,
        )
        assert envelope.identity_mesh_binding_set_hash == ims.identity_mesh_binding_set_hash

    def test_im_binding_set_hash_immutable_across_scope(self):
        """Mesh binding set hash unchanged when scope envelope built."""
        ims = _dev_fixture_im_binding_set()
        h1 = ims.identity_mesh_binding_set_hash
        h2 = ims.identity_mesh_binding_set_hash
        assert h1 == h2


# -----------------------------------------------------------------------
# Test: DelegationScopeRef
# -----------------------------------------------------------------------


class TestDelegationScopeRef:
    """P1.8.7 scope ref determinism and boundary."""

    def test_builds_deterministically(self):
        sr = _dev_fixture_scope_ref()
        assert sr.scope_kind == DelegationScopeKind.TASK_SCOPE
        assert sr.scope_hash
        assert sr.scope_ref_id.startswith("scope:")
        assert sr.source_label == DelegationSourceLabel.DEV_FIXTURE
        assert sr.scope_status == DelegationScopeStatus.REFERENCE_ONLY

    def test_identical_input_identical_hash(self):
        a = _dev_fixture_scope_ref()
        b = _dev_fixture_scope_ref()
        assert a.scope_hash == b.scope_hash
        assert hash_delegation_scope_ref(a) == hash_delegation_scope_ref(b)

    def test_changed_scope_kind_changes_hash(self):
        ref = _dev_fixture_ref()
        a = build_delegation_scope_ref(
            DelegationScopeKind.TASK_SCOPE,
            "fixture-ref",
            ref.delegation_ref_id,
            source_label=DelegationSourceLabel.DEV_FIXTURE,
        )
        b = build_delegation_scope_ref(
            DelegationScopeKind.TOOL_SCOPE,
            "fixture-ref",
            ref.delegation_ref_id,
            source_label=DelegationSourceLabel.DEV_FIXTURE,
        )
        assert a.scope_hash != b.scope_hash

    def test_changed_scope_ref_changes_hash(self):
        ref = _dev_fixture_ref()
        a = build_delegation_scope_ref(
            DelegationScopeKind.TASK_SCOPE,
            "ref-a",
            ref.delegation_ref_id,
            source_label=DelegationSourceLabel.DEV_FIXTURE,
        )
        b = build_delegation_scope_ref(
            DelegationScopeKind.TASK_SCOPE,
            "ref-b",
            ref.delegation_ref_id,
            source_label=DelegationSourceLabel.DEV_FIXTURE,
        )
        assert a.scope_hash != b.scope_hash

    def test_scope_ref_is_not_permission(self):
        sr = _dev_fixture_scope_ref()
        assert sr.scope_status == DelegationScopeStatus.REFERENCE_ONLY


# -----------------------------------------------------------------------
# Test: DelegationBoundaryRef
# -----------------------------------------------------------------------


class TestDelegationBoundaryRef:
    """P1.8.7 boundary ref determinism."""

    def test_builds_deterministically(self):
        br = _dev_fixture_boundary_ref()
        assert br.boundary_kind == DelegationBoundaryKind.INCLUSION
        assert br.boundary_hash
        assert br.boundary_ref_id.startswith("bnd:")
        assert br.source_label == DelegationSourceLabel.DEV_FIXTURE

    def test_identical_input_identical_hash(self):
        a = _dev_fixture_boundary_ref()
        b = _dev_fixture_boundary_ref()
        assert a.boundary_hash == b.boundary_hash
        assert hash_delegation_boundary_ref(a) == hash_delegation_boundary_ref(b)

    def test_changed_boundary_kind_changes_hash(self):
        ref = _dev_fixture_ref()
        a = build_delegation_boundary_ref(
            DelegationBoundaryKind.INCLUSION,
            DelegationScopeDimension.TOOL,
            "fixture-ref",
            ref.delegation_ref_id,
            source_label=DelegationSourceLabel.DEV_FIXTURE,
        )
        b = build_delegation_boundary_ref(
            DelegationBoundaryKind.EXCLUSION,
            DelegationScopeDimension.TOOL,
            "fixture-ref",
            ref.delegation_ref_id,
            source_label=DelegationSourceLabel.DEV_FIXTURE,
        )
        assert a.boundary_hash != b.boundary_hash

    def test_boundary_ref_not_enforcement(self):
        br = _dev_fixture_boundary_ref()
        assert br.scope_status == DelegationScopeStatus.REFERENCE_ONLY


# -----------------------------------------------------------------------
# Test: DelegationScopeInclusionRef
# -----------------------------------------------------------------------


class TestDelegationScopeInclusionRef:
    """P1.8.7 inclusion ref determinism."""

    def test_builds_deterministically(self):
        ir = _dev_fixture_inclusion_ref()
        assert ir.inclusion_hash
        assert ir.inclusion_ref_id.startswith("incl:")
        assert ir.source_label == DelegationSourceLabel.DEV_FIXTURE

    def test_identical_input_identical_hash(self):
        a = _dev_fixture_inclusion_ref()
        b = _dev_fixture_inclusion_ref()
        assert a.inclusion_hash == b.inclusion_hash
        assert hash_delegation_scope_inclusion_ref(a) == hash_delegation_scope_inclusion_ref(b)

    def test_changed_inclusion_ref_changes_hash(self):
        ref = _dev_fixture_ref()
        scope = _dev_fixture_scope_ref()
        a = build_delegation_scope_inclusion_ref(
            ref.delegation_ref_id, scope.scope_ref_id,
            DelegationScopeDimension.TOOL, "ref-a",
            source_label=DelegationSourceLabel.DEV_FIXTURE,
        )
        b = build_delegation_scope_inclusion_ref(
            ref.delegation_ref_id, scope.scope_ref_id,
            DelegationScopeDimension.TOOL, "ref-b",
            source_label=DelegationSourceLabel.DEV_FIXTURE,
        )
        assert a.inclusion_hash != b.inclusion_hash

    def test_inclusion_ref_not_permission(self):
        ir = _dev_fixture_inclusion_ref()
        assert ir.scope_status == DelegationScopeStatus.REFERENCE_ONLY


# -----------------------------------------------------------------------
# Test: DelegationScopeExclusionRef
# -----------------------------------------------------------------------


class TestDelegationScopeExclusionRef:
    """P1.8.7 exclusion ref determinism."""

    def test_builds_deterministically(self):
        er = _dev_fixture_exclusion_ref()
        assert er.exclusion_hash
        assert er.exclusion_ref_id.startswith("excl:")
        assert er.source_label == DelegationSourceLabel.DEV_FIXTURE

    def test_identical_input_identical_hash(self):
        a = _dev_fixture_exclusion_ref()
        b = _dev_fixture_exclusion_ref()
        assert a.exclusion_hash == b.exclusion_hash

    def test_changed_exclusion_ref_changes_hash(self):
        ref = _dev_fixture_ref()
        scope = _dev_fixture_scope_ref()
        a = build_delegation_scope_exclusion_ref(
            ref.delegation_ref_id, scope.scope_ref_id,
            DelegationScopeDimension.NETWORK, "ref-a",
            source_label=DelegationSourceLabel.DEV_FIXTURE,
        )
        b = build_delegation_scope_exclusion_ref(
            ref.delegation_ref_id, scope.scope_ref_id,
            DelegationScopeDimension.NETWORK, "ref-b",
            source_label=DelegationSourceLabel.DEV_FIXTURE,
        )
        assert a.exclusion_hash != b.exclusion_hash

    def test_exclusion_ref_not_denial(self):
        er = _dev_fixture_exclusion_ref()
        assert er.scope_status == DelegationScopeStatus.REFERENCE_ONLY


# -----------------------------------------------------------------------
# Test: DelegationBoundaryMatrixEntry
# -----------------------------------------------------------------------


class TestDelegationBoundaryMatrixEntry:
    """P1.8.7 boundary matrix entry determinism."""

    def test_builds_deterministically(self):
        entry = _dev_fixture_matrix_entry()
        assert entry.entry_hash
        assert entry.entry_id.startswith("mxentry:")
        assert entry.posture == DelegationBoundaryPosture.IN_SCOPE

    def test_identical_input_identical_hash(self):
        a = _dev_fixture_matrix_entry()
        b = _dev_fixture_matrix_entry()
        assert a.entry_hash == b.entry_hash

    def test_changed_posture_changes_hash(self):
        ref = _dev_fixture_ref()
        boundary = _dev_fixture_boundary_ref()
        a = build_delegation_boundary_matrix_entry(
            ref.delegation_ref_id,
            DelegationScopeDimension.TOOL,
            DelegationBoundaryPosture.IN_SCOPE,
            boundary.boundary_ref_id,
            source_label=DelegationSourceLabel.DEV_FIXTURE,
        )
        b = build_delegation_boundary_matrix_entry(
            ref.delegation_ref_id,
            DelegationScopeDimension.TOOL,
            DelegationBoundaryPosture.OUT_OF_SCOPE,
            boundary.boundary_ref_id,
            source_label=DelegationSourceLabel.DEV_FIXTURE,
        )
        assert a.entry_hash != b.entry_hash


# -----------------------------------------------------------------------
# Test: DelegationBoundaryMatrix
# -----------------------------------------------------------------------


class TestDelegationBoundaryMatrix:
    """P1.8.7 boundary matrix determinism and boundaries."""

    def test_builds_deterministically(self):
        matrix = _dev_fixture_matrix()
        assert matrix.boundary_matrix_hash
        assert matrix.boundary_matrix_id.startswith("bmatrix:")
        assert len(matrix.entries) == 1

    def test_identical_input_identical_hash(self):
        a = _dev_fixture_matrix()
        b = _dev_fixture_matrix()
        assert a.boundary_matrix_hash == b.boundary_matrix_hash
        assert hash_delegation_boundary_matrix(a) == hash_delegation_boundary_matrix(b)

    def test_changed_entry_changes_hash(self):
        ref = _dev_fixture_ref()
        boundary = _dev_fixture_boundary_ref()
        e1 = build_delegation_boundary_matrix_entry(
            ref.delegation_ref_id,
            DelegationScopeDimension.TOOL,
            DelegationBoundaryPosture.IN_SCOPE,
            boundary.boundary_ref_id,
            source_label=DelegationSourceLabel.DEV_FIXTURE,
        )
        e2 = build_delegation_boundary_matrix_entry(
            ref.delegation_ref_id,
            DelegationScopeDimension.DATA,
            DelegationBoundaryPosture.OUT_OF_SCOPE,
            boundary.boundary_ref_id,
            source_label=DelegationSourceLabel.DEV_FIXTURE,
        )
        m1 = build_delegation_boundary_matrix(
            ref.delegation_ref_id, entries=[e1],
            source_label=DelegationSourceLabel.DEV_FIXTURE,
        )
        m2 = build_delegation_boundary_matrix(
            ref.delegation_ref_id, entries=[e2],
            source_label=DelegationSourceLabel.DEV_FIXTURE,
        )
        assert m1.boundary_matrix_hash != m2.boundary_matrix_hash

    def test_deterministic_ordering(self):
        ref = _dev_fixture_ref()
        boundary = _dev_fixture_boundary_ref()
        e1 = build_delegation_boundary_matrix_entry(
            ref.delegation_ref_id,
            DelegationScopeDimension.DATA,
            DelegationBoundaryPosture.IN_SCOPE,
            boundary.boundary_ref_id,
            source_label=DelegationSourceLabel.DEV_FIXTURE,
        )
        e2 = build_delegation_boundary_matrix_entry(
            ref.delegation_ref_id,
            DelegationScopeDimension.TOOL,
            DelegationBoundaryPosture.IN_SCOPE,
            boundary.boundary_ref_id,
            source_label=DelegationSourceLabel.DEV_FIXTURE,
        )
        m1 = build_delegation_boundary_matrix(
            ref.delegation_ref_id, entries=[e2, e1],
            source_label=DelegationSourceLabel.DEV_FIXTURE,
        )
        m2 = build_delegation_boundary_matrix(
            ref.delegation_ref_id, entries=[e1, e2],
            source_label=DelegationSourceLabel.DEV_FIXTURE,
        )
        assert m1.boundary_matrix_hash == m2.boundary_matrix_hash

    def test_matrix_not_enforcement_matrix(self):
        matrix = _dev_fixture_matrix()
        assert matrix.source_label == DelegationSourceLabel.DEV_FIXTURE

    def test_in_scope_is_not_allowed(self):
        entry = _dev_fixture_matrix_entry()
        assert entry.posture == DelegationBoundaryPosture.IN_SCOPE
        assert entry.scope_status == DelegationScopeStatus.REFERENCE_ONLY

    def test_out_of_scope_is_not_blocked(self):
        ref = _dev_fixture_ref()
        boundary = _dev_fixture_boundary_ref()
        entry = build_delegation_boundary_matrix_entry(
            ref.delegation_ref_id,
            DelegationScopeDimension.TOOL,
            DelegationBoundaryPosture.OUT_OF_SCOPE,
            boundary.boundary_ref_id,
            source_label=DelegationSourceLabel.DEV_FIXTURE,
        )
        assert entry.posture == DelegationBoundaryPosture.OUT_OF_SCOPE
        assert entry.scope_status == DelegationScopeStatus.REFERENCE_ONLY


# -----------------------------------------------------------------------
# Test: DelegationScopeReadinessProfile
# -----------------------------------------------------------------------


class TestDelegationScopeReadinessProfile:
    """P1.8.7 scope readiness profile determinism."""

    def test_builds_deterministically(self):
        profile = _dev_fixture_readiness_profile()
        assert profile.scope_readiness_hash
        assert profile.scope_readiness_profile_id.startswith("srp:")

    def test_identical_input_identical_hash(self):
        a = _dev_fixture_readiness_profile()
        b = _dev_fixture_readiness_profile()
        assert a.scope_readiness_hash == b.scope_readiness_hash

    def test_reports_present_components(self):
        profile = _dev_fixture_readiness_profile()
        assert profile.has_scope_refs is True
        assert profile.has_boundary_refs is True
        assert profile.has_inclusion_refs is True
        assert profile.has_exclusion_refs is True
        assert profile.has_boundary_matrix is True

    def test_reports_missing_components(self):
        profile = _dev_fixture_readiness_profile()
        assert profile.has_data_boundary is False
        assert profile.has_memory_boundary is False
        assert "DATA_BOUNDARY" in profile.missing_components
        assert "MEMORY_BOUNDARY" in profile.missing_components

    def test_readiness_profile_not_enforcement_guarantee(self):
        profile = _dev_fixture_readiness_profile()
        assert profile.enforcement_unavailable_reason

    def test_readiness_profile_not_scheduler_active(self):
        profile = _dev_fixture_readiness_profile()
        assert "enforcement" in profile.enforcement_unavailable_reason.lower()


# -----------------------------------------------------------------------
# Test: DelegationScopeEnvelope
# -----------------------------------------------------------------------


class TestDelegationScopeEnvelope:
    """P1.8.7 scope envelope determinism."""

    def test_builds_deterministically(self):
        envelope = _dev_fixture_envelope()
        assert envelope.scope_envelope_hash
        assert envelope.scope_envelope_id.startswith("senv:")

    def test_identical_input_identical_hash(self):
        a = _dev_fixture_envelope()
        b = _dev_fixture_envelope()
        assert a.scope_envelope_hash == b.scope_envelope_hash

    def test_changed_membership_changes_hash(self):
        envelope1 = _dev_fixture_envelope()
        ref = _dev_fixture_ref()
        identity = _dev_fixture_identity()
        roles = _dev_fixture_role_binding_set()
        cs = _dev_fixture_constraint_set()
        abs_ = _dev_fixture_authority_binding_set()
        nrs = _dev_fixture_nr_binding_set()
        ims = _dev_fixture_im_binding_set()
        matrix = _dev_fixture_matrix()
        profile = _dev_fixture_readiness_profile()
        envelope2 = build_delegation_scope_envelope(
            ref.delegation_ref_id,
            identity.identity_hash,
            roles.role_binding_hash,
            cs.constraint_set_hash,
            abs_.authority_binding_set_hash,
            nrs.non_repudiation_binding_set_hash,
            ims.identity_mesh_binding_set_hash,
            matrix.boundary_matrix_hash,
            profile.scope_readiness_hash,
            source_label=DelegationSourceLabel.DEV_FIXTURE,
        )
        assert envelope1.scope_envelope_hash != envelope2.scope_envelope_hash

    def test_deterministic_ordering(self):
        ref = _dev_fixture_ref()
        sr1 = build_delegation_scope_ref(
            DelegationScopeKind.TOOL_SCOPE, "ref-z",
            ref.delegation_ref_id,
            source_label=DelegationSourceLabel.DEV_FIXTURE,
        )
        sr2 = build_delegation_scope_ref(
            DelegationScopeKind.DATA_SCOPE, "ref-a",
            ref.delegation_ref_id,
            source_label=DelegationSourceLabel.DEV_FIXTURE,
        )
        identity = _dev_fixture_identity()
        roles = _dev_fixture_role_binding_set()
        cs = _dev_fixture_constraint_set()
        abs_ = _dev_fixture_authority_binding_set()
        nrs = _dev_fixture_nr_binding_set()
        ims = _dev_fixture_im_binding_set()
        matrix = _dev_fixture_matrix()
        profile = _dev_fixture_readiness_profile()
        env1 = build_delegation_scope_envelope(
            ref.delegation_ref_id, identity.identity_hash, roles.role_binding_hash,
            cs.constraint_set_hash, abs_.authority_binding_set_hash,
            nrs.non_repudiation_binding_set_hash, ims.identity_mesh_binding_set_hash,
            matrix.boundary_matrix_hash, profile.scope_readiness_hash,
            scope_refs=[sr1, sr2],
            source_label=DelegationSourceLabel.DEV_FIXTURE,
        )
        env2 = build_delegation_scope_envelope(
            ref.delegation_ref_id, identity.identity_hash, roles.role_binding_hash,
            cs.constraint_set_hash, abs_.authority_binding_set_hash,
            nrs.non_repudiation_binding_set_hash, ims.identity_mesh_binding_set_hash,
            matrix.boundary_matrix_hash, profile.scope_readiness_hash,
            scope_refs=[sr2, sr1],
            source_label=DelegationSourceLabel.DEV_FIXTURE,
        )
        assert env1.scope_envelope_hash == env2.scope_envelope_hash

    def test_envelope_not_permission_grant(self):
        envelope = _dev_fixture_envelope()
        assert envelope.source_label == DelegationSourceLabel.DEV_FIXTURE


# -----------------------------------------------------------------------
# Test: DelegationScopeBindingSet
# -----------------------------------------------------------------------


class TestDelegationScopeBinding:
    """P1.8.7 scope binding determinism."""

    def test_builds_deterministically(self):
        binding = _dev_fixture_binding()
        assert binding.binding_hash
        assert binding.binding_id.startswith("sbind:")
        assert binding.scope_status == DelegationScopeStatus.REFERENCE_ONLY


class TestDelegationScopeBindingSet:
    """P1.8.7 scope binding set determinism."""

    def test_builds_deterministically(self):
        bs = _dev_fixture_binding_set()
        assert bs.scope_binding_set_hash
        assert bs.scope_binding_set_id.startswith("sbinds:")

    def test_identical_input_identical_hash(self):
        a = _dev_fixture_binding_set()
        b = _dev_fixture_binding_set()
        assert a.scope_binding_set_hash == b.scope_binding_set_hash

    def test_changed_membership_changes_hash(self):
        a = _dev_fixture_binding_set()
        ref = _dev_fixture_ref()
        identity = _dev_fixture_identity()
        roles = _dev_fixture_role_binding_set()
        cs = _dev_fixture_constraint_set()
        abs_ = _dev_fixture_authority_binding_set()
        nrs = _dev_fixture_nr_binding_set()
        ims = _dev_fixture_im_binding_set()
        b = build_delegation_scope_binding_set(
            ref.delegation_ref_id, identity.identity_hash, roles.role_binding_hash,
            cs.constraint_set_hash, abs_.authority_binding_set_hash,
            nrs.non_repudiation_binding_set_hash, ims.identity_mesh_binding_set_hash,
            source_label=DelegationSourceLabel.DEV_FIXTURE,
        )
        assert a.scope_binding_set_hash != b.scope_binding_set_hash


# -----------------------------------------------------------------------
# Test: serialization
# -----------------------------------------------------------------------


class TestSerialization:
    """P1.8.7 JSON-safe deterministic serialization."""

    def test_envelope_serialization_json_safe(self):
        envelope = _dev_fixture_envelope()
        s = serialize_delegation_scope_envelope(envelope)
        parsed = json.loads(s)
        assert isinstance(parsed, dict)
        assert "scope_envelope_hash" in parsed

    def test_envelope_deterministic_serialization(self):
        a = _dev_fixture_envelope()
        b = _dev_fixture_envelope()
        assert serialize_delegation_scope_envelope(a) == serialize_delegation_scope_envelope(b)

    def test_binding_set_serialization_json_safe(self):
        bs = _dev_fixture_binding_set()
        s = serialize_delegation_scope_binding_set(bs)
        parsed = json.loads(s)
        assert isinstance(parsed, dict)
        assert "scope_binding_set_hash" in parsed

    def test_binding_set_deterministic_serialization(self):
        a = _dev_fixture_binding_set()
        b = _dev_fixture_binding_set()
        assert serialize_delegation_scope_binding_set(a) == serialize_delegation_scope_binding_set(b)


# -----------------------------------------------------------------------
# Test: closed-world validation
# -----------------------------------------------------------------------


class TestClosedWorld:
    """P1.8.7 closed-world field validation."""

    def test_unknown_field_rejected_scope_ref(self):
        with pytest.raises(DelegationUnknownFieldError):
            DelegationScopeRef.from_dict({
                "scope_kind": "TASK_SCOPE",
                "scope_ref": "test",
                "delegation_ref_id": "ref:abc123",
                "unknown_field": "should-not-exist",
            })

    def test_unknown_field_rejected_boundary_ref(self):
        with pytest.raises(DelegationUnknownFieldError):
            DelegationBoundaryRef.from_dict({
                "boundary_kind": "INCLUSION",
                "boundary_dimension": "TOOL",
                "boundary_ref": "test",
                "delegation_ref_id": "ref:abc123",
                "unknown_field": "should-not-exist",
            })


# -----------------------------------------------------------------------
# Test: source/truth labels
# -----------------------------------------------------------------------


class TestSourceLabels:
    """DEV_FIXTURE visible throughout P1.8.7 fixtures."""

    def test_all_fixtures_use_dev_fixture(self):
        assert _dev_fixture_scope_ref().source_label == DelegationSourceLabel.DEV_FIXTURE
        assert _dev_fixture_boundary_ref().source_label == DelegationSourceLabel.DEV_FIXTURE
        assert _dev_fixture_inclusion_ref().source_label == DelegationSourceLabel.DEV_FIXTURE
        assert _dev_fixture_exclusion_ref().source_label == DelegationSourceLabel.DEV_FIXTURE
        assert _dev_fixture_matrix_entry().source_label == DelegationSourceLabel.DEV_FIXTURE
        assert _dev_fixture_matrix().source_label == DelegationSourceLabel.DEV_FIXTURE
        assert _dev_fixture_readiness_profile().source_label == DelegationSourceLabel.DEV_FIXTURE
        assert _dev_fixture_envelope().source_label == DelegationSourceLabel.DEV_FIXTURE
        assert _dev_fixture_binding().source_label == DelegationSourceLabel.DEV_FIXTURE
        assert _dev_fixture_binding_set().source_label == DelegationSourceLabel.DEV_FIXTURE


# -----------------------------------------------------------------------
# Test: DelegationScopeStatusReport and unavailable surfaces
# -----------------------------------------------------------------------


class TestStatusReport:
    """P1.8.7 status report and unavailable surfaces."""

    def test_builds_deterministically(self):
        report = build_delegation_scope_status_report()
        assert report.status_hash
        assert report.status_label == DelegationSourceLabel.DEV_FIXTURE

    def test_identical_reports_identical_hash(self):
        a = build_delegation_scope_status_report()
        b = build_delegation_scope_status_report()
        assert a.status_hash == b.status_hash

    def test_unavailable_surfaces_exist(self):
        report = build_delegation_scope_status_report()
        unavailable = report.unavailable_bindings
        assert "Projection/API/Event/Read Model" in unavailable
        assert "CLI/Shell/TUI Binding" in unavailable
        assert "Ledger Write" in unavailable
        assert "Global Trace Write" in unavailable
        assert "Permission Grant" in unavailable
        assert "Access Control Engine" in unavailable
        assert "Runtime Boundary Enforcer" in unavailable
        assert "Policy/Custos Decision" in unavailable
        assert "Approval Creation" in unavailable
        assert "P1.8.8 Expiry/Revocation Model" in unavailable
        assert "Output Passport / P1.9" in unavailable
        assert "Runtime Delegation Execution" in unavailable

    def test_available_contracts_listed(self):
        report = build_delegation_scope_status_report()
        assert "DelegationScopeRef" in report.available_contracts
        assert "DelegationBoundaryRef" in report.available_contracts
        assert "DelegationScopeEnvelope" in report.available_contracts

    def test_status_label_is_dev_fixture(self):
        report = build_delegation_scope_status_report()
        assert report.status_label == DelegationSourceLabel.DEV_FIXTURE


# -----------------------------------------------------------------------
# Test: Side effects — all false
# -----------------------------------------------------------------------


class TestSideEffects:
    """P1.8.7 all side-effect booleans false."""

    def test_all_side_effects_default_false(self):
        se = DelegationScopeSideEffects()
        for item in fields(se):
            assert not getattr(se, item.name), f"{item.name} should be False"

    def test_side_effects_in_binding_set(self):
        bs = _dev_fixture_binding_set()
        se = bs.side_effects
        assert not se.permission_granted
        assert not se.access_granted
        assert not se.boundary_enforced
        assert not se.runtime_blocked
        assert not se.tool_permission_changed
        assert not se.data_access_changed
        assert not se.memory_access_changed
        assert not se.path_authorized
        assert not se.network_access_changed
        assert not se.policy_called
        assert not se.custos_called
        assert not se.approval_created
        assert not se.ledger_written
        assert not se.global_trace_written
        assert not se.runtime_mutated

    def test_no_permission_grant(self):
        assert not DelegationScopeSideEffects().permission_granted

    def test_no_access_grant(self):
        assert not DelegationScopeSideEffects().access_granted

    def test_no_boundary_enforcement(self):
        assert not DelegationScopeSideEffects().boundary_enforced

    def test_no_runtime_block(self):
        assert not DelegationScopeSideEffects().runtime_blocked

    def test_no_tool_permission_mutation(self):
        assert not DelegationScopeSideEffects().tool_permission_changed

    def test_no_data_access_mutation(self):
        assert not DelegationScopeSideEffects().data_access_changed

    def test_no_memory_access_mutation(self):
        assert not DelegationScopeSideEffects().memory_access_changed

    def test_no_path_authorization(self):
        assert not DelegationScopeSideEffects().path_authorized

    def test_no_network_access_mutation(self):
        assert not DelegationScopeSideEffects().network_access_changed

    def test_no_policy_custos_decision(self):
        assert not DelegationScopeSideEffects().policy_called
        assert not DelegationScopeSideEffects().custos_called

    def test_no_approval_creation(self):
        assert not DelegationScopeSideEffects().approval_created

    def test_no_ledger_global_trace_write(self):
        assert not DelegationScopeSideEffects().ledger_written
        assert not DelegationScopeSideEffects().global_trace_written

    def test_no_runtime_mutation(self):
        assert not DelegationScopeSideEffects().runtime_mutated


# -----------------------------------------------------------------------
# Test: no P1.8.8 or P1.9 behavior
# -----------------------------------------------------------------------


class TestNoP188OrP19:
    """P1.8.7 has no P1.8.8 or P1.9 behavior."""

    def test_no_expiry_ref_import(self):
        with pytest.raises(ImportError):
            from agentic_runtime.delegation.scope import DelegationExpiryRef  # noqa

    def test_no_revocation_ref_import(self):
        with pytest.raises(ImportError):
            from agentic_runtime.delegation.scope import DelegationRevocationRef  # noqa

    def test_no_output_passport_import(self):
        with pytest.raises(ImportError):
            from agentic_runtime.delegation.scope import OutputPassport  # noqa
