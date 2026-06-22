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


def test_valid_in_scope_write_allowed(write_kernel, card):
    card.authority.write_paths = ["src/"]
    write_kernel.sandbox.write_file("src/app.py", "version = 1\n")
    cmd = make_cmd(card, "write_file", {
        "path": "src/app.py", "content": "version = 2\n"})
    res = write_kernel.runtime.submit(cmd, card)
    assert res.decision.verdict.value == "allow"
    assert res.ok
    assert write_kernel.sandbox.read_file("src/app.py") == "version = 2\n"


def test_empty_read_paths_without_write_paths_denies_read(kernel):
    from agentic_runtime import AgentCard, AgentClass, AuthorityScope
    from agentic_runtime.core_types import PolicyVerdict

    card = AgentCard.make(
        "t", AgentClass.EXECUTION, "m",
        AuthorityScope(write_paths=[], read_paths=[], max_risk=RiskLevel.HIGH),
        allowed_tools=["read_file"],
    )
    cmd = make_cmd(card, "read_file", {"path": "any.txt"})
    decision = kernel.policy.evaluate(cmd, card)
    assert decision.verdict is PolicyVerdict.DENY


def test_run_tests_high_risk_without_hard_sandbox(kernel, card):
    cmd = make_cmd(card, "run_tests", {"test_file": "test_x.py"})
    decision = kernel.policy.evaluate(cmd, card)
    assert decision.risk is RiskLevel.HIGH
    assert not kernel.sandbox.is_hard_isolated


def test_issuer_card_mismatch_denied(kernel, card):
    """F-K01 regression: issuer on envelope must match submitting card."""
    from agentic_runtime import AgentCard, AgentClass, AuthorityScope
    from agentic_runtime.core_types import PolicyVerdict

    other = AgentCard.make(
        "other", AgentClass.EXECUTION, "m",
        AuthorityScope(write_paths=[], read_paths=["*"], max_risk=RiskLevel.LOW),
        allowed_tools=["read_file"],
    )
    cmd = make_cmd(other, "read_file", {"path": "README.md"})
    assert cmd.issuer_card_id == other.id
    assert cmd.issuer_card_id != card.id
    res = kernel.runtime.submit(cmd, card)
    assert res.decision.verdict is PolicyVerdict.DENY
    assert "ISSUER_MISMATCH" in res.observation.stderr
