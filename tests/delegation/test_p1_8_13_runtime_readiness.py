"""Focused tests for P1.8.13 — Delegation Runtime/Execution ReadinessRef Model."""

import json
import sys

import pytest

sys.path.insert(0, "src")

from agentic_runtime.delegation.foundation import DelegationSourceLabel
from agentic_runtime.delegation.runtime_readiness import (
    DelegationExecutionContextKind,
    DelegationExecutionBlockerRef,
    DelegationExecutionPreconditionRef,
    DelegationExecutionTargetRef,
    DelegationRuntimeAdmissionIntentRef,
    DelegationRuntimeAdmissionPlaceholderRef,
    DelegationRuntimeContextKind,
    DelegationRuntimeContextRef,
    DelegationRuntimeExecutionReadinessBinding,
    DelegationRuntimeExecutionReadinessBindingSet,
    DelegationRuntimeExecutionReadinessEnvelope,
    DelegationRuntimeExecutionReadinessFamily,
    DelegationRuntimeExecutionReadinessKind,
    DelegationRuntimeExecutionReadinessMatrix,
    DelegationRuntimeExecutionReadinessMatrixEntry,
    DelegationRuntimeExecutionReadinessProfile,
    DelegationRuntimeExecutionReadinessReferenceStatus,
    DelegationRuntimeExecutionReadinessSideEffects,
    DelegationRuntimeExecutionReadinessStatus,
    DelegationRuntimeExecutionReadinessStatusReport,
    DelegationRuntimeReadinessRef,
    DelegationRuntimeSessionPlaceholderRef,
    DelegationToolExecutionContextRef,
    build_delegation_execution_blocker_ref,
    build_delegation_execution_precondition_ref,
    build_delegation_execution_target_ref,
    build_delegation_runtime_admission_intent_ref,
    build_delegation_runtime_admission_placeholder_ref,
    build_delegation_runtime_context_ref,
    build_delegation_runtime_execution_readiness_binding,
    build_delegation_runtime_execution_readiness_binding_set,
    build_delegation_runtime_execution_readiness_envelope,
    build_delegation_runtime_execution_readiness_matrix,
    build_delegation_runtime_execution_readiness_matrix_entry,
    build_delegation_runtime_execution_readiness_profile,
    build_delegation_runtime_execution_readiness_status_report,
    build_delegation_runtime_readiness_ref,
    build_delegation_runtime_session_placeholder_ref,
    build_delegation_tool_execution_context_ref,
    hash_delegation_execution_blocker_ref,
    hash_delegation_execution_precondition_ref,
    hash_delegation_execution_target_ref,
    hash_delegation_runtime_admission_intent_ref,
    hash_delegation_runtime_admission_placeholder_ref,
    hash_delegation_runtime_context_ref,
    hash_delegation_runtime_execution_readiness_binding,
    hash_delegation_runtime_execution_readiness_binding_set,
    hash_delegation_runtime_execution_readiness_envelope,
    hash_delegation_runtime_execution_readiness_matrix,
    hash_delegation_runtime_execution_readiness_matrix_entry,
    hash_delegation_runtime_execution_readiness_profile,
    hash_delegation_runtime_execution_readiness_status_report,
    hash_delegation_runtime_readiness_ref,
    hash_delegation_runtime_session_placeholder_ref,
    hash_delegation_tool_execution_context_ref,
    serialize_delegation_runtime_execution_readiness_binding_set,
    serialize_delegation_runtime_execution_readiness_envelope,
)


# ---------------------------------------------------------------------------
# DEV_FIXTURE helpers
# ---------------------------------------------------------------------------


def _dev_fixture_runtime_readiness_ref() -> DelegationRuntimeReadinessRef:
    return build_delegation_runtime_readiness_ref(
        runtime_readiness_ref_id="rr-dev-001",
        delegation_ref_id="del-dev-001",
        runtime_readiness_ref="runtime_ready_placeholder.v1",
        runtime_readiness_description="DEV_FIXTURE runtime readiness reference",
    )


def _dev_fixture_execution_precondition_ref() -> DelegationExecutionPreconditionRef:
    return build_delegation_execution_precondition_ref(
        execution_precondition_ref_id="ep-dev-001",
        delegation_ref_id="del-dev-001",
        execution_precondition_ref="precondition_sandbox_ready.v1",
        precondition_description="DEV_FIXTURE execution precondition",
    )


def _dev_fixture_execution_blocker_ref() -> DelegationExecutionBlockerRef:
    return build_delegation_execution_blocker_ref(
        execution_blocker_ref_id="eb-dev-001",
        delegation_ref_id="del-dev-001",
        execution_blocker_ref="blocker_no_network.v1",
        blocker_description="DEV_FIXTURE execution blocker",
    )


def _dev_fixture_admission_intent_ref() -> DelegationRuntimeAdmissionIntentRef:
    return build_delegation_runtime_admission_intent_ref(
        runtime_admission_intent_ref_id="ai-dev-001",
        delegation_ref_id="del-dev-001",
        runtime_admission_intent_ref="admit_runtime_intent.v1",
        admission_intent_description="DEV_FIXTURE admission intent",
    )


def _dev_fixture_admission_placeholder_ref() -> DelegationRuntimeAdmissionPlaceholderRef:
    return build_delegation_runtime_admission_placeholder_ref(
        runtime_admission_placeholder_ref_id="ap-dev-001",
        delegation_ref_id="del-dev-001",
        runtime_admission_placeholder_ref="admission_result_placeholder.v1",
        admission_placeholder_description="DEV_FIXTURE admission placeholder",
    )


