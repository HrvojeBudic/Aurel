"""A2 seal — typed relation graph (memory-graph primitives).

Proves the A2 invariants of the governed edge funnel (`MemoryFabric.link` /
`MemoryWritePolicy.evaluate_link`) and the now-live `mem_link` tool:

1. A governed edge write succeeds, stores exactly one edge, and anchors exactly
   one `MemoryGovernanceRecord(action="link")` — no `StateTransitionRecord`.
2. Unknown endpoint fails closed (`unknown_endpoint`): no edge, deny row.
3. An agent cannot mint a *trust-elevating* edge: SUPERSEDES/CONTRADICTS without
   evidence is denied (`link_requires_evidence`), and an allowed agent edge never
   changes an endpoint's `truth_state` (edges are not the promotion ladder).
4. `mem_link` is live end-to-end through `MemoryToolSession` (one
   `charge_memory_write` per attempt, zero sandbox).
5. No-collapse: existing writes + retrieval are unchanged by linking; the graph
   read model is append-only and read-only.
6. `detect_supersession_chain` returns the ordered chain and fails closed on an
   id the graph never saw.
7. Structural governance: illegal relation and self-link are denied at the policy.
"""

from __future__ import annotations

from agentic_runtime import MemoryFabric, MemoryTruthState, MemoryWriteRequest
from agentic_runtime.budget import BudgetLedger
from agentic_runtime.memory_governance import MemoryLinkRequest, MemoryWritePolicy
from agentic_runtime.memory_graph import MemoryRelation, detect_supersession_chain
from agentic_runtime.memory_tools import MemoryToolSession
from agentic_runtime.trace import InMemoryTraceLedger

RUN = "run_a2"


def _harness():
    trace = InMemoryTraceLedger(run_id=RUN)
    fabric = MemoryFabric()
    fabric.bind_trace(trace)
    budget = BudgetLedger()
    return fabric, trace, budget


def _seed(fabric, content, *, truth="raw"):
    """Store a record directly through the fabric (does NOT touch the budget)."""
    decision = fabric.request_write(MemoryWriteRequest(
        content=content,
        proposed_truth_state=MemoryTruthState(truth),
        writer_kind="operator",
        source_run_id=RUN,
    ))
    return decision.record.memory_id


def _link_rows(trace) -> list[dict]:
    return [e for e in trace.replay()
            if e["kind"] == "memory_governance" and e["action"] == "link"]


def _state_rows(trace) -> list[dict]:
    return [e for e in trace.replay() if e["kind"] == "state_transition"]


# 1 ─ governed edge write succeeds, stored once, traced once, no state row.
def test_governed_edge_write_succeeds_and_traced_once():
    fabric, trace, budget = _harness()
    a = _seed(fabric, "the door was open")
    b = _seed(fabric, "the door is now closed")
    session = MemoryToolSession(fabric, budget, writer_kind="operator")

    result = session.invoke("mem_link", {
        "from_id": b, "to_id": a, "relation": "supersedes",
        "evidence_refs": ["obs:door-closed"],
    })

    assert result["ok"] is True
    assert result["verdict"] == "allow"
    assert result["relation"] == "supersedes"
    assert result["edge_id"]
    assert len(fabric.graph) == 1
    edge = fabric.graph.all_edges()[0]
    assert (edge.from_id, edge.to_id, edge.relation) == (b, a, MemoryRelation.SUPERSEDES)
    # Exactly one link governance row; no StateTransitionRecord from the funnel.
    assert len(_link_rows(trace)) == 1 and _link_rows(trace)[0]["verdict"] == "allow"
    assert len(_state_rows(trace)) == 0
    # One charge per attempt; never the sandbox.
    assert budget.memory_writes == 1
    assert budget.sandbox_executions == 0


# 2 ─ unknown endpoint fails closed (deny, no edge), attempt still charged once.
def test_unknown_endpoint_fails_closed():
    fabric, trace, budget = _harness()
    a = _seed(fabric, "real record")
    session = MemoryToolSession(fabric, budget, writer_kind="operator")

    result = session.invoke("mem_link", {
        "from_id": a, "to_id": "mem_does_not_exist", "relation": "relates_to",
    })

    assert result["ok"] is False
    assert result["verdict"] == "deny"
    assert result["reason_code"] == "unknown_endpoint"
    assert result["edge_id"] == ""
    assert len(fabric.graph) == 0
    rows = _link_rows(trace)
    assert len(rows) == 1 and rows[0]["verdict"] == "deny"
    assert budget.memory_writes == 1          # the attempt is charged, allow or deny


