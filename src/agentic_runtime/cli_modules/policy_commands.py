"""CLI commands for P1.6.18 Policy CLI/TUI Binding. Read-only projection surface."""
from __future__ import annotations

import argparse
import json

from ..policy_cards import (
    PolicyProjectionContract,
    PolicyProjectionSourceLabel,
    PolicyHarnessVerdict,
    build_policy_harness_report,
    build_policy_projection_contract,
    evaluate_policy_harness_case,
    policy_projection_to_json_safe_dict,
    run_policy_harness_suite,
)
from ..policy_cards.test_harness import policy_harness_report_to_canonical_dict
from ..policy_cards.policy_harness_registry import (
    default_policy_harness_suite,
    get_policy_harness_case,
    list_policy_harness_cases,
)


def _build_cli_projection(**kwargs: object) -> PolicyProjectionContract:
    return build_policy_projection_contract(cli_binding_available=True, **kwargs)


def format_policy_status_text(contract: PolicyProjectionContract) -> str:
    lines: list[str] = []
    lines.append(f"Policy Projection Contract: {contract.contract_version}")
    lines.append(f"Projection Hash: sha256:{contract.projection_hash}")
    lines.append(f"Source: {contract.source.value}")
    lines.append("Sections:")
    for section in sorted(contract.sections, key=lambda s: s.section_id):
        status_label = section.status.value
        lines.append(f"  * {section.section_id}: {section.source.value} / {status_label}")
        if section.unavailable_reason is not None:
            lines.append(f"    reason: {section.unavailable_reason.message}")
    lines.append("Readiness:")
    readiness = contract.readiness.to_canonical_dict()
    for key in sorted(readiness.keys()):
        lines.append(f"  * {key}: {str(readiness[key]).lower()}")
    if contract.unavailable_reasons:
        lines.append("Unavailable reasons:")
        for reason in contract.unavailable_reasons:
            lines.append(f"  * {reason.code}: {reason.message}")
    if contract.errors:
        lines.append("Errors:")
        for error in contract.errors:
            lines.append(f"  * {error.code}: {error.message}")
    return "\n".join(lines)


def format_policy_unavailable_text(contract: PolicyProjectionContract) -> str:
    unavailable = [
        section
        for section in contract.sections
        if section.source is PolicyProjectionSourceLabel.UNAVAILABLE
    ]
    if not unavailable:
        return "No unavailable policy projection sections."
    lines: list[str] = []
    for section in sorted(unavailable, key=lambda s: s.section_id):
        reason = (
            section.unavailable_reason.message
            if section.unavailable_reason is not None
            else "unavailable"
        )
        lines.append(f"{section.section_id}: {section.title}")
        lines.append("  source: UNAVAILABLE")
        lines.append(f"  status: {section.status.value}")
        lines.append(f"  reason: {reason}")
    return "\n".join(lines)


def _print_projection_json(contract: PolicyProjectionContract) -> None:
    payload = policy_projection_to_json_safe_dict(contract)
    print(json.dumps(payload, sort_keys=True, separators=(",", ":")))


def cmd_policy_status(args: argparse.Namespace) -> int:
    try:
        contract = _build_cli_projection()
    except Exception as exc:
        print(f"ERROR: projection build failed: {type(exc).__name__}: {exc}")
        return 2
    if args.json:
        _print_projection_json(contract)
    else:
        print(format_policy_status_text(contract))
    return 0


def cmd_policy_projection(args: argparse.Namespace) -> int:
    try:
        contract = _build_cli_projection()
    except Exception as exc:
        if args.json:
            print(json.dumps({
                "error": f"{type(exc).__name__}: {exc}",
                "source": PolicyProjectionSourceLabel.ERROR.value,
            }, sort_keys=True))
        else:
            print(f"ERROR: projection build failed: {type(exc).__name__}: {exc}")
        return 2
    if args.json:
        _print_projection_json(contract)
    else:
        print(format_policy_status_text(contract))
    return 0


