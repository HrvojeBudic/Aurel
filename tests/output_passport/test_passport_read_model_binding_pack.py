"""Focused tests for P1.9-B read model / test harness / binding pack."""

from __future__ import annotations

import json
import sys
from dataclasses import fields

import pytest

sys.path.insert(0, "src")

from agentic_runtime.output_passport import (
    OUTPUT_PASSPORT_P1_9_B_CHECKPOINT_IDS,
    OUTPUT_PASSPORT_P1_9_B_NEXT_PACK_ID,
    OUTPUT_PASSPORT_P1_9_B_PACK_TASK_ID,
    AgentOutputPassportBinding,
    BusinessEnvironmentOutputPassportBinding,
    MemoryVsEvidenceSupportBoundary,
    OutputPassportBindingStatus,
    OutputPassportBindingUnavailableReason,
    OutputPassportNonVerificationReason,
    OutputPassportOperatorReviewStatus,
    OutputPassportSideEffectProof,
    OutputPassportTruthLabel,
    OutputPassportVerificationStatus,
    P19BReadModelTestHarnessBindingPackResult,
    SupportDisclosureStatus,
    ToolOutputPassportBinding,
    WorkflowOutputPassportBinding,
    bind_passport_to_agent,
    bind_passport_to_business_environment,
    bind_passport_to_tool,
    bind_passport_to_workflow,
    build_dev_fixture_output_passport_payload,
    build_harness_case_with_binding_execution_flags,
    build_harness_case_with_truth_label_override,
    build_memory_supported_vs_evidence_supported_disclosure,
    build_operator_review_state_field,
    build_output_passport_read_model,
    build_output_passport_verification_contract,
    build_p1_9_a_passport_pack_result,
    build_p1_9_b_read_model_test_harness_binding_pack_result,
    run_output_passport_invariant_harness,
    serialize_output_passport_binding_result,
    serialize_output_passport_harness_summary,
    serialize_output_passport_read_model,
    serialize_output_passport_verification_contract,
    to_canonical_json,
)
from agentic_runtime.output_passport.foundation import OutputPassportValidationError
from agentic_runtime.output_passport.verification_contract import (
    build_output_passport_non_verification_boundary,
)


def assert_all_side_effects_false(proof: OutputPassportSideEffectProof) -> None:
    for side_effect_field in fields(proof):
        assert getattr(proof, side_effect_field.name) is False


def test_p1_9_a_dependency_imports_and_fixture_available():
    assert build_p1_9_a_passport_pack_result().pack_id == "P1.9-A"
    payload = build_dev_fixture_output_passport_payload()
    assert payload.identity.passport_id == "dev-passport-001"


def test_p1_9_8_read_model_builds_and_serializes():
    read_model = build_output_passport_read_model()
    assert read_model.checkpoint_id == "P1.9.8"
    assert read_model.truth_label is OutputPassportTruthLabel.READ_MODEL_ONLY
    assert read_model.verification_status is OutputPassportVerificationStatus.NOT_VERIFIED
    assert read_model.truth_label is not OutputPassportTruthLabel.LIVE
    assert read_model.truth_label is not OutputPassportTruthLabel.TRACE_VERIFIED
    assert_all_side_effects_false(read_model.side_effects)
    section_ids = {section.section_id for section in read_model.display_sections}
    assert section_ids == {
        "identity",
        "attribution",
        "authority_policy_risk",
        "memory_influence",
        "evidence_trace",
        "uncertainty",
        "hash",
        "verification_state",
    }
    serialized = serialize_output_passport_read_model(read_model)
    json.loads(serialized)


def test_p1_9_8_read_model_hash_summary_not_truth():
    read_model = build_output_passport_read_model()
    assert "hash_is_truth=false" in read_model.consumer_summary.hash_summary


@pytest.mark.parametrize(
    "truth_label",
    [
        OutputPassportTruthLabel.LIVE,
        OutputPassportTruthLabel.TRACE_VERIFIED,
        OutputPassportTruthLabel.EVIDENCE_FINAL,
    ],
)
def test_p1_9_8_read_model_forbidden_labels_detectable(truth_label):
    read_model = build_output_passport_read_model(truth_label=truth_label)
    assert read_model.truth_label is truth_label


def test_p1_9_9_verification_contract_default_not_verified():
    contract = build_output_passport_verification_contract()
    assert contract.verification_status is OutputPassportVerificationStatus.NOT_VERIFIED
    assert (
        contract.non_verification_reason
        is OutputPassportNonVerificationReason.NO_VERIFIER_AVAILABLE
    )
    assert contract.boundary.verifier_executed is False
    assert contract.boundary.trace_verified is False
    assert contract.boundary.ledger_written is False
    assert contract.boundary.global_trace_written is False
    assert contract.boundary.evidence_finalized is False
    assert contract.truth_label is OutputPassportTruthLabel.VERIFICATION_CONTRACT_ONLY
    assert_all_side_effects_false(contract.side_effects)


