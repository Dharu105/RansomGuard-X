"""Attack-graph node and edge schemas for the synthetic RMK lab."""
from __future__ import annotations

from typing import Any, TypedDict


class GraphNode(TypedDict, total=False):
    id: str
    name: str
    type: str
    criticality: str
    status: str
    compromised: bool
    privileged: bool
    risk: float
    first_seen: str | None
    last_seen: str | None
    observed_events: list[str]
    is_current: bool


class GraphEdge(TypedDict, total=False):
    id: str
    source: str
    target: str
    type: str
    observed: bool
    timestamp: str | None
    confidence: float


NODE_CATALOG: list[dict[str, Any]] = [
    {
        "id": "LAB-PC-21",
        "name": "LAB-PC-21",
        "type": "WORKSTATION",
        "criticality": "MEDIUM",
    },
    {
        "id": "student.kumar",
        "name": "Student Account",
        "type": "USER",
        "criticality": "HIGH",
    },
    {
        "id": "FAC-PC-07",
        "name": "FAC-PC-07",
        "type": "FACULTY_DEVICE",
        "criticality": "HIGH",
    },
    {
        "id": "FILE-SRV-01",
        "name": "FILE-SRV-01",
        "type": "FILE_SERVER",
        "criticality": "CRITICAL",
    },
    {
        "id": "BACKUP-SRV-01",
        "name": "BACKUP-SRV-01",
        "type": "BACKUP_SERVER",
        "criticality": "CRITICAL",
    },
]

EDGE_CATALOG: list[dict[str, Any]] = [
    {
        "source": "LAB-PC-21",
        "target": "student.kumar",
        "type": "AUTHENTICATION",
        "trigger": "credential_access",
    },
    {
        "source": "student.kumar",
        "target": "FAC-PC-07",
        "type": "LATERAL_MOVEMENT",
        "trigger": "lateral_movement",
    },
    {
        "source": "FAC-PC-07",
        "target": "FILE-SRV-01",
        "type": "DATA_ACCESS",
        "trigger": "file_server_access",
    },
    {
        "source": "FILE-SRV-01",
        "target": "BACKUP-SRV-01",
        "type": "BACKUP_ACCESS",
        "trigger": "backup_access_attempt",
    },
]

PATH_ORDER = ["LAB-PC-21", "student.kumar", "FAC-PC-07", "FILE-SRV-01", "BACKUP-SRV-01"]

CRIT_WEIGHT = {"MEDIUM": 1.0, "HIGH": 1.4, "CRITICAL": 1.8}
STATUS_WEIGHT = {
    "NORMAL": 0,
    "SUSPICIOUS": 18,
    "AT_RISK": 42,
    "COMPROMISED": 70,
    "PROTECTED": 8,
}

NODE_EVENT_MAP = {
    "LAB-PC-21": ["suspicious_process", "mass_file_modification", "rapid_file_rename", "privilege_escalation"],
    "student.kumar": ["credential_access", "privilege_escalation"],
    "FAC-PC-07": ["lateral_movement"],
    "FILE-SRV-01": ["file_server_access"],
    "BACKUP-SRV-01": ["backup_access_attempt"],
}
