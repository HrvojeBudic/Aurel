"""SPINE-LIVE-0 tests — the live-with-evidence primitive."""

from __future__ import annotations

from agentic_runtime.core_types import AgentCard
from agentic_runtime.model_router import MockModelClient, ModelRouter
from agentic_runtime.spine import (
    LiveEvidenceLabel,
    ModelCallEvidenceRef,
    capture_model_call_evidence,
    live_available,
)
from agentic_runtime.spine.live_evidence import ROUTER_REFUSAL_MODEL_NAME

_PLAN_JSON = (
    '{"intent_summary": "fix", "plan": [{"step_id": "s1", "tool": "read_file", '
    '"args": {"path": "a.py"}, "risk": "low", "reason": "inspect"}], '
    '"refusal_reason": null}'
)
_REFUSAL_JSON = (
    '{"intent_summary": "", "plan": [], "refusal_reason": "local_only blocks '
    'remote provider"}'
)


def _capture(raw: str, model_name: str = "mock-deterministic") -> ModelCallEvidenceRef:
    return capture_model_call_evidence(
        profile="balanced",
        model_name=model_name,
        system="SYS",
        user="USER",
        raw_response=raw,
    )


def test_live_response_is_available():
    ev = _capture(_PLAN_JSON)
    assert ev.label is LiveEvidenceLabel.LIVE
    assert ev.available is True
    assert live_available(ev) is True
    assert ev.prompt_hash and ev.response_hash
    assert ev.response_chars == len(_PLAN_JSON)


def test_provider_refusal_is_not_available():
    ev = _capture(_REFUSAL_JSON)
    assert ev.label is LiveEvidenceLabel.REFUSED
    assert ev.available is False
    assert live_available(ev) is False
    assert "local_only" in ev.refusal_reason


def test_router_exhaustion_is_not_available():
    ev = _capture(_REFUSAL_JSON, model_name=ROUTER_REFUSAL_MODEL_NAME)
    assert ev.label is LiveEvidenceLabel.REFUSED
    assert ev.available is False


def test_empty_response_is_error_not_available():
    ev = _capture("")
    assert ev.label is LiveEvidenceLabel.ERROR
    assert ev.available is False
    assert ev.response_hash == ""


def test_none_evidence_is_not_available():
    assert live_available(None) is False


def test_content_hash_is_deterministic():
    a = _capture(_PLAN_JSON)
    b = _capture(_PLAN_JSON)
    # ids/timestamps differ, but identifying content hash is stable
    assert a.content_hash() == b.content_hash()
    assert a.evidence_id != b.evidence_id


def test_evidence_grants_no_authority():
    ev = _capture(_PLAN_JSON)
    assert ev.authority_granted is False
    assert ev.permission_granted is False
    assert ev.execution_available is False


def test_available_requires_response_hash_invariant():
    # A LIVE label without a response hash can never be available.
    ev = ModelCallEvidenceRef(
        evidence_id="mcev_x",
        kind="model_call",
        contract_version="model_call_evidence.v1",
        label=LiveEvidenceLabel.LIVE,
        profile="balanced",
        model_name="mock",
        prompt_hash="abc",
        response_hash="",
        prompt_chars=1,
        response_chars=0,
        produced_at=0.0,
    )
    assert ev.available is False


def test_router_wrapper_produces_evidence_end_to_end():
    router = ModelRouter()
    router.register("balanced", [MockModelClient()])
    raw, model_name, ev = router.complete_with_evidence("balanced", "SYS", "USER")
    assert isinstance(ev, ModelCallEvidenceRef)
    assert ev.model_name == model_name
    assert ev.to_dict()["available"] == ev.available
    # Mock provider returns a real structured plan → live evidence.
    assert ev.available is True
    # sanity: an AgentCard import guards against accidental API drift
    assert AgentCard is not None
