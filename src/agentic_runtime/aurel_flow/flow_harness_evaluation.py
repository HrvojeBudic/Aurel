"""P3-FLOW-K runtime harness evaluation core / contract coverage / fixtures (P3.19).

Evaluation is grammar about P3, not more runtime power: a harness suite names
deterministic evaluation cases over existing P3 contracts, a harness run is
never workflow execution, a scenario fixture is DEV_FIXTURE test data and
never a live workflow or production simulation, and a coverage matrix says
which P3 contracts are represented and tested — coverage is not production
readiness and a harness result is not P5 proof. P3-FLOW-L seals, P4 executes,
P5 proves, P9 authorizes.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .errors import AurelFlowErrorCode, AurelFlowValidationError
from .types import FlowTruthLabel, _CanonicalMixin, stable_hash

AUREL_FLOW_K_PACK_ID = "P3-FLOW-K"
AUREL_FLOW_K_PACK_TITLE = (
    "Runtime Harness Evaluation / Quality Operations Pack"
)
AUREL_FLOW_K_REPORT_PATH = (
    "agent/reports/P3_FLOW_K_RUNTIME_HARNESS_EVALUATION_PACK.md"
)

HARNESS_EVALUATION_SUITE_VERSION = "runtime_harness_evaluation_suite.v1"
HARNESS_EVALUATION_RUN_VERSION = "runtime_harness_evaluation_run.v1"
HARNESS_EVALUATION_CASE_VERSION = "runtime_harness_evaluation_case.v1"
HARNESS_EVALUATION_BOUNDARY_VERSION = "runtime_harness_evaluation_boundary.v1"
HARNESS_EVALUATION_READ_MODEL_VERSION = (
    "runtime_harness_evaluation_read_model.v1"
)
CONTRACT_COVERAGE_ITEM_VERSION = "contract_coverage_item.v1"
CONTRACT_COVERAGE_MATRIX_VERSION = "contract_coverage_matrix.v1"
CONTRACT_COVERAGE_READ_MODEL_VERSION = "contract_coverage_read_model.v1"
HARNESS_SCENARIO_FIXTURE_VERSION = "harness_scenario_fixture.v1"
HARNESS_SCENARIO_CATALOG_VERSION = "harness_scenario_catalog.v1"
HARNESS_SCENARIO_READ_MODEL_VERSION = "harness_scenario_read_model.v1"

HARNESS_EXECUTION_UNAVAILABLE_REASON = (
    "a harness evaluation is deterministic local grammar over declared P3 "
    "contracts: no workflow executes, nothing is dispatched, runtime.submit "
    "is not wired, and an evaluation result is never P5 proof or production "
    "readiness — P3-FLOW-L seals, P4 executes, P5 proves, P9 authorizes"
)
FIXTURE_UNAVAILABLE_REASON = (
    "a scenario fixture is deterministic DEV_FIXTURE test data only: it is "
    "not live data, not a live workflow, and not a production simulation"
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


class HarnessScenarioKind(str, Enum):
    """Closed-world deterministic scenario vocabulary. Fixtures, not runs."""

    READY_NODE_FIXTURE = "READY_NODE_FIXTURE"
    WAITING_DEPENDENCY_FIXTURE = "WAITING_DEPENDENCY_FIXTURE"
    PAUSE_REQUIRED_FIXTURE = "PAUSE_REQUIRED_FIXTURE"
    RECOVERY_CANDIDATE_FIXTURE = "RECOVERY_CANDIDATE_FIXTURE"
    AUTHORITY_REQUIRED_FIXTURE = "AUTHORITY_REQUIRED_FIXTURE"
    CHECKPOINT_REQUIRED_FIXTURE = "CHECKPOINT_REQUIRED_FIXTURE"
    REPLAY_CANDIDATE_FIXTURE = "REPLAY_CANDIDATE_FIXTURE"
    RETRY_STORM_FIXTURE = "RETRY_STORM_FIXTURE"
    SEMANTIC_SILENT_FAILURE_FIXTURE = "SEMANTIC_SILENT_FAILURE_FIXTURE"
    AUTONOMY_VIOLATION_FIXTURE = "AUTONOMY_VIOLATION_FIXTURE"
    SCHEDULING_INTENT_FIXTURE = "SCHEDULING_INTENT_FIXTURE"
    SERVICE_REQUIREMENT_FIXTURE = "SERVICE_REQUIREMENT_FIXTURE"
    TOPOLOGY_RISK_FIXTURE = "TOPOLOGY_RISK_FIXTURE"
    P4_HANDOFF_FIXTURE = "P4_HANDOFF_FIXTURE"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"


@dataclass(frozen=True)
class HarnessScenarioFixture(_CanonicalMixin):
    """Deterministic DEV_FIXTURE test data. Never a live workflow."""

    fixture_id: str
    contract_version: str
    fixture_kind: HarnessScenarioKind
    fixture_label: str
    target_contracts: tuple[str, ...]
    truth_label: FlowTruthLabel
    unavailable_reason: str = FIXTURE_UNAVAILABLE_REASON
    deterministic: bool = True
    live_data: bool = False
    live_workflow: bool = False
    production_simulation: bool = False
    workflow_executed: bool = False

    def __post_init__(self) -> None:
        _forbid_false(self, "deterministic")
        _forbid_true(
            self,
            "live_data",
            "live_workflow",
            "production_simulation",
            "workflow_executed",
        )
        if self.truth_label is not FlowTruthLabel.DEV_FIXTURE:
            raise AurelFlowValidationError(
                "a scenario fixture must carry the DEV_FIXTURE truth label",
                code=AurelFlowErrorCode.FORBIDDEN_TRUTH_LABEL,
                field="truth_label",
            )
        if not self.fixture_label:
            raise AurelFlowValidationError(
                "a scenario fixture must carry a label",
                code=AurelFlowErrorCode.EMPTY_NODE_ID,
                field="fixture_label",
            )


def create_harness_scenario_fixture(
    *,
    fixture_kind: HarnessScenarioKind,
    fixture_label: str,
    target_contracts: tuple[str, ...],
) -> HarnessScenarioFixture:
    payload = {
        "contract_version": HARNESS_SCENARIO_FIXTURE_VERSION,
        "fixture_kind": fixture_kind.value,
        "fixture_label": fixture_label,
        "target_contracts": tuple(sorted(target_contracts)),
    }
    return HarnessScenarioFixture(
        fixture_id="flksf-" + stable_hash(payload)[:16],
        contract_version=HARNESS_SCENARIO_FIXTURE_VERSION,
        fixture_kind=fixture_kind,
        fixture_label=fixture_label,
        target_contracts=tuple(sorted(target_contracts)),
        truth_label=FlowTruthLabel.DEV_FIXTURE,
    )


@dataclass(frozen=True)
class HarnessScenarioCatalog(_CanonicalMixin):
    """Deterministic catalog of scenario fixtures."""

    catalog_id: str
    contract_version: str
    fixtures: tuple[HarnessScenarioFixture, ...]
    truth_label: FlowTruthLabel
    unavailable_reason: str = FIXTURE_UNAVAILABLE_REASON
    live_workflow: bool = False
    workflow_executed: bool = False

    def __post_init__(self) -> None:
        _forbid_true(self, "live_workflow", "workflow_executed")
        fixture_ids = [fixture.fixture_id for fixture in self.fixtures]
        if len(fixture_ids) != len(set(fixture_ids)):
            raise AurelFlowValidationError(
                "a scenario catalog must not repeat a fixture",
                code=AurelFlowErrorCode.DUPLICATE_NODE_ID,
                field="fixtures",
            )

    def contains_fixture(self, fixture_id: str) -> bool:
        return any(f.fixture_id == fixture_id for f in self.fixtures)


def build_harness_scenario_catalog(
    fixtures: tuple[HarnessScenarioFixture, ...],
) -> HarnessScenarioCatalog:
    payload = {
        "contract_version": HARNESS_SCENARIO_CATALOG_VERSION,
        "fixture_ids": tuple(sorted(f.fixture_id for f in fixtures)),
    }
    return HarnessScenarioCatalog(
        catalog_id="flksc-" + stable_hash(payload)[:16],
        contract_version=HARNESS_SCENARIO_CATALOG_VERSION,
        fixtures=fixtures,
        truth_label=FlowTruthLabel.DEV_FIXTURE,
    )


@dataclass(frozen=True)
class HarnessScenarioReadModel(_CanonicalMixin):
    """Deterministic read model over a scenario catalog."""

    read_model_id: str
    contract_version: str
    catalog_id: str
    fixture_count: int
    fixture_kind_counts: tuple[tuple[str, int], ...]
    target_contract_count: int
    truth_label: FlowTruthLabel
    unavailable_reason: str = FIXTURE_UNAVAILABLE_REASON
    live_workflow: bool = False
    workflow_executed: bool = False

    def __post_init__(self) -> None:
        _forbid_true(self, "live_workflow", "workflow_executed")


def build_harness_scenario_read_model(
    catalog: HarnessScenarioCatalog,
) -> HarnessScenarioReadModel:
    kind_counts: dict[str, int] = {}
    targets: set[str] = set()
    for fixture in catalog.fixtures:
        kind_counts[fixture.fixture_kind.value] = (
            kind_counts.get(fixture.fixture_kind.value, 0) + 1
        )
        targets.update(fixture.target_contracts)
    payload = {
        "contract_version": HARNESS_SCENARIO_READ_MODEL_VERSION,
        "catalog_id": catalog.catalog_id,
    }
    return HarnessScenarioReadModel(
        read_model_id="flksm-" + stable_hash(payload)[:16],
        contract_version=HARNESS_SCENARIO_READ_MODEL_VERSION,
        catalog_id=catalog.catalog_id,
        fixture_count=len(catalog.fixtures),
        fixture_kind_counts=tuple(sorted(kind_counts.items())),
        target_contract_count=len(targets),
        truth_label=FlowTruthLabel.READ_MODEL_ONLY,
    )


@dataclass(frozen=True)
class RuntimeHarnessEvaluationCase(_CanonicalMixin):
    """One deterministic evaluation case over declared contracts.

    A case binds a scenario fixture to target contracts; it is fixture-backed
    grammar, never a live workflow.
    """

    evaluation_case_id: str
    contract_version: str
    case_label: str
    scenario_fixture_id: str
    target_contracts: tuple[str, ...]
    truth_label: FlowTruthLabel
    unavailable_reason: str = HARNESS_EXECUTION_UNAVAILABLE_REASON
    deterministic: bool = True
    uses_dev_fixtures: bool = True
    live_workflow: bool = False
    workflow_executed: bool = False

    def __post_init__(self) -> None:
        _forbid_false(self, "deterministic", "uses_dev_fixtures")
        _forbid_true(self, "live_workflow", "workflow_executed")
        if not self.target_contracts:
            raise AurelFlowValidationError(
                "an evaluation case must target at least one contract",
                code=AurelFlowErrorCode.EMPTY_NODE_SET,
                field="target_contracts",
            )


def create_harness_evaluation_case(
    *,
    case_label: str,
    fixture: HarnessScenarioFixture,
    target_contracts: tuple[str, ...] = (),
) -> RuntimeHarnessEvaluationCase:
    targets = tuple(sorted(target_contracts or fixture.target_contracts))
    payload = {
        "contract_version": HARNESS_EVALUATION_CASE_VERSION,
        "case_label": case_label,
        "scenario_fixture_id": fixture.fixture_id,
        "target_contracts": targets,
    }
    return RuntimeHarnessEvaluationCase(
        evaluation_case_id="flkec-" + stable_hash(payload)[:16],
        contract_version=HARNESS_EVALUATION_CASE_VERSION,
        case_label=case_label,
        scenario_fixture_id=fixture.fixture_id,
        target_contracts=targets,
        truth_label=FlowTruthLabel.DEV_FIXTURE,
    )


@dataclass(frozen=True)
class RuntimeHarnessEvaluationSuite(_CanonicalMixin):
    """A named set of deterministic evaluation cases over a pack range."""

    evaluation_suite_id: str
    contract_version: str
    suite_label: str
    target_pack_range: str
    cases: tuple[RuntimeHarnessEvaluationCase, ...]
    truth_label: FlowTruthLabel
    unavailable_reason: str = HARNESS_EXECUTION_UNAVAILABLE_REASON
    deterministic: bool = True
    uses_dev_fixtures: bool = True
    live_workflow: bool = False
    workflow_executed: bool = False
    runtime_submit_wired: bool = False

    def __post_init__(self) -> None:
        _forbid_false(self, "deterministic", "uses_dev_fixtures")
        _forbid_true(
            self, "live_workflow", "workflow_executed", "runtime_submit_wired"
        )
        case_ids = [case.evaluation_case_id for case in self.cases]
        if len(case_ids) != len(set(case_ids)):
            raise AurelFlowValidationError(
                "an evaluation suite must not repeat a case",
                code=AurelFlowErrorCode.DUPLICATE_NODE_ID,
                field="cases",
            )
        if not self.cases:
            raise AurelFlowValidationError(
                "an evaluation suite must carry at least one case",
                code=AurelFlowErrorCode.EMPTY_NODE_SET,
                field="cases",
            )


def build_harness_evaluation_suite(
    *,
    suite_label: str,
    target_pack_range: str,
    cases: tuple[RuntimeHarnessEvaluationCase, ...],
) -> RuntimeHarnessEvaluationSuite:
    payload = {
        "contract_version": HARNESS_EVALUATION_SUITE_VERSION,
        "suite_label": suite_label,
        "target_pack_range": target_pack_range,
        "case_ids": tuple(sorted(c.evaluation_case_id for c in cases)),
    }
    return RuntimeHarnessEvaluationSuite(
        evaluation_suite_id="flkes-" + stable_hash(payload)[:16],
        contract_version=HARNESS_EVALUATION_SUITE_VERSION,
        suite_label=suite_label,
        target_pack_range=target_pack_range,
        cases=cases,
        truth_label=FlowTruthLabel.DEV_FIXTURE,
    )


@dataclass(frozen=True)
class RuntimeHarnessEvaluationRun(_CanonicalMixin):
    """One deterministic aggregation of a suite. Not workflow execution.

    The run derives target-contract totals from its suite; nothing runs, and
    the run's identity is a pure function of the suite.
    """

    evaluation_run_id: str
    contract_version: str
    evaluation_suite_id: str
    run_label: str
    target_pack_range: str
    evaluation_case_ids: tuple[str, ...]
    target_contracts: tuple[str, ...]
    truth_label: FlowTruthLabel
    unavailable_reason: str = HARNESS_EXECUTION_UNAVAILABLE_REASON
    deterministic: bool = True
    uses_dev_fixtures: bool = True
    live_workflow: bool = False
    workflow_executed: bool = False
    runtime_submit_wired: bool = False
    proof_available: bool = False
    trace_verified: bool = False
    production_ready: bool = False

    def __post_init__(self) -> None:
        _forbid_false(self, "deterministic", "uses_dev_fixtures")
        _forbid_true(
            self,
            "live_workflow",
            "workflow_executed",
            "runtime_submit_wired",
            "proof_available",
            "trace_verified",
            "production_ready",
        )


def derive_harness_evaluation_run(
    suite: RuntimeHarnessEvaluationSuite,
    *,
    run_label: str = "",
) -> RuntimeHarnessEvaluationRun:
    targets: set[str] = set()
    for case in suite.cases:
        targets.update(case.target_contracts)
    payload = {
        "contract_version": HARNESS_EVALUATION_RUN_VERSION,
        "evaluation_suite_id": suite.evaluation_suite_id,
        "run_label": run_label or suite.suite_label,
    }
    return RuntimeHarnessEvaluationRun(
        evaluation_run_id="flker-" + stable_hash(payload)[:16],
        contract_version=HARNESS_EVALUATION_RUN_VERSION,
        evaluation_suite_id=suite.evaluation_suite_id,
        run_label=run_label or suite.suite_label,
        target_pack_range=suite.target_pack_range,
        evaluation_case_ids=tuple(
            sorted(case.evaluation_case_id for case in suite.cases)
        ),
        target_contracts=tuple(sorted(targets)),
        truth_label=FlowTruthLabel.LOCAL_RUNTIME_SUBSTRATE,
    )


@dataclass(frozen=True)
class RuntimeHarnessEvaluationBoundary(_CanonicalMixin):
    """The harness law as fail-closed data. Evaluation is not execution."""

    boundary_id: str
    contract_version: str
    truth_label: FlowTruthLabel
    unavailable_reason: str = HARNESS_EXECUTION_UNAVAILABLE_REASON
    evaluation_is_not_execution: bool = True
    harness_result_is_not_proof: bool = True
    coverage_is_not_production_readiness: bool = True
    workflow_executed: bool = False
    runtime_submit_wired: bool = False
    dispatch_available: bool = False
    execution_available: bool = False

    def __post_init__(self) -> None:
        _forbid_false(
            self,
            "evaluation_is_not_execution",
            "harness_result_is_not_proof",
            "coverage_is_not_production_readiness",
        )
        _forbid_true(
            self,
            "workflow_executed",
            "runtime_submit_wired",
            "dispatch_available",
            "execution_available",
        )


def build_harness_evaluation_boundary() -> RuntimeHarnessEvaluationBoundary:
    payload = {"contract_version": HARNESS_EVALUATION_BOUNDARY_VERSION}
    return RuntimeHarnessEvaluationBoundary(
        boundary_id="flkeb-" + stable_hash(payload)[:16],
        contract_version=HARNESS_EVALUATION_BOUNDARY_VERSION,
        truth_label=FlowTruthLabel.CONTRACT_ONLY,
    )


@dataclass(frozen=True)
class RuntimeHarnessEvaluationReadModel(_CanonicalMixin):
    """Deterministic read model over one harness run."""

    read_model_id: str
    contract_version: str
    evaluation_run_id: str
    case_count: int
    target_contract_count: int
    boundary: RuntimeHarnessEvaluationBoundary
    truth_label: FlowTruthLabel
    unavailable_reason: str = HARNESS_EXECUTION_UNAVAILABLE_REASON
    workflow_executed: bool = False
    proof_available: bool = False
    production_ready: bool = False

    def __post_init__(self) -> None:
        _forbid_true(
            self, "workflow_executed", "proof_available", "production_ready"
        )


def build_harness_evaluation_read_model(
    run: RuntimeHarnessEvaluationRun,
) -> RuntimeHarnessEvaluationReadModel:
    payload = {
        "contract_version": HARNESS_EVALUATION_READ_MODEL_VERSION,
        "evaluation_run_id": run.evaluation_run_id,
    }
    return RuntimeHarnessEvaluationReadModel(
        read_model_id="flkem-" + stable_hash(payload)[:16],
        contract_version=HARNESS_EVALUATION_READ_MODEL_VERSION,
        evaluation_run_id=run.evaluation_run_id,
        case_count=len(run.evaluation_case_ids),
        target_contract_count=len(run.target_contracts),
        boundary=build_harness_evaluation_boundary(),
        truth_label=FlowTruthLabel.READ_MODEL_ONLY,
    )


class ContractCoverageArea(str, Enum):
    """Closed-world P3 contract areas the coverage matrix may rate."""

    WORKFLOW_GRAPH = "WORKFLOW_GRAPH"
    SCHEDULER_READY_QUEUE = "SCHEDULER_READY_QUEUE"
    RUNTIME_EVENT_STREAM = "RUNTIME_EVENT_STREAM"
    PAUSE_RESUME = "PAUSE_RESUME"
    RECOVERY_CANDIDATE = "RECOVERY_CANDIDATE"
    AUTHORITY_BOUNDARY = "AUTHORITY_BOUNDARY"
    DYNAMIC_GRAPH = "DYNAMIC_GRAPH"
    TOPOLOGY_RISK = "TOPOLOGY_RISK"
    CHECKPOINT_FORK_REPLAY = "CHECKPOINT_FORK_REPLAY"
    REVERT_CANDIDATE = "REVERT_CANDIDATE"
    RELIABILITY_CONTROL = "RELIABILITY_CONTROL"
    AUTONOMY_ENVELOPE = "AUTONOMY_ENVELOPE"
    SCHEDULING_INTENT = "SCHEDULING_INTENT"
    RESOURCE_PREDICTION = "RESOURCE_PREDICTION"
    COMPOUND_TOPOLOGY = "COMPOUND_TOPOLOGY"
    SERVICE_REF_BOUNDARY = "SERVICE_REF_BOUNDARY"
    P4_HANDOFF_CLARITY = "P4_HANDOFF_CLARITY"
    PROJECTION_ENVELOPE = "PROJECTION_ENVELOPE"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"


class ContractCoverageStatus(str, Enum):
    """Closed-world coverage statuses. COVERED is not production-ready."""

    COVERED = "COVERED"
    PARTIAL = "PARTIAL"
    MISSING = "MISSING"
    UNAVAILABLE = "UNAVAILABLE"
    BLOCKED = "BLOCKED"
    ERROR = "ERROR"


@dataclass(frozen=True)
class ContractCoverageItem(_CanonicalMixin):
    """One area's coverage rating with its evidence pointer."""

    coverage_item_id: str
    contract_version: str
    coverage_area: ContractCoverageArea
    status: ContractCoverageStatus
    evidence_note: str
    truth_label: FlowTruthLabel
    unavailable_reason: str = HARNESS_EXECUTION_UNAVAILABLE_REASON
    production_ready: bool = False
    proof_available: bool = False

    def __post_init__(self) -> None:
        _forbid_true(self, "production_ready", "proof_available")
        if (
            self.status
            in (ContractCoverageStatus.MISSING, ContractCoverageStatus.BLOCKED)
            and not self.evidence_note
        ):
            raise AurelFlowValidationError(
                "a MISSING/BLOCKED coverage item must explain itself",
                code=AurelFlowErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                field="evidence_note",
            )


