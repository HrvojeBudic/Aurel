"""P4-EXEC-A no-Custos-enforcement boundary tests.

Proves admission is not authorization: no Custos/P9 policy is enforced,
policy context is shadow-only, and the enforcement vocabulary is
structurally unconstructible in this pack.
"""

from __future__ import annotations

import dataclasses

import pytest

from agentic_runtime.aurel_exec import (
    AurelExecValidationError,
    ExecAdmissionState,
    ExecCustosStatus,
    ExecPolicyStatus,
    ExecUnavailableSystem,
    build_dev_fixture_admission_request,
    build_exec_projection,
    build_no_custos_enforcement_proof,
    decide_admission,
)


def test_custos_and_policy_status_vocabularies_cannot_claim_enforcement():
    assert "ENFORCED" not in ExecCustosStatus.__members__
    assert "AUTHORIZED" not in ExecCustosStatus.__members__
    assert "APPROVED" not in ExecCustosStatus.__members__
    assert "ENFORCED" not in ExecPolicyStatus.__members__


def test_admit_decision_is_not_authorization():
    decision = decide_admission(build_dev_fixture_admission_request())
    assert decision.state is ExecAdmissionState.ADMIT
    assert decision.custos_status is ExecCustosStatus.ENFORCEMENT_UNAVAILABLE
    assert decision.policy_status is ExecPolicyStatus.SHADOW_ONLY
    custos_reasons = [
        reason
        for reason in decision.unavailable_reasons
        if reason.system is ExecUnavailableSystem.CUSTOS_ENFORCEMENT
    ]
    assert custos_reasons
    assert custos_reasons[0].future_pack_owner == "P9 Custos"


def test_policy_context_ref_is_shadow_only_never_enforcement():
    with_policy = decide_admission(build_dev_fixture_admission_request())
    assert with_policy.policy_status is ExecPolicyStatus.SHADOW_ONLY
    without_policy = decide_admission(
        build_dev_fixture_admission_request(requested_policy_context_ref=None)
    )
    assert without_policy.policy_status is ExecPolicyStatus.ENFORCEMENT_UNAVAILABLE


def test_projection_cannot_claim_policy_enforcement_available():
    decision = decide_admission(build_dev_fixture_admission_request())
    projection = build_exec_projection(decision)
    assert projection.policy_enforcement_available is False
    with pytest.raises(AurelExecValidationError):
        dataclasses.replace(projection, policy_enforcement_available=True)


def test_no_custos_enforcement_proof_is_fail_closed_and_names_p9():
    proof = build_no_custos_enforcement_proof()
    assert proof.custos_enforced is False
    assert proof.policy_enforced is False
    assert proof.policy_shadow_only is True
    assert proof.future_pack_owner == "P9 Custos"
    for boundary_field in ("custos_enforced", "policy_enforced"):
        with pytest.raises(AurelExecValidationError):
            dataclasses.replace(proof, **{boundary_field: True})
    with pytest.raises(AurelExecValidationError):
        dataclasses.replace(proof, policy_shadow_only=False)


def test_aurel_exec_never_imports_custos_or_policy_runtime_modules():
    from pathlib import Path

    import agentic_runtime.aurel_exec as aurel_exec

    for module_path in sorted(Path(aurel_exec.__file__).parent.glob("*.py")):
        source = module_path.read_text(encoding="utf-8")
        for forbidden in (
            "from ..custos",
            "from agentic_runtime.custos",
            "from ..policy import",
            "from agentic_runtime.policy import",
            "from ..policy_cards",
            "from agentic_runtime.policy_cards",
            "from ..memory import",
            "from ..identity",
        ):
            assert forbidden not in source, f"{module_path.name} contains {forbidden!r}"
