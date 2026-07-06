"""P1.5.4 — Evaluation Criteria Schema + Sparse Criteria Readiness.

Reusable criteria schema layer for Aurel evaluations.
Core law: No criteria schema, no governed evaluation run.

Criteria schemas define what is being checked and how — they do NOT run
evaluation, create EvaluationResult, verify capability, or implement
Sparse Context Compiler / SSA / subquadratic model attention.
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
from .evaluation_objects import (
    EvaluationFailureMode,
)
from .evaluation_subject_registry import (
    EvaluationSubjectRegistryEntry,
    EvaluationSubjectStatus,
)


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class EvaluationCriterionKind(str, Enum):
    CORRECTNESS = "CORRECTNESS"
    GROUNDEDNESS = "GROUNDEDNESS"
    COMPLETENESS = "COMPLETENESS"
    CONSISTENCY = "CONSISTENCY"
    SAFETY = "SAFETY"
    POLICY_COMPLIANCE = "POLICY_COMPLIANCE"
    AUTHORITY_COMPLIANCE = "AUTHORITY_COMPLIANCE"
    EVIDENCE_QUALITY = "EVIDENCE_QUALITY"
    TRACEABILITY = "TRACEABILITY"
    REPRODUCIBILITY = "REPRODUCIBILITY"
    ROBUSTNESS = "ROBUSTNESS"
    REGRESSION_RESISTANCE = "REGRESSION_RESISTANCE"

    SPARSE_CONTEXT_QUALITY = "SPARSE_CONTEXT_QUALITY"
    EVIDENCE_RECALL = "EVIDENCE_RECALL"
    CONTEXT_BUDGET_EFFICIENCY = "CONTEXT_BUDGET_EFFICIENCY"
    MULTI_HOP_TRACE_INTEGRITY = "MULTI_HOP_TRACE_INTEGRITY"
    CONTRADICTION_SURVIVAL = "CONTRADICTION_SURVIVAL"
    LOST_CONTEXT_RISK = "LOST_CONTEXT_RISK"
    GOVERNED_CONTEXT_SELECTION = "GOVERNED_CONTEXT_SELECTION"
    AUTHORITY_AWARE_RETRIEVAL = "AUTHORITY_AWARE_RETRIEVAL"

    UNKNOWN = "UNKNOWN"


class EvaluationCriterionSeverity(str, Enum):
    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class EvaluationCriterionRequirementLevel(str, Enum):
    OPTIONAL = "OPTIONAL"
    RECOMMENDED = "RECOMMENDED"
    REQUIRED = "REQUIRED"
    BLOCKING = "BLOCKING"


class EvaluationCriterionEvidenceRequirement(str, Enum):
    NONE = "NONE"
    EVIDENCE_REF = "EVIDENCE_REF"
    SOURCE_REF = "SOURCE_REF"
    TRACE_REF = "TRACE_REF"
    TEST_RESULT = "TEST_RESULT"
    OPERATOR_REVIEW = "OPERATOR_REVIEW"
    POLICY_DECISION = "POLICY_DECISION"
    TRUST_EVIDENCE = "TRUST_EVIDENCE"
    CAPABILITY_EVIDENCE = "CAPABILITY_EVIDENCE"
    CONTEXT_TRACE = "CONTEXT_TRACE"
    RETRIEVAL_TRACE = "RETRIEVAL_TRACE"
    EVIDENCE_GRAPH = "EVIDENCE_GRAPH"
    UNKNOWN = "UNKNOWN"


# ---------------------------------------------------------------------------
# Invariants
# ---------------------------------------------------------------------------


P154_INVARIANTS: tuple[str, ...] = (
    "INV-P154-01: No criteria schema, no governed evaluation run.",
    "INV-P154-02: Criteria schema does not run evaluation.",
    "INV-P154-03: Criteria passing does not verify capability.",
    "INV-P154-04: BLOCKING criteria require evidence unless explicitly justified.",
    "INV-P154-05: UNKNOWN criterion kind cannot be REQUIRED or BLOCKING.",
    "INV-P154-06: Criteria applicability must be explicit.",
    "INV-P154-07: Duplicate criterion ids are invalid.",
    "INV-P154-08: Sparse context criteria are evaluative hooks, not ASCL implementation.",
    "INV-P154-09: No numeric score is introduced.",
    "INV-P154-10: P1.5.5 is the next module.",
    "INV-P154-SC-01: Sparse context quality is measurable before ASCL engine exists.",
    "INV-P154-SC-02: Lost context risk is a criterion, not a solved property.",
    "INV-P154-SC-03: Evidence recall criteria require evidence/retrieval/context trace refs later.",
    "INV-P154-SC-04: Criteria schema must not claim SSA/subquadratic model attention is implemented.",
    "INV-P154-SC-05: Sparse criteria do not imply Sparse Context Compiler exists.",
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
class EvaluationCriterionApplicability:
    domain: EvaluationDomain
    subject_type: EvaluationSubjectType
    origin_filter: tuple[str, ...] = ()
    category_filter: tuple[str, ...] = ()
    tag_filter: tuple[str, ...] = ()


@dataclass(frozen=True)
class EvaluationCriteriaSchemaItem:
    criterion_id: str
    kind: EvaluationCriterionKind
    name: str
    description: str

    severity: EvaluationCriterionSeverity
    requirement_level: EvaluationCriterionRequirementLevel
    evidence_requirement: EvaluationCriterionEvidenceRequirement

    applicable_failure_modes: tuple[EvaluationFailureMode, ...]
    applicability: EvaluationCriterionApplicability

    non_goals: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()


@dataclass(frozen=True)
class EvaluationCriteriaSchema:
    schema_id: str
    name: str
    description: str

    domain: EvaluationDomain
    subject_type: EvaluationSubjectType

    criteria: tuple[EvaluationCriteriaSchemaItem, ...]

    version: str = "1.0"
    owner_module: str | None = None

    warnings: tuple[str, ...] = ()
    blockers: tuple[str, ...] = ()
    summary: str = ""


@dataclass(frozen=True)
class EvaluationCriteriaSchemaRegistry:
    registry_id: str
    schemas: tuple[EvaluationCriteriaSchema, ...]

    warnings: tuple[str, ...] = ()
    blockers: tuple[str, ...] = ()
    summary: str = ""


@dataclass(frozen=True)
class EvaluationCriteriaSchemaResolution:
    subject_id: str
    schema_ids: tuple[str, ...]
    criteria: tuple[EvaluationCriteriaSchemaItem, ...]

    required_criteria: tuple[str, ...]
    blocking_criteria: tuple[str, ...]

    warnings: tuple[str, ...] = ()
    blockers: tuple[str, ...] = ()
    summary: str = ""


@dataclass(frozen=True)
class EvaluationCriteriaSchemaReport:
    report_id: str
    status: str
    summary: str

    schemas_created: int
    criteria_created: int

    sparse_criteria_ready: bool

    objects_added: tuple[str, ...]
    invariants: tuple[str, ...]
    warnings: tuple[str, ...]
    blockers: tuple[str, ...]

    next_module: str


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def validate_criterion_applicability(
    applicability: EvaluationCriterionApplicability,
) -> tuple[str, ...]:
    issues: list[str] = []

    if applicability.domain == EvaluationDomain.UNKNOWN:
        issues.append("applicability domain is UNKNOWN — not acceptable for governed criteria")

    if applicability.subject_type == EvaluationSubjectType.UNKNOWN:
        issues.append("applicability subject_type is UNKNOWN — not acceptable for governed criteria")

    return tuple(issues)


def validate_criteria_schema_item(
    item: EvaluationCriteriaSchemaItem,
) -> tuple[str, ...]:
    issues: list[str] = []

    if not item.criterion_id or not item.criterion_id.strip():
        issues.append("criterion_id must not be empty")

    if not item.name or not item.name.strip():
        issues.append("name must not be empty")

    # UNKNOWN kind cannot be REQUIRED or BLOCKING
    if item.kind == EvaluationCriterionKind.UNKNOWN:
        if item.requirement_level in (
            EvaluationCriterionRequirementLevel.REQUIRED,
            EvaluationCriterionRequirementLevel.BLOCKING,
        ):
            issues.append("UNKNOWN criterion kind cannot be REQUIRED or BLOCKING")

    # BLOCKING requires evidence unless explicitly justified in limitations
    if item.requirement_level == EvaluationCriterionRequirementLevel.BLOCKING:
        if item.evidence_requirement == EvaluationCriterionEvidenceRequirement.NONE:
            if not item.limitations:
                issues.append(
                    "BLOCKING criterion with NONE evidence requirement must have explicit limitations"
                )

    # Sparse context criteria must not claim compiler/SSA/subquadratic is implemented
    if item.kind in _SPARSE_CRITERION_KINDS:
        combined = " ".join((
            item.description,
            " ".join(item.non_goals),
            " ".join(item.limitations),
        )).lower()
        if "ssa" in combined:
            if "not implemented" not in combined and "does not" not in combined:
                issues.append(
                    "Sparse criterion must not claim SSA is implemented"
                )

    # Applicability validation
    issues.extend(validate_criterion_applicability(item.applicability))

    return tuple(issues)


def validate_evaluation_criteria_schema(
    schema: EvaluationCriteriaSchema,
) -> tuple[str, ...]:
    issues: list[str] = []

    if not schema.schema_id or not schema.schema_id.strip():
        issues.append("schema_id must not be empty")

    if not schema.name or not schema.name.strip():
        issues.append("schema name must not be empty")

    if not schema.criteria:
        issues.append("criteria must not be empty")

    # Duplicate criterion ids
    seen: set[str] = set()
    for item in schema.criteria:
        if item.criterion_id in seen:
            issues.append(f"duplicate criterion_id: {item.criterion_id!r}")
        else:
            seen.add(item.criterion_id)

    # UNKNOWN domain/type
    if schema.domain == EvaluationDomain.UNKNOWN:
        issues.append("UNKNOWN domain schema not allowed — define explicit domain")
    if schema.subject_type == EvaluationSubjectType.UNKNOWN:
        issues.append("UNKNOWN subject_type schema not allowed — define explicit subject_type")

    # Validate each item
    for item in schema.criteria:
        issues.extend(validate_criteria_schema_item(item))

    return tuple(issues)


# ---------------------------------------------------------------------------
# Resolution engine
# ---------------------------------------------------------------------------


def resolve_criteria_for_subject(
    *,
    subject_entry: EvaluationSubjectRegistryEntry,
    registry: EvaluationCriteriaSchemaRegistry,
) -> EvaluationCriteriaSchemaResolution:
    warnings: list[str] = []
    blockers: list[str] = []

    # Subject must be REGISTERED or ACTIVE
    if subject_entry.status not in (
        EvaluationSubjectStatus.REGISTERED,
        EvaluationSubjectStatus.ACTIVE,
    ):
        blockers.append(
            f"subject {subject_entry.subject.subject_id!r} is {subject_entry.status.value}, "
            f"not REGISTERED or ACTIVE — cannot resolve criteria"
        )
        return EvaluationCriteriaSchemaResolution(
            subject_id=subject_entry.subject.subject_id,
            schema_ids=(),
            criteria=(),
            required_criteria=(),
            blocking_criteria=(),
            warnings=tuple(warnings),
            blockers=tuple(blockers),
            summary=f"Blocked: subject status is {subject_entry.status.value}.",
        )

    # Match schemas by domain and subject_type
    matched_schemas: list[EvaluationCriteriaSchema] = []
    for schema in registry.schemas:
        if schema.domain != subject_entry.subject.domain:
            continue
        if schema.subject_type != subject_entry.subject.subject_type:
            continue
        matched_schemas.append(schema)

    if not matched_schemas:
        blockers.append(
            f"no criteria schema found for domain={subject_entry.subject.domain.value}, "
            f"subject_type={subject_entry.subject.subject_type.value}"
        )
        return EvaluationCriteriaSchemaResolution(
            subject_id=subject_entry.subject.subject_id,
            schema_ids=(),
            criteria=(),
            required_criteria=(),
            blocking_criteria=(),
            warnings=tuple(warnings),
            blockers=tuple(blockers),
            summary="Blocked: no matching criteria schema.",
        )

    # Collect criteria from matched schemas
    all_criteria: list[EvaluationCriteriaSchemaItem] = []
    schema_ids: list[str] = []
    seen_criterion_ids: set[str] = set()

    for schema in matched_schemas:
        schema_ids.append(schema.schema_id)
        for item in schema.criteria:
            if item.criterion_id in seen_criterion_ids:
                warnings.append(
                    f"duplicate criterion_id {item.criterion_id!r} across schemas"
                )
                continue
            seen_criterion_ids.add(item.criterion_id)
            all_criteria.append(item)

    required_ids: list[str] = []
    blocking_ids: list[str] = []

    for item in all_criteria:
        if item.requirement_level in (
            EvaluationCriterionRequirementLevel.REQUIRED,
            EvaluationCriterionRequirementLevel.BLOCKING,
        ):
            required_ids.append(item.criterion_id)
        if item.requirement_level == EvaluationCriterionRequirementLevel.BLOCKING:
            blocking_ids.append(item.criterion_id)

    return EvaluationCriteriaSchemaResolution(
        subject_id=subject_entry.subject.subject_id,
        schema_ids=tuple(schema_ids),
        criteria=tuple(all_criteria),
        required_criteria=tuple(required_ids),
        blocking_criteria=tuple(blocking_ids),
        warnings=tuple(warnings),
        blockers=tuple(blockers),
        summary=(
            f"Resolved {len(all_criteria)} criteria from {len(matched_schemas)} schema(s). "
            f"Required: {len(required_ids)}, Blocking: {len(blocking_ids)}."
        ),
    )


def list_criteria_schemas(
    registry: EvaluationCriteriaSchemaRegistry,
    *,
    domain: EvaluationDomain | None = None,
    subject_type: EvaluationSubjectType | None = None,
    kind: EvaluationCriterionKind | None = None,
) -> tuple[EvaluationCriteriaSchema, ...]:
    results: list[EvaluationCriteriaSchema] = []
    for schema in registry.schemas:
        if domain is not None and schema.domain != domain:
            continue
        if subject_type is not None and schema.subject_type != subject_type:
            continue
        if kind is not None:
            # Keep schema if at least one criterion matches kind
            has_kind = any(c.kind == kind for c in schema.criteria)
            if not has_kind:
                continue
        results.append(schema)
    return tuple(results)


# ---------------------------------------------------------------------------
# Default schema builder
# ---------------------------------------------------------------------------


def build_default_criteria_schema_for_subject_type(
    *,
    domain: EvaluationDomain,
    subject_type: EvaluationSubjectType,
) -> EvaluationCriteriaSchema:
    items: list[EvaluationCriteriaSchemaItem] = []

    # Core criteria for all subject types
    items.append(EvaluationCriteriaSchemaItem(
        criterion_id=f"ds_{domain.value.lower()}_{subject_type.value.lower()}_groundedness",
        kind=EvaluationCriterionKind.GROUNDEDNESS,
        name="Groundedness check",
        description="Output or claim must be grounded in evidence",
        severity=EvaluationCriterionSeverity.HIGH,
        requirement_level=EvaluationCriterionRequirementLevel.REQUIRED,
        evidence_requirement=EvaluationCriterionEvidenceRequirement.EVIDENCE_REF,
        applicable_failure_modes=(
            EvaluationFailureMode.MISSING_EVIDENCE,
            EvaluationFailureMode.INSUFFICIENT_EVIDENCE,
        ),
        applicability=EvaluationCriterionApplicability(
            domain=domain,
            subject_type=subject_type,
        ),
        non_goals=("Does not verify capability",),
    ))

    items.append(EvaluationCriteriaSchemaItem(
        criterion_id=f"ds_{domain.value.lower()}_{subject_type.value.lower()}_evidence_quality",
        kind=EvaluationCriterionKind.EVIDENCE_QUALITY,
        name="Evidence quality",
        description="Linked evidence meets quality requirements",
        severity=EvaluationCriterionSeverity.HIGH,
        requirement_level=EvaluationCriterionRequirementLevel.REQUIRED,
        evidence_requirement=EvaluationCriterionEvidenceRequirement.EVIDENCE_REF,
        applicable_failure_modes=(
            EvaluationFailureMode.INSUFFICIENT_EVIDENCE,
            EvaluationFailureMode.CONFLICTED_EVIDENCE,
            EvaluationFailureMode.STALE_EVIDENCE,
        ),
        applicability=EvaluationCriterionApplicability(
            domain=domain,
            subject_type=subject_type,
        ),
        non_goals=("Does not verify capability",),
    ))

    items.append(EvaluationCriteriaSchemaItem(
        criterion_id=f"ds_{domain.value.lower()}_{subject_type.value.lower()}_traceability",
        kind=EvaluationCriterionKind.TRACEABILITY,
        name="Traceability",
        description="Evaluation subject is traceable to registered origin",
        severity=EvaluationCriterionSeverity.MEDIUM,
        requirement_level=EvaluationCriterionRequirementLevel.REQUIRED,
        evidence_requirement=EvaluationCriterionEvidenceRequirement.SOURCE_REF,
        applicable_failure_modes=(EvaluationFailureMode.SCOPE_MISMATCH,),
        applicability=EvaluationCriterionApplicability(
            domain=domain,
            subject_type=subject_type,
        ),
        non_goals=("Does not verify capability",),
    ))

    items.append(EvaluationCriteriaSchemaItem(
        criterion_id=f"ds_{domain.value.lower()}_{subject_type.value.lower()}_policy",
        kind=EvaluationCriterionKind.POLICY_COMPLIANCE,
        name="Policy compliance",
        description="Subject and evaluation comply with governing policies",
        severity=EvaluationCriterionSeverity.CRITICAL,
        requirement_level=EvaluationCriterionRequirementLevel.BLOCKING,
        evidence_requirement=EvaluationCriterionEvidenceRequirement.POLICY_DECISION,
        applicable_failure_modes=(
            EvaluationFailureMode.CRITERION_FAILED,
            EvaluationFailureMode.REQUIRED_CRITERION_FAILED,
        ),
        applicability=EvaluationCriterionApplicability(
            domain=domain,
            subject_type=subject_type,
        ),
        non_goals=("Does not verify capability", "Does not implement Policy Cards (P1.6)"),
    ))

    ts = datetime.now(timezone.utc).isoformat()
    schema_id = "ds_" + hashlib.sha256(
        f"{domain.value}:{subject_type.value}:{ts}".encode()
    ).hexdigest()[:16]

    return EvaluationCriteriaSchema(
        schema_id=schema_id,
        name=f"Default criteria schema for {domain.value}/{subject_type.value}",
        description=f"Default reusable criteria for {domain.value} domain, {subject_type.value} subject type",
        domain=domain,
        subject_type=subject_type,
        criteria=tuple(items),
        version="1.0",
        owner_module="evaluation",
        summary=f"Default schema: {len(items)} criteria (Groundedness, Evidence, Traceability, Policy).",
    )


def build_default_sparse_criteria_schema() -> EvaluationCriteriaSchema:
    items: list[EvaluationCriteriaSchemaItem] = []

    items.append(EvaluationCriteriaSchemaItem(
        criterion_id="ds_sparse_context_quality",
        kind=EvaluationCriterionKind.SPARSE_CONTEXT_QUALITY,
        name="Sparse context quality",
        description="Sparse context selection maintains output quality relative to full-context baseline",
        severity=EvaluationCriterionSeverity.HIGH,
        requirement_level=EvaluationCriterionRequirementLevel.REQUIRED,
        evidence_requirement=EvaluationCriterionEvidenceRequirement.CONTEXT_TRACE,
        applicable_failure_modes=(
            EvaluationFailureMode.INSUFFICIENT_EVIDENCE,
            EvaluationFailureMode.CRITERION_FAILED,
        ),
        applicability=EvaluationCriterionApplicability(
            domain=EvaluationDomain.AUREL_CORE,
            subject_type=EvaluationSubjectType.PROCEDURE,
        ),
        non_goals=(
            "Does not verify capability",
            "Does not implement Sparse Context Compiler",
            "Does not claim SSA/subquadratic model attention is implemented",
        ),
        limitations=(
            "Sparse Context Compiler not implemented in P1.5.4",
            "ASCL execution not available for runtime evaluation",
        ),
    ))

    items.append(EvaluationCriteriaSchemaItem(
        criterion_id="ds_evidence_recall",
        kind=EvaluationCriterionKind.EVIDENCE_RECALL,
        name="Evidence recall",
        description="Key evidence is preserved across sparse context reduction",
        severity=EvaluationCriterionSeverity.HIGH,
        requirement_level=EvaluationCriterionRequirementLevel.REQUIRED,
        evidence_requirement=EvaluationCriterionEvidenceRequirement.RETRIEVAL_TRACE,
        applicable_failure_modes=(
            EvaluationFailureMode.MISSING_EVIDENCE,
            EvaluationFailureMode.INSUFFICIENT_EVIDENCE,
        ),
        applicability=EvaluationCriterionApplicability(
            domain=EvaluationDomain.AUREL_CORE,
            subject_type=EvaluationSubjectType.PROCEDURE,
        ),
        non_goals=(
            "Does not verify capability",
            "Does not implement retrieval router",
            "Does not claim SSA/subquadratic model attention is implemented",
        ),
        limitations=("Retrieval router not implemented in P1.5.4",),
    ))

    items.append(EvaluationCriteriaSchemaItem(
        criterion_id="ds_context_budget_efficiency",
        kind=EvaluationCriterionKind.CONTEXT_BUDGET_EFFICIENCY,
        name="Context budget efficiency",
        description="Sparse context budget is used efficiently without losing critical information",
        severity=EvaluationCriterionSeverity.MEDIUM,
        requirement_level=EvaluationCriterionRequirementLevel.RECOMMENDED,
        evidence_requirement=EvaluationCriterionEvidenceRequirement.CONTEXT_TRACE,
        applicable_failure_modes=(EvaluationFailureMode.INSUFFICIENT_EVIDENCE,),
        applicability=EvaluationCriterionApplicability(
            domain=EvaluationDomain.AUREL_CORE,
            subject_type=EvaluationSubjectType.PROCEDURE,
        ),
        non_goals=(
            "Does not verify capability",
            "Does not implement context budget engine",
        ),
        limitations=("Context budget engine not implemented in P1.5.4",),
    ))

    items.append(EvaluationCriteriaSchemaItem(
        criterion_id="ds_lost_context_risk",
        kind=EvaluationCriterionKind.LOST_CONTEXT_RISK,
        name="Lost context risk",
        description="Risk of losing context is assessed and bounded",
        severity=EvaluationCriterionSeverity.HIGH,
        requirement_level=EvaluationCriterionRequirementLevel.REQUIRED,
        evidence_requirement=EvaluationCriterionEvidenceRequirement.CONTEXT_TRACE,
        applicable_failure_modes=(EvaluationFailureMode.INSUFFICIENT_EVIDENCE,),
        applicability=EvaluationCriterionApplicability(
            domain=EvaluationDomain.AUREL_CORE,
            subject_type=EvaluationSubjectType.PROCEDURE,
        ),
        non_goals=(
            "Does not verify capability",
            "Does not claim lost context risk is solved",
            "Does not implement lost-context risk engine",
            "Does not claim SSA/subquadratic model attention is implemented",
        ),
        limitations=(
            "Lost context risk is an evaluable criterion, not a solved property",
            "Lost-context risk engine not implemented in P1.5.4",
        ),
    ))

    items.append(EvaluationCriteriaSchemaItem(
        criterion_id="ds_governed_context_selection",
        kind=EvaluationCriterionKind.GOVERNED_CONTEXT_SELECTION,
        name="Governed context selection",
        description="Context selection passes governance gates (authority, policy, evidence)",
        severity=EvaluationCriterionSeverity.HIGH,
        requirement_level=EvaluationCriterionRequirementLevel.REQUIRED,
        evidence_requirement=EvaluationCriterionEvidenceRequirement.EVIDENCE_GRAPH,
        applicable_failure_modes=(
            EvaluationFailureMode.CRITERION_FAILED,
            EvaluationFailureMode.REQUIRED_CRITERION_FAILED,
        ),
        applicability=EvaluationCriterionApplicability(
            domain=EvaluationDomain.AUREL_CORE,
            subject_type=EvaluationSubjectType.PROCEDURE,
        ),
        non_goals=(
            "Does not verify capability",
            "Does not implement evidence graph builder",
            "Does not claim SSA/subquadratic model attention is implemented",
        ),
        limitations=("Evidence graph builder not implemented in P1.5.4",),
    ))

    items.append(EvaluationCriteriaSchemaItem(
        criterion_id="ds_authority_aware_retrieval",
        kind=EvaluationCriterionKind.AUTHORITY_AWARE_RETRIEVAL,
        name="Authority-aware retrieval",
        description="Retrieved evidence respects authority constraints and trust boundaries",
        severity=EvaluationCriterionSeverity.MEDIUM,
        requirement_level=EvaluationCriterionRequirementLevel.RECOMMENDED,
        evidence_requirement=EvaluationCriterionEvidenceRequirement.RETRIEVAL_TRACE,
        applicable_failure_modes=(EvaluationFailureMode.INSUFFICIENT_EVIDENCE,),
        applicability=EvaluationCriterionApplicability(
            domain=EvaluationDomain.AUREL_CORE,
            subject_type=EvaluationSubjectType.PROCEDURE,
        ),
        non_goals=(
            "Does not verify capability",
            "Does not implement retrieval router",
            "Does not claim SSA/subquadratic model attention is implemented",
        ),
        limitations=("Retrieval router not implemented in P1.5.4",),
    ))

    ts = datetime.now(timezone.utc).isoformat()
    schema_id = "ds_sparse_" + hashlib.sha256(ts.encode()).hexdigest()[:16]

    return EvaluationCriteriaSchema(
        schema_id=schema_id,
        name="Default sparse criteria schema",
        description="Default reusable sparse context quality criteria for future ASCL evaluation",
        domain=EvaluationDomain.AUREL_CORE,
        subject_type=EvaluationSubjectType.PROCEDURE,
        criteria=tuple(items),
        version="1.0",
        owner_module="evaluation",
        summary=(
            f"Default sparse criteria schema: {len(items)} criteria. "
            "Sparse Context Compiler NOT implemented. "
            "SSA/subquadratic model attention NOT implemented."
        ),
    )


# ---------------------------------------------------------------------------
# Report builder
# ---------------------------------------------------------------------------


def build_p154_criteria_schema_report(
    *,
    schemas_created: int = 0,
    criteria_created: int = 0,
    sparse_criteria_ready: bool = False,
    warnings: tuple[str, ...] = (),
    blockers: tuple[str, ...] = (),
) -> EvaluationCriteriaSchemaReport:
    if blockers:
        status = "BLOCKED"
    elif warnings:
        status = "DEGRADED"
    else:
        status = "READY"

    ts = datetime.now(timezone.utc).isoformat()
    report_id = "p154_" + hashlib.sha256(ts.encode()).hexdigest()[:16]

    return EvaluationCriteriaSchemaReport(
        report_id=report_id,
        status=status,
        summary=(
            f"P1.5.4 Evaluation Criteria Schema {status}. "
            f"Schemas: {schemas_created}, Criteria: {criteria_created}. "
            f"Sparse criteria ready: {sparse_criteria_ready}. "
            f"Next: P1.5.5."
        ),
        schemas_created=schemas_created,
        criteria_created=criteria_created,
        sparse_criteria_ready=sparse_criteria_ready,
        objects_added=(
            "EvaluationCriterionKind",
            "EvaluationCriterionSeverity",
            "EvaluationCriterionRequirementLevel",
            "EvaluationCriterionEvidenceRequirement",
            "EvaluationCriterionApplicability",
            "EvaluationCriteriaSchemaItem",
            "EvaluationCriteriaSchema",
            "EvaluationCriteriaSchemaRegistry",
            "EvaluationCriteriaSchemaResolution",
            "EvaluationCriteriaSchemaReport",
        ),
        invariants=P154_INVARIANTS,
        warnings=warnings,
        blockers=blockers,
        next_module="P1.5.5 — Evaluation Run Envelope",
    )


# ---------------------------------------------------------------------------
# Serialization helpers
# ---------------------------------------------------------------------------


def criterion_applicability_to_dict(
    applicability: EvaluationCriterionApplicability,
) -> dict[str, object]:
    return {
        "domain": applicability.domain.value,
        "subject_type": applicability.subject_type.value,
        "origin_filter": list(applicability.origin_filter),
        "category_filter": list(applicability.category_filter),
        "tag_filter": list(applicability.tag_filter),
    }


def criteria_schema_item_to_dict(
    item: EvaluationCriteriaSchemaItem,
) -> dict[str, object]:
    return {
        "criterion_id": item.criterion_id,
        "kind": item.kind.value,
        "name": item.name,
        "description": item.description,
        "severity": item.severity.value,
        "requirement_level": item.requirement_level.value,
        "evidence_requirement": item.evidence_requirement.value,
        "applicable_failure_modes": [fm.value for fm in item.applicable_failure_modes],
        "applicability": criterion_applicability_to_dict(item.applicability),
        "non_goals": list(item.non_goals),
        "limitations": list(item.limitations),
    }


def criteria_schema_to_dict(
    schema: EvaluationCriteriaSchema,
) -> dict[str, object]:
    return {
        "schema_id": schema.schema_id,
        "name": schema.name,
        "description": schema.description,
        "domain": schema.domain.value,
        "subject_type": schema.subject_type.value,
        "criteria": [criteria_schema_item_to_dict(c) for c in schema.criteria],
        "version": schema.version,
        "owner_module": schema.owner_module,
        "warnings": list(schema.warnings),
        "blockers": list(schema.blockers),
        "summary": schema.summary,
    }


def criteria_schema_registry_to_dict(
    registry: EvaluationCriteriaSchemaRegistry,
) -> dict[str, object]:
    return {
        "registry_id": registry.registry_id,
        "schemas": [criteria_schema_to_dict(s) for s in registry.schemas],
        "warnings": list(registry.warnings),
        "blockers": list(registry.blockers),
        "summary": registry.summary,
    }


def criteria_schema_resolution_to_dict(
    resolution: EvaluationCriteriaSchemaResolution,
) -> dict[str, object]:
    return {
        "subject_id": resolution.subject_id,
        "schema_ids": list(resolution.schema_ids),
        "criteria": [criteria_schema_item_to_dict(c) for c in resolution.criteria],
        "required_criteria": list(resolution.required_criteria),
        "blocking_criteria": list(resolution.blocking_criteria),
        "warnings": list(resolution.warnings),
        "blockers": list(resolution.blockers),
        "summary": resolution.summary,
    }


def criteria_schema_report_to_dict(
    report: EvaluationCriteriaSchemaReport,
) -> dict[str, object]:
    return {
        "report_id": report.report_id,
        "status": report.status,
        "summary": report.summary,
        "schemas_created": report.schemas_created,
        "criteria_created": report.criteria_created,
        "sparse_criteria_ready": report.sparse_criteria_ready,
        "objects_added": list(report.objects_added),
        "invariants": list(report.invariants),
        "warnings": list(report.warnings),
        "blockers": list(report.blockers),
        "next_module": report.next_module,
    }


# ---------------------------------------------------------------------------
# Example helpers
# ---------------------------------------------------------------------------


def example_criteria_schema() -> EvaluationCriteriaSchema:
    """Example criteria schema for Aurel Core agent identity evaluation."""
    return build_default_criteria_schema_for_subject_type(
        domain=EvaluationDomain.AUREL_CORE,
        subject_type=EvaluationSubjectType.AGENT_IDENTITY,
    )


def example_sparse_criteria_schema() -> EvaluationCriteriaSchema:
    """Example sparse criteria schema for future ASCL evaluation."""
    return build_default_sparse_criteria_schema()


__all__ = [
    "EvaluationCriterionKind",
    "EvaluationCriterionSeverity",
    "EvaluationCriterionRequirementLevel",
    "EvaluationCriterionEvidenceRequirement",
    "EvaluationCriterionApplicability",
    "EvaluationCriteriaSchemaItem",
    "EvaluationCriteriaSchema",
    "EvaluationCriteriaSchemaRegistry",
    "EvaluationCriteriaSchemaResolution",
    "EvaluationCriteriaSchemaReport",
    "P154_INVARIANTS",
    "_SPARSE_CRITERION_KINDS",
    "validate_criterion_applicability",
    "validate_criteria_schema_item",
    "validate_evaluation_criteria_schema",
    "resolve_criteria_for_subject",
    "list_criteria_schemas",
    "build_default_criteria_schema_for_subject_type",
    "build_default_sparse_criteria_schema",
    "build_p154_criteria_schema_report",
    "criterion_applicability_to_dict",
    "criteria_schema_item_to_dict",
    "criteria_schema_to_dict",
    "criteria_schema_registry_to_dict",
    "criteria_schema_resolution_to_dict",
    "criteria_schema_report_to_dict",
    "example_criteria_schema",
    "example_sparse_criteria_schema",
]
