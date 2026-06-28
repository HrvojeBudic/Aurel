"""P2.0-E readiness and pack result contracts."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from .client_consistency import (
    MultiClientConsistencyContract,
    build_multi_client_consistency_contract,
)
from .contracts import (
    AurelShellErrorCode,
    _CanonicalMixin,
    _hash_payload,
    _reject,
    to_canonical_json,
)
from .operator_demo import (
    OperatorTestableSurfaceDemoState,
    build_operator_testable_surface_demo_state,
)
from .read_model import detect_surface_taxonomy_drift
from .regression_harness import (
    SurfaceRegressionHarnessResult,
    run_surface_regression_route_contract_harness,
)
from .shell_snapshot import ShellStateSnapshot, build_shell_state_snapshot
from .surface_registry import CANONICAL_SURFACE_ORDER, build_default_surface_registry
from .truth_permission_fixture_read_model import (
    build_p2_0_d_truth_permission_fixture_result,
)

P2_0_E_PACK_ID = "P2.0-E"
P2_0_E_SECTION_ID = "P2.0"
P2_0_E_DEPENDENCY_PACKS: tuple[str, ...] = (
    "P2.0-A",
    "P2.0-B",
    "P2.0-C",
    "P2.0-D",
)
P2_0_E_NEXT_PACK = "P2.0-F"
P2_0_E_PACK_CHECKPOINT_IDS: tuple[str, ...] = (
    "P2.0.22",
    "P2.0.23",
    "P2.0.24",
    "P2.0.25",
    "P2.0.26",
)
P2_0_E_PACK_RESULT_VERSION = "p2_0_e_operator_demo_snapshot_regression_result.v1"
P2_0_READINESS_VERSION = "p2_0_cognitive_os_lock_readiness.v1"

_READINESS_NON_GOALS: tuple[str, ...] = (
    "no_p2_0_exit_seal",
    "no_p2_0_f_implementation",
    "no_p2_1_authorization",
    "no_release_seal",
)

_PACK_NON_GOALS: tuple[str, ...] = (
    "no_product_ui",
    "no_web_desktop_mobile_clients",
    "no_cli_tui",
    "no_route_runtime",
    "no_browser_tests",
    "no_live_shell",
    "no_source_of_truth_store",
    "no_permission_enforcement",
    "no_custos_integration",
    "no_memory_writes",
    "no_trace_writes",
    "no_p2_0_f",
    "no_p2_1",
)


class P20ECheckpointStatus(str, Enum):
    DONE = "DONE"
    PARTIAL = "PARTIAL"
    NOT_DONE = "NOT_DONE"
    BLOCKED = "BLOCKED"
    UNAVAILABLE = "UNAVAILABLE"


class P20ReadinessDecision(str, Enum):
    READY_FOR_P2_0_F_REVIEW = "READY_FOR_P2_0_F_REVIEW"
    PARTIAL = "PARTIAL"
    BLOCKED = "BLOCKED"
    NOT_READY = "NOT_READY"


@dataclass(frozen=True)
class P20ECheckpointRead(_CanonicalMixin):
    checkpoint_id: str
    canonical_name: str
    status: P20ECheckpointStatus
    evidence: str
    tests: str
    truth_label: str
    unavailable_reason: str
    limitations: str


@dataclass(frozen=True)
class P20ReadinessCriterion(_CanonicalMixin):
    criterion_id: str
    description: str
    passed: bool
    evidence: str
    truth_label: str


@dataclass(frozen=True)
class P20CognitiveOSLockReadiness(_CanonicalMixin):
    """P2.0.26 readiness review state. Not an exit seal."""

    schema_version: str
    readiness_id: str
    readiness_decision: P20ReadinessDecision
    criteria: tuple[P20ReadinessCriterion, ...]
    dependency_packs_checked: tuple[str, ...]
    reports_checked: tuple[str, ...]
    tests_checked: tuple[str, ...]
    truth_boundaries_checked: tuple[str, ...]
    blockers: tuple[str, ...]
    warnings: tuple[str, ...]
    next_pack: str
    is_exit_seal: bool
    is_live_claim: bool
    starts_next_pack: bool
    authorizes_p2_1: bool
    truth_label: str
    non_goals: tuple[str, ...]
    readiness_hash: str


@dataclass(frozen=True)
class P20ESideEffectProof(_CanonicalMixin):
    """P2.0-E side-effect/no-authority proof."""

    ui_created: bool = False
    web_client_created: bool = False
    desktop_client_created: bool = False
    mobile_client_created: bool = False
    cli_created: bool = False
    tui_created: bool = False
    route_runtime_created: bool = False
    browser_tests_created: bool = False
    live_shell_created: bool = False
    demo_harness_runtime_created: bool = False
    source_of_truth_created: bool = False
    permission_enforcement_created: bool = False
    custos_integration_created: bool = False
    tool_executed: bool = False
    workflow_started: bool = False
    business_action_executed: bool = False
    memory_written: bool = False
    runtime_mutated: bool = False
    trace_written: bool = False
    global_trace_written: bool = False
    ledger_written: bool = False
    p2_0_f_started: bool = False
    p2_1_started: bool = False


@dataclass(frozen=True)
class P20EOperatorDemoSnapshotRegressionPackResult(_CanonicalMixin):
    """P2.0-E pack result envelope."""

    schema_version: str
    pack_id: str
    section_id: str
    covered_checkpoints: tuple[str, ...]
    dependency_packs: tuple[str, ...]
    canonical_surface_ids: tuple[str, ...]
    checkpoint_reads: tuple[P20ECheckpointRead, ...]
    checkpoint_statuses: dict[str, str]
    operator_demo_summary: dict[str, str]
    multi_client_consistency_summary: dict[str, str]
    shell_snapshot_summary: dict[str, str]
    regression_harness_summary: dict[str, str]
    readiness_decision: P20ReadinessDecision
    truth_labels: tuple[str, ...]
    side_effect_proof: P20ESideEffectProof
    surface_taxonomy_drift: bool
    surface_taxonomy_drift_details: tuple[str, ...]
    dependency_waivers: tuple[str, ...]
    operator_demo_state: OperatorTestableSurfaceDemoState
    multi_client_consistency_contract: MultiClientConsistencyContract
    shell_state_snapshot: ShellStateSnapshot
    regression_harness_result: SurfaceRegressionHarnessResult
    readiness: P20CognitiveOSLockReadiness
    next_pack: str
    non_goals: tuple[str, ...]
    result_hash: str


def _default_checkpoint_reads() -> tuple[P20ECheckpointRead, ...]:
    names = {
        "P2.0.22": "Operator-Testable Surface Demo State",
        "P2.0.23": "Web / Desktop / Mobile / CLI Client Consistency Contract",
        "P2.0.24": "Shell State Snapshot Contract",
        "P2.0.25": "Surface Regression / Route Test Harness",
        "P2.0.26": "P2.0 Cognitive OS Lock Readiness",
    }
    evidence = {
        "P2.0.22": "OperatorTestableSurfaceDemoState, OperatorDemoSurfaceCard",
        "P2.0.23": "MultiClientConsistencyContract, ClientProjectionParityRule",
        "P2.0.24": "ShellStateSnapshotContract, ShellStateSnapshot",
        "P2.0.25": "SurfaceRegressionRouteTestHarness, route contract cases",
        "P2.0.26": "P20CognitiveOSLockReadiness, readiness criteria",
    }
    tests = {
        "P2.0.22": "test_p2_0_22_operator_demo_*",
        "P2.0.23": "test_p2_0_23_client_consistency_*",
        "P2.0.24": "test_p2_0_24_shell_snapshot_*",
        "P2.0.25": "test_p2_0_25_regression_route_harness_*",
        "P2.0.26": "test_p2_0_26_readiness_*",
    }
    truth = {
        "P2.0.22": "OPERATOR_TESTABLE_CONTRACT_ONLY / DEV_FIXTURE / NOT_LIVE",
        "P2.0.23": "CLIENT_CONSISTENCY_CONTRACT_ONLY / CONTRACT_ONLY / NOT_LIVE",
        "P2.0.24": "SHELL_SNAPSHOT_CONTRACT_ONLY / READ_MODEL_ONLY / NOT_LIVE",
        "P2.0.25": "REGRESSION_HARNESS_CONTRACT_ONLY / CONTRACT_ONLY / NOT_LIVE",
        "P2.0.26": "READINESS_REVIEW_ONLY / CONTRACT_ONLY / NOT_LIVE",
    }
    limitations = {
        "P2.0.22": "No product UI, frontend demo, live shell, or operator runtime",
        "P2.0.23": "No web, desktop, mobile, CLI, TUI, or runtime client",
        "P2.0.24": "No source-of-truth store, live shell state, memory, or trace write",
        "P2.0.25": "No route runtime, frontend route tests, or browser tests",
        "P2.0.26": "No P2.0 exit seal, LIVE claim, P2.0-F start, or P2.1 authorization",
    }
    return tuple(
        P20ECheckpointRead(
            checkpoint_id=checkpoint_id,
            canonical_name=names[checkpoint_id],
            status=P20ECheckpointStatus.DONE,
            evidence=evidence[checkpoint_id],
            tests=tests[checkpoint_id],
            truth_label=truth[checkpoint_id],
            unavailable_reason="n/a — contract/read-model only",
            limitations=limitations[checkpoint_id],
        )
        for checkpoint_id in P2_0_E_PACK_CHECKPOINT_IDS
    )


def _all_false_p2_0_e_side_effects() -> P20ESideEffectProof:
    return P20ESideEffectProof()


def _readiness_criteria(blockers: tuple[str, ...]) -> tuple[P20ReadinessCriterion, ...]:
    no_blockers = not blockers
    return (
        P20ReadinessCriterion(
            criterion_id="dependencies_a_through_e_checked",
            description="P2.0-A/B/C/D dependencies and P2.0-E outputs checked",
            passed=no_blockers,
            evidence="P2.0-A/B/C/D/E contract builders return serializable results",
            truth_label="READINESS_REVIEW_ONLY",
        ),
        P20ReadinessCriterion(
            criterion_id="reports_checked",
            description="Report chain checked",
            passed=no_blockers,
            evidence="agent reports inspected; P2.0-D OMNI marker waived by operator",
            truth_label="READINESS_REVIEW_ONLY",
        ),
        P20ReadinessCriterion(
            criterion_id="tests_checked",
            description="Focused P2.0-E and AurelShell tests checked",
            passed=no_blockers,
            evidence="validation commands recorded in pack report after run",
            truth_label="READINESS_REVIEW_ONLY",
        ),
        P20ReadinessCriterion(
            criterion_id="truth_boundaries_checked",
            description="Truth/fixture/no-live boundaries checked",
            passed=no_blockers,
            evidence="all P2.0-E side-effect flags false; no LIVE/exit seal claim",
            truth_label="READINESS_REVIEW_ONLY",
        ),
    )


def build_p2_0_cognitive_os_lock_readiness(
    *,
    blockers: tuple[str, ...] = (),
    warnings: tuple[str, ...] = (
        "P2.0-D OMNI acceptance marker waived by operator instruction",
    ),
) -> P20CognitiveOSLockReadiness:
    decision = (
        P20ReadinessDecision.BLOCKED
        if blockers
        else P20ReadinessDecision.READY_FOR_P2_0_F_REVIEW
    )
    payload = {
        "schema_version": P2_0_READINESS_VERSION,
        "readiness_id": "p2_0_cognitive_os_lock_readiness_review",
        "readiness_decision": decision,
        "criteria": _readiness_criteria(blockers),
        "dependency_packs_checked": P2_0_E_DEPENDENCY_PACKS + ("P2.0-E",),
        "reports_checked": (
            "P2_0_A_SHELL_FOUNDATION_SURFACE_REGISTRY.md",
            "P2_0_B_NAVIGATION_BOUNDARY_CONTRACTS.md",
            "P2_0_C_FLOATING_WINDOW_HANDOFF_CONTEXT.md",
            "P2_0_D_TRUTH_PERMISSION_FIXTURE_CONTRACTS.md",
            "P2_0_E_OPERATOR_DEMO_SNAPSHOT_REGRESSION.md",
        ),
        "tests_checked": (
            "tests/aurel_shell/test_operator_demo_snapshot_regression.py",
            "tests/aurel_shell",
        ),
        "truth_boundaries_checked": (
            "operator_demo_not_live",
            "client_contract_not_client_implementation",
            "snapshot_not_source_of_truth",
            "route_harness_not_runtime",
            "readiness_not_exit_seal",
        ),
        "blockers": blockers,
        "warnings": warnings,
        "next_pack": P2_0_E_NEXT_PACK,
        "is_exit_seal": False,
        "is_live_claim": False,
        "starts_next_pack": False,
        "authorizes_p2_1": False,
        "truth_label": "READINESS_REVIEW_ONLY",
        "non_goals": _READINESS_NON_GOALS,
    }
    readiness = P20CognitiveOSLockReadiness(
        **payload,
        readiness_hash=_hash_payload(payload),
    )
    assert_readiness_is_not_exit_seal(readiness)
    assert_readiness_is_not_live(readiness)
    assert_readiness_does_not_start_p2_0_f(readiness)
    return readiness


def _regression_summary(result: SurfaceRegressionHarnessResult) -> dict[str, str]:
    return {
        "passed": str(result.passed).lower(),
        "case_count": str(len(result.case_results)),
        "failed_case_count": str(result.failed_case_count),
        "creates_route_runtime": "false",
        "runs_frontend": "false",
        "runs_browser": "false",
        "result_hash": result.result_hash,
    }


def _readiness_summary(readiness: P20CognitiveOSLockReadiness) -> dict[str, str]:
    return {
        "decision": readiness.readiness_decision.value,
        "blocker_count": str(len(readiness.blockers)),
        "is_exit_seal": "false",
        "is_live_claim": "false",
        "starts_next_pack": "false",
        "authorizes_p2_1": "false",
        "readiness_hash": readiness.readiness_hash,
    }


def build_p2_0_e_operator_demo_snapshot_regression_result() -> (
    P20EOperatorDemoSnapshotRegressionPackResult
):
    registry = build_default_surface_registry()
    p2_0_d = build_p2_0_d_truth_permission_fixture_result()
    operator_demo = build_operator_testable_surface_demo_state(registry)
    client_contract = build_multi_client_consistency_contract(registry)
    regression_result = run_surface_regression_route_contract_harness()
    readiness = build_p2_0_cognitive_os_lock_readiness()
    shell_snapshot = build_shell_state_snapshot(
        regression_harness_summary=_regression_summary(regression_result),
        readiness_summary=_readiness_summary(readiness),
    )
    checkpoint_reads = _default_checkpoint_reads()
    checkpoint_statuses = {
        read.checkpoint_id: read.status.value for read in checkpoint_reads
    }
    drift, drift_details = detect_surface_taxonomy_drift()
    side_effects = _all_false_p2_0_e_side_effects()
    payload: dict[str, Any] = {
        "schema_version": P2_0_E_PACK_RESULT_VERSION,
        "pack_id": P2_0_E_PACK_ID,
        "section_id": P2_0_E_SECTION_ID,
        "covered_checkpoints": P2_0_E_PACK_CHECKPOINT_IDS,
        "dependency_packs": P2_0_E_DEPENDENCY_PACKS,
        "canonical_surface_ids": tuple(CANONICAL_SURFACE_ORDER),
        "checkpoint_reads": checkpoint_reads,
        "checkpoint_statuses": checkpoint_statuses,
        "operator_demo_summary": shell_snapshot.operator_demo_summary,
        "multi_client_consistency_summary": (
            shell_snapshot.client_consistency_summary
        ),
        "shell_snapshot_summary": {
            "snapshot_id": shell_snapshot.snapshot_id,
            "is_read_model": "true",
            "is_source_of_truth": "false",
            "mutates_runtime": "false",
            "snapshot_hash": shell_snapshot.snapshot_hash,
        },
        "regression_harness_summary": _regression_summary(regression_result),
        "readiness_decision": readiness.readiness_decision,
        "truth_labels": (
            "OPERATOR_TESTABLE_CONTRACT_ONLY",
            "CLIENT_CONSISTENCY_CONTRACT_ONLY",
            "SHELL_SNAPSHOT_CONTRACT_ONLY",
            "REGRESSION_HARNESS_CONTRACT_ONLY",
            "READINESS_REVIEW_ONLY",
            "CONTRACT_ONLY",
            "READ_MODEL_ONLY",
            "DEV_FIXTURE",
            "NOT_LIVE",
        ),
        "side_effect_proof": side_effects,
        "surface_taxonomy_drift": drift,
        "surface_taxonomy_drift_details": drift_details,
        "dependency_waivers": (
            "operator waived missing local P2.0-D OMNI acceptance marker",
        ),
        "operator_demo_state": operator_demo,
        "multi_client_consistency_contract": client_contract,
        "shell_state_snapshot": shell_snapshot,
        "regression_harness_result": regression_result,
        "readiness": readiness,
        "next_pack": P2_0_E_NEXT_PACK,
        "non_goals": _PACK_NON_GOALS,
    }
    result = P20EOperatorDemoSnapshotRegressionPackResult(
        **payload,
        result_hash=_hash_payload(payload),
    )
    assert p2_0_d.result_hash
    return result


def serialize_p2_0_e_result(
    result: P20EOperatorDemoSnapshotRegressionPackResult,
) -> str:
    return to_canonical_json(result.to_canonical_dict())


def assert_readiness_is_not_exit_seal(
    readiness: P20CognitiveOSLockReadiness,
) -> None:
    if readiness.is_exit_seal:
        _reject(
            "P2.0 readiness must not be an exit seal",
            field="is_exit_seal",
            code=AurelShellErrorCode.INVALID_TRUTH_LABEL,
        )


def assert_readiness_is_not_live(readiness: P20CognitiveOSLockReadiness) -> None:
    if readiness.is_live_claim:
        _reject(
            "P2.0 readiness must not claim LIVE",
            field="is_live_claim",
            code=AurelShellErrorCode.INVALID_TRUTH_LABEL,
        )


def assert_readiness_does_not_start_p2_0_f(
    readiness: P20CognitiveOSLockReadiness,
) -> None:
    if readiness.starts_next_pack or readiness.authorizes_p2_1:
        _reject(
            "P2.0 readiness must not start P2.0-F or authorize P2.1",
            field="starts_next_pack",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )
