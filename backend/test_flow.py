"""End-to-end simulation + websocket check."""
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


def main() -> None:
    call("POST", "/api/simulation/reset", {})
    call("POST", "/api/simulation/start", {"scenario_id": "SCN-001"})
    scores = []
    for _ in range(8):
        st = call("POST", "/api/simulation/next-event", {})["state"]
        pred = (st.get("predictions") or [{}])[0]
        rec = st.get("recommended_defense") or {}
        scores.append(
            (
                st["current_event_index"],
                st["risk_score"],
                st["risk_band"],
                st["current_stage"],
                pred.get("predicted_target"),
                rec.get("action"),
            )
        )
    print("PROGRESS", scores)
    st = call(
        "POST",
        "/api/defense/approve",
        {
            "action": "ISOLATE_AND_REVOKE",
            "decision": "APPROVE",
            "approver": "qa",
            "reason": "contain",
        },
    )["state"]
    print("CONTAINED", (st.get("containment") or {}).get("contained"), "REGRET", st.get("defense_regret"))
    pid = (st.get("playbook") or {}).get("proposal_id")
    print("PROPOSAL", pid)
    if pid:
        print("PLAYBOOK", call("POST", "/api/playbook/approve", {"proposal_id": pid, "decision": "ACCEPT", "reviewer": "qa"}).get("result"))
    print("DROP", call("POST", "/api/robustness/drop-event", {"event_type": "credential_access"})["state"].get("robustness_signal"))
    integrity = call("GET", "/api/audit")["integrity"]
    print("AUDIT", integrity["intact"], integrity["entries"])
    asyncio.run(ws_check())
    print("DONE")


async def ws_check() -> None:
    async with websockets.connect("ws://127.0.0.1:8000/ws/events") as ws:
        msg = await asyncio.wait_for(ws.recv(), timeout=5)
        data = json.loads(msg)
        print("WS", data.get("type"), bool(data.get("state")))


if __name__ == "__main__":
    main()
