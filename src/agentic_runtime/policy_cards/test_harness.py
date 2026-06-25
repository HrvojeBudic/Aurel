"""Policy Test Harness (P1.6.16).

Deterministic, JSON-safe, hash-ready policy harness for shadow governance
scenario definition, execution, comparison, and reporting.

P1.6.16 introduces a deterministic policy test harness for shadow governance
validation; it does NOT enforce policy decisions, write to the Ledger, activate
approvals, block commands, or change runtime sandbox behavior.

The harness validates shadow governance — it does not enforce policy.

Family-decision scenarios reuse resolver-internal ``_attach_*_metadata`` hooks
after ``aggregate_family_decisions``; there is no parallel resolver.
"""
from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping as MappingABC
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Mapping, Sequence

from .conflict_algebra import PolicyConflictType, PolicyDecisionRank
from .errors import PolicyResolutionValidationError
from .resolution_context import EnforcementMode, PolicyResolutionContext
from .resolution_result import (
    FamilyDecision,
    PolicyFamily,
    PolicyFamilyDecision,
    ResolvedPolicySet,
    ShadowAction,
    decision_to_shadow_action,
)
from .resolver import aggregate_family_decisions, resolve_policy_cards
from .runtime_projection import (
    RuntimeEffectiveAction,
    RuntimePolicySnapshot,
    project_policy_resolution_against_runtime,
)
from .violation_trace import (
    PolicyViolationType,
    bind_policy_violation_from_resolution,
)


HARNESS_VERSION: str = "custos-v0-p1616"

_SENSITIVE_METADATA_KEYS = frozenset({
    "password", "passwd", "secret", "token", "api_key", "apikey",
    "authorization", "credential", "private_key", "access_key",
})
_SENSITIVE_PATTERN = re.compile(
    r"(password|secret|token|api[_-]?key|credential|private[_-]?key|authorization)",
    re.IGNORECASE,
)
_COMMAND_BODY_KEYS = frozenset({
    "command", "command_body", "argv", "shell_command", "raw_command", "payload",
})


class PolicyHarnessVerdict(str, Enum):
    PASS = "PASS"  # nosec B105 - enum verdict label, not a credential
    FAIL = "FAIL"
    WARN = "WARN"
    ERROR = "ERROR"
    SKIPPED = "SKIPPED"


class PolicyHarnessFailureType(str, Enum):
    EXPECTED_RANK_MISMATCH = "EXPECTED_RANK_MISMATCH"
    EXPECTED_ACTION_MISMATCH = "EXPECTED_ACTION_MISMATCH"
    EXPECTED_CONFLICT_MISSING = "EXPECTED_CONFLICT_MISSING"
    UNEXPECTED_CONFLICT = "UNEXPECTED_CONFLICT"
    EXPECTED_TRACE_MISSING = "EXPECTED_TRACE_MISSING"
    EXPECTED_VIOLATION_MISSING = "EXPECTED_VIOLATION_MISSING"
    UNEXPECTED_ENFORCEMENT = "UNEXPECTED_ENFORCEMENT"
    NON_DETERMINISTIC_HASH = "NON_DETERMINISTIC_HASH"
    ADAPTER_ERROR = "ADAPTER_ERROR"
    CONTEXT_BINDING_ERROR = "CONTEXT_BINDING_ERROR"
    REGISTRY_ERROR = "REGISTRY_ERROR"
    POLICY_DESIGN_ERROR = "POLICY_DESIGN_ERROR"
    UNKNOWN_ACTUAL_VALUE = "UNKNOWN_ACTUAL_VALUE"
    UNSUPPORTED_SCENARIO = "UNSUPPORTED_SCENARIO"


@dataclass(frozen=True)
class PolicyHarnessInput:
    risk_tier: str = "R2"
    operation_type: str = ""
    action_type: str = ""
    tool_name: str = ""
    data_scope: str = ""
    sandbox_profile: str = ""
    memory_write_intent: bool = False
    prompt_authority_context: str = ""
    cards: tuple[Any, ...] = ()
    p0_verdict: str = ""
    context_id: str = "harness-case"
    metadata: Mapping[str, Any] = field(default_factory=dict)
    family_decisions: tuple[PolicyFamilyDecision, ...] = ()
    resolved_policy: ResolvedPolicySet | None = None
    skip_resolver: bool = False


