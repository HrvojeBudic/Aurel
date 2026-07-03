"""P3-FLOW-K quality scorecards / regression guard rails / P4 readiness (P3.19).

A quality scorecard is advisory only — a score is never proof, release
approval, or production readiness. A regression guard rail reports risk and
never blocks git or enforces CI. A P4 handoff readiness assessment makes P4
gaps visible without implementing dispatch, wiring runtime.submit, or
allocating a worker.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .errors import AurelFlowErrorCode, AurelFlowValidationError
from .flow_harness_evaluation import RuntimeHarnessEvaluationRun
from .types import FlowTruthLabel, _CanonicalMixin, stable_hash

QUALITY_METRIC_ITEM_VERSION = "quality_metric_item.v1"
RUNTIME_QUALITY_SCORECARD_VERSION = "runtime_quality_scorecard.v1"
QUALITY_SCORECARD_READ_MODEL_VERSION = "quality_scorecard_read_model.v1"
REGRESSION_GUARD_FINDING_VERSION = "regression_guard_finding.v1"
RUNTIME_REGRESSION_GUARD_RAIL_VERSION = "runtime_regression_guard_rail.v1"
REGRESSION_GUARD_READ_MODEL_VERSION = "regression_guard_read_model.v1"
P4_HANDOFF_GAP_VERSION = "p4_handoff_gap.v1"
P4_HANDOFF_RISK_VERSION = "p4_handoff_risk.v1"
P4_HANDOFF_READINESS_ASSESSMENT_VERSION = (
    "p4_handoff_readiness_assessment.v1"
)
P4_HANDOFF_READ_MODEL_VERSION = "p4_handoff_read_model.v1"

ADVISORY_UNAVAILABLE_REASON = (
    "quality scores, regression guard findings, and P4 readiness checks are "
    "advisory reports only: no score is proof, no score approves a release, "
    "no guard blocks git or enforces CI, and no readiness check implements "
    "P4 — P3-FLOW-L seals, P4 executes, P5 proves, P9 authorizes"
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


class QualityMetric(str, Enum):
    """Closed-world advisory quality metric vocabulary."""

    CONTRACT_COMPLETENESS = "CONTRACT_COMPLETENESS"
    BOUNDARY_CLARITY = "BOUNDARY_CLARITY"
    DETERMINISM = "DETERMINISM"
    CLOSED_WORLD_VALIDATION = "CLOSED_WORLD_VALIDATION"
    PROJECTION_SAFETY = "PROJECTION_SAFETY"
    P4_HANDOFF_CLARITY = "P4_HANDOFF_CLARITY"
    P5_PROOF_AWARENESS = "P5_PROOF_AWARENESS"
    P9_AUTHORITY_AWARENESS = "P9_AUTHORITY_AWARENESS"
    TEST_COVERAGE = "TEST_COVERAGE"
    REPORT_COVERAGE = "REPORT_COVERAGE"
    OPERATIONAL_DEBT_RISK = "OPERATIONAL_DEBT_RISK"
    DX_COMPLEXITY_RISK = "DX_COMPLEXITY_RISK"
    SEAL_READINESS = "SEAL_READINESS"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"


class QualityMetricStatus(str, Enum):
    """Closed-world advisory metric statuses. STRONG is not approval."""

    STRONG = "STRONG"
    ACCEPTABLE = "ACCEPTABLE"
    PARTIAL = "PARTIAL"
    WEAK = "WEAK"
    MISSING = "MISSING"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"


@dataclass(frozen=True)
class QualityMetricItem(_CanonicalMixin):
    """One advisory metric rating with rationale. Never approval."""

    metric_item_id: str
    contract_version: str
    metric: QualityMetric
    status: QualityMetricStatus
    rationale: str
    truth_label: FlowTruthLabel
    unavailable_reason: str = ADVISORY_UNAVAILABLE_REASON
    advisory_only: bool = True
    score_is_proof: bool = False

    def __post_init__(self) -> None:
        _forbid_false(self, "advisory_only")
        _forbid_true(self, "score_is_proof")
        if not self.rationale:
            raise AurelFlowValidationError(
                "a quality metric rating must carry a rationale",
                code=AurelFlowErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                field="rationale",
            )


def create_quality_metric_item(
    *,
    metric: QualityMetric,
    status: QualityMetricStatus,
    rationale: str,
) -> QualityMetricItem:
    payload = {
        "contract_version": QUALITY_METRIC_ITEM_VERSION,
        "metric": metric.value,
        "status": status.value,
        "rationale": rationale,
    }
    return QualityMetricItem(
        metric_item_id="flkqi-" + stable_hash(payload)[:16],
        contract_version=QUALITY_METRIC_ITEM_VERSION,
        metric=metric,
        status=status,
        rationale=rationale,
        truth_label=FlowTruthLabel.LOCAL_RUNTIME_SUBSTRATE,
    )


@dataclass(frozen=True)
class RuntimeQualityScorecard(_CanonicalMixin):
    """Advisory quality state for one evaluation run. Not a release gate."""

    scorecard_id: str
    contract_version: str
    evaluation_run_id: str
    metric_items: tuple[QualityMetricItem, ...]
    truth_label: FlowTruthLabel
    unavailable_reason: str = ADVISORY_UNAVAILABLE_REASON
    advisory_only: bool = True
    score_is_proof: bool = False
    release_approved: bool = False
    production_ready: bool = False
    operator_approval_granted: bool = False

    def __post_init__(self) -> None:
        _forbid_false(self, "advisory_only")
        _forbid_true(
            self,
            "score_is_proof",
            "release_approved",
            "production_ready",
            "operator_approval_granted",
        )
        metrics = [item.metric for item in self.metric_items]
        if len(metrics) != len(set(metrics)):
            raise AurelFlowValidationError(
                "a scorecard must rate each metric at most once",
                code=AurelFlowErrorCode.DUPLICATE_NODE_ID,
                field="metric_items",
            )


def build_runtime_quality_scorecard(
    *,
    run: RuntimeHarnessEvaluationRun,
    metric_items: tuple[QualityMetricItem, ...],
) -> RuntimeQualityScorecard:
    payload = {
        "contract_version": RUNTIME_QUALITY_SCORECARD_VERSION,
        "evaluation_run_id": run.evaluation_run_id,
        "metric_item_ids": tuple(
            sorted(item.metric_item_id for item in metric_items)
        ),
    }
    return RuntimeQualityScorecard(
        scorecard_id="flkqs-" + stable_hash(payload)[:16],
        contract_version=RUNTIME_QUALITY_SCORECARD_VERSION,
        evaluation_run_id=run.evaluation_run_id,
        metric_items=metric_items,
        truth_label=FlowTruthLabel.LOCAL_RUNTIME_SUBSTRATE,
    )


@dataclass(frozen=True)
class QualityScorecardReadModel(_CanonicalMixin):
    """Deterministic read model over one scorecard."""

    read_model_id: str
    contract_version: str
    scorecard_id: str
    evaluation_run_id: str
    metric_count: int
    status_counts: tuple[tuple[str, int], ...]
    weak_or_missing_metric_values: tuple[str, ...]
    truth_label: FlowTruthLabel
    unavailable_reason: str = ADVISORY_UNAVAILABLE_REASON
    advisory_only: bool = True
    release_approved: bool = False
    production_ready: bool = False

    def __post_init__(self) -> None:
        _forbid_false(self, "advisory_only")
        _forbid_true(self, "release_approved", "production_ready")


def build_quality_scorecard_read_model(
    scorecard: RuntimeQualityScorecard,
) -> QualityScorecardReadModel:
    status_counts: dict[str, int] = {}
    weak_or_missing: list[str] = []
    for item in scorecard.metric_items:
        status_counts[item.status.value] = (
            status_counts.get(item.status.value, 0) + 1
        )
        if item.status in (
            QualityMetricStatus.WEAK,
            QualityMetricStatus.MISSING,
        ):
            weak_or_missing.append(item.metric.value)
    payload = {
        "contract_version": QUALITY_SCORECARD_READ_MODEL_VERSION,
        "scorecard_id": scorecard.scorecard_id,
    }
    return QualityScorecardReadModel(
        read_model_id="flkqm-" + stable_hash(payload)[:16],
        contract_version=QUALITY_SCORECARD_READ_MODEL_VERSION,
        scorecard_id=scorecard.scorecard_id,
        evaluation_run_id=scorecard.evaluation_run_id,
        metric_count=len(scorecard.metric_items),
        status_counts=tuple(sorted(status_counts.items())),
        weak_or_missing_metric_values=tuple(sorted(weak_or_missing)),
        truth_label=FlowTruthLabel.READ_MODEL_ONLY,
    )


class RegressionGuardKind(str, Enum):
    """Closed-world regression guard vocabulary. Reports, never CI."""

    NO_NEW_EXECUTION_IN_P3 = "NO_NEW_EXECUTION_IN_P3"
    NO_NEW_AUTHORITY_IN_P3 = "NO_NEW_AUTHORITY_IN_P3"
    NO_NEW_NETWORK_IN_P3 = "NO_NEW_NETWORK_IN_P3"
    NO_NEW_SERVICE_RUNTIME_IN_P3 = "NO_NEW_SERVICE_RUNTIME_IN_P3"
    NO_FAKE_LIVE_LABEL = "NO_FAKE_LIVE_LABEL"
    NO_FAKE_TRACE_VERIFIED_LABEL = "NO_FAKE_TRACE_VERIFIED_LABEL"
    NO_PRODUCTION_READY_CLAIM = "NO_PRODUCTION_READY_CLAIM"
    NO_P4_IMPLEMENTED_BEFORE_P3_SEAL = "NO_P4_IMPLEMENTED_BEFORE_P3_SEAL"
    NO_P5_IMPLEMENTED_BEFORE_P3_SEAL = "NO_P5_IMPLEMENTED_BEFORE_P3_SEAL"
    NO_P9_IMPLEMENTED_BEFORE_P3_SEAL = "NO_P9_IMPLEMENTED_BEFORE_P3_SEAL"
    NO_FRONTEND_CONTROL_SURFACE_IN_P3 = "NO_FRONTEND_CONTROL_SURFACE_IN_P3"
    NO_BROAD_DSL_EXPANSION_IN_K = "NO_BROAD_DSL_EXPANSION_IN_K"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"


class RegressionGuardStatus(str, Enum):
    """Closed-world guard outcomes."""

    PASS = "PASS"
    WARNING = "WARNING"
    FAIL = "FAIL"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"


class RegressionGuardSeverity(str, Enum):
    """Finding severity feeding the guard status ladder."""

    WARNING = "WARNING"
    FAIL = "FAIL"


@dataclass(frozen=True)
class RegressionGuardFinding(_CanonicalMixin):
    """One reported regression risk. Report, not enforcement."""

    finding_id: str
    contract_version: str
    guard_kind: RegressionGuardKind
    severity: RegressionGuardSeverity
    detail: str
    truth_label: FlowTruthLabel
    unavailable_reason: str = ADVISORY_UNAVAILABLE_REASON
    ci_enforced: bool = False
    git_blocked: bool = False
    runtime_mutated: bool = False

    def __post_init__(self) -> None:
        _forbid_true(self, "ci_enforced", "git_blocked", "runtime_mutated")


def create_regression_guard_finding(
    *,
    guard_kind: RegressionGuardKind,
    severity: RegressionGuardSeverity,
    detail: str,
) -> RegressionGuardFinding:
    payload = {
        "contract_version": REGRESSION_GUARD_FINDING_VERSION,
        "guard_kind": guard_kind.value,
        "severity": severity.value,
        "detail": detail,
    }
    return RegressionGuardFinding(
        finding_id="flkgf-" + stable_hash(payload)[:16],
        contract_version=REGRESSION_GUARD_FINDING_VERSION,
        guard_kind=guard_kind,
        severity=severity,
        detail=detail,
        truth_label=FlowTruthLabel.LOCAL_RUNTIME_SUBSTRATE,
    )


@dataclass(frozen=True)
class RuntimeRegressionGuardRail(_CanonicalMixin):
    """One guard rail outcome. Status derives from findings; nothing blocks."""

    guard_rail_id: str
    contract_version: str
    guard_kind: RegressionGuardKind
    findings: tuple[RegressionGuardFinding, ...]
    status: RegressionGuardStatus
    truth_label: FlowTruthLabel
    unavailable_reason: str = ADVISORY_UNAVAILABLE_REASON
    report_only: bool = True
    ci_enforced: bool = False
    git_blocked: bool = False
    runtime_mutated: bool = False

    def __post_init__(self) -> None:
        _forbid_false(self, "report_only")
        _forbid_true(self, "ci_enforced", "git_blocked", "runtime_mutated")
        for finding in self.findings:
            if finding.guard_kind is not self.guard_kind:
                raise AurelFlowValidationError(
                    "a guard rail may only carry findings of its own kind",
                    code=AurelFlowErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                    field="findings",
                )


def evaluate_regression_guard_rail(
    *,
    guard_kind: RegressionGuardKind,
    findings: tuple[RegressionGuardFinding, ...] = (),
) -> RuntimeRegressionGuardRail:
    """Deterministic status ladder: FAIL finding > WARNING finding > PASS."""

    if any(
        finding.severity is RegressionGuardSeverity.FAIL
        for finding in findings
    ):
        status = RegressionGuardStatus.FAIL
    elif findings:
        status = RegressionGuardStatus.WARNING
    else:
        status = RegressionGuardStatus.PASS
    payload = {
        "contract_version": RUNTIME_REGRESSION_GUARD_RAIL_VERSION,
        "guard_kind": guard_kind.value,
        "finding_ids": tuple(sorted(f.finding_id for f in findings)),
        "status": status.value,
    }
    return RuntimeRegressionGuardRail(
        guard_rail_id="flkgr-" + stable_hash(payload)[:16],
        contract_version=RUNTIME_REGRESSION_GUARD_RAIL_VERSION,
        guard_kind=guard_kind,
        findings=findings,
        status=status,
        truth_label=FlowTruthLabel.LOCAL_RUNTIME_SUBSTRATE,
    )


@dataclass(frozen=True)
class RegressionGuardReadModel(_CanonicalMixin):
    """Deterministic read model over guard rails."""

    read_model_id: str
    contract_version: str
    guard_rail_count: int
    status_counts: tuple[tuple[str, int], ...]
    failing_guard_kind_values: tuple[str, ...]
    all_passed: bool
    truth_label: FlowTruthLabel
    unavailable_reason: str = ADVISORY_UNAVAILABLE_REASON
    report_only: bool = True
    ci_enforced: bool = False
    git_blocked: bool = False

    def __post_init__(self) -> None:
        _forbid_false(self, "report_only")
        _forbid_true(self, "ci_enforced", "git_blocked")


def build_regression_guard_read_model(
    guard_rails: tuple[RuntimeRegressionGuardRail, ...],
) -> RegressionGuardReadModel:
    status_counts: dict[str, int] = {}
    failing: list[str] = []
    for rail in guard_rails:
        status_counts[rail.status.value] = (
            status_counts.get(rail.status.value, 0) + 1
        )
        if rail.status is RegressionGuardStatus.FAIL:
            failing.append(rail.guard_kind.value)
    payload = {
        "contract_version": REGRESSION_GUARD_READ_MODEL_VERSION,
        "guard_rail_ids": tuple(sorted(r.guard_rail_id for r in guard_rails)),
    }
    return RegressionGuardReadModel(
        read_model_id="flkgm-" + stable_hash(payload)[:16],
        contract_version=REGRESSION_GUARD_READ_MODEL_VERSION,
        guard_rail_count=len(guard_rails),
        status_counts=tuple(sorted(status_counts.items())),
        failing_guard_kind_values=tuple(sorted(failing)),
        all_passed=all(
            rail.status
            in (
                RegressionGuardStatus.PASS,
                RegressionGuardStatus.NOT_APPLICABLE,
            )
            for rail in guard_rails
        ),
        truth_label=FlowTruthLabel.READ_MODEL_ONLY,
    )


class P4HandoffReadinessCheck(str, Enum):
    """Closed-world P4 readiness checks. Readiness is not P4."""

    FLOW_READY_NODE_SURFACE_EXISTS = "FLOW_READY_NODE_SURFACE_EXISTS"
    SCHEDULING_INTENT_EXISTS = "SCHEDULING_INTENT_EXISTS"
    EXECUTION_REQUEST_CANDIDATE_EXISTS = "EXECUTION_REQUEST_CANDIDATE_EXISTS"
    SERVICE_REF_CONSUMPTION_SURFACE_EXISTS = (
        "SERVICE_REF_CONSUMPTION_SURFACE_EXISTS"
    )
    RUNTIME_SUBMIT_BOUNDARY_MARKED_UNAVAILABLE = (
        "RUNTIME_SUBMIT_BOUNDARY_MARKED_UNAVAILABLE"
    )
    P5_PROOF_BOUNDARY_MARKED_UNAVAILABLE = (
        "P5_PROOF_BOUNDARY_MARKED_UNAVAILABLE"
    )
    P9_AUTHORITY_BOUNDARY_MARKED_UNAVAILABLE = (
        "P9_AUTHORITY_BOUNDARY_MARKED_UNAVAILABLE"
    )
    NO_SERVICE_MESH_OVERREACH = "NO_SERVICE_MESH_OVERREACH"
    NO_RUNTIME_SUBMIT_WIRED = "NO_RUNTIME_SUBMIT_WIRED"
    P4_MINIMAL_BRIDGE_INPUTS_VISIBLE = "P4_MINIMAL_BRIDGE_INPUTS_VISIBLE"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"


@dataclass(frozen=True)
class P4HandoffGap(_CanonicalMixin):
    """One visible P4 readiness gap. Visibility, not implementation."""

    gap_id: str
    contract_version: str
    readiness_check: P4HandoffReadinessCheck
    detail: str
    truth_label: FlowTruthLabel
    unavailable_reason: str = ADVISORY_UNAVAILABLE_REASON
    p4_implemented: bool = False

    def __post_init__(self) -> None:
        _forbid_true(self, "p4_implemented")


def create_p4_handoff_gap(
    *, readiness_check: P4HandoffReadinessCheck, detail: str
) -> P4HandoffGap:
    payload = {
        "contract_version": P4_HANDOFF_GAP_VERSION,
        "readiness_check": readiness_check.value,
        "detail": detail,
    }
    return P4HandoffGap(
        gap_id="flkpg-" + stable_hash(payload)[:16],
        contract_version=P4_HANDOFF_GAP_VERSION,
        readiness_check=readiness_check,
        detail=detail,
        truth_label=FlowTruthLabel.LOCAL_RUNTIME_SUBSTRATE,
    )


@dataclass(frozen=True)
class P4HandoffRisk(_CanonicalMixin):
    """One named risk P4 will inherit. A risk note, not mitigation."""

    risk_id: str
    contract_version: str
    risk_label: str
    detail: str
    truth_label: FlowTruthLabel
    unavailable_reason: str = ADVISORY_UNAVAILABLE_REASON
    mitigated: bool = False
    p4_implemented: bool = False

    def __post_init__(self) -> None:
        _forbid_true(self, "mitigated", "p4_implemented")


def create_p4_handoff_risk(*, risk_label: str, detail: str) -> P4HandoffRisk:
    payload = {
        "contract_version": P4_HANDOFF_RISK_VERSION,
        "risk_label": risk_label,
        "detail": detail,
    }
    return P4HandoffRisk(
        risk_id="flkpr-" + stable_hash(payload)[:16],
        contract_version=P4_HANDOFF_RISK_VERSION,
        risk_label=risk_label,
        detail=detail,
        truth_label=FlowTruthLabel.LOCAL_RUNTIME_SUBSTRATE,
    )


@dataclass(frozen=True)
class P4HandoffReadinessAssessment(_CanonicalMixin):
    """Whether P3 clearly prepares P4. Assessment, never implementation.

    Every unsatisfied check must carry an explaining gap — readiness cannot
    silently drop a failed check.
    """

    p4_handoff_readiness_id: str
    contract_version: str
    evaluation_run_id: str
    readiness_check_results: tuple[tuple[P4HandoffReadinessCheck, bool], ...]
    gaps: tuple[P4HandoffGap, ...]
    risks: tuple[P4HandoffRisk, ...]
    minimal_bridge_inputs: tuple[str, ...]
    ready_candidate: bool
    truth_label: FlowTruthLabel
    unavailable_reason: str = ADVISORY_UNAVAILABLE_REASON
    p4_implemented: bool = False
    runtime_submit_wired: bool = False
    dispatch_available: bool = False
    execution_available: bool = False
    worker_allocated: bool = False

    def __post_init__(self) -> None:
        _forbid_true(
            self,
            "p4_implemented",
            "runtime_submit_wired",
            "dispatch_available",
            "execution_available",
            "worker_allocated",
        )
        checks = [check for check, _satisfied in self.readiness_check_results]
        if len(checks) != len(set(checks)):
            raise AurelFlowValidationError(
                "an assessment must rate each readiness check at most once",
                code=AurelFlowErrorCode.DUPLICATE_NODE_ID,
                field="readiness_check_results",
            )
        gap_checks = {gap.readiness_check for gap in self.gaps}
        for check, satisfied in self.readiness_check_results:
            if not satisfied and check not in gap_checks:
                raise AurelFlowValidationError(
                    f"unsatisfied check {check.value} must carry a gap",
                    code=AurelFlowErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                    field="gaps",
                )


def assess_p4_handoff_readiness(
    *,
    run: RuntimeHarnessEvaluationRun,
    readiness_check_results: tuple[tuple[P4HandoffReadinessCheck, bool], ...],
    gaps: tuple[P4HandoffGap, ...] = (),
    risks: tuple[P4HandoffRisk, ...] = (),
    minimal_bridge_inputs: tuple[str, ...] = (),
) -> P4HandoffReadinessAssessment:
    payload = {
        "contract_version": P4_HANDOFF_READINESS_ASSESSMENT_VERSION,
        "evaluation_run_id": run.evaluation_run_id,
        "readiness_check_results": tuple(
            (check.value, satisfied)
            for check, satisfied in readiness_check_results
        ),
        "gap_ids": tuple(sorted(gap.gap_id for gap in gaps)),
        "risk_ids": tuple(sorted(risk.risk_id for risk in risks)),
    }
    return P4HandoffReadinessAssessment(
        p4_handoff_readiness_id="flkpa-" + stable_hash(payload)[:16],
        contract_version=P4_HANDOFF_READINESS_ASSESSMENT_VERSION,
        evaluation_run_id=run.evaluation_run_id,
        readiness_check_results=readiness_check_results,
        gaps=gaps,
        risks=risks,
        minimal_bridge_inputs=tuple(sorted(minimal_bridge_inputs)),
        ready_candidate=bool(readiness_check_results)
        and all(satisfied for _check, satisfied in readiness_check_results),
        truth_label=FlowTruthLabel.LOCAL_RUNTIME_SUBSTRATE,
    )


@dataclass(frozen=True)
class P4HandoffReadModel(_CanonicalMixin):
    """Deterministic read model over one P4 readiness assessment."""

    read_model_id: str
    contract_version: str
    p4_handoff_readiness_id: str
    evaluation_run_id: str
    check_count: int
    satisfied_count: int
    gap_count: int
    risk_count: int
    ready_candidate: bool
    truth_label: FlowTruthLabel
    unavailable_reason: str = ADVISORY_UNAVAILABLE_REASON
    p4_implemented: bool = False
    runtime_submit_wired: bool = False
    dispatch_available: bool = False
    execution_available: bool = False

    def __post_init__(self) -> None:
        _forbid_true(
            self,
            "p4_implemented",
            "runtime_submit_wired",
            "dispatch_available",
            "execution_available",
        )


def build_p4_handoff_read_model(
    assessment: P4HandoffReadinessAssessment,
) -> P4HandoffReadModel:
    payload = {
        "contract_version": P4_HANDOFF_READ_MODEL_VERSION,
        "p4_handoff_readiness_id": assessment.p4_handoff_readiness_id,
    }
    return P4HandoffReadModel(
        read_model_id="flkpm-" + stable_hash(payload)[:16],
        contract_version=P4_HANDOFF_READ_MODEL_VERSION,
        p4_handoff_readiness_id=assessment.p4_handoff_readiness_id,
        evaluation_run_id=assessment.evaluation_run_id,
        check_count=len(assessment.readiness_check_results),
        satisfied_count=sum(
            1
            for _check, satisfied in assessment.readiness_check_results
            if satisfied
        ),
        gap_count=len(assessment.gaps),
        risk_count=len(assessment.risks),
        ready_candidate=assessment.ready_candidate,
        truth_label=FlowTruthLabel.READ_MODEL_ONLY,
    )
