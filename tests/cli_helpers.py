"""Shared helpers for subprocess-based CLI tests."""

from __future__ import annotations

import os
import subprocess
import sys
from collections.abc import Mapping
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CLI_TIMEOUT = 30


def run_cli(
    *args: str,
    timeout: int = DEFAULT_CLI_TIMEOUT,
    env: Mapping[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    run_env = os.environ.copy()
    run_env["PYTHONPATH"] = f"src{os.pathsep}."
    if env is not None:
        run_env.update(env)

    return subprocess.run(
        [sys.executable, "-m", "agentic_runtime.cli", *args],
        cwd=REPO_ROOT,
        env=run_env,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
