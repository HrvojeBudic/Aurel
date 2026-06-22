"""P1.4.16 Identity Test Battery.

Integrated test harness for the P1.4 identity/autonomy/governance stack.
Tests the full chain: source → attestation → autonomy → claims → doctrine
→ authority delta → consent binding → CLI visibility.

P1.4.16 implements an integrated identity/autonomy/governance test battery.
It does not add new authority, execute tools, grant consent, mutate real config,
or act as a full P20 seal.
"""
from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class IdentityBatteryStatus(str, Enum):
    PASSED = "PASSED"
    FAILED = "FAILED"
    DEGRADED = "DEGRADED"
    SKIPPED = "SKIPPED"


class IdentityTestSeverity(str, Enum):
    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class IdentityTestCase:
    case_id: str
    name: str
    description: str
    severity: IdentityTestSeverity
    module_refs: tuple[str, ...]
    invariant_refs: tuple[str, ...]


@dataclass(frozen=True)
class IdentityTestResult:
    case_id: str
    status: IdentityBatteryStatus
    severity: IdentityTestSeverity

    summary: str
    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()

    evidence_refs: tuple[str, ...] = ()
    duration_ms: int | None = None


@dataclass(frozen=True)
class IdentityTestBatteryReport:
    report_id: str
    status: IdentityBatteryStatus

    total_cases: int
    passed: int
    failed: int
    degraded: int
    skipped: int

    highest_failed_severity: IdentityTestSeverity | None

    results: tuple[IdentityTestResult, ...]
    critical_failures: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()

    summary: str = ""


# ---------------------------------------------------------------------------
# Serialization
# ---------------------------------------------------------------------------


def identity_test_result_to_dict(result: IdentityTestResult) -> dict[str, object]:
    return {
        "case_id": result.case_id,
        "status": result.status.value,
        "severity": result.severity.value,
        "summary": result.summary,
        "errors": list(result.errors),
        "warnings": list(result.warnings),
        "evidence_refs": list(result.evidence_refs),
        "duration_ms": result.duration_ms,
    }


def identity_test_battery_report_to_dict(report: IdentityTestBatteryReport) -> dict[str, object]:
    return {
        "report_id": report.report_id,
        "status": report.status.value,
        "total_cases": report.total_cases,
        "passed": report.passed,
        "failed": report.failed,
        "degraded": report.degraded,
        "skipped": report.skipped,
        "highest_failed_severity": (
            report.highest_failed_severity.value
            if report.highest_failed_severity
            else None
        ),
        "results": [identity_test_result_to_dict(r) for r in report.results],
        "critical_failures": list(report.critical_failures),
        "warnings": list(report.warnings),
        "summary": report.summary,
    }


# ---------------------------------------------------------------------------
# Human summary
# ---------------------------------------------------------------------------


def format_identity_test_battery_report(report: IdentityTestBatteryReport) -> str:
    lines = [f"Identity Test Battery: {report.status.value}", ""]
    lines.append(f"Total: {report.total_cases}")
    lines.append(f"Passed: {report.passed}")
    lines.append(f"Failed: {report.failed}")
    if report.degraded > 0:
        lines.append(f"Degraded: {report.degraded}")
    if report.skipped > 0:
        lines.append(f"Skipped: {report.skipped}")
    if report.highest_failed_severity:
        lines.append(f"Highest failed severity: {report.highest_failed_severity.value}")

    if report.critical_failures:
        lines.append("")
        lines.append("Critical failures:")
        for f in report.critical_failures:
            lines.append(f"  - {f}")

    if report.warnings:
        lines.append("")
        lines.append("Warnings:")
        for w in report.warnings:
            lines.append(f"  - {w}")

    lines.append("")
    lines.append("Next:")
    lines.append("  identity verify --json")
    lines.append("  identity test-battery list --json")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------


