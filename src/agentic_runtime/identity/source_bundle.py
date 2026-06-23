"""Shared immutable identity source bundle (P1.4.7-MG / P1.4.12)."""
from __future__ import annotations
from collections.abc import Sequence

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Protocol, cast

from ..prompts.compiler_policy import (
    IdentityPromptCompilerPolicy,
    IPC_VALIDATOR_VERSION,
    default_identity_prompt_compiler_path,
    parse_identity_prompt_compiler_document,
)
from ..prompts.identity_context_validation import validate_identity_prompt_compiler_policy
from ..yaml_minimal import YamlParseError, load_yaml
from .agent_identity_card_policy import (
    AGENT_IDENTITY_CARD_VALIDATOR_VERSION,
    AgentIdentityCardConfig,
    AgentIdentityCardError,
    default_agent_identity_card_path,
    parse_agent_identity_card_document,
)
from .agent_identity_card_validation import validate_agent_identity_card_config
from .communication_modes import (
    COMMUNICATION_MODES_VALIDATOR_VERSION,
    AurelCommunicationModeRegistry,
    default_communication_modes_path,
    parse_communication_modes_document,
)
from .kernel import (
    VALIDATOR_VERSION,
    AurelIdentityKernel,
    default_identity_kernel_path,
    parse_identity_kernel_document,
)
from .kernel_validation import validate_identity_kernel
from .mode_validation import validate_communication_mode_registry
from .operator_contract import (
    OPERATOR_CONTRACT_VALIDATOR_VERSION,
    AurelOperatorContract,
    default_operator_contract_path,
    parse_operator_contract_document,
)
from .operator_contract_validation import validate_operator_contract
from .persona import (
    PERSONA_VALIDATOR_VERSION,
    AurelPersonaManifest,
    default_persona_manifest_path,
    parse_persona_manifest_document,
)
from .persona_validation import validate_persona_manifest
from .self_model_policy import (
    SELF_MODEL_VALIDATOR_VERSION,
    SelfModelPolicy,
    default_self_model_policy_path,
    load_self_model_policy as _load_self_model_policy_from_file,
    parse_self_model_policy_document,
)
from .self_model_validation import validate_self_model_policy
from .source_attestation import (
    SourceAttestation,
    SourceKind,
    build_source_attestation_from_validation_result,
    hash_canonical_source,
    hash_raw_source,
)


class _ValidationResultLike(Protocol):
    valid: bool
    critical_failures: Sequence[str]
    errors: Sequence[str]


def _resolve_path(value: str | Path | None, default: Path) -> Path:
    return Path(value) if value is not None else default


def _read_raw_sources(paths: Mapping[str, Path]) -> dict[str, str]:
    raw_sources: dict[str, str] = {}
    for key, path in paths.items():
        if not path.is_file():
            raise AgentIdentityCardError(f"identity source file not found: {path}")
        raw_sources[key] = path.read_text(encoding="utf-8")
    return raw_sources


def _parse_yaml(raw: str, path: Path) -> dict:
    try:
        document = load_yaml(raw)
    except YamlParseError as exc:
        raise AgentIdentityCardError(f"YAML parse error in {path}: {exc}") from exc
    if not document:
        raise AgentIdentityCardError(f"identity source document is empty: {path}")
    return document


_SELF_MODEL_POLICY_DOCUMENT_OVERRIDES: dict[Path, dict] = {}


def load_self_model_policy(path: str | Path | None = None) -> SelfModelPolicy:
    """Compatibility seam that can parse the raw document captured by the bundle."""
    resolved = _resolve_path(path, default_self_model_policy_path())
    document = _SELF_MODEL_POLICY_DOCUMENT_OVERRIDES.get(resolved.resolve())
    if document is not None:
        return parse_self_model_policy_document(document)
    return _load_self_model_policy_from_file(resolved)


@dataclass(frozen=True)
class IdentitySourceBundle:
    identity_kernel: AurelIdentityKernel
    persona_manifest: AurelPersonaManifest
    operator_contract: AurelOperatorContract
    mode_registry: AurelCommunicationModeRegistry
    compiler_policy: IdentityPromptCompilerPolicy
    self_model_policy: SelfModelPolicy
    card_config: AgentIdentityCardConfig
    source_paths: Mapping[str, Path]
    raw_hashes: Mapping[str, str]
    canonical_hashes: Mapping[str, str]
    attestations: Mapping[SourceKind, SourceAttestation]


