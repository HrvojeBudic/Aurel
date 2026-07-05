"""SPINE-LIVE-0 — the live-with-evidence primitive.

The whole SPINE-LIVE series flips phases from contract-only theater to real
execution using one honest rule, already modelled by P4-EXEC-B: an availability
boolean is ``True`` **only** when a real evidence ref exists.

    # NOT: x_available = False               # eternal theater
    # NOR: x_available = True                 # dishonest claim
    # BUT: x_available = bool(evidence_ref)   # LIVE only with proof

This module defines the first concrete evidence ref — proof that a real model
call happened — plus the generic ``live_available`` gate that S1–S5 reuse.

Nothing here grants authority or permission. It records *that a call happened*
and hashes *what was said*; it never claims the plan was safe, permitted, or
executed. Those remain the runtime's, P4's, and P9's to decide.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum

from ..core_types import new_id, now, sha

MODEL_CALL_EVIDENCE_VERSION = "model_call_evidence.v1"

# The router returns this synthetic model name when no provider produced a
# completion (all providers down / profile blocked). It is never a live call.
ROUTER_REFUSAL_MODEL_NAME = "router"


class LiveEvidenceLabel(str, Enum):
    """Honest outcome label for a live-with-evidence ref."""

    LIVE = "LIVE"            # a real response with a stable content hash
    REFUSED = "REFUSED"      # the provider/router refused (honest, not live)
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"


def _detect_refusal_reason(raw_response: str, model_name: str) -> str:
    """Return a refusal reason if the completion is not a real model answer.

    A router-level failover exhaustion surfaces as ``model_name == "router"``.
    A provider refusal surfaces as a ``refusal_reason`` field in the JSON body.
    """
    if model_name == ROUTER_REFUSAL_MODEL_NAME:
        reason = "router refused: no provider produced a completion"
        try:
            data = json.loads(raw_response)
            if isinstance(data, dict) and data.get("refusal_reason"):
                return str(data["refusal_reason"])
        except (json.JSONDecodeError, TypeError):
            pass
        return reason
    try:
        data = json.loads(raw_response)
    except (json.JSONDecodeError, TypeError):
        return ""
    if isinstance(data, dict) and data.get("refusal_reason"):
        return str(data["refusal_reason"])
    return ""


@dataclass(frozen=True)
class ModelCallEvidenceRef:
    """Proof that a real model call happened. Never authority, never permission.

    ``available`` is the single load-bearing property: it is ``True`` only for a
    non-refusal response that carries both a prompt hash and a response hash.
    A construction that lacks a response hash can never be ``available``.
    """

    evidence_id: str
    kind: str
    contract_version: str
    label: LiveEvidenceLabel
    profile: str
    model_name: str
    prompt_hash: str
    response_hash: str
    prompt_chars: int
    response_chars: int
    produced_at: float
    refusal_reason: str = ""
    # Boundary booleans — an evidence ref is observation, not authority.
    authority_granted: bool = False
    permission_granted: bool = False
    execution_available: bool = False

    @property
    def available(self) -> bool:
        return (
            self.label is LiveEvidenceLabel.LIVE
            and bool(self.prompt_hash)
            and bool(self.response_hash)
            and not self.refusal_reason
        )

    def to_dict(self) -> dict:
        return {
            "evidence_id": self.evidence_id,
            "kind": self.kind,
            "contract_version": self.contract_version,
            "label": self.label.value,
            "profile": self.profile,
            "model_name": self.model_name,
            "prompt_hash": self.prompt_hash,
            "response_hash": self.response_hash,
            "prompt_chars": self.prompt_chars,
            "response_chars": self.response_chars,
            "produced_at": self.produced_at,
            "refusal_reason": self.refusal_reason,
            "available": self.available,
        }

    def content_hash(self) -> str:
        """Deterministic hash over the identifying content (not the id/time)."""
        return sha(
            self.contract_version,
            self.label.value,
            self.profile,
            self.model_name,
            self.prompt_hash,
            self.response_hash,
        )


def capture_model_call_evidence(
    *,
    profile: str,
    model_name: str,
    system: str,
    user: str,
    raw_response: str,
) -> ModelCallEvidenceRef:
    """Build a ``ModelCallEvidenceRef`` from one router completion.

    The prompt hash binds (profile, system, user) so an identical prompt is
    reproducible; the response hash binds the raw completion text. Refusals are
    labelled honestly and are never ``available``.
    """
    prompt_hash = sha(profile, system, user)
    response_hash = sha(raw_response) if raw_response else ""
    refusal_reason = _detect_refusal_reason(raw_response, model_name)
    if refusal_reason:
        label = LiveEvidenceLabel.REFUSED
    elif not response_hash:
        label = LiveEvidenceLabel.ERROR
    else:
        label = LiveEvidenceLabel.LIVE
    return ModelCallEvidenceRef(
        evidence_id=new_id("mcev"),
        kind="model_call",
        contract_version=MODEL_CALL_EVIDENCE_VERSION,
        label=label,
        profile=profile,
        model_name=model_name,
        prompt_hash=prompt_hash,
        response_hash=response_hash,
        prompt_chars=len(system) + len(user),
        response_chars=len(raw_response),
        produced_at=now(),
        refusal_reason=refusal_reason,
    )


def live_available(evidence: ModelCallEvidenceRef | None) -> bool:
    """The generic gate every SPINE phase reuses: live only with real proof."""
    return evidence is not None and evidence.available
