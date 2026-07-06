"""P0-S.1 seal — the reasoning_effort request field grants no execution power.

reasoning_effort is a request-only hint; providers may ignore it and it changes
no dispatch, gating, or output. Allocation ≠ authority.
"""
from __future__ import annotations

from agentic_runtime.model_providers.base import ModelRequest
from agentic_runtime.model_providers.mock_provider import MockProvider


def test_reasoning_effort_field_grants_no_execution_power():
    # field exists, request-only, conservative default
    assert ModelRequest(system_prompt="s", user_prompt="u").reasoning_effort == "auto"

    prov = MockProvider()
    low = prov.generate_structured_plan(
        ModelRequest(system_prompt="s", user_prompt="u", reasoning_effort="low"))
    high = prov.generate_structured_plan(
        ModelRequest(system_prompt="s", user_prompt="u", reasoning_effort="high"))

    # the hint changes nothing: identical plan, and it grants no usage/authority
    assert low.raw_text == high.raw_text
    assert low.usage is None and high.usage is None
