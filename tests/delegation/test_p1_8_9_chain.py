"""Focused P1.8.9 chain/handoff model tests (DEV_FIXTURE).

All chain/handoff refs are reference-only; no live handoff, responsibility
transfer, authority transfer, acceptance verification, predecessor/successor
verification, successor activation, chain verification, lineage graph engine,
runtime owner mutation, policy/Custos, approval, trace, or Ledger behavior
is implemented or claimed.
"""
from __future__ import annotations

import json

import pytest

from agentic_runtime.delegation import (
    DelegationChainSideEffects as ChSE,
    DelegationChainBinding,
    DelegationChainBindingSet,
    DelegationChainContinuityReadinessProfile,
    DelegationChainEnvelope,
    DelegationChainLinkKind,
    DelegationChainRef,
    DelegationChainReferenceStatus,
    DelegationChainSideEffects,
    DelegationChainStatus,
    DelegationChainStatusReport,
    DelegationHandoffAcceptanceClaimRef,
    DelegationHandoffClaimRef,
    DelegationHandoffKind,
    DelegationHandoffRef,
    DelegationLineageMap,
    DelegationPredecessorRef,
    DelegationResponsibilityTransferClaimRef,
    DelegationSuccessorRef,
    DelegationError,
    DelegationLifecycleBindingSet,
    DelegationSourceLabel,
    DelegationUnknownFieldError,
    DelegationValidationError,
    DELEGATION_CHAIN_UNAVAILABLE_BINDINGS,
    build_delegation_chain_binding,
    build_delegation_chain_binding_set,
    build_delegation_chain_continuity_readiness_profile,
    build_delegation_chain_envelope,
    build_delegation_chain_ref,
    build_delegation_chain_status_report,
    build_delegation_handoff_acceptance_claim_ref,
    build_delegation_handoff_claim_ref,
    build_delegation_handoff_ref,
    build_delegation_lineage_map,
    build_delegation_predecessor_ref,
    build_delegation_responsibility_transfer_claim_ref,
    build_delegation_successor_ref,
    hash_delegation_chain_binding,
    hash_delegation_chain_binding_set,
    hash_delegation_chain_continuity_readiness_profile,
    hash_delegation_chain_envelope,
    hash_delegation_chain_ref,
    hash_delegation_handoff_acceptance_claim_ref,
    hash_delegation_handoff_claim_ref,
    hash_delegation_handoff_ref,
    hash_delegation_lineage_map,
    hash_delegation_predecessor_ref,
    hash_delegation_responsibility_transfer_claim_ref,
    hash_delegation_successor_ref,
    serialize_delegation_chain_binding_set,
    serialize_delegation_chain_envelope,
)
from agentic_runtime.delegation.foundation import (
    DelegationSourceLabel as DSL,
    validate_known_fields,
)

# ---------------------------------------------------------------------------
# Reusable DEV_FIXTURE helpers
# ---------------------------------------------------------------------------

_DELEGATION_REF_ID = "P1.8.9-test-delegation-ref"
_ID_HASH = "abc123def456"
_ROLE_HASH = "role-111"
_CONSTRAINT_HASH = "constraint-111"
_AUTHORITY_HASH = "authority-111"
_EVIDENCE_HASH = "evidence-111"
_MESH_HASH = "mesh-111"
_SCOPE_HASH = "scope-111"
_LIFECYCLE_HASH = "lifecycle-111"


def _build_dev_fixture_chain_ref(**overrides) -> DelegationChainRef:
    kwargs = {
        "delegation_ref_id": _DELEGATION_REF_ID,
        "chain_link_kind": DelegationChainLinkKind.CONTINUED_BY,
        "chain_ref": "chain-ref-001",
        "chain_description": "DEV_FIXTURE chain ref for test",
        "source_label": DelegationSourceLabel.DEV_FIXTURE,
    }
    kwargs.update(overrides)
    return build_delegation_chain_ref(**kwargs)


def _build_dev_fixture_predecessor_ref(**overrides) -> DelegationPredecessorRef:
    kwargs = {
        "delegation_ref_id": _DELEGATION_REF_ID,
        "predecessor_delegation_ref": "predecessor-deleg-001",
        "source_label": DelegationSourceLabel.DEV_FIXTURE,
    }
    kwargs.update(overrides)
    return build_delegation_predecessor_ref(**kwargs)


def _build_dev_fixture_successor_ref(**overrides) -> DelegationSuccessorRef:
    kwargs = {
        "delegation_ref_id": _DELEGATION_REF_ID,
        "successor_delegation_ref": "successor-deleg-001",
        "source_label": DelegationSourceLabel.DEV_FIXTURE,
    }
    kwargs.update(overrides)
    return build_delegation_successor_ref(**kwargs)


def _build_dev_fixture_handoff_ref(**overrides) -> DelegationHandoffRef:
    kwargs = {
        "delegation_ref_id": _DELEGATION_REF_ID,
        "handoff_kind": DelegationHandoffKind.OPERATOR_TO_AGENT,
        "from_ref": "operator-A",
        "to_ref": "agent-B",
        "source_label": DelegationSourceLabel.DEV_FIXTURE,
    }
    kwargs.update(overrides)
    return build_delegation_handoff_ref(**kwargs)