def _build_case_registry() -> dict[str, IdentityTestCase]:
    """Build the test case registry. Requires scenario runners separately."""
    registry: list[IdentityTestCase] = []
    r = registry  # shorthand

    # -- 7.1 Smoke / import --
    r.append(IdentityTestCase(
        case_id="smoke_identity_modules",
        name="Import identity modules",
        description="All P1.4 identity modules are importable.",
        severity=IdentityTestSeverity.CRITICAL,
        module_refs=("identity",),
        invariant_refs=("INV-P1416-01",),
    ))
    r.append(IdentityTestCase(
        case_id="smoke_autonomy_modules",
        name="Import autonomy modules",
        description="Autonomy scale engine and measured autonomy modules are importable.",
        severity=IdentityTestSeverity.CRITICAL,
        module_refs=("autonomy",),
        invariant_refs=(),
    ))
    r.append(IdentityTestCase(
        case_id="smoke_claim_modules",
        name="Import claim modules",
        description="Capability claim boundary modules are importable.",
        severity=IdentityTestSeverity.CRITICAL,
        module_refs=("claims",),
        invariant_refs=(),
    ))
    r.append(IdentityTestCase(
        case_id="smoke_doctrine_modules",
        name="Import doctrine modules",
        description="External doctrine registry modules are importable.",
        severity=IdentityTestSeverity.CRITICAL,
        module_refs=("doctrine",),
        invariant_refs=(),
    ))
    r.append(IdentityTestCase(
        case_id="smoke_attestation_modules",
        name="Import attestation modules",
        description="Source attestation modules are importable.",
        severity=IdentityTestSeverity.CRITICAL,
        module_refs=("attestation",),
        invariant_refs=(),
    ))
    r.append(IdentityTestCase(
        case_id="smoke_authority_delta_modules",
        name="Import authority delta modules",
        description="Authority delta detector modules are importable.",
        severity=IdentityTestSeverity.CRITICAL,
        module_refs=("authority_delta",),
        invariant_refs=(),
    ))
    r.append(IdentityTestCase(
        case_id="smoke_consent_modules",
        name="Import consent modules",
        description="Operator consent binding modules are importable.",
        severity=IdentityTestSeverity.CRITICAL,
        module_refs=("consent",),
        invariant_refs=(),
    ))
    r.append(IdentityTestCase(
        case_id="smoke_cli_surface",
        name="Import CLI surface",
        description="Identity CLI surface module is importable.",
        severity=IdentityTestSeverity.CRITICAL,
        module_refs=("cli_surface",),
        invariant_refs=("INV-P1416-08",),
    ))

    # -- 7.3 Source attestation --
    r.append(IdentityTestCase(
        case_id="attestation_raw_hash_changes",
        name="Raw hash changes on source change",
        description="Raw hash must change when raw source bytes change.",
        severity=IdentityTestSeverity.HIGH,
        module_refs=("source_attestation",),
        invariant_refs=(),
    ))
    r.append(IdentityTestCase(
        case_id="attestation_canonical_hash_stable",
        name="Canonical hash stable for equivalents",
        description="Equivalent typed objects must produce stable canonical hash.",
        severity=IdentityTestSeverity.HIGH,
        module_refs=("source_attestation",),
        invariant_refs=(),
    ))

    # -- 7.8 Authority delta --
    r.append(IdentityTestCase(
        case_id="authority_delta_risk_ceiling_increase",
        name="Risk ceiling increase detected",
        description="Authority delta detector must detect risk ceiling increase.",
        severity=IdentityTestSeverity.CRITICAL,
        module_refs=("authority_delta",),
        invariant_refs=("INV-P1413-02",),
    ))
    r.append(IdentityTestCase(
        case_id="authority_delta_oversight_weakened",
        name="Oversight weakening detected",
        description="Authority delta detector must classify oversight weakening.",
        severity=IdentityTestSeverity.CRITICAL,
        module_refs=("authority_delta",),
        invariant_refs=("INV-P1413-04",),
    ))
    r.append(IdentityTestCase(
        case_id="authority_delta_external_effect_added",
        name="External-effect addition detected",
        description="Authority delta detector must detect external-effect tool additions.",
        severity=IdentityTestSeverity.CRITICAL,
        module_refs=("authority_delta",),
        invariant_refs=("INV-P1413-05",),
    ))
    r.append(IdentityTestCase(
        case_id="authority_delta_valid_source_still_requires_consent",
        name="Valid attested source can still require consent",
        description="An attested valid source can contain dangerous authority expansion.",
        severity=IdentityTestSeverity.HIGH,
        module_refs=("authority_delta", "source_attestation"),
        invariant_refs=("INV-P1413-01", "INV-P1414-02"),
    ))

    # -- 7.9 Operator consent --
    r.append(IdentityTestCase(
        case_id="consent_request_from_delta_report",
        name="Consent request from delta report",
        description="Consent request can be built from an authority delta report.",
        severity=IdentityTestSeverity.HIGH,
        module_refs=("authority_delta", "consent"),
        invariant_refs=("INV-P1414-01",),
    ))
    r.append(IdentityTestCase(
        case_id="consent_high_requires_risk_ack",
        name="HIGH/CRITICAL requires risk acknowledgement",
        description="HIGH severity consent grant fails without risk_acknowledged.",
        severity=IdentityTestSeverity.CRITICAL,
        module_refs=("consent",),
        invariant_refs=("INV-P1414-07",),
    ))
    r.append(IdentityTestCase(
        case_id="consent_binds_to_delta_id",
        name="Consent binds to delta ID",
        description="Consent for one delta does not cover another delta.",
        severity=IdentityTestSeverity.CRITICAL,
        module_refs=("consent",),
        invariant_refs=("INV-P1414-01",),
    ))
    r.append(IdentityTestCase(
        case_id="consent_binds_to_attestation_pair",
        name="Consent binds to attestation pair",
        description="Consent only validates when attestation IDs match.",
        severity=IdentityTestSeverity.CRITICAL,
        module_refs=("consent", "source_attestation"),
        invariant_refs=("INV-P1414-02",),
    ))
    r.append(IdentityTestCase(
        case_id="consent_revoked_invalid",
        name="Revoked consent is invalid",
        description="Revoked consent records never validate.",
        severity=IdentityTestSeverity.CRITICAL,
        module_refs=("consent",),
        invariant_refs=("INV-P1414-05",),
    ))
    r.append(IdentityTestCase(
        case_id="consent_expired_invalid",
        name="Expired consent is invalid",
        description="Expired consent records never validate.",
        severity=IdentityTestSeverity.CRITICAL,
        module_refs=("consent",),
        invariant_refs=("INV-P1414-06",),
    ))
    r.append(IdentityTestCase(
        case_id="consent_attestation_mismatch_invalid",
        name="Attestation mismatch invalid",
        description="New attestation mismatch invalidates consent.",
        severity=IdentityTestSeverity.CRITICAL,
        module_refs=("consent", "source_attestation"),
        invariant_refs=("INV-P1414-04",),
    ))
    r.append(IdentityTestCase(
        case_id="consent_does_not_grant_capability",
        name="Consent does not grant capability",
        description="A valid consent record does not mark capability as verified.",
        severity=IdentityTestSeverity.HIGH,
        module_refs=("consent", "claims"),
        invariant_refs=("INV-P1414-09",),
    ))

    # -- 7.10 CLI surface --
    r.append(IdentityTestCase(
        case_id="cli_status_json_works",
        name="identity status --json works",
        description="CLI identity status produces valid JSON.",
        severity=IdentityTestSeverity.CRITICAL,
        module_refs=("cli_surface",),
        invariant_refs=("INV-P1415-03",),
    ))
    r.append(IdentityTestCase(
        case_id="cli_verify_json_works",
        name="identity verify --json works",
        description="CLI identity verify produces valid JSON.",
        severity=IdentityTestSeverity.CRITICAL,
        module_refs=("cli_surface",),
        invariant_refs=("INV-P1415-03",),
    ))
    r.append(IdentityTestCase(
        case_id="cli_status_verify_read_only",
        name="Status and verify are read-only",
        description="Repeated status/verify calls produce identical output.",
        severity=IdentityTestSeverity.HIGH,
        module_refs=("cli_surface",),
        invariant_refs=("INV-P1415-02",),
    ))
    r.append(IdentityTestCase(
        case_id="cli_exposes_blockers",
        name="CLI exposes blockers",
        description="CLI status report exposes subsystem names and statuses.",
        severity=IdentityTestSeverity.MEDIUM,
        module_refs=("cli_surface",),
        invariant_refs=("INV-P1415-04",),
    ))

    # Build dict — ensure unique IDs
    result: dict[str, IdentityTestCase] = {}
    for case in registry:
        if case.case_id in result:
            raise AssertionError(f"Duplicate test case ID: {case.case_id}")
        result[case.case_id] = case
    return result


