"""Focused tests for P1.8-C delegation integration tail projection."""

import json
import sys
from dataclasses import fields
from pathlib import Path

import pytest

sys.path.insert(0, "src")

from agentic_runtime.delegation import (  # noqa: E402
    DELEGATION_ACTION_BOUNDARY_PACK_TASK_ID,
    DELEGATION_ACTOR_BOUNDARY_PACK_TASK_ID,
    DELEGATION_CLI_UNAVAILABLE_REASON,
    DELEGATION_INTEGRATION_TAIL_PACK_CHECKPOINT_IDS,
    DELEGATION_INTEGRATION_TAIL_PACK_TASK_ID,
    DELEGATION_NEXT_PACK,
    DelegationEventPayload,
    DelegationExitSealResult,
    DelegationOperatorDemoResult,
    DelegationOperatorDemoStatus,
    DelegationProjectionKind,
    DelegationProjectionSideEffects,
    DelegationProjectionStatus,
    DelegationProjectionTruthLabel,
    DelegationSectionProjectionPayload,
    DelegationSectionReadModel,
    DelegationSectionSealStatus,
    assert_event_not_dispatched,
    assert_projection_is_read_only,
    assert_seal_honest,
    build_p1_8_a_actor_boundary_pack_result,
    build_p1_8_b_action_boundary_pack_result,
    build_p1_8_delegation_event_payload,
    build_p1_8_delegation_projection_payload,
    build_p1_8_delegation_section_read_model,
    build_p1_8_exit_seal_result,
    build_p1_8_operator_demo_result,
    hash_delegation_action_boundary_pack_result,
    hash_delegation_actor_boundary_pack_result,
    hash_delegation_event_payload,
    hash_delegation_exit_seal_result,
    hash_delegation_operator_demo_result,
    hash_delegation_section_projection_payload,
    hash_delegation_section_read_model,
    serialize_delegation_action_boundary_pack_result,
    serialize_delegation_actor_boundary_pack_result,
    serialize_delegation_section_projection_payload,
    serialize_delegation_section_read_model,
    serialize_p1_8_delegation_projection,
)
from agentic_runtime.delegation.foundation import (  # noqa: E402
    DelegationSourceLabel,
)


def assert_all_side_effects_false(
    side_effects: DelegationProjectionSideEffects,
) -> None:
    for field in fields(side_effects):
        assert getattr(side_effects, field.name) is False


# ---------------------------------------------------------------------------
# Import / export tests
# ---------------------------------------------------------------------------


def test_module_and_package_exports_available():
    assert DELEGATION_INTEGRATION_TAIL_PACK_TASK_ID == "P1.8-C"
    assert DELEGATION_INTEGRATION_TAIL_PACK_CHECKPOINT_IDS == (
        "P1.8.27",
        "P1.8.28",
        "P1.8.29",
        "P1.8.30",
    )
    assert DELEGATION_NEXT_PACK == "P1.9-A"
    assert DelegationSectionReadModel is not None
    assert DelegationSectionProjectionPayload is not None
    assert DelegationEventPayload is not None
    assert DelegationOperatorDemoResult is not None
    assert DelegationExitSealResult is not None
    assert DelegationProjectionSideEffects is not None


def test_p1_8_a_exports_still_work():
    assert DELEGATION_ACTOR_BOUNDARY_PACK_TASK_ID == "P1.8-A"
    a_result = build_p1_8_a_actor_boundary_pack_result()
    assert a_result.task_id == "P1.8-A"
    assert len(hash_delegation_actor_boundary_pack_result(a_result)) == 64


def test_p1_8_b_exports_still_work():
    assert DELEGATION_ACTION_BOUNDARY_PACK_TASK_ID == "P1.8-B"
    b_result = build_p1_8_b_action_boundary_pack_result()
    assert b_result.task_id == "P1.8-B"
    assert len(hash_delegation_action_boundary_pack_result(b_result)) == 64


# ---------------------------------------------------------------------------
# Dependency tests
# ---------------------------------------------------------------------------


def test_p1_8_a_dependency_files_exist():
    assert Path("agent/reports/P1_8_A_ACTOR_BOUNDARY_PACK.md").is_file()
    assert Path("src/agentic_runtime/delegation/actor_boundary.py").is_file()
    assert Path("tests/delegation/test_actor_boundary.py").is_file()