def load_identity_source_bundle(
    *,
    kernel_path: str | Path | None = None,
    persona_path: str | Path | None = None,
    operator_path: str | Path | None = None,
    modes_path: str | Path | None = None,
    compiler_path: str | Path | None = None,
    self_model_policy_path: str | Path | None = None,
    card_config_path: str | Path | None = None,
) -> IdentitySourceBundle:
    """Load identity sources once with raw and canonical attestations."""
    paths = {
        "identity_kernel": _resolve_path(kernel_path, default_identity_kernel_path()),
        "persona_manifest": _resolve_path(persona_path, default_persona_manifest_path()),
        "operator_contract": _resolve_path(operator_path, default_operator_contract_path()),
        "communication_modes": _resolve_path(modes_path, default_communication_modes_path()),
        "identity_prompt_compiler": _resolve_path(
            compiler_path, default_identity_prompt_compiler_path()
        ),
        "self_model_policy": _resolve_path(
            self_model_policy_path, default_self_model_policy_path()
        ),
        "agent_identity_card_config": _resolve_path(
            card_config_path, default_agent_identity_card_path()
        ),
    }
    try:
        raw_sources = _read_raw_sources(paths)
        documents = {key: _parse_yaml(raw, paths[key]) for key, raw in raw_sources.items()}
        identity_kernel = parse_identity_kernel_document(documents["identity_kernel"])
        persona_manifest = parse_persona_manifest_document(documents["persona_manifest"])
        operator_contract = parse_operator_contract_document(documents["operator_contract"])
        mode_registry = parse_communication_modes_document(documents["communication_modes"])
        compiler_policy = parse_identity_prompt_compiler_document(
            documents["identity_prompt_compiler"]
        )
        # Preserve the P1.4.7-MG monkeypatch seam while using the raw
        # source document already captured for P1.4.12 attestation.
        self_model_policy_path = paths["self_model_policy"].resolve()
        _SELF_MODEL_POLICY_DOCUMENT_OVERRIDES[self_model_policy_path] = documents[
            "self_model_policy"
        ]
        try:
            self_model_policy = load_self_model_policy(paths["self_model_policy"])
        finally:
            _SELF_MODEL_POLICY_DOCUMENT_OVERRIDES.pop(self_model_policy_path, None)
        card_config = parse_agent_identity_card_document(documents["agent_identity_card_config"])
    except Exception as exc:
        if isinstance(exc, AgentIdentityCardError):
            raise
        raise AgentIdentityCardError(str(exc)) from exc

    raw_hashes = {key: hash_raw_source(raw) for key, raw in raw_sources.items()}
    canonical_hashes = {
        "identity_kernel": hash_canonical_source(identity_kernel),
        "persona_manifest": hash_canonical_source(persona_manifest),
        "operator_contract": hash_canonical_source(operator_contract),
        "communication_modes": hash_canonical_source(mode_registry),
        "identity_prompt_compiler": hash_canonical_source(compiler_policy),
        "self_model_policy": hash_canonical_source(self_model_policy),
        "agent_identity_card_config": hash_canonical_source(card_config),
    }

    validation_results = cast(
        dict[SourceKind, _ValidationResultLike],
        {
            SourceKind.IDENTITY_KERNEL: validate_identity_kernel(identity_kernel),
            SourceKind.PERSONA_MANIFEST: validate_persona_manifest(persona_manifest),
            SourceKind.OPERATOR_CONTRACT: validate_operator_contract(operator_contract),
            SourceKind.COMMUNICATION_MODES: validate_communication_mode_registry(mode_registry),
            SourceKind.IDENTITY_PROMPT_COMPILER: validate_identity_prompt_compiler_policy(
                compiler_policy
            ),
            SourceKind.SELF_MODEL_POLICY: validate_self_model_policy(self_model_policy),
            SourceKind.AGENT_IDENTITY_CARD_CONFIG: validate_agent_identity_card_config(
                card_config
            ),
        },
    )
    typed_objects = {
        SourceKind.IDENTITY_KERNEL: identity_kernel,
        SourceKind.PERSONA_MANIFEST: persona_manifest,
        SourceKind.OPERATOR_CONTRACT: operator_contract,
        SourceKind.COMMUNICATION_MODES: mode_registry,
        SourceKind.IDENTITY_PROMPT_COMPILER: compiler_policy,
        SourceKind.SELF_MODEL_POLICY: self_model_policy,
        SourceKind.AGENT_IDENTITY_CARD_CONFIG: card_config,
    }
    validator_meta = {
        SourceKind.IDENTITY_KERNEL: ("identity_kernel_validator", VALIDATOR_VERSION),
        SourceKind.PERSONA_MANIFEST: ("persona_manifest_validator", PERSONA_VALIDATOR_VERSION),
        SourceKind.OPERATOR_CONTRACT: (
            "operator_contract_validator",
            OPERATOR_CONTRACT_VALIDATOR_VERSION,
        ),
        SourceKind.COMMUNICATION_MODES: (
            "communication_modes_validator",
            COMMUNICATION_MODES_VALIDATOR_VERSION,
        ),
        SourceKind.IDENTITY_PROMPT_COMPILER: (
            "identity_prompt_compiler_validator",
            IPC_VALIDATOR_VERSION,
        ),
        SourceKind.SELF_MODEL_POLICY: (
            "self_model_policy_validator",
            SELF_MODEL_VALIDATOR_VERSION,
        ),
        SourceKind.AGENT_IDENTITY_CARD_CONFIG: (
            "agent_identity_card_config_validator",
            AGENT_IDENTITY_CARD_VALIDATOR_VERSION,
        ),
    }
    attestations: dict[SourceKind, SourceAttestation] = {}
    for source_kind, typed_object in typed_objects.items():
        key = source_kind.value
        validator_name, validator_version = validator_meta[source_kind]
        attestations[source_kind] = build_source_attestation_from_validation_result(
            source_kind=source_kind,
            source_path=paths[key],
            raw_source=raw_sources[key],
            typed_object=typed_object,
            validation_result=validation_results[source_kind],
            validator_name=validator_name,
            validator_version=validator_version,
            evidence_refs=("agent/reports/P1.4.12_RAW_SOURCE_CANONICAL_HASH_ATTESTATION.md",),
        )

    return IdentitySourceBundle(
        identity_kernel=identity_kernel,
        persona_manifest=persona_manifest,
        operator_contract=operator_contract,
        mode_registry=mode_registry,
        compiler_policy=compiler_policy,
        self_model_policy=self_model_policy,
        card_config=card_config,
        source_paths=paths,
        raw_hashes=raw_hashes,
        canonical_hashes=canonical_hashes,
        attestations=attestations,
    )


