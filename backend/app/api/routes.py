"""HTTP and WebSocket API. Frontend never invents security state."""
from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.audit.engine import serialize_logs, verify_chain
from app.database import get_db
from app.learning.engine import list_memory
from app.models import Asset, Incident, SecurityEvent
from app.investigator import engine as investigator_engine
from app.playbook import engine as playbook_evo
from app.playbooks.engine import list_playbooks, load_yaml, resolve_proposal
from app.schemas import (
    CounterfactualRequest,
    DefenseApproveRequest,
    DefenseRejectRequest,
    DefenseReviewRequest,
    DemoControlRequest,
    EvaluationRunRequest,
    InvestigateRequest,
    PlaybookApproveRequest,
    PlaybookChangeGovernanceRequest,
    ReplayRequest,
    RobustnessRequest,
    SimulationStartRequest,
)
from app.simulation.engine import engine
from app.ws import hub

router = APIRouter()
ROOT = Path(__file__).resolve().parents[3]


@router.get("/health")
def health():
    return {"ok": True, "service": "RansomGuard-X", "simulated": True}


@router.get("/simulation/state")
def get_state():
    return {"ok": True, "simulated": True, "state": engine.snapshot()}


@router.get("/detection/current")
def detection_current():
    state = engine.snapshot()
    payload = state.get("detection") or {}
    return {
        "ok": True,
        "simulated": True,
        "classification": payload.get("classification", "NORMAL"),
        "risk_score": payload.get("risk_score", 0),
        "risk_level": payload.get("risk_level", "LOW"),
        "attack_stage": payload.get("attack_stage", "NORMAL"),
        "intent": payload.get("intent", "No malicious progression indicated"),
        "confidence": payload.get("confidence", 0),
        "evidence": payload.get("evidence", []),
        "reason": payload.get("reason", ""),
        "label": payload.get("label", "SIMULATED / EXPERIMENTAL"),
    }


@router.post("/simulation/start")
async def start(req: SimulationStartRequest):
    state = await engine.start(req.scenario_id)
    return {"ok": True, "simulated": True, "state": state}


@router.post("/simulation/next-event")
async def next_event():
    state = await engine.next_event()
    return {"ok": True, "simulated": True, "state": state}


@router.post("/simulation/reset")
async def reset():
    state = await engine.reset()
    return {"ok": True, "simulated": True, "state": state}


@router.get("/forks")
def get_forks_alias():
    """Alias for GET /api/simulation/forks. Read-only."""
    return simulation_forks()


@router.get("/simulation/forks")
def simulation_forks():
    """Read-only defensive futures. Does not mutate live simulation state."""
    from app.simulation import fork_engine as forks_mod

    snap = engine.snapshot()
    payload = forks_mod.build(snap)
    return {"ok": True, **payload}


@router.get("/adaptation")
def get_adaptation():
    """Read-only adaptive-attacker robustness. Does not mutate live state."""
    from app.adaptation import engine as adaptation_engine

    snap = engine.snapshot()
    payload = adaptation_engine.analyze(snap)
    return {"ok": True, **payload}


@router.get("/simulation/scenarios")
def scenarios():
    return {"ok": True, "scenarios": engine.scenarios()}


@router.get("/incidents")
def incidents(db: Session = Depends(get_db)):
    rows = db.query(Incident).order_by(Incident.timestamp.desc()).all()
    return {
        "ok": True,
        "incidents": [
            {
                "id": r.id,
                "timestamp": r.timestamp.isoformat() if r.timestamp else "",
                "title": r.title,
                "risk_score": r.risk_score,
                "ransomware_confidence": r.ransomware_confidence,
                "attack_stage": r.attack_stage,
                "affected_assets": json.loads(r.affected_assets or "[]"),
                "predicted_target": r.predicted_target,
                "prediction_confidence": r.prediction_confidence,
                "recommended_action": r.recommended_action,
                "approval_status": r.approval_status,
                "actual_outcome": json.loads(r.actual_outcome or "{}"),
                "counterfactual_results": json.loads(r.counterfactual_results or "[]"),
                "defense_regret": r.defense_regret,
                "intervention_time": r.intervention_time,
                "status": r.status,
            }
            for r in rows
        ],
    }


