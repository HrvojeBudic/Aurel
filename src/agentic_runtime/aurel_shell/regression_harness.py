"""P2.0-E surface regression / route contract harness.

The harness checks contract invariants only. It does not create route runtime,
does not boot clients, and does not run frontend or browser tests.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from .boundaries import (
    build_hub_internal_tool_entry_boundary,
    build_settings_system_config_boundary,
    build_system_no_agent_access_boundary,
)
from .contracts import AurelShellErrorCode, _CanonicalMixin, _hash_payload, _reject
from .fixture_discipline import (
    build_surface_dev_fixture_disclosure,
    build_surface_mock_disclosure,
    build_surface_simulated_disclosure,
)
from .navigation_boundary import (
    build_aurel_logo_route_binding,
    build_no_universal_left_nav_contract,
)
from .operator_demo import build_operator_testable_surface_demo_state
from .shell_snapshot import build_shell_state_snapshot
from .surface_registry import AurelSurfaceKind, build_default_surface_registry
from .truth_labels import SurfaceTruthLabel
from .truth_permission_fixture_read_model import (
    build_p2_0_d_truth_permission_fixture_result,
)

SURFACE_REGRESSION_HARNESS_VERSION = "surface_regression_route_harness.v1"
SURFACE_ROUTE_CONTRACT_CASE_VERSION = "surface_route_contract_case.v1"
SURFACE_REGRESSION_RESULT_VERSION = "surface_regression_harness_result.v1"

_HARNESS_NON_GOALS: tuple[str, ...] = (
    "no_actual_route_runtime",
    "no_frontend_route_tests",
    "no_browser_tests",
    "no_client_app_boot",
)


@dataclass(frozen=True)
class SurfaceRouteContractCase(_CanonicalMixin):
    """Single route/surface invariant case."""

    schema_version: str
    case_id: str
    case_name: str
    checkpoint_ids: tuple[str, ...]
    input_contract_refs: tuple[str, ...]
    expected_result: str
    actual_result: str
    passed: bool
    truth_label: str
    creates_route_runtime: bool
    runs_frontend: bool
    runs_browser: bool
    mutates_runtime: bool
    non_goals: tuple[str, ...]
    case_hash: str


@dataclass(frozen=True)
class SurfaceRegressionRouteTestHarness(_CanonicalMixin):
    """P2.0.25 harness definition."""

    schema_version: str
    harness_id: str
    cases: tuple[SurfaceRouteContractCase, ...]
    case_count: int
    validates_contract_cases_only: bool
    creates_route_runtime: bool
    runs_frontend: bool
    runs_browser: bool
    mutates_runtime: bool
    truth_label: str
    non_goals: tuple[str, ...]
    harness_hash: str


@dataclass(frozen=True)
class SurfaceRegressionHarnessResult(_CanonicalMixin):
    """P2.0.25 harness result envelope."""

    schema_version: str
    harness: SurfaceRegressionRouteTestHarness
    passed: bool
    passed_case_count: int
    failed_case_count: int
    case_results: tuple[SurfaceRouteContractCase, ...]
    creates_route_runtime: bool
    runs_frontend: bool
    runs_browser: bool
    mutates_runtime: bool
    truth_label: str
    result_hash: str


def build_surface_route_contract_case(
    *,
    case_id: str,
    case_name: str,
    checkpoint_ids: tuple[str, ...],
    input_contract_refs: tuple[str, ...],
    passed: bool,
    expected_result: str = "PASS",
    actual_result: str | None = None,
) -> SurfaceRouteContractCase:
    if actual_result is None:
        actual_result = "PASS" if passed else "FAIL"
    payload = {
        "schema_version": SURFACE_ROUTE_CONTRACT_CASE_VERSION,
        "case_id": case_id,
        "case_name": case_name,
        "checkpoint_ids": checkpoint_ids,
        "input_contract_refs": input_contract_refs,
        "expected_result": expected_result,
        "actual_result": actual_result,
        "passed": passed,
        "truth_label": "REGRESSION_HARNESS_CONTRACT_ONLY",
        "creates_route_runtime": False,
        "runs_frontend": False,
        "runs_browser": False,
        "mutates_runtime": False,
        "non_goals": _HARNESS_NON_GOALS,
    }
    return SurfaceRouteContractCase(**payload, case_hash=_hash_payload(payload))


def _case_specs() -> tuple[
    tuple[str, str, tuple[str, ...], tuple[str, ...], Callable[[], bool]],
    ...,
]:
    return (
        (
            "exactly_seven_surfaces",
            "Exactly seven canonical surfaces",
            ("P2.0.22", "P2.0.25"),
            ("AurelSurfaceRegistry",),
            lambda: build_default_surface_registry().surface_count == 7,
        ),
        (
            "logo_routes_to_cro",
            "Aurel Logo routes to CRO contract",
            ("P2.0.25",),
            ("AurelLogoRouteBinding",),
            lambda: (
                build_aurel_logo_route_binding().target.surface_kind
                is AurelSurfaceKind.AUREL_CRO
            ),
        ),
        (
            "system_not_logo_default_route",
            "SYSTEM is not logo/default route",
            ("P2.0.25",),
            ("AurelLogoRouteBinding", "SystemNoAgentAccessBoundary"),
            lambda: (
                not build_aurel_logo_route_binding().target_is_system
                and not build_system_no_agent_access_boundary()
                .access_rule
                .default_route_target_allowed
            ),
        ),
        (
            "settings_not_system",
            "Settings is not SYSTEM",
            ("P2.0.25",),
            ("SettingsSystemConfigBoundary",),
            lambda: not build_settings_system_config_boundary().settings_is_system,
        ),
        (
            "hub_entry_not_tool_execution",
            "HUB entry is not tool execution",
            ("P2.0.25",),
            ("HubInternalToolEntryBoundary",),
            lambda: (
                not build_hub_internal_tool_entry_boundary()
                .tool_entry
                .hub_can_execute_tools
                and not build_hub_internal_tool_entry_boundary()
                .tool_entry
                .hub_entry_is_tool_call
            ),
        ),
        (
            "no_universal_left_nav",
            "No universal left nav contract",
            ("P2.0.25",),
            ("NoUniversalLeftNavContract",),
            lambda: not build_no_universal_left_nav_contract().global_left_nav_allowed,
        ),
        (
            "demo_states_truth_labeled",
            "All demo states truth-labeled",
            ("P2.0.22", "P2.0.25"),
            ("OperatorTestableSurfaceDemoState",),
            lambda: all(
                card.truth_label is SurfaceTruthLabel.DEV_FIXTURE
                for card in build_operator_testable_surface_demo_state().cards
            ),
        ),
        (
            "unavailable_states_reasoned",
            "All unavailable states reasoned",
            ("P2.0.20", "P2.0.25"),
            ("SurfaceUnavailableState",),
            lambda: all(
                state.unavailable_reason and state.next_action
                for state in build_p2_0_d_truth_permission_fixture_result()
                .unavailable_states
            ),
        ),
        (
            "fixtures_not_live",
            "Fixtures are not live",
            ("P2.0.21", "P2.0.25"),
            ("SurfaceFixtureDisclosure",),
            lambda: not any(
                disclosure.is_live
                for disclosure in (
                    build_surface_dev_fixture_disclosure(),
                    build_surface_mock_disclosure(),
                    build_surface_simulated_disclosure(),
                )
            ),
        ),
        (
            "snapshot_not_source_of_truth",
            "Snapshot is not source of truth",
            ("P2.0.24", "P2.0.25"),
            ("ShellStateSnapshot",),
            lambda: not build_shell_state_snapshot().is_source_of_truth,
        ),
    )


def build_surface_regression_route_test_harness() -> SurfaceRegressionRouteTestHarness:
    cases = tuple(
        build_surface_route_contract_case(
            case_id=case_id,
            case_name=case_name,
            checkpoint_ids=checkpoint_ids,
            input_contract_refs=input_contract_refs,
            passed=check(),
        )
        for case_id, case_name, checkpoint_ids, input_contract_refs, check in _case_specs()
    )
    payload = {
        "schema_version": SURFACE_REGRESSION_HARNESS_VERSION,
        "harness_id": "p2_0_e_surface_regression_route_contract_harness",
        "cases": cases,
        "case_count": len(cases),
        "validates_contract_cases_only": True,
        "creates_route_runtime": False,
        "runs_frontend": False,
        "runs_browser": False,
        "mutates_runtime": False,
        "truth_label": "REGRESSION_HARNESS_CONTRACT_ONLY",
        "non_goals": _HARNESS_NON_GOALS,
    }
    harness = SurfaceRegressionRouteTestHarness(
        **payload,
        harness_hash=_hash_payload(payload),
    )
    assert_route_harness_validates_contracts_only(harness)
    assert_route_harness_does_not_create_runtime_routes(harness)
    return harness


def run_surface_regression_route_contract_harness() -> SurfaceRegressionHarnessResult:
    harness = build_surface_regression_route_test_harness()
    passed_count = sum(1 for case in harness.cases if case.passed)
    failed_count = harness.case_count - passed_count
    payload = {
        "schema_version": SURFACE_REGRESSION_RESULT_VERSION,
        "harness": harness,
        "passed": failed_count == 0,
        "passed_case_count": passed_count,
        "failed_case_count": failed_count,
        "case_results": harness.cases,
        "creates_route_runtime": False,
        "runs_frontend": False,
        "runs_browser": False,
        "mutates_runtime": False,
        "truth_label": "REGRESSION_HARNESS_CONTRACT_ONLY",
    }
    result = SurfaceRegressionHarnessResult(
        **payload,
        result_hash=_hash_payload(payload),
    )
    assert_route_harness_does_not_create_runtime_routes(harness)
    return result


def assert_route_harness_validates_contracts_only(
    harness: SurfaceRegressionRouteTestHarness,
) -> None:
    if not harness.validates_contract_cases_only:
        _reject(
            "route harness must validate contract cases only",
            field="validates_contract_cases_only",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_route_harness_does_not_create_runtime_routes(
    harness: SurfaceRegressionRouteTestHarness | SurfaceRegressionHarnessResult,
) -> None:
    if (
        harness.creates_route_runtime
        or harness.runs_frontend
        or harness.runs_browser
        or harness.mutates_runtime
    ):
        _reject(
            "route harness must not create runtime routes or run frontend/browser",
            field="creates_route_runtime",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_logo_routes_to_cro_contract(
    result: SurfaceRegressionHarnessResult,
) -> None:
    _assert_case_passed(result, "logo_routes_to_cro")


def assert_system_is_not_logo_default_route(
    result: SurfaceRegressionHarnessResult,
) -> None:
    _assert_case_passed(result, "system_not_logo_default_route")


def assert_settings_is_not_system(result: SurfaceRegressionHarnessResult) -> None:
    _assert_case_passed(result, "settings_not_system")


def assert_hub_entry_is_not_tool_execution(
    result: SurfaceRegressionHarnessResult,
) -> None:
    _assert_case_passed(result, "hub_entry_not_tool_execution")


def assert_no_universal_left_nav_contract_holds(
    result: SurfaceRegressionHarnessResult,
) -> None:
    _assert_case_passed(result, "no_universal_left_nav")


def _assert_case_passed(result: SurfaceRegressionHarnessResult, case_id: str) -> None:
    for case in result.case_results:
        if case.case_id == case_id:
            if not case.passed:
                _reject(
                    f"route contract case failed: {case_id}",
                    field="case_results",
                    code=AurelShellErrorCode.VALIDATION_ERROR,
                )
            return
    _reject(
        f"route contract case missing: {case_id}",
        field="case_results",
        code=AurelShellErrorCode.VALIDATION_ERROR,
    )
