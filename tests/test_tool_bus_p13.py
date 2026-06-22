"""P0.13 — Tool Bus v1 tests."""

from __future__ import annotations

import pytest

from agentic_runtime import (
    AgentCard,
    AgentClass,
    AuthorityScope,
    RiskLevel,
    ToolRegistry,
    ToolRuntime,
    ToolSideEffectType,
    ToolSpec,
    build_runtime,
    default_contract_registry,
)
from agentic_runtime.core_types import CommandEnvelope, ObservationEnvelope
from tests.conftest import bounded_test_approver, requires_subprocess
from agentic_runtime.sandbox import UnsafeLocalSandbox


def _card(**kw):
    defaults = dict(
        name="Tool Bus Agent",
        agent_class=AgentClass.EXECUTION,
        mission="tool bus tests",
        authority=AuthorityScope(write_paths=["*"], read_paths=["*"],
                                 max_risk=RiskLevel.HIGH),
        allowed_tools=[
            "list_dir", "read_file", "search_text", "git_status", "git_diff",
            "write_file", "patch_file", "run_tests", "run_python", "run_shell",
        ],
        denied_tools=[],
    )
    defaults.update(kw)
    return AgentCard.make(**defaults)


def _cmd(card, tool, args):
    return CommandEnvelope.make(
        issuer_card_id=card.id,
        tool=tool,
        args=args,
        rationale="test",
        declared_risk=RiskLevel.LOW,
        expected_effect="test",
    )


def _kernel(tmp_path):
    return build_runtime(
        sandbox=UnsafeLocalSandbox(root=str(tmp_path)),
        approval_gate=bounded_test_approver(lambda r: True),
    )


def test_tool_registry_register_list_get_and_duplicate():
    reg = ToolRegistry()

    def handler(sb, args):
        return ObservationEnvelope.make("", success=True)

    spec = ToolSpec(
        "demo_tool",
        "demo",
        {},
        handler,
        side_effect_type=ToolSideEffectType.FILESYSTEM_READ,
    )
    reg.register(spec)
    assert reg.get("demo_tool") is spec
    assert [s.name for s in reg.list_tools()] == ["demo_tool"]
    with pytest.raises(ValueError):
        reg.register(spec)


def test_tool_bus_lists_builtin_tools(tmp_path):
    tools = ToolRuntime(UnsafeLocalSandbox(root=str(tmp_path)))
    names = {s.name for s in tools.list_tools()}
    assert {"list_dir", "read_file", "search_text", "git_status", "git_diff",
            "write_file", "patch_file", "run_tests", "run_python",
            "run_shell"}.issubset(names)
    assert tools.get("write_file").metadata.side_effect_type is ToolSideEffectType.FILESYSTEM_WRITE


def test_every_registered_builtin_has_contract(tmp_path):
    tools = ToolRuntime(UnsafeLocalSandbox(root=str(tmp_path)))
    contracts = default_contract_registry()
    missing = tools.registered - contracts.names
    assert not missing


def test_tool_bus_validates_input_when_contracts_bound(tmp_path):
    tools = ToolRuntime(UnsafeLocalSandbox(root=str(tmp_path)))
    tools.bind_contracts(default_contract_registry())
    res = tools.execute("write_file", {"path": "a.txt"})
    assert not res.success
    assert res.error.code == "missing_required_arg"


def test_unknown_tool_fails_structured(tmp_path):
    tools = ToolRuntime(UnsafeLocalSandbox(root=str(tmp_path)))
    res = tools.execute("missing_tool", {})
    assert not res.success
    assert res.error.code == "unknown_tool"


def test_read_file_inside_workspace(tmp_path):
    kernel = _kernel(tmp_path)
    kernel.sandbox.write_file("src/a.txt", "hello world")
    res = kernel.tools.execute("read_file", {"path": "src/a.txt", "max_bytes": 5})
    assert res.success
    assert res.artifacts["content"] == "hello"
    assert res.artifacts["truncated"] is True


def test_write_file_inside_workspace(tmp_path):
    kernel = _kernel(tmp_path)
    card = _card()
    res = kernel.runtime.submit(
        _cmd(card, "write_file",
             {"path": "src/a.txt", "content": "hello", "create_dirs": True}),
        card,
    )
    assert res.ok
    assert kernel.sandbox.read_file("src/a.txt") == "hello"


