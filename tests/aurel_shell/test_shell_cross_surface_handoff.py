"""Tests for P2.5-A cross-surface handoff foundation (P2.5.0-P2.5.5)."""

from __future__ import annotations

import json

import pytest

from agentic_runtime.aurel_shell.contracts import AurelShellValidationError
from agentic_runtime.aurel_shell.cross_surface_handoff import (
    P2_4_D_COMMIT_REF,
    P2_4_D_PACK_ID,
    P2_4_D_REPORT_PATH,
    P2_5_A_DEPENDENCY_PACK,
    P2_5_A_NEXT_PACK,
    P2_5_A_OFFICIAL_SECTION_NAME,
    P2_5_A_PACK_CHECKPOINT_IDS,
    P2_5_A_PACK_ID,
    P2_5_A_SECTION_ID,
    CrossSurfaceEligibility,
    CrossSurfaceEligibilityStatus,
    CrossSurfaceEndpoint,
    CrossSurfaceEndpointRole,
    CrossSurfaceHandoffFoundationResult,
    CrossSurfaceHandoffGate,
    CrossSurfaceHandoffGateStatus,
    CrossSurfaceHandoffId,
    CrossSurfaceHandoffIntent,
    CrossSurfaceHandoffIntentKind,
    CrossSurfaceNoRouteBoundary,
    CrossSurfacePayloadEnvelope,
    CrossSurfacePayloadKind,
    CrossSurfaceUnavailableReason,
    P25ACrossSurfaceHandoffResult,
    P25ASideEffectProof,
    build_cross_surface_eligibility,
    build_cross_surface_endpoint,
    build_cross_surface_handoff_foundation_result,
    build_cross_surface_handoff_gate,
    build_cross_surface_handoff_id,
    build_cross_surface_handoff_intent,
    build_cross_surface_no_route_boundary,
    build_cross_surface_payload_envelope,
    build_p2_5_a_cross_surface_handoff_result,
    build_p2_5_a_fixture_handoff_pipeline,
    build_p2_5_a_side_effect_proof,
    render_cross_surface_handoff_summary,
    serialize_p2_5_a_result,
)
from agentic_runtime.aurel_shell.surface_registry import (
    CANONICAL_SURFACE_KINDS,
    CANONICAL_SURFACE_ORDER,
    SURFACE_KIND_IDS,
    AurelSurfaceKind,
)

_CANONICAL_IDS = set(SURFACE_KIND_IDS.values())
_OLD_SURFACES = {"workspace", "strategy", "forum", "archivium",
                 "a_hub", "s_hub", "l_hub", "society_hub"}


# ---------------------------------------------------------------------------
# Module import
# ---------------------------------------------------------------------------

def test_module_imports_p2_5_a() -> None:
    import agentic_runtime.aurel_shell.cross_surface_handoff  # noqa: F401


# ---------------------------------------------------------------------------
# P2.5.0 — Gate / dependency tests
# ---------------------------------------------------------------------------

def test_p2_5_0_pack_identity_constants() -> None:
    assert P2_5_A_PACK_ID == "P2.5-A"
    assert P2_5_A_SECTION_ID == "P2.5"
    assert P2_5_A_OFFICIAL_SECTION_NAME == "Cross-Surface Handoff"
    assert P2_5_A_DEPENDENCY_PACK == P2_4_D_PACK_ID
    assert P2_5_A_DEPENDENCY_PACK == "P2.4-D"
    assert P2_5_A_NEXT_PACK == "P2.5-B"
    assert P2_5_A_PACK_CHECKPOINT_IDS == (
        "P2.5.0", "P2.5.1", "P2.5.2", "P2.5.3", "P2.5.4", "P2.5.5",
    )


def test_p2_5_0_handoff_section_gate_builds() -> None:
    gate = build_cross_surface_handoff_gate(repo_evidence_gate_passed=True)
    assert isinstance(gate, CrossSurfaceHandoffGate)
    assert gate.gate_id == "p2_5_a_cross_surface_handoff_section_gate"
    assert gate.section_id == P2_5_A_SECTION_ID
    assert gate.created_for_pack == P2_5_A_PACK_ID
    assert gate.repo_evidence_gate_passed is True
    assert gate.gate_status == CrossSurfaceHandoffGateStatus.READY


def test_p2_5_0_gate_status_closed_world() -> None:
    valid = {e.value for e in CrossSurfaceHandoffGateStatus}
    assert valid == {"READY", "BLOCKED", "PARTIAL", "ERROR"}


def test_p2_5_0_dependency_report_commit_validation_refs() -> None:
    gate = build_cross_surface_handoff_gate(repo_evidence_gate_passed=True)
    assert gate.dependency_pack == P2_4_D_PACK_ID
    assert gate.dependency_report_ref == P2_4_D_REPORT_PATH
    assert gate.dependency_commit_ref == P2_4_D_COMMIT_REF
    assert "validation" in gate.dependency_validation_ref.lower()
    assert "p2_4_d" in gate.dependency_section_seal_ref


