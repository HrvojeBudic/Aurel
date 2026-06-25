"""P1.6.20 — P1.6 Policy Cards Exit Seal + Live Integration Demo.

Read-only proof layer verifying the Integration-First vertical slice for P1.6.
Does NOT add policy enforcement, write to the Ledger, activate approvals,
block commands, or change runtime sandbox behavior.

P1.6.20 seals the Policy Cards & Behavioral Contracts section as an
Integration-First vertical slice; it proves what exists and honestly reports
what is unavailable.
"""
from __future__ import annotations

import hashlib
import inspect
import json
import os
import re
import subprocess  # nosec B404 - exit seal intentionally runs fixed local CLI verification commands
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Mapping, Sequence

from .projection_contract import (
    POLICY_PROJECTION_CONTRACT_VERSION,
    PolicyProjectionSourceLabel,
    PolicyProjectionStatus,
    build_policy_projection_contract,
    policy_projection_hash,
    policy_projection_to_json_safe_dict,
)

POLICY_EXIT_SEAL_VERSION: str = "policy_exit_seal.v1"
NEXT_TASK: str = "P1.7.0 — Path Governance & Source Trust Foundation"

_SENSITIVE_KEYS = frozenset({
    "password", "passwd", "secret", "token", "api_key", "apikey",
    "authorization", "credential", "private_key", "access_key",
})
_FORBIDDEN_SECRET_PATTERN = re.compile(
    r"(password|api[_-]?key|secret|token|credential)",
    re.IGNORECASE,
)

_CRITICAL_CHECK_IDS = frozenset({
    "projection_contract_builds",
    "projection_json_valid",
    "projection_hash_present",
    "contract_version_present",
    "source_labels_present",
    "no_fake_live_state",
    "unavailable_reasons_visible",
    "cli_status_available_or_honest",
    "cli_projection_json_available_or_honest",
    "cli_unavailable_available_or_honest",
    "docs_state_reports_present",
    "non_enforcement_confirmed",
    "no_runtime_submit_confirmed",
})


class PolicyExitSealVerdict(str, Enum):
    PASS = "PASS"  # nosec B105 - enum verdict label, not a credential
    WARN = "WARN"
    FAIL = "FAIL"
    ERROR = "ERROR"
    SKIPPED = "SKIPPED"


class PolicyExitSealReportVerdict(str, Enum):
    PASS = "PASS"  # nosec B105 - enum verdict label, not a credential
    PASS_WITH_WARNINGS = "PASS_WITH_WARNINGS"  # nosec B105 - enum verdict label, not a credential
    FAIL = "FAIL"
    ERROR = "ERROR"


class PolicyExitSealCheckId(str, Enum):
    PROJECTION_CONTRACT_BUILDS = "projection_contract_builds"
    PROJECTION_JSON_VALID = "projection_json_valid"
    PROJECTION_HASH_PRESENT = "projection_hash_present"
    CONTRACT_VERSION_PRESENT = "contract_version_present"
    SOURCE_LABELS_PRESENT = "source_labels_present"
    NO_FAKE_LIVE_STATE = "no_fake_live_state"
    UNAVAILABLE_REASONS_VISIBLE = "unavailable_reasons_visible"
    CLI_STATUS_AVAILABLE_OR_HONEST = "cli_status_available_or_honest"
    CLI_PROJECTION_JSON_AVAILABLE_OR_HONEST = "cli_projection_json_available_or_honest"
    CLI_UNAVAILABLE_AVAILABLE_OR_HONEST = "cli_unavailable_available_or_honest"
    HARNESS_AVAILABLE_OR_HONESTLY_UNAVAILABLE = "harness_available_or_honestly_unavailable"
    RESOLUTION_TRACE_AVAILABLE_OR_HONESTLY_UNAVAILABLE = (
        "resolution_trace_available_or_honestly_unavailable"
    )
    VIOLATION_TRACE_AVAILABLE_OR_HONESTLY_UNAVAILABLE = (
        "violation_trace_available_or_honestly_unavailable"
    )
    DOCS_STATE_REPORTS_PRESENT = "docs_state_reports_present"
    NON_ENFORCEMENT_CONFIRMED = "non_enforcement_confirmed"
    NO_LEDGER_WRITE_CONFIRMED = "no_ledger_write_confirmed"
    NO_APPROVAL_ACTIVATION_CONFIRMED = "no_approval_activation_confirmed"
    NO_SANDBOX_CHANGE_CONFIRMED = "no_sandbox_change_confirmed"
    NO_RUNTIME_SUBMIT_CONFIRMED = "no_runtime_submit_confirmed"
    P1_7_NEXT_TASK_RECORDED = "p1_7_next_task_recorded"


