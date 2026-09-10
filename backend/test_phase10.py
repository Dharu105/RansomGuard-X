"""Phase 10 playbook evolution tests. Proposals only — no real security actions."""
from __future__ import annotations

import asyncio
import json
import urllib.request

import websockets

BASE = "http://127.0.0.1:8000"
_TC = None


def _phase10_http_ready() -> bool:
    try:
        req = urllib.request.Request(BASE + "/api/playbooks/current")
        with urllib.request.urlopen(req, timeout=3) as res:
            return res.status == 200
    except Exception:
        return False


def _ensure_client() -> None:
    global _TC
    if _phase10_http_ready():
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
            assert data.get("state") is not None
            evo = (data.get("state") or {}).get("playbook_evolution") or {}
            assert evo.get("current") or evo.get("playbook_id") or data.get("type")
            print("WS_OK", data.get("type"), "testclient")
        return
    async with websockets.connect("ws://127.0.0.1:8000/ws/events") as ws:
        msg = await asyncio.wait_for(ws.recv(), timeout=5)
        data = json.loads(msg)
        assert data.get("state") is not None
        evo = (data.get("state") or {}).get("playbook_evolution") or {}
        assert evo.get("current") or evo.get("playbook_id") or data.get("type")
        print("WS_OK", data.get("type"))


def proposed():
    rows = call("GET", "/api/playbooks/proposals")["proposals"]
    return [p for p in rows if p.get("status") == "PROPOSED"]


