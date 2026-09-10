"""Phase 12 synthetic evaluation tests. No real security actions."""
from __future__ import annotations

import asyncio
import json
import urllib.request

import websockets

BASE = "http://127.0.0.1:8000"
_TC = None


def _ready() -> bool:
    try:
        req = urllib.request.Request(BASE + "/api/evaluation/scenarios")
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
        res = _TC.request(method, path, json=body if body is not None else None)
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
    with urllib.request.urlopen(req, timeout=120) as res:
        return json.loads(res.read().decode())


async def ws_check() -> None:
    if _TC is not None:
        with _TC.websocket_connect("/ws/events") as ws:
            data = ws.receive_json()
            assert data.get("state") is not None
            assert "evaluation" in (data.get("state") or {}) or "investigator" in (data.get("state") or {})
            print("WS_OK", data.get("type"), "testclient")
        return
    async with websockets.connect("ws://127.0.0.1:8000/ws/events") as ws:
        msg = await asyncio.wait_for(ws.recv(), timeout=5)
        data = json.loads(msg)
        assert data.get("state") is not None
        assert "evaluation" in data["state"]
        print("WS_OK", data.get("type"))


def main() -> None:
    _ensure_client()
    reset = call("POST", "/api/evaluation/reset", {})
    print("RESET", reset.get("has_report"), reset.get("history_count"))
    assert reset["has_report"] is False
    assert reset["history_count"] == 0

    scenarios = call("GET", "/api/evaluation/scenarios")["scenarios"]
    ids = [s["id"] for s in scenarios]
    print("SCENARIOS", ids)
    for sid in ["SCN-001", "SCN-002", "SCN-003", "SCN-004", "SCN-005", "SCN-006"]:
        assert sid in ids

    for sid in ids:
        row = call("POST", "/api/evaluation/run", {"scenario_id": sid})
        print("RUN", sid, row.get("evaluation_id"), row["scenarios"][0]["classification"], row["scenarios"][0]["detection_result"])
        assert row["synthetic"] is True
        assert row["real_network_action"] is False
        assert row["scenarios"][0]["scenario_id"] == sid
        assert row["scenarios"][0]["synthetic"] is True

    full = call("POST", "/api/evaluation/run", {})
    print("FULL", full["evaluation_id"], full["detection_metrics"])
    assert full["synthetic"] is True
    assert full["real_network_action"] is False
    assert len(full["scenarios"]) == 6
    det = full["detection_metrics"]
    for key in ("true_positives", "false_positives", "true_negatives", "false_negatives", "precision", "recall", "f1"):
        assert key in det
        assert det[key] != "invented"
    pred = full["prediction_metrics"]
    assert "prediction_accuracy" in pred
    assert "target_accuracy" in pred
    assert "action_accuracy" in pred
    defense = full["defense_metrics"]
    assert "average_risk_reduction" in defense
    adapt = full["adaptation_metrics"]
    assert "distribution" in adapt
    timing = full["timing_metrics"]
    assert timing["basis"] == "EVENT-BASED TIMING"
    fp = full["false_positive_metrics"]["rows"]
    scn6 = next(r for r in full["scenarios"] if r["scenario_id"] == "SCN-006")
    print("FP", scn6["classification"], scn6["false_positive"], scn6["expected_class"])
    assert scn6["expected_ransomware_likely"] is False
    assert any(r["scenario"] == "SCN-006" for r in fp)
    base = full["baseline_comparison"]
    assert base["traditional"]["prediction_availability"] == "NOT_AVAILABLE"
    assert base["ransomguard_x"]["prediction_availability"] == "AVAILABLE"
    loop = full["closed_loop_metrics"]
    for k in ("detection", "prediction", "defense", "adaptation", "learning", "playbook_evolution"):
        assert loop[k] in ("PASS", "NOT_AVAILABLE")
    assert "synthetic scenarios" in full["limitations"]
    assert "no real-world accuracy claim" in full["limitations"]

    again = call("POST", "/api/evaluation/run", {})
    assert again["detection_metrics"] == full["detection_metrics"]
    assert again["prediction_metrics"] == full["prediction_metrics"]
    assert again["adaptation_metrics"]["distribution"] == full["adaptation_metrics"]["distribution"]

    listing = call("GET", "/api/evaluation")
    assert listing["ok"] is True
    assert listing["detection_metrics"]["precision"] == full["detection_metrics"]["precision"]
    assert listing.get("ransomguard_x")
    report = call("GET", "/api/evaluation/report")
    assert report["report"]["evaluation_id"] == again["evaluation_id"]
    hist = report["history"]
    assert len(hist) >= 8

    call("POST", "/api/evaluation/reset", {})
    after = call("GET", "/api/evaluation/report")
    assert after["report"] is None
    assert after["history"] == []

    asyncio.run(ws_check())
    print("PHASE12_PASS")


if __name__ == "__main__":
    main()
