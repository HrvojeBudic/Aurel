"""P1.5.19 P1.5 Integrated Seal contracts.

Seal reports prove the entire P1.5 subsystem is coherent, trace-bound,
evidence-bound, limitation-bound, candidate-safe, and non-promotional.

These reports are PROJECTIONS — not canonical truth.
AurelTraceLog remains the only canonical truth source.
"""
from __future__ import annotations

from dataclasses import dataclass


# ---------------------------------------------------------------------------
# P15IntegratedSealReport
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class P15IntegratedSealReport:
    """Top-level report declaring whether P1.5 is sealed.

    This is a projection/report over canonical trace and artifacts.
    It is NOT canonical truth itself.
    """

    seal_id: str
    golden_thread_status: str  # passed / failed
    trace_integrity_status: str
    evaluation_integrity_status: str
    capability_claim_status: str
    feedback_safety_status: str
    memory_candidate_safety_status: str
    cold_cache_verification_status: str
    passed: bool
    warnings: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()
    created_at: str = ""

    def __post_init__(self) -> None:
        if not self.seal_id or not self.seal_id.strip():
            raise ValueError("seal_id must not be empty")
        if not self.golden_thread_status or not self.golden_thread_status.strip():
            raise ValueError("golden_thread_status must not be empty")
        if not self.trace_integrity_status or not self.trace_integrity_status.strip():
            raise ValueError("trace_integrity_status must not be empty")
        if not self.evaluation_integrity_status or not self.evaluation_integrity_status.strip():
            raise ValueError("evaluation_integrity_status must not be empty")
        if not self.capability_claim_status or not self.capability_claim_status.strip():
            raise ValueError("capability_claim_status must not be empty")
        if not self.feedback_safety_status or not self.feedback_safety_status.strip():
            raise ValueError("feedback_safety_status must not be empty")
        if not self.memory_candidate_safety_status or not self.memory_candidate_safety_status.strip():
            raise ValueError("memory_candidate_safety_status must not be empty")
        if not self.cold_cache_verification_status or not self.cold_cache_verification_status.strip():
            raise ValueError("cold_cache_verification_status must not be empty")
        if not self.created_at or not self.created_at.strip():
            raise ValueError("created_at must not be empty")

        # Passed must be false if any subsystem failed
        if self.passed:
            failed_statuses = []
            for field_name in (
                "golden_thread_status",
                "trace_integrity_status",
                "evaluation_integrity_status",
                "capability_claim_status",
                "feedback_safety_status",
                "memory_candidate_safety_status",
                "cold_cache_verification_status",
            ):
                if getattr(self, field_name) != "passed":
                    failed_statuses.append(field_name)
            if failed_statuses:
                raise ValueError(
                    f"passed must be False when these subsystems failed: "
                    f"{', '.join(failed_statuses)}"
                )


def p15_integrated_seal_report_to_dict(
    report: P15IntegratedSealReport,
) -> dict[str, object]:
    return {
        "seal_id": report.seal_id,
        "golden_thread_status": report.golden_thread_status,
        "trace_integrity_status": report.trace_integrity_status,
        "evaluation_integrity_status": report.evaluation_integrity_status,
        "capability_claim_status": report.capability_claim_status,
        "feedback_safety_status": report.feedback_safety_status,
        "memory_candidate_safety_status": report.memory_candidate_safety_status,
        "cold_cache_verification_status": report.cold_cache_verification_status,
        "passed": report.passed,
        "warnings": list(report.warnings),
        "errors": list(report.errors),
        "created_at": report.created_at,
    }


# ---------------------------------------------------------------------------
# GoldenThreadASealReport
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class GoldenThreadASealReport:
    """Proves the full Golden Thread A path exists and is internally linked.

    Every ref list must be non-empty — the seal requires all 10 artifact
    categories to be present in the chain.
    """

    report_id: str
    run_id: str
    trace_event_refs: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    verifier_result_refs: tuple[str, ...]
    capability_evidence_refs: tuple[str, ...]
    evaluation_case_refs: tuple[str, ...]
    evaluation_run_result_refs: tuple[str, ...]
    brain_context_refs: tuple[str, ...]
    capability_claim_refs: tuple[str, ...]
    feedback_refs: tuple[str, ...]
    memory_candidate_refs: tuple[str, ...]
    passed: bool
    warnings: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()
    created_at: str = ""

    def __post_init__(self) -> None:
        if not self.report_id or not self.report_id.strip():
            raise ValueError("report_id must not be empty")
        if not self.run_id or not self.run_id.strip():
            raise ValueError("run_id must not be empty")
        if not self.created_at or not self.created_at.strip():
            raise ValueError("created_at must not be empty")

        # All artifact ref lists must be non-empty for the seal
        required_non_empty = {
            "trace_event_refs": self.trace_event_refs,
            "evidence_refs": self.evidence_refs,
            "verifier_result_refs": self.verifier_result_refs,
            "capability_evidence_refs": self.capability_evidence_refs,
            "evaluation_case_refs": self.evaluation_case_refs,
            "evaluation_run_result_refs": self.evaluation_run_result_refs,
            "capability_claim_refs": self.capability_claim_refs,
            "feedback_refs": self.feedback_refs,
            "memory_candidate_refs": self.memory_candidate_refs,
        }
        for name, refs in required_non_empty.items():
            if not refs:
                raise ValueError(f"{name} must be non-empty for seal")

        if self.passed and self.errors:
            raise ValueError("passed cannot be True with non-empty errors")


