"""Path escape candidate detection contract (P1.7.5).

Boundary checks use only supplied PathIdentity, TrustedRoot, or
TrustedRootRegistry data with segment-aware string comparison.
Shadow-only — never runtime denial or block.
"""
from __future__ import annotations

from collections.abc import Mapping as MappingABC, Sequence
from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping

from .errors import (
    PathGovernanceError,
    PathGovernanceErrorCode,
    PathGovernanceValidationError,
)
from .labels import ProjectionSourceLabel
from .path_identity import PathIdentity
from .path_normalization import (
    PathEscapeSignal,
    PathNormalizationResult,
    normalize_path_for_governance,
)
from .serialization import stable_hash
from .trusted_roots import TrustedRoot, TrustedRootRegistry
from .validation import validate_known_fields

PATH_ESCAPE_DETECTION_TASK_ID = "P1.7.5"
PATH_ESCAPE_DETECTION_VERSION = "path_escape_detection_contract.v1"

PATH_BOUNDARY_CHECK_RESULT_KNOWN_FIELDS: frozenset[str] = frozenset({
    "raw_path",
    "normalized_path",
    "status",
    "escape_signals",
    "matched_root_id",
    "comparison_root_id",
    "source_label",
    "shadow_only",
    "enforced",
    "result_hash",
    "contract_version",
    "metadata",
})

ESCAPE_DETECTION_CONTRACT_KNOWN_FIELDS: frozenset[str] = frozenset({
    "contract_version",
    "created_by_task",
    "normalization_result",
    "boundary_result",
    "source_label",
    "notes",
    "metadata",
    "contract_hash",
})


class PathBoundaryStatus(str, Enum):
    """Candidate boundary classification; not safe, authorized, or enforced."""

    PATH_OK = "PATH_OK"
    PATH_OUTSIDE_TRUSTED_ROOT = "PATH_OUTSIDE_TRUSTED_ROOT"
    PATH_TRAVERSAL_CANDIDATE = "PATH_TRAVERSAL_CANDIDATE"
    PATH_UNRESOLVED = "PATH_UNRESOLVED"
    UNKNOWN = "UNKNOWN"


def _parse_source_label(value: ProjectionSourceLabel | str) -> ProjectionSourceLabel:
    if isinstance(value, ProjectionSourceLabel):
        return value
    if isinstance(value, str):
        try:
            return ProjectionSourceLabel(value)
        except ValueError as exc:
            raise PathGovernanceError(
                f"invalid source_label: {value!r}",
                code=PathGovernanceErrorCode.INVALID_SOURCE_LABEL,
                field="source_label",
            ) from exc
    raise PathGovernanceError(
        "source_label must be a string or ProjectionSourceLabel",
        code=PathGovernanceErrorCode.INVALID_SOURCE_LABEL,
        field="source_label",
    )


def _parse_boundary_status(value: PathBoundaryStatus | str) -> PathBoundaryStatus:
    if isinstance(value, PathBoundaryStatus):
        return value
    if isinstance(value, str):
        try:
            return PathBoundaryStatus(value)
        except ValueError as exc:
            raise PathGovernanceError(
                f"invalid status: {value!r}",
                code=PathGovernanceErrorCode.INVALID_ENUM,
                field="status",
            ) from exc
    raise PathGovernanceError(
        "status must be a string or PathBoundaryStatus",
        code=PathGovernanceErrorCode.INVALID_ENUM,
        field="status",
    )


def _parse_escape_signal(value: PathEscapeSignal | str) -> PathEscapeSignal:
    if isinstance(value, PathEscapeSignal):
        return value
    if isinstance(value, str):
        try:
            return PathEscapeSignal(value)
        except ValueError as exc:
            raise PathGovernanceError(
                f"invalid escape signal: {value!r}",
                code=PathGovernanceErrorCode.INVALID_ENUM,
                field="escape_signals",
            ) from exc
    raise PathGovernanceError(
        "escape signal must be a string or PathEscapeSignal",
        code=PathGovernanceErrorCode.INVALID_ENUM,
        field="escape_signals",
    )


def _freeze_metadata(metadata: Mapping[str, Any] | None) -> Mapping[str, Any]:
    raw = {} if metadata is None else metadata
    if not isinstance(raw, MappingABC):
        raise PathGovernanceValidationError(
            "metadata must be a mapping",
            code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
            field="metadata",
        )
    frozen = dict(raw)
    stable_hash(frozen)
    return MappingProxyType(frozen)


