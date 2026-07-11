"""``aurel corp`` — the Corp / Business Plane read-only surface (F7).

Read-only projections over the current runtime's trace: the Evidence Vault search
(`vault`) and the Output-Passport receipt-bundle export (`export`). Neither mutates
the trace; `export` optionally writes the bundle JSON to a file.
"""
from __future__ import annotations

import argparse
import json


def cmd_corp_vault(args: argparse.Namespace) -> int:
    """``aurel corp vault [--mandate|--client|--kind|--run] [--json]`` — search evidence."""
    from .. import build_runtime
    from ..corp import EvidenceVaultQuery, corp_registry_from_trace

    rt = build_runtime()
    query = EvidenceVaultQuery(rt.runtime.trace, corp_registry_from_trace(rt.runtime.trace))
    result = query.search(
        mandate_id=getattr(args, "mandate", "") or "",
        client_id=getattr(args, "client", "") or "",
        kind=getattr(args, "kind", "") or "",
        run_id=getattr(args, "run", "") or "",
    )
    if getattr(args, "json", False):
        print(json.dumps(result, indent=2))
    else:
        print(f"Evidence Vault: {result['count']} record(s)"
              + (" (truncated)" if result["truncated"] else ""))
        for ev in result["events"]:
            print(f"  {ev.get('kind', ''):26} mandate={ev.get('mandate_id', '') or '-':16} "
                  f"{ev['content_ref']}")
    return 0


def cmd_corp_export(args: argparse.Namespace) -> int:
    """``aurel corp export [--job J | --run R | --mandate M] [--out PATH]`` — Output Passport."""
    from .. import build_runtime
    from ..corp import EvidenceVaultQuery, corp_registry_from_trace

    rt = build_runtime()
    query = EvidenceVaultQuery(rt.runtime.trace, corp_registry_from_trace(rt.runtime.trace))
    bundle = query.export_receipt_bundle(
        job_id=getattr(args, "job", "") or "",
        run_id=getattr(args, "run", "") or "",
        mandate_id=getattr(args, "mandate", "") or "",
    )
    out = getattr(args, "out", "") or ""
    if out:
        with open(out, "w", encoding="utf-8") as fh:
            json.dump(bundle, fh, indent=2)
        print(f"wrote receipt bundle → {out} "
              f"(events={bundle.get('event_count', 0)}, verified={bundle.get('verified')})")
        return 0
    print(json.dumps(bundle, indent=2))
    return 0


def cmd_corp_seal(args: argparse.Namespace) -> int:
    """``aurel corp seal [--json]`` — the derived F7 exit seal (read-only)."""
    from ..f7_seal import build_f7_exit_seal

    seal = build_f7_exit_seal()
    if getattr(args, "json", False):
        print(json.dumps(seal.to_dict(), indent=2))
        return 0 if seal.sealed else 1
    print(f"F7 Corp / Business Plane exit seal: {seal.status.value}")
    for item in seal.items:
        mark = "OK " if item.status.value == "PASSED" else "XX "
        print(f"  {mark}{item.slice_id:6} {item.title}")
        if item.status.value != "PASSED":
            print(f"        module_present={item.module_present} "
                  f"report_present={item.report_present}")
    print("  flipped from F6 (now live):")
    for seam, owner in seal.flipped_from_f6:
        print(f"    + {seam} [{owner}]")
    print("  UNAVAILABLE (declared, deferred):")
    for u in seal.unavailable:
        print(f"    - {u.surface_id}: {u.reason} [{u.future_owner}]")
    return 0 if seal.sealed else 1


def cmd_corp_status(args: argparse.Namespace) -> int:
    """``aurel corp status`` — project the F7 north-star run from the trace (read-only)."""
    from .. import build_runtime
    from ..f7_projection import F7RunProjection

    print(json.dumps(F7RunProjection(build_runtime()).to_dict(), indent=2))
    return 0