def test_p1_8_b_dependency_files_exist():
    assert Path(
        "agent/reports/P1_8_B_PROPOSAL_PERMISSION_EXECUTION_OPERATOR_REVIEW_PACK.md"
    ).is_file()
    assert Path("src/agentic_runtime/delegation/action_boundary.py").is_file()
    assert Path("tests/delegation/test_action_boundary.py").is_file()


def test_p1_8_c_does_not_duplicate_a_or_b():
    a_result = build_p1_8_a_actor_boundary_pack_result()
    b_result = build_p1_8_b_action_boundary_pack_result()
    rm = build_p1_8_delegation_section_read_model(
        actor_boundary_pack=a_result,
        action_boundary_pack=b_result,
    )
    assert rm.actor_boundary_pack_ref == "P1.8-A"
    assert rm.action_boundary_pack_ref == "P1.8-B"
    assert rm.actor_boundary_result_hash == a_result.result_hash
    assert rm.action_boundary_result_hash == b_result.result_hash
    assert rm.actor_boundary_checkpoint_count == 6
    assert rm.action_boundary_checkpoint_count == 4


# ---------------------------------------------------------------------------
# Enum integrity
# ---------------------------------------------------------------------------


def test_projection_enums_include_expected_values():
    assert DelegationProjectionKind.SECTION_READ_MODEL.value == "section_read_model"
    assert DelegationProjectionKind.PROJECTION_PAYLOAD.value == "projection_payload"
    assert DelegationProjectionKind.EVENT_PAYLOAD.value == "event_payload"
    assert DelegationProjectionKind.EXIT_SEAL.value == "exit_seal"
    assert (
        DelegationProjectionStatus.CLI_UNAVAILABLE.value == "cli_unavailable"
    )
    assert (
        DelegationProjectionStatus.PROJECTION_READY.value == "projection_ready"
    )
    assert (
        DelegationProjectionTruthLabel.DEV_FIXTURE.value == "DEV_FIXTURE"
    )
    assert (
        DelegationProjectionTruthLabel.UNAVAILABLE_CLI_TUI_BINDING.value
        == "UNAVAILABLE_CLI_TUI_BINDING"
    )
    assert DelegationSectionSealStatus.SEAL_PARTIAL.value == "SEAL_PARTIAL"
    assert (
        DelegationOperatorDemoStatus.DEV_FIXTURE_ONLY.value == "DEV_FIXTURE_ONLY"
    )


# ---------------------------------------------------------------------------
# Projection / read model tests
# ---------------------------------------------------------------------------


def test_unified_projection_builds():
    rm = build_p1_8_delegation_section_read_model()
    assert rm.task_id == "P1.8-C"
    assert rm.schema_version.startswith("delegation_section_read_model")
    assert rm.actor_boundary_pack_ref == "P1.8-A"
    assert rm.action_boundary_pack_ref == "P1.8-B"
    assert len(rm.read_model_hash) == 64


def test_projection_includes_actor_boundary_result():
    rm = build_p1_8_delegation_section_read_model()
    a_result = build_p1_8_a_actor_boundary_pack_result()
    assert rm.actor_boundary_result_hash == a_result.result_hash
    assert rm.actor_boundary_checkpoint_count == 6


def test_projection_includes_action_boundary_result():
    rm = build_p1_8_delegation_section_read_model()
    b_result = build_p1_8_b_action_boundary_pack_result()
    assert rm.action_boundary_result_hash == b_result.result_hash
    assert rm.action_boundary_checkpoint_count == 4


def test_projection_includes_coverage():
    rm = build_p1_8_delegation_section_read_model()
    # Should include at least P1.8.17-P1.8.30
    assert "P1.8.17" in rm.covered_checkpoints
    assert "P1.8.22" in rm.covered_checkpoints
    assert "P1.8.23" in rm.covered_checkpoints
    assert "P1.8.26" in rm.covered_checkpoints
    assert "P1.8.27" in rm.covered_checkpoints
    assert "P1.8.30" in rm.covered_checkpoints
    assert len(rm.covered_checkpoints) >= 14


