"""
demo.py — End-to-end proof of the runtime on the canonical use case.

Run:  python -m agentic_runtime.demo
      python examples/demo.py
"""
from __future__ import annotations

import json

from . import build_runtime, AgentCard, AgentClass, AuthorityScope, Intent, RiskLevel
from .core_types import CommandEnvelope
from .hitl import AutoApprover
from .model_router import MockModelClient
from .sandbox import SandboxMode, UnsafeLocalSandbox
from .skills import CapabilityState as CS

BUGGY_CALC = "def add(a, b):\n    return a - b   # BUG: should be +\n"
TEST_CALC = (
    "import calc\n"
    "assert calc.add(2, 3) == 5, f'add broken: {calc.add(2,3)}'\n"
    "print('all tests passed')\n")

GOAL = "fix the add function bug in calc.py and make tests pass"

SCRIPTED_PLAN = json.dumps({"plan": [
    {"tool": "read_file", "args": {"path": "calc.py"},
     "rationale": "inspect the buggy function", "expected_effect": "no change",
     "risk": "trivial"},
    {"tool": "edit_file",
     "args": {"path": "calc.py", "find": "return a - b   # BUG: should be +",
              "replace": "return a + b"},
     "rationale": "correct the operator", "expected_effect": "add() returns sum",
     "risk": "medium"},
    {"tool": "run_tests", "args": {"test_file": "test_calc.py"},
     "rationale": "confirm the fix", "expected_effect": "tests exit 0",
     "risk": "low"},
]})


def seed_repo(kernel) -> None:
    kernel.sandbox.write_file("calc.py", BUGGY_CALC)
    kernel.sandbox.write_file("test_calc.py", TEST_CALC)
    kernel.verifier.test_integrity.snapshot()


def make_card() -> AgentCard:
    return AgentCard.make(
        name="Codebase Surgeon", agent_class=AgentClass.EXECUTION,
        mission="Safe code modification inside the assigned workspace",
        authority=AuthorityScope(
            write_paths=["calc.py"], read_paths=["*"],
            allow_network=False, allow_secrets=False, max_risk=RiskLevel.HIGH),
        allowed_tools=["read_file", "edit_file", "run_tests", "list_dir"],
        denied_tools=["run_shell", "network_fetch", "delete_file"],
        model_profile="balanced",
        escalation_policy=["destructive diff", "tests fail after 3 attempts"])


def banner(t: str) -> None:
    print("\n" + "=" * 70 + f"\n  {t}\n" + "=" * 70)


def build(scripted=True):
    mock = MockModelClient(scripted={GOAL: SCRIPTED_PLAN} if scripted else None)
    router_clients = {"balanced": [mock]}
    # Explicit demo-only unsafe sandbox — NOT a security boundary.
    unsafe = UnsafeLocalSandbox()
    approver = AutoApprover(
        lambda r: r.command.tool in {"read_file", "edit_file", "run_tests"},
    )
    return build_runtime(
        sandbox=unsafe,
        model_clients=router_clients,
        approval_gate=approver,
    )