def golden_thread_seal_report_to_dict(
    report: GoldenThreadASealReport,
) -> dict[str, object]:
    return {
        "report_id": report.report_id,
        "run_id": report.run_id,
        "trace_event_refs": list(report.trace_event_refs),
        "evidence_refs": list(report.evidence_refs),
        "verifier_result_refs": list(report.verifier_result_refs),
        "capability_evidence_refs": list(report.capability_evidence_refs),
        "evaluation_case_refs": list(report.evaluation_case_refs),
        "evaluation_run_result_refs": list(report.evaluation_run_result_refs),
        "brain_context_refs": list(report.brain_context_refs),
        "capability_claim_refs": list(report.capability_claim_refs),
        "feedback_refs": list(report.feedback_refs),
        "memory_candidate_refs": list(report.memory_candidate_refs),
        "passed": report.passed,
        "warnings": list(report.warnings),
        "errors": list(report.errors),
        "created_at": report.created_at,
    }


# ---------------------------------------------------------------------------
# ContractInvariantChecklist
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class InvariantResult:
    """Single invariant check result."""

    invariant_id: str
    description: str
    passed: bool
    reason: str = ""

    def __post_init__(self) -> None:
        if not self.invariant_id or not self.invariant_id.strip():
            raise ValueError("invariant_id must not be empty")
        if not self.description or not self.description.strip():
            raise ValueError("description must not be empty")


@dataclass(frozen=True)
class ContractInvariantChecklist:
    """Checklist that verifies all P1.5 hard invariants.

    If any invariant fails, passed = False.
    """

    checklist_id: str
    invariant_results: tuple[InvariantResult, ...]
    passed: bool
    created_at: str = ""

    def __post_init__(self) -> None:
        if not self.checklist_id or not self.checklist_id.strip():
            raise ValueError("checklist_id must not be empty")
        if not self.invariant_results:
            raise ValueError("invariant_results must be non-empty")
        if not self.created_at or not self.created_at.strip():
            raise ValueError("created_at must not be empty")

        # Auto-compute passed from invariant results
        expected_passed = all(r.passed for r in self.invariant_results)
        if self.passed != expected_passed:
            raise ValueError(
                f"passed={self.passed} but all invariants passed={expected_passed}"
            )

    @property
    def failed_invariants(self) -> tuple[str, ...]:
        return tuple(
            r.invariant_id for r in self.invariant_results if not r.passed
        )


def invariant_result_to_dict(result: InvariantResult) -> dict[str, object]:
    return {
        "invariant_id": result.invariant_id,
        "description": result.description,
        "passed": result.passed,
        "reason": result.reason,
    }


def contract_invariant_checklist_to_dict(
    checklist: ContractInvariantChecklist,
) -> dict[str, object]:
    return {
        "checklist_id": checklist.checklist_id,
        "invariant_results": [
            invariant_result_to_dict(r) for r in checklist.invariant_results
        ],
        "failed_invariants": list(checklist.failed_invariants),
        "passed": checklist.passed,
        "created_at": checklist.created_at,
    }


# ---------------------------------------------------------------------------
# ColdCacheVerificationReport
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ColdCacheVerificationReport:
    """Records whether seal evidence came from a cold-cache verification run.

    Cached pytest runs are NOT seal evidence.
    Cold-cache verification is required for the P1.5 seal.
    """

    report_id: str
    cache_cleared: bool
    command_used: str
    pytest_status: str  # passed / failed
    passed: bool
    cli_verify_status: str | None = None
    ruff_status: str | None = None
    mypy_status: str | None = None
    failures: tuple[str, ...] = ()
    unavailable_tools: tuple[str, ...] = ()
    created_at: str = ""

    def __post_init__(self) -> None:
        if not self.report_id or not self.report_id.strip():
            raise ValueError("report_id must not be empty")
        if not self.command_used or not self.command_used.strip():
            raise ValueError("command_used must not be empty")
        if not self.pytest_status or not self.pytest_status.strip():
            raise ValueError("pytest_status must not be empty")
        if not self.created_at or not self.created_at.strip():
            raise ValueError("created_at must not be empty")

        # Cache not cleared → cannot pass
        if self.passed and not self.cache_cleared:
            raise ValueError(
                "passed cannot be True when cache_cleared is False"
            )

        # Pytest failed → cannot pass
        if self.passed and self.pytest_status != "passed":
            raise ValueError(
                f"passed cannot be True when pytest_status is '{self.pytest_status}'"
            )

        # CLI verify failed → cannot pass
        if (
            self.passed
            and self.cli_verify_status is not None
            and self.cli_verify_status != "passed"
        ):
            raise ValueError(
                f"passed cannot be True when cli_verify_status is "
                f"'{self.cli_verify_status}'"
            )


def cold_cache_verification_report_to_dict(
    report: ColdCacheVerificationReport,
) -> dict[str, object]:
    return {
        "report_id": report.report_id,
        "cache_cleared": report.cache_cleared,
        "command_used": report.command_used,
        "pytest_status": report.pytest_status,
        "passed": report.passed,
        "cli_verify_status": report.cli_verify_status,
        "ruff_status": report.ruff_status,
        "mypy_status": report.mypy_status,
        "failures": list(report.failures),
        "unavailable_tools": list(report.unavailable_tools),
        "created_at": report.created_at,
    }
