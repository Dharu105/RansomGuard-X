"""Phase 13 demo-readiness: API health, WebSocket snapshot keys, no new security features."""
from __future__ import annotations

import asyncio
import json
import urllib.request

import websockets

BASE = "http://127.0.0.1:8000"
REQUIRED_STATE = (
    "detection",
    "attack_graph",
    "prediction",
    "defense",
    "attack_forks",
    "adaptation",
    "learning",
    "playbook_evolution",
    "investigator",
    "evaluation",
)


def call(method: str, path: str, body=None):
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(
        BASE + path,
        data=data,
        method=method,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as res:
        return json.loads(res.read().decode())


async def ws_check() -> None:
    async with websockets.connect("ws://127.0.0.1:8000/ws/events") as ws:
        msg = await asyncio.wait_for(ws.recv(), timeout=5)
        data = json.loads(msg)
        state = data.get("state") or {}
        assert state, "hello snapshot missing state"
        missing = [k for k in REQUIRED_STATE if k not in state]
        assert not missing, f"WS snapshot missing {missing}"
        print("WS_OK", data.get("type"), "keys", len(state))


def main() -> None:
    print("HEALTH", call("GET", "/api/health")["ok"])
    paths = [
        ("GET", "/api/detection/current"),
        ("GET", "/api/attack-graph"),
        ("GET", "/api/predictions"),
        ("GET", "/api/defense/recommend"),
        ("GET", "/api/forks"),
        ("GET", "/api/simulation/forks"),
        ("GET", "/api/adaptation"),
        ("GET", "/api/learning/summary"),
        ("GET", "/api/learning/history"),
        ("GET", "/api/learning/defense-memory"),
        ("GET", "/api/playbooks"),
        ("GET", "/api/playbooks/current"),
        ("GET", "/api/playbooks/proposals"),
        ("GET", "/api/investigator"),
        ("GET", "/api/evaluation"),
    ]
    for method, path in paths:
        row = call(method, path)
        assert row.get("ok") is True, path
        print("OK", path)

    call("POST", "/api/simulation/reset", {})
    hist = call("GET", "/api/learning/history")
    pb = call("GET", "/api/playbooks/current")
    assert hist["ok"] is True
    assert pb["playbook"]["playbook_id"] == "RANSOMWARE_CONTAINMENT"

    asyncio.run(ws_check())
    print("PHASE13_PASS")


if __name__ == "__main__":
    main()
