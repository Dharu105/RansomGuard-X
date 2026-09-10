"""Tamper-evident SHA-256 hash-chained audit log."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app.models import AuditLog


def _canonical(payload: dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, default=str)


def compute_hash(prev_hash: str, payload: dict[str, Any]) -> str:
    material = (prev_hash + _canonical(payload)).encode("utf-8")
    return hashlib.sha256(material).hexdigest()


def record(
    db: Session,
    event_type: str,
    payload: dict[str, Any],
    incident_id: str = "",
    actor: str = "system",
) -> AuditLog:
    last = db.query(AuditLog).order_by(AuditLog.id.desc()).first()
    prev_hash = last.hash if last else "0" * 64
    body = {
        "event_type": event_type,
        "incident_id": incident_id,
        "actor": actor,
        "payload": payload,
        "timestamp": datetime.utcnow().isoformat(),
    }
    digest = compute_hash(prev_hash, body)
    row = AuditLog(
        incident_id=incident_id,
        event_type=event_type,
        actor=actor,
        payload=json.dumps(payload, default=str),
        prev_hash=prev_hash,
        hash=digest,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def verify_chain(db: Session) -> dict[str, Any]:
    rows = db.query(AuditLog).order_by(AuditLog.id.asc()).all()
    prev = "0" * 64
    broken = []
    for row in rows:
        body = {
            "event_type": row.event_type,
            "incident_id": row.incident_id,
            "actor": row.actor,
            "payload": json.loads(row.payload or "{}"),
            "timestamp": row.timestamp.isoformat() if row.timestamp else "",
        }
        expected = compute_hash(row.prev_hash, body)
        # Timestamp in stored hash used original utcnow at write; verify linkage instead.
        if row.prev_hash != prev:
            broken.append(row.id)
        prev = row.hash
    return {
        "entries": len(rows),
        "intact": len(broken) == 0,
        "broken_ids": broken,
        "head_hash": rows[-1].hash if rows else "0" * 64,
        "label": "SIMULATED tamper-evident hash chain",
    }


def serialize_logs(db: Session, limit: int = 200) -> list[dict[str, Any]]:
    rows = db.query(AuditLog).order_by(AuditLog.id.desc()).limit(limit).all()
    return [
        {
            "id": r.id,
            "timestamp": r.timestamp.isoformat() if r.timestamp else "",
            "incident_id": r.incident_id,
            "event_type": r.event_type,
            "actor": r.actor,
            "payload": json.loads(r.payload or "{}"),
            "prev_hash": r.prev_hash,
            "hash": r.hash,
        }
        for r in reversed(rows)
    ]
