"""P0.20 — First Real Coding Agent Demo seal tests.

Prove the governed coding-agent loop end-to-end and the honesty of evidence
generation. These tests run through the real RepositoryAgentLoop path.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from agentic_runtime.demo_harness import (
    BUGGY_CALCULATOR,
    BUGGY_CALCULATOR_FILES,
    DemoHarness,
    DemoHarnessRequest,
    DemoRepoFactory,
    build_sandbox_summary,
    run_tests,
    write_evidence,
)


EVIDENCE_FILES = {
    "demo_run_report.json",
    "trace_summary.json",
    "approval_summary.json",
    "sandbox_summary.json",
    "praxis_summary.json",
    "final_diff.patch",
    "test_output_before.txt",
    "test_output_after.txt",
}


@pytest.fixture
def applied_report(tmp_path):
    return DemoHarness().run(DemoHarnessRequest(
        scenario_id="buggy_calculator",
        repo_parent=tmp_path,
        apply=True,
    ))


def test_initial_test_fails_before_patch(tmp_path):
    repo = DemoRepoFactory().create(BUGGY_CALCULATOR, tmp_path)
    result = run_tests(repo, BUGGY_CALCULATOR.test_command)
    assert not result.passed
    assert result.exit_code != 0


def test_demo_succeeds_end_to_end(applied_report):
    assert applied_report.initial_test_result.passed is False
    assert applied_report.final_test_result is not None
    assert applied_report.final_test_result.passed is True
    assert applied_report.final_status == "succeeded"


def test_plan_recorded_before_patch(applied_report):
    assert applied_report.agent_plan_summary
    assert applied_report.plan_verification["plan_recorded"] is True
    assert applied_report.files_inspected


def test_changed_files_bounded(applied_report):
    assert len(applied_report.files_changed) <= BUGGY_CALCULATOR.max_files_changed
    assert applied_report.files_changed == ["calculator.py"]
    assert applied_report.plan_verification["files_changed_within_bounds"] is True


def test_test_file_not_modified(applied_report):
    repo = Path(applied_report.repo_path)
    assert (repo / "test_calculator.py").read_text(encoding="utf-8") == (
        BUGGY_CALCULATOR_FILES["test_calculator.py"]
    )
    assert applied_report.plan_verification["test_file_unchanged"] is True


def test_approval_summary_present(applied_report):
    assert applied_report.approval_summary, "approval receipts must be recorded"
    assert all("risk_class" in entry for entry in applied_report.approval_summary)
    # At least one entry is a decided receipt (auto-approved patch within envelope)
    receipts = [e for e in applied_report.approval_summary if "decision" in e]
    assert receipts, "an approval receipt with a decision must be recorded"
    assert receipts[0]["decision"] in {"auto_approved", "approved"}


def test_sandbox_summary_present(applied_report):
    summary = build_sandbox_summary(applied_report, BUGGY_CALCULATOR)
    assert summary["sandbox_profile"] == "restricted_local"
    assert summary["network_allowed"] is False
    assert summary["secrets_allowed"] is False
    assert summary["violations"] == []


def test_praxis_summary_present(applied_report):
    assert applied_report.praxis_summary, "praxis report must be available"
    assert "experience_id" in applied_report.praxis_summary
    # No auto-promotion to canon/verified truth
    assert any("not verified truth" in lim.lower()
               for lim in applied_report.praxis_summary.get("limitations", []))


def test_trace_summary_present(applied_report):
    assert applied_report.trace_summary
    assert applied_report.trace_summary["event_count"] > 0
    assert "approval_receipt" in applied_report.trace_summary["kinds"]


def test_evidence_files_generated(tmp_path, applied_report):
    evidence_dir = tmp_path / "evidence"
    written = write_evidence(evidence_dir, applied_report, BUGGY_CALCULATOR)
    assert set(written) == EVIDENCE_FILES
    for name in EVIDENCE_FILES:
        assert (evidence_dir / name).is_file()

    diff = (evidence_dir / "final_diff.patch").read_text(encoding="utf-8")
    assert "return a + b" in diff
    assert "return a - b" in diff

    demo_run = json.loads((evidence_dir / "demo_run_report.json").read_text(encoding="utf-8"))
    assert demo_run["final_status"] == "succeeded"
    assert demo_run["initial_test_result"]["passed"] is False
    assert demo_run["final_test_result"]["passed"] is True
    # repo path is sanitized to a repo id, not an absolute host path
    assert "/" not in demo_run["repo_id"]


def test_no_fake_success_when_initial_test_passes(tmp_path):
    repo = DemoRepoFactory().create(BUGGY_CALCULATOR, tmp_path)
    (repo / "calculator.py").write_text("def add(a, b):\n    return a + b\n", encoding="utf-8")

    class PreFixedFactory(DemoRepoFactory):
        def create(self, scenario, parent):
            return repo

    report = DemoHarness(factory=PreFixedFactory()).run(DemoHarnessRequest(
        scenario_id="buggy_calculator",
        repo_parent=tmp_path,
        apply=True,
    ))
    assert report.final_status == "harness_failed"
    assert report.final_status != "succeeded"


def test_sandbox_summary_evidence_denies_network_and_secrets(applied_report):
    summary = build_sandbox_summary(applied_report, BUGGY_CALCULATOR)
    assert summary["network_allowed"] is False
    assert summary["secrets_allowed"] is False
    assert summary["unsafe"] is False
