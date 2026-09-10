"""Phase 8 adaptive attacker + robustness tests."""
from __future__ import annotations

import asyncio
import json
import urllib.request

import websockets

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
    return {
        "risk": state["risk_score"],
        "path": list(graph["attack_path"]),
        "current": graph["current_node"],
        "predicted": pred["predicted_target"],
        "containment": state.get("containment"),
        "compromised": [n["id"] for n in graph["nodes"] if n.get("compromised")],
        "statuses": {n["id"]: n["status"] for n in graph["nodes"]},
    }


async def ws_check() -> None:
    async with websockets.connect("ws://127.0.0.1:8000/ws/events") as ws:
        msg = await asyncio.wait_for(ws.recv(), timeout=5)
        data = json.loads(msg)
        assert data.get("state") is not None
        print("WS_OK", data.get("type"))


def main() -> None:
    call("POST", "/api/simulation/reset", {})
    empty = call("GET", "/api/adaptation")
    print("RESET", empty["defense_action"], empty["scenarios"], empty["robustness_score"])
    assert empty["defense_action"] is None
    assert empty["scenarios"] == []
    assert empty["robustness_score"] in (0, 0.0)

    call("POST", "/api/simulation/start", {"scenario_id": "SCN-001"})
    for _ in range(6):
        call("POST", "/api/simulation/next-event", {})

    rec = call("GET", "/api/defense/recommend")
    forks = call("GET", "/api/simulation/forks")
    assert rec["recommended_action"]
    assert len(forks["forks"]) >= 3

    before = capture()
    a = call("GET", "/api/adaptation")
    again = call("GET", "/api/adaptation")
    after = capture()
    print(
        "ADAPT",
        a["defense_action"],
        a["robustness_score"],
        a["robustness_class"],
        [s["outcome"] for s in a["scenarios"]],
        a["alternate_targets"],
    )
    assert after == before, "GET /api/adaptation mutated live state"
    assert a["defense_action"] == again["defense_action"]
    assert a["robustness_score"] == again["robustness_score"]
    assert [s["projected_risk"] for s in a["scenarios"]] == [s["projected_risk"] for s in again["scenarios"]]
    assert len(a["scenarios"]) == 4
    assert [s["adaptation_level"] for s in a["scenarios"]] == ["LOW", "MEDIUM", "HIGH", "VERY_HIGH"]
    assert [s["adaptation_score"] for s in a["scenarios"]] == [30, 50, 70, 90]
    assert 0 <= a["robustness_score"] <= 100
    assert a["robustness_class"] in ("ROBUST", "MODERATE", "FRAGILE", "UNCERTAIN")
    graph_ids = {n["id"] for n in call("GET", "/api/attack-graph")["nodes"]}
    for tgt in a["alternate_targets"]:
        assert tgt in graph_ids
    if a["protected_target"]:
        assert after["statuses"][a["protected_target"]] != "COMPROMISED" or a["protected_target"] in after["compromised"]
        # prediction ≠ containment: protected target is not newly marked compromised by adaptation GET
        assert after["statuses"][a["protected_target"]] == before["statuses"][a["protected_target"]]
    comps = a.get("comparisons") or []
    assert len(comps) >= 3
    scores = {c["defense_action"]: c["robustness_score"] for c in comps}
    assert len(set(scores.values())) >= 2
    asyncio.run(ws_check())

    call("POST", "/api/simulation/reset", {})
    cleared = call("GET", "/api/adaptation")
    assert cleared["defense_action"] is None
    assert cleared["scenarios"] == []
    assert cleared["robustness_score"] in (0, 0.0)
    print("PHASE8_PASS")


if __name__ == "__main__":
    main()
