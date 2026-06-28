"""Focused tests for P1.9-C truth boundary / failure / readiness pack."""

from __future__ import annotations

import json
import sys
from dataclasses import fields

import pytest

sys.path.insert(0, "src")

from agentic_runtime.output_passport import (
    OUTPUT_PASSPORT_P1_9_C_CHECKPOINT_IDS,
    OUTPUT_PASSPORT_P1_9_C_NEXT_PACK_ID,
    OUTPUT_PASSPORT_P1_9_C_PACK_TASK_ID,
    OutputPassportFailureReason,
    OutputPassportRealityLabel,
    OutputPassportSideEffectProof,
    OutputPassportTruthLabel,
    P19CTruthBoundaryFailureReadinessPackResult,
    ReplaySeedUnavailableReason,
    SURFACE_CONSUMER_KINDS,
    SurfacePassportConsumerKind,
    TracePayloadStatus,
    TraceVerificationClaimStatus,
    build_all_surface_passport_read_models,
    build_heretic_quarantined_output_disclosure,
    build_lora_adapter_influence_disclosure,
    build_mock_dev_fixture_simulated_disclosure,
    build_output_passport_failure_unavailable_handling,
    build_output_passport_operator_testable_path,
    build_output_passport_readiness_audit,
    build_output_passport_replay_seed,
    build_output_passport_revision_history,
    build_p1_9_a_passport_pack_result,
    build_p1_9_b_read_model_test_harness_binding_pack_result,
    build_p1_9_c_truth_boundary_failure_readiness_pack_result,
    build_surface_passport_read_model,
    build_trace_payload_vs_verification_boundary,
    run_output_passport_readiness_audit,
    serialize_fixture_disclosure,
    serialize_output_passport_truth_readiness_payload,
    serialize_replay_seed,
    serialize_surface_read_model,
    serialize_trace_verification_boundary,
)
from agentic_runtime.output_passport.foundation import OutputPassportValidationError
from agentic_runtime.output_passport.readiness_audit import (
    OutputPassportReadinessAuditStatus,
)


def assert_all_side_effects_false(proof: OutputPassportSideEffectProof) -> None:
    for side_effect_field in fields(proof):
        assert getattr(proof, side_effect_field.name) is False


def test_p1_9_a_b_dependency_imports():
    assert build_p1_9_a_passport_pack_result().pack_id == "P1.9-A"
    assert build_p1_9_b_read_model_test_harness_binding_pack_result().pack_id == "P1.9-B"


def test_p1_9_17_trace_payload_serializes_and_not_verified():
    payload_disclosure, boundary = build_trace_payload_vs_verification_boundary()
    assert payload_disclosure.trace_payload_present is True
    assert boundary.trace_verified is False
    assert boundary.ledger_written is False
    assert boundary.global_trace_written is False
    assert boundary.trace_verification_status is TraceVerificationClaimStatus.NOT_VERIFIED
    assert boundary.truth_label is OutputPassportTruthLabel.NOT_VERIFIED
    assert_all_side_effects_false(boundary.side_effects)
    json.loads(serialize_trace_verification_boundary(boundary))


def test_p1_9_17_reference_only_remains_not_verified():
    payload_disclosure, boundary = build_trace_payload_vs_verification_boundary(
        trace_payload_present=False,
        trace_ref_present=True,
        payload_ref=None,
        trace_payload_status=TracePayloadStatus.REFERENCE_ONLY,
    )
    assert payload_disclosure.reference_only_state is True
    assert boundary.trace_verified is False


def test_p1_9_17_payload_does_not_set_verification():
    _, boundary = build_trace_payload_vs_verification_boundary()
    assert boundary.trace_verified is False
    assert boundary.truth_label is not OutputPassportTruthLabel.TRACE_VERIFIED


