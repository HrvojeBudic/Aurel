"""``aurel secrets`` — per-provider API-key management over the SecretStore (F2).

``secrets set <provider>`` reads the key WITHOUT echo (getpass) and stores it via
the honest backend chain (OS keyring when available, else file-0600). ``secrets
status`` prints per-provider presence + backend + a masked sha256 fingerprint —
never a value. All output passes through the SecretRedactor defensively.
"""
from __future__ import annotations

import argparse
import getpass
import json


def cmd_secrets_set(args: argparse.Namespace) -> int:
    from ..secrets import SecretRedactor
    from ..secrets_store import SecretStore, SecretStoreError

    store = SecretStore()
    try:
        store.env_var_for(args.provider)
    except SecretStoreError as e:
        print(f"secrets: {e}")
        return 1
    value = getpass.getpass(f"API key for {args.provider} (input hidden): ")
    try:
        backend = store.set(args.provider, value)
    except SecretStoreError as e:
        print(SecretRedactor().redact(f"secrets: {e}"))
        return 1
    rows = {r.provider: r for r in store.status()}
    fp = rows[args.provider].fingerprint
    print(f"stored {args.provider} key in {backend} (fingerprint {fp})")
    if backend == "file-0600":
        print("note: OS keyring unavailable — key is in a chmod-0600 file "
              "(honest plaintext, no fake crypto)")
    return 0


def cmd_secrets_status(args: argparse.Namespace) -> int:
    from ..secrets import SecretRedactor
    from ..secrets_store import SecretStore

    redactor = SecretRedactor()
    rows = [r.to_dict() for r in SecretStore().status()]
    # Defensive: the store already masks, but never trust a single layer.
    for row in rows:
        for key, val in row.items():
            if isinstance(val, str):
                row[key] = redactor.redact(val)
    if getattr(args, "json", False):
        print(json.dumps(rows, indent=2, sort_keys=True))
        return 0
    print("provider    present  backend     fingerprint  env_var")
    for row in rows:
        print(f"{row['provider']:<11} {str(row['present']).lower():<8} "
              f"{row['backend'] or '-':<11} {row['fingerprint'] or '-':<12} "
              f"{row['env_var']}")
    return 0
