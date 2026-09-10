"""Safe simulated containment. Mutates synthetic SimulationState only."""
from __future__ import annotations

from typing import Any

from app.detection.engine import band

NODE_IDS = {"LAB-PC-21", "student.kumar", "FAC-PC-07", "FILE-SRV-01", "BACKUP-SRV-01"}

EFFECTS = {
    "ISOLATE_LAB_PC": {
        "protected_assets": ["LAB-PC-21"],
        "isolated_assets": ["LAB-PC-21"],
        "revoked_credentials": [],
        "blocked_paths": ["LAB-PC-21->student.kumar"],
        "expected_status": {"LAB-PC-21": "PROTECTED"},
    },
    "DISABLE_STUDENT_ACCOUNT": {
        "protected_assets": ["student.kumar"],
        "isolated_assets": [],
        "revoked_credentials": ["student.kumar", "CRED-STU-21"],
        "blocked_paths": ["LAB-PC-21->student.kumar", "student.kumar->FAC-PC-07"],
        "expected_status": {"student.kumar": "PROTECTED"},
    },
    "ISOLATE_FACULTY_PC": {
        "protected_assets": ["FAC-PC-07"],
        "isolated_assets": ["FAC-PC-07"],
        "revoked_credentials": [],
        "blocked_paths": ["student.kumar->FAC-PC-07", "FAC-PC-07->FILE-SRV-01"],
        "expected_status": {"FAC-PC-07": "PROTECTED"},
    },
    "PROTECT_FILE_SERVER": {
        "protected_assets": ["FILE-SRV-01"],
        "isolated_assets": [],
        "revoked_credentials": [],
        "blocked_paths": ["FAC-PC-07->FILE-SRV-01"],
        "expected_status": {"FILE-SRV-01": "PROTECTED"},
    },
    "PROTECT_BACKUP_SERVER": {
        "protected_assets": ["BACKUP-SRV-01"],
        "isolated_assets": [],
        "revoked_credentials": [],
        "blocked_paths": ["FILE-SRV-01->BACKUP-SRV-01"],
        "expected_status": {"BACKUP-SRV-01": "PROTECTED"},
    },
}

RISK_CUT = {
    "LAB-PC-21": 16,
    "student.kumar": 14,
    "FAC-PC-07": 18,
    "FILE-SRV-01": 22,
    "BACKUP-SRV-01": 24,
}


def apply(action: str, graph: dict[str, Any] | None = None) -> dict[str, Any]:
    """Project a synthetic containment outcome. No OS or network side effects."""
    spec = EFFECTS.get(action)
    if not spec:
        return {
            "contained": False,
            "action": action,
            "isolated_assets": [],
            "revoked_credentials": [],
            "blocked_paths": [],
            "protected_assets": [],
            "expected_status": {},
            "propagation_stopped": False,
            "simulated": True,
            "real_network_action": False,
            "notes": [f"Unknown simulated action {action}"],
        }
    current = (graph or {}).get("current_node") or (graph or {}).get("current_position")
    notes = [
        f"SIMULATED: {nid} marked PROTECTED" for nid in spec["protected_assets"]
    ]
    notes.append("real_network_action = false")
    return {
        "contained": True,
        "action": action,
        "isolated_assets": list(spec["isolated_assets"]),
        "revoked_credentials": list(spec["revoked_credentials"]),
        "blocked_paths": list(spec["blocked_paths"]),
        "protected_assets": list(spec["protected_assets"]),
        "expected_status": dict(spec["expected_status"]),
        "attacker_position": current,
        "propagation_stopped": True,
        "simulated": True,
        "real_network_action": False,
        "notes": notes,
    }


def protected_node_ids(containment: dict[str, Any] | None) -> set[str]:
    if not containment:
        return set()
    ids = set(containment.get("isolated_assets") or [])
    ids |= set(containment.get("protected_assets") or [])
    ids |= set(containment.get("revoked_credentials") or [])
    return {i for i in ids if i in NODE_IDS}


def verify(action: str, graph: dict[str, Any] | None, applied: dict[str, Any] | None) -> tuple[bool, str]:
    """Deterministic check that expected synthetic node states changed."""
    spec = EFFECTS.get(action)
    if not spec:
        return False, f"Cannot verify unknown simulated action {action}."
    nodes = {n["id"]: n for n in (graph or {}).get("nodes") or []}
    missing = []
    for nid, expected in spec["expected_status"].items():
        actual = (nodes.get(nid) or {}).get("status")
        if actual != expected:
            missing.append(f"{nid} expected {expected}, observed {actual or 'missing'}")
    protected = set(applied.get("protected_assets") or []) if applied else set()
    for nid in spec["protected_assets"]:
        if nid not in protected:
            missing.append(f"{nid} missing from simulated protected_assets")
    if missing:
        return False, "Simulated containment did not match expected state: " + "; ".join(missing)
    return True, f"Verified simulated protection for {', '.join(spec['protected_assets'])}."


def adjust_detection(det: dict[str, Any], containment: dict[str, Any] | None) -> dict[str, Any]:
    """Reduce blended detection risk using protected synthetic assets. Not a hardcoded pair."""
    if not det or not containment or not containment.get("contained"):
        return det
    protected = protected_node_ids(containment)
    if not protected:
        return det
    cut = sum(RISK_CUT.get(nid, 0) for nid in protected)
    before = float(det.get("risk_score") or 0)
    after = round(max(8.0, min(before, before - cut)), 1)
    det = dict(det)
    det["risk_score"] = after
    det["band"] = band(after)
    public = dict(det.get("public") or {})
    public["risk_score"] = after
    public["risk_level"] = det["band"]
    det["public"] = public
    return det
