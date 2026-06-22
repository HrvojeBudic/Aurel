"""P1.2.1 — Public entry smoke tests.

Verifies that all public entrypoints exit 0 and produce safe, honest output.
No API keys, no bubblewrap/docker, no real network required.

The env variable AGENTIC_SKIP_RECURSIVE_SMOKE=1 is set by _run() so that when
cli verify launches a nested pytest, this entire module is skipped to break the
recursion chain.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
PYTHONPATH = f"src{os.pathsep}."
_SKIP_RECURSIVE_SMOKE = "AGENTIC_SKIP_RECURSIVE_SMOKE"

# Skip entire module when running inside a nested pytest launched by _run().
pytestmark = pytest.mark.skipif(
    os.environ.get(_SKIP_RECURSIVE_SMOKE) == "1",
    reason="skipped in nested pytest to avoid recursive smoke test chain",
)


def _run(args: list[str], timeout: int = 60) -> subprocess.CompletedProcess:
    env = {
        **os.environ,
        "PYTHONPATH": PYTHONPATH,
        "AUREL_MODEL_PROVIDER": "mock",
        _SKIP_RECURSIVE_SMOKE: "1",
    }
    return subprocess.run(
        [sys.executable, *args],
        cwd=str(REPO_ROOT),
        env=env,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


# ---------------------------------------------------------------------------
# demo module
# ---------------------------------------------------------------------------

def test_demo_module_exits_zero():
    result = _run(["-m", "agentic_runtime.demo"], timeout=60)
    assert result.returncode == 0, (
        f"demo exited {result.returncode}\nstdout:\n{result.stdout[-800:]}\nstderr:\n{result.stderr[-400:]}"
    )


def test_demo_module_output_contains_safe_result():
    result = _run(["-m", "agentic_runtime.demo"], timeout=60)
    combined = result.stdout + result.stderr
    has_skill = "final skill:" in combined
    has_no_skill = "No compiled skills" in combined or "evidence gates" in combined
    assert has_skill or has_no_skill, (
        "demo output must contain either a compiled skill or a safe no-skill message.\n"
        f"stdout tail:\n{result.stdout[-600:]}"
    )


def test_demo_module_does_not_fake_skill():
    result = _run(["-m", "agentic_runtime.demo"], timeout=60)
    assert "IndexError" not in result.stdout
    assert "IndexError" not in result.stderr
    assert "list index out of range" not in result.stdout
    assert "list index out of range" not in result.stderr


# ---------------------------------------------------------------------------
# examples/demo.py
# ---------------------------------------------------------------------------

def test_examples_demo_exits_zero():
    result = _run(["examples/demo.py"], timeout=60)
    assert result.returncode == 0, (
        f"examples/demo.py exited {result.returncode}\nstdout:\n{result.stdout[-800:]}\nstderr:\n{result.stderr[-400:]}"
    )


def test_examples_demo_output_consistent():
    result = _run(["examples/demo.py"], timeout=60)
    combined = result.stdout + result.stderr
    has_skill = "final skill:" in combined
    has_no_skill = "No compiled skills" in combined or "evidence gates" in combined
    assert has_skill or has_no_skill, (
        "examples/demo.py output must contain either a compiled skill or a safe no-skill message.\n"
        f"stdout tail:\n{result.stdout[-600:]}"
    )


# ---------------------------------------------------------------------------
# CLI verify (runs pytest as a subprocess)
# The module-level pytestmark skips this entire file when inside a nested
# pytest launched by _run(), breaking the recursion chain automatically.
# ---------------------------------------------------------------------------

def test_cli_verify_exits_zero():
    result = _run(["-m", "agentic_runtime.cli", "verify"], timeout=180)
    assert result.returncode == 0, (
        f"cli verify exited {result.returncode}\nstdout:\n{result.stdout[-800:]}\nstderr:\n{result.stderr[-400:]}"
    )


# ---------------------------------------------------------------------------
# CLI alpha-seal
# ---------------------------------------------------------------------------

def test_cli_alpha_seal_skip_tests_exits_zero():
    """Smoke test: alpha-seal checks docs/compile/sandbox without re-running pytest.

    Using --skip-tests avoids nested pytest recursion when this test runs inside
    the main test suite.  The full ``alpha-seal --skip-coverage`` form is verified
    manually or in CI where it runs at the top level (not nested inside pytest).
    """
    result = _run(
        ["-m", "agentic_runtime.cli", "alpha-seal", "--skip-tests"],
        timeout=60,
    )
    assert result.returncode == 0, (
        f"cli alpha-seal --skip-tests exited {result.returncode}\n"
        f"stdout:\n{result.stdout[-800:]}\nstderr:\n{result.stderr[-400:]}"
    )
    assert "Alpha Seal" in result.stdout or "PASS" in result.stdout


# ---------------------------------------------------------------------------
# CLI status (fast sanity check)
# ---------------------------------------------------------------------------

def test_cli_status_exits_zero():
    result = _run(["-m", "agentic_runtime.cli", "status"], timeout=30)
    assert result.returncode == 0, (
        f"cli status exited {result.returncode}\nstderr:\n{result.stderr[-400:]}"
    )