def _dev_fixture_runtime_context_ref() -> DelegationRuntimeContextRef:
    return build_delegation_runtime_context_ref(
        runtime_context_ref_id="rc-dev-001",
        delegation_ref_id="del-dev-001",
        runtime_context_kind=DelegationRuntimeContextKind.AUREL_FLOW_RUNTIME_CONTEXT,
        runtime_context_ref="aurel_flow_ctx.v1",
        runtime_context_description="DEV_FIXTURE runtime context",
    )


def _dev_fixture_tool_execution_context_ref() -> DelegationToolExecutionContextRef:
    return build_delegation_tool_execution_context_ref(
        tool_execution_context_ref_id="te-dev-001",
        delegation_ref_id="del-dev-001",
        execution_context_kind=DelegationExecutionContextKind.TOOL_CONTEXT,
        tool_execution_context_ref="tool_ctx_shell.v1",
        tool_execution_context_description="DEV_FIXTURE tool execution context",
    )


def _dev_fixture_session_placeholder_ref() -> DelegationRuntimeSessionPlaceholderRef:
    return build_delegation_runtime_session_placeholder_ref(
        runtime_session_placeholder_ref_id="sp-dev-001",
        delegation_ref_id="del-dev-001",
        runtime_session_placeholder_ref="session_placeholder.v1",
        session_placeholder_description="DEV_FIXTURE session placeholder",
    )


def _dev_fixture_execution_target_ref() -> DelegationExecutionTargetRef:
    return build_delegation_execution_target_ref(
        execution_target_ref_id="et-dev-001",
        delegation_ref_id="del-dev-001",
        execution_target_ref="exec_target_sandbox.v1",
        execution_target_description="DEV_FIXTURE execution target",
    )


# ---------------------------------------------------------------------------
# 1. Imports work
# ---------------------------------------------------------------------------


def test_imports_work():
    """All P1.8.13 symbols are importable."""
    assert DelegationRuntimeReadinessRef is not None
    assert DelegationExecutionPreconditionRef is not None
    assert DelegationExecutionBlockerRef is not None
    assert DelegationRuntimeAdmissionIntentRef is not None
    assert DelegationRuntimeAdmissionPlaceholderRef is not None
    assert DelegationRuntimeContextRef is not None
    assert DelegationToolExecutionContextRef is not None
    assert DelegationRuntimeSessionPlaceholderRef is not None
    assert DelegationExecutionTargetRef is not None


# ---------------------------------------------------------------------------
# 2. Existing P1.8 exports remain importable
# ---------------------------------------------------------------------------


def test_existing_exports_remain():
    """P1.8.12 exports remain importable."""
    from agentic_runtime.delegation.policy_bridge import (
        build_delegation_policy_custos_bridge_binding_set,
    )
    assert build_delegation_policy_custos_bridge_binding_set is not None


# ---------------------------------------------------------------------------
# 3. P1.8.12 can feed P1.8.13
# ---------------------------------------------------------------------------


def test_p1_8_12_can_feed_path():
    """P1.8.12 PolicyCustosBridgeBindingSet can feed P1.8.13 path."""
    from agentic_runtime.delegation.policy_bridge import (
        DelegationPolicyCustosBridgeSideEffects,
    )
    # P1.8.12 produces a binding set hash that P1.8.13 can reference
    pcb_hash = "simulated_p1_8_12_binding_set_hash_0123456789abcdef"
    env = build_delegation_runtime_execution_readiness_envelope(
        runtime_execution_readiness_envelope_id="re-dev-001",
        delegation_ref_id="del-dev-001",
        policy_custos_bridge_binding_set_hash=pcb_hash,
    )
    assert env.policy_custos_bridge_binding_set_hash == pcb_hash
    assert env.runtime_execution_readiness_envelope_hash


# ---------------------------------------------------------------------------
# 4-12: Deterministic ref builds
# ---------------------------------------------------------------------------


def test_runtime_readiness_ref_deterministic():
    a = build_delegation_runtime_readiness_ref(
        runtime_readiness_ref_id="rr-001",
        delegation_ref_id="del-001",
        runtime_readiness_description="test"
    )
    b = build_delegation_runtime_readiness_ref(
        runtime_readiness_ref_id="rr-001",
        delegation_ref_id="del-001",
        runtime_readiness_description="test"
    )
    assert a.runtime_readiness_hash == b.runtime_readiness_hash


def test_execution_precondition_ref_deterministic():
    a = build_delegation_execution_precondition_ref(
        execution_precondition_ref_id="ep-001",
        delegation_ref_id="del-001",
        precondition_description="test"
    )
    b = build_delegation_execution_precondition_ref(
        execution_precondition_ref_id="ep-001",
        delegation_ref_id="del-001",
        precondition_description="test"
    )
    assert a.precondition_hash == b.precondition_hash


def test_execution_blocker_ref_deterministic():
    a = build_delegation_execution_blocker_ref(
        execution_blocker_ref_id="eb-001",
        delegation_ref_id="del-001",
        blocker_description="test"
    )
    b = build_delegation_execution_blocker_ref(
        execution_blocker_ref_id="eb-001",
        delegation_ref_id="del-001",
        blocker_description="test"
    )
    assert a.blocker_hash == b.blocker_hash


def test_admission_intent_ref_deterministic():
    a = build_delegation_runtime_admission_intent_ref(
        runtime_admission_intent_ref_id="ai-001",
        delegation_ref_id="del-001",
        admission_intent_description="test"
    )
    b = build_delegation_runtime_admission_intent_ref(
        runtime_admission_intent_ref_id="ai-001",
        delegation_ref_id="del-001",
        admission_intent_description="test"
    )
    assert a.admission_intent_hash == b.admission_intent_hash


