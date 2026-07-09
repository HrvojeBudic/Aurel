"""F4.1 seal — budget-aware context compression.

  1. compress_item — deterministic head+tail truncation, elision marker present,
     kept ≤ budget, provenance preserved, record links the original hash.
  2. assemble(compress=True) — an overflowing high-priority item is compressed to
     fit (not dropped) and the compression is recorded; a budget too small to
     compress into drops the item (recorded in dropped, not compressed).
  3. compress=False is byte-identical to F4.0 drop-only.
  4. A compressed external item stays instruction-ineligible + DATA-fenced.
"""
from __future__ import annotations

from agentic_runtime.context_loom import (
    MIN_COMPRESS_TOKENS,
    CompressionMethod,
    assemble,
    compress_item,
    make_context_item,
)
from agentic_runtime.context_loom.compression import _MARKER  # type: ignore
from agentic_runtime.external_ingress import SourceKind


def _op(text, prio=None):
    return make_context_item(text, SourceKind.OPERATOR, "op", prio)


def _ext(text, prio=None):
    return make_context_item(text, SourceKind.MCP_TOOL, "mcp", prio)


BIG = "HEAD_" + ("x" * 4000) + "_TAIL"  # ~1000 est tokens


# --------------------------------------------------------------------------- #
# 1. compress_item.
# --------------------------------------------------------------------------- #
def test_compress_truncates_head_tail_within_budget():
    item = _op(BIG)
    new, rec = compress_item(item, 20)
    assert new.est_tokens <= 20
    assert rec.method is CompressionMethod.TRUNCATE_HEAD_TAIL
    assert _MARKER.strip() in new.content
    assert new.content.startswith("HEAD_")     # head preserved
    assert new.content.endswith("_TAIL")       # tail preserved
    assert rec.elided_tokens > 0
    assert rec.original_hash == item.content_hash


def test_compress_is_deterministic():
    a = compress_item(_op(BIG), 20)[0]
    b = compress_item(_op(BIG), 20)[0]
    assert a.content == b.content
    assert a.content_hash == b.content_hash


def test_compress_preserves_provenance():
    item = _ext(BIG)
    new, _ = compress_item(item, 20)
    assert new.source_kind is item.source_kind
    assert new.origin_ref == item.origin_ref
    assert new.priority == item.priority
    assert new.label is item.label
    assert new.instruction_eligible is False   # still external
    assert new.content_hash != item.content_hash  # content changed


def test_compress_noop_when_already_fits():
    item = _op("small")
    new, rec = compress_item(item, 100)
    assert new is item
    assert rec.method is CompressionMethod.NONE
    assert rec.elided_tokens == 0


# --------------------------------------------------------------------------- #
# 2. assemble(compress=True).
# --------------------------------------------------------------------------- #
def test_assemble_compresses_overflowing_item_instead_of_dropping():
    bundle = assemble([_op(BIG, prio=100)], max_tokens=30, compress=True)
    assert len(bundle.items) == 1                 # kept, not dropped
    assert bundle.items[0].est_tokens <= 30
    assert bundle.total_est_tokens <= 30
    assert len(bundle.compressed) == 1
    assert bundle.dropped == ()


def test_assemble_drops_when_remaining_below_min():
    # Fill the budget with a high-priority item so the remainder is < MIN, then a
    # second overflowing item can't be compressed and is dropped.
    filler = _op("y" * (4 * 40), prio=100)        # ~40 tokens, fits budget 40
    big = _ext(BIG, prio=10)
    bundle = assemble([filler, big], max_tokens=40, compress=True)
    assert filler.content_hash in {i.content_hash for i in bundle.items}
    assert len(bundle.dropped) == 1               # big dropped (remaining < MIN)
    assert bundle.compressed == ()
    assert MIN_COMPRESS_TOKENS >= 1


# --------------------------------------------------------------------------- #
# 3. compress=False byte-identical to F4.0 drop-only.
# --------------------------------------------------------------------------- #
def test_compress_false_is_drop_only():
    items = [_op(BIG, prio=100), _ext("small", prio=10)]
    off = assemble(list(items), max_tokens=30, compress=False)
    # The big item overflows and is dropped; nothing compressed.
    assert off.compressed == ()
    assert any(d.content_hash == items[0].content_hash for d in off.dropped)


# --------------------------------------------------------------------------- #
# 4. Compressed external item stays data-only.
# --------------------------------------------------------------------------- #
def test_compressed_external_item_still_fenced():
    bundle = assemble([_ext(BIG, prio=100)], max_tokens=30, compress=True)
    assert bundle.items[0].instruction_eligible is False
    assert "EXTERNAL DATA" in bundle.to_prompt()
