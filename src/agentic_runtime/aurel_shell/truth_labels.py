"""AurelShell surface truth label contracts (P2.0-D / P2.0.18).

Truth labels are guarded claims with evidence requirements. A label is not
proof by itself: LIVE needs a tested live path, TRACE_VERIFIED needs actual
trace verification evidence, and fixture/mock/simulated labels are never LIVE.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .contracts import (
    AurelShellErrorCode,
    _CanonicalMixin,
    _hash_payload,
    _reject,
)
from .surface_registry import (
    AurelSurfaceKind,
    AurelSurfaceRegistry,
    build_default_surface_registry,
)

AUREL_TRUTH_LABEL_CONTRACT_VERSION = "aurel_truth_label_contract.v1"
AUREL_TRUTH_CLAIM_VERSION = "aurel_truth_claim.v1"


class SurfaceTruthLabel(str, Enum):
    CONTRACT_ONLY = "CONTRACT_ONLY"
    READ_MODEL_ONLY = "READ_MODEL_ONLY"
    PROJECTION_ONLY = "PROJECTION_ONLY"
    DEV_FIXTURE = "DEV_FIXTURE"
    MOCK = "MOCK"
    SIMULATED = "SIMULATED"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"
    NOT_LIVE = "NOT_LIVE"
    LIVE = "LIVE"
    TRACE_VERIFIED = "TRACE_VERIFIED"
    PERMISSION_MATRIX_CONTRACT_ONLY = "PERMISSION_MATRIX_CONTRACT_ONLY"
    UNAVAILABLE_STATE_CONTRACT_ONLY = "UNAVAILABLE_STATE_CONTRACT_ONLY"
    FIXTURE_DISCLOSURE_ONLY = "FIXTURE_DISCLOSURE_ONLY"


class SurfaceTruthEvidenceRequirement(str, Enum):
    CONTRACT_OBJECT_REQUIRED = "contract_object_required"
    TESTED_LIVE_PATH_REQUIRED = "tested_live_path_required"
    ACTUAL_TRACE_VERIFICATION_REQUIRED = "actual_trace_verification_required"
    VISIBLE_FIXTURE_DISCLOSURE_REQUIRED = "visible_fixture_disclosure_required"
    UNAVAILABLE_REASON_REQUIRED = "unavailable_reason_required"
    ERROR_DISCLOSURE_REQUIRED = "error_disclosure_required"


_NON_LIVE_LABELS: frozenset[SurfaceTruthLabel] = frozenset(
    {
        SurfaceTruthLabel.CONTRACT_ONLY,
        SurfaceTruthLabel.READ_MODEL_ONLY,
        SurfaceTruthLabel.PROJECTION_ONLY,
        SurfaceTruthLabel.DEV_FIXTURE,
        SurfaceTruthLabel.MOCK,
        SurfaceTruthLabel.SIMULATED,
        SurfaceTruthLabel.UNAVAILABLE,
        SurfaceTruthLabel.ERROR,
        SurfaceTruthLabel.NOT_LIVE,
        SurfaceTruthLabel.PERMISSION_MATRIX_CONTRACT_ONLY,
        SurfaceTruthLabel.UNAVAILABLE_STATE_CONTRACT_ONLY,
        SurfaceTruthLabel.FIXTURE_DISCLOSURE_ONLY,
    }
)

FORBIDDEN_TRUTH_LABELS_BY_DEFAULT: frozenset[str] = frozenset(
    {
        "PERMISSION_GRANTED",
        "AUTHORIZED_BY_MATRIX",
        "CUSTOS_REPLACED",
        "RUNTIME_PERMISSION_ENFORCED",
        "SYSTEM_AGENT_ACCESS",
        "ROOT_AUTHORITY_GRANTED",
        "TOOL_EXECUTED",
        "WORKFLOW_STARTED",
        "MEMORY_WRITTEN",
        "TRACE_WRITTEN",
        "PRODUCTION_DATA",
        "FIXTURE_AS_TRUTH",
        "MOCK_AS_LIVE",
        "SIMULATED_AS_LIVE",
        "P2_0_E_DONE",
        "P2_READY_FOR_CODING",
    }
)

_TRUTH_NON_GOALS: tuple[str, ...] = (
    "no_live_shell_path",
    "no_trace_verification_implementation",
    "no_ui_rendering",
    "no_production_proof",
)


@dataclass(frozen=True)
class SurfaceTruthBoundary(_CanonicalMixin):
    """Global truth-label guardrails for AurelShell surface state."""

    surface_state_has_truth_label: bool
    truth_label_requires_evidence: bool
    live_requires_tested_path: bool
    trace_verified_requires_actual_verification: bool
    dev_fixture_not_live: bool
    mock_not_live: bool
    simulated_not_live: bool
    unavailable_not_live: bool
    truth_label_is_not_proof: bool


@dataclass(frozen=True)
class SurfaceTruthLabelContract(_CanonicalMixin):
    """P2.0.18 contract: every surface state carries an honest label."""

    schema_version: str
    surface_state_has_truth_label: bool
    truth_label_requires_evidence: bool
    allowed_truth_labels: tuple[SurfaceTruthLabel, ...]
    forbidden_default_labels: tuple[str, ...]
    truth_boundary: SurfaceTruthBoundary
    non_goals: tuple[str, ...]
    contract_hash: str


@dataclass(frozen=True)
class SurfaceTruthClaim(_CanonicalMixin):
    """A truth label claim with explicit evidence requirements."""

    schema_version: str
    surface_id: str
    surface_kind: AurelSurfaceKind
    claim_id: str
    truth_label: SurfaceTruthLabel
    claim_scope: str
    evidence_requirement: SurfaceTruthEvidenceRequirement
    evidence_refs: tuple[str, ...]
    is_live_claim: bool
    is_trace_verified_claim: bool
    requires_tested_path: bool
    requires_actual_verification: bool
    is_fixture_label: bool
    is_mock_label: bool
    is_simulated_label: bool
    is_unavailable_label: bool
    allowed_without_evidence: bool
    truth_boundary: SurfaceTruthBoundary
    non_goals: tuple[str, ...]
    claim_hash: str


def _truth_boundary() -> SurfaceTruthBoundary:
    return SurfaceTruthBoundary(
        surface_state_has_truth_label=True,
        truth_label_requires_evidence=True,
        live_requires_tested_path=True,
        trace_verified_requires_actual_verification=True,
        dev_fixture_not_live=True,
        mock_not_live=True,
        simulated_not_live=True,
        unavailable_not_live=True,
        truth_label_is_not_proof=True,
    )


def build_surface_truth_label_contract() -> SurfaceTruthLabelContract:
    payload = {
        "schema_version": AUREL_TRUTH_LABEL_CONTRACT_VERSION,
        "surface_state_has_truth_label": True,
        "truth_label_requires_evidence": True,
        "allowed_truth_labels": tuple(SurfaceTruthLabel),
        "forbidden_default_labels": tuple(sorted(FORBIDDEN_TRUTH_LABELS_BY_DEFAULT)),
        "truth_boundary": _truth_boundary(),
        "non_goals": _TRUTH_NON_GOALS,
    }
    return SurfaceTruthLabelContract(**payload, contract_hash=_hash_payload(payload))


def _evidence_requirement_for(
    truth_label: SurfaceTruthLabel,
) -> SurfaceTruthEvidenceRequirement:
    if truth_label is SurfaceTruthLabel.LIVE:
        return SurfaceTruthEvidenceRequirement.TESTED_LIVE_PATH_REQUIRED
    if truth_label is SurfaceTruthLabel.TRACE_VERIFIED:
        return SurfaceTruthEvidenceRequirement.ACTUAL_TRACE_VERIFICATION_REQUIRED
    if truth_label in {
        SurfaceTruthLabel.DEV_FIXTURE,
        SurfaceTruthLabel.MOCK,
        SurfaceTruthLabel.SIMULATED,
    }:
        return SurfaceTruthEvidenceRequirement.VISIBLE_FIXTURE_DISCLOSURE_REQUIRED
    if truth_label is SurfaceTruthLabel.UNAVAILABLE:
        return SurfaceTruthEvidenceRequirement.UNAVAILABLE_REASON_REQUIRED
    if truth_label is SurfaceTruthLabel.ERROR:
        return SurfaceTruthEvidenceRequirement.ERROR_DISCLOSURE_REQUIRED
    return SurfaceTruthEvidenceRequirement.CONTRACT_OBJECT_REQUIRED


def build_surface_truth_claim(
    *,
    surface_id: str,
    surface_kind: AurelSurfaceKind | str,
    claim_id: str,
    truth_label: SurfaceTruthLabel | str = SurfaceTruthLabel.CONTRACT_ONLY,
    claim_scope: str = "surface_state_contract",
    evidence_requirement: SurfaceTruthEvidenceRequirement | str | None = None,
    evidence_refs: tuple[str, ...] = (),
    allowed_without_evidence: bool = False,
) -> SurfaceTruthClaim:
    if isinstance(surface_kind, str):
        surface_kind = AurelSurfaceKind(surface_kind)
    if isinstance(truth_label, str):
        truth_label = SurfaceTruthLabel(truth_label)
    if evidence_requirement is None:
        evidence_requirement = _evidence_requirement_for(truth_label)
    elif isinstance(evidence_requirement, str):
        evidence_requirement = SurfaceTruthEvidenceRequirement(evidence_requirement)

    payload = {
        "schema_version": AUREL_TRUTH_CLAIM_VERSION,
        "surface_id": surface_id,
        "surface_kind": surface_kind,
        "claim_id": claim_id,
        "truth_label": truth_label,
        "claim_scope": claim_scope,
        "evidence_requirement": evidence_requirement,
        "evidence_refs": tuple(evidence_refs),
        "is_live_claim": truth_label is SurfaceTruthLabel.LIVE,
        "is_trace_verified_claim": truth_label is SurfaceTruthLabel.TRACE_VERIFIED,
        "requires_tested_path": truth_label is SurfaceTruthLabel.LIVE,
        "requires_actual_verification": truth_label
        is SurfaceTruthLabel.TRACE_VERIFIED,
        "is_fixture_label": truth_label is SurfaceTruthLabel.DEV_FIXTURE,
        "is_mock_label": truth_label is SurfaceTruthLabel.MOCK,
        "is_simulated_label": truth_label is SurfaceTruthLabel.SIMULATED,
        "is_unavailable_label": truth_label is SurfaceTruthLabel.UNAVAILABLE,
        "allowed_without_evidence": allowed_without_evidence,
        "truth_boundary": _truth_boundary(),
        "non_goals": _TRUTH_NON_GOALS,
    }
    claim = SurfaceTruthClaim(**payload, claim_hash=_hash_payload(payload))
    assert_live_requires_tested_path(claim)
    assert_trace_verified_requires_actual_verification(claim)
    assert_dev_fixture_is_not_live(claim)
    assert_mock_is_not_live(claim)
    assert_simulated_is_not_live(claim)
    assert_unavailable_is_not_live(claim)
    return claim


def build_surface_truth_snapshot(
    registry: AurelSurfaceRegistry | None = None,
) -> tuple[SurfaceTruthClaim, ...]:
    if registry is None:
        registry = build_default_surface_registry()
    return tuple(
        build_surface_truth_claim(
            surface_id=surface.surface_id,
            surface_kind=surface.surface_kind,
            claim_id=f"{surface.surface_id}:truth_label_contract",
            truth_label=SurfaceTruthLabel.CONTRACT_ONLY,
            claim_scope="surface_state_contract",
            evidence_refs=(surface.surface_contract_hash,),
        )
        for surface in registry.surfaces
    )


def assert_live_requires_tested_path(claim: SurfaceTruthClaim) -> None:
    if claim.truth_label is SurfaceTruthLabel.LIVE:
        if not claim.requires_tested_path:
            _reject(
                "LIVE truth claim must require a tested live path",
                field="requires_tested_path",
                code=AurelShellErrorCode.INVALID_TRUTH_LABEL,
            )
        if not claim.evidence_refs:
            _reject(
                "LIVE truth claim requires tested live path evidence",
                field="evidence_refs",
                code=AurelShellErrorCode.INVALID_TRUTH_LABEL,
            )


def assert_trace_verified_requires_actual_verification(
    claim: SurfaceTruthClaim,
) -> None:
    if claim.truth_label is SurfaceTruthLabel.TRACE_VERIFIED:
        if not claim.requires_actual_verification:
            _reject(
                "TRACE_VERIFIED must require actual verification",
                field="requires_actual_verification",
                code=AurelShellErrorCode.INVALID_TRUTH_LABEL,
            )
        if not claim.evidence_refs:
            _reject(
                "TRACE_VERIFIED requires actual trace verification evidence",
                field="evidence_refs",
                code=AurelShellErrorCode.INVALID_TRUTH_LABEL,
            )


def assert_dev_fixture_is_not_live(claim: SurfaceTruthClaim) -> None:
    if claim.truth_label is SurfaceTruthLabel.DEV_FIXTURE and claim.is_live_claim:
        _reject(
            "DEV_FIXTURE must not be LIVE",
            field="truth_label",
            code=AurelShellErrorCode.INVALID_TRUTH_LABEL,
        )


def assert_mock_is_not_live(claim: SurfaceTruthClaim) -> None:
    if claim.truth_label is SurfaceTruthLabel.MOCK and claim.is_live_claim:
        _reject(
            "MOCK must not be LIVE",
            field="truth_label",
            code=AurelShellErrorCode.INVALID_TRUTH_LABEL,
        )


def assert_simulated_is_not_live(claim: SurfaceTruthClaim) -> None:
    if claim.truth_label is SurfaceTruthLabel.SIMULATED and claim.is_live_claim:
        _reject(
            "SIMULATED must not be LIVE",
            field="truth_label",
            code=AurelShellErrorCode.INVALID_TRUTH_LABEL,
        )


def assert_unavailable_is_not_live(claim: SurfaceTruthClaim) -> None:
    if claim.truth_label is SurfaceTruthLabel.UNAVAILABLE and claim.is_live_claim:
        _reject(
            "UNAVAILABLE must not be LIVE",
            field="truth_label",
            code=AurelShellErrorCode.INVALID_TRUTH_LABEL,
        )
    if claim.truth_label in _NON_LIVE_LABELS and claim.is_live_claim:
        _reject(
            f"{claim.truth_label.value} must not be LIVE",
            field="truth_label",
            code=AurelShellErrorCode.INVALID_TRUTH_LABEL,
        )
