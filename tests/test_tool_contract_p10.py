"""P0.10 — Tool Contract & Schema Enforcement Seal tests."""

from __future__ import annotations

import pytest

from agentic_runtime import (
    AgentCard,
    AgentClass,
    AuthorityScope,
    ArgSpec,
    ContractValidationResult,
    RiskLevel,
    SideEffect,
    ToolContract,
    ToolInputValidator,
    ToolOutputValidator,
    build_runtime,
    default_contract_registry,
)
from agentic_runtime.core_types import (
    CommandEnvelope,
    Intent,
    ObservationEnvelope,
)
from tests.conftest import bounded_test_approver
from agentic_runtime.model_router import MockModelClient
from agentic_runtime.sandbox import UnsafeLocalSandbox


def _card(**kw):
    defaults = dict(
        name="Contract Agent",
        agent_class=AgentClass.EXECUTION,
        mission="contract tests",
        authority=AuthorityScope(write_paths=["src/", "."], read_paths=["*"],
                                 max_risk=RiskLevel.HIGH),
        allowed_tools=["read_file", "write_file", "edit_file", "run_shell",
                       "run_tests", "list_dir"],
        denied_tools=[],
    )
    defaults.update(kw)
    return AgentCard.make(**defaults)


def _kernel(tmp_path, *, plan=None):
    model_clients = {"balanced": [MockModelClient(scripted=plan)]} if plan else None
    return build_runtime(
        sandbox=UnsafeLocalSandbox(root=str(tmp_path)),
        approval_gate=bounded_test_approver(
            lambda r: r.command.tool in {"read_file", "write_file", "edit_file", "run_tests"},
        ),
        model_clients=model_clients,
    )


def _cmd(card, tool, args):
    return CommandEnvelope.make(
        issuer_card_id=card.id, tool=tool, args=args,
        rationale="t", declared_risk=RiskLevel.LOW, expected_effect="t")


def _violations(kernel):
    return [r for r in kernel.trace.replay()
            if r.get("kind") == "tool_contract_violation"]


# --------------------------------------------------------------------------- #
# Pure validator unit tests.
# --------------------------------------------------------------------------- #
@pytest.fixture
def reg():
    return default_contract_registry()


@pytest.fixture
def iv():
    return ToolInputValidator()


def test_missing_required_arg_denied(reg, iv):
    res = iv.validate(reg.get("write_file"), {"path": "src/a.py"})
    assert not res.ok
    assert res.code == "missing_required_arg"
    assert res.arg == "content"


def test_wrong_arg_type_denied(reg, iv):
    res = iv.validate(reg.get("write_file"), {"path": "src/a.py", "content": 123})
    assert not res.ok
    assert res.code == "wrong_arg_type"
    assert res.arg == "content"


def test_extra_arg_denied(reg, iv):
    res = iv.validate(reg.get("write_file"),
                      {"path": "src/a.py", "content": "x", "bogus": 1})
    assert not res.ok
    assert res.code == "unexpected_arg"
    assert res.arg == "bogus"


def test_oversized_arg_denied(reg, iv):
    big = "z" * 200_000
    res = iv.validate(reg.get("write_file"), {"path": "src/a.py", "content": big})
    assert not res.ok
    assert res.code == "oversized_arg"


def test_null_not_allowed_denied(reg, iv):
    res = iv.validate(reg.get("write_file"), {"path": None, "content": "x"})
    assert not res.ok
    assert res.code == "null_not_allowed"


def test_invalid_enum_value_denied():
    iv = ToolInputValidator()
    contract = ToolContract(
        name="set_mode", description="t",
        input_schema={"mode": ArgSpec("str", enum=["fast", "safe"])},
        side_effect_profile=frozenset({SideEffect.MEMORY_WRITE}),
    )
    res = iv.validate(contract, {"mode": "turbo"})
    assert not res.ok
    assert res.code == "invalid_enum_value"


