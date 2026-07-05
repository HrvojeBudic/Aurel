"""P5-TRACE-B read-only submit trace coverage audit and report.

This module answers one question with evidence: **what does the existing
``AgenticRuntime.submit()`` already record in the trace ledger, and what would
P5-TRACE-C need to bridge?** It is a *read-only audit*. It does not modify
``runtime.submit()``, add trace-append hooks, or create any trace — building the
audit constructs plain dataclasses from a deterministic evidence map.

Doctrine anchors enforced structurally here:

* The audit is not runtime integration and is not the submit bridge — locked
  booleans make ``modifies_submit`` / ``adds_trace_append`` / ``is_bridge``
  unconstructible.
* Missing evidence is **not** failure by itself — it is P5-TRACE-C handoff
  material, surfaced as explicit gaps and recommendations.
* The report never claims complete coverage while any required evidence is
  missing or partial.

The default evidence map is grounded in a read-only inspection of the submit
path: ``submit()`` appends a hash-chained ``StateTransitionRecord`` (carrying
``before_state_hash`` / ``after_state_hash`` / ``observation_hash`` /
``command_hash`` / ``policy_verdict`` / ``verifier_result``) plus discrete
``ApprovalReceiptRecord`` / ``BudgetDecisionRecord`` / ``SandboxViolationRecord``
/ ``ToolContractViolationRecord`` / ``PlanningFailureRecord`` records on their
respective paths. Evidence that exists only as a *field inside the transition*
(not a discrete, independently referenceable record) is reported ``PARTIAL``;
evidence with no discrete record is reported ``MISSING``.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from .trace_hash import (
    AurelTraceError,
    TraceTruthLabel,
    canonical_trace_json,
    require_nonempty,
    trace_sha,
)
from .trace_inventory import ExistingTraceInventory, build_existing_trace_inventory

SUBMIT_TRACE_COVERAGE_AUDIT_ID = "submit-trace-coverage-audit.p5-trace-b.v1"
SUBMIT_TRACE_COVERAGE_REPORT_ID = "submit-trace-coverage-report.p5-trace-b.v1"


class SubmitEvidenceRequirementKind(str, Enum):
    COMMAND_ENVELOPE_RECORDED = "COMMAND_ENVELOPE_RECORDED"
    POLICY_DECISION_RECORDED = "POLICY_DECISION_RECORDED"
    HITL_DECISION_RECORDED = "HITL_DECISION_RECORDED"
    BUDGET_DECISION_RECORDED = "BUDGET_DECISION_RECORDED"
    SANDBOX_BEFORE_HASH_RECORDED = "SANDBOX_BEFORE_HASH_RECORDED"
    TOOL_INVOCATION_RECORDED = "TOOL_INVOCATION_RECORDED"
    TOOL_RESULT_RECORDED = "TOOL_RESULT_RECORDED"
    VERIFIER_RESULT_RECORDED = "VERIFIER_RESULT_RECORDED"
    SANDBOX_AFTER_HASH_RECORDED = "SANDBOX_AFTER_HASH_RECORDED"
    ROLLBACK_RESULT_RECORDED = "ROLLBACK_RESULT_RECORDED"
    MEMORY_WRITE_RECORDED = "MEMORY_WRITE_RECORDED"
    TRACE_APPEND_RECORDED = "TRACE_APPEND_RECORDED"
    OBSERVATION_RECORDED = "OBSERVATION_RECORDED"
    ERROR_RECORDED = "ERROR_RECORDED"


class SubmitCoverageStatus(str, Enum):
    COVERED = "COVERED"
    PARTIAL = "PARTIAL"
    MISSING = "MISSING"
    UNSUPPORTED = "UNSUPPORTED"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class SubmitEvidenceRequirement:
    """One evidence item governed submit should ideally trace."""

    requirement_id: str
    requirement_kind: SubmitEvidenceRequirementKind
    required_for_trace_integrity_verified: bool
    required_for_future_trace_verified: bool
    current_status: SubmitCoverageStatus
    owner_pack: str
    evidence: str = ""
    truth_label: TraceTruthLabel = TraceTruthLabel.LIVE

    def __post_init__(self) -> None:
        require_nonempty(self, "requirement_id", "owner_pack")
        if self.truth_label is TraceTruthLabel.TRACE_INTEGRITY_VERIFIED:
            raise AurelTraceError(
                "a submit evidence requirement is a LIVE contract, not a verified chain"
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "requirement_id": self.requirement_id,
            "requirement_kind": self.requirement_kind.value,
            "required_for_trace_integrity_verified": (
                self.required_for_trace_integrity_verified
            ),
            "required_for_future_trace_verified": (
                self.required_for_future_trace_verified
            ),
            "current_status": self.current_status.value,
            "owner_pack": self.owner_pack,
            "evidence": self.evidence,
            "truth_label": self.truth_label.value,
        }


@dataclass(frozen=True)
class SubmitTraceGap:
    """A partial/missing/unsupported requirement plus a P5-C recommendation."""

    gap_id: str
    requirement: SubmitEvidenceRequirement
    reason: str
    p5c_recommendation: str
    truth_label: TraceTruthLabel = TraceTruthLabel.LIVE

    def __post_init__(self) -> None:
        require_nonempty(self, "gap_id", "reason", "p5c_recommendation")

    def to_dict(self) -> dict[str, Any]:
        return {
            "gap_id": self.gap_id,
            "requirement": self.requirement.to_dict(),
            "reason": self.reason,
            "p5c_recommendation": self.p5c_recommendation,
            "truth_label": self.truth_label.value,
        }


@dataclass(frozen=True)
class SubmitEvidenceCoverageSummary:
    """Counts of requirements per coverage status."""

    covered: int
    partial: int
    missing: int
    unsupported: int
    unknown: int
    total: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "covered": self.covered,
            "partial": self.partial,
            "missing": self.missing,
            "unsupported": self.unsupported,
            "unknown": self.unknown,
            "total": self.total,
        }


@dataclass(frozen=True)
class SubmitTraceCoverageAudit:
    """Read-only audit over existing ``AgenticRuntime.submit`` trace behavior."""

    audit_id: str
    runtime_submit_path_inspected: bool
    requirements: tuple[SubmitEvidenceRequirement, ...]
    truth_label: TraceTruthLabel = TraceTruthLabel.LIVE

    # Locked: an audit is not runtime integration and not the submit bridge.
    modifies_submit: bool = False
    adds_trace_append: bool = False
    is_bridge: bool = False

    def __post_init__(self) -> None:
        require_nonempty(self, "audit_id")
        if not self.requirements:
            raise AurelTraceError("audit must list at least one requirement")
        for field_name in ("modifies_submit", "adds_trace_append", "is_bridge"):
            if getattr(self, field_name) is True:
                raise AurelTraceError(
                    f"{field_name} must be False — the coverage audit is read-only "
                    "and is not the P5-C bridge"
                )
        if self.truth_label is TraceTruthLabel.TRACE_INTEGRITY_VERIFIED:
            raise AurelTraceError("an audit is a LIVE diagnostic, not a verified chain")

    def _by_status(
        self, status: SubmitCoverageStatus
    ) -> tuple[SubmitEvidenceRequirement, ...]:
        return tuple(r for r in self.requirements if r.current_status is status)

    @property
    def covered_requirements(self) -> tuple[SubmitEvidenceRequirement, ...]:
        return self._by_status(SubmitCoverageStatus.COVERED)

    @property
    def partial_requirements(self) -> tuple[SubmitEvidenceRequirement, ...]:
        return self._by_status(SubmitCoverageStatus.PARTIAL)

    @property
    def missing_requirements(self) -> tuple[SubmitEvidenceRequirement, ...]:
        return self._by_status(SubmitCoverageStatus.MISSING)

    @property
    def unsupported_requirements(self) -> tuple[SubmitEvidenceRequirement, ...]:
        return self._by_status(SubmitCoverageStatus.UNSUPPORTED)

    @property
    def summary(self) -> SubmitEvidenceCoverageSummary:
        return SubmitEvidenceCoverageSummary(
            covered=len(self.covered_requirements),
            partial=len(self.partial_requirements),
            missing=len(self.missing_requirements),
            unsupported=len(self.unsupported_requirements),
            unknown=len(self._by_status(SubmitCoverageStatus.UNKNOWN)),
            total=len(self.requirements),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "audit_id": self.audit_id,
            "runtime_submit_path_inspected": self.runtime_submit_path_inspected,
            "requirements": [r.to_dict() for r in self.requirements],
            "summary": self.summary.to_dict(),
            "modifies_submit": self.modifies_submit,
            "adds_trace_append": self.adds_trace_append,
            "is_bridge": self.is_bridge,
            "truth_label": self.truth_label.value,
        }


@dataclass(frozen=True)
class SubmitTraceCoverageReport:
    """Operator-readable coverage result and P5-C handoff recommendations."""

    report_id: str
    covered: tuple[SubmitEvidenceRequirement, ...]
    partial: tuple[SubmitEvidenceRequirement, ...]
    missing: tuple[SubmitEvidenceRequirement, ...]
    unsupported: tuple[SubmitEvidenceRequirement, ...]
    p5c_recommendations: tuple[SubmitTraceGap, ...]
    coverage_percent: float | None = None
    truth_label: TraceTruthLabel = TraceTruthLabel.LIVE

    # Locked: the report cannot claim completion while required gaps remain.
    claims_complete_coverage: bool = False

    def __post_init__(self) -> None:
        require_nonempty(self, "report_id")
        required_gap = any(
            r.required_for_trace_integrity_verified for r in self.partial + self.missing
        )
        if self.claims_complete_coverage and required_gap:
            raise AurelTraceError(
                "report must not claim complete coverage while required evidence "
                "is partial or missing"
            )
        if self.truth_label is TraceTruthLabel.TRACE_INTEGRITY_VERIFIED:
            raise AurelTraceError("a coverage report is a LIVE diagnostic")

    def to_dict(self) -> dict[str, Any]:
        return {
            "report_id": self.report_id,
            "covered": [r.to_dict() for r in self.covered],
            "partial": [r.to_dict() for r in self.partial],
            "missing": [r.to_dict() for r in self.missing],
            "unsupported": [r.to_dict() for r in self.unsupported],
            "p5c_recommendations": [g.to_dict() for g in self.p5c_recommendations],
            "coverage_percent": self.coverage_percent,
            "claims_complete_coverage": self.claims_complete_coverage,
            "truth_label": self.truth_label.value,
        }


# --------------------------------------------------------------------------- #
#  Deterministic default evidence map (read-only submit-path inspection).
#
#  Each entry: (status, required_for_integrity, required_for_future_verified,
#               owner_pack, evidence).
# --------------------------------------------------------------------------- #
_K = SubmitEvidenceRequirementKind
_S = SubmitCoverageStatus

_DEFAULT_SUBMIT_EVIDENCE_MAP: dict[
    SubmitEvidenceRequirementKind, tuple[SubmitCoverageStatus, bool, bool, str, str]
] = {
    _K.SANDBOX_BEFORE_HASH_RECORDED: (
        _S.COVERED, True, True, "P5-TRACE-A",
        "before_state_hash captured on the appended StateTransitionRecord",
    ),
    _K.SANDBOX_AFTER_HASH_RECORDED: (
        _S.COVERED, True, True, "P5-TRACE-A",
        "after_state_hash captured on the appended StateTransitionRecord",
    ),
    _K.VERIFIER_RESULT_RECORDED: (
        _S.COVERED, True, True, "P5-TRACE-A",
        "verifier_result captured on the appended StateTransitionRecord",
    ),
    _K.TRACE_APPEND_RECORDED: (
        _S.COVERED, True, True, "P5-TRACE-A",
        "submit() appends a hash-chained StateTransitionRecord via trace.append",
    ),
    _K.TOOL_RESULT_RECORDED: (
        _S.COVERED, True, True, "P5-TRACE-A",
        "observation_hash captured on the appended StateTransitionRecord",
    ),
    _K.HITL_DECISION_RECORDED: (
        _S.COVERED, True, True, "P5-TRACE-A",
        "append_approval_receipt writes a discrete ApprovalReceiptRecord",
    ),
    _K.BUDGET_DECISION_RECORDED: (
        _S.COVERED, True, True, "P5-TRACE-A",
        "BudgetDecisionRecord written on budget-decision paths",
    ),
    _K.COMMAND_ENVELOPE_RECORDED: (
        _S.PARTIAL, True, True, "P5-TRACE-C",
        "only command_hash is embedded in the transition; no discrete, "
        "independently referenceable command-envelope record",
    ),
    _K.POLICY_DECISION_RECORDED: (
        _S.PARTIAL, True, True, "P5-TRACE-C",
        "only policy_verdict is embedded in the transition; no discrete "
        "policy-decision evidence record",
    ),
    _K.TOOL_INVOCATION_RECORDED: (
        _S.PARTIAL, False, True, "P5-TRACE-C",
        "tool invocation is implied by command_hash in the transition; no "
        "discrete tool-invocation record",
    ),
    _K.OBSERVATION_RECORDED: (
        _S.PARTIAL, False, True, "P5-TRACE-C",
        "observation is returned and its hash stored on the transition; the "
        "full observation is not a discrete trace record",
    ),
    _K.ERROR_RECORDED: (
        _S.PARTIAL, False, True, "P5-TRACE-C",
        "PlanningFailureRecord / violation records cover some error surfaces; "
        "not all submit error paths emit a discrete error record",
    ),
    _K.ROLLBACK_RESULT_RECORDED: (
        _S.MISSING, False, True, "P5-TRACE-C",
        "write rollback runs but is recorded only as observation/verifier "
        "evidence; there is no discrete rollback-result record",
    ),
    _K.MEMORY_WRITE_RECORDED: (
        _S.MISSING, False, True, "P5-TRACE-C",
        "MemoryGovernanceRecord exists in core_types but submit() does not emit "
        "a discrete memory-write record on the observed path",
    ),
}


def _requirement_id(kind: SubmitEvidenceRequirementKind) -> str:
    return "sreq-" + trace_sha(canonical_trace_json({"kind": kind.value}))[:32]


def build_submit_trace_coverage_audit(
    *,
    inventory: ExistingTraceInventory | None = None,
    evidence_map: dict[
        SubmitEvidenceRequirementKind,
        tuple[SubmitCoverageStatus, bool, bool, str, str],
    ]
    | None = None,
) -> SubmitTraceCoverageAudit:
    """Build the read-only submit trace coverage audit.

    The audit is deterministic: it iterates the closed ordered set of
    requirement kinds and maps each to a documented coverage status. It performs
    no ledger writes and never touches ``runtime.submit``. ``inventory`` is
    accepted for parity/traceability with the P5-A catalog (defaulted lazily).
    """

    # Bind the inventory read for traceability; the audit derives from the
    # documented evidence map, not from live ledger state.
    _ = inventory or build_existing_trace_inventory()
    the_map = evidence_map or _DEFAULT_SUBMIT_EVIDENCE_MAP
    requirements: list[SubmitEvidenceRequirement] = []
    for kind in SubmitEvidenceRequirementKind:
        status, req_integrity, req_future, owner, evidence = the_map[kind]
        requirements.append(
            SubmitEvidenceRequirement(
                requirement_id=_requirement_id(kind),
                requirement_kind=kind,
                required_for_trace_integrity_verified=req_integrity,
                required_for_future_trace_verified=req_future,
                current_status=status,
                owner_pack=owner,
                evidence=evidence,
            )
        )
    return SubmitTraceCoverageAudit(
        audit_id=SUBMIT_TRACE_COVERAGE_AUDIT_ID,
        runtime_submit_path_inspected=True,
        requirements=tuple(requirements),
    )


def _gap_recommendation(requirement: SubmitEvidenceRequirement) -> str:
    return (
        f"P5-TRACE-C should bridge {requirement.requirement_kind.value} by binding "
        f"a discrete trace/evidence ref during submit ({requirement.owner_pack})."
    )


def build_submit_trace_coverage_report(
    audit: SubmitTraceCoverageAudit,
) -> SubmitTraceCoverageReport:
    """Derive the operator-readable report and P5-C recommendations from an audit.

    ``coverage_percent`` is deterministic and documented: covered requirements
    that are required for trace-integrity, over the total required-for-integrity
    requirement count.
    """

    covered = audit.covered_requirements
    partial = audit.partial_requirements
    missing = audit.missing_requirements
    unsupported = audit.unsupported_requirements

    gaps: list[SubmitTraceGap] = []
    for requirement in partial + missing + unsupported:
        gaps.append(
            SubmitTraceGap(
                gap_id="sgap-"
                + trace_sha(
                    canonical_trace_json({"kind": requirement.requirement_kind.value})
                )[:32],
                requirement=requirement,
                reason=requirement.evidence
                or f"{requirement.requirement_kind.value} is {requirement.current_status.value}",
                p5c_recommendation=_gap_recommendation(requirement),
            )
        )

    required_total = sum(
        1 for r in audit.requirements if r.required_for_trace_integrity_verified
    )
    required_covered = sum(
        1
        for r in covered
        if r.required_for_trace_integrity_verified
    )
    coverage_percent = (
        round(100.0 * required_covered / required_total, 2)
        if required_total
        else None
    )

    return SubmitTraceCoverageReport(
        report_id=SUBMIT_TRACE_COVERAGE_REPORT_ID,
        covered=covered,
        partial=partial,
        missing=missing,
        unsupported=unsupported,
        p5c_recommendations=tuple(gaps),
        coverage_percent=coverage_percent,
    )
