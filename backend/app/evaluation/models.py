"""Synthetic evaluation models. Prototype measurement only."""
from __future__ import annotations

from typing import Any

NOT_ENOUGH_DATA = "NOT_ENOUGH_DATA"

LIMITATIONS = [
    "synthetic scenarios",
    "deterministic scoring",
    "limited scenario diversity",
    "no production telemetry",
    "no real ransomware execution",
    "no real network activity",
    "no real-world accuracy claim",
    "in-process learning/playbook memory where applicable",
    "EVENT-BASED TIMING (not wall-clock seconds)",
]

# Ground truth for binary ransomware-likely detection. Not a production label set.
SCENARIO_TRUTH: dict[str, dict[str, Any]] = {
    "SCN-001": {
        "name": "Progressive ransomware attack",
        "expected_ransomware_likely": True,
        "expected_class": "RANSOMWARE_LIKELY",
        "role": "progressive_attack",
    },
    "SCN-002": {
        "name": "Early detection / low impact",
        "expected_ransomware_likely": False,
        "expected_class": "SUSPICIOUS",
        "role": "early_low_impact",
    },
    "SCN-003": {
        "name": "Credential-first attack",
        "expected_ransomware_likely": True,
        "expected_class": "RANSOMWARE_LIKELY",
        "role": "credential_first",
    },
    "SCN-004": {
        "name": "Lateral movement attack",
        "expected_ransomware_likely": True,
        "expected_class": "RANSOMWARE_LIKELY",
        "role": "lateral_movement",
    },
    "SCN-005": {
        "name": "High adaptation / alternate path",
        "expected_ransomware_likely": True,
        "expected_class": "RANSOMWARE_LIKELY",
        "role": "high_adaptation",
    },
    "SCN-006": {
        "name": "Benign suspicious activity / false-positive scenario",
        "expected_ransomware_likely": False,
        "expected_class": "SUSPICIOUS",
        "role": "false_positive",
    },
}

EVAL_SCENARIO_IDS = ["SCN-001", "SCN-002", "SCN-003", "SCN-004", "SCN-005", "SCN-006"]
