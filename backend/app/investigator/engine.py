"""Evidence-grounded AI investigator. Explains synthetic incidents; never contains."""
from __future__ import annotations

import os
from typing import Any

from app.investigator.models import EMPTY, STORY_LINES


def analyze(state: dict[str, Any] | None) -> dict[str, Any]:
    """Build a structured investigation from existing application state only."""
    src = dict(state or {})
    src.pop("investigator", None)
    events = list(src.get("events") or [])
    if not events:
        empty = dict(EMPTY)
        empty["playbook_explanation"] = _playbook(src)
        empty["learning_explanation"] = _learning(src)
        empty["uncertainty"] = [
            "limited synthetic evidence",
            "no previous comparable incident in the current scenario",
            "prediction not yet resolved",
        ]
        empty["recommended_investigation_questions"] = [
            "Is there any synthetic telemetry to review yet?",
            "Should the safe simulation be started to collect evidence?",
        ]
        return empty
    return _analyze_with_events(src, events)


def _analyze_with_events(src: dict[str, Any], events: list[dict[str, Any]]) -> dict[str, Any]:
    detection = src.get("detection") or {}
    graph = src.get("attack_graph") or {}
    pred = src.get("prediction") or {}
    defense = src.get("defense") or {}
    adapt = src.get("adaptation") or {}
    blast = src.get("blast_radius") or graph.get("blast_radius") or {}
    current_node = graph.get("current_node")
    stage = detection.get("attack_stage") or src.get("current_stage") or "NORMAL"
    story = _story(events)
    observed_events = [e.get("event_type") for e in events if e.get("event_type")]
    observed_assets: list[str] = []
    for e in events:
        aid = e.get("asset_id")
        if aid and aid not in observed_assets:
            observed_assets.append(aid)
    nodes = {n["id"]: n for n in (graph.get("nodes") or [])}
    crit = (nodes.get(current_node) or {}).get("criticality")
    blast_n = len(blast.get("potentially_affected") or blast.get("at_risk") or [])
    if not blast_n:
        blast_n = int(blast.get("size") or 0)
    risk_score = src.get("risk_score") if src.get("risk_score") is not None else detection.get("risk_score") or 0
    risk_band = src.get("risk_band") or detection.get("risk_level") or "LOW"
    result = {
        "incident_summary": _summary(events, risk_band, stage, current_node, pred, defense),
        "attack_story": story,
        "current_risk": {
            "risk_score": risk_score,
            "risk_classification": risk_band,
            "attack_stage": stage,
            "current_node": current_node,
            "criticality": crit,
            "blast_radius": blast_n,
            "explanation": _risk_text(events, risk_band, stage, current_node, crit, blast_n),
            "label": "SIMULATED / EXPERIMENTAL",
        },
        "current_stage": stage,
        "observed_assets": observed_assets,
        "observed_events": observed_events,
        "key_evidence": _key_evidence(events, detection, graph, pred, defense, adapt),
        "prediction_explanation": _prediction(src, pred, graph, events),
        "defense_explanation": _defense(defense, pred),
        "adaptation_explanation": _adaptation(adapt),
        "learning_explanation": _learning(src),
        "playbook_explanation": _playbook(src),
        "uncertainty": [],
        "recommended_investigation_questions": [],
        "confidence": _confidence(events, detection, pred),
        "simulated": True,
        "real_network_action": False,
        "controls_containment": False,
        "source_of_truth": "deterministic_backend",
        "label": "SIMULATED / EXPERIMENTAL",
    }
    result["uncertainty"] = _uncertainty(src, events, pred, adapt)
    result["recommended_investigation_questions"] = _questions(src, pred, defense, adapt, result["playbook_explanation"])
    if os.getenv("INVESTIGATOR_USE_LLM") == "1":
        result["llm_summary"] = _optional_llm(result)
    return result


