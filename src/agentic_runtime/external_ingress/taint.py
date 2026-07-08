"""
taint.py — provenance labels for external content (F3.0 / D0 core).

The doctrine lives here as *type structure*, not policy code:

  - ``SourceKind`` is a closed-world enum. ``EXTERNAL_ORIGIN_KINDS`` is the
    frozen set of kinds that originate outside the trusted core.
  - ``TaintedContent`` is frozen. Its ``instruction_eligible`` is computed
    purely from ``source_kind`` — external origin ⇒ always ``False``. There is
    no constructor, no method, no flag that flips an external payload into an
    instruction. Consumers that build plans/instructions must refuse anything
    whose ``instruction_eligible`` is False.

Because eligibility is derived (not stored), it cannot be forged by handing the
constructor a crafted field. An injection *scan* result is deliberately NOT an
input to labelling: a clean scan cannot upgrade untrusted → trusted, and a dirty
scan cannot downgrade operator → untrusted. Provenance is the sole authority.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from enum import Enum


class SourceKind(str, Enum):
    """Where a piece of content came from. Closed-world."""

    # Trusted-internal origins (instruction-eligible where the caller allows).
    OPERATOR = "operator"            # the human operator
    MODEL_OUTPUT = "model_output"    # our own model, via PlanValidator
    INTERNAL = "internal"            # runtime-authored / trusted subsystem

    # External origins (NEVER instruction-eligible).
    MCP_TOOL = "mcp_tool"            # result from an external MCP server we call
    MCP_CLIENT = "mcp_client"        # payload from an external MCP client of ours
    A2A_MESSAGE = "a2a_message"      # message from another agent
    NETWORK_FETCH = "network_fetch"  # governed network pull
    SCRAPE = "scrape"                # scraped document
    EXTERNAL_EXECUTOR = "external_executor"  # e.g. a Claude Code session
    UNKNOWN = "unknown"              # unclassified ⇒ treated as external


# The frozen set of origins that are NOT trusted to carry instructions.
# UNKNOWN is included: unclassified provenance fails closed to external.
EXTERNAL_ORIGIN_KINDS: frozenset[SourceKind] = frozenset(
    {
        SourceKind.MCP_TOOL,
        SourceKind.MCP_CLIENT,
        SourceKind.A2A_MESSAGE,
        SourceKind.NETWORK_FETCH,
        SourceKind.SCRAPE,
        SourceKind.EXTERNAL_EXECUTOR,
        SourceKind.UNKNOWN,
    }
)

# Trusted-internal origins, for symmetry / explicitness.
TRUSTED_ORIGIN_KINDS: frozenset[SourceKind] = frozenset(
    {SourceKind.OPERATOR, SourceKind.MODEL_OUTPUT, SourceKind.INTERNAL}
)


class TaintLabel(str, Enum):
    """Severity-ordered provenance label. Derived from source_kind."""

    TRUSTED = "trusted"          # internal origin
    UNTRUSTED = "untrusted"      # external origin, admitted as data
    QUARANTINED = "quarantined"  # external origin held back entirely (fail closed)


def _label_for(source_kind: SourceKind) -> TaintLabel:
    """Provenance → label. External origins default to UNTRUSTED."""
    if source_kind in TRUSTED_ORIGIN_KINDS:
        return TaintLabel.TRUSTED
    return TaintLabel.UNTRUSTED


def _hash(content: str) -> str:
    """Deterministic content fingerprint (sha256 hex). No RNG, no ``hash()``."""
    return hashlib.sha256(content.encode("utf-8", errors="surrogatepass")).hexdigest()


@dataclass(frozen=True)
class TaintedContent:
    """External or internal content with an immutable provenance label.

    ``instruction_eligible`` is a *computed* property, never a stored field, so a
    crafted constructor call cannot claim eligibility it does not have.
    """

    content: str
    source_kind: SourceKind
    origin_ref: str            # provenance ref (trace id / run id / caller id)
    label: TaintLabel
    content_hash: str

    @property
    def is_external_origin(self) -> bool:
        return self.source_kind in EXTERNAL_ORIGIN_KINDS

    @property
    def instruction_eligible(self) -> bool:
        """Structural gate: external origin is NEVER instruction-eligible.

        Also fails closed on QUARANTINED regardless of origin. The only True
        case is a genuinely internal, non-quarantined origin.
        """
        if self.label is TaintLabel.QUARANTINED:
            return False
        return not self.is_external_origin

    def quarantined(self) -> "TaintedContent":
        """Return a QUARANTINED copy (held back entirely). Never widens trust."""
        if self.label is TaintLabel.QUARANTINED:
            return self
        return TaintedContent(
            content=self.content,
            source_kind=self.source_kind,
            origin_ref=self.origin_ref,
            label=TaintLabel.QUARANTINED,
            content_hash=self.content_hash,
        )

    def to_dict(self) -> dict:
        return {
            "source_kind": self.source_kind.value,
            "origin_ref": self.origin_ref,
            "label": self.label.value,
            "content_hash": self.content_hash,
            "is_external_origin": self.is_external_origin,
            "instruction_eligible": self.instruction_eligible,
        }


def make_tainted(
    content: str,
    source_kind: SourceKind,
    origin_ref: str,
) -> TaintedContent:
    """Construct a labelled payload. Label is derived from provenance alone.

    The caller cannot pass a label — it is computed, so there is no path to
    hand-forge TRUSTED onto external content.
    """
    return TaintedContent(
        content=content,
        source_kind=source_kind,
        origin_ref=origin_ref,
        label=_label_for(source_kind),
        content_hash=_hash(content),
    )