def test_p2_5_0_omni_evidence_ignored_when_override_active() -> None:
    gate = build_cross_surface_handoff_gate(repo_evidence_gate_passed=True)
    assert gate.omni_evidence_required is False
    assert gate.omni_evidence_ignored_by_operator_instruction is True


def test_p2_5_0_gate_does_not_claim_live() -> None:
    gate = build_cross_surface_handoff_gate(repo_evidence_gate_passed=True)
    assert "LIVE" not in gate.truth_label.upper() or "NOT_LIVE" in gate.truth_label


def test_p2_5_0_gate_does_not_claim_trace_verified() -> None:
    gate = build_cross_surface_handoff_gate(repo_evidence_gate_passed=True)
    assert "TRACE_VERIFIED" not in gate.truth_label or "NOT_TRACE_VERIFIED" in gate.truth_label


def test_p2_5_0_gate_does_not_claim_product_behavior() -> None:
    gate = build_cross_surface_handoff_gate(repo_evidence_gate_passed=True)
    assert "NOT_PRODUCT_BEHAVIOR" in gate.truth_label


def test_p2_5_0_gate_blocks_when_repo_evidence_fails() -> None:
    gate = build_cross_surface_handoff_gate(repo_evidence_gate_passed=False)
    assert gate.repo_evidence_gate_passed is False
    assert gate.gate_status == CrossSurfaceHandoffGateStatus.BLOCKED


def test_p2_5_a_does_not_start_p2_5_b() -> None:
    assert P2_5_A_NEXT_PACK == "P2.5-B"
    proof = build_p2_5_a_side_effect_proof()
    assert proof.p2_5_b_started is False


def test_p2_5_a_does_not_start_future_packs() -> None:
    proof = build_p2_5_a_side_effect_proof()
    assert proof.p2_5_b_started is False
    assert proof.p2_6_started is False
    assert proof.p2_7_started is False
    assert proof.p2_10_started is False
    assert proof.p2_13_started is False


# ---------------------------------------------------------------------------
# P2.5.1 — Handoff Identity / Intent
# ---------------------------------------------------------------------------

def test_p2_5_1_handoff_id_builds() -> None:
    obj = build_cross_surface_handoff_id(
        source_surface_id="hq",
        target_surface_id="corp",
        payload_kind="DEV_FIXTURE_REF",
        intent_kind="DEV_FIXTURE",
    )
    assert isinstance(obj, CrossSurfaceHandoffId)
    assert obj.source_surface_id == "hq"
    assert obj.target_surface_id == "corp"
    assert obj.handoff_id


def test_p2_5_1_handoff_intent_builds() -> None:
    intent = build_cross_surface_handoff_intent(
        intent_kind=CrossSurfaceHandoffIntentKind.DEV_FIXTURE,
        description="test handoff",
        source_surface_id="hq",
        target_surface_id="ide",
    )
    assert isinstance(intent, CrossSurfaceHandoffIntent)
    assert intent.intent_kind == CrossSurfaceHandoffIntentKind.DEV_FIXTURE


def test_p2_5_1_intent_kind_closed_world() -> None:
    valid = {e.value for e in CrossSurfaceHandoffIntentKind}
    assert valid == {
        "OPEN_REFERENCE", "CONTINUE_CONTEXT", "INSPECT_OBJECT",
        "COMPARE_CONTEXT", "SEND_TO_SURFACE", "REQUEST_ATTENTION",
        "DEV_FIXTURE", "UNKNOWN_UNAVAILABLE",
    }


def test_p2_5_1_intent_serializes() -> None:
    intent = build_cross_surface_handoff_intent(
        intent_kind=CrossSurfaceHandoffIntentKind.CONTINUE_CONTEXT,
        description="continue context",
        source_surface_id="hq",
        target_surface_id="corp",
    )
    d = intent._to_stable_dict()
    assert d["executes_command"] is False
    assert d["executes_route"] is False
    assert d["switches_surface"] is False
    assert d["is_authorization"] is False
    assert json.dumps(d)


def test_p2_5_1_intent_executes_command_is_false() -> None:
    intent = build_cross_surface_handoff_intent(
        intent_kind=CrossSurfaceHandoffIntentKind.OPEN_REFERENCE,
        description="open ref",
        source_surface_id="hq",
        target_surface_id="ide",
    )
    assert intent.executes_command is False


def test_p2_5_1_intent_executes_route_is_false() -> None:
    intent = build_cross_surface_handoff_intent(
        intent_kind=CrossSurfaceHandoffIntentKind.SEND_TO_SURFACE,
        description="send",
        source_surface_id="corp",
        target_surface_id="hub",
    )
    assert intent.executes_route is False


def test_p2_5_1_intent_switches_surface_is_false() -> None:
    intent = build_cross_surface_handoff_intent(
        intent_kind=CrossSurfaceHandoffIntentKind.REQUEST_ATTENTION,
        description="attention",
        source_surface_id="ide",
        target_surface_id="hq",
    )
    assert intent.switches_surface is False