def test_p1_9_9_cannot_claim_verified_without_proof():
    with pytest.raises(OutputPassportValidationError):
        build_output_passport_verification_contract(
            verification_status=OutputPassportVerificationStatus.VERIFIED,
        )


def test_p1_9_9_verification_contract_serializes():
    contract = build_output_passport_verification_contract()
    json.loads(serialize_output_passport_verification_contract(contract))


def test_p1_9_9_non_verification_boundary_future_requirements():
    boundary = build_output_passport_non_verification_boundary()
    assert boundary.future_requirements
    assert boundary.contract_is_verification is False


def test_p1_9_10_harness_passes_valid_fixture():
    summary = run_output_passport_invariant_harness()
    assert summary.all_passed is True
    assert summary.fail_count == 0
    assert summary.truth_label is OutputPassportTruthLabel.TEST_HARNESS_ONLY
    assert_all_side_effects_false(summary.side_effects)
    json.loads(serialize_output_passport_harness_summary(summary))


def test_p1_9_10_harness_fails_fake_live():
    case = build_harness_case_with_truth_label_override(
        truth_label=OutputPassportTruthLabel.LIVE,
    )
    summary = run_output_passport_invariant_harness(case=case)
    assert summary.all_passed is False
    assert any(
        not result.passed
        and result.reason == "read_model truth_label is LIVE"
        for result in summary.results
    )


def test_p1_9_10_harness_fails_fake_trace_verified():
    case = build_harness_case_with_truth_label_override(
        truth_label=OutputPassportTruthLabel.TRACE_VERIFIED,
    )
    summary = run_output_passport_invariant_harness(case=case)
    assert summary.all_passed is False


def test_p1_9_10_harness_fails_fake_evidence_final():
    case = build_harness_case_with_truth_label_override(
        truth_label=OutputPassportTruthLabel.EVIDENCE_FINAL,
    )
    summary = run_output_passport_invariant_harness(case=case)
    assert summary.all_passed is False


def test_p1_9_10_harness_fails_binding_claiming_execution():
    case = build_harness_case_with_binding_execution_flags()
    summary = run_output_passport_invariant_harness(case=case)
    assert summary.all_passed is False


def test_p1_9_11_operator_review_state_serializes():
    review = build_operator_review_state_field()
    assert review.review_status is OutputPassportOperatorReviewStatus.NOT_REQUIRED
    assert review.grants_permission is False
    assert review.approves_execution is False
    assert review.truth_label is OutputPassportTruthLabel.REVIEW_STATE_ONLY
    assert_all_side_effects_false(review.side_effects)
    json.loads(to_canonical_json(review))


@pytest.mark.parametrize(
    "status",
    [
        OutputPassportOperatorReviewStatus.PENDING,
        OutputPassportOperatorReviewStatus.REJECTED,
        OutputPassportOperatorReviewStatus.REVISION_REQUESTED,
    ],
)
def test_p1_9_11_operator_review_states_supported(status):
    review = build_operator_review_state_field(review_status=status)
    assert review.review_status is status
    assert review.grants_permission is False
    assert review.approves_execution is False


def test_p1_9_11_review_embedded_in_read_model():
    read_model = build_output_passport_read_model()
    assert read_model.operator_review_state.review_status is (
        OutputPassportOperatorReviewStatus.NOT_REQUIRED
    )


def test_p1_9_12_business_binding_builds():
    binding = bind_passport_to_business_environment()
    assert isinstance(binding, BusinessEnvironmentOutputPassportBinding)
    assert binding.binding_status is OutputPassportBindingStatus.REFERENCE_ONLY
    assert binding.binding_truth_label is OutputPassportTruthLabel.REFERENCE_ONLY
    assert binding.side_effects.business_action_executed is False
    json.loads(to_canonical_json(binding))


def test_p1_9_12_business_binding_unavailable_reason():
    binding = bind_passport_to_business_environment(business_environment_ref=None)
    assert binding.binding_status is OutputPassportBindingStatus.UNAVAILABLE
    assert (
        binding.unavailable_reason
        is OutputPassportBindingUnavailableReason.UNAVAILABLE_BUSINESS_CONTEXT
    )


def test_p1_9_13_workflow_binding_builds():
    binding = bind_passport_to_workflow()
    assert isinstance(binding, WorkflowOutputPassportBinding)
    assert binding.binding_truth_label is OutputPassportTruthLabel.REFERENCE_ONLY
    assert binding.side_effects.workflow_executed is False
    assert binding.side_effects.workflow_mutated is False


