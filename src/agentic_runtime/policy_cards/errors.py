"""Policy Card error taxonomy (P1.6.0).

Small, explicit error classes for policy card loading, validation,
serialization, and hashing. All errors inherit from PolicyCardError
which itself inherits from ValueError — consistent with the repo
convention of per-module ValueError subclasses.
"""
from __future__ import annotations


class PolicyCardError(ValueError):
    """Base error for all policy card operations."""


class PolicyCardValidationError(PolicyCardError):
    """Raised when a policy card fails structured validation."""


class PolicyCardSerializationError(PolicyCardError):
    """Raised when canonical serialization fails."""


class PolicyCardHashError(PolicyCardError):
    """Raised when canonical hash computation fails."""


class PolicyCardUnknownFieldError(PolicyCardValidationError):
    """Raised when an unknown top-level field is found — closed-world enforcement."""


class PolicyCardUnsafeFieldError(PolicyCardValidationError):
    """Raised when a dangerous metadata key or unsafe field is detected."""


# ---------------------------------------------------------------------------
# Behavioral Contract errors (P1.6.2)
# ---------------------------------------------------------------------------


class BehavioralContractError(PolicyCardError):
    """Base error for all behavioral contract operations."""


class BehavioralContractValidationError(BehavioralContractError):
    """Raised when a behavioral contract fails structured validation."""


class BehavioralContractSerializationError(BehavioralContractError):
    """Raised when canonical serialization fails."""


class BehavioralContractHashError(BehavioralContractError):
    """Raised when canonical hash computation fails."""


class BehavioralContractUnknownFieldError(BehavioralContractValidationError):
    """Raised when an unknown top-level field is found — closed-world enforcement."""


class BehavioralContractUnsafeFieldError(BehavioralContractValidationError):
    """Raised when a dangerous metadata key or unsafe field is detected."""


# ---------------------------------------------------------------------------
# Risk Tier Policy Card errors (P1.6.3)
# ---------------------------------------------------------------------------


class RiskTierPolicyCardError(PolicyCardError):
    """Base error for all risk tier policy card operations."""


class RiskTierPolicyCardValidationError(RiskTierPolicyCardError):
    """Raised when a risk tier policy card fails structured validation."""


class RiskTierPolicyCardSerializationError(RiskTierPolicyCardError):
    """Raised when canonical serialization fails."""


class RiskTierPolicyCardHashError(RiskTierPolicyCardError):
    """Raised when canonical hash computation fails."""


class RiskTierPolicyCardUnknownFieldError(RiskTierPolicyCardValidationError):
    """Raised when an unknown field is found - closed-world enforcement."""


class RiskTierPolicyCardUnsafeFieldError(RiskTierPolicyCardValidationError):
    """Raised when a dangerous metadata key or unsafe field is detected."""


# ---------------------------------------------------------------------------
# Human Oversight Policy Card errors (P1.6.4)
# ---------------------------------------------------------------------------


class HumanOversightPolicyCardError(PolicyCardError):
    """Base error for all human oversight policy card operations."""


class HumanOversightPolicyCardValidationError(HumanOversightPolicyCardError):
    """Raised when a human oversight policy card fails structured validation."""


class HumanOversightPolicyCardSerializationError(HumanOversightPolicyCardError):
    """Raised when canonical serialization fails."""


class HumanOversightPolicyCardHashError(HumanOversightPolicyCardError):
    """Raised when canonical hash computation fails."""


class HumanOversightPolicyCardUnknownFieldError(HumanOversightPolicyCardValidationError):
    """Raised when an unknown field is found - closed-world enforcement."""


class HumanOversightPolicyCardUnsafeFieldError(HumanOversightPolicyCardValidationError):
    """Raised when a dangerous metadata key or unsafe field is detected."""


# ---------------------------------------------------------------------------
# Data Residency Policy Card errors (P1.6.5)
# ---------------------------------------------------------------------------


class DataResidencyPolicyCardError(PolicyCardError):
    """Base error for all data residency policy card operations."""


class DataResidencyPolicyCardValidationError(DataResidencyPolicyCardError):
    """Raised when a data residency policy card fails structured validation."""


class DataResidencyPolicyCardSerializationError(DataResidencyPolicyCardError):
    """Raised when canonical serialization fails."""


class DataResidencyPolicyCardHashError(DataResidencyPolicyCardError):
    """Raised when canonical hash computation fails."""


class DataResidencyPolicyCardUnknownFieldError(DataResidencyPolicyCardValidationError):
    """Raised when an unknown field is found - closed-world enforcement."""


class DataResidencyPolicyCardUnsafeFieldError(DataResidencyPolicyCardValidationError):
    """Raised when a dangerous metadata key or unsafe field is detected."""


# ---------------------------------------------------------------------------
# Tool Permission Policy Card errors (P1.6.6)
# ---------------------------------------------------------------------------


class ToolPermissionPolicyCardError(PolicyCardError):
    """Base error for all tool permission policy card operations."""


class ToolPermissionPolicyCardValidationError(ToolPermissionPolicyCardError):
    """Raised when a tool permission policy card fails structured validation."""


