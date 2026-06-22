"""P1.4.20 tests: exit seal core, governance, adversarial, CLI, docs."""
from __future__ import annotations

import json
import os
import subprocess
import sys

from agentic_runtime.identity.p14_exit_seal import (
    P14SealCheckResult,
    P14SealCheckSeverity,
    P14SealCheckStatus,
    P14SealReport,
    P14SealStatus,
    P14_LIMITATIONS,
    decide_p14_seal_status,
    format_p14_seal_report,
    p14_seal_check_to_dict,
    p14_seal_checks,
    p14_seal_report_to_dict,
    run_p14_exit_seal,
    run_p14_seal_check,
)

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _read_doc(path: str) -> str:
    full = os.path.join(REPO, path)
    if os.path.isfile(full):
        with open(full) as f:
            return f.read()
    return ""


def _run_cli(*args: str, timeout_s: int = 30) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "agentic_runtime.cli", *args],
        capture_output=True, text=True, timeout=timeout_s, cwd=REPO,
    )


# ── Core ──

def test_registry_not_empty():
    assert len(p14_seal_checks()) > 40


def test_check_ids_unique():
    ids = [c.check_id for c in p14_seal_checks()]
    assert len(ids) == len(set(ids))


def test_check_serializes():
    d = p14_seal_check_to_dict(p14_seal_checks()[0])
    assert json.loads(json.dumps(d))["check_id"] == d["check_id"]


def test_run_exit_seal_returns_report():
    r = run_p14_exit_seal()
    assert isinstance(r, P14SealReport)
    assert len(r.checks) > 40


def test_report_json_serializable():
    r = run_p14_exit_seal()
    p = json.loads(json.dumps(p14_seal_report_to_dict(r)))
    assert p["decision"]["status"] in ("SEALED", "SEALED_WITH_LIMITATIONS", "BLOCKED", "FAILED")


def test_critical_failure_blocks():
    cf = P14SealCheckResult("cid", P14SealCheckStatus.FAILED, P14SealCheckSeverity.CRITICAL, "fail")
    ok = P14SealCheckResult("ok", P14SealCheckStatus.PASSED, P14SealCheckSeverity.LOW, "ok")
    assert decide_p14_seal_status((cf, ok), ()).status == P14SealStatus.BLOCKED


def test_sealed_with_limitations_allowed():
    ok = P14SealCheckResult("ok", P14SealCheckStatus.PASSED, P14SealCheckSeverity.MEDIUM, "ok")
    assert decide_p14_seal_status((ok,), P14_LIMITATIONS).status == P14SealStatus.SEALED_WITH_LIMITATIONS


def test_format_mentions_decision():
    assert "Exit Seal" in format_p14_seal_report(run_p14_exit_seal())
    assert "P1.5.0" in format_p14_seal_report(run_p14_exit_seal())


# ── Governance ──

def test_autonomy_no_global():
    from agentic_runtime.identity.autonomy_scale_engine import AutonomyLevel
    assert "GLOBAL" not in {lv.value for lv in AutonomyLevel}


def test_lifecycle_no_authority():
    from agentic_runtime.identity.agent_lifecycle import AgentLifecycleEligibilityProfile
    fields = AgentLifecycleEligibilityProfile.__dataclass_fields__
    assert "grants_authority" not in fields
    assert "permissions" not in fields


def test_trust_no_numeric():
    from agentic_runtime.identity.trust_evidence import TrustEvidenceBundle
    for n, f in TrustEvidenceBundle.__dataclass_fields__.items():
        if "score" in n.lower() and f.type in (int, float):
            assert False, f"Numeric: {n}"


def test_trust_evidence_not_truth():
    from agentic_runtime.identity.trust_evidence import TrustEvidenceRef
    ref = TrustEvidenceRef(evidence_id="e1", kind="REPORT", ref="r.md")
    assert not hasattr(ref, "verified") and not hasattr(ref, "truth")


# ── Adversarial ──

def test_revoked_cannot_reactivate():
    from agentic_runtime.identity.agent_lifecycle import (
        AgentLifecycleState, AgentLifecycleTransitionRequest, validate_agent_lifecycle_transition)
    req = AgentLifecycleTransitionRequest(
        request_id="seal_1", agent_id="t", old_state=AgentLifecycleState.REVOKED,
        requested_state=AgentLifecycleState.ACTIVE,
        reason_code="OVERRIDE", reason_text="test",
        requested_by="t")
    assert not validate_agent_lifecycle_transition(req).allowed