# Global registry (built once)
_test_case_registry: dict[str, IdentityTestCase] | None = None


def identity_test_cases() -> tuple[IdentityTestCase, ...]:
    """Return all registered identity test cases. Registry must not be empty."""
    global _test_case_registry
    if _test_case_registry is None:
        _test_case_registry = _build_case_registry()
    return tuple(_test_case_registry.values())


# ---------------------------------------------------------------------------
# Scenario runners map (case_id -> callable)
# ---------------------------------------------------------------------------


# Late import to avoid circular dependencies
def _get_scenario_runner(case_id: str) -> Callable[[], IdentityTestResult] | None:
    """Return the scenario runner for a given case_id, or None if not found."""
    from agentic_runtime.identity import identity_test_battery_scenarios as s

    runners: dict[str, Callable[[], IdentityTestResult]] = {
        "smoke_identity_modules": s.run_smoke_identity_modules,
        "smoke_autonomy_modules": s.run_smoke_autonomy_modules,
        "smoke_claim_modules": s.run_smoke_claim_modules,
        "smoke_doctrine_modules": s.run_smoke_doctrine_modules,
        "smoke_attestation_modules": s.run_smoke_attestation_modules,
        "smoke_authority_delta_modules": s.run_smoke_authority_delta_modules,
        "smoke_consent_modules": s.run_smoke_consent_modules,
        "smoke_cli_surface": s.run_smoke_cli_surface,
        "attestation_raw_hash_changes": s.run_attestation_raw_hash_changes,
        "attestation_canonical_hash_stable": s.run_attestation_canonical_hash_stable,
        "authority_delta_risk_ceiling_increase": s.run_authority_delta_risk_ceiling_increase,
        "authority_delta_oversight_weakened": s.run_authority_delta_oversight_weakened,
        "authority_delta_external_effect_added": s.run_authority_delta_external_effect_added,
        "authority_delta_valid_source_still_requires_consent": s.run_auth_delta_valid_source_requires_consent,
        "consent_request_from_delta_report": s.run_consent_request_from_delta_report,
        "consent_high_requires_risk_ack": s.run_consent_high_requires_risk_ack,
        "consent_binds_to_delta_id": s.run_consent_binds_to_delta_id,
        "consent_binds_to_attestation_pair": s.run_consent_binds_to_attestation_pair,
        "consent_revoked_invalid": s.run_consent_revoked_invalid,
        "consent_expired_invalid": s.run_consent_expired_invalid,
        "consent_attestation_mismatch_invalid": s.run_consent_attestation_mismatch_invalid,
        "consent_does_not_grant_capability": s.run_consent_does_not_grant_capability,
        "cli_status_json_works": s.run_cli_status_json_works,
        "cli_verify_json_works": s.run_cli_verify_json_works,
        "cli_status_verify_read_only": s.run_cli_status_verify_read_only,
        "cli_exposes_blockers": s.run_cli_exposes_blockers,
    }
    return runners.get(case_id)