@router.get("/incidents/{incident_id}")
def incident_detail(incident_id: str, db: Session = Depends(get_db)):
    r = db.query(Incident).filter(Incident.id == incident_id).first()
    if not r:
        return {"ok": False, "error": "Incident not found"}
    return {
        "ok": True,
        "incident": {
            "id": r.id,
            "timestamp": r.timestamp.isoformat() if r.timestamp else "",
            "title": r.title,
            "risk_score": r.risk_score,
            "ransomware_confidence": r.ransomware_confidence,
            "attack_stage": r.attack_stage,
            "affected_assets": json.loads(r.affected_assets or "[]"),
            "predicted_target": r.predicted_target,
            "prediction_confidence": r.prediction_confidence,
            "recommended_action": r.recommended_action,
            "approval_status": r.approval_status,
            "actual_outcome": json.loads(r.actual_outcome or "{}"),
            "counterfactual_results": json.loads(r.counterfactual_results or "[]"),
            "defense_regret": r.defense_regret,
            "intervention_time": r.intervention_time,
            "status": r.status,
        },
    }


@router.get("/events")
def events(db: Session = Depends(get_db)):
    live = engine.snapshot().get("events", [])
    live_id = engine.snapshot().get("incident_id", "")
    rows = (
        db.query(SecurityEvent)
        .filter(SecurityEvent.incident_id == live_id)
        .order_by(SecurityEvent.timestamp.asc())
        .all()
    )
    stored = [
        {
            "id": e.id,
            "incident_id": e.incident_id,
            "timestamp": e.timestamp,
            "event_type": e.event_type,
            "asset_id": e.asset_id,
            "mitre": e.mitre,
            "payload": json.loads(e.payload or "{}"),
        }
        for e in rows
    ]
    return {"ok": True, "events": live, "live": live, "stored": stored, "simulated": True}


@router.get("/assets")
def assets(db: Session = Depends(get_db)):
    rows = db.query(Asset).all()
    return {
        "ok": True,
        "assets": [
            {
                "id": a.id,
                "name": a.name,
                "type": a.type,
                "criticality": a.criticality,
                "owner": a.owner,
                "segment": a.segment,
                "os": a.os,
                "current_state": a.current_state,
                "risk_score": a.risk_score,
            }
            for a in rows
        ],
        "disclaimer": "Fictional assets for RMK College Cyber Defense Center demo.",
    }


@router.get("/attack-graph")
def attack_graph():
    state = engine.snapshot()
    graph = state.get("attack_graph") or {}
    return {
        "ok": True,
        "simulated": True,
        "nodes": graph.get("nodes") or [],
        "edges": graph.get("edges") or [],
        "attack_path": graph.get("attack_path") or state.get("attack_path") or [],
        "current_node": graph.get("current_node"),
        "current_stage": graph.get("current_stage") or state.get("current_stage"),
        "graph_risk": graph.get("graph_risk", 0),
        "graph": graph,
        "label": graph.get("label", "SIMULATED attack graph"),
    }


@router.get("/predictions")
def predictions():
    state = engine.snapshot()
    pred = state.get("prediction") or {}
    return {
        "ok": True,
        "simulated": True,
        "predicted_target": pred.get("predicted_target"),
        "predicted_action": pred.get("predicted_action"),
        "confidence": pred.get("confidence", 0),
        "reason": pred.get("reason", ""),
        "evidence": pred.get("evidence") or [],
        "alternatives": pred.get("alternatives") or [],
        "current_node": pred.get("current_node"),
        "current_stage": pred.get("current_stage") or state.get("current_stage"),
        "history": state.get("prediction_history") or [],
        "label": pred.get("label", "SIMULATED prediction"),
        "predictions": state.get("predictions") or [],
    }


@router.get("/defense/recommend")
def get_defense_recommend():
    state = engine.snapshot()
    d = state.get("defense") or {}
    return {
        "ok": True,
        "simulated": True,
        "real_network_action": False,
        "recommended_action": d.get("recommended_action"),
        "recommended_reason": d.get("recommended_reason", ""),
        "recommended_score": d.get("recommended_score", 0),
        "options": d.get("options") or [],
        "forks": d.get("forks") or [],
        "current_node": d.get("current_node"),
        "predicted_target": d.get("predicted_target"),
        "pending_approval": state.get("pending_approval"),
        "approval_status": state.get("approval_status"),
        "selected_action": state.get("selected_action"),
        "containment_status": state.get("containment_status"),
        "label": d.get("label", "SIMULATED defense projection"),
    }


@router.get("/defense/status")
def defense_status():
    state = engine.snapshot()
    pending = state.get("approval_status") == "PENDING_REVIEW"
    return {
        "ok": True,
        "simulated": True,
        "pending_approval": pending,
        "approval_status": state.get("approval_status") or "NONE",
        "selected_action": state.get("selected_action"),
        "approved_by": state.get("approved_by"),
        "approval_timestamp": state.get("approval_timestamp"),
        "containment_status": state.get("containment_status") or "NOT_APPLIED",
        "containment_verify_reason": state.get("containment_verify_reason"),
    }


