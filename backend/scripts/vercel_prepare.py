"""Copy repo-level config/ml into the backend service directory during Vercel builds."""
from __future__ import annotations

import os
import shutil
from pathlib import Path


def main() -> None:
    if not os.getenv("VERCEL"):
        return
    backend = Path(__file__).resolve().parents[1]
    repo = Path(__file__).resolve().parents[2]
    for name in ("config", "ml"):
        src = repo / name
        dst = backend / name
        if src.exists():
            shutil.copytree(src, dst, dirs_exist_ok=True)


if __name__ == "__main__":
    main()
