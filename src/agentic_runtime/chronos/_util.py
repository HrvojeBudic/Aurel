"""Shared Chronos helpers — read-only trace/event access."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from ..trace import _load_jsonl


def load_run_events(trace_dir: str, run_id: str) -> list[dict[str, Any]]:
    path = Path(trace_dir) / "runs" / run_id / "events.jsonl"
    if not path.exists():
        return []
    return _load_jsonl(path)


def state_transitions(trace_dir: str, run_id: str) -> list[dict[str, Any]]:
    return [
        ev
        for ev in load_run_events(trace_dir, run_id)
        if ev.get("event_type") == "state_transition"
    ]
