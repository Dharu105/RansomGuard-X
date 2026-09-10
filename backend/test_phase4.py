"""Phase 4 next-target prediction tests against a running server."""
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


def pred():
    return call("GET", "/api/predictions")


def graph():
    return call("GET", "/api/attack-graph")


def det():
    return call("GET", "/api/detection/current")


def node_status(nid: str) -> str:
    g = graph()
    return next(n["status"] for n in g["nodes"] if n["id"] == nid)


def main() -> None:
    call("POST", "/api/simulation/reset", {})
    p = pred()
    print("RESET", p["predicted_target"], p["predicted_action"], p["confidence"], p["alternatives"])
    assert p["predicted_target"] is None
    assert p["predicted_action"] is None
    assert p["confidence"] == 0
    assert p["alternatives"] == []

    call("POST", "/api/simulation/start", {"scenario_id": "SCN-001"})
    p = pred()
    assert p["predicted_target"] is None

    expect = {
        "suspicious_process": ("LAB-PC-21", "MASS_FILE_MODIFICATION"),
        "mass_file_modification": ("LAB-PC-21", "RAPID_FILE_RENAME"),
        "rapid_file_rename": ("student.kumar", "CREDENTIAL_ACCESS"),
        "credential_access": ("student.kumar", "PRIVILEGE_ESCALATION"),
        "privilege_escalation": ("FAC-PC-07", "LATERAL_MOVEMENT"),
        "lateral_movement": ("FILE-SRV-01", "FILE_SERVER_ACCESS"),
        "file_server_access": ("BACKUP-SRV-01", "BACKUP_ACCESS"),
        "backup_access_attempt": ("BACKUP-SRV-01", "RANSOMWARE_IMPACT"),
    }
    for ev, (target, action) in expect.items():
        call("POST", "/api/simulation/next-event", {})
        p = pred()
        g = graph()
        d = det()
        again = pred()
        print("STEP", ev, p["predicted_target"], p["predicted_action"], p["confidence"], p["current_node"], p["current_stage"])
        assert p["predicted_target"] == again["predicted_target"]
        assert p["predicted_action"] == again["predicted_action"]
        assert p["predicted_target"] == target
        assert p["predicted_action"] == action
        assert 0 <= p["confidence"] <= 100
        assert p["predicted_target"] is not None
        alts = p["alternatives"]
        if len(alts) >= 2:
            scores = [a["confidence"] for a in alts]
            assert scores == sorted(scores, reverse=True)
        assert p["current_node"] == g["current_node"]
        assert p["current_stage"] == d["attack_stage"]
        if p["predicted_target"] != g["current_node"]:
            assert node_status(p["predicted_target"]) != "COMPROMISED"
        last_ev = ev.replace("_attempt", "") if False else ev
        joined = " ".join(p["evidence"]).lower()
        assert last_ev.replace("_", " ") in joined or ev in joined or "observed" in joined

    rst = call("POST", "/api/simulation/reset", {})["state"]
    p = pred()
    assert rst.get("prediction", {}).get("predicted_target") is None
    assert p["predicted_target"] is None
    assert p["confidence"] == 0
    assert p["alternatives"] == []
    print("PHASE4_PASS")


if __name__ == "__main__":
    main()