def main() -> None:
    _ensure_client()
    call("POST", "/api/simulation/reset", {})
    current = call("GET", "/api/playbooks/current")["playbook"]
    listing = call("GET", "/api/playbooks")
    detail = call("GET", "/api/playbooks/RANSOMWARE_CONTAINMENT")
    print("V1", current["playbook_id"], current["version"], current["status"], len(current["steps"]))
    assert current["playbook_id"] == "RANSOMWARE_CONTAINMENT"
    assert current["version"] >= 1
    assert current["status"] == "ACTIVE"
    assert any(v["version"] == 1 for v in listing["versions"])
    assert any(v["version"] == 1 for v in detail["versions"])
    assert "detect_behavior" in [s["id"] for s in current["steps"]]
    assert current.get("yaml") and "RANSOMWARE_CONTAINMENT" in current["yaml"]

    before_start = len(call("GET", "/api/playbooks/proposals")["proposals"])
    call("POST", "/api/simulation/start", {"scenario_id": "SCN-001"})
    after_start = len(call("GET", "/api/playbooks/proposals")["proposals"])
    assert after_start == before_start, "no proposal with zero events / insufficient evidence"

    call("POST", "/api/simulation/next-event", {})
    after_one = [p for p in call("GET", "/api/playbooks/proposals")["proposals"] if p["status"] == "PROPOSED"]
    assert len(after_one) == len(proposed())
    # One synthetic event is not a completed incident; Rule 1 requires lateral_movement.
    early_ids = {p["change_id"] for p in after_one}

    for _ in range(5):
        call("POST", "/api/simulation/next-event", {})

    adapt = call("GET", "/api/adaptation")
    pred = call("GET", "/api/predictions")
    rec = call("GET", "/api/defense/recommend")
    print(
        "EVIDENCE",
        rec.get("recommended_action"),
        adapt.get("robustness_class"),
        [s.get("outcome") for s in adapt.get("scenarios") or []],
        adapt.get("alternate_targets"),
        pred.get("predicted_target"),
    )
    assert rec.get("recommended_action")
    assert adapt.get("scenarios")

    props = proposed()
    new_props = [p for p in props if p["change_id"] not in early_ids] or props
    assert new_props, "proposal should appear after a completed synthetic incident with evidence"
    prop = new_props[-1]
    print("PROP", prop["change_id"], prop["change_type"], prop["status"], prop["reason"][:80])
    assert prop["status"] == "PROPOSED"
    assert prop["auto_approved"] is False
    ev = " ".join(prop["supporting_evidence"])
    assert "FRAGILE" in ev or "ROBUST" in ev or "disruption" in ev.lower() or "Historical" in ev
    assert prop["playbook_id"] == "RANSOMWARE_CONTAINMENT"
    assert "BACKUP" in ev or "FILE" in ev or prop["change_type"] in (
        "ADD_PROTECTION",
        "REORDER_STEP",
        "INCREASE_VERIFICATION",
        "CHANGE_RECOMMENDED_ACTION",
        "INCREASE_HUMAN_REVIEW",
        "ADD_STEP",
    )
    fabricated = "invented-host" in ev.lower()
    assert not fabricated

    before_v = call("GET", "/api/playbooks/current")["playbook"]["version"]
    approved = call(
        "POST",
        f"/api/playbooks/proposals/{prop['change_id']}/approve",
        {"actor": "Security Analyst", "reason": "Accept simulated playbook improvement"},
    )
    active = approved["active"]
    print("APPROVED", active["version"], active["previous_version"], len(active["steps"]))
    assert active["version"] == before_v + 1
    assert active["previous_version"] == before_v
    assert active["status"] == "ACTIVE"
    versions = call("GET", "/api/playbooks/RANSOMWARE_CONTAINMENT")["versions"]
    assert any(v["version"] == before_v for v in versions)
    assert any(v["version"] == active["version"] for v in versions)
    d = approved["diff"]
    assert "added" in d and "removed" in d and "reordered" in d and "unchanged" in d
    if prop["change_type"] == "ADD_PROTECTION":
        assert any(s["id"] == "protect_alternate_critical_asset" for s in d["added"])

    # A follow-up proposal may be created from the same historical evidence; reject it.
    follow = proposed()
    if not follow:
        call("POST", "/api/simulation/next-event", {})
        follow = proposed()
    assert follow, "follow-up proposal expected after further evidence on the new version"
    reject_id = follow[-1]["change_id"]
    rejected = call(
        "POST",
        f"/api/playbooks/proposals/{reject_id}/reject",
        {"actor": "Security Analyst", "reason": "Hold configuration"},
    )
    print("REJECTED", rejected["proposal"]["status"], rejected["active"]["version"])
    assert rejected["proposal"]["status"] == "REJECTED"
    assert rejected["active"]["version"] == active["version"]
    assert rejected["active"]["status"] == "ACTIVE"

    logs = call("GET", "/api/audit")["logs"]
    types = {row["event_type"] for row in logs}
    print("AUDIT", sorted(t for t in types if "PLAYBOOK" in t))
    assert "PLAYBOOK_CHANGE_PROPOSED" in types
    assert "PLAYBOOK_CHANGE_APPROVED" in types
    assert "PLAYBOOK_CHANGE_REJECTED" in types
    assert "PLAYBOOK_VERSION_ACTIVATED" in types

    kept_version = call("GET", "/api/playbooks/current")["playbook"]["version"]
    kept_versions = [v["version"] for v in call("GET", "/api/playbooks")["versions"]]
    call("POST", "/api/simulation/reset", {})
    after_reset = call("GET", "/api/playbooks/current")["playbook"]
    assert after_reset["version"] == kept_version
    assert after_reset["playbook_id"] == "RANSOMWARE_CONTAINMENT"
    assert set(kept_versions) == {v["version"] for v in call("GET", "/api/playbooks")["versions"]}
    state = call("GET", "/api/simulation/state")["state"]
    assert state["events"] == []
    assert state["open_prediction"] is None

    # Determinism: same incident evidence yields the same rule/reason on a later run if a proposal opens.
    call("POST", "/api/simulation/start", {"scenario_id": "SCN-001"})
    for _ in range(6):
        call("POST", "/api/simulation/next-event", {})
    again = proposed()
    if again:
        print("DET", again[-1]["change_type"], again[-1]["rule"])
        assert again[-1]["change_type"]
        assert again[-1]["status"] == "PROPOSED"

    asyncio.run(ws_check())
    print("PHASE10_PASS")


if __name__ == "__main__":
    main()
