"""A1a — Memory ops as governed tools.

A thin, governed dispatcher (`MemoryToolSession`) that lets an entity *propose*
memory operations. It never stores directly: every write routes through the
EXISTING ``MemoryFabric.request_write`` funnel (policy → ``_trace_memory`` →
single ``MemoryGovernanceRecord``), and reads route through ``retrieve``.

Boundary (cross-cutting invariants):

* **Entity proposes, runtime disposes.** The caller supplies ``content`` /
  ``truth_state`` via tool args; the *writer identity* is a property of the
  session (set by whoever constructs it), never a tool arg — so an agent cannot
  pass ``writer_kind`` and cannot self-elevate. ``MemoryWritePolicy`` disposes.
* **Not the sandbox / not ``runtime.submit``.** Memory tools take no sandbox
  snapshot, produce no ``StateTransitionRecord``, and incur no
  ``charge_sandbox_execution`` — exactly one ``charge_memory_write`` per governed
  write attempt (allow OR deny), mirroring ``runtime._record_command_memory`` and
  ``entity._remember``. ``mem_search`` is read-only and charges nothing.
* **Fail-closed / no-overclaim.** ``mem_update`` / ``mem_delete`` / ``mem_link``
  are declared but honestly UNAVAILABLE in A1a (their fabric primitives arrive in
  A2/A4); they perform no write and incur no charge.
"""

from __future__ import annotations

from typing import Any, Optional

from .core_types import MemoryTruthState
from .tool_contracts import ToolContractRegistry, ToolInputValidator, memory_contract_registry

MEMORY_TOOL_NAMES = frozenset(
    {"mem_add", "mem_update", "mem_delete", "mem_search", "mem_link"}
)
MEMORY_WRITE_TOOLS = frozenset({"mem_add", "mem_update", "mem_delete", "mem_link"})
MEMORY_READ_TOOLS = frozenset({"mem_search"})
# Declared in A1a but not yet backed by a fabric primitive (graph=A2, revision=A4).
_UNAVAILABLE_TOOLS = frozenset({"mem_update", "mem_delete", "mem_link"})

# Mirrors ``memory_governance.AGENT_WRITER`` — the least-privilege writer kind.
# Defined locally to keep import time trivial (no eager governance import).
_AGENT_WRITER = "agent"


def _writer_kind_from_card(card: Any) -> str:
    """Derive the session's writer identity from the card the runtime attaches.

    Identity is a property of the caller, never a tool arg: an agent cannot pass
    ``writer_kind`` and cannot self-elevate. With no card we fail to the least
    privilege (agent); a card may declare its writer kind explicitly."""
    if card is None:
        return _AGENT_WRITER
    for attr in ("memory_writer_kind", "writer_kind"):
        val = getattr(card, attr, None)
        if val:
            return str(val)
    return _AGENT_WRITER


class MemoryToolSession:
    """Governed dispatcher for the memory tools. Constructed by the runtime/entity;
    the ``writer_kind`` it carries is the caller's true identity, not an arg."""

    def __init__(
        self,
        fabric: Any,
        budget: Any,
        *,
        writer_kind: Optional[str] = None,
        created_by: str = "",
        card: Any = None,
        contracts: Optional[ToolContractRegistry] = None,
    ) -> None:
        self.fabric = fabric
        self.budget = budget
        self.card = card
        # Identity is set by the constructor (the runtime), never by tool args.
        # An explicit writer_kind wins; otherwise it is derived from the card
        # (agent cannot self-elevate). Absent both, least privilege (agent).
        self.writer_kind = writer_kind or _writer_kind_from_card(card)
        self.created_by = created_by or (str(getattr(card, "id", "")) if card else "")
        self.contracts = contracts or memory_contract_registry()
        self.validator = ToolInputValidator()

    # -- identity -------------------------------------------------------- #
    def _writer_kind(self) -> str:
        """The session's fixed writer identity. Agents cannot self-elevate: the
        tool contracts expose no ``writer_kind`` arg, so this value is never
        caller-controlled."""
        return self.writer_kind

    def _run_id(self) -> str:
        trace = getattr(self.fabric, "_trace", None)
        return str(getattr(trace, "run_id", "") or "")

    # -- dispatch -------------------------------------------------------- #
    def invoke(self, tool_name: str, args: dict) -> dict:
        if tool_name not in MEMORY_TOOL_NAMES:
            return {"ok": False, "tool": tool_name, "reason_code": "unknown_memory_tool",
                    "message": f"no such memory tool: {tool_name}"}
        contract = self.contracts.get(tool_name)
        if contract is None:
            return {"ok": False, "tool": tool_name, "reason_code": "no_contract",
                    "message": f"{tool_name} has no registered memory contract"}
        check = self.validator.validate(contract, args)
        if not check.ok:
            return {"ok": False, "tool": tool_name, "reason_code": check.code,
                    "message": check.message}
        if tool_name in _UNAVAILABLE_TOOLS:
            return self._unavailable(tool_name)
        if tool_name == "mem_add":
            return self._mem_add(args)
        if tool_name == "mem_search":
            return self._mem_search(args)
        # Unreachable (all names covered above); fail closed rather than guess.
        return {"ok": False, "tool": tool_name, "reason_code": "unhandled",
                "message": f"no handler for {tool_name}"}

    # -- handlers -------------------------------------------------------- #
    def _unavailable(self, tool_name: str) -> dict:
        return {
            "ok": False,
            "tool": tool_name,
            "unavailable": True,
            "reason_code": "requires_a2_a4",
            "message": (f"{tool_name} is declared but not yet implemented — memory "
                        "graph (A2) / belief-revision (A4) primitives are required"),
        }

    def _mem_add(self, args: dict) -> dict:
        from .memory_governance import MemoryWriteRequest

        truth = (MemoryTruthState(args["truth_state"])
                 if args.get("truth_state") else MemoryTruthState.RAW)
        req = MemoryWriteRequest(
            content=args["content"],
            proposed_truth_state=truth,
            writer_kind=self._writer_kind(),
            created_by=self.created_by,
            source_run_id=self._run_id(),
            source_trace_ids=list(args.get("source_trace_ids", [])),
            evidence_refs=list(args.get("evidence_refs", [])),
            confidence=float(args.get("confidence", 0.5)),
            importance=float(args.get("importance", 0.5)),
        )
        # Exactly one charge per governed write ATTEMPT (allow or deny), before
        # the single request_write — which anchors one MemoryGovernanceRecord.
        self.budget.charge_memory_write()
        decision = self.fabric.request_write(req)
        return {
            "ok": bool(decision.allowed),
            "tool": "mem_add",
            "verdict": "allow" if decision.allowed else "deny",
            "reason_code": decision.reason_code,
            "message": decision.message,
            "truth_state": decision.effective_truth_state.value,
            "memory_id": decision.record.memory_id if decision.record else "",
        }

    def _mem_search(self, args: dict) -> dict:
        # Read-only: no charge, no write, no sandbox.
        k = int(args.get("k", 5))
        records = self.fabric.retrieve(args["query"], k=k)
        return {
            "ok": True,
            "tool": "mem_search",
            "read_only": True,
            "count": len(records),
            "results": [
                {"memory_id": r.memory_id, "content": r.content,
                 "tier": r.tier.value, "truth_state": r.truth_state.value,
                 "confidence": r.confidence}
                for r in records
            ],
        }


__all__ = [
    "MEMORY_TOOL_NAMES",
    "MEMORY_WRITE_TOOLS",
    "MEMORY_READ_TOOLS",
    "MemoryToolSession",
]
