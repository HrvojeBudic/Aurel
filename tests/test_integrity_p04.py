"""P0.4 test integrity verifier tests."""

from agentic_runtime import build_runtime
from agentic_runtime.core_types import RiskLevel
from tests.conftest import bounded_test_approver
from agentic_runtime.sandbox import UnsafeLocalSandbox
from agentic_runtime.test_integrity import (
    MUTATE_PROTECTED_TOOL,
    PROTECTED_FILE_MUTATION,
    FileIntegritySnapshot,
    ProtectedPathPolicy,
)
from tests.conftest import make_cmd


def test_source_mutation_allowed_when_authorized(kernel, card):
    card.authority.write_paths = ["src/"]
    kernel.sandbox.write_file("src/app.py", "v1\n")
    kernel.verifier.test_integrity.snapshot()
    cmd = make_cmd(card, "write_file", {
        "path": "src/app.py", "content": "v2\n"})
    res = kernel.runtime.submit(cmd, card)
    assert res.ok
    assert kernel.sandbox.read_file("src/app.py") == "v2\n"


def test_protected_test_mutation_denied_by_policy(kernel, card):
    card.authority.write_paths = ["tests/"]
    kernel.sandbox.write_file("tests/test_app.py", "assert True\n")
    cmd = make_cmd(card, "write_file", {
        "path": "tests/test_app.py", "content": "assert False\n"})
    res = kernel.runtime.submit(cmd, card)
    assert res.decision.verdict.value == "deny"
    assert MUTATE_PROTECTED_TOOL in res.decision.reasons[0]


def test_golden_fixture_mutation_denied(kernel, card):
    card.authority.write_paths = ["fixtures/golden/"]
    kernel.sandbox.write_file("fixtures/golden/out.json", '{"a":1}\n')
    kernel.verifier.test_integrity.snapshot()
    cmd = make_cmd(card, "write_file", {
        "path": "fixtures/golden/out.json", "content": '{"a":999}\n'})
    res = kernel.runtime.submit(cmd, card)
    assert not res.ok
    assert res.decision.verdict.value == "deny" or res.verifier.code == PROTECTED_FILE_MUTATION


def test_added_protected_test_detected(kernel, card):
    card.authority.write_paths = ["src/"]
    kernel.sandbox.write_file("src/app.py", "x\n")
    kernel.verifier.test_integrity.snapshot()
    ti = kernel.verifier.test_integrity
    before = ti.capture()
    kernel.sandbox.write_file("tests/test_new.py", "assert True\n")
    from agentic_runtime.core_types import ObservationEnvelope
    cmd = make_cmd(card, "read_file", {"path": "src/app.py"})
    obs = ObservationEnvelope.make(cmd.id, success=True)
    result = ti.verify(cmd, obs, card, before=before)
    assert not result.passed
    assert result.code == PROTECTED_FILE_MUTATION
    assert "tests/test_new.py" in result.evidence["added_files"]


def test_deleted_protected_test_detected(kernel, card):
    card.authority.write_paths = ["src/"]
    kernel.sandbox.write_file("test_del.py", "assert True\n")
    kernel.verifier.test_integrity.snapshot()
    before = kernel.verifier.test_integrity.capture()
    import os
    os.remove(f"{kernel.sandbox.root}/test_del.py")
    from agentic_runtime.core_types import ObservationEnvelope
    cmd = make_cmd(card, "read_file", {"path": "src/app.py"})
    obs = ObservationEnvelope.make(cmd.id, success=True)
    result = kernel.verifier.test_integrity.verify(cmd, obs, card, before=before)
    assert not result.passed
    assert "test_del.py" in result.evidence["deleted_files"]


