"""``agentic-runtime doctor`` — host capability diagnostics (M0).

Runs the *functional* isolation probes plus a ledger write+verify roundtrip,
then reports which governance levels (G0-G5) are physically achievable on this
host. Nothing here claims a capability it did not just exercise.
"""

from __future__ import annotations

import argparse
import json
import tempfile
from typing import Any


def _probe_sandboxes() -> list[dict[str, Any]]:
    from ..sandbox import SandboxMode, probe_backend

    return [
        probe_backend(SandboxMode.BUBBLEWRAP),
        probe_backend(SandboxMode.DOCKER),
        probe_backend(SandboxMode.UNSAFE_LOCAL),
    ]


def _probe_subprocess() -> dict[str, Any]:
    """Nested subprocess timeout enforcement (governed exec depends on it)."""
    import sys

    from ..sandbox import UnsafeLocalSandbox

    try:
        with tempfile.TemporaryDirectory() as td:
            sbx = UnsafeLocalSandbox(root=td)
            res = sbx.run_shell(
                [sys.executable, "-c", "import time; time.sleep(2)"], timeout=0.5
            )
            ok = bool(res.timed_out) and res.error_kind != "sandbox_error"
            return {"check": "subprocess_timeout", "ok": ok,
                    "reason": "" if ok else (res.stderr or "timeout not enforced")}
    except OSError as e:
        return {"check": "subprocess_timeout", "ok": False, "reason": str(e)}


def _probe_ledger() -> dict[str, Any]:
    """Persistent ledger write + verify roundtrip."""
    from ..core_types import PlanningFailureRecord
    from ..trace import PersistentTraceLedger

    try:
        with tempfile.TemporaryDirectory() as td:
            led = PersistentTraceLedger(base_dir=td, run_id="doctor", checkpoint_every=2)
            for i in range(4):
                led.append_planning_failure(
                    PlanningFailureRecord.make(f"i{i}", "doctor", "rejected", "probe")
                )
            led.seal_run("completed")
            rep = led.verify_persisted()
            return {"check": "ledger_roundtrip", "ok": bool(rep.get("ok")),
                    "reason": rep.get("reason", "")}
    except Exception as e:  # noqa: BLE001 - diagnostic must never raise
        return {"check": "ledger_roundtrip", "ok": False, "reason": repr(e)}


def _probe_anchor() -> dict[str, Any]:
    """Anchor sink reachability (present after M2; degrade gracefully if absent)."""
    try:
        from ..trace_anchor import default_anchor_sink

        sink = default_anchor_sink()
        ok = sink.reachable()
        return {"check": "anchor_reachable", "ok": ok,
                "reason": "" if ok else "anchor sink not reachable"}
    except ImportError:
        return {"check": "anchor_reachable", "ok": False,
                "reason": "anchor sink not implemented yet (M2 pending)"}
    except Exception as e:  # noqa: BLE001
        return {"check": "anchor_reachable", "ok": False, "reason": repr(e)}


def _achievable_levels(sandboxes: list[dict[str, Any]], anchor_ok: bool) -> dict[str, Any]:
    """Which G-levels are physically possible given probed capabilities."""
    hard_ok = any(s["available"] and s["hard_isolated"] for s in sandboxes)
    levels = {}
    # G0-G3 need a functional hard sandbox; G4 is the ceiling until an anchor
    # exists; G5 (HERETIC) additionally requires the anchored trace floor.
    for lvl in ("G0", "G1", "G2", "G3"):
        levels[lvl] = {"achievable": hard_ok,
                       "blocker": "" if hard_ok else "no functional hard sandbox"}
    levels["G4"] = {"achievable": hard_ok,
                    "blocker": "" if hard_ok else "no functional hard sandbox"}
    g5_ok = hard_ok and anchor_ok
    levels["G5"] = {"achievable": g5_ok,
                    "blocker": "" if g5_ok else
                    ("no functional hard sandbox" if not hard_ok
                     else "no anchored trace (G5 HERETIC floor)")}
    return levels


def run_doctor(no_cache: bool = False) -> dict[str, Any]:
    if no_cache:
        from ..sandbox import clear_probe_cache

        clear_probe_cache()
    sandboxes = _probe_sandboxes()
    subprocess_check = _probe_subprocess()
    ledger_check = _probe_ledger()
    anchor_check = _probe_anchor()
    levels = _achievable_levels(sandboxes, anchor_check["ok"])
    all_green = (
        any(s["available"] and s["hard_isolated"] for s in sandboxes)
        and subprocess_check["ok"]
        and ledger_check["ok"]
    )
    return {
        "sandboxes": sandboxes,
        "checks": [subprocess_check, ledger_check, anchor_check],
        "governance_levels": levels,
        "hard_isolation_available": any(
            s["available"] and s["hard_isolated"] for s in sandboxes
        ),
        "healthy": all_green,
    }


def _fmt(report: dict[str, Any]) -> str:
    lines = ["Aurel doctor — host capability report", ""]
    lines.append("Sandbox backends (functional probes):")
    for s in report["sandboxes"]:
        mark = "ok  " if s["available"] and s.get("hard_isolated") else (
            "soft" if s["available"] else "FAIL")
        lines.append(f"  [{mark}] {s['backend']:12s} {s['reason']}")
    lines.append("")
    lines.append("Checks:")
    for c in report["checks"]:
        lines.append(f"  [{'ok' if c['ok'] else 'FAIL'}] {c['check']}: {c['reason'] or 'ok'}")
    lines.append("")
    lines.append("Governance levels achievable on this host:")
    for lvl, info in report["governance_levels"].items():
        mark = "ok  " if info["achievable"] else "no  "
        lines.append(f"  [{mark}] {lvl}{('  — ' + info['blocker']) if info['blocker'] else ''}")
    lines.append("")
    lines.append(f"Overall: {'HEALTHY' if report['healthy'] else 'DEGRADED'}")
    return "\n".join(lines)


def cmd_doctor(args: argparse.Namespace) -> int:
    report = run_doctor(no_cache=bool(getattr(args, "no_cache", False)))
    if getattr(args, "json", False):
        print(json.dumps(report, indent=2, sort_keys=True, default=str))
    else:
        print(_fmt(report))
    return 0 if report["healthy"] else 1
