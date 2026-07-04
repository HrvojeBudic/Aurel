"""P4-EXEC-G capability coverage / audits / handoff matrix / P4 exit seal.

The exit seal is evidence, not vibes: `P4ExitSeal.seal_status` can be
SEALED only when the large pre-seal validation summary actually passed —
a SEALED verdict over failing or missing gates is unconstructible. The
coverage matrix is total over P4.0–P4.20 with every row carrying evidence
or an unavailable reason; the truth-label audit fails ERROR on any
TRACE_VERIFIED appearance (P5 does not exist yet); the unavailable-state
audit requires a future owner for every absent system; the handoff matrix
assigns P5/P8/P9/P2/Rust-WASM ownership. Sealing P4 means the execution
kernel foundation is bounded, visible, report-backed, validated, and
handoff-ready — not that future execution features exist.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .exec_errors import AurelExecErrorCode, AurelExecValidationError
from .exec_types import (
    ExecTruthLabel,
    _ExecCanonicalMixin,
    forbid_false,
    forbid_true,
    require_nonempty,
    stable_hash,
)

CAPABILITY_COVERAGE_MATRIX_VERSION = "exec_capability_coverage_matrix.v1"
TRUTH_LABEL_AUDIT_VERSION = "exec_truth_label_audit.v1"
UNAVAILABLE_STATE_AUDIT_VERSION = "exec_unavailable_state_audit.v1"
P4_HANDOFF_MATRIX_VERSION = "p4_handoff_matrix.v1"
P4_EXIT_SEAL_VERSION = "p4_exit_seal.v1"
VALIDATION_GATE_RESULT_VERSION = "validation_gate_result.v1"
VALIDATION_SUMMARY_VERSION = "validation_summary.v1"

P4_CAPABILITY_ROWS: tuple[str, ...] = (
    "P4.0 doctrine / kernel boundary",
    "P4.1 contract types / truth labels",
    "P4.2 P3 to P4 admission bridge",
    "P4.3 execution lease",
    "P4.4 job / attempt lifecycle",
    "P4.5 execution session",
    "P4.6 runtime submit bridge",
    "P4.7 in-process worker slot / queue claim",
    "P4.8 local message kernel",
    "P4.9 checkpoint / rollback refs",
    "P4.10 execution mode registry",
    "P4.11 tool execution profile",
    "P4.12 model execution profile",
    "P4.13 terminal / code execution profile",
    "P4.14 verifier hook / semantic guard",
    "P4.15 failure classification / bounded recovery",
    "P4.16 algedonic signals",
    "P4.17 topology / concurrency / backpressure",
    "P4.18 harness telemetry / ExecBench",
    "P4.19 projection / CLI / Shell binding",
    "P4.20 exit seal / handoff",
)


class CapabilityStatus(str, Enum):
    LIVE = "LIVE"
    PROFILE_ONLY = "PROFILE_ONLY"
    TRACE_BOUND = "TRACE_BOUND"
    UNAVAILABLE = "UNAVAILABLE"
    DEFERRED = "DEFERRED"
    ERROR = "ERROR"


class SealStatus(str, Enum):
    SEALED = "SEALED"
    SEAL_BLOCKED = "SEAL_BLOCKED"
    ERROR = "ERROR"


class GateResult(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    NOT_REQUIRED = "NOT_REQUIRED"
    NOT_RUN = "NOT_RUN"
    WAIVED = "WAIVED"


_ACCEPTABLE_GATE_RESULTS = (
    GateResult.PASS,
    GateResult.NOT_APPLICABLE,
    GateResult.NOT_REQUIRED,
    GateResult.WAIVED,
)


@dataclass(frozen=True)
class CapabilityCoverageItem(_ExecCanonicalMixin):
    """One P4.x row. Must explain itself."""

    capability: str
    status: CapabilityStatus
    evidence: str
    truth_label: ExecTruthLabel

    def __post_init__(self) -> None:
        require_nonempty(self, "capability", code=AurelExecErrorCode.EMPTY_FIELD)
        require_nonempty(self, "evidence", code=AurelExecErrorCode.EMPTY_FIELD)
        if self.capability not in P4_CAPABILITY_ROWS:
            raise AurelExecValidationError(
                f"unknown capability row {self.capability!r}",
                code=AurelExecErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                field="capability",
            )


@dataclass(frozen=True)
class ExecCapabilityCoverageMatrix(_ExecCanonicalMixin):
    """Total P4.0–P4.20 coverage. A missing or duplicate row is
    unconstructible; every row carries evidence."""

    matrix_id: str
    items: tuple[CapabilityCoverageItem, ...]
    truth_label: ExecTruthLabel
    contract_version: str = CAPABILITY_COVERAGE_MATRIX_VERSION

    def __post_init__(self) -> None:
        require_nonempty(self, "matrix_id", code=AurelExecErrorCode.EMPTY_FIELD)
        covered = [item.capability for item in self.items]
        if covered != list(P4_CAPABILITY_ROWS):
            raise AurelExecValidationError(
                "coverage matrix must be total over P4.0..P4.20 in order",
                code=AurelExecErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                field="items",
            )

    def status_of(self, capability: str) -> CapabilityStatus:
        for item in self.items:
            if item.capability == capability:
                return item.status
        raise AurelExecValidationError(
            f"unknown capability {capability!r}",
            code=AurelExecErrorCode.ERROR,
            field="items",
        )

    @property
    def matrix_hash(self) -> str:
        return stable_hash(self)


def build_p4_capability_coverage_matrix() -> ExecCapabilityCoverageMatrix:
    """Repo-truth default coverage for the sealed P4 stack."""
    live = CapabilityStatus.LIVE
    rows: tuple[tuple[str, CapabilityStatus, str], ...] = (
        ("P4.0 doctrine / kernel boundary", live, "exec_types.py doctrine + A report; boundary tests"),
        ("P4.1 contract types / truth labels", live, "exec_types.py enums; test_exec_types.py"),
        ("P4.2 P3 to P4 admission bridge", live, "exec_admission.py eight-gate chain; test_exec_admission.py"),
        ("P4.3 execution lease", live, "exec_lease.py; test_exec_lease.py"),
        ("P4.4 job / attempt lifecycle", live, "exec_job.py transition maps; test_exec_job_lifecycle.py"),
        ("P4.5 execution session", live, "exec_session.py; test_exec_session.py"),
        ("P4.6 runtime submit bridge", live, "exec_runtime_bridge.py; real-kernel demo test_exec_first_read_file_demo.py"),
        ("P4.7 in-process worker slot / queue claim", live, "exec_queue.py + exec_worker.py; test_exec_worker_slot.py"),
        ("P4.8 local message kernel", live, "exec_messages.py local log (not a bus); test_exec_messages.py"),
        ("P4.9 checkpoint / rollback refs", live, "exec_checkpoint.py refs only (rollback not executed); test_exec_checkpoint_refs.py"),
        ("P4.10 execution mode registry", live, "exec_modes.py closed world; test_exec_modes.py"),
        ("P4.11 tool execution profile", live, "exec_mode_profiles.py read_file-only bridge path; test_exec_tool_profile.py"),
        ("P4.12 model execution profile", CapabilityStatus.PROFILE_ONLY, "ModelExecutionProfile — model calls structurally unavailable; test_exec_risky_mode_profiles.py"),
        ("P4.13 terminal / code execution profile", CapabilityStatus.UNAVAILABLE, "Terminal/Code profiles — every execution boolean unconstructible; sandbox/verifier/P9 canon required first"),
        ("P4.14 verifier hook / semantic guard", CapabilityStatus.PROFILE_ONLY, "VerifierHook — no AVAILABLE member; evidence-producing verifier is future canon; test_exec_verification.py"),
        ("P4.15 failure classification / bounded recovery", live, "exec_failure.py + exec_recovery.py total tables (plans only, no recovery execution); tests"),
        ("P4.16 algedonic signals", live, "exec_algedonic.py urgency visibility; test_exec_algedonic_signal.py"),
        ("P4.17 topology / concurrency / backpressure", live, "exec_topology.py + exec_pressure.py local control plane; tests"),
        ("P4.18 harness telemetry / ExecBench", live, "exec_bench.py measured-only telemetry; test_exec_bench.py"),
        ("P4.19 projection / CLI / Shell binding", live, "exec_status.py read model + binding contract (CLI wiring UNAVAILABLE with reason; Shell UI UNAVAILABLE)"),
        ("P4.20 exit seal / handoff", live, "exec_seal.py + seal report + release evidence + large validation gate"),
    )
    return ExecCapabilityCoverageMatrix(
        matrix_id="exec-coverage-" + stable_hash(P4_CAPABILITY_ROWS)[:16],
        items=tuple(
            CapabilityCoverageItem(
                capability=capability,
                status=status,
                evidence=evidence,
                truth_label=ExecTruthLabel.LIVE,
            )
            for capability, status, evidence in rows
        ),
        truth_label=ExecTruthLabel.LIVE,
    )


@dataclass(frozen=True)
class TruthLabelAudit(_ExecCanonicalMixin):
    """Truth-label census over provided labels. Any TRACE_VERIFIED
    appearance forces audit_status ERROR — the claim is impossible pre-P5
    (the label has no enum member), so its presence means corrupted data."""

    audit_id: str
    live_items: int
    profile_only_items: int
    trace_bound_items: int
    trace_verified_items: int
    simulated_items: int
    dev_fixture_items: int
    unavailable_items: int
    error_items: int
    fake_live_risks: tuple[str, ...]
    fake_trace_verified_risks: tuple[str, ...]
    audit_status: str
    truth_label: ExecTruthLabel
    contract_version: str = TRUTH_LABEL_AUDIT_VERSION

    def __post_init__(self) -> None:
        require_nonempty(self, "audit_id", code=AurelExecErrorCode.EMPTY_FIELD)
        if self.trace_verified_items > 0 and self.audit_status != "ERROR":
            raise AurelExecValidationError(
                "TRACE_VERIFIED items before P5 force audit_status=ERROR",
                code=AurelExecErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                field="audit_status",
            )
        if self.audit_status not in ("PASS", "ERROR"):
            raise AurelExecValidationError(
                "audit_status must be PASS or ERROR",
                code=AurelExecErrorCode.ERROR,
                field="audit_status",
            )


def build_truth_label_audit(
    labels: tuple[ExecTruthLabel, ...],
    *,
    raw_label_values: tuple[str, ...] = (),
) -> TruthLabelAudit:
    """Census the provided labels. ``raw_label_values`` lets callers audit
    string-labeled surfaces; a raw 'TRACE_VERIFIED' forces ERROR."""
    def _count(*members: ExecTruthLabel) -> int:
        return sum(1 for label in labels if label in members)

    trace_verified = sum(1 for raw in raw_label_values if raw == "TRACE_VERIFIED")
    fake_trace_risks = tuple(
        f"raw label {raw!r} claims trace verification without P5"
        for raw in raw_label_values
        if raw == "TRACE_VERIFIED"
    )
    return TruthLabelAudit(
        audit_id="exec-truth-audit-" + stable_hash((labels, raw_label_values))[:16],
        live_items=_count(ExecTruthLabel.LIVE),
        profile_only_items=0,  # PROFILE_ONLY posture lives in availability statuses
        trace_bound_items=_count(ExecTruthLabel.TRACE_BOUND),
        trace_verified_items=trace_verified,
        simulated_items=_count(ExecTruthLabel.SIMULATED),
        dev_fixture_items=_count(ExecTruthLabel.DEV_FIXTURE),
        unavailable_items=_count(
            ExecTruthLabel.UNAVAILABLE,
            ExecTruthLabel.RUNTIME_SUBMIT_UNAVAILABLE,
            ExecTruthLabel.TRACE_BOUND_UNAVAILABLE,
            ExecTruthLabel.TRACE_VERIFIED_UNAVAILABLE,
            ExecTruthLabel.POLICY_ENFORCED_UNAVAILABLE,
            ExecTruthLabel.POLICY_SHADOW,
        ),
        error_items=_count(ExecTruthLabel.ERROR),
        fake_live_risks=(),
        fake_trace_verified_risks=fake_trace_risks,
        audit_status="ERROR" if trace_verified else "PASS",
        truth_label=ExecTruthLabel.LIVE,
    )


REQUIRED_UNAVAILABLE_OWNERS: dict[str, str] = {
    "shell_ui": "P2 AurelShell",
    "p5_trace_verification": "P5 AurelTrace",
    "p8_routing": "P8 Atlas / coordination layer",
    "p9_enforcement": "P9 Custos",
    "rust_wasm_substrate": "future substrate extraction (operator-decided)",
    "worker_pool": "future Rust/WASM substrate / runtime hardening",
    "deterministic_replay_engine": "future substrate / P5+ runtime hardening",
    "durable_event_log": "P5 / future substrate",
}


@dataclass(frozen=True)
class UnavailableStateEntry(_ExecCanonicalMixin):
    system: str
    reason: str
    future_owner: str

    def __post_init__(self) -> None:
        require_nonempty(self, "system", code=AurelExecErrorCode.EMPTY_FIELD)
        require_nonempty(self, "reason", code=AurelExecErrorCode.EMPTY_FIELD)
        require_nonempty(self, "future_owner", code=AurelExecErrorCode.EMPTY_FIELD)


@dataclass(frozen=True)
class UnavailableStateAudit(_ExecCanonicalMixin):
    """Every absent system carries a reason and a future owner; a truncated
    audit (missing a required system) is unconstructible."""

    audit_id: str
    entries: tuple[UnavailableStateEntry, ...]
    truth_label: ExecTruthLabel
    contract_version: str = UNAVAILABLE_STATE_AUDIT_VERSION

    def __post_init__(self) -> None:
        require_nonempty(self, "audit_id", code=AurelExecErrorCode.EMPTY_FIELD)
        covered = {entry.system for entry in self.entries}
        missing = set(REQUIRED_UNAVAILABLE_OWNERS) - covered
        if missing:
            raise AurelExecValidationError(
                "unavailable-state audit must cover: " + ", ".join(sorted(missing)),
                code=AurelExecErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                field="entries",
            )
        for entry in self.entries:
            expected = REQUIRED_UNAVAILABLE_OWNERS.get(entry.system)
            if expected is not None and entry.future_owner != expected:
                raise AurelExecValidationError(
                    f"{entry.system} must be owned by {expected!r}",
                    code=AurelExecErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                    field="entries",
                )


def build_unavailable_state_audit() -> UnavailableStateAudit:
    reasons = {
        "shell_ui": "no Shell UI/React/API exists for AurelExec",
        "p5_trace_verification": "trace refs are bound, never verified, in P4",
        "p8_routing": "no routing/coordination engine exists in P4",
        "p9_enforcement": "admission/judgment are structural gates, not authority",
        "rust_wasm_substrate": "no Rust/WASM code exists; contracts are extraction-ready",
        "worker_pool": "exactly one local in-process worker slot exists (C canon)",
        "deterministic_replay_engine": "no replay engine exists; refs only",
        "durable_event_log": "the local message log is in-memory and not a bus",
    }
    return UnavailableStateAudit(
        audit_id="exec-unavail-audit-"
        + stable_hash(tuple(sorted(REQUIRED_UNAVAILABLE_OWNERS)))[:16],
        entries=tuple(
            UnavailableStateEntry(
                system=system,
                reason=reasons[system],
                future_owner=owner,
            )
            for system, owner in sorted(REQUIRED_UNAVAILABLE_OWNERS.items())
        ),
        truth_label=ExecTruthLabel.LIVE,
    )


P4_HANDOFF_OWNERS: dict[str, tuple[str, ...]] = {
    "P5 AurelTrace": (
        "trace verification",
        "durable evidence spine",
        "trace event canonicalization",
        "replay/evidence binding",
        "TRACE_VERIFIED truth",
    ),
    "P8 Atlas / coordination": (
        "routing / model-worker coordination",
        "topology-aware model/tool routing",
        "later distributed coordination handoff",
    ),
    "P9 Custos": (
        "authority / enforcement",
        "high-risk recovery approval",
        "Custos policy runtime hardening",
        "backpressure override authority",
    ),
    "P2 AurelShell": (
        "operator UI projection",
        "Shell command surfaces",
        "frontend visibility",
        "non-mock AurelExec dashboards",
    ),
    "Future Rust/WASM substrate": (
        "deterministic event log",
        "deterministic replay",
        "durable worker leases",
        "real worker pool",
        "high-throughput execution",
        "WASM/sandbox boundary",
        "workflow exact-copy/fork substrate",
    ),
}


@dataclass(frozen=True)
class P4HandoffRow(_ExecCanonicalMixin):
    owner: str
    owns: tuple[str, ...]

    def __post_init__(self) -> None:
        require_nonempty(self, "owner", code=AurelExecErrorCode.EMPTY_FIELD)
        if not self.owns:
            raise AurelExecValidationError(
                "a handoff row must own something",
                code=AurelExecErrorCode.EMPTY_FIELD,
                field="owns",
            )


@dataclass(frozen=True)
class P4HandoffMatrix(_ExecCanonicalMixin):
    """Who owns what next. A matrix missing a required owner is
    unconstructible; owning is future work, never present capability."""

    matrix_id: str
    rows: tuple[P4HandoffRow, ...]
    truth_label: ExecTruthLabel
    contract_version: str = P4_HANDOFF_MATRIX_VERSION
    handoff_is_implementation: bool = False

    def __post_init__(self) -> None:
        require_nonempty(self, "matrix_id", code=AurelExecErrorCode.EMPTY_FIELD)
        forbid_true(self, "handoff_is_implementation")
        owners = [row.owner for row in self.rows]
        if owners != list(P4_HANDOFF_OWNERS):
            raise AurelExecValidationError(
                "handoff matrix must cover P5/P8/P9/P2/Rust-WASM owners in order",
                code=AurelExecErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                field="rows",
            )

    @property
    def matrix_hash(self) -> str:
        return stable_hash(self)


def build_p4_handoff_matrix() -> P4HandoffMatrix:
    return P4HandoffMatrix(
        matrix_id="p4-handoff-" + stable_hash(tuple(P4_HANDOFF_OWNERS))[:16],
        rows=tuple(
            P4HandoffRow(owner=owner, owns=owns)
            for owner, owns in P4_HANDOFF_OWNERS.items()
        ),
        truth_label=ExecTruthLabel.LIVE,
    )


@dataclass(frozen=True)
class ValidationGateResult(_ExecCanonicalMixin):
    """One validation gate outcome, recorded exactly as it ran."""

    gate_name: str
    command: str
    result: GateResult
    notes: str
    required: bool = True
    contract_version: str = VALIDATION_GATE_RESULT_VERSION

    def __post_init__(self) -> None:
        require_nonempty(self, "gate_name", code=AurelExecErrorCode.EMPTY_FIELD)
        require_nonempty(self, "command", code=AurelExecErrorCode.EMPTY_FIELD)
        require_nonempty(self, "notes", code=AurelExecErrorCode.EMPTY_FIELD)


@dataclass(frozen=True)
class ValidationSummary(_ExecCanonicalMixin):
    """A gate table whose pass verdict is derived, never declared: a
    summary claiming pass over a failing required gate is unconstructible."""

    summary_id: str
    gates: tuple[ValidationGateResult, ...]
    all_required_gates_pass: bool
    truth_label: ExecTruthLabel
    contract_version: str = VALIDATION_SUMMARY_VERSION

    def __post_init__(self) -> None:
        require_nonempty(self, "summary_id", code=AurelExecErrorCode.EMPTY_FIELD)
        if not self.gates:
            raise AurelExecValidationError(
                "a validation summary needs gates",
                code=AurelExecErrorCode.EMPTY_FIELD,
                field="gates",
            )
        derived = all(
            gate.result in _ACCEPTABLE_GATE_RESULTS
            for gate in self.gates
            if gate.required
        )
        if self.all_required_gates_pass != derived:
            raise AurelExecValidationError(
                "all_required_gates_pass must match the recorded gates",
                code=AurelExecErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                field="all_required_gates_pass",
            )


def build_validation_summary(
    gates: tuple[ValidationGateResult, ...],
) -> ValidationSummary:
    derived = all(
        gate.result in _ACCEPTABLE_GATE_RESULTS for gate in gates if gate.required
    )
    return ValidationSummary(
        summary_id="exec-validation-"
        + stable_hash(tuple((g.gate_name, g.result.value) for g in gates))[:16],
        gates=gates,
        all_required_gates_pass=derived,
        truth_label=ExecTruthLabel.LIVE,
    )


@dataclass(frozen=True)
class P4ExitSeal(_ExecCanonicalMixin):
    """The P4 exit seal. SEALED over a non-passing large validation summary
    is unconstructible — the seal is evidence, not vibes.

    Sealing means P4 is bounded, visible, report-backed, validated, and
    handoff-ready. It does not mean future execution features exist:
    ``future_features_implemented`` is structurally False.
    """

    seal_id: str
    sealed_domain: str
    seal_status: SealStatus
    covered_packs: tuple[str, ...]
    coverage_matrix_ref: str
    handoff_matrix_ref: str
    truth_label_audit_ref: str
    unavailable_audit_ref: str
    focused_validation: ValidationSummary
    large_validation: ValidationSummary
    reports_indexed: tuple[str, ...]
    remaining_risks: tuple[str, ...]
    next_domain: str
    truth_label: ExecTruthLabel
    contract_version: str = P4_EXIT_SEAL_VERSION
    commit_hash: str | None = None
    final_git_status: str | None = None
    future_features_implemented: bool = False
    python_final_kernel_claim: bool = False
    trace_verified: bool = False
    seal_is_runtime_mutation: bool = False

    def __post_init__(self) -> None:
        require_nonempty(self, "seal_id", code=AurelExecErrorCode.EMPTY_FIELD)
        require_nonempty(self, "sealed_domain", code=AurelExecErrorCode.EMPTY_FIELD)
        require_nonempty(self, "next_domain", code=AurelExecErrorCode.EMPTY_FIELD)
        forbid_true(
            self,
            "future_features_implemented",
            "python_final_kernel_claim",
            "trace_verified",
            "seal_is_runtime_mutation",
        )
        if not self.covered_packs:
            raise AurelExecValidationError(
                "a seal must name its covered packs",
                code=AurelExecErrorCode.EMPTY_FIELD,
                field="covered_packs",
            )
        if self.seal_status is SealStatus.SEALED:
            if not self.focused_validation.all_required_gates_pass:
                raise AurelExecValidationError(
                    "SEALED requires the focused validation gates to pass",
                    code=AurelExecErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                    field="seal_status",
                )
            if not self.large_validation.all_required_gates_pass:
                raise AurelExecValidationError(
                    "SEALED requires the large pre-seal validation gates to "
                    "pass; a failing gate forces SEAL_BLOCKED",
                    code=AurelExecErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                    field="seal_status",
                )

    @property
    def seal_hash(self) -> str:
        return stable_hash(self)


def build_p4_exit_seal(
    *,
    coverage_matrix: ExecCapabilityCoverageMatrix,
    handoff_matrix: P4HandoffMatrix,
    truth_label_audit: TruthLabelAudit,
    unavailable_audit: UnavailableStateAudit,
    focused_validation: ValidationSummary,
    large_validation: ValidationSummary,
    reports_indexed: tuple[str, ...],
    remaining_risks: tuple[str, ...],
    commit_hash: str | None = None,
    final_git_status: str | None = None,
) -> P4ExitSeal:
    """Build the seal with a derived verdict: SEALED only when every
    required focused and large gate passed and the truth audit passed."""
    sealed = (
        focused_validation.all_required_gates_pass
        and large_validation.all_required_gates_pass
        and truth_label_audit.audit_status == "PASS"
    )
    return P4ExitSeal(
        seal_id="p4-exit-seal-"
        + stable_hash(
            (coverage_matrix.matrix_hash, large_validation.summary_id)
        )[:16],
        sealed_domain="P4 AurelExec execution kernel foundation",
        seal_status=SealStatus.SEALED if sealed else SealStatus.SEAL_BLOCKED,
        covered_packs=(
            "P4-EXEC-A",
            "P4-EXEC-B",
            "P4-EXEC-C",
            "P4-EXEC-D",
            "P4-EXEC-E",
            "P4-EXEC-F",
            "P4-EXEC-G",
        ),
        coverage_matrix_ref=coverage_matrix.matrix_id,
        handoff_matrix_ref=handoff_matrix.matrix_id,
        truth_label_audit_ref=truth_label_audit.audit_id,
        unavailable_audit_ref=unavailable_audit.audit_id,
        focused_validation=focused_validation,
        large_validation=large_validation,
        reports_indexed=reports_indexed,
        remaining_risks=remaining_risks,
        next_domain="P5 AurelTrace Spine",
        truth_label=ExecTruthLabel.LIVE,
        commit_hash=commit_hash,
        final_git_status=final_git_status,
    )
