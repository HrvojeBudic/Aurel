"""P3-FLOW-K boundary compliance probes / runtime invariant probes (P3.19).

Probes are read-only accountability: a boundary compliance probe checks the
fail-closed boolean and truth-label posture of an existing contract object
and detects violations without enforcing, mutating, or punishing anything;
a runtime invariant probe encodes AurelFlow laws (scheduling intent is not
dispatch, service ref is not endpoint, topology health is not proof, ...) as
deterministic attribute checks and never repairs or rewrites a contract.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Mapping

from .errors import AurelFlowErrorCode, AurelFlowValidationError
from .types import FlowTruthLabel, _CanonicalMixin, stable_hash

BOUNDARY_COMPLIANCE_PROBE_VERSION = "boundary_compliance_probe.v1"
BOUNDARY_COMPLIANCE_FINDING_VERSION = "boundary_compliance_finding.v1"
BOUNDARY_COMPLIANCE_READ_MODEL_VERSION = "boundary_compliance_read_model.v1"
RUNTIME_INVARIANT_PROBE_VERSION = "runtime_invariant_probe.v1"
RUNTIME_INVARIANT_FINDING_VERSION = "runtime_invariant_finding.v1"
RUNTIME_INVARIANT_READ_MODEL_VERSION = "runtime_invariant_read_model.v1"

PROBE_ENFORCEMENT_UNAVAILABLE_REASON = (
    "a probe detects and reports only: it enforces no runtime policy, "
    "mutates no contract, repairs nothing, and punishes nothing — "
    "enforcement belongs to P9 Custos and proof to P5 AurelTrace"
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


class BoundaryComplianceCategory(str, Enum):
    """Closed-world boundary categories a compliance probe may check."""

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
    NO_FAKE_LIVE = "NO_FAKE_LIVE"
    NO_FAKE_TRACE_VERIFIED = "NO_FAKE_TRACE_VERIFIED"
    NO_PRODUCTION_CLAIM = "NO_PRODUCTION_CLAIM"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"


class BoundaryComplianceStatus(str, Enum):
    """Closed-world compliance probe outcomes."""

    PASS = "PASS"
    WARNING = "WARNING"
    FAIL = "FAIL"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"


# Which attributes each category inspects. An attribute that is True on the
# probed object is a boundary violation for that category.
_CATEGORY_FORBIDDEN_ATTRIBUTES: Mapping[
    BoundaryComplianceCategory, tuple[str, ...]
] = {
    BoundaryComplianceCategory.NO_RUNTIME_SUBMIT: ("runtime_submit_wired",),
    BoundaryComplianceCategory.NO_EXECUTION: (
        "execution_available",
        "workflow_executed",
        "execution_performed",
    ),
    BoundaryComplianceCategory.NO_DISPATCH: ("dispatch_available", "dispatched"),
    BoundaryComplianceCategory.NO_SERVICE_RUNTIME: (
        "service_runtime_available",
        "live_process",
        "live_endpoint",
    ),
    BoundaryComplianceCategory.NO_NETWORK: (
        "network_called",
        "network_transport_available",
        "transport_bound",
        "message_sent",
    ),
    BoundaryComplianceCategory.NO_TOOL_CALL: ("tool_invoked",),
    BoundaryComplianceCategory.NO_MODEL_CALL: ("model_invoked",),
    BoundaryComplianceCategory.NO_SANDBOX_EXECUTION: (
        "sandbox_executed",
        "subprocess_spawned",
    ),
    BoundaryComplianceCategory.NO_TRACE_WRITE: ("trace_written",),
    BoundaryComplianceCategory.NO_LEDGER_WRITE: ("ledger_written",),
    BoundaryComplianceCategory.NO_MEMORY_WRITE: ("memory_access_performed",),
    BoundaryComplianceCategory.NO_POLICY_MUTATION: ("policy_mutated",),
    BoundaryComplianceCategory.NO_IDENTITY_MUTATION: ("identity_mutated",),
    BoundaryComplianceCategory.NO_REACT_CONTROL: (
        "frontend_mutation_allowed",
        "ui_dispatch_allowed",
        "ui_schedule_action_allowed",
        "ui_route_action_allowed",
        "ui_service_invocation_allowed",
    ),
    BoundaryComplianceCategory.NO_PRODUCTION_CLAIM: (
        "production_ready",
        "release_approved",
    ),
}

_FORBIDDEN_TRUTH_LABEL_CATEGORIES: Mapping[
    BoundaryComplianceCategory, FlowTruthLabel
] = {
    BoundaryComplianceCategory.NO_FAKE_LIVE: FlowTruthLabel.LIVE,
    BoundaryComplianceCategory.NO_FAKE_TRACE_VERIFIED: (
        FlowTruthLabel.TRACE_VERIFIED
    ),
}


@dataclass(frozen=True)
class BoundaryComplianceFinding(_CanonicalMixin):
    """One detected boundary violation. Detection, never punishment."""

    finding_id: str
    contract_version: str
    probe_category: BoundaryComplianceCategory
    detail: str
    truth_label: FlowTruthLabel
    unavailable_reason: str = PROBE_ENFORCEMENT_UNAVAILABLE_REASON
    enforcement_performed: bool = False
    mutation_performed: bool = False
    punishment_applied: bool = False

    def __post_init__(self) -> None:
        _forbid_true(
            self,
            "enforcement_performed",
            "mutation_performed",
            "punishment_applied",
        )


@dataclass(frozen=True)
class BoundaryComplianceProbe(_CanonicalMixin):
    """One read-only compliance check outcome over one contract object."""

    probe_id: str
    contract_version: str
    probe_category: BoundaryComplianceCategory
    evaluated_contract_id: str
    findings: tuple[BoundaryComplianceFinding, ...]
    status: BoundaryComplianceStatus
    truth_label: FlowTruthLabel
    unavailable_reason: str = PROBE_ENFORCEMENT_UNAVAILABLE_REASON
    read_only: bool = True
    enforcement_performed: bool = False
    mutation_performed: bool = False
    runtime_policy_changed: bool = False
    punishment_applied: bool = False

    def __post_init__(self) -> None:
        _forbid_false(self, "read_only")
        _forbid_true(
            self,
            "enforcement_performed",
            "mutation_performed",
            "runtime_policy_changed",
            "punishment_applied",
        )
        if self.status is BoundaryComplianceStatus.FAIL and not self.findings:
            raise AurelFlowValidationError(
                "a FAIL compliance status requires at least one finding",
                code=AurelFlowErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                field="findings",
            )


def _object_contract_id(subject: object) -> str:
    for id_field in (
        "atomic_unit_id",
        "scheduling_intent_id",
        "service_ref_id",
        "topology_id",
        "health_frame_id",
        "projection_id",
        "envelope_id",
        "handoff_frame_id",
        "bridge_id",
        "read_model_id",
    ):
        value = getattr(subject, id_field, "")
        if value:
            return str(value)
    return type(subject).__name__


def run_boundary_compliance_probe(
    *,
    category: BoundaryComplianceCategory,
    subject: object,
) -> BoundaryComplianceProbe:
    """Deterministic read-only check of one object against one category.

    Inspects the subject's fail-closed booleans / truth label; an attribute
    the subject does not carry is NOT_APPLICABLE evidence, never a pass
    invented from silence. The subject is never mutated.
    """

    evaluated_contract_id = _object_contract_id(subject)
    findings: list[BoundaryComplianceFinding] = []
    applicable = False
    if category in _FORBIDDEN_TRUTH_LABEL_CATEGORIES:
        label = getattr(subject, "truth_label", None)
        applicable = label is not None
        if label is _FORBIDDEN_TRUTH_LABEL_CATEGORIES[category]:
            findings.append(
                _compliance_finding(
                    category,
                    f"{evaluated_contract_id} carries forbidden truth label "
                    f"{label.value}",
                )
            )
    else:
        for attribute in _CATEGORY_FORBIDDEN_ATTRIBUTES.get(category, ()):
            if not hasattr(subject, attribute):
                continue
            applicable = True
            if getattr(subject, attribute):
                findings.append(
                    _compliance_finding(
                        category,
                        f"{evaluated_contract_id}.{attribute} is True",
                    )
                )
    if category in (
        BoundaryComplianceCategory.UNAVAILABLE,
        BoundaryComplianceCategory.ERROR,
    ):
        status = BoundaryComplianceStatus(category.value)
    elif not applicable:
        status = BoundaryComplianceStatus.NOT_APPLICABLE
    elif findings:
        status = BoundaryComplianceStatus.FAIL
    else:
        status = BoundaryComplianceStatus.PASS
    payload = {
        "contract_version": BOUNDARY_COMPLIANCE_PROBE_VERSION,
        "probe_category": category.value,
        "evaluated_contract_id": evaluated_contract_id,
        "finding_ids": tuple(sorted(f.finding_id for f in findings)),
        "status": status.value,
    }
    return BoundaryComplianceProbe(
        probe_id="flkbp-" + stable_hash(payload)[:16],
        contract_version=BOUNDARY_COMPLIANCE_PROBE_VERSION,
        probe_category=category,
        evaluated_contract_id=evaluated_contract_id,
        findings=tuple(findings),
        status=status,
        truth_label=FlowTruthLabel.LOCAL_RUNTIME_SUBSTRATE,
    )


def _compliance_finding(
    category: BoundaryComplianceCategory, detail: str
) -> BoundaryComplianceFinding:
    payload = {
        "contract_version": BOUNDARY_COMPLIANCE_FINDING_VERSION,
        "probe_category": category.value,
        "detail": detail,
    }
    return BoundaryComplianceFinding(
        finding_id="flkbf-" + stable_hash(payload)[:16],
        contract_version=BOUNDARY_COMPLIANCE_FINDING_VERSION,
        probe_category=category,
        detail=detail,
        truth_label=FlowTruthLabel.LOCAL_RUNTIME_SUBSTRATE,
    )


@dataclass(frozen=True)
class BoundaryComplianceReadModel(_CanonicalMixin):
    """Deterministic read model over compliance probes."""

    read_model_id: str
    contract_version: str
    probe_count: int
    status_counts: tuple[tuple[str, int], ...]
    failing_probe_ids: tuple[str, ...]
    all_applicable_passed: bool
    truth_label: FlowTruthLabel
    unavailable_reason: str = PROBE_ENFORCEMENT_UNAVAILABLE_REASON
    enforcement_performed: bool = False
    runtime_policy_changed: bool = False

    def __post_init__(self) -> None:
        _forbid_true(self, "enforcement_performed", "runtime_policy_changed")


def build_boundary_compliance_read_model(
    probes: tuple[BoundaryComplianceProbe, ...],
) -> BoundaryComplianceReadModel:
    status_counts: dict[str, int] = {}
    for probe in probes:
        status_counts[probe.status.value] = (
            status_counts.get(probe.status.value, 0) + 1
        )
    failing = tuple(
        sorted(
            probe.probe_id
            for probe in probes
            if probe.status is BoundaryComplianceStatus.FAIL
        )
    )
    payload = {
        "contract_version": BOUNDARY_COMPLIANCE_READ_MODEL_VERSION,
        "probe_ids": tuple(sorted(p.probe_id for p in probes)),
    }
    return BoundaryComplianceReadModel(
        read_model_id="flkbm-" + stable_hash(payload)[:16],
        contract_version=BOUNDARY_COMPLIANCE_READ_MODEL_VERSION,
        probe_count=len(probes),
        status_counts=tuple(sorted(status_counts.items())),
        failing_probe_ids=failing,
        all_applicable_passed=not failing
        and not any(
            probe.status is BoundaryComplianceStatus.WARNING
            for probe in probes
        ),
        truth_label=FlowTruthLabel.READ_MODEL_ONLY,
    )


class RuntimeInvariantKind(str, Enum):
    """Closed-world AurelFlow laws an invariant probe may check."""

    PROPOSAL_IS_NOT_PERMISSION = "PROPOSAL_IS_NOT_PERMISSION"
    PERMISSION_REQUEST_IS_NOT_PERMISSION = (
        "PERMISSION_REQUEST_IS_NOT_PERMISSION"
    )
    EXECUTION_REQUEST_IS_NOT_EXECUTION = "EXECUTION_REQUEST_IS_NOT_EXECUTION"
    PROOF_EXPECTATION_IS_NOT_PROOF = "PROOF_EXPECTATION_IS_NOT_PROOF"
    OPERATOR_SIGNAL_IS_NOT_AUTHORITY = "OPERATOR_SIGNAL_IS_NOT_AUTHORITY"
    DIAGNOSIS_IS_NOT_PROOF = "DIAGNOSIS_IS_NOT_PROOF"
    RECOVERY_CANDIDATE_IS_NOT_RECOVERY_EXECUTION = (
        "RECOVERY_CANDIDATE_IS_NOT_RECOVERY_EXECUTION"
    )
    CHECKPOINT_IS_NOT_PERSISTENCE_PROOF = "CHECKPOINT_IS_NOT_PERSISTENCE_PROOF"
    REPLAY_PLAN_IS_NOT_REPLAY_EXECUTION = "REPLAY_PLAN_IS_NOT_REPLAY_EXECUTION"
    REVERT_CANDIDATE_IS_NOT_ROLLBACK_EXECUTION = (
        "REVERT_CANDIDATE_IS_NOT_ROLLBACK_EXECUTION"
    )
    AUTONOMY_LEVEL_IS_NOT_AUTHORITY = "AUTONOMY_LEVEL_IS_NOT_AUTHORITY"
    SCOPE_ENVELOPE_IS_NOT_PERMISSION = "SCOPE_ENVELOPE_IS_NOT_PERMISSION"
    SCHEDULING_INTENT_IS_NOT_DISPATCH = "SCHEDULING_INTENT_IS_NOT_DISPATCH"
    RESOURCE_PREDICTION_IS_NOT_ALLOCATION = (
        "RESOURCE_PREDICTION_IS_NOT_ALLOCATION"
    )
    SERVICE_REF_IS_NOT_ENDPOINT = "SERVICE_REF_IS_NOT_ENDPOINT"
    ROUTING_CANDIDATE_IS_NOT_NETWORK_ROUTING = (
        "ROUTING_CANDIDATE_IS_NOT_NETWORK_ROUTING"
    )
    TOPOLOGY_HEALTH_IS_NOT_PROOF = "TOPOLOGY_HEALTH_IS_NOT_PROOF"
    REACT_PROJECTION_IS_NOT_CONTROL = "REACT_PROJECTION_IS_NOT_CONTROL"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"


class RuntimeInvariantStatus(str, Enum):
    """Closed-world invariant probe outcomes."""

    SATISFIED = "SATISFIED"
    WARNING = "WARNING"
    VIOLATED = "VIOLATED"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"


# Attributes that must be False on the probed object for the law to hold.
_INVARIANT_MUST_BE_FALSE: Mapping[RuntimeInvariantKind, tuple[str, ...]] = {
    RuntimeInvariantKind.PROPOSAL_IS_NOT_PERMISSION: (
        "permission_granted",
        "authority_granted",
    ),
    RuntimeInvariantKind.PERMISSION_REQUEST_IS_NOT_PERMISSION: (
        "permission_granted",
    ),
    RuntimeInvariantKind.EXECUTION_REQUEST_IS_NOT_EXECUTION: (
        "execution_available",
        "workflow_executed",
    ),
    RuntimeInvariantKind.PROOF_EXPECTATION_IS_NOT_PROOF: (
        "proof_available",
        "trace_verified",
    ),
    RuntimeInvariantKind.OPERATOR_SIGNAL_IS_NOT_AUTHORITY: (
        "authority_granted",
    ),
    RuntimeInvariantKind.DIAGNOSIS_IS_NOT_PROOF: (
        "proof_available",
        "trace_verified",
    ),
    RuntimeInvariantKind.RECOVERY_CANDIDATE_IS_NOT_RECOVERY_EXECUTION: (
        "recovery_executed",
        "execution_available",
    ),
    RuntimeInvariantKind.CHECKPOINT_IS_NOT_PERSISTENCE_PROOF: (
        "persisted",
        "trace_verified",
    ),
    RuntimeInvariantKind.REPLAY_PLAN_IS_NOT_REPLAY_EXECUTION: (
        "execution_available",
        "workflow_executed",
    ),
    RuntimeInvariantKind.REVERT_CANDIDATE_IS_NOT_ROLLBACK_EXECUTION: (
        "rollback_executed",
        "safe_to_execute",
    ),
    RuntimeInvariantKind.AUTONOMY_LEVEL_IS_NOT_AUTHORITY: (
        "authority_granted",
        "permission_granted",
    ),
    RuntimeInvariantKind.SCOPE_ENVELOPE_IS_NOT_PERMISSION: (
        "scope_authorizes_action",
        "scope_executes_action",
    ),
    RuntimeInvariantKind.SCHEDULING_INTENT_IS_NOT_DISPATCH: (
        "dispatched",
        "queued",
        "execution_available",
    ),
    RuntimeInvariantKind.RESOURCE_PREDICTION_IS_NOT_ALLOCATION: (
        "resource_allocated",
        "resource_reserved",
        "measured_usage",
    ),
    RuntimeInvariantKind.SERVICE_REF_IS_NOT_ENDPOINT: (
        "live_handle",
        "endpoint_available",
        "transport_available",
        "invocation_available",
    ),
    RuntimeInvariantKind.ROUTING_CANDIDATE_IS_NOT_NETWORK_ROUTING: (
        "message_sent",
        "network_called",
        "service_invoked",
    ),
    RuntimeInvariantKind.TOPOLOGY_HEALTH_IS_NOT_PROOF: (
        "proof_available",
        "trace_verified",
        "service_health_checked",
    ),
    RuntimeInvariantKind.REACT_PROJECTION_IS_NOT_CONTROL: (
        "frontend_mutation_allowed",
        "ui_dispatch_allowed",
        "ui_schedule_action_allowed",
        "ui_route_action_allowed",
        "ui_service_invocation_allowed",
        "ui_service_mesh_control_allowed",
    ),
}


@dataclass(frozen=True)
class RuntimeInvariantFinding(_CanonicalMixin):
    """One detected invariant violation. A finding is not repair."""

    finding_id: str
    contract_version: str
    invariant_kind: RuntimeInvariantKind
    detail: str
    truth_label: FlowTruthLabel
    unavailable_reason: str = PROBE_ENFORCEMENT_UNAVAILABLE_REASON
    repair_executed: bool = False
    contract_rewritten: bool = False
    enforcement_performed: bool = False

    def __post_init__(self) -> None:
        _forbid_true(
            self,
            "repair_executed",
            "contract_rewritten",
            "enforcement_performed",
        )


@dataclass(frozen=True)
class RuntimeInvariantProbe(_CanonicalMixin):
    """One read-only invariant check outcome over one contract object."""

    invariant_probe_id: str
    contract_version: str
    invariant_kind: RuntimeInvariantKind
    evaluated_contract_id: str
    findings: tuple[RuntimeInvariantFinding, ...]
    status: RuntimeInvariantStatus
    truth_label: FlowTruthLabel
    unavailable_reason: str = PROBE_ENFORCEMENT_UNAVAILABLE_REASON
    read_only: bool = True
    repair_executed: bool = False
    contract_rewritten: bool = False
    enforcement_performed: bool = False

    def __post_init__(self) -> None:
        _forbid_false(self, "read_only")
        _forbid_true(
            self,
            "repair_executed",
            "contract_rewritten",
            "enforcement_performed",
        )
        if self.status is RuntimeInvariantStatus.VIOLATED and not self.findings:
            raise AurelFlowValidationError(
                "a VIOLATED invariant status requires at least one finding",
                code=AurelFlowErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                field="findings",
            )


def probe_runtime_invariant(
    *,
    invariant_kind: RuntimeInvariantKind,
    subject: object,
) -> RuntimeInvariantProbe:
    """Deterministic read-only law check over one object's boolean posture.

    SATISFIED when every law-relevant attribute the subject carries is False;
    VIOLATED when any is True; NOT_APPLICABLE when the subject carries none
    of the law's attributes. The subject is never mutated or repaired.
    """

    evaluated_contract_id = _object_contract_id(subject)
    findings: list[RuntimeInvariantFinding] = []
    applicable = False
    for attribute in _INVARIANT_MUST_BE_FALSE.get(invariant_kind, ()):
        if not hasattr(subject, attribute):
            continue
        applicable = True
        if getattr(subject, attribute):
            finding_payload = {
                "contract_version": RUNTIME_INVARIANT_FINDING_VERSION,
                "invariant_kind": invariant_kind.value,
                "detail": f"{evaluated_contract_id}.{attribute} is True",
            }
            findings.append(
                RuntimeInvariantFinding(
                    finding_id="flkif-" + stable_hash(finding_payload)[:16],
                    contract_version=RUNTIME_INVARIANT_FINDING_VERSION,
                    invariant_kind=invariant_kind,
                    detail=f"{evaluated_contract_id}.{attribute} is True",
                    truth_label=FlowTruthLabel.LOCAL_RUNTIME_SUBSTRATE,
                )
            )
    if invariant_kind in (
        RuntimeInvariantKind.UNAVAILABLE,
        RuntimeInvariantKind.ERROR,
    ):
        status = RuntimeInvariantStatus(invariant_kind.value)
    elif not applicable:
        status = RuntimeInvariantStatus.NOT_APPLICABLE
    elif findings:
        status = RuntimeInvariantStatus.VIOLATED
    else:
        status = RuntimeInvariantStatus.SATISFIED
    payload = {
        "contract_version": RUNTIME_INVARIANT_PROBE_VERSION,
        "invariant_kind": invariant_kind.value,
        "evaluated_contract_id": evaluated_contract_id,
        "finding_ids": tuple(sorted(f.finding_id for f in findings)),
        "status": status.value,
    }
    return RuntimeInvariantProbe(
        invariant_probe_id="flkip-" + stable_hash(payload)[:16],
        contract_version=RUNTIME_INVARIANT_PROBE_VERSION,
        invariant_kind=invariant_kind,
        evaluated_contract_id=evaluated_contract_id,
        findings=tuple(findings),
        status=status,
        truth_label=FlowTruthLabel.LOCAL_RUNTIME_SUBSTRATE,
    )


@dataclass(frozen=True)
class RuntimeInvariantReadModel(_CanonicalMixin):
    """Deterministic read model over invariant probes."""

    read_model_id: str
    contract_version: str
    probe_count: int
    status_counts: tuple[tuple[str, int], ...]
    violated_probe_ids: tuple[str, ...]
    all_applicable_satisfied: bool
    truth_label: FlowTruthLabel
    unavailable_reason: str = PROBE_ENFORCEMENT_UNAVAILABLE_REASON
    repair_executed: bool = False
    enforcement_performed: bool = False

    def __post_init__(self) -> None:
        _forbid_true(self, "repair_executed", "enforcement_performed")


def build_runtime_invariant_read_model(
    probes: tuple[RuntimeInvariantProbe, ...],
) -> RuntimeInvariantReadModel:
    status_counts: dict[str, int] = {}
    for probe in probes:
        status_counts[probe.status.value] = (
            status_counts.get(probe.status.value, 0) + 1
        )
    violated = tuple(
        sorted(
            probe.invariant_probe_id
            for probe in probes
            if probe.status is RuntimeInvariantStatus.VIOLATED
        )
    )
    payload = {
        "contract_version": RUNTIME_INVARIANT_READ_MODEL_VERSION,
        "probe_ids": tuple(sorted(p.invariant_probe_id for p in probes)),
    }
    return RuntimeInvariantReadModel(
        read_model_id="flkim-" + stable_hash(payload)[:16],
        contract_version=RUNTIME_INVARIANT_READ_MODEL_VERSION,
        probe_count=len(probes),
        status_counts=tuple(sorted(status_counts.items())),
        violated_probe_ids=violated,
        all_applicable_satisfied=not violated
        and not any(
            probe.status is RuntimeInvariantStatus.WARNING for probe in probes
        ),
        truth_label=FlowTruthLabel.READ_MODEL_ONLY,
    )
