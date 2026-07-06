"""Dual Kernel — Σ vector, routing, constraints, merge gate + NC firewall.

Real objects throughout: no mocks. The commit round-trip drives a genuine
WorldLineForest fork → MergeGate.commit → merge, proving the gate is functional
end to end and that a rejected fork never touches live state.
"""
from __future__ import annotations

from agentic_runtime import (
    AgentCard,
    AgentClass,
    AuthorityScope,
    RiskLevel,
    StateStore,
    UnsafeLocalSandbox,
    WorldLineForest,
    build_runtime,
)
from agentic_runtime.core_types import CommandEnvelope, Intent, VerifierResult
from agentic_runtime.dual_kernel import (
    ConstraintSet,
    GovernanceStateVector,
    MergeContext,
    MergeGate,
    MergeVerdict,
    Route,
    SigmaGovernor,
    autonomy_index,
    binding_for,
    compliance_lower_bound,
    load_bindings,
    no_recovery_compliance,
    validate_coverage,
)
from agentic_runtime.dual_kernel.merge_gate import GATE_IDS
from agentic_runtime.hitl import AutoApprover
from agentic_runtime.policy import PolicyDecision, PolicyVerdict


# --------------------------------------------------------------------------- #
#  builders (real cards / commands)
# --------------------------------------------------------------------------- #
def _exec_card(**auth_kw) -> AgentCard:
    auth = AuthorityScope(write_paths=["src/"], read_paths=["*"],
                          max_risk=RiskLevel.HIGH, **auth_kw)
    return AgentCard.make(name="Exec", agent_class=AgentClass.EXECUTION,
                          mission="dk", authority=auth,
                          allowed_tools=["read_file", "write_file", "list_dir"])


def _read_card() -> AgentCard:
    auth = AuthorityScope(write_paths=[], read_paths=["*"], max_risk=RiskLevel.LOW)
    return AgentCard.make(name="Reader", agent_class=AgentClass.RESEARCH,
                          mission="dk", authority=auth,
                          allowed_tools=["read_file", "list_dir"])


def _high_card() -> AgentCard:
    auth = AuthorityScope(write_paths=["*"], read_paths=["*"],
                          max_risk=RiskLevel.HIGH, allow_network=True)
    return AgentCard.make(name="High", agent_class=AgentClass.CORE, mission="dk",
                          authority=auth, allowed_tools=["run_shell", "write_file"],
                          escalation_policy=["prime", "operator"])


def _cmd(card, tool="write_file", path="src/x.py"):
    return CommandEnvelope.make(issuer_card_id=card.id, tool=tool,
                                args={"path": path, "content": "X\n"},
                                rationale="dk", declared_risk=RiskLevel.LOW,
                                expected_effect="write")


def _decision(risk=RiskLevel.LOW):
    return PolicyDecision(verdict=PolicyVerdict.ALLOW, risk=risk, reasons=[])


def _sigma(card, risk=RiskLevel.LOW, approved=False, cmd=None):
    gov = SigmaGovernor()
    intent = Intent.make("do the thing")
    sigma = gov.register_task(card, intent)
    return sigma.update(cmd or _cmd(card), _decision(risk), approved=approved)


# --------------------------------------------------------------------------- #
#  Σ vector
# --------------------------------------------------------------------------- #
def test_sigma_registration_is_identity_only():
    card = _exec_card()
    sigma = SigmaGovernor().register_task(card, Intent.make("t"))
    assert sigma.authority_card_id == card.id
    assert sigma.step_count == 0
    assert sigma.max_sensitivity is RiskLevel.TRIVIAL


def test_sigma_update_is_monotone():
    card = _exec_card()
    s0 = SigmaGovernor().register_task(card, Intent.make("t"))
    s1 = s0.update(_cmd(card), _decision(RiskLevel.MEDIUM))
    s2 = s1.update(_cmd(card, tool="read_file"), _decision(RiskLevel.LOW))
    # sensitivity never weakens even though the 2nd step is lower risk
    assert s2.max_sensitivity is RiskLevel.MEDIUM
    assert s2.step_count == 2
    assert "src/x.py" in s2.write_paths_touched


def test_sigma_tracks_net_and_barriers():
    card = _exec_card(allow_network=True)
    s = _sigma(card, cmd=_cmd(card, tool="network_fetch", path="https://x"))
    # network_fetch has no 'path' write, but flags net + a barrier tag
    assert s.net_or_secrets_used is True
    s2 = s.update(_cmd(card, path="docs/readme.md"), _decision())
    assert s2.crosses_barrier(_cmd(card, path="secrets/key")) is True