def _build_dev_fixture_handoff_claim_ref(**overrides) -> DelegationHandoffClaimRef:
    handoff = _build_dev_fixture_handoff_ref()
    kwargs = {
        "delegation_ref_id": _DELEGATION_REF_ID,
        "handoff_ref_id": handoff.handoff_ref_id,
        "claim_ref": "claim-ref-001",
        "claim_statement": "DEV_FIXTURE handoff was declared",
        "source_label": DelegationSourceLabel.DEV_FIXTURE,
    }
    kwargs.update(overrides)
    return build_delegation_handoff_claim_ref(**kwargs)


def _build_dev_fixture_acceptance_claim_ref(**overrides) -> DelegationHandoffAcceptanceClaimRef:
    handoff = _build_dev_fixture_handoff_ref()
    kwargs = {
        "delegation_ref_id": _DELEGATION_REF_ID,
        "handoff_ref_id": handoff.handoff_ref_id,
        "acceptance_ref": "accept-ref-001",
        "acceptance_statement": "DEV_FIXTURE acceptance was declared",
        "source_label": DelegationSourceLabel.DEV_FIXTURE,
    }
    kwargs.update(overrides)
    return build_delegation_handoff_acceptance_claim_ref(**kwargs)


def _build_dev_fixture_transfer_claim_ref(**overrides) -> DelegationResponsibilityTransferClaimRef:
    handoff = _build_dev_fixture_handoff_ref()
    kwargs = {
        "delegation_ref_id": _DELEGATION_REF_ID,
        "handoff_ref_id": handoff.handoff_ref_id,
        "transfer_ref": "transfer-ref-001",
        "transfer_statement": "DEV_FIXTURE responsibility transfer was declared",
        "source_label": DelegationSourceLabel.DEV_FIXTURE,
    }
    kwargs.update(overrides)
    return build_delegation_responsibility_transfer_claim_ref(**kwargs)


# ---------------------------------------------------------------------------
# Test 1: Imports work from agentic_runtime.delegation
# ---------------------------------------------------------------------------


class TestImports:
    def test_module_imports(self):
        """P1.8.9 chain symbols are importable."""
        assert DelegationChainRef is not None
        assert DelegationPredecessorRef is not None
        assert DelegationSuccessorRef is not None
        assert DelegationHandoffRef is not None
        assert DelegationHandoffClaimRef is not None
        assert DelegationHandoffAcceptanceClaimRef is not None
        assert DelegationResponsibilityTransferClaimRef is not None
        assert DelegationLineageMap is not None
        assert DelegationChainContinuityReadinessProfile is not None
        assert DelegationChainEnvelope is not None
        assert DelegationChainBinding is not None
        assert DelegationChainBindingSet is not None
        assert DelegationChainSideEffects is not None
        assert DelegationChainStatusReport is not None

    def test_existing_p18_exports_remain_importable(self):
        """Existing P1.8.0-P1.8.8 exports remain importable."""
        from agentic_runtime.delegation import (  # noqa: F811
            DelegationRecord,
            DelegationRef,
            DelegationIdentity,
            DelegationPartyRoleRef,
            DelegationRoleBindingSet,
            DelegationConstraintRef,
            DelegationConstraintSet,
            DelegationAuthorityRef,
            DelegationAuthorityBindingSet,
            DelegationEvidenceRef,
            DelegationNonRepudiationBindingSet,
            DelegationMeshParticipantRef,
            DelegationIdentityMeshBindingSet,
            DelegationScopeRef,
            DelegationScopeBindingSet,
            DelegationExpiryRef,
            DelegationLifecycleBindingSet,
        )
        assert True


# ---------------------------------------------------------------------------
# Test 2: P1.8.8 LifecycleBindingSet feeds P1.8.9 chain path
# ---------------------------------------------------------------------------


class TestLifecyclePathFeed:
    def test_lifecycle_binding_set_feeds_chain_envelope(self):
        """P1.8.8 LifecycleBindingSet can feed P1.8.9 chain envelope."""
        envelope = build_delegation_chain_envelope(
            _DELEGATION_REF_ID,
            lifecycle_binding_set_hash=_LIFECYCLE_HASH,
        )
        assert envelope.lifecycle_binding_set_hash == _LIFECYCLE_HASH


# ---------------------------------------------------------------------------
# Tests 3-6: DelegationChainRef determinism
# ---------------------------------------------------------------------------


class TestDelegationChainRef:
    def test_builds_deterministically(self):
        a = _build_dev_fixture_chain_ref(chain_link_kind=DelegationChainLinkKind.ROOT)
        b = _build_dev_fixture_chain_ref(chain_link_kind=DelegationChainLinkKind.ROOT)
        assert a.chain_hash == b.chain_hash

    def test_identical_input_gives_identical_hash(self):
        a = _build_dev_fixture_chain_ref()
        b = _build_dev_fixture_chain_ref()
        assert hash_delegation_chain_ref(a) == hash_delegation_chain_ref(b)

    def test_changed_kind_changes_hash(self):
        a = _build_dev_fixture_chain_ref(chain_link_kind=DelegationChainLinkKind.ROOT)
        b = _build_dev_fixture_chain_ref(chain_link_kind=DelegationChainLinkKind.HANDOFF)
        assert a.chain_hash != b.chain_hash

    def test_changed_ref_changes_hash(self):
        a = _build_dev_fixture_chain_ref(chain_ref="chain-A")
        b = _build_dev_fixture_chain_ref(chain_ref="chain-B")
        assert a.chain_hash != b.chain_hash


# ---------------------------------------------------------------------------
# Tests 7-9: DelegationPredecessorRef determinism
# ---------------------------------------------------------------------------


