"""P1.ENF-F-A governance drift and claim mismatch gates."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Mapping

from .entrypoint_governance_guard import (
    EntrypointBypassGuardResult,
    EntrypointGovernanceClassification,
)
from .governance_enforcement import GovernanceEnforcementMode


class ShadowMigrationGateStatus(str, Enum):
    PASS_ENFORCEMENT_BRIDGE_PRESENT = "pass_enforcement_bridge_present"
    WARN_SHADOW_COMPATIBILITY_MODE_PRESENT = "warn_shadow_compatibility_mode_present"
    FAIL_SHADOW_ONLY_AFTER_ENFORCEMENT_REQUIRED = (
        "fail_shadow_only_after_enforcement_required"
    )
    FAIL_PASSIVE_ARTIFACT_ONLY = "fail_passive_artifact_only"
    UNAVAILABLE = "unavailable"


class ContractMismatchGateStatus(str, Enum):
    PASS_HONEST_CONTRACT_ONLY = "pass_honest_contract_only"
    WARN_BINDING_UNAVAILABLE = "warn_binding_unavailable"
    FAIL_FAKE_LIVE_CLAIM = "fail_fake_live_claim"
    FAIL_FAKE_TRACE_VERIFIED_CLAIM = "fail_fake_trace_verified_claim"
    FAIL_SEALED_WITHOUT_UNAVAILABLE_REASON = "fail_sealed_without_unavailable_reason"
    UNAVAILABLE = "unavailable"


class UnknownEntrypointRiskGateStatus(str, Enum):
    PASS = "pass"
    FAIL_P1_ENF_B_EVIDENCE_MISSING = "fail_p1_enf_b_evidence_missing"
    FAIL_UNKNOWN_MARKED_SAFE = "fail_unknown_marked_safe"
    WARN_DELEGATION_REQUIRED_REMAINS = "warn_delegation_required_remains"
    BLOCKED_UNKNOWN_EXECUTION_RISK = "blocked_unknown_execution_risk"
    UNAVAILABLE = "unavailable"


class ClaimDriftGateStatus(str, Enum):
    PASS = "pass"
    WARN_WEAK_EVIDENCE = "warn_weak_evidence"
    FAIL_FAKE_LIVE = "fail_fake_live"
    FAIL_FAKE_TRACE_VERIFIED = "fail_fake_trace_verified"
    FAIL_TOOLING_OVERCLAIM = "fail_tooling_overclaim"
    FAIL_FULL_SUITE_OVERCLAIM = "fail_full_suite_overclaim"
    FAIL_COVERAGE_OVERCLAIM = "fail_coverage_overclaim"
    UNAVAILABLE = "unavailable"


@dataclass(frozen=True)
class PolicyShadowMigrationFinding:
    module: str
    shadow_only: bool
    enforcement_bridge_present: bool
    reason_code: str

    def to_canonical_dict(self) -> dict[str, object]:
        return {
            "enforcement_bridge_present": self.enforcement_bridge_present,
            "module": self.module,
            "reason_code": self.reason_code,
            "shadow_only": self.shadow_only,
        }


@dataclass(frozen=True)
class IdentityShadowMigrationFinding:
    module: str
    shadow_only: bool
    submit_context_present: bool
    reason_code: str

    def to_canonical_dict(self) -> dict[str, object]:
        return {
            "module": self.module,
            "reason_code": self.reason_code,
            "shadow_only": self.shadow_only,
            "submit_context_present": self.submit_context_present,
        }


@dataclass(frozen=True)
class EnforcementBridgePresence:
    policy_submit_influence_present: bool = False
    identity_submit_context_present: bool = False
    entrypoint_guard_present: bool = False
    governance_enforcement_modes_present: bool = False

    @property
    def bridge_present(self) -> bool:
        return (
            self.policy_submit_influence_present
            and self.identity_submit_context_present
            and self.entrypoint_guard_present
            and self.governance_enforcement_modes_present
        )

    def to_canonical_dict(self) -> dict[str, bool]:
        return {
            "bridge_present": self.bridge_present,
            "entrypoint_guard_present": self.entrypoint_guard_present,
            "governance_enforcement_modes_present": (
                self.governance_enforcement_modes_present
            ),
            "identity_submit_context_present": self.identity_submit_context_present,
            "policy_submit_influence_present": self.policy_submit_influence_present,
        }


@dataclass(frozen=True)
class ShadowMigrationGateInput:
    enforcement_bridge: EnforcementBridgePresence = field(
        default_factory=EnforcementBridgePresence
    )
    active_mode: GovernanceEnforcementMode = GovernanceEnforcementMode.SHADOW_ONLY
    claims_enforcement_active: bool = False
    passive_artifact_only: bool = False
    shadow_compatibility_allowed: bool = True


@dataclass(frozen=True)
class ShadowMigrationGateResult:
    status: ShadowMigrationGateStatus
    truth_label: str = "GOVERNANCE_GATE"
    policy_findings: tuple[PolicyShadowMigrationFinding, ...] = ()
    identity_findings: tuple[IdentityShadowMigrationFinding, ...] = ()
    reason_codes: tuple[str, ...] = ()

    def to_canonical_dict(self) -> dict[str, object]:
        return {
            "identity_findings": [
                item.to_canonical_dict() for item in self.identity_findings
            ],
            "policy_findings": [item.to_canonical_dict() for item in self.policy_findings],
            "reason_codes": sorted(self.reason_codes),
            "status": self.status.value,
            "truth_label": self.truth_label,
        }


@dataclass(frozen=True)
class SealedContractReadinessFinding:
    module: str
    sealed: bool
    unavailable_reason_present: bool
    reason_code: str

    def to_canonical_dict(self) -> dict[str, object]:
        return {
            "module": self.module,
            "reason_code": self.reason_code,
            "sealed": self.sealed,
            "unavailable_reason_present": self.unavailable_reason_present,
        }


@dataclass(frozen=True)
class BindingUnavailableFinding:
    module: str
    binding_unavailable: bool
    honest_unavailable_disclosure: bool
    reason_code: str

    def to_canonical_dict(self) -> dict[str, object]:
        return {
            "binding_unavailable": self.binding_unavailable,
            "honest_unavailable_disclosure": self.honest_unavailable_disclosure,
            "module": self.module,
            "reason_code": self.reason_code,
        }


@dataclass(frozen=True)
class FakeVerticalSliceRisk:
    module: str
    claim: str
    reason_code: str

    def to_canonical_dict(self) -> dict[str, str]:
        return {
            "claim": self.claim,
            "module": self.module,
            "reason_code": self.reason_code,
        }


@dataclass(frozen=True)
class ContractMismatchGateInput:
    contract_only: bool = True
    side_effects_all_false: bool = True
    binding_unavailable: bool = False
    claims_live: bool = False
    claims_trace_verified: bool = False
    claims_sealed: bool = False
    unavailable_reason_present: bool = False
    live_evidence_present: bool = False
    trace_verification_present: bool = False
    module_name: str = ""


@dataclass(frozen=True)
class ContractMismatchGateResult:
    status: ContractMismatchGateStatus
    truth_label: str = "DRIFT_DETECTION"
    sealed_findings: tuple[SealedContractReadinessFinding, ...] = ()
    binding_findings: tuple[BindingUnavailableFinding, ...] = ()
    fake_vertical_slice_risks: tuple[FakeVerticalSliceRisk, ...] = ()
    reason_codes: tuple[str, ...] = ()

    def to_canonical_dict(self) -> dict[str, object]:
        return {
            "binding_findings": [
                item.to_canonical_dict() for item in self.binding_findings
            ],
            "fake_vertical_slice_risks": [
                item.to_canonical_dict() for item in self.fake_vertical_slice_risks
            ],
            "reason_codes": sorted(self.reason_codes),
            "sealed_findings": [
                item.to_canonical_dict() for item in self.sealed_findings
            ],
            "status": self.status.value,
            "truth_label": self.truth_label,
        }


@dataclass(frozen=True)
class BypassRiskFinding:
    entrypoint: str
    classification: EntrypointGovernanceClassification
    marked_safe: bool
    reason_code: str

    def to_canonical_dict(self) -> dict[str, str]:
        return {
            "classification": self.classification.value,
            "entrypoint": self.entrypoint,
            "marked_safe": str(self.marked_safe),
            "reason_code": self.reason_code,
        }


@dataclass(frozen=True)
class UnknownEntrypointRiskGateInput:
    p1_enf_b_report_present: bool = False
    classification_matrix_present: bool = False
    entrypoint_results: tuple[EntrypointBypassGuardResult, ...] = ()
    repo_agent_classified: bool = False


@dataclass(frozen=True)
class UnknownEntrypointRiskGateResult:
    status: UnknownEntrypointRiskGateStatus
    truth_label: str = "GOVERNANCE_GATE"
    bypass_findings: tuple[BypassRiskFinding, ...] = ()
    reason_codes: tuple[str, ...] = ()

    def to_canonical_dict(self) -> dict[str, object]:
        return {
            "bypass_findings": [item.to_canonical_dict() for item in self.bypass_findings],
            "reason_codes": sorted(self.reason_codes),
            "status": self.status.value,
            "truth_label": self.truth_label,
        }


@dataclass(frozen=True)
class EvidenceClaimRequirement:
    claim: str
    required_evidence: str
    evidence_present: bool

    def to_canonical_dict(self) -> dict[str, object]:
        return {
            "claim": self.claim,
            "evidence_present": self.evidence_present,
            "required_evidence": self.required_evidence,
        }


@dataclass(frozen=True)
class TruthLabelOverclaimFinding:
    claim: str
    source: str
    required_evidence: str
    evidence_present: bool
    reason_code: str

    def to_canonical_dict(self) -> dict[str, object]:
        return {
            "claim": self.claim,
            "evidence_present": self.evidence_present,
            "reason_code": self.reason_code,
            "required_evidence": self.required_evidence,
            "source": self.source,
        }


@dataclass(frozen=True)
class ClaimDriftGateInput:
    claims: Mapping[str, bool] = field(default_factory=dict)
    evidence: Mapping[str, bool] = field(default_factory=dict)
    source: str = "report"


@dataclass(frozen=True)
class ClaimDriftGateResult:
    status: ClaimDriftGateStatus
    truth_label: str = "DRIFT_DETECTION"
    overclaims: tuple[TruthLabelOverclaimFinding, ...] = ()
    requirements: tuple[EvidenceClaimRequirement, ...] = ()
    reason_codes: tuple[str, ...] = ()

    def to_canonical_dict(self) -> dict[str, object]:
        return {
            "overclaims": [item.to_canonical_dict() for item in self.overclaims],
            "reason_codes": sorted(self.reason_codes),
            "requirements": [item.to_canonical_dict() for item in self.requirements],
            "status": self.status.value,
            "truth_label": self.truth_label,
        }


@dataclass(frozen=True)
class P1ENFFASideEffectProof:
    p1_enf_c_implemented: bool = False
    p1_enf_f_b_implemented: bool = False
    p1_enf_d1_implemented: bool = False
    p1_enf_e_implemented: bool = False
    p2_9_b_implemented: bool = False
    full_ci_created: bool = False
    global_mypy_strictness_enabled: bool = False
    shell_command_router_created: bool = False
    product_ui_created: bool = False
    repo_agent_rewritten: bool = False
    sandbox_backend_hardened: bool = False
    runtime_submit_rewritten: bool = False
    trace_memory_rewritten: bool = False
    fake_live_claimed: bool = False
    fake_trace_verified_claimed: bool = False
    all_drift_impossible_claimed: bool = False

    def to_canonical_dict(self) -> dict[str, bool]:
        return {
            "all_drift_impossible_claimed": self.all_drift_impossible_claimed,
            "fake_live_claimed": self.fake_live_claimed,
            "fake_trace_verified_claimed": self.fake_trace_verified_claimed,
            "full_ci_created": self.full_ci_created,
            "global_mypy_strictness_enabled": self.global_mypy_strictness_enabled,
            "p1_enf_c_implemented": self.p1_enf_c_implemented,
            "p1_enf_d1_implemented": self.p1_enf_d1_implemented,
            "p1_enf_e_implemented": self.p1_enf_e_implemented,
            "p1_enf_f_b_implemented": self.p1_enf_f_b_implemented,
            "p2_9_b_implemented": self.p2_9_b_implemented,
            "product_ui_created": self.product_ui_created,
            "repo_agent_rewritten": self.repo_agent_rewritten,
            "runtime_submit_rewritten": self.runtime_submit_rewritten,
            "sandbox_backend_hardened": self.sandbox_backend_hardened,
            "shell_command_router_created": self.shell_command_router_created,
            "trace_memory_rewritten": self.trace_memory_rewritten,
        }


class ShadowStillActiveGate:
    def evaluate(
        self, gate_input: ShadowMigrationGateInput
    ) -> ShadowMigrationGateResult:
        return evaluate_shadow_still_active_gate(gate_input)


class ContractEnforcementMismatchGate:
    def evaluate(
        self, gate_input: ContractMismatchGateInput
    ) -> ContractMismatchGateResult:
        return evaluate_contract_enforcement_mismatch_gate(gate_input)


class UnknownEntrypointRiskGate:
    def evaluate(
        self, gate_input: UnknownEntrypointRiskGateInput
    ) -> UnknownEntrypointRiskGateResult:
        return evaluate_unknown_entrypoint_risk_gate(gate_input)


class ReportCodeClaimDriftGate:
    def evaluate(self, gate_input: ClaimDriftGateInput) -> ClaimDriftGateResult:
        return evaluate_report_code_claim_drift_gate(gate_input)


_UNKNOWN_SAFE_CLASSIFICATIONS = frozenset(
    {
        EntrypointGovernanceClassification.NON_EXECUTING_CONTRACT_ONLY,
        EntrypointGovernanceClassification.NON_EXECUTING_READ_MODEL_ONLY,
        EntrypointGovernanceClassification.GOVERNED_RUNTIME_SUBMIT,
        EntrypointGovernanceClassification.GOVERNED_DELEGATION_CONFIRMED,
    }
)


def evaluate_shadow_still_active_gate(
    gate_input: ShadowMigrationGateInput,
) -> ShadowMigrationGateResult:
    if gate_input.passive_artifact_only and gate_input.claims_enforcement_active:
        return ShadowMigrationGateResult(
            status=ShadowMigrationGateStatus.FAIL_PASSIVE_ARTIFACT_ONLY,
            reason_codes=("PASSIVE_ARTIFACT_ONLY_ENFORCEMENT_OVERCLAIM",),
        )

    if (
        gate_input.claims_enforcement_active
        and not gate_input.enforcement_bridge.bridge_present
    ):
        return ShadowMigrationGateResult(
            status=ShadowMigrationGateStatus.FAIL_PASSIVE_ARTIFACT_ONLY,
            reason_codes=("ENFORCEMENT_CLAIM_WITHOUT_BRIDGE",),
        )

    if (
        gate_input.claims_enforcement_active
        and gate_input.active_mode is GovernanceEnforcementMode.SHADOW_ONLY
        and not gate_input.shadow_compatibility_allowed
    ):
        return ShadowMigrationGateResult(
            status=ShadowMigrationGateStatus.FAIL_SHADOW_ONLY_AFTER_ENFORCEMENT_REQUIRED,
            reason_codes=("SHADOW_ONLY_AFTER_ENFORCEMENT_REQUIRED",),
        )

    if gate_input.enforcement_bridge.bridge_present:
        if (
            gate_input.active_mode is GovernanceEnforcementMode.SHADOW_ONLY
            and gate_input.shadow_compatibility_allowed
        ):
            return ShadowMigrationGateResult(
                status=ShadowMigrationGateStatus.WARN_SHADOW_COMPATIBILITY_MODE_PRESENT,
                reason_codes=("ENFORCEMENT_BRIDGE_WITH_SHADOW_COMPATIBILITY",),
            )
        return ShadowMigrationGateResult(
            status=ShadowMigrationGateStatus.PASS_ENFORCEMENT_BRIDGE_PRESENT,
            reason_codes=("ENFORCEMENT_BRIDGE_PRESENT",),
        )

    return ShadowMigrationGateResult(
        status=ShadowMigrationGateStatus.UNAVAILABLE,
        reason_codes=("ENFORCEMENT_BRIDGE_EVIDENCE_UNAVAILABLE",),
    )


def evaluate_contract_enforcement_mismatch_gate(
    gate_input: ContractMismatchGateInput,
) -> ContractMismatchGateResult:
    if gate_input.claims_live and not gate_input.live_evidence_present:
        return ContractMismatchGateResult(
            status=ContractMismatchGateStatus.FAIL_FAKE_LIVE_CLAIM,
            fake_vertical_slice_risks=(
                FakeVerticalSliceRisk(
                    module=gate_input.module_name,
                    claim="LIVE",
                    reason_code="LIVE_WITHOUT_LIVE_EVIDENCE",
                ),
            ),
            reason_codes=("FAKE_LIVE_CLAIM",),
        )

    if gate_input.claims_trace_verified and not gate_input.trace_verification_present:
        return ContractMismatchGateResult(
            status=ContractMismatchGateStatus.FAIL_FAKE_TRACE_VERIFIED_CLAIM,
            fake_vertical_slice_risks=(
                FakeVerticalSliceRisk(
                    module=gate_input.module_name,
                    claim="TRACE_VERIFIED",
                    reason_code="TRACE_VERIFIED_WITHOUT_VERIFICATION",
                ),
            ),
            reason_codes=("FAKE_TRACE_VERIFIED_CLAIM",),
        )

    if gate_input.claims_sealed and not gate_input.unavailable_reason_present:
        return ContractMismatchGateResult(
            status=ContractMismatchGateStatus.FAIL_SEALED_WITHOUT_UNAVAILABLE_REASON,
            sealed_findings=(
                SealedContractReadinessFinding(
                    module=gate_input.module_name,
                    sealed=True,
                    unavailable_reason_present=False,
                    reason_code="SEALED_WITHOUT_UNAVAILABLE_REASON",
                ),
            ),
            reason_codes=("SEALED_WITHOUT_UNAVAILABLE_REASON",),
        )

    if (
        gate_input.binding_unavailable
        and gate_input.unavailable_reason_present
    ):
        return ContractMismatchGateResult(
            status=ContractMismatchGateStatus.WARN_BINDING_UNAVAILABLE,
            binding_findings=(
                BindingUnavailableFinding(
                    module=gate_input.module_name,
                    binding_unavailable=True,
                    honest_unavailable_disclosure=True,
                    reason_code="HONEST_BINDING_UNAVAILABLE",
                ),
            ),
            reason_codes=("HONEST_BINDING_UNAVAILABLE",),
        )

    if gate_input.contract_only and gate_input.side_effects_all_false:
        return ContractMismatchGateResult(
            status=ContractMismatchGateStatus.PASS_HONEST_CONTRACT_ONLY,
            reason_codes=("HONEST_CONTRACT_ONLY",),
        )

    return ContractMismatchGateResult(
        status=ContractMismatchGateStatus.UNAVAILABLE,
        reason_codes=("CONTRACT_MISMATCH_INPUT_INCOMPLETE",),
    )


def evaluate_unknown_entrypoint_risk_gate(
    gate_input: UnknownEntrypointRiskGateInput,
) -> UnknownEntrypointRiskGateResult:
    if not gate_input.p1_enf_b_report_present:
        return UnknownEntrypointRiskGateResult(
            status=UnknownEntrypointRiskGateStatus.FAIL_P1_ENF_B_EVIDENCE_MISSING,
            reason_codes=("P1_ENF_B_REPORT_MISSING",),
        )

    if not gate_input.classification_matrix_present:
        return UnknownEntrypointRiskGateResult(
            status=UnknownEntrypointRiskGateStatus.UNAVAILABLE,
            reason_codes=("CLASSIFICATION_MATRIX_MISSING",),
        )

    bypass_findings: list[BypassRiskFinding] = []
    delegation_warnings = False
    unknown_blocked = False

    for result in gate_input.entrypoint_results:
        if result.metadata.get("marked_safe"):
            bypass_findings.append(
                BypassRiskFinding(
                    entrypoint=result.entrypoint,
                    classification=result.classification,
                    marked_safe=True,
                    reason_code="UNKNOWN_ENTRYPOINT_MARKED_SAFE",
                )
            )
            continue
        if result.classification in _UNKNOWN_SAFE_CLASSIFICATIONS:
            continue
        if result.classification in {
            EntrypointGovernanceClassification.GOVERNED_DELEGATION_REQUIRED,
        }:
            delegation_warnings = True
            continue
        if result.classification in {
            EntrypointGovernanceClassification.BLOCKED_UNKNOWN_EXECUTION_RISK,
            EntrypointGovernanceClassification.BLOCKED_POLICY_BYPASS_RISK,
            EntrypointGovernanceClassification.BLOCKED_IDENTITY_BYPASS_RISK,
        }:
            unknown_blocked = True
            continue

    if bypass_findings:
        return UnknownEntrypointRiskGateResult(
            status=UnknownEntrypointRiskGateStatus.FAIL_UNKNOWN_MARKED_SAFE,
            bypass_findings=tuple(bypass_findings),
            reason_codes=("UNKNOWN_MARKED_SAFE",),
        )

    if delegation_warnings:
        return UnknownEntrypointRiskGateResult(
            status=UnknownEntrypointRiskGateStatus.WARN_DELEGATION_REQUIRED_REMAINS,
            reason_codes=("DELEGATION_REQUIRED_REMAINS_VISIBLE",),
        )

    if unknown_blocked or gate_input.repo_agent_classified:
        return UnknownEntrypointRiskGateResult(
            status=UnknownEntrypointRiskGateStatus.PASS,
            reason_codes=("UNKNOWN_RISK_BLOCKED_OR_CLASSIFIED",),
        )

    return UnknownEntrypointRiskGateResult(
        status=UnknownEntrypointRiskGateStatus.BLOCKED_UNKNOWN_EXECUTION_RISK,
        reason_codes=("UNKNOWN_EXECUTION_RISK_REMAINS",),
    )


_CLAIM_EVIDENCE_REQUIREMENTS: dict[str, str] = {
    "LIVE": "live_path_evidence",
    "TRACE_VERIFIED": "trace_verification_evidence",
    "full_suite_pass": "full_suite_completed",
    "coverage_pass": "coverage_run_completed",
    "mypy_pass": "mypy_run_completed",
    "ruff_pass": "ruff_run_completed",
}


def evaluate_report_code_claim_drift_gate(
    gate_input: ClaimDriftGateInput,
) -> ClaimDriftGateResult:
    requirements: list[EvidenceClaimRequirement] = []
    overclaims: list[TruthLabelOverclaimFinding] = []

    for claim, required_evidence in _CLAIM_EVIDENCE_REQUIREMENTS.items():
        claimed = gate_input.claims.get(claim, False)
        evidence_present = gate_input.evidence.get(required_evidence, False)
        requirements.append(
            EvidenceClaimRequirement(
                claim=claim,
                required_evidence=required_evidence,
                evidence_present=evidence_present,
            )
        )
        if claimed and not evidence_present:
            overclaims.append(
                TruthLabelOverclaimFinding(
                    claim=claim,
                    source=gate_input.source,
                    required_evidence=required_evidence,
                    evidence_present=False,
                    reason_code=f"{claim}_WITHOUT_EVIDENCE",
                )
            )

    if overclaims:
        first = overclaims[0]
        status = _overclaim_status(first.claim)
        return ClaimDriftGateResult(
            status=status,
            overclaims=tuple(overclaims),
            requirements=tuple(requirements),
            reason_codes=tuple(item.reason_code for item in overclaims),
        )

    weak = any(
        gate_input.claims.get("enforced", False)
        and not gate_input.evidence.get("enforcement_bridge_present", False)
        for _ in [0]
    )
    if weak:
        return ClaimDriftGateResult(
            status=ClaimDriftGateStatus.WARN_WEAK_EVIDENCE,
            requirements=tuple(requirements),
            reason_codes=("WEAK_ENFORCEMENT_EVIDENCE",),
        )

    return ClaimDriftGateResult(
        status=ClaimDriftGateStatus.PASS,
        requirements=tuple(requirements),
        reason_codes=("CLAIMS_MATCH_EVIDENCE",),
    )


def _overclaim_status(claim: str) -> ClaimDriftGateStatus:
    mapping = {
        "LIVE": ClaimDriftGateStatus.FAIL_FAKE_LIVE,
        "TRACE_VERIFIED": ClaimDriftGateStatus.FAIL_FAKE_TRACE_VERIFIED,
        "full_suite_pass": ClaimDriftGateStatus.FAIL_FULL_SUITE_OVERCLAIM,
        "coverage_pass": ClaimDriftGateStatus.FAIL_COVERAGE_OVERCLAIM,
        "mypy_pass": ClaimDriftGateStatus.FAIL_TOOLING_OVERCLAIM,
        "ruff_pass": ClaimDriftGateStatus.FAIL_TOOLING_OVERCLAIM,
    }
    return mapping.get(claim, ClaimDriftGateStatus.WARN_WEAK_EVIDENCE)