@dataclass(frozen=True)
class PolicyHarnessExpected:
    expected_shadow_action: str = ""
    expected_strictest_rank: str = ""
    expected_conflict_types: tuple[str, ...] = ()
    expected_violation_types: tuple[str, ...] = ()
    expected_resolution_trace: bool = False
    expected_violation_trace: bool = False
    expected_enforced: bool = False
    expected_shadow_only: bool = True
    expected_reason_codes: tuple[str, ...] = ()
    expected_hash_stability: bool = True
    expected_verdict: PolicyHarnessVerdict = PolicyHarnessVerdict.PASS
    allow_unexpected_conflicts: bool = False


@dataclass(frozen=True)
class PolicyHarnessActual:
    actual_shadow_action: str = ""
    actual_strictest_rank: str = ""
    actual_conflict_types: tuple[str, ...] = ()
    actual_violation_types: tuple[str, ...] = ()
    resolution_trace_hash: str = ""
    violation_hash: str = ""
    projection_hash: str = ""
    runtime_snapshot_hash: str = ""
    shadow_only: bool = True
    enforced: bool = False
    reason_codes: tuple[str, ...] = ()
    conflict_codes: tuple[str, ...] = ()
    raw_safe_metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PolicyHarnessFailure:
    failure_type: PolicyHarnessFailureType
    message: str = ""
    field_name: str = ""
    expected_value: str = ""
    actual_value: str = ""

    def to_canonical_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "failure_type": self.failure_type.value,
            "message": self.message,
        }
        if self.field_name:
            result["field_name"] = self.field_name
        if self.expected_value:
            result["expected_value"] = self.expected_value
        if self.actual_value:
            result["actual_value"] = self.actual_value
        return dict(sorted(result.items(), key=lambda i: i[0]))