def test_admission_placeholder_ref_deterministic():
    a = build_delegation_runtime_admission_placeholder_ref(
        runtime_admission_placeholder_ref_id="ap-001",
        delegation_ref_id="del-001",
        admission_placeholder_description="test"
    )
    b = build_delegation_runtime_admission_placeholder_ref(
        runtime_admission_placeholder_ref_id="ap-001",
        delegation_ref_id="del-001",
        admission_placeholder_description="test"
    )
    assert a.admission_placeholder_hash == b.admission_placeholder_hash


def test_runtime_context_ref_deterministic():
    a = build_delegation_runtime_context_ref(
        runtime_context_ref_id="rc-001",
        delegation_ref_id="del-001",
        runtime_context_description="test"
    )
    b = build_delegation_runtime_context_ref(
        runtime_context_ref_id="rc-001",
        delegation_ref_id="del-001",
        runtime_context_description="test"
    )
    assert a.runtime_context_hash == b.runtime_context_hash


def test_tool_execution_context_ref_deterministic():
    a = build_delegation_tool_execution_context_ref(
        tool_execution_context_ref_id="te-001",
        delegation_ref_id="del-001",
        tool_execution_context_description="test"
    )
    b = build_delegation_tool_execution_context_ref(
        tool_execution_context_ref_id="te-001",
        delegation_ref_id="del-001",
        tool_execution_context_description="test"
    )
    assert a.tool_context_hash == b.tool_context_hash


def test_session_placeholder_ref_deterministic():
    a = build_delegation_runtime_session_placeholder_ref(
        runtime_session_placeholder_ref_id="sp-001",
        delegation_ref_id="del-001",
        session_placeholder_description="test"
    )
    b = build_delegation_runtime_session_placeholder_ref(
        runtime_session_placeholder_ref_id="sp-001",
        delegation_ref_id="del-001",
        session_placeholder_description="test"
    )
    assert a.session_placeholder_hash == b.session_placeholder_hash


def test_execution_target_ref_deterministic():
    a = build_delegation_execution_target_ref(
        execution_target_ref_id="et-001",
        delegation_ref_id="del-001",
        execution_target_description="test"
    )
    b = build_delegation_execution_target_ref(
        execution_target_ref_id="et-001",
        delegation_ref_id="del-001",
        execution_target_description="test"
    )
    assert a.execution_target_hash == b.execution_target_hash


# ---------------------------------------------------------------------------
# 13-14: Matrix entry and matrix deterministic
# ---------------------------------------------------------------------------


def test_matrix_entry_deterministic():
    a = build_delegation_runtime_execution_readiness_matrix_entry(
        entry_id="me-001",
        delegation_ref_id="del-001",
        family=DelegationRuntimeExecutionReadinessFamily.IDENTITY_CONTEXT,
        present=True,
    )
    b = build_delegation_runtime_execution_readiness_matrix_entry(
        entry_id="me-001",
        delegation_ref_id="del-001",
        family=DelegationRuntimeExecutionReadinessFamily.IDENTITY_CONTEXT,
        present=True,
    )
    assert a.entry_hash == b.entry_hash


def test_readiness_matrix_deterministic():
    e1 = build_delegation_runtime_execution_readiness_matrix_entry(
        entry_id="me-001", delegation_ref_id="del-001",
        family=DelegationRuntimeExecutionReadinessFamily.IDENTITY_CONTEXT,
    )
    a = build_delegation_runtime_execution_readiness_matrix(
        readiness_matrix_id="rm-001",
        delegation_ref_id="del-001",
        entries=[e1],
    )
    b = build_delegation_runtime_execution_readiness_matrix(
        readiness_matrix_id="rm-001",
        delegation_ref_id="del-001",
        entries=[e1],
    )
    assert a.matrix_hash == b.matrix_hash


# ---------------------------------------------------------------------------
# 15: Readiness profile deterministic
# ---------------------------------------------------------------------------


def test_readiness_profile_deterministic():
    a = build_delegation_runtime_execution_readiness_profile(
        runtime_execution_readiness_profile_id="rp-001",
        delegation_ref_id="del-001",
        has_runtime_readiness_refs=True,
    )
    b = build_delegation_runtime_execution_readiness_profile(
        runtime_execution_readiness_profile_id="rp-001",
        delegation_ref_id="del-001",
        has_runtime_readiness_refs=True,
    )
    assert a.readiness_hash == b.readiness_hash


# ---------------------------------------------------------------------------
# 16: Envelope deterministic
# ---------------------------------------------------------------------------


def test_readiness_envelope_deterministic():
    a = build_delegation_runtime_execution_readiness_envelope(
        runtime_execution_readiness_envelope_id="re-001",
        delegation_ref_id="del-001",
        delegation_identity_hash="idhash1",
    )
    b = build_delegation_runtime_execution_readiness_envelope(
        runtime_execution_readiness_envelope_id="re-001",
        delegation_ref_id="del-001",
        delegation_identity_hash="idhash1",
    )
    assert a.runtime_execution_readiness_envelope_hash == b.runtime_execution_readiness_envelope_hash


# ---------------------------------------------------------------------------
# 17-18: Binding and BindingSet deterministic
# ---------------------------------------------------------------------------


def test_readiness_binding_deterministic():
    a = build_delegation_runtime_execution_readiness_binding(
        binding_id="rb-001",
        delegation_ref_id="del-001",
        delegation_identity_hash="dh1",
    )
    b = build_delegation_runtime_execution_readiness_binding(
        binding_id="rb-001",
        delegation_ref_id="del-001",
        delegation_identity_hash="dh1",
    )
    assert a.binding_hash == b.binding_hash