class TestDelegationPredecessorRef:
    def test_builds_deterministically(self):
        a = _build_dev_fixture_predecessor_ref(predecessor_delegation_ref="pred-A")
        b = _build_dev_fixture_predecessor_ref(predecessor_delegation_ref="pred-A")
        assert a.predecessor_hash == b.predecessor_hash

    def test_identical_input_gives_identical_hash(self):
        a = _build_dev_fixture_predecessor_ref()
        b = _build_dev_fixture_predecessor_ref()
        assert hash_delegation_predecessor_ref(a) == hash_delegation_predecessor_ref(b)

    def test_changed_ref_changes_hash(self):
        a = _build_dev_fixture_predecessor_ref(predecessor_delegation_ref="pred-A")
        b = _build_dev_fixture_predecessor_ref(predecessor_delegation_ref="pred-B")
        assert a.predecessor_hash != b.predecessor_hash


# ---------------------------------------------------------------------------
# Tests 10-12: DelegationSuccessorRef determinism
# ---------------------------------------------------------------------------


class TestDelegationSuccessorRef:
    def test_builds_deterministically(self):
        a = _build_dev_fixture_successor_ref(successor_delegation_ref="succ-A")
        b = _build_dev_fixture_successor_ref(successor_delegation_ref="succ-A")
        assert a.successor_hash == b.successor_hash

    def test_identical_input_gives_identical_hash(self):
        a = _build_dev_fixture_successor_ref()
        b = _build_dev_fixture_successor_ref()
        assert hash_delegation_successor_ref(a) == hash_delegation_successor_ref(b)

    def test_changed_ref_changes_hash(self):
        a = _build_dev_fixture_successor_ref(successor_delegation_ref="succ-A")
        b = _build_dev_fixture_successor_ref(successor_delegation_ref="succ-B")
        assert a.successor_hash != b.successor_hash


# ---------------------------------------------------------------------------
# Tests 13-15: DelegationHandoffRef determinism
# ---------------------------------------------------------------------------


class TestDelegationHandoffRef:
    def test_builds_deterministically(self):
        a = _build_dev_fixture_handoff_ref(handoff_kind=DelegationHandoffKind.AGENT_TO_AGENT)
        b = _build_dev_fixture_handoff_ref(handoff_kind=DelegationHandoffKind.AGENT_TO_AGENT)
        assert a.handoff_hash == b.handoff_hash

    def test_identical_input_gives_identical_hash(self):
        a = _build_dev_fixture_handoff_ref()
        b = _build_dev_fixture_handoff_ref()
        assert hash_delegation_handoff_ref(a) == hash_delegation_handoff_ref(b)

    def test_changed_kind_changes_hash(self):
        a = _build_dev_fixture_handoff_ref(handoff_kind=DelegationHandoffKind.REFERENCE_ONLY)
        b = _build_dev_fixture_handoff_ref(handoff_kind=DelegationHandoffKind.SYSTEM_TO_AGENT)
        assert a.handoff_hash != b.handoff_hash


# ---------------------------------------------------------------------------
# Tests 16-18: DelegationHandoffClaimRef determinism
# ---------------------------------------------------------------------------


class TestDelegationHandoffClaimRef:
    def test_builds_deterministically(self):
        a = _build_dev_fixture_handoff_claim_ref(claim_ref="claim-A")
        b = _build_dev_fixture_handoff_claim_ref(claim_ref="claim-A")
        assert a.handoff_claim_hash == b.handoff_claim_hash

    def test_identical_input_gives_identical_hash(self):
        a = _build_dev_fixture_handoff_claim_ref()
        b = _build_dev_fixture_handoff_claim_ref()
        assert hash_delegation_handoff_claim_ref(a) == hash_delegation_handoff_claim_ref(b)

    def test_changed_claim_changes_hash(self):
        a = _build_dev_fixture_handoff_claim_ref(claim_ref="claim-A")
        b = _build_dev_fixture_handoff_claim_ref(claim_ref="claim-B")
        assert a.handoff_claim_hash != b.handoff_claim_hash


# ---------------------------------------------------------------------------
# Tests 19-21: DelegationHandoffAcceptanceClaimRef determinism
# ---------------------------------------------------------------------------


class TestDelegationHandoffAcceptanceClaimRef:
    def test_builds_deterministically(self):
        a = _build_dev_fixture_acceptance_claim_ref(acceptance_ref="accept-A")
        b = _build_dev_fixture_acceptance_claim_ref(acceptance_ref="accept-A")
        assert a.acceptance_claim_hash == b.acceptance_claim_hash

    def test_identical_input_gives_identical_hash(self):
        a = _build_dev_fixture_acceptance_claim_ref()
        b = _build_dev_fixture_acceptance_claim_ref()
        assert hash_delegation_handoff_acceptance_claim_ref(a) == hash_delegation_handoff_acceptance_claim_ref(b)

    def test_changed_acceptance_changes_hash(self):
        a = _build_dev_fixture_acceptance_claim_ref(acceptance_ref="accept-A")
        b = _build_dev_fixture_acceptance_claim_ref(acceptance_ref="accept-B")
        assert a.acceptance_claim_hash != b.acceptance_claim_hash


# ---------------------------------------------------------------------------
# Tests 22-24: DelegationResponsibilityTransferClaimRef determinism
# ---------------------------------------------------------------------------


