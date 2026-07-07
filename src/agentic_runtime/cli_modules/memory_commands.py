"""``agentic-runtime memory`` — read-only Memory Explorer surface (A7).

Projects a run's memory state from its persisted trace (and, optionally, the A3
durable JSONL store for record content). Everything printed is a projection over
the governed trace — a display, never source, granting no write or execution. If
the trace/durable data is missing, the commands say so honestly rather than
fabricate a view.
"""
from __future__ import annotations

import argparse
import json


def _load_projection(args: argparse.Namespace):
    """Build a MemoryProjection from the persisted trace (+ optional durable store).

    Returns ``(projection, error)`` — ``error`` is a human string when the trace
    cannot be read, so callers fail closed instead of fabricating a view."""
    from pathlib import Path

    from ..memory_projection import MemoryProjection
    from ..trace import PersistentTraceLedger

    # Fail closed on a missing run rather than silently showing an empty view.
    # Check BEFORE constructing the ledger — constructing one materializes an
    # empty run dir, which would make a non-existent run look like an empty one.
    events_path = Path(args.trace_dir) / "runs" / args.run_id / "events.jsonl"
    if not events_path.is_file():
        return None, f"no trace found for run={args.run_id!r} under {args.trace_dir!r}"

    try:
        led = PersistentTraceLedger(base_dir=args.trace_dir, run_id=args.run_id)
    except Exception as exc:  # noqa: BLE001 - honest surface of any read failure
        return None, f"cannot open trace run={args.run_id!r} under {args.trace_dir!r}: {exc}"

    backend = None
    durable = getattr(args, "durable", None)
    if durable:
        from ..memory_persistence import FileMemoryBackend
        backend = FileMemoryBackend(durable)
    try:
        proj = MemoryProjection.from_trace(led, backend=backend)
    except Exception as exc:  # noqa: BLE001
        return None, f"cannot project memory from trace: {exc}"
    return proj, None


def _fail(msg: str, as_json: bool) -> int:
    if as_json:
        print(json.dumps({"ok": False, "error": msg}, indent=2, sort_keys=True))
    else:
        print(f"memory: {msg}")
    return 1


def cmd_memory_explore(args: argparse.Namespace) -> int:
    """Current records + graph/edge/rejected counts (projection over trace)."""
    proj, err = _load_projection(args)
    as_json = getattr(args, "json", False)
    if err:
        return _fail(err, as_json)
    report = proj.to_dict()
    if as_json:
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0
    print(f"memory explore  run={args.run_id}  (projection over trace)")
    print(f"current records: {report['current_count']}   edges: {report['edge_count']}"
          f"   rejected: {report['rejected_count']}   "
          f"content_available: {report['content_available']}")
    for rec in proj.records():
        content = rec["content"]
        tail = f"  {content}" if content is not None else ""
        print(f"  [{rec['truth_state'] or '?':<10}] {rec['memory_id']}{tail}")
    return 0


def cmd_memory_history(args: argparse.Namespace) -> int:
    """Belief-history (supersession chain) for one memory id, oldest → newest."""
    proj, err = _load_projection(args)
    as_json = getattr(args, "json", False)
    if err:
        return _fail(err, as_json)
    chain = proj.belief_history(args.memory_id)
    if as_json:
        print(json.dumps({"memory_id": args.memory_id, "chain": chain,
                          "found": bool(chain)}, indent=2, sort_keys=True))
        return 0
    if not chain:
        print(f"memory history  {args.memory_id}: no such memory in the trace")
        return 0
    print(f"memory history  {args.memory_id}  (oldest → newest)")
    print("  " + " → ".join(chain))
    return 0


def cmd_memory_graph(args: argparse.Namespace) -> int:
    """Typed memory edges reconstructed from the trace (A2)."""
    proj, err = _load_projection(args)
    as_json = getattr(args, "json", False)
    if err:
        return _fail(err, as_json)
    edges = proj.edge_tuples()
    if as_json:
        print(json.dumps({"edges": [list(t) for t in edges], "count": len(edges)},
                         indent=2, sort_keys=True))
        return 0
    print(f"memory graph  run={args.run_id}  ({len(edges)} edges)")
    for frm, to, rel in edges:
        print(f"  {frm}  --{rel}-->  {to}")
    return 0


def cmd_memory_rejected(args: argparse.Namespace) -> int:
    """Governance deny rows kept for audit (projection over trace)."""
    proj, err = _load_projection(args)
    as_json = getattr(args, "json", False)
    if err:
        return _fail(err, as_json)
    if as_json:
        print(json.dumps({"rejected": proj.rejected, "count": len(proj.rejected)},
                         indent=2, sort_keys=True))
        return 0
    print(f"memory rejected  run={args.run_id}  ({len(proj.rejected)} denied)")
    for r in proj.rejected:
        print(f"  {r['action']:<8} deny  {r['reason_code']}  (→{r['to']})")
    return 0