def test_p2_5_1_intent_is_authorization_is_false() -> None:
    intent = build_cross_surface_handoff_intent(
        intent_kind=CrossSurfaceHandoffIntentKind.INSPECT_OBJECT,
        description="inspect",
        source_surface_id="hq",
        target_surface_id="ide",
    )
    assert intent.is_authorization is False


def test_p2_5_1_intent_rejects_execute_command() -> None:
    with pytest.raises(AurelShellValidationError):
        CrossSurfaceHandoffIntent(
            intent_id="test",
            intent_kind=CrossSurfaceHandoffIntentKind.DEV_FIXTURE,
            description="bad",
            requested_by="test",
            source_surface_id="hq",
            target_surface_id="corp",
            executes_command=True,
            executes_route=False,
            switches_surface=False,
            is_authorization=False,
            truth_label="test",
            limitations=(),
        )


def test_p2_5_1_intent_rejects_execute_route() -> None:
    with pytest.raises(AurelShellValidationError):
        CrossSurfaceHandoffIntent(
            intent_id="test",
            intent_kind=CrossSurfaceHandoffIntentKind.DEV_FIXTURE,
            description="bad",
            requested_by="test",
            source_surface_id="hq",
            target_surface_id="corp",
            executes_command=False,
            executes_route=True,
            switches_surface=False,
            is_authorization=False,
            truth_label="test",
            limitations=(),
        )


def test_p2_5_1_intent_rejects_switch_surface() -> None:
    with pytest.raises(AurelShellValidationError):
        CrossSurfaceHandoffIntent(
            intent_id="test",
            intent_kind=CrossSurfaceHandoffIntentKind.DEV_FIXTURE,
            description="bad",
            requested_by="test",
            source_surface_id="hq",
            target_surface_id="corp",
            executes_command=False,
            executes_route=False,
            switches_surface=True,
            is_authorization=False,
            truth_label="test",
            limitations=(),
        )


def test_p2_5_1_handoff_id_deterministic() -> None:
    a = build_cross_surface_handoff_id(
        source_surface_id="hq", target_surface_id="corp",
        payload_kind="DEV_FIXTURE_REF", intent_kind="DEV_FIXTURE",
    )
    b = build_cross_surface_handoff_id(
        source_surface_id="hq", target_surface_id="corp",
        payload_kind="DEV_FIXTURE_REF", intent_kind="DEV_FIXTURE",
    )
    assert a.handoff_id == b.handoff_id


# ---------------------------------------------------------------------------
# P2.5.2 — Source / Target Surface Contract
# ---------------------------------------------------------------------------

def test_p2_5_2_source_endpoint_builds() -> None:
    ep = build_cross_surface_endpoint(
        endpoint_role=CrossSurfaceEndpointRole.SOURCE,
        surface_id="hq",
    )
    assert isinstance(ep, CrossSurfaceEndpoint)
    assert ep.endpoint_role == CrossSurfaceEndpointRole.SOURCE
    assert ep.surface_id == "hq"
    assert ep.active_navigation_mutation is False
    assert ep.runtime_switch is False


def test_p2_5_2_target_endpoint_builds() -> None:
    ep = build_cross_surface_endpoint(
        endpoint_role=CrossSurfaceEndpointRole.TARGET,
        surface_id="corp",
    )
    assert ep.endpoint_role == CrossSurfaceEndpointRole.TARGET
    assert ep.surface_id == "corp"


def test_p2_5_2_endpoint_role_closed_world() -> None:
    valid = {e.value for e in CrossSurfaceEndpointRole}
    assert valid == {"SOURCE", "TARGET"}


def test_p2_5_2_official_surfaces_accepted() -> None:
    for sid in _CANONICAL_IDS:
        ep = build_cross_surface_endpoint(
            endpoint_role=CrossSurfaceEndpointRole.SOURCE,
            surface_id=sid,
        )
        assert ep.surface_known is True
        assert ep.uses_official_surface_registry is True


def test_p2_5_2_unknown_surface_marked_unavailable() -> None:
    ep = build_cross_surface_endpoint(
        endpoint_role=CrossSurfaceEndpointRole.SOURCE,
        surface_id="unknown_surface_xyz",
    )
    assert ep.surface_known is False
    assert ep.uses_official_surface_registry is False


def test_p2_5_2_old_surfaces_not_official() -> None:
    for old_id in _OLD_SURFACES:
        ep = build_cross_surface_endpoint(
            endpoint_role=CrossSurfaceEndpointRole.SOURCE,
            surface_id=old_id,
        )
        assert ep.surface_known is False


def test_p2_5_2_target_runtime_switch_is_false() -> None:
    ep = build_cross_surface_endpoint(
        endpoint_role=CrossSurfaceEndpointRole.TARGET,
        surface_id="ide",
    )
    assert ep.runtime_switch is False


def test_p2_5_2_source_active_navigation_mutation_is_false() -> None:
    ep = build_cross_surface_endpoint(
        endpoint_role=CrossSurfaceEndpointRole.SOURCE,
        surface_id="aurel_cro",
    )
    assert ep.active_navigation_mutation is False