class ToolPermissionPolicyCardSerializationError(ToolPermissionPolicyCardError):
    """Raised when canonical serialization fails."""


class ToolPermissionPolicyCardHashError(ToolPermissionPolicyCardError):
    """Raised when canonical hash computation fails."""


class ToolPermissionPolicyCardUnknownFieldError(ToolPermissionPolicyCardValidationError):
    """Raised when an unknown field is found - closed-world enforcement."""


class ToolPermissionPolicyCardUnsafeFieldError(ToolPermissionPolicyCardValidationError):
    """Raised when a dangerous metadata key or unsafe field is detected."""


# ---------------------------------------------------------------------------
# Memory Write Policy Card errors (P1.6.7)
# ---------------------------------------------------------------------------


class MemoryWritePolicyCardError(PolicyCardError):
    """Base error for all memory write policy card operations."""


class MemoryWritePolicyCardValidationError(MemoryWritePolicyCardError):
    """Raised when a memory write policy card fails structured validation."""


class MemoryWritePolicyCardSerializationError(MemoryWritePolicyCardError):
    """Raised when canonical serialization fails."""


class MemoryWritePolicyCardHashError(MemoryWritePolicyCardError):
    """Raised when canonical hash computation fails."""


class MemoryWritePolicyCardUnknownFieldError(MemoryWritePolicyCardValidationError):
    """Raised when an unknown field is found - closed-world enforcement."""


class MemoryWritePolicyCardUnsafeFieldError(MemoryWritePolicyCardValidationError):
    """Raised when a dangerous metadata key or unsafe field is detected."""


# ---------------------------------------------------------------------------
# Prompt Policy Card errors (P1.6.8)
# ---------------------------------------------------------------------------


class PromptPolicyCardError(PolicyCardError):
    """Base error for all prompt policy card operations."""


class PromptPolicyCardValidationError(PromptPolicyCardError):
    """Raised when a prompt policy card fails structured validation."""


class PromptPolicyCardSerializationError(PromptPolicyCardError):
    """Raised when canonical serialization fails."""


class PromptPolicyCardHashError(PromptPolicyCardError):
    """Raised when canonical hash computation fails."""


class PromptPolicyCardUnknownFieldError(PromptPolicyCardValidationError):
    """Raised when an unknown field is found - closed-world enforcement."""


class PromptPolicyCardUnsafeFieldError(PromptPolicyCardValidationError):
    """Raised when a dangerous metadata key or unsafe field is detected."""


# ---------------------------------------------------------------------------
# Sandbox Policy Card errors (P1.6.9)
# ---------------------------------------------------------------------------


class SandboxPolicyCardError(PolicyCardError):
    """Base error for all sandbox policy card operations."""


class SandboxPolicyCardValidationError(SandboxPolicyCardError):
    """Raised when a sandbox policy card fails structured validation."""


class SandboxPolicyCardSerializationError(SandboxPolicyCardError):
    """Raised when canonical serialization fails."""


class SandboxPolicyCardHashError(SandboxPolicyCardError):
    """Raised when canonical hash computation fails."""


class SandboxPolicyCardUnknownFieldError(SandboxPolicyCardValidationError):
    """Raised when an unknown field is found - closed-world enforcement."""


class SandboxPolicyCardUnsafeFieldError(SandboxPolicyCardValidationError):
    """Raised when a dangerous metadata key or unsafe field is detected."""


class SandboxPolicyCardDecisionError(SandboxPolicyCardError):
    """Raised when sandbox policy decision evaluation encounters an unrecoverable error."""


class SandboxPolicyCardSchemaError(SandboxPolicyCardError):
    """Raised when sandbox policy schema is structurally invalid."""


# ---------------------------------------------------------------------------
# Custos v0 Policy Runtime Resolver errors (P1.6.10)
# ---------------------------------------------------------------------------


class PolicyResolutionError(PolicyCardError):
    """Base error for all Custos v0 policy resolution operations."""


class PolicyResolutionValidationError(PolicyResolutionError):
    """Raised when resolver input (cards/mode/duplicates) fails structured validation."""


class PolicyResolutionContextError(PolicyResolutionError):
    """Raised when a PolicyResolutionContext is invalid or fails closed-world loading."""


class PolicyResolutionSerializationError(PolicyResolutionError):
    """Raised when resolver context/result canonical serialization fails."""


class PolicyResolutionAdapterError(PolicyResolutionError):
    """Raised when a policy family adapter encounters an unrecoverable error."""


# ---------------------------------------------------------------------------
# Policy resolution registry/binding errors (P1.6.11)
# ---------------------------------------------------------------------------


class PolicyCardRegistryError(PolicyCardError):
    """Base error for policy-card registry operations."""


class PolicyCardRegistryValidationError(PolicyCardRegistryError):
    """Raised when registry input fails deterministic validation."""


class PolicyContextBindingError(PolicyResolutionContextError):
    """Raised when runtime-like metadata cannot bind to a resolution context."""


class PolicyRiskMappingError(PolicyResolutionError):
    """Raised when a risk vocabulary value cannot be translated safely."""
