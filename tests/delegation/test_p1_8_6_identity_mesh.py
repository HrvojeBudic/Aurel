"""P1.8.6 — AgentIdentityMeshRef Binding / Mesh Hook tests."""
from __future__ import annotations

import json
from dataclasses import fields

import pytest

from agentic_runtime.delegation.foundation import (
    DelegationActorKind,
    DelegationAuthorityKind,
    DelegationConstraintKind,
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
    DelegationIdentityMeshSideEffects,
    DelegationIdentityMeshStatusReport,
    DelegationMeshParticipantKind,
    DelegationMeshParticipantRef,
    DelegationMeshRefStatus,
    DelegationMeshRelationshipKind,
    DelegationMeshRelationshipMap,
    DelegationMeshRelationshipRef,
    DelegationMeshResolutionReadinessProfile,
    DelegationMeshResolutionStatus,
    DelegationMeshScopeKind,
    DelegationMeshScopeRef,
    DelegationRoleKind,
    DelegationSourceLabel,
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
    build_delegation_identity_mesh_status_report,
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
    hash_delegation_identity_mesh_binding,
    hash_delegation_identity_mesh_binding_set,
    hash_delegation_identity_mesh_envelope,
    hash_delegation_mesh_participant_ref,
    hash_delegation_mesh_relationship_map,
    hash_delegation_mesh_relationship_ref,
    hash_delegation_mesh_resolution_readiness_profile,
    hash_delegation_mesh_scope_ref,
    serialize_delegation_identity_mesh_binding,
    serialize_delegation_identity_mesh_binding_set,
    serialize_delegation_identity_mesh_envelope,
    serialize_delegation_mesh_participant_ref,
    serialize_delegation_mesh_relationship_map,
    serialize_delegation_mesh_relationship_ref,
    serialize_delegation_mesh_resolution_readiness_profile,
    serialize_delegation_mesh_scope_ref,
)

from agentic_runtime.delegation.identity_mesh import (
    DelegationValidationError,
    DelegationUnknownFieldError,
)

DEV_FIXTURE_CREATED_AT = "2026-06-27T00:00:00Z"


# -----------------------------------------------------------------------
# DEV_FIXTURE builder chain (exact pattern from P1.8.5)
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


