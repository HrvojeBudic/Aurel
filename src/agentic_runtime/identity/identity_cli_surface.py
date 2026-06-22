"""P1.4.15 Identity Governance Command Surface.

Provides a unified command surface over the P1.4 identity, autonomy, claim,
doctrine, attestation, authority-delta, and consent modules.

This is a command surface, NOT an interactive agent terminal. It exposes
status, verify, and routes subcommands to their respective modules.

P1.4.15 implements a command surface, not an interactive agent terminal.
It does not execute tools, grant consent, mutate identity sources,
or create new authority.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class IdentityCliStatus(str, Enum):
    OK = "OK"
    DEGRADED = "DEGRADED"
    BLOCKED = "BLOCKED"
    UNKNOWN = "UNKNOWN"


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class IdentityCliEnvelope:
    ok: bool
    command: str
    status: IdentityCliStatus
    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    result: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class IdentitySubsystemStatus:
    name: str
    status: IdentityCliStatus
    summary: str
    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class IdentityStatusReport:
    status: IdentityCliStatus
    subsystems: tuple[IdentitySubsystemStatus, ...]
    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    suggested_next_commands: tuple[str, ...] = ()


# ---------------------------------------------------------------------------
# Subsystem names (standardized)
# ---------------------------------------------------------------------------

SUBSYSTEM_KERNEL = "identity_kernel"
SUBSYSTEM_PERSONA = "persona_manifest"
SUBSYSTEM_OPERATOR_CONTRACT = "operator_contract"
SUBSYSTEM_COMMUNICATION_MODES = "communication_modes"
SUBSYSTEM_IDENTITY_CARD = "agent_identity_card"
SUBSYSTEM_SELF_MODEL = "self_model"
SUBSYSTEM_AUTONOMY = "autonomy_engine"
SUBSYSTEM_CLAIMS = "capability_claims"
SUBSYSTEM_DOCTRINE = "doctrine_registry"
SUBSYSTEM_ATTESTATION = "source_attestations"
SUBSYSTEM_AUTHORITY_DELTA = "authority_delta_detector"
SUBSYSTEM_CONSENT = "operator_consent_binding"

ALL_SUBSYSTEMS = (
    SUBSYSTEM_KERNEL,
    SUBSYSTEM_CLAIMS,
    SUBSYSTEM_DOCTRINE,
    SUBSYSTEM_ATTESTATION,
    SUBSYSTEM_AUTHORITY_DELTA,
    SUBSYSTEM_CONSENT,
)


# ---------------------------------------------------------------------------
# Engine: envelope
# ---------------------------------------------------------------------------


def build_identity_cli_envelope(
    *,
    command: str,
    status: IdentityCliStatus,
    result: Mapping[str, object] | None = None,
    errors: tuple[str, ...] = (),
    warnings: tuple[str, ...] = (),
) -> IdentityCliEnvelope:
    """Build a standardized identity CLI envelope.

    ok = true only when status == OK and errors is empty.
    """
    ok = status == IdentityCliStatus.OK and len(errors) == 0
    return IdentityCliEnvelope(
        ok=ok,
        command=command,
        status=status,
        errors=errors,
        warnings=warnings,
        result=result or {},
    )


def identity_cli_envelope_to_dict(envelope: IdentityCliEnvelope) -> dict[str, object]:
    """Serialize an IdentityCliEnvelope to a stable JSON-able dict."""
    return {
        "ok": envelope.ok,
        "command": envelope.command,
        "status": envelope.status.value,
        "errors": list(envelope.errors),
        "warnings": list(envelope.warnings),
        "result": envelope.result,
    }


def identity_substatus_to_dict(ss: IdentitySubsystemStatus) -> dict[str, object]:
    return {
        "name": ss.name,
        "status": ss.status.value,
        "summary": ss.summary,
        "errors": list(ss.errors),
        "warnings": list(ss.warnings),
    }


def identity_status_report_to_dict(report: IdentityStatusReport) -> dict[str, object]:
    return {
        "status": report.status.value,
        "subsystems": [identity_substatus_to_dict(s) for s in report.subsystems],
        "errors": list(report.errors),
        "warnings": list(report.warnings),
        "suggested_next_commands": list(report.suggested_next_commands),
    }


# ---------------------------------------------------------------------------
# Engine: lightweight subsystem presence checks (read-only)
# ---------------------------------------------------------------------------


def _check_module_available(module_path: str, module_label: str) -> tuple[bool, str]:
    """Lightweight import check. Returns (ok, error_message)."""
    try:
        __import__(module_path)
        return True, ""
    except ImportError:
        return False, f"module_not_importable:{module_label}"


def _check_subsystem(name: str) -> IdentitySubsystemStatus:
    """Probe a single subsystem."""
    # kernel check
    if name == SUBSYSTEM_KERNEL:
        ok, err = _check_module_available(
            "agentic_runtime.identity.kernel", "identity_kernel"
        )
        if ok:
            return IdentitySubsystemStatus(
                name=name,
                status=IdentityCliStatus.OK,
                summary="Identity kernel importable",
            )
        return IdentitySubsystemStatus(
            name=name,
            status=IdentityCliStatus.BLOCKED,
            summary="Identity kernel unavailable",
            errors=(err,),
        )

    # claims check
    if name == SUBSYSTEM_CLAIMS:
        ok, err = _check_module_available(
            "agentic_runtime.identity.capability_claims", "capability_claims"
        )
        if ok:
            return IdentitySubsystemStatus(
                name=name,
                status=IdentityCliStatus.OK,
                summary="Capability claim boundary engine importable",
            )
        return IdentitySubsystemStatus(
            name=name,
            status=IdentityCliStatus.BLOCKED,
            summary="Claim boundary engine unavailable",
            errors=(err,),
        )

    # doctrine check
    if name == SUBSYSTEM_DOCTRINE:
        ok, err = _check_module_available(
            "agentic_runtime.identity.external_doctrine", "external_doctrine"
        )
        if ok:
            return IdentitySubsystemStatus(
                name=name,
                status=IdentityCliStatus.OK,
                summary="Doctrine registry importable",
            )
        return IdentitySubsystemStatus(
            name=name,
            status=IdentityCliStatus.BLOCKED,
            summary="Doctrine registry unavailable",
            errors=(err,),
        )

    # attestation check
    if name == SUBSYSTEM_ATTESTATION:
        ok, err = _check_module_available(
            "agentic_runtime.identity.source_attestation", "source_attestation"
        )
        if ok:
            return IdentitySubsystemStatus(
                name=name,
                status=IdentityCliStatus.OK,
                summary="Source attestation module importable",
            )
        return IdentitySubsystemStatus(
            name=name,
            status=IdentityCliStatus.BLOCKED,
            summary="Source attestation unavailable",
            errors=(err,),
        )

    # authority-delta check
    if name == SUBSYSTEM_AUTHORITY_DELTA:
        ok, err = _check_module_available(
            "agentic_runtime.identity.authority_delta", "authority_delta"
        )
        if ok:
            return IdentitySubsystemStatus(
                name=name,
                status=IdentityCliStatus.OK,
                summary="Authority delta detector importable",
            )
        return IdentitySubsystemStatus(
            name=name,
            status=IdentityCliStatus.BLOCKED,
            summary="Authority delta detector unavailable",
            errors=(err,),
        )

    # consent check
    if name == SUBSYSTEM_CONSENT:
        ok, err = _check_module_available(
            "agentic_runtime.identity.operator_consent", "operator_consent"
        )
        if ok:
            return IdentitySubsystemStatus(
                name=name,
                status=IdentityCliStatus.OK,
                summary="Operator consent binding importable",
            )
        return IdentitySubsystemStatus(
            name=name,
            status=IdentityCliStatus.BLOCKED,
            summary="Operator consent binding unavailable",
            errors=(err,),
        )

    return IdentitySubsystemStatus(
        name=name,
        status=IdentityCliStatus.UNKNOWN,
        summary=f"Unknown subsystem: {name}",
        errors=(f"unknown_subsystem:{name}",),
    )


# ---------------------------------------------------------------------------
# Engine: status report
# ---------------------------------------------------------------------------


def build_identity_status_report() -> IdentityStatusReport:
    """Build the overall identity governance status report. Read-only."""
    subsystems: list[IdentitySubsystemStatus] = []
    all_errors: list[str] = []
    all_warnings: list[str] = []

    for name in ALL_SUBSYSTEMS:
        ss = _check_subsystem(name)
        subsystems.append(ss)
        all_errors.extend(ss.errors)
        all_warnings.extend(ss.warnings)

    # Determine overall status
    statuses = {s.status for s in subsystems}
    if IdentityCliStatus.BLOCKED in statuses:
        overall = IdentityCliStatus.BLOCKED
    elif IdentityCliStatus.UNKNOWN in statuses:
        overall = IdentityCliStatus.DEGRADED
    elif IdentityCliStatus.DEGRADED in statuses:
        overall = IdentityCliStatus.DEGRADED
    else:
        overall = IdentityCliStatus.OK

    # Suggested next commands when not OK
    next_cmds: list[str] = []
    if overall != IdentityCliStatus.OK:
        next_cmds.append("identity verify --json")
        for ss in subsystems:
            if ss.status != IdentityCliStatus.OK:
                if ss.name == SUBSYSTEM_ATTESTATION:
                    next_cmds.append("identity attestation validate --json")
                elif ss.name == SUBSYSTEM_DOCTRINE:
                    next_cmds.append("identity doctrine validate --json")
                elif ss.name == SUBSYSTEM_CLAIMS:
                    next_cmds.append("identity claims validate --json")
                elif ss.name == SUBSYSTEM_AUTHORITY_DELTA:
                    next_cmds.append(
                        "identity authority-delta compare --old <old.json> "
                        "--new <new.json> --source-kind <kind> --json"
                    )
                elif ss.name == SUBSYSTEM_CONSENT:
                    next_cmds.append(
                        "identity consent validate --record <record.json> "
                        "--delta-report <report.json> --json"
                    )

    # Deduplicate while preserving order
    seen: set[str] = set()
    deduplicated: list[str] = []
    for cmd in next_cmds:
        if cmd not in seen:
            seen.add(cmd)
            deduplicated.append(cmd)

    return IdentityStatusReport(
        status=overall,
        subsystems=tuple(subsystems),
        errors=tuple(all_errors),
        warnings=tuple(all_warnings),
        suggested_next_commands=tuple(deduplicated),
    )


# ---------------------------------------------------------------------------
# Engine: verify surface
# ---------------------------------------------------------------------------


def verify_identity_surface() -> IdentityStatusReport:
    """Run non-destructive validation across P1.4 modules. Read-only."""
    report = build_identity_status_report()

    # Additional checks beyond basic importability
    extra_errors: list[str] = []
    extra_warnings: list[str] = []
    updated_subsystems: list[IdentitySubsystemStatus] = []

    for ss in report.subsystems:
        new_errors = list(ss.errors)
        new_warnings = list(ss.warnings)

        # Try validator function existence for key modules
        if ss.name == SUBSYSTEM_KERNEL and ss.status == IdentityCliStatus.OK:
            try:
                from agentic_runtime.identity.kernel import (
                    IdentityKernelValidationResult,
                )
                _ = IdentityKernelValidationResult  # just check import
            except (ImportError, AttributeError):
                new_warnings.append("kernel_validator_not_confirmed")

        if ss.name == SUBSYSTEM_DOCTRINE and ss.status == IdentityCliStatus.OK:
            try:
                from agentic_runtime.identity.external_doctrine import (
                    ExternalDoctrineInput,
                )
                _ = ExternalDoctrineInput
            except (ImportError, AttributeError):
                new_warnings.append("doctrine_model_not_confirmed")

        if ss.name == SUBSYSTEM_ATTESTATION and ss.status == IdentityCliStatus.OK:
            try:
                from agentic_runtime.identity.source_attestation import (
                    validate_source_attestation,
                )
                _ = validate_source_attestation
            except (ImportError, AttributeError):
                new_warnings.append("attestation_validator_not_confirmed")

        if ss.name == SUBSYSTEM_CONSENT and ss.status == IdentityCliStatus.OK:
            try:
                from agentic_runtime.identity.operator_consent import (
                    validate_operator_consent_binding,
                )
                _ = validate_operator_consent_binding
            except (ImportError, AttributeError):
                new_warnings.append("consent_validator_not_confirmed")

        updated = IdentitySubsystemStatus(
            name=ss.name,
            status=ss.status,
            summary=ss.summary,
            errors=tuple(new_errors),
            warnings=tuple(new_warnings),
        )
        updated_subsystems.append(updated)
        extra_errors.extend(new_errors)
        extra_warnings.extend(new_warnings)

    statuses = {s.status for s in updated_subsystems}
    overall = report.status
    if IdentityCliStatus.BLOCKED in statuses:
        overall = IdentityCliStatus.BLOCKED
    elif IdentityCliStatus.UNKNOWN in statuses:
        overall = IdentityCliStatus.DEGRADED

    next_cmds = list(report.suggested_next_commands)
    if not next_cmds:
        next_cmds.append("identity status --json")

    return IdentityStatusReport(
        status=overall,
        subsystems=tuple(updated_subsystems),
        errors=tuple(extra_errors),
        warnings=tuple(extra_warnings),
        suggested_next_commands=tuple(next_cmds),
    )


# ---------------------------------------------------------------------------
# Human-readable formatters
# ---------------------------------------------------------------------------


def format_identity_status_human(report: IdentityStatusReport) -> str:
    """Format an IdentityStatusReport into human-readable text."""
    lines = [f"Identity Status: {report.status.value}", ""]
    lines.append("Summary:")
    for ss in report.subsystems:
        marker = {
            IdentityCliStatus.OK: "OK",
            IdentityCliStatus.DEGRADED: "DEGRADED",
            IdentityCliStatus.BLOCKED: "BLOCKED",
            IdentityCliStatus.UNKNOWN: "UNKNOWN",
        }.get(ss.status, "?")
        lines.append(f"  {ss.name}: {marker}")

    if report.errors:
        lines.append("")
        lines.append("Blockers:")
        for e in report.errors:
            lines.append(f"  - {e}")

    if report.warnings:
        lines.append("")
        lines.append("Warnings:")
        for w in report.warnings:
            lines.append(f"  - {w}")

    if report.suggested_next_commands:
        lines.append("")
        lines.append("Suggested next commands:")
        for cmd in report.suggested_next_commands:
            lines.append(f"  {cmd}")

    return "\n".join(lines)


def format_envelope_human(envelope: IdentityCliEnvelope) -> str:
    """Format an IdentityCliEnvelope into human-readable text."""
    lines = [
        f"Command: {envelope.command}",
        f"Status: {envelope.status.value}",
    ]
    if envelope.errors:
        lines.append("Errors:")
        for e in envelope.errors:
            lines.append(f"  - {e}")
    if envelope.warnings:
        lines.append("Warnings:")
        for w in envelope.warnings:
            lines.append(f"  - {w}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

__all__ = [
    "IdentityCliStatus",
    "IdentityCliEnvelope",
    "IdentitySubsystemStatus",
    "IdentityStatusReport",
    "build_identity_cli_envelope",
    "identity_cli_envelope_to_dict",
    "identity_substatus_to_dict",
    "identity_status_report_to_dict",
    "build_identity_status_report",
    "verify_identity_surface",
    "format_identity_status_human",
    "format_envelope_human",
]
