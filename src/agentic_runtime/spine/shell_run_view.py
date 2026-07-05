"""SPINE-LIVE-4 — Shell live run view.

The P2 Shell surface has always reported binding as ``UNAVAILABLE`` because no
live data path existed. This module supplies the first real one: a read-only
view built from the S3 persisted trace on disk. When a run exists, the operator
sees LIVE transitions and a recomputed ``trace_verified`` verdict; when none
exists, the view is honestly ``UNAVAILABLE``.

    shell_binding_live = bool(persisted_trace_ref)

A view reads and renders; it dispatches nothing, mutates nothing, and grants no
authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .trace_verify import (
    TraceVerifiedLabel,
    replay_persisted_trace,
    verify_persisted_trace,
)

SHELL_RUN_VIEW_VERSION = "shell_run_view.v1"

TRUTH_LABEL_LIVE = "LIVE"
TRUTH_LABEL_UNAVAILABLE = "UNAVAILABLE"


@dataclass(frozen=True)
class ShellRunView:
    """Read-only operator view of one persisted spine run. Not control."""

    contract_version: str
    run_id: str
    trace_dir: str
    shell_binding_live: bool
    truth_label: str
    trace_verified: bool
    event_count: int
    head_hash: str
    transitions: tuple[dict, ...]
    unavailable_reason: str

    def to_dict(self) -> dict:
        return {
            "contract_version": self.contract_version,
            "run_id": self.run_id,
            "trace_dir": self.trace_dir,
            "shell_binding_live": self.shell_binding_live,
            "truth_label": self.truth_label,
            "trace_verified": self.trace_verified,
            "event_count": self.event_count,
            "head_hash": self.head_hash,
            "transitions": list(self.transitions),
            "unavailable_reason": self.unavailable_reason,
        }


def build_shell_run_view(base_dir: str | Path, run_id: str) -> ShellRunView:
    """Build a live run view from the persisted trace, honest when absent."""
    verified = verify_persisted_trace(base_dir, run_id)
    if verified.label is TraceVerifiedLabel.UNAVAILABLE:
        return ShellRunView(
            contract_version=SHELL_RUN_VIEW_VERSION,
            run_id=run_id,
            trace_dir=str(base_dir),
            shell_binding_live=False,
            truth_label=TRUTH_LABEL_UNAVAILABLE,
            trace_verified=False,
            event_count=0,
            head_hash="",
            transitions=(),
            unavailable_reason=verified.reason,
        )
    transitions = tuple(replay_persisted_trace(base_dir, run_id))
    return ShellRunView(
        contract_version=SHELL_RUN_VIEW_VERSION,
        run_id=run_id,
        trace_dir=str(base_dir),
        shell_binding_live=True,
        truth_label=TRUTH_LABEL_LIVE,
        trace_verified=verified.trace_verified,
        event_count=verified.event_count,
        head_hash=verified.persisted_head_hash,
        transitions=transitions,
        unavailable_reason="",
    )


def format_shell_run_view_text(view: ShellRunView) -> str:
    """Deterministic human-readable render of a run view."""
    if not view.shell_binding_live:
        return (
            f"run-view {view.run_id}: UNAVAILABLE — {view.unavailable_reason}"
        )
    lines = [
        f"run-view {view.run_id}  [{view.truth_label}]",
        f"  trace_verified: {view.trace_verified}",
        f"  events: {view.event_count}   head: {view.head_hash[:16]}",
        "  transitions:",
    ]
    for row in view.transitions:
        lines.append(
            f"    [{row.get('sequence')}] {row.get('event_type')} "
            f"{str(row.get('entry_hash') or '')[:12]}"
        )
    return "\n".join(lines)


__all__ = [
    "SHELL_RUN_VIEW_VERSION",
    "ShellRunView",
    "build_shell_run_view",
    "format_shell_run_view_text",
]
