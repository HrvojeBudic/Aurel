"""``agentic-runtime reasoning`` — read-only reasoning scheduler surface (B6).

Shows the scheduler configuration and a workload projection folded from a run's
reasoning trace events. Everything printed is a DSD-01I projection — a display of
the trace, never source, and it grants no allocation or execution.
"""
from __future__ import annotations

import argparse
import json


def cmd_reasoning_status(args: argparse.Namespace) -> int:
    """Show the reasoning scheduler flag + the effort / difficulty vocabularies."""
    from ..reasoning.difficulty_estimator import DifficultyBand
    from ..reasoning.reasoning_scheduler import enabled
    from ..reasoning.step_verifier import model_judge_available
    from ..reasoning.thinking_budget import EffortLevel

    report = {
        "flag": "AUREL_REASONING_SCHEDULER",
        "enabled": enabled(),
        "effort_levels": [e.value for e in EffortLevel],
        "difficulty_bands": [d.value for d in DifficultyBand],
        "model_judge_available": model_judge_available(),
    }
    if getattr(args, "json", False):
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0
    print(f"reasoning scheduler  {report['flag']}={report['enabled']}")
    print(f"effort:      {' < '.join(report['effort_levels'])}")
    print(f"difficulty:  {' < '.join(report['difficulty_bands'])}")
    print(f"model_judge_available: {report['model_judge_available']} (PRM is advisory)")
    return 0


def cmd_reasoning_workload(args: argparse.Namespace) -> int:
    """Project a run's reasoning workload from its persisted trace (read-only)."""
    from ..reasoning.workload_projection import WorkloadView
    from ..trace import PersistentTraceLedger

    led = PersistentTraceLedger(base_dir=args.trace_dir, run_id=args.run_id)
    view = WorkloadView.from_records(led.replay())
    if getattr(args, "json", False):
        print(json.dumps(view.to_dict(), indent=2, sort_keys=True))
        return 0
    d = view.to_dict()
    print(f"reasoning workload  run={args.run_id}  (projection over trace)")
    print(f"allocations: {d['allocations']}   escalations: {d['escalations']}"
          f"   replan_attempts: {d['total_replan_attempts']}")
    print(f"effort:     {d['effort_histogram']}")
    print(f"difficulty: {d['difficulty_histogram']}")
    print(f"profile:    {d['profile_histogram']}")
    return 0
