"""Phase 2 detection/risk/stage/intent tests against a running server."""
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


def det():
    return call("GET", "/api/detection/current")


def main() -> None:
    call("POST", "/api/simulation/reset", {})
    empty = det()
    print("NO_EVENTS", empty["classification"], empty["risk_score"], empty["attack_stage"], empty["evidence"])
    assert empty["classification"] == "NORMAL"
    assert empty["risk_score"] == 0
    assert empty["evidence"] == []
    assert empty["attack_stage"] == "NORMAL"

    call("POST", "/api/simulation/start", {"scenario_id": "SCN-001"})
    scores = []
    prev = -1
    for expected in [
        "suspicious_process",
        "mass_file_modification",
        "rapid_file_rename",
        "credential_access",
        "privilege_escalation",
        "lateral_movement",
        "file_server_access",
        "backup_access_attempt",
    ]:
        st = call("POST", "/api/simulation/next-event", {})["state"]
        d = det()
        last = st["events"][-1]["event_type"]
        assert last == expected
        assert expected in d["evidence"]
        assert d["risk_score"] > prev
        assert d["risk_score"] < 100
        prev = d["risk_score"]
        scores.append(
            (
                last,
                d["classification"],
                d["risk_score"],
                d["risk_level"],
                d["attack_stage"],
                d["intent"],
                d["confidence"],
                d["evidence"],
            )
        )
        print("STEP", scores[-1][:6])

    assert scores[0][3] in ("LOW", "MEDIUM")
    assert scores[2][3] == "HIGH"  # rapid_file_rename
    assert scores[4][3] == "CRITICAL"  # privilege_escalation
    assert scores[-1][2] >= scores[0][2]
    assert scores[-1][1] == "RANSOMWARE_LIKELY"
    assert scores[-1][3] == "CRITICAL"
    assert scores[-1][4] == "RANSOMWARE_IMPACT"
    assert "backup_access_attempt" in scores[-1][7]
    print("PHASE2_PASS")


if __name__ == "__main__":
    main()
