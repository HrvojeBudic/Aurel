"""Path normalization and escape signal detection (P1.7.5).

String-level normalization only — no filesystem access, resolver behavior,
authority decisions, sandbox policy, or runtime enforcement.
"""
from __future__ import annotations

import re
from collections.abc import Mapping as MappingABC
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
from .serialization import stable_hash
from .validation import validate_known_fields

PATH_NORMALIZATION_TASK_ID = "P1.7.5"
PATH_NORMALIZATION_VERSION = "path_normalization.v1"

PATH_NORMALIZATION_RESULT_KNOWN_FIELDS: frozenset[str] = frozenset({
    "raw_path",
    "normalized_path",
    "display_path",
    "normalization_status",
    "signals",
    "warnings",
    "source_label",
    "result_hash",
    "contract_version",
    "metadata",
})

_WINDOWS_DRIVE_PATTERN = re.compile(r"^[A-Za-z]:")


class PathNormalizationStatus(str, Enum):
    """String normalization outcome; not safety, permission, or authority."""

    NORMALIZED = "NORMALIZED"
    NORMALIZED_WITH_WARNINGS = "NORMALIZED_WITH_WARNINGS"
    UNRESOLVED = "UNRESOLVED"
    UNSUPPORTED = "UNSUPPORTED"
    ERROR = "ERROR"


class PathEscapeSignal(str, Enum):
    """Candidate escape signal; shadow observation only, never enforcement."""

    TRAVERSAL_SEGMENT = "TRAVERSAL_SEGMENT"
    ABSOLUTE_PATH_WITHOUT_ROOT_CONTEXT = "ABSOLUTE_PATH_WITHOUT_ROOT_CONTEXT"
    ROOT_MISMATCH_CANDIDATE = "ROOT_MISMATCH_CANDIDATE"
    WINDOWS_DRIVE_PREFIX = "WINDOWS_DRIVE_PREFIX"
    HOME_EXPANSION_CANDIDATE = "HOME_EXPANSION_CANDIDATE"
    UNC_PATH_CANDIDATE = "UNC_PATH_CANDIDATE"
    MIXED_SEPARATOR_CANDIDATE = "MIXED_SEPARATOR_CANDIDATE"
    EMPTY_PATH = "EMPTY_PATH"
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


def _parse_normalization_status(
    value: PathNormalizationStatus | str,
) -> PathNormalizationStatus:
    if isinstance(value, PathNormalizationStatus):
        return value
    if isinstance(value, str):
        try:
            return PathNormalizationStatus(value)
        except ValueError as exc:
            raise PathGovernanceError(
                f"invalid normalization_status: {value!r}",
                code=PathGovernanceErrorCode.INVALID_ENUM,
                field="normalization_status",
            ) from exc
    raise PathGovernanceError(
        "normalization_status must be a string or PathNormalizationStatus",
        code=PathGovernanceErrorCode.INVALID_ENUM,
        field="normalization_status",
    )


