"""Policy Cards & Behavioral Contracts (P1.6.0).

First-class, typed, versioned, scoped, validated, deterministic, hash-ready,
closed-world governance objects for AurelCore.

Policy is not documentation. Policy is not a prompt. Policy is not advice.
Policy is a governed runtime object.

Architectural laws:
  - A policy card must never grant authority merely by existing.
  - A behavioral contract must never grant authority, bypass policy cards,
    or enforce runtime behavior.
  - Unknown authority/safety fields must fail closed.
  - Metadata must not become a shadow control plane.
  - Raw source hash and canonical hash are conceptually separate.
  - P1.6.0-P1.6.2 are foundation only.
"""
from __future__ import annotations

from .contract_schema import (
    BEHAVIORAL_CONTRACT_BEHAVIOR_FIELDS,
    BEHAVIORAL_CONTRACT_CANONICAL_FIELDS,
    BEHAVIORAL_CONTRACT_CONTROL_FIELDS,
    BEHAVIORAL_CONTRACT_DANGEROUS_FIELD_NAMES,
    BEHAVIORAL_CONTRACT_DANGEROUS_METADATA_KEYS,
    BEHAVIORAL_CONTRACT_DESCRIPTIVE_FIELDS,
    BEHAVIORAL_CONTRACT_EVIDENCE_FIELDS,
    BEHAVIORAL_CONTRACT_FORBIDDEN_FIELDS,
    BEHAVIORAL_CONTRACT_IDENTITY_FIELDS,
    BEHAVIORAL_CONTRACT_OPTIONAL_FIELDS,
    BEHAVIORAL_CONTRACT_REQUIRED_FIELDS,
    BEHAVIORAL_CONTRACT_RUNTIME_FUTURE_FIELDS,
    BEHAVIORAL_CONTRACT_SCHEMA_VERSION,
    BEHAVIORAL_CONTRACT_SOURCE_FIELDS,
    BEHAVIORAL_CONTRACT_SUBJECT_FIELDS,
    SUPPORTED_BEHAVIORAL_CONTRACT_SCHEMA_VERSIONS,
    export_behavioral_contract_schema,
    get_behavioral_contract_schema,
    is_supported_behavioral_contract_schema_version,
    validate_behavioral_contract_schema_version,
)
from .contracts import (
    BehavioralContract,
    BehavioralContractEscalationAction,
    BehavioralContractEscalationRule,
    BehavioralContractEscalationTrigger,
    BehavioralContractEvidenceRequirement,
    BehavioralContractEvidenceType,
    BehavioralContractIdentity,
    BehavioralContractObligation,
    BehavioralContractObligationType,
    BehavioralContractPostcondition,
    BehavioralContractPostconditionType,
    BehavioralContractPrecondition,
    BehavioralContractPreconditionType,
    BehavioralContractProhibition,
    BehavioralContractProhibitionType,
    BehavioralContractScope,
    BehavioralContractScopeType,
    BehavioralContractSource,
    BehavioralContractStatus,
    BehavioralContractSubject,
    BehavioralContractSubjectType,
    BehavioralContractValidationIssue,
    BehavioralContractValidationResult,
    behavioral_contract_to_canonical_dict,
    compute_behavioral_contract_hash,
    load_behavioral_contract_from_dict,
    serialize_behavioral_contract_canonical,
    validate_behavioral_contract,
)
from .errors import (
    BehavioralContractError,
    BehavioralContractHashError,
    BehavioralContractSerializationError,
    BehavioralContractUnknownFieldError,
    BehavioralContractUnsafeFieldError,
    BehavioralContractValidationError,
    PolicyCardError,
    PolicyCardHashError,
    PolicyCardSerializationError,
    PolicyCardUnknownFieldError,
    PolicyCardUnsafeFieldError,
    PolicyCardValidationError,
)
from .hashing import compute_policy_card_hash
from .models import (
    PolicyCard,
    PolicyCardAuthorityBinding,
    PolicyCardIdentity,
    PolicyCardKind,
    PolicyCardRiskBinding,
    PolicyCardScope,
    PolicyCardScopeType,
    PolicyCardSource,
    PolicyCardStatus,
    PolicyCardValidationIssue,
    PolicyCardValidationResult,
)
from .schema import (
    POLICY_CARD_CANONICAL_FIELDS,
    POLICY_CARD_DANGEROUS_METADATA_KEYS,
    POLICY_CARD_FORBIDDEN_FIELDS,
    POLICY_CARD_OPTIONAL_FIELDS,
    POLICY_CARD_REQUIRED_FIELDS,
    POLICY_CARD_SCHEMA_VERSION,
    SUPPORTED_POLICY_CARD_SCHEMA_VERSIONS,
    export_policy_card_schema,
    get_policy_card_schema,
    is_supported_policy_card_schema_version,
    validate_policy_card_schema_version,
)
from .serialization import (
    policy_card_to_canonical_dict,
    serialize_policy_card_canonical,
)
from .validation import (
    DANGEROUS_METADATA_KEYS,
    DANGEROUS_TOP_LEVEL_FIELDS,
    load_policy_card_from_dict,
    validate_policy_card,
)

