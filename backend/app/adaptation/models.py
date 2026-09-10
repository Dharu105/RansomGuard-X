"""Synthetic adaptive-attacker models. Simulation labels only."""
from __future__ import annotations

from typing import Any, TypedDict

LEVELS: list[tuple[str, int]] = [
    ("LOW", 30),
    ("MEDIUM", 50),
    ("HIGH", 70),
    ("VERY_HIGH", 90),
]


class AdaptationScenario(TypedDict, total=False):
    adaptation_level: str
    adaptation_score: int
    projected_risk: float
    blast_radius: int
    alternate_target: str | None
    outcome: str
    reason: str
    simulated: bool


EMPTY_ADAPTATION: dict[str, Any] = {
    "defense_action": None,
    "original_target": None,
    "protected_target": None,
    "robustness_score": 0,
    "robustness_class": "UNCERTAIN",
    "scenarios": [],
    "alternate_targets": [],
    "comparisons": [],
    "summary": "",
    "simulated": True,
    "label": "SIMULATED adaptation — not a real attacker",
}
