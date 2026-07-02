"""P3-FLOW-G failure taxonomy tests.

The failure taxonomy is closed-world, classification is deterministic, and
neither a failure signal nor a classification is proof or recovery execution.
"""

from __future__ import annotations

import pytest

from agentic_runtime.aurel_flow import (
    AurelFlowValidationError,
    FailureRootCauseCategory,
    FailureSeverity,
    FlowTruthLabel,
    RuntimeFailureKind,
    build_failure_classification_read_model,
    build_flow_demo_bundle,
    classify_runtime_failure,
    create_runtime_failure_signal,
    failure_classification_table,
)

EXPECTED_FAILURE_KINDS = {
    "TOOL_TIMEOUT",
    "TOOL_RATE_LIMITED",
    "TOOL_UNAVAILABLE",
    "SCHEMA_MISMATCH",
    "MALFORMED_JSON",
    "MISSING_FIELD",
    "TYPE_ERROR",
    "CONTEXT_DECAY",
    "STALE_RETRIEVAL",
    "CONTRADICTORY_EVIDENCE",
    "CONTROL_LOOP_COLLAPSE",
    "RETRY_STORM",
    "NO_PROGRESS",
    "SEMANTIC_SILENT_FAILURE",
    "UNSUPPORTED_OUTPUT",
    "EVIDENCE_MISSING",
    "TOPOLOGY_AMPLIFICATION_RISK",
    "DIVERSITY_CORRELATION_RISK",
    "CHECKPOINT_REQUIRED_MISSING",
    "UNKNOWN",
    "UNAVAILABLE",
    "ERROR",
}


def _signal(kind: RuntimeFailureKind = RuntimeFailureKind.TOOL_TIMEOUT):
    bundle = build_flow_demo_bundle()
    return bundle, create_runtime_failure_signal(
        bundle.run, failure_kind=kind, detail="taxonomy test", node_id="fetch"
    )


def test_failure_kind_vocabulary_is_exactly_the_closed_world_set() -> None:
    assert {kind.value for kind in RuntimeFailureKind} == EXPECTED_FAILURE_KINDS


def test_severity_vocabulary_is_closed_world() -> None:
    assert {severity.value for severity in FailureSeverity} == {
        "LOW",
        "MEDIUM",
        "HIGH",
        "CRITICAL",
        "UNKNOWN",
    }


def test_semantic_and_loop_failures_are_first_class_kinds() -> None:
    assert RuntimeFailureKind.SEMANTIC_SILENT_FAILURE in RuntimeFailureKind
    assert RuntimeFailureKind.UNSUPPORTED_OUTPUT in RuntimeFailureKind
    assert RuntimeFailureKind.EVIDENCE_MISSING in RuntimeFailureKind
    assert RuntimeFailureKind.RETRY_STORM in RuntimeFailureKind
    assert RuntimeFailureKind.NO_PROGRESS in RuntimeFailureKind


def test_failure_signal_is_deterministic_and_step_anchored() -> None:
    bundle, signal = _signal()
    again = create_runtime_failure_signal(
        bundle.run,
        failure_kind=RuntimeFailureKind.TOOL_TIMEOUT,
        detail="taxonomy test",
        node_id="fetch",
    )
    assert again.failure_signal_id == signal.failure_signal_id
    assert signal.failure_signal_id.startswith("flfsg-")
    assert signal.detected_at_logical_sequence == bundle.run.state.step


def test_failure_signal_cannot_claim_proof_or_recovery() -> None:
    _bundle, signal = _signal()
    assert signal.proof_available is False
    assert signal.trace_verified is False
    assert signal.recovery_executed is False
    with pytest.raises(AurelFlowValidationError):
        type(signal)(
            **{
                **{
                    field.name: getattr(signal, field.name)
                    for field in signal.__dataclass_fields__.values()
                },
                "proof_available": True,
            }
        )


def test_classification_table_is_total_over_the_taxonomy() -> None:
    table = failure_classification_table()
    assert set(table) == set(RuntimeFailureKind)


def test_classification_is_deterministic() -> None:
    _bundle, signal = _signal()
    first = classify_runtime_failure(signal)
    second = classify_runtime_failure(signal)
    assert first.classification_id == second.classification_id
    assert first.classification_is_not_proof is True
    assert first.proof_available is False


def test_control_loop_collapse_classifies_critical_control_loop() -> None:
    _bundle, signal = _signal(RuntimeFailureKind.CONTROL_LOOP_COLLAPSE)
    frame = classify_runtime_failure(signal)
    assert frame.severity is FailureSeverity.CRITICAL
    assert frame.root_cause_category is FailureRootCauseCategory.CONTROL_LOOP


def test_semantic_silent_failure_classifies_semantic_output_high() -> None:
    _bundle, signal = _signal(RuntimeFailureKind.SEMANTIC_SILENT_FAILURE)
    frame = classify_runtime_failure(signal)
    assert frame.severity is FailureSeverity.HIGH
    assert frame.root_cause_category is FailureRootCauseCategory.SEMANTIC_OUTPUT


def test_classification_read_model_counts_and_rejects_mismatch() -> None:
    bundle, signal = _signal()
    frame = classify_runtime_failure(signal)
    read_model = build_failure_classification_read_model(
        bundle.run.run_id, (frame,)
    )
    assert read_model.classification_count == 1
    assert read_model.severity_counts == {"MEDIUM": 1}
    assert read_model.critical_present is False
    assert read_model.truth_label is FlowTruthLabel.READ_MODEL_ONLY
    with pytest.raises(AurelFlowValidationError):
        build_failure_classification_read_model("other-run", (frame,))


def test_taxonomy_construction_does_not_mutate_demo_run() -> None:
    bundle, signal = _signal()
    step_before = bundle.run.state.step
    history_before = len(bundle.run.history)
    classify_runtime_failure(signal)
    build_failure_classification_read_model(
        bundle.run.run_id, (classify_runtime_failure(signal),)
    )
    assert bundle.run.state.step == step_before
    assert len(bundle.run.history) == history_before