def _parse_escape_signal(value: PathEscapeSignal | str) -> PathEscapeSignal:
    if isinstance(value, PathEscapeSignal):
        return value
    if isinstance(value, str):
        try:
            return PathEscapeSignal(value)
        except ValueError as exc:
            raise PathGovernanceError(
                f"invalid signal: {value!r}",
                code=PathGovernanceErrorCode.INVALID_ENUM,
                field="signals",
            ) from exc
    raise PathGovernanceError(
        "signal must be a string or PathEscapeSignal",
        code=PathGovernanceErrorCode.INVALID_ENUM,
        field="signals",
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


def _freeze_signals(
    signals: tuple[PathEscapeSignal, ...] | list[PathEscapeSignal | str] | None,
) -> tuple[PathEscapeSignal, ...]:
    raw = () if signals is None else signals
    if isinstance(raw, str) or not isinstance(raw, (tuple, list)):
        raise PathGovernanceValidationError(
            "signals must be a list or tuple of PathEscapeSignal values",
            code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
            field="signals",
        )
    parsed = tuple(_parse_escape_signal(item) for item in raw)
    return tuple(sorted(parsed, key=lambda item: item.value))


def _freeze_warnings(warnings: tuple[str, ...] | list[str] | None) -> tuple[str, ...]:
    raw = () if warnings is None else warnings
    if isinstance(raw, str) or not isinstance(raw, (tuple, list)):
        raise PathGovernanceValidationError(
            "warnings must be a list or tuple of strings",
            code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
            field="warnings",
        )
    return tuple(str(item) for item in raw)


def _normalize_governance_string(raw_path: str) -> str:
    """Normalize path at string level without resolving .. or touching filesystem."""
    path = raw_path.strip().replace("\\", "/")
    is_absolute = path.startswith("/")
    parts: list[str] = []
    for segment in path.split("/"):
        if segment in ("", "."):
            continue
        parts.append(segment)
    normalized = "/".join(parts)
    if is_absolute:
        normalized = f"/{normalized}" if normalized else "/"
    return normalized


def _detect_escape_signals(raw_path: str, normalized_path: str) -> tuple[PathEscapeSignal, ...]:
    """Detect candidate escape signals from raw and normalized strings."""
    signals: list[PathEscapeSignal] = []

    if raw_path.strip() == "":
        signals.append(PathEscapeSignal.EMPTY_PATH)
        return tuple(sorted(signals, key=lambda item: item.value))

    if "\\" in raw_path and "/" in raw_path:
        signals.append(PathEscapeSignal.MIXED_SEPARATOR_CANDIDATE)

    if _WINDOWS_DRIVE_PATTERN.match(raw_path.lstrip()) or _WINDOWS_DRIVE_PATTERN.match(
        normalized_path.lstrip(),
    ):
        signals.append(PathEscapeSignal.WINDOWS_DRIVE_PREFIX)

    if raw_path.startswith("\\\\") or raw_path.startswith("//"):
        signals.append(PathEscapeSignal.UNC_PATH_CANDIDATE)

    if raw_path.startswith("~") or "/~" in raw_path or "\\~" in raw_path:
        signals.append(PathEscapeSignal.HOME_EXPANSION_CANDIDATE)

    if ".." in normalized_path.split("/"):
        signals.append(PathEscapeSignal.TRAVERSAL_SEGMENT)

    if normalized_path.startswith("/"):
        signals.append(PathEscapeSignal.ABSOLUTE_PATH_WITHOUT_ROOT_CONTEXT)

    if not signals:
        return ()
    return tuple(sorted(set(signals), key=lambda item: item.value))


def _normalization_warnings(signals: tuple[PathEscapeSignal, ...]) -> tuple[str, ...]:
    warnings: list[str] = []
    for signal in signals:
        if signal is PathEscapeSignal.TRAVERSAL_SEGMENT:
            warnings.append(
                "Traversal-like segments preserved; candidate signal only, not enforcement",
            )
        elif signal is PathEscapeSignal.EMPTY_PATH:
            warnings.append("Empty path input; candidate signal only, not enforcement")
        elif signal is PathEscapeSignal.ABSOLUTE_PATH_WITHOUT_ROOT_CONTEXT:
            warnings.append(
                "Absolute path without root context; candidate signal only, not enforcement",
            )
        elif signal is PathEscapeSignal.WINDOWS_DRIVE_PREFIX:
            warnings.append(
                "Windows drive prefix detected; candidate signal only, not enforcement",
            )
        elif signal is PathEscapeSignal.UNC_PATH_CANDIDATE:
            warnings.append("UNC path detected; candidate signal only, not enforcement")
        elif signal is PathEscapeSignal.HOME_EXPANSION_CANDIDATE:
            warnings.append(
                "Home expansion detected; candidate signal only, not enforcement",
            )
        elif signal is PathEscapeSignal.MIXED_SEPARATOR_CANDIDATE:
            warnings.append(
                "Mixed path separators detected; candidate signal only, not enforcement",
            )
        elif signal is PathEscapeSignal.ROOT_MISMATCH_CANDIDATE:
            warnings.append(
                "Root mismatch candidate detected; candidate signal only, not enforcement",
            )
        elif signal is PathEscapeSignal.UNKNOWN:
            warnings.append("Unknown path signal; candidate signal only, not enforcement")
    return tuple(warnings)


def _select_normalization_status(
    signals: tuple[PathEscapeSignal, ...],
    *,
    is_empty: bool,
) -> PathNormalizationStatus:
    if is_empty:
        return PathNormalizationStatus.ERROR
    if PathEscapeSignal.UNKNOWN in signals:
        return PathNormalizationStatus.UNRESOLVED
    if signals:
        return PathNormalizationStatus.NORMALIZED_WITH_WARNINGS
    return PathNormalizationStatus.NORMALIZED


def compute_normalization_result_hash(
    *,
    raw_path: str,
    normalized_path: str,
    display_path: str,
    normalization_status: PathNormalizationStatus,
    signals: tuple[PathEscapeSignal, ...],
    warnings: tuple[str, ...],
    source_label: ProjectionSourceLabel,
    contract_version: str,
    metadata: Mapping[str, Any],
) -> str:
    """Compute deterministic normalization result hash."""
    return stable_hash({
        "contract_version": contract_version,
        "display_path": display_path,
        "metadata": dict(sorted(metadata.items(), key=lambda item: item[0])),
        "normalization_status": normalization_status.value,
        "normalized_path": normalized_path,
        "raw_path": raw_path,
        "signals": [item.value for item in signals],
        "source_label": source_label.value,
        "warnings": list(warnings),
    })


@dataclass(frozen=True)
class PathNormalizationResult:
    """Deterministic path normalization result; not permission or enforcement."""

    raw_path: str
    normalized_path: str
    display_path: str
    normalization_status: PathNormalizationStatus
    signals: tuple[PathEscapeSignal, ...] = field(default_factory=tuple)
    warnings: tuple[str, ...] = field(default_factory=tuple)
    source_label: ProjectionSourceLabel = ProjectionSourceLabel.LIVE
    result_hash: str = ""
    contract_version: str = PATH_NORMALIZATION_VERSION
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.raw_path, str):
            raise PathGovernanceValidationError(
                "raw_path must be a string",
                code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
                field="raw_path",
            )
        if self.contract_version != PATH_NORMALIZATION_VERSION:
            raise PathGovernanceValidationError(
                "contract_version must be path_normalization.v1",
                code=PathGovernanceErrorCode.INVALID_VERSION,
                field="contract_version",
            )
        normalization_status = _parse_normalization_status(self.normalization_status)
        source_label = _parse_source_label(self.source_label)
        signals = _freeze_signals(self.signals)
        warnings = _freeze_warnings(self.warnings)
        metadata = _freeze_metadata(self.metadata)

        if normalization_status is PathNormalizationStatus.ERROR:
            normalized_path = self.normalized_path if isinstance(self.normalized_path, str) else ""
            display_path = self.display_path if isinstance(self.display_path, str) else ""
        else:
            if not isinstance(self.normalized_path, str):
                raise PathGovernanceValidationError(
                    "normalized_path must be a string",
                    code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
                    field="normalized_path",
                )
            if not isinstance(self.display_path, str):
                raise PathGovernanceValidationError(
                    "display_path must be a string",
                    code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
                    field="display_path",
                )
            normalized_path = self.normalized_path
            display_path = self.display_path

        result_hash = compute_normalization_result_hash(
            raw_path=self.raw_path,
            normalized_path=normalized_path,
            display_path=display_path,
            normalization_status=normalization_status,
            signals=signals,
            warnings=warnings,
            source_label=source_label,
            contract_version=self.contract_version,
            metadata=metadata,
        )
        if self.result_hash not in ("", result_hash):
            raise PathGovernanceValidationError(
                "result_hash does not match normalization content",
                code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
                field="result_hash",
            )
        object.__setattr__(self, "normalization_status", normalization_status)
        object.__setattr__(self, "source_label", source_label)
        object.__setattr__(self, "signals", signals)
        object.__setattr__(self, "warnings", warnings)
        object.__setattr__(self, "metadata", metadata)
        object.__setattr__(self, "normalized_path", normalized_path)
        object.__setattr__(self, "display_path", display_path)
        object.__setattr__(self, "result_hash", result_hash)

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "contract_version": self.contract_version,
            "display_path": self.display_path,
            "metadata": dict(sorted(self.metadata.items(), key=lambda item: item[0])),
            "normalization_status": self.normalization_status.value,
            "normalized_path": self.normalized_path,
            "raw_path": self.raw_path,
            "result_hash": self.result_hash,
            "signals": [item.value for item in self.signals],
            "source_label": self.source_label.value,
            "warnings": list(self.warnings),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> PathNormalizationResult:
        validate_known_fields(
            data,
            PATH_NORMALIZATION_RESULT_KNOWN_FIELDS,
            label="path_normalization_result",
        )
        return cls(
            raw_path=data["raw_path"],
            normalized_path=data.get("normalized_path", ""),
            display_path=data.get("display_path", ""),
            normalization_status=data.get(
                "normalization_status",
                PathNormalizationStatus.UNRESOLVED,
            ),
            signals=data.get("signals", ()),
            warnings=data.get("warnings", ()),
            source_label=data.get("source_label", ProjectionSourceLabel.LIVE),
            result_hash=data.get("result_hash", ""),
            contract_version=data.get("contract_version", PATH_NORMALIZATION_VERSION),
            metadata=data.get("metadata", {}),
        )


