"""P1.ENF-A identity submit context binding."""
from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Mapping

from .governance_enforcement import GovernanceEnforcementMode
from .identity.source_bundle import IdentitySourceBundle, load_identity_source_bundle


class IdentitySubmitContextStatus(str, Enum):
    BOUND = "bound"
    ADVISORY_MISSING = "advisory_missing"
    BLOCKED_MISSING_REQUIRED_CONTEXT = "blocked_missing_required_context"
    BLOCKED_INVALID_CONTEXT = "blocked_invalid_context"
    UNAVAILABLE = "unavailable"
    ERROR = "error"


class IdentityMissingContextBehavior(str, Enum):
    RECORD_ADVISORY = "record_advisory"
    FAIL_CLOSED = "fail_closed"
    MARK_UNAVAILABLE = "mark_unavailable"


@dataclass(frozen=True)
class IdentitySubmitContextHash:
    value: str

    def __post_init__(self) -> None:
        if len(self.value) != 64 or any(ch not in "0123456789abcdef" for ch in self.value):
            raise ValueError("identity submit context hash must be a SHA-256 hex digest")


@dataclass(frozen=True)
class IdentitySubmitContext:
    identity_kernel_hash: str
    persona_manifest_hash: str
    operator_contract_hash: str
    canonical_hashes: Mapping[str, str]
    raw_hashes: Mapping[str, str]
    source_paths: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for field_name in (
            "identity_kernel_hash",
            "persona_manifest_hash",
            "operator_contract_hash",
        ):
            value = getattr(self, field_name)
            if len(value) != 64 or any(ch not in "0123456789abcdef" for ch in value):
                raise ValueError(f"{field_name} must be a SHA-256 hex digest")

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "canonical_hashes": dict(sorted(self.canonical_hashes.items())),
            "identity_kernel_hash": self.identity_kernel_hash,
            "operator_contract_hash": self.operator_contract_hash,
            "persona_manifest_hash": self.persona_manifest_hash,
            "raw_hashes": dict(sorted(self.raw_hashes.items())),
            "source_paths": dict(sorted(self.source_paths.items())),
        }

    @property
    def context_hash(self) -> IdentitySubmitContextHash:
        payload = json.dumps(
            self.to_canonical_dict(),
            sort_keys=True,
            separators=(",", ":"),
        )
        return IdentitySubmitContextHash(hashlib.sha256(payload.encode("utf-8")).hexdigest())


@dataclass(frozen=True)
class IdentitySubmitArtifact:
    mode: GovernanceEnforcementMode
    status: IdentitySubmitContextStatus
    missing_behavior: IdentityMissingContextBehavior
    enforced: bool
    context_hash: str = ""
    identity_kernel_hash: str = ""
    persona_manifest_hash: str = ""
    operator_contract_hash: str = ""
    reason_codes: tuple[str, ...] = ()
    error_type: str = ""

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "context_hash": self.context_hash,
            "enforced": self.enforced,
            "error_type": self.error_type,
            "identity_kernel_hash": self.identity_kernel_hash,
            "missing_behavior": self.missing_behavior.value,
            "mode": self.mode.value,
            "operator_contract_hash": self.operator_contract_hash,
            "persona_manifest_hash": self.persona_manifest_hash,
            "reason_codes": sorted(self.reason_codes),
            "status": self.status.value,
        }

    @property
    def artifact_hash(self) -> str:
        payload = json.dumps(
            self.to_canonical_dict(),
            sort_keys=True,
            separators=(",", ":"),
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class IdentitySubmitPreflightResult:
    status: IdentitySubmitContextStatus
    should_block: bool
    artifact: IdentitySubmitArtifact
    context: IdentitySubmitContext | None = None

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "artifact": self.artifact.to_canonical_dict(),
            "artifact_hash": self.artifact.artifact_hash,
            "should_block": self.should_block,
            "status": self.status.value,
        }


IdentitySubmitContextLoader = Callable[[], IdentitySourceBundle | IdentitySubmitContext | None]


def build_identity_submit_context(
    bundle: IdentitySourceBundle | Mapping[str, Any],
) -> IdentitySubmitContext:
    if isinstance(bundle, IdentitySourceBundle):
        canonical_hashes = dict(bundle.canonical_hashes)
        raw_hashes = dict(bundle.raw_hashes)
        source_paths = {
            key: str(Path(path))
            for key, path in bundle.source_paths.items()
        }
    else:
        canonical_hashes = dict(bundle.get("canonical_hashes", {}))
        raw_hashes = dict(bundle.get("raw_hashes", {}))
        source_paths = dict(bundle.get("source_paths", {}))
    return IdentitySubmitContext(
        identity_kernel_hash=canonical_hashes["identity_kernel"],
        persona_manifest_hash=canonical_hashes["persona_manifest"],
        operator_contract_hash=canonical_hashes["operator_contract"],
        canonical_hashes=canonical_hashes,
        raw_hashes=raw_hashes,
        source_paths=source_paths,
    )


