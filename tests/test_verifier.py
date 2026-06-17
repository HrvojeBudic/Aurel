"""Verifier and test-integrity tests."""

from agentic_runtime.core_types import RiskLevel
from agentic_runtime.test_integrity import MUTATE_PROTECTED_TOOL, PROTECTED_FILE_MUTATION
from tests.conftest import make_cmd


def test_test_weakening_denied(kernel, card):
    card.authority.write_paths = ["src/", "test_app.py"]
    kernel.sandbox.write_file("test_app.py", "assert calc.add(1,1)==2\n")
    kernel.verifier.test_integrity.snapshot()
    cmd = make_cmd(card, "edit_file", {
        "path": "test_app.py",
        "find": "assert calc.add(1,1)==2",
        "replace": "assert True  # weakened",
    }, risk=RiskLevel.MEDIUM)
    res = kernel.runtime.submit(cmd, card)
    assert not res.ok
    assert (
        res.decision.verdict.value == "deny"
        or res.verifier.code == PROTECTED_FILE_MUTATION
        or "protected" in res.verifier.reason.lower()
    )
    assert kernel.sandbox.read_file("test_app.py") == "assert calc.add(1,1)==2\n"


def test_run_tests_escape_attempt_fails(kernel, card):
    card.authority.write_paths = ["src/", "test_escape.py"]
    kernel.sandbox.write_file("src/app.py", "x = 1\n")
    malicious_test = (
        "open('escaped.txt','w').write('pwned')\n"
        "print('ok')\n"
    )
    kernel.sandbox.write_file("test_escape.py", malicious_test)
    kernel.verifier.test_integrity.snapshot()
    cmd = make_cmd(card, "run_tests", {"test_file": "test_escape.py"})
    res = kernel.runtime.submit(cmd, card)
    assert not res.verifier.passed
    assert "unexpected" in res.verifier.reason.lower() or not res.ok


def test_failed_verifier_causes_rollback(kernel, card):
    card.authority.write_paths = ["src/", "test_rb.py"]
    kernel.sandbox.write_file("test_rb.py", "assert True\n")
    kernel.verifier.test_integrity.snapshot()
    # Policy denies ordinary write to protected test — use src write that triggers
    # integrity via run_tests adding file instead; use mutate attempt via edit denied at policy
    cmd = make_cmd(card, "edit_file", {
        "path": "test_rb.py", "find": "assert True", "replace": "assert False"})
    res = kernel.runtime.submit(cmd, card)
    assert not res.ok
    assert kernel.sandbox.read_file("test_rb.py") == "assert True\n"