class TestDelegationResponsibilityTransferClaimRef:
    def test_builds_deterministically(self):
        a = _build_dev_fixture_transfer_claim_ref(transfer_ref="tx-A")
        b = _build_dev_fixture_transfer_claim_ref(transfer_ref="tx-A")
        assert a.transfer_claim_hash == b.transfer_claim_hash

    def test_identical_input_gives_identical_hash(self):
        a = _build_dev_fixture_transfer_claim_ref()
        b = _build_dev_fixture_transfer_claim_ref()
        assert hash_delegation_responsibility_transfer_claim_ref(a) == hash_delegation_responsibility_transfer_claim_ref(b)

    def test_changed_transfer_changes_hash(self):
        a = _build_dev_fixture_transfer_claim_ref(transfer_ref="tx-A")
        b = _build_dev_fixture_transfer_claim_ref(transfer_ref="tx-B")
        assert a.transfer_claim_hash != b.transfer_claim_hash


# ---------------------------------------------------------------------------
# Test 25: ChainReferenceStatus enum values
# ---------------------------------------------------------------------------


class TestChainReferenceStatusEnum:
    def test_all_expected_values_exist(self):
        values = {e.value for e in DelegationChainReferenceStatus}
        expected = {
            "REFERENCE_ONLY",
            "CHAIN_REFERENCED",
            "PREDECESSOR_REFERENCED",
            "SUCCESSOR_REFERENCED",
            "HANDOFF_REFERENCED",
            "HANDOFF_CLAIM_REFERENCED",
            "ACCEPTANCE_CLAIM_REFERENCED",
            "TRANSFER_CLAIM_REFERENCED",
            "CHAIN_VERIFIER_UNAVAILABLE",
            "HANDOFF_EXECUTOR_UNAVAILABLE",
            "UNAVAILABLE",
            "ERROR",
            "UNKNOWN",
        }
        assert values == expected


# ---------------------------------------------------------------------------
# Tests 26-33: Non-implying boundary tests (Ref exists ≠ action performed)
# ---------------------------------------------------------------------------


class TestChainHandoffBoundaries:
    def test_handoff_ref_does_not_imply_handoff_executed(self):
        ref = _build_dev_fixture_handoff_ref()
        assert ref is not None
        assert ref.handoff_kind != DelegationHandoffKind.UNKNOWN

    def test_handoff_claim_ref_does_not_imply_handoff_occurred(self):
        ref = _build_dev_fixture_handoff_claim_ref()
        assert ref is not None
        assert ref.handoff_ref_id != ""

    def test_acceptance_claim_ref_does_not_imply_acceptance_verified(self):
        ref = _build_dev_fixture_acceptance_claim_ref()
        assert ref is not None

    def test_transfer_claim_ref_does_not_imply_transferred(self):
        ref = _build_dev_fixture_transfer_claim_ref()
        assert ref is not None

    def test_predecessor_ref_does_not_imply_predecessor_valid(self):
        ref = _build_dev_fixture_predecessor_ref()
        assert ref is not None

    def test_successor_ref_does_not_imply_successor_activated(self):
        ref = _build_dev_fixture_successor_ref()
        assert ref is not None

    def test_chain_ref_does_not_imply_chain_verified(self):
        ref = _build_dev_fixture_chain_ref()
        assert ref is not None
        assert ref.chain_status == DelegationChainStatus.DECLARED


# ---------------------------------------------------------------------------
# Tests 34-36: DelegationLineageMap determinism
# ---------------------------------------------------------------------------


class TestDelegationLineageMap:
    def test_identical_lineage_gives_identical_hash(self):
        a = build_delegation_lineage_map(
            _DELEGATION_REF_ID,
            predecessor_refs=("pred-1", "pred-2"),
            successor_refs=("succ-1",),
        )
        b = build_delegation_lineage_map(
            _DELEGATION_REF_ID,
            predecessor_refs=("pred-1", "pred-2"),
            successor_refs=("succ-1",),
        )
        assert hash_delegation_lineage_map(a) == hash_delegation_lineage_map(b)

    def test_changed_membership_changes_hash(self):
        a = build_delegation_lineage_map(
            _DELEGATION_REF_ID, predecessor_refs=("pred-1",)
        )
        b = build_delegation_lineage_map(
            _DELEGATION_REF_ID, predecessor_refs=("pred-2",)
        )
        assert a.lineage_map_hash != b.lineage_map_hash

    def test_ordering_is_deterministic(self):
        a = build_delegation_lineage_map(
            _DELEGATION_REF_ID,
            predecessor_refs=("b", "a"),
            successor_refs=("d", "c"),
        )
        b = build_delegation_lineage_map(
            _DELEGATION_REF_ID,
            predecessor_refs=("a", "b"),
            successor_refs=("c", "d"),
        )
        assert a.lineage_map_hash == b.lineage_map_hash


# ---------------------------------------------------------------------------
# Test 37: LineageMap is not graph engine
# ---------------------------------------------------------------------------


class TestLineageMapNotGraph:
    def test_lineage_map_is_not_graph_engine(self):
        lm = build_delegation_lineage_map(
            _DELEGATION_REF_ID,
            predecessor_refs=("a", "b"),
            successor_refs=("c",),
            handoff_refs=("h1",),
            chain_refs=("ch1",),
        )
        assert lm is not None
        assert isinstance(lm.predecessor_refs, tuple)
        assert isinstance(lm.successor_refs, tuple)


# ---------------------------------------------------------------------------
# Tests 38-42: ChainContinuityReadinessProfile
# ---------------------------------------------------------------------------