def test_projection_includes_truth_labels():
    rm = build_p1_8_delegation_section_read_model()
    assert rm.truth_label == DelegationProjectionTruthLabel.DEV_FIXTURE
    assert rm.source_label == DelegationSourceLabel.DEV_FIXTURE


def test_projection_includes_unavailable_reasons():
    rm = build_p1_8_delegation_section_read_model()
    assert len(rm.unavailable_reasons) > 0
    assert "runtime_enforcement" in rm.unavailable_reason_details
    assert "trace_verification" in rm.unavailable_reason_details
    assert "cli_tui_binding" in rm.unavailable_reason_details


def test_projection_includes_next_pack_handoff():
    rm = build_p1_8_delegation_section_read_model()
    assert rm.next_pack == "P1.9-A"


def test_projection_is_json_safe():
    rm = build_p1_8_delegation_section_read_model()
    serialized = serialize_delegation_section_read_model(rm)
    payload = json.loads(serialized)
    assert payload["task_id"] == "P1.8-C"
    assert payload["actor_boundary_pack_ref"] == "P1.8-A"
    assert payload["action_boundary_pack_ref"] == "P1.8-B"
    assert len(payload["read_model_hash"]) == 64


def test_projection_deterministic():
    rm_a = build_p1_8_delegation_section_read_model()
    rm_b = build_p1_8_delegation_section_read_model()
    assert hash_delegation_section_read_model(rm_a) == hash_delegation_section_read_model(rm_b)
    assert serialize_delegation_section_read_model(rm_a) == serialize_delegation_section_read_model(rm_b)


def test_projection_never_claims_live():
    rm = build_p1_8_delegation_section_read_model()
    assert rm.truth_label != DelegationProjectionTruthLabel.CONTRACT_ONLY
    assert rm.truth_label == DelegationProjectionTruthLabel.DEV_FIXTURE
    assert rm.runtime_enforcement_status == DelegationProjectionStatus.UNAVAILABLE
    assert rm.trace_verification_status == DelegationProjectionStatus.UNAVAILABLE


def test_projection_never_claims_trace_verified():
    rm = build_p1_8_delegation_section_read_model()
    assert rm.trace_verification_status == DelegationProjectionStatus.UNAVAILABLE


def test_projection_projection_payload_builds():
    pp = build_p1_8_delegation_projection_payload()
    assert pp.task_id == "P1.8-C"
    assert pp.projection_kind == DelegationProjectionKind.PROJECTION_PAYLOAD
    assert len(pp.projection_hash) == 64
    assert pp.cli_status == DelegationProjectionStatus.CLI_UNAVAILABLE


def test_projection_payload_json_safe():
    pp = build_p1_8_delegation_projection_payload()
    serialized = serialize_delegation_section_projection_payload(pp)
    payload = json.loads(serialized)
    assert payload["projection_kind"] == "projection_payload"
    assert payload["read_model_hash"] is not None
    assert payload["next_pack"] == "P1.9-A"


# ---------------------------------------------------------------------------
# Event / payload tests
# ---------------------------------------------------------------------------


def test_event_payload_builds():
    event = build_p1_8_delegation_event_payload()
    assert event.task_id == "P1.8-C"
    assert event.event_kind == DelegationProjectionKind.EVENT_PAYLOAD
    assert event.dispatched is False
    assert len(event.event_payload_hash) == 64


def test_event_payload_does_not_dispatch():
    event = build_p1_8_delegation_event_payload()
    assert event.dispatched is False
    assert event.event_bus_status == DelegationProjectionStatus.UNAVAILABLE
    assert "dispatch" in event.unavailable_reason.lower() or "unavailable" in event.unavailable_reason.lower()


def test_event_payload_assertion():
    event = build_p1_8_delegation_event_payload()
    assert_event_not_dispatched(event)


def test_event_payload_deterministic():
    event_a = build_p1_8_delegation_event_payload()
    event_b = build_p1_8_delegation_event_payload()
    assert hash_delegation_event_payload(event_a) == hash_delegation_event_payload(event_b)


def test_event_payload_json_safe():
    event = build_p1_8_delegation_event_payload()
    payload = json.loads(json.dumps(event.to_canonical_dict(), sort_keys=True))
    assert payload["task_id"] == "P1.8-C"
    assert payload["dispatched"] is False


