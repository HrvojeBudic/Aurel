"""``aurel chronos`` — F8 Time Plane read-only forensic surface."""
from __future__ import annotations

import argparse
import json
import sys


def _unavailable_json(reason: str) -> None:
    print(json.dumps({"available": False, "reason": reason}, indent=2))


def _require_chronos(args: argparse.Namespace) -> bool:
    from ..chronos import flag_enabled

    if flag_enabled():
        return True
    reason = "Chronos unavailable — set AUREL_CHRONOS=1 to enable read-only replay/fork/diff"
    if getattr(args, "json", False):
        _unavailable_json(reason)
    else:
        print(reason, file=sys.stderr)
    return False


def _default_trace_dir() -> str:
    from .. import build_runtime

    rt = build_runtime()
    trace = rt.runtime.trace
    base = getattr(trace, "base_dir", None)
    if base is not None:
        return str(base)
    return ".traces"


def cmd_chronos_replay(args: argparse.Namespace) -> int:
    if not _require_chronos(args):
        return 1
    from ..chronos import ChronosReplay

    trace_dir = getattr(args, "trace_dir", "") or _default_trace_dir()
    result = ChronosReplay.from_run(trace_dir, args.run_id)
    if getattr(args, "json", False):
        print(json.dumps(result.to_dict(), indent=2))
    else:
        print(
            f"Chronos replay {result.run_id}: "
            f"replayable={result.replayable} checked={result.checked_count} "
            f"reason={result.reason}"
        )
        if result.mismatch_at is not None:
            print(f"  mismatch_at={result.mismatch_at}")
    return 0 if result.replayable else 1


def cmd_chronos_fork(args: argparse.Namespace) -> int:
    if not _require_chronos(args):
        return 1
    from ..chronos import ChronosFork
    from ..worldline import ForkError

    trace_dir = getattr(args, "trace_dir", "") or _default_trace_dir()
    try:
        result = ChronosFork.fork_at(trace_dir, args.run_id, int(args.at))
    except ForkError as exc:
        if getattr(args, "json", False):
            print(json.dumps({"ok": False, "error": str(exc)}, indent=2))
        else:
            print(f"fork failed: {exc}", file=sys.stderr)
        return 1
    if getattr(args, "json", False):
        print(json.dumps(result.to_dict(), indent=2))
    else:
        print(
            f"forked {result.parent_run_id}@{result.transition_index} → "
            f"child_run_id={result.child_run_id} fork_id={result.fork_id}"
        )
    return 0


def cmd_chronos_diff(args: argparse.Namespace) -> int:
    if not _require_chronos(args):
        return 1
    from ..chronos import ChronosDiff

    trace_dir = getattr(args, "trace_dir", "") or _default_trace_dir()
    result = ChronosDiff.compare(trace_dir, args.run_a, args.run_b)
    if getattr(args, "json", False):
        print(json.dumps(result.to_dict(), indent=2))
    else:
        print(f"Chronos diff {result.run_a} vs {result.run_b}:")
        print(f"  added={len(result.added)} removed={len(result.removed)} "
              f"changed={len(result.changed)}")
    return 0
