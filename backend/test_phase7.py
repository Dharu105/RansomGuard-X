"""Phase 7 Attack Fork Lab tests against a running server."""
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


def capture():
    state = call("GET", "/api/simulation/state")["state"]
    graph = call("GET", "/api/attack-graph")
    pred = call("GET", "/api/predictions")
    det = call("GET", "/api/detection/current")
    rec = call("GET", "/api/defense/recommend")
    return {
        "risk": state["risk_score"],
        "path": list(graph["attack_path"]),
        "current": graph["current_node"],
        "predicted": pred["predicted_target"],
        "defense": rec["recommended_action"],
        "compromised": [n["id"] for n in graph["nodes"] if n.get("compromised")],
        "containment": state.get("containment"),
        "approval": state.get("approval_status"),
    }


def main() -> None:
    call("POST", "/api/simulation/reset", {})
    empty = call("GET", "/api/simulation/forks")
    print("RESET", empty["forks"], empty["best_fork"])
    assert empty["forks"] == []
    assert empty["best_fork"] is None

    call("POST", "/api/simulation/start", {"scenario_id": "SCN-001"})
    for _ in range(6):
        call("POST", "/api/simulation/next-event", {})

    before = capture()
    print("LIVE", before["risk"], before["current"], before["predicted"])
    forks = call("GET", "/api/simulation/forks")
    after = capture()
    print("FORKS", len(forks["forks"]), "BEST", (forks["best_fork"] or {}).get("defense_action"))

    assert after == before, "GET /api/simulation/forks mutated live state"
    assert forks["live_state_mutated"] is False
    assert after["containment"] is None
    assert len(forks["forks"]) >= 3
    assert forks["current_state"]["risk"] == before["risk"]
    assert forks["current_state"]["current_node"] == before["current"]
    assert forks["current_state"]["predicted_target"] == before["predicted"]

    scores = [f["fork_score"] for f in forks["forks"]]
    assert scores == sorted(scores, reverse=True)
    best = forks["best_fork"]
    assert best is not None
    assert best["fork_score"] == forks["forks"][0]["fork_score"]
    assert best["defense_action"] == forks["forks"][0]["defense_action"]
    assert best.get("applied") is False

    risks = {f["defense_action"]: f["projected_risk"] for f in forks["forks"]}
    assert len(set(risks.values())) >= 2
    for f in forks["forks"]:
        assert f["projected_risk"] <= f["risk_before"]
        assert f["blast_radius_after"] <= f["blast_radius_before"]
        assert 0 <= f["fork_score"] <= 100
        assert f["simulated"] is True

    protect = next(f for f in forks["forks"] if f["defense_action"] == "PROTECT_FILE_SERVER")
    assert before["predicted"] == "FILE-SRV-01"
    assert protect["projected_next_target"] == "BACKUP-SRV-01"
    assert "FILE-SRV-01" in protect["protected_assets"]

    reviewed = call("POST", "/api/defense/review", {"action": best["defense_action"]})
    assert reviewed["approval_status"] == "PENDING_REVIEW"
    assert reviewed["containment_status"] == "NOT_APPLIED"
    assert reviewed["executed"] is False
    assert reviewed["state"]["containment"] is None
    assert call("GET", "/api/detection/current")["risk_score"] == before["risk"]

    call("POST", "/api/simulation/reset", {})
    cleared = call("GET", "/api/simulation/forks")
    assert cleared["forks"] == []
    assert cleared["best_fork"] is None
    print("PHASE7_PASS")


if __name__ == "__main__":
    main()