# ---------------------------------------------------------------------------
# CLI unavailable tests
# ---------------------------------------------------------------------------


def test_p1_8_28_cli_is_unavailable():
    rm = build_p1_8_delegation_section_read_model()
    assert rm.cli_status == DelegationProjectionStatus.CLI_UNAVAILABLE


def test_cli_unavailable_reason_is_present():
    rm = build_p1_8_delegation_section_read_model()
    assert "cli_tui_binding" in rm.unavailable_reason_details
    reason = rm.unavailable_reason_details["cli_tui_binding"]
    assert len(reason) > 20
    assert "unavailable" in reason.lower() or "UNAVAILABLE" in reason


def test_operator_testable_path_exists():
    # Builder functions and tests themselves provide the operator-testable path
    rm = build_p1_8_delegation_section_read_model()
    assert rm.read_model_hash
    assert rm.actor_boundary_result_hash
    assert rm.action_boundary_result_hash

    pp = build_p1_8_delegation_projection_payload()
    assert pp.projection_hash

    event = build_p1_8_delegation_event_payload()
    assert event.event_payload_hash


# ---------------------------------------------------------------------------
# Demo / seal tests
# ---------------------------------------------------------------------------


def test_demo_result_builds():
    demo = build_p1_8_operator_demo_result()
    assert demo.task_id == "P1.8-C"
    assert demo.demo_status == DelegationOperatorDemoStatus.DEV_FIXTURE_ONLY
    assert demo.actor_boundary_present is True
    assert demo.action_boundary_present is True
    assert demo.projection_present is True
    assert demo.runtime_enforcement_available is False
    assert demo.trace_verification_available is False
    assert demo.seal_status == DelegationSectionSealStatus.SEAL_PARTIAL
    assert len(demo.demo_result_hash) == 64


def test_demo_result_deterministic():
    demo_a = build_p1_8_operator_demo_result()
    demo_b = build_p1_8_operator_demo_result()
    assert hash_delegation_operator_demo_result(demo_a) == hash_delegation_operator_demo_result(demo_b)


def test_seal_result_builds():
    seal = build_p1_8_exit_seal_result()
    assert seal.task_id == "P1.8-C"
    assert seal.seal_status == DelegationSectionSealStatus.SEAL_PARTIAL
    assert seal.live_claimed is False
    assert seal.trace_verified_claimed is False
    assert seal.runtime_enforcement_declared is False
    assert seal.trace_verification_declared is False
    assert seal.next_pack == "P1.9-A"
    assert len(seal.seal_hash) == 64


def test_seal_result_deterministic():
    seal_a = build_p1_8_exit_seal_result()
    seal_b = build_p1_8_exit_seal_result()
    assert hash_delegation_exit_seal_result(seal_a) == hash_delegation_exit_seal_result(seal_b)


def test_seal_result_checkpoint_coverage():
    seal = build_p1_8_exit_seal_result()
    assert seal.actor_boundary_checkpoint_count == 6
    assert seal.action_boundary_checkpoint_count == 4
    assert seal.tail_checkpoint_count == 4
    total = seal.actor_boundary_checkpoint_count + seal.action_boundary_checkpoint_count + seal.tail_checkpoint_count
    assert total == 14  # P1.8.17-P1.8.30


def test_seal_never_claims_live():
    seal = build_p1_8_exit_seal_result()
    assert seal.live_claimed is False
    assert seal.trace_verified_claimed is False


def test_seal_never_claims_trace_verified():
    seal = build_p1_8_exit_seal_result()
    assert seal.trace_verified_claimed is False
    assert seal.trace_verification_declared is False


def test_seal_assertion_honest():
    seal = build_p1_8_exit_seal_result()
    assert_seal_honest(seal)


# ---------------------------------------------------------------------------
# Side-effect proof tests
# ---------------------------------------------------------------------------


def test_all_side_effects_are_false():
    rm = build_p1_8_delegation_section_read_model()
    assert_all_side_effects_false(rm.side_effects)


def test_no_policy_decision_emitted():
    rm = build_p1_8_delegation_section_read_model()
    assert rm.side_effects.policy_decision_emitted is False
    assert rm.side_effects.custos_decision_emitted is False