def _freeze_escape_signals(
    signals: tuple[PathEscapeSignal, ...] | list[PathEscapeSignal | str] | None,
) -> tuple[PathEscapeSignal, ...]:
    raw = () if signals is None else signals
    if isinstance(raw, str) or not isinstance(raw, (tuple, list)):
        raise PathGovernanceValidationError(
            "escape_signals must be a list or tuple of PathEscapeSignal values",
            code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
            field="escape_signals",
        )
    parsed = tuple(_parse_escape_signal(item) for item in raw)
    return tuple(sorted(parsed, key=lambda item: item.value))


def _freeze_notes(notes: Sequence[str] | None) -> tuple[str, ...]:
    raw = () if notes is None else notes
    if isinstance(raw, str) or not isinstance(raw, Sequence):
        raise PathGovernanceValidationError(
            "notes must be a sequence of strings",
            code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
            field="notes",
        )
    return tuple(str(item) for item in raw)


def _optional_root_id(value: Any) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or value == "":
        raise PathGovernanceValidationError(
            "root id fields must be a non-empty string or None",
            code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
            field="root_id",
        )
    return value


def _path_segments(path: str) -> tuple[str, ...]:
    return tuple(segment for segment in path.split("/") if segment)


def _path_under_root(normalized_path: str, root_path: str) -> bool:
    """Segment-aware prefix comparison without filesystem access."""
    path_segments = _path_segments(normalized_path)
    root_segments = _path_segments(root_path)
    if not root_segments:
        return False
    if len(path_segments) < len(root_segments):
        return False
    return path_segments[: len(root_segments)] == root_segments


def _resolve_input_path(
    *,
    path_identity: PathIdentity | None,
    raw_path: str | None,
) -> tuple[str, str]:
    if path_identity is not None and raw_path is not None:
        identity_raw = path_identity.path_ref.raw_path
        if identity_raw != raw_path:
            raise PathGovernanceValidationError(
                "path_identity and raw_path conflict; supply one authoritative input",
                code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
                field="raw_path",
            )
    if path_identity is not None:
        return (
            path_identity.path_ref.raw_path,
            path_identity.canonical_ref.normalized_path,
        )
    if raw_path is not None:
        if not isinstance(raw_path, str):
            raise PathGovernanceValidationError(
                "raw_path must be a string",
                code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
                field="raw_path",
            )
        normalization = normalize_path_for_governance(raw_path)
        return raw_path, normalization.normalized_path
    raise PathGovernanceValidationError(
        "path_identity or raw_path is required",
        code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
        field="raw_path",
    )


def _collect_trusted_roots(
    *,
    trusted_root: TrustedRoot | None,
    trusted_root_registry: TrustedRootRegistry | None,
) -> tuple[TrustedRoot, ...]:
    if trusted_root is not None and trusted_root_registry is not None:
        raise PathGovernanceValidationError(
            "trusted_root and trusted_root_registry are mutually exclusive inputs",
            code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
            field="trusted_root_registry",
        )
    if trusted_root is not None:
        return (trusted_root,)
    if trusted_root_registry is not None:
        return trusted_root_registry.trusted_roots
    return ()


def compute_boundary_result_hash(
    *,
    raw_path: str,
    normalized_path: str,
    status: PathBoundaryStatus,
    escape_signals: tuple[PathEscapeSignal, ...],
    matched_root_id: str | None,
    comparison_root_id: str | None,
    source_label: ProjectionSourceLabel,
    shadow_only: bool,
    enforced: bool,
    contract_version: str,
    metadata: Mapping[str, Any],
) -> str:
    """Compute deterministic boundary check result hash."""
    return stable_hash({
        "comparison_root_id": comparison_root_id,
        "contract_version": contract_version,
        "enforced": enforced,
        "escape_signals": [item.value for item in escape_signals],
        "matched_root_id": matched_root_id,
        "metadata": dict(sorted(metadata.items(), key=lambda item: item[0])),
        "normalized_path": normalized_path,
        "raw_path": raw_path,
        "shadow_only": shadow_only,
        "source_label": source_label.value,
        "status": status.value,
    })


