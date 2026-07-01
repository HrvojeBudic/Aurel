"""Evidence reference integrity tests for P2.9-A Shell Exit Seal foundation."""

from __future__ import annotations

import subprocess
from pathlib import Path

from agentic_runtime.aurel_shell.shell_exit_seal_foundation import (
    P2_9_A_NEXT_PACK,
    P29ASideEffectProof,
    _PRIOR_SECTION_EVIDENCE_SPECS,
    build_p2_9_a_shell_exit_seal_foundation_result,
)

REPO_ROOT = Path(__file__).resolve().parents[2]

_UNKNOWN_COMMIT_MARKERS = frozenset({"UNKNOWN", "UNAVAILABLE", "AMBIGUOUS"})

_EXPECTED_COMMIT_SUBJECT_TOKENS: dict[str, tuple[str, ...]] = {
    "P2.0": ("P2.0", "shell"),
    "P2.1": ("P2.1", "topbar"),
    "P2.2": ("P2.2", "local", "navigation"),
    "P2.3": ("P2.3", "workspace", "window"),
    "P2.4": ("P2.4", "command", "palette"),
    "P2.5": ("P2.5", "handoff"),
    "P2.6": ("P2.6", "projection"),
    "P2.7": ("P2.7", "binding"),
    "P2.8": ("P2.8", "shell", "state"),
}


def _git(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ("git", "-C", str(REPO_ROOT), *args),
        check=False,
        text=True,
        capture_output=True,
    )


def _active_prior_section_refs() -> tuple[tuple[str, str, str, str, str, str, str], ...]:
    return _PRIOR_SECTION_EVIDENCE_SPECS


def _stale_prior_section_test_paths() -> tuple[str, ...]:
    prefix = "tests/aurel_shell/test_"
    suffix = ".py"
    names = (
        "topbar_integration_tail",
        "local_navigation_integration_tail",
        "workspace_window_section_projection",
        "global_command_section_projection",
        "cross_surface_handoff_section_projection",
        "surface_projection_section_seal",
    )
    return tuple(f"{prefix}{name}{suffix}" for name in names)


def test_p2_9_a_prior_section_test_refs_exist() -> None:
    for spec in _active_prior_section_refs():
        test_ref = spec[5]
        assert (REPO_ROOT / test_ref).is_file(), test_ref


def test_p2_9_a_report_refs_exist_or_are_marked_unavailable() -> None:
    for spec in _active_prior_section_refs():
        section_id, _name, _pack, report_ref, _commit_ref, _test_ref, _status = spec
        if report_ref in _UNKNOWN_COMMIT_MARKERS:
            continue
        assert (REPO_ROOT / report_ref).is_file(), section_id


def test_p2_9_a_commit_refs_resolve_or_are_marked_ambiguous() -> None:
    for spec in _active_prior_section_refs():
        section_id, _name, _pack, _report_ref, commit_ref, _test_ref, _status = spec
        if commit_ref in _UNKNOWN_COMMIT_MARKERS:
            continue
        resolved = _git("cat-file", "-e", f"{commit_ref}^{{commit}}")
        assert resolved.returncode == 0, (section_id, commit_ref, resolved.stderr)

        subject = _git("show", "-s", "--format=%s", commit_ref)
        assert subject.returncode == 0, (section_id, commit_ref, subject.stderr)
        lower_subject = subject.stdout.strip().lower()
        for token in _EXPECTED_COMMIT_SUBJECT_TOKENS[section_id]:
            assert token.lower() in lower_subject, (section_id, commit_ref, lower_subject)


def test_p2_9_a_no_stale_prior_section_test_paths_remain() -> None:
    active_refs = "\n".join(spec[5] for spec in _active_prior_section_refs())
    source = (REPO_ROOT / "src/agentic_runtime/aurel_shell/shell_exit_seal_foundation.py").read_text()
    for stale_ref in _stale_prior_section_test_paths():
        assert stale_ref not in active_refs
        assert stale_ref not in source


def test_p2_9_a_repair_does_not_claim_trace_verified() -> None:
    result = build_p2_9_a_shell_exit_seal_foundation_result()
    assert result.claims_trace_verified is False
    assert result.foundation_result.claims_trace_verified is False
    assert result.prior_section_evidence_intake.claims_trace_verified is False
    assert result.side_effect_proof.trace_verified_claimed is False


def test_p2_9_a_repair_does_not_claim_live() -> None:
    result = build_p2_9_a_shell_exit_seal_foundation_result()
    assert result.claims_live is False
    assert result.foundation_result.claims_live is False
    assert result.no_live_runtime_boundary.live_shell_runtime_created is False
    assert result.side_effect_proof.live_claimed is False
    assert result.side_effect_proof.live_shell_runtime_created is False


def test_p2_9_a_repair_does_not_claim_release_or_product_readiness() -> None:
    result = build_p2_9_a_shell_exit_seal_foundation_result()
    assert result.claims_release_scope is False
    assert result.claims_product_behavior is False
    assert result.claims_product_readiness is False
    assert result.foundation_result.is_release_seal is False
    assert result.foundation_result.claims_product_readiness is False
    assert result.no_release_seal_boundary.release_seal_created is False
    assert result.no_product_readiness_boundary.product_readiness_claimed is False
    assert result.side_effect_proof.release_seal_created is False
    assert result.side_effect_proof.product_readiness_claimed is False


def test_p2_9_a_repair_does_not_start_p2_9_b() -> None:
    result = build_p2_9_a_shell_exit_seal_foundation_result()
    handoff = result.p2_9_b_handoff_contract
    assert result.next_pack == P2_9_A_NEXT_PACK == "P2.9-B"
    assert result.starts_future_work is False
    assert handoff.handoff_to_pack == "P2.9-B"
    assert handoff.is_p2_9_b_implementation is False
    assert handoff.starts_p2_9_b is False
    assert result.side_effect_proof.p2_9_b_started is False


def test_p2_9_a_repair_does_not_claim_p2_or_shell_complete() -> None:
    result = build_p2_9_a_shell_exit_seal_foundation_result()
    assert result.claims_p2_complete is False
    assert result.claims_shell_complete is False
    assert result.foundation_result.claims_p2_complete is False
    assert result.foundation_result.claims_shell_complete is False
    assert result.side_effect_proof.p2_complete_claimed is False
    assert result.side_effect_proof.shell_complete_claimed is False


def test_p2_9_a_repair_does_not_change_runtime_policy_trace_memory_or_storage() -> None:
    proof = build_p2_9_a_shell_exit_seal_foundation_result().side_effect_proof
    assert isinstance(proof, P29ASideEffectProof)
    assert proof.runtime_dispatch_created is False
    assert proof.command_execution_created is False
    assert proof.permission_enforcement_created is False
    assert proof.custos_decisioning_created is False
    assert proof.trace_written is False
    assert proof.memory_written is False
    assert proof.storage_written is False
