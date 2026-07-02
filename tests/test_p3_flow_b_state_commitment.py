from __future__ import annotations

from dataclasses import replace

import pytest

from agentic_runtime.aurel_flow import (
    AurelFlowErrorCode,
    AurelFlowValidationError,
    MUTATION_SCOPE_INTERNAL,
    RuntimeSymbolState,
    commit_internal_runtime_state,
    create_mediated_actor_output,
    create_runtime_state_commitment,
)


def _output(**overrides):
    params = dict(
        actor_id="actor-1",
        target_run_id="wfrun-test",
        target_node_id="work",
        proposed_symbol_or_state_ref="work.result.v1",
    )
    params.update(overrides)
    return create_mediated_actor_output(**params)


def _commitment(output=None):
    return create_runtime_state_commitment(
        output or _output(),
        previous_state_ref="work.result.v0",
        proposed_state_ref="work.result.v1",
    )


def test_mediated_output_cannot_allow_direct_state_mutation() -> None:
    output = _output()

    assert output.direct_state_mutation_allowed is False
    with pytest.raises(AurelFlowValidationError) as excinfo:
        replace(output, direct_state_mutation_allowed=True)

    assert excinfo.value.code is AurelFlowErrorCode.DIRECT_STATE_MUTATION_FORBIDDEN


def test_commitment_lifecycle_proposed_to_committed_internal() -> None:
    commitment = _commitment()

    assert commitment.commit_status is RuntimeSymbolState.PROPOSED
    assert commitment.state_mutated is False

    result = commit_internal_runtime_state(commitment)

    assert result.accepted is True
    assert result.commitment.commit_status is RuntimeSymbolState.COMMITTED_INTERNAL
    assert result.commitment.state_mutated is True
    assert result.commitment.mutation_scope == MUTATION_SCOPE_INTERNAL
    assert result.internal_only is True
    assert "not a Ledger commit" in result.reason


def test_committed_internal_means_internal_only() -> None:
    result = commit_internal_runtime_state(_commitment())
    committed = result.commitment

    assert committed.authority_granted is False
    assert committed.ledger_written is False
    assert committed.external_side_effect is False
    assert result.ledger_written is False
    assert result.external_side_effect is False


def test_rejected_validation_blocks_internal_commit() -> None:
    rejected_output = _output(validation_status=RuntimeSymbolState.REJECTED)
    result = commit_internal_runtime_state(_commitment(rejected_output))

    assert result.accepted is False
    assert result.commitment.commit_status is RuntimeSymbolState.REJECTED
    assert "validation_status" in result.reason


def test_already_committed_commitment_cannot_commit_again() -> None:
    first = commit_internal_runtime_state(_commitment())
    second = commit_internal_runtime_state(first.commitment)

    assert second.accepted is False
    assert "not committable" in second.reason


def test_commitment_boundary_booleans_fail_closed() -> None:
    commitment = _commitment()

    for boundary_field in ("authority_granted", "ledger_written", "external_side_effect"):
        with pytest.raises(AurelFlowValidationError) as excinfo:
            replace(commitment, **{boundary_field: True})
        assert excinfo.value.code is AurelFlowErrorCode.FORBIDDEN_BOUNDARY_CLAIM

    with pytest.raises(AurelFlowValidationError):
        replace(commitment, mutation_scope="EXTERNAL_WORLD")


def test_deterministic_ids_and_empty_actor_fail_closed() -> None:
    assert _output().output_id == _output().output_id
    assert _commitment().commitment_id == _commitment().commitment_id

    with pytest.raises(AurelFlowValidationError) as excinfo:
        create_mediated_actor_output(
            actor_id="",
            target_run_id="wfrun-test",
            proposed_symbol_or_state_ref="ref",
        )

    assert excinfo.value.code is AurelFlowErrorCode.EMPTY_ACTOR_ID
