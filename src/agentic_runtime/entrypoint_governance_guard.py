"""P1.ENF-A entrypoint bypass guard read model."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping


class EntrypointGovernanceClassification(str, Enum):
    NON_EXECUTING_CONTRACT_ONLY = "non_executing_contract_only"
    GOVERNED_RUNTIME_SUBMIT = "governed_runtime_submit"
    GOVERNED_DELEGATION_REQUIRED = "governed_delegation_required"
    BLOCKED_UNKNOWN_EXECUTION_RISK = "blocked_unknown_execution_risk"
    UNAVAILABLE = "unavailable"


class EntrypointBypassRisk(str, Enum):
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    UNKNOWN = "unknown"


class GovernedDelegationRequirement(str, Enum):
    NOT_REQUIRED = "not_required"
    REQUIRED = "required"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class NonExecutingEntrypointProof:
    module_name: str
    contract_only: bool = True
    command_router_created: bool = False
    product_execution_created: bool = False
    runtime_submit_called: bool = False

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "command_router_created": self.command_router_created,
            "contract_only": self.contract_only,
            "module_name": self.module_name,
            "product_execution_created": self.product_execution_created,
            "runtime_submit_called": self.runtime_submit_called,
        }


@dataclass(frozen=True)
class EntrypointBypassGuardResult:
    entrypoint: str
    classification: EntrypointGovernanceClassification
    bypass_risk: EntrypointBypassRisk
    delegation_requirement: GovernedDelegationRequirement
    reason_codes: tuple[str, ...] = ()
    non_executing_proof: NonExecutingEntrypointProof | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def to_canonical_dict(self) -> dict[str, Any]:
        result = {
            "bypass_risk": self.bypass_risk.value,
            "classification": self.classification.value,
            "delegation_requirement": self.delegation_requirement.value,
            "entrypoint": self.entrypoint,
            "metadata": dict(sorted(self.metadata.items())),
            "reason_codes": sorted(self.reason_codes),
        }
        if self.non_executing_proof is not None:
            result["non_executing_proof"] = (
                self.non_executing_proof.to_canonical_dict()
            )
        return result

    @property
    def result_hash(self) -> str:
        payload = json.dumps(
            self.to_canonical_dict(),
            sort_keys=True,
            separators=(",", ":"),
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class EntrypointGovernanceGuard:
    """Classify entrypoints without creating execution capability."""

    def classify(self, entrypoint: str) -> EntrypointBypassGuardResult:
        return classify_entrypoint_governance(entrypoint)


_AUREL_SHELL_CONTRACT_PREFIX = "agentic_runtime.aurel_shell."


def classify_entrypoint_governance(entrypoint: str) -> EntrypointBypassGuardResult:
    normalized = entrypoint.strip()
    if normalized in {
        "agentic_runtime.runtime.AgenticRuntime.submit",
        "AgenticRuntime.submit",
        "runtime.submit",
    }:
        return EntrypointBypassGuardResult(
            entrypoint=normalized,
            classification=EntrypointGovernanceClassification.GOVERNED_RUNTIME_SUBMIT,
            bypass_risk=EntrypointBypassRisk.NONE,
            delegation_requirement=GovernedDelegationRequirement.NOT_REQUIRED,
            reason_codes=("RUNTIME_SUBMIT_IS_GOVERNED_DISPOSAL_PATH",),
        )
    if normalized.startswith(_AUREL_SHELL_CONTRACT_PREFIX):
        return EntrypointBypassGuardResult(
            entrypoint=normalized,
            classification=(
                EntrypointGovernanceClassification.NON_EXECUTING_CONTRACT_ONLY
            ),
            bypass_risk=EntrypointBypassRisk.LOW,
            delegation_requirement=GovernedDelegationRequirement.NOT_REQUIRED,
            reason_codes=("AUREL_SHELL_CONTRACT_READ_MODEL_ONLY",),
            non_executing_proof=NonExecutingEntrypointProof(module_name=normalized),
        )
    if normalized.startswith("agentic_runtime.repo_agent"):
        return EntrypointBypassGuardResult(
            entrypoint=normalized,
            classification=(
                EntrypointGovernanceClassification.GOVERNED_DELEGATION_REQUIRED
            ),
            bypass_risk=EntrypointBypassRisk.MEDIUM,
            delegation_requirement=GovernedDelegationRequirement.REQUIRED,
            reason_codes=("REPO_AGENT_EXECUTION_LIKE_PATH_REQUIRES_RUNTIME_SUBMIT",),
            metadata={"known_runtime_submit_delegation": True},
        )
    if _looks_execution_like(normalized):
        return EntrypointBypassGuardResult(
            entrypoint=normalized,
            classification=(
                EntrypointGovernanceClassification.BLOCKED_UNKNOWN_EXECUTION_RISK
            ),
            bypass_risk=EntrypointBypassRisk.UNKNOWN,
            delegation_requirement=GovernedDelegationRequirement.UNKNOWN,
            reason_codes=("UNKNOWN_EXECUTION_LIKE_ENTRYPOINT_BLOCKED",),
        )
    return EntrypointBypassGuardResult(
        entrypoint=normalized,
        classification=EntrypointGovernanceClassification.UNAVAILABLE,
        bypass_risk=EntrypointBypassRisk.UNKNOWN,
        delegation_requirement=GovernedDelegationRequirement.UNKNOWN,
        reason_codes=("ENTRYPOINT_NOT_CLASSIFIED_FOR_P1_ENF_A",),
    )


def _looks_execution_like(entrypoint: str) -> bool:
    lowered = entrypoint.lower()
    return any(
        token in lowered
        for token in (
            "execute",
            "dispatch",
            "run_shell",
            "command_router",
            "tool_call",
            "subprocess",
            "submit",
        )
    )
