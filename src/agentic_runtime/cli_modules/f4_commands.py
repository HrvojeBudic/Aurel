"""``aurel f4 seal`` / ``aurel f4 loom`` — F4.4 read-only inspection.

``seal`` prints the derived F4 exit seal (SEALED only when every slice module +
report is present; deferred surfaces explicit as UNAVAILABLE). ``loom`` projects a
demo ContextLoom assembly (provenance mix, budget outcome, external-fenced render)
without executing anything. ``seal`` exits non-zero when the phase is not SEALED.
"""
from __future__ import annotations

import argparse
import json


def cmd_f4_seal(args: argparse.Namespace) -> int:
    from ..f4_seal import build_f4_exit_seal

    seal = build_f4_exit_seal(reports_dir=getattr(args, "reports_dir", "agent/reports"))
    if getattr(args, "json", False):
        print(json.dumps(seal.to_dict(), indent=2, sort_keys=True))
    else:
        d = seal.to_dict()
        print(f"F4 exit seal: {seal.status.value}  "
              f"({d['passed']} passed / {d['blocked']} blocked)")
        for item in seal.items:
            mark = "ok" if item.status.value == "PASSED" else "BLOCKED"
            print(f"  [{mark:7}] {item.slice_id}  {item.title}")
        print("  unavailable (explicit, not overclaimed):")
        for u in seal.unavailable:
            print(f"    - {u.surface_id}: {u.reason}  → {u.future_owner}")
    return 0 if seal.sealed else 2


def cmd_f4_loom(args: argparse.Namespace) -> int:
    from ..context_loom import assemble, make_context_item
    from ..external_ingress import SourceKind
    from ..f4_projection import project_context_bundle

    # A demo assembly: an operator goal + memory + an external (scraped) item,
    # budget-fit with compression so the external item is fenced and possibly cut.
    items = [
        make_context_item("Operator goal: summarize the repo.", SourceKind.OPERATOR, "op"),
        make_context_item("prior note: tests live under tests/", SourceKind.INTERNAL, "memory"),
        make_context_item("SCRAPED: " + ("lorem ipsum " * 40), SourceKind.SCRAPE, "scrape"),
    ]
    bundle = assemble(items, max_tokens=getattr(args, "max_tokens", 60), compress=True)
    out = {
        "projection": project_context_bundle(bundle),
        "rendered_prompt": bundle.to_prompt(),
    }
    print(json.dumps(out, indent=2, sort_keys=True))
    return 0