def validate_identity_source_bundle(bundle: IdentitySourceBundle) -> tuple[str, ...]:
    """Validate all bundle sources; return critical failure messages."""
    checks: tuple[_ValidationResultLike, ...] = (
        validate_identity_kernel(bundle.identity_kernel),
        validate_persona_manifest(bundle.persona_manifest),
        validate_operator_contract(bundle.operator_contract),
        validate_communication_mode_registry(bundle.mode_registry),
        validate_identity_prompt_compiler_policy(bundle.compiler_policy),
        validate_self_model_policy(bundle.self_model_policy),
        validate_agent_identity_card_config(bundle.card_config),
    )
    failures: list[str] = []
    for result in checks:
        if not result.valid:
            failures.extend(result.critical_failures or result.errors)
    for source_kind, attestation in bundle.attestations.items():
        if attestation.validation_status.value not in {"VALID", "VALID_WITH_WARNINGS"}:
            failures.append(f"{source_kind.value}: source attestation is {attestation.validation_status.value}")
    return tuple(failures)


def build_aurel_self_model_from_bundle(
    bundle: IdentitySourceBundle,
    *,
    prompt_mode: str = "FOCUS",
    include_prompt_context: bool = True,
    runtime_version: str | None = None,
):
    """Build self-model from a pre-loaded identity source bundle."""
    from .self_model_builder import build_aurel_self_model

    identity_prompt_context = None
    if include_prompt_context:
        from ..prompts.identity_context_compiler import compile_identity_prompt_context

        compile_result = compile_identity_prompt_context(
            bundle.identity_kernel,
            bundle.persona_manifest,
            bundle.operator_contract,
            bundle.mode_registry,
            prompt_mode,
            bundle.compiler_policy,
        )
        if not compile_result.valid or compile_result.context is None:
            raise AgentIdentityCardError(
                "; ".join(compile_result.critical_failures or compile_result.errors)
            )
        identity_prompt_context = compile_result.context

    return build_aurel_self_model(
        bundle.identity_kernel,
        bundle.persona_manifest,
        bundle.operator_contract,
        bundle.mode_registry,
        bundle.compiler_policy,
        identity_prompt_context,
        bundle.self_model_policy,
        runtime_version=runtime_version,
    )


__all__ = [
    "IdentitySourceBundle",
    "build_aurel_self_model_from_bundle",
    "load_identity_source_bundle",
    "validate_identity_source_bundle",
]