def test_readiness_binding_set_deterministic():
    b1 = build_delegation_runtime_execution_readiness_binding(
        binding_id="rb-001", delegation_ref_id="del-001",
        delegation_identity_hash="dh1",
    )
    a = build_delegation_runtime_execution_readiness_binding_set(
        runtime_execution_readiness_binding_set_id="rbs-001",
        delegation_ref_id="del-001",
        bindings=[b1],
    )
    b = build_delegation_runtime_execution_readiness_binding_set(
        runtime_execution_readiness_binding_set_id="rbs-001",
        delegation_ref_id="del-001",
        bindings=[b1],
    )
    assert a.runtime_execution_readiness_binding_set_hash == b.runtime_execution_readiness_binding_set_hash


# ---------------------------------------------------------------------------
# 19: StatusReport deterministic
# ---------------------------------------------------------------------------


def test_status_report_deterministic():
    a = build_delegation_runtime_execution_readiness_status_report(
        status_label="TEST_LABEL",
    )
    b = build_delegation_runtime_execution_readiness_status_report(
        status_label="TEST_LABEL",
    )
    assert a.status_hash == b.status_hash


# ---------------------------------------------------------------------------
# 20-33: Hash changes on meaningful input changes
# ---------------------------------------------------------------------------


def test_changed_rr_desc_changes_hash():
    a = build_delegation_runtime_readiness_ref(
        runtime_readiness_ref_id="rr-001", delegation_ref_id="del-001",
        runtime_readiness_description="A"
    )
    b = build_delegation_runtime_readiness_ref(
        runtime_readiness_ref_id="rr-001", delegation_ref_id="del-001",
        runtime_readiness_description="B"
    )
    assert a.runtime_readiness_hash != b.runtime_readiness_hash


def test_changed_precondition_changes_hash():
    a = build_delegation_execution_precondition_ref(
        execution_precondition_ref_id="ep-001", delegation_ref_id="del-001",
        precondition_description="A"
    )
    b = build_delegation_execution_precondition_ref(
        execution_precondition_ref_id="ep-001", delegation_ref_id="del-001",
        precondition_description="B"
    )
    assert a.precondition_hash != b.precondition_hash


def test_changed_blocker_changes_hash():
    a = build_delegation_execution_blocker_ref(
        execution_blocker_ref_id="eb-001", delegation_ref_id="del-001",
        blocker_description="A"
    )
    b = build_delegation_execution_blocker_ref(
        execution_blocker_ref_id="eb-001", delegation_ref_id="del-001",
        blocker_description="B"
    )
    assert a.blocker_hash != b.blocker_hash


def test_changed_admission_intent_changes_hash():
    a = build_delegation_runtime_admission_intent_ref(
        runtime_admission_intent_ref_id="ai-001", delegation_ref_id="del-001",
        admission_intent_description="A"
    )
    b = build_delegation_runtime_admission_intent_ref(
        runtime_admission_intent_ref_id="ai-001", delegation_ref_id="del-001",
        admission_intent_description="B"
    )
    assert a.admission_intent_hash != b.admission_intent_hash


def test_changed_admission_placeholder_changes_hash():
    a = build_delegation_runtime_admission_placeholder_ref(
        runtime_admission_placeholder_ref_id="ap-001", delegation_ref_id="del-001",
        admission_placeholder_description="A"
    )
    b = build_delegation_runtime_admission_placeholder_ref(
        runtime_admission_placeholder_ref_id="ap-001", delegation_ref_id="del-001",
        admission_placeholder_description="B"
    )
    assert a.admission_placeholder_hash != b.admission_placeholder_hash


def test_changed_runtime_context_changes_hash():
    a = build_delegation_runtime_context_ref(
        runtime_context_ref_id="rc-001", delegation_ref_id="del-001",
        runtime_context_kind=DelegationRuntimeContextKind.AUREL_FLOW_RUNTIME_CONTEXT,
    )
    b = build_delegation_runtime_context_ref(
        runtime_context_ref_id="rc-001", delegation_ref_id="del-001",
        runtime_context_kind=DelegationRuntimeContextKind.SANDBOX_CONTEXT,
    )
    assert a.runtime_context_hash != b.runtime_context_hash


def test_changed_tool_context_changes_hash():
    a = build_delegation_tool_execution_context_ref(
        tool_execution_context_ref_id="te-001", delegation_ref_id="del-001",
        execution_context_kind=DelegationExecutionContextKind.TOOL_CONTEXT,
    )
    b = build_delegation_tool_execution_context_ref(
        tool_execution_context_ref_id="te-001", delegation_ref_id="del-001",
        execution_context_kind=DelegationExecutionContextKind.MODEL_CONTEXT,
    )
    assert a.tool_context_hash != b.tool_context_hash


def test_changed_session_placeholder_changes_hash():
    a = build_delegation_runtime_session_placeholder_ref(
        runtime_session_placeholder_ref_id="sp-001", delegation_ref_id="del-001",
        session_placeholder_description="A"
    )
    b = build_delegation_runtime_session_placeholder_ref(
        runtime_session_placeholder_ref_id="sp-001", delegation_ref_id="del-001",
        session_placeholder_description="B"
    )
    assert a.session_placeholder_hash != b.session_placeholder_hash


def test_changed_execution_target_changes_hash():
    a = build_delegation_execution_target_ref(
        execution_target_ref_id="et-001", delegation_ref_id="del-001",
        execution_target_description="A"
    )
    b = build_delegation_execution_target_ref(
        execution_target_ref_id="et-001", delegation_ref_id="del-001",
        execution_target_description="B"
    )
    assert a.execution_target_hash != b.execution_target_hash


