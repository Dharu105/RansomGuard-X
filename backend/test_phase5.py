"""Phase 5 adaptive defense recommendation tests against a running server."""
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


def defense():
    return call("GET", "/api/defense/recommend")


def pred():
    return call("GET", "/api/predictions")


def scores(payload):
    return {o["action"]: o["defense_score"] for o in payload["options"]}


def check_options(d, *, expect_rec: bool):
    opts = d["options"]
    if expect_rec:
        assert len(opts) >= 3
        assert d["recommended_action"]
        assert d["recommended_score"] == opts[0]["defense_score"]
        assert d["recommended_action"] == opts[0]["action"]
        ranked = [o["defense_score"] for o in opts]
        assert ranked == sorted(ranked, reverse=True)
        for o in opts:
            assert 0 <= o["defense_score"] <= 100
            assert 0 <= o["confidence"] <= 100
            assert o["risk_after"] <= o["risk_before"]
            assert o["blast_radius_after"] <= o["blast_radius_before"]
            assert o.get("real_network_action") is False
            assert o.get("simulated") is True
    else:
        assert d["recommended_action"] is None
        assert d["recommended_score"] in (0, 0.0)
        assert d["options"] == []


def main() -> None:
    call("POST", "/api/simulation/reset", {})
    d = defense()
    print("RESET", d["recommended_action"], d["recommended_score"], d["options"])
    check_options(d, expect_rec=False)
    assert d.get("pending_approval") in (None, {})

    call("POST", "/api/simulation/start", {"scenario_id": "SCN-001"})
    d = defense()
    check_options(d, expect_rec=False)

    steps = [
        "suspicious_process",
        "mass_file_modification",
        "rapid_file_rename",
        "credential_access",
        "privilege_escalation",
        "lateral_movement",
        "file_server_access",
        "backup_access_attempt",
    ]
    seen = []
    for ev in steps:
        call("POST", "/api/simulation/next-event", {})
        d = defense()
        p = pred()
        again = defense()
        state = call("GET", "/api/simulation/state")["state"]
        print(
            "STEP",
            ev,
            d["recommended_action"],
            d["recommended_score"],
            [o["action"] for o in d["options"][:3]],
            p["predicted_target"],
        )
        check_options(d, expect_rec=True)
        assert d["recommended_action"] == again["recommended_action"]
        assert d["recommended_score"] == again["recommended_score"]
        assert [o["action"] for o in d["options"]] == [o["action"] for o in again["options"]]
        assert state.get("containment") is None
        seen.append((ev, d, p))

        if ev == "suspicious_process":
            s = scores(d)
            assert s["ISOLATE_LAB_PC"] > s["PROTECT_BACKUP_SERVER"]
        if ev == "lateral_movement":
            s = scores(d)
            assert p["predicted_target"] == "FILE-SRV-01"
            assert s["PROTECT_FILE_SERVER"] > s["ISOLATE_LAB_PC"]
            assert d["recommended_action"] == "PROTECT_FILE_SERVER"
        if ev == "file_server_access":
            s = scores(d)
            assert p["predicted_target"] == "BACKUP-SRV-01"
            assert s["PROTECT_BACKUP_SERVER"] >= s["PROTECT_FILE_SERVER"]
            assert d["recommended_action"] == "PROTECT_BACKUP_SERVER"
        if ev == "backup_access_attempt":
            s = scores(d)
            assert s["PROTECT_BACKUP_SERVER"] >= s["ISOLATE_LAB_PC"]

    # Review queues approval without executing containment
    queued = call("POST", "/api/defense/review", {})
    assert queued["executed"] is False
    assert queued["state"]["containment"] is None
    assert queued["state"]["pending_approval"]["status"] == "PENDING_REVIEW"
    assert queued["state"]["pending_approval"]["executed"] is False

    call("POST", "/api/simulation/reset", {})
    d = defense()
    check_options(d, expect_rec=False)
    assert d.get("pending_approval") in (None, {})
    print("PHASE5_PASS")


if __name__ == "__main__":
    main()
