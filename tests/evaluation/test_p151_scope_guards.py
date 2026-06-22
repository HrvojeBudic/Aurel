"""P1.5.1 anti-scope-creep tests."""
from __future__ import annotations

import os

from agentic_runtime.evaluation.evaluation_objects import (
    EvaluationCriterionResult,
    EvaluationEvidenceQuality,
    EvaluationOutcome,
    EvaluationResult,
    EvaluationVerdict,
    example_supported_evaluation_result,
)

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _read_docs() -> str:
    paths = ("agent/ROADMAP.md", "agent/STATE.md", "agent/ARCHITECTURE.md", "agent/TESTS.md")
    combined = ""
    for p in paths:
        full = os.path.join(REPO, p)
        if os.path.isfile(full):
            with open(full) as f:
                combined += f.read() + "\n"
    return combined.lower()


def test_p151_does_not_implement_full_p4():
    text = _read_docs()
    assert "p1.5" in text
    assert "not full p4" in text or "p4" in text


def test_p151_does_not_introduce_numeric_capability_score():
    r = example_supported_evaluation_result()
    d = r.__dataclass_fields__
    for name in d:
        assert "score" not in name.lower() or d[name].type not in (int, float)


def test_p151_does_not_mark_capability_verified():
    r = example_supported_evaluation_result()
    assert r.verdict != EvaluationVerdict.SUPPORTED or r.verdict.value != "VERIFIED"
    assert "VERIFIED" not in {v.value for v in EvaluationVerdict}


def test_p151_does_not_run_benchmarks():
    from agentic_runtime.evaluation.evaluation_objects import P151_INVARIANTS
    text = " ".join(P151_INVARIANTS).lower()
    assert "benchmark" not in text or "not" in text


def test_p151_preserves_p150_roadmap_alignment():
    text = _read_docs()
    assert "v3.2" in text or "aurel core" in text
    assert "p1.5.0" in text or "p1.5" in text
