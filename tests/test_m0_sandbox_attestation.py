"""M0 — functional sandbox probes, host attestation, and doctor diagnostics.

These assert the *honesty* invariant: a probe may only report ``available`` after
a real sandboxed execution, and the trace records the true isolation posture.
"""

from __future__ import annotations

import json

from agentic_runtime.core_types import SandboxAttestationRecord
from agentic_runtime.sandbox import (
    SandboxMode,
    clear_probe_cache,
    host_fingerprint,
    probe_backend,
)
from agentic_runtime.trace import PersistentTraceLedger, InMemoryTraceLedger


def test_probe_backend_shape_unsafe():
    att = probe_backend(SandboxMode.UNSAFE_LOCAL)
    assert att["backend"] == "unsafe_local"
    assert att["available"] is True
    assert att["hard_isolated"] is False  # unsafe is never a boundary
    assert "host" in att and "userns" in att["host"]


def test_probe_backend_hard_reports_bool_not_crash():
    # Whether or not bwrap works here, the probe must return a clean dict and
    # never claim hard isolation without availability.
    for mode in (SandboxMode.BUBBLEWRAP, SandboxMode.DOCKER):
        att = probe_backend(mode)
        assert att["backend"] == mode.value
        assert isinstance(att["available"], bool)
        if not att["available"]:
            assert att["hard_isolated"] is False
            assert att["reason"]  # must explain why
        assert att["probe"]  # the probe command is disclosed


def test_probe_cache_roundtrip():
    clear_probe_cache()
    a = probe_backend(SandboxMode.BUBBLEWRAP)
    b = probe_backend(SandboxMode.BUBBLEWRAP)
    assert a == b  # cached, stable within TTL


def test_host_fingerprint_stable_keys():
    fp = host_fingerprint()
    assert set(fp) >= {"system", "release", "machine", "userns"}


def test_attestation_record_hash_chains_in_memory():
    led = InMemoryTraceLedger(run_id="att-mem")
    att = probe_backend(SandboxMode.BUBBLEWRAP)
    rec = led.append_sandbox_attestation(SandboxAttestationRecord.make("att-mem", att))
    ok, broken = led.verify_chain()
    assert ok and broken is None
    assert rec.entry_hash
    kinds = [e["kind"] for e in led.replay()]
    assert "sandbox_attestation" in kinds


def test_attestation_record_persists_and_reloads(tmp_path):
    led = PersistentTraceLedger(base_dir=str(tmp_path), run_id="att-disk", checkpoint_every=5)
    att = probe_backend(SandboxMode.DOCKER)
    led.append_sandbox_attestation(SandboxAttestationRecord.make("att-disk", att))
    led.seal_run("completed")
    # fresh verifier reads from disk
    led2 = PersistentTraceLedger(base_dir=str(tmp_path), run_id="att-disk", checkpoint_every=5)
    rep = led2.verify_persisted()
    assert rep["ok"], rep
    kinds = [e["kind"] for e in led2.replay()]
    assert "sandbox_attestation" in kinds


def test_attestation_tamper_breaks_chain(tmp_path):
    led = PersistentTraceLedger(base_dir=str(tmp_path), run_id="att-tamper", checkpoint_every=5)
    att = probe_backend(SandboxMode.BUBBLEWRAP)
    led.append_sandbox_attestation(SandboxAttestationRecord.make("att-tamper", att))
    led.seal_run("completed")
    lines = led.events_path.read_text().strip().split("\n")
    ev = json.loads(lines[0])
    ev["payload"]["available"] = True
    ev["payload"]["hard_isolated"] = True  # forge a stronger claim
    lines[0] = json.dumps(ev)
    led.events_path.write_text("\n".join(lines) + "\n")
    led2 = PersistentTraceLedger(base_dir=str(tmp_path), run_id="att-tamper", checkpoint_every=5)
    rep = led2.verify_persisted()
    assert not rep["ok"]  # forging the attestation is detected


def test_doctor_report_is_honest():
    from agentic_runtime.cli_modules.doctor import run_doctor

    rep = run_doctor(no_cache=True)
    assert "sandboxes" in rep and "governance_levels" in rep
    # G0-G5 require hard isolation; if none is available none may be achievable.
    if not rep["hard_isolation_available"]:
        assert all(not v["achievable"] for v in rep["governance_levels"].values())
    # the report is JSON-serializable (evidence artifact)
    json.dumps(rep, default=str)