# --------------------------------------------------------------------------- #
#  routing / autonomy
# --------------------------------------------------------------------------- #
def test_autonomy_index_bands():
    assert autonomy_index(_read_card()) == 0
    # observability is fixed at 0 (trace is always-on) so the ceiling is 8,
    # which is already the top of the hard-gated band (>= 8).
    assert autonomy_index(_high_card()) == 8


def test_route_fast_for_reversible_low_risk():
    card = _read_card()
    dec = SigmaGovernor().admit_step(
        _sigma(card, cmd=_cmd(card, tool="read_file")),
        _cmd(card, tool="read_file"), _decision(RiskLevel.LOW), card)
    assert dec.route is Route.FAST


def test_route_hard_for_high_autonomy():
    card = _high_card()
    dec = SigmaGovernor().admit_step(
        _sigma(card), _cmd(card), _decision(RiskLevel.LOW), card)
    assert dec.route is Route.HARD_GATED


def test_route_hard_on_low_identity_confidence():
    card = _read_card()
    dec = SigmaGovernor().admit_step(
        _sigma(card), _cmd(card, tool="read_file"), _decision(RiskLevel.LOW),
        card, identity_confidence=0.2)
    assert dec.route is Route.HARD_GATED
    assert dec.blocked is True


# --------------------------------------------------------------------------- #
#  constraints + ABC bound
# --------------------------------------------------------------------------- #
def test_hard_invariant_blocks_out_of_authority_risk():
    card = _exec_card()  # max_risk HIGH
    cs = ConstraintSet.default()
    sigma = _sigma(card, risk=RiskLevel.CRITICAL)  # above HIGH
    assert "within_authority_risk" in cs.hard_violations(sigma, _cmd(card), card)


def test_hard_invariant_blocks_unauthorised_network():
    card = _exec_card()  # allow_network defaults False
    cs = ConstraintSet.default()
    sigma = SigmaGovernor().register_task(card, Intent.make("t"))
    cmd = _cmd(card, tool="network_fetch", path="https://x")
    assert "no_secrets_egress" in cs.hard_violations(sigma, cmd, card)


def test_abc_recovery_bound_beats_exponential_decay():
    # Lemma 3.10 worked example.
    assert round(no_recovery_compliance(0.99, 100), 3) == 0.366
    assert compliance_lower_bound(0.99, 0.95, 100) == 0.95
    assert compliance_lower_bound(0.99, 0.0, 100) < no_recovery_compliance(0.99, 100) + 1


# --------------------------------------------------------------------------- #
#  NC firewall
# --------------------------------------------------------------------------- #
def test_every_gate_is_canon_bound():
    validate_coverage(GATE_IDS)  # raises if any gate lacks a binding
    for gid in GATE_IDS:
        assert binding_for(gid).nc_law


def test_bindings_load_and_are_unique():
    bindings = load_bindings()
    assert len(bindings) == len(GATE_IDS)


def test_unknown_gate_has_no_binding():
    try:
        binding_for("not_a_gate")
    except KeyError:
        return
    raise AssertionError("expected KeyError for uncovered gate")


# --------------------------------------------------------------------------- #
#  merge gate — decision logic (pure, real inputs)
# --------------------------------------------------------------------------- #
def _clean_ctx(card, **over) -> MergeContext:
    base = dict(
        cmd=_cmd(card),
        verifier_result=VerifierResult(True, "write_file_verifier", reason="ok"),
        sigma=_sigma(card),
        card=card,
        child_write_paths=("src/x.py",),
        evidence_refs=("state:abc123",),
        simulation_resolved=True,
        rollback_path_defined=True,
    )
    base.update(over)
    return MergeContext(**base)


def test_merge_gate_pass_on_clean_fork():
    dec = MergeGate().evaluate(_clean_ctx(_exec_card()))
    assert dec.final_status is MergeVerdict.PASS
    assert dec.mergeable is True
    assert dec.blockers == []


def test_failed_verification_is_blocking():
    ctx = _clean_ctx(
        _exec_card(),
        verifier_result=VerifierResult(False, "write_file_verifier",
                                       reason="diverges"))
    dec = MergeGate().evaluate(ctx)
    assert dec.final_status is MergeVerdict.BLOCKING_FAIL
    assert "state_verification" in dec.blockers


