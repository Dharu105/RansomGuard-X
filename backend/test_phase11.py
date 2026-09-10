"""Phase 11 AI investigator tests. Explanation only — no security actions."""
from __future__ import annotations

import asyncio
import json
import urllib.request

import websockets

BASE = "http://127.0.0.1:8000"
_TC = None


def _ready() -> bool:
    try:
        req = urllib.request.Request(BASE + "/api/investigator")
        with urllib.request.urlopen(req, timeout=3) as res:
            return res.status == 200
    except Exception:
        return False


def _ensure_client() -> None:
    global _TC
    if _ready():
        _TC = None
        return
    from fastapi.testclient import TestClient
    from app.main import app

    _TC = TestClient(app)


def call(method: str, path: str, body=None):
    if _TC is not None:
        res = _TC.request(method, path, json=body)
        if res.status_code >= 400:
            raise AssertionError(f"{method} {path} -> {res.status_code} {res.text}")
        return res.json()
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(
        BASE + path,
        data=data,
        method=method,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=20) as res:
        return json.loads(res.read().decode())


async def ws_check() -> None:
    if _TC is not None:
        with _TC.websocket_connect("/ws/events") as ws:
            data = ws.receive_json()
            inv = (data.get("state") or {}).get("investigator") or {}
            assert data.get("state") is not None
            assert "incident_summary" in inv or data.get("type")
            print("WS_OK", data.get("type"), "testclient")
        return
    async with websockets.connect("ws://127.0.0.1:8000/ws/events") as ws:
        msg = await asyncio.wait_for(ws.recv(), timeout=5)
        data = json.loads(msg)
        inv = (data.get("state") or {}).get("investigator") or {}
        assert data.get("state") is not None
        assert "incident_summary" in inv
        print("WS_OK", data.get("type"))


def main() -> None:
    _ensure_client()
    call("POST", "/api/simulation/reset", {})
    empty = call("GET", "/api/investigator")
    print("EMPTY", empty.get("current_stage"), empty.get("attack_story"), empty.get("real_network_action"))
    assert empty["ok"] is True
    assert empty["attack_story"] == []
    assert empty["observed_events"] == []
    assert empty["real_network_action"] is False
    assert empty["controls_containment"] is False
    assert empty["uncertainty"]
    story0 = call("GET", "/api/investigator/story")
    assert story0["attack_story"] == []

    call("POST", "/api/simulation/start", {"scenario_id": "SCN-001"})
    types = []
    for _ in range(6):
        st = call("POST", "/api/simulation/next-event", {})["state"]
        types = [e["event_type"] for e in st["events"]]

    inv = call("GET", "/api/investigator")
    rec = call("GET", "/api/defense/recommend")
    adapt = call("GET", "/api/adaptation")
    pred = call("GET", "/api/predictions")
    print("STORY", [s["event_type"] for s in inv["attack_story"]])
    print("PRED", inv["prediction_explanation"]["label"], inv["prediction_explanation"]["predicted_target"])
    print("DEF", inv["defense_explanation"]["recommended_action"], rec.get("recommended_action"))
    print("ADAPT", inv["adaptation_explanation"]["label"], inv["adaptation_explanation"].get("robustness_class"))

    story_types = [s["event_type"] for s in inv["attack_story"]]
    assert story_types == types
    assert all(s["kind"] == "OBSERVED" for s in inv["attack_story"])
    assert "backup_access_attempt" not in story_types
    assert "PREDICTION" in inv["prediction_explanation"]["label"]
    assert "NOT OBSERVED" in inv["prediction_explanation"]["label"]
    assert inv["prediction_explanation"]["predicted_target"] == pred["predicted_target"]
    assert "SIMULATED" in inv["adaptation_explanation"]["label"]
    assert inv["defense_explanation"]["recommended_action"] == rec["recommended_action"]
    assert inv["defense_explanation"]["executed"] is False
    assert inv["defense_explanation"]["real_network_action"] is False
    assert inv["uncertainty"]
    assert "SIMULATION" in inv["learning_explanation"]["label"]
    play = inv["playbook_explanation"]
    assert "HUMAN APPROVAL" in play["label"]
    if play.get("evidence"):
        joined = " ".join(str(x) for x in play["evidence"])
        assert "invented-host" not in joined.lower()
    ev_text = " ".join(e["text"] for e in inv["key_evidence"])
    if rec.get("recommended_action"):
        assert rec["recommended_action"] in ev_text or rec["recommended_action"] in (inv["defense_explanation"]["explanation"] or "")
    assert inv["source_of_truth"] == "deterministic_backend"

    again = call("GET", "/api/investigator")
    assert again["attack_story"] == inv["attack_story"]
    assert again["prediction_explanation"]["predicted_target"] == inv["prediction_explanation"]["predicted_target"]
    assert again["defense_explanation"]["recommended_action"] == inv["defense_explanation"]["recommended_action"]
    evid = call("GET", "/api/investigator/evidence")
    assert "key_evidence" in evid

    asyncio.run(ws_check())
    print("PHASE11_PASS")


if __name__ == "__main__":
    main()
