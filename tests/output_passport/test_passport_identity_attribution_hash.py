"""Focused tests for P1.9-A output passport identity/attribution/hash pack."""

from __future__ import annotations

import json
import sys
from dataclasses import fields

import pytest

sys.path.insert(0, "src")

from agentic_runtime.output_passport import (
    OUTPUT_PASSPORT_NEXT_PACK_ID,
    OUTPUT_PASSPORT_PACK_CHECKPOINT_IDS,
    OUTPUT_PASSPORT_PACK_TASK_ID,
    OutputPassportBoundary,
    OutputPassportFoundation,
    OutputPassportInfluenceStatus,
    OutputPassportPayload,
    OutputPassportSideEffectProof,
    OutputPassportTruthLabel,
    OutputPassportUncertaintyLevel,
    OutputPassportVerificationStatus,
    P19APassportIdentityAttributionHashPackResult,
    build_assumption_limitation_uncertainty_envelope,
    build_authority_policy_risk_disclosure,
    build_dev_fixture_output_passport_payload,
    build_evidence_trace_binding,
    build_memory_influence_disclosure,
    build_output_passport_attribution_envelope,
    build_output_passport_foundation,
    build_output_passport_identity,
    build_output_passport_subject_ref,
    build_p1_9_a_passport_pack_result,
    compute_output_passport_hash,
    serialize_output_passport_payload,
    to_canonical_json,
)
from agentic_runtime.output_passport.foundation import (
    OutputPassportAttributionKind,
    OutputPassportValidationError,
)


def assert_all_side_effects_false(proof: OutputPassportSideEffectProof) -> None:
    for side_effect_field in fields(proof):
        assert getattr(proof, side_effect_field.name) is False


def test_module_and_package_exports_available():
    assert OUTPUT_PASSPORT_PACK_TASK_ID == "P1.9-A"
    assert OUTPUT_PASSPORT_PACK_CHECKPOINT_IDS == (
        "P1.9.0",
        "P1.9.1",
        "P1.9.2",
        "P1.9.3",
        "P1.9.4",
        "P1.9.5",
        "P1.9.6",
        "P1.9.7",
    )
    assert OutputPassportFoundation is not None
    assert P19APassportIdentityAttributionHashPackResult is not None


def test_p1_9_0_foundation_builds_and_serializes():
    foundation = build_output_passport_foundation()
    assert foundation.checkpoint_id == "P1.9.0"
    assert foundation.boundary.passport_is_proof is False
    assert foundation.boundary.passport_is_verification is False
    assert foundation.boundary.attribution_is_trust is False
    assert foundation.boundary.trace_ref_is_trace_verified is False
    assert foundation.boundary.evidence_ref_is_finality is False
    assert foundation.boundary.hash_is_truth is False
    assert foundation.boundary.passport_is_ledger is False
    assert foundation.truth_label is OutputPassportTruthLabel.CONTRACT_ONLY
    assert foundation.verification_status is OutputPassportVerificationStatus.NOT_VERIFIED
    assert_all_side_effects_false(foundation.side_effects)
    serialized = to_canonical_json(foundation)
    json.loads(serialized)


def test_p1_9_0_foundation_forbidden_side_effects_false():
    foundation = build_output_passport_foundation()
    proof = foundation.side_effects
    assert proof.ledger_written is False
    assert proof.global_trace_written is False
    assert proof.trace_verified is False
    assert proof.memory_read is False
    assert proof.memory_written is False
    assert proof.policy_enforced is False
    assert proof.custos_called is False
    assert proof.live_passport_generated is False


def test_p1_9_1_identity_builds_and_rejects_missing_fields():
    identity = build_output_passport_identity()
    assert identity.passport_id == "dev-passport-001"
    assert identity.subject_ref.subject_ref_id
    assert identity.truth_label is OutputPassportTruthLabel.CONTRACT_ONLY
    assert identity.verification_status is OutputPassportVerificationStatus.NOT_VERIFIED
    assert identity.truth_label is not OutputPassportTruthLabel.TRACE_VERIFIED
    with pytest.raises(OutputPassportValidationError):
        build_output_passport_identity(passport_id="")
    with pytest.raises(OutputPassportValidationError):
        build_output_passport_subject_ref(subject_ref_id="")


def test_p1_9_1_identity_serialization_stable():
    first = build_output_passport_identity()
    second = build_output_passport_identity()
    assert first.identity_hash == second.identity_hash
    assert to_canonical_json(first) == to_canonical_json(second)


