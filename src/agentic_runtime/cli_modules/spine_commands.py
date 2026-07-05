"""SPINE-LIVE-5 — spine slice CLI (end-to-end living thread)."""

from __future__ import annotations

import argparse
import json
import tempfile


def cmd_spine_run(args: argparse.Namespace) -> int:
    """Run the end-to-end spine slice and print its aggregate evidence JSON.

    Uses a real hard-isolated sandbox when available; otherwise reports an
    honest UNAVAILABLE result (a valid governed outcome). Read-through: the
    only writes happen inside the governed, isolation-gated runtime.
    """
    from ..spine.harness import run_spine_slice

    trace_dir = args.trace_dir
    if trace_dir is None:
        trace_dir = tempfile.mkdtemp(prefix="spine_trace_")

    result = run_spine_slice(trace_dir=trace_dir, run_id=args.run_id)
    print(json.dumps(result.to_dict(), sort_keys=True, indent=2 if not args.json else None))
    return 0 if result.spine_live else 1
