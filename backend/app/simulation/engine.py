"""Authoritative simulation state-transition engine."""
from __future__ import annotations

import asyncio
import copy
import json
from datetime import datetime
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.adaptation import engine as adaptation
from app.ai.investigator import investigate
from app.audit import engine as audit
from app.counterfactual import engine as cf
from app.database import SessionLocal
from app.defense import engine as defense
from app.detection import engine as detection
from app.evaluation import engine as evaluation
from app.graph import engine as graph_engine
from app.investigator import engine as investigator_engine
from app.attack_graph.engine import build as build_attack_graph
from app.intent import engine as intent_engine
from app.intervention import engine as intervention
from app.learning import engine as learning
from app.models import Decision, DefenseAction, Incident, SecurityEvent
from app.playbook import engine as playbook_evo
from app.playbooks import engine as playbooks
from app.prediction import engine as prediction
from app.simulation.events import SCENARIOS, scenario_catalog
from app.simulation import fork_engine
from app.ws import hub

REPLAY_STAGES = [
    "Initial Access",
    "Credential Access",
    "Privilege Escalation",
    "Lateral Movement",
    "File Server Access",
    "Backup Access",
    "Ransomware Impact",
]


def _empty_state() -> dict[str, Any]:
    detection = {
        "classification": "NORMAL",
        "risk_score": 0,
        "risk_level": "LOW",
        "attack_stage": "NORMAL",
        "intent": "No malicious progression indicated",
        "confidence": 6.0,
        "evidence": [],
        "reason": "No behavioral events observed.",
        "label": "SIMULATED / EXPERIMENTAL",
        "simulated": True,
    }
    return {
        "scenario_id": "SCN-001",
        "incident_id": "INC-LIVE",
        "current_event_index": 0,
        "events": [],
        "current_stage": "NORMAL",
        "risk_score": 0,
        "risk_band": "LOW",
        "ransomware_confidence": 0,
        "attack_intent": None,
        "attack_graph": build_attack_graph([], detection),
        "predictions": [],
        "prediction": {
            "predicted_target": None,
            "predicted_action": None,
            "confidence": 0,
            "reason": "",
            "evidence": [],
            "alternatives": [],
            "current_node": None,
            "current_stage": "NORMAL",
            "simulated": True,
        },
        "open_prediction": None,
        "prediction_outcomes": [],
        "prediction_history": [],
        "blast_radius": {},
        "defense_options": [],
        "recommended_defense": None,
        "defense": {
            "recommended_action": None,
            "recommended_reason": "",
            "recommended_score": 0,
            "options": [],
            "forks": [],
            "current_node": None,
            "predicted_target": None,
            "simulated": True,
            "real_network_action": False,
        },
        "pending_approval": None,
        "approval_status": "NONE",
        "selected_action": None,
        "approved_by": None,
        "approval_timestamp": None,
        "containment_status": "NOT_APPLIED",
        "approval": None,
        "containment": None,
        "intervention_window": {},
        "attack_forks": {
            "current_state": {
                "risk": 0,
                "current_node": None,
                "predicted_target": None,
                "attack_stage": "NORMAL",
                "blast_radius": 0,
            },
            "forks": [],
            "best_fork": None,
            "simulated": True,
        },
        "alternate_realities": {},
        "adaptive_paths": {},
        "robustness": {},
        "adaptation": {
            "defense_action": None,
            "original_target": None,
            "protected_target": None,
            "robustness_score": 0,
            "robustness_class": "UNCERTAIN",
            "scenarios": [],
            "alternate_targets": [],
            "comparisons": [],
            "summary": "",
            "simulated": True,
        },
        "missed_impact": {},
        "defense_regret": 0,
        "defense_regret_detail": {},
        "incident_replay": {"index": 0, "playing": False, "speed": 1.0, "stages": REPLAY_STAGES},
        "learning": {},
        "playbook": {},
        "playbook_evolution": {},
        "audit_log": [],
        "loop_stage": "OBSERVE",
        "demo": {"running": False, "paused": False, "elapsed": 0, "phase": "idle"},
        "connection": "ok",
        "simulated": True,
        "organization": "RMK College Cyber Defense Center",
        "disclaimer": "Fictional organization. All attacks and defenses are simulated.",
        "mitre": {},
        "time_machine": {},
        "false_positive_context": {},
        "uncertainty": {},
        "prediction_vs_reality": {},
        "what": {
            "happening": "Environment is quiet.",
            "going": "No predicted movement.",
            "should_do": "Continue observation.",
            "if_not": "No simulated impact yet.",
        },
        "assets_summary": {
            "protected": 8,
            "at_risk": 0,
            "active_incidents": 0,
            "threat_level": "LOW",
        },
        "attack_path": [],
        "scenario_path": ["LAB-PC-21", "student.kumar", "FAC-PC-07", "FILE-SRV-01", "BACKUP-SRV-01"],
        "safe_mode": True,
        "detection": detection,
    }