def _dev_fixture_non_repudiation_binding_set():
    """P1.8.5 DEV_FIXTURE DelegationNonRepudiationBindingSet."""
    ref = _dev_fixture_ref()
    identity = _dev_fixture_identity()
    roles = _dev_fixture_role_binding_set()
    constraints = _dev_fixture_constraint_set()
    auth_set = _dev_fixture_authority_binding_set()
    nb = build_delegation_non_repudiation_binding(
        delegation_ref_id=ref.delegation_ref_id,
        delegation_identity_hash=identity.identity_hash,
        role_binding_hash=roles.role_binding_hash,
        constraint_set_hash=constraints.constraint_set_hash,
        authority_binding_set_hash=auth_set.authority_binding_set_hash,
        evidence_envelope_hash="evenv:0000000000000000",
        completeness_profile_hash="cmpprof:0000000000000000",
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    return build_delegation_non_repudiation_binding_set(
        delegation_ref_id=ref.delegation_ref_id,
        delegation_identity_hash=identity.identity_hash,
        role_binding_hash=roles.role_binding_hash,
        constraint_set_hash=constraints.constraint_set_hash,
        authority_binding_set_hash=auth_set.authority_binding_set_hash,
        bindings=[nb],
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )


# -----------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------


class TestImports:
    def test_imports_work_from_agentic_runtime_delegation(self):
        """Test 1: Imports work from agentic_runtime.delegation."""
        from agentic_runtime.delegation import (
            DelegationMeshParticipantKind,
            DelegationMeshParticipantRef,
            DelegationIdentityMeshEnvelope,
            DelegationMeshResolutionReadinessProfile,
            DelegationMeshRelationshipMap,
            DelegationIdentityMeshBinding,
            DelegationIdentityMeshBindingSet,
            DelegationIdentityMeshSideEffects,
            DelegationIdentityMeshStatusReport,
        )
        assert True

    def test_existing_p1_8_0_thru_p1_8_5_exports_remain_importable(self):
        """Test 2: Existing P1.8.0-P1.8.5 exports remain importable."""
        from agentic_runtime.delegation import (
            DelegationRecord,
            DelegationRef,
            DelegationRoleBindingSet,
            DelegationConstraintSet,
            DelegationAuthorityBindingSet,
            DelegationNonRepudiationBindingSet,
        )
        assert True


# -----------------------------------------------------------------------
# DelegationMeshParticipantRef
# -----------------------------------------------------------------------


class TestDelegationMeshParticipantRef:
    def test_builds_deterministically(self):
        """Test 4: DelegationMeshParticipantRef builds deterministically."""
        a = build_delegation_mesh_participant_ref(
            delegation_ref_id="dref:abc123",
            participant_kind=DelegationMeshParticipantKind.OPERATOR_REF,
            participant_ref="operator/hrv",
            participant_label="hrv",
        )
        b = build_delegation_mesh_participant_ref(
            delegation_ref_id="dref:abc123",
            participant_kind=DelegationMeshParticipantKind.OPERATOR_REF,
            participant_ref="operator/hrv",
            participant_label="hrv",
        )
        assert a.participant_hash == b.participant_hash
        assert a.participant_ref_id == b.participant_ref_id

    def test_identical_input_gives_identical_hash(self):
        """Test 13: Identical participant input gives identical participant_hash."""
        a = DelegationMeshParticipantRef(
            delegation_ref_id="dref:x",
            participant_kind=DelegationMeshParticipantKind.AGENT_REF,
            participant_ref="agent/aurel",
            participant_label="aurel",
        )
        b = DelegationMeshParticipantRef(
            delegation_ref_id="dref:x",
            participant_kind=DelegationMeshParticipantKind.AGENT_REF,
            participant_ref="agent/aurel",
            participant_label="aurel",
        )
        assert a.participant_hash == b.participant_hash

    def test_changed_kind_changes_hash(self):
        """Test 14: Changed participant kind changes participant_hash."""
        a = build_delegation_mesh_participant_ref(
            delegation_ref_id="dref:x",
            participant_kind=DelegationMeshParticipantKind.OPERATOR_REF,
            participant_ref="ref",
            participant_label="label",
        )
        b = build_delegation_mesh_participant_ref(
            delegation_ref_id="dref:x",
            participant_kind=DelegationMeshParticipantKind.AGENT_REF,
            participant_ref="ref",
            participant_label="label",
        )
        assert a.participant_hash != b.participant_hash

    def test_changed_ref_changes_hash(self):
        """Changed participant_ref changes participant_hash."""
        a = build_delegation_mesh_participant_ref(
            delegation_ref_id="dref:x",
            participant_kind=DelegationMeshParticipantKind.AGENT_REF,
            participant_ref="agent/a",
            participant_label="label",
        )
        b = build_delegation_mesh_participant_ref(
            delegation_ref_id="dref:x",
            participant_kind=DelegationMeshParticipantKind.AGENT_REF,
            participant_ref="agent/b",
            participant_label="label",
        )
        assert a.participant_hash != b.participant_hash

    def test_changed_label_changes_hash(self):
        """Changed participant_label changes participant_hash."""
        a = build_delegation_mesh_participant_ref(
            delegation_ref_id="dref:x",
            participant_kind=DelegationMeshParticipantKind.AGENT_REF,
            participant_ref="agent/a",
            participant_label="label-a",
        )
        b = build_delegation_mesh_participant_ref(
            delegation_ref_id="dref:x",
            participant_kind=DelegationMeshParticipantKind.AGENT_REF,
            participant_ref="agent/a",
            participant_label="label-b",
        )
        assert a.participant_hash != b.participant_hash

    def test_is_not_identity_authentication(self):
        """ParticipantRef is not identity authentication."""
        pr = build_delegation_mesh_participant_ref(
            delegation_ref_id="dref:x",
            participant_kind=DelegationMeshParticipantKind.OPERATOR_REF,
            participant_ref="operator/hrv",
            participant_label="hrv",
        )
        assert pr.mesh_ref_status == DelegationMeshRefStatus.REFERENCE_ONLY

    def test_default_source_label_is_dev_fixture(self):
        """Test 34: Source/truth labels are visible."""
        pr = build_delegation_mesh_participant_ref(
            delegation_ref_id="dref:x",
            participant_kind=DelegationMeshParticipantKind.SYSTEM_REF,
            participant_ref="system/pipeline",
            participant_label="pipeline",
        )
        assert pr.source_label == DelegationSourceLabel.DEV_FIXTURE

    def test_all_participant_kinds_usable(self):
        kinds = list(DelegationMeshParticipantKind)
        for kind in kinds:
            pr = build_delegation_mesh_participant_ref(
                delegation_ref_id="dref:x",
                participant_kind=kind,
                participant_ref=f"ref/{kind.value}",
                participant_label="test",
            )
            assert pr.participant_kind == kind

    def test_serialization_is_json_safe_and_deterministic(self):
        """Test 32: Serialization is JSON-safe and deterministic."""
        pr = build_delegation_mesh_participant_ref(
            delegation_ref_id="dref:json",
            participant_kind=DelegationMeshParticipantKind.ROLE_REF,
            participant_ref="role/admin",
            participant_label="admin role",
        )
        s = serialize_delegation_mesh_participant_ref(pr)
        d = json.loads(s)
        assert d["participant_kind"] == "ROLE_REF"
        assert d["participant_ref"] == "role/admin"
        s2 = serialize_delegation_mesh_participant_ref(pr)
        assert s == s2

    def test_closed_world_validation_rejects_unknown_fields(self):
        """Test 33: Closed-world validation rejects unknown fields."""
        with pytest.raises(DelegationUnknownFieldError):
            DelegationMeshParticipantRef.from_dict({
                "delegation_ref_id": "dref:x",
                "participant_kind": "AGENT_REF",
                "participant_ref": "agent/x",
                "participant_label": "x",
                "unknown_field": "bad",
            })


# -----------------------------------------------------------------------
# DelegationMeshRelationshipRef
# -----------------------------------------------------------------------


class TestDelegationMeshRelationshipRef:
    def test_builds_deterministically(self):
        """Test 5: DelegationMeshRelationshipRef builds deterministically."""
        a = build_delegation_mesh_relationship_ref(
            delegation_ref_id="dref:abc",
            relationship_kind=DelegationMeshRelationshipKind.DELEGATOR_TO_DELEGATE,
            from_participant_ref_id="mpr:aaaa",
            to_participant_ref_id="mpr:bbbb",
        )
        b = build_delegation_mesh_relationship_ref(
            delegation_ref_id="dref:abc",
            relationship_kind=DelegationMeshRelationshipKind.DELEGATOR_TO_DELEGATE,
            from_participant_ref_id="mpr:aaaa",
            to_participant_ref_id="mpr:bbbb",
        )
        assert a.relationship_hash == b.relationship_hash

    def test_changed_kind_changes_hash(self):
        """Test 15: Changed relationship kind changes relationship_hash."""
        a = build_delegation_mesh_relationship_ref(
            delegation_ref_id="dref:x",
            relationship_kind=DelegationMeshRelationshipKind.DELEGATOR_TO_DELEGATE,
            from_participant_ref_id="mpr:a",
            to_participant_ref_id="mpr:b",
        )
        b = build_delegation_mesh_relationship_ref(
            delegation_ref_id="dref:x",
            relationship_kind=DelegationMeshRelationshipKind.AGENT_TO_SERVICE,
            from_participant_ref_id="mpr:a",
            to_participant_ref_id="mpr:b",
        )
        assert a.relationship_hash != b.relationship_hash

    def test_changed_participants_changes_hash(self):
        """Changed from/to participant refs change relationship_hash."""
        a = build_delegation_mesh_relationship_ref(
            delegation_ref_id="dref:x",
            relationship_kind=DelegationMeshRelationshipKind.REFERENCE_ONLY,
            from_participant_ref_id="mpr:a",
            to_participant_ref_id="mpr:b",
        )
        b = build_delegation_mesh_relationship_ref(
            delegation_ref_id="dref:x",
            relationship_kind=DelegationMeshRelationshipKind.REFERENCE_ONLY,
            from_participant_ref_id="mpr:a",
            to_participant_ref_id="mpr:c",
        )
        assert a.relationship_hash != b.relationship_hash

    def test_changed_context_changes_hash(self):
        """Changed relationship_context_ref changes relationship_hash."""
        a = build_delegation_mesh_relationship_ref(
            delegation_ref_id="dref:x",
            relationship_kind=DelegationMeshRelationshipKind.ROLE_TO_AGENT,
            from_participant_ref_id="mpr:a",
            to_participant_ref_id="mpr:b",
            relationship_context_ref="ctx/audit",
        )
        b = build_delegation_mesh_relationship_ref(
            delegation_ref_id="dref:x",
            relationship_kind=DelegationMeshRelationshipKind.ROLE_TO_AGENT,
            from_participant_ref_id="mpr:a",
            to_participant_ref_id="mpr:b",
            relationship_context_ref="ctx/runtime",
        )
        assert a.relationship_hash != b.relationship_hash

    def test_is_not_trust_verification(self):
        """RelationshipRef is not trust verification."""
        r = build_delegation_mesh_relationship_ref(
            delegation_ref_id="dref:x",
            relationship_kind=DelegationMeshRelationshipKind.REFERENCE_ONLY,
            from_participant_ref_id="mpr:a",
            to_participant_ref_id="mpr:b",
        )
        assert r.mesh_ref_status == DelegationMeshRefStatus.REFERENCE_ONLY


# -----------------------------------------------------------------------
# DelegationMeshScopeRef
# -----------------------------------------------------------------------


class TestDelegationMeshScopeRef:
    def test_builds_deterministically(self):
        """Test 6: DelegationMeshScopeRef builds deterministically."""
        a = build_delegation_mesh_scope_ref(
            delegation_ref_id="dref:abc",
            mesh_scope_kind=DelegationMeshScopeKind.DELEGATION_LOCAL,
            mesh_scope_ref="delegations/audit-001",
        )
        b = build_delegation_mesh_scope_ref(
            delegation_ref_id="dref:abc",
            mesh_scope_kind=DelegationMeshScopeKind.DELEGATION_LOCAL,
            mesh_scope_ref="delegations/audit-001",
        )
        assert a.mesh_scope_hash == b.mesh_scope_hash

    def test_changed_scope_changes_hash(self):
        """Test 16: Changed mesh scope changes mesh_scope_hash."""
        a = build_delegation_mesh_scope_ref(
            delegation_ref_id="dref:x",
            mesh_scope_kind=DelegationMeshScopeKind.DELEGATION_LOCAL,
            mesh_scope_ref="scope/a",
        )
        b = build_delegation_mesh_scope_ref(
            delegation_ref_id="dref:x",
            mesh_scope_kind=DelegationMeshScopeKind.AGENT_LOCAL,
            mesh_scope_ref="scope/a",
        )
        assert a.mesh_scope_hash != b.mesh_scope_hash

    def test_is_not_permission_scope(self):
        """Test 28: MeshScopeRef is not permission scope."""
        ms = build_delegation_mesh_scope_ref(
            delegation_ref_id="dref:x",
            mesh_scope_kind=DelegationMeshScopeKind.DELEGATION_LOCAL,
            mesh_scope_ref="scope/x",
        )
        assert ms.mesh_ref_status == DelegationMeshRefStatus.REFERENCE_ONLY


# -----------------------------------------------------------------------
# DelegationIdentityMeshEnvelope
# -----------------------------------------------------------------------


class TestDelegationIdentityMeshEnvelope:
    def test_builds_deterministically(self):
        """Test 7: DelegationIdentityMeshEnvelope builds deterministically."""
        a = build_delegation_identity_mesh_envelope(
            delegation_ref_id="dref:env",
            delegation_identity_hash="idhash:aaa",
            role_binding_hash="rbhash:aaa",
            constraint_set_hash="cshash:aaa",
            authority_binding_set_hash="abshash:aaa",
            non_repudiation_binding_set_hash="nrbshash:aaa",
        )
        b = build_delegation_identity_mesh_envelope(
            delegation_ref_id="dref:env",
            delegation_identity_hash="idhash:aaa",
            role_binding_hash="rbhash:aaa",
            constraint_set_hash="cshash:aaa",
            authority_binding_set_hash="abshash:aaa",
            non_repudiation_binding_set_hash="nrbshash:aaa",
        )
        assert a.identity_mesh_envelope_hash == b.identity_mesh_envelope_hash

    def test_identical_envelope_gives_identical_hash(self):
        """Test 17: Identical envelope gives identical hash."""
        pr = build_delegation_mesh_participant_ref(
            delegation_ref_id="dref:e",
            participant_kind=DelegationMeshParticipantKind.OPERATOR_REF,
            participant_ref="op/x",
            participant_label="op",
        )
        a = DelegationIdentityMeshEnvelope(
            delegation_ref_id="dref:e",
            delegation_identity_hash="i:a",
            role_binding_hash="rb:a",
            constraint_set_hash="cs:a",
            authority_binding_set_hash="abs:a",
            non_repudiation_binding_set_hash="nbs:a",
            participant_refs=(pr,),
        )
        b = DelegationIdentityMeshEnvelope(
            delegation_ref_id="dref:e",
            delegation_identity_hash="i:a",
            role_binding_hash="rb:a",
            constraint_set_hash="cs:a",
            authority_binding_set_hash="abs:a",
            non_repudiation_binding_set_hash="nbs:a",
            participant_refs=(pr,),
        )
        assert a.identity_mesh_envelope_hash == b.identity_mesh_envelope_hash

    def test_changed_participant_membership_changes_hash(self):
        """Test 18: Changed participant membership changes hash."""
        pr1 = build_delegation_mesh_participant_ref(
            delegation_ref_id="dref:e",
            participant_kind=DelegationMeshParticipantKind.OPERATOR_REF,
            participant_ref="op/x",
            participant_label="op",
        )
        pr2 = build_delegation_mesh_participant_ref(
            delegation_ref_id="dref:e",
            participant_kind=DelegationMeshParticipantKind.AGENT_REF,
            participant_ref="agent/y",
            participant_label="y",
        )
        a = DelegationIdentityMeshEnvelope(
            delegation_ref_id="dref:e",
            delegation_identity_hash="i:a",
            role_binding_hash="rb:a",
            constraint_set_hash="cs:a",
            authority_binding_set_hash="abs:a",
            non_repudiation_binding_set_hash="nbs:a",
            participant_refs=(pr1,),
        )
        b = DelegationIdentityMeshEnvelope(
            delegation_ref_id="dref:e",
            delegation_identity_hash="i:a",
            role_binding_hash="rb:a",
            constraint_set_hash="cs:a",
            authority_binding_set_hash="abs:a",
            non_repudiation_binding_set_hash="nbs:a",
            participant_refs=(pr1, pr2),
        )
        assert a.identity_mesh_envelope_hash != b.identity_mesh_envelope_hash

    def test_changed_relationship_membership_changes_hash(self):
        """Test 19: Changed relationship membership changes hash."""
        rr = build_delegation_mesh_relationship_ref(
            delegation_ref_id="dref:e",
            relationship_kind=DelegationMeshRelationshipKind.REFERENCE_ONLY,
            from_participant_ref_id="mpr:a",
            to_participant_ref_id="mpr:b",
        )
        a = DelegationIdentityMeshEnvelope(
            delegation_ref_id="dref:e",
            delegation_identity_hash="i:a",
            role_binding_hash="rb:a",
            constraint_set_hash="cs:a",
            authority_binding_set_hash="abs:a",
            non_repudiation_binding_set_hash="nbs:a",
            relationship_refs=(),
        )
        b = DelegationIdentityMeshEnvelope(
            delegation_ref_id="dref:e",
            delegation_identity_hash="i:a",
            role_binding_hash="rb:a",
            constraint_set_hash="cs:a",
            authority_binding_set_hash="abs:a",
            non_repudiation_binding_set_hash="nbs:a",
            relationship_refs=(rr,),
        )
        assert a.identity_mesh_envelope_hash != b.identity_mesh_envelope_hash

    def test_ordering_is_deterministic(self):
        """Test 20: Identity mesh envelope ordering is deterministic."""
        pr_a = build_delegation_mesh_participant_ref(
            delegation_ref_id="dref:ord",
            participant_kind=DelegationMeshParticipantKind.OPERATOR_REF,
            participant_ref="op/hrv",
            participant_label="hrv",
        )
        pr_b = build_delegation_mesh_participant_ref(
            delegation_ref_id="dref:ord",
            participant_kind=DelegationMeshParticipantKind.AGENT_REF,
            participant_ref="agent/aurel",
            participant_label="aurel",
        )
        e1 = DelegationIdentityMeshEnvelope(
            delegation_ref_id="dref:ord",
            delegation_identity_hash="i:a",
            role_binding_hash="rb:a",
            constraint_set_hash="cs:a",
            authority_binding_set_hash="abs:a",
            non_repudiation_binding_set_hash="nbs:a",
            participant_refs=(pr_a, pr_b),
        )
        e2 = DelegationIdentityMeshEnvelope(
            delegation_ref_id="dref:ord",
            delegation_identity_hash="i:a",
            role_binding_hash="rb:a",
            constraint_set_hash="cs:a",
            authority_binding_set_hash="abs:a",
            non_repudiation_binding_set_hash="nbs:a",
            participant_refs=(pr_b, pr_a),
        )
        assert e1.identity_mesh_envelope_hash == e2.identity_mesh_envelope_hash

    def test_changed_mesh_scope_changes_envelope_hash(self):
        """Changed mesh scope changes envelope hash."""
        ms_a = build_delegation_mesh_scope_ref(
            delegation_ref_id="dref:e",
            mesh_scope_kind=DelegationMeshScopeKind.DELEGATION_LOCAL,
            mesh_scope_ref="scope/a",
        )
        ms_b = build_delegation_mesh_scope_ref(
            delegation_ref_id="dref:e",
            mesh_scope_kind=DelegationMeshScopeKind.AGENT_LOCAL,
            mesh_scope_ref="scope/b",
        )
        a = DelegationIdentityMeshEnvelope(
            delegation_ref_id="dref:e",
            delegation_identity_hash="i:a",
            role_binding_hash="rb:a",
            constraint_set_hash="cs:a",
            authority_binding_set_hash="abs:a",
            non_repudiation_binding_set_hash="nbs:a",
            mesh_scope_ref=ms_a,
        )
        b = DelegationIdentityMeshEnvelope(
            delegation_ref_id="dref:e",
            delegation_identity_hash="i:a",
            role_binding_hash="rb:a",
            constraint_set_hash="cs:a",
            authority_binding_set_hash="abs:a",
            non_repudiation_binding_set_hash="nbs:a",
            mesh_scope_ref=ms_b,
        )
        assert a.identity_mesh_envelope_hash != b.identity_mesh_envelope_hash

    def test_p1_8_5_nrb_set_can_feed_p1_8_6_identity_mesh_path(self):
        """Test 3: P1.8.5 NonRepudiationBindingSet feeds P1.8.6 identity mesh."""
        nrbs = _dev_fixture_non_repudiation_binding_set()
        pr = build_delegation_mesh_participant_ref(
            delegation_ref_id=nrbs.delegation_ref_id,
            participant_kind=DelegationMeshParticipantKind.OPERATOR_REF,
            participant_ref="operator/hrv",
            participant_label="hrv",
        )
        envelope = build_delegation_identity_mesh_envelope(
            delegation_ref_id=nrbs.delegation_ref_id,
            delegation_identity_hash=nrbs.delegation_identity_hash,
            role_binding_hash=nrbs.role_binding_hash,
            constraint_set_hash=nrbs.constraint_set_hash,
            authority_binding_set_hash=nrbs.authority_binding_set_hash,
            non_repudiation_binding_set_hash=nrbs.non_repudiation_binding_set_hash,
            participant_refs=[pr],
        )
        assert envelope.identity_mesh_envelope_hash


# -----------------------------------------------------------------------
# DelegationMeshResolutionReadinessProfile
# -----------------------------------------------------------------------


class TestDelegationMeshResolutionReadinessProfile:
    def test_builds_deterministically(self):
        """Test 8: ReadinessProfile builds deterministically."""
        a = build_delegation_mesh_resolution_readiness_profile(
            delegation_ref_id="dref:rp",
            identity_mesh_envelope_hash="ime:aaa",
        )
        b = build_delegation_mesh_resolution_readiness_profile(
            delegation_ref_id="dref:rp",
            identity_mesh_envelope_hash="ime:aaa",
        )
        assert a.readiness_hash == b.readiness_hash

    def test_identical_profile_gives_identical_hash(self):
        """Test 21: Identical readiness profile gives identical hash."""
        a = DelegationMeshResolutionReadinessProfile(
            delegation_ref_id="dref:r",
            identity_mesh_envelope_hash="ime:a",
            has_operator_ref=True,
        )
        b = DelegationMeshResolutionReadinessProfile(
            delegation_ref_id="dref:r",
            identity_mesh_envelope_hash="ime:a",
            has_operator_ref=True,
        )
        assert a.readiness_hash == b.readiness_hash

    def test_reports_present_components(self):
        """Test 22: Readiness profile reports present components."""
        rp = DelegationMeshResolutionReadinessProfile(
            delegation_ref_id="dref:r",
            identity_mesh_envelope_hash="ime:a",
            has_operator_ref=True,
            has_agent_ref=True,
            has_relationship_refs=True,
            has_mesh_scope_ref=True,
        )
        assert rp.has_operator_ref is True
        assert rp.has_agent_ref is True
        assert rp.has_relationship_refs is True
        assert rp.has_mesh_scope_ref is True

    def test_reports_missing_components(self):
        """Test 23: Readiness profile reports missing components."""
        rp = DelegationMeshResolutionReadinessProfile(
            delegation_ref_id="dref:r",
            identity_mesh_envelope_hash="ime:a",
            has_operator_ref=False,
            has_agent_ref=False,
            missing_components=["agent_ref", "system_ref"],
        )
        assert rp.has_operator_ref is False
        assert rp.has_agent_ref is False
        assert "agent_ref" in rp.missing_components
        assert "system_ref" in rp.missing_components

    def test_is_not_trust_score(self):
        """Test 24: Readiness profile is not trust score."""
        rp = build_delegation_mesh_resolution_readiness_profile(
            delegation_ref_id="dref:r",
            identity_mesh_envelope_hash="ime:a",
            has_operator_ref=True,
        )
        assert rp.resolver_unavailable_reason == (
            "identity mesh resolver not available in P1.8.6"
        )


# -----------------------------------------------------------------------
# DelegationMeshRelationshipMap
# -----------------------------------------------------------------------


class TestDelegationMeshRelationshipMap:
    def test_builds_deterministically(self):
        """Test 9: MeshRelationshipMap builds deterministically."""
        a = build_delegation_mesh_relationship_map(
            delegation_ref_id="dref:map",
        )
        b = build_delegation_mesh_relationship_map(
            delegation_ref_id="dref:map",
        )
        assert a.relationship_map_hash == b.relationship_map_hash

    def test_identical_map_gives_identical_hash(self):
        """Test 25: Identical relationship map gives identical hash."""
        pr = build_delegation_mesh_participant_ref(
            delegation_ref_id="dref:m",
            participant_kind=DelegationMeshParticipantKind.OPERATOR_REF,
            participant_ref="op/x",
            participant_label="x",
        )
        a = DelegationMeshRelationshipMap(
            delegation_ref_id="dref:m",
            participant_refs=(pr,),
        )
        b = DelegationMeshRelationshipMap(
            delegation_ref_id="dref:m",
            participant_refs=(pr,),
        )
        assert a.relationship_map_hash == b.relationship_map_hash

    def test_changed_membership_changes_hash(self):
        """Test 26: Changed relationship map membership changes hash."""
        pr1 = build_delegation_mesh_participant_ref(
            delegation_ref_id="dref:m",
            participant_kind=DelegationMeshParticipantKind.OPERATOR_REF,
            participant_ref="op/x",
            participant_label="x",
        )
        pr2 = build_delegation_mesh_participant_ref(
            delegation_ref_id="dref:m",
            participant_kind=DelegationMeshParticipantKind.AGENT_REF,
            participant_ref="agent/y",
            participant_label="y",
        )
        a = DelegationMeshRelationshipMap(
            delegation_ref_id="dref:m",
            participant_refs=(pr1,),
        )
        b = DelegationMeshRelationshipMap(
            delegation_ref_id="dref:m",
            participant_refs=(pr1, pr2),
        )
        assert a.relationship_map_hash != b.relationship_map_hash

    def test_is_not_graph_engine(self):
        """Test 27: MeshRelationshipMap is not graph engine."""
        m = build_delegation_mesh_relationship_map(
            delegation_ref_id="dref:m",
        )
        assert m.relationship_map_id.startswith("mrm:")


# -----------------------------------------------------------------------
# DelegationIdentityMeshBinding
# -----------------------------------------------------------------------


class TestDelegationIdentityMeshBinding:
    def test_builds_deterministically(self):
        """Test 10: IdentityMeshBinding builds deterministically."""
        a = build_delegation_identity_mesh_binding(
            delegation_ref_id="dref:b",
            delegation_identity_hash="i:a",
            role_binding_hash="rb:a",
            constraint_set_hash="cs:a",
            authority_binding_set_hash="abs:a",
            non_repudiation_binding_set_hash="nbs:a",
            identity_mesh_envelope_hash="ime:a",
            readiness_hash="mrp:a",
            relationship_map_hash="mrm:a",
        )
        b = build_delegation_identity_mesh_binding(
            delegation_ref_id="dref:b",
            delegation_identity_hash="i:a",
            role_binding_hash="rb:a",
            constraint_set_hash="cs:a",
            authority_binding_set_hash="abs:a",
            non_repudiation_binding_set_hash="nbs:a",
            identity_mesh_envelope_hash="ime:a",
            readiness_hash="mrp:a",
            relationship_map_hash="mrm:a",
        )
        assert a.binding_hash == b.binding_hash

    def test_is_not_identity_resolution(self):
        """IdentityMeshBinding is not identity resolution."""
        binding = build_delegation_identity_mesh_binding(
            delegation_ref_id="dref:b",
            delegation_identity_hash="i:a",
            role_binding_hash="rb:a",
            constraint_set_hash="cs:a",
            authority_binding_set_hash="abs:a",
            non_repudiation_binding_set_hash="nbs:a",
            identity_mesh_envelope_hash="ime:a",
            readiness_hash="mrp:a",
            relationship_map_hash="mrm:a",
        )
        assert binding.resolution_status == (
            DelegationMeshResolutionStatus.REFERENCE_ONLY
        )


# -----------------------------------------------------------------------
# DelegationIdentityMeshBindingSet
# -----------------------------------------------------------------------


class TestDelegationIdentityMeshBindingSet:
    def test_builds_deterministically(self):
        """Test 11: IdentityMeshBindingSet builds deterministically."""
        a = build_delegation_identity_mesh_binding_set(
            delegation_ref_id="dref:bs",
            delegation_identity_hash="i:a",
            role_binding_hash="rb:a",
            constraint_set_hash="cs:a",
            authority_binding_set_hash="abs:a",
            non_repudiation_binding_set_hash="nbs:a",
            bindings=[],
        )
        b = build_delegation_identity_mesh_binding_set(
            delegation_ref_id="dref:bs",
            delegation_identity_hash="i:a",
            role_binding_hash="rb:a",
            constraint_set_hash="cs:a",
            authority_binding_set_hash="abs:a",
            non_repudiation_binding_set_hash="nbs:a",
            bindings=[],
        )
        assert a.identity_mesh_binding_set_hash == b.identity_mesh_binding_set_hash

    def test_identical_binding_set_gives_identical_hash(self):
        """Test 29: Identical binding set gives identical hash."""
        a = DelegationIdentityMeshBindingSet(
            delegation_ref_id="dref:bs",
            delegation_identity_hash="i:a",
            role_binding_hash="rb:a",
            constraint_set_hash="cs:a",
            authority_binding_set_hash="abs:a",
            non_repudiation_binding_set_hash="nbs:a",
        )
        b = DelegationIdentityMeshBindingSet(
            delegation_ref_id="dref:bs",
            delegation_identity_hash="i:a",
            role_binding_hash="rb:a",
            constraint_set_hash="cs:a",
            authority_binding_set_hash="abs:a",
            non_repudiation_binding_set_hash="nbs:a",
        )
        assert a.identity_mesh_binding_set_hash == b.identity_mesh_binding_set_hash

    def test_changed_binding_membership_changes_hash(self):
        """Test 30: Changed binding membership changes hash."""
        b1 = build_delegation_identity_mesh_binding(
            delegation_ref_id="dref:bs",
            delegation_identity_hash="i:a",
            role_binding_hash="rb:a",
            constraint_set_hash="cs:a",
            authority_binding_set_hash="abs:a",
            non_repudiation_binding_set_hash="nbs:a",
            identity_mesh_envelope_hash="ime:a",
            readiness_hash="mrp:a",
            relationship_map_hash="mrm:a",
        )
        b2 = build_delegation_identity_mesh_binding(
            delegation_ref_id="dref:bs",
            delegation_identity_hash="i:a",
            role_binding_hash="rb:a",
            constraint_set_hash="cs:a",
            authority_binding_set_hash="abs:a",
            non_repudiation_binding_set_hash="nbs:a",
            identity_mesh_envelope_hash="ime:b",
            readiness_hash="mrp:b",
            relationship_map_hash="mrm:b",
        )
        a = DelegationIdentityMeshBindingSet(
            delegation_ref_id="dref:bs",
            delegation_identity_hash="i:a",
            role_binding_hash="rb:a",
            constraint_set_hash="cs:a",
            authority_binding_set_hash="abs:a",
            non_repudiation_binding_set_hash="nbs:a",
            bindings=(b1,),
        )
        b_set = DelegationIdentityMeshBindingSet(
            delegation_ref_id="dref:bs",
            delegation_identity_hash="i:a",
            role_binding_hash="rb:a",
            constraint_set_hash="cs:a",
            authority_binding_set_hash="abs:a",
            non_repudiation_binding_set_hash="nbs:a",
            bindings=(b1, b2),
        )
        assert a.identity_mesh_binding_set_hash != b_set.identity_mesh_binding_set_hash

    def test_p1_8_5_nrbs_fed_to_dev_fixture_chain(self):
        """DEV_FIXTURE chain: P1.8.5 → P1.8.6 identity mesh path."""
        nrbs = _dev_fixture_non_repudiation_binding_set()
        pr = build_delegation_mesh_participant_ref(
            delegation_ref_id=nrbs.delegation_ref_id,
            participant_kind=DelegationMeshParticipantKind.OPERATOR_REF,
            participant_ref="operator/hrv",
            participant_label="hrv",
        )
        ms = build_delegation_mesh_scope_ref(
            delegation_ref_id=nrbs.delegation_ref_id,
            mesh_scope_kind=DelegationMeshScopeKind.DELEGATION_LOCAL,
            mesh_scope_ref="delegations/audit-001",
        )
        envelope = build_delegation_identity_mesh_envelope(
            delegation_ref_id=nrbs.delegation_ref_id,
            delegation_identity_hash=nrbs.delegation_identity_hash,
            role_binding_hash=nrbs.role_binding_hash,
            constraint_set_hash=nrbs.constraint_set_hash,
            authority_binding_set_hash=nrbs.authority_binding_set_hash,
            non_repudiation_binding_set_hash=nrbs.non_repudiation_binding_set_hash,
            participant_refs=[pr],
            mesh_scope_ref=ms,
        )
        rp = build_delegation_mesh_resolution_readiness_profile(
            delegation_ref_id=nrbs.delegation_ref_id,
            identity_mesh_envelope_hash=envelope.identity_mesh_envelope_hash,
            has_operator_ref=True,
        )
        mrm = build_delegation_mesh_relationship_map(
            delegation_ref_id=nrbs.delegation_ref_id,
            participant_refs=[pr],
        )
        binding = build_delegation_identity_mesh_binding(
            delegation_ref_id=nrbs.delegation_ref_id,
            delegation_identity_hash=nrbs.delegation_identity_hash,
            role_binding_hash=nrbs.role_binding_hash,
            constraint_set_hash=nrbs.constraint_set_hash,
            authority_binding_set_hash=nrbs.authority_binding_set_hash,
            non_repudiation_binding_set_hash=nrbs.non_repudiation_binding_set_hash,
            identity_mesh_envelope_hash=envelope.identity_mesh_envelope_hash,
            readiness_hash=rp.readiness_hash,
            relationship_map_hash=mrm.relationship_map_hash,
        )
        bs = build_delegation_identity_mesh_binding_set(
            delegation_ref_id=nrbs.delegation_ref_id,
            delegation_identity_hash=nrbs.delegation_identity_hash,
            role_binding_hash=nrbs.role_binding_hash,
            constraint_set_hash=nrbs.constraint_set_hash,
            authority_binding_set_hash=nrbs.authority_binding_set_hash,
            non_repudiation_binding_set_hash=nrbs.non_repudiation_binding_set_hash,
            bindings=[binding],
        )
        assert bs.identity_mesh_binding_set_hash
        assert bs.side_effects.identity_resolved is False


# -----------------------------------------------------------------------
# DelegationIdentityMeshStatusReport
# -----------------------------------------------------------------------


class TestDelegationIdentityMeshStatusReport:
    def test_builds_deterministically(self):
        """Test 12: Status report builds deterministically."""
        a = build_delegation_identity_mesh_status_report()
        b = build_delegation_identity_mesh_status_report()
        assert a.status_hash == b.status_hash

    def test_dev_fixture_label_is_visible(self):
        """Test 35: DEV_FIXTURE path is explicit."""
        report = build_delegation_identity_mesh_status_report()
        assert report.status_label == DelegationSourceLabel.DEV_FIXTURE

    def test_unavailable_reasons_exist(self):
        """Test 36: UNAVAILABLE reasons exist for future surfaces."""
        report = build_delegation_identity_mesh_status_report()
        assert "Identity Resolver" in report.unavailable_bindings
        assert "Participant Authenticator" in report.unavailable_bindings
        assert "Trust Scoring" in report.unavailable_bindings
        assert "Agent Activation" in report.unavailable_bindings
        assert "Graph Database" in report.unavailable_bindings
        assert "Output Passport / P1.9" in report.unavailable_bindings
        assert "P1.8.7 Scope / Boundary Model" in report.unavailable_bindings

    def test_available_contracts_listed(self):
        report = build_delegation_identity_mesh_status_report()
        assert "DelegationMeshParticipantRef" in report.available_contracts
        assert "DelegationIdentityMeshEnvelope" in report.available_contracts
        assert "DelegationIdentityMeshBindingSet" in report.available_contracts


# -----------------------------------------------------------------------
# DelegationIdentityMeshSideEffects
# -----------------------------------------------------------------------


class TestDelegationIdentityMeshSideEffects:
    def test_all_side_effects_false(self):
        """Test 37: All side effects booleans are false."""
        se = DelegationIdentityMeshSideEffects()
        for f in fields(se):
            assert getattr(se, f.name) is False

    def test_no_identity_resolution(self):
        """Test 38: No identity resolution."""
        se = DelegationIdentityMeshSideEffects()
        assert se.identity_resolved is False

    def test_no_participant_authentication(self):
        """Test 39: No participant authentication."""
        se = DelegationIdentityMeshSideEffects()
        assert se.participant_authenticated is False

    def test_no_relationship_verification(self):
        """Test 40: No relationship verification."""
        se = DelegationIdentityMeshSideEffects()
        assert se.relationship_verified is False

    def test_no_trust_scoring(self):
        """Test 41: No trust scoring."""
        se = DelegationIdentityMeshSideEffects()
        assert se.trust_scored is False

    def test_no_agent_activation(self):
        """Test 42: No agent activation."""
        se = DelegationIdentityMeshSideEffects()
        assert se.agent_activated is False

    def test_no_permission_grant(self):
        """Test 43: No permission grant."""
        se = DelegationIdentityMeshSideEffects()
        assert se.permission_granted is False

    def test_no_authority_grant(self):
        """Test 44: No authority grant."""
        se = DelegationIdentityMeshSideEffects()
        assert se.authority_granted is False

    def test_no_policy_custos_decision(self):
        """Test 45: No policy/Custos decision."""
        se = DelegationIdentityMeshSideEffects()
        assert se.policy_called is False
        assert se.custos_called is False

    def test_no_ledger_global_trace_write(self):
        """Test 46: No Ledger/global trace write."""
        se = DelegationIdentityMeshSideEffects()
        assert se.ledger_written is False
        assert se.global_trace_written is False

    def test_no_runtime_mutation(self):
        """Test 47: No runtime mutation."""
        se = DelegationIdentityMeshSideEffects()
        assert se.runtime_mutated is False


# -----------------------------------------------------------------------
# MeshResolutionStatus
# -----------------------------------------------------------------------


class TestDelegationMeshResolutionStatus:
    def test_includes_all_required_values(self):
        """Test 31: MeshResolutionStatus includes all required values."""
        values = {e.value for e in DelegationMeshResolutionStatus}
        assert "REFERENCE_ONLY" in values
        assert "RESOLUTION_UNAVAILABLE" in values
        assert "RESOLVER_UNAVAILABLE" in values
        assert "NOT_RESOLVED" in values
        assert "UNAVAILABLE" in values
        assert "ERROR" in values
        assert "UNKNOWN" in values


# -----------------------------------------------------------------------
# Hash function tests
# -----------------------------------------------------------------------


class TestHashFunctions:
    def test_hash_participant_ref(self):
        pr = build_delegation_mesh_participant_ref(
            delegation_ref_id="dref:h",
            participant_kind=DelegationMeshParticipantKind.AGENT_REF,
            participant_ref="agent/a",
            participant_label="a",
        )
        assert hash_delegation_mesh_participant_ref(pr) == pr.participant_hash

    def test_hash_relationship_ref(self):
        rr = build_delegation_mesh_relationship_ref(
            delegation_ref_id="dref:h",
            relationship_kind=DelegationMeshRelationshipKind.REFERENCE_ONLY,
            from_participant_ref_id="mpr:a",
            to_participant_ref_id="mpr:b",
        )
        assert hash_delegation_mesh_relationship_ref(rr) == rr.relationship_hash

    def test_hash_scope_ref(self):
        ms = build_delegation_mesh_scope_ref(
            delegation_ref_id="dref:h",
            mesh_scope_kind=DelegationMeshScopeKind.DELEGATION_LOCAL,
            mesh_scope_ref="scope/x",
        )
        assert hash_delegation_mesh_scope_ref(ms) == ms.mesh_scope_hash

    def test_hash_envelope(self):
        env = build_delegation_identity_mesh_envelope(
            delegation_ref_id="dref:h",
            delegation_identity_hash="i:a",
            role_binding_hash="rb:a",
            constraint_set_hash="cs:a",
            authority_binding_set_hash="abs:a",
            non_repudiation_binding_set_hash="nbs:a",
        )
        assert hash_delegation_identity_mesh_envelope(env) == (
            env.identity_mesh_envelope_hash
        )

    def test_hash_readiness_profile(self):
        rp = build_delegation_mesh_resolution_readiness_profile(
            delegation_ref_id="dref:h",
            identity_mesh_envelope_hash="ime:a",
        )
        assert hash_delegation_mesh_resolution_readiness_profile(rp) == (
            rp.readiness_hash
        )

    def test_hash_relationship_map(self):
        mrm = build_delegation_mesh_relationship_map(
            delegation_ref_id="dref:h",
        )
        assert hash_delegation_mesh_relationship_map(mrm) == (
            mrm.relationship_map_hash
        )

    def test_hash_binding(self):
        binding = build_delegation_identity_mesh_binding(
            delegation_ref_id="dref:h",
            delegation_identity_hash="i:a",
            role_binding_hash="rb:a",
            constraint_set_hash="cs:a",
            authority_binding_set_hash="abs:a",
            non_repudiation_binding_set_hash="nbs:a",
            identity_mesh_envelope_hash="ime:a",
            readiness_hash="mrp:a",
            relationship_map_hash="mrm:a",
        )
        assert hash_delegation_identity_mesh_binding(binding) == binding.binding_hash

    def test_hash_binding_set(self):
        bs = build_delegation_identity_mesh_binding_set(
            delegation_ref_id="dref:h",
            delegation_identity_hash="i:a",
            role_binding_hash="rb:a",
            constraint_set_hash="cs:a",
            authority_binding_set_hash="abs:a",
            non_repudiation_binding_set_hash="nbs:a",
            bindings=[],
        )
        assert hash_delegation_identity_mesh_binding_set(bs) == (
            bs.identity_mesh_binding_set_hash
        )


# -----------------------------------------------------------------------
# Serialization tests
# -----------------------------------------------------------------------


class TestSerialization:
    def test_serialize_participant_ref_json_safe(self):
        pr = build_delegation_mesh_participant_ref(
            delegation_ref_id="dref:s",
            participant_kind=DelegationMeshParticipantKind.SERVICE_REF,
            participant_ref="svc/kb",
            participant_label="kb",
        )
        s = serialize_delegation_mesh_participant_ref(pr)
        d = json.loads(s)
        assert isinstance(d, dict)
        assert d["participant_kind"] == "SERVICE_REF"

    def test_serialize_envelope_json_safe(self):
        env = build_delegation_identity_mesh_envelope(
            delegation_ref_id="dref:s",
            delegation_identity_hash="i:a",
            role_binding_hash="rb:a",
            constraint_set_hash="cs:a",
            authority_binding_set_hash="abs:a",
            non_repudiation_binding_set_hash="nbs:a",
        )
        s = serialize_delegation_identity_mesh_envelope(env)
        d = json.loads(s)
        assert isinstance(d, dict)

    def test_serialize_binding_set_json_safe(self):
        bs = build_delegation_identity_mesh_binding_set(
            delegation_ref_id="dref:s",
            delegation_identity_hash="i:a",
            role_binding_hash="rb:a",
            constraint_set_hash="cs:a",
            authority_binding_set_hash="abs:a",
            non_repudiation_binding_set_hash="nbs:a",
            bindings=[],
        )
        s = serialize_delegation_identity_mesh_binding_set(bs)
        d = json.loads(s)
        assert isinstance(d, dict)


# -----------------------------------------------------------------------
# Boundary tests
# -----------------------------------------------------------------------


class TestBoundaries:
    def test_no_graph_engine_behavior(self):
        """Test 48: No graph engine behavior."""
        mrm = build_delegation_mesh_relationship_map(
            delegation_ref_id="dref:m",
        )
        assert isinstance(mrm.relationship_map_hash, str)

    def test_no_p1_8_7_scope_boundary_behavior(self):
        """Test 49: No P1.8.7 scope/boundary behavior."""
        ms = build_delegation_mesh_scope_ref(
            delegation_ref_id="dref:x",
            mesh_scope_kind=DelegationMeshScopeKind.DELEGATION_LOCAL,
            mesh_scope_ref="scope/x",
        )
        assert ms.mesh_ref_status == DelegationMeshRefStatus.REFERENCE_ONLY

    def test_no_output_passport_p1_9_behavior(self):
        """Test 50: No Output Passport / P1.9 behavior."""
        report = build_delegation_identity_mesh_status_report()
        assert "Output Passport / P1.9" in report.unavailable_bindings