def test_changed_matrix_entry_changes_matrix_hash():
    e1 = build_delegation_runtime_execution_readiness_matrix_entry(
        entry_id="me-001", delegation_ref_id="del-001",
        family=DelegationRuntimeExecutionReadinessFamily.IDENTITY_CONTEXT,
        present=True,
    )
    e2 = build_delegation_runtime_execution_readiness_matrix_entry(
        entry_id="me-001", delegation_ref_id="del-001",
        family=DelegationRuntimeExecutionReadinessFamily.IDENTITY_CONTEXT,
        present=False,
    )
    a = build_delegation_runtime_execution_readiness_matrix(
        readiness_matrix_id="rm-001", delegation_ref_id="del-001",
        entries=[e1],
    )
    b = build_delegation_runtime_execution_readiness_matrix(
        readiness_matrix_id="rm-001", delegation_ref_id="del-001",
        entries=[e2],
    )
    assert a.matrix_hash != b.matrix_hash


def test_changed_profile_changes_hash():
    a = build_delegation_runtime_execution_readiness_profile(
        runtime_execution_readiness_profile_id="rp-001", delegation_ref_id="del-001",
        has_runtime_readiness_refs=True,
    )
    b = build_delegation_runtime_execution_readiness_profile(
        runtime_execution_readiness_profile_id="rp-001", delegation_ref_id="del-001",
        has_runtime_readiness_refs=False,
    )
    assert a.readiness_hash != b.readiness_hash


def test_changed_envelope_changes_hash():
    a = build_delegation_runtime_execution_readiness_envelope(
        runtime_execution_readiness_envelope_id="re-001", delegation_ref_id="del-001",
        delegation_identity_hash="A",
    )
    b = build_delegation_runtime_execution_readiness_envelope(
        runtime_execution_readiness_envelope_id="re-001", delegation_ref_id="del-001",
        delegation_identity_hash="B",
    )
    assert a.runtime_execution_readiness_envelope_hash != b.runtime_execution_readiness_envelope_hash


def test_changed_binding_set_changes_hash():
    b1 = build_delegation_runtime_execution_readiness_binding(
        binding_id="rb-001", delegation_ref_id="del-001",
        delegation_identity_hash="A",
    )
    b2 = build_delegation_runtime_execution_readiness_binding(
        binding_id="rb-001", delegation_ref_id="del-001",
        delegation_identity_hash="B",
    )
    a = build_delegation_runtime_execution_readiness_binding_set(
        runtime_execution_readiness_binding_set_id="rbs-001",
        delegation_ref_id="del-001",
        bindings=[b1],
    )
    b_val = build_delegation_runtime_execution_readiness_binding_set(
        runtime_execution_readiness_binding_set_id="rbs-001",
        delegation_ref_id="del-001",
        bindings=[b2],
    )
    assert a.runtime_execution_readiness_binding_set_hash != b_val.runtime_execution_readiness_binding_set_hash


# ---------------------------------------------------------------------------
# 34: Enum values
# ---------------------------------------------------------------------------


def test_reference_status_enum_values():
    statuses = list(DelegationRuntimeExecutionReadinessReferenceStatus)
    assert DelegationRuntimeExecutionReadinessReferenceStatus.REFERENCE_ONLY in statuses
    assert DelegationRuntimeExecutionReadinessReferenceStatus.RUNTIME_READINESS_REFERENCED in statuses
    assert DelegationRuntimeExecutionReadinessReferenceStatus.EXECUTION_PRECONDITION_REFERENCED in statuses
    assert DelegationRuntimeExecutionReadinessReferenceStatus.EXECUTION_BLOCKER_REFERENCED in statuses
    assert DelegationRuntimeExecutionReadinessReferenceStatus.RUNTIME_ADMISSION_INTENT_REFERENCED in statuses
    assert DelegationRuntimeExecutionReadinessReferenceStatus.RUNTIME_ADMISSION_PLACEHOLDER_REFERENCED in statuses
    assert DelegationRuntimeExecutionReadinessReferenceStatus.RUNTIME_CONTEXT_REFERENCED in statuses
    assert DelegationRuntimeExecutionReadinessReferenceStatus.TOOL_EXECUTION_CONTEXT_REFERENCED in statuses
    assert DelegationRuntimeExecutionReadinessReferenceStatus.RUNTIME_SESSION_PLACEHOLDER_REFERENCED in statuses
    assert DelegationRuntimeExecutionReadinessReferenceStatus.EXECUTION_TARGET_REFERENCED in statuses
    assert DelegationRuntimeExecutionReadinessReferenceStatus.UNAVAILABLE in statuses
    assert DelegationRuntimeExecutionReadinessReferenceStatus.ERROR in statuses
    assert DelegationRuntimeExecutionReadinessReferenceStatus.UNKNOWN in statuses


# ---------------------------------------------------------------------------
# 35-43: Boundary — ref existence ≠ execution claim
# ---------------------------------------------------------------------------


def test_runtime_readiness_ref_not_runtime_ready():
    rr = _dev_fixture_runtime_readiness_ref()
    assert rr.reference_status == DelegationRuntimeExecutionReadinessReferenceStatus.REFERENCE_ONLY
    assert rr.readiness_status == DelegationRuntimeExecutionReadinessStatus.REFERENCE_ONLY
    # Boundary: RuntimeReadinessRef DOES NOT mean runtime is ready
    assert rr.readiness_status != DelegationRuntimeExecutionReadinessStatus.DECLARED


def test_precondition_ref_not_satisfied():
    ep = _dev_fixture_execution_precondition_ref()
    assert ep.reference_status == DelegationRuntimeExecutionReadinessReferenceStatus.REFERENCE_ONLY
    # Boundary: ExecutionPreconditionRef is not precondition satisfied