def _story(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for i, e in enumerate(events, start=1):
        et = e.get("event_type") or "unknown"
        asset = e.get("asset_id") or "unknown"
        template = STORY_LINES.get(et, "{event} observed on {asset}")
        out.append(
            {
                "step": i,
                "event_id": e.get("id"),
                "event_type": et,
                "asset_id": asset,
                "timestamp": e.get("timestamp"),
                "text": template.format(asset=asset, event=et),
                "kind": "OBSERVED",
                "label": "OBSERVED",
            }
        )
    return out


def _key_evidence(events, detection, graph, pred, defense, adapt) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for ev in detection.get("evidence") or []:
        items.append({"kind": "OBSERVED", "source": "detection", "text": str(ev)})
    if graph.get("current_node"):
        items.append({"kind": "OBSERVED", "source": "attack_graph", "text": f"Current node {graph['current_node']}"})
    if pred.get("predicted_target"):
        items.append(
            {
                "kind": "PREDICTED",
                "source": "prediction",
                "text": f"{pred['predicted_target']} / {pred.get('predicted_action')}",
            }
        )
    if defense.get("recommended_action"):
        items.append(
            {
                "kind": "SIMULATED",
                "source": "defense",
                "text": f"Recommended {defense['recommended_action']}",
            }
        )
    if adapt.get("robustness_class"):
        items.append(
            {
                "kind": "SIMULATED",
                "source": "adaptation",
                "text": f"Robustness {adapt['robustness_class']}",
            }
        )
    last = events[-1] if events else None
    if last:
        items.append(
            {
                "kind": "OBSERVED",
                "source": "event_history",
                "text": f"Last event {last.get('event_type')} on {last.get('asset_id')}",
            }
        )
    return items


def _risk_text(events, band, stage, node, crit, blast_n) -> str:
    types = [e.get("event_type") for e in events]
    parts = [f"Risk is {band} at stage {stage}"]
    if "credential_access" in types and "privilege_escalation" in types:
        parts.append("because credential access and privilege escalation were observed")
        if "lateral_movement" in types:
            parts.append("followed by lateral movement toward a critical asset")
    elif types:
        parts.append("based on observed " + ", ".join(t for t in types if t))
    if node:
        parts.append(f"Current node is {node}")
        if crit:
            parts.append(f"with {crit} criticality")
    if blast_n:
        parts.append(f"Projected blast radius includes {blast_n} asset(s)")
    parts.append("This is a simulated estimate, not scientific certainty.")
    return ". ".join(parts) + "."


def _summary(events, band, stage, node, pred, defense) -> str:
    last = events[-1]
    rec = defense.get("recommended_action") or "none"
    tgt = pred.get("predicted_target") or "none"
    return (
        f"Synthetic incident with {len(events)} observed event(s). "
        f"Stage {stage}, risk {band}, current node {node or 'none'}. "
        f"Last observed event: {last.get('event_type')} on {last.get('asset_id')}. "
        f"Predicted next target {tgt} (PREDICTION — NOT OBSERVED REALITY). "
        f"Recommended simulated defense {rec} is not executed by the investigator."
    )


def _prediction(src, pred, graph, events) -> dict[str, Any]:
    if not pred.get("predicted_target"):
        return dict(EMPTY["prediction_explanation"])
    last = events[-1] if events else {}
    evidence = []
    if graph.get("current_node"):
        evidence.append(f"current attack node {graph['current_node']}")
    if last:
        evidence.append(f"last observed event {last.get('event_type')}")
    evidence.append("attack graph reachability")
    node = next((n for n in (graph.get("nodes") or []) if n.get("id") == pred.get("predicted_target")), None)
    if node and node.get("criticality"):
        evidence.append(f"target criticality {node['criticality']}")
    if (src.get("learning") or {}).get("memory_adjustments"):
        evidence.append("historical prediction outcomes")
    return {
        "predicted_target": pred.get("predicted_target"),
        "predicted_action": pred.get("predicted_action"),
        "confidence": pred.get("confidence") or 0,
        "reason": pred.get("reason") or "",
        "alternatives": pred.get("alternatives") or [],
        "evidence": evidence,
        "explanation": (
            f"The model predicts {pred.get('predicted_target')} / {pred.get('predicted_action')} "
            f"from current node {graph.get('current_node')} after {last.get('event_type')}. "
            f"PREDICTION — NOT OBSERVED REALITY."
        ),
        "label": "PREDICTION — NOT OBSERVED REALITY",
    }


def _defense(defense: dict[str, Any], pred: dict[str, Any]) -> dict[str, Any]:
    rec = defense.get("recommended_action")
    if not rec:
        return dict(EMPTY["defense_explanation"])
    options = list(defense.get("options") or [])
    top = next((o for o in options if o.get("action") == rec), {})
    alts = []
    for o in options:
        if o.get("action") == rec:
            continue
        alts.append(
            {
                "action": o.get("action"),
                "score": o.get("score") or o.get("overall_defense_score"),
                "risk_after": o.get("risk_after"),
                "disruption": o.get("operational_disruption"),
                "why_lower": (
                    f"{o.get('action')} ranked lower (score {o.get('score') or o.get('overall_defense_score')}, "
                    f"disruption {o.get('operational_disruption')})."
                ),
            }
        )
    evidence = [f"recommended {rec}", f"predicted target {pred.get('predicted_target')}"]
    if top.get("risk_before") is not None:
        evidence.append(f"risk {top.get('risk_before')} → {top.get('risk_after')}")
    if top.get("blast_radius_before") is not None:
        evidence.append(f"blast radius {top.get('blast_radius_before')} → {top.get('blast_radius_after')}")
    if top.get("operational_disruption"):
        evidence.append(f"operational disruption {top.get('operational_disruption')}")
    return {
        "recommended_action": rec,
        "score": defense.get("recommended_score") or top.get("score"),
        "risk_before": top.get("risk_before"),
        "risk_after": top.get("risk_after"),
        "blast_radius_before": top.get("blast_radius_before"),
        "blast_radius_after": top.get("blast_radius_after"),
        "operational_disruption": top.get("operational_disruption"),
        "reason": defense.get("recommended_reason") or top.get("reason") or "",
        "alternatives": alts[:4],
        "evidence": evidence,
        "executed": False,
        "real_network_action": False,
        "explanation": (
            f"Recommended {rec} because it reduces simulated risk "
            f"{top.get('risk_before')} → {top.get('risk_after')} for predicted target "
            f"{pred.get('predicted_target')}. The investigator does not execute this defense."
        ),
        "label": "SIMULATED defense projection — not executed",
    }


def _adaptation(adapt: dict[str, Any]) -> dict[str, Any]:
    scenarios = adapt.get("scenarios") or []
    if not adapt.get("defense_action") and not scenarios:
        return dict(EMPTY["adaptation_explanation"])
    high = next((s for s in scenarios if s.get("adaptation_level") == "HIGH"), None) or {}
    alt = high.get("alternate_target") or ((adapt.get("alternate_targets") or [None])[0])
    evidence = [
        f"defense {adapt.get('defense_action')}",
        f"robustness {adapt.get('robustness_class')}",
        f"HIGH outcome {high.get('outcome')}",
    ]
    if alt:
        evidence.append(f"alternate target {alt}")
    expl = (
        f"Under high simulated attacker adaptation, {adapt.get('defense_action')} "
        f"produced outcome {high.get('outcome')}"
        + (f" toward {alt}" if alt else "")
        + f". Robustness is {adapt.get('robustness_class')}. SIMULATED ADAPTATION."
    )
    return {
        "available": True,
        "defense_action": adapt.get("defense_action"),
        "robustness_class": adapt.get("robustness_class"),
        "robustness_score": adapt.get("robustness_score"),
        "adaptation_level": high.get("adaptation_level"),
        "outcome": high.get("outcome"),
        "alternate_target": alt,
        "risk_change": high.get("projected_risk"),
        "explanation": expl,
        "evidence": evidence,
        "label": "SIMULATED ADAPTATION",
        "simulated": True,
    }


def _learning(src: dict[str, Any]) -> dict[str, Any]:
    learn = src.get("learning") or {}
    summary = learn.get("summary") or {}
    recent = [r for r in (learn.get("recent_outcomes") or []) if r.get("outcome") and r.get("outcome") != "UNRESOLVED"]
    openp = learn.get("open_prediction") or src.get("open_prediction")
    adjustments = learn.get("memory_adjustments") or []
    if not recent and not openp and not adjustments:
        return dict(EMPTY["learning_explanation"])
    last = recent[0] if recent else None
    bits = ["SIMULATION / EXPERIMENTAL."]
    if last:
        bits.append(
            f"Previous prediction {last.get('predicted_target')} vs actual {last.get('actual_target')} "
            f"was {last.get('outcome')}."
        )
    if openp and openp.get("outcome") == "UNRESOLVED":
        bits.append(f"Current prediction {openp.get('predicted_target')} remains UNRESOLVED.")
    if adjustments:
        bits.append(
            "Historical adjustments: "
            + ", ".join(f"{a.get('target')} {a.get('historical_adjustment')}" for a in adjustments[:4])
        )
    bits.append("These figures are not production AI accuracy.")
    evidence = []
    if last:
        evidence.append(f"{last.get('prediction_id')} {last.get('outcome')}")
    for a in adjustments[:4]:
        evidence.append(f"{a.get('target')} adj {a.get('historical_adjustment')}")
    return {
        "label": "SIMULATION / EXPERIMENTAL",
        "explanation": " ".join(bits),
        "previous": last,
        "open_prediction": openp,
        "history": recent[:8],
        "adjustments": adjustments,
        "summary": {
            "resolved_predictions": summary.get("resolved_predictions"),
            "overall_accuracy": summary.get("overall_accuracy"),
        },
        "evidence": evidence,
    }


def _playbook(src: dict[str, Any]) -> dict[str, Any]:
    evo = src.get("playbook_evolution") or {}
    current = evo.get("current") or {}
    openp = evo.get("open_proposal")
    if not current and not openp:
        return dict(EMPTY["playbook_explanation"])
    if openp:
        return {
            "label": "EVIDENCE-BACKED PROPOSAL REQUIRING HUMAN APPROVAL.",
            "current_version": openp.get("current_version") or current.get("version"),
            "proposed_version": openp.get("proposed_version"),
            "reason": openp.get("reason"),
            "expected_benefit": openp.get("expected_benefit"),
            "risk": openp.get("risk"),
            "status": openp.get("status"),
            "change_type": openp.get("change_type"),
            "evidence": list(openp.get("supporting_evidence") or []),
            "explanation": f"{openp.get('reason')} EVIDENCE-BACKED PROPOSAL REQUIRING HUMAN APPROVAL.",
            "auto_approved": False,
        }
    return {
        "label": "EVIDENCE-BACKED PROPOSAL REQUIRING HUMAN APPROVAL.",
        "current_version": current.get("version"),
        "proposed_version": None,
        "reason": None,
        "expected_benefit": None,
        "risk": None,
        "status": current.get("status"),
        "evidence": list(current.get("evidence") or []),
        "explanation": (
            f"Active playbook {current.get('label') or current.get('playbook_id')} "
            f"version {current.get('version')}. No open proposal. "
            "EVIDENCE-BACKED PROPOSAL REQUIRING HUMAN APPROVAL."
        ),
        "auto_approved": False,
    }


def _uncertainty(src, events, pred, adapt) -> list[str]:
    items = []
    if len(events) < 3:
        items.append("limited synthetic evidence")
    openp = src.get("open_prediction") or (src.get("learning") or {}).get("open_prediction")
    if openp and openp.get("outcome") == "UNRESOLVED":
        items.append("prediction not yet resolved")
        items.append("Prediction remains unresolved because the predicted target has not yet been observed.")
    summary = ((src.get("learning") or {}).get("summary") or {})
    if not summary.get("resolved_predictions"):
        items.append("insufficient historical incidents")
        items.append("no previous comparable incident")
    if adapt.get("scenarios"):
        items.append("adaptation outcome is simulated")
    if len(pred.get("alternatives") or []) > 1:
        items.append("multiple possible targets")
    conf = pred.get("confidence") or 0
    if events and conf and conf < 70:
        items.append("low confidence evidence")
    if not items:
        items.append("adaptation outcome is simulated")
    return items


def _questions(src, pred, defense, adapt, play_ex) -> list[str]:
    qs = ["Which observed event first increased risk significantly?"]
    graph = src.get("attack_graph") or {}
    if graph.get("current_node"):
        qs.append("Which asset is currently most exposed?")
    if pred.get("predicted_target"):
        qs.append(f"Why was {pred['predicted_target']} selected as the predicted target?")
    if adapt.get("alternate_targets"):
        qs.append("What alternative target was identified?")
        qs.append("What happens under high attacker adaptation?")
    if defense.get("recommended_action"):
        qs.append("Which defense produced the lowest simulated residual risk?")
    learn = src.get("learning") or {}
    if learn.get("recent_outcomes") or (learn.get("summary") or {}).get("resolved_predictions"):
        qs.append("Has this prediction been correct in previous simulations?")
    if play_ex.get("proposed_version"):
        qs.append("Why did the playbook engine propose a change?")
    return qs


def _confidence(events, detection, pred) -> float:
    n = len(events)
    dconf = float(detection.get("confidence") or 0)
    pconf = float(pred.get("confidence") or 0)
    return float(min(92.0, round(12 + 6 * n + 0.15 * dconf + 0.1 * pconf, 1)))


def _optional_llm(structured: dict[str, Any]) -> str | None:
    """Rewrite only. Never used as source of truth. Off unless INVESTIGATOR_USE_LLM=1."""
    try:
        from app.ai.investigator import _gemini_answer
    except Exception:
        return None
    prompt = (
        "Rewrite this RansomGuard-X investigation as a short analyst briefing. "
        "Use ONLY the provided summary. Do not invent events or execute containment.\n"
        f"{structured.get('incident_summary')}\nUncertainty: {structured.get('uncertainty')}"
    )
    return _gemini_answer(prompt)