def test_path_traversal_rejected(tmp_path):
    kernel = _kernel(tmp_path)
    card = _card()
    res = kernel.runtime.submit(
        _cmd(card, "read_file", {"path": "../secret.txt"}),
        card,
    )
    assert not res.ok
    assert res.decision.verdict.value == "deny"


def test_write_outside_root_rejected(tmp_path):
    kernel = _kernel(tmp_path)
    card = _card()
    res = kernel.runtime.submit(
        _cmd(card, "write_file", {"path": "/etc/passwd", "content": "no"}),
        card,
    )
    assert not res.ok
    assert res.decision.verdict.value == "deny"


def test_search_text_returns_structured_matches(tmp_path):
    kernel = _kernel(tmp_path)
    kernel.sandbox.write_file("src/a.txt", "alpha\nneedle here\n")
    res = kernel.tools.execute(
        "search_text",
        {"root": "src", "query": "needle", "glob": "*.txt", "max_results": 5},
    )
    assert res.success
    assert res.artifacts["matches"][0]["line"] == 2


def test_patch_file_applies_simple_fixture(tmp_path):
    kernel = _kernel(tmp_path)
    kernel.sandbox.write_file("src/a.txt", "hello\nworld\n")
    patch = "--- a/src/a.txt\n+++ b/src/a.txt\n@@\n hello\n-world\n+there\n"
    card = _card()
    res = kernel.runtime.submit(
        _cmd(card, "patch_file", {"path": "src/a.txt", "patch": patch}),
        card,
    )
    assert res.ok
    assert kernel.sandbox.read_file("src/a.txt") == "hello\nthere\n"


def test_patch_file_rejects_invalid_patch_cleanly(tmp_path):
    kernel = _kernel(tmp_path)
    kernel.sandbox.write_file("src/a.txt", "hello\n")
    card = _card()
    res = kernel.runtime.submit(
        _cmd(card, "patch_file", {"path": "src/a.txt", "patch": "not a diff"}),
        card,
    )
    assert not res.ok
    assert "invalid patch" in res.observation.stderr


def test_run_tests_returns_structured_result(tmp_path):
    kernel = _kernel(tmp_path)
    kernel.sandbox.write_file("test_ok.py", "assert True\n")
    res = kernel.tools.execute(
        "run_tests",
        {"command": ["python3", "test_ok.py"], "timeout_seconds": 5},
    )
    assert "exit_code" in res.artifacts
    assert "duration_ms" in res.artifacts


def test_run_python_returns_structured_result(tmp_path):
    kernel = _kernel(tmp_path)
    res = kernel.tools.execute(
        "run_python",
        {"args": ["-c", "print('ok')"], "timeout_seconds": 5},
    )
    assert res.success
    assert res.artifacts["exit_code"] == 0
    assert "ok" in res.stdout


@requires_subprocess
def test_run_shell_timeout_is_enforced(tmp_path):
    kernel = _kernel(tmp_path)
    res = kernel.tools.execute(
        "run_shell",
        {"command": "sleep 2", "timeout_seconds": 1},
    )
    assert not res.success
    assert res.artifacts["timed_out"] is True


def test_execution_failure_returns_structured_result(tmp_path):
    kernel = _kernel(tmp_path)
    res = kernel.tools.execute(
        "run_python",
        {"args": ["-c", "import sys; sys.exit(2)"], "timeout_seconds": 5},
    )
    assert not res.success
    assert res.artifacts["exit_code"] == 2
    assert res.error is None


def test_runtime_invalid_tool_fails_safely(tmp_path):
    kernel = _kernel(tmp_path)
    card = _card(allowed_tools=["ghost"])
    res = kernel.runtime.submit(_cmd(card, "ghost", {}), card)
    assert res.decision.verdict.value == "deny"
    assert res.verifier.code == "INPUT_CONTRACT_VIOLATION"


def test_write_tool_still_uses_policy_sandbox_verifier(tmp_path):
    kernel = _kernel(tmp_path)
    card = _card(authority=AuthorityScope(write_paths=["src/"], read_paths=["*"],
                                          max_risk=RiskLevel.HIGH))
    ok = kernel.runtime.submit(
        _cmd(card, "write_file", {"path": "src/a.txt", "content": "x"}),
        card,
    )
    assert ok.ok
    assert ok.verifier.verifier == "write_file_verifier"

    denied = kernel.runtime.submit(
        _cmd(card, "write_file", {"path": "other/a.txt", "content": "x"}),
        card,
    )
    assert denied.decision.verdict.value == "deny"