def test_p1_9_2_attribution_envelope_supports_all_categories():
    envelope = build_output_passport_attribution_envelope()
    assert envelope.actor_attribution.attribution_kind is OutputPassportAttributionKind.DECLARED
    assert envelope.agent_attribution.attribution_kind is OutputPassportAttributionKind.DECLARED
    assert envelope.model_attribution.attribution_kind is OutputPassportAttributionKind.DECLARED
    assert envelope.tool_attribution.attribution_kind is OutputPassportAttributionKind.UNAVAILABLE
    assert envelope.truth_label is OutputPassportTruthLabel.DECLARED_ATTRIBUTION


def test_p1_9_2_unknown_attribution_explicit():
    envelope = build_output_passport_attribution_envelope(unknown_attribution_declared=True)
    assert envelope.unknown_attribution_declared is True


@pytest.mark.parametrize(
    "truth_label",
    ["TRACE_VERIFIED", "LIVE", "LEDGER_VERIFIED", "EVIDENCE_FINAL"],
)
def test_p1_9_2_rejects_forbidden_truth_labels(truth_label):
    with pytest.raises(OutputPassportValidationError):
        build_output_passport_attribution_envelope(truth_label=truth_label)


def test_p1_9_3_authority_policy_risk_disclosure_builds():
    disclosure = build_authority_policy_risk_disclosure()
    assert disclosure.authority_context_ref.authority_context_ref_id
    assert disclosure.policy_context_ref.policy_context_ref_id
    assert disclosure.risk_disclosure.risk_tier.value == "R2"
    assert disclosure.authorization_status.value == "disclosure_only"
    assert disclosure.truth_label is OutputPassportTruthLabel.DISCLOSURE_ONLY


def test_p1_9_3_disclosure_does_not_grant_permission():
    disclosure = build_authority_policy_risk_disclosure()
    assert disclosure.authorization_status.value != "authorized"
    assert disclosure.invariants


@pytest.mark.parametrize(
    "status",
    [
        OutputPassportInfluenceStatus.DECLARED,
        OutputPassportInfluenceStatus.NONE_DECLARED,
        OutputPassportInfluenceStatus.UNAVAILABLE,
        OutputPassportInfluenceStatus.REDACTED,
        OutputPassportInfluenceStatus.UNKNOWN,
        OutputPassportInfluenceStatus.NOT_APPLICABLE,
    ],
)
def test_p1_9_4_memory_influence_statuses_serialize(status):
    refs = () if status is OutputPassportInfluenceStatus.NONE_DECLARED else None
    disclosure = build_memory_influence_disclosure(
        influence_status=status,
        influence_refs=refs,
    )
    assert disclosure.influence_status is status
    json.loads(to_canonical_json(disclosure))


def test_p1_9_4_memory_side_effects_false():
    payload = build_dev_fixture_output_passport_payload()
    assert payload.side_effects.memory_read is False
    assert payload.side_effects.memory_written is False


def test_p1_9_5_evidence_trace_binding_reference_only():
    binding = build_evidence_trace_binding()
    assert binding.evidence_ref is not None
    assert binding.trace_ref is not None
    assert binding.verification_status is OutputPassportVerificationStatus.NOT_VERIFIED
    assert binding.truth_label is OutputPassportTruthLabel.REFERENCE_ONLY


def test_p1_9_5_rejects_verified_status():
    with pytest.raises(OutputPassportValidationError):
        build_evidence_trace_binding(verification_status="VERIFIED")


def test_p1_9_5_no_fake_trace_verified():
    binding = build_evidence_trace_binding()
    assert binding.trace_ref.verification_status is OutputPassportVerificationStatus.NOT_VERIFIED
    payload = build_dev_fixture_output_passport_payload()
    assert payload.side_effects.ledger_written is False
    assert payload.side_effects.global_trace_written is False
    assert payload.side_effects.trace_verified is False


def test_p1_9_6_assumption_limitation_uncertainty_envelope():
    envelope = build_assumption_limitation_uncertainty_envelope()
    assert len(envelope.assumptions) >= 1
    assert len(envelope.limitations) >= 1
    assert envelope.unknowns == ()
    assert envelope.uncertainty.uncertainty_level is OutputPassportUncertaintyLevel.MEDIUM


