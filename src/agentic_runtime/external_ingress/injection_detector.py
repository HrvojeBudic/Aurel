"""
injection_detector.py — advisory prompt-injection signatures (F3.0 / D0).

Deterministic, stdlib-only signature scan over external content. It is
**advisory** — it annotates a payload with what looks suspicious; it has NO
authority over instruction-eligibility (that is provenance-structural, see
``taint.py``). A clean scan never upgrades trust; a dirty scan never blocks by
itself. The scan exists so downstream surfaces (gate, gateway, Self-RAG) can
*warn*, quarantine on operator policy, and keep evidence — not to be the gate.

Signatures are conservative, case-insensitive, and fixed (no learning, no RNG).
``scan_for_injection`` never raises: any input, however malformed, yields a
result. Findings are returned in a stable, deterministic order.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum


class Severity(str, Enum):
    """Advisory severity. Ordered LOW < MEDIUM < HIGH via ``_RANK``."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


_RANK: dict[Severity, int] = {Severity.LOW: 0, Severity.MEDIUM: 1, Severity.HIGH: 2}


class InjectionSignature(str, Enum):
    """Closed-world catalogue of known injection shapes."""

    INSTRUCTION_OVERRIDE = "instruction_override"   # "ignore previous instructions"
    ROLE_HIJACK = "role_hijack"                     # "you are now DAN / a new persona"
    SYSTEM_PROMPT_PROBE = "system_prompt_probe"     # "reveal your system prompt"
    SECRET_EXFIL = "secret_exfil"                   # "print your api key / secret"
    TOOL_INJECTION = "tool_injection"               # fake tool-call / function markers
    POLICY_OVERRIDE = "policy_override"             # "disregard your rules/policy"


# (signature, severity, compiled pattern). Order here defines a stable tiebreak.
_SIGNATURES: tuple[tuple[InjectionSignature, Severity, "re.Pattern[str]"], ...] = (
    (
        InjectionSignature.INSTRUCTION_OVERRIDE,
        Severity.HIGH,
        re.compile(
            r"\b(ignore|disregard|forget|override)\b[^.\n]{0,40}\b"
            r"(previous|prior|above|earlier|all)\b[^.\n]{0,20}\b"
            r"(instruction|instructions|prompt|prompts|context)\b",
            re.IGNORECASE,
        ),
    ),
    (
        InjectionSignature.ROLE_HIJACK,
        Severity.HIGH,
        re.compile(
            r"\byou\s+are\s+now\b|\bact\s+as\b[^.\n]{0,30}\b(dan|jailbreak|"
            r"unrestricted|no\s+longer\s+bound)\b|\bpretend\s+you\s+are\b",
            re.IGNORECASE,
        ),
    ),
    (
        InjectionSignature.SYSTEM_PROMPT_PROBE,
        Severity.MEDIUM,
        re.compile(
            r"\b(reveal|show|print|repeat|output|leak)\b[^.\n]{0,30}\b"
            r"(system\s+prompt|initial\s+instructions|your\s+instructions|"
            r"the\s+prompt\s+above)\b",
            re.IGNORECASE,
        ),
    ),
    (
        InjectionSignature.SECRET_EXFIL,
        Severity.HIGH,
        re.compile(
            r"\b(print|reveal|show|send|exfiltrate|leak|give\s+me)\b[^.\n]{0,30}\b"
            r"(api[_\s-]?key|secret|password|token|credential|private\s+key)\b",
            re.IGNORECASE,
        ),
    ),
    (
        InjectionSignature.TOOL_INJECTION,
        Severity.MEDIUM,
        re.compile(
            r"<\s*/?\s*(tool_call|function_call|invoke|tool)\b|"
            r"```\s*(tool|function|invoke)\b|\bassistant\s*:\s*\{",
            re.IGNORECASE,
        ),
    ),
    (
        InjectionSignature.POLICY_OVERRIDE,
        Severity.HIGH,
        re.compile(
            r"\b(disregard|ignore|bypass|violate)\b[^.\n]{0,30}\b"
            r"(your\s+)?(rules|policy|policies|guidelines|guardrails|safety)\b",
            re.IGNORECASE,
        ),
    ),
)


@dataclass(frozen=True)
class InjectionFinding:
    """One matched signature and where it hit."""

    signature: InjectionSignature
    severity: Severity
    start: int
    end: int
    matched_text: str

    def to_dict(self) -> dict:
        return {
            "signature": self.signature.value,
            "severity": self.severity.value,
            "start": self.start,
            "end": self.end,
            "matched_text": self.matched_text,
        }


@dataclass(frozen=True)
class InjectionScanResult:
    """Advisory scan outcome. Findings are deterministically ordered."""

    findings: tuple[InjectionFinding, ...] = field(default_factory=tuple)

    @property
    def has_findings(self) -> bool:
        return len(self.findings) > 0

    @property
    def max_severity(self) -> Severity | None:
        if not self.findings:
            return None
        return max((f.severity for f in self.findings), key=lambda s: _RANK[s])

    def to_dict(self) -> dict:
        return {
            "has_findings": self.has_findings,
            "max_severity": self.max_severity.value if self.max_severity else None,
            "findings": [f.to_dict() for f in self.findings],
        }


def scan_for_injection(content: str) -> InjectionScanResult:
    """Scan text for known injection shapes. Advisory only; never raises.

    Deterministic: findings are sorted by (start, signature value) so the same
    input always yields byte-identical output. Non-str input fails closed to an
    empty result rather than raising.
    """
    if not isinstance(content, str) or not content:
        return InjectionScanResult(findings=())

    found: list[InjectionFinding] = []
    for signature, severity, pattern in _SIGNATURES:
        for m in pattern.finditer(content):
            found.append(
                InjectionFinding(
                    signature=signature,
                    severity=severity,
                    start=m.start(),
                    end=m.end(),
                    matched_text=m.group(0),
                )
            )

    found.sort(key=lambda f: (f.start, f.signature.value))
    return InjectionScanResult(findings=tuple(found))
