"""Output Passport disclosure states (P1.9-C / P1.9.18-P1.9.20).

Non-live fixture disclosure, heretic/quarantine disclosure, and LoRA/adapter
influence disclosure without runtime execution, promotion, or trust claims.

Architectural law:
  - MOCK is not LIVE.
  - DEV_FIXTURE is not production.
  - SIMULATED is not operational reality.
  - Heretic output is not trusted output.
  - Quarantined output is not accepted output.
  - LoRA influence is not LoRA approval.
  - Adapter influence is not adapter promotion.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
from typing import Any

from .foundation import (
    FORBIDDEN_DEFAULT_TRUTH_LABELS,
    OutputPassportErrorCode,
    OutputPassportSideEffectProof,
    OutputPassportSourceLabel,
    OutputPassportTruthLabel,
    OutputPassportValidationError,
    stable_hash,
    to_canonical_json,
)

OUTPUT_PASSPORT_FIXTURE_DISCLOSURE_TASK_ID = "P1.9.18"
OUTPUT_PASSPORT_HERETIC_DISCLOSURE_TASK_ID = "P1.9.19"
OUTPUT_PASSPORT_LORA_DISCLOSURE_TASK_ID = "P1.9.20"
OUTPUT_PASSPORT_FIXTURE_DISCLOSURE_VERSION = (
    "output_passport_fixture_disclosure.v1"
)
OUTPUT_PASSPORT_REALITY_LABEL_VERSION = "output_passport_reality_label.v1"
OUTPUT_PASSPORT_MOCK_BOUNDARY_VERSION = "output_passport_mock_boundary.v1"
OUTPUT_PASSPORT_HERETIC_DISCLOSURE_VERSION = "output_passport_heretic_disclosure.v1"
OUTPUT_PASSPORT_QUARANTINE_DISCLOSURE_VERSION = (
    "output_passport_quarantine_disclosure.v1"
)
OUTPUT_PASSPORT_LORA_INFLUENCE_VERSION = "output_passport_lora_influence.v1"
OUTPUT_PASSPORT_ADAPTER_INFLUENCE_VERSION = (
    "output_passport_adapter_influence.v1"
)


class OutputPassportRealityLabel(str, Enum):
    """Operational reality label — distinct non-live states."""

    MOCK = "MOCK"
    DEV_FIXTURE = "DEV_FIXTURE"
    SIMULATED = "SIMULATED"
    NOT_LIVE = "NOT_LIVE"
    LIVE_UNAVAILABLE = "LIVE_UNAVAILABLE"


class QuarantineReviewState(str, Enum):
    """Quarantine review state — not acceptance."""

    REVIEW_REQUIRED = "review_required"
    PENDING_REVIEW = "pending_review"
    REJECTED = "rejected"
    UNAVAILABLE = "unavailable"
    NOT_APPLICABLE = "not_applicable"


class ModelAdaptationInfluenceStatus(str, Enum):
    """Model adaptation influence status — not approval or promotion."""

    INFLUENCE_DECLARED = "influence_declared"
    INFLUENCE_UNAVAILABLE = "influence_unavailable"
    INFLUENCE_REDACTED = "influence_redacted"
    NOT_APPLICABLE = "not_applicable"


class _CanonicalMixin:
    def to_canonical_dict(self) -> dict[str, Any]:
        return _canonical_dataclass_dict(self)


def _canonical_value(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return _canonical_dataclass_dict(value)
    if isinstance(value, Mapping):
        return {
            str(_canonical_value(key)): _canonical_value(item)
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
        }
    if isinstance(value, (list, tuple)):
        return [_canonical_value(item) for item in value]
    return value


def _canonical_dataclass_dict(value: Any) -> dict[str, Any]:
    return {
        field.name: _canonical_value(getattr(value, field.name))
        for field in fields(value)
    }


def _hash_payload(payload: Mapping[str, Any]) -> str:
    return stable_hash(dict(payload))


def _all_false_side_effects() -> OutputPassportSideEffectProof:
    return OutputPassportSideEffectProof()


def _reject_live_claim(reality_label: OutputPassportRealityLabel) -> None:
    if reality_label is OutputPassportRealityLabel.LIVE_UNAVAILABLE:
        return
    # LIVE is not a valid OutputPassportRealityLabel enum member


def _reject_forbidden_truth_label(
    truth_label: OutputPassportTruthLabel,
    *,
    field_name: str = "truth_label",
) -> None:
    if truth_label in FORBIDDEN_DEFAULT_TRUTH_LABELS:
        raise OutputPassportValidationError(
            f"forbidden {field_name}: {truth_label.value}",
            code=OutputPassportErrorCode.FORBIDDEN_VERIFICATION_LABEL,
            field=field_name,
        )


@dataclass(frozen=True)
class OutputPassportFixtureDisclosure(_CanonicalMixin):
    """P1.9.18 non-live fixture disclosure."""

    schema_version: str
    checkpoint_id: str
    reality_label: OutputPassportRealityLabel
    non_live_reason: str
    live_unavailable_reason: str
    truth_label: OutputPassportTruthLabel
    source_label: OutputPassportSourceLabel
    side_effects: OutputPassportSideEffectProof
    fixture_disclosure_hash: str


@dataclass(frozen=True)
class MockDevFixtureSimulatedBoundary(_CanonicalMixin):
    """Boundary invariants for MOCK / DEV_FIXTURE / SIMULATED."""

    schema_version: str
    checkpoint_id: str
    mock_is_live: bool
    dev_fixture_is_production: bool
    simulated_is_operational: bool
    invariants: tuple[str, ...]
    truth_label: OutputPassportTruthLabel
    source_label: OutputPassportSourceLabel
    side_effects: OutputPassportSideEffectProof
    mock_boundary_hash: str


@dataclass(frozen=True)
class HereticOutputDisclosure(_CanonicalMixin):
    """P1.9.19 heretic output disclosure — not trusted by default."""

    schema_version: str
    checkpoint_id: str
    heretic_origin_declared: bool
    trust_status: OutputPassportTruthLabel
    accepted_output: bool
    disclosure_reason: str
    truth_label: OutputPassportTruthLabel
    source_label: OutputPassportSourceLabel
    side_effects: OutputPassportSideEffectProof
    heretic_disclosure_hash: str


@dataclass(frozen=True)
class QuarantinedOutputDisclosure(_CanonicalMixin):
    """P1.9.19 quarantined output disclosure — not accepted by default."""

    schema_version: str
    checkpoint_id: str
    quarantine_status: OutputPassportTruthLabel
    quarantine_reason: str
    review_state: QuarantineReviewState
    review_required: bool
    accepted_output: bool
    truth_label: OutputPassportTruthLabel
    source_label: OutputPassportSourceLabel
    side_effects: OutputPassportSideEffectProof
    quarantine_disclosure_hash: str


@dataclass(frozen=True)
class LoRAInfluenceDisclosure(_CanonicalMixin):
    """P1.9.20 LoRA influence disclosure — not approval."""

    schema_version: str
    checkpoint_id: str
    lora_influence_declared: bool
    influence_status: ModelAdaptationInfluenceStatus
    approval_status: OutputPassportTruthLabel
    promotion_status: OutputPassportTruthLabel
    influence_ref: str | None
    unavailable_reason: str | None
    truth_label: OutputPassportTruthLabel
    source_label: OutputPassportSourceLabel
    side_effects: OutputPassportSideEffectProof
    lora_influence_hash: str


@dataclass(frozen=True)
class AdapterInfluenceDisclosure(_CanonicalMixin):
    """P1.9.20 adapter influence disclosure — not promotion."""

    schema_version: str
    checkpoint_id: str
    adapter_influence_declared: bool
    influence_status: ModelAdaptationInfluenceStatus
    approval_status: OutputPassportTruthLabel
    promotion_status: OutputPassportTruthLabel
    adapter_ref: str | None
    unavailable_reason: str | None
    truth_label: OutputPassportTruthLabel
    source_label: OutputPassportSourceLabel
    side_effects: OutputPassportSideEffectProof
    adapter_influence_hash: str


MOCK_BOUNDARY_INVARIANTS: tuple[str, ...] = (
    "mock_is_not_live",
    "dev_fixture_is_not_production",
    "simulated_is_not_operational_reality",
    "non_live_requires_reason",
)


def build_mock_dev_fixture_simulated_disclosure(
    *,
    reality_label: OutputPassportRealityLabel | str = (
        OutputPassportRealityLabel.DEV_FIXTURE
    ),
    checkpoint_id: str = "P1.9.18",
    non_live_reason: str = "p1_9_c_contract_only_dev_fixture",
    live_unavailable_reason: str = "live_runtime_unavailable_in_p1_9_c",
    source_label: OutputPassportSourceLabel | str = OutputPassportSourceLabel.DEV_FIXTURE,
) -> tuple[OutputPassportFixtureDisclosure, MockDevFixtureSimulatedBoundary]:
    if isinstance(reality_label, str):
        reality_label = OutputPassportRealityLabel(reality_label)
    if isinstance(source_label, str):
        source_label = OutputPassportSourceLabel(source_label)

    _reject_live_claim(reality_label)
    truth_map = {
        OutputPassportRealityLabel.MOCK: OutputPassportTruthLabel.MOCK,
        OutputPassportRealityLabel.DEV_FIXTURE: OutputPassportTruthLabel.DEV_FIXTURE,
        OutputPassportRealityLabel.SIMULATED: OutputPassportTruthLabel.SIMULATED,
        OutputPassportRealityLabel.NOT_LIVE: OutputPassportTruthLabel.NOT_LIVE,
        OutputPassportRealityLabel.LIVE_UNAVAILABLE: OutputPassportTruthLabel.NOT_LIVE,
    }
    truth_label = truth_map[reality_label]
    _reject_forbidden_truth_label(truth_label)

    side_effects = _all_false_side_effects()
    fixture_payload = {
        "schema_version": OUTPUT_PASSPORT_FIXTURE_DISCLOSURE_VERSION,
        "checkpoint_id": checkpoint_id,
        "reality_label": reality_label,
        "non_live_reason": non_live_reason,
        "live_unavailable_reason": live_unavailable_reason,
        "truth_label": truth_label,
        "source_label": source_label,
        "side_effects": side_effects,
    }
    fixture = OutputPassportFixtureDisclosure(
        **fixture_payload,
        fixture_disclosure_hash=_hash_payload(fixture_payload),
    )

    boundary_payload = {
        "schema_version": OUTPUT_PASSPORT_MOCK_BOUNDARY_VERSION,
        "checkpoint_id": checkpoint_id,
        "mock_is_live": False,
        "dev_fixture_is_production": False,
        "simulated_is_operational": False,
        "invariants": MOCK_BOUNDARY_INVARIANTS,
        "truth_label": OutputPassportTruthLabel.CONTRACT_ONLY,
        "source_label": source_label,
        "side_effects": side_effects,
    }
    boundary = MockDevFixtureSimulatedBoundary(
        **boundary_payload,
        mock_boundary_hash=_hash_payload(boundary_payload),
    )
    return fixture, boundary


def build_heretic_quarantined_output_disclosure(
    *,
    checkpoint_id: str = "P1.9.19",
    heretic_origin_declared: bool = True,
    quarantine_reason: str = "heretic_context_output_requires_review",
    source_label: OutputPassportSourceLabel | str = OutputPassportSourceLabel.DEV_FIXTURE,
) -> tuple[HereticOutputDisclosure, QuarantinedOutputDisclosure]:
    if isinstance(source_label, str):
        source_label = OutputPassportSourceLabel(source_label)

    side_effects = _all_false_side_effects()
    heretic_payload = {
        "schema_version": OUTPUT_PASSPORT_HERETIC_DISCLOSURE_VERSION,
        "checkpoint_id": checkpoint_id,
        "heretic_origin_declared": heretic_origin_declared,
        "trust_status": OutputPassportTruthLabel.NOT_TRUSTED,
        "accepted_output": False,
        "disclosure_reason": "heretic_output_disclosure_only_not_trusted",
        "truth_label": OutputPassportTruthLabel.DISCLOSURE_ONLY,
        "source_label": source_label,
        "side_effects": side_effects,
    }
    heretic = HereticOutputDisclosure(
        **heretic_payload,
        heretic_disclosure_hash=_hash_payload(heretic_payload),
    )

    quarantine_payload = {
        "schema_version": OUTPUT_PASSPORT_QUARANTINE_DISCLOSURE_VERSION,
        "checkpoint_id": checkpoint_id,
        "quarantine_status": OutputPassportTruthLabel.QUARANTINED,
        "quarantine_reason": quarantine_reason,
        "review_state": QuarantineReviewState.REVIEW_REQUIRED,
        "review_required": True,
        "accepted_output": False,
        "truth_label": OutputPassportTruthLabel.QUARANTINED,
        "source_label": source_label,
        "side_effects": side_effects,
    }
    quarantine = QuarantinedOutputDisclosure(
        **quarantine_payload,
        quarantine_disclosure_hash=_hash_payload(quarantine_payload),
    )
    return heretic, quarantine


def build_lora_adapter_influence_disclosure(
    *,
    checkpoint_id: str = "P1.9.20",
    lora_influence_declared: bool = True,
    adapter_influence_declared: bool = True,
    lora_ref: str | None = "dev-lora-ref-001",
    adapter_ref: str | None = "dev-adapter-ref-001",
    source_label: OutputPassportSourceLabel | str = OutputPassportSourceLabel.DEV_FIXTURE,
) -> tuple[LoRAInfluenceDisclosure, AdapterInfluenceDisclosure]:
    if isinstance(source_label, str):
        source_label = OutputPassportSourceLabel(source_label)

    side_effects = _all_false_side_effects()
    lora_payload = {
        "schema_version": OUTPUT_PASSPORT_LORA_INFLUENCE_VERSION,
        "checkpoint_id": checkpoint_id,
        "lora_influence_declared": lora_influence_declared,
        "influence_status": ModelAdaptationInfluenceStatus.INFLUENCE_DECLARED,
        "approval_status": OutputPassportTruthLabel.NOT_APPROVAL,
        "promotion_status": OutputPassportTruthLabel.NOT_PROMOTION,
        "influence_ref": lora_ref,
        "unavailable_reason": None,
        "truth_label": OutputPassportTruthLabel.DISCLOSURE_ONLY,
        "source_label": source_label,
        "side_effects": side_effects,
    }
    lora = LoRAInfluenceDisclosure(
        **lora_payload,
        lora_influence_hash=_hash_payload(lora_payload),
    )

    adapter_payload = {
        "schema_version": OUTPUT_PASSPORT_ADAPTER_INFLUENCE_VERSION,
        "checkpoint_id": checkpoint_id,
        "adapter_influence_declared": adapter_influence_declared,
        "influence_status": ModelAdaptationInfluenceStatus.INFLUENCE_DECLARED,
        "approval_status": OutputPassportTruthLabel.NOT_APPROVAL,
        "promotion_status": OutputPassportTruthLabel.NOT_PROMOTION,
        "adapter_ref": adapter_ref,
        "unavailable_reason": None,
        "truth_label": OutputPassportTruthLabel.DISCLOSURE_ONLY,
        "source_label": source_label,
        "side_effects": side_effects,
    }
    adapter = AdapterInfluenceDisclosure(
        **adapter_payload,
        adapter_influence_hash=_hash_payload(adapter_payload),
    )
    return lora, adapter


def serialize_fixture_disclosure(disclosure: OutputPassportFixtureDisclosure) -> str:
    return to_canonical_json(disclosure)