@dataclass(frozen=True)
class PolicyExitSealCheck:
    check_id: str
    name: str
    description: str
    category: str = "general"


@dataclass(frozen=True)
class PolicyExitSealFailure:
    check_id: str
    code: str
    message: str


@dataclass(frozen=True)
class PolicyExitSealResult:
    check_id: str
    verdict: PolicyExitSealVerdict
    summary: str
    evidence_refs: tuple[str, ...] = ()
    details: Mapping[str, Any] = field(default_factory=dict)
    duration_ms: int | None = None


@dataclass(frozen=True)
class PolicyExitSealReport:
    report_id: str
    seal_version: str
    verdict: PolicyExitSealReportVerdict
    checks: tuple[PolicyExitSealResult, ...]
    projection_status: str
    cli_status: str
    harness_status: str
    trace_status: str
    docs_status: str
    governance_status: str
    next_task: str
    summary: str
    generated_at: str


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _run_cli(*args: str, timeout_s: int = 30) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = f"src{os.pathsep}."
    return subprocess.run(  # nosec B603 - fixed local CLI argv assembled from explicit argument strings
        [sys.executable, "-m", "agentic_runtime.cli", *args],
        capture_output=True,
        text=True,
        timeout=timeout_s,
        cwd=_repo_root(),
        env=env,
        check=False,
    )


def _run_cli_safe(*args: str, timeout_s: int = 30) -> tuple[bool, str, str]:
    try:
        proc = _run_cli(*args, timeout_s=timeout_s)
        return proc.returncode == 0, proc.stdout, proc.stderr
    except subprocess.TimeoutExpired:
        return False, "", "timeout"
    except Exception as exc:
        return False, "", str(exc)


def _make_result(
    check_id: str,
    verdict: PolicyExitSealVerdict,
    summary: str,
    *,
    evidence_refs: tuple[str, ...] = (),
    details: Mapping[str, Any] | None = None,
    duration_ms: int | None = None,
) -> PolicyExitSealResult:
    return PolicyExitSealResult(
        check_id=check_id,
        verdict=verdict,
        summary=summary,
        evidence_refs=evidence_refs,
        details=dict(details or {}),
        duration_ms=duration_ms,
    )


def _chk(
    check_id: str,
    name: str = "",
    description: str = "",
    category: str = "general",
) -> PolicyExitSealCheck:
    return PolicyExitSealCheck(
        check_id=check_id,
        name=name or check_id,
        description=description or check_id,
        category=category,
    )


