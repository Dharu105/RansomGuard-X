import { useMemo } from "react";
import { useSearchParams } from "react-router-dom";
import { useSimulation } from "../hooks/useSimulation.jsx";
import EventStream from "../components/EventStream.jsx";
import DetectionPanel from "../components/DetectionPanel.jsx";
import AttackGraphView from "../components/AttackGraph.jsx";
import PredictionPanel from "../components/PredictionPanel.jsx";
import DefensePanel from "../components/DefensePanel.jsx";
import AttackForkLab from "../components/AttackForkLab.jsx";
import AdaptationPanel from "../components/AdaptationPanel.jsx";
import LearningPanel from "../components/LearningPanel.jsx";
import PlaybookEvolutionPanel from "../components/PlaybookEvolutionPanel.jsx";
import AIInvestigatorPanel from "../components/AIInvestigatorPanel.jsx";
import EvaluationPanel from "../components/EvaluationPanel.jsx";
import ThreatCore from "../components/ThreatCore.jsx";
import AttackTimeline from "../components/AttackTimeline.jsx";
import HeroIntel from "../components/HeroIntel.jsx";
import { EmptyState, LoopStrip } from "../components/ui.jsx";

const LOOP = ["DETECT", "UNDERSTAND", "PREDICT", "SIMULATE", "RESPOND", "LEARN", "EVOLVE", "EVALUATE"];

const TABS = [
  { id: "incident", label: "Telemetry" },
  { id: "detect", label: "Detection" },
  { id: "graph", label: "Graph" },
  { id: "predict", label: "Forecast" },
  { id: "defend", label: "Defense" },
  { id: "forks", label: "Fork Lab" },
  { id: "adapt", label: "Adaptation" },
  { id: "learn", label: "Learning" },
  { id: "playbook", label: "Playbooks" },
  { id: "investigate", label: "Investigator" },
  { id: "evaluate", label: "Evaluation" },
];

function loopActive(state) {
  const stage = (state?.loop_stage || "OBSERVE").toUpperCase();
  if (stage in { OBSERVE: 1, DETECT: 1 }) return "DETECT";
  if (stage === "UNDERSTAND") return "UNDERSTAND";
  if (stage === "PREDICT") return "PREDICT";
  if (stage in { COMPARE: 1, REPLAY: 1 }) return "SIMULATE";
  if (stage in { DECIDE: 1, DEFEND: 1 }) return "RESPOND";
  if (stage === "LEARN") return "LEARN";
  if ((state?.playbook_evolution || {}).open_proposal) return "EVOLVE";
  if ((state?.evaluation || {}).has_report) return "EVALUATE";
  return "DETECT";
}

