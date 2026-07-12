"""F8.0 — Chronos diff: deterministic causal graph comparison (read-only)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ._util import state_transitions


@dataclass(frozen=True)
class DiffResult:
    run_a: str
    run_b: str
    added: tuple[str, ...]
    removed: tuple[str, ...]
    changed: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_a": self.run_a,
            "run_b": self.run_b,
            "added": list(self.added),
            "removed": list(self.removed),
            "changed": list(self.changed),
        }


def _transition_signature(event: dict[str, Any]) -> str:
    payload = event.get("payload") or {}
    return "|".join(
        [
            str(event.get("entry_hash", "")),
            str(payload.get("command_hash", "")),
            str(payload.get("after_state_hash", "")),
            str(payload.get("verdict", "")),
        ]
    )


class ChronosDiff:
    """Compare two runs via causal graph node signatures."""

    @classmethod
    def compare(cls, trace_dir: str, run_a: str, run_b: str) -> DiffResult:
        trans_a = state_transitions(trace_dir, run_a)
        trans_b = state_transitions(trace_dir, run_b)
        sig_a = {_transition_signature(ev) for ev in trans_a}
        sig_b = {_transition_signature(ev) for ev in trans_b}
        added = tuple(sorted(sig_b - sig_a))
        removed = tuple(sorted(sig_a - sig_b))
        changed_list: list[str] = []
        for index in range(min(len(trans_a), len(trans_b))):
            sa = _transition_signature(trans_a[index])
            sb = _transition_signature(trans_b[index])
            if sa != sb and sa not in added and sb not in removed:
                changed_list.append(f"index:{index}")
        return DiffResult(
            run_a=run_a,
            run_b=run_b,
            added=added,
            removed=removed,
            changed=tuple(changed_list),
        )
