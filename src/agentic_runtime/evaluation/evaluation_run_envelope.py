"""P1.5.5 — Evaluation Run Envelope + Sparse Run Readiness.

Governed evaluation run envelope layer.
Core law: No governed evaluation execution without a valid run envelope.

EvaluationRunEnvelope does NOT execute evaluation, create EvaluationResult,
create CapabilityEvidenceRecord, verify capability, or call LLMs/tools.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum

from .evaluation_foundation import (
    EvaluationDomain,
    EvaluationSubjectType,
)
from .evaluation_criteria_schema import (
    EvaluationCriteriaSchemaItem,
    EvaluationCriteriaSchemaResolution,
    EvaluationCriterionEvidenceRequirement,
    EvaluationCriterionKind,
    EvaluationCriterionRequirementLevel,
    criteria_schema_resolution_to_dict,
)
from .evaluation_subject_registry import (
    EvaluationSubjectRegistryEntry,
    EvaluationSubjectStatus,
    evaluation_subject_registry_entry_to_dict,
)


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class EvaluationRunStatus(str, Enum):
    DRAFT = "DRAFT"
    READY = "READY"
    BLOCKED = "BLOCKED"
    INVALID = "INVALID"
    CANCELLED = "CANCELLED"
    COMPLETED = "COMPLETED"
    UNKNOWN = "UNKNOWN"


class EvaluationRunIntent(str, Enum):
    CAPABILITY_CHECK = "CAPABILITY_CHECK"
    CLAIM_SUPPORT_CHECK = "CLAIM_SUPPORT_CHECK"
    REGRESSION_CHECK = "REGRESSION_CHECK"
    ADVERSARIAL_CHECK = "ADVERSARIAL_CHECK"
    BENCHMARK_PREP = "BENCHMARK_PREP"
    TRUST_EVIDENCE_CHECK = "TRUST_EVIDENCE_CHECK"
    SPARSE_CONTEXT_CHECK = "SPARSE_CONTEXT_CHECK"
    POLICY_COMPLIANCE_CHECK = "POLICY_COMPLIANCE_CHECK"
    UNKNOWN = "UNKNOWN"


class EvaluationRunMode(str, Enum):
    DRY_RUN = "DRY_RUN"
    STATIC_REVIEW = "STATIC_REVIEW"
    FIXTURE_BASED = "FIXTURE_BASED"
    HUMAN_REVIEW = "HUMAN_REVIEW"
    LLM_JUDGE_PLANNED = "LLM_JUDGE_PLANNED"
    TOOL_EXECUTION_PLANNED = "TOOL_EXECUTION_PLANNED"
    UNKNOWN = "UNKNOWN"


class EvaluationEvaluatorType(str, Enum):
    DETERMINISTIC = "DETERMINISTIC"
    HUMAN = "HUMAN"
    LLM_JUDGE = "LLM_JUDGE"
    TOOL_BASED = "TOOL_BASED"
    HYBRID = "HYBRID"
    UNKNOWN = "UNKNOWN"


# ---------------------------------------------------------------------------
# Invariants
# ---------------------------------------------------------------------------


P155_INVARIANTS: tuple[str, ...] = (
    "INV-P155-01: No governed evaluation execution without a valid run envelope.",
    "INV-P155-02: Run envelope does not execute evaluation.",
    "INV-P155-03: Run envelope does not create EvaluationResult.",
    "INV-P155-04: Run envelope does not verify capability.",
    "INV-P155-05: READY envelope requires registered/active subject.",
    "INV-P155-06: READY envelope requires resolved criteria.",
    "INV-P155-07: READY envelope requires known evaluator type.",
    "INV-P155-08: Required/blocking evidence requirements must be satisfied.",
    "INV-P155-09: Sparse run metadata does not imply ASCL implementation.",
    "INV-P155-10: P1.5.6 is the next module.",
    "INV-P155-SC-01: Sparse-context run envelopes may require retrieval/context/evidence graph traces.",
    "INV-P155-SC-02: Lost context risk may be required as metadata, not solved here.",
    "INV-P155-SC-03: Envelope must not claim Sparse Context Compiler, SSA, or true subquadratic attention is implemented.",
)

_SPARSE_CRITERION_KINDS: frozenset[EvaluationCriterionKind] = frozenset({
    EvaluationCriterionKind.SPARSE_CONTEXT_QUALITY,
    EvaluationCriterionKind.EVIDENCE_RECALL,
    EvaluationCriterionKind.CONTEXT_BUDGET_EFFICIENCY,
    EvaluationCriterionKind.MULTI_HOP_TRACE_INTEGRITY,
    EvaluationCriterionKind.CONTRADICTION_SURVIVAL,
    EvaluationCriterionKind.LOST_CONTEXT_RISK,
    EvaluationCriterionKind.GOVERNED_CONTEXT_SELECTION,
    EvaluationCriterionKind.AUTHORITY_AWARE_RETRIEVAL,
})


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class EvaluationRunEvidenceRequirement:
    requirement_id: str
    evidence_requirement: EvaluationCriterionEvidenceRequirement
    required: bool
    satisfied: bool
    evidence_refs: tuple[str, ...] = ()
    missing_reason: str | None = None


@dataclass(frozen=True)
class GovernedEvaluationRunEnvelope:
    run_id: str

    status: EvaluationRunStatus
    intent: EvaluationRunIntent
    mode: EvaluationRunMode

    subject_entry: EvaluationSubjectRegistryEntry
    criteria_resolution: EvaluationCriteriaSchemaResolution

    evaluator_type: EvaluationEvaluatorType
    evaluator_ref: str | None = None

    scope_id: str | None = None
    policy_refs: tuple[str, ...] = ()
    evidence_requirements: tuple[EvaluationRunEvidenceRequirement, ...] = ()

    input_refs: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()
    context_refs: tuple[str, ...] = ()

    sparse_context_required: bool = False
    retrieval_trace_required: bool = False
    context_trace_required: bool = False
    evidence_graph_required: bool = False
    lost_context_risk_required: bool = False

    warnings: tuple[str, ...] = ()
    blockers: tuple[str, ...] = ()

    summary: str = ""


@dataclass(frozen=True)
class EvaluationRunEnvelopeValidation:
    valid: bool
    status: EvaluationRunStatus
    blockers: tuple[str, ...]
    warnings: tuple[str, ...]
    summary: str


@dataclass(frozen=True)
class EvaluationRunEnvelopeReport:
    report_id: str
    status: str
    summary: str

    envelopes_created: int
    envelopes_ready: int
    envelopes_blocked: int

    sparse_run_readiness: str

    objects_added: tuple[str, ...]
    invariants: tuple[str, ...]
    warnings: tuple[str, ...]
    blockers: tuple[str, ...]

    next_module: str


# ---------------------------------------------------------------------------
# Engine functions
# ---------------------------------------------------------------------------


def build_evidence_requirements_from_criteria(
    criteria: tuple[EvaluationCriteriaSchemaItem, ...],
    evidence_refs: tuple[str, ...] = (),
) -> tuple[EvaluationRunEvidenceRequirement, ...]:
    requirements: list[EvaluationRunEvidenceRequirement] = []
    has_any_refs = len(evidence_refs) > 0

    for item in criteria:
        if item.evidence_requirement == EvaluationCriterionEvidenceRequirement.NONE:
            continue

        req_id = f"ev_req_{item.criterion_id}"
        is_required = item.requirement_level in (
            EvaluationCriterionRequirementLevel.REQUIRED,
            EvaluationCriterionRequirementLevel.BLOCKING,
        )

        satisfied = has_any_refs

        missing = None if satisfied else "no evidence refs provided" if is_required else None

        requirements.append(EvaluationRunEvidenceRequirement(
            requirement_id=req_id,
            evidence_requirement=item.evidence_requirement,
            required=is_required,
            satisfied=satisfied,
            evidence_refs=evidence_refs,
            missing_reason=missing,
        ))

    return tuple(requirements)


def build_governed_evaluation_run_envelope(
    *,
    run_id: str,
    intent: EvaluationRunIntent,
    mode: EvaluationRunMode,
    subject_entry: EvaluationSubjectRegistryEntry,
    criteria_resolution: EvaluationCriteriaSchemaResolution,
    evaluator_type: EvaluationEvaluatorType,
    evaluator_ref: str | None = None,
    scope_id: str | None = None,
    policy_refs: tuple[str, ...] = (),
    input_refs: tuple[str, ...] = (),
    evidence_refs: tuple[str, ...] = (),
    context_refs: tuple[str, ...] = (),
) -> GovernedEvaluationRunEnvelope:
    warnings: list[str] = []
    blockers: list[str] = []

    # Derive evidence requirements from criteria
    evidence_requirements = build_evidence_requirements_from_criteria(
        criteria_resolution.criteria,
        evidence_refs=evidence_refs,
    )

    # Sparse context derivation
    sparse_context_required = False
    retrieval_trace_required = False
    context_trace_required = False
    evidence_graph_required = False
    lost_context_risk_required = False

    if intent == EvaluationRunIntent.SPARSE_CONTEXT_CHECK:
        sparse_context_required = True

    for item in criteria_resolution.criteria:
        if item.kind in _SPARSE_CRITERION_KINDS:
            sparse_context_required = True
        if item.kind == EvaluationCriterionKind.LOST_CONTEXT_RISK:
            lost_context_risk_required = True

    for req in evidence_requirements:
        if req.evidence_requirement == EvaluationCriterionEvidenceRequirement.RETRIEVAL_TRACE:
            retrieval_trace_required = True
        if req.evidence_requirement == EvaluationCriterionEvidenceRequirement.CONTEXT_TRACE:
            context_trace_required = True
        if req.evidence_requirement == EvaluationCriterionEvidenceRequirement.EVIDENCE_GRAPH:
            evidence_graph_required = True

    # Subject validation
    if subject_entry.status not in (
        EvaluationSubjectStatus.REGISTERED,
        EvaluationSubjectStatus.ACTIVE,
    ):
        blockers.append(
            f"subject {subject_entry.subject.subject_id!r} is {subject_entry.status.value}, "
            f"not REGISTERED or ACTIVE"
        )

    # Criteria resolution blockers
    if criteria_resolution.blockers:
        blockers.extend(criteria_resolution.blockers)

    # No criteria
    if not criteria_resolution.criteria:
        blockers.append("no criteria resolved for envelope")

    # Unknown evaluator
    if evaluator_type == EvaluationEvaluatorType.UNKNOWN:
        blockers.append("evaluator_type is UNKNOWN")

    # Evidence requirements
    for req in evidence_requirements:
        if req.required and not req.satisfied:
            blockers.append(
                f"required evidence requirement {req.requirement_id!r} not satisfied: "
                f"{req.missing_reason or 'missing evidence'}"
            )

    # Warnings-only
    if intent == EvaluationRunIntent.UNKNOWN:
        warnings.append("run intent is UNKNOWN")
    if mode == EvaluationRunMode.UNKNOWN:
        warnings.append("run mode is UNKNOWN")

    status = resolve_run_readiness(blockers=tuple(blockers), warnings=tuple(warnings))

    return GovernedEvaluationRunEnvelope(
        run_id=run_id,
        status=status,
        intent=intent,
        mode=mode,
        subject_entry=subject_entry,
        criteria_resolution=criteria_resolution,
        evaluator_type=evaluator_type,
        evaluator_ref=evaluator_ref,
        scope_id=scope_id,
        policy_refs=policy_refs,
        evidence_requirements=evidence_requirements,
        input_refs=input_refs,
        evidence_refs=evidence_refs,
        context_refs=context_refs,
        sparse_context_required=sparse_context_required,
        retrieval_trace_required=retrieval_trace_required,
        context_trace_required=context_trace_required,
        evidence_graph_required=evidence_graph_required,
        lost_context_risk_required=lost_context_risk_required,
        warnings=tuple(warnings),
        blockers=tuple(blockers),
        summary=f"Evaluation run {status.value}: {len(blockers)} blocker(s), {len(warnings)} warning(s).",
    )


def validate_governed_evaluation_run_envelope(
    envelope: GovernedEvaluationRunEnvelope,
) -> EvaluationRunEnvelopeValidation:
    blockers: list[str] = []
    warnings: list[str] = []

    if not envelope.run_id or not envelope.run_id.strip():
        blockers.append("run_id must not be empty")

    if envelope.intent == EvaluationRunIntent.UNKNOWN:
        blockers.append("run intent is UNKNOWN")

    if envelope.mode == EvaluationRunMode.UNKNOWN:
        blockers.append("run mode is UNKNOWN")

    if envelope.evaluator_type == EvaluationEvaluatorType.UNKNOWN:
        blockers.append("evaluator_type is UNKNOWN")

    # Subject must be REGISTERED or ACTIVE
    if envelope.subject_entry.status not in (
        EvaluationSubjectStatus.REGISTERED,
        EvaluationSubjectStatus.ACTIVE,
    ):
        blockers.append(
            f"subject status is {envelope.subject_entry.status.value}, not REGISTERED or ACTIVE"
        )

    # Criteria resolution blockers
    if envelope.criteria_resolution.blockers:
        blockers.extend(envelope.criteria_resolution.blockers)

    # Must have criteria
    if not envelope.criteria_resolution.criteria:
        blockers.append("envelope has no criteria")

    # Unsatisfied required evidence
    for req in envelope.evidence_requirements:
        if req.required and not req.satisfied:
            blockers.append(
                f"required evidence requirement {req.requirement_id!r} not satisfied"
            )

    # Sparse context check requires sparse requirements
    if envelope.intent == EvaluationRunIntent.SPARSE_CONTEXT_CHECK:
        if not envelope.sparse_context_required:
            blockers.append(
                "SPARSE_CONTEXT_CHECK intent but sparse_context_required is False"
            )

    # READY cannot have blockers
    if envelope.status == EvaluationRunStatus.READY and blockers:
        blockers.append(
            f"envelope status is READY but {len(blockers)} blocker(s) found"
        )

    # Collect envelope-level warnings
    if envelope.warnings:
        warnings.extend(envelope.warnings)

    valid = len(blockers) == 0
    status = EvaluationRunStatus.READY if valid else EvaluationRunStatus.BLOCKED

    return EvaluationRunEnvelopeValidation(
        valid=valid,
        status=status,
        blockers=tuple(blockers),
        warnings=tuple(warnings),
        summary=(
            f"{'Valid' if valid else 'Blocked'}: "
            f"{len(blockers)} blocker(s), {len(warnings)} warning(s)."
        ),
    )


def resolve_run_readiness(
    *,
    blockers: tuple[str, ...],
    warnings: tuple[str, ...],
) -> EvaluationRunStatus:
    if blockers:
        return EvaluationRunStatus.BLOCKED
    return EvaluationRunStatus.READY


def build_p155_run_envelope_report(
    *,
    envelopes_created: int = 0,
    envelopes_ready: int = 0,
    envelopes_blocked: int = 0,
    sparse_run_readiness: str = "ENVELOPE_METADATA_ONLY",
    warnings: tuple[str, ...] = (),
    blockers: tuple[str, ...] = (),
) -> EvaluationRunEnvelopeReport:
    if blockers:
        status = "BLOCKED"
    elif warnings:
        status = "DEGRADED"
    else:
        status = "READY"

    ts = datetime.now(timezone.utc).isoformat()
    report_id = "p155_" + hashlib.sha256(ts.encode()).hexdigest()[:16]

    return EvaluationRunEnvelopeReport(
        report_id=report_id,
        status=status,
        summary=(
            f"P1.5.5 Evaluation Run Envelope {status}. "
            f"Created: {envelopes_created}, Ready: {envelopes_ready}, Blocked: {envelopes_blocked}. "
            f"Sparse readiness: {sparse_run_readiness}. "
            f"Next: P1.5.6."
        ),
        envelopes_created=envelopes_created,
        envelopes_ready=envelopes_ready,
        envelopes_blocked=envelopes_blocked,
        sparse_run_readiness=sparse_run_readiness,
        objects_added=(
            "EvaluationRunStatus",
            "EvaluationRunIntent",
            "EvaluationRunMode",
            "EvaluationEvaluatorType",
            "EvaluationRunEvidenceRequirement",
            "GovernedEvaluationRunEnvelope",
            "EvaluationRunEnvelopeValidation",
            "EvaluationRunEnvelopeReport",
        ),
        invariants=P155_INVARIANTS,
        warnings=warnings,
        blockers=blockers,
        next_module="P1.5.6 — Result Classification Engine",
    )


# ---------------------------------------------------------------------------
# Serialization helpers
# ---------------------------------------------------------------------------


def run_evidence_requirement_to_dict(
    req: EvaluationRunEvidenceRequirement,
) -> dict[str, object]:
    return {
        "requirement_id": req.requirement_id,
        "evidence_requirement": req.evidence_requirement.value,
        "required": req.required,
        "satisfied": req.satisfied,
        "evidence_refs": list(req.evidence_refs),
        "missing_reason": req.missing_reason,
    }


def governed_evaluation_run_envelope_to_dict(
    envelope: GovernedEvaluationRunEnvelope,
) -> dict[str, object]:
    return {
        "run_id": envelope.run_id,
        "status": envelope.status.value,
        "intent": envelope.intent.value,
        "mode": envelope.mode.value,
        "subject_entry": evaluation_subject_registry_entry_to_dict(envelope.subject_entry),
        "criteria_resolution": criteria_schema_resolution_to_dict(envelope.criteria_resolution),
        "evaluator_type": envelope.evaluator_type.value,
        "evaluator_ref": envelope.evaluator_ref,
        "scope_id": envelope.scope_id,
        "policy_refs": list(envelope.policy_refs),
        "evidence_requirements": [
            run_evidence_requirement_to_dict(r) for r in envelope.evidence_requirements
        ],
        "input_refs": list(envelope.input_refs),
        "evidence_refs": list(envelope.evidence_refs),
        "context_refs": list(envelope.context_refs),
        "sparse_context_required": envelope.sparse_context_required,
        "retrieval_trace_required": envelope.retrieval_trace_required,
        "context_trace_required": envelope.context_trace_required,
        "evidence_graph_required": envelope.evidence_graph_required,
        "lost_context_risk_required": envelope.lost_context_risk_required,
        "warnings": list(envelope.warnings),
        "blockers": list(envelope.blockers),
        "summary": envelope.summary,
    }


def run_envelope_validation_to_dict(
    validation: EvaluationRunEnvelopeValidation,
) -> dict[str, object]:
    return {
        "valid": validation.valid,
        "status": validation.status.value,
        "blockers": list(validation.blockers),
        "warnings": list(validation.warnings),
        "summary": validation.summary,
    }


def run_envelope_report_to_dict(
    report: EvaluationRunEnvelopeReport,
) -> dict[str, object]:
    return {
        "report_id": report.report_id,
        "status": report.status,
        "summary": report.summary,
        "envelopes_created": report.envelopes_created,
        "envelopes_ready": report.envelopes_ready,
        "envelopes_blocked": report.envelopes_blocked,
        "sparse_run_readiness": report.sparse_run_readiness,
        "objects_added": list(report.objects_added),
        "invariants": list(report.invariants),
        "warnings": list(report.warnings),
        "blockers": list(report.blockers),
        "next_module": report.next_module,
    }


# ---------------------------------------------------------------------------
# Example helpers
# ---------------------------------------------------------------------------


def example_ready_run_envelope() -> GovernedEvaluationRunEnvelope:
    from .evaluation_criteria_schema import (
        build_default_criteria_schema_for_subject_type,
        resolve_criteria_for_subject as resolve_criteria,
    )
    from .evaluation_subject_registry import example_registered_core_subject

    subject_entry = example_registered_core_subject()
    schema = build_default_criteria_schema_for_subject_type(
        domain=EvaluationDomain.AUREL_CORE,
        subject_type=EvaluationSubjectType.AGENT_IDENTITY,
    )
    from .evaluation_criteria_schema import EvaluationCriteriaSchemaRegistry
    registry = EvaluationCriteriaSchemaRegistry(
        registry_id="reg_example",
        schemas=(schema,),
    )
    criteria_resolution = resolve_criteria(subject_entry=subject_entry, registry=registry)

    return build_governed_evaluation_run_envelope(
        run_id="run_example_ready",
        intent=EvaluationRunIntent.CAPABILITY_CHECK,
        mode=EvaluationRunMode.STATIC_REVIEW,
        subject_entry=subject_entry,
        criteria_resolution=criteria_resolution,
        evaluator_type=EvaluationEvaluatorType.DETERMINISTIC,
        evaluator_ref="p155_example",
        scope_id="scope_aurel_core",
        evidence_refs=("ref_001",),
    )


def example_sparse_ready_run_envelope() -> GovernedEvaluationRunEnvelope:
    from .evaluation_criteria_schema import (
        EvaluationCriteriaSchemaRegistry,
        build_default_sparse_criteria_schema,
        resolve_criteria_for_subject as resolve_criteria,
    )
    from .evaluation_subject_registry import example_registered_sparse_context_subject

    subject_entry = example_registered_sparse_context_subject()
    schema = build_default_sparse_criteria_schema()
    registry = EvaluationCriteriaSchemaRegistry(
        registry_id="reg_sparse_example",
        schemas=(schema,),
    )
    criteria_resolution = resolve_criteria(subject_entry=subject_entry, registry=registry)

    return build_governed_evaluation_run_envelope(
        run_id="run_example_sparse",
        intent=EvaluationRunIntent.SPARSE_CONTEXT_CHECK,
        mode=EvaluationRunMode.STATIC_REVIEW,
        subject_entry=subject_entry,
        criteria_resolution=criteria_resolution,
        evaluator_type=EvaluationEvaluatorType.DETERMINISTIC,
        evaluator_ref="p155_sparse_example",
        scope_id="scope_aurel_core",
        evidence_refs=("ref_sc_001",),
        context_refs=("ctx_001",),
    )


__all__ = [
    "EvaluationRunStatus",
    "EvaluationRunIntent",
    "EvaluationRunMode",
    "EvaluationEvaluatorType",
    "EvaluationRunEvidenceRequirement",
    "GovernedEvaluationRunEnvelope",
    "EvaluationRunEnvelopeValidation",
    "EvaluationRunEnvelopeReport",
    "P155_INVARIANTS",
    "build_evidence_requirements_from_criteria",
    "build_governed_evaluation_run_envelope",
    "validate_governed_evaluation_run_envelope",
    "resolve_run_readiness",
    "build_p155_run_envelope_report",
    "run_evidence_requirement_to_dict",
    "governed_evaluation_run_envelope_to_dict",
    "run_envelope_validation_to_dict",
    "run_envelope_report_to_dict",
    "example_ready_run_envelope",
    "example_sparse_ready_run_envelope",
]
