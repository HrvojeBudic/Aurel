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

    kwargs = {}
    if getattr(args, "goal", None):
        kwargs["goal"] = args.goal
    result = run_spine_slice(
        trace_dir=trace_dir,
        run_id=args.run_id,
        model_client=model_client,
        plan_driven=bool(getattr(args, "plan_driven", False)),
        **kwargs,
    )
    print(json.dumps(result.to_dict(), sort_keys=True, indent=2 if not args.json else None))
    return 0 if result.spine_live else 1


def cmd_spine_replay(args: argparse.Namespace) -> int:
    """Record a run's model I/O then replay it from the cassette — no network.

    Determinism is reported at the governed-mutation world-state level: every
    write node must reproduce the same ``after_state_hash`` and every node the
    same outcome, driving the model from the cassette alone. Uses a real hard
    sandbox when available, else an honest UNAVAILABLE.
    """
    import tempfile

    from ..spine.harness import _auto_hard_sandbox, replay_spine_run

    trace_dir = args.trace_dir or tempfile.mkdtemp(prefix="spine_replay_")

    def _factory():
        sbx = _auto_hard_sandbox()
        if sbx is None:
            from ..sandbox import UnsafeLocalSandbox

            # honest: unsafe local can still demonstrate replay determinism of
            # mutations, but it is not a security boundary.
            sbx = UnsafeLocalSandbox()
        return sbx

    kwargs = {"plan_driven": bool(getattr(args, "plan_driven", False))}
    if getattr(args, "goal", None):
        kwargs["goal"] = args.goal
    report = replay_spine_run(trace_dir=trace_dir, sandbox_factory=_factory, **kwargs)
    print(json.dumps(report, indent=2, sort_keys=True, default=str))
    return 0 if report["deterministic"] else 1


def cmd_spine_serve(args: argparse.Namespace) -> int:
    """Launch the local SPINE-LIVE web console (blocking)."""
    from ..spine.webui import serve_spine_ui

    serve_spine_ui(host=args.host, port=args.port)
    return 0