def cmd_policy_unavailable(args: argparse.Namespace) -> int:
    try:
        contract = _build_cli_projection()
    except Exception as exc:
        print(f"ERROR: projection build failed: {type(exc).__name__}: {exc}")
        return 2
    text = format_policy_unavailable_text(contract)
    if args.json:
        unavailable = [
            {
                "section_id": section.section_id,
                "title": section.title,
                "source": PolicyProjectionSourceLabel.UNAVAILABLE.value,
                "status": section.status.value,
                "reason": (
                    section.unavailable_reason.message
                    if section.unavailable_reason is not None
                    else ""
                ),
            }
            for section in contract.sections
            if section.source is PolicyProjectionSourceLabel.UNAVAILABLE
        ]
        print(json.dumps({"unavailable_sections": unavailable}, sort_keys=True))
    else:
        print(text)
    return 0


def cmd_policy_harness_list(args: argparse.Namespace) -> int:
    cases = list_policy_harness_cases()
    if args.json:
        rows = [
            {
                "case_id": case.case_id,
                "title": case.title,
                "source": PolicyProjectionSourceLabel.LIVE.value,
            }
            for case in cases
        ]
        print(json.dumps(rows, sort_keys=True))
    else:
        print(f"Policy Harness Cases: {len(cases)}")
        for case in cases:
            print(f"  {case.case_id}: {case.title} [LIVE]")
    return 0


def _format_harness_report_text(report: object) -> str:
    from ..policy_cards.test_harness import PolicyHarnessReport
    if not isinstance(report, PolicyHarnessReport):
        raise TypeError("report must be a PolicyHarnessReport")
    lines = [
        f"suite_id: {report.suite_id}",
        f"case_count: {report.case_count}",
        f"passed: {report.passed}",
        f"failed: {report.failed}",
        f"warned: {report.warned}",
        f"errored: {report.errored}",
        f"skipped: {report.skipped}",
        f"report_hash: {report.report_hash}",
        f"shadow_only_status: {report.shadow_only_status}",
        "enforced: false",
    ]
    return "\n".join(lines)


def _harness_exit_code(report: object) -> int:
    from ..policy_cards.test_harness import PolicyHarnessReport
    if not isinstance(report, PolicyHarnessReport):
        raise TypeError("report must be a PolicyHarnessReport")
    if report.failed > 0:
        return 1
    return 0


def cmd_policy_harness_run(args: argparse.Namespace) -> int:
    case_id = getattr(args, "case", None) or ""
    if case_id:
        case = get_policy_harness_case(case_id)
        if case is None:
            message = f"Unknown case_id: {case_id}"
            if args.json:
                print(json.dumps({
                    "error": message,
                    "source": PolicyProjectionSourceLabel.UNAVAILABLE.value,
                }, sort_keys=True))
            else:
                print(message)
            return 4
        result = evaluate_policy_harness_case(case)
        if args.json:
            print(json.dumps({
                "case_id": result.case_id,
                "verdict": result.verdict.value,
                "canonical_hash": result.canonical_hash,
                "shadow_only": result.actual.shadow_only,
                "enforced": False,
            }, sort_keys=True))
        else:
            print(f"case_id: {result.case_id}")
            print(f"verdict: {result.verdict.value}")
            print(f"canonical_hash: {result.canonical_hash}")
            print(f"shadow_only: {result.actual.shadow_only}")
            print("enforced: false")
        if result.verdict is PolicyHarnessVerdict.FAIL:
            return 1
        return 0

    suite = default_policy_harness_suite()
    run = run_policy_harness_suite(suite)
    report = build_policy_harness_report(run)
    if args.json:
        payload = policy_harness_report_to_canonical_dict(report, include_hash=True)
        payload["enforced"] = False
        print(json.dumps(payload, sort_keys=True))
    else:
        print(_format_harness_report_text(report))
    return _harness_exit_code(report)