def create_contract_coverage_item(
    *,
    coverage_area: ContractCoverageArea,
    status: ContractCoverageStatus,
    evidence_note: str,
) -> ContractCoverageItem:
    payload = {
        "contract_version": CONTRACT_COVERAGE_ITEM_VERSION,
        "coverage_area": coverage_area.value,
        "status": status.value,
        "evidence_note": evidence_note,
    }
    return ContractCoverageItem(
        coverage_item_id="flkci-" + stable_hash(payload)[:16],
        contract_version=CONTRACT_COVERAGE_ITEM_VERSION,
        coverage_area=coverage_area,
        status=status,
        evidence_note=evidence_note,
        truth_label=FlowTruthLabel.LOCAL_RUNTIME_SUBSTRATE,
    )


@dataclass(frozen=True)
class ContractCoverageMatrix(_CanonicalMixin):
    """Coverage over P3 contract areas. Coverage is not readiness or proof."""

    coverage_matrix_id: str
    contract_version: str
    evaluation_run_id: str
    coverage_items: tuple[ContractCoverageItem, ...]
    covered_count: int
    partial_count: int
    missing_count: int
    unavailable_count: int
    blocked_count: int
    truth_label: FlowTruthLabel
    unavailable_reason: str = HARNESS_EXECUTION_UNAVAILABLE_REASON
    production_ready: bool = False
    proof_available: bool = False
    trace_verified: bool = False

    def __post_init__(self) -> None:
        _forbid_true(
            self, "production_ready", "proof_available", "trace_verified"
        )
        areas = [item.coverage_area for item in self.coverage_items]
        if len(areas) != len(set(areas)):
            raise AurelFlowValidationError(
                "a coverage matrix must rate each area at most once",
                code=AurelFlowErrorCode.DUPLICATE_NODE_ID,
                field="coverage_items",
            )