# ---------------------------------------------------------------------------
# Engine: run one case
# ---------------------------------------------------------------------------


def run_identity_test_case(case: IdentityTestCase) -> IdentityTestResult:
    """Run a single identity test case. Catches expected failures gracefully."""
    start = time.monotonic()
    runner = _get_scenario_runner(case.case_id)
    if runner is None:
        end = time.monotonic()
        return IdentityTestResult(
            case_id=case.case_id,
            status=IdentityBatteryStatus.SKIPPED,
            severity=case.severity,
            summary=f"No scenario runner registered for {case.case_id}",
            warnings=("no_runner",),
            duration_ms=int((end - start) * 1000),
        )

    try:
        result = runner()
    except Exception as exc:
        end = time.monotonic()
        return IdentityTestResult(
            case_id=case.case_id,
            status=IdentityBatteryStatus.FAILED,
            severity=case.severity,
            summary=f"Unexpected exception: {exc}",
            errors=(f"exception:{type(exc).__name__}:{exc}",),
            evidence_refs=(case.case_id,),
            duration_ms=int((end - start) * 1000),
        )

    # Preserve duration from the scenario runner if it didn't set it
    end = time.monotonic()
    if result.duration_ms is None:
        # Create a new result with duration
        return IdentityTestResult(
            case_id=result.case_id,
            status=result.status,
            severity=result.severity,
            summary=result.summary,
            errors=result.errors,
            warnings=result.warnings,
            evidence_refs=result.evidence_refs,
            duration_ms=int((end - start) * 1000),
        )
    return result