def test_unknown_tool_and_no_contract(reg):
    registered = {"read_file", "ghost_tool"}
    # Not registered at all.
    _, gate = reg.resolve_for_execution("does_not_exist", registered)
    assert not gate.ok and gate.code == "unknown_tool"
    # Registered as a tool but has no contract.
    _, gate2 = reg.resolve_for_execution("ghost_tool", registered)
    assert not gate2.ok and gate2.code == "no_contract"


def test_list_str_type_and_size(reg, iv):
    ok = iv.validate(reg.get("run_shell"), {"cmd": ["ls", "-la"]})
    assert ok.ok
    bad = iv.validate(reg.get("run_shell"), {"cmd": ["ls", 5]})
    assert not bad.ok and bad.code == "wrong_arg_type"


def test_side_effect_profile_present_on_all_contracts(reg):
    for name in reg.names:
        c = reg.get(name)
        assert c.side_effect_profile, f"{name} missing side_effect_profile"
        for se in c.side_effect_profile:
            assert isinstance(se, SideEffect)


# --------------------------------------------------------------------------- #
# Output validator.
# --------------------------------------------------------------------------- #
def test_output_schema_violation(reg):
    ov = ToolOutputValidator()
    # write_file success must carry a 'path' artifact.
    bad = ObservationEnvelope.make("c1", success=True, artifacts={})
    res = ov.validate(reg.get("write_file"), bad)
    assert not res.ok
    assert res.code == "missing_output_artifact"


def test_output_artifact_wrong_type(reg):
    ov = ToolOutputValidator()
    bad = ObservationEnvelope.make("c1", success=True, artifacts={"path": 5})
    res = ov.validate(reg.get("write_file"), bad)
    assert not res.ok
    assert res.code == "output_artifact_wrong_type"


def test_output_wrong_scalar_type(reg):
    ov = ToolOutputValidator()
    bad = ObservationEnvelope.make("c1", success=True, artifacts={"path": "p"})
    bad.stdout = 123  # corrupt the envelope
    res = ov.validate(reg.get("write_file"), bad)
    assert not res.ok
    assert res.code == "output_wrong_type"


# --------------------------------------------------------------------------- #
# Runtime integration: violations are denied, traced, and never completed.
# --------------------------------------------------------------------------- #
def test_runtime_denies_missing_arg_and_traces(tmp_path):
    kernel = _kernel(tmp_path)
    card = _card()
    res = kernel.runtime.submit(_cmd(card, "write_file", {"path": "src/a.py"}), card)
    assert res.decision.verdict.value == "deny"
    assert res.verifier.code == "INPUT_CONTRACT_VIOLATION"
    assert not res.ok
    v = _violations(kernel)
    assert any(x["phase"] == "input" and x["code"] == "missing_required_arg"
               for x in v)


def test_runtime_denies_extra_arg(tmp_path):
    kernel = _kernel(tmp_path)
    card = _card()
    res = kernel.runtime.submit(
        _cmd(card, "write_file",
             {"path": "src/a.py", "content": "x", "evil": True}), card)
    assert res.decision.verdict.value == "deny"
    assert any(x["code"] == "unexpected_arg" for x in _violations(kernel))


def test_runtime_denies_unknown_tool(tmp_path):
    kernel = _kernel(tmp_path)
    card = _card(allowed_tools=["read_file", "ghost"])
    res = kernel.runtime.submit(_cmd(card, "ghost", {}), card)
    assert res.decision.verdict.value == "deny"
    assert res.verifier.code == "INPUT_CONTRACT_VIOLATION"
    assert any(x["code"] == "unknown_tool" for x in _violations(kernel))


def test_runtime_denies_tool_without_contract(tmp_path):
    from agentic_runtime.tools import ToolSpec
    kernel = _kernel(tmp_path)

    def handler(sb, args):
        return ObservationEnvelope.make("", success=True)

    kernel.tools.register(ToolSpec("uncontracted", "no contract", {}, handler))
    # Registered as a tool, but no contract exists -> must be denied.
    card = _card(allowed_tools=["uncontracted"])
    res = kernel.runtime.submit(_cmd(card, "uncontracted", {}), card)
    assert res.decision.verdict.value == "deny"
    assert any(x["code"] == "no_contract" for x in _violations(kernel))


