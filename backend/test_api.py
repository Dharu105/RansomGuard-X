"""Smoke-test core API endpoints against a running server."""
from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:8000"


def call(method: str, path: str, body: dict | None = None) -> dict:
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(
        BASE + path,
        data=data,
        method=method,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=20) as res:
        return json.loads(res.read().decode())


def main() -> int:
    failures = []
    tests = [
        ("GET", "/", None),
        ("GET", "/api/health", None),
        ("GET", "/api/simulation/state", None),
        ("GET", "/api/assets", None),
        ("GET", "/api/incidents", None),
        ("GET", "/api/events", None),
        ("GET", "/api/predictions", None),
        ("GET", "/api/attack-graph", None),
        ("GET", "/api/playbooks", None),
        ("GET", "/api/playbooks/yaml", None),
        ("GET", "/api/evaluation", None),
        ("GET", "/api/audit", None),
        ("GET", "/api/memory", None),
        ("GET", "/api/history/metrics", None),
        ("POST", "/api/simulation/reset", {}),
        ("POST", "/api/simulation/start", {"scenario_id": "SCN-001"}),
        ("POST", "/api/simulation/next-event", {}),
        ("POST", "/api/defense/recommend", {}),
        ("POST", "/api/defense/simulate", {"action": "ISOLATE_AND_REVOKE"}),
        ("POST", "/api/counterfactual/run", {"action": "ISOLATE_AND_REVOKE", "intervention_index": 3}),
        ("POST", "/api/robustness/test", {"rates": [30, 50, 70, 90]}),
        ("POST", "/api/intervention", {"index": 3}),
        ("POST", "/api/replay", {"command": "NEXT"}),
        ("POST", "/api/ai/investigate", {"question": "Why was isolation recommended?"}),
        ("POST", "/api/defense/approve", {"action": "ISOLATE_AND_REVOKE", "decision": "APPROVE", "approver": "test", "reason": "api smoke"}),
        ("POST", "/api/simulation/reset", {}),
    ]
    for method, path, body in tests:
        try:
            payload = call(method, path, body)
            ok = payload.get("ok", True) if isinstance(payload, dict) else True
            print(f"OK  {method} {path} ok={ok}")
        except urllib.error.HTTPError as e:
            print(f"FAIL {method} {path} HTTP {e.code}")
            failures.append(path)
        except Exception as e:
            print(f"FAIL {method} {path} {e}")
            failures.append(path)
    if failures:
        print("Failed:", failures)
        return 1
    print("All endpoint smoke tests passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
