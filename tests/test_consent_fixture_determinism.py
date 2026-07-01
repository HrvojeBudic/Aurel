"""Prove tracked consent fixtures are not mutated by consent CLI tests."""
from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

import pytest

TRACKED_CONSENT_FIXTURES = (
    "consent_request.json",
    "consent_record.json",
    "consent_revoked.json",
    "delta_report.json",
    "delta_report_mismatch.json",
)


def _fixture_dir() -> Path:
    return Path(__file__).resolve().parent / "fixtures" / "consent"


def _fixture_hashes() -> dict[str, str]:
    base = _fixture_dir()
    return {
        name: hashlib.sha256(base.joinpath(name).read_bytes()).hexdigest()
        for name in TRACKED_CONSENT_FIXTURES
        if base.joinpath(name).exists()
    }


def test_consent_fixtures_are_not_mutated_by_cli_tests():
    before = _fixture_hashes()
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/identity/test_operator_consent_cli.py",
            "-q",
        ],
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    after = _fixture_hashes()
    assert before == after


def test_consent_fixture_generation_uses_tmp_path(tmp_path: Path):
    from tests.identity.test_operator_consent_cli import build_consent_cli_workspace

    workspace = tmp_path / "consent_cli"
    workspace.mkdir()
    paths = build_consent_cli_workspace(workspace)
    tracked = _fixture_dir().resolve()
    for path in paths.values():
        resolved = path.resolve()
        assert tracked not in resolved.parents
        assert not str(resolved).startswith(str(tracked))


def test_consent_fixture_timestamps_are_stable():
    request = (_fixture_dir() / "consent_request.json").read_text()
    record = (_fixture_dir() / "consent_record.json").read_text()
    revoked = (_fixture_dir() / "consent_revoked.json").read_text()
    assert "2026-06-25T09:51:28.848451+00:00" in request
    assert "2026-06-25T09:51:29.584891+00:00" in record
    assert "2026-06-25T09:51:33.948335+00:00" in revoked


def test_consent_fixture_hashes_remain_unchanged_after_focused_tests():
    before = _fixture_hashes()
    subprocess.run(
        [sys.executable, "-m", "pytest", __file__ + "::test_consent_fixtures_are_not_mutated_by_cli_tests", "-q"],
        check=True,
        timeout=120,
    )
    assert _fixture_hashes() == before
