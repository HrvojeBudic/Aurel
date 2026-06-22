"""Shared CLI helpers for agentic_runtime."""
from __future__ import annotations

import argparse
from pathlib import Path

from ..model_config import default_config_dir


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def config_dir(args: argparse.Namespace) -> Path:
    if getattr(args, "config_dir", None):
        return Path(args.config_dir)
    return default_config_dir()


def optional_cli_path(value: str) -> Path | None:
    return Path(value) if value else None
