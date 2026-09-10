"""Deterministic attack-intent analysis. No LLM."""
from __future__ import annotations

from typing import Any


def infer_intent(events: list[dict[str, Any]]) -> dict[str, Any]:
    types = [e.get("event_type") for e in events]
    has_mass = "mass_file_modification" in types
    has_rename = "rapid_file_rename" in types
    has_cred = "credential_access" in types
    has_priv = "privilege_escalation" in types
    has_lat = "lateral_movement" in types
    has_bak = "backup_access_attempt" in types
    has_fs = "file_server_access" in types
    has_proc = "suspicious_process" in types

    intent = "No malicious progression indicated"
    current_intent = "NONE"
    confidence = 6.0
    reason = "No behavioral events observed."
    evidence: list[str] = []

    if has_proc and not (has_mass or has_cred):
        intent = "Suspicious execution on a lab endpoint"
        current_intent = "SUSPICIOUS_EXECUTION"
        confidence = 28.0
        reason = "A suspicious process was created without correlated file or credential activity."
        evidence = ["suspicious_process"]
    if has_mass and not has_rename:
        intent = "Possible staging or destructive file activity"
        current_intent = "FILE_IMPACT_STAGING"
        confidence = 48.0
        reason = "Mass file modification increases risk but is not sufficient alone for ransomware classification."
        evidence = [t for t in ("suspicious_process", "mass_file_modification") if t in types]
    if has_mass and has_rename:
        intent = "Potential ransomware progression"
        current_intent = "RANSOMWARE_PREPARATION"
        confidence = 64.0
        reason = "Rapid file modifications and renaming indicate possible encryption-like behavior."
        evidence = [t for t in ("mass_file_modification", "rapid_file_rename") if t in types]
    if has_mass and has_rename and has_cred:
        intent = "Potential ransomware progression"
        current_intent = "RANSOMWARE_PREPARATION"
        confidence = 76.0
        reason = "File-impact behavior plus credential access suggests preparation for wider compromise."
        evidence = [t for t in ("mass_file_modification", "rapid_file_rename", "credential_access") if t in types]
    if has_priv and has_lat and has_fs:
        intent = "Potential ransomware progression"
        current_intent = "PROPAGATION_TOWARD_FILE_SERVER"
        confidence = 86.0
        reason = "Privilege escalation and lateral movement reached the file server path."
        evidence = [t for t in ("privilege_escalation", "lateral_movement", "file_server_access") if t in types]
    if has_priv and has_lat and has_bak:
        intent = "Potential ransomware progression"
        current_intent = "PROPAGATION_RECOVERY_DISRUPTION"
        confidence = 92.0
        reason = "Backup access after lateral movement is consistent with recovery disruption."
        evidence = [t for t in ("privilege_escalation", "lateral_movement", "backup_access_attempt") if t in types]
    elif has_bak:
        intent = "Potential ransomware progression"
        current_intent = "PROPAGATION_RECOVERY_DISRUPTION"
        confidence = max(confidence, 90.0)
        reason = "Backup access attempt after earlier impact signals indicates likely recovery disruption."
        evidence = [t for t in types if t]

    lo = max(0.0, confidence - 4.5)
    hi = min(99.0, confidence + 4.5)
    return {
        "intent": intent,
        "current_intent": current_intent,
        "confidence": round(confidence, 1),
        "confidence_range": [round(lo, 1), round(hi, 1)],
        "reason": reason,
        "supporting_evidence": evidence,
        "simulated": True,
    }
