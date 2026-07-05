"""P5-TRACE-C runtime submit trace binding — an adapter over P5-B coverage.

This module maps a P5-TRACE-B ``SubmitTraceCoverageReport`` into a
``RuntimeSubmitTraceBinding`` of ``EvidenceRef`` objects. It is **read-model
only**: it never imports, calls, or mutates the governed runtime submit path,
never invokes the tool dispatch path, and never appends trace. Binding is not
execution; a COMPLETE binding is not ``TRACE_VERIFIED``.

Missing evidence from the P5-B report stays explicit as ``MISSING`` /
``PARTIAL`` / ``UNSUPPORTED`` evidence refs — that is the P5-TRACE-D handoff, not
a defect. The one canonical hash truth and truth vocabulary are reused from
P5-A; there is no ``TRACE_VERIFIED`` label.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .evidence_ref import (
    EvidenceKind,
    EvidenceRef,
    EvidenceStatus,
    TraceBindingCoverageStatus,
    make_evidence_ref,
    make_missing_evidence_ref,
)
from .submit_coverage import (
    SubmitCoverageStatus,
    SubmitEvidenceRequirement,
    SubmitEvidenceRequirementKind,
    SubmitTraceCoverageReport,
)
from .trace_hash import (
    AurelTraceError,
    TraceTruthLabel,
    canonical_trace_json,
    require_nonempty,
    trace_sha,
)

RUNTIME_SUBMIT_DOMAIN = "runtime.submit"

# Total map: each P5-B submit evidence requirement kind -> one evidence kind.
_K = SubmitEvidenceRequirementKind
_E = EvidenceKind
_REQUIREMENT_KIND_TO_EVIDENCE_KIND: dict[SubmitEvidenceRequirementKind, EvidenceKind] = {
    _K.COMMAND_ENVELOPE_RECORDED: _E.COMMAND_EVIDENCE,
    _K.POLICY_DECISION_RECORDED: _E.POLICY_EVIDENCE,
    _K.HITL_DECISION_RECORDED: _E.APPROVAL_EVIDENCE,
    _K.BUDGET_DECISION_RECORDED: _E.BUDGET_EVIDENCE,
    _K.SANDBOX_BEFORE_HASH_RECORDED: _E.SANDBOX_EVIDENCE,
    _K.TOOL_INVOCATION_RECORDED: _E.TOOL_INVOCATION_EVIDENCE,
    _K.TOOL_RESULT_RECORDED: _E.TOOL_RESULT_EVIDENCE,
    _K.VERIFIER_RESULT_RECORDED: _E.VERIFIER_EVIDENCE,
    _K.SANDBOX_AFTER_HASH_RECORDED: _E.SANDBOX_EVIDENCE,
    _K.ROLLBACK_RESULT_RECORDED: _E.ROLLBACK_EVIDENCE,
    _K.MEMORY_WRITE_RECORDED: _E.MEMORY_EVIDENCE,
    _K.TRACE_APPEND_RECORDED: _E.TRACE_APPEND_EVIDENCE,
    _K.OBSERVATION_RECORDED: _E.OBSERVATION_EVIDENCE,
    _K.ERROR_RECORDED: _E.ERROR_EVIDENCE,
}

# Which requirement kind fills which named binding slot.
_REQUIREMENT_KIND_TO_SLOT: dict[SubmitEvidenceRequirementKind, str] = {
    _K.COMMAND_ENVELOPE_RECORDED: "command_evidence_ref",
    _K.POLICY_DECISION_RECORDED: "policy_evidence_ref",
    _K.HITL_DECISION_RECORDED: "approval_evidence_ref",
    _K.BUDGET_DECISION_RECORDED: "budget_evidence_ref",
    _K.SANDBOX_BEFORE_HASH_RECORDED: "sandbox_before_evidence_ref",
    _K.TOOL_INVOCATION_RECORDED: "tool_invocation_evidence_ref",
    _K.TOOL_RESULT_RECORDED: "tool_result_evidence_ref",
    _K.VERIFIER_RESULT_RECORDED: "verifier_evidence_ref",
    _K.SANDBOX_AFTER_HASH_RECORDED: "sandbox_after_evidence_ref",
    _K.ROLLBACK_RESULT_RECORDED: "rollback_evidence_ref",
    _K.MEMORY_WRITE_RECORDED: "memory_evidence_ref",
    _K.TRACE_APPEND_RECORDED: "trace_append_evidence_ref",
    _K.ERROR_RECORDED: "error_evidence_ref",
    # OBSERVATION_RECORDED has no dedicated slot; it lives in evidence_refs only.
}


@dataclass(frozen=True)
class TraceBindingCoverageSummary:
    """Read-only deterministic count of evidence statuses across a binding."""

    summary_id: str
    coverage_status: TraceBindingCoverageStatus
    present_count: int
    partial_count: int
    missing_count: int
    unsupported_count: int
    error_count: int
    total: int
    truth_label: TraceTruthLabel = TraceTruthLabel.LIVE

    def to_dict(self) -> dict[str, Any]:
        return {
            "summary_id": self.summary_id,
            "coverage_status": self.coverage_status.value,
            "present_count": self.present_count,
            "partial_count": self.partial_count,
            "missing_count": self.missing_count,
            "unsupported_count": self.unsupported_count,
            "error_count": self.error_count,
            "total": self.total,
            "truth_label": self.truth_label.value,
        }


@dataclass(frozen=True)
class RuntimeSubmitTraceBinding:
    """Trace/evidence binding for one governed runtime submit path.

    Maps existing/expected evidence; it does not submit commands, call tools,
    append trace, or authorize. A COMPLETE ``coverage_status`` is not a claim of
    ``TRACE_VERIFIED``.
    """

    binding_id: str
    coverage_status: TraceBindingCoverageStatus
    evidence_refs: tuple[EvidenceRef, ...]
    missing_evidence: tuple[EvidenceRef, ...] = ()
    partial_evidence: tuple[EvidenceRef, ...] = ()
    command_evidence_ref: EvidenceRef | None = None
    policy_evidence_ref: EvidenceRef | None = None
    approval_evidence_ref: EvidenceRef | None = None
    budget_evidence_ref: EvidenceRef | None = None
    sandbox_before_evidence_ref: EvidenceRef | None = None
    tool_invocation_evidence_ref: EvidenceRef | None = None
    tool_result_evidence_ref: EvidenceRef | None = None
    verifier_evidence_ref: EvidenceRef | None = None
    sandbox_after_evidence_ref: EvidenceRef | None = None
    rollback_evidence_ref: EvidenceRef | None = None
    memory_evidence_ref: EvidenceRef | None = None
    trace_append_evidence_ref: EvidenceRef | None = None
    error_evidence_ref: EvidenceRef | None = None
    trace_binding_ref_id: str | None = None
    truth_label: TraceTruthLabel = TraceTruthLabel.TRACE_BOUND

    # Locked: a binding references; it does not execute, mutate, or verify.
    submits_command: bool = False
    calls_tool: bool = False
    appends_trace: bool = False
    authorizes: bool = False
    trace_verified: bool = False

    def __post_init__(self) -> None:
        require_nonempty(self, "binding_id")
        for field_name in (
            "submits_command",
            "calls_tool",
            "appends_trace",
            "authorizes",
            "trace_verified",
        ):
            if getattr(self, field_name) is True:
                raise AurelTraceError(
                    f"{field_name} must be False — a runtime submit binding "
                    "references evidence, it does not execute/mutate/verify"
                )
        if self.truth_label is TraceTruthLabel.TRACE_INTEGRITY_VERIFIED:
            raise AurelTraceError(
                "a runtime submit binding is TRACE_BOUND; the resolver (P5-D) verifies"
            )

    def to_dict(self) -> dict[str, Any]:
        slots = {
            name: (getattr(self, name).to_dict() if getattr(self, name) else None)
            for name in _REQUIREMENT_KIND_TO_SLOT.values()
        }
        return {
            "binding_id": self.binding_id,
            "coverage_status": self.coverage_status.value,
            "evidence_refs": [r.to_dict() for r in self.evidence_refs],
            "missing_evidence": [r.to_dict() for r in self.missing_evidence],
            "partial_evidence": [r.to_dict() for r in self.partial_evidence],
            "trace_binding_ref_id": self.trace_binding_ref_id,
            "submits_command": self.submits_command,
            "calls_tool": self.calls_tool,
            "appends_trace": self.appends_trace,
            "authorizes": self.authorizes,
            "trace_verified": self.trace_verified,
            "truth_label": self.truth_label.value,
            **slots,
        }


def _coverage_status_from_refs(
    refs: tuple[EvidenceRef, ...],
) -> TraceBindingCoverageStatus:
    if not refs:
        return TraceBindingCoverageStatus.MISSING
    if any(r.status is EvidenceStatus.ERROR for r in refs):
        return TraceBindingCoverageStatus.ERROR
    present = sum(1 for r in refs if r.is_present)
    if present == len(refs):
        return TraceBindingCoverageStatus.COMPLETE
    if present == 0:
        return TraceBindingCoverageStatus.MISSING
    return TraceBindingCoverageStatus.PARTIAL


def _evidence_ref_for_requirement(
    requirement: SubmitEvidenceRequirement,
    *,
    trace_binding_ref_id: str | None,
    receipt_ids: dict[SubmitEvidenceRequirementKind, str] | None,
) -> EvidenceRef:
    evidence_kind = _REQUIREMENT_KIND_TO_EVIDENCE_KIND[requirement.requirement_kind]
    receipt_id = (receipt_ids or {}).get(requirement.requirement_kind)
    status = requirement.current_status
    if status is SubmitCoverageStatus.COVERED:
        return make_evidence_ref(
            evidence_kind=evidence_kind,
            source_domain=RUNTIME_SUBMIT_DOMAIN,
            source_object_id=requirement.requirement_kind.value,
            status=EvidenceStatus.PRESENT,
            trace_binding_ref_id=trace_binding_ref_id,
            verification_receipt_id=receipt_id,
        )
    if status is SubmitCoverageStatus.PARTIAL:
        return make_missing_evidence_ref(
            evidence_kind=evidence_kind,
            source_domain=RUNTIME_SUBMIT_DOMAIN,
            source_object_id=requirement.requirement_kind.value,
            missing_reason=requirement.evidence
            or f"{requirement.requirement_kind.value} is partial",
            status=EvidenceStatus.PARTIAL,
        )
    if status is SubmitCoverageStatus.UNSUPPORTED:
        return make_missing_evidence_ref(
            evidence_kind=evidence_kind,
            source_domain=RUNTIME_SUBMIT_DOMAIN,
            source_object_id=requirement.requirement_kind.value,
            missing_reason=requirement.evidence
            or f"{requirement.requirement_kind.value} is unsupported",
            status=EvidenceStatus.UNSUPPORTED,
        )
    if status is SubmitCoverageStatus.MISSING:
        return make_missing_evidence_ref(
            evidence_kind=evidence_kind,
            source_domain=RUNTIME_SUBMIT_DOMAIN,
            source_object_id=requirement.requirement_kind.value,
            missing_reason=requirement.evidence
            or f"{requirement.requirement_kind.value} is missing",
            status=EvidenceStatus.MISSING,
        )
    # UNKNOWN -> ERROR evidence with an explicit reason.
    return EvidenceRef(
        evidence_ref_id="evref-"
        + trace_sha(
            canonical_trace_json(
                {
                    "evidence_kind": evidence_kind.value,
                    "source_domain": RUNTIME_SUBMIT_DOMAIN,
                    "source_object_id": requirement.requirement_kind.value,
                }
            )
        )[:40],
        evidence_kind=evidence_kind,
        source_domain=RUNTIME_SUBMIT_DOMAIN,
        source_object_id=requirement.requirement_kind.value,
        status=EvidenceStatus.ERROR,
        missing_reason=f"{requirement.requirement_kind.value} coverage is UNKNOWN",
    )


def build_runtime_submit_trace_binding(
    report: SubmitTraceCoverageReport,
    *,
    trace_binding_ref_id: str | None = None,
    receipt_ids: dict[SubmitEvidenceRequirementKind, str] | None = None,
) -> RuntimeSubmitTraceBinding:
    """Build a runtime submit trace binding from a P5-B coverage report.

    Every requirement in the report becomes an ``EvidenceRef`` placed in its
    named slot (where one exists) and in the generic ``evidence_refs`` tuple.
    Missing/partial evidence is preserved verbatim. A COMPLETE coverage status
    (only possible when every requirement is PRESENT) does not set any verified
    truth label.
    """

    requirements = tuple(report.covered + report.partial + report.missing + report.unsupported)
    refs: list[EvidenceRef] = []
    slots: dict[str, EvidenceRef] = {}
    for requirement in requirements:
        ref = _evidence_ref_for_requirement(
            requirement,
            trace_binding_ref_id=trace_binding_ref_id,
            receipt_ids=receipt_ids,
        )
        refs.append(ref)
        slot = _REQUIREMENT_KIND_TO_SLOT.get(requirement.requirement_kind)
        if slot is not None:
            slots[slot] = ref
    refs_tuple = tuple(refs)
    missing = tuple(r for r in refs_tuple if r.status is EvidenceStatus.MISSING)
    partial = tuple(r for r in refs_tuple if r.status is EvidenceStatus.PARTIAL)
    coverage_status = _coverage_status_from_refs(refs_tuple)
    binding_id = "rsbind-" + trace_sha(
        canonical_trace_json(
            {
                "report_id": report.report_id,
                "trace_binding_ref_id": trace_binding_ref_id,
                "evidence_ref_ids": [r.evidence_ref_id for r in refs_tuple],
            }
        )
    )[:40]
    return RuntimeSubmitTraceBinding(
        binding_id=binding_id,
        coverage_status=coverage_status,
        evidence_refs=refs_tuple,
        missing_evidence=missing,
        partial_evidence=partial,
        trace_binding_ref_id=trace_binding_ref_id,
        **slots,
    )


# ``RuntimeSubmitTraceBridge`` groups the builders as a small stateless namespace.
@dataclass(frozen=True)
class RuntimeSubmitTraceBridge:
    """Stateless adapter over P5-B coverage reports. Holds no runtime handle."""

    bridge_id: str = "runtime-submit-trace-bridge.p5-trace-c.v1"
    truth_label: TraceTruthLabel = TraceTruthLabel.LIVE

    # Locked: the bridge maps refs; it never calls submit or dispatches tools.
    calls_runtime_submit: bool = False
    calls_tool_dispatch: bool = False
    appends_trace: bool = False

    def __post_init__(self) -> None:
        for field_name in (
            "calls_runtime_submit",
            "calls_tool_dispatch",
            "appends_trace",
        ):
            if getattr(self, field_name) is True:
                raise AurelTraceError(
                    f"{field_name} must be False — the bridge is a read-only adapter"
                )

    def build_binding(
        self,
        report: SubmitTraceCoverageReport,
        *,
        trace_binding_ref_id: str | None = None,
        receipt_ids: dict[SubmitEvidenceRequirementKind, str] | None = None,
    ) -> RuntimeSubmitTraceBinding:
        return build_runtime_submit_trace_binding(
            report,
            trace_binding_ref_id=trace_binding_ref_id,
            receipt_ids=receipt_ids,
        )


def binding_from_submit_coverage_report(
    report: SubmitTraceCoverageReport,
    *,
    trace_binding_ref_id: str | None = None,
    receipt_ids: dict[SubmitEvidenceRequirementKind, str] | None = None,
) -> RuntimeSubmitTraceBinding:
    """Alias builder matching the dispatch's suggested helper name."""

    return build_runtime_submit_trace_binding(
        report,
        trace_binding_ref_id=trace_binding_ref_id,
        receipt_ids=receipt_ids,
    )