def test_p2_5_2_endpoint_rejects_runtime_switch() -> None:
    with pytest.raises(AurelShellValidationError):
        CrossSurfaceEndpoint(
            endpoint_id="test",
            endpoint_role=CrossSurfaceEndpointRole.TARGET,
            surface_id="hq",
            surface_label="HQ",
            uses_official_surface_registry=True,
            surface_known=True,
            surface_taxonomy_drift=False,
            active_navigation_mutation=False,
            runtime_switch=True,
            truth_label="test",
            limitations=(),
        )


def test_p2_5_2_endpoint_rejects_active_nav_mutation() -> None:
    with pytest.raises(AurelShellValidationError):
        CrossSurfaceEndpoint(
            endpoint_id="test",
            endpoint_role=CrossSurfaceEndpointRole.SOURCE,
            surface_id="hq",
            surface_label="HQ",
            uses_official_surface_registry=True,
            surface_known=True,
            surface_taxonomy_drift=False,
            active_navigation_mutation=True,
            runtime_switch=False,
            truth_label="test",
            limitations=(),
        )


# ---------------------------------------------------------------------------
# P2.5.3 — Payload / Reference Envelope
# ---------------------------------------------------------------------------

def test_p2_5_3_payload_envelope_builds() -> None:
    env = build_cross_surface_payload_envelope(
        payload_kind=CrossSurfacePayloadKind.DEV_FIXTURE_REF,
        payload_ref="test_ref_123",
        payload_label="Test payload",
    )
    assert isinstance(env, CrossSurfacePayloadEnvelope)
    assert env.payload_kind == CrossSurfacePayloadKind.DEV_FIXTURE_REF
    assert env.payload_ref == "test_ref_123"


def test_p2_5_3_payload_kind_closed_world() -> None:
    valid = {e.value for e in CrossSurfacePayloadKind}
    assert valid == {
        "COMMAND_RESULT_REF", "COMMAND_PROPOSAL_REF",
        "OBJECT_REF", "ARTIFACT_REF", "WINDOW_STATE_REF",
        "SURFACE_CONTEXT_REF", "SYSTEM_STATUS_REF",
        "DEV_FIXTURE_REF", "UNKNOWN_UNAVAILABLE",
    }


def test_p2_5_3_payload_envelope_serializes() -> None:
    env = build_cross_surface_payload_envelope(
        payload_kind=CrossSurfacePayloadKind.OBJECT_REF,
        payload_ref="ref_abc",
    )
    d = env._to_stable_dict()
    assert json.dumps(d)


def test_p2_5_3_payload_envelope_not_storage_write() -> None:
    env = build_cross_surface_payload_envelope(
        payload_kind=CrossSurfacePayloadKind.ARTIFACT_REF,
        payload_ref="ref",
    )
    assert env.storage_written is False


def test_p2_5_3_payload_envelope_not_memory_write() -> None:
    env = build_cross_surface_payload_envelope(
        payload_kind=CrossSurfacePayloadKind.COMMAND_RESULT_REF,
        payload_ref="ref",
    )
    assert env.memory_written is False


def test_p2_5_3_payload_envelope_not_trace_write() -> None:
    env = build_cross_surface_payload_envelope(
        payload_kind=CrossSurfacePayloadKind.WINDOW_STATE_REF,
        payload_ref="ref",
    )
    assert env.trace_written is False


def test_p2_5_3_payload_envelope_not_object_transfer() -> None:
    env = build_cross_surface_payload_envelope(
        payload_kind=CrossSurfacePayloadKind.SURFACE_CONTEXT_REF,
        payload_ref="ref",
    )
    assert env.ownership_transferred is False
    assert env.object_copied is False
    assert env.object_moved is False


def test_p2_5_3_payload_envelope_rejects_ownership() -> None:
    with pytest.raises(AurelShellValidationError):
        CrossSurfacePayloadEnvelope(
            payload_envelope_id="test",
            payload_kind=CrossSurfacePayloadKind.DEV_FIXTURE_REF,
            payload_ref="ref",
            payload_label="",
            source_ref="",
            ownership_transferred=True,
            storage_written=False,
            memory_written=False,
            trace_written=False,
            object_copied=False,
            object_moved=False,
            truth_label="test",
            limitations=(),
        )


def test_p2_5_3_payload_envelope_rejects_storage() -> None:
    with pytest.raises(AurelShellValidationError):
        CrossSurfacePayloadEnvelope(
            payload_envelope_id="test",
            payload_kind=CrossSurfacePayloadKind.DEV_FIXTURE_REF,
            payload_ref="ref",
            payload_label="",
            source_ref="",
            ownership_transferred=False,
            storage_written=True,
            memory_written=False,
            trace_written=False,
            object_copied=False,
            object_moved=False,
            truth_label="test",
            limitations=(),
        )


# ---------------------------------------------------------------------------
# P2.5.4 — Eligibility / Unavailable-State
# ---------------------------------------------------------------------------

def test_p2_5_4_eligibility_builds() -> None:
    elig = build_cross_surface_eligibility()
    assert isinstance(elig, CrossSurfaceEligibility)
    assert elig.eligible_contract_only is True
    assert elig.is_permission_decision is False


