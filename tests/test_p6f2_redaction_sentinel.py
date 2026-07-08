"""F2 seal — central secret redaction + per-provider sentinel.

A resolved API key must never survive into any observable byte stream: the trace,
a model cassette on disk, a log line, or a provider/router error. This seal
injects a UNIQUE sentinel per provider, registers each with the process-wide
redactor (as ``SecretStore``/``EnvSecretProvider`` do on every real resolution),
then exercises each leak surface and asserts the sentinel appears in NONE of the
resulting output.

The sentinels are deliberately LOW-ENTROPY, non-``sk-`` tokens that the redactor's
heuristic patterns (``sk-…``, ``Bearer …``, ``…=secret``, 32+ char high-entropy)
do NOT match. So the only thing that can redact them is exact-match against the
registered-secret registry — which is exactly the central mechanism under test.
A control token proves legitimate content is preserved (no over-redaction).
"""

from __future__ import annotations

import json

import pytest

from agentic_runtime.model_cassette import ModelCassette
from agentic_runtime.model_providers.http_utils import post_json
from agentic_runtime.model_router import ModelRouter
from agentic_runtime.secrets import SecretRedactor, register_secret_value
from agentic_runtime.trace import InMemoryTraceLedger
from agentic_runtime.core_types import PlanningFailureRecord

# provider → unique sentinel "key" (only exact-match registry redaction can catch
# these: no sk- prefix, no KEY= form, < 32 chars so the entropy rule never fires).
SENTINELS = {
    "anthropic": "sentinelvaluealpha",
    "deepseek": "sentinelvaluebravo",
    "qwen": "sentinelvaluegamma",
    "kimi": "sentinelvaluedelta",
    "openai": "sentinelvalueecho",
}
CONTROL = "ordinaryword12345"      # not a secret — must be PRESERVED everywhere


@pytest.fixture(autouse=True)
def _register_sentinels():
    for value in SENTINELS.values():
        register_secret_value(value)


def _no_sentinels(blob: str) -> None:
    for provider, value in SENTINELS.items():
        assert value not in blob, f"{provider} sentinel leaked into: {blob[:200]!r}"


# --------------------------------------------------------------------------- #
# 1. Cassette on disk — the recorded completion is redacted before it is
#    persisted (exact-match only, so real completions are not corrupted).
# --------------------------------------------------------------------------- #
def test_cassette_never_persists_a_sentinel(tmp_path):
    path = tmp_path / "cassette.jsonl"
    cassette = ModelCassette(path)
    for provider, value in SENTINELS.items():
        raw = json.dumps({"answer": value, "keep": CONTROL})
        cassette.record(provider, f"sys-{provider}", f"usr-{provider}", raw)

    on_disk = path.read_text(encoding="utf-8")
    _no_sentinels(on_disk)                       # no key survives to disk
    assert "[REDACTED]" in on_disk               # it was actively redacted
    assert CONTROL in on_disk                    # legitimate content preserved

    # replay/lookup also serves redacted content, never the raw key.
    replay = ModelCassette(path)
    got = replay.lookup("qwen", "sys-qwen", "usr-qwen")
    assert got is not None and "sentinelvaluegamma" not in got and CONTROL in got


# --------------------------------------------------------------------------- #
# 2. Provider error — post_json carries the key in the Authorization header, yet
#    its error string is a typed code that never echoes the header/key/URL.
# --------------------------------------------------------------------------- #
def test_provider_error_never_contains_sentinel():
    errors = []
    for value in SENTINELS.values():
        # localhost:1 refuses immediately (offline, deterministic).
        data, error, _latency = post_json(
            "http://127.0.0.1:1/v1/chat/completions",
            {"model": "x", "messages": []},
            headers={"Authorization": f"Bearer {value}"},
            timeout=1.0,
        )
        assert data is None and error                # it failed, as intended
        errors.append(error)
    joined = " ".join(errors)
    _no_sentinels(joined)
    # Each error is a whitespace-free typed code — never a free-form dump of the
    # request (which would carry the Authorization header / key).
    for e in errors:
        assert " " not in e and "Bearer" not in e, e


# --------------------------------------------------------------------------- #
# 3. Router failover error — a provider raising an exception whose message
#    contains the key is redacted at the router boundary before it is returned.
# --------------------------------------------------------------------------- #
def test_router_failover_error_never_contains_sentinel():
    outputs = []
    for provider, value in SENTINELS.items():
        class _RaisingClient:
            name = provider

            def complete(self, system: str, user: str) -> str:
                raise RuntimeError(f"401 unauthorized for key {value}")

        router = ModelRouter(default_provider="mock")
        router.register("balanced", [_RaisingClient()])
        raw, who = router.complete("balanced", "s", "u")
        outputs.append(raw)
    _no_sentinels(" ".join(outputs))


# --------------------------------------------------------------------------- #
# 4. Trace — a sentinel-bearing error, redacted at the boundary (as the runtime
#    does) before it is written to a trace record, leaves the replayed trace
#    clean; an un-redacted control proves the assertion would catch a leak.
# --------------------------------------------------------------------------- #
def test_trace_replay_never_contains_sentinel():
    redactor = SecretRedactor()
    trace = InMemoryTraceLedger(run_id="run_f2f")
    for provider, value in SENTINELS.items():
        raw_error = f"RuntimeError: provider {provider} rejected key {value}"
        # sanity: the raw error DOES contain the sentinel (the test can catch leaks)
        assert value in raw_error
        redacted = redactor.redact(raw_error)
        assert value not in redacted
        trace.append_planning_failure(PlanningFailureRecord.make(
            intent_id=f"intent-{provider}", issuer_card_id="card_x",
            status="model_unavailable", reason=redacted))

    dump = json.dumps(list(trace.replay()), default=str)
    _no_sentinels(dump)
    ok, broken = trace.verify_chain()
    assert ok and broken is None                 # redaction did not break the chain


# --------------------------------------------------------------------------- #
# 5. Logs — arbitrary operator-facing log lines pass through the central
#    redactor and never surface a registered key.
# --------------------------------------------------------------------------- #
def test_logs_never_contain_sentinel():
    redactor = SecretRedactor()
    lines = []
    for provider, value in SENTINELS.items():
        raw_line = f"[warn] {provider} auth failed using {value} — retrying"
        redacted = redactor.redact(raw_line)
        assert "[REDACTED]" in redacted
        lines.append(redacted)
    _no_sentinels("\n".join(lines))
