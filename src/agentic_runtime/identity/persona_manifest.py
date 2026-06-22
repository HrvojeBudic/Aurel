"""Persona Manifest public API shim (P1.4.2).

Re-exports the persona manifest API so it is importable as
``agentic_runtime.identity.persona_manifest``. Implementation lives in
``persona.py``, ``persona_validation.py``, ``persona_hash.py``, and
``persona_summary.py``.
"""
from __future__ import annotations

from .persona import (
    PERSONA_VALIDATOR_VERSION,
    AurelPersonaManifest,
    PersonaBoundaries,
    PersonaChallengeBehavior,
    PersonaHonesty,
    PersonaInvariant,
    PersonaManifestAttestation,
    PersonaManifestError,
    PersonaManifestHash,
    PersonaManifestValidationResult,
    PersonaOperatorInteraction,
    PersonaPosture,
    PersonaPromptSafety,
    PersonaRiskCommunication,
    PersonaSafeSummary,
    PersonaVoice,
    default_persona_manifest_path,
    load_persona_manifest,
    parse_persona_manifest_document,
)
from .persona_hash import compute_persona_manifest_hash, persona_to_canonical_dict
from .persona_summary import build_persona_safe_summary, persona_safe_summary_to_dict
from .persona_validation import (
    build_persona_manifest_attestation,
    validate_persona_manifest,
    write_persona_manifest_attestation,
)

__all__ = [
    "PERSONA_VALIDATOR_VERSION",
    "AurelPersonaManifest",
    "PersonaBoundaries",
    "PersonaChallengeBehavior",
    "PersonaHonesty",
    "PersonaInvariant",
    "PersonaManifestAttestation",
    "PersonaManifestError",
    "PersonaManifestHash",
    "PersonaManifestValidationResult",
    "PersonaOperatorInteraction",
    "PersonaPosture",
    "PersonaPromptSafety",
    "PersonaRiskCommunication",
    "PersonaSafeSummary",
    "PersonaVoice",
    "build_persona_manifest_attestation",
    "build_persona_safe_summary",
    "compute_persona_manifest_hash",
    "default_persona_manifest_path",
    "load_persona_manifest",
    "parse_persona_manifest_document",
    "persona_safe_summary_to_dict",
    "persona_to_canonical_dict",
    "validate_persona_manifest",
    "write_persona_manifest_attestation",
]