def test_p2_5_4_eligibility_status_closed_world() -> None:
    valid = {e.value for e in CrossSurfaceEligibilityStatus}
    assert valid == {"ELIGIBLE_CONTRACT_ONLY", "UNAVAILABLE", "BLOCKED", "PARTIAL", "ERROR"}


def test_p2_5_4_unavailable_reasons_represented() -> None:
    elig = build_cross_surface_eligibility()
    assert len(elig.unavailable_reasons) >= 1
    for r in elig.unavailable_reasons:
        assert isinstance(r, CrossSurfaceUnavailableReason)
        assert r.capability
        assert r.reason
        assert r.future_pack_or_section


def test_p2_5_4_eligible_contract_only_represented() -> None:
    elig = build_cross_surface_eligibility()
    assert elig.eligible_contract_only is True
    assert elig.eligibility_status == CrossSurfaceEligibilityStatus.ELIGIBLE_CONTRACT_ONLY


def test_p2_5_4_is_permission_decision_false() -> None:
    elig = build_cross_surface_eligibility()
    assert elig.is_permission_decision is False


def test_p2_5_4_grants_permission_false() -> None:
    elig = build_cross_surface_eligibility()
    assert elig.grants_permission is False


def test_p2_5_4_denies_permission_false() -> None:
    elig = build_cross_surface_eligibility()
    assert elig.denies_permission is False


def test_p2_5_4_activates_approval_false() -> None:
    elig = build_cross_surface_eligibility()
    assert elig.activates_approval is False


def test_p2_5_4_blocks_runtime_false() -> None:
    elig = build_cross_surface_eligibility()
    assert elig.blocks_runtime is False


def test_p2_5_4_eligibility_rejects_permission_decision() -> None:
    with pytest.raises(AurelShellValidationError):
        CrossSurfaceEligibility(
            eligibility_id="test",
            eligibility_status=CrossSurfaceEligibilityStatus.ELIGIBLE_CONTRACT_ONLY,
            eligible_contract_only=True,
            unavailable_reasons=(),
            requires_permission_later=True,
            requires_approval_later=True,
            requires_route_runtime_later=True,
            requires_ui_later=True,
            is_permission_decision=True,
            grants_permission=False,
            denies_permission=False,
            activates_approval=False,
            blocks_runtime=False,
            truth_label="test",
            limitations=(),
        )


# ---------------------------------------------------------------------------
# P2.5.5 — No-Route / No-Runtime Boundary + Foundation Result
# ---------------------------------------------------------------------------

def test_p2_5_5_no_route_boundary_builds() -> None:
    h_id = build_cross_surface_handoff_id(
        source_surface_id="hq", target_surface_id="corp",
        payload_kind="DEV_FIXTURE_REF", intent_kind="DEV_FIXTURE",
    )
    b = build_cross_surface_no_route_boundary(handoff_id=h_id.handoff_id)
    assert isinstance(b, CrossSurfaceNoRouteBoundary)


def test_p2_5_5_boundary_active_true() -> None:
    h_id = build_cross_surface_handoff_id(
        source_surface_id="hq", target_surface_id="corp",
        payload_kind="DEV_FIXTURE_REF", intent_kind="DEV_FIXTURE",
    )
    b = build_cross_surface_no_route_boundary(handoff_id=h_id.handoff_id)
    assert b.boundary_active is True


def test_p2_5_5_surface_switch_allowed_false() -> None:
    h_id = build_cross_surface_handoff_id(
        source_surface_id="hq", target_surface_id="corp",
        payload_kind="DEV_FIXTURE_REF", intent_kind="DEV_FIXTURE",
    )
    b = build_cross_surface_no_route_boundary(handoff_id=h_id.handoff_id)
    assert b.surface_switch_allowed is False


def test_p2_5_5_route_execution_allowed_false() -> None:
    h_id = build_cross_surface_handoff_id(
        source_surface_id="hq", target_surface_id="corp",
        payload_kind="DEV_FIXTURE_REF", intent_kind="DEV_FIXTURE",
    )
    b = build_cross_surface_no_route_boundary(handoff_id=h_id.handoff_id)
    assert b.route_execution_allowed is False


def test_p2_5_5_all_boundary_execution_booleans_false() -> None:
    h_id = build_cross_surface_handoff_id(
        source_surface_id="hq", target_surface_id="corp",
        payload_kind="DEV_FIXTURE_REF", intent_kind="DEV_FIXTURE",
    )
    b = build_cross_surface_no_route_boundary(handoff_id=h_id.handoff_id)
    assert b.route_handler_invoked is False
    assert b.ui_transition_created is False
    assert b.drag_drop_created is False
    assert b.command_execution_allowed is False
    assert b.approval_activated is False
    assert b.permission_enforced is False
    assert b.tool_invoked is False
    assert b.workflow_dispatched is False
    assert b.storage_written is False
    assert b.memory_written is False
    assert b.trace_written is False
    assert b.runtime_mutated is False