@router.post("/defense/recommend")
async def recommend():
    state = await engine.recommend()
    return {"ok": True, "state": state}


@router.post("/defense/review")
async def defense_review(req: DefenseReviewRequest | None = None):
    """Queue selected defense for human approval. Does not contain."""
    req = req or DefenseReviewRequest()
    try:
        state = await engine.prepare_review(req.action)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    preview = state.get("approval_preview") or {}
    return {
        "ok": True,
        "executed": False,
        "simulated": True,
        "real_network_action": False,
        "action": preview.get("action") or state.get("selected_action"),
        "approval_status": state.get("approval_status"),
        "containment_status": state.get("containment_status"),
        "projected_risk": [preview.get("projected_risk_before"), preview.get("projected_risk_after")],
        "projected_blast_radius": [
            preview.get("projected_blast_radius_before"),
            preview.get("projected_blast_radius_after"),
        ],
        "operational_disruption": preview.get("operational_disruption"),
        "reason": preview.get("reason"),
        "state": state,
    }


@router.post("/defense/approve")
async def approve(req: DefenseApproveRequest):
    snap = engine.snapshot()
    pending = snap.get("approval_status") == "PENDING_REVIEW"
    actor = req.approved_by or req.approver
    if pending and req.decision != "REJECT":
        try:
            state = await engine.approve_gated(req.action, actor, req.reason)
        except PermissionError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return {"ok": True, "state": state}
    if req.approved_by and not pending:
        raise HTTPException(status_code=400, detail="No defense action is pending human review.")
    if pending and req.decision == "REJECT":
        try:
            state = await engine.reject_gated(req.action, actor, req.reason)
        except PermissionError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return {"ok": True, "state": state}
    state = await engine.approve(req.action, req.decision, req.approver, req.reason, req.modified_action)
    return {"ok": True, "state": state}


@router.post("/defense/reject")
async def defense_reject(req: DefenseRejectRequest):
    try:
        state = await engine.reject_gated(req.action, req.rejected_by, req.reason)
    except PermissionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"ok": True, "state": state}


@router.post("/defense/simulate")
async def simulate(req: DefenseApproveRequest):
    state = await engine.simulate_defense(req.modified_action or req.action)
    return {"ok": True, "state": state}


@router.post("/replay")
def replay(req: ReplayRequest):
    state = engine.replay_control(req.command, req.speed, req.index)
    return {"ok": True, "state": state}


@router.post("/counterfactual/run")
async def counterfactual(req: CounterfactualRequest):
    state = await engine.run_counterfactual(req.action, req.intervention_index)
    return {"ok": True, "state": state, "result": state.get("last_counterfactual")}


@router.post("/robustness/test")
async def robustness(req: RobustnessRequest):
    state = await engine.robustness(req.action, req.rates)
    return {"ok": True, "state": state}


@router.post("/robustness/drop-event")
def drop_event(payload: dict):
    state = engine.robustness_drop_event(payload.get("event_type", "credential_access"))
    return {"ok": True, "state": state}


@router.post("/intervention")
def set_intervention(payload: dict):
    state = engine.set_intervention(int(payload.get("index", 3)))
    return {"ok": True, "state": state}


@router.post("/playbook/propose")
def propose_playbook():
    state = engine.snapshot()
    return {"ok": True, "playbook": state.get("playbook")}


@router.post("/playbook/approve")
def approve_playbook(req: PlaybookApproveRequest, db: Session = Depends(get_db)):
    result = resolve_proposal(db, req.proposal_id, req.decision, req.reviewer)
    engine.state["playbook"] = {**(engine.state.get("playbook") or {}), **result}
    engine._audit("playbook_decision", result, actor=req.reviewer)
    return {"ok": True, "result": result, "state": engine.snapshot()}


@router.get("/playbooks")
def get_playbooks(db: Session = Depends(get_db)):
    evo = playbook_evo.snapshot()
    return {
        "ok": True,
        "simulated": True,
        "playbooks": list_playbooks(db),
        "raw_yaml": load_yaml(),
        "evolution": evo,
        "versions": evo.get("versions") or [],
        "current": evo.get("current"),
        "proposals": evo.get("proposals") or [],
        "note": "The system proposes evidence-backed playbook improvements for human approval.",
    }


@router.get("/playbooks/current")
def get_playbook_current():
    cur = playbook_evo.current()
    return {"ok": True, "simulated": True, "playbook": cur, "yaml": cur.get("yaml")}


