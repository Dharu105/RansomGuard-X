"""NetworkX attack graph for the fictional RMK lab topology."""
from __future__ import annotations

from typing import Any

import networkx as nx

CRITICALITY_SCORE = {"Low": 20, "Medium": 45, "High": 75, "Critical": 95}

BASE_NODES = [
    {"id": "LAB-PC-21", "type": "Endpoint", "criticality": "Medium", "label": "LAB-PC-21"},
    {"id": "LAB-PC-22", "type": "Endpoint", "criticality": "Medium", "label": "LAB-PC-22"},
    {"id": "FAC-PC-07", "type": "Endpoint", "criticality": "Medium", "label": "FAC-PC-07"},
    {"id": "ADMIN-PC-03", "type": "Endpoint", "criticality": "High", "label": "ADMIN-PC-03"},
    {"id": "FILE-SRV-01", "type": "Server", "criticality": "High", "label": "FILE-SRV-01"},
    {"id": "ERP-SRV-01", "type": "Server", "criticality": "Critical", "label": "ERP-SRV-01"},
    {"id": "LMS-SRV-01", "type": "Server", "criticality": "Critical", "label": "LMS-SRV-01"},
    {"id": "BACKUP-SRV-01", "type": "Backup", "criticality": "Critical", "label": "BACKUP-SRV-01"},
    {"id": "student.kumar", "type": "User", "criticality": "Medium", "label": "student.kumar"},
    {"id": "faculty.meena", "type": "User", "criticality": "Medium", "label": "faculty.meena"},
    {"id": "svc.backup", "type": "User", "criticality": "High", "label": "svc.backup"},
    {"id": "CRED-STU-21", "type": "Credential", "criticality": "Medium", "label": "CRED-STU-21"},
    {"id": "LAB-VLAN", "type": "Network Segment", "criticality": "Medium", "label": "LAB-VLAN"},
    {"id": "FACULTY-VLAN", "type": "Network Segment", "criticality": "Medium", "label": "FACULTY-VLAN"},
    {"id": "SERVER-VLAN", "type": "Network Segment", "criticality": "High", "label": "SERVER-VLAN"},
    {"id": "BACKUP-VLAN", "type": "Network Segment", "criticality": "Critical", "label": "BACKUP-VLAN"},
]

BASE_EDGES = [
    ("LAB-PC-21", "LAB-VLAN", "CONNECTED_TO"),
    ("LAB-PC-22", "LAB-VLAN", "CONNECTED_TO"),
    ("FAC-PC-07", "FACULTY-VLAN", "CONNECTED_TO"),
    ("ADMIN-PC-03", "LAB-VLAN", "CONNECTED_TO"),
    ("FILE-SRV-01", "SERVER-VLAN", "CONNECTED_TO"),
    ("ERP-SRV-01", "SERVER-VLAN", "CONNECTED_TO"),
    ("LMS-SRV-01", "SERVER-VLAN", "CONNECTED_TO"),
    ("BACKUP-SRV-01", "BACKUP-VLAN", "CONNECTED_TO"),
    ("LAB-VLAN", "FACULTY-VLAN", "CONNECTED_TO"),
    ("FACULTY-VLAN", "SERVER-VLAN", "CONNECTED_TO"),
    ("SERVER-VLAN", "BACKUP-VLAN", "CONNECTED_TO"),
    ("student.kumar", "LAB-PC-21", "AUTHENTICATED_TO"),
    ("student.kumar", "CRED-STU-21", "AUTHENTICATED_TO"),
    ("faculty.meena", "FAC-PC-07", "AUTHENTICATED_TO"),
    ("LAB-PC-21", "FAC-PC-07", "CAN_ACCESS"),
    ("FAC-PC-07", "FILE-SRV-01", "CAN_ACCESS"),
    ("FILE-SRV-01", "BACKUP-SRV-01", "CAN_ACCESS"),
    ("FAC-PC-07", "ERP-SRV-01", "CAN_ACCESS"),
    ("ADMIN-PC-03", "LMS-SRV-01", "CAN_ACCESS"),
    ("svc.backup", "BACKUP-SRV-01", "CAN_ACCESS"),
    ("svc.backup", "FILE-SRV-01", "CAN_ACCESS"),
]