def load_default_identity_submit_context() -> IdentitySubmitContext:
    return build_identity_submit_context(load_identity_source_bundle())


def evaluate_identity_submit_preflight(
    *,
    mode: GovernanceEnforcementMode,
    require_identity_context: bool,
    loader: IdentitySubmitContextLoader | None,
) -> IdentitySubmitPreflightResult:
    missing_behavior = _missing_behavior(mode, require_identity_context)
    if mode is GovernanceEnforcementMode.DISABLED_UNAVAILABLE:
        return _result(
            mode,
            IdentitySubmitContextStatus.UNAVAILABLE,
            missing_behavior,
            should_block=False,
            enforced=False,
            reason_codes=("IDENTITY_SUBMIT_CONTEXT_DISABLED",),
        )
    if loader is None:
        return _missing_result(mode, missing_behavior)
    try:
        loaded = loader()
        if loaded is None:
            return _missing_result(mode, missing_behavior)
        context = (
            loaded
            if isinstance(loaded, IdentitySubmitContext)
            else build_identity_submit_context(loaded)
        )
        artifact = IdentitySubmitArtifact(
            mode=mode,
            status=IdentitySubmitContextStatus.BOUND,
            missing_behavior=missing_behavior,
            enforced=False,
            context_hash=context.context_hash.value,
            identity_kernel_hash=context.identity_kernel_hash,
            persona_manifest_hash=context.persona_manifest_hash,
            operator_contract_hash=context.operator_contract_hash,
            reason_codes=("IDENTITY_CONTEXT_BOUND_TO_SUBMIT_PREFLIGHT",),
        )
        return IdentitySubmitPreflightResult(
            status=IdentitySubmitContextStatus.BOUND,
            should_block=False,
            artifact=artifact,
            context=context,
        )
    except Exception as exc:
        should_block = mode is GovernanceEnforcementMode.ENFORCE_FAIL_CLOSED
        status = (
            IdentitySubmitContextStatus.BLOCKED_INVALID_CONTEXT
            if should_block
            else IdentitySubmitContextStatus.ERROR
        )
        return _result(
            mode,
            status,
            missing_behavior,
            should_block=should_block,
            enforced=should_block,
            reason_codes=(f"IDENTITY_CONTEXT_ERROR_{type(exc).__name__}",),
            error_type=type(exc).__name__,
        )


def identity_submit_preflight_to_artifact(
    result: IdentitySubmitPreflightResult,
) -> dict[str, Any]:
    return result.to_canonical_dict()


def _missing_behavior(
    mode: GovernanceEnforcementMode,
    require_identity_context: bool,
) -> IdentityMissingContextBehavior:
    if mode is GovernanceEnforcementMode.ENFORCE_FAIL_CLOSED and require_identity_context:
        return IdentityMissingContextBehavior.FAIL_CLOSED
    if mode is GovernanceEnforcementMode.DISABLED_UNAVAILABLE:
        return IdentityMissingContextBehavior.MARK_UNAVAILABLE
    return IdentityMissingContextBehavior.RECORD_ADVISORY


def _missing_result(
    mode: GovernanceEnforcementMode,
    missing_behavior: IdentityMissingContextBehavior,
) -> IdentitySubmitPreflightResult:
    should_block = missing_behavior is IdentityMissingContextBehavior.FAIL_CLOSED
    status = (
        IdentitySubmitContextStatus.BLOCKED_MISSING_REQUIRED_CONTEXT
        if should_block
        else IdentitySubmitContextStatus.ADVISORY_MISSING
    )
    return _result(
        mode,
        status,
        missing_behavior,
        should_block=should_block,
        enforced=should_block,
        reason_codes=("IDENTITY_SUBMIT_CONTEXT_MISSING",),
    )


def _result(
    mode: GovernanceEnforcementMode,
    status: IdentitySubmitContextStatus,
    missing_behavior: IdentityMissingContextBehavior,
    *,
    should_block: bool,
    enforced: bool,
    reason_codes: tuple[str, ...],
    error_type: str = "",
) -> IdentitySubmitPreflightResult:
    artifact = IdentitySubmitArtifact(
        mode=mode,
        status=status,
        missing_behavior=missing_behavior,
        enforced=enforced,
        reason_codes=reason_codes,
        error_type=error_type,
    )
    return IdentitySubmitPreflightResult(
        status=status,
        should_block=should_block,
        artifact=artifact,
    )