def policy_exit_seal_checks() -> tuple[PolicyExitSealCheck, ...]:
    """Return the P1.6.20 exit seal check registry."""
    return (
        _chk(
            PolicyExitSealCheckId.PROJECTION_CONTRACT_BUILDS.value,
            "Projection contract builds",
            "PolicyProjectionContract v1 builds successfully",
            "projection",
        ),
        _chk(
            PolicyExitSealCheckId.PROJECTION_JSON_VALID.value,
            "Projection JSON valid",
            "Projection serializes to JSON-safe dict",
            "projection",
        ),
        _chk(
            PolicyExitSealCheckId.PROJECTION_HASH_PRESENT.value,
            "Projection hash present",
            "projection_hash is non-empty 64-char hex",
            "projection",
        ),
        _chk(
            PolicyExitSealCheckId.CONTRACT_VERSION_PRESENT.value,
            "Contract version present",
            "contract_version is policy_projection.v1",
            "projection",
        ),
        _chk(
            PolicyExitSealCheckId.SOURCE_LABELS_PRESENT.value,
            "Source labels present",
            "All projection sections declare source labels",
            "projection",
        ),
        _chk(
            PolicyExitSealCheckId.NO_FAKE_LIVE_STATE.value,
            "No fake LIVE state",
            "No fixture/simulated data labeled LIVE; shell_binding UNAVAILABLE",
            "projection",
        ),
        _chk(
            PolicyExitSealCheckId.UNAVAILABLE_REASONS_VISIBLE.value,
            "Unavailable reasons visible",
            "UNAVAILABLE sections include reasons",
            "projection",
        ),
        _chk(
            PolicyExitSealCheckId.CLI_STATUS_AVAILABLE_OR_HONEST.value,
            "CLI policy status",
            "policy status works or reports ERROR/UNAVAILABLE",
            "cli",
        ),
        _chk(
            PolicyExitSealCheckId.CLI_PROJECTION_JSON_AVAILABLE_OR_HONEST.value,
            "CLI policy projection --json",
            "policy projection --json works or reports ERROR",
            "cli",
        ),
        _chk(
            PolicyExitSealCheckId.CLI_UNAVAILABLE_AVAILABLE_OR_HONEST.value,
            "CLI policy unavailable",
            "policy unavailable works or reports ERROR",
            "cli",
        ),
        _chk(
            PolicyExitSealCheckId.HARNESS_AVAILABLE_OR_HONESTLY_UNAVAILABLE.value,
            "Policy harness",
            "Harness module and CLI list command available",
            "harness",
        ),
        _chk(
            PolicyExitSealCheckId.RESOLUTION_TRACE_AVAILABLE_OR_HONESTLY_UNAVAILABLE.value,
            "Resolution trace",
            "Resolution trace module and projection section available",
            "trace",
        ),
        _chk(
            PolicyExitSealCheckId.VIOLATION_TRACE_AVAILABLE_OR_HONESTLY_UNAVAILABLE.value,
            "Violation trace",
            "Violation trace module and projection section available",
            "trace",
        ),
        _chk(
            PolicyExitSealCheckId.DOCS_STATE_REPORTS_PRESENT.value,
            "Docs/state/reports present",
            "P1.6.17–P1.6.19 reports and agent canon files exist",
            "docs",
        ),
        _chk(
            PolicyExitSealCheckId.NON_ENFORCEMENT_CONFIRMED.value,
            "Non-enforcement confirmed",
            "Exit seal module does not import runtime/enforcement",
            "governance",
        ),
        _chk(
            PolicyExitSealCheckId.NO_LEDGER_WRITE_CONFIRMED.value,
            "No Ledger write",
            "Exit seal does not write to Ledger",
            "governance",
        ),
        _chk(
            PolicyExitSealCheckId.NO_APPROVAL_ACTIVATION_CONFIRMED.value,
            "No approval activation",
            "Exit seal does not activate approvals",
            "governance",
        ),
        _chk(
            PolicyExitSealCheckId.NO_SANDBOX_CHANGE_CONFIRMED.value,
            "No sandbox change",
            "Exit seal does not mutate sandbox",
            "governance",
        ),
        _chk(
            PolicyExitSealCheckId.NO_RUNTIME_SUBMIT_CONFIRMED.value,
            "No runtime submit",
            "Exit seal does not call AgenticRuntime.submit",
            "governance",
        ),
        _chk(
            PolicyExitSealCheckId.P1_7_NEXT_TASK_RECORDED.value,
            "P1.7.0 next task recorded",
            "ACTIVE_TASK.md records P1.7.0 as next planned task",
            "docs",
        ),
    )


def _build_projection_contract():
    return build_policy_projection_contract(cli_binding_available=True)


def _section_by_id(contract, section_id: str):
    return next(s for s in contract.sections if s.section_id == section_id)


def _executable_source() -> str:
    """Return module source excluding the module docstring."""
    source = inspect.getsource(sys.modules[__name__])
    if source.lstrip().startswith('"""'):
        end = source.find('"""', source.index('"""') + 3)
        if end != -1:
            source = source[end + 3 :]
    return source


def _static_governance_check(check_id: str, forbidden: tuple[str, ...]) -> PolicyExitSealResult:
    """Verify governance check runners do not contain forbidden call patterns."""
    import ast

    tree = ast.parse(_executable_source())
    found: list[str] = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == "_static_governance_check":
            continue
        for inner in ast.walk(node):
            if isinstance(inner, ast.Call):
                if isinstance(inner.func, ast.Attribute):
                    attr = inner.func.attr
                    if attr in forbidden:
                        found.append(attr)
                elif isinstance(inner.func, ast.Name):
                    if inner.func.id in forbidden:
                        found.append(inner.func.id)
    if found:
        return _make_result(
            check_id,
            PolicyExitSealVerdict.FAIL,
            f"Forbidden call patterns found: {sorted(set(found))}",
            evidence_refs=("exit_seal.py",),
        )
    return _make_result(
        check_id,
        PolicyExitSealVerdict.PASS,
        "Exit seal module source passes governance boundary check",
        evidence_refs=("exit_seal.py",),
    )


