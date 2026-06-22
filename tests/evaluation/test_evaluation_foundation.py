"""P1.5.0 core evaluation foundation tests."""
from __future__ import annotations

import json
import pytest

from agentic_runtime.evaluation.evaluation_foundation import (
    EvaluationDomain,
    EvaluationSubjectType,
    EvaluationCriterion,
    build_evaluation_subject,
    build_evaluation_run_envelope,
    build_p150_foundation_report,
    default_evaluation_scope_for_domain,
    default_criteria_for_domain,
    evaluation_run_envelope_to_dict,
    evaluation_foundation_report_to_dict,
    validate_evaluation_run_envelope,
)


def test_evaluation_domain_closed_world():
    assert EvaluationDomain.AUREL_CORE.value == "AUREL_CORE"
    assert EvaluationDomain.UNKNOWN.value == "UNKNOWN"
    assert len(EvaluationDomain) >= 10


def test_evaluation_subject_type_closed_world():
    assert EvaluationSubjectType.CAPABILITY_CLAIM.value == "CAPABILITY_CLAIM"
    assert EvaluationSubjectType.HUB_OUTPUT.value == "HUB_OUTPUT"
    assert len(EvaluationSubjectType) >= 10


def test_build_evaluation_subject():
    subj = build_evaluation_subject(
        subject_id="subj_1",
        subject_type=EvaluationSubjectType.CAPABILITY_CLAIM,
        domain=EvaluationDomain.CAPABILITY_CLAIM,
        title="Test claim",
        evidence_refs=("ev_1",),
    )
    assert subj.subject_id == "subj_1"
    assert subj.evidence_refs == ("ev_1",)


def test_build_evaluation_subject_rejects_empty_id():
    with pytest.raises(ValueError, match="subject_id"):
        build_evaluation_subject(
            subject_id="",
            subject_type=EvaluationSubjectType.UNKNOWN,
            domain=EvaluationDomain.UNKNOWN,
        )


def test_default_scope_for_aurel_core():
    scope = default_evaluation_scope_for_domain(EvaluationDomain.AUREL_CORE)
    assert scope.domain == EvaluationDomain.AUREL_CORE
    assert EvaluationSubjectType.AGENT_IDENTITY in scope.subject_types
    assert len(scope.non_goals) > 0


def test_default_scope_unknown_conservative():
    scope = default_evaluation_scope_for_domain(EvaluationDomain.UNKNOWN)
    assert scope.domain == EvaluationDomain.UNKNOWN
    assert "Does not verify capability" in scope.non_goals[0]


def test_build_evaluation_run_envelope():
    subj = build_evaluation_subject(
        subject_id="s1", subject_type=EvaluationSubjectType.AGENT_IDENTITY,
        domain=EvaluationDomain.AUREL_CORE,
    )
    scope = default_evaluation_scope_for_domain(EvaluationDomain.AUREL_CORE)
    criteria = default_criteria_for_domain(EvaluationDomain.AUREL_CORE)
    env = build_evaluation_run_envelope(
        run_id="run_1", subject=subj, scope=scope, criteria=criteria, evaluator="test",
    )
    assert env.run_id == "run_1"
    assert env.evaluator == "test"
    assert len(env.criteria) > 0


def test_build_envelope_rejects_empty_run_id():
    subj = build_evaluation_subject(
        subject_id="s1", subject_type=EvaluationSubjectType.AGENT_IDENTITY,
        domain=EvaluationDomain.AUREL_CORE,
    )
    scope = default_evaluation_scope_for_domain(EvaluationDomain.AUREL_CORE)
    crit = (EvaluationCriterion("c1", "n", "d"),)
    with pytest.raises(ValueError, match="run_id"):
        build_evaluation_run_envelope(
            run_id="", subject=subj, scope=scope, criteria=crit, evaluator="test",
        )


