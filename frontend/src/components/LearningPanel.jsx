import { fmt } from "../utils/format.js";
import { MetaBadge } from "./ui.jsx";

function outcomeTone(o) {
  if (o === "CORRECT") return "text-soc-good";
  if (o === "PARTIAL") return "text-soc-warn";
  if (o === "INCORRECT") return "text-soc-crit";
  return "text-soc-muted";
}

export default function LearningPanel({ learning }) {
  const L = learning || {};
  const summary = L.summary || {};
  const recent = (L.recent_outcomes || []).filter((r) => r.outcome && r.outcome !== "UNRESOLVED");
  const adjustments = L.memory_adjustments || [];
  const defenseMem = L.defense_memory || [];
  const openp = L.open_prediction;

  return (
    <div className="panel p-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="text-[10px] font-semibold uppercase tracking-[0.16em] text-soc-muted">Incident memory</div>
        <MetaBadge tone="mute">Simulation / experimental</MetaBadge>
      </div>
      <p className="mt-1 text-sm text-soc-muted">Incident memory from synthetic simulation history.</p>

      <div className="mt-4 grid gap-3 md:grid-cols-4">
        <div className="rounded-lg border border-indigo-500/20 bg-[#0c1422] p-3">
          <div className="text-[10px] uppercase text-indigo-300">Prediction</div>
          <div className="mt-2 font-mono">{openp?.predicted_target || recent[0]?.predicted_target || "—"}</div>
        </div>
        <div className="flex items-center justify-center text-soc-muted">↓</div>
        <div className="rounded-lg border border-cyan-500/20 bg-[#0c1422] p-3">
          <div className="text-[10px] uppercase text-cyan-400">Reality</div>
          <div className="mt-2 font-mono">{recent[0]?.actual_target || (openp ? "UNRESOLVED" : "—")}</div>
        </div>
        <div className="rounded-lg border border-soc-border bg-[#0c1422] p-3">
          <div className="text-[10px] uppercase text-soc-muted">Outcome → memory</div>
          <div className={`mt-2 font-semibold ${outcomeTone(recent[0]?.outcome)}`}>{recent[0]?.outcome || (openp ? "WAITING" : "NONE")}</div>
        </div>
      </div>

      <div className="mt-4 flex flex-wrap items-center gap-2 text-[11px] uppercase tracking-wide text-soc-muted">
        <span>Prediction</span><span>↓</span>
        <span>Reality</span><span>↓</span>
        <span>Outcome</span><span>↓</span>
        <span>Learning</span>
      </div>

      <div className="mt-3 grid gap-3 md:grid-cols-2">
        <div className="rounded-lg bg-soc-raised p-3">
          <div className="text-[10px] uppercase text-soc-muted">Current incident</div>
          {openp ? (
            <>
              <div className="text-sm">Prediction: <b className="font-mono">{openp.predicted_target}</b></div>
              <div className="text-sm">Action: {openp.predicted_action}</div>
              <div className="text-sm">Result: UNRESOLVED</div>
              <div className="text-xs text-soc-muted">Waiting for the next synthetic event. Not marked correct yet.</div>
            </>
          ) : (
            <div className="text-sm text-soc-muted">No open prediction in the current scenario.</div>
          )}
        </div>
        <div className="rounded-lg bg-soc-raised p-3">
          <div className="text-[10px] uppercase text-soc-muted">Simulation learning</div>
          <div className="text-lg font-semibold">Overall {fmt(summary.overall_accuracy || 0)}%</div>
          <div className="text-sm">Target accuracy {fmt(summary.target_accuracy || 0)}%</div>
          <div className="text-sm">Action accuracy {fmt(summary.action_accuracy || 0)}%</div>
          <div className="text-sm">Resolved {summary.resolved_predictions || 0}</div>
        </div>
      </div>

      {recent.length > 0 && (
        <div className="mt-4 overflow-x-auto">
          <div className="text-[10px] uppercase text-soc-muted">Recent outcomes</div>
          <table className="mt-2 w-full text-left text-sm">
            <thead className="text-xs text-soc-muted">
              <tr>
                <th className="py-1">Prediction</th>
                <th>Actual</th>
                <th>Result</th>
                <th>Confidence</th>
              </tr>
            </thead>
            <tbody>
              {recent.map((r) => (
                <tr key={r.prediction_id}>
                  <td className="py-1 font-mono">{r.predicted_target}</td>
                  <td className="font-mono">{r.actual_target}</td>
                  <td className={outcomeTone(r.outcome)}>{r.outcome}</td>
                  <td>{fmt(r.confidence)}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <div className="mt-4">
        <div className="text-[10px] uppercase text-soc-muted">Learning memory</div>
        <p className="mt-1 text-[11px] text-soc-muted">
          Historical outcomes provide bounded adjustments (−10 to +10); current evidence remains primary.
          Simulation reset clears the current scenario, not this memory.
        </p>
        {adjustments.length === 0 ? (
          <p className="mt-2 text-sm text-soc-muted">No historical adjustments yet.</p>
        ) : (
          <ul className="mt-2 space-y-1 text-sm">
            {adjustments.map((m) => (
              <li key={m.target} className="font-mono">
                {m.target}: historical adjustment {m.historical_adjustment > 0 ? "+" : ""}
                {m.historical_adjustment}
              </li>
            ))}
          </ul>
        )}
      </div>

      <div className="mt-4">
        <div className="text-[10px] uppercase text-soc-muted">Defense memory</div>
        {defenseMem.length === 0 ? (
          <p className="mt-2 text-sm text-soc-muted">No stored defense outcomes yet.</p>
        ) : (
          <div className="mt-2 grid gap-2 md:grid-cols-2">
            {defenseMem.map((d) => (
              <div key={d.defense_action} className="rounded-lg border border-soc-border p-3 text-sm">
                <div className="font-semibold font-mono">{d.defense_action}</div>
                <div>Previous outcome: {d.previous_outcome || "n/a"}</div>
                <div>Adaptive outcome: {d.adaptive_outcome || "n/a"}</div>
                <div>Robustness: {d.robustness || "n/a"}</div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
