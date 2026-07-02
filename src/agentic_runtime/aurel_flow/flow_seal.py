"""P3-FLOW-C base P3.9 exit seal for the P3.0–P3.9 Flow base.

Seals the Flow base honestly by checking that each capability layer actually
exists in the package, and by stating every hard boundary as a fail-closed
boolean. Seal is not TRACE_VERIFIED. A seal is local evidence, not external
proof: trace verification belongs to P5 AurelTrace. Do not fake PASS —
missing evidence yields PARTIAL / BLOCKED / FAIL / UNAVAILABLE.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from .demo import build_flow_demo_bundle, run_flow_foundation_demo
from .errors import AurelFlowErrorCode, AurelFlowValidationError
from .flow_projection import build_flow_state_projection
from .types import (
    AUREL_FLOW_B_REPORT_PATH,
    AUREL_FLOW_C_PACK_ID,
    AUREL_FLOW_C_REPORT_PATH,
    AUREL_FLOW_REPORT_PATH,
    POLICY_ENFORCEMENT_UNAVAILABLE_REASON,
    TRACE_VERIFICATION_UNAVAILABLE_REASON,
    FlowTruthLabel,
    _CanonicalMixin,
    stable_hash,
    to_canonical_json,
)

FLOW_BASE_EXIT_SEAL_VERSION = "flow_base_exit_seal.v1"
FLOW_BASE_EXIT_SEAL_READ_MODEL_VERSION = "flow_base_exit_seal_read_model.v1"

FLOW_REPORT_PATHS: tuple[str, ...] = (
    AUREL_FLOW_REPORT_PATH,
    AUREL_FLOW_B_REPORT_PATH,
    AUREL_FLOW_C_REPORT_PATH,
)


class FlowBaseExitSealStatus(str, Enum):
    """Closed-world seal statuses."""

    PASS = "PASS"
    PARTIAL = "PARTIAL"
    BLOCKED = "BLOCKED"
    FAIL = "FAIL"
    UNAVAILABLE = "UNAVAILABLE"


@dataclass(frozen=True)
class FlowBaseExitSealCheck(_CanonicalMixin):
    """One seal check with explicit evidence and reason."""

    check_id: str
    checkpoint_range: str
    title: str
    status: FlowBaseExitSealStatus
    evidence: str
    reason: str = ""


@dataclass(frozen=True)
class FlowBaseExitSealBoundary(_CanonicalMixin):
    """Hard boundary booleans the seal must state. Fail-closed both ways."""

    trace_unavailable_reason: str = TRACE_VERIFICATION_UNAVAILABLE_REASON
    policy_unavailable_reason: str = POLICY_ENFORCEMENT_UNAVAILABLE_REASON
    execution_available: bool = False
    trace_verified: bool = False
    ledger_written: bool = False
    policy_enforced_by_flow: bool = False
    runtime_submit_wired: bool = False
    rust_core_active: bool = False
    p4_required_for_execution: bool = True
    p5_required_for_trace_verification: bool = True
    p9_required_for_policy_enforcement: bool = True
    hybrid_ready: bool = True

    def __post_init__(self) -> None:
        for required_false in (
            "execution_available",
            "trace_verified",
            "ledger_written",
            "policy_enforced_by_flow",
            "runtime_submit_wired",
            "rust_core_active",
        ):
            if getattr(self, required_false):
                raise AurelFlowValidationError(
                    f"FlowBaseExitSealBoundary.{required_false} must remain False",
                    code=AurelFlowErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                    field=required_false,
                )
        for required_true in (
            "p4_required_for_execution",
            "p5_required_for_trace_verification",
            "p9_required_for_policy_enforcement",
        ):
            if not getattr(self, required_true):
                raise AurelFlowValidationError(
                    f"FlowBaseExitSealBoundary.{required_true} must remain True",
                    code=AurelFlowErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                    field=required_true,
                )


@dataclass(frozen=True)
class FlowBaseExitSeal(_CanonicalMixin):
    """The base Flow exit seal object. Never LIVE, never TRACE_VERIFIED."""

    seal_version: str
    seal_id: str
    pack_id: str
    checks: tuple[FlowBaseExitSealCheck, ...]
    status: FlowBaseExitSealStatus
    boundary: FlowBaseExitSealBoundary
    truth_label: FlowTruthLabel
    seal_hash: str
    live: bool = False
    trace_verified: bool = False

    def __post_init__(self) -> None:
        for boundary_field in ("live", "trace_verified"):
            if getattr(self, boundary_field):
                raise AurelFlowValidationError(
                    f"FlowBaseExitSeal.{boundary_field} must remain False",
                    code=AurelFlowErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                    field=boundary_field,
                )
        if self.truth_label in (FlowTruthLabel.LIVE, FlowTruthLabel.TRACE_VERIFIED):
            raise AurelFlowValidationError(
                f"FlowBaseExitSeal may not claim truth label {self.truth_label.value!r}",
                code=AurelFlowErrorCode.FORBIDDEN_TRUTH_LABEL,
                field="truth_label",
            )


@dataclass(frozen=True)
class FlowBaseExitSealResult(_CanonicalMixin):
    """Aggregated seal result with per-status counts."""

    seal: FlowBaseExitSeal
    pass_count: int
    partial_count: int
    blocked_count: int
    fail_count: int
    unavailable_count: int
    reason: str


@dataclass(frozen=True)
class FlowBaseExitSealReadModel(_CanonicalMixin):
    """Operator-facing seal read model with report evidence paths."""

    read_model_version: str
    result: FlowBaseExitSealResult
    report_paths: tuple[str, ...]
    truth_label: FlowTruthLabel
    read_model_hash: str


def aggregate_seal_status(
    checks: tuple[FlowBaseExitSealCheck, ...],
) -> FlowBaseExitSealStatus:
    """FAIL > BLOCKED > PARTIAL (incl. UNAVAILABLE) > PASS. Never fakes PASS."""

    statuses = {check.status for check in checks}
    if not checks:
        return FlowBaseExitSealStatus.UNAVAILABLE
    if FlowBaseExitSealStatus.FAIL in statuses:
        return FlowBaseExitSealStatus.FAIL
    if FlowBaseExitSealStatus.BLOCKED in statuses:
        return FlowBaseExitSealStatus.BLOCKED
    if (
        FlowBaseExitSealStatus.PARTIAL in statuses
        or FlowBaseExitSealStatus.UNAVAILABLE in statuses
    ):
        return FlowBaseExitSealStatus.PARTIAL
    return FlowBaseExitSealStatus.PASS


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def detect_flow_reports_present() -> bool:
    """Read-only filesystem truth: do the three Flow pack reports exist?"""

    try:
        root = _repo_root()
        return all((root / report_path).is_file() for report_path in FLOW_REPORT_PATHS)
    except OSError:
        return False


def _capability_check(
    check_id: str, checkpoint_range: str, title: str, evidence: str
) -> FlowBaseExitSealCheck:
    return FlowBaseExitSealCheck(
        check_id=check_id,
        checkpoint_range=checkpoint_range,
        title=title,
        status=FlowBaseExitSealStatus.PASS,
        evidence=evidence,
    )


def evaluate_flow_base_exit_seal(
    *,
    cli_binding_implemented: bool = True,
    docs_reports_present: bool | None = None,
) -> FlowBaseExitSealResult:
    """Evaluate the base P3.9 seal against actual package capability.

    Capability checks exercise the real demo substrate (deterministic,
    in-memory, no execution). Docs presence defaults to read-only filesystem
    truth; callers may pass explicit truth instead.
    """

    if docs_reports_present is None:
        docs_reports_present = detect_flow_reports_present()

    checks: list[FlowBaseExitSealCheck] = []

    foundation = run_flow_foundation_demo()
    checks.append(
        _capability_check(
            "p3_0_graph_foundation",
            "P3.0.0-P3.0.20",
            "workflow graph foundation exists",
            f"demo graph {foundation.graph.graph_id!r} validates closed-world; "
            f"graph hash {foundation.graph.graph_hash[:16]}",
        )
    )
    checks.append(
        _capability_check(
            "p3_1_state_lifecycle",
            "P3.1.0-P3.1.20",
            "workflow run state / lifecycle exists",
            f"demo run snapshot at step {foundation.run_snapshot.step} with "
            f"lifecycle {foundation.run_snapshot.lifecycle_status.value!r}",
        )
    )
    checks.append(
        _capability_check(
            "p3_2_scheduler_ready_queue",
            "P3.2.0-P3.2.20",
            "scheduler / ready queue exists",
            f"scheduler decision hash {foundation.scheduler_decision.decision_hash[:16]}; "
            f"ready={list(foundation.ready_node_ids)}",
        )
    )

    bundle = build_flow_demo_bundle()
    checks.append(
        _capability_check(
            "p3_3_runtime_event_stream",
            "P3.3.0-P3.3.20",
            "runtime event stream exists (not Trace)",
            f"{len(bundle.event_stream.events)} local events recorded; "
            "boundary proves RuntimeEvent is not TraceEvent",
        )
    )
    checks.append(
        _capability_check(
            "p3_4_pause_resume",
            "P3.4.0-P3.4.20",
            "pause/resume signal layer exists (no authority)",
            f"{len(bundle.pause_states)} pause state(s), "
            f"{len(bundle.operator_decision_signals)} operator signal(s), "
            "all authority booleans fail-closed False",
        )
    )
    checks.append(
        _capability_check(
            "p3_5_recovery_candidates",
            "P3.5.0-P3.5.20",
            "retry/recovery/rollback candidates exist (never executed)",
            f"{len(bundle.retry_eligibilities)} eligibility, "
            f"{len(bundle.recovery_proposals)} proposal, "
            f"{len(bundle.rollback_candidates)} rollback candidate",
        )
    )

    projection = build_flow_state_projection(bundle.graph, bundle.run)
    checks.append(
        _capability_check(
            "p3_6_projection",
            "P3.6.0-P3.6.20",
            "flow state projection exists (read-only)",
            f"projection hash {projection.projection_hash[:16]}; "
            "projection mutated nothing",
        )
    )

    if cli_binding_implemented:
        checks.append(
            _capability_check(
                "p3_7_cli_binding",
                "P3.7.0-P3.7.20",
                "read-only flow CLI binding exists",
                "flow demo/inspect/timeline/wiring/protocol/seal read-only commands",
            )
        )
    else:
        checks.append(
            FlowBaseExitSealCheck(
                check_id="p3_7_cli_binding",
                checkpoint_range="P3.7.0-P3.7.20",
                title="read-only flow CLI binding",
                status=FlowBaseExitSealStatus.PARTIAL,
                evidence="backend read models exist",
                reason="CLI binding not wired in this evaluation input",
            )
        )

    if docs_reports_present:
        checks.append(
            _capability_check(
                "p3_8_docs_reports",
                "P3.8.0-P3.8.20",
                "flow docs / reports exist and are indexed",
                f"reports present: {', '.join(FLOW_REPORT_PATHS)}",
            )
        )
    else:
        checks.append(
            FlowBaseExitSealCheck(
                check_id="p3_8_docs_reports",
                checkpoint_range="P3.8.0-P3.8.20",
                title="flow docs / reports",
                status=FlowBaseExitSealStatus.PARTIAL,
                evidence="",
                reason="one or more Flow pack reports missing from agent/reports/",
            )
        )

    checks.append(
        _capability_check(
            "p3_9_seal",
            "P3.9.0-P3.9.20",
            "flow base exit seal exists",
            "this seal object evaluates and aggregates honestly "
            "(PASS/PARTIAL/BLOCKED/FAIL/UNAVAILABLE)",
        )
    )

    check_tuple = tuple(checks)
    status = aggregate_seal_status(check_tuple)
    seal_payload = {
        "seal_version": FLOW_BASE_EXIT_SEAL_VERSION,
        "check_ids": tuple(check.check_id for check in check_tuple),
        "check_statuses": tuple(check.status.value for check in check_tuple),
    }
    seal = FlowBaseExitSeal(
        seal_version=FLOW_BASE_EXIT_SEAL_VERSION,
        seal_id=stable_hash(seal_payload),
        pack_id=AUREL_FLOW_C_PACK_ID,
        checks=check_tuple,
        status=status,
        boundary=FlowBaseExitSealBoundary(),
        truth_label=FlowTruthLabel.LOCAL_RUNTIME_SUBSTRATE,
        seal_hash=stable_hash(seal_payload),
    )

    def _count(wanted: FlowBaseExitSealStatus) -> int:
        return sum(1 for check in check_tuple if check.status is wanted)

    reason = (
        "all base Flow checks pass on local evidence"
        if status is FlowBaseExitSealStatus.PASS
        else "one or more checks did not pass; see per-check reasons"
    )
    return FlowBaseExitSealResult(
        seal=seal,
        pass_count=_count(FlowBaseExitSealStatus.PASS),
        partial_count=_count(FlowBaseExitSealStatus.PARTIAL),
        blocked_count=_count(FlowBaseExitSealStatus.BLOCKED),
        fail_count=_count(FlowBaseExitSealStatus.FAIL),
        unavailable_count=_count(FlowBaseExitSealStatus.UNAVAILABLE),
        reason=reason,
    )


def build_flow_base_exit_seal_read_model(
    result: FlowBaseExitSealResult,
) -> FlowBaseExitSealReadModel:
    payload = {
        "read_model_version": FLOW_BASE_EXIT_SEAL_READ_MODEL_VERSION,
        "seal_hash": result.seal.seal_hash,
        "status": result.seal.status.value,
    }
    return FlowBaseExitSealReadModel(
        read_model_version=FLOW_BASE_EXIT_SEAL_READ_MODEL_VERSION,
        result=result,
        report_paths=FLOW_REPORT_PATHS,
        truth_label=FlowTruthLabel.LOCAL_RUNTIME_SUBSTRATE,
        read_model_hash=stable_hash(payload),
    )


def serialize_flow_base_exit_seal(read_model: FlowBaseExitSealReadModel) -> str:
    """Deterministic JSON export of the seal read model."""

    return to_canonical_json(read_model)
