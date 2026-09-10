"""Isolation Forest anomaly model with deterministic fallback."""
from __future__ import annotations

from typing import Any

from app.detection.features import FEATURE_NAMES, extract_features, feature_vector
from app.paths import repo_root

ROOT = repo_root()
MODEL_PATH = ROOT / "ml" / "models" / "isolation_forest.joblib"

FALLBACK_WEIGHTS = {
    "file_modifications": 18,
    "file_renames": 14,
    "process_count": 8,
    "process_creation_rate": 6,
    "network_connections": 12,
    "credential_events": 14,
    "privilege_changes": 14,
}


def _fallback_score(vector: list[float]) -> float:
    raw = sum(v * FALLBACK_WEIGHTS[name] for v, name in zip(vector, FEATURE_NAMES))
    return round(max(0.0, min(100.0, raw * 1.15)), 1)


def score_events(events: list[dict[str, Any]]) -> dict[str, Any]:
    vector = feature_vector(events)
    features = extract_features(events)
    score = _fallback_score(vector)
    model_used = False
    try:
        if MODEL_PATH.exists():
            import joblib
            import numpy as np

            model = joblib.load(MODEL_PATH)
            arr = np.array(vector, dtype=float).reshape(1, -1)
            if getattr(model, "n_features_in_", len(vector)) != len(vector):
                raise ValueError("feature dimension mismatch")
            decision = float(model.decision_function(arr)[0])
            score = round(float(max(0.0, min(100.0, (-decision + 0.15) * 160))), 1)
            model_used = True
    except Exception:
        model_used = False
        score = _fallback_score(vector)

    return {
        "anomaly_score": score,
        "model_used": model_used,
        "fallback": not model_used,
        "features": features,
        "label": "SIMULATED anomaly score — not real-world ML accuracy",
    }


def train_and_persist() -> dict[str, Any]:
    import joblib
    import numpy as np
    from sklearn.ensemble import IsolationForest

    rng = np.random.default_rng(42)
    n = len(FEATURE_NAMES)
    benign = rng.poisson(0.12, size=(220, n)).astype(float)
    attack = rng.poisson(1.4, size=(50, n)).astype(float)
    attack[:, 0:2] += 1.8
    attack[:, 5:7] += 1.2
    X = np.vstack([benign, attack])
    model = IsolationForest(n_estimators=80, contamination=0.18, random_state=42)
    model.fit(X)
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    return {"trained": True, "samples": int(X.shape[0]), "features": FEATURE_NAMES, "path": str(MODEL_PATH)}
