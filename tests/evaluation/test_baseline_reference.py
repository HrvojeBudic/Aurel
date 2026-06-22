"""P1.5.10 baseline reference validation tests."""
from __future__ import annotations

from agentic_runtime.evaluation.baseline_comparison import (
    BaselineReference,
    BaselineReferenceKind,
    BaselineStatus,
    validate_baseline_reference,
)


def _make_ref(**kwargs) -> BaselineReference:
    defaults = {
        "baseline_id": "baseline_test_001",
        "kind": BaselineReferenceKind.EVALUATION_RESULT,
        "status": BaselineStatus.ACTIVE,
        "source_ref": "source_001",
        "result_refs": ("result_001",),
        "evidence_refs": (),
        "binding_refs": (),
        "hygiene_refs": (),
        "adversarial_case_refs": (),
        "created_at": None,
        "updated_at": None,
        "version": None,
        "limitations": (),
        "warnings": (),
        "blockers": (),
        "summary": "test baseline reference",
    }
    defaults.update(kwargs)
    return BaselineReference(**defaults)


class TestBaselineReferenceValidation:
    def test_validate_baseline_reference_rejects_empty_id(self):
        issues = validate_baseline_reference(_make_ref(baseline_id=""))
        assert any("baseline_id must not be empty" in i for i in issues)

    def test_active_baseline_requires_refs(self):
        issues = validate_baseline_reference(
            _make_ref(source_ref=None, result_refs=(), evidence_refs=())
        )
        assert any("requires at least one reference" in i for i in issues)

    def test_unknown_kind_cannot_be_active(self):
        issues = validate_baseline_reference(
            _make_ref(kind=BaselineReferenceKind.UNKNOWN)
        )
        assert any("UNKNOWN kind" in i for i in issues)

    def test_invalid_baseline_requires_blocker(self):
        issues = validate_baseline_reference(
            _make_ref(status=BaselineStatus.INVALID, blockers=())
        )
        assert any("INVALID baseline requires" in i for i in issues)

    def test_blocked_baseline_requires_blocker(self):
        issues = validate_baseline_reference(
            _make_ref(status=BaselineStatus.BLOCKED, blockers=())
        )
        assert any("BLOCKED baseline requires" in i for i in issues)

    def test_stale_baseline_warns(self):
        issues = validate_baseline_reference(
            _make_ref(status=BaselineStatus.STALE, warnings=())
        )
        assert any("STALE baseline should include a warning" in i for i in issues)

    def test_numeric_score_claim_rejected_or_warned(self):
        issues = validate_baseline_reference(
            _make_ref(summary="improvement_score = 0.91 over baseline")
        )
        assert any("numeric score" in i for i in issues)