@pytest.mark.parametrize(
    "reality_label,expected_truth",
    [
        (OutputPassportRealityLabel.MOCK, OutputPassportTruthLabel.MOCK),
        (OutputPassportRealityLabel.DEV_FIXTURE, OutputPassportTruthLabel.DEV_FIXTURE),
        (OutputPassportRealityLabel.SIMULATED, OutputPassportTruthLabel.SIMULATED),
    ],
)
def test_p1_9_18_non_live_labels_distinct(reality_label, expected_truth):
    fixture, boundary = build_mock_dev_fixture_simulated_disclosure(
        reality_label=reality_label,
    )
    assert fixture.reality_label is reality_label
    assert fixture.truth_label is expected_truth
    assert boundary.mock_is_live is False
    assert fixture.live_unavailable_reason
    json.loads(serialize_fixture_disclosure(fixture))


def test_p1_9_18_labels_cannot_collapse_to_live():
    fixture, _ = build_mock_dev_fixture_simulated_disclosure()
    assert fixture.truth_label is not OutputPassportTruthLabel.LIVE


def test_p1_9_19_heretic_quarantine_disclosure():
    heretic, quarantine = build_heretic_quarantined_output_disclosure()
    assert heretic.heretic_origin_declared is True
    assert heretic.trust_status is OutputPassportTruthLabel.NOT_TRUSTED
    assert heretic.accepted_output is False
    assert quarantine.accepted_output is False
    assert quarantine.review_required is True
    assert quarantine.quarantine_status is OutputPassportTruthLabel.QUARANTINED
    assert_all_side_effects_false(heretic.side_effects)


def test_p1_9_20_lora_adapter_influence_not_approval():
    lora, adapter = build_lora_adapter_influence_disclosure()
    assert lora.approval_status is OutputPassportTruthLabel.NOT_APPROVAL
    assert lora.promotion_status is OutputPassportTruthLabel.NOT_PROMOTION
    assert adapter.approval_status is OutputPassportTruthLabel.NOT_APPROVAL
    assert adapter.promotion_status is OutputPassportTruthLabel.NOT_PROMOTION
    assert_all_side_effects_false(lora.side_effects)


@pytest.mark.parametrize(
    "consumer_kind",
    list(SurfacePassportConsumerKind),
)
def test_p1_9_21_surface_read_models(consumer_kind):
    read_model = build_surface_passport_read_model(consumer_kind=consumer_kind)
    assert read_model.truth_label is OutputPassportTruthLabel.READ_MODEL_ONLY
    assert read_model.readiness_summary.ui_available is False
    assert read_model.readiness_summary.shell_route_created is False
    assert read_model.side_effects.surface_ui_created is False
    json.loads(serialize_surface_read_model(read_model))


def test_p1_9_21_all_five_surfaces():
    surfaces = build_all_surface_passport_read_models()
    assert len(surfaces) == len(SURFACE_CONSUMER_KINDS) == 5
    kinds = {s.consumer_kind for s in surfaces}
    assert SurfacePassportConsumerKind.AUREL_CRO in kinds
    assert SurfacePassportConsumerKind.IDE in kinds


def test_p1_9_22_operator_test_path():
    path = build_output_passport_operator_testable_path()
    assert path.truth_label is OutputPassportTruthLabel.TEST_PATH_ONLY
    assert len(path.steps) == 6
    assert path.result.fake_live_detected is False
    assert path.result.fake_trace_verified_detected is False
    assert path.result.fake_seal_detected is False
    assert_all_side_effects_false(path.side_effects)


def test_p1_9_22_path_catches_fake_labels():
    path = build_output_passport_operator_testable_path(
        truth_labels_to_check=(
            OutputPassportTruthLabel.LIVE,
            OutputPassportTruthLabel.TRACE_VERIFIED,
            OutputPassportTruthLabel.EXIT_SEALED,
        ),
    )
    assert path.result.fake_live_detected is True
    assert path.result.fake_trace_verified_detected is True
    assert path.result.fake_seal_detected is True
    assert path.result.all_steps_passed is False


def test_p1_9_23_revision_history_append_only():
    history = build_output_passport_revision_history(
        rejection_reason="operator_rejected_initial_submission",
    )
    assert history.append_only_contract is True
    assert history.destructive_overwrite_forbidden is True
    assert len(history.entries) == 1
    assert history.entries[0].previous_passport_ref == "dev-passport-001-v0"
    assert len(history.rejections) == 1


