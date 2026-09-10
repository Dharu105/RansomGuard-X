"""Seed fictional RMK College Cyber Defense Center demo data."""
from __future__ import annotations

import json
from datetime import datetime, timedelta

import yaml
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import (
    Asset,
    Credential,
    DefenseMemory,
    Incident,
    Playbook,
    SimulationScenario,
    User,
)
from app.playbooks.engine import seed_playbooks
from app.simulation.events import SCENARIOS

ROOT_ASSETS = None


def _load_assets() -> dict:
    from pathlib import Path

    path = Path(__file__).resolve().parents[2] / "config" / "assets.yaml"
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def seed_if_empty() -> None:
    db = SessionLocal()
    try:
        if db.query(Asset).count() == 0:
            _seed_assets(db)
        if db.query(SimulationScenario).count() == 0:
            _seed_scenarios(db)
        seed_playbooks(db)
        if db.query(Incident).count() == 0:
            _seed_history(db)
        db.commit()
    finally:
        db.close()


def _seed_assets(db: Session) -> None:
    cfg = _load_assets()
    for a in cfg.get("assets", []):
        db.add(
            Asset(
                id=a["id"],
                name=a["name"],
                type=a["type"],
                criticality=a["criticality"],
                owner=a["owner"],
                segment=a["segment"],
                os=a["os"],
            )
        )
    for u in cfg.get("users", []):
        db.add(User(id=u["id"], role=u["role"], privilege=u["privilege"]))
    for c in cfg.get("credentials", []):
        db.add(Credential(id=c["id"], user_id=c["user_id"], type=c["type"]))


def _seed_scenarios(db: Session) -> None:
    for sid, meta in SCENARIOS.items():
        db.add(
            SimulationScenario(
                id=sid,
                name=meta["name"],
                description=meta["description"],
                kind=meta["kind"],
            )
        )


def _seed_history(db: Session) -> None:
    now = datetime.utcnow()
    historic = [
        dict(
            id="INC-001",
            title="Credential compromise",
            attack_stage="CREDENTIAL_ACCESS",
            risk_score=46,
            ransomware_confidence=22,
            predicted_target="FAC-PC-07",
            prediction_confidence=61,
            recommended_action="REVOKE_CREDENTIALS",
            approval_status="approved",
            defense_regret=18,
            status="closed",
            affected=["LAB-PC-21"],
            outcome={"contained": True, "systems": 2},
            ts=now - timedelta(days=12),
        ),
        dict(
            id="INC-002",
            title="Lateral movement",
            attack_stage="LATERAL_MOVEMENT",
            risk_score=72,
            ransomware_confidence=58,
            predicted_target="FILE-SRV-01",
            prediction_confidence=81,
            recommended_action="ISOLATE_AND_REVOKE",
            approval_status="approved",
            defense_regret=11,
            status="closed",
            affected=["LAB-PC-21", "FAC-PC-07"],
            outcome={"contained": True, "systems": 2},
            ts=now - timedelta(days=5),
        ),
        dict(
            id="INC-003",
            title="Ransomware simulation",
            attack_stage="INHIBIT_RECOVERY",
            risk_score=91,
            ransomware_confidence=88,
            predicted_target="BACKUP-SRV-01",
            prediction_confidence=86,
            recommended_action="ISOLATE_AND_REVOKE",
            approval_status="approved",
            defense_regret=36,
            status="closed",
            affected=["LAB-PC-21", "FAC-PC-07", "FILE-SRV-01", "BACKUP-SRV-01"],
            outcome={"contained": False, "systems": 4},
            ts=now - timedelta(days=1),
        ),
    ]
    for h in historic:
        db.add(
            Incident(
                id=h["id"],
                timestamp=h["ts"],
                title=h["title"],
                risk_score=h["risk_score"],
                ransomware_confidence=h["ransomware_confidence"],
                attack_stage=h["attack_stage"],
                affected_assets=json.dumps(h["affected"]),
                predicted_target=h["predicted_target"],
                prediction_confidence=h["prediction_confidence"],
                recommended_action=h["recommended_action"],
                approval_status=h["approval_status"],
                actual_outcome=json.dumps(h["outcome"]),
                counterfactual_results=json.dumps(
                    [{"action": "ISOLATE_AND_REVOKE", "systems_affected": 1, "label": "SIMULATED"}]
                ),
                defense_regret=h["defense_regret"],
                intervention_time="10:03",
                status=h["status"],
                scenario_id="SCN-001",
            )
        )
        db.add(
            DefenseMemory(
                incident_id=h["id"],
                pattern=h["attack_stage"],
                defense_used=h["recommended_action"],
                outcome="contained" if h["outcome"]["contained"] else "missed",
                impact=json.dumps(h["outcome"]),
                decision_quality="good" if h["defense_regret"] < 20 else "fair",
                recommended_future="ISOLATE_AND_REVOKE",
            )
        )
