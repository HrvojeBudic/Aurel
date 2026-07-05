"""SPINE-LIVE-5 — spine slice CLI (end-to-end living thread)."""

from __future__ import annotations

import argparse
import json
import os
import tempfile


def cmd_spine_run(args: argparse.Namespace) -> int:
    """Run the end-to-end spine slice and print its aggregate evidence JSON.

    Uses a real hard-isolated sandbox when available; otherwise reports an
    honest UNAVAILABLE result (a valid governed outcome). With ``--live`` (or
    ``AUREL_LIVE=1``) the cognition leg calls DeepSeek instead of the mock
    model; ``--model pro|flash`` selects deepseek-v4-pro / deepseek-v4-flash.
    Read-through: the only writes happen inside the governed, gated runtime.
    """
    from ..spine.harness import build_deepseek_client, run_spine_slice

    trace_dir = args.trace_dir
    if trace_dir is None:
        trace_dir = tempfile.mkdtemp(prefix="spine_trace_")

    live = args.live or os.environ.get("AUREL_LIVE") == "1"
    model_client = build_deepseek_client(args.model) if live else None

    result = run_spine_slice(
        trace_dir=trace_dir, run_id=args.run_id, model_client=model_client
    )
    print(json.dumps(result.to_dict(), sort_keys=True, indent=2 if not args.json else None))
    return 0 if result.spine_live else 1
