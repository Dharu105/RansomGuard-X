"""Evidence-backed synthetic playbook evolution. Proposes only; never auto-executes."""
from __future__ import annotations

from datetime import datetime
from typing import Any

import yaml

from app.playbook.models import PLAYBOOK_ID, V1_STEPS

_CHANGE_SEQ = 0
_VERSIONS: dict[int, dict[str, Any]] = {}
_ACTIVE = 1
_PROPOSALS: list[dict[str, Any]] = []


def _now() -> str:
    return datetime.utcnow().isoformat()


def _yaml_for(version: int, steps: list[dict[str, Any]], reason: str = "") -> str:
    payload = {
        "playbook": {
            "id": PLAYBOOK_ID,
            "version": version,
            "trigger": "ransomware_likely",
            "status": "ACTIVE" if version == _ACTIVE else "SUPERSEDED",
            "reason_for_change": reason,
        },
        "steps": [s["id"] for s in steps],
        "recommended_actions": ["SIMULATED_CONTAINMENT", "HUMAN_APPROVAL"],
        "note": "YAML is documentation only. It is not executed as code.",
    }
    return yaml.safe_dump(payload, sort_keys=False)


def _seed() -> None:
    if _VERSIONS:
        return
    _VERSIONS[1] = {
        "playbook_id": PLAYBOOK_ID,
        "version": 1,
        "created_at": _now(),
        "status": "ACTIVE",
        "trigger": "ransomware_likely",
        "steps": list(V1_STEPS),
        "recommended_actions": ["SIMULATED_CONTAINMENT", "HUMAN_APPROVAL"],
        "reason_for_change": "Initial synthetic ransomware containment workflow.",
        "evidence": ["Seeded RANSOMWARE_CONTAINMENT_V1"],
        "previous_version": None,
        "yaml": _yaml_for(1, V1_STEPS, "Initial version"),
        "simulated": True,
    }


_seed()


def version_label(version: int) -> str:
    return f"{PLAYBOOK_ID}_V{version}"


def current() -> dict[str, Any]:
    _seed()
    row = dict(_VERSIONS[_ACTIVE])
    row["label"] = version_label(_ACTIVE)
    return row


def versions() -> list[dict[str, Any]]:
    _seed()
    return [{**dict(_VERSIONS[v]), "label": version_label(v)} for v in sorted(_VERSIONS)]


def proposals(status: str | None = None) -> list[dict[str, Any]]:
    rows = list(_PROPOSALS)
    if status:
        rows = [p for p in rows if p["status"] == status]
    return rows


def snapshot() -> dict[str, Any]:
    cur = current()
    open_p = next((p for p in reversed(_PROPOSALS) if p["status"] == "PROPOSED"), None)
    diff = None
    if open_p:
        diff = diff_steps(cur["steps"], open_p.get("proposed_steps") or cur["steps"])
    return {
        "playbook_id": PLAYBOOK_ID,
        "current": cur,
        "versions": versions(),
        "proposals": list(_PROPOSALS),
        "open_proposal": open_p,
        "diff": diff,
        "label": "Synthetic workflow description — not executed",
        "simulated": True,
        "auto_approved": False,
    }


def collect_evidence(state: dict[str, Any]) -> dict[str, Any]:
    adapt = state.get("adaptation") or {}
    learning = state.get("learning") or {}
    defense = state.get("defense") or {}
    scenarios = adapt.get("scenarios") or []
    high = next((s for s in scenarios if s.get("adaptation_level") in ("HIGH", "VERY_HIGH")), None)
    alt = None
    if high and high.get("alternate_target"):
        alt = high["alternate_target"]
    elif adapt.get("alternate_targets"):
        alt = adapt["alternate_targets"][0]
    missed = [
        m["target"]
        for m in (learning.get("memory_adjustments") or [])
        if float(m.get("historical_adjustment") or 0) < 0
    ]
    return {
        "defense_action": adapt.get("defense_action") or defense.get("recommended_action"),
        "robustness": adapt.get("robustness_class"),
        "robustness_score": adapt.get("robustness_score"),
        "high_outcome": (high or {}).get("outcome"),
        "low_risk": (scenarios[0] or {}).get("projected_risk") if scenarios else None,
        "high_risk": (high or {}).get("projected_risk"),
        "alternate_target": alt,
        "disruption": next(
            (o.get("operational_disruption") for o in (defense.get("options") or []) if o.get("action") == defense.get("recommended_action")),
            None,
        ),
        "missed_targets": missed,
        "has_events": bool(state.get("events")),
        "has_adaptation": bool(scenarios),
    }