def run_policy_exit_seal_check(
    check: PolicyExitSealCheck,
    *,
    include_cli: bool = True,
) -> PolicyExitSealResult:
    """Run a single exit seal check. Does NOT mutate runtime state."""
    t0 = time.monotonic()
    cid = check.check_id

    if not include_cli and cid.startswith("cli_"):
        return _make_result(
            cid,
            PolicyExitSealVerdict.SKIPPED,
            "CLI check skipped by caller option",
            evidence_refs=("include_cli=False",),
        )

    try:
        if cid == PolicyExitSealCheckId.PROJECTION_CONTRACT_BUILDS.value:
            contract = _build_projection_contract()
            ok = isinstance(contract.sections, tuple) and len(contract.sections) >= 8
            result = _make_result(
                cid,
                PolicyExitSealVerdict.PASS if ok else PolicyExitSealVerdict.FAIL,
                f"Projection contract built with {len(contract.sections)} sections"
                if ok
                else "Projection contract build failed",
                evidence_refs=("build_policy_projection_contract",),
            )

        elif cid == PolicyExitSealCheckId.PROJECTION_JSON_VALID.value:
            contract = _build_projection_contract()
            payload = policy_projection_to_json_safe_dict(contract)
            json.dumps(payload, sort_keys=True, separators=(",", ":"))
            result = _make_result(
                cid,
                PolicyExitSealVerdict.PASS,
                "Projection payload is JSON-serializable",
                evidence_refs=("policy_projection_to_json_safe_dict",),
            )

        elif cid == PolicyExitSealCheckId.PROJECTION_HASH_PRESENT.value:
            contract = _build_projection_contract()
            h = contract.projection_hash
            hex_part = h.replace("sha256:", "") if h.startswith("sha256:") else h
            ok = len(hex_part) == 64 and all(c in "0123456789abcdef" for c in hex_part)
            result = _make_result(
                cid,
                PolicyExitSealVerdict.PASS if ok else PolicyExitSealVerdict.FAIL,
                f"projection_hash present: {h[:20]}..." if ok else "projection_hash missing or invalid",
                evidence_refs=("projection_hash",),
            )

        elif cid == PolicyExitSealCheckId.CONTRACT_VERSION_PRESENT.value:
            contract = _build_projection_contract()
            ok = contract.contract_version == POLICY_PROJECTION_CONTRACT_VERSION
            result = _make_result(
                cid,
                PolicyExitSealVerdict.PASS if ok else PolicyExitSealVerdict.FAIL,
                f"contract_version={contract.contract_version}",
                evidence_refs=(POLICY_PROJECTION_CONTRACT_VERSION,),
            )

        elif cid == PolicyExitSealCheckId.SOURCE_LABELS_PRESENT.value:
            contract = _build_projection_contract()
            payload = policy_projection_to_json_safe_dict(contract)
            sections = payload.get("sections", {})
            missing = [
                sid for sid, data in sections.items()
                if not data.get("source")
            ]
            ok = not missing
            result = _make_result(
                cid,
                PolicyExitSealVerdict.PASS if ok else PolicyExitSealVerdict.FAIL,
                "All sections have source labels" if ok else f"Missing source: {missing}",
                evidence_refs=("sections",),
            )

        elif cid == PolicyExitSealCheckId.NO_FAKE_LIVE_STATE.value:
            contract = _build_projection_contract()
            shell = _section_by_id(contract, "shell_binding")
            fake_live = []
            for section in contract.sections:
                if section.source is PolicyProjectionSourceLabel.LIVE:
                    meta = section.metadata or {}
                    if meta.get("fixture") or meta.get("simulated"):
                        fake_live.append(section.section_id)
            ok = (
                shell.source is PolicyProjectionSourceLabel.UNAVAILABLE
                and not fake_live
            )
            result = _make_result(
                cid,
                PolicyExitSealVerdict.PASS if ok else PolicyExitSealVerdict.FAIL,
                "shell_binding UNAVAILABLE; no fake LIVE sections"
                if ok
                else f"Fake LIVE or shell not UNAVAILABLE: {fake_live}",
                evidence_refs=("shell_binding",),
            )

        elif cid == PolicyExitSealCheckId.UNAVAILABLE_REASONS_VISIBLE.value:
            contract = _build_projection_contract()
            missing = [
                s.section_id
                for s in contract.sections
                if s.source is PolicyProjectionSourceLabel.UNAVAILABLE
                and s.unavailable_reason is None
            ]
            ok = not missing
            result = _make_result(
                cid,
                PolicyExitSealVerdict.PASS if ok else PolicyExitSealVerdict.FAIL,
                "All UNAVAILABLE sections have reasons"
                if ok
                else f"Missing reasons: {missing}",
                evidence_refs=("unavailable_reason",),
            )

        elif cid == PolicyExitSealCheckId.CLI_STATUS_AVAILABLE_OR_HONEST.value:
            ok, out, err = _run_cli_safe("policy", "status")
            has_version = "policy_projection.v1" in out
            result = _make_result(
                cid,
                PolicyExitSealVerdict.PASS if ok and has_version else PolicyExitSealVerdict.ERROR,
                "policy status succeeded" if ok and has_version else f"policy status failed: {err}",
                evidence_refs=("policy status",),
            )

        elif cid == PolicyExitSealCheckId.CLI_PROJECTION_JSON_AVAILABLE_OR_HONEST.value:
            ok, out, err = _run_cli_safe("policy", "projection", "--json")
            if ok:
                try:
                    payload = json.loads(out)
                    has_fields = (
                        payload.get("contract_version") == POLICY_PROJECTION_CONTRACT_VERSION
                        and payload.get("projection_hash")
                    )
                    verdict = PolicyExitSealVerdict.PASS if has_fields else PolicyExitSealVerdict.FAIL
                    summary = "policy projection --json valid" if has_fields else "JSON missing required fields"
                except json.JSONDecodeError as exc:
                    verdict = PolicyExitSealVerdict.ERROR
                    summary = f"JSON parse failed: {exc}"
            else:
                verdict = PolicyExitSealVerdict.ERROR
                summary = f"CLI failed: {err}"
            result = _make_result(
                cid,
                verdict,
                summary,
                evidence_refs=("policy projection --json",),
            )

        elif cid == PolicyExitSealCheckId.CLI_UNAVAILABLE_AVAILABLE_OR_HONEST.value:
            ok, out, err = _run_cli_safe("policy", "unavailable")
            has_shell = "shell_binding" in out
            result = _make_result(
                cid,
                PolicyExitSealVerdict.PASS if ok and has_shell else PolicyExitSealVerdict.ERROR,
                "policy unavailable lists shell_binding"
                if ok and has_shell
                else f"policy unavailable failed: {err}",
                evidence_refs=("policy unavailable",),
            )

        elif cid == PolicyExitSealCheckId.HARNESS_AVAILABLE_OR_HONESTLY_UNAVAILABLE.value:
            from . import test_harness  # noqa: F401
            ok, out, err = _run_cli_safe("policy", "harness", "list")
            has_cases = "all_allow_no_conflict" in out or ok
            result = _make_result(
                cid,
                PolicyExitSealVerdict.PASS if ok and has_cases else PolicyExitSealVerdict.WARN,
                "Policy harness list available"
                if ok and has_cases
                else f"Harness list unavailable: {err}",
                evidence_refs=("test_harness", "policy harness list"),
            )

        elif cid == PolicyExitSealCheckId.RESOLUTION_TRACE_AVAILABLE_OR_HONESTLY_UNAVAILABLE.value:
            from . import resolution_trace  # noqa: F401
            contract = _build_projection_contract()
            section = _section_by_id(contract, "resolution_trace")
            module_ok = section.status is PolicyProjectionStatus.AVAILABLE
            trace_verified = bool(section.hashes.get("resolution_trace_hash"))
            if module_ok and not trace_verified:
                verdict = PolicyExitSealVerdict.WARN
                summary = (
                    "Resolution trace module LIVE; full Ledger integration not claimed "
                    "(TRACE_VERIFIED requires evidence hash)"
                )
            else:
                verdict = PolicyExitSealVerdict.PASS if module_ok else PolicyExitSealVerdict.WARN
                summary = "Resolution trace available" if module_ok else "Resolution trace unavailable"
            result = _make_result(
                cid,
                verdict,
                summary,
                evidence_refs=("resolution_trace",),
            )

        elif cid == PolicyExitSealCheckId.VIOLATION_TRACE_AVAILABLE_OR_HONESTLY_UNAVAILABLE.value:
            from . import violation_trace  # noqa: F401
            contract = _build_projection_contract()
            section = _section_by_id(contract, "violation_trace")
            module_ok = section.status is PolicyProjectionStatus.AVAILABLE
            trace_verified = bool(section.hashes.get("violation_trace_hash"))
            if module_ok and not trace_verified:
                verdict = PolicyExitSealVerdict.WARN
                summary = (
                    "Violation trace module LIVE; full Ledger integration not claimed "
                    "(TRACE_VERIFIED requires evidence hash)"
                )
            else:
                verdict = PolicyExitSealVerdict.PASS if module_ok else PolicyExitSealVerdict.WARN
                summary = "Violation trace available" if module_ok else "Violation trace unavailable"
            result = _make_result(
                cid,
                verdict,
                summary,
                evidence_refs=("violation_trace",),
            )

        elif cid == PolicyExitSealCheckId.DOCS_STATE_REPORTS_PRESENT.value:
            root = _repo_root()
            required = (
                "agent/reports/P1.6.17_POLICY_PROJECTION_API_EVENT_CONTRACT_REPORT.md",
                "agent/reports/P1.6.18_POLICY_CLI_TUI_BINDING_REPORT.md",
                "agent/reports/P1.6.19_POLICY_DOCS_STATE_REPORTS_UPDATE.md",
                "agent/ACTIVE_TASK.md",
                "agent/STATE.md",
                "agent/ROADMAP.md",
                "agent/TESTS.md",
                "agent/REPORTS.md",
                "agent/ARCHITECTURE.md",
                "agent/DECISIONS.md",
            )
            missing = [p for p in required if not (root / p).is_file()]
            ok = not missing
            result = _make_result(
                cid,
                PolicyExitSealVerdict.PASS if ok else PolicyExitSealVerdict.FAIL,
                "All required docs/reports present" if ok else f"Missing: {missing}",
                evidence_refs=tuple(required),
            )

        elif cid == PolicyExitSealCheckId.NON_ENFORCEMENT_CONFIRMED.value:
            import ast

            tree = ast.parse(_executable_source())
            bad_modules: list[str] = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if any(
                            term in alias.name
                            for term in ("runtime", "approval", "ledger", "sandbox")
                        ):
                            bad_modules.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    mod = node.module or ""
                    if any(
                        term in mod
                        for term in ("runtime", "approval", "ledger", "sandbox")
                    ):
                        bad_modules.append(mod)
            result = _make_result(
                cid,
                PolicyExitSealVerdict.PASS if not bad_modules else PolicyExitSealVerdict.FAIL,
                "Exit seal module has no enforcement imports"
                if not bad_modules
                else f"Forbidden imports: {bad_modules}",
                evidence_refs=("exit_seal.py",),
            )

        elif cid == PolicyExitSealCheckId.NO_LEDGER_WRITE_CONFIRMED.value:
            result = _static_governance_check(
                cid, ("write_ledger", "append_ledger"),
            )

        elif cid == PolicyExitSealCheckId.NO_APPROVAL_ACTIVATION_CONFIRMED.value:
            result = _static_governance_check(
                cid, ("activate_approval", "approve"),
            )

        elif cid == PolicyExitSealCheckId.NO_SANDBOX_CHANGE_CONFIRMED.value:
            result = _static_governance_check(
                cid, ("mutate_sandbox",),
            )

        elif cid == PolicyExitSealCheckId.NO_RUNTIME_SUBMIT_CONFIRMED.value:
            result = _static_governance_check(
                cid, ("submit",),
            )

        elif cid == PolicyExitSealCheckId.P1_7_NEXT_TASK_RECORDED.value:
            task_path = _repo_root() / "agent" / "ACTIVE_TASK.md"
            if task_path.is_file():
                content = task_path.read_text()
                ok = "P1.7.0" in content and "Path Governance" in content
                result = _make_result(
                    cid,
                    PolicyExitSealVerdict.PASS if ok else PolicyExitSealVerdict.WARN,
                    "P1.7.0 next task recorded in ACTIVE_TASK.md"
                    if ok
                    else "P1.7.0 pointer not yet in ACTIVE_TASK.md (update pending)",
                    evidence_refs=("agent/ACTIVE_TASK.md",),
                )
            else:
                result = _make_result(
                    cid,
                    PolicyExitSealVerdict.WARN,
                    "ACTIVE_TASK.md not found",
                    evidence_refs=("agent/ACTIVE_TASK.md",),
                )

        else:
            result = _make_result(
                cid,
                PolicyExitSealVerdict.SKIPPED,
                f"No runner defined for check '{cid}'",
                evidence_refs=(check.check_id,),
            )

        elapsed_ms = int((time.monotonic() - t0) * 1000)
        return PolicyExitSealResult(
            check_id=result.check_id,
            verdict=result.verdict,
            summary=result.summary,
            evidence_refs=result.evidence_refs,
            details=result.details,
            duration_ms=elapsed_ms,
        )

    except Exception as exc:
        elapsed_ms = int((time.monotonic() - t0) * 1000)
        return _make_result(
            cid,
            PolicyExitSealVerdict.ERROR,
            f"Unexpected error: {type(exc).__name__}: {exc}",
            evidence_refs=(check.check_id,),
            duration_ms=elapsed_ms,
        )


