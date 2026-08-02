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
from .aureleu_read_model import AurelEUReadModel
from .board import BoardJournal
from .conversation import RoomHistoryProjection, rooms_from_trace
from .corp_read_model import CorpReadModel
from .dn import DnStatusReadModel
from .hq_command import HQCommandReadModel
from .library import LibraryReadModel, claims_library_time_travel, memory_asof_available
from .system_read_model import SystemReadModel, flag_enabled as system_flag_enabled
from .workbench import ApprovalWorkbenchReadModel
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
    as_of = _one(params, "as_of", "")
    valid_s = _one(params, "valid_time", "")
    trans_s = _one(params, "transaction_time", "") or as_of
    valid_time = float(valid_s) if valid_s else None
    transaction_time = float(trans_s) if trans_s else None
    memory_id = _one(params, "memory_id", "")

    lib = LibraryReadModel.from_trace(
        reads.trace,
        fabric=getattr(reads.runtime, "memory", None),
    )
    if valid_time is not None or transaction_time is not None:
        if not memory_asof_available():
            return {
                "available": False,
                "status": "UNAVAILABLE",
                "reason": "library as-of requires AUREL_SYSTEM=1",
                "claims_time_travel": claims_library_time_travel(),
            }
        try:
            lib = lib.as_of(
                valid_time,
                transaction_time,
                fabric=getattr(reads.runtime, "memory", None),
            )
        except ValueError as exc:
            raise ReadModelError(str(exc)) from exc

    body = lib.to_dict()
    if memory_id:
        body["provenance_chain"] = lib.provenance_chain(memory_id)
    if transaction_time is not None or valid_time is not None:
        body["as_of"] = {
            "valid_time": valid_time,
            "transaction_time": transaction_time,
        }
    return body


def _hq_command(reads: "LiveReadModels", _params: "dict[str, list[str]]") -> dict:
    # `inbox` is the live pending queue (None when the server is unbound, in which
    # case the model honestly reports pending_source='unavailable').
    return HQCommandReadModel.from_runtime(reads.runtime, inbox=reads.inbox).to_dict()


def _board(reads: "LiveReadModels", _params: "dict[str, list[str]]") -> dict:
    return {"decisions": [e.to_dict() for e in BoardJournal.from_trace(reads.trace)],
            "options": BoardJournal.options_from_trace(reads.trace)}


def _aureleu_dn(reads: "LiveReadModels", _params: "dict[str, list[str]]") -> dict:
    return DnStatusReadModel.status()


def _aureleu(reads: "LiveReadModels", _params: "dict[str, list[str]]") -> dict:
    return AurelEUReadModel(reads.runtime).to_dict()


def _corp_portfolio(reads: "LiveReadModels", _params: "dict[str, list[str]]") -> dict:
    return CorpReadModel.from_runtime(reads.runtime).portfolio_view()


def _corp_runtime(reads: "LiveReadModels", params: "dict[str, list[str]]") -> dict:
    job = _one(params, "job", "")
    return CorpReadModel.from_runtime(reads.runtime).runtime_feed(job)


def _corp_workbench(reads: "LiveReadModels", _params: "dict[str, list[str]]") -> dict:
    # The bound inbox supplies the enriched pending items; without one the model
    # returns [] and the trace-derived tool history stays live (F5.5 discipline).
    return ApprovalWorkbenchReadModel.from_runtime(
        reads.runtime, inbox=reads.inbox).to_dict()


def _corp_kpi(reads: "LiveReadModels", _params: "dict[str, list[str]]") -> dict:
    from ..corp import ReflexFlywheelView
    inner = reads.runtime
    return ReflexFlywheelView.build(
        skills=getattr(inner, "skills", None),
        ledger=getattr(inner, "budget", None)).to_dict()


def _system_unavailable() -> dict:
    from .system_read_model import unavailable_payload
    return unavailable_payload()


def _system_audit(reads: "LiveReadModels", params: "dict[str, list[str]]") -> dict:
    if not system_flag_enabled():
        return _system_unavailable()
    since = float(_one(params, "since", "0") or "0")
    until = float(_one(params, "until", "0") or "0")
    offset = int(_one(params, "offset", "0") or "0")
    limit = int(_one(params, "limit", "0") or "0")
    return SystemReadModel.from_runtime(reads.runtime, router=reads.router).audit_log(
        kind=_one(params, "kind", ""),
        mandate_id=_one(params, "mandate", "") or _one(params, "mandate_id", ""),
        agent_id=_one(params, "agent", "") or _one(params, "agent_id", ""),
        since=since,
        until=until,
        offset=offset,
        limit=limit,
    )


def _system_model(reads: "LiveReadModels", _params: "dict[str, list[str]]") -> dict:
    if not system_flag_enabled():
        return _system_unavailable()
    return SystemReadModel.from_runtime(reads.runtime, router=reads.router).model_routing()


def _system_policies(reads: "LiveReadModels", _params: "dict[str, list[str]]") -> dict:
    if not system_flag_enabled():
        return _system_unavailable()
    return SystemReadModel.from_runtime(reads.runtime, router=reads.router).policy_browser()


def _system_archive(reads: "LiveReadModels", _params: "dict[str, list[str]]") -> dict:
    if not system_flag_enabled():
        return _system_unavailable()
    return SystemReadModel.from_runtime(reads.runtime, router=reads.router).archive_status()


def _system_usage(reads: "LiveReadModels", _params: "dict[str, list[str]]") -> dict:
    if not system_flag_enabled():
        return _system_unavailable()
    return SystemReadModel.from_runtime(reads.runtime, router=reads.router).usage()


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
    "aureleu": _aureleu,
    "aureleu/dn": _aureleu_dn,
    "corp/portfolio": _corp_portfolio,
    "corp/runtime": _corp_runtime,
    "corp/workbench": _corp_workbench,
    "corp/kpi": _corp_kpi,
    "system/audit": _system_audit,
    "system/usage": _system_usage,
    "system/model_routing": _system_model,
    "system/policies": _system_policies,
    "system/archive": _system_archive,
}


class LiveReadModels:
    """Pure live read projections over one runtime's trace (zero writes)."""

    def __init__(self, runtime: Any, *, inbox: Any = None) -> None:
        # Hold the runtime; the trace is resolved lazily per read (matching the
        # dispatcher's discipline — a runtime that is never read is never touched).
        # Each read calls replay() fresh, so newly appended events show up — live.
        self._source = runtime
        self._runtime = getattr(runtime, "runtime", runtime)
        # Operational, not a projection: the in-process pending queue. Reads stay
        # read-only — they only ever call `inbox.pending()`.
        self._inbox = inbox

    @property
    def router(self) -> Any:
        return getattr(self._source, "router", None)

    @property
    def inbox(self) -> Any:
        return self._inbox

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