@router.get("/playbooks/proposals")
def get_playbook_proposals():
    return {
        "ok": True,
        "simulated": True,
        "proposals": playbook_evo.proposals(),
        "auto_approved": False,
        "note": "Proposals never auto-apply. Human review is required.",
    }


@router.get("/playbooks/yaml")
def playbook_yaml():
    rules = (ROOT / "config" / "detection_rules.yaml").read_text(encoding="utf-8")
    pbs = load_yaml()
    assets = (ROOT / "config" / "assets.yaml").read_text(encoding="utf-8")
    evo = playbook_evo.current()
    return {
        "ok": True,
        "playbooks": pbs,
        "detection_rules": rules,
        "assets": assets,
        "evolution_yaml": evo.get("yaml"),
        "note": "YAML is documentation only and is not executed as code.",
    }


@router.get("/playbooks/{playbook_id}")
def get_playbook_detail(playbook_id: str, db: Session = Depends(get_db)):
    if playbook_id.upper().replace("-", "_") in (
        playbook_evo.PLAYBOOK_ID,
        playbook_evo.PLAYBOOK_ID.replace("_", "-"),
        f"{playbook_evo.PLAYBOOK_ID}_V1",
    ) or playbook_id.upper().startswith("RANSOMWARE_CONTAINMENT"):
        cur = playbook_evo.current()
        vers = playbook_evo.versions()
        return {
            "ok": True,
            "simulated": True,
            "playbook_id": playbook_evo.PLAYBOOK_ID,
            "current": cur,
            "versions": vers,
            "proposals": playbook_evo.proposals(),
            "yaml": cur.get("yaml"),
        }
    rows = [p for p in list_playbooks(db) if str(p.get("id") or p.get("playbook_id")) == playbook_id]
    if not rows:
        raise HTTPException(status_code=404, detail="Unknown playbook")
    return {"ok": True, "playbook": rows[0], "playbooks": rows}


@router.post("/playbooks/proposals/{change_id}/approve")
async def approve_playbook_change(change_id: str, req: PlaybookChangeGovernanceRequest | None = None):
    body = req or PlaybookChangeGovernanceRequest()
    try:
        result = await engine.approve_playbook_change(change_id, body.actor, body.reason)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Unknown change {change_id}")
    except PermissionError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    return {
        "ok": True,
        "simulated": True,
        "real_network_action": False,
        "note": "Approval changes only synthetic playbook configuration.",
        **result,
        "state": engine.snapshot(),
    }


@router.post("/playbooks/proposals/{change_id}/reject")
async def reject_playbook_change(change_id: str, req: PlaybookChangeGovernanceRequest | None = None):
    body = req or PlaybookChangeGovernanceRequest()
    try:
        result = await engine.reject_playbook_change(change_id, body.actor, body.reason)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Unknown change {change_id}")
    except PermissionError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    return {
        "ok": True,
        "simulated": True,
        "real_network_action": False,
        **result,
        "state": engine.snapshot(),
    }


@router.get("/investigator")
def get_investigator():
    payload = investigator_engine.analyze(engine.snapshot())
    return {"ok": True, "simulated": True, "real_network_action": False, **payload}


@router.get("/investigator/story")
def get_investigator_story():
    payload = investigator_engine.analyze(engine.snapshot())
    return {
        "ok": True,
        "simulated": True,
        "attack_story": payload.get("attack_story") or [],
        "incident_summary": payload.get("incident_summary"),
    }


@router.get("/investigator/evidence")
def get_investigator_evidence():
    payload = investigator_engine.analyze(engine.snapshot())
    return {
        "ok": True,
        "simulated": True,
        "key_evidence": payload.get("key_evidence") or [],
        "uncertainty": payload.get("uncertainty") or [],
    }


@router.post("/ai/investigate")
def ai_investigate(req: InvestigateRequest):
    return {"ok": True, **engine.investigate(req.question)}


@router.get("/evaluation/scenarios")
def evaluation_scenarios():
    from app.evaluation import engine as eval_engine

    return {"ok": True, "synthetic": True, "scenarios": eval_engine.list_eval_scenarios()}


@router.get("/evaluation/report")
def evaluation_report():
    from app.evaluation import engine as eval_engine

    report = eval_engine.current_report()
    return {
        "ok": True,
        "synthetic": True,
        "real_network_action": False,
        "report": report,
        "history": eval_engine.history(),
    }


