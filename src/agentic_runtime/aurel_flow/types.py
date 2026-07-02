"""P3-FLOW-A AurelFlow shared types, truth labels, and canonical serialization.

AurelFlow orchestrates; AurelExec (P4) executes later. Every object in this
package is a local, deterministic, in-memory runtime substrate. Nothing here
executes tools, commands, subprocesses, network calls, sandbox actions,
workers, or business actions, and nothing here writes trace, ledger, memory,
policy, or identity state.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import fields, is_dataclass
from enum import Enum
from typing import Any, Mapping

AUREL_FLOW_PACK_ID = "P3-FLOW-A"
AUREL_FLOW_PACK_TITLE = "AurelFlow Runtime Foundation Superpack"
AUREL_FLOW_REPORT_PATH = "agent/reports/P3_FLOW_A_AURELFLOW_RUNTIME_FOUNDATION_SUPERPACK.md"

EXECUTION_UNAVAILABLE_REASON = (
    "execution is not implemented in P3-FLOW-A; governed execution belongs to P4 AurelExec"
)
TRACE_VERIFICATION_UNAVAILABLE_REASON = (
    "trace verification is not implemented in P3-FLOW-A; the evidence spine belongs to P5 AurelTrace"
)
CLI_BINDING_UNAVAILABLE_REASON = (
    "no Flow CLI/TUI binding is implemented in P3-FLOW-A; Flow CLI/TUI binding belongs to P3.7"
)
EVENT_STREAM_UNAVAILABLE_REASON = (
    "no runtime event stream is implemented in P3-FLOW-A; the event stream belongs to P3.3 / P3-FLOW-B"
)
APPROVAL_RUNTIME_UNAVAILABLE_REASON = (
    "no approval pause/resume runtime is implemented in P3-FLOW-A; approval runtime belongs to P3.4"
)
PERSISTENCE_UNAVAILABLE_REASON = (
    "workflow run state is in-memory only in P3-FLOW-A; no database, file, or external persistence exists"
)


class FlowTruthLabel(str, Enum):
    """Honest truth labels for AurelFlow foundation objects.

    LIVE and TRACE_VERIFIED exist in the vocabulary but are never assigned by
    this pack: nothing in P3-FLOW-A is live and nothing is trace-verified.
    """

    LIVE = "LIVE"
    TRACE_VERIFIED = "TRACE_VERIFIED"
    SIMULATED = "SIMULATED"
    DEV_FIXTURE = "DEV_FIXTURE"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"
    LOCAL_RUNTIME_SUBSTRATE = "LOCAL_RUNTIME_SUBSTRATE"
    CONTRACT_ONLY = "CONTRACT_ONLY"


class FlowSourceLabel(str, Enum):
    LOCAL_CONSTRUCTION = "LOCAL_CONSTRUCTION"
    DEV_FIXTURE = "DEV_FIXTURE"
    TEST_FIXTURE = "TEST_FIXTURE"


FORBIDDEN_FLOW_TRUTH_LABELS: tuple[FlowTruthLabel, ...] = (
    FlowTruthLabel.LIVE,
    FlowTruthLabel.TRACE_VERIFIED,
)


def _canonical_value(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value) and not isinstance(value, type):
        return canonical_dataclass_dict(value)
    if isinstance(value, Mapping):
        return {
            str(_canonical_value(key)): _canonical_value(item)
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
        }
    if isinstance(value, (list, tuple)):
        return [_canonical_value(item) for item in value]
    return value


def canonical_dataclass_dict(value: Any) -> dict[str, Any]:
    return {field.name: _canonical_value(getattr(value, field.name)) for field in fields(value)}


def to_canonical_json(value: Any) -> str:
    return json.dumps(_canonical_value(value), sort_keys=True, separators=(",", ":"))


def stable_hash(value: Any) -> str:
    return hashlib.sha256(to_canonical_json(value).encode("utf-8")).hexdigest()


class _CanonicalMixin:
    def to_canonical_dict(self) -> dict[str, Any]:
        return canonical_dataclass_dict(self)