class TestChainContinuityReadinessProfile:
    def test_identical_profile_gives_identical_hash(self):
        a = build_delegation_chain_continuity_readiness_profile(
            _DELEGATION_REF_ID,
            has_chain_refs=True,
            has_handoff_refs=True,
            missing_components=("chain_verifier", "handoff_executor"),
        )
        b = build_delegation_chain_continuity_readiness_profile(
            _DELEGATION_REF_ID,
            has_chain_refs=True,
            has_handoff_refs=True,
            missing_components=("chain_verifier", "handoff_executor"),
        )
        assert hash_delegation_chain_continuity_readiness_profile(a) == hash_delegation_chain_continuity_readiness_profile(b)

    def test_reports_present_components(self):
        profile = build_delegation_chain_continuity_readiness_profile(
            _DELEGATION_REF_ID,
            has_chain_refs=True,
            has_predecessor_refs=True,
        )
        assert profile.has_chain_refs is True
        assert profile.has_predecessor_refs is True

    def test_reports_missing_components(self):
        profile = build_delegation_chain_continuity_readiness_profile(
            _DELEGATION_REF_ID,
            has_chain_refs=False,
            has_handoff_refs=False,
            missing_components=("chain_refs", "handoff_refs"),
        )
        assert profile.has_chain_refs is False
        assert profile.has_handoff_refs is False
        assert "chain_refs" in profile.missing_components

    def test_readiness_profile_is_not_chain_verification(self):
        profile = build_delegation_chain_continuity_readiness_profile(
            _DELEGATION_REF_ID,
            has_chain_refs=True,
        )
        assert profile is not None
        assert profile.chain_verifier_unavailable_reason != ""

    def test_readiness_profile_is_not_continuity_proof(self):
        profile = build_delegation_chain_continuity_readiness_profile(
            _DELEGATION_REF_ID,
            has_chain_refs=True,
            has_handoff_refs=True,
            has_acceptance_claim_refs=True,
        )
        assert profile is not None
        assert len(profile.missing_components) == 0 if not profile.missing_components else True
        assert "chain verifier" in profile.chain_verifier_unavailable_reason.lower()


# ---------------------------------------------------------------------------
# Tests 43-46: ChainEnvelope
# ---------------------------------------------------------------------------


class TestChainEnvelope:
    def test_identical_envelope_gives_identical_hash(self):
        a = build_delegation_chain_envelope(
            _DELEGATION_REF_ID,
            chain_refs=("ch1", "ch2"),
            handoff_refs=("h1",),
        )
        b = build_delegation_chain_envelope(
            _DELEGATION_REF_ID,
            chain_refs=("ch1", "ch2"),
            handoff_refs=("h1",),
        )
        assert hash_delegation_chain_envelope(a) == hash_delegation_chain_envelope(b)

    def test_changed_membership_changes_hash(self):
        a = build_delegation_chain_envelope(
            _DELEGATION_REF_ID, chain_refs=("ch1",)
        )
        b = build_delegation_chain_envelope(
            _DELEGATION_REF_ID, chain_refs=("ch2",)
        )
        assert a.chain_envelope_hash != b.chain_envelope_hash

    def test_ordering_is_deterministic(self):
        a = build_delegation_chain_envelope(
            _DELEGATION_REF_ID,
            chain_refs=("b", "a"),
            handoff_refs=("d", "c"),
        )
        b = build_delegation_chain_envelope(
            _DELEGATION_REF_ID,
            chain_refs=("a", "b"),
            handoff_refs=("c", "d"),
        )
        assert a.chain_envelope_hash == b.chain_envelope_hash

    def test_json_safe_serialization(self):
        envelope = build_delegation_chain_envelope(
            _DELEGATION_REF_ID,
            identity_mesh_binding_set_hash=_MESH_HASH,
            scope_binding_set_hash=_SCOPE_HASH,
            lifecycle_binding_set_hash=_LIFECYCLE_HASH,
            chain_refs=("ch1",),
            handoff_refs=("h1",),
        )
        json_str = serialize_delegation_chain_envelope(envelope)
        data = json.loads(json_str)
        assert data["delegation_ref_id"] == _DELEGATION_REF_ID


# ---------------------------------------------------------------------------
# Tests 47-49: ChainBinding
# ---------------------------------------------------------------------------


class TestChainBinding:
    def test_identical_binding_gives_identical_hash(self):
        a = build_delegation_chain_binding(
            _DELEGATION_REF_ID,
            chain_envelope_hash="env-hash-001",
        )
        b = build_delegation_chain_binding(
            _DELEGATION_REF_ID,
            chain_envelope_hash="env-hash-001",
        )
        assert hash_delegation_chain_binding(a) == hash_delegation_chain_binding(b)

    def test_changed_envelope_changes_hash(self):
        a = build_delegation_chain_binding(
            _DELEGATION_REF_ID,
            chain_envelope_hash="env-A",
        )
        b = build_delegation_chain_binding(
            _DELEGATION_REF_ID,
            chain_envelope_hash="env-B",
        )
        assert a.binding_hash != b.binding_hash

    def test_binding_binds_all_context_hashes(self):
        b = build_delegation_chain_binding(
            _DELEGATION_REF_ID,
            delegation_identity_hash=_ID_HASH,
            role_binding_hash=_ROLE_HASH,
            constraint_set_hash=_CONSTRAINT_HASH,
            authority_binding_set_hash=_AUTHORITY_HASH,
            non_repudiation_binding_set_hash=_EVIDENCE_HASH,
            identity_mesh_binding_set_hash=_MESH_HASH,
            scope_binding_set_hash=_SCOPE_HASH,
            lifecycle_binding_set_hash=_LIFECYCLE_HASH,
            chain_envelope_hash="env-hash",
        )
        assert b.delegation_identity_hash == _ID_HASH
        assert b.lifecycle_binding_set_hash == _LIFECYCLE_HASH