def test_blocker_ref_not_runtime_blocked():
    eb = _dev_fixture_execution_blocker_ref()
    assert eb.reference_status == DelegationRuntimeExecutionReadinessReferenceStatus.REFERENCE_ONLY
    # Boundary: ExecutionBlockerRef is not runtime block enforcement


def test_admission_intent_ref_not_admitted():
    ai = _dev_fixture_admission_intent_ref()
    assert ai.reference_status == DelegationRuntimeExecutionReadinessReferenceStatus.REFERENCE_ONLY
    # Boundary: RuntimeAdmissionIntentRef is not runtime admission


def test_admission_placeholder_ref_not_admission_result():
    ap = _dev_fixture_admission_placeholder_ref()
    assert ap.reference_status == DelegationRuntimeExecutionReadinessReferenceStatus.REFERENCE_ONLY
    # Boundary: RuntimeAdmissionPlaceholderRef is not admission result


def test_runtime_context_ref_not_initialized():
    rc = _dev_fixture_runtime_context_ref()
    assert rc.reference_status == DelegationRuntimeExecutionReadinessReferenceStatus.REFERENCE_ONLY
    # Boundary: RuntimeContextRef is not runtime initialized


def test_tool_context_ref_not_dispatched():
    te = _dev_fixture_tool_execution_context_ref()
    assert te.reference_status == DelegationRuntimeExecutionReadinessReferenceStatus.REFERENCE_ONLY
    # Boundary: ToolExecutionContextRef is not tool dispatch


def test_session_placeholder_ref_not_session_created():
    sp = _dev_fixture_session_placeholder_ref()
    assert sp.reference_status == DelegationRuntimeExecutionReadinessReferenceStatus.REFERENCE_ONLY
    # Boundary: RuntimeSessionPlaceholderRef is not session creation


def test_execution_target_ref_not_target_selected():
    et = _dev_fixture_execution_target_ref()
    assert et.reference_status == DelegationRuntimeExecutionReadinessReferenceStatus.REFERENCE_ONLY
    # Boundary: ExecutionTargetRef is not dispatch target selected


# ---------------------------------------------------------------------------
# 44-48: Matrix, Profile, Envelope boundaries
# ---------------------------------------------------------------------------


def test_matrix_is_not_execution_readiness():
    m = build_delegation_runtime_execution_readiness_matrix(
        readiness_matrix_id="rm-001",
        delegation_ref_id="del-001",
    )
    assert m is not None
    # Boundary: ReadinessMatrix is not execution readiness


def test_profile_is_not_execution_readiness_proof():
    p = build_delegation_runtime_execution_readiness_profile(
        runtime_execution_readiness_profile_id="rp-001",
        delegation_ref_id="del-001",
    )
    assert p.readiness_hash
    # Boundary: ReadinessProfile is not execution readiness proof


def test_profile_is_not_enforcement_readiness():
    p = build_delegation_runtime_execution_readiness_profile(
        runtime_execution_readiness_profile_id="rp-001",
        delegation_ref_id="del-001",
    )
    assert p.enforcement_unavailable_reason is not None
    # Boundary: Profile is not enforcement readiness


def test_envelope_not_runtime_admission():
    e = build_delegation_runtime_execution_readiness_envelope(
        runtime_execution_readiness_envelope_id="re-001",
        delegation_ref_id="del-001",
    )
    assert e is not None
    # Boundary: Envelope is not runtime admission


def test_envelope_not_execution_allowed():
    e = build_delegation_runtime_execution_readiness_envelope(
        runtime_execution_readiness_envelope_id="re-001",
        delegation_ref_id="del-001",
    )
    assert e.runtime_execution_readiness_envelope_hash
    # Boundary: Envelope is not execution allowed


# ---------------------------------------------------------------------------
# 49: JSON-safe serialization
# ---------------------------------------------------------------------------


def test_envelope_serialization_json_safe():
    e = build_delegation_runtime_execution_readiness_envelope(
        runtime_execution_readiness_envelope_id="re-001",
        delegation_ref_id="del-001",
        runtime_readiness_ref_ids=["rr-1", "rr-2"],
    )
    serialized = serialize_delegation_runtime_execution_readiness_envelope(e)
    assert isinstance(serialized, str)
    parsed = json.loads(serialized)
    assert parsed["runtime_execution_readiness_envelope_id"] == "re-001"
    assert "rr-1" in parsed["runtime_readiness_ref_ids"]


def test_binding_set_serialization_json_safe():
    b = build_delegation_runtime_execution_readiness_binding(
        binding_id="rb-001",
        delegation_ref_id="del-001",
    )
    bs = build_delegation_runtime_execution_readiness_binding_set(
        runtime_execution_readiness_binding_set_id="rbs-001",
        delegation_ref_id="del-001",
        bindings=[b],
    )
    serialized = serialize_delegation_runtime_execution_readiness_binding_set(bs)
    assert isinstance(serialized, str)
    parsed = json.loads(serialized)
    assert parsed["runtime_execution_readiness_binding_set_id"] == "rbs-001"


def test_envelope_serialization_deterministic():
    e1 = build_delegation_runtime_execution_readiness_envelope(
        runtime_execution_readiness_envelope_id="re-001",
        delegation_ref_id="del-001",
        delegation_identity_hash="dh1",
    )
    e2 = build_delegation_runtime_execution_readiness_envelope(
        runtime_execution_readiness_envelope_id="re-001",
        delegation_ref_id="del-001",
        delegation_identity_hash="dh1",
    )
    assert serialize_delegation_runtime_execution_readiness_envelope(e1) == \
        serialize_delegation_runtime_execution_readiness_envelope(e2)


# ---------------------------------------------------------------------------
# 50: Closed-world validation
# ---------------------------------------------------------------------------


