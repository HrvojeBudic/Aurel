"""P1.8.3 — Delegation Constraint Model tests."""
from __future__ import annotations

import json
from dataclasses import fields

import pytest

from agentic_runtime.delegation import (
    DelegationConstraintBinding,
    DelegationConstraintKind,
    DelegationConstraintRef,
    DelegationConstraintSet,
    DelegationConstraintSeverity,
    DelegationConstraintSideEffects,
    DelegationConstraintStatus,
    DelegationConstraintStatusReport,
    DelegationRoleKind,
    DelegationRoleBindingSet,
    DelegationSourceLabel,
    DelegatedSubjectRef,
    DelegationPartyRoleRef,
    build_delegated_subject_ref,
    build_delegation_constraint_binding,
    build_delegation_constraint_ref,
    build_delegation_constraint_set,
    build_delegation_constraint_status_report,
    build_delegation_identity,
    build_delegation_party_role_ref,
    build_delegation_ref,
    build_delegation_role_binding_set,
    hash_delegation_constraint_ref,
    hash_delegation_constraint_set,
    serialize_delegation_constraint_ref,
    serialize_delegation_constraint_set,
)
from agentic_runtime.delegation.constraints import (
    DelegationValidationError,
    DelegationUnknownFieldError,
)
from agentic_runtime.delegation.foundation import (
    DelegationActorKind,
    DelegationAuthorityKind,
    DelegationConstraint,
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

DEV_FIXTURE_CREATED_AT = "2026-06-27T00:00:00Z"


# -----------------------------------------------------------------------
# DEV_FIXTURE builder chain: P1.8.0 → P1.8.1 → P1.8.2 → P1.8.3
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


def _dev_fixture_constraint_refs():
    """Build DEV_FIXTURE time/scope/tool/data/risk/review constraints."""
    ref = _dev_fixture_ref()
    return [
        build_delegation_constraint_ref(
            delegation_ref_id=ref.delegation_ref_id,
            constraint_kind=DelegationConstraintKind.TIME_BOUND,
            constraint_value="2026-06-27T12:00:00Z",
            constraint_severity=DelegationConstraintSeverity.HIGH,
            source_label=DelegationSourceLabel.DEV_FIXTURE,
        ),
        build_delegation_constraint_ref(
            delegation_ref_id=ref.delegation_ref_id,
            constraint_kind=DelegationConstraintKind.SCOPE_BOUND,
            constraint_value="src/agentic_runtime/delegation/",
            constraint_severity=DelegationConstraintSeverity.MEDIUM,
            required_review=True,
            review_ref="review:0000000000000001",
            source_label=DelegationSourceLabel.DEV_FIXTURE,
        ),
        build_delegation_constraint_ref(
            delegation_ref_id=ref.delegation_ref_id,
            constraint_kind=DelegationConstraintKind.TOOL_BOUND,
            constraint_value="write_file_only",
            constraint_severity=DelegationConstraintSeverity.HIGH,
            source_label=DelegationSourceLabel.DEV_FIXTURE,
        ),
        build_delegation_constraint_ref(
            delegation_ref_id=ref.delegation_ref_id,
            constraint_kind=DelegationConstraintKind.DATA_BOUND,
            constraint_value="delegation-module-data-only",
            constraint_severity=DelegationConstraintSeverity.CRITICAL,
            source_label=DelegationSourceLabel.DEV_FIXTURE,
        ),
        build_delegation_constraint_ref(
            delegation_ref_id=ref.delegation_ref_id,
            constraint_kind=DelegationConstraintKind.RISK_BOUND,
            constraint_value="risk-tier-R4",
            constraint_severity=DelegationConstraintSeverity.CRITICAL,
            required_review=True,
            source_label=DelegationSourceLabel.DEV_FIXTURE,
        ),
        build_delegation_constraint_ref(
            delegation_ref_id=ref.delegation_ref_id,
            constraint_kind=DelegationConstraintKind.OPERATOR_REVIEW_REQUIRED,
            constraint_value="operator-approval-before-commit",
            constraint_severity=DelegationConstraintSeverity.HIGH,
            required_review=True,
            review_ref="review:0000000000000002",
            source_label=DelegationSourceLabel.DEV_FIXTURE,
        ),
    ]


# -----------------------------------------------------------------------
# Test 1: Imports work from agentic_runtime.delegation
# -----------------------------------------------------------------------


def test_p1_8_3_imports_work() -> None:
    import agentic_runtime.delegation as delegation

    # P1.8.3 symbols
    assert hasattr(delegation, "DelegationConstraintSeverity")
    assert hasattr(delegation, "DelegationConstraintStatus")
    assert hasattr(delegation, "DelegationConstraintRef")
    assert hasattr(delegation, "DelegationConstraintBinding")
    assert hasattr(delegation, "DelegationConstraintSet")
    assert hasattr(delegation, "DelegationConstraintSideEffects")
    assert hasattr(delegation, "DelegationConstraintStatusReport")
    assert hasattr(delegation, "build_delegation_constraint_ref")
    assert hasattr(delegation, "build_delegation_constraint_binding")
    assert hasattr(delegation, "build_delegation_constraint_set")
    assert hasattr(delegation, "build_delegation_constraint_status_report")
    assert hasattr(delegation, "serialize_delegation_constraint_ref")
    assert hasattr(delegation, "serialize_delegation_constraint_set")
    assert hasattr(delegation, "hash_delegation_constraint_ref")
    assert hasattr(delegation, "hash_delegation_constraint_set")


def test_p1_8_0_exports_preserved() -> None:
    import agentic_runtime.delegation as delegation

    assert hasattr(delegation, "DelegationRecord")
    assert hasattr(delegation, "build_delegation_record")
    assert hasattr(delegation, "DelegationConstraintKind")
    assert hasattr(delegation, "DelegationSourceLabel")


def test_p1_8_1_exports_preserved() -> None:
    import agentic_runtime.delegation as delegation

    assert hasattr(delegation, "DelegationRef")
    assert hasattr(delegation, "DelegationIdentity")
    assert hasattr(delegation, "build_delegation_ref")
    assert hasattr(delegation, "build_delegation_identity")


def test_p1_8_2_exports_preserved() -> None:
    import agentic_runtime.delegation as delegation

    assert hasattr(delegation, "DelegationRoleBindingSet")
    assert hasattr(delegation, "DelegationPartyRoleRef")
    assert hasattr(delegation, "DelegatedSubjectRef")
    assert hasattr(delegation, "build_delegation_role_binding_set")


# -----------------------------------------------------------------------
# Test 2: DelegationConstraintRef builds deterministically
# -----------------------------------------------------------------------


def test_constraint_ref_deterministic_build() -> None:
    ref = _dev_fixture_ref()
    cr1 = build_delegation_constraint_ref(
        delegation_ref_id=ref.delegation_ref_id,
        constraint_kind=DelegationConstraintKind.TIME_BOUND,
        constraint_value="2026-06-27T12:00:00Z",
        constraint_severity=DelegationConstraintSeverity.HIGH,
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    cr2 = build_delegation_constraint_ref(
        delegation_ref_id=ref.delegation_ref_id,
        constraint_kind=DelegationConstraintKind.TIME_BOUND,
        constraint_value="2026-06-27T12:00:00Z",
        constraint_severity=DelegationConstraintSeverity.HIGH,
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    assert cr1.constraint_hash == cr2.constraint_hash
    assert cr1.constraint_ref_id == cr2.constraint_ref_id


def test_constraint_ref_hash_changes_with_kind() -> None:
    ref = _dev_fixture_ref()
    cr1 = build_delegation_constraint_ref(
        delegation_ref_id=ref.delegation_ref_id,
        constraint_kind=DelegationConstraintKind.TIME_BOUND,
        constraint_value="x",
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    cr2 = build_delegation_constraint_ref(
        delegation_ref_id=ref.delegation_ref_id,
        constraint_kind=DelegationConstraintKind.SCOPE_BOUND,
        constraint_value="x",
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    assert cr1.constraint_hash != cr2.constraint_hash


def test_constraint_ref_hash_changes_with_value() -> None:
    ref = _dev_fixture_ref()
    cr1 = build_delegation_constraint_ref(
        delegation_ref_id=ref.delegation_ref_id,
        constraint_kind=DelegationConstraintKind.TIME_BOUND,
        constraint_value="a",
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    cr2 = build_delegation_constraint_ref(
        delegation_ref_id=ref.delegation_ref_id,
        constraint_kind=DelegationConstraintKind.TIME_BOUND,
        constraint_value="b",
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    assert cr1.constraint_hash != cr2.constraint_hash


def test_constraint_ref_hash_changes_with_severity() -> None:
    ref = _dev_fixture_ref()
    cr1 = build_delegation_constraint_ref(
        delegation_ref_id=ref.delegation_ref_id,
        constraint_kind=DelegationConstraintKind.TIME_BOUND,
        constraint_value="x",
        constraint_severity=DelegationConstraintSeverity.LOW,
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    cr2 = build_delegation_constraint_ref(
        delegation_ref_id=ref.delegation_ref_id,
        constraint_kind=DelegationConstraintKind.TIME_BOUND,
        constraint_value="x",
        constraint_severity=DelegationConstraintSeverity.HIGH,
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    assert cr1.constraint_hash != cr2.constraint_hash


def test_constraint_ref_hash_changes_with_required_review() -> None:
    ref = _dev_fixture_ref()
    cr1 = build_delegation_constraint_ref(
        delegation_ref_id=ref.delegation_ref_id,
        constraint_kind=DelegationConstraintKind.SCOPE_BOUND,
        constraint_value="x",
        required_review=False,
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    cr2 = build_delegation_constraint_ref(
        delegation_ref_id=ref.delegation_ref_id,
        constraint_kind=DelegationConstraintKind.SCOPE_BOUND,
        constraint_value="x",
        required_review=True,
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    assert cr1.constraint_hash != cr2.constraint_hash


def test_constraint_ref_hash_changes_with_review_ref() -> None:
    ref = _dev_fixture_ref()
    cr1 = build_delegation_constraint_ref(
        delegation_ref_id=ref.delegation_ref_id,
        constraint_kind=DelegationConstraintKind.OPERATOR_REVIEW_REQUIRED,
        constraint_value="x",
        required_review=True,
        review_ref="review:aaa",
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    cr2 = build_delegation_constraint_ref(
        delegation_ref_id=ref.delegation_ref_id,
        constraint_kind=DelegationConstraintKind.OPERATOR_REVIEW_REQUIRED,
        constraint_value="x",
        required_review=True,
        review_ref="review:bbb",
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    assert cr1.constraint_hash != cr2.constraint_hash


def test_constraint_ref_source_label_visible() -> None:
    cr = build_delegation_constraint_ref(
        delegation_ref_id="ref:0000000000000000",
        constraint_kind=DelegationConstraintKind.TIME_BOUND,
        constraint_value="x",
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    assert cr.source_label == DelegationSourceLabel.DEV_FIXTURE
    assert cr.constraint_status == DelegationConstraintStatus.DECLARED


# -----------------------------------------------------------------------
# Test 3: DelegationConstraintBinding builds deterministically
# -----------------------------------------------------------------------


def test_constraint_binding_deterministic_build() -> None:
    ref = _dev_fixture_ref()
    identity = _dev_fixture_identity()
    role_set = _dev_fixture_role_binding_set()
    cr = build_delegation_constraint_ref(
        delegation_ref_id=ref.delegation_ref_id,
        constraint_kind=DelegationConstraintKind.TIME_BOUND,
        constraint_value="x",
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    b1 = build_delegation_constraint_binding(
        delegation_ref_id=ref.delegation_ref_id,
        delegation_identity_hash=identity.identity_hash,
        role_binding_hash=role_set.role_binding_hash,
        constraint_ref_id=cr.constraint_ref_id,
        constraint_hash=cr.constraint_hash,
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    b2 = build_delegation_constraint_binding(
        delegation_ref_id=ref.delegation_ref_id,
        delegation_identity_hash=identity.identity_hash,
        role_binding_hash=role_set.role_binding_hash,
        constraint_ref_id=cr.constraint_ref_id,
        constraint_hash=cr.constraint_hash,
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    assert b1.binding_hash == b2.binding_hash
    assert b1.binding_id == b2.binding_id


# -----------------------------------------------------------------------
# Test 4: DelegationConstraintSet builds deterministically
# -----------------------------------------------------------------------


def test_constraint_set_deterministic_build() -> None:
    ref = _dev_fixture_ref()
    identity = _dev_fixture_identity()
    role_set = _dev_fixture_role_binding_set()
    crs = _dev_fixture_constraint_refs()
    bindings = [
        build_delegation_constraint_binding(
            delegation_ref_id=ref.delegation_ref_id,
            delegation_identity_hash=identity.identity_hash,
            role_binding_hash=role_set.role_binding_hash,
            constraint_ref_id=cr.constraint_ref_id,
            constraint_hash=cr.constraint_hash,
            source_label=DelegationSourceLabel.DEV_FIXTURE,
        )
        for cr in crs
    ]
    cs1 = build_delegation_constraint_set(
        delegation_ref_id=ref.delegation_ref_id,
        delegation_identity_hash=identity.identity_hash,
        role_binding_hash=role_set.role_binding_hash,
        constraints=crs,
        bindings=bindings,
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    cs2 = build_delegation_constraint_set(
        delegation_ref_id=ref.delegation_ref_id,
        delegation_identity_hash=identity.identity_hash,
        role_binding_hash=role_set.role_binding_hash,
        constraints=crs,
        bindings=bindings,
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    assert cs1.constraint_set_hash == cs2.constraint_set_hash
    assert cs1.constraint_set_id == cs2.constraint_set_id


def test_constraint_set_hash_changes_with_different_constraints() -> None:
    ref = _dev_fixture_ref()
    identity = _dev_fixture_identity()
    role_set = _dev_fixture_role_binding_set()
    cr_time = build_delegation_constraint_ref(
        delegation_ref_id=ref.delegation_ref_id,
        constraint_kind=DelegationConstraintKind.TIME_BOUND,
        constraint_value="x",
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    cr_scope = build_delegation_constraint_ref(
        delegation_ref_id=ref.delegation_ref_id,
        constraint_kind=DelegationConstraintKind.SCOPE_BOUND,
        constraint_value="y",
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    cs1 = build_delegation_constraint_set(
        delegation_ref_id=ref.delegation_ref_id,
        delegation_identity_hash=identity.identity_hash,
        role_binding_hash=role_set.role_binding_hash,
        constraints=[cr_time],
        bindings=[],
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    cs2 = build_delegation_constraint_set(
        delegation_ref_id=ref.delegation_ref_id,
        delegation_identity_hash=identity.identity_hash,
        role_binding_hash=role_set.role_binding_hash,
        constraints=[cr_scope],
        bindings=[],
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    assert cs1.constraint_set_hash != cs2.constraint_set_hash


def test_constraint_set_ordering_deterministic() -> None:
    """Constraint refs are sorted by constraint_ref_id regardless of input order."""
    ref = _dev_fixture_ref()
    identity = _dev_fixture_identity()
    role_set = _dev_fixture_role_binding_set()

    cr_a = build_delegation_constraint_ref(
        delegation_ref_id=ref.delegation_ref_id,
        constraint_kind=DelegationConstraintKind.TIME_BOUND,
        constraint_value="a",
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    cr_b = build_delegation_constraint_ref(
        delegation_ref_id=ref.delegation_ref_id,
        constraint_kind=DelegationConstraintKind.SCOPE_BOUND,
        constraint_value="b",
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    cs_ab = build_delegation_constraint_set(
        delegation_ref_id=ref.delegation_ref_id,
        delegation_identity_hash=identity.identity_hash,
        role_binding_hash=role_set.role_binding_hash,
        constraints=[cr_a, cr_b],
        bindings=[],
    )
    cs_ba = build_delegation_constraint_set(
        delegation_ref_id=ref.delegation_ref_id,
        delegation_identity_hash=identity.identity_hash,
        role_binding_hash=role_set.role_binding_hash,
        constraints=[cr_b, cr_a],
        bindings=[],
    )
    assert cs_ab.constraint_set_hash == cs_ba.constraint_set_hash
    assert [c.constraint_ref_id for c in cs_ab.constraints] == [
        c.constraint_ref_id for c in cs_ba.constraints
    ]


# -----------------------------------------------------------------------
# Test 5: DelegationConstraintStatusReport + unavailable reasons
# -----------------------------------------------------------------------


def test_constraint_status_report_builds() -> None:
    report = build_delegation_constraint_status_report()
    assert report.status_label == DelegationSourceLabel.DEV_FIXTURE
    assert report.schema_version == "delegation_constraint_status_report.v1"
    assert len(report.available_contracts) >= 7
    assert report.status_hash != ""


def test_unavailable_reasons_exist() -> None:
    report = build_delegation_constraint_status_report()
    assert "Constraint Enforcement" in report.unavailable_bindings
    assert "Policy/Custos Enforcement" in report.unavailable_bindings
    assert "Approval Activation" in report.unavailable_bindings
    assert "Ledger Write" in report.unavailable_bindings
    assert "Global Trace Write" in report.unavailable_bindings
    assert "Runtime Blocker" in report.unavailable_bindings
    assert "Tool Permission Mutation" in report.unavailable_bindings
    assert "Data Access Mutation" in report.unavailable_bindings
    assert "Scheduler Mutation" in report.unavailable_bindings
    assert "Authority Bridge" in report.unavailable_bindings
    assert "Delegation Resolver" in report.unavailable_bindings
    assert "Delegation Chain Resolver" in report.unavailable_bindings
    assert "Non-Repudiation Verifier" in report.unavailable_bindings
    assert "Violation/Drift Detector" in report.unavailable_bindings
    assert "Runtime Delegation Execution" in report.unavailable_bindings
    assert "CLI/Shell/TUI Binding" in report.unavailable_bindings
    assert "Projection/API/Event/Read Model" in report.unavailable_bindings


# -----------------------------------------------------------------------
# Test 6: JSON-safe serialization
# -----------------------------------------------------------------------


def test_constraint_ref_json_safe() -> None:
    cr = build_delegation_constraint_ref(
        delegation_ref_id="ref:0000000000000000",
        constraint_kind=DelegationConstraintKind.TIME_BOUND,
        constraint_value="2026-06-27T12:00:00Z",
        constraint_severity=DelegationConstraintSeverity.HIGH,
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    serialized = serialize_delegation_constraint_ref(cr)
    parsed = json.loads(serialized)
    assert parsed["constraint_kind"] == "TIME_BOUND"
    assert parsed["constraint_value"] == "2026-06-27T12:00:00Z"
    assert parsed["constraint_severity"] == "HIGH"
    assert parsed["source_label"] == "DEV_FIXTURE"


def test_constraint_ref_json_deterministic() -> None:
    ref = _dev_fixture_ref()
    cr1 = build_delegation_constraint_ref(
        delegation_ref_id=ref.delegation_ref_id,
        constraint_kind=DelegationConstraintKind.TIME_BOUND,
        constraint_value="x",
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    cr2 = build_delegation_constraint_ref(
        delegation_ref_id=ref.delegation_ref_id,
        constraint_kind=DelegationConstraintKind.TIME_BOUND,
        constraint_value="x",
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    assert serialize_delegation_constraint_ref(cr1) == serialize_delegation_constraint_ref(cr2)


# -----------------------------------------------------------------------
# Test 7: Closed-world validation
# -----------------------------------------------------------------------


def test_constraint_ref_rejects_unknown_field() -> None:
    ref = _dev_fixture_ref()
    cr = build_delegation_constraint_ref(
        delegation_ref_id=ref.delegation_ref_id,
        constraint_kind=DelegationConstraintKind.TIME_BOUND,
        constraint_value="x",
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    bad_data = cr.to_canonical_dict()
    bad_data["nonexistent_field"] = "boom"
    with pytest.raises(DelegationUnknownFieldError):
        DelegationConstraintRef.from_dict(bad_data)


def test_constraint_set_rejects_unknown_field() -> None:
    ref = _dev_fixture_ref()
    identity = _dev_fixture_identity()
    role_set = _dev_fixture_role_binding_set()
    cs = build_delegation_constraint_set(
        delegation_ref_id=ref.delegation_ref_id,
        delegation_identity_hash=identity.identity_hash,
        role_binding_hash=role_set.role_binding_hash,
        constraints=[],
        bindings=[],
    )
    bad_data = cs.to_canonical_dict()
    bad_data["nonexistent_field"] = "boom"
    with pytest.raises(DelegationUnknownFieldError):
        DelegationConstraintSet.from_dict(bad_data)


# -----------------------------------------------------------------------
# Test 8: All side effects are false
# -----------------------------------------------------------------------


def test_constraint_side_effects_all_false() -> None:
    se = DelegationConstraintSideEffects()
    for f in fields(se):
        assert getattr(se, f.name) is False, f"{f.name} must be false"


def test_constraint_set_side_effects_inherited_false() -> None:
    ref = _dev_fixture_ref()
    identity = _dev_fixture_identity()
    role_set = _dev_fixture_role_binding_set()
    cs = build_delegation_constraint_set(
        delegation_ref_id=ref.delegation_ref_id,
        delegation_identity_hash=identity.identity_hash,
        role_binding_hash=role_set.role_binding_hash,
        constraints=[],
        bindings=[],
    )
    for f in fields(cs.side_effects):
        assert getattr(cs.side_effects, f.name) is False, (
            f"constraint_set.side_effects.{f.name} must be false"
        )


# -----------------------------------------------------------------------
# Test 9: Constraint boundary assertions (explicit negatives)
# -----------------------------------------------------------------------


def test_constraint_exists_does_not_imply_enforcement() -> None:
    cr = build_delegation_constraint_ref(
        delegation_ref_id="ref:0000000000000000",
        constraint_kind=DelegationConstraintKind.TIME_BOUND,
        constraint_value="x",
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    assert cr.constraint_status == DelegationConstraintStatus.DECLARED
    assert cr.constraint_status is not DelegationConstraintStatus.ERROR
    # Existence is not enforcement — no field in DelegationConstraintRef
    # implies enforcement.
    assert "enforced" not in cr.to_canonical_dict()


def test_required_review_does_not_imply_approval_created() -> None:
    cr = build_delegation_constraint_ref(
        delegation_ref_id="ref:0000000000000000",
        constraint_kind=DelegationConstraintKind.OPERATOR_REVIEW_REQUIRED,
        constraint_value="requires-approval",
        required_review=True,
        review_ref="review:abc",
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    assert cr.required_review is True
    # required_review is metadata only; it does not create approval
    assert "approval" not in cr.to_canonical_dict()


def test_risk_bound_does_not_imply_policy_decision() -> None:
    cr = build_delegation_constraint_ref(
        delegation_ref_id="ref:0000000000000000",
        constraint_kind=DelegationConstraintKind.RISK_BOUND,
        constraint_value="R5",
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    assert cr.constraint_kind == DelegationConstraintKind.RISK_BOUND
    assert cr.constraint_hash is not None
    # risk_bound is metadata only; no policy call
    se = DelegationConstraintSideEffects()
    assert se.policy_called is False
    assert se.custos_called is False


def test_tool_bound_does_not_imply_tool_permission_changed() -> None:
    cr = build_delegation_constraint_ref(
        delegation_ref_id="ref:0000000000000000",
        constraint_kind=DelegationConstraintKind.TOOL_BOUND,
        constraint_value="read-only",
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    assert cr.constraint_kind == DelegationConstraintKind.TOOL_BOUND
    se = DelegationConstraintSideEffects()
    assert se.tool_permission_changed is False


def test_data_bound_does_not_imply_data_access_changed() -> None:
    cr = build_delegation_constraint_ref(
        delegation_ref_id="ref:0000000000000000",
        constraint_kind=DelegationConstraintKind.DATA_BOUND,
        constraint_value="local-only",
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    assert cr.constraint_kind == DelegationConstraintKind.DATA_BOUND
    se = DelegationConstraintSideEffects()
    assert se.data_access_changed is False


def test_time_bound_does_not_imply_scheduler_changed() -> None:
    cr = build_delegation_constraint_ref(
        delegation_ref_id="ref:0000000000000000",
        constraint_kind=DelegationConstraintKind.TIME_BOUND,
        constraint_value="2026-06-27T12:00:00Z",
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    assert cr.constraint_kind == DelegationConstraintKind.TIME_BOUND
    se = DelegationConstraintSideEffects()
    assert se.scheduler_changed is False


def test_constraint_hash_is_not_trace_verified() -> None:
    cr = build_delegation_constraint_ref(
        delegation_ref_id="ref:0000000000000000",
        constraint_kind=DelegationConstraintKind.TIME_BOUND,
        constraint_value="x",
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    assert cr.source_label == DelegationSourceLabel.DEV_FIXTURE
    assert cr.source_label is not DelegationSourceLabel.TRACE_VERIFIED
    assert cr.constraint_hash != ""
    # constraint_hash exists but is not TRACE_VERIFIED


def test_constraint_binding_is_not_authority_grant() -> None:
    ref = _dev_fixture_ref()
    identity = _dev_fixture_identity()
    role_set = _dev_fixture_role_binding_set()
    cr = build_delegation_constraint_ref(
        delegation_ref_id=ref.delegation_ref_id,
        constraint_kind=DelegationConstraintKind.TIME_BOUND,
        constraint_value="x",
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    binding = build_delegation_constraint_binding(
        delegation_ref_id=ref.delegation_ref_id,
        delegation_identity_hash=identity.identity_hash,
        role_binding_hash=role_set.role_binding_hash,
        constraint_ref_id=cr.constraint_ref_id,
        constraint_hash=cr.constraint_hash,
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    assert binding.binding_hash != ""
    # binding exists but no authority verification
    se = DelegationConstraintSideEffects()
    assert se.authority_verified is False


def test_constraint_set_is_not_runtime_blocking() -> None:
    ref = _dev_fixture_ref()
    identity = _dev_fixture_identity()
    role_set = _dev_fixture_role_binding_set()
    cs = build_delegation_constraint_set(
        delegation_ref_id=ref.delegation_ref_id,
        delegation_identity_hash=identity.identity_hash,
        role_binding_hash=role_set.role_binding_hash,
        constraints=_dev_fixture_constraint_refs(),
        bindings=[],
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    assert cs.constraint_set_hash != ""
    se = cs.side_effects
    assert se.constraint_enforced is False
    assert se.delegation_blocked is False


# -----------------------------------------------------------------------
# Test 10: No policy/Custos/approval/Ledger/global trace/runtime mutations
# -----------------------------------------------------------------------


def test_no_policy_custos_approval_ledger_or_runtime_mutation() -> None:
    cr = build_delegation_constraint_ref(
        delegation_ref_id="ref:0000000000000000",
        constraint_kind=DelegationConstraintKind.SCOPE_BOUND,
        constraint_value="x",
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    # The constraint itself has no such fields
    canon = cr.to_canonical_dict()
    assert "policy_called" not in canon
    assert "custos_called" not in canon
    assert "approval_created" not in canon
    assert "ledger_written" not in canon
    assert "global_trace_written" not in canon
    assert "runtime_mutated" not in canon


# -----------------------------------------------------------------------
# Test 11: DEV_FIXTURE chain works end-to-end
# -----------------------------------------------------------------------


def test_dev_fixture_chain_p1_8_2_role_set_feeds_p1_8_3_constraints() -> None:
    """P1.8.2 DEV_FIXTURE DelegationRoleBindingSet → P1.8.3 constraints."""
    ref = _dev_fixture_ref()
    identity = _dev_fixture_identity()
    role_set = _dev_fixture_role_binding_set()

    # Verify P1.8.2 fixture is usable
    assert role_set.binding_set_id != ""
    assert role_set.role_binding_hash != ""

    crs = _dev_fixture_constraint_refs()
    assert len(crs) == 6

    bindings = [
        build_delegation_constraint_binding(
            delegation_ref_id=ref.delegation_ref_id,
            delegation_identity_hash=identity.identity_hash,
            role_binding_hash=role_set.role_binding_hash,
            constraint_ref_id=cr.constraint_ref_id,
            constraint_hash=cr.constraint_hash,
            source_label=DelegationSourceLabel.DEV_FIXTURE,
        )
        for cr in crs
    ]

    cs = build_delegation_constraint_set(
        delegation_ref_id=ref.delegation_ref_id,
        delegation_identity_hash=identity.identity_hash,
        role_binding_hash=role_set.role_binding_hash,
        constraints=crs,
        bindings=bindings,
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    assert cs.constraint_set_hash != ""
    assert len(cs.constraints) == 6
    assert len(cs.bindings) == 6


# -----------------------------------------------------------------------
# Test 12: from_dict round-trips
# -----------------------------------------------------------------------


def test_constraint_ref_from_dict_round_trip() -> None:
    cr = build_delegation_constraint_ref(
        delegation_ref_id="ref:0000000000000000",
        constraint_kind=DelegationConstraintKind.TIME_BOUND,
        constraint_value="x",
        constraint_severity=DelegationConstraintSeverity.HIGH,
        required_review=True,
        review_ref="review:xyz",
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    canon = cr.to_canonical_dict()
    cr2 = DelegationConstraintRef.from_dict(canon)
    assert cr2.constraint_hash == cr.constraint_hash
    assert cr2.constraint_ref_id == cr.constraint_ref_id
    assert cr2.constraint_kind == cr.constraint_kind
    assert cr2.constraint_value == cr.constraint_value
    assert cr2.constraint_severity == cr.constraint_severity
    assert cr2.required_review == cr.required_review
    assert cr2.review_ref == cr.review_ref


def test_constraint_set_from_dict_round_trip() -> None:
    ref = _dev_fixture_ref()
    identity = _dev_fixture_identity()
    role_set = _dev_fixture_role_binding_set()
    crs = _dev_fixture_constraint_refs()
    cs = build_delegation_constraint_set(
        delegation_ref_id=ref.delegation_ref_id,
        delegation_identity_hash=identity.identity_hash,
        role_binding_hash=role_set.role_binding_hash,
        constraints=crs,
        bindings=[],
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    canon = cs.to_canonical_dict()
    cs2 = DelegationConstraintSet.from_dict(canon)
    assert cs2.constraint_set_hash == cs.constraint_set_hash
    assert cs2.constraint_set_id == cs.constraint_set_id
    assert len(cs2.constraints) == len(cs.constraints)