@router.post("/evaluation/run")
async def run_evaluation(req: EvaluationRunRequest | None = None):
    from app.evaluation import engine as eval_engine

    body = req or EvaluationRunRequest()
    try:
        report = await eval_engine.run(body.scenario_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    await engine.broadcast("evaluation")
    return {"ok": True, "real_network_action": False, **report}


@router.post("/evaluation/reset")
async def reset_evaluation():
    from app.evaluation import engine as eval_engine

    snap = eval_engine.reset_evaluation()
    await engine.broadcast("evaluation")
    return {"ok": True, "synthetic": True, **snap}


@router.get("/evaluation")
def get_evaluation():
    from app.evaluation import engine as eval_engine
    from app.evaluation.models import LIMITATIONS

    live = engine.evaluation()
    report = eval_engine.current_report()
    payload = {"ok": True, **live, "synthetic": True, "real_network_action": False, "limitations": list(LIMITATIONS)}
    if report:
        payload["evaluation_id"] = report["evaluation_id"]
        payload["timestamp"] = report["timestamp"]
        payload["scenarios"] = report["scenarios"]
        payload["detection_metrics"] = report["detection_metrics"]
        payload["prediction_metrics"] = report["prediction_metrics"]
        payload["defense_metrics"] = report["defense_metrics"]
        payload["adaptation_metrics"] = report["adaptation_metrics"]
        payload["timing_metrics"] = report["timing_metrics"]
        payload["false_positive_metrics"] = report["false_positive_metrics"]
        payload["baseline_comparison"] = report["baseline_comparison"]
        payload["closed_loop_metrics"] = report["closed_loop_metrics"]
        payload["report"] = report
        payload["label"] = report.get("label") or live.get("label")
    else:
        payload["evaluation_id"] = None
        payload["scenarios"] = []
        payload["detection_metrics"] = None
        payload["prediction_metrics"] = None
        payload["defense_metrics"] = None
        payload["adaptation_metrics"] = None
        payload["timing_metrics"] = None
        payload["false_positive_metrics"] = None
        payload["baseline_comparison"] = None
        payload["closed_loop_metrics"] = None
        payload["report"] = None
    return payload


@router.get("/memory")
def memory(db: Session = Depends(get_db)):
    return {"ok": True, "memory": list_memory(db)}


@router.get("/learning/summary")
def learning_summary():
    from app.learning import engine as learning_engine

    state = engine.snapshot()
    payload = learning_engine.summarize(state.get("open_prediction"), state.get("prediction_outcomes") or [])
    return {"ok": True, **payload}


@router.get("/learning/history")
def learning_history():
    from app.learning import engine as learning_engine

    state = engine.snapshot()
    current = list(state.get("prediction_outcomes") or [])
    openp = state.get("open_prediction")
    history = current + ([openp] if openp else [])
    return {
        "ok": True,
        "simulated": True,
        "label": "SIMULATION / EXPERIMENTAL",
        "history": history,
        "persistent": learning_engine.summarize()["recent_outcomes"],
        "open_prediction": openp,
    }


@router.get("/learning/defense-memory")
def learning_defense_memory():
    from app.learning import engine as learning_engine

    return {
        "ok": True,
        "simulated": True,
        "label": "SIMULATION / EXPERIMENTAL",
        "defense_memory": learning_engine.defense_memory_list(),
    }


@router.get("/audit")
def audit(db: Session = Depends(get_db)):
    return {"ok": True, "logs": serialize_logs(db), "integrity": verify_chain(db)}


@router.get("/history/metrics")
def history_metrics(db: Session = Depends(get_db)):
    rows = db.query(Incident).all()
    return {
        "ok": True,
        "label": "SIMULATED / EXPERIMENTAL",
        "defense_effectiveness": [{"id": r.id, "value": max(0, 100 - r.defense_regret)} for r in rows],
        "propagation_reduction": [{"id": r.id, "value": 100 - min(100, r.risk_score * 0.4)} for r in rows],
        "false_positives": [{"name": "Rule-only", "value": 27}, {"name": "RansomGuard-X", "value": 8}],
        "mttd": [{"id": r.id, "minutes": 2 if r.risk_score > 50 else 4} for r in rows],
        "mttr": [{"id": r.id, "minutes": 6 if r.approval_status == "approved" else 18} for r in rows],
        "recommendation_improvement": [
            {"id": "INC-001", "value": 62},
            {"id": "INC-002", "value": 74},
            {"id": "INC-003", "value": 81},
        ],
    }


@router.post("/demo")
async def demo(req: DemoControlRequest):
    state = await engine.demo(req.command)
    return {"ok": True, "state": state}


@router.websocket("/ws/events")
async def ws_events(ws: WebSocket):
    await hub.connect(ws)
    await ws.send_json({"type": "hello", "state": engine.snapshot()})
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        hub.disconnect(ws)