@dataclass(frozen=True)
class PolicyHarnessCase:
    case_id: str
    title: str = ""
    description: str = ""
    input: PolicyHarnessInput = field(default_factory=PolicyHarnessInput)
    expected: PolicyHarnessExpected = field(default_factory=PolicyHarnessExpected)
    tags: tuple[str, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def to_canonical_dict(self) -> dict[str, Any]:
        return policy_harness_case_to_canonical_dict(self)


@dataclass(frozen=True)
class PolicyHarnessResult:
    case_id: str
    verdict: PolicyHarnessVerdict
    actual: PolicyHarnessActual
    expected_vs_actual: Mapping[str, Any] = field(default_factory=dict)
    failures: tuple[PolicyHarnessFailure, ...] = ()
    warnings: tuple[str, ...] = ()
    canonical_hash: str | None = None

    def to_canonical_dict(self, *, include_hash: bool = False) -> dict[str, Any]:
        return policy_harness_result_to_canonical_dict(self, include_hash=include_hash)

    def with_canonical_hash(self) -> PolicyHarnessResult:
        h = policy_harness_result_hash(self)
        return replace(self, canonical_hash=h)


@dataclass(frozen=True)
class PolicyHarnessSuite:
    suite_id: str
    title: str = ""
    cases: tuple[PolicyHarnessCase, ...] = ()
    tags: tuple[str, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PolicyHarnessRun:
    suite_id: str
    results: tuple[PolicyHarnessResult, ...] = ()
    started_at: str = ""
    harness_version: str = HARNESS_VERSION

    def __post_init__(self) -> None:
        if not self.started_at:
            object.__setattr__(
                self,
                "started_at",
                datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            )


@dataclass(frozen=True)
class PolicyHarnessMatrix:
    """Named scenario registry for documentation and optional suite building."""

    scenarios: Mapping[str, PolicyHarnessCase] = field(default_factory=dict)


@dataclass(frozen=True)
class PolicyHarnessReport:
    suite_id: str
    case_count: int = 0
    passed: int = 0
    failed: int = 0
    warned: int = 0
    errored: int = 0
    skipped: int = 0
    coverage_by_conflict_type: Mapping[str, int] = field(default_factory=dict)
    coverage_by_policy_family: Mapping[str, int] = field(default_factory=dict)
    coverage_by_violation_type: Mapping[str, int] = field(default_factory=dict)
    determinism_status: str = "UNKNOWN"
    shadow_only_status: str = "UNKNOWN"
    results: tuple[PolicyHarnessResult, ...] = ()
    report_hash: str | None = None
    harness_version: str = HARNESS_VERSION

    def to_canonical_dict(self, *, include_hash: bool = False) -> dict[str, Any]:
        return policy_harness_report_to_canonical_dict(self, include_hash=include_hash)

    def with_report_hash(self) -> PolicyHarnessReport:
        h = policy_harness_report_hash(self)
        return replace(self, report_hash=h)


# ---------------------------------------------------------------------------
# Metadata safety
# ---------------------------------------------------------------------------


def _assert_json_safe(value: object, path: str) -> None:
    if value is None or isinstance(value, str | int | float | bool):
        return
    if isinstance(value, list | tuple):
        for idx, item in enumerate(value):
            _assert_json_safe(item, f"{path}[{idx}]")
        return
    if isinstance(value, MappingABC):
        for key, item in value.items():
            if not isinstance(key, str):
                raise ValueError(f"metadata key at {path} must be a string")
            _assert_json_safe(item, f"{path}.{key}")
        return
    raise ValueError(f"value at {path} is not JSON-safe")


def _sanitize_metadata(metadata: Mapping[str, Any] | None) -> dict[str, Any]:
    if not metadata:
        return {}
    sanitized: dict[str, Any] = {}
    for key, value in metadata.items():
        if not isinstance(key, str):
            continue
        key_lower = key.lower()
        if key_lower in _COMMAND_BODY_KEYS:
            continue
        if key_lower in _SENSITIVE_METADATA_KEYS or _SENSITIVE_PATTERN.search(key):
            continue
        try:
            _assert_json_safe(value, f"metadata.{key}")
        except ValueError:
            continue
        sanitized[key] = value
    return dict(sorted(sanitized.items(), key=lambda i: i[0]))


# ---------------------------------------------------------------------------
# Canonicalization & hashing
# ---------------------------------------------------------------------------


def canonical_policy_harness_dict(payload: Mapping[str, Any]) -> dict[str, Any]:
    return dict(sorted(dict(payload).items(), key=lambda i: i[0]))


def policy_harness_case_to_canonical_dict(case: PolicyHarnessCase) -> dict[str, Any]:
    result: dict[str, Any] = {
        "case_id": case.case_id,
        "description": case.description,
        "expected": {
            "expected_conflict_types": sorted(case.expected.expected_conflict_types),
            "expected_enforced": case.expected.expected_enforced,
            "expected_hash_stability": case.expected.expected_hash_stability,
            "expected_resolution_trace": case.expected.expected_resolution_trace,
            "expected_shadow_action": case.expected.expected_shadow_action,
            "expected_shadow_only": case.expected.expected_shadow_only,
            "expected_strictest_rank": case.expected.expected_strictest_rank,
            "expected_verdict": case.expected.expected_verdict.value,
            "expected_violation_trace": case.expected.expected_violation_trace,
            "expected_violation_types": sorted(case.expected.expected_violation_types),
            "expected_reason_codes": sorted(case.expected.expected_reason_codes),
        },
        "input": {
            "context_id": case.input.context_id,
            "memory_write_intent": case.input.memory_write_intent,
            "p0_verdict": case.input.p0_verdict,
            "risk_tier": case.input.risk_tier,
            "skip_resolver": case.input.skip_resolver,
            "tool_name": case.input.tool_name,
        },
        "tags": sorted(case.tags),
        "title": case.title,
    }
    if case.metadata:
        result["metadata"] = _sanitize_metadata(case.metadata)
    return dict(sorted(result.items(), key=lambda i: i[0]))


def policy_harness_case_hash(case: PolicyHarnessCase) -> str:
    canonical = json.dumps(
        policy_harness_case_to_canonical_dict(case),
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def policy_harness_actual_to_canonical_dict(actual: PolicyHarnessActual) -> dict[str, Any]:
    return {
        "actual_conflict_types": sorted(actual.actual_conflict_types),
        "actual_shadow_action": actual.actual_shadow_action,
        "actual_strictest_rank": actual.actual_strictest_rank,
        "actual_violation_types": sorted(actual.actual_violation_types),
        "conflict_codes": sorted(actual.conflict_codes),
        "enforced": actual.enforced,
        "projection_hash": actual.projection_hash,
        "reason_codes": sorted(actual.reason_codes),
        "resolution_trace_hash": actual.resolution_trace_hash,
        "runtime_snapshot_hash": actual.runtime_snapshot_hash,
        "shadow_only": actual.shadow_only,
        "violation_hash": actual.violation_hash,
        "raw_safe_metadata": dict(sorted(dict(actual.raw_safe_metadata).items())),
    }


def policy_harness_result_to_canonical_dict(
    result: PolicyHarnessResult,
    *,
    include_hash: bool = False,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "actual": policy_harness_actual_to_canonical_dict(result.actual),
        "case_id": result.case_id,
        "expected_vs_actual": dict(sorted(dict(result.expected_vs_actual).items())),
        "failures": [f.to_canonical_dict() for f in result.failures],
        "verdict": result.verdict.value,
        "warnings": sorted(result.warnings),
    }
    if include_hash and result.canonical_hash is not None:
        payload["canonical_hash"] = result.canonical_hash
    return dict(sorted(payload.items(), key=lambda i: i[0]))


def policy_harness_result_hash(result: PolicyHarnessResult) -> str:
    canonical = json.dumps(
        policy_harness_result_to_canonical_dict(result, include_hash=False),
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def policy_harness_report_to_canonical_dict(
    report: PolicyHarnessReport,
    *,
    include_hash: bool = False,
) -> dict[str, Any]:
    sorted_results = sorted(report.results, key=lambda r: r.case_id)
    payload: dict[str, Any] = {
        "case_count": report.case_count,
        "coverage_by_conflict_type": dict(
            sorted(dict(report.coverage_by_conflict_type).items()),
        ),
        "coverage_by_policy_family": dict(
            sorted(dict(report.coverage_by_policy_family).items()),
        ),
        "coverage_by_violation_type": dict(
            sorted(dict(report.coverage_by_violation_type).items()),
        ),
        "determinism_status": report.determinism_status,
        "errored": report.errored,
        "failed": report.failed,
        "harness_version": report.harness_version,
        "passed": report.passed,
        "results": [
            r.to_canonical_dict(include_hash=True) for r in sorted_results
        ],
        "shadow_only_status": report.shadow_only_status,
        "skipped": report.skipped,
        "suite_id": report.suite_id,
        "warned": report.warned,
    }
    if include_hash and report.report_hash is not None:
        payload["report_hash"] = report.report_hash
    return dict(sorted(payload.items(), key=lambda i: i[0]))


def policy_harness_report_hash(report: PolicyHarnessReport) -> str:
    canonical = json.dumps(
        policy_harness_report_to_canonical_dict(report, include_hash=False),
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Actual extraction
# ---------------------------------------------------------------------------


def _normalize_action(value: str) -> str:
    return value.strip().lower().replace("-", "_")


def _actual_from_resolved_policy_set(
    resolution: ResolvedPolicySet,
    *,
    p0_verdict: str = "",
) -> PolicyHarnessActual:
    strictest_rank = ""
    conflict_types: list[str] = []
    conflict_codes: list[str] = []
    if resolution.conflict_resolution is not None:
        strictest_rank = str(resolution.conflict_resolution.get("winning_rank", ""))
        raw_codes = resolution.conflict_resolution.get("conflict_codes", ()) or ()
        conflict_codes = [str(c) for c in raw_codes]
        conflict_types = list(conflict_codes)

    violation_types: list[str] = []
    violation_hash = resolution.violation_trace_hash or ""
    if resolution.violation_trace is not None:
        violation_types.append(
            str(resolution.violation_trace.get("violation_type", "")),
        )
    elif not p0_verdict:
        violation_env = bind_policy_violation_from_resolution(resolution)
        violation_event = violation_env.trace_event
        violation_hash = violation_event.violation_hash or violation_hash
        if violation_event.violation_type:
            violation_types = [violation_event.violation_type]

    projection_hash = ""
    runtime_snapshot_hash = ""
    if p0_verdict:
        snapshot = RuntimePolicySnapshot(
            runtime_effective_action=_runtime_action_from_verdict(p0_verdict),
            policy_verdict=p0_verdict,
        ).with_runtime_snapshot_hash()
        projection = project_policy_resolution_against_runtime(snapshot, resolution)
        violation_env = bind_policy_violation_from_resolution(
            resolution,
            projection=projection,
            runtime_snapshot=snapshot,
        )
        violation_event = violation_env.trace_event
        violation_hash = violation_event.violation_hash or violation_hash
        if violation_event.violation_type:
            violation_types = [violation_event.violation_type]
        projection_hash = projection.projection_hash or ""
        runtime_snapshot_hash = snapshot.runtime_snapshot_hash or ""

    return PolicyHarnessActual(
        actual_shadow_action=resolution.effective_shadow_action.value,
        actual_strictest_rank=strictest_rank,
        actual_conflict_types=tuple(sorted(set(conflict_types))),
        actual_violation_types=tuple(sorted(set(vt for vt in violation_types if vt))),
        resolution_trace_hash=resolution.resolution_trace_hash or "",
        violation_hash=violation_hash,
        projection_hash=projection_hash,
        runtime_snapshot_hash=runtime_snapshot_hash,
        shadow_only=True,
        enforced=False,
        reason_codes=resolution.reason_codes,
        conflict_codes=tuple(sorted(conflict_codes)),
        raw_safe_metadata={
            "resolution_id": resolution.resolution_id,
            "context_hash": resolution.context_hash,
        },
    )


def _runtime_action_from_verdict(p0_verdict: str) -> RuntimeEffectiveAction:
    key = _normalize_action(p0_verdict)
    mapping = {
        "allow": RuntimeEffectiveAction.RUNTIME_ALLOW,
        "deny": RuntimeEffectiveAction.RUNTIME_DENY,
        "require_approval": RuntimeEffectiveAction.RUNTIME_REQUIRE_APPROVAL,
        "warn": RuntimeEffectiveAction.RUNTIME_WARN,
    }
    return mapping.get(key, RuntimeEffectiveAction.RUNTIME_UNKNOWN)


def _build_context_from_input(inp: PolicyHarnessInput) -> PolicyResolutionContext:
    return PolicyResolutionContext(
        context_id=inp.context_id,
        risk_tier=inp.risk_tier,
        tool_name=inp.tool_name,
        memory_write_intent=inp.memory_write_intent,
        metadata=dict(inp.metadata),
    )


def _execute_case_input(inp: PolicyHarnessInput) -> PolicyHarnessActual:
    if inp.resolved_policy is not None:
        return _actual_from_resolved_policy_set(inp.resolved_policy, p0_verdict=inp.p0_verdict)

    if inp.family_decisions:
        overall, shadow, reasons, warnings, violations, approvals = (
            aggregate_family_decisions(inp.family_decisions)
        )
        resolution = ResolvedPolicySet(
            resolution_id=f"harness-{inp.context_id}",
            context_hash=_build_context_from_input(inp).context_hash,
            enforcement_mode=EnforcementMode.SHADOW,
            overall_decision=overall,
            effective_shadow_action=shadow,
            family_decisions=inp.family_decisions,
            reason_codes=reasons,
            warnings=warnings,
            violations=violations,
            approval_requirements=approvals,
        )
        from .resolver import _attach_conflict_metadata, _attach_trace_metadata, _attach_violation_metadata

        resolution = _attach_conflict_metadata(
            resolution, list(inp.family_decisions), _build_context_from_input(inp),
        )
        resolution = _attach_trace_metadata(resolution)
        resolution = _attach_violation_metadata(resolution)
        resolution = resolution.with_canonical_hash()
        return _actual_from_resolved_policy_set(resolution, p0_verdict=inp.p0_verdict)

    if inp.skip_resolver and not inp.cards:
        raise PolicyResolutionValidationError("no cards or family decisions provided")

    context = _build_context_from_input(inp)
    resolution = resolve_policy_cards(context, list(inp.cards))
    return _actual_from_resolved_policy_set(resolution, p0_verdict=inp.p0_verdict)


# ---------------------------------------------------------------------------
# Comparator
# ---------------------------------------------------------------------------


def compare_policy_harness_expected_actual(
    expected: PolicyHarnessExpected,
    actual: PolicyHarnessActual,
) -> tuple[PolicyHarnessVerdict, tuple[PolicyHarnessFailure, ...], tuple[str, ...], dict[str, Any]]:
    failures: list[PolicyHarnessFailure] = []
    warnings: list[str] = []
    comparisons: dict[str, Any] = {}

    if expected.expected_enforced is False and actual.enforced is not False:
        failures.append(
            PolicyHarnessFailure(
                failure_type=PolicyHarnessFailureType.UNEXPECTED_ENFORCEMENT,
                message="enforced must be false",
                field_name="enforced",
                expected_value="false",
                actual_value=str(actual.enforced),
            )
        )

    if expected.expected_shadow_only and not actual.shadow_only:
        failures.append(
            PolicyHarnessFailure(
                failure_type=PolicyHarnessFailureType.UNEXPECTED_ENFORCEMENT,
                message="shadow_only must be true",
                field_name="shadow_only",
                expected_value="true",
                actual_value=str(actual.shadow_only),
            )
        )

    if expected.expected_shadow_action:
        exp_action = _normalize_action(expected.expected_shadow_action)
        act_action = _normalize_action(actual.actual_shadow_action)
        comparisons["shadow_action"] = {"expected": exp_action, "actual": act_action}
        if exp_action != act_action:
            failures.append(
                PolicyHarnessFailure(
                    failure_type=PolicyHarnessFailureType.EXPECTED_ACTION_MISMATCH,
                    message="shadow action mismatch",
                    field_name="actual_shadow_action",
                    expected_value=exp_action,
                    actual_value=act_action,
                )
            )

    if expected.expected_strictest_rank:
        exp_rank = expected.expected_strictest_rank.upper()
        act_rank = actual.actual_strictest_rank.upper()
        comparisons["strictest_rank"] = {"expected": exp_rank, "actual": act_rank}
        if exp_rank != act_rank:
            failures.append(
                PolicyHarnessFailure(
                    failure_type=PolicyHarnessFailureType.EXPECTED_RANK_MISMATCH,
                    message="strictest rank mismatch",
                    field_name="actual_strictest_rank",
                    expected_value=exp_rank,
                    actual_value=act_rank,
                )
            )

    if expected.expected_conflict_types:
        expected_set = {c.lower() for c in expected.expected_conflict_types}
        actual_set = {c.lower() for c in actual.actual_conflict_types}
        comparisons["conflict_types"] = {
            "expected": sorted(expected_set),
            "actual": sorted(actual_set),
        }
        missing = expected_set - actual_set
        if missing:
            failures.append(
                PolicyHarnessFailure(
                    failure_type=PolicyHarnessFailureType.EXPECTED_CONFLICT_MISSING,
                    message=f"missing conflict types: {sorted(missing)}",
                    field_name="actual_conflict_types",
                )
            )
        if not expected.allow_unexpected_conflicts:
            unexpected = actual_set - expected_set
            if unexpected:
                failures.append(
                    PolicyHarnessFailure(
                        failure_type=PolicyHarnessFailureType.UNEXPECTED_CONFLICT,
                        message=f"unexpected conflict types: {sorted(unexpected)}",
                        field_name="actual_conflict_types",
                    )
                )

    if expected.expected_violation_types:
        expected_v = {v.upper() for v in expected.expected_violation_types}
        actual_v = {v.upper() for v in actual.actual_violation_types}
        comparisons["violation_types"] = {
            "expected": sorted(expected_v),
            "actual": sorted(actual_v),
        }
        if not expected_v.intersection(actual_v):
            failures.append(
                PolicyHarnessFailure(
                    failure_type=PolicyHarnessFailureType.EXPECTED_VIOLATION_MISSING,
                    message="expected violation type not observed",
                    field_name="actual_violation_types",
                )
            )

    if expected.expected_resolution_trace and not actual.resolution_trace_hash:
        failures.append(
            PolicyHarnessFailure(
                failure_type=PolicyHarnessFailureType.EXPECTED_TRACE_MISSING,
                message="resolution trace hash missing",
                field_name="resolution_trace_hash",
            )
        )

    if expected.expected_violation_trace and not actual.violation_hash:
        failures.append(
            PolicyHarnessFailure(
                failure_type=PolicyHarnessFailureType.EXPECTED_VIOLATION_MISSING,
                message="violation hash missing",
                field_name="violation_hash",
            )
        )

    if expected.expected_reason_codes:
        expected_reasons = {r.upper() for r in expected.expected_reason_codes}
        actual_reasons = {r.upper() for r in actual.reason_codes}
        missing_reasons = expected_reasons - actual_reasons
        if missing_reasons:
            failures.append(
                PolicyHarnessFailure(
                    failure_type=PolicyHarnessFailureType.UNKNOWN_ACTUAL_VALUE,
                    message=f"missing reason codes: {sorted(missing_reasons)}",
                    field_name="reason_codes",
                )
            )

    critical = {
        PolicyHarnessFailureType.EXPECTED_ACTION_MISMATCH,
        PolicyHarnessFailureType.EXPECTED_RANK_MISMATCH,
        PolicyHarnessFailureType.EXPECTED_CONFLICT_MISSING,
        PolicyHarnessFailureType.EXPECTED_TRACE_MISSING,
        PolicyHarnessFailureType.EXPECTED_VIOLATION_MISSING,
        PolicyHarnessFailureType.UNEXPECTED_ENFORCEMENT,
        PolicyHarnessFailureType.NON_DETERMINISTIC_HASH,
        PolicyHarnessFailureType.ADAPTER_ERROR,
        PolicyHarnessFailureType.CONTEXT_BINDING_ERROR,
        PolicyHarnessFailureType.REGISTRY_ERROR,
    }
    has_critical = any(f.failure_type in critical for f in failures)

    if failures and has_critical:
        verdict = PolicyHarnessVerdict.FAIL
    elif failures:
        verdict = PolicyHarnessVerdict.WARN
    elif warnings:
        verdict = PolicyHarnessVerdict.WARN
    else:
        verdict = PolicyHarnessVerdict.PASS

    return verdict, tuple(failures), tuple(warnings), comparisons


def build_actual_from_resolution(
    resolution: ResolvedPolicySet,
    *,
    p0_verdict: str = "",
) -> PolicyHarnessActual:
    """Build harness actual from an existing ResolvedPolicySet."""
    return _actual_from_resolved_policy_set(resolution, p0_verdict=p0_verdict)


def evaluate_policy_harness_case(case: PolicyHarnessCase) -> PolicyHarnessResult:
    failures: list[PolicyHarnessFailure] = []
    warnings: list[str] = []
    comparisons: dict[str, Any] = {}

    try:
        actual = _execute_case_input(case.input)
    except PolicyResolutionValidationError as exc:
        failure = PolicyHarnessFailure(
            failure_type=PolicyHarnessFailureType.REGISTRY_ERROR,
            message=str(exc),
        )
        return PolicyHarnessResult(
            case_id=case.case_id,
            verdict=PolicyHarnessVerdict.ERROR,
            actual=PolicyHarnessActual(),
            failures=(failure,),
        ).with_canonical_hash()
    except Exception as exc:
        failure = PolicyHarnessFailure(
            failure_type=PolicyHarnessFailureType.ADAPTER_ERROR,
            message=f"{type(exc).__name__}: {exc}",
        )
        return PolicyHarnessResult(
            case_id=case.case_id,
            verdict=PolicyHarnessVerdict.ERROR,
            actual=PolicyHarnessActual(),
            failures=(failure,),
        ).with_canonical_hash()

    verdict, cmp_failures, cmp_warnings, comparisons = (
        compare_policy_harness_expected_actual(case.expected, actual)
    )
    failures.extend(cmp_failures)
    warnings.extend(cmp_warnings)

    if case.expected.expected_hash_stability:
        repeat = _execute_case_input(case.input)
        h1 = policy_harness_result_hash(
            PolicyHarnessResult(
                case_id=case.case_id,
                verdict=verdict,
                actual=actual,
                expected_vs_actual=comparisons,
            )
        )
        h2 = policy_harness_result_hash(
            PolicyHarnessResult(
                case_id=case.case_id,
                verdict=verdict,
                actual=repeat,
                expected_vs_actual=comparisons,
            )
        )
        if h1 != h2:
            failures.append(
                PolicyHarnessFailure(
                    failure_type=PolicyHarnessFailureType.NON_DETERMINISTIC_HASH,
                    message="repeated evaluation produced different result hash",
                    expected_value=h1,
                    actual_value=h2,
                )
            )
            verdict = PolicyHarnessVerdict.FAIL

    if case.expected.expected_verdict != PolicyHarnessVerdict.PASS:
        if verdict != case.expected.expected_verdict:
            failures.append(
                PolicyHarnessFailure(
                    failure_type=PolicyHarnessFailureType.POLICY_DESIGN_ERROR,
                    message="verdict mismatch vs expected_verdict",
                    expected_value=case.expected.expected_verdict.value,
                    actual_value=verdict.value,
                )
            )
            verdict = case.expected.expected_verdict

    return PolicyHarnessResult(
        case_id=case.case_id,
        verdict=verdict,
        actual=actual,
        expected_vs_actual=comparisons,
        failures=tuple(failures),
        warnings=tuple(warnings),
    ).with_canonical_hash()


def run_policy_harness_suite(suite: PolicyHarnessSuite) -> PolicyHarnessRun:
    results = tuple(evaluate_policy_harness_case(case) for case in suite.cases)
    return PolicyHarnessRun(suite_id=suite.suite_id, results=results)


def build_policy_harness_report(run: PolicyHarnessRun) -> PolicyHarnessReport:
    results = tuple(sorted(run.results, key=lambda r: r.case_id))
    passed = sum(1 for r in results if r.verdict == PolicyHarnessVerdict.PASS)
    failed = sum(1 for r in results if r.verdict == PolicyHarnessVerdict.FAIL)
    warned = sum(1 for r in results if r.verdict == PolicyHarnessVerdict.WARN)
    errored = sum(1 for r in results if r.verdict == PolicyHarnessVerdict.ERROR)
    skipped = sum(1 for r in results if r.verdict == PolicyHarnessVerdict.SKIPPED)

    coverage_conflict: dict[str, int] = {}
    coverage_family: dict[str, int] = {}
    coverage_violation: dict[str, int] = {}
    for result in results:
        for ct in result.actual.actual_conflict_types:
            coverage_conflict[ct] = coverage_conflict.get(ct, 0) + 1
        for vt in result.actual.actual_violation_types:
            coverage_violation[vt] = coverage_violation.get(vt, 0) + 1
        fam = result.actual.raw_safe_metadata.get("policy_families")
        if isinstance(fam, list):
            for f in fam:
                coverage_family[str(f)] = coverage_family.get(str(f), 0) + 1

    shadow_only_ok = all(
        r.actual.shadow_only and not r.actual.enforced for r in results
    )
    determinism_ok = not any(
        f.failure_type == PolicyHarnessFailureType.NON_DETERMINISTIC_HASH
        for r in results
        for f in r.failures
    )

    report = PolicyHarnessReport(
        suite_id=run.suite_id,
        case_count=len(results),
        passed=passed,
        failed=failed,
        warned=warned,
        errored=errored,
        skipped=skipped,
        coverage_by_conflict_type=coverage_conflict,
        coverage_by_policy_family=coverage_family,
        coverage_by_violation_type=coverage_violation,
        determinism_status="PASS" if determinism_ok else "FAIL",
        shadow_only_status="PASS" if shadow_only_ok else "FAIL",
        results=results,
    )
    return report.with_report_hash()