def normalize_path_for_governance(
    raw_path: str,
    source_label: ProjectionSourceLabel = ProjectionSourceLabel.LIVE,
    metadata: Mapping[str, Any] | None = None,
) -> PathNormalizationResult:
    """Normalize a path string for governance without filesystem access."""
    if not isinstance(raw_path, str):
        raise PathGovernanceValidationError(
            "raw_path must be an explicit string",
            code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
            field="raw_path",
        )

    frozen_metadata = _freeze_metadata(metadata)
    parsed_source_label = _parse_source_label(source_label)

    if raw_path.strip() == "":
        signals = (PathEscapeSignal.EMPTY_PATH,)
        warnings = _normalization_warnings(signals)
        return PathNormalizationResult(
            raw_path=raw_path,
            normalized_path="",
            display_path="",
            normalization_status=PathNormalizationStatus.ERROR,
            signals=signals,
            warnings=warnings,
            source_label=parsed_source_label,
            metadata=frozen_metadata,
        )

    normalized_path = _normalize_governance_string(raw_path)
    display_path = normalized_path
    signals = _detect_escape_signals(raw_path, normalized_path)
    warnings = _normalization_warnings(signals)
    normalization_status = _select_normalization_status(signals, is_empty=False)

    return PathNormalizationResult(
        raw_path=raw_path,
        normalized_path=normalized_path,
        display_path=display_path,
        normalization_status=normalization_status,
        signals=signals,
        warnings=warnings,
        source_label=parsed_source_label,
        metadata=frozen_metadata,
    )