def test_p2_5_5_no_route_boundary_rejects_inactive() -> None:
    with pytest.raises(AurelShellValidationError):
        CrossSurfaceNoRouteBoundary(
            boundary_id="test",
            handoff_id="test",
            boundary_active=False,
            surface_switch_allowed=False,
            route_execution_allowed=False,
            route_handler_invoked=False,
            ui_transition_created=False,
            drag_drop_created=False,
            command_execution_allowed=False,
            approval_activated=False,
            permission_enforced=False,
            tool_invoked=False,
            workflow_dispatched=False,
            storage_written=False,
            memory_written=False,
            trace_written=False,
            runtime_mutated=False,
            reason="test",
            truth_label="test",
            limitations=(),
        )


def test_p2_5_5_handoff_foundation_result_builds() -> None:
    fr = build_cross_surface_handoff_foundation_result(
        handoff_id="h1",
        intent="i1",
        source_endpoint="s1",
        target_endpoint="t1",
        payload_envelope="p1",
        eligibility="e1",
        no_route_boundary="b1",
    )
    assert isinstance(fr, CrossSurfaceHandoffFoundationResult)
    assert fr.section_id == P2_5_A_SECTION_ID
    assert fr.created_for_pack == P2_5_A_PACK_ID


def test_p2_5_5_foundation_result_serializes_deterministically() -> None:
    fr_a = build_cross_surface_handoff_foundation_result(
        handoff_id="h1", intent="i1", source_endpoint="s1",
        target_endpoint="t1", payload_envelope="p1",
        eligibility="e1", no_route_boundary="b1",
    )
    fr_b = build_cross_surface_handoff_foundation_result(
        handoff_id="h1", intent="i1", source_endpoint="s1",
        target_endpoint="t1", payload_envelope="p1",
        eligibility="e1", no_route_boundary="b1",
    )
    assert fr_a._to_stable_dict() == fr_b._to_stable_dict()
    assert fr_a.foundation_result_id == fr_b.foundation_result_id


def test_p2_5_5_is_transition_result_false() -> None:
    fr = build_cross_surface_handoff_foundation_result(
        handoff_id="h1", intent="i1", source_endpoint="s1",
        target_endpoint="t1", payload_envelope="p1",
        eligibility="e1", no_route_boundary="b1",
    )
    assert fr.is_transition_result is False


def test_p2_5_5_is_route_result_false() -> None:
    fr = build_cross_surface_handoff_foundation_result(
        handoff_id="h1", intent="i1", source_endpoint="s1",
        target_endpoint="t1", payload_envelope="p1",
        eligibility="e1", no_route_boundary="b1",
    )
    assert fr.is_route_result is False


def test_p2_5_5_is_live_ui_false() -> None:
    fr = build_cross_surface_handoff_foundation_result(
        handoff_id="h1", intent="i1", source_endpoint="s1",
        target_endpoint="t1", payload_envelope="p1",
        eligibility="e1", no_route_boundary="b1",
    )
    assert fr.is_live_ui is False


def test_p2_5_5_is_source_of_truth_false() -> None:
    fr = build_cross_surface_handoff_foundation_result(
        handoff_id="h1", intent="i1", source_endpoint="s1",
        target_endpoint="t1", payload_envelope="p1",
        eligibility="e1", no_route_boundary="b1",
    )
    assert fr.is_source_of_truth is False


def test_p2_5_5_no_surface_switch() -> None:
    fr = build_cross_surface_handoff_foundation_result(
        handoff_id="h1", intent="i1", source_endpoint="s1",
        target_endpoint="t1", payload_envelope="p1",
        eligibility="e1", no_route_boundary="b1",
    )
    assert fr.switches_surface is False


def test_p2_5_5_no_route_execution() -> None:
    fr = build_cross_surface_handoff_foundation_result(
        handoff_id="h1", intent="i1", source_endpoint="s1",
        target_endpoint="t1", payload_envelope="p1",
        eligibility="e1", no_route_boundary="b1",
    )
    assert fr.executes_route is False


def test_p2_5_5_no_runtime_mutation() -> None:
    fr = build_cross_surface_handoff_foundation_result(
        handoff_id="h1", intent="i1", source_endpoint="s1",
        target_endpoint="t1", payload_envelope="p1",
        eligibility="e1", no_route_boundary="b1",
    )
    assert fr.mutates_runtime is False
    assert fr.writes_memory is False
    assert fr.writes_trace is False
    assert fr.writes_storage is False


