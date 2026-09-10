import { fmt } from "../utils/format.js";
import EvidenceStack from "./EvidenceStack.jsx";
import { EmptyState, MetaBadge } from "./ui.jsx";

export default function PredictionPanel({ prediction, currentNode }) {
  const p = prediction || {};
  const alts = p.alternatives || [];
  const evidence = p.evidence || [];
  const has = Boolean(p.predicted_target);

  return (
    <div className="panel border-violet-500/30 p-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="text-[10px] font-semibold uppercase tracking-[0.16em] text-violet-400">Next target prediction</div>
        <MetaBadge tone="blue">Prediction — not observed reality</MetaBadge>
      </div>
      <p className="mt-1 text-[11px] text-soc-muted">{p.label || "SIMULATED prediction — not real-world accuracy"}</p>
      {!has ? (
        <div className="mt-3">
          <EmptyState title="No prediction yet" body="Advance synthetic events until the intelligence layer can forecast the next target." />
        </div>
      ) : (
        <>
          <div className="mt-4 grid gap-3 md:grid-cols-4">
            <div className="rounded-lg bg-soc-raised p-3">
              <div className="text-[10px] uppercase tracking-wide text-soc-muted">Current node</div>
              <div className="mt-1 font-mono text-lg font-semibold">{currentNode || p.current_node || "none"}</div>
            </div>
            <div className="rounded-lg border border-violet-500/40 bg-violet-500/10 p-3">
              <div className="text-[10px] uppercase tracking-wide text-soc-muted">Target</div>
              <div className="mt-1 font-mono text-lg font-semibold text-violet-400">{p.predicted_target}</div>
            </div>
            <div className="rounded-lg border border-blue-500/40 bg-blue-500/10 p-3">
              <div className="text-[10px] uppercase tracking-wide text-soc-muted">Action</div>
              <div className="mt-1 font-mono text-lg font-semibold text-blue-400">{p.predicted_action}</div>
            </div>
            <div className="rounded-lg bg-soc-raised p-3">
              <div className="text-[10px] uppercase tracking-wide text-soc-muted">Prediction score</div>
              <div className="mt-1 font-mono text-3xl font-semibold text-blue-400">{fmt(p.confidence || 0)}</div>
            </div>
          </div>
          <p className="mt-4 text-sm">{p.reason}</p>
          <div className="mt-4 text-[10px] uppercase tracking-wide text-soc-muted">Supporting evidence</div>
          <div className="mt-2">
            <EvidenceStack items={evidence} />
          </div>
          {alts.length > 0 ? (
            <div className="mt-4 grid gap-3 md:grid-cols-3">
              {alts.map((a) => (
                <div key={a.predicted_target} className="rounded-lg border border-soc-border p-3">
                  <div className="text-[10px] uppercase text-soc-muted">Alternative</div>
                  <div className="font-mono font-semibold">{a.predicted_target}</div>
                  <div className="text-sm">{fmt(a.confidence)}%</div>
                  <div className="font-mono text-xs text-soc-muted">{a.predicted_action}</div>
                </div>
              ))}
            </div>
          ) : null}
        </>
      )}
    </div>
  );
}