def test_p1_9_24_replay_seed_no_execution():
    seed = build_output_passport_replay_seed()
    assert seed.determinism_boundary.replay_executed is False
    assert seed.determinism_boundary.output_verified is False
    assert seed.determinism_boundary.model_called is False
    assert seed.truth_label is OutputPassportTruthLabel.REPLAY_SEED_ONLY
    assert seed.replay_unavailable_reason is not None
    assert_all_side_effects_false(seed.side_effects)
    json.loads(serialize_replay_seed(seed))


def test_p1_9_24_missing_prerequisites_unavailable():
    seed = build_output_passport_replay_seed(input_refs=(), hash_refs=())
    assert seed.replay_unavailable_reason is ReplaySeedUnavailableReason.MISSING_INPUT_REFS


def test_p1_9_25_failure_unavailable_serializes():
    failure, unavailable = build_output_passport_failure_unavailable_handling()
    assert failure.failure_kind is OutputPassportFailureReason.CONTRACT_VIOLATION
    assert unavailable.unavailable_reason
    assert unavailable.truth_label is OutputPassportTruthLabel.UNAVAILABLE


def test_p1_9_25_missing_unavailable_reason_invalid():
    with pytest.raises(OutputPassportValidationError):
        build_output_passport_failure_unavailable_handling(unavailable_reason="")


def test_p1_9_25_unknown_failure_reason_rejected():
    with pytest.raises(ValueError):
        OutputPassportFailureReason("not_a_real_failure")


def test_p1_9_26_readiness_audit_passes_valid_fixture():
    audit = build_output_passport_readiness_audit()
    assert audit.truth_label is OutputPassportTruthLabel.READINESS_AUDIT_ONLY
    assert audit.truth_label is not OutputPassportTruthLabel.SEALED
    assert audit.truth_label is not OutputPassportTruthLabel.EXIT_SEALED
    assert audit.audit_result.next_pack == "P1.9-D"
    assert audit.audit_result.next_pack_tasks
    assert audit.audit_result.audit_status in (
        OutputPassportReadinessAuditStatus.CONDITIONAL,
        OutputPassportReadinessAuditStatus.READY,
    )


def test_p1_9_26_audit_fails_fake_seal():
    result = run_output_passport_readiness_audit(
        truth_labels=(OutputPassportTruthLabel.EXIT_SEALED,),
    )
    assert result.audit_status is OutputPassportReadinessAuditStatus.BLOCKED
    assert "fake_seal_label_detected" in result.gaps


def test_p1_9_26_audit_fails_fake_trace_verified():
    result = run_output_passport_readiness_audit(
        truth_labels=(OutputPassportTruthLabel.TRACE_VERIFIED,),
    )
    assert result.audit_status is OutputPassportReadinessAuditStatus.BLOCKED


def test_pack_result_covers_p1_9_17_to_26():
    result = build_p1_9_c_truth_boundary_failure_readiness_pack_result()
    assert isinstance(result, P19CTruthBoundaryFailureReadinessPackResult)
    assert result.pack_id == OUTPUT_PASSPORT_P1_9_C_PACK_TASK_ID
    assert result.next_pack == OUTPUT_PASSPORT_P1_9_C_NEXT_PACK_ID
    assert result.covered_checkpoints == OUTPUT_PASSPORT_P1_9_C_CHECKPOINT_IDS
    assert len(result.checkpoint_reads) == 10
    for checkpoint_id in OUTPUT_PASSPORT_P1_9_C_CHECKPOINT_IDS:
        assert result.checkpoint_statuses[checkpoint_id] == "DONE"
    assert_all_side_effects_false(result.side_effect_proof)
    json.loads(serialize_output_passport_truth_readiness_payload(result))


def test_p1_9_c_extended_side_effects_all_false():
    result = build_p1_9_c_truth_boundary_failure_readiness_pack_result()
    proof = result.side_effect_proof
    assert proof.heretic_executed is False
    assert proof.heretic_accepted is False
    assert proof.quarantine_released is False
    assert proof.lora_activated is False
    assert proof.lora_promoted is False
    assert proof.replay_executed is False
    assert proof.exit_sealed is False
    assert proof.surface_ui_created is False
    assert proof.cli_binding_created is False
