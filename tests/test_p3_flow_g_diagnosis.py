"""P3-FLOW-G root-cause diagnosis / semantic silent failure tests.

Diagnosis is advisory: confidence is not verification, evidence refs never
retrieve, low confidence forces human review, and semantic silent failures
are runtime failure candidates rather than harmless warnings.
"""

from __future__ import annotations

import pytest

from agentic_runtime.aurel_flow import (
    AurelFlowValidationError,
    DiagnosisConfidence,
    DiagnosisEvidenceKind,
    FailureRootCauseCategory,
    FlowTruthLabel,
    RuntimeFailureKind,
    build_diagnosis_read_model,
    build_diagnosis_uncertainty_frame,
    build_flow_demo_bundle,
    build_semantic_failure_read_model,
    create_contradiction_check_requirement,
    create_diagnosis_evidence_ref,
    create_evidence_missing_signal,
    create_evidence_support_requirement,
    create_root_cause_diagnosis,
    create_runtime_failure_signal,
    create_semantic_silent_failure_signal,
    create_unsupported_output_signal,
)


def _diagnosis_fixture(confidence: DiagnosisConfidence = DiagnosisConfidence.MEDIUM):
    bundle = build_flow_demo_bundle()
    signal = create_runtime_failure_signal(
        bundle.run,
        failure_kind=RuntimeFailureKind.CONTRADICTORY_EVIDENCE,
        detail="diagnosis test",
    )
    diagnosis = create_root_cause_diagnosis(
        signal,
        candidate_root_cause=FailureRootCauseCategory.CONTEXT_EVIDENCE,
        confidence=confidence,
        diagnostic_evidence_refs=(
            create_diagnosis_evidence_ref(
                evidence_kind=DiagnosisEvidenceKind.FAILURE_SIGNAL,
                target_id=signal.failure_signal_id,
            ),
        ),
        uncertainty_reason="single evidence source",
    )
    return bundle, signal, diagnosis


def test_diagnosis_is_deterministic_and_not_proof() -> None:
    _bundle, signal, diagnosis = _diagnosis_fixture()
    again = create_root_cause_diagnosis(
        signal,
        candidate_root_cause=FailureRootCauseCategory.CONTEXT_EVIDENCE,
        confidence=DiagnosisConfidence.MEDIUM,
        diagnostic_evidence_refs=diagnosis.diagnostic_evidence_refs,
        uncertainty_reason="single evidence source",
    )
    assert again.diagnosis_id == diagnosis.diagnosis_id
    assert diagnosis.diagnosis_is_not_proof is True
    assert diagnosis.proof_available is False
    assert diagnosis.trace_verified is False


def test_diagnosis_cannot_claim_proof() -> None:
    _bundle, _signal, diagnosis = _diagnosis_fixture()
    with pytest.raises(AurelFlowValidationError):
        type(diagnosis)(
            **{
                **{
                    field.name: getattr(diagnosis, field.name)
                    for field in diagnosis.__dataclass_fields__.values()
                },
                "proof_available": True,
            }
        )


def test_confidence_vocabulary_has_no_proof_grade_member() -> None:
    confidence_values = {confidence.value for confidence in DiagnosisConfidence}
    assert confidence_values == {"VERY_LOW", "LOW", "MEDIUM", "HIGH", "UNKNOWN"}
    assert "CERTAIN" not in confidence_values
    assert "PROVEN" not in confidence_values
    assert "VERIFIED" not in confidence_values


def test_low_confidence_forces_human_review() -> None:
    _bundle, _signal, diagnosis = _diagnosis_fixture(DiagnosisConfidence.LOW)
    assert diagnosis.requires_human_review is True
    with pytest.raises(AurelFlowValidationError):
        type(diagnosis)(
            **{
                **{
                    field.name: getattr(diagnosis, field.name)
                    for field in diagnosis.__dataclass_fields__.values()
                },
                "requires_human_review": False,
            }
        )


def test_evidence_ref_never_retrieves_evidence() -> None:
    ref = create_diagnosis_evidence_ref(
        evidence_kind=DiagnosisEvidenceKind.RUNTIME_EVENT, target_id="flevt-x"
    )
    assert ref.evidence_retrieved is False
    assert ref.retrieval_available is False
    with pytest.raises(AurelFlowValidationError):
        type(ref)(
            **{
                **{
                    field.name: getattr(ref, field.name)
                    for field in ref.__dataclass_fields__.values()
                },
                "evidence_retrieved": True,
            }
        )