def build_contract_coverage_matrix(
    *,
    run: RuntimeHarnessEvaluationRun,
    coverage_items: tuple[ContractCoverageItem, ...],
) -> ContractCoverageMatrix:
    def count(status: ContractCoverageStatus) -> int:
        return sum(1 for item in coverage_items if item.status is status)

    payload = {
        "contract_version": CONTRACT_COVERAGE_MATRIX_VERSION,
        "evaluation_run_id": run.evaluation_run_id,
        "coverage_item_ids": tuple(
            sorted(item.coverage_item_id for item in coverage_items)
        ),
    }
    return ContractCoverageMatrix(
        coverage_matrix_id="flkcm-" + stable_hash(payload)[:16],
        contract_version=CONTRACT_COVERAGE_MATRIX_VERSION,
        evaluation_run_id=run.evaluation_run_id,
        coverage_items=coverage_items,
        covered_count=count(ContractCoverageStatus.COVERED),
        partial_count=count(ContractCoverageStatus.PARTIAL),
        missing_count=count(ContractCoverageStatus.MISSING),
        unavailable_count=count(ContractCoverageStatus.UNAVAILABLE),
        blocked_count=count(ContractCoverageStatus.BLOCKED),
        truth_label=FlowTruthLabel.LOCAL_RUNTIME_SUBSTRATE,
    )