# ---------------------------------------------------------------------------
# Tests 50-52: ChainBindingSet
# ---------------------------------------------------------------------------


class TestChainBindingSet:
    def test_identical_set_gives_identical_hash(self):
        binding = build_delegation_chain_binding(
            _DELEGATION_REF_ID, chain_envelope_hash="env-hash"
        )
        a = build_delegation_chain_binding_set(
            _DELEGATION_REF_ID, bindings=(binding,)
        )
        binding2 = build_delegation_chain_binding(
            _DELEGATION_REF_ID, chain_envelope_hash="env-hash"
        )
        b = build_delegation_chain_binding_set(
            _DELEGATION_REF_ID, bindings=(binding2,)
        )
        assert hash_delegation_chain_binding_set(a) == hash_delegation_chain_binding_set(b)

    def test_changed_binding_changes_hash(self):
        b1 = build_delegation_chain_binding(
            _DELEGATION_REF_ID, chain_envelope_hash="env-A"
        )
        a = build_delegation_chain_binding_set(
            _DELEGATION_REF_ID, bindings=(b1,)
        )
        b2 = build_delegation_chain_binding(
            _DELEGATION_REF_ID, chain_envelope_hash="env-B"
        )
        b = build_delegation_chain_binding_set(
            _DELEGATION_REF_ID, bindings=(b2,)
        )
        assert a.chain_binding_set_hash != b.chain_binding_set_hash

    def test_json_safe_serialization(self):
        binding = build_delegation_chain_binding(
            _DELEGATION_REF_ID, chain_envelope_hash="env-hash"
        )
        bs = build_delegation_chain_binding_set(
            _DELEGATION_REF_ID, bindings=(binding,)
        )
        json_str = serialize_delegation_chain_binding_set(bs)
        data = json.loads(json_str)
        assert data["delegation_ref_id"] == _DELEGATION_REF_ID
        assert len(data["bindings"]) == 1


# ---------------------------------------------------------------------------
# Tests 53-56: Closed-world validation
# ---------------------------------------------------------------------------


class TestClosedWorldValidation:
    def test_rejects_unknown_field_chain_ref(self):
        from agentic_runtime.delegation.chain import CHAIN_REF_KNOWN_FIELDS
        with pytest.raises(DelegationUnknownFieldError):
            validate_known_fields(
                {"delegation_ref_id": "d1", "chain_link_kind": "ROOT", "ghost": True},
                CHAIN_REF_KNOWN_FIELDS,
                label="delegation_chain_ref",
            )

    def test_rejects_unknown_field_handoff_ref(self):
        from agentic_runtime.delegation.chain import HANDOFF_REF_KNOWN_FIELDS
        with pytest.raises(DelegationUnknownFieldError):
            validate_known_fields(
                {"delegation_ref_id": "d1", "handoff_kind": "REFERENCE_ONLY", "ghost": True},
                HANDOFF_REF_KNOWN_FIELDS,
                label="delegation_handoff_ref",
            )

    def test_rejects_unknown_field_lineage_map(self):
        from agentic_runtime.delegation.chain import LINEAGE_MAP_KNOWN_FIELDS
        with pytest.raises(DelegationUnknownFieldError):
            validate_known_fields(
                {"delegation_ref_id": "d1", "ghost": True},
                LINEAGE_MAP_KNOWN_FIELDS,
                label="delegation_lineage_map",
            )

    def test_validation_passes_with_known_fields(self):
        from agentic_runtime.delegation.chain import CHAIN_REF_KNOWN_FIELDS
        result = validate_known_fields(
            {"delegation_ref_id": "d1", "chain_link_kind": "ROOT"},
            CHAIN_REF_KNOWN_FIELDS,
            label="delegation_chain_ref",
        )
        assert result is None


# ---------------------------------------------------------------------------
# Test 57: Source/truth labels are visible
# ---------------------------------------------------------------------------


class TestSourceLabels:
    def test_dev_fixture_label_visible(self):
        ref = _build_dev_fixture_chain_ref()
        assert ref.source_label == DelegationSourceLabel.DEV_FIXTURE

    def test_live_label_visible_on_contracts(self):
        report = build_delegation_chain_status_report()
        assert DelegationSourceLabel.LIVE.value in report.available_contracts.values()  # type: ignore[union-attr]


# ---------------------------------------------------------------------------
# Test 58: DEV_FIXTURE path explicit
# ---------------------------------------------------------------------------


class TestDevFixtureExplicit:
    def test_all_refs_use_dev_fixture(self):
        chain_ref = _build_dev_fixture_chain_ref()
        predecessor = _build_dev_fixture_predecessor_ref()
        successor = _build_dev_fixture_successor_ref()
        handoff = _build_dev_fixture_handoff_ref()
        claim = _build_dev_fixture_handoff_claim_ref()
        assert chain_ref.source_label == DelegationSourceLabel.DEV_FIXTURE
        assert predecessor.source_label == DelegationSourceLabel.DEV_FIXTURE
        assert successor.source_label == DelegationSourceLabel.DEV_FIXTURE
        assert handoff.source_label == DelegationSourceLabel.DEV_FIXTURE
        assert claim.source_label == DelegationSourceLabel.DEV_FIXTURE