export default function CommandCenter() {
  const { state, actions, busy, error, status } = useSimulation();
  const [params, setParams] = useSearchParams();
  const tabParam = params.get("tab") || "incident";
  const tab = TABS.some((t) => t.id === tabParam) ? tabParam : "incident";
  const events = state?.events || [];
  const lastId = events.length ? events[events.length - 1].id : null;
  const activeLoop = useMemo(() => (state ? loopActive(state) : "DETECT"), [state]);

  const setTab = (id) => {
    const next = new URLSearchParams(params);
    if (id === "incident") next.delete("tab");
    else next.set("tab", id);
    setParams(next, { replace: true });
  };

  if (!state) {
    if (status === "error" || error) {
      return (
        <EmptyState
          title="Connection interrupted"
          body={error || "Unable to receive live simulation updates."}
          action={
            <button className="btn btn-ghost mt-4" onClick={() => actions.refresh()}>
              Retry
            </button>
          }
        />
      );
    }
    return <EmptyState title="Connecting to simulation" body="Establishing the command-center session." />;
  }

  const idle = events.length === 0;
  const showOps = tab !== "incident";

  return (
    <div className="space-y-3">
      <div className="war-frame">
        <div className="relative z-10 flex flex-wrap items-center justify-between gap-2 border-b border-soc-border/80 px-4 py-2.5">
          <div>
            <div className="text-[11px] font-semibold uppercase tracking-[0.22em]">RansomGuard-X</div>
            <div className="text-[10px] uppercase tracking-[0.12em] text-soc-muted">AI Cyber-Resilience Command Center</div>
          </div>
          <div className="flex items-center gap-3 text-[10px] uppercase tracking-wide">
            <span className={idle ? "text-soc-muted" : "text-cyan-400"}>● {idle ? "Standby" : "Live incident"}</span>
            <span className="font-mono text-soc-text">{state.current_stage || "NORMAL"}</span>
            <span className="hidden text-soc-muted sm:inline">See the Threat. Shape the Defense.</span>
          </div>
        </div>

        <div className="relative z-10 grid gap-3 p-3 xl:grid-cols-[188px_minmax(0,1fr)_272px]">
          <ThreatCore
            score={state.risk_score}
            band={state.risk_band}
            events={events.length}
            assets={state.assets_summary?.at_risk ?? 0}
            stage={state.current_stage}
            idle={idle}
          />
          <AttackGraphView
            graph={state.attack_graph}
            predictedTarget={state.prediction?.predicted_target}
            compact
            alive={!idle}
          />
          <HeroIntel
            idle={idle}
            prediction={state.prediction}
            currentNode={state.attack_graph?.current_node}
            defense={state.defense}
            busy={busy}
            onReview={(action) => {
              actions.reviewDefense(action);
              setTab("defend");
            }}
            onOpenDefense={() => setTab("defend")}
            onOpenPredict={() => setTab("predict")}
          />
        </div>
        <div className="relative z-10 px-3 pb-3">
          <AttackTimeline events={events} lastId={lastId} />
        </div>
      </div>

      <LoopStrip steps={LOOP} active={activeLoop} />

      <div className="flex flex-wrap gap-1" role="tablist" aria-label="Operations views">
        {TABS.map((t) => (
          <button
            key={t.id}
            type="button"
            role="tab"
            aria-selected={tab === t.id}
            className={`ops-tab ${tab === t.id ? "ops-tab-on" : "hover:text-white"}`}
            onClick={() => setTab(t.id)}
          >
            {t.label}
          </button>
        ))}
      </div>

      {tab === "incident" && <EventStream events={events} lastId={lastId} />}
      {tab === "detect" && <DetectionPanel detection={state.detection} />}
      {tab === "graph" && showOps && (
        <AttackGraphView graph={state.attack_graph} predictedTarget={state.prediction?.predicted_target} alive={!idle} />
      )}
      {tab === "predict" && (
        <PredictionPanel prediction={state.prediction} currentNode={state.attack_graph?.current_node} />
      )}
      {tab === "defend" && (
        <DefensePanel
          defense={state.defense}
          pendingApproval={state.pending_approval}
          approvalStatus={state.approval_status}
          containmentStatus={state.containment_status}
          selectedAction={state.selected_action}
          approvedBy={state.approved_by}
          verifyReason={state.containment_verify_reason}
          busy={busy}
          onReview={(action) => actions.reviewDefense(action)}
          onApprove={(action) => actions.approveDefense({ action, approved_by: "Security Analyst" })}
          onReject={(action, reason) =>
            actions.rejectDefense({ action, rejected_by: "Security Analyst", reason })
          }
        />
      )}
      {tab === "forks" && (
        <AttackForkLab
          forksPayload={state.attack_forks}
          busy={busy}
          onReview={(action) => actions.reviewDefense(action)}
        />
      )}
      {tab === "adapt" && <AdaptationPanel adaptation={state.adaptation} />}
      {tab === "learn" && <LearningPanel learning={state.learning} />}
      {tab === "playbook" && (
        <PlaybookEvolutionPanel
          evolution={state.playbook_evolution}
          busy={busy}
          onApprove={(changeId) =>
            actions.approvePlaybookChange({ change_id: changeId, actor: "Security Analyst" })
          }
          onReject={(changeId) =>
            actions.rejectPlaybookChange({
              change_id: changeId,
              actor: "Security Analyst",
              reason: "Not appropriate for this synthetic incident",
            })
          }
        />
      )}
      {tab === "investigate" && <AIInvestigatorPanel investigator={state.investigator} />}
      {tab === "evaluate" && (
        <EvaluationPanel
          evaluation={state.evaluation}
          busy={busy}
          onRun={() => actions.runEvaluation()}
          onReset={() => actions.resetEvaluation()}
        />
      )}
    </div>
  );
}
