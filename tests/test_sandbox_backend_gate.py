"""P1.ENF-E sandbox backend gate unit tests."""
from __future__ import annotations

from agentic_runtime import (
    GovernanceEnforcementMode,
    SandboxBackendGateMode,
    SandboxBackendDecision,
    SandboxSafetyClass,
    UnsafeLocalSandbox,
    classify_sandbox_backend,
    evaluate_sandbox_backend_gate,
    sandbox_backend_requirement_from_config,
)
from agentic_runtime.sandbox import BubblewrapSandbox


def test_unsafe_local_sandbox_classified_as_unsafe(tmp_path):
    backend = UnsafeLocalSandbox(root=str(tmp_path))
    capability = classify_sandbox_backend(backend)

    assert capability.safety_class is SandboxSafetyClass.UNSAFE_LOCAL
    assert capability.is_security_boundary is False
    assert capability.backend_kind.value == "UnsafeLocalSandbox"


def test_dev_fixture_not_live():
    class DevFixtureSandbox(UnsafeLocalSandbox):
        pass

    capability = classify_sandbox_backend(
        DevFixtureSandbox(),
        dev_fixture=True,
    )

    assert capability.safety_class is SandboxSafetyClass.DEV_FIXTURE
    assert "DEV_FIXTURE is not LIVE" in capability.limitations[0]


def test_require_safe_verified_denies_unsafe_local(tmp_path):
    backend = UnsafeLocalSandbox(root=str(tmp_path))
    requirement = sandbox_backend_requirement_from_config(
        mode=GovernanceEnforcementMode.ENFORCE_FAIL_CLOSED,
        require_safe_sandbox_backend=False,
        gate_mode=SandboxBackendGateMode.REQUIRE_SAFE_VERIFIED,
        submit_metadata=None,
    )

    result = evaluate_sandbox_backend_gate(
        mode=GovernanceEnforcementMode.ENFORCE_FAIL_CLOSED,
        backend=backend,
        requirement=requirement,
    )

    assert result.decision is SandboxBackendDecision.UNAVAILABLE
    assert result.should_block is True
    assert "safe_verified_not_proven" in result.artifact.unavailable_reasons


def test_require_safe_verified_unavailable_when_no_safe_backend(tmp_path):
    backend = UnsafeLocalSandbox(root=str(tmp_path))
    requirement = sandbox_backend_requirement_from_config(
        mode=GovernanceEnforcementMode.ADVISORY,
        require_safe_sandbox_backend=False,
        gate_mode=SandboxBackendGateMode.REQUIRE_SAFE_VERIFIED,
        submit_metadata=None,
    )

    result = evaluate_sandbox_backend_gate(
        mode=GovernanceEnforcementMode.ADVISORY,
        backend=backend,
        requirement=requirement,
    )

    assert result.decision is SandboxBackendDecision.UNAVAILABLE
    assert result.should_block is False


def test_dev_allow_unsafe_local_allows_with_warning_truth_label(tmp_path):
    backend = UnsafeLocalSandbox(root=str(tmp_path))
    requirement = sandbox_backend_requirement_from_config(
        mode=GovernanceEnforcementMode.ADVISORY,
        require_safe_sandbox_backend=False,
        gate_mode=SandboxBackendGateMode.DEV_ALLOW_UNSAFE,
        submit_metadata=None,
    )

    result = evaluate_sandbox_backend_gate(
        mode=GovernanceEnforcementMode.ADVISORY,
        backend=backend,
        requirement=requirement,
    )

    assert result.decision in {
        SandboxBackendDecision.ALLOW,
        SandboxBackendDecision.WARN,
    }
    assert result.should_block is False
    assert result.artifact.truth_label == "SANDBOX_BACKEND_GATED"
    assert result.artifact.unsafe_backend_allowed_reason == "explicit_dev_allow_unsafe_gate"
    assert result.artifact.warnings


def test_live_claim_denied_with_dev_fixture_backend():
    class DevFixtureSandbox(UnsafeLocalSandbox):
        pass

    requirement = sandbox_backend_requirement_from_config(
        mode=GovernanceEnforcementMode.ENFORCE_FAIL_CLOSED,
        require_safe_sandbox_backend=False,
        gate_mode=SandboxBackendGateMode.DEV_ALLOW_UNSAFE,
        submit_metadata={
            "args": {
                "_sandbox_backend_signals": {
                    "dev_fixture_backend": True,
                    "claims_live_execution": True,
                }
            }
        },
    )

    result = evaluate_sandbox_backend_gate(
        mode=GovernanceEnforcementMode.ENFORCE_FAIL_CLOSED,
        backend=DevFixtureSandbox(),
        requirement=requirement,
    )

    assert result.decision is SandboxBackendDecision.DENY
    assert result.should_block is True
    assert result.artifact.violations[0].key == "live_claim_denied"


def test_sandbox_gate_result_contains_evidence_refs(tmp_path):
    backend = UnsafeLocalSandbox(root=str(tmp_path))
    requirement = sandbox_backend_requirement_from_config(
        mode=GovernanceEnforcementMode.SHADOW_ONLY,
        require_safe_sandbox_backend=False,
        gate_mode=SandboxBackendGateMode.DEV_ALLOW_UNSAFE,
        submit_metadata=None,
    )

    result = evaluate_sandbox_backend_gate(
        mode=GovernanceEnforcementMode.SHADOW_ONLY,
        backend=backend,
        requirement=requirement,
    )

    artifact = result.artifact
    assert artifact.sandbox_backend_kind == "UnsafeLocalSandbox"
    assert artifact.sandbox_safety_class == SandboxSafetyClass.UNSAFE_LOCAL.value
    assert artifact.sandbox_gate_decision == result.decision.value
    assert "src/agentic_runtime/sandbox.py" in artifact.evidence_refs
    assert result.artifact.artifact_hash


def test_restricted_local_classification_for_hard_backends():
    import tempfile

    bwrap = BubblewrapSandbox(root=tempfile.mkdtemp(prefix="ar_test_bwrap_"))
    capability = classify_sandbox_backend(bwrap)
    assert capability.safety_class is SandboxSafetyClass.RESTRICTED_LOCAL
    assert capability.is_hard_isolated is True


def test_require_restricted_or_safe_denies_unsafe_local(tmp_path):
    backend = UnsafeLocalSandbox(root=str(tmp_path))
    requirement = sandbox_backend_requirement_from_config(
        mode=GovernanceEnforcementMode.ENFORCE_FAIL_CLOSED,
        require_safe_sandbox_backend=True,
        gate_mode=None,
        submit_metadata=None,
    )

    result = evaluate_sandbox_backend_gate(
        mode=GovernanceEnforcementMode.ENFORCE_FAIL_CLOSED,
        backend=backend,
        requirement=requirement,
    )

    assert result.decision is SandboxBackendDecision.DENY
    assert result.should_block is True
    assert result.artifact.truth_label == "BLOCKED_UNSAFE_SANDBOX_PROMOTION"
