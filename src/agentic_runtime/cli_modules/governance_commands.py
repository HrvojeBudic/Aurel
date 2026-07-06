"""``agentic-runtime governance`` — the G0–G5 scale surface (M6)."""

from __future__ import annotations

import argparse
import json


def cmd_governance_levels(args: argparse.Namespace) -> int:
    """Print the governance spectrum G0–G5 and each level's gate state."""
    from ..governance.profile import GovernanceLevel, profile_for

    rows = [profile_for(lvl).to_dict() for lvl in GovernanceLevel]
    if getattr(args, "json", False):
        print(json.dumps(rows, indent=2, sort_keys=True))
        return 0
    print("Governance scale  ABSOLUTE GOVERNED (G0) ⟷ HERETIC (G5)")
    print(f"{'lvl':4} {'auto≤':6} {'cap':5} {'enforce':22} {'sbx':4} {'anchor':7} trace")
    for r in rows:
        print(f"{r['level']:4} {r['auto_approve_max']:6} {r['reversibility_cap']:5} "
              f"{r['enforcement_mode']:22} {str(r['sandbox_required']):4} "
              f"{str(r['anchor_required']):7} {r['trace_required']}")
    print("\nFloor (all levels incl. HERETIC): anchored trace on; no self-escalation.")
    return 0


def cmd_governance_audit(args: argparse.Namespace) -> int:
    """Audit a persisted run for drift above its declared governance level."""
    from ..governance import GovernanceLevel, audit_governance
    from ..trace import PersistentTraceLedger

    led = PersistentTraceLedger(
        base_dir=args.trace_dir, run_id=args.run_id, checkpoint_every=args.checkpoint_every
    )
    events = list(led.replay())
    declared = GovernanceLevel(args.declared)
    report = audit_governance(declared, events)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 1 if report["drift_detected"] else 0
