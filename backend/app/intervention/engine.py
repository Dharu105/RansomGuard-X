"""Intervention window classification and impact by time."""
from __future__ import annotations

from typing import Any

from app.counterfactual.engine import run

TIMELINE = [
    {"index": 0, "time": "10:01", "event": "suspicious_process", "label": "SAFE"},
    {"index": 1, "time": "10:02", "event": "mass_file_modification", "label": "GOOD"},
    {"index": 2, "time": "10:02", "event": "rapid_file_rename", "label": "GOOD"},
    {"index": 3, "time": "10:03", "event": "credential_access", "label": "BEST"},
    {"index": 4, "time": "10:04", "event": "privilege_escalation", "label": "RISKY"},
    {"index": 5, "time": "10:05", "event": "lateral_movement", "label": "RISKY"},
    {"index": 6, "time": "10:06", "event": "file_server_access", "label": "TOO_LATE"},
    {"index": 7, "time": "10:07", "event": "backup_access_attempt", "label": "TOO_LATE"},
]


def classify(index: int) -> str:
    if index <= 0:
        return "SAFE"
    if index <= 2:
        return "GOOD"
    if index == 3:
        return "BEST"
    if index <= 5:
        return "RISKY"
    return "TOO_LATE"


def window(action: str = "ISOLATE_AND_REVOKE") -> dict[str, Any]:
    points = []
    for item in TIMELINE:
        impact = run(action, item["index"])
        points.append(
            {
                **item,
                "classification": classify(item["index"]),
                "impact": impact,
            }
        )
    last_safe = next((p for p in reversed(points) if p["classification"] in ("SAFE", "GOOD", "BEST")), points[0])
    return {
        "timeline": points,
        "last_safe_intervention": last_safe,
        "best_index": 3,
        "best_time": "10:03",
        "simulated": True,
    }


def impact_at(index: int, action: str = "ISOLATE_AND_REVOKE") -> dict[str, Any]:
    return {
        "index": index,
        "classification": classify(index),
        "time": TIMELINE[index]["time"] if 0 <= index < len(TIMELINE) else "n/a",
        "impact": run(action, index),
        "last_safe": "10:03",
        "simulated": True,
    }
