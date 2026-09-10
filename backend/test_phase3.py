"""Phase 3 attack-graph tests against a running server."""
from __future__ import annotations

import json
import urllib.request

BASE = "http://127.0.0.1:8000"


def call(method: str, path: str, body=None):
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(
        BASE + path,
        data=data,
        method=method,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=20) as res:
        return json.loads(res.read().decode())


def graph():
    return call("GET", "/api/attack-graph")


def node(g, nid):
    return next(n for n in g["nodes"] if n["id"] == nid)


def edge(g, src, dst):
    return next(e for e in g["edges"] if e["source"] == src and e["target"] == dst)


def main() -> None:
    call("POST", "/api/simulation/reset", {})
    g = graph()
    print("RESET", g["attack_path"], g["current_node"], g["graph_risk"])
    assert g["attack_path"] == []
    assert g["current_node"] is None
    assert node(g, "FAC-PC-07")["status"] == "NORMAL"
    assert edge(g, "student.kumar", "FAC-PC-07")["observed"] is False

    call("POST", "/api/simulation/start", {"scenario_id": "SCN-001"})
    prev_risk = -1
    expect = [
        ("suspicious_process", "LAB-PC-21", ["LAB-PC-21"]),
        ("mass_file_modification", "LAB-PC-21", ["LAB-PC-21"]),
        ("rapid_file_rename", "LAB-PC-21", ["LAB-PC-21"]),
        ("credential_access", "student.kumar", ["LAB-PC-21", "student.kumar"]),
        ("privilege_escalation", "student.kumar", ["LAB-PC-21", "student.kumar"]),
        ("lateral_movement", "FAC-PC-07", ["LAB-PC-21", "student.kumar", "FAC-PC-07"]),
        ("file_server_access", "FILE-SRV-01", ["LAB-PC-21", "student.kumar", "FAC-PC-07", "FILE-SRV-01"]),
        ("backup_access_attempt", "BACKUP-SRV-01", ["LAB-PC-21", "student.kumar", "FAC-PC-07", "FILE-SRV-01", "BACKUP-SRV-01"]),
    ]
    for ev, current, path in expect:
        call("POST", "/api/simulation/next-event", {})
        g = graph()
        print("STEP", ev, g["current_node"], g["attack_path"], g["graph_risk"], node(g, current)["status"])
        assert g["current_node"] == current
        assert g["attack_path"] == path
        assert g["graph_risk"] >= prev_risk
        prev_risk = g["graph_risk"]
        if ev == "suspicious_process":
            assert node(g, "LAB-PC-21")["status"] == "SUSPICIOUS"
            assert node(g, "FILE-SRV-01")["status"] == "NORMAL"
            assert edge(g, "FAC-PC-07", "FILE-SRV-01")["observed"] is False
        if ev == "credential_access":
            assert node(g, "student.kumar")["compromised"] is True
            assert edge(g, "LAB-PC-21", "student.kumar")["observed"] is True
        if ev == "lateral_movement":
            assert node(g, "FAC-PC-07")["status"] == "COMPROMISED"
            assert edge(g, "student.kumar", "FAC-PC-07")["observed"] is True
            assert node(g, "BACKUP-SRV-01")["status"] == "NORMAL"
        if ev == "file_server_access":
            assert node(g, "FILE-SRV-01")["status"] == "AT_RISK"
            assert edge(g, "FAC-PC-07", "FILE-SRV-01")["observed"] is True
        if ev == "backup_access_attempt":
            assert node(g, "BACKUP-SRV-01")["status"] == "AT_RISK"
            assert edge(g, "FILE-SRV-01", "BACKUP-SRV-01")["observed"] is True

    rst = call("POST", "/api/simulation/reset", {})["state"]
    g = graph()
    assert rst["attack_path"] == []
    assert g["attack_path"] == []
    assert node(g, "LAB-PC-21")["status"] == "NORMAL"
    print("PHASE3_PASS")


if __name__ == "__main__":
    main()
