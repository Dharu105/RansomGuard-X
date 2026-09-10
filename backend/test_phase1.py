"""Phase 1 API + WebSocket + start/next/reset checks."""
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
        print("WS_OK", data.get("type"))


def main() -> None:
    print("GET /api/simulation/state", call("GET", "/api/simulation/state")["ok"])
    print("GET /api/assets", len(call("GET", "/api/assets")["assets"]))
    print("GET /api/events", call("GET", "/api/events")["ok"])
    st = call("POST", "/api/simulation/start", {"scenario_id": "SCN-001"})["state"]
    print("START", st["incident_id"], st["current_event_index"], st["risk_score"])
    types = []
    for _ in range(8):
        st = call("POST", "/api/simulation/next-event", {})["state"]
        if st["events"]:
            types.append(st["events"][-1]["event_type"])
    print("EVENTS", types)
    live = call("GET", "/api/events")
    print("DB_LIVE", len(live["live"]), "STORED", len(live["stored"]))
    assert types[0] == "suspicious_process"
    assert "backup_access_attempt" in types
    assert st["risk_score"] > 0
    rst = call("POST", "/api/simulation/reset", {})["state"]
    print("RESET", rst["current_event_index"], rst["events"], rst["risk_score"])
    assert rst["events"] == []
    assert rst["risk_score"] == 0
    after = call("GET", "/api/events")
    assert after["live"] == []
    asyncio.run(ws_check())
    print("PHASE1_PASS")


if __name__ == "__main__":
    main()
