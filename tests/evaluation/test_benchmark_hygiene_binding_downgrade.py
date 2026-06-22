"""Benchmark hygiene binding downgrade tests — P1.5.8."""
from __future__ import annotations

from dataclasses import replace

from agentic_runtime.evaluation.benchmark_hygiene import (
    BenchmarkHygieneDecision,
    BenchmarkRepresentativeness,
    apply_hygiene_to_evidence_binding,
    assess_benchmark_hygiene,
    example_clean_benchmark_fixture_boundary,
    example_leaky_benchmark_fixture_boundary,
    resolve_hygiene_decision,
)
from agentic_runtime.evaluation.capability_evidence import (
    CapabilityEvidenceKind,
    CapabilityEvidenceRecord,
    CapabilityEvidenceStatus,
    CapabilityEvidenceStrength,
)
from agentic_runtime.evaluation.evidence_claim_binding import (
    ClaimBindingRelationship,
    ClaimBindingStatus,
    ClaimConflictLevel,
    ClaimSupportLevel,
    bind_evidence_to_claim,
)


def _binding(strength: CapabilityEvidenceStrength = CapabilityEvidenceStrength.STRONG):
    evidence = CapabilityEvidenceRecord(
        evidence_id="ev_001",
        kind=CapabilityEvidenceKind.EVALUATION_RESULT,
        status=CapabilityEvidenceStatus.USABLE,
        strength=strength,
        claim_id="claim_001",
        source_result_ids=("result_001",),
        source_result_set_ids=("rset_001",),
    )
    return bind_evidence_to_claim(binding_id="b1", claim_id="claim_001", evidence=evidence)


def test_hygiene_never_increases_binding_support():
    binding = _binding(CapabilityEvidenceStrength.WEAK)
    assessment = assess_benchmark_hygiene(
        assessment_id="a1",
        boundary=example_clean_benchmark_fixture_boundary(),
        representativeness=BenchmarkRepresentativeness.REPRESENTATIVE,
    )
    decision = resolve_hygiene_decision(decision_id="d1", assessment=assessment)
    downgraded = apply_hygiene_to_evidence_binding(binding=binding, hygiene_decision=decision)
    assert downgraded.support_level == ClaimSupportLevel.WEAK


def test_hygiene_can_downgrade_strong_to_moderate():
    binding = _binding()
    assessment = assess_benchmark_hygiene(
        assessment_id="a1",
        boundary=example_clean_benchmark_fixture_boundary(),
        representativeness=BenchmarkRepresentativeness.NARROW,
    )
    decision = resolve_hygiene_decision(decision_id="d1", assessment=assessment)
    downgraded = apply_hygiene_to_evidence_binding(binding=binding, hygiene_decision=decision)
    assert downgraded.support_level == ClaimSupportLevel.MODERATE
    assert downgraded.relationship == ClaimBindingRelationship.SUPPORTS


def test_hygiene_can_downgrade_support_to_insufficient():
    binding = _binding()
    assessment = assess_benchmark_hygiene(
        assessment_id="a1",
        boundary=example_clean_benchmark_fixture_boundary(),
        representativeness=BenchmarkRepresentativeness.REPRESENTATIVE,
    )
    decision = BenchmarkHygieneDecision(
        decision_id="d_manual",
        assessment=assessment,
        evidence_usable_for_claim_support=True,
        max_allowed_support_level=ClaimSupportLevel.NONE,
        recommended_binding_relationship=ClaimBindingRelationship.INSUFFICIENT,
        recommended_binding_status=ClaimBindingStatus.INSUFFICIENT,
        warnings=("manual insufficient cap",),
        blockers=(),
        summary="manual insufficient hygiene decision",
    )
    downgraded = apply_hygiene_to_evidence_binding(binding=binding, hygiene_decision=decision)
    assert downgraded.relationship == ClaimBindingRelationship.INSUFFICIENT
    assert downgraded.support_level == ClaimSupportLevel.NONE


def test_hygiene_can_block_contaminated_binding():
    binding = _binding()
    assessment = assess_benchmark_hygiene(
        assessment_id="a1",
        boundary=example_leaky_benchmark_fixture_boundary(),
        representativeness=BenchmarkRepresentativeness.REPRESENTATIVE,
    )
    decision = resolve_hygiene_decision(decision_id="d1", assessment=assessment)
    downgraded = apply_hygiene_to_evidence_binding(binding=binding, hygiene_decision=decision)
    assert downgraded.relationship == ClaimBindingRelationship.BLOCKS
    assert downgraded.status == ClaimBindingStatus.BLOCKED
    assert downgraded.support_level == ClaimSupportLevel.NONE
    assert downgraded.conflict_level in (ClaimConflictLevel.HIGH, ClaimConflictLevel.CRITICAL)


def test_hygiene_preserves_claim_and_evidence_ids():
    binding = _binding()
    decision = resolve_hygiene_decision(
        decision_id="d1",
        assessment=assess_benchmark_hygiene(
            assessment_id="a1",
            boundary=replace(example_clean_benchmark_fixture_boundary(), updated_at="stale"),
            representativeness=BenchmarkRepresentativeness.REPRESENTATIVE,
        ),
    )
    downgraded = apply_hygiene_to_evidence_binding(binding=binding, hygiene_decision=decision)
    assert downgraded.claim_id == binding.claim_id
    assert downgraded.evidence_id == binding.evidence_id


def test_hygiene_preserves_source_result_refs():
    binding = _binding()
    decision = resolve_hygiene_decision(
        decision_id="d1",
        assessment=assess_benchmark_hygiene(
            assessment_id="a1",
            boundary=example_clean_benchmark_fixture_boundary(),
            representativeness=BenchmarkRepresentativeness.REPRESENTATIVE,
        ),
    )
    downgraded = apply_hygiene_to_evidence_binding(binding=binding, hygiene_decision=decision)
    assert downgraded.source_result_ids == binding.source_result_ids
    assert downgraded.source_result_set_ids == binding.source_result_set_ids


def test_hygiene_does_not_verify_claim():
    binding = _binding()
    decision = resolve_hygiene_decision(
        decision_id="d1",
        assessment=assess_benchmark_hygiene(
            assessment_id="a1",
            boundary=example_clean_benchmark_fixture_boundary(),
            representativeness=BenchmarkRepresentativeness.REPRESENTATIVE,
        ),
    )
    downgraded = apply_hygiene_to_evidence_binding(binding=binding, hygiene_decision=decision)
    assert "VERIFIED" not in downgraded.status.value
    assert "VERIFIED" not in downgraded.summary.upper()


def test_hygiene_does_not_mutate_original_binding():
    binding = _binding()
    decision = resolve_hygiene_decision(
        decision_id="d1",
        assessment=assess_benchmark_hygiene(
            assessment_id="a1",
            boundary=example_leaky_benchmark_fixture_boundary(),
            representativeness=BenchmarkRepresentativeness.REPRESENTATIVE,
        ),
    )
    downgraded = apply_hygiene_to_evidence_binding(binding=binding, hygiene_decision=decision)
    assert downgraded is not binding
    assert binding.relationship == ClaimBindingRelationship.SUPPORTS
    assert binding.support_level == ClaimSupportLevel.STRONG