def test_p2_5_5_next_pack_is_p2_5_b() -> None:
    sid = build_cross_surface_handoff_id(
        source_surface_id="hq", target_surface_id="corp",
        payload_kind="DEV_FIXTURE_REF", intent_kind="DEV_FIXTURE",
    )
    intent = build_cross_surface_handoff_intent(
        intent_kind=CrossSurfaceHandoffIntentKind.DEV_FIXTURE,
        description="test",
        source_surface_id="hq",
        target_surface_id="corp",
    )
    src = build_cross_surface_endpoint(
        endpoint_role=CrossSurfaceEndpointRole.SOURCE, surface_id="hq")
    tgt = build_cross_surface_endpoint(
        endpoint_role=CrossSurfaceEndpointRole.TARGET, surface_id="corp")
    env = build_cross_surface_payload_envelope(
        payload_kind=CrossSurfacePayloadKind.DEV_FIXTURE_REF, payload_ref="ref")
    elig = build_cross_surface_eligibility()
    boundary = build_cross_surface_no_route_boundary(handoff_id=sid.handoff_id)
    fr = build_cross_surface_handoff_foundation_result(
        handoff_id=sid.handoff_id, intent=intent.intent_id,
        source_endpoint=src.endpoint_id, target_endpoint=tgt.endpoint_id,
        payload_envelope=env.payload_envelope_id,
        eligibility=elig.eligibility_id,
        no_route_boundary=boundary.boundary_id,
    )
    proof = build_p2_5_a_side_effect_proof()
    from agentic_runtime.aurel_shell.contracts import _hash_payload, to_canonical_json
    result = build_p2_5_a_cross_surface_handoff_result(
        handoff_gate="gate", handoff_id=sid.handoff_id,
        intent=intent.intent_id, source_endpoint=src.endpoint_id,
        target_endpoint=tgt.endpoint_id,
        payload_envelope=env.payload_envelope_id,
        eligibility=elig.eligibility_id,
        unavailable_reasons=len(elig.unavailable_reasons),
        no_route_boundary=boundary.boundary_id,
        foundation_result=fr.foundation_result_id,
        side_effect_proof=_hash_payload(proof._to_stable_dict()),
    )
    assert result.next_pack == P2_5_A_NEXT_PACK
    assert result.next_pack == "P2.5-B"


# ---------------------------------------------------------------------------
# Side-effect proof
# ---------------------------------------------------------------------------

def test_side_effect_proof_all_fields_false() -> None:
    proof = build_p2_5_a_side_effect_proof()
    assert proof.cross_surface_ui_created is False
    assert proof.drag_drop_created is False
    assert proof.handoff_animation_created is False
    assert proof.frontend_ui_created is False
    assert proof.browser_ui_created is False
    assert proof.tauri_app_created is False
    assert proof.desktop_app_created is False
    assert proof.keyboard_listener_created is False
    assert proof.shortcut_handler_created is False
    assert proof.surface_runtime_switch_created is False
    assert proof.route_execution_created is False
    assert proof.route_handler_created is False
    assert proof.route_runtime_created is False
    assert proof.command_execution_created is False
    assert proof.command_router_created is False
    assert proof.command_handler_created is False
    assert proof.command_invocation_created is False
    assert proof.tool_invocation_created is False
    assert proof.workflow_dispatch_created is False
    assert proof.approval_created is False
    assert proof.approval_activated is False
    assert proof.permission_enforcement_created is False
    assert proof.permission_granted is False
    assert proof.permission_denied is False
    assert proof.runtime_blocking_created is False
    assert proof.custos_integration_created is False
    assert proof.api_server_created is False
    assert proof.http_routes_created is False
    assert proof.event_bus_created is False
    assert proof.runtime_events_emitted is False
    assert proof.local_storage_written is False
    assert proof.browser_storage_written is False
    assert proof.memory_written is False
    assert proof.trace_written is False
    assert proof.runtime_mutated is False
    assert proof.source_of_truth_created is False
    assert proof.live_claimed is False
    assert proof.trace_verified_claimed is False
    assert proof.release_scope_claimed is False
    assert proof.product_behavior_claimed is False
    assert proof.p2_5_b_started is False
    assert proof.p2_6_started is False
    assert proof.p2_7_started is False
    assert proof.p2_10_started is False
    assert proof.p2_13_started is False


def test_side_effect_proof_rejects_true_field() -> None:
    with pytest.raises(AurelShellValidationError):
        P25ASideEffectProof(
            cross_surface_ui_created=True,
            drag_drop_created=False,
            handoff_animation_created=False,
            frontend_ui_created=False,
            browser_ui_created=False,
            tauri_app_created=False,
            desktop_app_created=False,
            keyboard_listener_created=False,
            shortcut_handler_created=False,
            surface_runtime_switch_created=False,
            route_execution_created=False,
            route_handler_created=False,
            route_runtime_created=False,
            command_execution_created=False,
            command_router_created=False,
            command_handler_created=False,
            command_invocation_created=False,
            tool_invocation_created=False,
            workflow_dispatch_created=False,
            approval_created=False,
            approval_activated=False,
            permission_enforcement_created=False,
            permission_granted=False,
            permission_denied=False,
            runtime_blocking_created=False,
            custos_integration_created=False,
            api_server_created=False,
            http_routes_created=False,
            event_bus_created=False,
            runtime_events_emitted=False,
            local_storage_written=False,
            browser_storage_written=False,
            memory_written=False,
            trace_written=False,
            runtime_mutated=False,
            source_of_truth_created=False,
            live_claimed=False,
            trace_verified_claimed=False,
            release_scope_claimed=False,
            product_behavior_claimed=False,
            p2_5_b_started=False,
            p2_6_started=False,
            p2_7_started=False,
            p2_10_started=False,
            p2_13_started=False,
        )