__all__ = [
    # ─ Policy Card models ─
    "PolicyCard",
    "PolicyCardIdentity",
    "PolicyCardKind",
    "PolicyCardStatus",
    "PolicyCardScope",
    "PolicyCardScopeType",
    "PolicyCardRiskBinding",
    "PolicyCardAuthorityBinding",
    "PolicyCardSource",
    "PolicyCardValidationIssue",
    "PolicyCardValidationResult",
    # ─ Policy Card schema ─
    "POLICY_CARD_SCHEMA_VERSION",
    "SUPPORTED_POLICY_CARD_SCHEMA_VERSIONS",
    "POLICY_CARD_REQUIRED_FIELDS",
    "POLICY_CARD_OPTIONAL_FIELDS",
    "POLICY_CARD_FORBIDDEN_FIELDS",
    "POLICY_CARD_CANONICAL_FIELDS",
    "POLICY_CARD_DANGEROUS_METADATA_KEYS",
    "export_policy_card_schema",
    "get_policy_card_schema",
    "is_supported_policy_card_schema_version",
    "validate_policy_card_schema_version",
    # ─ Policy Card validation ─
    "validate_policy_card",
    "load_policy_card_from_dict",
    "DANGEROUS_TOP_LEVEL_FIELDS",
    "DANGEROUS_METADATA_KEYS",
    # ─ Policy Card serialization ─
    "serialize_policy_card_canonical",
    "policy_card_to_canonical_dict",
    # ─ Policy Card hashing ─
    "compute_policy_card_hash",
    # ─ Policy Card errors ─
    "PolicyCardError",
    "PolicyCardValidationError",
    "PolicyCardSerializationError",
    "PolicyCardHashError",
    "PolicyCardUnknownFieldError",
    "PolicyCardUnsafeFieldError",
    # ─ Behavioral Contract enums ─
    "BehavioralContractStatus",
    "BehavioralContractSubjectType",
    "BehavioralContractScopeType",
    "BehavioralContractObligationType",
    "BehavioralContractProhibitionType",
    "BehavioralContractPreconditionType",
    "BehavioralContractPostconditionType",
    "BehavioralContractEvidenceType",
    "BehavioralContractEscalationTrigger",
    "BehavioralContractEscalationAction",
    # ─ Behavioral Contract models ─
    "BehavioralContract",
    "BehavioralContractIdentity",
    "BehavioralContractSubject",
    "BehavioralContractScope",
    "BehavioralContractObligation",
    "BehavioralContractProhibition",
    "BehavioralContractPrecondition",
    "BehavioralContractPostcondition",
    "BehavioralContractEvidenceRequirement",
    "BehavioralContractEscalationRule",
    "BehavioralContractSource",
    "BehavioralContractValidationIssue",
    "BehavioralContractValidationResult",
    # ─ Behavioral Contract schema ─
    "BEHAVIORAL_CONTRACT_SCHEMA_VERSION",
    "SUPPORTED_BEHAVIORAL_CONTRACT_SCHEMA_VERSIONS",
    "BEHAVIORAL_CONTRACT_REQUIRED_FIELDS",
    "BEHAVIORAL_CONTRACT_OPTIONAL_FIELDS",
    "BEHAVIORAL_CONTRACT_FORBIDDEN_FIELDS",
    "BEHAVIORAL_CONTRACT_CANONICAL_FIELDS",
    "BEHAVIORAL_CONTRACT_CONTROL_FIELDS",
    "BEHAVIORAL_CONTRACT_IDENTITY_FIELDS",
    "BEHAVIORAL_CONTRACT_SUBJECT_FIELDS",
    "BEHAVIORAL_CONTRACT_BEHAVIOR_FIELDS",
    "BEHAVIORAL_CONTRACT_EVIDENCE_FIELDS",
    "BEHAVIORAL_CONTRACT_SOURCE_FIELDS",
    "BEHAVIORAL_CONTRACT_DESCRIPTIVE_FIELDS",
    "BEHAVIORAL_CONTRACT_RUNTIME_FUTURE_FIELDS",
    "BEHAVIORAL_CONTRACT_DANGEROUS_FIELD_NAMES",
    "BEHAVIORAL_CONTRACT_DANGEROUS_METADATA_KEYS",
    "export_behavioral_contract_schema",
    "get_behavioral_contract_schema",
    "is_supported_behavioral_contract_schema_version",
    "validate_behavioral_contract_schema_version",
    # ─ Behavioral Contract validation ─
    "validate_behavioral_contract",
    "load_behavioral_contract_from_dict",
    # ─ Behavioral Contract serialization ─
    "serialize_behavioral_contract_canonical",
    "behavioral_contract_to_canonical_dict",
    # ─ Behavioral Contract hashing ─
    "compute_behavioral_contract_hash",
    # ─ Behavioral Contract errors ─
    "BehavioralContractError",
    "BehavioralContractValidationError",
    "BehavioralContractSerializationError",
    "BehavioralContractHashError",
    "BehavioralContractUnknownFieldError",
    "BehavioralContractUnsafeFieldError",
]