# ---------------------------------------------------------------------------
# Engine: run full battery
# ---------------------------------------------------------------------------


_SEVERITY_ORDER = {
    IdentityTestSeverity.INFO: 0,
    IdentityTestSeverity.LOW: 1,
    IdentityTestSeverity.MEDIUM: 2,
    IdentityTestSeverity.HIGH: 3,
    IdentityTestSeverity.CRITICAL: 4,
}


def run_identity_test_battery(
    *,
    include_adversarial: bool = True,
    include_cli: bool = True,
) -> IdentityTestBatteryReport:
    """Run all registered cases. Returns a structured battery report."""
    cases = identity_test_cases()
    results: list[IdentityTestResult] = []
    passed = 0
    failed = 0
    degraded = 0
    skipped = 0
    critical_failures: list[str] = []
    warnings: list[str] = []
    highest_failed_sev: IdentityTestSeverity | None = None

    for case in cases:
        # Filter rules: some cases are CLI-only
        if not include_cli and case.case_id.startswith("cli_"):
            continue
        if not include_adversarial:
            # Smoke cases are always included
            if not case.case_id.startswith("smoke_"):
                continue

        result = run_identity_test_case(case)
        results.append(result)

        if result.status == IdentityBatteryStatus.PASSED:
            passed += 1
        elif result.status == IdentityBatteryStatus.FAILED:
            failed += 1
            if case.severity in (IdentityTestSeverity.CRITICAL, IdentityTestSeverity.HIGH):
                critical_failures.append(case.case_id)
            # Track highest failed severity
            sev_level = _SEVERITY_ORDER.get(case.severity, 0)
            if result.status == IdentityBatteryStatus.FAILED:
                if highest_failed_sev is None:
                    highest_failed_sev = case.severity
                elif _SEVERITY_ORDER.get(highest_failed_sev, 0) < sev_level:
                    highest_failed_sev = case.severity
        elif result.status == IdentityBatteryStatus.DEGRADED:
            degraded += 1
            if case.severity == IdentityTestSeverity.CRITICAL:
                critical_failures.append(case.case_id)
        elif result.status == IdentityBatteryStatus.SKIPPED:
            skipped += 1

        for e in result.errors:
            if e not in warnings:
                warnings.append(e)

    # Determine overall status
    if critical_failures:
        overall = IdentityBatteryStatus.FAILED
    elif failed > 0:
        overall = IdentityBatteryStatus.FAILED
    elif degraded > 0:
        overall = IdentityBatteryStatus.DEGRADED
    elif skipped > 0:
        overall = IdentityBatteryStatus.DEGRADED
    else:
        overall = IdentityBatteryStatus.PASSED

    total = passed + failed + degraded + skipped
    summary = (
        f"Identity Test Battery: {overall.value}. "
        f"Total: {total}, Passed: {passed}, Failed: {failed}"
    )
    if degraded:
        summary += f", Degraded: {degraded}"
    if skipped:
        summary += f", Skipped: {skipped}"

    report_id = (
        "itb_"
        + hashlib.sha256(json.dumps(sorted(c.case_id for c in cases)).encode()).hexdigest()[:20]
    )

    return IdentityTestBatteryReport(
        report_id=report_id,
        status=overall,
        total_cases=total,
        passed=passed,
        failed=failed,
        degraded=degraded,
        skipped=skipped,
        highest_failed_severity=highest_failed_sev,
        results=tuple(results),
        critical_failures=tuple(critical_failures),
        warnings=tuple(warnings),
        summary=summary,
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

__all__ = [
    "IdentityBatteryStatus",
    "IdentityTestSeverity",
    "IdentityTestCase",
    "IdentityTestResult",
    "IdentityTestBatteryReport",
    "identity_test_cases",
    "run_identity_test_case",
    "run_identity_test_battery",
    "identity_test_result_to_dict",
    "identity_test_battery_report_to_dict",
    "format_identity_test_battery_report",
]