def build_graph() -> nx.DiGraph:
    g = nx.DiGraph()
    for n in BASE_NODES:
        g.add_node(n["id"], **n)
    for src, dst, rel in BASE_EDGES:
        g.add_edge(src, dst, relation=rel)
    return g


def _position_from_events(events: list[dict[str, Any]], containment: dict[str, Any] | None) -> str:
    if containment and containment.get("contained"):
        return containment.get("attacker_position", "LAB-PC-21")
    types = [e.get("event_type") for e in events]
    if "backup_access_attempt" in types:
        return "BACKUP-SRV-01"
    if "file_server_access" in types:
        return "FILE-SRV-01"
    if "lateral_movement" in types:
        return "FAC-PC-07"
    if events:
        return "LAB-PC-21"
    return ""


def snapshot(
    events: list[dict[str, Any]],
    risk_score: float,
    predictions: list[dict[str, Any]],
    containment: dict[str, Any] | None = None,
    blocked: list[str] | None = None,
) -> dict[str, Any]:
    g = build_graph()
    current = _position_from_events(events, containment)
    predicted = predictions[0]["predicted_target"] if predictions else ""
    blocked = blocked or []
    contained_assets = set((containment or {}).get("isolated_assets", []))
    revoked = set((containment or {}).get("revoked_credentials", []))

    compromised: set[str] = set()
    types = [e.get("event_type") for e in events]
    if events:
        compromised.add("LAB-PC-21")
        compromised.add("student.kumar")
        compromised.add("CRED-STU-21")
    if "lateral_movement" in types and "LAB-PC-21" not in contained_assets:
        compromised.add("FAC-PC-07")
    if "file_server_access" in types and "FAC-PC-07" in compromised:
        compromised.add("FILE-SRV-01")
    if "backup_access_attempt" in types and "FILE-SRV-01" in compromised:
        compromised.add("BACKUP-SRV-01")

    blast = []
    if current and current in g:
        for n in nx.descendants(g, current):
            if n not in compromised:
                blast.append(n)

    nodes = []
    for nid, data in g.nodes(data=True):
        state = "healthy"
        p_comp = 0.05
        node_risk = 8.0
        if nid in compromised:
            state = "compromised"
            p_comp = 0.92
            node_risk = min(100, risk_score)
        elif nid == predicted:
            state = "predicted"
            p_comp = 0.74
            node_risk = 70
        elif nid in blast:
            state = "exposed"
            p_comp = 0.41
            node_risk = 48
        if nid in contained_assets:
            state = "isolated"
            p_comp = 0.12
        if nid in revoked:
            state = "revoked"
            p_comp = 0.08
        nodes.append(
            {
                "id": nid,
                "asset_id": nid,
                "asset_type": data.get("type"),
                "label": data.get("label", nid),
                "criticality": data.get("criticality"),
                "risk_score": node_risk,
                "current_state": state,
                "compromise_probability": p_comp,
                "is_current": nid == current,
                "is_predicted": nid == predicted,
                "is_critical": data.get("criticality") in ("High", "Critical"),
                "in_blast_radius": nid in blast,
            }
        )

    edges = []
    for src, dst, data in g.edges(data=True):
        rel = data.get("relation", "CONNECTED_TO")
        kind = rel
        if src in compromised and dst in compromised:
            kind = "LATERAL_MOVEMENT"
        if dst == predicted and src in compromised:
            kind = "TARGETED"
        blocked_edge = f"{src}->{dst}" in blocked or (src in contained_assets)
        edges.append(
            {
                "id": f"{src}->{dst}",
                "source": src,
                "target": dst,
                "relation": rel,
                "kind": kind,
                "blocked": blocked_edge,
            }
        )

    critical_exposed = [
        n["id"]
        for n in nodes
        if n["is_critical"] and n["current_state"] in ("compromised", "exposed", "predicted")
    ]
    return {
        "nodes": nodes,
        "edges": edges,
        "current_position": current,
        "predicted_next": predicted,
        "compromised": sorted(compromised),
        "blast_radius": {
            "current_affected": sorted(compromised),
            "potentially_affected": blast,
            "critical_assets_exposed": critical_exposed,
            "backup_exposure": "BACKUP-SRV-01" in blast or "BACKUP-SRV-01" in compromised,
            "label": "SIMULATED graph propagation",
        },
        "simulated": True,
    }