def test_draft_not_active():
    from agentic_runtime.identity.agent_lifecycle import (
        AgentLifecycleState, AgentLifecycleTransitionRequest, validate_agent_lifecycle_transition)
    req = AgentLifecycleTransitionRequest(
        request_id="seal_2", agent_id="t", old_state=AgentLifecycleState.DRAFT,
        requested_state=AgentLifecycleState.ACTIVE,
        reason_code="ACTIVATION", reason_text="test",
        requested_by="t")
    assert not validate_agent_lifecycle_transition(req).allowed


def test_active_no_evidence_not_supported():
    from agentic_runtime.identity.trust_evidence import build_trust_evidence_bundle, TrustPosture
    b = build_trust_evidence_bundle(agent_id="t", lifecycle_state="ACTIVE", evidence_refs=())
    assert b.trust_posture != TrustPosture.SUPPORTED


def test_revoked_evidence_blocks():
    from agentic_runtime.identity.trust_evidence import (
        TrustEvidenceKind, TrustEvidenceRef, TrustEvidenceStatus,
        TrustPosture, build_trust_evidence_bundle)
    ref = TrustEvidenceRef(evidence_id="e1", kind=TrustEvidenceKind.IDENTITY_CARD,
                           ref="c.yaml", status=TrustEvidenceStatus.REVOKED)
    assert build_trust_evidence_bundle(agent_id="t", lifecycle_state="DRAFT",
                                       evidence_refs=(ref,)).trust_posture != TrustPosture.SUPPORTED


def test_expired_evidence_not_supported():
    from agentic_runtime.identity.trust_evidence import (
        TrustEvidenceKind, TrustEvidenceRef, TrustEvidenceStatus,
        TrustPosture, build_trust_evidence_bundle)
    ref = TrustEvidenceRef(evidence_id="e1", kind=TrustEvidenceKind.IDENTITY_CARD,
                           ref="c.yaml", status=TrustEvidenceStatus.EXPIRED)
    assert build_trust_evidence_bundle(agent_id="t", lifecycle_state="DRAFT",
                                       evidence_refs=(ref,)).trust_posture != TrustPosture.SUPPORTED


def test_import_checks_all_pass():
    for c in p14_seal_checks():
        if c.check_id.startswith("p14_import_"):
            assert run_p14_seal_check(c).status == P14SealCheckStatus.PASSED, \
                f"{c.check_id}: {run_p14_seal_check(c).summary}"


# ── CLI ──

def test_cli_list_checks_json():
    r = _run_cli("identity", "p14-seal", "list-checks", "--json", timeout_s=30)
    assert r.returncode == 0
    assert len(json.loads(r.stdout)) > 40


def test_cli_run_check_json():
    r = _run_cli("identity", "p14-seal", "run-check",
                 "--check-id", "p14_import_test_battery", "--json", timeout_s=30)
    d = json.loads(r.stdout)
    assert d["check_id"] == "p14_import_test_battery"
    assert d["status"] == "PASSED"


def test_cli_run_human():
    r = _run_cli("identity", "p14-seal", "run", timeout_s=180)
    assert "Exit Seal" in r.stdout
    assert "P1.5.0" in r.stdout


def test_cli_idempotent():
    r1 = _run_cli("identity", "p14-seal", "list-checks", "--json", timeout_s=30)
    r2 = _run_cli("identity", "p14-seal", "list-checks", "--json", timeout_s=30)
    assert r1.stdout.strip() == r2.stdout.strip()


# ── Docs ──

_DOCS = ("agent/STATE.md", "agent/ROADMAP.md", "agent/ARCHITECTURE.md")


def test_docs_no_autonomy_claim():
    for p in _DOCS:
        assert "fully autonomous" not in _read_doc(p).lower(), p


def test_docs_no_production_ready():
    for p in _DOCS:
        assert "production-ready" not in _read_doc(p).lower(), p


def test_docs_no_self_improvement():
    for p in _DOCS:
        assert "self-improving" not in _read_doc(p).lower(), p


def test_docs_numbering():
    assert "P1.5" in _read_doc("agent/ROADMAP.md")


def test_docs_handoff_p150():
    combined = _read_doc("agent/ROADMAP.md") + _read_doc("agent/STATE.md")
    assert "P1.5" in combined


# ── Limitations ──

def test_limitations_include_gaps():
    t = " ".join(P14_LIMITATIONS)
    for gap in ("P1.5", "P1.6", "P1.8"):
        assert gap in t
