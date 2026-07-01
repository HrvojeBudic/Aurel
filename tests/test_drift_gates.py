"""Focused tests for P1.ENF-F-A governance drift gates."""
from __future__ import annotations

from agentic_runtime.drift_gates import (
    ClaimDriftGateInput,
    ClaimDriftGateStatus,
    ContractEnforcementMismatchGate,
    ContractMismatchGateInput,
    ContractMismatchGateStatus,
    EnforcementBridgePresence,
    P1ENFFASideEffectProof,
    ReportCodeClaimDriftGate,
    ShadowMigrationGateInput,
    ShadowMigrationGateStatus,
    ShadowStillActiveGate,
    UnknownEntrypointRiskGate,
    UnknownEntrypointRiskGateInput,
    UnknownEntrypointRiskGateStatus,
    evaluate_report_code_claim_drift_gate,
    evaluate_shadow_still_active_gate,
    evaluate_unknown_entrypoint_risk_gate,
)
from agentic_runtime.entrypoint_governance_guard import (
    EntrypointBypassGuardResult,
    EntrypointBypassRisk,
    EntrypointGovernanceClassification,
    GovernedDelegationRequirement,
)
from agentic_runtime.governance_enforcement import GovernanceEnforcementMode


def test_shadow_gate_allows_shadow_compatibility_mode_without_overclaim():
    result = evaluate_shadow_still_active_gate(
        ShadowMigrationGateInput(
            enforcement_bridge=EnforcementBridgePresence(
                policy_submit_influence_present=True,
                identity_submit_context_present=True,
                entrypoint_guard_present=True,
                governance_enforcement_modes_present=True,
            ),
            active_mode=GovernanceEnforcementMode.SHADOW_ONLY,
            claims_enforcement_active=False,
            shadow_compatibility_allowed=True,
        )
    )
    assert (
        result.status
        is ShadowMigrationGateStatus.WARN_SHADOW_COMPATIBILITY_MODE_PRESENT
    )


def test_shadow_gate_blocks_passive_artifact_only_enforcement_claim():
    result = ShadowStillActiveGate().evaluate(
        ShadowMigrationGateInput(
            claims_enforcement_active=True,
            passive_artifact_only=True,
            enforcement_bridge=EnforcementBridgePresence(
                policy_submit_influence_present=True,
                identity_submit_context_present=True,
                entrypoint_guard_present=True,
                governance_enforcement_modes_present=True,
            ),
        )
    )
    assert result.status is ShadowMigrationGateStatus.FAIL_PASSIVE_ARTIFACT_ONLY


def test_contract_gate_passes_honest_contract_only_unavailable_binding():
    result = ContractEnforcementMismatchGate().evaluate(
        ContractMismatchGateInput(
            contract_only=True,
            side_effects_all_false=True,
            binding_unavailable=True,
            unavailable_reason_present=True,
            module_name="agentic_runtime.aurel_shell.shell_binding_foundation",
        )
    )
    assert result.status is ContractMismatchGateStatus.WARN_BINDING_UNAVAILABLE


def test_contract_gate_blocks_fake_live_claim():
    result = ContractEnforcementMismatchGate().evaluate(
        ContractMismatchGateInput(
            contract_only=True,
            claims_live=True,
            live_evidence_present=False,
            module_name="agentic_runtime.aurel_shell.example",
        )
    )
    assert result.status is ContractMismatchGateStatus.FAIL_FAKE_LIVE_CLAIM


def test_contract_gate_blocks_fake_trace_verified_claim():
    result = ContractEnforcementMismatchGate().evaluate(
        ContractMismatchGateInput(
            contract_only=True,
            claims_trace_verified=True,
            trace_verification_present=False,
            module_name="agentic_runtime.aurel_shell.example",
        )
    )
    assert result.status is ContractMismatchGateStatus.FAIL_FAKE_TRACE_VERIFIED_CLAIM


def test_unknown_entrypoint_gate_blocks_unknown_marked_safe():
    result = evaluate_unknown_entrypoint_risk_gate(
        UnknownEntrypointRiskGateInput(
            p1_enf_b_report_present=True,
            classification_matrix_present=True,
            entrypoint_results=(
                EntrypointBypassGuardResult(
                    entrypoint="custom.execution.path",
                    classification=(
                        EntrypointGovernanceClassification.BLOCKED_UNKNOWN_EXECUTION_RISK
                    ),
                    bypass_risk=EntrypointBypassRisk.UNKNOWN,
                    delegation_requirement=GovernedDelegationRequirement.UNKNOWN,
                    metadata={"marked_safe": True},
                ),
            ),
        )
    )
    assert result.status is UnknownEntrypointRiskGateStatus.FAIL_UNKNOWN_MARKED_SAFE


def test_unknown_entrypoint_gate_allows_delegation_required_with_warning():
    result = UnknownEntrypointRiskGate().evaluate(
        UnknownEntrypointRiskGateInput(
            p1_enf_b_report_present=True,
            classification_matrix_present=True,
            repo_agent_classified=True,
            entrypoint_results=(
                EntrypointBypassGuardResult(
                    entrypoint="agentic_runtime.repo_agent.RepositoryAgentLoop",
                    classification=(
                        EntrypointGovernanceClassification.GOVERNED_DELEGATION_REQUIRED
                    ),
                    bypass_risk=EntrypointBypassRisk.MEDIUM,
                    delegation_requirement=GovernedDelegationRequirement.REQUIRED,
                ),
            ),
        )
    )
    assert (
        result.status
        is UnknownEntrypointRiskGateStatus.WARN_DELEGATION_REQUIRED_REMAINS
    )


def test_claim_drift_gate_requires_evidence_for_trace_verified():
    result = evaluate_report_code_claim_drift_gate(
        ClaimDriftGateInput(
            claims={"TRACE_VERIFIED": True},
            evidence={"trace_verification_evidence": False},
            source="agent/STATE.md",
        )
    )
    assert result.status is ClaimDriftGateStatus.FAIL_FAKE_TRACE_VERIFIED


def test_claim_drift_gate_requires_evidence_for_full_suite_pass():
    result = ReportCodeClaimDriftGate().evaluate(
        ClaimDriftGateInput(
            claims={"full_suite_pass": True},
            evidence={"full_suite_completed": False},
        )
    )
    assert result.status is ClaimDriftGateStatus.FAIL_FULL_SUITE_OVERCLAIM


def test_claim_drift_gate_requires_evidence_for_coverage_pass():
    result = evaluate_report_code_claim_drift_gate(
        ClaimDriftGateInput(
            claims={"coverage_pass": True},
            evidence={"coverage_run_completed": False},
        )
    )
    assert result.status is ClaimDriftGateStatus.FAIL_COVERAGE_OVERCLAIM


def test_p1_enf_f_a_does_not_implement_p1_enf_c():
    proof = P1ENFFASideEffectProof()
    assert proof.p1_enf_c_implemented is False


def test_p1_enf_f_a_does_not_implement_p2_9_b():
    proof = P1ENFFASideEffectProof()
    assert proof.p2_9_b_implemented is False
