"""P1.8.0 — Delegation / Non-Repudiation / Agent Identity Mesh Foundation tests."""
from __future__ import annotations

import importlib
import inspect
import json
import pkgutil
import sys
from dataclasses import fields
from typing import Any

import pytest

from agentic_runtime.delegation import (
    DELEGATION_SCHEMA_VERSION,
    DELEGATION_UNAVAILABLE_BINDINGS,
    DelegationActorKind,
    DelegationAuthorityKind,
    DelegationConstraintKind,
    DelegationFoundationCapability,
    DelegationRecord,
    DelegationSideEffects,
    DelegationSourceLabel,
    DelegationSubjectKind,
    DelegationUnknownFieldError,
    NonRepudiationProofStatus,
    build_agent_identity_mesh_ref,
    build_delegation_actor_ref,
    build_delegation_authority_ref,
    build_delegation_constraint,
    build_delegation_foundation_status,
    build_delegation_record,
    build_delegation_subject,
    build_non_repudiation_ref,
    hash_delegation_record,
    serialize_delegation_record,
    to_canonical_dict,
    to_canonical_json,
)

DEV_FIXTURE_CREATED_AT = "2026-06-26T00:00:00Z"

_FORBIDDEN_RUNTIME_MODULES = frozenset({
    "agentic_runtime.runtime",
    "agentic_runtime.trace",
    "agentic_runtime.sandbox",
    "agentic_runtime.sandbox_policy",
    "agentic_runtime.approval",
    "agentic_runtime.policy",
    "agentic_runtime.tools",
    "agentic_runtime.cli",
    "agentic_runtime.ledger",
    "agentic_runtime.path_governance",
    "agentic_runtime.policy_cards",
})

_ENFORCEMENT_METHOD_NAMES = frozenset({
    "enforce",
    "block",
    "apply",
    "approve",
    "submit",
    "execute",
    "resolve",
    "verify_signature",
    "activate",
    "write_ledger",
})

_FORBIDDEN_RECORD_FIELD_NAMES = frozenset({
    "approved",
    "authorized",
    "permission_granted",
    "enforced",
    "verified",
    "executed",
})


def _dev_fixture_chain(**record_overrides: Any) -> DelegationRecord:
    delegator = record_overrides.pop(
        "delegator",
        build_delegation_actor_ref(
            DelegationActorKind.OPERATOR,
            "fixture-operator",
            source_label=DelegationSourceLabel.DEV_FIXTURE,
        ),
    )
    delegate = record_overrides.pop(
        "delegate",
        build_delegation_actor_ref(
            DelegationActorKind.AGENT,
            "fixture-agent",
            source_label=DelegationSourceLabel.DEV_FIXTURE,
        ),
    )
    subject = record_overrides.pop(
        "subject",
        build_delegation_subject(
            DelegationSubjectKind.ACTION,
            "fixture-action-ref",
            description="DEV_FIXTURE delegated action subject",
            source_label=DelegationSourceLabel.DEV_FIXTURE,
        ),
    )
    authority_ref = record_overrides.pop(
        "authority_ref",
        build_delegation_authority_ref(
            DelegationAuthorityKind.OPERATOR_DECLARED,
            "operator-declared fixture authority context",
            source_label=DelegationSourceLabel.DEV_FIXTURE,
        ),
    )
    constraints = record_overrides.pop(
        "constraints",
        [
            build_delegation_constraint(
                DelegationConstraintKind.SCOPE_BOUND,
                "fixture-scope",
                required_review=True,
                source_label=DelegationSourceLabel.DEV_FIXTURE,
            ),
        ],
    )
    non_repudiation_ref = record_overrides.pop(
        "non_repudiation_ref",
        build_non_repudiation_ref(
            proof_status=NonRepudiationProofStatus.REFERENCE_ONLY,
            source_label=DelegationSourceLabel.DEV_FIXTURE,
        ),
    )
    identity_mesh_ref = record_overrides.pop(
        "identity_mesh_ref",
        build_agent_identity_mesh_ref(
            "fixture-agent-ref",
            "fixture-identity-ref",
            "fixture-mesh-scope",
            relationship_ref="fixture-relationship",
            source_label=DelegationSourceLabel.DEV_FIXTURE,
        ),
    )
    return build_delegation_record(
        delegator,
        delegate,
        subject,
        authority_ref,
        constraints,
        non_repudiation_ref,
        identity_mesh_ref,
        created_at=DEV_FIXTURE_CREATED_AT,
        source_label=DelegationSourceLabel.DEV_FIXTURE,
        **record_overrides,
    )


