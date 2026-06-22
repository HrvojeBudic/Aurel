"""P1.5.5 run envelope serialization tests."""
from __future__ import annotations

import json

import pytest

from agentic_runtime.evaluation.evaluation_run_envelope import (
    EvaluationEvaluatorType,
    EvaluationRunEnvelopeReport,
    EvaluationRunEnvelopeValidation,
    EvaluationRunEvidenceRequirement,
    EvaluationRunIntent,
    EvaluationRunMode,
    EvaluationRunStatus,
    GovernedEvaluationRunEnvelope,
    build_p155_run_envelope_report,
    example_ready_run_envelope,
    example_sparse_ready_run_envelope,
    governed_evaluation_run_envelope_to_dict,
    resolve_run_readiness,
    run_envelope_report_to_dict,
    run_envelope_validation_to_dict,
    run_evidence_requirement_to_dict,
)
from agentic_runtime.evaluation.evaluation_criteria_schema import EvaluationCriterionEvidenceRequirement


class TestSerialization:
    def test_run_evidence_requirement_json_serializable(self):
        req = EvaluationRunEvidenceRequirement(
            requirement_id="req_001",
            evidence_requirement=EvaluationCriterionEvidenceRequirement.EVIDENCE_REF,
            required=True,
            satisfied=True,
            evidence_refs=("ref_a", "ref_b"),
        )
        d = run_evidence_requirement_to_dict(req)
        s = json.dumps(d)
        assert "req_001" in s
        assert "EVIDENCE_REF" in s

    def test_governed_run_envelope_json_serializable(self):
        envelope = example_ready_run_envelope()
        d = governed_evaluation_run_envelope_to_dict(envelope)
        s = json.dumps(d)
        assert "run_example_ready" in s
        assert "READY" in s

    def test_run_envelope_validation_json_serializable(self):
        validation = EvaluationRunEnvelopeValidation(
            valid=True,
            status=EvaluationRunStatus.READY,
            blockers=(),
            warnings=(),
            summary="Valid",
        )
        d = run_envelope_validation_to_dict(validation)
        s = json.dumps(d)
        assert "true" in s.lower()

    def test_run_envelope_report_json_serializable(self):
        report = build_p155_run_envelope_report(envelopes_created=5, envelopes_ready=3, envelopes_blocked=2)
        d = run_envelope_report_to_dict(report)
        s = json.dumps(d)
        assert "p155_" in s
        assert "P1.5.6" in s
        assert d["sparse_run_readiness"] == "ENVELOPE_METADATA_ONLY"

    def test_resolve_run_readiness_ready(self):
        assert resolve_run_readiness(blockers=(), warnings=()) == EvaluationRunStatus.READY

    def test_resolve_run_readiness_blocked(self):
        assert resolve_run_readiness(blockers=("test blocker",), warnings=()) == EvaluationRunStatus.BLOCKED

    def test_sparse_envelope_json_serializable(self):
        envelope = example_sparse_ready_run_envelope()
        d = governed_evaluation_run_envelope_to_dict(envelope)
        s = json.dumps(d)
        assert "run_example_sparse" in s
        assert d["sparse_context_required"] is True