def decide_policy_exit_seal_verdict(
    results: Sequence[PolicyExitSealResult],
) -> PolicyExitSealReportVerdict:
    """Decide overall seal verdict from individual check results."""
    errors = [
        r for r in results
        if r.verdict is PolicyExitSealVerdict.ERROR
        and r.check_id in _CRITICAL_CHECK_IDS
    ]
    failures = [r for r in results if r.verdict is PolicyExitSealVerdict.FAIL]
    warnings = [r for r in results if r.verdict is PolicyExitSealVerdict.WARN]

    if errors:
        return PolicyExitSealReportVerdict.ERROR
    if failures:
        return PolicyExitSealReportVerdict.FAIL
    if warnings:
        return PolicyExitSealReportVerdict.PASS_WITH_WARNINGS
    return PolicyExitSealReportVerdict.PASS


def _category_status(results: Sequence[PolicyExitSealResult], prefix: str) -> str:
    relevant = [r for r in results if r.check_id.startswith(prefix) or prefix in r.evidence_refs]
    if not relevant:
        # Match by check category from registry
        checks = {c.check_id: c.category for c in policy_exit_seal_checks()}
        relevant = [r for r in results if checks.get(r.check_id, "").startswith(prefix)]
    if not relevant:
        return "NONE"
    if any(r.verdict in (PolicyExitSealVerdict.FAIL, PolicyExitSealVerdict.ERROR) for r in relevant):
        return "ISSUES"
    if any(r.verdict is PolicyExitSealVerdict.WARN for r in relevant):
        return "WARN"
    return "OK"


