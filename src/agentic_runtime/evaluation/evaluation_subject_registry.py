"""P1.5.3 — Evaluation Subject Registry + Sparse Cognition Readiness.

Registry of objects that Aurel is allowed to evaluate.
Core law: No registered subject, no governed evaluation.

Subject registration does NOT verify capability, run evaluation, or implement
Hub runtimes or Sparse Context Compiler.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum

from .evaluation_foundation import (
    EvaluationDomain,
    EvaluationSubject,
    EvaluationSubjectType,
    evaluation_subject_to_dict,
)


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class EvaluationSubjectStatus(str, Enum):
    DRAFT = "DRAFT"
    REGISTERED = "REGISTERED"
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    DEPRECATED = "DEPRECATED"
    REJECTED = "REJECTED"
    INVALID = "INVALID"
    UNKNOWN = "UNKNOWN"


class EvaluationSubjectOrigin(str, Enum):
    AUREL_CORE = "AUREL_CORE"
    IDENTITY_MODULE = "IDENTITY_MODULE"
    EVALUATION_MODULE = "EVALUATION_MODULE"
    CLAIM_BOUNDARY = "CLAIM_BOUNDARY"
    TRUST_EVIDENCE = "TRUST_EVIDENCE"
    CAPABILITY_EVIDENCE = "CAPABILITY_EVIDENCE"
    OPERATOR_PROVIDED = "OPERATOR_PROVIDED"

    SPARSE_CONTEXT = "SPARSE_CONTEXT"

    A_HUB = "A_HUB"
    S_HUB = "S_HUB"
    L_HUB = "L_HUB"
    IDE = "IDE"

    EXTERNAL = "EXTERNAL"
    UNKNOWN = "UNKNOWN"


class EvaluationSubjectCategory(str, Enum):
    STANDARD = "STANDARD"

    SPARSE_CONTEXT_PLAN = "SPARSE_CONTEXT_PLAN"
    CONTEXT_ASSEMBLY_PLAN = "CONTEXT_ASSEMBLY_PLAN"
    RETRIEVAL_TRACE = "RETRIEVAL_TRACE"
    EVIDENCE_GRAPH = "EVIDENCE_GRAPH"
    CONTEXT_BUDGET = "CONTEXT_BUDGET"
    LOST_CONTEXT_RISK_ASSESSMENT = "LOST_CONTEXT_RISK_ASSESSMENT"
    MULTI_HOP_EVIDENCE_TASK = "MULTI_HOP_EVIDENCE_TASK"
    CONTRADICTION_SCAN_TASK = "CONTRADICTION_SCAN_TASK"
    LONG_ARTIFACT_REASONING_TASK = "LONG_ARTIFACT_REASONING_TASK"

    UNKNOWN = "UNKNOWN"


# ---------------------------------------------------------------------------
# Invariants
# ---------------------------------------------------------------------------


P153_INVARIANTS: tuple[str, ...] = (
    "INV-P153-01: No registered subject, no governed evaluation.",
    "INV-P153-02: Subject registration does not verify capability.",
    "INV-P153-03: Subject registration does not run evaluation.",
    "INV-P153-04: ACTIVE subject requires allowed scope or explicit reason.",
    "INV-P153-05: UNKNOWN domain/type cannot silently become ACTIVE.",
    "INV-P153-06: Hub-origin subjects are future-ready references, not runtime implementation claims.",
    "INV-P153-07: Registry is closed-world for status and origin.",
    "INV-P153-08: Duplicate subject ids are invalid.",
    "INV-P153-09: Registry is read-only unless explicit registration function is called.",
    "INV-P153-10: P1.5.4 defines criteria schema next.",
    "INV-P153-SC-01: Sparse context subjects may be registered for evaluation, but P1.5.3 does not implement sparse retrieval or context compilation.",
    "INV-P153-SC-02: No governed evaluation may run on an unregistered Sparse Context subject.",
    "INV-P153-SC-03: Sparse Context evaluation subjects must carry source/evidence refs or remain non-ACTIVE with warning/limitation.",
    "INV-P153-SC-04: Lost context risk is an evaluable subject, not a solved problem.",
    "INV-P153-SC-05: Sparse context registration does not prove evidence recall or reasoning quality.",
    "INV-P153-SC-06: P1.5.3 must not claim SSA/subquadratic model attention is implemented.",
)


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class EvaluationSubjectRegistryEntry:
    entry_id: str
    subject: EvaluationSubject

    status: EvaluationSubjectStatus
    origin: EvaluationSubjectOrigin

    owner_module: str | None = None
    registered_by: str | None = None
    registered_at: str | None = None

    allowed_scope_ids: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()
    source_refs: tuple[str, ...] = ()

    categories: tuple[EvaluationSubjectCategory, ...] = ()
    tags: tuple[str, ...] = ()

    limitations: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    blockers: tuple[str, ...] = ()

    summary: str = ""


@dataclass(frozen=True)
class EvaluationSubjectRegistrationRequest:
    request_id: str
    subject: EvaluationSubject
    origin: EvaluationSubjectOrigin

    requested_by: str | None = None
    owner_module: str | None = None
    allowed_scope_ids: tuple[str, ...] = ()

    evidence_refs: tuple[str, ...] = ()
    source_refs: tuple[str, ...] = ()

    categories: tuple[str, ...] = ()
    tags: tuple[str, ...] = ()

    reason: str = ""


@dataclass(frozen=True)
class EvaluationSubjectRegistrationDecision:
    request_id: str
    accepted: bool
    status: EvaluationSubjectStatus

    entry: EvaluationSubjectRegistryEntry | None = None

    blockers: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    summary: str = ""


@dataclass(frozen=True)
class EvaluationSubjectRegistry:
    registry_id: str
    entries: tuple[EvaluationSubjectRegistryEntry, ...]

    warnings: tuple[str, ...] = ()
    blockers: tuple[str, ...] = ()
    summary: str = ""


@dataclass(frozen=True)
class EvaluationSubjectRegistryReport:
    report_id: str
    status: str
    summary: str

    entries_registered: int
    entries_rejected: int

    objects_added: tuple[str, ...]
    invariants: tuple[str, ...]
    warnings: tuple[str, ...]
    blockers: tuple[str, ...]

    sparse_cognition_readiness: str
    next_module: str


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

_HUB_ORIGINS: frozenset[EvaluationSubjectOrigin] = frozenset({
    EvaluationSubjectOrigin.A_HUB,
    EvaluationSubjectOrigin.S_HUB,
    EvaluationSubjectOrigin.L_HUB,
    EvaluationSubjectOrigin.IDE,
})

_SPARSE_CATEGORIES: frozenset[EvaluationSubjectCategory] = frozenset({
    EvaluationSubjectCategory.SPARSE_CONTEXT_PLAN,
    EvaluationSubjectCategory.CONTEXT_ASSEMBLY_PLAN,
    EvaluationSubjectCategory.RETRIEVAL_TRACE,
    EvaluationSubjectCategory.EVIDENCE_GRAPH,
    EvaluationSubjectCategory.CONTEXT_BUDGET,
    EvaluationSubjectCategory.LOST_CONTEXT_RISK_ASSESSMENT,
    EvaluationSubjectCategory.MULTI_HOP_EVIDENCE_TASK,
    EvaluationSubjectCategory.CONTRADICTION_SCAN_TASK,
    EvaluationSubjectCategory.LONG_ARTIFACT_REASONING_TASK,
})


def _has_sparse_category(entry: EvaluationSubjectRegistryEntry) -> bool:
    return bool(set(entry.categories) & _SPARSE_CATEGORIES)


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def validate_evaluation_subject_registry_entry(
    entry: EvaluationSubjectRegistryEntry,
) -> tuple[str, ...]:
    issues: list[str] = []

    if not entry.entry_id or not entry.entry_id.strip():
        issues.append("entry_id must not be empty")

    if not entry.subject.subject_id or not entry.subject.subject_id.strip():
        issues.append("subject.subject_id must not be empty")

    # ACTIVE requires allowed scope or explicit reason
    if entry.status == EvaluationSubjectStatus.ACTIVE:
        if not entry.allowed_scope_ids:
            if not entry.summary:
                issues.append(
                    "ACTIVE status requires at least one allowed scope or explicit reason in summary"
                )
        # SPARSE_CONTEXT ACTIVE requires evidence/source refs or limitation
        if entry.origin == EvaluationSubjectOrigin.SPARSE_CONTEXT:
            if not entry.evidence_refs and not entry.source_refs and not entry.limitations:
                issues.append(
                    "ACTIVE SPARSE_CONTEXT subject requires evidence_refs, source_refs, or explicit limitations"
                )
        # Hub origin ACTIVE requires evidence/source refs or limitation
        if entry.origin in _HUB_ORIGINS:
            if not entry.evidence_refs and not entry.source_refs and not entry.limitations:
                issues.append(
                    f"ACTIVE Hub-origin ({entry.origin.value}) subject requires evidence_refs, source_refs, or explicit limitations"
                )

    # REJECTED requires blockers
    if entry.status == EvaluationSubjectStatus.REJECTED and not entry.blockers:
        issues.append("REJECTED status requires at least one blocker")

    # INVALID requires blockers
    if entry.status == EvaluationSubjectStatus.INVALID and not entry.blockers:
        issues.append("INVALID status requires at least one blocker")

    # UNKNOWN origin/status requires warning or blocker
    if entry.origin == EvaluationSubjectOrigin.UNKNOWN:
        if not entry.warnings and not entry.blockers:
            issues.append("UNKNOWN origin requires warning or blocker")

    if entry.status == EvaluationSubjectStatus.UNKNOWN:
        if not entry.warnings and not entry.blockers:
            issues.append("UNKNOWN status requires warning or blocker")

    # UNKNOWN domain/type cannot be ACTIVE
    if entry.status == EvaluationSubjectStatus.ACTIVE:
        if entry.subject.domain == EvaluationDomain.UNKNOWN:
            issues.append("ACTIVE subject cannot have UNKNOWN domain")
        if entry.subject.subject_type == EvaluationSubjectType.UNKNOWN:
            issues.append("ACTIVE subject cannot have UNKNOWN subject_type")

    return tuple(issues)


def validate_evaluation_subject_registration_request(
    request: EvaluationSubjectRegistrationRequest,
) -> tuple[str, ...]:
    issues: list[str] = []

    if not request.request_id or not request.request_id.strip():
        issues.append("request_id must not be empty")

    if not request.subject.subject_id or not request.subject.subject_id.strip():
        issues.append("subject.subject_id must not be empty")

    if not request.reason or not request.reason.strip():
        issues.append("reason must not be empty")

    # UNKNOWN domain always emits a validation warning
    if request.subject.domain == EvaluationDomain.UNKNOWN:
        issues.append(
            "UNKNOWN domain — registration requires explicit evidence and will not be ACTIVE"
        )

    # UNKNOWN subject type always emits a validation warning
    if request.subject.subject_type == EvaluationSubjectType.UNKNOWN:
        issues.append(
            "UNKNOWN subject_type — registration requires explicit evidence and will not be ACTIVE"
        )

    # Hub origin without source/evidence refs -> warning (but still allows registration)
    if request.origin in _HUB_ORIGINS:
        if not request.evidence_refs and not request.source_refs:
            issues.append(
                f"Hub origin ({request.origin.value}) registered without source/evidence refs — "
                "subject will not be ACTIVE; future Hub runtime not implemented"
            )

    # Sparse context origin without source/evidence refs -> warning
    if request.origin == EvaluationSubjectOrigin.SPARSE_CONTEXT:
        if not request.evidence_refs and not request.source_refs:
            issues.append(
                "SPARSE_CONTEXT origin registered without source/evidence refs — "
                "subject will not be ACTIVE; Sparse Context Compiler not implemented"
            )

    return tuple(issues)


def validate_evaluation_subject_registry(
    registry: EvaluationSubjectRegistry,
) -> tuple[str, ...]:
    issues: list[str] = []

    if not registry.registry_id or not registry.registry_id.strip():
        issues.append("registry_id must not be empty")

    entry_ids: set[str] = set()
    subject_ids: set[str] = set()

    for entry in registry.entries:
        # duplicate entry ids
        if entry.entry_id in entry_ids:
            issues.append(f"duplicate entry_id: {entry.entry_id!r}")
        else:
            entry_ids.add(entry.entry_id)

        # duplicate subject ids
        sid = entry.subject.subject_id
        if sid in subject_ids:
            issues.append(f"duplicate subject_id: {sid!r}")
        else:
            subject_ids.add(sid)

        # validate individual entry
        entry_issues = validate_evaluation_subject_registry_entry(entry)
        issues.extend(entry_issues)

    # ACTIVE entries with unresolved blockers
    for entry in registry.entries:
        if entry.status == EvaluationSubjectStatus.ACTIVE and entry.blockers:
            issues.append(
                f"ACTIVE entry {entry.entry_id!r} has unresolved blockers: {entry.blockers}"
            )

    return tuple(issues)


# ---------------------------------------------------------------------------
# Registration engine
# ---------------------------------------------------------------------------


def register_evaluation_subject(
    request: EvaluationSubjectRegistrationRequest,
) -> EvaluationSubjectRegistrationDecision:
    # Run validation first
    req_issues = validate_evaluation_subject_registration_request(request)

    # Collect blockers (issues that are strict blockers) vs warnings
    blockers: list[str] = []
    warnings: list[str] = []

    for issue in req_issues:
        # Issues about empty fields are blockers
        if (
            "must not be empty" in issue
            or "UNKNOWN domain requires" in issue
            or "UNKNOWN subject_type requires" in issue
        ):
            blockers.append(issue)
        else:
            # Hub/sparse-context without refs are warnings, not blockers
            warnings.append(issue)

    # UNKNOWN domain/type blocks acceptance
    if request.subject.domain == EvaluationDomain.UNKNOWN:
        blockers.append("UNKNOWN domain — registration rejected")
    if request.subject.subject_type == EvaluationSubjectType.UNKNOWN:
        blockers.append("UNKNOWN subject_type — registration rejected")

    if blockers:
        return EvaluationSubjectRegistrationDecision(
            request_id=request.request_id,
            accepted=False,
            status=EvaluationSubjectStatus.REJECTED,
            blockers=tuple(blockers),
            warnings=tuple(warnings),
            summary=f"Registration rejected: {len(blockers)} blocker(s). {len(warnings)} warning(s).",
        )

    # Determine status
    # Default: REGISTERED, not ACTIVE (P1.5.4 criteria schema not yet implemented)
    status = EvaluationSubjectStatus.REGISTERED

    # Hub/sparse-context without refs stays DRAFT with warning
    if request.origin in _HUB_ORIGINS and not request.evidence_refs and not request.source_refs:
        status = EvaluationSubjectStatus.DRAFT
    if request.origin == EvaluationSubjectOrigin.SPARSE_CONTEXT and not request.evidence_refs and not request.source_refs:
        status = EvaluationSubjectStatus.DRAFT

    # Convert categories string list to enum
    categories: tuple[EvaluationSubjectCategory, ...] = ()
    for cat_str in request.categories:
        try:
            categories += (EvaluationSubjectCategory(cat_str),)
        except ValueError:
            warnings.append(f"Unknown category ignored: {cat_str!r}")

    entry_warnings = list(warnings)
    if status == EvaluationSubjectStatus.DRAFT:
        entry_warnings.append("Subject is DRAFT — not eligible for evaluation yet")

    ts = datetime.now(timezone.utc).isoformat()
    entry_id = "entry_" + hashlib.sha256(
        f"{request.request_id}:{request.subject.subject_id}:{ts}".encode()
    ).hexdigest()[:16]

    entry = EvaluationSubjectRegistryEntry(
        entry_id=entry_id,
        subject=request.subject,
        status=status,
        origin=request.origin,
        owner_module=request.owner_module,
        registered_by=request.requested_by,
        registered_at=ts,
        allowed_scope_ids=request.allowed_scope_ids,
        evidence_refs=request.evidence_refs,
        source_refs=request.source_refs,
        categories=categories,
        tags=request.tags,
        warnings=tuple(entry_warnings),
    )

    return EvaluationSubjectRegistrationDecision(
        request_id=request.request_id,
        accepted=True,
        status=status,
        entry=entry,
        warnings=tuple(warnings),
        summary=f"Subject registered as {status.value}. Registration does not run evaluation or verify capability.",
    )


# ---------------------------------------------------------------------------
# Registry engine
# ---------------------------------------------------------------------------


def resolve_evaluation_subject(
    registry: EvaluationSubjectRegistry,
    subject_id: str,
) -> EvaluationSubjectRegistryEntry | None:
    if not subject_id or not subject_id.strip():
        return None
    for entry in registry.entries:
        if entry.subject.subject_id == subject_id.strip():
            return entry
    return None


def list_evaluation_subjects(
    registry: EvaluationSubjectRegistry,
    *,
    domain: EvaluationDomain | None = None,
    subject_type: EvaluationSubjectType | None = None,
    status: EvaluationSubjectStatus | None = None,
    origin: EvaluationSubjectOrigin | None = None,
    category: EvaluationSubjectCategory | None = None,
    tag: str | None = None,
) -> tuple[EvaluationSubjectRegistryEntry, ...]:
    results: list[EvaluationSubjectRegistryEntry] = []
    for entry in registry.entries:
        if domain is not None and entry.subject.domain != domain:
            continue
        if subject_type is not None and entry.subject.subject_type != subject_type:
            continue
        if status is not None and entry.status != status:
            continue
        if origin is not None and entry.origin != origin:
            continue
        if category is not None and category not in entry.categories:
            continue
        if tag is not None and tag not in entry.tags:
            continue
        results.append(entry)
    return tuple(results)


# ---------------------------------------------------------------------------
# Report builder
# ---------------------------------------------------------------------------


def build_p153_subject_registry_report(
    *,
    entries_registered: int = 0,
    entries_rejected: int = 0,
    warnings: tuple[str, ...] = (),
    blockers: tuple[str, ...] = (),
) -> EvaluationSubjectRegistryReport:
    if blockers:
        status = "BLOCKED"
    elif warnings:
        status = "DEGRADED"
    else:
        status = "READY"

    ts = datetime.now(timezone.utc).isoformat()
    report_id = "p153_" + hashlib.sha256(ts.encode()).hexdigest()[:16]

    return EvaluationSubjectRegistryReport(
        report_id=report_id,
        status=status,
        summary=(
            f"P1.5.3 Evaluation Subject Registry {status}. "
            f"Registered: {entries_registered}, Rejected: {entries_rejected}. "
            f"Next: P1.5.4."
        ),
        entries_registered=entries_registered,
        entries_rejected=entries_rejected,
        objects_added=(
            "EvaluationSubjectStatus",
            "EvaluationSubjectOrigin",
            "EvaluationSubjectCategory",
            "EvaluationSubjectRegistryEntry",
            "EvaluationSubjectRegistrationRequest",
            "EvaluationSubjectRegistrationDecision",
            "EvaluationSubjectRegistry",
            "EvaluationSubjectRegistryReport",
        ),
        invariants=P153_INVARIANTS,
        warnings=warnings,
        blockers=blockers,
        sparse_cognition_readiness="REGISTERABLE_SUBJECTS_ONLY",
        next_module="P1.5.4 — Evaluation Criteria Schema",
    )


# ---------------------------------------------------------------------------
# Serialization helpers
# ---------------------------------------------------------------------------


def evaluation_subject_registry_entry_to_dict(
    entry: EvaluationSubjectRegistryEntry,
) -> dict[str, object]:
    return {
        "entry_id": entry.entry_id,
        "subject": evaluation_subject_to_dict(entry.subject),
        "status": entry.status.value,
        "origin": entry.origin.value,
        "owner_module": entry.owner_module,
        "registered_by": entry.registered_by,
        "registered_at": entry.registered_at,
        "allowed_scope_ids": list(entry.allowed_scope_ids),
        "evidence_refs": list(entry.evidence_refs),
        "source_refs": list(entry.source_refs),
        "categories": [c.value for c in entry.categories],
        "tags": list(entry.tags),
        "limitations": list(entry.limitations),
        "warnings": list(entry.warnings),
        "blockers": list(entry.blockers),
        "summary": entry.summary,
    }


def evaluation_subject_registration_request_to_dict(
    request: EvaluationSubjectRegistrationRequest,
) -> dict[str, object]:
    return {
        "request_id": request.request_id,
        "subject": evaluation_subject_to_dict(request.subject),
        "origin": request.origin.value,
        "requested_by": request.requested_by,
        "owner_module": request.owner_module,
        "allowed_scope_ids": list(request.allowed_scope_ids),
        "evidence_refs": list(request.evidence_refs),
        "source_refs": list(request.source_refs),
        "categories": list(request.categories),
        "tags": list(request.tags),
        "reason": request.reason,
    }


def evaluation_subject_registration_decision_to_dict(
    decision: EvaluationSubjectRegistrationDecision,
) -> dict[str, object]:
    return {
        "request_id": decision.request_id,
        "accepted": decision.accepted,
        "status": decision.status.value,
        "entry": (
            evaluation_subject_registry_entry_to_dict(decision.entry)
            if decision.entry
            else None
        ),
        "blockers": list(decision.blockers),
        "warnings": list(decision.warnings),
        "summary": decision.summary,
    }


def evaluation_subject_registry_to_dict(
    registry: EvaluationSubjectRegistry,
) -> dict[str, object]:
    return {
        "registry_id": registry.registry_id,
        "entries": [
            evaluation_subject_registry_entry_to_dict(e) for e in registry.entries
        ],
        "warnings": list(registry.warnings),
        "blockers": list(registry.blockers),
        "summary": registry.summary,
    }


def evaluation_subject_registry_report_to_dict(
    report: EvaluationSubjectRegistryReport,
) -> dict[str, object]:
    return {
        "report_id": report.report_id,
        "status": report.status,
        "summary": report.summary,
        "entries_registered": report.entries_registered,
        "entries_rejected": report.entries_rejected,
        "objects_added": list(report.objects_added),
        "invariants": list(report.invariants),
        "warnings": list(report.warnings),
        "blockers": list(report.blockers),
        "sparse_cognition_readiness": report.sparse_cognition_readiness,
        "next_module": report.next_module,
    }


# ---------------------------------------------------------------------------
# Example helpers (for CLI and tests)
# ---------------------------------------------------------------------------


def example_registered_core_subject() -> EvaluationSubjectRegistryEntry:
    from .evaluation_foundation import build_evaluation_subject

    subj = build_evaluation_subject(
        subject_id="subj_aurel_core_governance",
        subject_type=EvaluationSubjectType.AGENT_IDENTITY,
        domain=EvaluationDomain.AUREL_CORE,
        title="Aurel Core Governance Evaluation Subject",
        evidence_refs=("ref_gov_001",),
    )
    return EvaluationSubjectRegistryEntry(
        entry_id="entry_example_core",
        subject=subj,
        status=EvaluationSubjectStatus.REGISTERED,
        origin=EvaluationSubjectOrigin.EVALUATION_MODULE,
        owner_module="evaluation",
        registered_by="p153_module_init",
        registered_at=datetime.now(timezone.utc).isoformat(),
        allowed_scope_ids=("scope_aurel_core",),
        evidence_refs=("ref_gov_001",),
        categories=(EvaluationSubjectCategory.STANDARD,),
        summary="Example registered Aurel Core governance subject.",
    )


def example_registered_sparse_context_subject() -> EvaluationSubjectRegistryEntry:
    from .evaluation_foundation import build_evaluation_subject

    subj = build_evaluation_subject(
        subject_id="subj_sparse_context_budget_001",
        subject_type=EvaluationSubjectType.PROCEDURE,
        domain=EvaluationDomain.AUREL_CORE,
        title="Sparse Context Budget Evaluation Subject (future-ready)",
        source_ref="ref_sc_budget_001",
    )
    return EvaluationSubjectRegistryEntry(
        entry_id="entry_example_sc_budget",
        subject=subj,
        status=EvaluationSubjectStatus.REGISTERED,
        origin=EvaluationSubjectOrigin.SPARSE_CONTEXT,
        owner_module="evaluation",
        registered_by="p153_module_init",
        registered_at=datetime.now(timezone.utc).isoformat(),
        allowed_scope_ids=(),
        source_refs=("ref_sc_budget_001",),
        categories=(EvaluationSubjectCategory.CONTEXT_BUDGET,),
        tags=("sparse_cognition", "future_ready", "ascl_v0_1"),
        limitations=(
            "Sparse Context Compiler not implemented in P1.5.3",
            "Context budget evaluation not yet runtime-validated",
        ),
        summary=(
            "Future-ready sparse context budget evaluation subject. "
            "Does not claim SSA or subquadratic model attention is implemented."
        ),
    )


def example_subject_registry() -> EvaluationSubjectRegistry:
    entry1 = example_registered_core_subject()
    entry2 = example_registered_sparse_context_subject()
    return EvaluationSubjectRegistry(
        registry_id="registry_p153_example",
        entries=(entry1, entry2),
        summary="Example P1.5.3 subject registry with core and sparse context subjects.",
    )


__all__ = [
    "EvaluationSubjectStatus",
    "EvaluationSubjectOrigin",
    "EvaluationSubjectCategory",
    "EvaluationSubjectRegistryEntry",
    "EvaluationSubjectRegistrationRequest",
    "EvaluationSubjectRegistrationDecision",
    "EvaluationSubjectRegistry",
    "EvaluationSubjectRegistryReport",
    "P153_INVARIANTS",
    "_HUB_ORIGINS",
    "_SPARSE_CATEGORIES",
    "validate_evaluation_subject_registry_entry",
    "validate_evaluation_subject_registration_request",
    "validate_evaluation_subject_registry",
    "register_evaluation_subject",
    "resolve_evaluation_subject",
    "list_evaluation_subjects",
    "build_p153_subject_registry_report",
    "evaluation_subject_registry_entry_to_dict",
    "evaluation_subject_registration_request_to_dict",
    "evaluation_subject_registration_decision_to_dict",
    "evaluation_subject_registry_to_dict",
    "evaluation_subject_registry_report_to_dict",
    "example_registered_core_subject",
    "example_registered_sparse_context_subject",
    "example_subject_registry",
]
