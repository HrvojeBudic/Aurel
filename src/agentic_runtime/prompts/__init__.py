"""Identity Prompt Context Compiler public API (P1.4.5)."""
from __future__ import annotations

from .compiler_policy import (
    IPC_VALIDATOR_VERSION,
    IdentityPromptCompilerError,
    IdentityPromptCompilerPolicy,
    default_identity_prompt_compiler_path,
    load_identity_prompt_compiler_policy,
    parse_identity_prompt_compiler_document,
)
from .identity_context import (
    IdentityPromptAttestation,
    IdentityPromptBoundaryCheck,
    IdentityPromptCompileResult,
    IdentityPromptContext,
    IdentityPromptContextHash,
    IdentityPromptContradiction,
    IdentityPromptSection,
    IdentityPromptSourceBundle,
    IdentityPromptValidationResult,
)
from .identity_context_attestation import (
    build_identity_prompt_attestation,
    write_identity_prompt_attestation,
)
from .identity_context_hash import (
    compute_identity_prompt_compiler_policy_hash,
    compute_identity_prompt_context_hash,
    context_to_canonical_dict,
    policy_to_canonical_dict,
)
from .identity_context_validation import (
    validate_identity_prompt_compiler_policy,
    validate_identity_prompt_context,
)

__all__ = [
    "IPC_VALIDATOR_VERSION",
    "IdentityPromptAttestation",
    "IdentityPromptBoundaryCheck",
    "IdentityPromptCompileResult",
    "IdentityPromptCompilerError",
    "IdentityPromptCompilerPolicy",
    "IdentityPromptContext",
    "IdentityPromptContextHash",
    "IdentityPromptContradiction",
    "IdentityPromptSection",
    "IdentityPromptSourceBundle",
    "IdentityPromptValidationResult",
    "build_identity_prompt_attestation",
    "compile_identity_prompt_context",
    "compile_identity_prompt_context_from_paths",
    "compute_identity_prompt_compiler_policy_hash",
    "compute_identity_prompt_context_hash",
    "context_sections_dict",
    "context_to_canonical_dict",
    "default_identity_prompt_compiler_path",
    "load_identity_prompt_compiler_policy",
    "parse_identity_prompt_compiler_document",
    "policy_to_canonical_dict",
    "render_identity_prompt_context",
    "validate_identity_prompt_compiler_policy",
    "validate_identity_prompt_context",
    "write_identity_prompt_attestation",
]

_COMPILER_EXPORTS = frozenset({
    "compile_identity_prompt_context",
    "compile_identity_prompt_context_from_paths",
    "context_sections_dict",
    "render_identity_prompt_context",
})


def __getattr__(name: str):
    if name in _COMPILER_EXPORTS:
        from . import identity_context_compiler as _compiler
        return getattr(_compiler, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