def test_validate_requires_criteria():
    subj = build_evaluation_subject(
        subject_id="s1", subject_type=EvaluationSubjectType.AGENT_IDENTITY,
        domain=EvaluationDomain.AUREL_CORE,
    )
    scope = default_evaluation_scope_for_domain(EvaluationDomain.AUREL_CORE)
    env = build_evaluation_run_envelope(
        run_id="r1", subject=subj, scope=scope,
        criteria=(EvaluationCriterion("c1", "n", "d"),), evaluator="e",
    )
    assert validate_evaluation_run_envelope(env) == ()


def test_validate_rejects_empty_evaluator():
    from agentic_runtime.evaluation.evaluation_foundation import EvaluationRunEnvelope
    subj = build_evaluation_subject(
        subject_id="s1", subject_type=EvaluationSubjectType.AGENT_IDENTITY,
        domain=EvaluationDomain.AUREL_CORE,
    )
    scope = default_evaluation_scope_for_domain(EvaluationDomain.AUREL_CORE)
    env = EvaluationRunEnvelope(
        run_id="r1", subject=subj, scope=scope,
        criteria=(EvaluationCriterion("c1", "n", "d"),),
        evaluator="", created_at="2026-01-01T00:00:00+00:00",
    )
    blockers = validate_evaluation_run_envelope(env)
    assert any("evaluator" in b for b in blockers)


def test_validate_rejects_subject_type_outside_scope():
    subj = build_evaluation_subject(
        subject_id="s1", subject_type=EvaluationSubjectType.HUB_OUTPUT,
        domain=EvaluationDomain.HUB_HANDOFF,
    )
    scope = default_evaluation_scope_for_domain(EvaluationDomain.AUREL_CORE)
    env = build_evaluation_run_envelope(
        run_id="r1", subject=subj, scope=scope,
        criteria=(EvaluationCriterion("c1", "n", "d"),), evaluator="e",
    )
    blockers = validate_evaluation_run_envelope(env)
    assert any("subject type" in b for b in blockers)


def test_validate_rejects_domain_mismatch():
    subj = build_evaluation_subject(
        subject_id="s1", subject_type=EvaluationSubjectType.CAPABILITY_CLAIM,
        domain=EvaluationDomain.CAPABILITY_CLAIM,
    )
    scope = default_evaluation_scope_for_domain(EvaluationDomain.AUREL_CORE)
    env = build_evaluation_run_envelope(
        run_id="r1", subject=subj, scope=scope,
        criteria=(EvaluationCriterion("c1", "n", "d"),), evaluator="e",
    )
    blockers = validate_evaluation_run_envelope(env)
    assert any("domain" in b for b in blockers)


def test_evaluation_run_envelope_json_serializable():
    subj = build_evaluation_subject(
        subject_id="s1", subject_type=EvaluationSubjectType.AGENT_IDENTITY,
        domain=EvaluationDomain.AUREL_CORE,
    )
    scope = default_evaluation_scope_for_domain(EvaluationDomain.AUREL_CORE)
    env = build_evaluation_run_envelope(
        run_id="r1", subject=subj, scope=scope,
        criteria=default_criteria_for_domain(EvaluationDomain.AUREL_CORE),
        evaluator="e",
    )
    d = evaluation_run_envelope_to_dict(env)
    assert json.loads(json.dumps(d))["run_id"] == "r1"


def test_p150_foundation_report_json_serializable():
    report = build_p150_foundation_report(docs_updated=("a",), docs_missing=())
    d = evaluation_foundation_report_to_dict(report)
    p = json.loads(json.dumps(d))
    assert p["status"] == "READY"
    assert "P1.5.1" in p["next_module"]


def test_p150_foundation_report_blocked():
    report = build_p150_foundation_report(
        docs_updated=(), docs_missing=(), blockers=("blocker",),
    )
    assert report.status == "BLOCKED"


def test_p150_foundation_report_degraded():
    report = build_p150_foundation_report(
        docs_updated=(), docs_missing=(), warnings=("warn",),
    )
    assert report.status == "DEGRADED"
