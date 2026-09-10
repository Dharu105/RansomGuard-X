"""Behavioral detection, risk scoring, attack stage, and evidence."""
from __future__ import annotations

from typing import Any

import yaml

from app.detection.models import score_events
from app.paths import repo_root

ROOT = repo_root()
RULES_PATH = ROOT / "config" / "detection_rules.yaml"

# Incremental weights so the score rises without jumping to 100.
WEIGHTS = {
    "suspicious_process": 22,
    "mass_file_modification": 24,
    "rapid_file_rename": 18,
    "credential_access": 10,
    "privilege_escalation": 14,
    "lateral_movement": 5,
    "file_server_access": 4,
    "backup_access_attempt": 3,
    "suspicious_network": 4,
}

MITRE_MAP = {
    "suspicious_process": {"id": "T1059", "name": "Command and Scripting Interpreter"},
    "mass_file_modification": {"id": "T1486", "name": "Data Encrypted for Impact"},
    "rapid_file_rename": {"id": "T1486", "name": "Data Encrypted for Impact"},
    "credential_access": {"id": "T1078", "name": "Valid Accounts"},
    "privilege_escalation": {"id": "T1068", "name": "Exploitation for Privilege Escalation"},
    "lateral_movement": {"id": "T1021", "name": "Remote Services"},
    "file_server_access": {"id": "T1021", "name": "Remote Services"},
    "backup_access_attempt": {"id": "T1486", "name": "Data Encrypted for Impact"},
    "suspicious_network": {"id": "T1071", "name": "Application Layer Protocol"},
}

STAGE_BY_EVENT = {
    "suspicious_process": "INITIAL_ACCESS",
    "mass_file_modification": "EXECUTION",
    "rapid_file_rename": "EXECUTION",
    "credential_access": "CREDENTIAL_ACCESS",
    "privilege_escalation": "PRIVILEGE_ESCALATION",
    "lateral_movement": "LATERAL_MOVEMENT",
    "file_server_access": "DATA_ACCESS",
    "backup_access_attempt": "RANSOMWARE_IMPACT",
    "suspicious_network": "INITIAL_ACCESS",
}

EVIDENCE_ORDER = [
    "suspicious_process",
    "mass_file_modification",
    "rapid_file_rename",
    "credential_access",
    "privilege_escalation",
    "lateral_movement",
    "file_server_access",
    "backup_access_attempt",
]


def load_rules() -> dict[str, Any]:
    if RULES_PATH.exists():
        with RULES_PATH.open("r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {"rules": [], "weights": WEIGHTS}


def band(score: float) -> str:
    if score <= 30:
        return "LOW"
    if score <= 60:
        return "MEDIUM"
    if score <= 80:
        return "HIGH"
    return "CRITICAL"


def classify(score: float, types: set[str]) -> str:
    if not types:
        return "NORMAL"
    ransomware_core = {"mass_file_modification", "rapid_file_rename"}
    if ransomware_core <= types and (
        "credential_access" in types
        or "privilege_escalation" in types
        or "backup_access_attempt" in types
        or "lateral_movement" in types
    ):
        return "RANSOMWARE_LIKELY"
    if score >= 81:
        return "RANSOMWARE_LIKELY" if "mass_file_modification" in types else "HIGH_RISK"
    if score >= 55 or "rapid_file_rename" in types:
        return "HIGH_RISK"
    return "SUSPICIOUS"


def risk_from_events(events: list[dict[str, Any]]) -> dict[str, Any]:
    raw = 0
    fired = []
    for ev in events:
        t = ev.get("event_type", "")
        w = WEIGHTS.get(t, 0)
        if w:
            raw += w
            fired.append({"event_id": ev.get("id"), "type": t, "weight": w, "rule": f"RGX-{t}"})
    rule_score = min(99, raw)
    anomaly = score_events(events)
    blended = min(99.0, round(0.94 * rule_score + 0.06 * anomaly["anomaly_score"], 1))
    return {
        "risk_score": blended,
        "rule_score": rule_score,
        "anomaly": anomaly,
        "band": band(blended),
        "fired_rules": fired,
        "simulated": True,
    }


def stage_from_events(events: list[dict[str, Any]]) -> str:
    if not events:
        return "NORMAL"
    last = events[-1].get("event_type", "")
    return STAGE_BY_EVENT.get(last, "NORMAL")


def evidence_from_events(events: list[dict[str, Any]]) -> list[str]:
    seen = []
    types = [e.get("event_type") for e in events]
    for name in EVIDENCE_ORDER:
        if name in types and name not in seen:
            seen.append(name)
    return seen


def mitre_coverage(events: list[dict[str, Any]]) -> dict[str, Any]:
    seen = {}
    for ev in events:
        m = MITRE_MAP.get(ev.get("event_type", ""))
        if m:
            seen[m["id"]] = m
    catalog = [
        {"id": "T1059", "name": "Command and Scripting Interpreter"},
        {"id": "T1078", "name": "Valid Accounts"},
        {"id": "T1068", "name": "Exploitation for Privilege Escalation"},
        {"id": "T1021", "name": "Remote Services"},
        {"id": "T1486", "name": "Data Encrypted for Impact"},
    ]
    return {
        "observed": list(seen.values()),
        "catalog": catalog,
        "coverage": round(100 * len(seen) / len(catalog), 1) if catalog else 0,
    }


def detect(events: list[dict[str, Any]]) -> dict[str, Any]:
    from app.intent.engine import infer_intent

    risk = risk_from_events(events)
    types = {e.get("event_type") for e in events if e.get("event_type")}
    stage = stage_from_events(events)
    intent = infer_intent(events)
    classification = classify(risk["risk_score"], types)
    ransomware = 0.0
    if "mass_file_modification" in types:
        ransomware += 22
    if "rapid_file_rename" in types:
        ransomware += 16
    if "credential_access" in types:
        ransomware += 12
    if "privilege_escalation" in types:
        ransomware += 12
    if "lateral_movement" in types:
        ransomware += 14
    if "backup_access_attempt" in types:
        ransomware += 16
    ransomware = min(96.0, ransomware)
    evidence = evidence_from_events(events)
    public = {
        "classification": classification,
        "risk_score": risk["risk_score"],
        "risk_level": risk["band"],
        "attack_stage": stage,
        "intent": intent.get("intent") or intent.get("current_intent"),
        "confidence": intent.get("confidence", 0),
        "evidence": evidence,
        "reason": intent.get("reason", ""),
        "label": "SIMULATED / EXPERIMENTAL",
        "simulated": True,
    }
    return {
        **risk,
        "attack_stage": stage,
        "ransomware_confidence": round(ransomware, 1),
        "mitre": mitre_coverage(events),
        "classification": classification,
        "evidence": evidence,
        "public": public,
    }
