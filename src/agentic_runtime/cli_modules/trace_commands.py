"""Read-only AurelTrace CLI commands (P5-TRACE-D resolver/query binding).

These commands display TRACE_VERIFIED resolver decisions over a DEV_FIXTURE demo
trace substrate. They are strictly read-only: no runtime submit, no trace append,
no repair, no replay, no approval, no policy enforcement, no memory write, no
mutating subcommands. Output is resolver-backed — a target is reported
TRACE_VERIFIED only when the resolver returns that status.
"""

from __future__ import annotations

import argparse
import json

from ..aurel_trace.trace_demo import build_demo_trace_substrate
from ..aurel_trace.trace_query import TraceQueryReadModel


def _read_model() -> TraceQueryReadModel:
    substrate = build_demo_trace_substrate()
    return TraceQueryReadModel(
        read_model_id="trace-cli-demo.p5-trace-d.v1",
        decisions=substrate.decisions,
    )


def _emit(payload: dict, as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return
    for line in _render_lines(payload):
        print(line)


def _render_lines(payload: dict) -> list[str]:
    lines = ["AurelTrace verification status (DEV_FIXTURE, resolver-backed):"]
    for decision in payload.get("decisions", []):
        lines.append(
            f"  [{decision['status']}] {decision['target_kind']} "
            f"{decision['target_id']} — {decision['reason']}"
        )
        if decision.get("missing_evidence"):
            lines.append(
                "      missing evidence: " + ", ".join(decision["missing_evidence"])
            )
        if decision.get("blocking_findings"):
            lines.append(
                "      blocking findings: " + ", ".join(decision["blocking_findings"])
            )
    if "audit" in payload:
        audit = payload["audit"]
        lines.append(
            f"  audit: {audit['verified_count']} verified / "
            f"{audit['targets_checked']} checked "
            f"(bound={audit['trace_bound_count']} partial={audit['partial_count']} "
            f"denied={audit['denied_count']} error={audit['error_count']})"
        )
    return lines


def cmd_trace_status(args: argparse.Namespace) -> int:
    model = _read_model()
    payload = {
        "read_model_id": model.read_model_id,
        "decisions": [d.to_dict() for d in model.decisions],
        "audit": model.summarize_audit().to_dict(),
        "dev_fixture": True,
    }
    _emit(payload, getattr(args, "json", False))
    return 0


def cmd_trace_verify(args: argparse.Namespace) -> int:
    model = _read_model()
    summaries = [model.summarize_verification(d).to_dict() for d in model.decisions]
    payload = {
        "read_model_id": model.read_model_id,
        "verifications": summaries,
        "dev_fixture": True,
    }
    if getattr(args, "json", False):
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print("AurelTrace verification (DEV_FIXTURE, resolver-backed):")
        for summary in summaries:
            verified = "VERIFIED" if summary["verified"] else "not verified"
            print(
                f"  [{summary['verification_status']}] {summary['target_id']} "
                f"({verified}) — {summary['reason']}"
            )
    return 0


def cmd_trace_anchor_verify(args: argparse.Namespace) -> int:
    """Verify a persisted run against its external anchor (M2).

    Read-only: re-verifies the on-disk chain and, when an anchor exists for the
    run outside the agent's write domain, confirms the anchored merkle root
    still matches — catching a full re-forge that internal verification alone
    would miss.
    """
    from ..trace import PersistentTraceLedger

    led = PersistentTraceLedger(
        base_dir=args.trace_dir, run_id=args.run_id, checkpoint_every=args.checkpoint_every
    )
    report = led.verify_persisted()
    if getattr(args, "json", False):
        print(json.dumps(report, indent=2, sort_keys=True, default=str))
    else:
        status = "OK" if report["ok"] else "FAIL"
        anchored = report.get("anchored")
        print(f"trace anchor-verify [{status}] run={args.run_id}")
        print(f"  events: {report.get('event_count')}")
        print(f"  anchored: {anchored}")
        if not report["ok"]:
            print(f"  reason: {report.get('reason')}")
        elif not anchored:
            print("  note: no external anchor recorded for this run "
                  "(internal chain verified only)")
    return 0 if report["ok"] else 1


def cmd_trace_inspect(args: argparse.Namespace) -> int:
    target = getattr(args, "target", None)
    model = _read_model()
    if not target:
        print(
            json.dumps(
                {
                    "error": "trace inspect requires --target <id>",
                    "available_targets": [d.target_id for d in model.decisions],
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 2
    match = next((d for d in model.decisions if d.target_id == target), None)
    if match is None:
        print(
            json.dumps(
                {
                    "target": target,
                    "status": "UNAVAILABLE",
                    "reason": "no resolver decision for this target in the demo substrate",
                    "available_targets": [d.target_id for d in model.decisions],
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 0
    print(json.dumps(match.to_dict(), indent=2, sort_keys=True))
    return 0


def cmd_trace_audit(args: argparse.Namespace) -> int:
    model = _read_model()
    audit = model.summarize_audit().to_dict()
    if getattr(args, "json", False):
        print(json.dumps(audit, indent=2, sort_keys=True))
    else:
        print(
            f"AurelTrace audit (DEV_FIXTURE): {audit['verified_count']} verified / "
            f"{audit['targets_checked']} checked; bound={audit['trace_bound_count']} "
            f"partial={audit['partial_count']} denied={audit['denied_count']} "
            f"error={audit['error_count']}"
        )
    return 0
