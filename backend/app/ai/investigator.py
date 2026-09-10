"""Evidence-grounded investigator. Gemini optional; deterministic fallback always works."""
from __future__ import annotations

import os
from typing import Any


def _gemini_answer(prompt: str) -> str | None:
    key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not key:
        return None
    try:
        import httpx

        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            "gemini-2.0-flash:generateContent"
        )
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.2, "maxOutputTokens": 800},
        }
        r = httpx.post(url, params={"key": key}, json=payload, timeout=12.0)
        r.raise_for_status()
        data = r.json()
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        return text
    except Exception:
        return None


def investigate(question: str, state: dict[str, Any]) -> dict[str, Any]:
    grounded = _fallback(question, state)
    prompt = _prompt(question, state)
    llm = _gemini_answer(prompt)
    return {
        "question": question,
        "answer": llm or grounded["answer"],
        "source": "gemini" if llm else "deterministic_fallback",
        "evidence": grounded["evidence"],
        "invented_telemetry": False,
        "simulated": True,
    }


def _prompt(question: str, state: dict[str, Any]) -> str:
    evidence = {
        "incident_id": state.get("incident_id"),
        "risk_score": state.get("risk_score"),
        "ransomware_confidence": state.get("ransomware_confidence"),
        "current_stage": state.get("current_stage"),
        "attack_intent": state.get("attack_intent"),
        "predictions": state.get("predictions", [])[:3],
        "recommended_defense": state.get("recommended_defense"),
        "containment": state.get("containment"),
        "defense_regret": state.get("defense_regret"),
        "missed_impact": state.get("missed_impact"),
        "events": [
            {"time": e.get("timestamp"), "type": e.get("event_type"), "asset": e.get("asset_id")}
            for e in state.get("events", [])
        ],
    }
    return (
        "You are RansomGuard-X investigator for a SAFE simulated SOC demo. "
        "Use ONLY the JSON evidence. Never invent telemetry. Label estimates as simulated.\n"
        f"EVIDENCE:\n{evidence}\n\nQUESTION:\n{question}"
    )


def _fallback(question: str, state: dict[str, Any]) -> dict[str, Any]:
    q = question.lower()
    events = state.get("events", [])
    types = [e.get("event_type") for e in events]
    intent = (state.get("attack_intent") or {}).get("current_intent", "NONE")
    rec = (state.get("recommended_defense") or {}).get("action", "NO_ACTION")
    pred = (state.get("predictions") or [{}])
    target = pred[0].get("predicted_target", "unknown") if pred else "unknown"
    regret = state.get("defense_regret") or 0
    missed = state.get("missed_impact") or {}
    evidence = [
        f"Stage={state.get('current_stage')}",
        f"Risk={state.get('risk_score')}",
        f"Ransomware confidence={state.get('ransomware_confidence')}",
        f"Events={types}",
        f"Intent={intent}",
    ]

    if "ransomware" in q or "classified" in q:
        answer = (
            f"Classification uses correlated synthetic telemetry, not extensions alone. "
            f"Observed {types}. Intent engine reports {intent} with ransomware confidence "
            f"{state.get('ransomware_confidence')}. This is a simulated estimate."
        )
    elif "target" in q or "next" in q:
        answer = (
            f"Predicted next target is {target} from graph reachability, criticality, and stage "
            f"{state.get('current_stage')}. Confidence range is shown in the prediction panel. Simulated."
        )
    elif "isolat" in q:
        answer = (
            f"Isolation is recommended as {rec} because it stops LAB-PC-21 as the current foothold "
            f"while avoiding emergency server shutdown. Residual risk and downtime are simulated scores."
        )
    elif "revok" in q and "earlier" in q:
        answer = (
            "Revoking credentials earlier (around 10:03) reduces simulated lateral authentication. "
            "Counterfactual engine estimates fewer affected systems versus waiting until backup access."
        )
    elif "missed" in q or "intervention" in q:
        answer = (
            f"Largest missed intervention is the BEST window at 10:03 (credential access). "
            f"Avoidable systems={missed.get('avoidable_systems', 'n/a')}, "
            f"avoidable exposure={missed.get('avoidable_exposure', 'n/a')} (SIMULATED ESTIMATE)."
        )
    elif "robust" in q:
        rob = state.get("robustness") or {}
        answer = (
            f"Robustness verdict is {rob.get('verdict', 'not yet tested')}. "
            f"Defense ranking is re-scored at 30/50/70/90% attacker adaptation. {rob.get('note', '')}"
        )
    elif "report" in q:
        answer = _report(state)
    else:
        answer = (
            f"Current simulated incident {state.get('incident_id')} is at stage "
            f"{state.get('current_stage')} with risk {state.get('risk_score')}. "
            f"Recommended action {rec}. I can only reason over current incident state."
        )
    return {"answer": answer, "evidence": evidence}


def _report(state: dict[str, Any]) -> str:
    return (
        f"SIMULATED INCIDENT REPORT\n"
        f"Organization: RMK College Cyber Defense Center (fictional)\n"
        f"Incident: {state.get('incident_id')}\n"
        f"Stage: {state.get('current_stage')}\n"
        f"Risk: {state.get('risk_score')} | Ransomware confidence: {state.get('ransomware_confidence')}\n"
        f"Predicted target: {(state.get('predictions') or [{}])[0].get('predicted_target') if state.get('predictions') else 'n/a'}\n"
        f"Recommended defense: {(state.get('recommended_defense') or {}).get('action')}\n"
        f"Approval: {state.get('approval')}\n"
        f"Containment: {bool((state.get('containment') or {}).get('contained'))}\n"
        f"Defense regret: {state.get('defense_regret')}\n"
        f"All figures are experimental simulation outputs."
    )