# ---------------------------------------------------------------------------
# Fixture pipeline + result
# ---------------------------------------------------------------------------

def test_fixture_pipeline_complete() -> None:
    result = build_p2_5_a_fixture_handoff_pipeline(
        source_surface_id="hq", target_surface_id="corp",
    )
    assert isinstance(result, P25ACrossSurfaceHandoffResult)
    assert result.pack_id == P2_5_A_PACK_ID
    assert result.section_id == P2_5_A_SECTION_ID
    assert result.dependency_pack == P2_4_D_PACK_ID
    assert result.next_pack == P2_5_A_NEXT_PACK
    assert result.covered_checkpoints == P2_5_A_PACK_CHECKPOINT_IDS
    assert result.claims_live is False
    assert result.claims_trace_verified is False
    assert result.claims_release_scope is False
    assert result.claims_product_behavior is False
    assert result.starts_future_work is False


def test_fixture_pipeline_result_serializes() -> None:
    result = build_p2_5_a_fixture_handoff_pipeline(
        source_surface_id="hq", target_surface_id="ide",
    )
    d = serialize_p2_5_a_result(result)
    assert isinstance(d, str)
    loaded = json.loads(d)
    assert loaded["pack_id"] == P2_5_A_PACK_ID
    assert json.dumps(json.loads(d))


def test_fixture_pipeline_result_deterministic() -> None:
    a = build_p2_5_a_fixture_handoff_pipeline(
        source_surface_id="hq", target_surface_id="corp",
    )
    b = build_p2_5_a_fixture_handoff_pipeline(
        source_surface_id="hq", target_surface_id="corp",
    )
    assert serialize_p2_5_a_result(a) == serialize_p2_5_a_result(b)


def test_fixture_pipeline_unavailable_reasons_count() -> None:
    result = build_p2_5_a_fixture_handoff_pipeline(
        source_surface_id="corp", target_surface_id="hub",
    )
    assert result.unavailable_reasons >= 1
    assert isinstance(result.unavailable_reasons, int)


def test_render_summary_returns_string() -> None:
    result = build_p2_5_a_fixture_handoff_pipeline(
        source_surface_id="hq", target_surface_id="ide",
    )
    summary = render_cross_surface_handoff_summary(result)
    assert isinstance(summary, str)
    assert P2_5_A_PACK_ID in summary
    assert P2_5_A_SECTION_ID in summary


def test_result_does_not_claim_live() -> None:
    result = build_p2_5_a_fixture_handoff_pipeline(
        source_surface_id="aurel_cro", target_surface_id="hq",
    )
    assert result.claims_live is False
    assert result.claims_trace_verified is False


def test_result_does_not_claim_release_scope() -> None:
    result = build_p2_5_a_fixture_handoff_pipeline(
        source_surface_id="ide", target_surface_id="hub",
    )
    assert result.claims_release_scope is False


def test_result_does_not_claim_product_behavior() -> None:
    result = build_p2_5_a_fixture_handoff_pipeline(
        source_surface_id="settings", target_surface_id="system",
    )
    assert result.claims_product_behavior is False


def test_result_does_not_start_future_work() -> None:
    result = build_p2_5_a_fixture_handoff_pipeline(
        source_surface_id="hub", target_surface_id="ide",
    )
    assert result.starts_future_work is False


# ---------------------------------------------------------------------------
# Integration / variant tests
# ---------------------------------------------------------------------------

def test_all_intent_kinds_build() -> None:
    for kind in CrossSurfaceHandoffIntentKind:
        intent = build_cross_surface_handoff_intent(
            intent_kind=kind,
            description=f"test {kind.value}",
            source_surface_id="hq",
            target_surface_id="corp",
        )
        assert intent.executes_command is False
        assert intent.executes_route is False


def test_all_payload_kinds_build() -> None:
    for kind in CrossSurfacePayloadKind:
        env = build_cross_surface_payload_envelope(
            payload_kind=kind,
            payload_ref=f"ref_{kind.value}",
        )
        assert env.storage_written is False
        assert env.memory_written is False


def test_all_official_surfaces_as_source_and_target() -> None:
    for sid in _CANONICAL_IDS:
        src = build_cross_surface_endpoint(
            endpoint_role=CrossSurfaceEndpointRole.SOURCE,
            surface_id=sid,
        )
        assert src.surface_known is True
        tgt = build_cross_surface_endpoint(
            endpoint_role=CrossSurfaceEndpointRole.TARGET,
            surface_id=sid,
        )
        assert tgt.surface_known is True


def test_handoff_id_differs_for_different_surfaces() -> None:
    a = build_cross_surface_handoff_id(
        source_surface_id="hq", target_surface_id="corp",
        payload_kind="DEV_FIXTURE_REF", intent_kind="DEV_FIXTURE",
    )
    b = build_cross_surface_handoff_id(
        source_surface_id="hq", target_surface_id="ide",
        payload_kind="DEV_FIXTURE_REF", intent_kind="DEV_FIXTURE",
    )
    assert a.handoff_id != b.handoff_id
