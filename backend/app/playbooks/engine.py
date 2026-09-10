"""YAML playbook loading, proposal, and versioning."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from sqlalchemy.orm import Session

from app.models import Playbook, PlaybookVersion

ROOT = Path(__file__).resolve().parents[3]
PLAYBOOK_PATH = ROOT / "config" / "playbooks.yaml"


def load_yaml() -> str:
    return PLAYBOOK_PATH.read_text(encoding="utf-8") if PLAYBOOK_PATH.exists() else ""


def seed_playbooks(db: Session) -> None:
    if db.query(Playbook).count() > 0:
        return
    data = yaml.safe_load(load_yaml()) or {}
    for pb in data.get("playbooks", []):
        body = yaml.safe_dump(pb, sort_keys=False)
        row = Playbook(
            id=pb["id"],
            name=pb["name"],
            yaml_body=body,
            status="active",
            current_version=1,
        )
        db.add(row)
        db.add(
            PlaybookVersion(
                playbook_id=pb["id"],
                version=1,
                yaml_body=body,
                change_reason="Initial seeded playbook",
                status="accepted",
            )
        )
    db.commit()


def list_playbooks(db: Session) -> list[dict[str, Any]]:
    rows = db.query(Playbook).all()
    out = []
    for r in rows:
        versions = (
            db.query(PlaybookVersion)
            .filter(PlaybookVersion.playbook_id == r.id)
            .order_by(PlaybookVersion.version.desc())
            .all()
        )
        out.append(
            {
                "id": r.id,
                "name": r.name,
                "yaml_body": r.yaml_body,
                "status": r.status,
                "current_version": r.current_version,
                "versions": [
                    {
                        "id": v.id,
                        "version": v.version,
                        "status": v.status,
                        "change_reason": v.change_reason,
                        "yaml_body": v.yaml_body,
                    }
                    for v in versions
                ],
            }
        )
    return out


def propose_update(db: Session, incident_id: str, regret: float, action: str) -> dict[str, Any]:
    pb = db.query(Playbook).filter(Playbook.id == "PB-RANSOM-LM-001").first()
    if not pb:
        return {"proposed": False, "reason": "Playbook missing"}
    new_version = pb.current_version + 1
    current = yaml.safe_load(pb.yaml_body) or {}
    current["version"] = new_version
    current["learning"] = {
        "store_outcome": True,
        "propose_update": True,
        "last_incident": incident_id,
        "suggested_default_action": action,
        "note": "Proposed from simulated incident learning. Not auto-applied.",
    }
    if regret > 20:
        actions = current.get("actions", [])
        if "isolate_endpoint" not in actions:
            actions.append("isolate_endpoint")
        current["actions"] = actions
        current["trigger"]["risk_score"] = ">70"
    body = yaml.safe_dump(current, sort_keys=False)
    row = PlaybookVersion(
        playbook_id=pb.id,
        version=new_version,
        yaml_body=body,
        change_reason=f"Learning from {incident_id}: prefer {action}; regret={regret}",
        status="proposed",
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return {
        "proposed": True,
        "proposal_id": row.id,
        "playbook_id": pb.id,
        "version": new_version,
        "yaml_body": body,
        "change_reason": row.change_reason,
        "status": "proposed",
        "note": "Human review required. Production controls are not silently changed.",
    }


def resolve_proposal(db: Session, proposal_id: int, decision: str, reviewer: str) -> dict[str, Any]:
    row = db.query(PlaybookVersion).filter(PlaybookVersion.id == proposal_id).first()
    if not row:
        return {"ok": False, "error": "Proposal not found"}
    if decision == "ACCEPT":
        row.status = "accepted"
        pb = db.query(Playbook).filter(Playbook.id == row.playbook_id).first()
        if pb:
            pb.yaml_body = row.yaml_body
            pb.current_version = row.version
    elif decision == "REJECT":
        row.status = "rejected"
    else:
        row.status = "review"
    db.commit()
    return {
        "ok": True,
        "proposal_id": row.id,
        "status": row.status,
        "reviewer": reviewer,
        "version": row.version,
    }