def test_unresolved_simulation_blocks_merge():
    dec = MergeGate().evaluate(_clean_ctx(_exec_card(), simulation_resolved=False))
    assert dec.final_status is MergeVerdict.BLOCKING_FAIL
    assert dec.simulation_live_status == "UNRESOLVED"


def test_out_of_scope_write_fails_c1():
    dec = MergeGate().evaluate(
        _clean_ctx(_exec_card(), child_write_paths=("etc/passwd",)))
    assert "C1_interface_compatibility" in dec.blockers
    assert dec.final_status is MergeVerdict.FAIL


def test_high_sensitivity_without_approval_routes_to_authority_review():
    card = _exec_card()
    ctx = _clean_ctx(card, sigma=_sigma(card, risk=RiskLevel.HIGH, approved=False))
    dec = MergeGate().evaluate(ctx)
    assert dec.final_status is MergeVerdict.NEEDS_AUTHORITY_REVIEW
    assert dec.authority_status == "UNRESOLVED"


def test_decision_carries_nc_laws():
    dec = MergeGate().evaluate(_clean_ctx(_exec_card(), simulation_resolved=False))
    assert "NC-01I-068" in dec.to_dict()["nc_laws"]


# --------------------------------------------------------------------------- #
#  merge gate — real fork/commit round-trip (no mocks)
# --------------------------------------------------------------------------- #
def _approver():
    return AutoApprover(lambda r: True, allow_r2=True, allow_r3=True,
                        allow_r4=True, allow_r5=True)


def _merge_card() -> AgentCard:
    return AgentCard.make(
        name="Merge", agent_class=AgentClass.EXECUTION, mission="merge",
        authority=AuthorityScope(write_paths=["src/"], read_paths=["*"],
                                 max_risk=RiskLevel.HIGH),
        allowed_tools=["read_file", "write_file", "list_dir"])


def _forked_child(tmp_path):
    trace_dir = str(tmp_path / "traces")
    store = StateStore(trace_dir)
    kernel = build_runtime(
        sandbox=UnsafeLocalSandbox(root=str(tmp_path / "ws")),
        approval_gate=_approver(), trace_backend="persistent",
        trace_dir=trace_dir, retain_states=True, state_store=store)
    card = _merge_card()
    base = CommandEnvelope.make(issuer_card_id=card.id, tool="write_file",
                                args={"path": "src/base.py", "content": "BASE\n"},
                                rationale="m", declared_risk=RiskLevel.LOW,
                                expected_effect="base")
    r = kernel.runtime.submit(base, card)
    assert r.ok
    kernel.trace.seal_run("completed")
    parent_id = kernel.trace.run_id

    forest = WorldLineForest(trace_dir)
    res = forest.fork(parent_id, r.transition.entry_hash,
                      sandbox_factory=lambda p: UnsafeLocalSandbox(root=p))
    child = build_runtime(
        sandbox=res.sandbox, approval_gate=_approver(),
        trace_backend="persistent", trace_dir=trace_dir,
        trace_run_id=res.child_run_id, retain_states=True, state_store=store)
    cr = child.runtime.submit(
        CommandEnvelope.make(issuer_card_id=card.id, tool="write_file",
                             args={"path": "src/feature.py", "content": "FEAT\n"},
                             rationale="m", declared_risk=RiskLevel.LOW,
                             expected_effect="feature"), card)
    assert cr.ok
    child.trace.seal_run("completed")
    return forest, parent_id, res.child_run_id, card


def test_commit_merges_live_only_on_pass(tmp_path):
    forest, parent_id, child_id, card = _forked_child(tmp_path)
    gate = MergeGate()
    ctx = _clean_ctx(card, child_write_paths=("src/feature.py",))
    decision = gate.evaluate(ctx)
    assert decision.final_status is MergeVerdict.PASS

    result = gate.commit(decision, forest, parent_id, child_id)
    assert result is not None and result.clean
    assert forest.store.has(result.merged_state_hash)
    assert len(forest.merges()) == 1


def test_commit_discards_fork_on_reject(tmp_path):
    forest, parent_id, child_id, card = _forked_child(tmp_path)
    gate = MergeGate()
    # a rejected verdict must NOT touch the forest
    bad = gate.evaluate(_clean_ctx(card, simulation_resolved=False,
                                   child_write_paths=("src/feature.py",)))
    assert not bad.mergeable
    assert gate.commit(bad, forest, parent_id, child_id) is None
    assert forest.merges() == []  # live state provably untouched