def main() -> None:
    banner("1. GOVERNED RUN — entity proposes, runtime disposes")
    print(f"  sandbox: {UnsafeLocalSandbox.UNSAFE_WARNING}")
    print(f"  mode: {SandboxMode.UNSAFE_LOCAL.value}")
    kernel = build()
    seed_repo(kernel)
    kernel.memory.assert_canon(
        "Never weaken tests to make them pass. Fix the code, not the test.")
    entity = kernel.spawn(make_card())

    report = entity.run(Intent.make(GOAL))
    print(json.dumps(report, indent=2))

    print("\n-- verified file state after run --")
    print(kernel.sandbox.read_file("calc.py").strip())

    banner("2. TRACE LEDGER — causal replay")
    for i, row in enumerate(kernel.trace.replay()):
        if row.get("kind") == "planning_failure":
            print(f"  [{i}] {row['issuer'][:14]} {'planning_fail':>16} "
                  f"status={row['status']} reason={row['reason'][:40]}")
        elif row.get("kind") == "runtime_status_transition":
            print(f"  [{i}] {row['issuer'][:14]} {'run_state':>16} "
                  f"{row['from']} -> {row['to']} ({row['reason_code']})")
        elif row.get("kind") == "budget_decision":
            print(f"  [{i}] {row['issuer'][:14]} {'budget':>16} "
                  f"{row['metric']}={row['used']:.1f}/{row['limit']:.1f} "
                  f"{row['verdict']}")
        elif row.get("kind") == "memory_governance":
            print(f"  [{i}] {row['issuer'][:14]} {'memory':>16} "
                  f"{row['action']} {row['to']} {row['verdict']} "
                  f"({row['reason_code']})")
        elif row.get("kind") == "tool_contract_violation":
            print(f"  [{i}] {row['issuer'][:14]} {'contract':>16} "
                  f"{row['tool']} {row['phase']} DENY ({row['code']})")
        elif row.get("kind") == "approval_receipt":
            print(f"  [{i}] {row['issuer'][:14]} {'approval':>16} "
                  f"{row['tool']} {row['risk_class']} {row['outcome']} "
                  f"({row['decided_by']})")
        else:
            print(f"  [{i}] {row['issuer'][:14]} {row['verdict']:>16} "
                  f"{row['before']}->{row['after']} verified={row['verified']} "
                  f"({row['verifier']})")
    ok, broken = kernel.trace.verify_chain()
    print(f"\n  chain intact: {ok}  merkle_root: {kernel.trace.merkle_root()[:24]}")

    banner("3. TAMPER DETECTION — mutate a past record, re-verify")
    victim = next(r for r in kernel.trace if hasattr(r, "verifier_result"))
    original = victim.verifier_result.passed
    victim.verifier_result.passed = not original
    ok2, idx = kernel.trace.verify_chain()
    print(f"  forged verifier_result on txn[1]; chain intact now: {ok2} "
          f"(first broken index: {idx})")
    victim.verifier_result.passed = original

    banner("4. AUTHORITY — out-of-scope write is DENIED")
    rogue = CommandEnvelope.make(
        issuer_card_id=entity.card.id, tool="edit_file",
        args={"path": "/etc/passwd", "find": "x", "replace": "y"},
        rationale="attempt privilege escalation", declared_risk=RiskLevel.LOW,
        expected_effect="none")
    res = kernel.runtime.submit(rogue, entity.card)
    print(f"  policy verdict: {res.decision.verdict.value}  executed: {res.ok}")
    print(f"  reasons: {res.decision.reasons}")

    banner("5. HITL — HIGH-risk run_shell requires approval; auto-approver DENIES")
    card2 = make_card()
    card2.authority.max_risk = RiskLevel.MEDIUM  # run_shell is HIGH → escalate
    card2.allowed_tools = card2.allowed_tools + ["run_shell"]
    card2.denied_tools = [t for t in card2.denied_tools if t != "run_shell"]
    shell = CommandEnvelope.make(
        issuer_card_id=card2.id, tool="run_shell",
        args={"cmd": ["rm", "-rf", "."]}, rationale="cleanup",
        declared_risk=RiskLevel.LOW, expected_effect="remove files")
    res = kernel.runtime.submit(shell, card2)
    print(f"  policy verdict: {res.decision.verdict.value}")
    print(f"  risk re-scored: {res.decision.risk.value}")
    print(f"  reasons: {res.decision.reasons}")
    print(f"  executed: {res.ok}")
    if res.verifier.verifier == "hitl":
        print(f"  hitl outcome: DENIED — {res.verifier.reason}")
    elif res.ok:
        print("  outcome: ALLOWED and executed")
    else:
        print("  outcome: allowed by policy but failed in sandbox")
        print(f"  stderr: {res.observation.stderr[:80]}")

    banner("5b. TEST INTEGRITY — weakening test_calc.py is DENIED")
    weaken = CommandEnvelope.make(
        issuer_card_id=entity.card.id, tool="edit_file",
        args={"path": "test_calc.py",
              "find": "assert calc.add(2, 3) == 5",
              "replace": "assert True  # weakened"},
        rationale="attempt to weaken tests", declared_risk=RiskLevel.LOW,
        expected_effect="tests always pass")
    kernel.verifier.test_integrity.snapshot()
    res = kernel.runtime.submit(weaken, entity.card)
    print(f"  policy verdict: {res.decision.verdict.value}  executed: {res.ok}")
    print(f"  verifier: {res.verifier.verifier}  code: {res.verifier.code}")
    print(f"  reason: {res.verifier.reason}")
    if res.verifier.evidence.get("changed_files"):
        print(f"  changed_files: {res.verifier.evidence['changed_files']}")
    print(f"  test still strict: {'assert calc.add(2, 3) == 5' in kernel.sandbox.read_file('test_calc.py')}")
    if res.transition:
        print(f"  trace records violation: verified={res.transition.verifier_result.passed}")

    banner("6. MATURATION — repeat the task, compile + promote skill to REFLEX")
    kernel = build()
    entity = kernel.spawn(make_card())
    for run_no in range(1, 7):
        seed_repo(kernel)
        entity.state.__init__()
        entity._executed_commands = []
        rep = entity.run(Intent.make(GOAL))
        skills = kernel.skills.all()
        sk = skills[0] if skills else None
        if sk and sk.state in (CS.CANDIDATE, CS.REPEATED):
            kernel.skills.promote_tested(sk.id, passed=True)
        if sk:
            llm = rep["budget"]["llm_calls"]
            state = sk.state.value
            print(f"  run {run_no}: status={rep['status']:>9}  "
                  f"llm_calls={llm}  skill_state={state}  "
                  f"success_rate={sk.success_rate:.2f}")
        else:
            print(f"  run {run_no}: status={rep['status']}")

    banner("RESULT")
    skills = kernel.skills.all()
    if not skills:
        print("  No compiled skills — evidence gates were not satisfied.")
        print("  This is a safe governed outcome, not a runtime error.")
        print("  Escalation / human review is the correct governed path when")
        print("  the runtime cannot promote a skill without sufficient evidence.")
        print(f"\n  trace intact: {kernel.trace.verify_chain()[0]}  "
              f"memory: {kernel.memory.stats()}  skills: {kernel.skills.stats()}")
    else:
        sk = skills[0]
        print(f"  final skill: '{sk.name}'  state={sk.state.value}  "
              f"uses={sk.success_count}  rate={sk.success_rate:.2f}")
        print(f"  reflex reached: {sk.state == CS.REFLEX}")
        print("  -> once REFLEX, planning reuses the cached verified plan with NO")
        print("     model call, but STILL runs policy + sandbox + verify every time.")
        print(f"\n  trace intact: {kernel.trace.verify_chain()[0]}  "
              f"memory: {kernel.memory.stats()}  skills: {kernel.skills.stats()}")


if __name__ == "__main__":
    main()
