"""Phase 9 prediction outcome learning tests."""
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


async def ws_check() -> None:
    async with websockets.connect("ws://127.0.0.1:8000/ws/events") as ws:
        msg = await asyncio.wait_for(ws.recv(), timeout=5)
        data = json.loads(msg)
        assert data.get("state") is not None
        learn = (data.get("state") or {}).get("learning") or {}
        assert "summary" in learn or learn.get("label") or data.get("type")
        print("WS_OK", data.get("type"))


def main() -> None:
    call("POST", "/api/simulation/reset", {})
    hist = call("GET", "/api/learning/history")
    assert hist["open_prediction"] is None

    call("POST", "/api/simulation/start", {"scenario_id": "SCN-001"})
    call("POST", "/api/simulation/next-event", {})
    hist = call("GET", "/api/learning/history")
    openp = hist["open_prediction"]
    pred = call("GET", "/api/predictions")
    print("OPEN", openp["predicted_target"], openp["predicted_action"], openp["outcome"])
    assert openp["outcome"] == "UNRESOLVED"
    assert openp["predicted_target"] == pred["predicted_target"]
    assert openp["actual_target"] is None

    call("POST", "/api/simulation/next-event", {})
    hist = call("GET", "/api/learning/history")
    resolved = [r for r in hist["history"] if r.get("outcome") != "UNRESOLVED"]
    assert resolved, "previous prediction was not resolved"
    last = resolved[-1]
    print("RESOLVED", last["predicted_target"], last["actual_target"], last["outcome"], last["predicted_action"], last["actual_action"])
    assert last["actual_target"] == "LAB-PC-21"
    assert last["actual_action"] == "MASS_FILE_MODIFICATION"
    if last["target_correct"] and last["action_correct"]:
        assert last["outcome"] == "CORRECT"
    elif last["target_correct"] or last["action_correct"]:
        assert last["outcome"] == "PARTIAL"
    else:
        assert last["outcome"] == "INCORRECT"
    openp = hist["open_prediction"]
    assert openp["outcome"] == "UNRESOLVED"
    assert openp["prediction_id"] != last["prediction_id"]

    for _ in range(4):
        call("POST", "/api/simulation/next-event", {})
    summary = call("GET", "/api/learning/summary")
    print(
        "ACC",
        summary["resolved_predictions"],
        summary["correct_predictions"],
        summary["target_accuracy"],
        summary["overall_accuracy"],
    )
    assert summary["resolved_predictions"] >= 1
    assert summary["correct_predictions"] + summary["partial_predictions"] + summary["incorrect_predictions"] == summary["resolved_predictions"]
    assert 0 <= summary["target_accuracy"] <= 100
    assert 0 <= summary["action_accuracy"] <= 100
    assert 0 <= summary["overall_accuracy"] <= 100
    again = call("GET", "/api/learning/summary")
    assert again["overall_accuracy"] == summary["overall_accuracy"]
    for adj in summary["memory_adjustments"]:
        assert -10 <= adj["historical_adjustment"] <= 10
    pred = call("GET", "/api/predictions")
    assert pred["predicted_target"] == "FILE-SRV-01"
    dmem = call("GET", "/api/learning/defense-memory")["defense_memory"]
    assert dmem
    assert any(d.get("defense_action") for d in dmem)

    resolved_before_reset = summary["resolved_predictions"]
    adjustments_before = summary["memory_adjustments"]
    call("POST", "/api/simulation/reset", {})
    state = call("GET", "/api/simulation/state")["state"]
    assert state["events"] == []
    assert state.get("open_prediction") is None
    after = call("GET", "/api/learning/summary")
    assert after["resolved_predictions"] == resolved_before_reset
    assert after["memory_adjustments"] == adjustments_before
    assert call("GET", "/api/learning/defense-memory")["defense_memory"]

    asyncio.run(ws_check())
    print("PHASE9_PASS")


if __name__ == "__main__":
    main()
