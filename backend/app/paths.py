"""Locate the repo root that contains config/ (local) or the Vercel service root after copy."""
from __future__ import annotations

from pathlib import Path


def repo_root() -> Path:
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "config" / "assets.yaml").exists():
            return parent
    return here.parents[2]
