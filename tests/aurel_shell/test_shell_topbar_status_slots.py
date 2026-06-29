"""Tests for P2.1-B topbar status slots / availability / operator context."""

from __future__ import annotations

import json
from dataclasses import fields, is_dataclass

import pytest

from agentic_runtime.aurel_shell import AurelShellValidationError, CANONICAL_SURFACE_ORDER
from agentic_runtime.aurel_shell.topbar_status import (
    P2_1_A_REPORT_FILENAME,
    P2_1_B_NEXT_PACK,
    P2_1_B_PACK_CHECKPOINT_IDS,
    TopbarAttentionKind,
    TopbarAttentionSeverity,
    TopbarOperatorContextAvailability,
    TopbarProtectedBoundaryReason,
    TopbarSurfaceAvailabilityStatus,
    assert_p2_1_b_depends_on_p2_1_a,
    assert_p2_1_b_does_not_start_p2_1_c,
    assert_p2_1_b_does_not_start_p2_2,
    assert_topbar_status_extends_p2_1_a_read_model,
    build_p2_1_b_side_effect_proof,
    build_p2_1_b_topbar_status_slots_result,
    build_protected_boundary_slot,
    build_protected_boundary_slots,
    build_surface_availability_slot,
    build_surface_availability_slots,
    build_topbar_attention_status_slot,
    build_topbar_attention_status_slots,
    build_topbar_operator_context_slot,
    build_topbar_status_projection,
    serialize_p2_1_b_result,
)
from agentic_runtime.aurel_shell.topbar import (
    build_default_topbar_surface_registry,
    build_global_topbar_read_model,
)


def _all_dataclass_bools_false(value: object) -> bool:
    assert is_dataclass(value)
    return all(
        getattr(value, field.name) is False
        for field in fields(value)
        if isinstance(getattr(value, field.name), bool)
    )


# ---------------------------------------------------------------------------
# Dispatch / dependency
# ---------------------------------------------------------------------------


def test_aurel_shell_module_imports_topbar_status() -> None:
    import agentic_runtime.aurel_shell.topbar_status  # noqa: F401


def test_p2_1_a_report_dependency_represented() -> None:
    result = build_p2_1_b_topbar_status_slots_result()
    assert result.depends_on_pack == "P2.1-A"
    assert result.depends_on_report == P2_1_A_REPORT_FILENAME
    assert_p2_1_b_depends_on_p2_1_a(result)


def test_p2_1_a_registry_read_model_dependency_represented() -> None:
    projection = build_topbar_status_projection()
    assert projection.registry_ref == "topbar_surface_registry_default"
    assert projection.topbar_read_model_ref == "global_topbar_read_model_default"


def test_p2_1_b_does_not_start_future_packs() -> None:
    projection = build_topbar_status_projection()
    assert projection.starts_p2_1_c is False
    assert projection.starts_p2_2 is False
    assert_p2_1_b_does_not_start_p2_1_c(projection)
    assert_p2_1_b_does_not_start_p2_2(projection)


# ---------------------------------------------------------------------------
# P2.1.6 operator context slot
# ---------------------------------------------------------------------------


def test_operator_context_slot_builds_and_serializes() -> None:
    slot = build_topbar_operator_context_slot()
    payload = slot.to_canonical_dict()
    assert payload["operator_context_id"] == "operator_context_default"
    assert payload["operator_display_label"] == "Operator"
    assert json.loads(serialize_p2_1_b_result(build_p2_1_b_topbar_status_slots_result()))


def test_unavailable_operator_context_requires_reason() -> None:
    with pytest.raises(AurelShellValidationError):
        build_topbar_operator_context_slot(
            availability=TopbarOperatorContextAvailability.UNAVAILABLE
        )


def test_operator_context_is_not_authority_or_auth_session() -> None:
    slot = build_topbar_operator_context_slot()
    assert slot.is_authenticated_context is False
    assert slot.is_authority_grant is False
    assert slot.authority_granted is False
    assert slot.auth_session_created is False
    assert slot.identity_mutated is False


