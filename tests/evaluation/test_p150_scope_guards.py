"""P1.5.0 anti-scope-creep tests."""
from __future__ import annotations

import os

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _read_all_docs() -> str:
    paths = (
        "agent/ROADMAP.md", "agent/STATE.md", "agent/ARCHITECTURE.md",
        "agent/DECISIONS.md", "agent/TESTS.md", "agent/REPORTS.md",
        "agent/ACTIVE_TASK.md",
    )
    combined = ""
    for p in paths:
        full = os.path.join(REPO, p)
        if os.path.isfile(full):
            with open(full) as f:
                combined += f.read() + "\n"
    return combined.lower()


def test_p150_does_not_claim_full_p4_evaluation_mirror():
    text = _read_all_docs()
    # Should mention P4 distinction, not claim P4 is complete
    assert "p4" in text or "full evaluation mirror" in text or "not full p4" in text


def test_p150_does_not_start_p22_p24():
    text = _read_all_docs()
    # Should mention P22-P24 as future, not as current/active
    if "p22" in text:
        assert "not start" in text or "do not jump" in text or "added" in text or "future" in text


def test_p150_does_not_claim_hub_runtime_implemented():
    text = _read_all_docs()
    assert "hub runtime implemented" not in text
    assert "a-hub runtime" not in text or "not implemented" in text or "independent" in text


def test_p150_does_not_claim_model_of_models_implemented():
    text = _read_all_docs()
    if "model-of-models" in text or "model of models" in text:
        assert "not implemented" in text or "eventually" in text or "future" in text


def test_p150_does_not_claim_model_of_work_implemented():
    text = _read_all_docs()
    if "model-of-work" in text or "model of work" in text:
        assert "not implemented" in text or "eventually" in text or "future" in text


def test_p150_does_not_claim_lora_training_implemented():
    text = _read_all_docs()
    assert "lora training implemented" not in text


def test_p150_does_not_claim_capability_verified_by_envelope_alone():
    from agentic_runtime.evaluation.evaluation_foundation import (
        EvaluationDomain, EvaluationSubjectType,
        build_evaluation_subject, build_evaluation_run_envelope,
        default_evaluation_scope_for_domain, default_criteria_for_domain,
    )
    subj = build_evaluation_subject(
        subject_id="c1", subject_type=EvaluationSubjectType.CAPABILITY_CLAIM,
        domain=EvaluationDomain.CAPABILITY_CLAIM,
    )
    scope = default_evaluation_scope_for_domain(EvaluationDomain.CAPABILITY_CLAIM)
    env = build_evaluation_run_envelope(
        run_id="r1", subject=subj, scope=scope,
        criteria=default_criteria_for_domain(EvaluationDomain.CAPABILITY_CLAIM),
        evaluator="test",
    )
    # Envelope exists but does NOT have a verified/truth field
    assert not hasattr(env, "verified")
    assert not hasattr(env, "capability_verified")
    assert "not verify" in scope.non_goals[0].lower() or "does not verify" in " ".join(scope.non_goals).lower()