def consider(state: dict[str, Any]) -> dict[str, Any] | None:
    """Propose a playbook change only when historical synthetic evidence exists."""
    _seed()
    events = state.get("events") or []
    if not events:
        return None
    ev = collect_evidence(state)
    if not ev["has_adaptation"]:
        return None
    types = {e.get("event_type") for e in events}
    progressed = "lateral_movement" in types
    rule = None
    change_type = None
    reason = None
    expected = None
    risk = "Low — configuration only; no real security action."
    proposed_steps = [dict(s) for s in current()["steps"]]
    evidence: list[str] = []
    ids = [s["id"] for s in proposed_steps]
    has_alt_step = "protect_alternate_critical_asset" in ids

    if (
        progressed
        and ev["robustness"] == "FRAGILE"
        and ev["high_outcome"] == "ALTERNATE_PATH"
        and ev["alternate_target"]
        and not has_alt_step
    ):
        rule = "RULE_1_ALTERNATE_PATH"
        change_type = "ADD_PROTECTION"
        insert_at = ids.index("predict_next_target") + 1 if "predict_next_target" in ids else len(proposed_steps)
        proposed_steps.insert(
            insert_at,
            {
                "id": "protect_alternate_critical_asset",
                "title": f"Protect alternate critical asset ({ev['alternate_target']})",
            },
        )
        reason = (
            f"Historical simulated incidents show that protecting the predicted target "
            f"({ev['defense_action']}) can cause an alternate path toward {ev['alternate_target']} "
            f"under high attacker adaptation."
        )
        expected = f"Add a verification/protection step for {ev['alternate_target']}."
        evidence = [
            f"{ev['defense_action']}",
            f"Robustness: {ev['robustness']}",
            f"High adaptation outcome: {ev['high_outcome']}",
            f"Alternate target: {ev['alternate_target']}",
        ]
        if ev["low_risk"] is not None and ev["high_risk"] is not None:
            evidence.append(f"Residual risk {ev['low_risk']} → {ev['high_risk']} under simulated adaptation")
    elif (
        progressed
        and ev["robustness"] == "FRAGILE"
        and ev["high_outcome"] == "ALTERNATE_PATH"
        and ev["alternate_target"]
        and has_alt_step
        and "increase_human_review" not in ids
    ):
        rule = "RULE_1_FOLLOWUP_REVIEW"
        change_type = "INCREASE_HUMAN_REVIEW"
        insert_at = ids.index("request_human_approval") if "request_human_approval" in ids else len(proposed_steps)
        proposed_steps.insert(
            insert_at,
            {
                "id": "increase_human_review",
                "title": "Increase human review before simulated containment",
            },
        )
        reason = (
            f"After adding alternate-path protection, simulated adaptation toward {ev['alternate_target']} "
            f"remains FRAGILE. Increase human review before containment."
        )
        expected = "Require an extra analyst confirmation gate."
        evidence = [
            f"{ev['defense_action']}",
            f"Robustness: {ev['robustness']}",
            f"High adaptation outcome: {ev['high_outcome']}",
            f"Alternate target: {ev['alternate_target']}",
        ]
    elif (
        progressed
        and ev["robustness"] == "FRAGILE"
        and ev["high_outcome"] == "ALTERNATE_PATH"
        and ev["alternate_target"]
        and has_alt_step
        and "verify_alternate_path" not in ids
    ):
        rule = "RULE_1_FOLLOWUP_VERIFY"
        change_type = "INCREASE_VERIFICATION"
        insert_at = ids.index("verify_containment") + 1 if "verify_containment" in ids else len(proposed_steps)
        proposed_steps.insert(
            insert_at,
            {
                "id": "verify_alternate_path",
                "title": f"Increase verification of alternate path toward {ev['alternate_target']}",
            },
        )
        reason = (
            f"Simulated adaptation toward {ev['alternate_target']} remains FRAGILE after prior playbook revisions. "
            f"Increase verification of that alternate path."
        )
        expected = f"Confirm {ev['alternate_target']} stays covered after simulated containment."
        evidence = [
            f"{ev['defense_action']}",
            f"Robustness: {ev['robustness']}",
            f"High adaptation outcome: {ev['high_outcome']}",
            f"Alternate target: {ev['alternate_target']}",
        ]
    elif progressed and ev["robustness"] == "ROBUST" and ev["defense_action"]:
        rule = "RULE_2_ROBUST"
        change_type = "REORDER_STEP"
        if "compare_defenses" in ids and "identify_attack_path" in ids:
            compare = next(s for s in proposed_steps if s["id"] == "compare_defenses")
            proposed_steps = [s for s in proposed_steps if s["id"] != "compare_defenses"]
            at = next(i for i, s in enumerate(proposed_steps) if s["id"] == "identify_attack_path") + 1
            proposed_steps.insert(at, compare)
        reason = (
            f"{ev['defense_action']} was ROBUST across simulated adaptation levels. "
            f"Promote this defense earlier in the playbook."
        )
        expected = "Surface the robust defense sooner during human review."
        evidence = [f"{ev['defense_action']}", f"Robustness: {ev['robustness']}"]
    elif progressed and ev["missed_targets"]:
        rule = "RULE_3_MISSED_TARGET"
        change_type = "INCREASE_VERIFICATION"
        missed = ev["missed_targets"][0]
        if "investigate_missed_target" not in ids:
            proposed_steps.insert(
                ids.index("predict_next_target") + 1 if "predict_next_target" in ids else 3,
                {"id": "investigate_missed_target", "title": f"Increase investigation priority for {missed}"},
            )
        reason = (
            f"Predictions historically missed {missed}. "
            f"Increase investigation priority for the historically missed target."
        )
        expected = f"Analysts review {missed} before approving containment."
        evidence = [f"Historical adjustment negative for {t}" for t in ev["missed_targets"]]
    elif progressed and ev["disruption"] == "HIGH":
        rule = "RULE_4_DISRUPTION"
        change_type = "CHANGE_RECOMMENDED_ACTION"
        reason = (
            "Operational disruption is consistently high. "
            "Prefer a lower-disruption alternative when equivalent risk reduction is available."
        )
        expected = "Bias compare_defenses toward lower-disruption options."
        evidence = [f"Recommended disruption: {ev['disruption']}"]
    else:
        return None

    existing = [
        p
        for p in _PROPOSALS
        if p["status"] == "PROPOSED" and p.get("rule") == rule and p["current_version"] == _ACTIVE
    ]
    if existing:
        return existing[-1]

    return _add_proposal(rule, change_type, reason, expected, risk, evidence, proposed_steps)