@dataclass(frozen=True)
class PathBoundaryCheckResult:
    """Shadow boundary check result; candidate classification only."""

    raw_path: str
    normalized_path: str
    status: PathBoundaryStatus
    escape_signals: tuple[PathEscapeSignal, ...] = field(default_factory=tuple)
    matched_root_id: str | None = None
    comparison_root_id: str | None = None
    source_label: ProjectionSourceLabel = ProjectionSourceLabel.LIVE
    shadow_only: bool = True
    enforced: bool = False
    result_hash: str = ""
    contract_version: str = PATH_ESCAPE_DETECTION_VERSION
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.raw_path, str):
            raise PathGovernanceValidationError(
                "raw_path must be a string",
                code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
                field="raw_path",
            )
        if not isinstance(self.normalized_path, str):
            raise PathGovernanceValidationError(
                "normalized_path must be a string",
                code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
                field="normalized_path",
            )
        if self.contract_version != PATH_ESCAPE_DETECTION_VERSION:
            raise PathGovernanceValidationError(
                "contract_version must be path_escape_detection_contract.v1",
                code=PathGovernanceErrorCode.INVALID_VERSION,
                field="contract_version",
            )
        if self.enforced is not False:
            raise PathGovernanceValidationError(
                "enforced must remain False for P1.7.5 shadow-only boundary checks",
                code=PathGovernanceErrorCode.ENFORCEMENT_NOT_AVAILABLE,
                field="enforced",
            )
        if self.shadow_only is not True:
            raise PathGovernanceValidationError(
                "shadow_only must remain True for P1.7.5 shadow-only boundary checks",
                code=PathGovernanceErrorCode.ENFORCEMENT_NOT_AVAILABLE,
                field="shadow_only",
            )
        status = _parse_boundary_status(self.status)
        source_label = _parse_source_label(self.source_label)
        escape_signals = _freeze_escape_signals(self.escape_signals)
        matched_root_id = _optional_root_id(self.matched_root_id)
        comparison_root_id = _optional_root_id(self.comparison_root_id)
        metadata = _freeze_metadata(self.metadata)
        result_hash = compute_boundary_result_hash(
            raw_path=self.raw_path,
            normalized_path=self.normalized_path,
            status=status,
            escape_signals=escape_signals,
            matched_root_id=matched_root_id,
            comparison_root_id=comparison_root_id,
            source_label=source_label,
            shadow_only=True,
            enforced=False,
            contract_version=self.contract_version,
            metadata=metadata,
        )
        if self.result_hash not in ("", result_hash):
            raise PathGovernanceValidationError(
                "result_hash does not match boundary check content",
                code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
                field="result_hash",
            )
        object.__setattr__(self, "status", status)
        object.__setattr__(self, "source_label", source_label)
        object.__setattr__(self, "escape_signals", escape_signals)
        object.__setattr__(self, "matched_root_id", matched_root_id)
        object.__setattr__(self, "comparison_root_id", comparison_root_id)
        object.__setattr__(self, "metadata", metadata)
        object.__setattr__(self, "result_hash", result_hash)

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "comparison_root_id": self.comparison_root_id,
            "contract_version": self.contract_version,
            "enforced": self.enforced,
            "escape_signals": [item.value for item in self.escape_signals],
            "matched_root_id": self.matched_root_id,
            "metadata": dict(sorted(self.metadata.items(), key=lambda item: item[0])),
            "normalized_path": self.normalized_path,
            "raw_path": self.raw_path,
            "result_hash": self.result_hash,
            "shadow_only": self.shadow_only,
            "source_label": self.source_label.value,
            "status": self.status.value,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> PathBoundaryCheckResult:
        validate_known_fields(
            data,
            PATH_BOUNDARY_CHECK_RESULT_KNOWN_FIELDS,
            label="path_boundary_check_result",
        )
        return cls(
            raw_path=data["raw_path"],
            normalized_path=data["normalized_path"],
            status=data.get("status", PathBoundaryStatus.UNKNOWN),
            escape_signals=data.get("escape_signals", ()),
            matched_root_id=data.get("matched_root_id"),
            comparison_root_id=data.get("comparison_root_id"),
            source_label=data.get("source_label", ProjectionSourceLabel.LIVE),
            shadow_only=data.get("shadow_only", True),
            enforced=data.get("enforced", False),
            result_hash=data.get("result_hash", ""),
            contract_version=data.get(
                "contract_version",
                PATH_ESCAPE_DETECTION_VERSION,
            ),
            metadata=data.get("metadata", {}),
        )


