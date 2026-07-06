"""``agentic-runtime dual-kernel`` — inspect the dual-kernel governance surface.

Read-only operator surface over the dual kernel: routing configuration, the
canon firewall (NC-law ⇄ gate bindings), and the tamper-evident decision ledger.
Everything printed is a DSD-01I projection — a display of the source ledger, not
the source itself.
"""
from __future__ import annotations

import argparse
import json


def cmd_dual_kernel_status(args: argparse.Namespace) -> int:
    """Show whether the dual kernel is enabled and that every gate is canon-bound."""
    from ..dual_kernel import load_bindings, validate_coverage
    from ..dual_kernel.kernel import _flag_enabled
    from ..dual_kernel.merge_gate import GATE_IDS

    try:
        validate_coverage(GATE_IDS)
        coverage = "ok"
    except AssertionError as e:
        coverage = f"BREACH: {e}"

    report = {
        "flag": "AUREL_DUAL_KERNEL",
        "enabled": _flag_enabled(),
        "merge_gates": len(GATE_IDS),
        "nc_bindings": len(load_bindings()),
        "canon_coverage": coverage,
        "routes": ["fast", "governed", "hard"],
    }
    if getattr(args, "json", False):
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0
    print(f"dual kernel  flag={report['flag']}={report['enabled']}")
    print(f"merge gates: {report['merge_gates']}   nc bindings: {report['nc_bindings']}"
          f"   coverage: {report['canon_coverage']}")
    print(f"routes: {' | '.join(report['routes'])}")
    return 0 if coverage == "ok" else 1


def cmd_dual_kernel_bindings(args: argparse.Namespace) -> int:
    """Print the canon firewall: each merge-gate check → the NC-law it protects."""
    from ..dual_kernel import load_bindings

    bindings = load_bindings()
    if getattr(args, "json", False):
        print(json.dumps(
            {gid: b.__dict__ for gid, b in bindings.items()},
            indent=2, sort_keys=True))
        return 0
    print(f"{'gate':30} {'nc_law':16} {'verdict_on_fail':20} statement")
    for gid, b in bindings.items():
        print(f"{gid:30} {b.nc_law:16} {b.verdict_on_fail:20} {b.statement}")
    return 0


def cmd_dual_kernel_verify_ledger(args: argparse.Namespace) -> int:
    """Verify the hash-chain of a persisted dual-kernel decision ledger."""
    from ..dual_kernel import DualKernelLedger

    led = DualKernelLedger.load(args.path)
    report = led.verify()
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report.get("ok") else 1


def cmd_dual_kernel_show(args: argparse.Namespace) -> int:
    """Print the 01I read-model projection of a decision ledger (display only)."""
    from ..dual_kernel import DualKernelLedger

    led = DualKernelLedger.load(args.path)
    proj = led.projection()
    if getattr(args, "json", False):
        print(json.dumps(proj, indent=2, sort_keys=True))
        return 0
    print(f"{'seq':4} {'route':9} {'final_status':18} {'exec':5} nc_laws")
    for row in proj:
        print(f"{row['seq']:<4} {row['route']:9} {row['final_status']:18} "
              f"{str(row['executed']):5} {','.join(row['nc_laws'])}")
    return 0