@dataclass(frozen=True)
class ContractCoverageReadModel(_CanonicalMixin):
    """Deterministic read model over one coverage matrix."""

    read_model_id: str
    contract_version: str
    coverage_matrix_id: str
    evaluation_run_id: str
    area_count: int
    status_counts: tuple[tuple[str, int], ...]
    fully_covered: bool
    truth_label: FlowTruthLabel
    unavailable_reason: str = HARNESS_EXECUTION_UNAVAILABLE_REASON
    production_ready: bool = False
    proof_available: bool = False

    def __post_init__(self) -> None:
        _forbid_true(self, "production_ready", "proof_available")


def build_contract_coverage_read_model(
    matrix: ContractCoverageMatrix,
) -> ContractCoverageReadModel:
    status_counts: dict[str, int] = {}
    for item in matrix.coverage_items:
        status_counts[item.status.value] = (
            status_counts.get(item.status.value, 0) + 1
        )
    payload = {
        "contract_version": CONTRACT_COVERAGE_READ_MODEL_VERSION,
        "coverage_matrix_id": matrix.coverage_matrix_id,
    }
    return ContractCoverageReadModel(
        read_model_id="flkcr-" + stable_hash(payload)[:16],
        contract_version=CONTRACT_COVERAGE_READ_MODEL_VERSION,
        coverage_matrix_id=matrix.coverage_matrix_id,
        evaluation_run_id=matrix.evaluation_run_id,
        area_count=len(matrix.coverage_items),
        status_counts=tuple(sorted(status_counts.items())),
        fully_covered=bool(matrix.coverage_items)
        and matrix.covered_count == len(matrix.coverage_items),
        truth_label=FlowTruthLabel.READ_MODEL_ONLY,
    )