def missing_evidence_from_coverage_report(
    report: SubmitTraceCoverageReport,
) -> tuple[EvidenceRef, ...]:
    """Return the missing (and partial/unsupported) evidence refs for the report."""

    binding = build_runtime_submit_trace_binding(report)
    return tuple(
        r
        for r in binding.evidence_refs
        if r.status
        in (
            EvidenceStatus.MISSING,
            EvidenceStatus.PARTIAL,
            EvidenceStatus.UNSUPPORTED,
        )
    )


def runtime_submit_binding_status(
    binding: RuntimeSubmitTraceBinding,
) -> TraceBindingCoverageStatus:
    return binding.coverage_status


def summarize_binding_coverage(
    binding: RuntimeSubmitTraceBinding,
) -> TraceBindingCoverageSummary:
    """Summarize evidence coverage for one binding, read-only and deterministic."""

    refs = binding.evidence_refs
    present = sum(
        1
        for r in refs
        if r.status
        in (
            EvidenceStatus.PRESENT,
            EvidenceStatus.TRACE_BOUND,
            EvidenceStatus.TRACE_INTEGRITY_VERIFIED,
        )
    )
    partial = sum(1 for r in refs if r.status is EvidenceStatus.PARTIAL)
    missing = sum(1 for r in refs if r.status is EvidenceStatus.MISSING)
    unsupported = sum(1 for r in refs if r.status is EvidenceStatus.UNSUPPORTED)
    error = sum(1 for r in refs if r.status is EvidenceStatus.ERROR)
    summary_id = "rsbsum-" + trace_sha(
        canonical_trace_json({"binding_id": binding.binding_id})
    )[:32]
    return TraceBindingCoverageSummary(
        summary_id=summary_id,
        coverage_status=binding.coverage_status,
        present_count=present,
        partial_count=partial,
        missing_count=missing,
        unsupported_count=unsupported,
        error_count=error,
        total=len(refs),
    )