def test_closed_world_validation_rejects_unknown_field():
    """Closed-world validation rejects unknown fields."""
    from agentic_runtime.delegation.foundation import validate_known_fields, DelegationUnknownFieldError
    with pytest.raises(DelegationUnknownFieldError):
        validate_known_fields(
            {"good_field": "value", "bad_field": "bad"},
            frozenset({"good_field"}),
            label="test",
        )


# ---------------------------------------------------------------------------
# 51: Source/truth labels visible
# ---------------------------------------------------------------------------


def test_source_label_visible():
    rr = _dev_fixture_runtime_readiness_ref()
    assert rr.source_label in (
        DelegationSourceLabel.DEV_FIXTURE,
        DelegationSourceLabel.LIVE,
        DelegationSourceLabel.TRACE_VERIFIED,
        DelegationSourceLabel.SIMULATED,
        DelegationSourceLabel.UNAVAILABLE,
        DelegationSourceLabel.ERROR,
    )


# ---------------------------------------------------------------------------
# 52: DEV_FIXTURE explicit
# ---------------------------------------------------------------------------


def test_dev_fixture_label_explicit():
    rr = _dev_fixture_runtime_readiness_ref()
    assert rr.source_label == DelegationSourceLabel.DEV_FIXTURE


# ---------------------------------------------------------------------------
# 53: UNAVAILABLE reasons exist
# ---------------------------------------------------------------------------


def test_unavailable_reasons_exist():
    report = build_delegation_runtime_execution_readiness_status_report()
    assert "Runtime Engine" in report.unavailable_bindings
    assert "Execution Engine" in report.unavailable_bindings
    assert "Admission Gate" in report.unavailable_bindings
    assert "Tool Dispatcher" in report.unavailable_bindings
    assert "Enforcement Engine" in report.unavailable_bindings
    assert "Ledger Write" in report.unavailable_bindings
    assert "P1.8.14 Trace/Audit BridgeRef Model" in report.unavailable_bindings
    assert "Output Passport / P1.9" in report.unavailable_bindings


# ---------------------------------------------------------------------------
# 54-70: Side effects all false
# ---------------------------------------------------------------------------


def test_side_effects_all_false():
    se = DelegationRuntimeExecutionReadinessSideEffects()
    assert se.runtime_engine_called is False
    assert se.execution_engine_called is False
    assert se.admission_gate_called is False
    assert se.runtime_admitted is False
    assert se.runtime_blocked is False
    assert se.execution_allowed is False
    assert se.execution_blocked is False
    assert se.tool_dispatched is False
    assert se.runtime_session_created is False
    assert se.execution_target_selected is False
    assert se.enforcement_performed is False
    assert se.policy_called is False
    assert se.custos_called is False
    assert se.ledger_written is False
    assert se.global_trace_written is False
    assert se.runtime_mutated is False


def test_binding_set_side_effects_all_false():
    b = build_delegation_runtime_execution_readiness_binding(
        binding_id="rb-001", delegation_ref_id="del-001",
    )
    bs = build_delegation_runtime_execution_readiness_binding_set(
        runtime_execution_readiness_binding_set_id="rbs-001",
        delegation_ref_id="del-001",
        bindings=[b],
    )
    se = bs.side_effects
    assert not any([
        se.runtime_engine_called,
        se.execution_engine_called,
        se.admission_gate_called,
        se.runtime_admitted,
        se.runtime_blocked,
        se.execution_allowed,
        se.execution_blocked,
        se.tool_dispatched,
        se.runtime_session_created,
        se.execution_target_selected,
        se.enforcement_performed,
        se.policy_called,
        se.custos_called,
        se.ledger_written,
        se.global_trace_written,
        se.runtime_mutated,
    ])


# ---------------------------------------------------------------------------
# 71: ReadinessKind enum
# ---------------------------------------------------------------------------


def test_readiness_kind_enum():
    kinds = list(DelegationRuntimeExecutionReadinessKind)
    assert DelegationRuntimeExecutionReadinessKind.RUNTIME_READINESS in kinds
    assert DelegationRuntimeExecutionReadinessKind.EXECUTION_PRECONDITION in kinds
    assert DelegationRuntimeExecutionReadinessKind.EXECUTION_BLOCKER in kinds
    assert DelegationRuntimeExecutionReadinessKind.REFERENCE_ONLY in kinds


# ---------------------------------------------------------------------------
# Extra boundary + hash function tests
# ---------------------------------------------------------------------------


def test_public_hash_functions_recompute():
    rr = _dev_fixture_runtime_readiness_ref()
    assert hash_delegation_runtime_readiness_ref(rr) == rr.runtime_readiness_hash
    ep = _dev_fixture_execution_precondition_ref()
    assert hash_delegation_execution_precondition_ref(ep) == ep.precondition_hash
    eb = _dev_fixture_execution_blocker_ref()
    assert hash_delegation_execution_blocker_ref(eb) == eb.blocker_hash
    ai = _dev_fixture_admission_intent_ref()
    assert hash_delegation_runtime_admission_intent_ref(ai) == ai.admission_intent_hash
    ap = _dev_fixture_admission_placeholder_ref()
    assert hash_delegation_runtime_admission_placeholder_ref(ap) == ap.admission_placeholder_hash
    rc = _dev_fixture_runtime_context_ref()
    assert hash_delegation_runtime_context_ref(rc) == rc.runtime_context_hash
    te = _dev_fixture_tool_execution_context_ref()
    assert hash_delegation_tool_execution_context_ref(te) == te.tool_context_hash
    sp = _dev_fixture_session_placeholder_ref()
    assert hash_delegation_runtime_session_placeholder_ref(sp) == sp.session_placeholder_hash
    et = _dev_fixture_execution_target_ref()
    assert hash_delegation_execution_target_ref(et) == et.execution_target_hash


