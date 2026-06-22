"""Authority relation anchor for Aurel Operator Relationship Contract (P1.4.3).

This module summarizes the principal/delegate relationship only. It does not
implement delegation mesh, grant scopes, or create delegation grants.
"""
from __future__ import annotations

from .operator_contract import AurelOperatorContract, AuthorityRelation


def build_authority_relation(contract: AurelOperatorContract) -> AuthorityRelation:
    """Build a relationship anchor from a validated operator contract."""
    principal = contract.parties.principal
    delegate = contract.parties.delegate
    auth = contract.authority
    return AuthorityRelation(
        principal_id=principal.id,
        principal_role=principal.role,
        delegate_id=delegate.id,
        delegate_role=delegate.role,
        final_authority=principal.id,
        delegate_can_self_escalate=auth.aurel_can_self_escalate,
        delegate_can_replace_principal=auth.aurel_can_replace_operator,
    )