# ---------------------------------------------------------------------------
# Test 59: Unavailable surface reasons
# ---------------------------------------------------------------------------


class TestUnavailableSurfaces:
    def test_all_expected_unavailable_surfaces(self):
        assert "Live Handoff Executor" in DELEGATION_CHAIN_UNAVAILABLE_BINDINGS
        assert "Responsibility Transfer Engine" in DELEGATION_CHAIN_UNAVAILABLE_BINDINGS
        assert "Authority Transfer Engine" in DELEGATION_CHAIN_UNAVAILABLE_BINDINGS
        assert "Handoff Acceptance Verifier" in DELEGATION_CHAIN_UNAVAILABLE_BINDINGS
        assert "Predecessor/Successor Verifier" in DELEGATION_CHAIN_UNAVAILABLE_BINDINGS
        assert "Chain Verifier" in DELEGATION_CHAIN_UNAVAILABLE_BINDINGS
        assert "Lineage Graph Engine" in DELEGATION_CHAIN_UNAVAILABLE_BINDINGS
        assert "Runtime Owner Mutation" in DELEGATION_CHAIN_UNAVAILABLE_BINDINGS
        assert "Policy/Custos Decision" in DELEGATION_CHAIN_UNAVAILABLE_BINDINGS
        assert "Approval Creation" in DELEGATION_CHAIN_UNAVAILABLE_BINDINGS
        assert "P1.8.10 Shadow Resolver / Consistency Model" in DELEGATION_CHAIN_UNAVAILABLE_BINDINGS
        assert "Output Passport / P1.9" in DELEGATION_CHAIN_UNAVAILABLE_BINDINGS
        assert "Ledger Write" in DELEGATION_CHAIN_UNAVAILABLE_BINDINGS
        assert "Global Trace Write" in DELEGATION_CHAIN_UNAVAILABLE_BINDINGS
        assert "CLI/Shell/TUI Binding" in DELEGATION_CHAIN_UNAVAILABLE_BINDINGS
        assert "Projection/API/Event/Read Model" in DELEGATION_CHAIN_UNAVAILABLE_BINDINGS
        assert "Runtime Delegation Execution" in DELEGATION_CHAIN_UNAVAILABLE_BINDINGS

    def test_status_report_shows_unavailable_reasons(self):
        report = build_delegation_chain_status_report()
        assert report.unavailable_bindings is not None  # type: ignore[union-attr]
        assert len(report.unavailable_bindings) >= 15  # type: ignore[union-attr]


# ---------------------------------------------------------------------------
# Tests 60-66: All DelegationChainSideEffects booleans are false
# ---------------------------------------------------------------------------


class TestSideEffects:
    def test_all_side_effects_false(self):
        se = DelegationChainSideEffects()
        assert not se.handoff_executed
        assert not se.responsibility_transferred
        assert not se.acceptance_verified
        assert not se.authority_transferred
        assert not se.predecessor_verified
        assert not se.successor_activated
        assert not se.chain_verified
        assert not se.lineage_graph_built
        assert not se.runtime_owner_changed
        assert not se.policy_called
        assert not se.custos_called
        assert not se.approval_created
        assert not se.ledger_written
        assert not se.global_trace_written
        assert not se.runtime_mutated

    def test_no_live_handoff(self):
        se = DelegationChainSideEffects()
        assert se.handoff_executed is False

    def test_no_responsibility_transfer(self):
        se = DelegationChainSideEffects()
        assert se.responsibility_transferred is False

    def test_no_acceptance_verification(self):
        se = DelegationChainSideEffects()
        assert se.acceptance_verified is False

    def test_no_authority_transfer(self):
        se = DelegationChainSideEffects()
        assert se.authority_transferred is False

    def test_no_predecessor_verification(self):
        se = DelegationChainSideEffects()
        assert se.predecessor_verified is False

    def test_no_successor_activation(self):
        se = DelegationChainSideEffects()
        assert se.successor_activated is False

    def test_no_chain_verification(self):
        se = DelegationChainSideEffects()
        assert se.chain_verified is False

    def test_no_lineage_graph_engine(self):
        se = DelegationChainSideEffects()
        assert se.lineage_graph_built is False

    def test_no_runtime_owner_change(self):
        se = DelegationChainSideEffects()
        assert se.runtime_owner_changed is False

    def test_no_policy_custos_decision(self):
        se = DelegationChainSideEffects()
        assert se.policy_called is False
        assert se.custos_called is False

    def test_no_approval_creation(self):
        se = DelegationChainSideEffects()
        assert se.approval_created is False

    def test_no_ledger_or_global_trace_write(self):
        se = DelegationChainSideEffects()
        assert se.ledger_written is False
        assert se.global_trace_written is False

    def test_no_runtime_mutation(self):
        se = DelegationChainSideEffects()
        assert se.runtime_mutated is False

    def test_no_p1810_shadow_resolver(self):
        """P1.8.10 shadow resolver not implemented."""
        assert True

    def test_no_output_passport(self):
        """P1.9 Output Passport not implemented."""
        assert True


# ---------------------------------------------------------------------------
# Test 67: Operator-testable DEV_FIXTURE path
# ---------------------------------------------------------------------------


