"""Phase 6 human approval and simulated containment tests."""
from __future__ import annotations

import json
import urllib.error
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


def node(nid: str) -> dict:
    g = call("GET", "/api/attack-graph")
    return next(n for n in g["nodes"] if n["id"] == nid)


def status():
    return call("GET", "/api/defense/status")


def advance(n: int) -> None:
    for _ in range(n):
        call("POST", "/api/simulation/next-event", {})


def main() -> None:
    call("POST", "/api/simulation/reset", {})
    st = status()
    print("RESET", st["approval_status"], st["containment_status"], st["pending_approval"])
    assert st["approval_status"] == "NONE"
    assert st["containment_status"] == "NOT_APPLIED"
    assert st["pending_approval"] is False
    assert st["selected_action"] is None

    try:
        call("POST", "/api/defense/approve", {"action": "PROTECT_FILE_SERVER", "approved_by": "Security Analyst"})
        raise AssertionError("approve without pending should fail")
    except urllib.error.HTTPError as exc:
        assert exc.code == 400

    call("POST", "/api/simulation/start", {"scenario_id": "SCN-001"})
    advance(6)  # through lateral_movement
    rec = call("GET", "/api/defense/recommend")
    pred = call("GET", "/api/predictions")
    det_before = call("GET", "/api/detection/current")
    graph_before = call("GET", "/api/attack-graph")
    print("REC", rec["recommended_action"], "PRED", pred["predicted_target"], "RISK", det_before["risk_score"])
    assert rec["recommended_action"]
    assert len(rec["options"]) >= 3
    assert pred["predicted_target"] == "FILE-SRV-01"
    file_before = next(n["status"] for n in graph_before["nodes"] if n["id"] == "FILE-SRV-01")
    assert file_before != "PROTECTED"
    path_before = list(graph_before["attack_path"])

    reviewed = call("POST", "/api/defense/review", {"action": "PROTECT_FILE_SERVER"})
    print("REVIEW", reviewed["approval_status"], reviewed["containment_status"], reviewed["executed"])
    assert reviewed["executed"] is False
    assert reviewed["approval_status"] == "PENDING_REVIEW"
    assert reviewed["containment_status"] == "NOT_APPLIED"
    assert reviewed["action"] == "PROTECT_FILE_SERVER"
    assert reviewed["state"]["containment"] is None
    assert node("FILE-SRV-01")["status"] == file_before
    st = status()
    assert st["pending_approval"] is True
    assert st["approval_status"] == "PENDING_REVIEW"
    assert st["selected_action"] == "PROTECT_FILE_SERVER"
    assert st["containment_status"] == "NOT_APPLIED"

    approved = call(
        "POST",
        "/api/defense/approve",
        {"action": "PROTECT_FILE_SERVER", "approved_by": "Security Analyst"},
    )
    state = approved["state"]
    st = status()
    det_after = call("GET", "/api/detection/current")
    graph_after = call("GET", "/api/attack-graph")
    pred_after = call("GET", "/api/predictions")
    rec_after = call("GET", "/api/defense/recommend")
    file_after = next(n for n in graph_after["nodes"] if n["id"] == "FILE-SRV-01")
    print(
        "APPROVE",
        st["approval_status"],
        st["containment_status"],
        file_after["status"],
        det_after["risk_score"],
        pred_after["predicted_target"],
    )
    assert st["approval_status"] == "APPROVED"
    assert st["approved_by"] == "Security Analyst"
    assert st["approval_timestamp"]
    assert st["containment_status"] == "VERIFIED"
    assert state["containment"]["simulated"] is True
    assert state["containment"]["real_network_action"] is False
    assert file_after["status"] == "PROTECTED"
    assert det_after["risk_score"] < det_before["risk_score"]
    assert graph_after["attack_path"] == path_before
    assert graph_after["graph_risk"] <= graph_before["graph_risk"]
    assert pred_after["predicted_target"] != "FILE-SRV-01"
    assert rec_after["options"]
    assert rec_after["recommended_action"]

    logs = call("GET", "/api/audit")["logs"]
    types = {row["event_type"] for row in logs}
    for needed in ("DEFENSE_REVIEWED", "DEFENSE_APPROVED", "CONTAINMENT_SIMULATED", "CONTAINMENT_VERIFIED"):
        assert needed in types, needed

    call("POST", "/api/simulation/reset", {})
    call("POST", "/api/simulation/start", {"scenario_id": "SCN-001"})
    advance(6)
    before = node("FILE-SRV-01")["status"]
    risk_before = call("GET", "/api/detection/current")["risk_score"]
    call("POST", "/api/defense/review", {"action": "PROTECT_FILE_SERVER"})
    rejected = call(
        "POST",
        "/api/defense/reject",
        {
            "action": "PROTECT_FILE_SERVER",
            "rejected_by": "Security Analyst",
            "reason": "Operational disruption too high",
        },
    )
    st = status()
    after = node("FILE-SRV-01")["status"]
    print("REJECT", st["approval_status"], st["containment_status"], after)
    assert st["approval_status"] == "REJECTED"
    assert st["approved_by"] is None
    assert st["containment_status"] == "NOT_APPLIED"
    assert rejected["state"]["containment"] is None
    assert after == before
    assert call("GET", "/api/detection/current")["risk_score"] == risk_before
    logs = call("GET", "/api/audit")["logs"]
    assert any(row["event_type"] == "DEFENSE_REJECTED" for row in logs)

    call("POST", "/api/simulation/reset", {})
    st = status()
    assert st["approval_status"] == "NONE"
    assert st["containment_status"] == "NOT_APPLIED"
    assert st["pending_approval"] is False
    assert st["selected_action"] is None
    print("PHASE6_PASS")


if __name__ == "__main__":
    main()
