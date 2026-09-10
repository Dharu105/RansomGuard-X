"""SQLAlchemy models for RansomGuard-X."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Asset(Base):
    __tablename__ = "assets"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(128))
    type: Mapped[str] = mapped_column(String(64))
    criticality: Mapped[str] = mapped_column(String(32))
    owner: Mapped[str] = mapped_column(String(64))
    segment: Mapped[str] = mapped_column(String(64))
    os: Mapped[str] = mapped_column(String(64))
    current_state: Mapped[str] = mapped_column(String(64), default="healthy")
    risk_score: Mapped[float] = mapped_column(Float, default=0.0)


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    role: Mapped[str] = mapped_column(String(64))
    privilege: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(32), default="active")


class Credential(Base):
    __tablename__ = "credentials"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(64))
    type: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(32), default="valid")


class SecurityEvent(Base):
    __tablename__ = "security_events"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    incident_id: Mapped[str] = mapped_column(String(64), index=True)
    timestamp: Mapped[str] = mapped_column(String(32))
    event_type: Mapped[str] = mapped_column(String(64))
    asset_id: Mapped[str] = mapped_column(String(64))
    payload: Mapped[str] = mapped_column(Text, default="{}")
    mitre: Mapped[str] = mapped_column(String(32), default="")
    simulated: Mapped[int] = mapped_column(Integer, default=1)


class Incident(Base):
    __tablename__ = "incidents"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    risk_score: Mapped[float] = mapped_column(Float, default=0.0)
    ransomware_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    attack_stage: Mapped[str] = mapped_column(String(64), default="NORMAL")
    affected_assets: Mapped[str] = mapped_column(Text, default="[]")
    predicted_target: Mapped[str] = mapped_column(String(64), default="")
    prediction_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    recommended_action: Mapped[str] = mapped_column(String(64), default="NO_ACTION")
    approval_status: Mapped[str] = mapped_column(String(32), default="pending")
    actual_outcome: Mapped[str] = mapped_column(Text, default="{}")
    counterfactual_results: Mapped[str] = mapped_column(Text, default="[]")
    defense_regret: Mapped[float] = mapped_column(Float, default=0.0)
    intervention_time: Mapped[str] = mapped_column(String(32), default="")
    status: Mapped[str] = mapped_column(String(32), default="open")
    title: Mapped[str] = mapped_column(String(128), default="")
    scenario_id: Mapped[str] = mapped_column(String(64), default="SCN-001")


class AttackStage(Base):
    __tablename__ = "attack_stages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    incident_id: Mapped[str] = mapped_column(String(64), index=True)
    stage: Mapped[str] = mapped_column(String(64))
    entered_at: Mapped[str] = mapped_column(String(32))


class AttackGraphNode(Base):
    __tablename__ = "attack_graph_nodes"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    incident_id: Mapped[str] = mapped_column(String(64), index=True)
    asset_id: Mapped[str] = mapped_column(String(64))
    asset_type: Mapped[str] = mapped_column(String(64))
    criticality: Mapped[str] = mapped_column(String(32))
    risk_score: Mapped[float] = mapped_column(Float, default=0.0)
    current_state: Mapped[str] = mapped_column(String(64), default="healthy")
    compromise_probability: Mapped[float] = mapped_column(Float, default=0.0)


class Prediction(Base):
    __tablename__ = "predictions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    incident_id: Mapped[str] = mapped_column(String(64), index=True)
    predicted_target: Mapped[str] = mapped_column(String(64))
    confidence: Mapped[float] = mapped_column(Float)
    lead_time: Mapped[str] = mapped_column(String(32))
    reasons: Mapped[str] = mapped_column(Text, default="[]")
    actual_target: Mapped[str] = mapped_column(String(64), default="")
    correct: Mapped[int] = mapped_column(Integer, default=-1)


class DefenseAction(Base):
    __tablename__ = "defense_actions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    incident_id: Mapped[str] = mapped_column(String(64), index=True)
    action: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(32))
    approver: Mapped[str] = mapped_column(String(64), default="")
    reason: Mapped[str] = mapped_column(Text, default="")
    simulated: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class SimulationScenario(Base):
    __tablename__ = "simulation_scenarios"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(128))
    description: Mapped[str] = mapped_column(Text, default="")
    kind: Mapped[str] = mapped_column(String(32), default="attack")


class SimulationResult(Base):
    __tablename__ = "simulation_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    scenario_id: Mapped[str] = mapped_column(String(64))
    incident_id: Mapped[str] = mapped_column(String(64))
    payload: Mapped[str] = mapped_column(Text, default="{}")


class Decision(Base):
    __tablename__ = "decisions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    incident_id: Mapped[str] = mapped_column(String(64), index=True)
    action: Mapped[str] = mapped_column(String(64))
    decision: Mapped[str] = mapped_column(String(32))
    approver: Mapped[str] = mapped_column(String(64))
    reason: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    incident_id: Mapped[str] = mapped_column(String(64), default="")
    event_type: Mapped[str] = mapped_column(String(64))
    actor: Mapped[str] = mapped_column(String(64), default="system")
    payload: Mapped[str] = mapped_column(Text, default="{}")
    prev_hash: Mapped[str] = mapped_column(String(64), default="")
    hash: Mapped[str] = mapped_column(String(64), default="")


class DefenseMemory(Base):
    __tablename__ = "defense_memory"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    incident_id: Mapped[str] = mapped_column(String(64))
    pattern: Mapped[str] = mapped_column(Text)
    defense_used: Mapped[str] = mapped_column(String(64))
    outcome: Mapped[str] = mapped_column(String(64))
    impact: Mapped[str] = mapped_column(Text, default="{}")
    decision_quality: Mapped[str] = mapped_column(String(32))
    recommended_future: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Playbook(Base):
    __tablename__ = "playbooks"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(128))
    yaml_body: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), default="active")
    current_version: Mapped[int] = mapped_column(Integer, default=1)


class PlaybookVersion(Base):
    __tablename__ = "playbook_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    playbook_id: Mapped[str] = mapped_column(String(64), index=True)
    version: Mapped[int] = mapped_column(Integer)
    yaml_body: Mapped[str] = mapped_column(Text)
    change_reason: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(32), default="proposed")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
