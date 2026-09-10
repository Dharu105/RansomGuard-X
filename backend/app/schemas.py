"""Pydantic schemas for RansomGuard-X APIs."""
from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class DefenseApproveRequest(BaseModel):
    action: str
    decision: str = "APPROVE"
    approver: str = "analyst.demo"
    approved_by: Optional[str] = None
    reason: str = "Approved for simulated containment"
    modified_action: Optional[str] = None


class DefenseReviewRequest(BaseModel):
    action: Optional[str] = None


class DefenseRejectRequest(BaseModel):
    action: str
    rejected_by: str = "Security Analyst"
    reason: str = "Operational disruption too high"


class CounterfactualRequest(BaseModel):
    action: str = "ISOLATE_AND_REVOKE"
    intervention_index: int = 3


class PlaybookApproveRequest(BaseModel):
    proposal_id: int
    decision: str = "ACCEPT"
    reviewer: str = "analyst.demo"


class PlaybookChangeGovernanceRequest(BaseModel):
    actor: str = "Security Analyst"
    reason: str = ""


class InvestigateRequest(BaseModel):
    question: str
    incident_id: Optional[str] = None


class SimulationStartRequest(BaseModel):
    scenario_id: str = "SCN-001"


class EvaluationRunRequest(BaseModel):
    scenario_id: Optional[str] = None


class RobustnessRequest(BaseModel):
    action: Optional[str] = None
    rates: list[int] = Field(default_factory=lambda: [30, 50, 70, 90])


class DemoControlRequest(BaseModel):
    command: str = "START"


class ReplayRequest(BaseModel):
    command: str = "PLAY"
    speed: float = 1.0
    index: Optional[int] = None


class StateEnvelope(BaseModel):
    ok: bool = True
    simulated: bool = True
    state: dict[str, Any]