def test_uncertainty_frame_is_first_class_and_requires_review() -> None:
    _bundle, _signal, diagnosis = _diagnosis_fixture()
    frame = build_diagnosis_uncertainty_frame(
        diagnosis,
        uncertainty_reason="alternative causes remain plausible",
        alternative_root_causes=(FailureRootCauseCategory.TOOL_INFRASTRUCTURE,),
    )
    assert frame.requires_human_review is True
    assert frame.proof_available is False
    assert frame.alternative_root_causes == (
        FailureRootCauseCategory.TOOL_INFRASTRUCTURE,
    )


def test_diagnosis_read_model_aggregates_and_rejects_mismatch() -> None:
    bundle, _signal, diagnosis = _diagnosis_fixture(DiagnosisConfidence.LOW)
    read_model = build_diagnosis_read_model(bundle.run.run_id, (diagnosis,))
    assert read_model.diagnosis_count == 1
    assert read_model.low_confidence_count == 1
    assert read_model.any_requires_human_review is True
    assert read_model.diagnosis_is_not_proof is True
    with pytest.raises(AurelFlowValidationError):
        build_diagnosis_read_model("other-run", (diagnosis,))


def test_semantic_silent_failure_is_failure_candidate_not_warning() -> None:
    bundle = build_flow_demo_bundle()
    signal = create_semantic_silent_failure_signal(
        bundle.run, detail="looks fine, unsupported", node_id="fetch"
    )
    assert signal.treated_as_runtime_failure_candidate is True
    assert signal.is_harmless_warning is False
    assert signal.as_runtime_failure_kind is (
        RuntimeFailureKind.SEMANTIC_SILENT_FAILURE
    )
    with pytest.raises(AurelFlowValidationError):
        type(signal)(
            **{
                **{
                    field.name: getattr(signal, field.name)
                    for field in signal.__dataclass_fields__.values()
                },
                "is_harmless_warning": True,
            }
        )


def test_unsupported_output_and_evidence_missing_are_failure_candidates() -> None:
    bundle = build_flow_demo_bundle()
    unsupported = create_unsupported_output_signal(bundle.run, detail="no support")
    missing = create_evidence_missing_signal(bundle.run, detail="no evidence")
    assert unsupported.unsupported_output_detected is True
    assert unsupported.as_runtime_failure_kind is (
        RuntimeFailureKind.UNSUPPORTED_OUTPUT
    )
    assert missing.evidence_missing is True
    assert missing.as_runtime_failure_kind is RuntimeFailureKind.EVIDENCE_MISSING
    for signal in (unsupported, missing):
        assert signal.treated_as_runtime_failure_candidate is True
        assert signal.is_harmless_warning is False
        assert signal.proof_available is False


def test_evidence_and_contradiction_requirements_do_not_execute() -> None:
    bundle = build_flow_demo_bundle()
    support = create_evidence_support_requirement(run_id=bundle.run.run_id)
    contradiction = create_contradiction_check_requirement(
        run_id=bundle.run.run_id
    )
    assert support.semantic_support_required is True
    assert support.evidence_retrieved is False
    assert support.retrieval_available is False
    assert contradiction.contradiction_check_required is True
    assert contradiction.verifier_executed is False
    assert contradiction.proof_available is False


def test_semantic_failure_read_model_counts_all_candidate_kinds() -> None:
    bundle = build_flow_demo_bundle()
    run_id = bundle.run.run_id
    read_model = build_semantic_failure_read_model(
        run_id,
        semantic_silent_failures=(
            create_semantic_silent_failure_signal(bundle.run, detail="s"),
        ),
        unsupported_outputs=(
            create_unsupported_output_signal(bundle.run, detail="u"),
        ),
        evidence_missing_signals=(
            create_evidence_missing_signal(bundle.run, detail="m"),
        ),
        evidence_support_requirements=(
            create_evidence_support_requirement(run_id=run_id),
        ),
        contradiction_check_requirements=(
            create_contradiction_check_requirement(run_id=run_id),
        ),
    )
    assert read_model.semantic_silent_failure_count == 1
    assert read_model.unsupported_output_count == 1
    assert read_model.evidence_missing_count == 1
    assert read_model.any_semantic_failure_candidate is True
    assert read_model.semantic_failures_are_failure_candidates is True
    assert read_model.verifier_executed is False
    assert read_model.truth_label is FlowTruthLabel.READ_MODEL_ONLY
