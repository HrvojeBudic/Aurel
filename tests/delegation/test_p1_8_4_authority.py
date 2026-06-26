"""P1.8.4 — Delegation AuthorityRef Binding tests."""
from __future__ import annotations

import json
from dataclasses import fields

import pytest

from agentic_runtime.delegation import (
    DelegationAuthorityBinding,
    DelegationAuthorityBindingSet,
    DelegationAuthorityRef,
    DelegationAuthorityRefKind,
    DelegationAuthorityRefStatus,
    DelegationAuthoritySideEffects,
    DelegationAuthorityStatusReport,
    DelegationConstraintKind,
    DelegationConstraintRef,
    DelegationConstraintSet,
    DelegationConstraintSeverity,
    DelegationConstraintStatus,
    DelegationRoleBindingSet,
    DelegationRoleKind,
    DelegationSourceLabel,
    DelegationSubjectKind,
    DelegatedSubjectRef,
    DelegationPartyRoleRef,
    NonRepudiationProofStatus,
    build_delegated_subject_ref,
    build_delegation_authority_binding,
    build_delegation_authority_binding_set,
    build_delegation_authority_ref,
    build_delegation_authority_status_report,
    build_delegation_constraint_binding,
    build_delegation_constraint_ref,
    build_delegation_constraint_set,
    build_delegation_identity,
    build_delegation_party_role_ref,
    build_delegation_ref,
    build_delegation_role_binding_set,
    hash_delegation_authority_binding_set,
    hash_delegation_authority_ref,
    serialize_delegation_authority_binding_set,
    serialize_delegation_authority_ref,
)
from agentic_runtime.delegation.authority import (
    DelegationValidationError,
    DelegationUnknownFieldError,
)
from agentic_runtime.delegation.foundation import (
    DelegationActorKind,
    DelegationAuthorityKind,
    DelegationConstraint,
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
# DEV_FIXTURE builder chain: P1.8.0 → P1.8.1 → P1.8.2 → P1.8.3 → P1.8.4
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


def _dev_fixture_authority_ref(
    delegation_ref_id: str = "ref:0000000000000000",
):
    """P1.8.4 DEV_FIXTURE DelegationAuthorityRef."""
    return build_delegation_authority_ref(
        delegation_ref_id=delegation_ref_id,
        authority_kind=DelegationAuthorityRefKind.OPERATOR_DECLARED,
        authority_basis="DEV_FIXTURE operator-declared authority",
        policy_context_ref="policy_ctx:fixture",
        path_authority_ref="path_auth:fixture",
        constraint_context_ref="cons_ctx:fixture",
        source_label=DelegationSourceLabel.DEV_FIXTURE,
        authority_status=DelegationAuthorityRefStatus.REFERENCE_ONLY,
    )


# -----------------------------------------------------------------------
# Test 1: Imports work
# -----------------------------------------------------------------------


def test_p184_imports_all_exist():
    """All P1.8.4 symbols importable from agentic_runtime.delegation."""
    assert DelegationAuthorityRefKind is not None
    assert DelegationAuthorityRefStatus is not None
    assert DelegationAuthorityRef is not None
    assert DelegationAuthorityBinding is not None
    assert DelegationAuthorityBindingSet is not None
    assert DelegationAuthoritySideEffects is not None
    assert DelegationAuthorityStatusReport is not None
    assert build_delegation_authority_ref is not None
    assert build_delegation_authority_binding is not None
    assert build_delegation_authority_binding_set is not None
    assert build_delegation_authority_status_report is not None
    assert hash_delegation_authority_ref is not None
    assert hash_delegation_authority_binding_set is not None
    assert serialize_delegation_authority_ref is not None
    assert serialize_delegation_authority_binding_set is not None


def test_p184_existing_p180_exports_remain():
    """P1.8.0 exports still importable."""
    from agentic_runtime.delegation import (
        DelegationRecord,
        DelegationActorKind,
        build_delegation_record,
    )
    assert DelegationRecord is not None
    assert DelegationActorKind is not None
    assert build_delegation_record is not None


def test_p184_existing_p181_exports_remain():
    """P1.8.1 exports still importable."""
    from agentic_runtime.delegation import (
        DelegationRef,
        DelegationIdentity,
        build_delegation_ref,
    )
    assert DelegationRef is not None
    assert DelegationIdentity is not None
    assert build_delegation_ref is not None


def test_p184_existing_p182_exports_remain():
    """P1.8.2 exports still importable."""
    from agentic_runtime.delegation import (
        DelegationRoleBindingSet,
        DelegationPartyRoleRef,
    )
    assert DelegationRoleBindingSet is not None
    assert DelegationPartyRoleRef is not None


def test_p184_existing_p183_exports_remain():
    """P1.8.3 exports still importable."""
    from agentic_runtime.delegation import (
        DelegationConstraintSet,
        DelegationConstraintRef,
    )
    assert DelegationConstraintSet is not None
    assert DelegationConstraintRef is not None


# -----------------------------------------------------------------------
# Test: P1.8.3 constraint set feeds P1.8.4 authority bindings
# -----------------------------------------------------------------------


def test_p184_p183_constraint_set_feeds_authority():
    """P1.8.3 DEV_FIXTURE DelegationConstraintSet can feed P1.8.4
       authority bindings."""
    constraint_set = _dev_fixture_constraint_set()
    ref = _dev_fixture_ref()
    identity = _dev_fixture_identity()

    auth_ref = build_delegation_authority_ref(
        delegation_ref_id=ref.delegation_ref_id,
        authority_kind=DelegationAuthorityRefKind.OPERATOR_DECLARED,
        authority_basis="operator authority with constraint context",
        constraint_context_ref=constraint_set.constraint_set_id,
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    assert auth_ref.constraint_context_ref == constraint_set.constraint_set_id
    assert auth_ref.authority_status == DelegationAuthorityRefStatus.REFERENCE_ONLY

    binding = build_delegation_authority_binding(
        delegation_ref_id=ref.delegation_ref_id,
        delegation_identity_hash=identity.identity_hash,
        role_binding_hash=_dev_fixture_role_binding_set().role_binding_hash,
        constraint_set_hash=constraint_set.constraint_set_hash,
        authority_ref_id=auth_ref.authority_ref_id,
        authority_ref_hash=auth_ref.authority_ref_hash,
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    assert binding.constraint_set_hash == constraint_set.constraint_set_hash
    assert binding.binding_id.startswith("authbind:")
    assert not binding.binding_hash.startswith("TRACE")


# -----------------------------------------------------------------------
# Test: DelegationAuthorityRef determinism
# -----------------------------------------------------------------------


def test_authority_ref_deterministic():
    """Same input → same authority_ref_id and authority_ref_hash."""
    a1 = _dev_fixture_authority_ref()
    a2 = _dev_fixture_authority_ref()
    assert a1.authority_ref_id == a2.authority_ref_id
    assert a1.authority_ref_hash == a2.authority_ref_hash
    assert a1.to_canonical_dict() == a2.to_canonical_dict()


def test_authority_ref_kind_changes_hash():
    """Changed authority_kind → different authority_ref_hash."""
    a1 = _dev_fixture_authority_ref()
    a2 = build_delegation_authority_ref(
        delegation_ref_id="ref:0000000000000000",
        authority_kind=DelegationAuthorityRefKind.SYSTEM_DECLARED,
        authority_basis="DEV_FIXTURE operator-declared authority",
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    assert a1.authority_ref_hash != a2.authority_ref_hash


def test_authority_ref_basis_changes_hash():
    """Changed authority_basis → different authority_ref_hash."""
    a1 = _dev_fixture_authority_ref()
    a2 = build_delegation_authority_ref(
        delegation_ref_id="ref:0000000000000000",
        authority_kind=DelegationAuthorityRefKind.OPERATOR_DECLARED,
        authority_basis="different basis",
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    assert a1.authority_ref_hash != a2.authority_ref_hash


def test_authority_ref_policy_context_ref_changes_hash():
    """Changed policy_context_ref → different authority_ref_hash."""
    a1 = build_delegation_authority_ref(
        delegation_ref_id="ref:0000000000000000",
        authority_kind=DelegationAuthorityRefKind.OPERATOR_DECLARED,
        authority_basis="basis",
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    a2 = build_delegation_authority_ref(
        delegation_ref_id="ref:0000000000000000",
        authority_kind=DelegationAuthorityRefKind.OPERATOR_DECLARED,
        authority_basis="basis",
        policy_context_ref="other_policy_ctx",
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    assert a1.authority_ref_hash != a2.authority_ref_hash


def test_authority_ref_path_authority_ref_changes_hash():
    """Changed path_authority_ref → different authority_ref_hash."""
    a1 = build_delegation_authority_ref(
        delegation_ref_id="ref:0000000000000000",
        authority_kind=DelegationAuthorityRefKind.OPERATOR_DECLARED,
        authority_basis="basis",
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    a2 = build_delegation_authority_ref(
        delegation_ref_id="ref:0000000000000000",
        authority_kind=DelegationAuthorityRefKind.OPERATOR_DECLARED,
        authority_basis="basis",
        path_authority_ref="other_path_auth",
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    assert a1.authority_ref_hash != a2.authority_ref_hash


def test_authority_ref_same_kind_different_delegation_changes_hash():
    """Different delegation_ref_id → different hash (even same kind/basis)."""
    a1 = _dev_fixture_authority_ref("ref:1111111111111111")
    a2 = _dev_fixture_authority_ref("ref:2222222222222222")
    assert a1.authority_ref_hash != a2.authority_ref_hash


# -----------------------------------------------------------------------
# Test: DelegationAuthorityBinding determinism
# -----------------------------------------------------------------------


def test_authority_binding_deterministic():
    """Same input → same binding_id and binding_hash."""
    auth_ref = _dev_fixture_authority_ref()
    b1 = build_delegation_authority_binding(
        delegation_ref_id="ref:0000000000000000",
        delegation_identity_hash="idhash:aaaaaaaaaaaaaaaa",
        role_binding_hash="rbhash:bbbbbbbbbbbbbbbb",
        constraint_set_hash="cshash:cccccccccccccccc",
        authority_ref_id=auth_ref.authority_ref_id,
        authority_ref_hash=auth_ref.authority_ref_hash,
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    b2 = build_delegation_authority_binding(
        delegation_ref_id="ref:0000000000000000",
        delegation_identity_hash="idhash:aaaaaaaaaaaaaaaa",
        role_binding_hash="rbhash:bbbbbbbbbbbbbbbb",
        constraint_set_hash="cshash:cccccccccccccccc",
        authority_ref_id=auth_ref.authority_ref_id,
        authority_ref_hash=auth_ref.authority_ref_hash,
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    assert b1.binding_id == b2.binding_id
    assert b1.binding_hash == b2.binding_hash


# -----------------------------------------------------------------------
# Test: DelegationAuthorityBindingSet determinism
# -----------------------------------------------------------------------


def test_authority_binding_set_deterministic():
    """Same input → same authority_binding_set_id and hash."""
    ref = _dev_fixture_ref()
    identity = _dev_fixture_identity()
    roles = _dev_fixture_role_binding_set()
    cs = _dev_fixture_constraint_set()
    auth_ref = _dev_fixture_authority_ref(ref.delegation_ref_id)

    def _make_set():
        binding = build_delegation_authority_binding(
            delegation_ref_id=ref.delegation_ref_id,
            delegation_identity_hash=identity.identity_hash,
            role_binding_hash=roles.role_binding_hash,
            constraint_set_hash=cs.constraint_set_hash,
            authority_ref_id=auth_ref.authority_ref_id,
            authority_ref_hash=auth_ref.authority_ref_hash,
            source_label=DelegationSourceLabel.DEV_FIXTURE,
        )
        return build_delegation_authority_binding_set(
            delegation_ref_id=ref.delegation_ref_id,
            delegation_identity_hash=identity.identity_hash,
            role_binding_hash=roles.role_binding_hash,
            constraint_set_hash=cs.constraint_set_hash,
            authority_refs=[auth_ref],
            bindings=[binding],
            source_label=DelegationSourceLabel.DEV_FIXTURE,
        )

    s1 = _make_set()
    s2 = _make_set()
    assert s1.authority_binding_set_id == s2.authority_binding_set_id
    assert s1.authority_binding_set_hash == s2.authority_binding_set_hash


def test_authority_binding_set_changed_membership_changes_hash():
    """Adding or removing an authority ref changes
       authority_binding_set_hash."""
    ref = _dev_fixture_ref()
    identity = _dev_fixture_identity()
    roles = _dev_fixture_role_binding_set()
    cs = _dev_fixture_constraint_set()
    auth_ref_a = _dev_fixture_authority_ref(ref.delegation_ref_id)
    auth_ref_b = build_delegation_authority_ref(
        delegation_ref_id=ref.delegation_ref_id,
        authority_kind=DelegationAuthorityRefKind.SYSTEM_DECLARED,
        authority_basis="second authority",
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )

    binding_a = build_delegation_authority_binding(
        delegation_ref_id=ref.delegation_ref_id,
        delegation_identity_hash=identity.identity_hash,
        role_binding_hash=roles.role_binding_hash,
        constraint_set_hash=cs.constraint_set_hash,
        authority_ref_id=auth_ref_a.authority_ref_id,
        authority_ref_hash=auth_ref_a.authority_ref_hash,
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    binding_b = build_delegation_authority_binding(
        delegation_ref_id=ref.delegation_ref_id,
        delegation_identity_hash=identity.identity_hash,
        role_binding_hash=roles.role_binding_hash,
        constraint_set_hash=cs.constraint_set_hash,
        authority_ref_id=auth_ref_b.authority_ref_id,
        authority_ref_hash=auth_ref_b.authority_ref_hash,
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )

    s1 = build_delegation_authority_binding_set(
        delegation_ref_id=ref.delegation_ref_id,
        delegation_identity_hash=identity.identity_hash,
        role_binding_hash=roles.role_binding_hash,
        constraint_set_hash=cs.constraint_set_hash,
        authority_refs=[auth_ref_a],
        bindings=[binding_a],
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    s2 = build_delegation_authority_binding_set(
        delegation_ref_id=ref.delegation_ref_id,
        delegation_identity_hash=identity.identity_hash,
        role_binding_hash=roles.role_binding_hash,
        constraint_set_hash=cs.constraint_set_hash,
        authority_refs=[auth_ref_a, auth_ref_b],
        bindings=[binding_a, binding_b],
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    assert s1.authority_binding_set_hash != s2.authority_binding_set_hash


def test_authority_binding_set_ordering_deterministic():
    """Order of refs/bindings in tuple is deterministic (by ref_id/binding_id)."""
    ref = _dev_fixture_ref()
    identity = _dev_fixture_identity()
    roles = _dev_fixture_role_binding_set()
    cs = _dev_fixture_constraint_set()

    # Create two refs: one with ID starting with 'z', one with 'a'
    auth_z = build_delegation_authority_ref(
        delegation_ref_id=ref.delegation_ref_id,
        authority_kind=DelegationAuthorityRefKind.POLICY_CONTEXT_REFERENCED,
        authority_basis="zzzz authority",
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    auth_a = build_delegation_authority_ref(
        delegation_ref_id=ref.delegation_ref_id,
        authority_kind=DelegationAuthorityRefKind.SYSTEM_DECLARED,
        authority_basis="aaaa authority",
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )

    s1 = build_delegation_authority_binding_set(
        delegation_ref_id=ref.delegation_ref_id,
        delegation_identity_hash=identity.identity_hash,
        role_binding_hash=roles.role_binding_hash,
        constraint_set_hash=cs.constraint_set_hash,
        authority_refs=[auth_z, auth_a],
        bindings=[],
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    s2 = build_delegation_authority_binding_set(
        delegation_ref_id=ref.delegation_ref_id,
        delegation_identity_hash=identity.identity_hash,
        role_binding_hash=roles.role_binding_hash,
        constraint_set_hash=cs.constraint_set_hash,
        authority_refs=[auth_a, auth_z],
        bindings=[],
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    # Input order differs but output order and hash must be identical
    assert s1.authority_binding_set_hash == s2.authority_binding_set_hash
    # The sorted output order must be identical between s1 and s2
    ref_ids_s1 = [ar.authority_ref_id for ar in s1.authority_refs]
    ref_ids_s2 = [ar.authority_ref_id for ar in s2.authority_refs]
    assert ref_ids_s1 == ref_ids_s2, (
        f"deterministic ordering must produce same output: "
        f"{ref_ids_s1} != {ref_ids_s2}"
    )
    # Both auth_a and auth_z must be present (in sorted order)
    expected_ids = sorted([
        auth_a.authority_ref_id,
        auth_z.authority_ref_id,
    ])
    assert ref_ids_s1 == expected_ids


# -----------------------------------------------------------------------
# Test: Serialization
# -----------------------------------------------------------------------


def test_authority_ref_serialization_json_safe():
    """Serialization is JSON-safe and deterministic."""
    auth = _dev_fixture_authority_ref()
    s1 = serialize_delegation_authority_ref(auth)
    s2 = serialize_delegation_authority_ref(auth)
    assert s1 == s2
    parsed = json.loads(s1)
    assert isinstance(parsed, dict)
    assert parsed["authority_kind"] == "OPERATOR_DECLARED"


def test_authority_binding_set_serialization_json_safe():
    """Authority binding set serialization is JSON-safe and deterministic."""
    ref = _dev_fixture_ref()
    identity = _dev_fixture_identity()
    roles = _dev_fixture_role_binding_set()
    cs = _dev_fixture_constraint_set()
    auth_ref = _dev_fixture_authority_ref(ref.delegation_ref_id)
    binding = build_delegation_authority_binding(
        delegation_ref_id=ref.delegation_ref_id,
        delegation_identity_hash=identity.identity_hash,
        role_binding_hash=roles.role_binding_hash,
        constraint_set_hash=cs.constraint_set_hash,
        authority_ref_id=auth_ref.authority_ref_id,
        authority_ref_hash=auth_ref.authority_ref_hash,
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    s = build_delegation_authority_binding_set(
        delegation_ref_id=ref.delegation_ref_id,
        delegation_identity_hash=identity.identity_hash,
        role_binding_hash=roles.role_binding_hash,
        constraint_set_hash=cs.constraint_set_hash,
        authority_refs=[auth_ref],
        bindings=[binding],
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    j1 = serialize_delegation_authority_binding_set(s)
    j2 = serialize_delegation_authority_binding_set(s)
    assert j1 == j2
    parsed = json.loads(j1)
    assert isinstance(parsed, dict)
    assert "authority_refs" in parsed


# -----------------------------------------------------------------------
# Test: Closed-world validation
# -----------------------------------------------------------------------


def test_authority_ref_rejects_unknown_fields():
    """DelegationAuthorityRef rejects unknown fields."""
    with pytest.raises(DelegationUnknownFieldError):
        DelegationAuthorityRef.from_dict({
            "delegation_ref_id": "x",
            "authority_kind": "OPERATOR_DECLARED",
            "authority_basis": "basis",
            "source_label": "DEV_FIXTURE",
            "unknown_field": "should reject",
        })


def test_authority_binding_rejects_unknown_fields():
    """DelegationAuthorityBinding rejects unknown fields."""
    with pytest.raises(DelegationUnknownFieldError):
        DelegationAuthorityBinding.from_dict({
            "delegation_ref_id": "x",
            "delegation_identity_hash": "x",
            "role_binding_hash": "x",
            "constraint_set_hash": "x",
            "authority_ref_id": "x",
            "authority_ref_hash": "x",
            "source_label": "DEV_FIXTURE",
            "bogus": True,
        })


def test_authority_binding_set_rejects_unknown_fields():
    """DelegationAuthorityBindingSet rejects unknown fields."""
    with pytest.raises(DelegationUnknownFieldError):
        DelegationAuthorityBindingSet.from_dict({
            "delegation_ref_id": "x",
            "delegation_identity_hash": "x",
            "role_binding_hash": "x",
            "constraint_set_hash": "x",
            "authority_refs": [],
            "bindings": [],
            "source_label": "DEV_FIXTURE",
            "bogus": True,
        })


# -----------------------------------------------------------------------
# Test: Source / truth labels
# -----------------------------------------------------------------------


def test_authority_ref_source_label_visible():
    """DEV_FIXTURE source_label is visible."""
    auth = _dev_fixture_authority_ref()
    assert auth.source_label == DelegationSourceLabel.DEV_FIXTURE


def test_authority_ref_kind_enum_values():
    """DelegationAuthorityRefKind values are importable."""
    assert DelegationAuthorityRefKind.OPERATOR_DECLARED.value == "OPERATOR_DECLARED"
    assert DelegationAuthorityRefKind.POLICY_CONTEXT_REFERENCED.value == "POLICY_CONTEXT_REFERENCED"
    assert DelegationAuthorityRefKind.PATH_AUTHORITY_REFERENCED.value == "PATH_AUTHORITY_REFERENCED"
    assert DelegationAuthorityRefKind.SYSTEM_DECLARED.value == "SYSTEM_DECLARED"
    assert DelegationAuthorityRefKind.CONSTRAINT_CONTEXT_REFERENCED.value == "CONSTRAINT_CONTEXT_REFERENCED"
    assert DelegationAuthorityRefKind.UNKNOWN.value == "UNKNOWN"


def test_authority_ref_status_enum_values():
    """DelegationAuthorityRefStatus values are importable."""
    assert DelegationAuthorityRefStatus.REFERENCE_ONLY.value == "REFERENCE_ONLY"
    assert DelegationAuthorityRefStatus.DECLARED.value == "DECLARED"
    assert DelegationAuthorityRefStatus.UNAVAILABLE.value == "UNAVAILABLE"
    assert DelegationAuthorityRefStatus.ERROR.value == "ERROR"
    assert DelegationAuthorityRefStatus.UNKNOWN.value == "UNKNOWN"


# -----------------------------------------------------------------------
# Test: UNAVAILABLE reasons
# -----------------------------------------------------------------------


def test_authority_status_report_unavailable_bindings():
    """DelegationAuthorityStatusReport has unavailable bindings."""
    report = build_delegation_authority_status_report()
    assert report.status_label == DelegationSourceLabel.DEV_FIXTURE
    unavailable = dict(report.unavailable_bindings)
    assert "Approval Activation" in unavailable
    assert "Authority Grant" in unavailable
    assert "Authority Resolver" in unavailable
    assert "Authority Verifier" in unavailable
    assert "CLI/Shell/TUI Binding" in unavailable
    assert "Constraint Enforcement" in unavailable
    assert "Global Trace Write" in unavailable
    assert "Ledger Write" in unavailable
    assert "Path Authorization" in unavailable
    assert "Permission Grant" in unavailable
    assert "Policy/Custos Decision" in unavailable
    assert "Policy/Custos Enforcement" in unavailable
    assert "Projection/API/Event/Read Model" in unavailable
    assert "Runtime Delegation Execution" in unavailable
    for reason in unavailable.values():
        assert isinstance(reason, str)
        assert len(reason) > 0


# -----------------------------------------------------------------------
# Test: DelegationAuthoritySideEffects all false
# -----------------------------------------------------------------------


def test_authority_side_effects_all_false():
    """All DelegationAuthoritySideEffects booleans are false by default."""
    se = DelegationAuthoritySideEffects()
    for f in fields(se):
        assert getattr(se, f.name) is False, (
            f"side_effect {f.name} must be False"
        )


def test_authority_status_report_side_effects_all_false():
    """Status report side effects all false."""
    report = build_delegation_authority_status_report()
    se = report.side_effects
    for f in fields(DelegationAuthoritySideEffects):
        assert getattr(se, f.name) is False


# -----------------------------------------------------------------------
# Test: DelegationAuthorityStatusReport determinism
# -----------------------------------------------------------------------


def test_authority_status_report_deterministic():
    """Two status reports are identical."""
    r1 = build_delegation_authority_status_report()
    r2 = build_delegation_authority_status_report()
    assert r1.status_hash == r2.status_hash
    assert r1.to_canonical_dict() == r2.to_canonical_dict()


# -----------------------------------------------------------------------
# Test: hash wrappers
# -----------------------------------------------------------------------


def test_hashing_wrappers():
    """hash_* and the dataclass hash fields match."""
    auth = _dev_fixture_authority_ref()
    assert hash_delegation_authority_ref(auth) == auth.authority_ref_hash
    assert len(auth.authority_ref_hash) == 64

    ref = _dev_fixture_ref()
    identity = _dev_fixture_identity()
    roles = _dev_fixture_role_binding_set()
    cs = _dev_fixture_constraint_set()
    binding = build_delegation_authority_binding(
        delegation_ref_id=ref.delegation_ref_id,
        delegation_identity_hash=identity.identity_hash,
        role_binding_hash=roles.role_binding_hash,
        constraint_set_hash=cs.constraint_set_hash,
        authority_ref_id=auth.authority_ref_id,
        authority_ref_hash=auth.authority_ref_hash,
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    s = build_delegation_authority_binding_set(
        delegation_ref_id=ref.delegation_ref_id,
        delegation_identity_hash=identity.identity_hash,
        role_binding_hash=roles.role_binding_hash,
        constraint_set_hash=cs.constraint_set_hash,
        authority_refs=[auth],
        bindings=[binding],
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    assert hash_delegation_authority_binding_set(s) == s.authority_binding_set_hash
    assert len(s.authority_binding_set_hash) == 64


# -----------------------------------------------------------------------
# Test: Core boundary assertions
# -----------------------------------------------------------------------


def test_authority_ref_not_grant():
    """AuthorityRef exists ≠ authority granted."""
    auth = _dev_fixture_authority_ref()
    assert auth.authority_ref_id is not None
    assert auth.authority_status == DelegationAuthorityRefStatus.REFERENCE_ONLY
    assert DelegationAuthoritySideEffects().permission_granted is False


def test_authority_basis_not_verified():
    """Authority basis exists ≠ authority verified."""
    auth = _dev_fixture_authority_ref()
    assert len(auth.authority_basis) > 0
    assert DelegationAuthoritySideEffects().authority_verified is False


def test_policy_context_ref_not_decision():
    """policy_context_ref ≠ policy/Custos decision."""
    auth = _dev_fixture_authority_ref()
    assert auth.policy_context_ref is not None
    assert DelegationAuthoritySideEffects().policy_called is False
    assert DelegationAuthoritySideEffects().custos_called is False


def test_path_authority_ref_not_authorized():
    """path_authority_ref ≠ path authorized."""
    auth = _dev_fixture_authority_ref()
    assert auth.path_authority_ref is not None
    assert DelegationAuthoritySideEffects().path_authorized is False


def test_operator_declaration_not_authority_proof():
    """OPERATOR_DECLARED ≠ legal/operational authority proven."""
    auth = _dev_fixture_authority_ref()
    assert auth.authority_kind == DelegationAuthorityRefKind.OPERATOR_DECLARED
    assert DelegationAuthoritySideEffects().authority_verified is False
    assert DelegationAuthoritySideEffects().permission_granted is False


def test_authority_binding_not_approval():
    """Authority binding ≠ approval created."""
    ref = _dev_fixture_ref()
    identity = _dev_fixture_identity()
    roles = _dev_fixture_role_binding_set()
    cs = _dev_fixture_constraint_set()
    auth_ref = _dev_fixture_authority_ref(ref.delegation_ref_id)
    binding = build_delegation_authority_binding(
        delegation_ref_id=ref.delegation_ref_id,
        delegation_identity_hash=identity.identity_hash,
        role_binding_hash=roles.role_binding_hash,
        constraint_set_hash=cs.constraint_set_hash,
        authority_ref_id=auth_ref.authority_ref_id,
        authority_ref_hash=auth_ref.authority_ref_hash,
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    assert binding.binding_id is not None
    assert DelegationAuthoritySideEffects().approval_created is False


def test_authority_binding_not_permission():
    """Authority binding ≠ permission granted."""
    se = DelegationAuthoritySideEffects()
    assert se.permission_granted is False


def test_authority_hash_not_trace_verified():
    """authority_ref_hash ≠ TRACE_VERIFIED."""
    auth = _dev_fixture_authority_ref()
    assert len(auth.authority_ref_hash) > 0
    assert auth.source_label != DelegationSourceLabel.TRACE_VERIFIED
    assert not auth.authority_ref_hash.startswith("TRACE")


def test_authority_binding_set_not_runtime_execution():
    """authority_binding_set_hash exists ≠ runtime execution."""
    ref = _dev_fixture_ref()
    identity = _dev_fixture_identity()
    roles = _dev_fixture_role_binding_set()
    cs = _dev_fixture_constraint_set()
    auth = _dev_fixture_authority_ref(ref.delegation_ref_id)
    binding = build_delegation_authority_binding(
        delegation_ref_id=ref.delegation_ref_id,
        delegation_identity_hash=identity.identity_hash,
        role_binding_hash=roles.role_binding_hash,
        constraint_set_hash=cs.constraint_set_hash,
        authority_ref_id=auth.authority_ref_id,
        authority_ref_hash=auth.authority_ref_hash,
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    s = build_delegation_authority_binding_set(
        delegation_ref_id=ref.delegation_ref_id,
        delegation_identity_hash=identity.identity_hash,
        role_binding_hash=roles.role_binding_hash,
        constraint_set_hash=cs.constraint_set_hash,
        authority_refs=[auth],
        bindings=[binding],
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    assert len(s.authority_binding_set_hash) > 0
    assert DelegationAuthoritySideEffects().delegation_executed is False


def test_no_field_implies_policy_custos_approval():
    """No field implies policy/Custos approval, Ledger/global trace write,
       runtime execution, resolver, enforcement, authority verification,
       authority grant, path authorization, or non-repudiation verification."""
    se = DelegationAuthoritySideEffects()
    assert se.policy_called is False
    assert se.custos_called is False
    assert se.approval_created is False
    assert se.permission_granted is False
    assert se.authority_verified is False
    assert se.path_authorized is False
    assert se.ledger_written is False
    assert se.global_trace_written is False
    assert se.runtime_mutated is False
    assert se.constraint_enforced is False
    assert se.delegation_executed is False


def test_authority_ref_id_prefix():
    """Authority ref ID has correct prefix."""
    auth = _dev_fixture_authority_ref()
    assert auth.authority_ref_id.startswith("authref:")


def test_authority_binding_set_id_prefix():
    """Authority binding set ID has correct prefix."""
    ref = _dev_fixture_ref()
    identity = _dev_fixture_identity()
    roles = _dev_fixture_role_binding_set()
    cs = _dev_fixture_constraint_set()
    auth = _dev_fixture_authority_ref(ref.delegation_ref_id)
    binding = build_delegation_authority_binding(
        delegation_ref_id=ref.delegation_ref_id,
        delegation_identity_hash=identity.identity_hash,
        role_binding_hash=roles.role_binding_hash,
        constraint_set_hash=cs.constraint_set_hash,
        authority_ref_id=auth.authority_ref_id,
        authority_ref_hash=auth.authority_ref_hash,
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    s = build_delegation_authority_binding_set(
        delegation_ref_id=ref.delegation_ref_id,
        delegation_identity_hash=identity.identity_hash,
        role_binding_hash=roles.role_binding_hash,
        constraint_set_hash=cs.constraint_set_hash,
        authority_refs=[auth],
        bindings=[binding],
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    assert s.authority_binding_set_id.startswith("authbset:")
