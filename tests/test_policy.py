"""Policy engine security tests."""

from agentic_runtime.core_types import RiskLevel
from tests.conftest import make_cmd


def test_out_of_scope_write_denied(kernel, card):
    card.authority.write_paths = ["src/"]
    kernel.sandbox.write_file("src/app.py", "x")
    cmd = make_cmd(card, "edit_file", {
        "path": "/etc/passwd", "find": "a", "replace": "b"})
    res = kernel.runtime.submit(cmd, card)
    assert res.decision.verdict.value == "deny"
    assert any("absolute" in r or "resolution" in r for r in res.decision.reasons)


def test_path_traversal_write_denied(kernel, card):
    kernel.sandbox.write_file("src/app.py", "x")
    kernel.sandbox.write_file("outside.py", "secret")
    cmd = make_cmd(card, "edit_file", {
        "path": "src/../outside.py", "find": "secret", "replace": "pwned"})
    res = kernel.runtime.submit(cmd, card)
    assert res.decision.verdict.value == "deny"
    assert any(
        "outside.py" in r or "authority" in r or "traversal" in r or "resolution" in r
        for r in res.decision.reasons
    )


def test_valid_in_scope_write_allowed(kernel, card):
    card.authority.write_paths = ["src/"]
    kernel.sandbox.write_file("src/app.py", "version = 1\n")
    cmd = make_cmd(card, "write_file", {
        "path": "src/app.py", "content": "version = 2\n"})
    res = kernel.runtime.submit(cmd, card)
    assert res.decision.verdict.value == "allow"
    assert res.ok
    assert kernel.sandbox.read_file("src/app.py") == "version = 2\n"


def test_run_tests_high_risk_without_hard_sandbox(kernel, card):
    cmd = make_cmd(card, "run_tests", {"test_file": "test_x.py"})
    decision = kernel.policy.evaluate(cmd, card)
    assert decision.risk is RiskLevel.HIGH
    assert not kernel.sandbox.is_hard_isolated