def test_valid_tool_input_executes(tmp_path):
    kernel = _kernel(tmp_path)
    card = _card()
    res = kernel.runtime.submit(
        _cmd(card, "write_file", {"path": "src/a.py", "content": "hello\n"}), card)
    assert res.decision.verdict.value == "allow"
    assert res.ok
    assert res.verifier.passed
    assert kernel.sandbox.read_file("src/a.py") == "hello\n"


def test_output_violation_not_treated_as_success(tmp_path):
    """A successful tool whose output breaks its contract must not verify-pass."""
    from agentic_runtime.tool_contracts import (ToolContract, ArgSpec,
                                                OutputContract, SideEffect)
    kernel = _kernel(tmp_path)
    # Tighten list_dir's output contract to demand an artifact the real handler
    # never produces. The tool still succeeds, but its output is now invalid.
    kernel.runtime.contracts.register(ToolContract(
        name="list_dir", description="list",
        input_schema={"path": ArgSpec("str", required=False)},
        side_effect_profile=frozenset({SideEffect.FILESYSTEM_READ}),
        output_schema=OutputContract(required_artifacts={"never_present": "str"}),
    ))
    card = _card(allowed_tools=["list_dir"])
    res = kernel.runtime.submit(_cmd(card, "list_dir", {"path": "."}), card)
    assert not res.verifier.passed
    assert res.verifier.code == "OUTPUT_CONTRACT_VIOLATION"
    assert any(x["phase"] == "output" for x in _violations(kernel))


def test_contract_failure_does_not_report_completed(tmp_path):
    # Plan calls write_file with a missing 'content' arg -> contract denies it.
    plan = {"plan": [{"tool": "write_file", "args": {"path": "src/a.py"},
                      "reason": "write without content"}]}
    import json
    kernel = _kernel(tmp_path, plan={"do it": json.dumps(plan)})
    card = _card()
    entity = kernel.spawn(card)
    report = entity.run(Intent.make("do it"))
    assert report["status"] != "completed"
    assert report["reason_code"] == "tool_contract_violation"
    assert any(x["phase"] == "input" for x in _violations(kernel))


def test_valid_plan_still_completes(tmp_path):
    import json
    plan = {"plan": [{"tool": "write_file",
                      "args": {"path": "src/out.txt", "content": "hi"},
                      "reason": "create"}]}
    kernel = _kernel(tmp_path, plan={"make it": json.dumps(plan)})
    card = _card()
    entity = kernel.spawn(card)
    report = entity.run(Intent.make("make it"))
    assert report["status"] == "completed"


# --------------------------------------------------------------------------- #
# Side-effect profile feeds policy/risk.
# --------------------------------------------------------------------------- #
def test_side_effect_profile_feeds_risk(tmp_path):
    kernel = _kernel(tmp_path)
    # A card whose ceiling is LOW: run_shell (shell_execution -> HIGH) must
    # exceed the ceiling and escalate rather than silently allow.
    card = _card(allowed_tools=["run_shell"],
                 authority=AuthorityScope(write_paths=["."], read_paths=["*"],
                                          max_risk=RiskLevel.LOW))
    decision = kernel.policy.evaluate(_cmd(card, "run_shell", {"cmd": ["ls"]}), card)
    assert decision.risk is RiskLevel.HIGH
    assert decision.verdict.value in ("require_approval", "deny")


def test_contract_violation_chain_is_intact(tmp_path):
    kernel = _kernel(tmp_path)
    card = _card()
    kernel.runtime.submit(_cmd(card, "write_file", {"path": "src/a.py"}), card)
    ok, broken = kernel.trace.verify_chain()
    assert ok, f"chain broken at {broken}"
