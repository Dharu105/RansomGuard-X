"""Synthetic defense option models. No real security commands."""
from __future__ import annotations

from typing import Any, TypedDict


class DefenseOption(TypedDict, total=False):
    action: str
    title: str
    description: str
    risk_before: float
    risk_after: float
    risk_reduction: float
    blast_radius_before: int
    blast_radius_after: int
    operational_disruption: str
    reversibility: str
    confidence: float
    defense_score: float
    reason: str
    protects: list[str]
    simulated: bool
    real_network_action: bool


class DefenseRecommendation(TypedDict, total=False):
    recommended_action: str | None
    recommended_reason: str
    recommended_score: float
    options: list[DefenseOption]
    forks: list[dict[str, Any]]
    current_node: str | None
    predicted_target: str | None
    simulated: bool


EMPTY_DEFENSE: DefenseRecommendation = {
    "recommended_action": None,
    "recommended_reason": "",
    "recommended_score": 0,
    "options": [],
    "forks": [],
    "current_node": None,
    "predicted_target": None,
    "simulated": True,
    "real_network_action": False,
    "label": "SIMULATED defense projection — no real containment",
}
