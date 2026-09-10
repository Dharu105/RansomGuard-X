"""Incident memory models for prediction outcome learning. Synthetic only."""
from __future__ import annotations

from typing import Any

EVENT_TO_TARGET = {
    "suspicious_process": "LAB-PC-21",
    "mass_file_modification": "LAB-PC-21",
    "rapid_file_rename": "LAB-PC-21",
    "credential_access": "student.kumar",
    "privilege_escalation": "student.kumar",
    "lateral_movement": "FAC-PC-07",
    "file_server_access": "FILE-SRV-01",
    "backup_access_attempt": "BACKUP-SRV-01",
}

EVENT_TO_ACTION = {
    "suspicious_process": "SUSPICIOUS_PROCESS",
    "mass_file_modification": "MASS_FILE_MODIFICATION",
    "rapid_file_rename": "RAPID_FILE_RENAME",
    "credential_access": "CREDENTIAL_ACCESS",
    "privilege_escalation": "PRIVILEGE_ESCALATION",
    "lateral_movement": "LATERAL_MOVEMENT",
    "file_server_access": "FILE_SERVER_ACCESS",
    "backup_access_attempt": "BACKUP_ACCESS",
}

EMPTY_SUMMARY = {
    "total_predictions": 0,
    "resolved_predictions": 0,
    "correct_predictions": 0,
    "partial_predictions": 0,
    "incorrect_predictions": 0,
    "target_accuracy": 0,
    "action_accuracy": 0,
    "overall_accuracy": 0,
    "recent_outcomes": [],
    "memory_adjustments": [],
    "label": "SIMULATION / EXPERIMENTAL",
}