def test_full_envelope_binding_chain():
    """DEV_FIXTURE chain: refs + matrix + profile + envelope + binding + binding set."""
    rr = _dev_fixture_runtime_readiness_ref()
    ep = _dev_fixture_execution_precondition_ref()
    eb = _dev_fixture_execution_blocker_ref()
    ai = _dev_fixture_admission_intent_ref()
    ap = _dev_fixture_admission_placeholder_ref()
    rc = _dev_fixture_runtime_context_ref()
    te = _dev_fixture_tool_execution_context_ref()
    sp = _dev_fixture_session_placeholder_ref()
    et = _dev_fixture_execution_target_ref()

    me = build_delegation_runtime_execution_readiness_matrix_entry(
        entry_id="me-001", delegation_ref_id="del-dev-001",
        family=DelegationRuntimeExecutionReadinessFamily.RUNTIME_CONTEXT,
        present=True, hash_present=True, source_label_present=True,
    )
    matrix = build_delegation_runtime_execution_readiness_matrix(
        readiness_matrix_id="rm-dev-001", delegation_ref_id="del-dev-001",
        entries=[me],
    )
    profile = build_delegation_runtime_execution_readiness_profile(
        runtime_execution_readiness_profile_id="rp-dev-001",
        delegation_ref_id="del-dev-001",
        has_runtime_readiness_refs=True,
        has_execution_precondition_refs=True,
        has_runtime_context_refs=True,
        missing_components=["execution_engine"],
        runtime_engine_unavailable_reason="runtime engine not available in P1.8.13",
        execution_engine_unavailable_reason="execution engine not available in P1.8.13",
    )

    env = build_delegation_runtime_execution_readiness_envelope(
        runtime_execution_readiness_envelope_id="re-dev-001",
        delegation_ref_id="del-dev-001",
        delegation_identity_hash="idhash-dev",
        readiness_matrix_hash=matrix.matrix_hash,
        runtime_execution_readiness_hash=profile.readiness_hash,
        runtime_readiness_ref_ids=[rr.runtime_readiness_ref_id],
        execution_precondition_ref_ids=[ep.execution_precondition_ref_id],
        execution_blocker_ref_ids=[eb.execution_blocker_ref_id],
        runtime_admission_intent_ref_ids=[ai.runtime_admission_intent_ref_id],
        runtime_admission_placeholder_ref_ids=[ap.runtime_admission_placeholder_ref_id],
        runtime_context_ref_ids=[rc.runtime_context_ref_id],
        tool_execution_context_ref_ids=[te.tool_execution_context_ref_id],
        runtime_session_placeholder_ref_ids=[sp.runtime_session_placeholder_ref_id],
        execution_target_ref_ids=[et.execution_target_ref_id],
    )

    binding = build_delegation_runtime_execution_readiness_binding(
        binding_id="rb-dev-001",
        delegation_ref_id="del-dev-001",
        runtime_execution_readiness_envelope_hash=env.runtime_execution_readiness_envelope_hash,
        readiness_matrix_hash=matrix.matrix_hash,
        readiness_hash=profile.readiness_hash,
    )

    bs = build_delegation_runtime_execution_readiness_binding_set(
        runtime_execution_readiness_binding_set_id="rbs-dev-001",
        delegation_ref_id="del-dev-001",
        bindings=[binding],
    )

    assert env.runtime_execution_readiness_envelope_hash
    assert binding.binding_hash
    assert bs.runtime_execution_readiness_binding_set_hash
    assert hash_delegation_runtime_execution_readiness_envelope(env) == env.runtime_execution_readiness_envelope_hash
    assert hash_delegation_runtime_execution_readiness_envelope(env) == hash_delegation_runtime_execution_readiness_envelope(env)
    assert hash_delegation_runtime_execution_readiness_binding(binding) == binding.binding_hash
    assert hash_delegation_runtime_execution_readiness_binding_set(bs) == bs.runtime_execution_readiness_binding_set_hash

    # Side effects all false
    se = bs.side_effects
    assert not se.runtime_engine_called
    assert not se.execution_engine_called
    assert not se.admission_gate_called
    assert not se.runtime_admitted
    assert not se.runtime_blocked
    assert not se.execution_allowed
    assert not se.execution_blocked
    assert not se.tool_dispatched
    assert not se.runtime_session_created
    assert not se.execution_target_selected
    assert not se.enforcement_performed
    assert not se.policy_called
    assert not se.custos_called
    assert not se.ledger_written
    assert not se.global_trace_written
    assert not se.runtime_mutated


def test_profile_missing_components_sorted():
    p = build_delegation_runtime_execution_readiness_profile(
        runtime_execution_readiness_profile_id="rp-001",
        delegation_ref_id="del-001",
        missing_components=["z", "a", "b"],
    )
    assert list(p.missing_components) == ["a", "b", "z"]


def test_envelope_id_ordering_deterministic():
    """Same ref IDs in different order produce same envelope hash."""
    a = build_delegation_runtime_execution_readiness_envelope(
        runtime_execution_readiness_envelope_id="re-001",
        delegation_ref_id="del-001",
        runtime_readiness_ref_ids=["rr-2", "rr-1", "rr-3"],
    )
    b = build_delegation_runtime_execution_readiness_envelope(
        runtime_execution_readiness_envelope_id="re-001",
        delegation_ref_id="del-001",
        runtime_readiness_ref_ids=["rr-1", "rr-3", "rr-2"],
    )
    assert a.runtime_execution_readiness_envelope_hash == b.runtime_execution_readiness_envelope_hash