def test_no_approval_created():
    rm = build_p1_8_delegation_section_read_model()
    assert rm.side_effects.approval_created is False
    assert rm.side_effects.permission_granted is False


def test_no_execution_started():
    rm = build_p1_8_delegation_section_read_model()
    assert rm.side_effects.execution_started is False
    assert rm.side_effects.workflow_executed is False
    assert rm.side_effects.tool_executed is False


def test_no_ledger_or_trace_written():
    rm = build_p1_8_delegation_section_read_model()
    assert rm.side_effects.ledger_written is False
    assert rm.side_effects.global_trace_written is False


def test_no_memory_written():
    rm = build_p1_8_delegation_section_read_model()
    assert rm.side_effects.memory_written is False


def test_no_event_dispatched():
    rm = build_p1_8_delegation_section_read_model()
    assert rm.side_effects.event_dispatched is False


def test_no_system_or_runtime_mutation():
    rm = build_p1_8_delegation_section_read_model()
    assert rm.side_effects.system_boundary_mutated is False
    assert rm.side_effects.runtime_mutated is False


# ---------------------------------------------------------------------------
# Serialize convenience
# ---------------------------------------------------------------------------


def test_serialize_p1_8_projection_returns_json():
    result = serialize_p1_8_delegation_projection()
    payload = json.loads(result)
    assert payload["task_id"] == "P1.8-C"
    assert "read_model_hash" in payload


def test_serialize_p1_8_projection_deterministic():
    a = serialize_p1_8_delegation_projection()
    b = serialize_p1_8_delegation_projection()
    assert a == b


# ---------------------------------------------------------------------------
# Projection assertion helpers
# ---------------------------------------------------------------------------


def test_assertion_helpers_dont_crash_on_valid_data():
    pp = build_p1_8_delegation_projection_payload()
    event = build_p1_8_delegation_event_payload()
    seal = build_p1_8_exit_seal_result()

    assert_projection_is_read_only(pp)
    assert_event_not_dispatched(event)
    assert_seal_honest(seal)


# ---------------------------------------------------------------------------
# Truth label boundary
# ---------------------------------------------------------------------------


def test_projection_truth_label_is_honest():
    pp = build_p1_8_delegation_projection_payload()
    # Projection is PROJECTION_ONLY, not LIVE
    assert pp.truth_label == DelegationProjectionTruthLabel.PROJECTION_ONLY
    assert pp.truth_label != DelegationProjectionTruthLabel.CONTRACT_ONLY


def test_demo_truth_label_is_honest():
    demo = build_p1_8_operator_demo_result()
    assert demo.demo_status == DelegationOperatorDemoStatus.DEV_FIXTURE_ONLY
    assert demo.runtime_enforcement_available is False
    assert demo.trace_verification_available is False


# ---------------------------------------------------------------------------
# Full integration chain
# ---------------------------------------------------------------------------


def test_full_integration_chain():
    """Prove A -> B -> C chain: build all three, verify they compose."""
    a_result = build_p1_8_a_actor_boundary_pack_result()
    b_result = build_p1_8_b_action_boundary_pack_result()
    c_rm = build_p1_8_delegation_section_read_model(
        actor_boundary_pack=a_result,
        action_boundary_pack=b_result,
    )
    assert c_rm.actor_boundary_result_hash == a_result.result_hash
    assert c_rm.action_boundary_result_hash == b_result.result_hash

    c_pp = build_p1_8_delegation_projection_payload(read_model=c_rm)
    assert c_pp.read_model_hash == c_rm.read_model_hash

    c_event = build_p1_8_delegation_event_payload(projection_payload=c_pp)
    assert c_event.projection_payload_hash == c_pp.projection_hash

    c_demo = build_p1_8_operator_demo_result()
    assert c_demo.actor_boundary_present is True
    assert c_demo.action_boundary_present is True
    assert c_demo.projection_present is True

    c_seal = build_p1_8_exit_seal_result()
    assert c_seal.next_pack == "P1.9-A"

    # All serializable
    assert len(serialize_delegation_actor_boundary_pack_result(a_result)) > 0
    assert len(serialize_delegation_action_boundary_pack_result(b_result)) > 0
    assert len(serialize_delegation_section_read_model(c_rm)) > 0

    # All side effects false
    assert_all_side_effects_false(c_rm.side_effects)
