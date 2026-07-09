"""
read_models.py — live read projections behind `GET /read/{model}` (F5.1).

Every read is a **pure projection over the trace**: same trace ⇒ same bytes, zero
writes, no subsystem call beyond `replay()`. A small registry maps a model name to
a deterministic builder `(trace, params) → dict`. The projections are the ones the
one door already produces — Signal/WorkOPS history, the WorkOPS task list, the
approval audit, the room index — so `/read` is genuinely live, never a static
fixture. When the Front server is OFF there is no live read at all; the web/shell
dev fixture is the honest fallback (F5.8), never a faked "live".
"""
from __future__ import annotations

from typing import Any, Callable
from urllib.parse import parse_qs, urlparse

from .approval_inbox import ApprovalInbox
from .board import BoardJournal
from .conversation import RoomHistoryProjection, rooms_from_trace
from .hq_command import HQCommandReadModel
from .library import LibraryReadModel
from .workops import WorkOpsChatReadModel, workops_room

# A builder maps (reads-context, query-params) → the model-specific body dict.
# The context exposes `.trace` (pure projections) and `.runtime` (live operational
# views such as the budget ledger). Every builder is read-only.
ReadBuilder = Callable[["LiveReadModels", "dict[str, list[str]]"], dict]


class ReadModelError(ValueError):
    """A malformed read request (e.g. a missing required param). Fail-closed → 400."""


def _one(params: "dict[str, list[str]]", key: str, default: str) -> str:
    values = params.get(key)
    return values[0] if values else default


def _signal_history(reads: "LiveReadModels", params: "dict[str, list[str]]") -> dict:
    room = _one(params, "room", "signal:main")
    hist = RoomHistoryProjection.from_trace(reads.trace, room)
    return {"room": room, "entries": [h.to_dict() for h in hist]}


def _workops_tasks(reads: "LiveReadModels", _params: "dict[str, list[str]]") -> dict:
    return {"tasks": [t.to_dict() for t in WorkOpsChatReadModel.tasks(reads.trace)]}


def _workops_history(reads: "LiveReadModels", params: "dict[str, list[str]]") -> dict:
    task = _one(params, "task", "")
    if not task:
        raise ReadModelError("workops/history requires a 'task' query param")
    hist = WorkOpsChatReadModel.history(reads.trace, task)
    return {"task": task, "room": workops_room(task),
            "entries": [h.to_dict() for h in hist]}


def _approvals(reads: "LiveReadModels", _params: "dict[str, list[str]]") -> dict:
    return {"audit": ApprovalInbox.audit_from_trace(reads.trace)}


def _rooms(reads: "LiveReadModels", params: "dict[str, list[str]]") -> dict:
    prefix = _one(params, "prefix", "")
    return {"prefix": prefix, "rooms": rooms_from_trace(reads.trace, prefix)}


def _library(reads: "LiveReadModels", params: "dict[str, list[str]]") -> dict:
    lib = LibraryReadModel.from_trace(reads.trace)
    memory_id = _one(params, "memory_id", "")
    body = lib.to_dict()
    if memory_id:  # optional drill-down into one record's provenance chain
        body["provenance_chain"] = lib.provenance_chain(memory_id)
    return body


def _hq_command(reads: "LiveReadModels", _params: "dict[str, list[str]]") -> dict:
    return HQCommandReadModel.from_runtime(reads.runtime).to_dict()


def _board(reads: "LiveReadModels", _params: "dict[str, list[str]]") -> dict:
    return {"decisions": [e.to_dict() for e in BoardJournal.from_trace(reads.trace)]}


# The complete live-read registry. Every entry is read-only.
_REGISTRY: "dict[str, ReadBuilder]" = {
    "signal/history": _signal_history,
    "workops/tasks": _workops_tasks,
    "workops/history": _workops_history,
    "approvals": _approvals,
    "rooms": _rooms,
    "library": _library,
    "hq/command": _hq_command,
    "board": _board,
}


class LiveReadModels:
    """Pure live read projections over one runtime's trace (zero writes)."""

    def __init__(self, runtime: Any) -> None:
        # Hold the runtime; the trace is resolved lazily per read (matching the
        # dispatcher's discipline — a runtime that is never read is never touched).
        # Each read calls replay() fresh, so newly appended events show up — live.
        self._runtime = getattr(runtime, "runtime", runtime)

    @property
    def runtime(self) -> Any:
        return self._runtime

    @property
    def trace(self) -> Any:
        return self._runtime.trace

    @staticmethod
    def known() -> tuple[str, ...]:
        return tuple(sorted(_REGISTRY))

    def build(self, model: str, params: "dict[str, list[str]]") -> dict:
        """The model-specific body, or raise. Read-only — used by the seal to
        compare against a direct projection."""
        builder = _REGISTRY.get(model)
        if builder is None:
            raise ReadModelError(f"unknown read model {model!r}")
        return builder(self, params)

    def read(self, path: str) -> tuple[int, dict]:
        """Handle `GET /read/{model}[?params]`. 404 unknown, 400 malformed, else live."""
        parsed = urlparse(path)
        model = parsed.path[len("/read/"):]
        params = parse_qs(parsed.query)
        if model not in _REGISTRY:
            return 404, {"error": f"unknown read model {model!r}",
                         "known": list(self.known())}
        try:
            body = self.build(model, params)
        except ReadModelError as e:
            return 400, {"error": str(e)}
        return 200, {"model": model, "live": True, **body}
