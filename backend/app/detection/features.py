"""Behavioral feature extraction from synthetic security events."""
from __future__ import annotations

from typing import Any

FEATURE_NAMES = [
    "file_modifications",
    "file_renames",
    "process_count",
    "process_creation_rate",
    "network_connections",
    "credential_events",
    "privilege_changes",
]

NETWORK_TYPES = {"lateral_movement", "file_server_access", "backup_access_attempt", "suspicious_network"}


def extract_features(events: list[dict[str, Any]]) -> dict[str, float]:
    types = [e.get("event_type") for e in events]
    n = max(len(events), 1)
    mods = float(types.count("mass_file_modification"))
    renames = float(types.count("rapid_file_rename"))
    procs = float(types.count("suspicious_process"))
    creds = float(types.count("credential_access"))
    privs = float(types.count("privilege_escalation"))
    nets = float(sum(1 for t in types if t in NETWORK_TYPES))
    # Burst details from synthetic payloads when present
    for ev in events:
        details = ev.get("details") or {}
        if ev.get("event_type") == "mass_file_modification":
            mods += float(details.get("files_touched", 0)) / 200.0
        if ev.get("event_type") == "rapid_file_rename":
            renames += float(details.get("renames", 0)) / 120.0
    return {
        "file_modifications": round(mods, 3),
        "file_renames": round(renames, 3),
        "process_count": procs,
        "process_creation_rate": round(procs / n, 3),
        "network_connections": nets,
        "credential_events": creds,
        "privilege_changes": privs,
    }


def feature_vector(events: list[dict[str, Any]]) -> list[float]:
    feats = extract_features(events)
    return [float(feats[name]) for name in FEATURE_NAMES]
