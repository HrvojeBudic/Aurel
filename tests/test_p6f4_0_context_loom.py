"""F4.0 seal — ContextLoom foundation (governed context assembly).

  1. Provenance + taint (reuse F3.0) — external items are instruction-ineligible;
     internal items are eligible; label derived from origin.
  2. Deterministic + content-addressed — same items ⇒ same order + same
     context_ref; dedup by content hash.
  3. Budget-aware, no silent loss — a token ceiling drops lowest-priority items
     and RECORDS every drop; highest priority is kept.
  4. Rendering doctrine — external items are fenced as untrusted data in
     to_prompt; internal items render plainly.
  5. Flag default OFF.
"""
from __future__ import annotations

from agentic_runtime.context_loom import (
    assemble,
    flag_enabled,
    make_context_item,
)
from agentic_runtime.external_ingress import SourceKind, TaintLabel


def _op(text, prio=None):
    return make_context_item(text, SourceKind.OPERATOR, "op", prio)


def _ext(text, prio=None):
    return make_context_item(text, SourceKind.MCP_TOOL, "mcp", prio)


# --------------------------------------------------------------------------- #
# 1. Provenance + taint.
# --------------------------------------------------------------------------- #
def test_external_item_is_instruction_ineligible():
    item = _ext("some tool output")
    assert item.is_external_origin is True
    assert item.instruction_eligible is False
    assert item.label is TaintLabel.UNTRUSTED


def test_internal_item_is_eligible():
    item = _op("operator goal")
    assert item.is_external_origin is False
    assert item.instruction_eligible is True
    assert item.label is TaintLabel.TRUSTED


def test_default_priority_orders_trusted_above_external():
    assert _op("a").priority > _ext("b").priority


# --------------------------------------------------------------------------- #
# 2. Deterministic + content-addressed.
# --------------------------------------------------------------------------- #
def test_assembly_is_deterministic():
    items = [_op("a"), _ext("b"), _op("c")]
    a = assemble(list(items))
    b = assemble(list(items))
    assert a.context_ref == b.context_ref
    assert [i.content_hash for i in a.items] == [i.content_hash for i in b.items]


def test_dedup_by_content_hash():
    bundle = assemble([_op("same"), _op("same"), _op("other")])
    hashes = [i.content_hash for i in bundle.items]
    assert len(hashes) == len(set(hashes)) == 2


def test_context_ref_changes_with_content():
    r1 = assemble([_op("a")]).context_ref
    r2 = assemble([_op("b")]).context_ref
    assert r1 != r2


def test_empty_input_is_stable_empty_bundle():
    bundle = assemble([])
    assert bundle.items == ()
    assert bundle.total_est_tokens == 0
    assert bundle.context_ref  # a stable ref, not a crash


# --------------------------------------------------------------------------- #
# 3. Budget-aware, no silent loss.
# --------------------------------------------------------------------------- #
def test_budget_drops_lowest_priority_and_records_it():
    # High-priority operator item + low-priority external item; tiny budget.
    high = _op("A" * 40, prio=100)   # ~10 tokens
    low = _ext("B" * 40, prio=10)    # ~10 tokens
    bundle = assemble([high, low], max_tokens=10)
    kept = {i.content_hash for i in bundle.items}
    assert high.content_hash in kept
    assert low.content_hash not in kept
    # The drop is recorded, never silent.
    assert len(bundle.dropped) == 1
    assert bundle.dropped[0].content_hash == low.content_hash
    assert bundle.dropped[0].reason == "over_token_budget"
    assert bundle.total_est_tokens <= 10


def test_no_budget_keeps_everything():
    bundle = assemble([_op("a"), _ext("b")])
    assert len(bundle.items) == 2
    assert bundle.dropped == ()


# --------------------------------------------------------------------------- #
# 4. Rendering doctrine.
# --------------------------------------------------------------------------- #
def test_render_fences_external_as_data():
    bundle = assemble([_op("OPERATOR GOAL"), _ext("scraped junk")])
    prompt = bundle.to_prompt()
    assert "OPERATOR GOAL" in prompt
    assert "EXTERNAL DATA" in prompt          # external is fenced
    assert "scraped junk" in prompt
    # The operator content is not inside a data fence.
    assert prompt.index("OPERATOR GOAL") < prompt.index("EXTERNAL DATA")


def test_render_no_fence_when_all_internal():
    bundle = assemble([_op("a"), _op("b")])
    assert "EXTERNAL DATA" not in bundle.to_prompt()


# --------------------------------------------------------------------------- #
# 5. Flag default OFF.
# --------------------------------------------------------------------------- #
def test_flag_defaults_off(monkeypatch):
    monkeypatch.delenv("AUREL_CONTEXTLOOM", raising=False)
    assert flag_enabled() is False
    monkeypatch.setenv("AUREL_CONTEXTLOOM", "1")
    assert flag_enabled() is True