def test_p1_9_6_empty_lists_explicit():
    envelope = build_assumption_limitation_uncertainty_envelope(
        assumptions=(),
        limitations=(),
        unknowns=(),
    )
    assert envelope.assumptions == ()
    assert envelope.limitations == ()


def test_p1_9_6_rejects_invalid_uncertainty_level():
    from agentic_runtime.output_passport.foundation import PassportUncertainty

    with pytest.raises(OutputPassportValidationError):
        build_assumption_limitation_uncertainty_envelope(
            uncertainty=PassportUncertainty(
                uncertainty_level="not_a_level",
                uncertainty_status="declared",
                confidence_notes="",
                confidence_unavailable_reason=None,
            )
        )


def test_p1_9_7_hash_stable_and_changes_on_mutation():
    payload_a = build_dev_fixture_output_passport_payload()
    payload_b = build_dev_fixture_output_passport_payload()
    hash_a = compute_output_passport_hash(payload_a)
    hash_b = compute_output_passport_hash(payload_b)
    assert hash_a == hash_b
    assert payload_a.payload_hash == payload_b.payload_hash
    assert hash_a == compute_output_passport_hash(payload_a)

    mutated_identity = build_output_passport_identity(passport_id="dev-passport-002")
    payload_mutated = build_dev_fixture_output_passport_payload(identity=mutated_identity)
    hash_mutated = compute_output_passport_hash(payload_mutated)
    assert hash_mutated != hash_a


def test_p1_9_7_hash_json_safe_and_not_proof():
    payload = build_dev_fixture_output_passport_payload()
    serialized = serialize_output_passport_payload(payload)
    json.loads(serialized)
    contract = payload.hash_contract
    assert contract.hash_is_verification is False
    assert contract.determinism_profile.hash_is_truth is False
    assert contract.hash_truth_label is OutputPassportTruthLabel.DETERMINISTIC_PAYLOAD_HASH


def test_p1_9_7_volatile_fields_excluded_from_hash():
    payload = build_dev_fixture_output_passport_payload()
    hash_before = compute_output_passport_hash(payload)
    reparsed = OutputPassportPayload(
        schema_version=payload.schema_version,
        foundation=payload.foundation,
        identity=payload.identity,
        attribution_envelope=payload.attribution_envelope,
        authority_policy_risk=payload.authority_policy_risk,
        memory_influence=payload.memory_influence,
        evidence_trace_binding=payload.evidence_trace_binding,
        uncertainty_envelope=payload.uncertainty_envelope,
        hash_contract=payload.hash_contract,
        truth_label=payload.truth_label,
        source_label=payload.source_label,
        side_effects=payload.side_effects,
        payload_hash="different-volatile-value",
    )
    assert compute_output_passport_hash(reparsed) == hash_before


def test_pack_result_covers_all_checkpoints():
    result = build_p1_9_a_passport_pack_result()
    assert result.pack_id == "P1.9-A"
    assert result.section_id == "P1.9"
    assert result.covered_checkpoints == OUTPUT_PASSPORT_PACK_CHECKPOINT_IDS
    assert result.next_pack == OUTPUT_PASSPORT_NEXT_PACK_ID
    assert len(result.checkpoint_reads) == 8
    for checkpoint_id in OUTPUT_PASSPORT_PACK_CHECKPOINT_IDS:
        assert checkpoint_id in result.checkpoint_statuses
        assert result.checkpoint_statuses[checkpoint_id] == "DONE"


def test_pack_result_truth_labels_honest():
    result = build_p1_9_a_passport_pack_result()
    assert OutputPassportTruthLabel.DEV_FIXTURE in result.truth_labels
    assert OutputPassportTruthLabel.CONTRACT_ONLY in result.truth_labels
    assert OutputPassportTruthLabel.TRACE_VERIFIED not in result.truth_labels
    assert OutputPassportTruthLabel.LIVE not in result.truth_labels
    assert result.payload.truth_label is OutputPassportTruthLabel.DEV_FIXTURE
    assert_all_side_effects_false(result.side_effect_proof)


def test_pack_result_unavailable_reasons_explicit():
    result = build_p1_9_a_passport_pack_result()
    assert result.unavailable_reasons
    assert result.unavailable_reason_details
    assert "READ_MODEL_UNAVAILABLE" in {
        reason.value for reason in result.unavailable_reasons
    }


def test_boundary_defaults_all_false():
    boundary = OutputPassportBoundary()
    assert boundary.passport_is_proof is False
    assert boundary.disclosure_is_permission is False
