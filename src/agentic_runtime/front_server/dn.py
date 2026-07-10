"""
dn.py — surface the DN (dual-kernel) mechanisms through AurelEU (F6.6).

This slice is mostly *wiring*: the σ-governor (graduated autonomy) and the
merge-gate (weighted readiness verdict with an **absolute verifier veto**) already
live in `dual_kernel/`. F6.6 exposes them read-only through AurelEU / HQ.Command so
the operator can see how autonomy is graduated and how a merge verdict is reached.
Nothing here changes the default path; when `AUREL_DUAL_KERNEL` is OFF the mechanisms
are declared UNAVAILABLE, never faked.
"""
from __future__ import annotations

import os
from typing import Any

from ..dual_kernel import routing
from ..dual_kernel.merge_gate import MergeGate

_DK_FLAG = "AUREL_DUAL_KERNEL"

# The verifier veto is absolute: a failed state verification can never merge, no
# matter what other (weighted) signals say. Declared here as a hard-wired claim.
CLAIMS_VERIFIER_VETO_ABSOLUTE = True


def dual_kernel_enabled() -> bool:
    return os.environ.get(_DK_FLAG, "").strip() in ("1", "true", "TRUE", "on")


def graduated_autonomy(card: Any) -> int:
    """The σ graduated-autonomy index (0–10; higher = less freedom without governance)."""
    return routing.autonomy_index(card)


def evaluate_merge(ctx: Any) -> dict:
    """The weighted merge verdict via `MergeGate`. The verifier veto is absolute:
    a failed `verifier_result` is always a blocker and can never be mergeable."""
    decision = MergeGate().evaluate(ctx)
    return {
        "verdict": decision.final_status.value,
        "mergeable": decision.mergeable,
        "verifier_vetoed": not ctx.verifier_result.passed,
        "blockers": list(decision.blockers),
    }


class DnStatusReadModel:
    """Read-only DN status for `GET /read/aureleu/dn`. Honest about availability."""

    @staticmethod
    def status() -> dict:
        live = dual_kernel_enabled()
        return {
            "dual_kernel_enabled": live,
            "graduated_autonomy": (
                "live via SigmaGovernor" if live
                else "UNAVAILABLE (AUREL_DUAL_KERNEL off)"),
            "weighted_merge_verdict": (
                "live via MergeGate" if live
                else "UNAVAILABLE (AUREL_DUAL_KERNEL off)"),
            "verifier_veto": "absolute",
            "claims_verifier_veto_absolute": CLAIMS_VERIFIER_VETO_ABSOLUTE,
        }