def _add_proposal(
    rule: str,
    change_type: str,
    reason: str,
    expected: str,
    risk: str,
    evidence: list[str],
    proposed_steps: list[dict[str, Any]],
) -> dict[str, Any]:
    global _CHANGE_SEQ
    _CHANGE_SEQ += 1
    cur = _ACTIVE
    row = {
        "change_id": f"CHG-{_CHANGE_SEQ:04d}",
        "playbook_id": PLAYBOOK_ID,
        "current_version": cur,
        "proposed_version": cur + 1,
        "change_type": change_type,
        "rule": rule,
        "reason": reason,
        "supporting_evidence": evidence,
        "expected_benefit": expected,
        "risk": risk,
        "status": "PROPOSED",
        "proposed_steps": proposed_steps,
        "created_at": _now(),
        "simulated": True,
        "auto_approved": False,
        "audited": False,
        "label": "Proposal only — human review required",
    }
    _PROPOSALS.append(row)
    return row


def diff_steps(old: list[dict[str, Any]], new: list[dict[str, Any]]) -> dict[str, Any]:
    old_ids = [s["id"] for s in old]
    new_ids = [s["id"] for s in new]
    added = [s for s in new if s["id"] not in old_ids]
    removed = [s for s in old if s["id"] not in new_ids]
    shared_old = [i for i in old_ids if i in new_ids]
    shared_new = [i for i in new_ids if i in old_ids]
    reordered = shared_old != shared_new
    unchanged = [s for s in new if s["id"] in old_ids]
    return {
        "from_version": None,
        "to_version": None,
        "added": added,
        "removed": removed,
        "reordered": reordered,
        "unchanged": unchanged,
        "old_ids": old_ids,
        "new_ids": new_ids,
    }


def approve(change_id: str, actor: str = "Security Analyst", reason: str = "") -> dict[str, Any]:
    global _ACTIVE
    prop = next((p for p in _PROPOSALS if p["change_id"] == change_id), None)
    if not prop:
        raise KeyError(f"Unknown change {change_id}")
    if prop["status"] != "PROPOSED":
        raise PermissionError(f"Change {change_id} is {prop['status']}, not PROPOSED.")
    prev = _ACTIVE
    new_v = prev + 1
    steps = [dict(s) for s in prop["proposed_steps"]]
    _VERSIONS[prev]["status"] = "SUPERSEDED"
    _VERSIONS[new_v] = {
        "playbook_id": PLAYBOOK_ID,
        "version": new_v,
        "created_at": _now(),
        "status": "ACTIVE",
        "trigger": "ransomware_likely",
        "steps": steps,
        "recommended_actions": ["SIMULATED_CONTAINMENT", "HUMAN_APPROVAL"],
        "reason_for_change": reason or prop["reason"],
        "evidence": list(prop["supporting_evidence"]),
        "previous_version": prev,
        "yaml": _yaml_for(new_v, steps, prop["reason"]),
        "simulated": True,
    }
    _ACTIVE = new_v
    prop["status"] = "APPROVED"
    prop["approved_by"] = actor
    prop["resolved_at"] = _now()
    d = diff_steps(_VERSIONS[prev]["steps"], steps)
    d["from_version"] = prev
    d["to_version"] = new_v
    return {"ok": True, "proposal": prop, "active": current(), "diff": d}


def reject(change_id: str, actor: str = "Security Analyst", reason: str = "") -> dict[str, Any]:
    prop = next((p for p in _PROPOSALS if p["change_id"] == change_id), None)
    if not prop:
        raise KeyError(f"Unknown change {change_id}")
    if prop["status"] != "PROPOSED":
        raise PermissionError(f"Change {change_id} is {prop['status']}, not PROPOSED.")
    prop["status"] = "REJECTED"
    prop["rejected_by"] = actor
    prop["reject_reason"] = reason
    prop["resolved_at"] = _now()
    return {"ok": True, "proposal": prop, "active": current()}
