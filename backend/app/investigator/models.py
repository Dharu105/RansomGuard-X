"""Structured investigation result. Explanation only — not an action controller."""
from __future__ import annotations

from typing import Any

STORY_LINES = {
    "suspicious_process": "Suspicious process detected on {asset}",
    "mass_file_modification": "Mass file modification observed on {asset}",
    "rapid_file_rename": "Rapid file renaming observed on {asset}",
    "credential_access": "Credential access detected on {asset}",
    "privilege_escalation": "Privilege escalation detected on {asset}",
    "lateral_movement": "Lateral movement reached {asset}",
    "file_server_access": "File server access reached {asset}",
    "backup_access_attempt": "Backup access attempt observed on {asset}",
}

EMPTY: dict[str, Any] = {
    "incident_summary": "No synthetic events have been observed. The environment is quiet.",
    "attack_story": [],
    "current_risk": {
        "risk_score": 0,
        "risk_classification": "LOW",
        "attack_stage": "NORMAL",
        "current_node": None,
        "criticality": None,
        "blast_radius": 0,
        "explanation": "No observed activity. Risk is not elevated.",
        "label": "SIMULATED / EXPERIMENTAL",
    },
    "current_stage": "NORMAL",
    "observed_assets": [],
    "observed_events": [],
    "key_evidence": [],
    "prediction_explanation": {
        "predicted_target": None,
        "predicted_action": None,
        "label": "PREDICTION — NOT OBSERVED REALITY",
        "explanation": "No prediction is available because no synthetic events have been observed.",
        "evidence": [],
        "alternatives": [],
        "confidence": 0,
    },
    "defense_explanation": {
        "recommended_action": None,
        "explanation": "No defense is recommended because no synthetic incident is in progress.",
        "label": "SIMULATED defense projection — not executed",
        "executed": False,
        "real_network_action": False,
        "evidence": [],
        "alternatives": [],
    },
    "adaptation_explanation": {
        "available": False,
        "label": "SIMULATED ADAPTATION",
        "explanation": "No simulated adaptation results yet.",
        "evidence": [],
    },
    "learning_explanation": {
        "label": "SIMULATION / EXPERIMENTAL",
        "explanation": "No previous comparable synthetic incidents are stored yet.",
        "evidence": [],
        "history": [],
    },
    "playbook_explanation": {
        "label": "EVIDENCE-BACKED PROPOSAL REQUIRING HUMAN APPROVAL.",
        "explanation": "No playbook proposal is active.",
        "current_version": None,
        "proposed_version": None,
        "status": None,
        "evidence": [],
    },
    "uncertainty": [],
    "recommended_investigation_questions": [
        "Is there any synthetic telemetry to review yet?",
    ],
    "confidence": 0,
    "simulated": True,
    "real_network_action": False,
    "controls_containment": False,
    "source_of_truth": "deterministic_backend",
    "label": "SIMULATED / EXPERIMENTAL",
}