def test_package_imports_from_agentic_runtime_delegation() -> None:
    import agentic_runtime.delegation as delegation

    assert delegation.__all__
    status = build_delegation_foundation_status()
    assert status.schema_version == "delegation_foundation_status.v1"


def test_delegation_actor_ref_builds_deterministically() -> None:
    first = build_delegation_actor_ref(
        DelegationActorKind.OPERATOR,
        "operator-alpha",
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    second = build_delegation_actor_ref(
        DelegationActorKind.OPERATOR,
        "operator-alpha",
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    assert first == second
    assert first.actor_ref_hash == second.actor_ref_hash
    assert first.source_label is DelegationSourceLabel.DEV_FIXTURE


def test_delegation_subject_builds_deterministically() -> None:
    first = build_delegation_subject(
        DelegationSubjectKind.TASK,
        "task-ref-001",
        description="fixture task",
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    second = build_delegation_subject(
        DelegationSubjectKind.TASK,
        "task-ref-001",
        description="fixture task",
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    assert first == second
    assert first.subject_hash == second.subject_hash


def test_delegation_authority_ref_does_not_imply_granted_authority() -> None:
    authority_ref = build_delegation_authority_ref(
        DelegationAuthorityKind.POLICY_CONTEXT_REFERENCED,
        "referenced policy context only",
        policy_context_ref="policy-context-fixture",
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    payload = authority_ref.to_canonical_dict()
    assert "granted" not in payload
    assert "authorized" not in payload
    assert authority_ref.authority_kind is DelegationAuthorityKind.POLICY_CONTEXT_REFERENCED


def test_delegation_constraint_is_descriptive_and_not_enforced() -> None:
    constraint = build_delegation_constraint(
        DelegationConstraintKind.OPERATOR_REVIEW_REQUIRED,
        "operator review required before action",
        required_review=True,
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    payload = constraint.to_canonical_dict()
    assert payload["required_review"] is True
    assert "enforced" not in payload
    assert constraint.constraint_kind is DelegationConstraintKind.OPERATOR_REVIEW_REQUIRED


def test_non_repudiation_ref_defaults_to_reference_only() -> None:
    non_repudiation_ref = build_non_repudiation_ref(
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    assert non_repudiation_ref.proof_status is NonRepudiationProofStatus.REFERENCE_ONLY
    assert non_repudiation_ref.evidence_ref is None
    assert non_repudiation_ref.signature_ref is None


def test_trace_referenced_is_not_trace_verified() -> None:
    non_repudiation_ref = build_non_repudiation_ref(
        proof_status=NonRepudiationProofStatus.TRACE_REFERENCED,
        trace_ref="trace-ref-fixture",
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    assert non_repudiation_ref.proof_status is NonRepudiationProofStatus.TRACE_REFERENCED
    assert non_repudiation_ref.proof_status is not NonRepudiationProofStatus.REFERENCE_ONLY
    assert DelegationSourceLabel.TRACE_VERIFIED.value not in (
        non_repudiation_ref.to_canonical_dict().values()
    )


def test_signature_referenced_is_not_crypto_finality() -> None:
    non_repudiation_ref = build_non_repudiation_ref(
        proof_status=NonRepudiationProofStatus.SIGNATURE_REFERENCED,
        signature_ref="signature-ref-fixture",
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    payload = non_repudiation_ref.to_canonical_dict()
    assert payload["proof_status"] == NonRepudiationProofStatus.SIGNATURE_REFERENCED.value
    assert "verified" not in payload
    assert "final" not in payload


def test_agent_identity_mesh_ref_does_not_activate_or_resolve_mesh() -> None:
    mesh_ref = build_agent_identity_mesh_ref(
        "agent-ref-fixture",
        "identity-ref-fixture",
        "mesh-scope-fixture",
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    payload = mesh_ref.to_canonical_dict()
    assert "activated" not in payload
    assert "resolved" not in payload
    assert mesh_ref.source_label is DelegationSourceLabel.DEV_FIXTURE


def test_delegation_record_builds_from_dev_fixture_components() -> None:
    record = _dev_fixture_chain()
    assert record.schema_version == DELEGATION_SCHEMA_VERSION
    assert record.source_label is DelegationSourceLabel.DEV_FIXTURE
    assert record.delegator.source_label is DelegationSourceLabel.DEV_FIXTURE
    assert record.delegate.source_label is DelegationSourceLabel.DEV_FIXTURE
    assert record.non_repudiation_ref.proof_status is NonRepudiationProofStatus.REFERENCE_ONLY


def test_identical_record_input_produces_identical_record_hash() -> None:
    first = _dev_fixture_chain()
    second = _dev_fixture_chain()
    assert first.record_hash == second.record_hash
    assert hash_delegation_record(first) == hash_delegation_record(second)
    assert len(first.record_hash) == 64


def test_changed_subject_delegate_or_constraint_changes_record_hash() -> None:
    base = _dev_fixture_chain()
    changed_subject = _dev_fixture_chain(
        subject=build_delegation_subject(
            DelegationSubjectKind.OUTPUT,
            "different-subject-ref",
            source_label=DelegationSourceLabel.DEV_FIXTURE,
        ),
    )
    changed_delegate = _dev_fixture_chain(
        delegate=build_delegation_actor_ref(
            DelegationActorKind.SERVICE,
            "different-delegate",
            source_label=DelegationSourceLabel.DEV_FIXTURE,
        ),
    )
    changed_constraint = _dev_fixture_chain(
        constraints=[
            build_delegation_constraint(
                DelegationConstraintKind.TIME_BOUND,
                "different-constraint",
                source_label=DelegationSourceLabel.DEV_FIXTURE,
            ),
        ],
    )
    assert changed_subject.record_hash != base.record_hash
    assert changed_delegate.record_hash != base.record_hash
    assert changed_constraint.record_hash != base.record_hash


def test_serialization_is_json_safe_and_deterministic() -> None:
    record = _dev_fixture_chain()
    first_json = serialize_delegation_record(record)
    second_json = serialize_delegation_record(record)
    assert first_json == second_json
    decoded = json.loads(first_json)
    assert decoded["record_hash"] == record.record_hash
    assert to_canonical_json(record) == first_json
    assert to_canonical_dict(record) == decoded


def test_source_and_truth_labels_are_visible() -> None:
    record = _dev_fixture_chain()
    status = build_delegation_foundation_status()
    assert record.source_label.value == "DEV_FIXTURE"
    assert status.status_label is DelegationSourceLabel.DEV_FIXTURE
    assert status.capabilities[DelegationFoundationCapability.FOUNDATION_SCHEMA.value] == "LIVE"


def test_unavailable_reasons_exist_for_future_surfaces() -> None:
    status = build_delegation_foundation_status()
    assert status.unavailable_bindings == DELEGATION_UNAVAILABLE_BINDINGS
    assert "Projection/API/Event/Read Model" in status.unavailable_bindings
    assert "CLI/Shell/TUI Binding" in status.unavailable_bindings
    assert "Ledger Write" in status.unavailable_bindings
    assert status.capabilities[DelegationFoundationCapability.CLI_SHELL_TUI.value] == "UNAVAILABLE"


def test_all_delegation_side_effects_booleans_are_false() -> None:
    record = _dev_fixture_chain()
    status = build_delegation_foundation_status()
    for side_effects in (record.side_effects, status.side_effects, DelegationSideEffects()):
        for item in fields(side_effects):
            assert getattr(side_effects, item.name) is False


def test_no_field_implies_approval_permission_enforcement_or_verification() -> None:
    record = _dev_fixture_chain()
    record_fields = {item.name for item in fields(record)}
    side_effect_fields = {item.name for item in fields(DelegationSideEffects())}
    assert _FORBIDDEN_RECORD_FIELD_NAMES.isdisjoint(record_fields)
    assert side_effect_fields == {
        "policy_called",
        "custos_called",
        "approval_created",
        "ledger_written",
        "global_trace_written",
        "runtime_mutated",
        "delegation_enforced",
        "agent_activated",
        "identity_mesh_resolved",
        "crypto_signature_verified",
    }
    for name in side_effect_fields:
        assert getattr(record.side_effects, name) is False


def test_invalid_enum_or_value_input_fails_closed() -> None:
    with pytest.raises(Exception):
        build_delegation_actor_ref("NOT_A_KIND", "bad-actor")

    payload = _dev_fixture_chain().to_canonical_dict()
    payload["shadow_permission_grant"] = True
    with pytest.raises(DelegationUnknownFieldError):
        DelegationRecord.from_dict(payload)


def test_foundation_status_includes_schema_version_and_status_hash() -> None:
    first = build_delegation_foundation_status()
    second = build_delegation_foundation_status()
    assert first.schema_version == "delegation_foundation_status.v1"
    assert first.status_hash
    assert len(first.status_hash) == 64
    assert first.status_hash == second.status_hash


def test_dev_fixture_path_is_explicit_in_tests() -> None:
    record = _dev_fixture_chain()
    status = build_delegation_foundation_status()
    assert record.source_label is DelegationSourceLabel.DEV_FIXTURE
    assert record.delegator.source_label is DelegationSourceLabel.DEV_FIXTURE
    assert record.delegate.source_label is DelegationSourceLabel.DEV_FIXTURE
    assert record.subject.source_label is DelegationSourceLabel.DEV_FIXTURE
    assert record.authority_ref.source_label is DelegationSourceLabel.DEV_FIXTURE
    assert record.constraints[0].source_label is DelegationSourceLabel.DEV_FIXTURE
    assert record.non_repudiation_ref.source_label is DelegationSourceLabel.DEV_FIXTURE
    assert record.identity_mesh_ref.source_label is DelegationSourceLabel.DEV_FIXTURE
    assert status.status_label is DelegationSourceLabel.DEV_FIXTURE
    assert record.created_at == DEV_FIXTURE_CREATED_AT


def test_no_runtime_boundary_imports() -> None:
    import agentic_runtime.delegation as delegation

    loaded_modules = [
        name
        for name in sys.modules
        if name.startswith("agentic_runtime.delegation")
    ]
    assert loaded_modules

    for module_name in loaded_modules:
        module = sys.modules[module_name]
        for attr_name in dir(module):
            obj = getattr(module, attr_name, None)
            if obj is None or not hasattr(obj, "__module__"):
                continue
            imported_module = getattr(obj, "__module__", "")
            for forbidden in _FORBIDDEN_RUNTIME_MODULES:
                assert not imported_module.startswith(forbidden)

    module_names = [
        info.name
        for info in pkgutil.iter_modules(delegation.__path__, prefix=f"{delegation.__name__}.")
    ]
    for module_name in module_names:
        source = inspect.getsource(importlib.import_module(module_name))
        for forbidden in _FORBIDDEN_RUNTIME_MODULES:
            assert f"from {forbidden}" not in source
            assert f"import {forbidden}" not in source


def test_no_enforcement_methods_on_public_classes() -> None:
    import agentic_runtime.delegation as delegation

    for name in delegation.__all__:
        obj = getattr(delegation, name)
        if inspect.isclass(obj):
            methods = {
                member
                for member, _ in inspect.getmembers(obj, predicate=inspect.isfunction)
            }
            assert not _ENFORCEMENT_METHOD_NAMES & methods