# ---------------------------------------------------------------------------
# P2.1.7 availability slot
# ---------------------------------------------------------------------------


def test_availability_slots_build_for_official_topbar_surfaces() -> None:
    slots = build_surface_availability_slots()
    assert tuple(slot.surface_id for slot in slots) == CANONICAL_SURFACE_ORDER


def test_availability_statuses_are_closed_world() -> None:
    with pytest.raises(AurelShellValidationError):
        build_surface_availability_slot("hq", availability_status="LIVE")


def test_unavailable_availability_without_reason_rejected() -> None:
    with pytest.raises(AurelShellValidationError):
        build_surface_availability_slot(
            "hq",
            availability_status=TopbarSurfaceAvailabilityStatus.UNAVAILABLE_BACKEND_MISSING,
        )


def test_available_contract_and_fixture_are_not_live() -> None:
    contract = build_surface_availability_slot("hq")
    fixture = build_surface_availability_slot(
        "hub",
        availability_status=TopbarSurfaceAvailabilityStatus.DEV_FIXTURE_AVAILABLE,
    )
    assert contract.availability_status == TopbarSurfaceAvailabilityStatus.AVAILABLE_CONTRACT
    assert contract.is_live is False
    assert contract.is_contract_available is True
    assert fixture.is_dev_fixture is True
    assert fixture.is_live is False


def test_backend_missing_and_future_pack_requirement_represented() -> None:
    slot = build_surface_availability_slot(
        "corp",
        availability_status=TopbarSurfaceAvailabilityStatus.UNAVAILABLE_BACKEND_MISSING,
        unavailable_reason="UNAVAILABLE_BACKEND_MISSING: Business backend missing",
        required_backend="BusinessEnvironment runtime backend",
        required_future_pack="P2.2",
    )
    assert slot.is_unavailable is True
    assert slot.required_backend == "BusinessEnvironment runtime backend"
    assert slot.required_future_pack == "P2.2"
    assert slot.requires_runtime_probe is False
    assert slot.runtime_probe_performed is False


# ---------------------------------------------------------------------------
# P2.1.8 protected boundary / SYSTEM guard
# ---------------------------------------------------------------------------


def test_protected_boundary_slots_build_for_system_and_settings() -> None:
    slots = build_protected_boundary_slots()
    assert tuple(slot.surface_id for slot in slots) == ("system", "settings")


def test_system_protected_slot_operator_only_agent_blocked() -> None:
    slot = build_protected_boundary_slot("system")
    assert slot.protected_reason == TopbarProtectedBoundaryReason.SYSTEM_PROTECTED
    assert slot.operator_only is True
    assert slot.agent_access_allowed is False
    assert slot.requires_explicit_operator_action is True
    assert slot.is_system_root is True


def test_settings_is_non_root_configuration_slot() -> None:
    slot = build_protected_boundary_slot("settings")
    assert slot.is_settings_non_root is True
    assert slot.is_system_root is False


def test_protected_boundary_display_does_not_enforce_or_grant() -> None:
    for slot in build_protected_boundary_slots():
        assert slot.enforces_security is False
        assert slot.grants_access is False
        assert slot.custos_called is False
        assert slot.policy_enforced is False


# ---------------------------------------------------------------------------
# P2.1.9 attention/status indicator
# ---------------------------------------------------------------------------


def test_attention_slot_builds_and_links_surface() -> None:
    slot = build_topbar_attention_status_slot(surface_id="hq")
    assert slot.attention_kind == TopbarAttentionKind.INFO
    assert slot.surface_id == "hq"
    assert slot.severity == TopbarAttentionSeverity.LOW


