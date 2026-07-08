"""
sanitization.py — the audited boundary where tainted content crosses (F3.0 / D0).

External content is not forbidden from entering a context — it is forbidden from
entering as *instruction*. ``SanitizationCrossing`` is the single, explicit,
recorded seam where a ``TaintedContent`` is admitted **as inert data only**:

  - ``crosses_as_instruction`` is a computed property hard-wired to ``False``.
    There is no field, argument, or method that can make it True — the forbid is
    structural, mirroring ``TaintedContent.instruction_eligible``.
  - QUARANTINED content yields no data view at all (``data_view()`` → None):
    fail closed. Nothing raw escapes quarantine.
  - Every crossing carries the advisory injection scan as evidence, so a
    downstream consumer can warn / quarantine on operator policy without the scan
    ever being the gate.

The crossing does not execute, mutate, upload, or persist anything; it is a pure
value describing an admission decision.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from .injection_detector import InjectionScanResult, scan_for_injection
from .taint import TaintedContent, TaintLabel


class CrossingKind(str, Enum):
    """How content is admitted. Closed-world; only DATA_ONLY admits anything."""

    DATA_ONLY = "data_only"    # admitted as inert data (the only admitting kind)
    QUARANTINED = "quarantined"  # held back; nothing admitted


@dataclass(frozen=True)
class SanitizationCrossing:
    """A recorded admission of tainted content as data (never instruction)."""

    source: TaintedContent
    crossing_kind: CrossingKind
    scan: InjectionScanResult

    @property
    def crosses_as_instruction(self) -> bool:
        """Structurally False, always. External data never becomes instruction."""
        return False

    @property
    def admitted(self) -> bool:
        return self.crossing_kind is CrossingKind.DATA_ONLY

    def data_view(self) -> Optional[str]:
        """The content as inert data, or None if quarantined (fail closed).

        The returned string is the raw content — callers treat it strictly as
        data. Quarantine yields nothing rather than a redacted guess.
        """
        if self.crossing_kind is not CrossingKind.DATA_ONLY:
            return None
        return self.source.content

    def to_dict(self) -> dict:
        return {
            "source": self.source.to_dict(),
            "crossing_kind": self.crossing_kind.value,
            "crosses_as_instruction": self.crosses_as_instruction,
            "admitted": self.admitted,
            "scan": self.scan.to_dict(),
        }


def cross_as_data(content: TaintedContent) -> SanitizationCrossing:
    """Admit content as data. QUARANTINED content is held back (fail closed).

    The injection scan is attached as advisory evidence but does not decide
    admission — provenance does. A dirty scan on admissible content still
    crosses as data (with the warning recorded); the scan never blocks here.
    """
    scan = scan_for_injection(content.content)
    if content.label is TaintLabel.QUARANTINED:
        return SanitizationCrossing(
            source=content,
            crossing_kind=CrossingKind.QUARANTINED,
            scan=scan,
        )
    return SanitizationCrossing(
        source=content,
        crossing_kind=CrossingKind.DATA_ONLY,
        scan=scan,
    )