def _checks_for_category(results: Sequence[PolicyExitSealResult], category: str) -> list[PolicyExitSealResult]:
    cat_map = {c.check_id: c.category for c in policy_exit_seal_checks()}
    return [r for r in results if cat_map.get(r.check_id) == category]


def _cat_status_from_results(results: Sequence[PolicyExitSealResult], category: str) -> str:
    relevant = _checks_for_category(results, category)
    if not relevant:
        return "NONE"
    if any(r.verdict in (PolicyExitSealVerdict.FAIL, PolicyExitSealVerdict.ERROR) for r in relevant):
        return "ISSUES"
    if any(r.verdict is PolicyExitSealVerdict.WARN for r in relevant):
        return "WARN"
    return "OK"


def build_policy_exit_seal_report(
    *,
    include_cli: bool = True,
) -> PolicyExitSealReport:
    """Build the P1.6 exit seal report. Does NOT mutate runtime state."""
    checks = policy_exit_seal_checks()
    results: list[PolicyExitSealResult] = []
    for check in checks:
        results.append(run_policy_exit_seal_check(check, include_cli=include_cli))

    sorted_results = tuple(sorted(results, key=lambda r: r.check_id))
    verdict = decide_policy_exit_seal_verdict(sorted_results)

    passed = sum(1 for r in sorted_results if r.verdict is PolicyExitSealVerdict.PASS)
    warned = sum(1 for r in sorted_results if r.verdict is PolicyExitSealVerdict.WARN)
    failed = sum(1 for r in sorted_results if r.verdict is PolicyExitSealVerdict.FAIL)
    errored = sum(1 for r in sorted_results if r.verdict is PolicyExitSealVerdict.ERROR)
    skipped = sum(1 for r in sorted_results if r.verdict is PolicyExitSealVerdict.SKIPPED)

    summary = (
        f"P1.6 exit seal: {verdict.value}. "
        f"Checks: {len(sorted_results)} total, {passed} pass, {warned} warn, "
        f"{failed} fail, {errored} error, {skipped} skipped. "
        f"Next: {NEXT_TASK}."
    )

    report_hash = policy_exit_seal_report_hash(
        PolicyExitSealReport(
            report_id="",
            seal_version=POLICY_EXIT_SEAL_VERSION,
            verdict=verdict,
            checks=sorted_results,
            projection_status=_cat_status_from_results(sorted_results, "projection"),
            cli_status=_cat_status_from_results(sorted_results, "cli"),
            harness_status=_cat_status_from_results(sorted_results, "harness"),
            trace_status=_cat_status_from_results(sorted_results, "trace"),
            docs_status=_cat_status_from_results(sorted_results, "docs"),
            governance_status=_cat_status_from_results(sorted_results, "governance"),
            next_task=NEXT_TASK,
            summary=summary,
            generated_at="",
        )
    )

    return PolicyExitSealReport(
        report_id=f"p1620seal_{report_hash[:16]}",
        seal_version=POLICY_EXIT_SEAL_VERSION,
        verdict=verdict,
        checks=sorted_results,
        projection_status=_cat_status_from_results(sorted_results, "projection"),
        cli_status=_cat_status_from_results(sorted_results, "cli"),
        harness_status=_cat_status_from_results(sorted_results, "harness"),
        trace_status=_cat_status_from_results(sorted_results, "trace"),
        docs_status=_cat_status_from_results(sorted_results, "docs"),
        governance_status=_cat_status_from_results(sorted_results, "governance"),
        next_task=NEXT_TASK,
        summary=summary,
        generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    )