@pytest.mark.parametrize("kind", tuple(TopbarAttentionKind))
def test_allowed_attention_kinds_accepted(kind: TopbarAttentionKind) -> None:
    reason = (
        "UNAVAILABLE: required for unavailable attention"
        if kind == TopbarAttentionKind.UNAVAILABLE
        else ""
    )
    slot = build_topbar_attention_status_slot(
        attention_kind=kind,
        unavailable_reason=reason,
    )
    assert slot.attention_kind == kind


def test_invalid_attention_kind_rejected() -> None:
    with pytest.raises(AurelShellValidationError):
        build_topbar_attention_status_slot(attention_kind="NOTICE")


@pytest.mark.parametrize("severity", tuple(TopbarAttentionSeverity))
def test_allowed_attention_severities_accepted(
    severity: TopbarAttentionSeverity,
) -> None:
    slot = build_topbar_attention_status_slot(severity=severity)
    assert slot.severity == severity


def test_invalid_attention_severity_rejected() -> None:
    with pytest.raises(AurelShellValidationError):
        build_topbar_attention_status_slot(severity="CRITICAL")


def test_attention_slots_are_not_events_or_notification_engine() -> None:
    for slot in build_topbar_attention_status_slots():
        assert slot.is_runtime_event is False
        assert slot.is_notification_engine is False
        assert slot.approval_queue_created is False
        assert slot.workflow_started is False


# ---------------------------------------------------------------------------
# P2.1.10 status projection/result
# ---------------------------------------------------------------------------


def test_status_projection_builds_and_includes_all_slot_groups() -> None:
    projection = build_topbar_status_projection()
    assert projection.operator_context_slot.operator_context_id
    assert len(projection.surface_availability_slots) == 7
    assert {slot.surface_id for slot in projection.protected_boundary_slots} == {
        "system",
        "settings",
    }
    assert projection.attention_status_slots
    assert projection.unavailable_bindings


def test_status_projection_extends_p2_1_a_registry_read_model() -> None:
    registry = build_default_topbar_surface_registry()
    read_model = build_global_topbar_read_model(registry=registry)
    assert_topbar_status_extends_p2_1_a_read_model(
        read_model,
        registry,
    )


def test_status_projection_references_registry_and_read_model() -> None:
    projection = build_topbar_status_projection()
    assert projection.registry_ref == "topbar_surface_registry_default"
    assert projection.topbar_read_model_ref == "global_topbar_read_model_default"


def test_pack_result_covers_p2_1_6_to_p2_1_10_and_next_pack() -> None:
    result = build_p2_1_b_topbar_status_slots_result()
    assert result.covered_checkpoints == P2_1_B_PACK_CHECKPOINT_IDS
    assert result.checkpoint_statuses == {
        checkpoint: "DONE" for checkpoint in P2_1_B_PACK_CHECKPOINT_IDS
    }
    assert result.next_pack == P2_1_B_NEXT_PACK


def test_unavailable_bindings_include_reasons() -> None:
    projection = build_topbar_status_projection()
    assert projection.unavailable_bindings
    assert all(binding.unavailable_reason for binding in projection.unavailable_bindings)


def test_side_effect_proof_false_for_forbidden_work() -> None:
    proof = build_p2_1_b_side_effect_proof()
    assert _all_dataclass_bools_false(proof)


def test_projection_has_no_ui_runtime_notification_memory_trace_effects() -> None:
    projection = build_topbar_status_projection()
    assert projection.is_live_ui is False
    assert projection.creates_ui is False
    assert projection.creates_notification_engine is False
    assert projection.emits_runtime_event is False
    assert projection.mutates_runtime is False
    assert projection.writes_memory is False
    assert projection.writes_trace is False
    assert projection.side_effect_proof.notification_engine_created is False
    assert projection.side_effect_proof.runtime_event_stream_created is False
    assert projection.side_effect_proof.auth_session_backend_created is False
    assert projection.side_effect_proof.permission_enforcement_created is False
    assert projection.side_effect_proof.custos_integration_created is False