def test_approved_protected_mutation_via_dedicated_pathway(tmp_path):
    from agentic_runtime import AgentCard, AgentClass, AuthorityScope

    kernel = build_runtime(
        sandbox=UnsafeLocalSandbox(root=str(tmp_path)),
        approval_gate=bounded_test_approver(
            lambda r: r.command.tool == MUTATE_PROTECTED_TOOL,
            allow_r4=True,
        ),
    )
    card = AgentCard.make(
        "t", AgentClass.EXECUTION, "m",
        AuthorityScope(
            write_paths=["tests/"], allow_protected_mutation=True,
            max_risk=RiskLevel.HIGH),
        allowed_tools=["mutate_protected_verification", "read_file"],
    )
    kernel.sandbox.write_file("tests/test_ok.py", "assert False\n")
    kernel.verifier.test_integrity.snapshot()
    cmd = make_cmd(card, MUTATE_PROTECTED_TOOL, {
        "path": "tests/test_ok.py",
        "content": "assert True\n",
        "approved": True,
    }, risk=RiskLevel.HIGH)
    res = kernel.runtime.submit(cmd, card)
    assert res.ok
    assert kernel.sandbox.read_file("tests/test_ok.py") == "assert True\n"


def test_source_fix_with_unchanged_tests_passes(kernel, card):
    card.authority.write_paths = ["src/", "tests/"]
    kernel.sandbox.write_file("src/app.py", "def f(): return 0\n")
    kernel.sandbox.write_file("tests/test_app.py", "from src.app import f\nassert f()==0\n")
    kernel.verifier.test_integrity.snapshot()
    cmd = make_cmd(card, "write_file", {
        "path": "src/app.py", "content": "def f(): return 1\n"})
    res = kernel.runtime.submit(cmd, card)
    assert res.ok
    assert res.verifier.code != PROTECTED_FILE_MUTATION


def test_integrity_violation_traced(tmp_path):
    from agentic_runtime import AgentCard, AgentClass, AuthorityScope, build_runtime

    kernel = build_runtime(
        sandbox=UnsafeLocalSandbox(root=str(tmp_path)),
        approval_gate=bounded_test_approver(
            lambda r: r.command.tool in ("run_tests", "run_shell"),
            allow_r4=True,
        ),
    )
    card = AgentCard.make(
        "t", AgentClass.EXECUTION, "m",
        AuthorityScope(write_paths=["."], max_risk=RiskLevel.HIGH),
        allowed_tools=["run_shell", "read_file"],
    )
    kernel.verifier.test_integrity.snapshot()
    cmd = make_cmd(card, "run_shell", {
        "cmd": ["python3", "-c", "open('test_x.py','w').write('x')"],
    }, risk=RiskLevel.HIGH)
    res = kernel.runtime.submit(cmd, card)
    assert not res.ok
    assert res.transition is not None
    assert res.transition.verifier_result.code == PROTECTED_FILE_MUTATION
    assert "test_x.py" in (
        res.transition.verifier_result.evidence.get("added_files", [])
    )


def test_protected_path_policy_patterns():
    pol = ProtectedPathPolicy()
    assert pol.is_protected("tests/unit/test_x.py")
    assert pol.is_protected("test_foo.py")
    assert pol.is_protected("pkg/foo_test.py")
    assert pol.is_protected("fixtures/golden/a.json")
    assert pol.is_protected("verifiers/check.py")
    assert pol.is_protected("evals/run.py")
    assert not pol.is_protected("src/app.py")


def test_snapshot_diff_structured(tmp_path):
    from agentic_runtime.sandbox import UnsafeLocalSandbox

    sbx = UnsafeLocalSandbox(root=str(tmp_path))
    sbx.write_file("tests/a.py", "1")
    pol = ProtectedPathPolicy()
    before = FileIntegritySnapshot.capture(sbx, pol)
    sbx.write_file("tests/a.py", "2")
    sbx.write_file("tests/b.py", "new")
    after = FileIntegritySnapshot.capture(sbx, pol)
    d = before.diff(after)
    assert "tests/a.py" in d["changed_files"]
    assert "tests/b.py" in d["added_files"]