def compute_contract_hash(
    *,
    contract_version: str,
    created_by_task: str,
    normalization_result: PathNormalizationResult,
    boundary_result: PathBoundaryCheckResult,
    source_label: ProjectionSourceLabel,
    notes: tuple[str, ...],
    metadata: Mapping[str, Any],
) -> str:
    """Compute deterministic escape detection contract hash."""
    return stable_hash({
        "boundary_result": boundary_result.to_canonical_dict(),
        "contract_version": contract_version,
        "created_by_task": created_by_task,
        "metadata": dict(sorted(metadata.items(), key=lambda item: item[0])),
        "normalization_result": normalization_result.to_canonical_dict(),
        "notes": list(notes),
        "source_label": source_label.value,
    })


@dataclass(frozen=True)
class EscapeDetectionContract:
    """Small wrapper binding normalization and boundary shadow results."""

    normalization_result: PathNormalizationResult
    boundary_result: PathBoundaryCheckResult
    contract_hash: str = ""
    contract_version: str = PATH_ESCAPE_DETECTION_VERSION
    created_by_task: str = PATH_ESCAPE_DETECTION_TASK_ID
    source_label: ProjectionSourceLabel = ProjectionSourceLabel.LIVE
    notes: tuple[str, ...] = field(default_factory=tuple)
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.normalization_result, PathNormalizationResult):
            raise PathGovernanceValidationError(
                "normalization_result must be a PathNormalizationResult",
                code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
                field="normalization_result",
            )
        if not isinstance(self.boundary_result, PathBoundaryCheckResult):
            raise PathGovernanceValidationError(
                "boundary_result must be a PathBoundaryCheckResult",
                code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
                field="boundary_result",
            )
        if self.contract_version != PATH_ESCAPE_DETECTION_VERSION:
            raise PathGovernanceValidationError(
                "contract_version must be path_escape_detection_contract.v1",
                code=PathGovernanceErrorCode.INVALID_VERSION,
                field="contract_version",
            )
        if self.created_by_task != PATH_ESCAPE_DETECTION_TASK_ID:
            raise PathGovernanceValidationError(
                "created_by_task must be P1.7.5",
                code=PathGovernanceErrorCode.INVALID_VERSION,
                field="created_by_task",
            )
        source_label = _parse_source_label(self.source_label)
        notes = _freeze_notes(self.notes)
        metadata = _freeze_metadata(self.metadata)
        contract_hash = compute_contract_hash(
            contract_version=self.contract_version,
            created_by_task=self.created_by_task,
            normalization_result=self.normalization_result,
            boundary_result=self.boundary_result,
            source_label=source_label,
            notes=notes,
            metadata=metadata,
        )
        if self.contract_hash not in ("", contract_hash):
            raise PathGovernanceValidationError(
                "contract_hash does not match contract content",
                code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
                field="contract_hash",
            )
        object.__setattr__(self, "source_label", source_label)
        object.__setattr__(self, "notes", notes)
        object.__setattr__(self, "metadata", metadata)
        object.__setattr__(self, "contract_hash", contract_hash)

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "boundary_result": self.boundary_result.to_canonical_dict(),
            "contract_hash": self.contract_hash,
            "contract_version": self.contract_version,
            "created_by_task": self.created_by_task,
            "metadata": dict(sorted(self.metadata.items(), key=lambda item: item[0])),
            "normalization_result": self.normalization_result.to_canonical_dict(),
            "notes": list(self.notes),
            "source_label": self.source_label.value,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> EscapeDetectionContract:
        validate_known_fields(
            data,
            ESCAPE_DETECTION_CONTRACT_KNOWN_FIELDS,
            label="escape_detection_contract",
        )
        normalization = data["normalization_result"]
        boundary = data["boundary_result"]
        return cls(
            normalization_result=(
                normalization
                if isinstance(normalization, PathNormalizationResult)
                else PathNormalizationResult.from_dict(normalization)
            ),
            boundary_result=(
                boundary
                if isinstance(boundary, PathBoundaryCheckResult)
                else PathBoundaryCheckResult.from_dict(boundary)
            ),
            contract_hash=data.get("contract_hash", ""),
            contract_version=data.get(
                "contract_version",
                PATH_ESCAPE_DETECTION_VERSION,
            ),
            created_by_task=data.get("created_by_task", PATH_ESCAPE_DETECTION_TASK_ID),
            source_label=data.get("source_label", ProjectionSourceLabel.LIVE),
            notes=data.get("notes", ()),
            metadata=data.get("metadata", {}),
        )


