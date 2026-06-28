"""Focused tests for P1.9-D integration tail pack."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import fields
from pathlib import Path

sys.path.insert(0, "src")

from agentic_runtime.output_passport import (
    OUTPUT_PASSPORT_P1_9_D_CHECKPOINT_IDS,
    OUTPUT_PASSPORT_P1_9_D_PACK_TASK_ID,
    P19ExitSealDecision,
    P19LiveDemoStatus,
    P19P2ReadinessStatus,
    OutputPassportAPIRuntimeStatus,
    OutputPassportEventRuntimeStatus,
    OutputPassportProjectionStatus,
    OutputPassportSideEffectProof,
    OutputPassportTruthLabel,
    P19DIntegrationTailSideEffectProof,
    assert_seal_honest,
    build_output_passport_api_contract,
    build_output_passport_cli_binding_contract,
    build_output_passport_cli_binding_status,
    build_output_passport_docs_state_report_update,
    build_output_passport_event_contract,
    build_output_passport_projection_contract,
    build_output_passport_projection_payload,
    build_output_passport_tui_binding_status,
    build_p1_9_a_passport_pack_result,
    build_p1_9_b_read_model_test_harness_binding_pack_result,
    build_p1_9_c_truth_boundary_failure_readiness_pack_result,
    build_p1_9_d_integration_tail_pack_result,
    build_p1_9_exit_seal_checklist,
    build_p1_9_live_integration_demo_result,
    handle_output_passport_cli_inspect,
    run_p1_9_exit_seal_checklist,
    serialize_output_passport_projection_payload,
    serialize_p1_9_exit_seal_result,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def assert_all_foundation_side_effects_false(proof: OutputPassportSideEffectProof) -> None:
    for side_effect_field in fields(proof):
        assert getattr(proof, side_effect_field.name) is False


def assert_all_p19d_side_effects_false(proof: P19DIntegrationTailSideEffectProof) -> None:
    for side_effect_field in fields(proof):
        assert getattr(proof, side_effect_field.name) is False


def test_p1_9_abc_dependency_imports():
    assert build_p1_9_a_passport_pack_result().pack_id == "P1.9-A"
    assert build_p1_9_b_read_model_test_harness_binding_pack_result().pack_id == "P1.9-B"
    assert build_p1_9_c_truth_boundary_failure_readiness_pack_result().pack_id == "P1.9-C"


def test_p1_9_27_projection_payload_serializes():
    payload = build_output_passport_projection_payload()
    assert payload.projection_status is OutputPassportProjectionStatus.PROJECTION_ONLY
    assert payload.side_effects.runtime_mutated is False
    json.loads(serialize_output_passport_projection_payload(payload))


def test_p1_9_27_projection_includes_truth_labels_and_read_model():
    payload = build_output_passport_projection_payload()
    assert OutputPassportTruthLabel.CONTRACT_ONLY in payload.truth_labels
    assert payload.passport_read_model_ref
    assert payload.trace_truth_boundary_summary
    assert payload.failure_unavailable_summary


def test_p1_9_27_api_contract_not_live_runtime():
    api = build_output_passport_api_contract()
    assert api.runtime_status is OutputPassportAPIRuntimeStatus.UNAVAILABLE_API_RUNTIME
    assert "UNAVAILABLE_API_RUNTIME" in api.unavailable_reason
    assert api.side_effects.runtime_mutated is False


def test_p1_9_27_event_contract_not_emitted():
    event = build_output_passport_event_contract()
    assert event.runtime_status is OutputPassportEventRuntimeStatus.UNAVAILABLE_EVENT_RUNTIME
    assert event.side_effects.runtime_mutated is False
    assert "UNAVAILABLE_EVENT_RUNTIME" in event.unavailable_reason


def test_p1_9_27_projection_contract_bundle():
    contract = build_output_passport_projection_contract()
    assert contract.projection_status is OutputPassportProjectionStatus.PROJECTION_ONLY
    assert contract.api_contract.runtime_status is OutputPassportAPIRuntimeStatus.UNAVAILABLE_API_RUNTIME
    assert contract.event_contract.runtime_status is OutputPassportEventRuntimeStatus.UNAVAILABLE_EVENT_RUNTIME
    assert_all_foundation_side_effects_false(contract.side_effects)


def test_p1_9_28_cli_binding_contract_serializes():
    contract = build_output_passport_cli_binding_contract()
    assert contract.read_only is True
    assert contract.dev_fixture_supported is True
    assert_all_foundation_side_effects_false(contract.side_effects)
    json.loads(json.dumps(contract.to_canonical_dict()))


def test_p1_9_28_cli_inspect_read_only_no_authority():
    result = handle_output_passport_cli_inspect(dev_fixture=True)
    assert result["read_only"] is True
    assert result["authority_granted"] is False
    assert result["approval_created"] is False
    assert result["projection_payload_hash"]


def test_p1_9_28_tui_unavailable_reason():
    tui = build_output_passport_tui_binding_status()
    assert "UNAVAILABLE_TUI_BINDING" in tui.unavailable_reason


def test_p1_9_28_cli_binding_available():
    cli = build_output_passport_cli_binding_status()
    assert cli.status.value == "CLI_READ_ONLY"
    assert cli.inspect_command.read_only is True


def test_p1_9_29_docs_state_report_update():
    update = build_output_passport_docs_state_report_update(repo_root=REPO_ROOT)
    assert update.report_chain
    assert update.state_sync_summary.roadmap_mirror_updated is True
    indexed = [e for e in update.report_entries if e.indexed]
    assert len(indexed) >= 3
    json.loads(json.dumps(update.to_canonical_dict()))


def test_p1_9_30_live_demo_honest_dev_fixture():
    demo = build_p1_9_live_integration_demo_result()
    assert demo.demo_status is P19LiveDemoStatus.DEV_FIXTURE
    assert demo.truth_label is OutputPassportTruthLabel.DEV_FIXTURE
    assert demo.truth_label is not OutputPassportTruthLabel.LIVE
    assert demo.unavailable_reason
    assert_all_foundation_side_effects_false(demo.side_effects)


def test_p1_9_30_seal_checklist_passes_without_fake_labels():
    checklist = build_p1_9_exit_seal_checklist(repo_root=REPO_ROOT)
    assert checklist.failed_count == 0
    assert checklist.fake_live_detected is False
    assert checklist.fake_trace_verified_detected is False
    assert checklist.fake_exit_sealed_detected is False


def test_p1_9_30_seal_checklist_fails_fake_live():
    checklist = build_p1_9_exit_seal_checklist(
        repo_root=REPO_ROOT,
        truth_labels=[OutputPassportTruthLabel.LIVE],
    )
    assert checklist.fake_live_detected is True
    assert checklist.failed_count > 0


def test_p1_9_30_seal_checklist_fails_fake_trace_verified():
    checklist = build_p1_9_exit_seal_checklist(
        repo_root=REPO_ROOT,
        truth_labels=[OutputPassportTruthLabel.TRACE_VERIFIED],
    )
    assert checklist.fake_trace_verified_detected is True


def test_p1_9_30_seal_checklist_fails_fake_exit_sealed():
    checklist = build_p1_9_exit_seal_checklist(
        repo_root=REPO_ROOT,
        truth_labels=[OutputPassportTruthLabel.EXIT_SEALED],
    )
    assert checklist.fake_exit_sealed_detected is True


def test_p1_9_30_seal_not_sealed_blocks_p2():
    seal = run_p1_9_exit_seal_checklist(repo_root=REPO_ROOT)
    assert seal.decision is not P19ExitSealDecision.SEALED
    assert seal.p2_readiness_blocked is True
    assert_seal_honest(seal)
    json.loads(serialize_p1_9_exit_seal_result(seal))


def test_p1_9_30_seal_checklist_fails_missing_reports():
    missing_root = REPO_ROOT / "nonexistent_repo_path_for_test"
    checklist = build_p1_9_exit_seal_checklist(repo_root=missing_root)
    assert checklist.failed_count > 0


def test_p1_9_d_pack_result_coverage():
    result = build_p1_9_d_integration_tail_pack_result(repo_root=REPO_ROOT)
    assert result.pack_id == OUTPUT_PASSPORT_P1_9_D_PACK_TASK_ID
    assert result.covered_checkpoints == OUTPUT_PASSPORT_P1_9_D_CHECKPOINT_IDS
    for checkpoint_id in OUTPUT_PASSPORT_P1_9_D_CHECKPOINT_IDS:
        assert checkpoint_id in result.checkpoint_statuses
    assert result.p2_readiness_status is P19P2ReadinessStatus.NOT_READY_FOR_P2
    assert_all_p19d_side_effects_false(result.side_effect_proof)


def test_p1_9_d_pack_no_fake_live_labels():
    result = build_p1_9_d_integration_tail_pack_result(repo_root=REPO_ROOT)
    forbidden = {
        OutputPassportTruthLabel.LIVE,
        OutputPassportTruthLabel.TRACE_VERIFIED,
        OutputPassportTruthLabel.EXIT_SEALED,
    }
    assert forbidden.isdisjoint(set(result.truth_labels))


def test_cli_module_inspect_subprocess():
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "agentic_runtime.cli",
            "output-passport",
            "inspect",
            "--dev-fixture",
            "--json",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": "src"},
    )
    assert proc.returncode == 0
    payload = json.loads(proc.stdout)
    assert payload["read_only"] is True