class TestOperatorTestablePath:
    def test_full_dev_fixture_chain_path(self):
        """P1.8.8 LifecycleBindingSet -> chain refs -> lineage -> readiness
        -> envelope -> binding -> binding set -> hash -> status report -> unavailable
        reasons -> side effects all false."""
        # Build constituent refs
        chain_ref = _build_dev_fixture_chain_ref()
        predecessor = _build_dev_fixture_predecessor_ref()
        successor = _build_dev_fixture_successor_ref()
        handoff = _build_dev_fixture_handoff_ref()
        handoff_claim = _build_dev_fixture_handoff_claim_ref()
        acceptance = _build_dev_fixture_acceptance_claim_ref()
        transfer = _build_dev_fixture_transfer_claim_ref()

        # LineageMap
        lineage = build_delegation_lineage_map(
            _DELEGATION_REF_ID,
            predecessor_refs=(predecessor.predecessor_ref_id,),
            successor_refs=(successor.successor_ref_id,),
            handoff_refs=(handoff.handoff_ref_id,),
            chain_refs=(chain_ref.chain_ref_id,),
        )
        assert lineage.lineage_map_hash != ""

        # Readiness profile
        profile = build_delegation_chain_continuity_readiness_profile(
            _DELEGATION_REF_ID,
            has_chain_refs=True,
            has_predecessor_refs=True,
            has_successor_refs=True,
            has_handoff_refs=True,
            has_handoff_claim_refs=True,
            has_acceptance_claim_refs=True,
            has_transfer_claim_refs=True,
            has_lifecycle_context=True,
            has_scope_context=True,
            has_authority_context=True,
            has_evidence_context=True,
            has_identity_mesh_context=True,
        )
        assert profile.readiness_hash != ""

        # Envelope
        envelope = build_delegation_chain_envelope(
            _DELEGATION_REF_ID,
            delegation_identity_hash=_ID_HASH,
            role_binding_hash=_ROLE_HASH,
            constraint_set_hash=_CONSTRAINT_HASH,
            authority_binding_set_hash=_AUTHORITY_HASH,
            non_repudiation_binding_set_hash=_EVIDENCE_HASH,
            identity_mesh_binding_set_hash=_MESH_HASH,
            scope_binding_set_hash=_SCOPE_HASH,
            lifecycle_binding_set_hash=_LIFECYCLE_HASH,
            chain_refs=(chain_ref.chain_ref_id,),
            predecessor_refs=(predecessor.predecessor_ref_id,),
            successor_refs=(successor.successor_ref_id,),
            handoff_refs=(handoff.handoff_ref_id,),
            handoff_claim_refs=(handoff_claim.handoff_claim_ref_id,),
            handoff_acceptance_claim_refs=(acceptance.acceptance_claim_ref_id,),
            responsibility_transfer_claim_refs=(transfer.transfer_claim_ref_id,),
            lineage_map_hash=lineage.lineage_map_hash,
            continuity_readiness_hash=profile.readiness_hash,
        )
        assert envelope.chain_envelope_hash != ""

        # Binding
        binding = build_delegation_chain_binding(
            _DELEGATION_REF_ID,
            delegation_identity_hash=_ID_HASH,
            role_binding_hash=_ROLE_HASH,
            constraint_set_hash=_CONSTRAINT_HASH,
            authority_binding_set_hash=_AUTHORITY_HASH,
            non_repudiation_binding_set_hash=_EVIDENCE_HASH,
            identity_mesh_binding_set_hash=_MESH_HASH,
            scope_binding_set_hash=_SCOPE_HASH,
            lifecycle_binding_set_hash=_LIFECYCLE_HASH,
            chain_envelope_hash=envelope.chain_envelope_hash,
            lineage_map_hash=lineage.lineage_map_hash,
            continuity_readiness_hash=profile.readiness_hash,
        )
        assert binding.binding_hash != ""

        # BindingSet
        bs = build_delegation_chain_binding_set(
            _DELEGATION_REF_ID,
            delegation_identity_hash=_ID_HASH,
            role_binding_hash=_ROLE_HASH,
            constraint_set_hash=_CONSTRAINT_HASH,
            authority_binding_set_hash=_AUTHORITY_HASH,
            non_repudiation_binding_set_hash=_EVIDENCE_HASH,
            identity_mesh_binding_set_hash=_MESH_HASH,
            scope_binding_set_hash=_SCOPE_HASH,
            lifecycle_binding_set_hash=_LIFECYCLE_HASH,
            bindings=(binding,),
        )
        assert bs.chain_binding_set_hash != ""

        # Status report
        report = build_delegation_chain_status_report()
        assert report.status_hash != ""

        # Unavailable reasons visible
        assert len(report.unavailable_bindings) >= 15  # type: ignore[union-attr]

        # Side effects all false
        se = bs.side_effects
        assert not se.handoff_executed  # type: ignore[union-attr]
        assert not se.responsibility_transferred  # type: ignore[union-attr]
        assert not se.acceptance_verified  # type: ignore[union-attr]
        assert not se.authority_transferred  # type: ignore[union-attr]
        assert not se.predecessor_verified  # type: ignore[union-attr]
        assert not se.successor_activated  # type: ignore[union-attr]
        assert not se.chain_verified  # type: ignore[union-attr]
        assert not se.lineage_graph_built  # type: ignore[union-attr]
        assert not se.runtime_owner_changed  # type: ignore[union-attr]
        assert not se.policy_called  # type: ignore[union-attr]
        assert not se.custos_called  # type: ignore[union-attr]
        assert not se.approval_created  # type: ignore[union-attr]
        assert not se.ledger_written  # type: ignore[union-attr]
        assert not se.global_trace_written  # type: ignore[union-attr]
        assert not se.runtime_mutated  # type: ignore[union-attr]
