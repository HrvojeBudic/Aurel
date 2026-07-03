"""P3-FLOW-L truth-label audit / unavailable ledger / boundary exit audit.

Every audit here is read-only bookkeeping over already-constructed objects:
a truth-label audit is not Trace verification, an unavailable ledger is not
implementation, and a boundary exit audit is not enforcement. Nothing is
mutated, punished, repaired, or certified.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .errors import AurelFlowErrorCode, AurelFlowValidationError
from .types import FlowTruthLabel, _CanonicalMixin, stable_hash

TRUTH_LABEL_AUDIT_FINDING_VERSION = "p3_truth_label_audit_finding.v1"
TRUTH_LABEL_AUDIT_READ_MODEL_VERSION = "p3_truth_label_audit_read_model.v1"
UNAVAILABLE_SYSTEM_ENTRY_VERSION = "p3_unavailable_system_entry.v1"
UNAVAILABLE_SYSTEMS_LEDGER_VERSION = "p3_unavailable_systems_ledger.v1"
BOUNDARY_EXIT_FINDING_VERSION = "p3_boundary_exit_finding.v1"
BOUNDARY_EXIT_AUDIT_READ_MODEL_VERSION = "p3_boundary_exit_read_model.v1"

P3_AUDIT_UNAVAILABLE_REASON = (
    "P3-FLOW-L audits are read-only seal bookkeeping: a truth-label audit "
    "is not Trace verification, an unavailable ledger implements nothing, "
    "and a boundary exit audit enforces nothing"
)


def _forbid_true(obj: object, *boundary_fields: str) -> None:
    for boundary_field in boundary_fields:
        if getattr(obj, boundary_field):
            raise AurelFlowValidationError(
                f"{type(obj).__name__}.{boundary_field} must remain False",
                code=AurelFlowErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                field=boundary_field,
            )


def _forbid_false(obj: object, *boundary_fields: str) -> None:
    for boundary_field in boundary_fields:
        if not getattr(obj, boundary_field):
            raise AurelFlowValidationError(
                f"{type(obj).__name__}.{boundary_field} must remain True",
                code=AurelFlowErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                field=boundary_field,
            )


class P3AuditStatus(str, Enum):
    """Shared audit vocabulary. There is no ENFORCED/REPAIRED member."""

    PASS = "PASS"
    FAIL = "FAIL"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class TruthLabelAuditCategory(str, Enum):
    NO_FAKE_LIVE = "NO_FAKE_LIVE"
    NO_FAKE_TRACE_VERIFIED = "NO_FAKE_TRACE_VERIFIED"
    NO_FAKE_PRODUCTION_READY = "NO_FAKE_PRODUCTION_READY"
    DEV_FIXTURE_EXPLICIT = "DEV_FIXTURE_EXPLICIT"
    SIMULATED_EXPLICIT = "SIMULATED_EXPLICIT"
    UNAVAILABLE_EXPLICIT = "UNAVAILABLE_EXPLICIT"
    ERROR_EXPLICIT = "ERROR_EXPLICIT"
    CONTRACT_ONLY_EXPLICIT = "CONTRACT_ONLY_EXPLICIT"
    READ_MODEL_ONLY_EXPLICIT = "READ_MODEL_ONLY_EXPLICIT"
    CANDIDATE_ONLY_EXPLICIT = "CANDIDATE_ONLY_EXPLICIT"
    ADVISORY_EXPLICIT = "ADVISORY_EXPLICIT"


@dataclass(frozen=True)
class TruthLabelAuditFinding(_CanonicalMixin):
    """One truth-label observation. A finding is not repair."""

    finding_id: str
    contract_version: str
    category: TruthLabelAuditCategory
    status: P3AuditStatus
    detail: str
    truth_label: FlowTruthLabel
    unavailable_reason: str = P3_AUDIT_UNAVAILABLE_REASON
    repair_performed: bool = False

    def __post_init__(self) -> None:
        _forbid_true(self, "repair_performed")


@dataclass(frozen=True)
class TruthLabelAuditReadModel(_CanonicalMixin):
    """Deterministic truth-label audit result. Not Trace verification."""

    read_model_id: str
    contract_version: str
    subject_type_names: tuple[str, ...]
    findings: tuple[TruthLabelAuditFinding, ...]
    failing_category_values: tuple[str, ...]
    all_applicable_passed: bool
    truth_label: FlowTruthLabel
    unavailable_reason: str = P3_AUDIT_UNAVAILABLE_REASON
    live_claim_allowed: bool = False
    trace_verified_claim_allowed: bool = False
    production_ready_claim_allowed: bool = False

    def __post_init__(self) -> None:
        _forbid_true(
            self,
            "live_claim_allowed",
            "trace_verified_claim_allowed",
            "production_ready_claim_allowed",
        )


def _truth_label_value(subject: object) -> str | None:
    label = getattr(subject, "truth_label", None)
    if label is None:
        return None
    return getattr(label, "value", str(label))


_FORBIDDEN_CLAIM_ATTRS: dict[TruthLabelAuditCategory, tuple[str, ...]] = {
    TruthLabelAuditCategory.NO_FAKE_LIVE: (
        "live_claimed",
        "live_path_available",
    ),
    TruthLabelAuditCategory.NO_FAKE_TRACE_VERIFIED: (
        "trace_verified",
        "trace_verified_claimed",
    ),
    TruthLabelAuditCategory.NO_FAKE_PRODUCTION_READY: (
        "production_ready",
        "release_approved",
    ),
}

_FORBIDDEN_CLAIM_LABELS: dict[TruthLabelAuditCategory, str] = {
    TruthLabelAuditCategory.NO_FAKE_LIVE: FlowTruthLabel.LIVE.value,
    TruthLabelAuditCategory.NO_FAKE_TRACE_VERIFIED: (
        FlowTruthLabel.TRACE_VERIFIED.value
    ),
}

_EXPLICIT_LABEL_CATEGORIES: dict[TruthLabelAuditCategory, str] = {
    TruthLabelAuditCategory.DEV_FIXTURE_EXPLICIT: (
        FlowTruthLabel.DEV_FIXTURE.value
    ),
    TruthLabelAuditCategory.SIMULATED_EXPLICIT: (
        FlowTruthLabel.SIMULATED.value
    ),
    TruthLabelAuditCategory.UNAVAILABLE_EXPLICIT: (
        FlowTruthLabel.UNAVAILABLE.value
    ),
    TruthLabelAuditCategory.ERROR_EXPLICIT: FlowTruthLabel.ERROR.value,
    TruthLabelAuditCategory.CONTRACT_ONLY_EXPLICIT: (
        FlowTruthLabel.CONTRACT_ONLY.value
    ),
    TruthLabelAuditCategory.READ_MODEL_ONLY_EXPLICIT: (
        FlowTruthLabel.READ_MODEL_ONLY.value
    ),
}

_EXPLICIT_FLAG_CATEGORIES: dict[TruthLabelAuditCategory, str] = {
    TruthLabelAuditCategory.CANDIDATE_ONLY_EXPLICIT: "candidate_only",
    TruthLabelAuditCategory.ADVISORY_EXPLICIT: "advisory_only",
}


def _truth_finding(
    category: TruthLabelAuditCategory,
    status: P3AuditStatus,
    detail: str,
) -> TruthLabelAuditFinding:
    payload = {
        "contract_version": TRUTH_LABEL_AUDIT_FINDING_VERSION,
        "category": category.value,
        "status": status.value,
        "detail": detail,
    }
    return TruthLabelAuditFinding(
        finding_id="flltf-" + stable_hash(payload)[:16],
        contract_version=TRUTH_LABEL_AUDIT_FINDING_VERSION,
        category=category,
        status=status,
        detail=detail,
        truth_label=FlowTruthLabel.READ_MODEL_ONLY,
    )


def audit_truth_labels(
    subjects: tuple[object, ...],
) -> TruthLabelAuditReadModel:
    """Deterministic read-only sweep over subject truth posture.

    A LIVE or TRACE_VERIFIED label, or a True production/live/trace claim
    boolean, fails its category; explicit-label categories PASS when the
    label appears and are honestly NOT_APPLICABLE when it does not.
    """

    findings: list[TruthLabelAuditFinding] = []
    for category in TruthLabelAuditCategory:
        offenders: list[str] = []
        if category in _FORBIDDEN_CLAIM_ATTRS:
            forbidden_label = _FORBIDDEN_CLAIM_LABELS.get(category)
            for subject in subjects:
                reasons: list[str] = []
                if (
                    forbidden_label is not None
                    and _truth_label_value(subject) == forbidden_label
                ):
                    reasons.append(f"truth_label={forbidden_label}")
                for attr in _FORBIDDEN_CLAIM_ATTRS[category]:
                    if getattr(subject, attr, False):
                        reasons.append(f"{attr}=True")
                if reasons:
                    offenders.append(
                        f"{type(subject).__name__}({', '.join(reasons)})"
                    )
            if offenders:
                findings.append(
                    _truth_finding(
                        category,
                        P3AuditStatus.FAIL,
                        "forbidden claim on " + "; ".join(sorted(offenders)),
                    )
                )
            else:
                findings.append(
                    _truth_finding(
                        category,
                        P3AuditStatus.PASS,
                        "no subject carries this forbidden claim",
                    )
                )
        elif category in _EXPLICIT_LABEL_CATEGORIES:
            wanted = _EXPLICIT_LABEL_CATEGORIES[category]
            if any(
                _truth_label_value(subject) == wanted for subject in subjects
            ):
                findings.append(
                    _truth_finding(
                        category,
                        P3AuditStatus.PASS,
                        f"the {wanted} label is carried explicitly",
                    )
                )
            else:
                findings.append(
                    _truth_finding(
                        category,
                        P3AuditStatus.NOT_APPLICABLE,
                        f"no audited subject uses the {wanted} label",
                    )
                )
        else:
            flag = _EXPLICIT_FLAG_CATEGORIES[category]
            flagged = [
                subject
                for subject in subjects
                if hasattr(subject, flag)
            ]
            if not flagged:
                findings.append(
                    _truth_finding(
                        category,
                        P3AuditStatus.NOT_APPLICABLE,
                        f"no audited subject declares {flag}",
                    )
                )
            elif all(getattr(subject, flag) for subject in flagged):
                findings.append(
                    _truth_finding(
                        category,
                        P3AuditStatus.PASS,
                        f"every subject declaring {flag} keeps it True",
                    )
                )
            else:
                offenders = sorted(
                    type(subject).__name__
                    for subject in flagged
                    if not getattr(subject, flag)
                )
                findings.append(
                    _truth_finding(
                        category,
                        P3AuditStatus.FAIL,
                        f"{flag} is declared but False on "
                        + "; ".join(offenders),
                    )
                )
    failing = tuple(
        finding.category.value
        for finding in findings
        if finding.status is P3AuditStatus.FAIL
    )
    subject_type_names = tuple(
        sorted({type(subject).__name__ for subject in subjects})
    )
    payload = {
        "contract_version": TRUTH_LABEL_AUDIT_READ_MODEL_VERSION,
        "subject_type_names": subject_type_names,
        "finding_ids": tuple(
            sorted(finding.finding_id for finding in findings)
        ),
    }
    return TruthLabelAuditReadModel(
        read_model_id="flltr-" + stable_hash(payload)[:16],
        contract_version=TRUTH_LABEL_AUDIT_READ_MODEL_VERSION,
        subject_type_names=subject_type_names,
        findings=tuple(findings),
        failing_category_values=failing,
        all_applicable_passed=not failing,
        truth_label=FlowTruthLabel.READ_MODEL_ONLY,
    )


class UnavailableSystem(str, Enum):
    """Closed-world ledger of systems P3 deliberately does not have."""

    RUNTIME_SUBMIT_BRIDGE = "RUNTIME_SUBMIT_BRIDGE"
    P4_EXECUTION = "P4_EXECUTION"
    P5_TRACE_VERIFICATION = "P5_TRACE_VERIFICATION"
    P9_CUSTOS_ENFORCEMENT = "P9_CUSTOS_ENFORCEMENT"
    PRODUCTION_LIVE_PATH = "PRODUCTION_LIVE_PATH"
    SAFE_VERIFIED_SANDBOX = "SAFE_VERIFIED_SANDBOX"
    PERSISTENCE = "PERSISTENCE"
    REAL_WORKER_DISPATCH = "REAL_WORKER_DISPATCH"
    REAL_SERVICE_RUNTIME = "REAL_SERVICE_RUNTIME"
    NETWORK_TRANSPORT = "NETWORK_TRANSPORT"
    MODEL_INVOCATION = "MODEL_INVOCATION"
    TOOL_INVOCATION = "TOOL_INVOCATION"
    SANDBOX_EXECUTION = "SANDBOX_EXECUTION"
    MEMORY_WRITE_PATH = "MEMORY_WRITE_PATH"
    POLICY_MUTATION_PATH = "POLICY_MUTATION_PATH"
    IDENTITY_MUTATION_PATH = "IDENTITY_MUTATION_PATH"
    REACT_CONTROL_SURFACE = "REACT_CONTROL_SURFACE"
    API_SERVER = "API_SERVER"
    DATABASE_EVENT_STORE = "DATABASE_EVENT_STORE"


_UNAVAILABLE_SYSTEM_LEDGER_ROWS: dict[UnavailableSystem, tuple[str, str]] = {
    UnavailableSystem.RUNTIME_SUBMIT_BRIDGE: (
        "runtime.submit is mapped as a boundary and never wired or called",
        "P4-EXEC-A AurelExec",
    ),
    UnavailableSystem.P4_EXECUTION: (
        "no execution engine, worker, or dispatch path exists in P3",
        "P4 AurelExec",
    ),
    UnavailableSystem.P5_TRACE_VERIFICATION: (
        "no Trace/Ledger write or verification exists; seal is not proof",
        "P5 AurelTrace",
    ),
    UnavailableSystem.P9_CUSTOS_ENFORCEMENT: (
        "no authority is granted or enforced; audits are not enforcement",
        "P9 Custos",
    ),
    UnavailableSystem.PRODUCTION_LIVE_PATH: (
        "no LIVE path exists; the P3 seal is control-plane truth only",
        "P4+P5+P9 combined",
    ),
    UnavailableSystem.SAFE_VERIFIED_SANDBOX: (
        "no verified sandbox exists; sandbox requirements never execute",
        "P4 AurelExec + P9 Custos",
    ),
    UnavailableSystem.PERSISTENCE: (
        "no database, event store, durable history, or seal ledger exists; "
        "all P3 state is in-memory",
        "P4/P5/P6 persistence strategy",
    ),
    UnavailableSystem.REAL_WORKER_DISPATCH: (
        "queue placement stays candidate-only; no worker receives work",
        "P4 AurelExec",
    ),
    UnavailableSystem.REAL_SERVICE_RUNTIME: (
        "topology is a map; no service runs, discovers, or routes",
        "P4 AurelExec",
    ),
    UnavailableSystem.NETWORK_TRANSPORT: (
        "no socket, HTTP client, message bus, or transport exists",
        "P4 AurelExec",
    ),
    UnavailableSystem.MODEL_INVOCATION: (
        "model requirements are declared and never invoked",
        "P4 AurelExec + P9 Custos",
    ),
    UnavailableSystem.TOOL_INVOCATION: (
        "tool requirements are declared and never invoked",
        "P4 AurelExec + P9 Custos",
    ),
    UnavailableSystem.SANDBOX_EXECUTION: (
        "sandbox requirements are declared and never executed",
        "P4 AurelExec + P9 Custos",
    ),
    UnavailableSystem.MEMORY_WRITE_PATH: (
        "no memory read/write path exists in AurelFlow",
        "P4 AurelExec + P6 memory domain",
    ),
    UnavailableSystem.POLICY_MUTATION_PATH: (
        "no policy is read, written, or enforced by AurelFlow",
        "P9 Custos",
    ),
    UnavailableSystem.IDENTITY_MUTATION_PATH: (
        "no identity state is read or mutated by AurelFlow",
        "P9 Custos",
    ),
    UnavailableSystem.REACT_CONTROL_SURFACE: (
        "React remains projection-only; no control surface exists",
        "future AurelShell/React over P4+P9",
    ),
    UnavailableSystem.API_SERVER: (
        "no API server, REST route, or WebSocket exists",
        "future AurelShell service layer",
    ),
    UnavailableSystem.DATABASE_EVENT_STORE: (
        "no database or event store backs any AurelFlow contract",
        "P4/P5/P6 persistence strategy",
    ),
}


@dataclass(frozen=True)
class UnavailableSystemEntry(_CanonicalMixin):
    """One honestly-absent system with reason and future owner."""

    entry_id: str
    contract_version: str
    system: UnavailableSystem
    reason: str
    future_owner: str
    truth_label: FlowTruthLabel
    unavailable_reason: str = P3_AUDIT_UNAVAILABLE_REASON
    implemented: bool = False

    def __post_init__(self) -> None:
        _forbid_true(self, "implemented")
        if self.truth_label is not FlowTruthLabel.UNAVAILABLE:
            raise AurelFlowValidationError(
                "an unavailable system entry must carry the UNAVAILABLE "
                "truth label",
                code=AurelFlowErrorCode.FORBIDDEN_TRUTH_LABEL,
                field="truth_label",
            )


@dataclass(frozen=True)
class UnavailableSystemsLedger(_CanonicalMixin):
    """Total ledger of absent systems. Recording is not implementing."""

    ledger_id: str
    contract_version: str
    entries: tuple[UnavailableSystemEntry, ...]
    truth_label: FlowTruthLabel
    unavailable_reason: str = P3_AUDIT_UNAVAILABLE_REASON
    unavailable_system_implemented: bool = False
    runtime_submit_wired: bool = False
    p4_implemented: bool = False
    p5_implemented: bool = False
    p9_implemented: bool = False
    persistence_implemented: bool = False

    def __post_init__(self) -> None:
        _forbid_true(
            self,
            "unavailable_system_implemented",
            "runtime_submit_wired",
            "p4_implemented",
            "p5_implemented",
            "p9_implemented",
            "persistence_implemented",
        )
        recorded = {entry.system for entry in self.entries}
        if len(recorded) != len(self.entries):
            raise AurelFlowValidationError(
                "an unavailable system may appear only once in the ledger",
                code=AurelFlowErrorCode.INVALID_SEAL_CHECK,
                field="entries",
            )
        absent = tuple(
            system for system in UnavailableSystem if system not in recorded
        )
        if absent:
            raise AurelFlowValidationError(
                "the unavailable systems ledger must be total; absent: "
                + ", ".join(system.value for system in absent),
                code=AurelFlowErrorCode.INVALID_SEAL_CHECK,
                field="entries",
            )


def build_unavailable_systems_ledger() -> UnavailableSystemsLedger:
    entries: list[UnavailableSystemEntry] = []
    for system in UnavailableSystem:
        reason, future_owner = _UNAVAILABLE_SYSTEM_LEDGER_ROWS[system]
        entry_payload = {
            "contract_version": UNAVAILABLE_SYSTEM_ENTRY_VERSION,
            "system": system.value,
        }
        entries.append(
            UnavailableSystemEntry(
                entry_id="fllue-" + stable_hash(entry_payload)[:16],
                contract_version=UNAVAILABLE_SYSTEM_ENTRY_VERSION,
                system=system,
                reason=reason,
                future_owner=future_owner,
                truth_label=FlowTruthLabel.UNAVAILABLE,
            )
        )
    payload = {
        "contract_version": UNAVAILABLE_SYSTEMS_LEDGER_VERSION,
        "entry_ids": tuple(sorted(entry.entry_id for entry in entries)),
    }
    return UnavailableSystemsLedger(
        ledger_id="fllul-" + stable_hash(payload)[:16],
        contract_version=UNAVAILABLE_SYSTEMS_LEDGER_VERSION,
        entries=tuple(entries),
        truth_label=FlowTruthLabel.LOCAL_RUNTIME_SUBSTRATE,
    )


class BoundaryExitCategory(str, Enum):
    """Closed-world P3 exit boundaries audited by P3-FLOW-L."""

    NO_RUNTIME_SUBMIT = "NO_RUNTIME_SUBMIT"
    NO_EXECUTION = "NO_EXECUTION"
    NO_DISPATCH = "NO_DISPATCH"
    NO_SERVICE_RUNTIME = "NO_SERVICE_RUNTIME"
    NO_NETWORK = "NO_NETWORK"
    NO_TOOL_CALL = "NO_TOOL_CALL"
    NO_MODEL_CALL = "NO_MODEL_CALL"
    NO_SANDBOX_EXECUTION = "NO_SANDBOX_EXECUTION"
    NO_TRACE_WRITE = "NO_TRACE_WRITE"
    NO_LEDGER_WRITE = "NO_LEDGER_WRITE"
    NO_MEMORY_WRITE = "NO_MEMORY_WRITE"
    NO_POLICY_MUTATION = "NO_POLICY_MUTATION"
    NO_IDENTITY_MUTATION = "NO_IDENTITY_MUTATION"
    NO_REACT_CONTROL = "NO_REACT_CONTROL"
    NO_PRODUCTION_CLAIM = "NO_PRODUCTION_CLAIM"
    NO_FINAL_AUTHORITY = "NO_FINAL_AUTHORITY"
    NO_P4_IMPLEMENTATION = "NO_P4_IMPLEMENTATION"
    NO_P5_IMPLEMENTATION = "NO_P5_IMPLEMENTATION"
    NO_P9_IMPLEMENTATION = "NO_P9_IMPLEMENTATION"
    NO_PERSISTENCE_IMPLEMENTATION = "NO_PERSISTENCE_IMPLEMENTATION"


_BOUNDARY_EXIT_FORBIDDEN_ATTRS: dict[
    BoundaryExitCategory, tuple[str, ...]
] = {
    BoundaryExitCategory.NO_RUNTIME_SUBMIT: (
        "runtime_submit_wired",
        "runtime_submit_called",
    ),
    BoundaryExitCategory.NO_EXECUTION: (
        "workflow_executed",
        "execution_available",
        "execution_request_created",
    ),
    BoundaryExitCategory.NO_DISPATCH: (
        "dispatch_available",
        "dispatched",
        "queued",
        "worker_allocated",
        "worker_spawned",
    ),
    BoundaryExitCategory.NO_SERVICE_RUNTIME: (
        "service_runtime_available",
        "service_invoked",
    ),
    BoundaryExitCategory.NO_NETWORK: ("network_called",),
    BoundaryExitCategory.NO_TOOL_CALL: ("tool_invoked",),
    BoundaryExitCategory.NO_MODEL_CALL: ("model_invoked",),
    BoundaryExitCategory.NO_SANDBOX_EXECUTION: ("sandbox_executed",),
    BoundaryExitCategory.NO_TRACE_WRITE: (
        "trace_written",
        "trace_write_performed",
    ),
    BoundaryExitCategory.NO_LEDGER_WRITE: (
        "ledger_written",
        "ledger_write_performed",
    ),
    BoundaryExitCategory.NO_MEMORY_WRITE: (
        "memory_write_performed",
        "memory_access_performed",
    ),
    BoundaryExitCategory.NO_POLICY_MUTATION: (
        "policy_mutation_performed",
        "policy_mutated",
    ),
    BoundaryExitCategory.NO_IDENTITY_MUTATION: (
        "identity_mutation_performed",
        "identity_mutated",
    ),
    BoundaryExitCategory.NO_REACT_CONTROL: (
        "frontend_mutation_allowed",
        "ui_execution_allowed",
        "ui_runtime_submit_allowed",
        "ui_release_approval_authority",
    ),
    BoundaryExitCategory.NO_PRODUCTION_CLAIM: (
        "production_ready",
        "release_approved",
        "live_path_available",
    ),
    BoundaryExitCategory.NO_FINAL_AUTHORITY: (
        "authority_granted",
        "permission_granted",
    ),
    BoundaryExitCategory.NO_P4_IMPLEMENTATION: ("p4_implemented",),
    BoundaryExitCategory.NO_P5_IMPLEMENTATION: (
        "p5_implemented",
        "proof_available",
    ),
    BoundaryExitCategory.NO_P9_IMPLEMENTATION: ("p9_implemented",),
    BoundaryExitCategory.NO_PERSISTENCE_IMPLEMENTATION: (
        "persistence_implemented",
    ),
}


@dataclass(frozen=True)
class BoundaryExitFinding(_CanonicalMixin):
    """One boundary observation. A finding is not enforcement."""

    finding_id: str
    contract_version: str
    category: BoundaryExitCategory
    status: P3AuditStatus
    detail: str
    truth_label: FlowTruthLabel
    unavailable_reason: str = P3_AUDIT_UNAVAILABLE_REASON
    enforcement_performed: bool = False

    def __post_init__(self) -> None:
        _forbid_true(self, "enforcement_performed")


@dataclass(frozen=True)
class BoundaryExitAuditReadModel(_CanonicalMixin):
    """Deterministic exit-boundary audit. Read-only, never enforcement."""

    read_model_id: str
    contract_version: str
    subject_type_names: tuple[str, ...]
    findings: tuple[BoundaryExitFinding, ...]
    failing_category_values: tuple[str, ...]
    all_applicable_passed: bool
    truth_label: FlowTruthLabel
    unavailable_reason: str = P3_AUDIT_UNAVAILABLE_REASON
    read_only: bool = True
    enforcement_performed: bool = False
    mutation_performed: bool = False
    runtime_policy_changed: bool = False
    production_ready: bool = False

    def __post_init__(self) -> None:
        _forbid_false(self, "read_only")
        _forbid_true(
            self,
            "enforcement_performed",
            "mutation_performed",
            "runtime_policy_changed",
            "production_ready",
        )


def _exit_finding(
    category: BoundaryExitCategory,
    status: P3AuditStatus,
    detail: str,
) -> BoundaryExitFinding:
    payload = {
        "contract_version": BOUNDARY_EXIT_FINDING_VERSION,
        "category": category.value,
        "status": status.value,
        "detail": detail,
    }
    return BoundaryExitFinding(
        finding_id="fllbf-" + stable_hash(payload)[:16],
        contract_version=BOUNDARY_EXIT_FINDING_VERSION,
        category=category,
        status=status,
        detail=detail,
        truth_label=FlowTruthLabel.READ_MODEL_ONLY,
    )


def run_boundary_exit_audit(
    subjects: tuple[object, ...],
) -> BoundaryExitAuditReadModel:
    """Read-only category -> forbidden-attribute sweep over real objects.

    A category with no declaring subject is honestly NOT_APPLICABLE; a True
    forbidden boolean fails its category with a named offender. The audit
    changes nothing and certifies nothing.
    """

    findings: list[BoundaryExitFinding] = []
    for category in BoundaryExitCategory:
        attrs = _BOUNDARY_EXIT_FORBIDDEN_ATTRS[category]
        declaring = [
            subject
            for subject in subjects
            if any(hasattr(subject, attr) for attr in attrs)
        ]
        if not declaring:
            findings.append(
                _exit_finding(
                    category,
                    P3AuditStatus.NOT_APPLICABLE,
                    "no audited subject declares "
                    + ", ".join(attrs),
                )
            )
            continue
        offenders = sorted(
            f"{type(subject).__name__}.{attr}"
            for subject in declaring
            for attr in attrs
            if getattr(subject, attr, False)
        )
        if offenders:
            findings.append(
                _exit_finding(
                    category,
                    P3AuditStatus.FAIL,
                    "forbidden True on " + "; ".join(offenders),
                )
            )
        else:
            findings.append(
                _exit_finding(
                    category,
                    P3AuditStatus.PASS,
                    f"{len(declaring)} declaring subjects keep every "
                    "forbidden boolean False",
                )
            )
    failing = tuple(
        finding.category.value
        for finding in findings
        if finding.status is P3AuditStatus.FAIL
    )
    subject_type_names = tuple(
        sorted({type(subject).__name__ for subject in subjects})
    )
    payload = {
        "contract_version": BOUNDARY_EXIT_AUDIT_READ_MODEL_VERSION,
        "subject_type_names": subject_type_names,
        "finding_ids": tuple(
            sorted(finding.finding_id for finding in findings)
        ),
    }
    return BoundaryExitAuditReadModel(
        read_model_id="fllbr-" + stable_hash(payload)[:16],
        contract_version=BOUNDARY_EXIT_AUDIT_READ_MODEL_VERSION,
        subject_type_names=subject_type_names,
        findings=tuple(findings),
        failing_category_values=failing,
        all_applicable_passed=not failing,
        truth_label=FlowTruthLabel.READ_MODEL_ONLY,
    )