class SimulationEngine:
    def __init__(self, silent: bool = False) -> None:
        self.state = _empty_state()
        self._demo_task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()
        self._silent = silent

    def snapshot(self) -> dict[str, Any]:
        snap = copy.deepcopy(self.state)
        snap["playbook_evolution"] = playbook_evo.snapshot()
        if self._silent:
            snap["investigator"] = {"incident_summary": "Evaluation runner — explanation omitted"}
        else:
            snap["investigator"] = investigator_engine.analyze(snap)
            snap["evaluation"] = evaluation.public_snapshot()
        return snap

    def _db(self) -> Session:
        return SessionLocal()

    def _persist_event(self, ev: dict[str, Any]) -> None:
        if self._silent:
            return
        db = self._db()
        try:
            db_id = f"{self.state['incident_id']}:{ev['id']}"
            if db.query(SecurityEvent).filter(SecurityEvent.id == db_id).first():
                return
            db.add(
                SecurityEvent(
                    id=db_id,
                    incident_id=self.state["incident_id"],
                    timestamp=ev["timestamp"],
                    event_type=ev["event_type"],
                    asset_id=ev["asset_id"],
                    payload=json.dumps(ev),
                    mitre=ev.get("mitre", ""),
                    simulated=1,
                )
            )
            db.commit()
        finally:
            db.close()

    def _clear_live_events(self) -> None:
        if self._silent:
            return
        db = self._db()
        try:
            db.query(SecurityEvent).filter(SecurityEvent.incident_id.like("INC-LIVE%")).delete(
                synchronize_session=False
            )
            db.commit()
        finally:
            db.close()

    def _ensure_incident_row(self) -> None:
        if self._silent:
            return
        db = self._db()
        try:
            row = db.query(Incident).filter(Incident.id == self.state["incident_id"]).first()
            if not row:
                db.add(
                    Incident(
                        id=self.state["incident_id"],
                        title="Live ransomware-path simulation",
                        scenario_id=self.state["scenario_id"],
                        status="open",
                    )
                )
                db.commit()
        finally:
            db.close()

    def _save_incident(self) -> None:
        if self._silent:
            return
        db = self._db()
        try:
            row = db.query(Incident).filter(Incident.id == self.state["incident_id"]).first()
            if not row:
                return
            row.risk_score = self.state["risk_score"]
            row.ransomware_confidence = self.state["ransomware_confidence"]
            row.attack_stage = self.state["current_stage"]
            row.affected_assets = json.dumps(self.state.get("blast_radius", {}).get("current_affected", []))
            preds = self.state.get("predictions") or []
            row.predicted_target = preds[0]["predicted_target"] if preds else ""
            row.prediction_confidence = preds[0]["confidence"] if preds else 0
            rec = self.state.get("recommended_defense") or {}
            row.recommended_action = rec.get("action", "NO_ACTION")
            appr = self.state.get("approval") or {}
            row.approval_status = appr.get("decision", "pending")
            row.actual_outcome = json.dumps(self.state.get("containment") or {})
            row.counterfactual_results = json.dumps(self.state.get("counterfactuals") or [])
            row.defense_regret = float(self.state.get("defense_regret") or 0)
            iw = self.state.get("intervention_window") or {}
            row.intervention_time = (iw.get("last_safe_intervention") or {}).get("time", "")
            row.status = "contained" if (self.state.get("containment") or {}).get("contained") else "open"
            db.commit()
        finally:
            db.close()

    def _audit(self, event_type: str, payload: dict[str, Any], actor: str = "system") -> None:
        if self._silent:
            return
        db = self._db()
        try:
            audit.record(db, event_type, payload, self.state.get("incident_id", ""), actor)
            self.state["audit_log"] = audit.serialize_logs(db)
        finally:
            db.close()

    def _loop_stage(self) -> str:
        if self.state.get("playbook", {}).get("proposed") or self.state.get("learning", {}).get("quality"):
            return "LEARN"
        if self.state.get("defense_regret_detail"):
            return "COMPARE"
        if self.state.get("counterfactuals"):
            return "REPLAY"
        if (self.state.get("containment") or {}).get("contained"):
            return "DEFEND"
        if self.state.get("approval"):
            return "DECIDE"
        if self.state.get("predictions"):
            return "PREDICT"
        if self.state.get("attack_intent"):
            return "UNDERSTAND"
        if self.state.get("events"):
            return "DETECT"
        return "OBSERVE"

    def _what(self) -> dict[str, str]:
        intent = (self.state.get("attack_intent") or {}).get("current_intent", "NONE")
        pred = (self.state.get("predictions") or [{}])
        target = pred[0].get("predicted_target", "none") if pred else "none"
        rec = (self.state.get("recommended_defense") or {}).get("action", "NO_ACTION")
        cf_none = cf.run("NO_ACTION", max(0, self.state["current_event_index"] - 1))
        happening = "No correlated threat activity."
        if self.state["events"]:
            last = self.state["events"][-1]
            happening = f"{last['event_type']} on {last['asset_id']} ({last['timestamp']}). Intent: {intent}."
        going = f"Simulated next target: {target}." if target != "none" else "No predicted movement."
        should = f"Recommended simulated action: {rec}."
        if_not = (
            f"If no action: ~{cf_none['systems_affected']} systems, exposure {cf_none['exposure']} "
            f"(SIMULATED / ESTIMATED)."
        )
        return {"happening": happening, "going": going, "should_do": should, "if_not": if_not}

    def _time_machine(self) -> dict[str, Any]:
        idx = max(0, self.state["current_event_index"] - 1)
        branches = {}
        for action in ["NO_ACTION", "REVOKE_CREDENTIALS", "ISOLATE_ENDPOINT", "ISOLATE_AND_REVOKE"]:
            branches[action] = cf.run(action, idx)
        return {
            "past": [e.get("event_type") for e in self.state["events"][:-1]],
            "current": self.state["events"][-1]["event_type"] if self.state["events"] else "NORMAL",
            "predicted_future": (self.state.get("predictions") or [{}])[0].get("predicted_target") if self.state.get("predictions") else None,
            "alternate_futures": branches,
            "you_are_here": True,
        }

    def recompute(self, dropped_types: Optional[list[str]] = None) -> None:
        events = list(self.state["events"])
        if dropped_types:
            events = [e for e in events if e.get("event_type") not in dropped_types]
        det = detection.detect(events)
        contained = self.state.get("containment")
        if (self.state.get("containment_status") in ("SIMULATED", "VERIFIED")) and contained:
            from app.defense.containment import adjust_detection

            det = adjust_detection(det, contained)
        self.state["risk_score"] = det["risk_score"]
        self.state["risk_band"] = det["band"]
        self.state["ransomware_confidence"] = det["ransomware_confidence"]
        self.state["current_stage"] = det["attack_stage"]
        self.state["mitre"] = det["mitre"]
        self.state["attack_intent"] = intent_engine.infer_intent(events)
        self.state["detection"] = det["public"]

        db = self._db()
        try:
            mem = learning.list_memory(db)
        finally:
            db.close()

        rec = defense.recommend(
            det["risk_score"],
            det["attack_stage"],
            (self.state["attack_intent"] or {}).get("current_intent", "NONE"),
            mem,
        )
        self.state["defense_options"] = rec["options"]
        self.state["recommended_defense"] = rec["recommended_defense"]
        self.state["approval_gate"] = rec["approval_gate"]

        live_graph = build_attack_graph(events, det.get("public") or {}, contained)
        self.state["attack_graph"] = live_graph
        self.state["attack_path"] = live_graph.get("attack_path") or []

        forecast = prediction.forecast(
            events,
            live_graph,
            det.get("public") or {},
            bool(contained and contained.get("contained")),
            learning.adjustments(),
        )
        self.state["prediction"] = forecast
        self.state["predictions"] = forecast.get("ranked") or []
        if not events:
            self.state["prediction_history"] = []
            self.state["open_prediction"] = None
            self.state["prediction_outcomes"] = []
        elif forecast.get("predicted_target"):
            openp = self.state.get("open_prediction")
            if not openp or openp.get("outcome") != "UNRESOLVED":
                self.state["open_prediction"] = learning.new_prediction(forecast, events[-1])
            hist = list(self.state.get("prediction_outcomes") or [])
            if self.state.get("open_prediction"):
                hist = hist + [self.state["open_prediction"]]
            self.state["prediction_history"] = hist[-40:]

        adaptive = defense.recommend_adaptive(
            events,
            live_graph,
            det.get("public") or {},
            forecast,
            bool(contained and contained.get("contained")),
        )
        self.state["defense"] = adaptive
        if not events:
            self.state["pending_approval"] = None
            self.state["approval_status"] = "NONE"
            self.state["selected_action"] = None
            self.state["approved_by"] = None
            self.state["approval_timestamp"] = None
            self.state["containment_status"] = "NOT_APPLIED"

        preds = self.state["predictions"]

        g = graph_engine.snapshot(
            events,
            det["risk_score"],
            preds,
            contained,
            (contained or {}).get("blocked_paths") if contained else None,
        )
        self.state["topology_graph"] = g
        self.state["blast_radius"] = g["blast_radius"]
        self.state["intervention_window"] = intervention.window(
            (self.state.get("recommended_defense") or {}).get("action", "ISOLATE_AND_REVOKE")
        )
        self.state["loop_stage"] = self._loop_stage()
        self.state["what"] = self._what()
        self.state["time_machine"] = self._time_machine()
        at_risk = len(g["blast_radius"].get("potentially_affected") or [])
        affected = len(g["blast_radius"].get("current_affected") or [])
        self.state["assets_summary"] = {
            "protected": max(0, 8 - affected),
            "at_risk": at_risk,
            "active_incidents": 1 if events else 0,
            "threat_level": det["band"],
        }
        if preds:
            p = preds[0]
            self.state["uncertainty"] = {
                "next_target": p["predicted_target"],
                "confidence_range": p.get("confidence_range"),
                "defense_ranges": [
                    {"action": o["action"], "range": o.get("confidence_range")}
                    for o in self.state["defense_options"][:3]
                ],
            }
        # False positive context: process-only vs correlated
        types = {e.get("event_type") for e in events}
        context = "low"
        if "suspicious_process" in types and not (types & {"mass_file_modification", "credential_access"}):
            context = "low — process without impact correlation"
        elif "suspicious_process" in types and "mass_file_modification" in types and "credential_access" not in types:
            context = "medium/high — process plus mass modification"
        elif {"suspicious_process", "mass_file_modification", "credential_access", "lateral_movement"} <= types:
            context = "critical — correlated ransomware-prep chain"
        self.state["false_positive_context"] = {
            "correlation": context,
            "event_types": sorted(types),
            "note": "Benign look-alikes stay low without multi-signal correlation.",
        }
        self.state["attack_forks"] = fork_engine.build(self.state)
        self.state["adaptation"] = adaptation.analyze(self.state)
        if events:
            learning.record_defense_outcome(
                (self.state.get("defense") or {}).get("recommended_action"),
                self.state.get("adaptation"),
            )
        self.state["learning"] = learning.snapshot_learning(self.state)
        proposal = playbook_evo.consider(self.state)
        self.state["playbook_evolution"] = playbook_evo.snapshot()
        if proposal and not proposal.get("audited"):
            self._audit(
                "PLAYBOOK_CHANGE_PROPOSED",
                {
                    "timestamp": proposal.get("created_at"),
                    "playbook": proposal["playbook_id"],
                    "version": proposal["current_version"],
                    "proposed_version": proposal["proposed_version"],
                    "actor": "system",
                    "reason": proposal["reason"],
                    "change": proposal["change_id"],
                    "change_type": proposal["change_type"],
                },
            )
            proposal["audited"] = True
        self._save_incident()

    async def broadcast(self, kind: str = "state") -> None:
        if self._silent:
            return
        await hub.broadcast({"type": kind, "state": self.snapshot(), "ts": datetime.utcnow().isoformat()})

    async def start(self, scenario_id: str = "SCN-001") -> dict[str, Any]:
        if scenario_id not in SCENARIOS:
            scenario_id = "SCN-001"
        if self._demo_task:
            self._demo_task.cancel()
            self._demo_task = None
        self._clear_live_events()
        self.state = _empty_state()
        self.state["scenario_id"] = scenario_id
        suffix = datetime.utcnow().strftime("%H%M%S")
        self.state["incident_id"] = f"INC-LIVE-{suffix}"
        self._ensure_incident_row()
        self._audit("simulation_start", {"scenario_id": scenario_id})
        self.recompute()
        await self.broadcast("simulation_start")
        return self.snapshot()

    async def next_event(self) -> dict[str, Any]:
        catalog = SCENARIOS[self.state["scenario_id"]]["events"]
        idx = self.state["current_event_index"]
        if idx >= len(catalog):
            self._finalize_prediction_vs_reality()
            await self.broadcast("complete")
            return self.snapshot()
        if (self.state.get("containment") or {}).get("propagation_stopped") and idx >= 5:
            # Containment stops further propagation events after lateral stage
            self.state["loop_stage"] = "DEFEND"
            await self.broadcast("contained_hold")
            return self.snapshot()
        ev = dict(catalog[idx])
        ev["simulated"] = True
        pending = self.state.get("open_prediction")
        if pending and pending.get("outcome") == "UNRESOLVED":
            resolved = learning.resolve(pending, ev)
            outcomes = list(self.state.get("prediction_outcomes") or [])
            outcomes.append(resolved)
            self.state["prediction_outcomes"] = outcomes[-40:]
            self.state["open_prediction"] = None
        self.state["events"].append(ev)
        self.state["current_event_index"] = idx + 1
        self._persist_event(ev)
        self.recompute()
        self._audit("event", {"event_id": ev["id"], "type": ev["event_type"]})
        # Auto-contain LOW only for benign / false-positive scenarios.
        gate = self.state.get("approval_gate") or {}
        scenario = SCENARIOS.get(self.state.get("scenario_id"), {})
        if (
            scenario.get("kind") == "benign"
            and gate.get("level") == "LOW"
            and not self.state.get("approval")
            and self.state.get("recommended_defense")
        ):
            await self.approve(
                action=self.state["recommended_defense"]["action"],
                decision="AUTO_APPROVE",
                approver="system",
                reason="LOW risk automatic simulated response for benign scenario",
            )
        await self.broadcast("event")
        return self.snapshot()

    async def reset(self) -> dict[str, Any]:
        if self._demo_task:
            self._demo_task.cancel()
            self._demo_task = None
        self._clear_live_events()
        self.state = _empty_state()
        self._audit("simulation_reset", {})
        await self.broadcast("reset")
        return self.snapshot()

    async def recommend(self) -> dict[str, Any]:
        self.recompute()
        self._audit("defense_recommend", {"action": (self.state.get("defense") or {}).get("recommended_action")})
        await self.broadcast("recommend")
        return self.snapshot()

    async def prepare_review(self, action: str | None = None) -> dict[str, Any]:
        rec = (self.state.get("defense") or {}).get("recommended_action")
        chosen = action or rec
        if not chosen:
            raise ValueError("No defense action available to review.")
        options = (self.state.get("defense") or {}).get("options") or []
        opt = next((o for o in options if o.get("action") == chosen), None)
        now = datetime.utcnow().isoformat()
        self.state["selected_action"] = chosen
        self.state["approval_status"] = "PENDING_REVIEW"
        self.state["approved_by"] = None
        self.state["approval_timestamp"] = None
        self.state["containment_status"] = "NOT_APPLIED"
        self.state["pending_approval"] = {
            "action": chosen,
            "status": "PENDING_REVIEW",
            "executed": False,
            "pending": True,
            "simulated": True,
            "real_network_action": False,
            "note": "Queued for human approval. No containment executed.",
        }
        preview = {
            "action": chosen,
            "approval_status": "PENDING_REVIEW",
            "containment_status": "NOT_APPLIED",
            "projected_risk_before": (opt or {}).get("risk_before"),
            "projected_risk_after": (opt or {}).get("risk_after"),
            "projected_blast_radius_before": (opt or {}).get("blast_radius_before"),
            "projected_blast_radius_after": (opt or {}).get("blast_radius_after"),
            "operational_disruption": (opt or {}).get("operational_disruption"),
            "reversibility": (opt or {}).get("reversibility"),
            "reason": (opt or {}).get("reason") or (self.state.get("defense") or {}).get("recommended_reason"),
        }
        self.state["approval_preview"] = preview
        self._audit(
            "DEFENSE_REVIEWED",
            {"timestamp": now, "action": chosen, "status": "PENDING_REVIEW", "actor": "analyst", "reason": preview["reason"]},
            actor="analyst",
        )
        await self.broadcast("defense_review")
        return self.snapshot()

    async def approve_gated(self, action: str, approved_by: str, reason: str = "Approved for simulated containment") -> dict[str, Any]:
        if self.state.get("approval_status") != "PENDING_REVIEW":
            raise PermissionError("No defense action is pending human review.")
        pending_action = self.state.get("selected_action") or (self.state.get("pending_approval") or {}).get("action")
        if action and pending_action and action != pending_action:
            raise PermissionError(f"Pending action is {pending_action}, not {action}.")
        chosen = pending_action or action
        now = datetime.utcnow().isoformat()
        self.state["approval_status"] = "APPROVED"
        self.state["selected_action"] = chosen
        self.state["approved_by"] = approved_by
        self.state["approval_timestamp"] = now
        self.state["pending_approval"] = {
            "action": chosen,
            "status": "APPROVED",
            "executed": True,
            "pending": False,
            "simulated": True,
            "real_network_action": False,
        }
        self.state["approval"] = {
            "decision": "APPROVE",
            "action": chosen,
            "requested": action,
            "approver": approved_by,
            "reason": reason,
            "at": now,
        }
        self._audit(
            "DEFENSE_APPROVED",
            {"timestamp": now, "action": chosen, "status": "APPROVED", "actor": approved_by, "reason": reason},
            actor=approved_by,
        )
        from app.defense.containment import apply as apply_containment, verify as verify_containment

        applied = apply_containment(chosen, self.state.get("attack_graph") or {})
        self.state["containment"] = applied
        self.state["containment_status"] = "SIMULATED"
        self._audit(
            "CONTAINMENT_SIMULATED",
            {"timestamp": now, "action": chosen, "status": "SIMULATED", "actor": approved_by, "reason": "Synthetic state transition only"},
            actor=approved_by,
        )
        self.recompute()
        ok, verify_reason = verify_containment(chosen, self.state.get("attack_graph") or {}, applied)
        self.state["containment_status"] = "VERIFIED" if ok else "FAILED"
        self.state["containment_verify_reason"] = verify_reason
        applied["verification"] = {"ok": ok, "reason": verify_reason, "status": self.state["containment_status"]}
        self.state["containment"] = applied
        self._audit(
            "CONTAINMENT_VERIFIED" if ok else "CONTAINMENT_FAILED",
            {"timestamp": datetime.utcnow().isoformat(), "action": chosen, "status": self.state["containment_status"], "actor": approved_by, "reason": verify_reason},
            actor=approved_by,
        )
        await self.broadcast("approval")
        return self.snapshot()

    async def reject_gated(self, action: str, rejected_by: str, reason: str) -> dict[str, Any]:
        if self.state.get("approval_status") != "PENDING_REVIEW":
            raise PermissionError("No defense action is pending human review.")
        pending_action = self.state.get("selected_action") or (self.state.get("pending_approval") or {}).get("action")
        now = datetime.utcnow().isoformat()
        self.state["approval_status"] = "REJECTED"
        self.state["approved_by"] = None
        self.state["approval_timestamp"] = now
        self.state["containment_status"] = "NOT_APPLIED"
        self.state["containment"] = None
        self.state["selected_action"] = pending_action or action
        self.state["pending_approval"] = {
            "action": pending_action or action,
            "status": "REJECTED",
            "executed": False,
            "pending": False,
            "reason": reason,
            "simulated": True,
            "real_network_action": False,
        }
        self.state["approval"] = {
            "decision": "REJECT",
            "action": pending_action or action,
            "requested": action,
            "approver": rejected_by,
            "reason": reason,
            "at": now,
        }
        self._audit(
            "DEFENSE_REJECTED",
            {"timestamp": now, "action": pending_action or action, "status": "REJECTED", "actor": rejected_by, "reason": reason},
            actor=rejected_by,
        )
        await self.broadcast("defense_rejected")
        return self.snapshot()

    async def simulate_defense(self, action: str) -> dict[str, Any]:
        sim = defense.simulate_containment(action, self.state.get("attack_graph") or {})
        preview = cf.run(action, max(0, self.state["current_event_index"] - 1))
        self.state["defense_preview"] = {**sim, "counterfactual": preview}
        self._audit("defense_simulate", {"action": action})
        await self.broadcast("simulate")
        return self.snapshot()

    async def approve(self, action: str, decision: str, approver: str, reason: str, modified_action: Optional[str] = None) -> dict[str, Any]:
        chosen = modified_action or action
        if decision in ("REJECT",):
            chosen = "NO_ACTION"
        self.state["approval"] = {
            "decision": decision,
            "action": chosen,
            "requested": action,
            "approver": approver,
            "reason": reason,
            "at": datetime.utcnow().isoformat(),
        }
        if not self._silent:
            db = self._db()
            try:
                db.add(
                    Decision(
                        incident_id=self.state["incident_id"],
                        action=chosen,
                        decision=decision,
                        approver=approver,
                        reason=reason,
                    )
                )
                db.add(
                    DefenseAction(
                        incident_id=self.state["incident_id"],
                        action=chosen,
                        status=decision,
                        approver=approver,
                        reason=reason,
                        simulated=1,
                    )
                )
                db.commit()
            finally:
                db.close()
        self._audit("defense_decision", {"decision": decision, "action": chosen, "reason": reason}, actor=approver)

        if decision in ("APPROVE", "AUTO_APPROVE", "MODIFY"):
            contained = defense.simulate_containment(chosen, self.state.get("attack_graph") or {})
            self.state["containment"] = contained
            self.state["adaptive_paths"] = adaptation.adapt(chosen, True)
            idx = max(0, self.state["current_event_index"] - 1)
            actual = cf.run(chosen, idx)
            alts = cf.run_all(idx)
            best_idx = min(3, idx)  # BEST window at 10:03 when that time has passed
            candidates = alts + [cf.run(a, best_idx) for a in ["REVOKE_CREDENTIALS", "ISOLATE_ENDPOINT", "ISOLATE_AND_REVOKE"]]
            best = max(candidates, key=lambda x: (x["containment"], -x["systems_affected"]))
            self.state["counterfactuals"] = alts
            self.state["alternate_realities"] = cf.alternate_realities(chosen, idx)
            missed = cf.missed_impact(actual, best)
            regret = cf.defense_regret(actual, best)
            self.state["missed_impact"] = missed
            self.state["defense_regret"] = regret["defense_regret_score"]
            self.state["defense_regret_detail"] = regret
            quality = learning.quality_from_regret(regret["defense_regret_score"])
            if not self._silent:
                db = self._db()
                try:
                    learning.record_memory(
                        db,
                        self.state["incident_id"],
                        self.state["current_stage"],
                        chosen,
                        "contained" if contained.get("contained") else "open",
                        missed,
                        quality,
                        best["action"],
                    )
                    proposal = playbooks.propose_update(
                        db, self.state["incident_id"], regret["defense_regret_score"], best["action"]
                    )
                    self.state["playbook"] = proposal
                    prev = dict(self.state.get("learning") or {})
                    self.state["learning"] = {
                        **prev,
                        "memory": learning.list_memory(db)[:8],
                        "quality": quality,
                        "future_action": best["action"],
                    }
                finally:
                    db.close()
            self.recompute()
        await self.broadcast("approval")
        return self.snapshot()

    async def run_counterfactual(self, action: str, intervention_index: int) -> dict[str, Any]:
        result = cf.run(action, intervention_index)
        self.state["last_counterfactual"] = result
        existing = self.state.get("counterfactuals") or []
        self.state["counterfactuals"] = existing + [result]
        self.state["alternate_realities"] = cf.alternate_realities(
            (self.state.get("approval") or {}).get("action") or "NO_ACTION",
            intervention_index,
        )
        self._audit("counterfactual", result)
        await self.broadcast("counterfactual")
        return self.snapshot()

    async def robustness(self, action: Optional[str], rates: list[int]) -> dict[str, Any]:
        act = action or (self.state.get("recommended_defense") or {}).get("action")
        self.state["robustness"] = adaptation.robustness_test(act, rates)
        self._audit("robustness", self.state["robustness"])
        await self.broadcast("robustness")
        return self.snapshot()

    def robustness_drop_event(self, event_type: str) -> dict[str, Any]:
        before = self.state.get("ransomware_confidence")
        self.recompute(dropped_types=[event_type])
        after = self.state.get("ransomware_confidence")
        drop = (before or 0) - (after or 0)
        self.state["robustness_signal"] = {
            "removed": event_type,
            "confidence_before": before,
            "confidence_after": after,
            "drop": drop,
            "uncertain": drop >= 15,
            "note": "UNCERTAIN — HUMAN REVIEW REQUIRED" if drop >= 15 else "Confidence remained relatively stable",
        }
        return self.snapshot()

    def set_intervention(self, index: int) -> dict[str, Any]:
        action = (self.state.get("recommended_defense") or {}).get("action", "ISOLATE_AND_REVOKE")
        self.state["selected_intervention"] = intervention.impact_at(index, action)
        return self.snapshot()

    def replay_control(self, command: str, speed: float = 1.0, index: Optional[int] = None) -> dict[str, Any]:
        r = self.state["incident_replay"]
        if command == "PLAY":
            r["playing"] = True
        elif command == "PAUSE":
            r["playing"] = False
        elif command == "REPLAY":
            r["index"] = 0
            r["playing"] = True
        elif command == "PREVIOUS":
            r["index"] = max(0, r["index"] - 1)
        elif command == "NEXT":
            r["index"] = min(len(self.state["events"]), r["index"] + 1)
        elif command == "SEEK" and index is not None:
            r["index"] = max(0, min(len(self.state["events"]), index))
        r["speed"] = speed
        idx = min(r["index"], max(0, len(self.state["events"]) - 1)) if self.state["events"] else 0
        known = self.state["events"][: idx + 1] if self.state["events"] else []
        r["focus"] = {
            "event": known[-1] if known else None,
            "defender_knew": [e["event_type"] for e in known],
            "available_action": (self.state.get("recommended_defense") or {}).get("action"),
            "would_have_happened": cf.run("ISOLATE_AND_REVOKE", idx) if known else None,
        }
        self.state["incident_replay"] = r
        return self.snapshot()

    def _finalize_prediction_vs_reality(self) -> None:
        events = self.state["events"]
        actual = "BACKUP-SRV-01" if any(e.get("event_type") == "backup_access_attempt" for e in events) else (
            "FILE-SRV-01" if any(e.get("event_type") == "file_server_access" for e in events) else "FAC-PC-07"
        )
        pred = (self.state.get("predictions") or [{}])[0].get("predicted_target", "")
        conf = (self.state.get("predictions") or [{}])[0].get("confidence", 0)
        self.state["prediction_vs_reality"] = learning.compare_prediction(pred, actual, conf)

    def investigate(self, question: str) -> dict[str, Any]:
        result = investigate(question, self.snapshot())
        self._audit("ai_investigate", {"question": question, "source": result["source"]})
        return result

    def evaluation(self) -> dict[str, Any]:
        return evaluation.evaluate(self.snapshot())

    def scenarios(self) -> list[dict[str, Any]]:
        return scenario_catalog()

    async def demo(self, command: str) -> dict[str, Any]:
        if command == "RESET":
            return await self.reset()
        if command == "PAUSE":
            self.state["demo"]["paused"] = True
            await self.broadcast("demo")
            return self.snapshot()
        if command == "START":
            if self._demo_task:
                self._demo_task.cancel()
            await self.start("SCN-001")
            self.state["demo"] = {"running": True, "paused": False, "elapsed": 0, "phase": "safe"}
            self._demo_task = asyncio.create_task(self._run_demo())
        return self.snapshot()

    async def _run_demo(self) -> None:
        # 3-minute script driving the SAME simulation state
        script = [
            (0, "safe", None),
            (20, "suspicious", "next"),
            (40, "confidence", "next"),
            (40, "confidence", "next"),
            (60, "graph", "next"),
            (80, "predict", "next"),
            (100, "defense", "recommend"),
            (120, "approval", "approve"),
            (135, "containment", None),
            (150, "replay", "cf"),
            (160, "alternate", None),
            (170, "regret", "robust"),
            (180, "playbook", None),
        ]
        start = datetime.utcnow()
        cursor = 0
        try:
            while cursor < len(script):
                await asyncio.sleep(0.4)
                if self.state.get("demo", {}).get("paused"):
                    continue
                elapsed = (datetime.utcnow() - start).total_seconds()
                self.state["demo"]["elapsed"] = int(elapsed)
                t, phase, action = script[cursor]
                if elapsed < t:
                    continue
                self.state["demo"]["phase"] = phase
                if action == "next":
                    await self.next_event()
                elif action == "recommend":
                    await self.recommend()
                elif action == "approve":
                    rec = (self.state.get("recommended_defense") or {}).get("action", "ISOLATE_AND_REVOKE")
                    await self.approve(rec, "APPROVE", "demo.admin", "3-minute demo simulated approval")
                elif action == "cf":
                    await self.run_counterfactual("ISOLATE_AND_REVOKE", 3)
                elif action == "robust":
                    await self.robustness(None, [30, 50, 70, 90])
                cursor += 1
                await self.broadcast("demo")
            self.state["demo"]["running"] = False
            self.state["demo"]["phase"] = "complete"
            await self.broadcast("demo")
        except asyncio.CancelledError:
            return

    async def approve_playbook_change(self, change_id: str, actor: str, reason: str = "") -> dict[str, Any]:
        result = playbook_evo.approve(change_id, actor, reason)
        prop = result["proposal"]
        active = result["active"]
        self._audit(
            "PLAYBOOK_CHANGE_APPROVED",
            {
                "timestamp": prop.get("resolved_at"),
                "playbook": prop["playbook_id"],
                "version": active["version"],
                "actor": actor,
                "reason": reason or prop.get("reason"),
                "change": change_id,
            },
            actor=actor,
        )
        self._audit(
            "PLAYBOOK_VERSION_ACTIVATED",
            {
                "timestamp": active.get("created_at"),
                "playbook": active["playbook_id"],
                "version": active["version"],
                "actor": actor,
                "reason": active.get("reason_for_change"),
                "change": change_id,
            },
            actor=actor,
        )
        follow = playbook_evo.consider(self.state)
        if follow and not follow.get("audited"):
            self._audit(
                "PLAYBOOK_CHANGE_PROPOSED",
                {
                    "timestamp": follow.get("created_at"),
                    "playbook": follow["playbook_id"],
                    "version": follow["current_version"],
                    "proposed_version": follow["proposed_version"],
                    "actor": "system",
                    "reason": follow["reason"],
                    "change": follow["change_id"],
                    "change_type": follow["change_type"],
                },
            )
            follow["audited"] = True
        self.state["playbook_evolution"] = playbook_evo.snapshot()
        await self.broadcast("playbook_approved")
        return result

    async def reject_playbook_change(self, change_id: str, actor: str, reason: str = "") -> dict[str, Any]:
        result = playbook_evo.reject(change_id, actor, reason)
        prop = result["proposal"]
        self._audit(
            "PLAYBOOK_CHANGE_REJECTED",
            {
                "timestamp": prop.get("resolved_at"),
                "playbook": prop["playbook_id"],
                "version": prop.get("current_version"),
                "actor": actor,
                "reason": reason or prop.get("reject_reason"),
                "change": change_id,
            },
            actor=actor,
        )
        self.state["playbook_evolution"] = playbook_evo.snapshot()
        await self.broadcast("playbook_rejected")
        return result


engine = SimulationEngine()