def test_p1_9_13_workflow_binding_unavailable_reason():
    binding = bind_passport_to_workflow(workflow_ref=None)
    assert binding.binding_status is OutputPassportBindingStatus.UNAVAILABLE
    assert (
        binding.unavailable_reason
        is OutputPassportBindingUnavailableReason.UNAVAILABLE_WORKFLOW_CONTEXT
    )


def test_p1_9_14_agent_binding_builds():
    binding = bind_passport_to_agent()
    assert isinstance(binding, AgentOutputPassportBinding)
    assert binding.binding_truth_label is OutputPassportTruthLabel.REFERENCE_ONLY
    assert binding.side_effects.agent_executed is False
    assert binding.side_effects.agent_authority_created is False


def test_p1_9_14_agent_binding_unavailable_reason():
    binding = bind_passport_to_agent(agent_ref=None)
    assert binding.binding_status is OutputPassportBindingStatus.UNAVAILABLE
    assert (
        binding.unavailable_reason
        is OutputPassportBindingUnavailableReason.UNAVAILABLE_AGENT_CONTEXT
    )


def test_p1_9_15_tool_binding_builds():
    binding = bind_passport_to_tool()
    assert isinstance(binding, ToolOutputPassportBinding)
    assert binding.binding_truth_label is OutputPassportTruthLabel.REFERENCE_ONLY
    assert binding.side_effects.tool_executed is False
    assert binding.side_effects.tool_permission_granted is False


def test_p1_9_15_tool_binding_unavailable_reason():
    binding = bind_passport_to_tool(tool_ref=None)
    assert binding.binding_status is OutputPassportBindingStatus.UNAVAILABLE
    assert (
        binding.unavailable_reason
        is OutputPassportBindingUnavailableReason.UNAVAILABLE_TOOL_CONTEXT
    )


@pytest.mark.parametrize(
    "status",
    [
        SupportDisclosureStatus.MEMORY_SUPPORTED,
        SupportDisclosureStatus.EVIDENCE_SUPPORTED,
        SupportDisclosureStatus.BOTH_MEMORY_AND_EVIDENCE_SUPPORTED,
        SupportDisclosureStatus.UNSUPPORTED,
        SupportDisclosureStatus.UNAVAILABLE,
        SupportDisclosureStatus.REDACTED,
    ],
)
def test_p1_9_16_support_states_serialize(status):
    boundary = build_memory_supported_vs_evidence_supported_disclosure(
        support_status=status,
    )
    assert isinstance(boundary, MemoryVsEvidenceSupportBoundary)
    assert boundary.memory_implies_evidence is False
    assert boundary.evidence_implies_verified is False
    assert boundary.evidence_disclosure.implies_trace_verified is False
    assert_all_side_effects_false(boundary.side_effects)
    json.loads(to_canonical_json(boundary))


def test_p1_9_16_memory_support_does_not_imply_evidence():
    boundary = build_memory_supported_vs_evidence_supported_disclosure(
        support_status=SupportDisclosureStatus.MEMORY_SUPPORTED,
    )
    assert boundary.memory_only is True
    assert boundary.evidence_only is False
    assert boundary.memory_implies_evidence is False


def test_p1_9_16_evidence_support_does_not_imply_verified():
    boundary = build_memory_supported_vs_evidence_supported_disclosure(
        support_status=SupportDisclosureStatus.EVIDENCE_SUPPORTED,
    )
    assert boundary.evidence_only is True
    assert boundary.evidence_implies_verified is False
    assert boundary.evidence_disclosure.implies_verified is False


def test_p1_9_b_pack_result_covers_checkpoints():
    result = build_p1_9_b_read_model_test_harness_binding_pack_result()
    assert isinstance(result, P19BReadModelTestHarnessBindingPackResult)
    assert result.pack_id == OUTPUT_PASSPORT_P1_9_B_PACK_TASK_ID
    assert result.covered_checkpoints == OUTPUT_PASSPORT_P1_9_B_CHECKPOINT_IDS
    assert result.next_pack == OUTPUT_PASSPORT_P1_9_B_NEXT_PACK_ID
    assert len(result.checkpoint_reads) == 9
    for checkpoint_id in OUTPUT_PASSPORT_P1_9_B_CHECKPOINT_IDS:
        assert result.checkpoint_statuses[checkpoint_id] == "DONE"
    assert result.harness_summary.all_passed is True
    assert_all_side_effects_false(result.side_effect_proof)
    json.loads(serialize_output_passport_binding_result(result))


def test_p1_9_b_pack_result_truth_labels_honest():
    result = build_p1_9_b_read_model_test_harness_binding_pack_result()
    labels = set(result.truth_labels)
    assert OutputPassportTruthLabel.READ_MODEL_ONLY in labels
    assert OutputPassportTruthLabel.VERIFICATION_CONTRACT_ONLY in labels
    assert OutputPassportTruthLabel.LIVE not in labels
    assert OutputPassportTruthLabel.TRACE_VERIFIED not in labels
