"""Train Isolation Forest and Random Forest on synthetic data."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from app.detection.anomaly import train_and_persist  # noqa: E402
from app.prediction.engine import train_rf  # noqa: E402


if __name__ == "__main__":
    print(train_and_persist())
    print(train_rf())