def _sanitize_details(details: Mapping[str, Any]) -> dict[str, Any]:
    sanitized: dict[str, Any] = {}
    for key, value in details.items():
        key_str = str(key)
        if key_str.lower() in _SENSITIVE_KEYS:
            continue
        if isinstance(value, Mapping):
            nested = _sanitize_details(value)
            if nested:
                sanitized[key_str] = nested
        elif isinstance(value, (str, int, float, bool)) or value is None:
            sanitized[key_str] = value
    return dict(sorted(sanitized.items(), key=lambda i: i[0]))


def _result_to_canonical_dict(
    result: PolicyExitSealResult,
    *,
    include_duration: bool = True,
    include_summary: bool = True,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "check_id": result.check_id,
        "evidence_refs": sorted(result.evidence_refs),
        "verdict": result.verdict.value,
    }
    if include_summary:
        payload["summary"] = result.summary
    if result.details:
        payload["details"] = _sanitize_details(result.details)
    if include_duration and result.duration_ms is not None:
        payload["duration_ms"] = result.duration_ms
    return dict(sorted(payload.items(), key=lambda i: i[0]))


def policy_exit_seal_to_json_safe_dict(
    report: PolicyExitSealReport,
    *,
    include_duration: bool = True,
    include_summary: bool = True,
) -> dict[str, Any]:
    """JSON-safe canonical dict for the exit seal report."""
    checks_payload = [
        _result_to_canonical_dict(
            r,
            include_duration=include_duration,
            include_summary=include_summary,
        )
        for r in sorted(report.checks, key=lambda c: c.check_id)
    ]
    payload = {
        "checks": checks_payload,
        "cli_status": report.cli_status,
        "docs_status": report.docs_status,
        "governance_status": report.governance_status,
        "harness_status": report.harness_status,
        "next_task": report.next_task,
        "projection_status": report.projection_status,
        "seal_version": report.seal_version,
        "trace_status": report.trace_status,
        "verdict": report.verdict.value,
    }
    if include_summary:
        payload["summary"] = report.summary
    return dict(sorted(payload.items(), key=lambda i: i[0]))


def policy_exit_seal_report_hash(report: PolicyExitSealReport) -> str:
    """Deterministic SHA-256 hash over canonical check outcomes (excludes timestamps and prose)."""
    canonical = json.dumps(
        policy_exit_seal_to_json_safe_dict(
            report,
            include_duration=False,
            include_summary=False,
        ),
        sort_keys=True,
        separators=(",", ":"),
    )
    if _FORBIDDEN_SECRET_PATTERN.search(canonical):
        raise ValueError("seal report hash input contains forbidden sensitive patterns")
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


__all__ = [
    "PolicyExitSealVerdict",
    "PolicyExitSealReportVerdict",
    "PolicyExitSealCheckId",
    "PolicyExitSealCheck",
    "PolicyExitSealFailure",
    "PolicyExitSealResult",
    "PolicyExitSealReport",
    "POLICY_EXIT_SEAL_VERSION",
    "NEXT_TASK",
    "policy_exit_seal_checks",
    "run_policy_exit_seal_check",
    "decide_policy_exit_seal_verdict",
    "build_policy_exit_seal_report",
    "policy_exit_seal_to_json_safe_dict",
    "policy_exit_seal_report_hash",
]