def detect_path_escape_candidates(
    *,
    path_identity: PathIdentity | None = None,
    raw_path: str | None = None,
    trusted_root: TrustedRoot | None = None,
    trusted_root_registry: TrustedRootRegistry | None = None,
    source_label: ProjectionSourceLabel = ProjectionSourceLabel.LIVE,
    metadata: Mapping[str, Any] | None = None,
) -> EscapeDetectionContract:
    """Detect path escape candidates using supplied string context only."""
    parsed_source_label = _parse_source_label(source_label)
    frozen_metadata = _freeze_metadata(metadata)
    input_raw_path, normalized_path = _resolve_input_path(
        path_identity=path_identity,
        raw_path=raw_path,
    )
    normalization = normalize_path_for_governance(
        input_raw_path,
        source_label=parsed_source_label,
        metadata=frozen_metadata,
    )

    signals = list(normalization.escape_signals)
    roots = _collect_trusted_roots(
        trusted_root=trusted_root,
        trusted_root_registry=trusted_root_registry,
    )
    sorted_roots = tuple(sorted(roots, key=lambda item: item.root_id))

    if not sorted_roots:
        if normalized_path.startswith("/"):
            if PathEscapeSignal.ABSOLUTE_PATH_WITHOUT_ROOT_CONTEXT not in signals:
                signals.append(PathEscapeSignal.ABSOLUTE_PATH_WITHOUT_ROOT_CONTEXT)
        boundary = PathBoundaryCheckResult(
            raw_path=input_raw_path,
            normalized_path=normalized_path,
            status=PathBoundaryStatus.PATH_UNRESOLVED,
            escape_signals=tuple(sorted(set(signals), key=lambda item: item.value)),
            source_label=parsed_source_label,
            metadata=frozen_metadata,
        )
        return EscapeDetectionContract(
            normalization_result=normalization,
            boundary_result=boundary,
            source_label=parsed_source_label,
            notes=(
                "P1.7.5 escape detection is shadow-only candidate classification.",
                "PATH_UNRESOLVED means trusted root context was not supplied.",
                "PATH_OK would mean no candidate mismatch under supplied string context only.",
            ),
            metadata=frozen_metadata,
        )

    if PathEscapeSignal.TRAVERSAL_CANDIDATE in signals:
        comparison_root = sorted_roots[0]
        boundary = PathBoundaryCheckResult(
            raw_path=input_raw_path,
            normalized_path=normalized_path,
            status=PathBoundaryStatus.PATH_TRAVERSAL_CANDIDATE,
            escape_signals=tuple(sorted(set(signals), key=lambda item: item.value)),
            comparison_root_id=comparison_root.root_id,
            source_label=parsed_source_label,
            metadata=frozen_metadata,
        )
        return EscapeDetectionContract(
            normalization_result=normalization,
            boundary_result=boundary,
            source_label=parsed_source_label,
            notes=(
                "P1.7.5 escape detection is shadow-only candidate classification.",
                "PATH_TRAVERSAL_CANDIDATE is not runtime denial or block.",
            ),
            metadata=frozen_metadata,
        )

    matched_root: TrustedRoot | None = None
    for root in sorted_roots:
        root_path = root.path_identity.canonical_ref.normalized_path
        if _path_under_root(normalized_path, root_path):
            matched_root = root
            break

    comparison_root = matched_root or sorted_roots[0]
    if matched_root is not None:
        status = PathBoundaryStatus.PATH_OK
        matched_root_id = matched_root.root_id
        if PathEscapeSignal.ROOT_MISMATCH in signals:
            signals = [item for item in signals if item is not PathEscapeSignal.ROOT_MISMATCH]
    else:
        status = PathBoundaryStatus.PATH_OUTSIDE_TRUSTED_ROOT
        matched_root_id = None
        if PathEscapeSignal.ROOT_MISMATCH not in signals:
            signals.append(PathEscapeSignal.ROOT_MISMATCH)

    boundary = PathBoundaryCheckResult(
        raw_path=input_raw_path,
        normalized_path=normalized_path,
        status=status,
        escape_signals=tuple(sorted(set(signals), key=lambda item: item.value)),
        matched_root_id=matched_root_id,
        comparison_root_id=comparison_root.root_id,
        source_label=parsed_source_label,
        metadata=frozen_metadata,
    )
    return EscapeDetectionContract(
        normalization_result=normalization,
        boundary_result=boundary,
        source_label=parsed_source_label,
        notes=(
            "P1.7.5 escape detection is shadow-only candidate classification.",
            "PATH_OK means no candidate mismatch under supplied string context only.",
            "PATH_OUTSIDE_TRUSTED_ROOT is not runtime denial or block.",
        ),
        metadata=frozen_metadata,
    )
