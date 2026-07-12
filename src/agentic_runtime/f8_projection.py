"""
f8_projection.py — the F8.6 north-star run projection (Time Plane §7).

A single read-only view composing Chronos replay, System forensics read-models,
Library time-travel availability, and succession-drill capability for one
persisted run. Zero writes — every field is a pure projection.
"""
from __future__ import annotations

from typing import Any, Optional

from .front_server.library import claims_library_time_travel
from .front_server.system_read_model import SystemReadModel, flag_enabled as system_flag_enabled


class F8RunProjection:
    """Time Plane north-star: run → replay → System forensics + Library as-of seam."""

    def __init__(
        self,
        runtime: Any,
        *,
        run_id: Optional[str] = None,
        trace_dir: Optional[str] = None,
        sandbox_factory: Any = None,
    ) -> None:
        self._inner = getattr(runtime, "runtime", runtime)
        self._run_id = run_id or getattr(self._inner.trace, "run_id", None)
        self._trace_dir = trace_dir or getattr(self._inner.trace, "base_dir", None)
        self._sandbox_factory = sandbox_factory

    def _chronos_replay(self) -> dict:
        if not self._run_id or not self._trace_dir:
            return {
                "available": False,
                "replayable": False,
                "reason": "no persisted run_id or trace_dir",
            }
        from .chronos import ChronosReplay, flag_enabled as chronos_flag

        if not chronos_flag():
            return {
                "available": False,
                "replayable": False,
                "reason": "AUREL_CHRONOS off",
            }
        result = ChronosReplay.from_run(
            str(self._trace_dir),
            self._run_id,
            sandbox_factory=self._sandbox_factory,
        )
        body = result.to_dict()
        body["available"] = True
        return body

    def _fork_gate_events(self) -> list[dict]:
        trace = self._inner.trace
        if not hasattr(trace, "replay"):
            return []
        return [
            ev for ev in trace.replay()
            if ev.get("event_type") == "fork_gate_evidence"
        ]

    def _system_forensics(self) -> dict:
        if not system_flag_enabled():
            return {"available": False, "reason": "AUREL_SYSTEM off"}
        model = SystemReadModel.from_runtime(self._inner)
        return {
            "available": True,
            "audit": model.audit_log(limit=20),
            "usage": model.usage(),
            "model_routing": model.model_routing(),
            "policies": model.policy_browser(),
            "archive": model.archive_status(),
        }

    def to_dict(self) -> dict:
        replay = self._chronos_replay()
        system = self._system_forensics()
        replayable = bool(replay.get("replayable"))
        return {
            "run_id": self._run_id,
            "trace_dir": str(self._trace_dir) if self._trace_dir else None,
            "chronos_replay": replay,
            "fork_gate_evidence": self._fork_gate_events(),
            "system": system,
            "library_time_travel": claims_library_time_travel(),
            "succession_drill_module": True,
            "replayable": replayable and system.get("available", False),
        }


__all__ = ["F8RunProjection"]
