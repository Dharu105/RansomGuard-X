"""NetworkX attack graph driven only by observed synthetic events."""
from __future__ import annotations

from typing import Any

import networkx as nx

from app.attack_graph.models import (
    CRIT_WEIGHT,
    EDGE_CATALOG,
    NODE_CATALOG,
    NODE_EVENT_MAP,
    PATH_ORDER,
    STATUS_WEIGHT,
)


def _types(events: list[dict[str, Any]]) -> set[str]:
    return {e.get("event_type") for e in events if e.get("event_type")}


def _times_for(events: list[dict[str, Any]], event_types: list[str]) -> tuple[str | None, str | None]:
    stamps = [e.get("timestamp") for e in events if e.get("event_type") in event_types]
    if not stamps:
        return None, None
    return stamps[0], stamps[-1]


def _events_for(events: list[dict[str, Any]], event_types: list[str]) -> list[str]:
    seen: list[str] = []
    for e in events:
        t = e.get("event_type")
        if t in event_types and t not in seen:
            seen.append(t)
    return seen


def _node_status(nid: str, types: set[str], contained: set[str]) -> tuple[str, bool, bool]:
    if nid in contained:
        return "PROTECTED", False, False
    if nid == "LAB-PC-21":
        if "rapid_file_rename" in types or "credential_access" in types:
            return "COMPROMISED", True, "privilege_escalation" in types
        if "mass_file_modification" in types or "suspicious_process" in types:
            return "SUSPICIOUS", False, False
        return "NORMAL", False, False
    if nid == "student.kumar":
        if "credential_access" in types:
            return "COMPROMISED", True, "privilege_escalation" in types
        return "NORMAL", False, False
    if nid == "FAC-PC-07":
        if "lateral_movement" in types:
            return "COMPROMISED", True, False
        return "NORMAL", False, False
    if nid == "FILE-SRV-01":
        if "file_server_access" in types:
            return "AT_RISK", False, False
        return "NORMAL", False, False
    if nid == "BACKUP-SRV-01":
        if "backup_access_attempt" in types:
            return "AT_RISK", False, False
        return "NORMAL", False, False
    return "NORMAL", False, False


def _node_risk(status: str, criticality: str, extra: float) -> float:
    base = STATUS_WEIGHT[status] * CRIT_WEIGHT.get(criticality, 1.0)
    return round(min(99.0, base + extra), 1)


def _observed_path(types: set[str]) -> list[str]:
    if not types:
        return []
    path = ["LAB-PC-21"]
    if "credential_access" in types:
        path.append("student.kumar")
    if "lateral_movement" in types:
        path.append("FAC-PC-07")
    if "file_server_access" in types:
        path.append("FILE-SRV-01")
    if "backup_access_attempt" in types:
        path.append("BACKUP-SRV-01")
    return path


def _graph_risk(nodes: list[dict[str, Any]], types: set[str], stage: str) -> float:
    score = 0.0
    for n in nodes:
        if n["status"] == "COMPROMISED":
            score += 14 * CRIT_WEIGHT.get(n["criticality"], 1.0)
        elif n["status"] == "AT_RISK":
            score += 9 * CRIT_WEIGHT.get(n["criticality"], 1.0)
        elif n["status"] == "SUSPICIOUS":
            score += 4
    if "lateral_movement" in types:
        score += 8
    if "file_server_access" in types:
        score += 10
    if "backup_access_attempt" in types:
        score += 12
    stage_bonus = {
        "NORMAL": 0,
        "INITIAL_ACCESS": 4,
        "EXECUTION": 8,
        "CREDENTIAL_ACCESS": 12,
        "PRIVILEGE_ESCALATION": 16,
        "LATERAL_MOVEMENT": 20,
        "DATA_ACCESS": 24,
        "RANSOMWARE_IMPACT": 28,
    }
    score += stage_bonus.get(stage, 0)
    return round(min(99.0, score), 1)


def build(
    events: list[dict[str, Any]],
    detection: dict[str, Any] | None = None,
    containment: dict[str, Any] | None = None,
) -> dict[str, Any]:
    types = _types(events)
    detection = detection or {}
    contained = set((containment or {}).get("isolated_assets", [])) | set(
        (containment or {}).get("revoked_credentials", [])
    ) | set((containment or {}).get("protected_assets", []))
    contained = {i for i in contained if i in {n["id"] for n in NODE_CATALOG}}
    g = nx.DiGraph()
    nodes: list[dict[str, Any]] = []
    path = _observed_path(types)
    current = path[-1] if path else None
    extra_lab = 8.0 if "mass_file_modification" in types else 0.0
    if "rapid_file_rename" in types:
        extra_lab += 10.0

    for spec in NODE_CATALOG:
        nid = spec["id"]
        status, compromised, privileged = _node_status(nid, types, contained)
        related = NODE_EVENT_MAP.get(nid, [])
        first_seen, last_seen = _times_for(events, related)
        observed = _events_for(events, related)
        extra = extra_lab if nid == "LAB-PC-21" else 0.0
        node = {
            **spec,
            "status": status,
            "compromised": compromised,
            "privileged": privileged,
            "risk": _node_risk(status, spec["criticality"], extra),
            "first_seen": first_seen,
            "last_seen": last_seen,
            "observed_events": observed,
            "is_current": nid == current,
        }
        g.add_node(nid, **node)
        nodes.append(node)

    edges: list[dict[str, Any]] = []
    for spec in EDGE_CATALOG:
        trigger = spec["trigger"]
        observed = trigger in types
        ts = next((e.get("timestamp") for e in events if e.get("event_type") == trigger), None)
        blocked_ids = set((containment or {}).get("blocked_paths") or [])
        edge = {
            "id": f"{spec['source']}->{spec['target']}",
            "source": spec["source"],
            "target": spec["target"],
            "type": spec["type"],
            "observed": observed,
            "timestamp": ts if observed else None,
            "confidence": 88.0 if observed else 12.0,
            "blocked": f"{spec['source']}->{spec['target']}" in blocked_ids,
        }
        g.add_edge(spec["source"], spec["target"], **edge)
        edges.append(edge)

    stage = detection.get("attack_stage") or ("NORMAL" if not events else "INITIAL_ACCESS")
    payload = {
        "nodes": nodes,
        "edges": edges,
        "attack_path": path,
        "current_node": current,
        "current_position": current or "",
        "current_stage": stage,
        "graph_risk": _graph_risk(nodes, types, stage),
        "path_order": PATH_ORDER,
        "nx_nodes": g.number_of_nodes(),
        "nx_edges": g.number_of_edges(),
        "simulated": True,
        "label": "SIMULATED attack graph",
    }
    return payload
