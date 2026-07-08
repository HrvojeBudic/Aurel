"""F2 seal — ``aurel secrets set/status`` CLI.

Proves: ``secrets set`` reads via getpass (no echo — stdin is never read raw),
stores through the SecretStore chain and prints backend + fingerprint only;
``secrets status`` prints masked rows (never a value), honest empty state, and
deterministic ``--json``; unknown provider fails closed; the subcommands are
wired into the main parser.
"""

from __future__ import annotations

import argparse
import json

import agentic_runtime.cli_modules.secrets_commands as sc


def _fail_if_prompted(prompt: str = "") -> str:
    raise AssertionError(
        "getpass was invoked without a test mock — a real stdin prompt would "
        "block the test process forever")


def _isolate(tmp_path, monkeypatch):
    """Route the store at a temp dir with no keyring and a clean env.

    Also arms a getpass FAILSAFE: any code path that reaches an unmocked stdin
    prompt fails instantly instead of blocking. Tests that legitimately exercise
    ``secrets set`` override the mock with a fixed value.
    """
    monkeypatch.setenv("AUREL_SECRETS_DIR", str(tmp_path / "secrets"))
    from agentic_runtime.secrets_store import DEFAULT_PROVIDER_KEY_ENVS
    for env_var in DEFAULT_PROVIDER_KEY_ENVS.values():
        monkeypatch.delenv(env_var, raising=False)
    # Force the no-keyring path so tests never touch the real OS store.
    from agentic_runtime import secrets_store
    monkeypatch.setattr(secrets_store._KeyringCli, "__init__",
                        lambda self: setattr(self, "_tool", None))
    # Never block on stdin: unmocked prompts fail fast.
    monkeypatch.setattr("getpass.getpass", _fail_if_prompted)


def test_secrets_set_no_echo_and_masked_output(tmp_path, monkeypatch, capsys):
    _isolate(tmp_path, monkeypatch)
    monkeypatch.setattr("getpass.getpass", lambda prompt="": "sk-typed-secretly")

    rc = sc.cmd_secrets_set(argparse.Namespace(provider="qwen"))
    out = capsys.readouterr().out

    assert rc == 0
    assert "stored qwen key in file-0600" in out
    assert "sk-typed-secretly" not in out                # value never echoed
    assert "fingerprint" in out


def test_secrets_status_masked_and_json(tmp_path, monkeypatch, capsys):
    _isolate(tmp_path, monkeypatch)
    monkeypatch.setattr("getpass.getpass", lambda prompt="": "sk-status-secret")
    sc.cmd_secrets_set(argparse.Namespace(provider="kimi"))
    capsys.readouterr()

    rc = sc.cmd_secrets_status(argparse.Namespace(json=True))
    out = capsys.readouterr().out
    assert rc == 0
    rows = {r["provider"]: r for r in json.loads(out)}
    assert rows["kimi"]["present"] is True
    assert rows["kimi"]["backend"] == "file-0600"
    assert len(rows["kimi"]["fingerprint"]) == 8
    assert rows["qwen"]["present"] is False               # honest empty state
    assert "sk-status-secret" not in out                  # never the value

    rc2 = sc.cmd_secrets_status(argparse.Namespace(json=False))
    table = capsys.readouterr().out
    assert rc2 == 0
    assert "kimi" in table and "sk-status-secret" not in table


def test_secrets_set_unknown_provider_fails_closed(tmp_path, monkeypatch, capsys):
    _isolate(tmp_path, monkeypatch)
    rc = sc.cmd_secrets_set(argparse.Namespace(provider="notaprovider"))
    out = capsys.readouterr().out
    assert rc == 1
    assert "unknown provider" in out


def test_secrets_cli_wired_into_main_parser(tmp_path, monkeypatch, capsys):
    _isolate(tmp_path, monkeypatch)
    import agentic_runtime.cli as cli
    rc = cli.main(["secrets", "status", "--json"])
    out = capsys.readouterr().out
    assert rc == 0
    assert isinstance(json.loads(out), list)