# 3 ─ agent cannot mint a trust-elevating edge.
def test_agent_cannot_mint_trust_elevating_edge():
    fabric, trace, budget = _harness()
    old = _seed(fabric, "candidate belief", truth="candidate")
    new = _seed(fabric, "newer belief")
    agent = MemoryToolSession(fabric, budget, writer_kind="agent")

    # (a) SUPERSEDES without evidence is denied for the agent — no fiat retirement.
    denied = agent.invoke("mem_link", {
        "from_id": new, "to_id": old, "relation": "supersedes",
    })
    assert denied["ok"] is False
    assert denied["reason_code"] == "link_requires_evidence"
    assert len(fabric.graph) == 0

    # (b) An allowed agent edge (SUPPORTS, no evidence needed) never elevates the
    #     endpoint's truth_state — an edge is not a promotion.
    before = fabric.by_id[old].truth_state
    ok = agent.invoke("mem_link", {
        "from_id": new, "to_id": old, "relation": "supports",
    })
    assert ok["ok"] is True
    assert fabric.by_id[old].truth_state is before is MemoryTruthState.CANDIDATE
    assert len(fabric.graph) == 1


# 4 ─ mem_link live end-to-end; non-gated relation needs no evidence.
def test_mem_link_live_end_to_end():
    fabric, trace, budget = _harness()
    a = _seed(fabric, "fact A")
    b = _seed(fabric, "fact B")
    session = MemoryToolSession(fabric, budget, writer_kind="agent")

    result = session.invoke("mem_link", {
        "from_id": a, "to_id": b, "relation": "relates_to",
    })
    assert result["ok"] is True
    assert fabric.graph.neighbors(a) == [b]
    assert budget.memory_writes == 1
    assert budget.sandbox_executions == 0


# 5 ─ no-collapse: existing writes + retrieval unchanged; graph read-only.
def test_no_collapse_writes_and_retrieval_unchanged():
    fabric, trace, budget = _harness()
    a = _seed(fabric, "sky is blue")
    b = _seed(fabric, "grass is green")
    stats_before = fabric.stats()
    retrieved_before = [r.memory_id for r in fabric.retrieve("sky", k=5)]

    session = MemoryToolSession(fabric, budget, writer_kind="operator")
    session.invoke("mem_link", {"from_id": a, "to_id": b, "relation": "relates_to"})

    # Linking added no record and hid none: store + retrieval are unchanged.
    assert fabric.stats() == stats_before
    assert [r.memory_id for r in fabric.retrieve("sky", k=5)] == retrieved_before

    # A subsequent governed mem_add still works and is unaffected by the graph.
    added = session.invoke("mem_add", {"content": "new observation"})
    assert added["ok"] is True

    # Graph reads are copies — mutating a returned list cannot corrupt the index.
    got = fabric.graph.edges_from(a)
    got.clear()
    assert len(fabric.graph.edges_from(a)) == 1


# 6 ─ detect_supersession_chain: ordered chain, fail-closed on unknown id.
def test_detect_supersession_chain():
    fabric, trace, budget = _harness()
    r1 = _seed(fabric, "v1")
    r2 = _seed(fabric, "v2")
    r3 = _seed(fabric, "v3")
    session = MemoryToolSession(fabric, budget, writer_kind="operator")
    session.invoke("mem_link", {"from_id": r2, "to_id": r1,
                                "relation": "supersedes", "evidence_refs": ["e1"]})
    session.invoke("mem_link", {"from_id": r3, "to_id": r2,
                                "relation": "supersedes", "evidence_refs": ["e2"]})

    assert detect_supersession_chain(fabric.graph, r2) == [r1, r2, r3]
    assert detect_supersession_chain(fabric.graph, r1) == [r1, r2, r3]
    assert detect_supersession_chain(fabric.graph, "mem_unknown") == []


# 7 ─ structural governance denials at the policy layer (illegal relation, self-link).
def test_policy_illegal_relation_and_self_link_denied():
    policy = MemoryWritePolicy()
    known = {"m1", "m2"}

    illegal = policy.evaluate_link(
        MemoryLinkRequest(from_id="m1", to_id="m2", relation="teleports",
                          writer_kind="operator", source_run_id=RUN),
        known)
    assert illegal.allowed is False and illegal.reason_code == "illegal_relation"

    loop = policy.evaluate_link(
        MemoryLinkRequest(from_id="m1", to_id="m1", relation="relates_to",
                          writer_kind="operator", source_run_id=RUN),
        known)
    assert loop.allowed is False and loop.reason_code == "self_link_forbidden"

    missing_trace = policy.evaluate_link(
        MemoryLinkRequest(from_id="m1", to_id="m2", relation="relates_to",
                          writer_kind="operator", source_run_id=""),
        known)
    assert missing_trace.allowed is False
    assert missing_trace.reason_code == "missing_trace_reference"
